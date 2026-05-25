# Backend/api/rag/indexador.py

import fitz  # pymupdf
import ollama
import time
import threading
from pathlib import Path

# OCR deshabilitado hasta implementacion futura
OCR_DISPONIBLE = False

from . import normalizar_nombre_coleccion, get_cliente_chroma, detectar_idioma

CHUNK_SIZE      = 200
CHUNK_OVERLAP   = 30
MIN_CHUNK_WORDS = 10

# Keywords que indican paginas de tablas de averias/troubleshooting
_TABLA_KEYWORDS = [
    "sintoma", "causa probable", "accion correctiva",
    "symptom", "probable cause", "corrective action",
    "fault", "remedy", "busqueda de averias", "troubleshooting",
]

_progreso: dict = {}
_lock = threading.Lock()


def get_progreso(nombre_maquina: str) -> dict:
    key = normalizar_nombre_coleccion(nombre_maquina)
    with _lock:
        return dict(_progreso.get(key, {"estado": "no_iniciado"}))


def _set_progreso(key: str, datos: dict):
    with _lock:
        _progreso[key] = datos


def _construir_mapa_secciones(toc: list, total_paginas: int) -> list:
    if not toc:
        return []
    secciones = []
    for i, entrada in enumerate(toc):
        _, titulo, pagina_inicio = entrada
        pagina_fin = toc[i + 1][2] - 1 if i + 1 < len(toc) else total_paginas
        secciones.append({
            "titulo":        titulo.strip(),
            "pagina_inicio": pagina_inicio,
            "pagina_fin":    max(pagina_inicio, pagina_fin),
        })
    return secciones


def _obtener_seccion_para_pagina(pagina: int, secciones: list) -> str:
    seccion_actual = ""
    for s in secciones:
        if s["pagina_inicio"] <= pagina:
            seccion_actual = s["titulo"]
        else:
            break
    return seccion_actual


def _reformatear_filas_tabla(filas: list) -> list:
    """
    Si las filas contienen encabezados SINTOMA/CAUSA/ACCION, convierte cada
    fila a texto natural para mejorar la calidad del embedding.
    "EL COMPRESOR NO ARRANCA | Interruptor abierto | Cerrar el seccionador"
    -> "Síntoma: EL COMPRESOR NO ARRANCA. Causa probable: Interruptor abierto. Acción correctiva: Cerrar el seccionador."
    """
    es_tabla_averias = any(
        "|" in f and any(kw in f.lower() for kw in ["sintoma", "symptom", "causa", "fault"])
        for f in filas
    )
    if not es_tabla_averias:
        return filas

    resultado = []
    sintoma_actual = ""

    for fila in filas:
        partes = [p.strip() for p in fila.split("|")]

        # Encabezado de columnas → saltar
        if len(partes) >= 2 and any(kw in partes[0].lower() for kw in ["sintoma", "symptom", "fault"]):
            continue

        # Fila sin pipes
        if len(partes) == 1:
            texto = partes[0].strip()
            # Sintoma ALL_CAPS sin digitos → actualizar sintoma actual
            if (texto.upper() == texto
                    and len(texto.split()) >= 2
                    and not any(c.isdigit() for c in texto)):
                sintoma_actual = texto
                # No agregar sola: se incorpora en las filas de causa/accion siguientes
            else:
                resultado.append(fila)
            continue

        # Fila con pipes
        col1 = partes[0].strip()
        col2 = partes[1].strip() if len(partes) > 1 else ""
        col3 = partes[2].strip() if len(partes) > 2 else ""

        # Col1 es sintoma si es ALL_CAPS sin digitos
        col1_es_sintoma = (col1.upper() == col1
                           and len(col1.split()) >= 2
                           and not any(c.isdigit() for c in col1))

        if col1_es_sintoma:
            sintoma_actual = col1
            causa  = col2
            accion = col3
        else:
            causa  = col1
            accion = col2

        if not sintoma_actual:
            resultado.append(fila)
            continue

        partes_nat = [f"Sintoma: {sintoma_actual}"]
        if causa:
            partes_nat.append(f"Causa probable: {causa}")
        if accion:
            partes_nat.append(f"Accion correctiva: {accion}")
        resultado.append(". ".join(partes_nat) + ".")

    return resultado if resultado else filas


def _filas_por_posicion(pagina) -> list:
    """
    Para paginas con tablas: agrupa lineas por coordenada Y.
    Cada fila -> texto natural reconstruido desde columnas SINTOMA/CAUSA/ACCION.
    Intenta find_tables() (PyMuPDF >= 1.23) primero, luego fallback Y-position.
    """
    try:
        tabs = pagina.find_tables()
        if tabs.tables:
            filas = []
            for tabla in tabs.tables:
                for fila in tabla.extract():
                    celdas = [str(c).strip() if c else "" for c in fila]
                    texto = " | ".join(c for c in celdas if c)
                    if len(texto.split()) >= 2:
                        filas.append(texto)
            if filas:
                return _reformatear_filas_tabla(filas)
    except AttributeError:
        pass

    lineas = []
    try:
        data = pagina.get_text("dict")
        for bloque in data.get("blocks", []):
            if bloque.get("type") != 0:
                continue
            for linea in bloque.get("lines", []):
                y_top  = linea["bbox"][1]
                x_left = linea["bbox"][0]
                texto  = " ".join(span["text"] for span in linea.get("spans", [])).strip()
                if texto:
                    lineas.append({"y": y_top, "x": x_left, "texto": texto})
    except Exception:
        return []

    if not lineas:
        return []

    lineas.sort(key=lambda l: (round(l["y"] / 4) * 4, l["x"]))
    grupos = []
    grupo_actual = [lineas[0]]
    for linea in lineas[1:]:
        if abs(linea["y"] - grupo_actual[-1]["y"]) <= 4:
            grupo_actual.append(linea)
        else:
            grupos.append(grupo_actual)
            grupo_actual = [linea]
    if grupo_actual:
        grupos.append(grupo_actual)

    resultado = []
    for grupo in grupos:
        grupo.sort(key=lambda l: l["x"])
        texto_fila = " ".join(" | ".join(l["texto"] for l in grupo).split())
        palabras = texto_fila.split()
        es_caps_solo = (len(palabras) == 1
                        and texto_fila.strip().upper() == texto_fila.strip()
                        and texto_fila.strip().isalpha())
        if len(palabras) >= 2 or es_caps_solo:
            resultado.append(texto_fila)

    # ── Merge fragmentos de sintoma partidos ────────────────────────────────────
    # "EL COMPRESOR NO" + fila_causa_accion + "ARRANCA"
    # → "EL COMPRESOR NO ARRANCA"
    # Condiciones: fragmento ALL_CAPS sin digitos, con max 2 filas intermedias.
    merged = []
    caps_pendiente_idx = -1
    rows_since_caps    = 0

    for fila in resultado:
        partes  = fila.split(" | ")
        primera = partes[0].strip()
        es_solo_caps = (len(partes) == 1
                        and primera.upper() == primera
                        and len(primera) > 1
                        and primera not in ("SINTOMA", "SYMPTOM")
                        and not any(c.isdigit() for c in primera))
        if es_solo_caps:
            if caps_pendiente_idx >= 0 and rows_since_caps <= 2:
                merged[caps_pendiente_idx] = merged[caps_pendiente_idx] + " " + primera
                caps_pendiente_idx = -1
                rows_since_caps    = 0
            else:
                caps_pendiente_idx = len(merged)
                rows_since_caps    = 0
                merged.append(fila)
        else:
            merged.append(fila)
            if caps_pendiente_idx >= 0:
                rows_since_caps += 1
                if rows_since_caps > 2:
                    caps_pendiente_idx = -1
                    rows_since_caps    = 0

    return _reformatear_filas_tabla(merged)


def _tiene_tabla(pagina, bloques_raw: list) -> bool:
    """
    Detecta si una pagina contiene una tabla.
    Criterio 1: >= 40% de bloques son cortos (< 8 palabras).
    Criterio 2: la pagina contiene keywords tipicas de tablas de averias.
    """
    if not bloques_raw:
        return False
    n_cortos = sum(1 for b in bloques_raw if len(b[4].split()) < 8)
    if (n_cortos / len(bloques_raw)) >= 0.4:
        return True
    texto_lower = pagina.get_text("text").lower()
    return any(kw in texto_lower for kw in _TABLA_KEYWORDS)


def extraer_bloques_pdf(ruta_pdf: str) -> tuple:
    doc           = fitz.open(ruta_pdf)
    total_paginas = doc.page_count
    toc           = doc.get_toc()
    secciones     = _construir_mapa_secciones(toc, total_paginas)
    bloques       = []

    for num_pag, pagina in enumerate(doc):
        pag_num     = num_pag + 1
        bloques_raw = [b for b in pagina.get_text("blocks") if b[6] == 0 and b[4].strip()]

        if _tiene_tabla(pagina, bloques_raw):
            for fila in _filas_por_posicion(pagina):
                bloques.append({"pagina": pag_num, "texto": fila})
        else:
            bloques_pag = []
            for bloque in bloques_raw:
                texto = " ".join(bloque[4].split())
                if len(texto.split()) >= 3:
                    bloques_pag.append({"pagina": pag_num, "texto": texto})

            fusionados = []
            pendiente  = ""
            for b in bloques_pag:
                if pendiente:
                    b = {"pagina": pag_num, "texto": pendiente + " " + b["texto"]}
                    pendiente = ""
                palabras_merged = len(b["texto"].split())
                if palabras_merged < 8:
                    pendiente = b["texto"]
                else:
                    fusionados.append(b)
            if pendiente:
                if fusionados:
                    fusionados[-1]["texto"] += " " + pendiente
                else:
                    fusionados.append({"pagina": pag_num, "texto": pendiente})
            bloques.extend(fusionados)

    doc.close()
    return bloques, secciones


def chunkear_bloques(bloques: list, secciones: list) -> list:
    chunks          = []
    buffer_palabras = []
    buffer_pagina   = 0
    buffer_seccion  = ""

    def _flush(palabras, pagina, seccion):
        if len(palabras) < MIN_CHUNK_WORDS:
            return
        prefijo = f"[Seccion: {seccion}]\n" if seccion else ""
        chunks.append({"texto": prefijo + " ".join(palabras), "pagina": pagina, "seccion": seccion})

    for bloque in bloques:
        palabras_bloque = bloque["texto"].split()
        pagina_bloque   = bloque["pagina"]
        seccion_bloque  = _obtener_seccion_para_pagina(pagina_bloque, secciones)

        if len(buffer_palabras) + len(palabras_bloque) > CHUNK_SIZE and buffer_palabras:
            _flush(buffer_palabras, buffer_pagina, buffer_seccion)
            overlap         = buffer_palabras[-CHUNK_OVERLAP:] if len(buffer_palabras) > CHUNK_OVERLAP else buffer_palabras[:]
            buffer_palabras = overlap
            buffer_pagina   = pagina_bloque
            buffer_seccion  = seccion_bloque

        if not buffer_palabras:
            buffer_pagina  = pagina_bloque
            buffer_seccion = seccion_bloque

        buffer_palabras.extend(palabras_bloque)

        if len(buffer_palabras) >= CHUNK_SIZE:
            _flush(buffer_palabras, buffer_pagina, buffer_seccion)
            overlap         = buffer_palabras[-CHUNK_OVERLAP:] if len(buffer_palabras) > CHUNK_OVERLAP else []
            buffer_palabras = overlap
            buffer_pagina   = pagina_bloque
            buffer_seccion  = seccion_bloque

    if buffer_palabras:
        _flush(buffer_palabras, buffer_pagina, buffer_seccion)

    return chunks


def generar_embedding(texto: str) -> list:
    try:
        return ollama.embeddings(model="nomic-embed-text", prompt=texto[:2000])["embedding"]
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar con Ollama: {e}")


def indexar_manual(nombre_maquina: str, ruta_pdf: str) -> dict:
    cliente  = get_cliente_chroma()
    col_name = normalizar_nombre_coleccion(nombre_maquina)

    _set_progreso(col_name, {
        "estado": "preparando", "chunks_procesados": 0, "chunks_total": 0,
        "porcentaje": 0, "segundos_restantes": None,
        "mensaje": "Extrayendo texto del PDF...",
    })

    try:
        cliente.delete_collection(col_name)
    except Exception:
        pass

    coleccion = cliente.create_collection(name=col_name, metadata={"hnsw:space": "cosine"})

    _set_progreso(col_name, {**get_progreso(nombre_maquina), "mensaje": "Analizando estructura del PDF..."})

    bloques, secciones = extraer_bloques_pdf(ruta_pdf)
    n_secciones        = len(secciones)

    _set_progreso(col_name, {**get_progreso(nombre_maquina),
                             "mensaje": f"Dividiendo en fragmentos ({n_secciones} secciones detectadas)..."})

    chunks = chunkear_bloques(bloques, secciones)
    total  = len(chunks)

    if total == 0:
        _set_progreso(col_name, {
            "estado": "error", "porcentaje": 0,
            "mensaje": "Este PDF no contiene texto seleccionable (posiblemente escaneado). El soporte OCR estara disponible en una proxima version.",
        })
        return {"maquina": nombre_maquina, "chunks": 0}

    _set_progreso(col_name, {
        "estado": "indexando", "chunks_procesados": 0, "chunks_total": total,
        "porcentaje": 0, "segundos_restantes": None,
        "mensaje": f"Generando embeddings (0/{total})...",
    })

    print(f"[RAG] Indexando '{nombre_maquina}': {total} chunks, {n_secciones} secciones...")
    tiempo_inicio = time.time()
    tiempos_chunk = []

    for i, chunk in enumerate(chunks):
        t0     = time.time()
        idioma = detectar_idioma(chunk["texto"])

        texto_indexar = chunk["texto"]
        if idioma == "en":
            try:
                resp = ollama.generate(
                    model="llama3.2:3b",
                    prompt=(
                        "Translate to Spanish. Keep numbers, units and model names. "
                        "Output only the translation:\n\n" + chunk["texto"][:600]
                    ),
                    stream=False,
                    options={"num_predict": 250, "temperature": 0, "num_ctx": 1024},
                )
                traduccion = resp.get("response", "").strip()
                if traduccion:
                    texto_indexar = traduccion
                    idioma = "es"
            except Exception:
                pass

        embedding = generar_embedding(texto_indexar)
        coleccion.add(
            ids        = [f"{col_name}_chunk_{i}"],
            embeddings = [embedding],
            documents  = [texto_indexar],
            metadatas  = [{
                "maquina":  nombre_maquina,
                "pagina":   chunk["pagina"],
                "chunk_id": i,
                "seccion":  chunk.get("seccion", ""),
                "idioma":   idioma,
            }],
        )
        tiempos_chunk.append(time.time() - t0)
        promedio      = sum(tiempos_chunk) / len(tiempos_chunk)
        segundos_rest = round(promedio * (total - i - 1))
        porcentaje    = round(((i + 1) / total) * 100)
        _set_progreso(col_name, {
            "estado": "indexando", "chunks_procesados": i + 1, "chunks_total": total,
            "porcentaje": porcentaje, "segundos_restantes": segundos_rest,
            "mensaje": f"Procesando fragmento {i + 1} de {total}...",
        })

    tiempo_total = round(time.time() - tiempo_inicio)
    _set_progreso(col_name, {
        "estado": "completado", "chunks_procesados": total, "chunks_total": total,
        "porcentaje": 100, "segundos_restantes": 0,
        "mensaje": f"Indexado en {tiempo_total}s ({total} fragmentos, {n_secciones} secciones)",
    })
    print(f"[RAG] '{nombre_maquina}' indexado ({total} chunks, {n_secciones} secciones, {tiempo_total}s)")
    return {"maquina": nombre_maquina, "chunks": total, "secciones": n_secciones}


def esta_indexado(nombre_maquina: str) -> bool:
    try:
        coleccion = get_cliente_chroma().get_collection(
            name=normalizar_nombre_coleccion(nombre_maquina)
        )
        if coleccion.count() == 0:
            return False
        from .retriever import _embedding
        emb = _embedding("test")
        coleccion.query(query_embeddings=[emb], n_results=1)
        return True
    except Exception:
        return False
