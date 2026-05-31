# Backend/api/rag/indexador.py

import re
import fitz  # pymupdf
import ollama
import time
import threading
from pathlib import Path

# OCR deshabilitado hasta implementacion futura
OCR_DISPONIBLE = False

from . import normalizar_nombre_coleccion, get_cliente_chroma, detectar_idioma, LLM_MODEL, LLM_KEEP_ALIVE

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


# ══════════════════════════════════════════════════════════════════════════════
#  EXTRACCION DE TABLAS — reconstruccion por columnas (validada con manuales reales)
#
#  Estrategia (reemplaza el heuristico ALL_CAPS anterior, que generaba falsos
#  positivos del tipo "Sintoma: WS CONTROLLER"):
#   1. Una pagina solo recibe etiquetado SINTOMA/CAUSA/ACCION si REALMENTE tiene
#      esos encabezados (_es_pagina_averias). El resto va como lineas planas.
#   2. Las columnas se detectan por el encabezado o por los 2 mayores gaps en X,
#      lo que maneja correctamente el layout a varias columnas (antes se mezclaban
#      las filas y se partian sintomas como "EL COMPRESOR NO ARRANCA").
#   3. Un sintoma puede ocupar varias lineas (wrapping) y tener varias causas; se
#      agrupa todo en un bloque por sintoma.
# ══════════════════════════════════════════════════════════════════════════════

_SECCION_RE = re.compile(
    r"^(secci[oó]n|gu[ií]a de|b[uú]squeda de averias|sintoma\b|s[ií]ntoma\b|"
    r"\d+\.\d+|p[aá]gina|tabla\b|cuadro\b)", re.I)


def _agrupar_en_lineas(words: list, tol: int = 4) -> list:
    """Agrupa los words de fitz (x0,y0,x1,y1,texto,...) en lineas visuales por Y.
    Devuelve una lista de lineas; cada linea es una lista de (x0, texto) ordenada por X."""
    lineas: dict = {}
    for w in words:
        x0, y0, texto = w[0], w[1], str(w[4])
        if not texto.strip():
            continue
        clave = round(y0 / tol) * tol
        lineas.setdefault(clave, []).append((x0, texto))
    salida = []
    for y in sorted(lineas):
        salida.append((y, sorted(lineas[y], key=lambda c: c[0])))
    return salida


def _es_pagina_averias(pagina) -> bool:
    """True solo si la pagina tiene encabezados de tabla de averias (SINTOMA + CAUSA).
    Esto evita etiquetar como 'Sintoma' a titulos de seccion o pantallas de config."""
    t = pagina.get_text("text").upper()
    tiene_sintoma = any(k in t for k in ("SINTOMA", "SÍNTOMA", "SYMPTOM"))
    tiene_causa   = any(k in t for k in ("CAUSA", "CAUSE", "FAULT"))
    return tiene_sintoma and tiene_causa


def _detectar_columnas(lineas: list) -> list:
    """Coordenadas X de inicio de cada columna. Prioriza el encabezado
    SINTOMA/CAUSA/ACCION; si no esta, usa los 2 mayores gaps horizontales."""
    for _y, celdas in lineas:
        up = " ".join(t for _, t in celdas).upper()
        if "SINTOMA" in up and "CAUSA" in up and ("ACCION" in up or "ACCIÓN" in up):
            cols = []
            for x, t in celdas:
                tu = t.upper().rstrip(":")
                if tu in ("SINTOMA", "SÍNTOMA", "CAUSA", "ACCION", "ACCIÓN"):
                    if not cols or x - cols[-1] > 30:
                        cols.append(x)
            if len(cols) >= 2:
                return cols
    xs = sorted({round(x) for _y, celdas in lineas for x, _ in celdas})
    if len(xs) < 3:
        return xs or [0]
    gaps = sorted(((xs[i + 1] - xs[i], xs[i + 1]) for i in range(len(xs) - 1)), reverse=True)[:2]
    return sorted([xs[0]] + [g[1] for g in gaps])


def _es_caps(s: str) -> bool:
    letras = re.sub(r"[^A-Za-zÁÉÍÓÚÑáéíóúñ]", "", s)
    return len(letras) >= 3 and s.upper() == s


def _reconstruir_tabla_averias(lineas: list, col_starts: list) -> list:
    """Reconstruye una tabla SINTOMA/CAUSA/ACCION emparejando cada causa con su
    accion. Una causa nueva empieza cuando la 2da columna arranca en MAYUSCULA
    (las lineas que la continuan arrancan en minuscula). Devuelve un bloque por
    sintoma con TODAS sus parejas 'causa -> accion'."""
    if len(col_starts) < 2:
        return []
    thresholds = [(col_starts[i] + col_starts[i + 1]) / 2 for i in range(len(col_starts) - 1)]

    def columna_de(x):
        for i, t in enumerate(thresholds):
            if x < t:
                return i
        return len(thresholds)

    # Empezar DESPUES del encabezado SINTOMA/CAUSA/ACCION (saltea la prosa de
    # introduccion a 2 columnas). Si no hay encabezado (continuacion), procesa todo.
    inicio = 0
    for idx, (_y, celdas) in enumerate(lineas):
        up = " ".join(t for _, t in celdas).upper()
        if "SINTOMA" in up and "CAUSA" in up and ("ACCION" in up or "ACCIÓN" in up):
            inicio = idx + 1
            break

    bloques = []
    actual  = None
    par     = None
    prev_col1_vacia = True

    for _y, celdas in lineas[inicio:]:
        cols = [""] * len(col_starts)
        for x, texto in celdas:
            cols[columna_de(x)] = (cols[columna_de(x)] + " " + texto).strip()
        c1 = cols[0]
        c2 = cols[1] if len(cols) > 1 else ""
        c3 = cols[2] if len(cols) > 2 else ""
        linea_completa = " ".join(cols).strip()

        if _SECCION_RE.match(linea_completa) or _SECCION_RE.match(c1):
            continue

        # Sintoma (col 1, mayusculas; puede ocupar varias lineas)
        if _es_caps(c1) and (actual is None or prev_col1_vacia):
            actual = {"sintoma": c1, "pares": []}
            bloques.append(actual)
            par = None
        elif actual is not None and _es_caps(c1):
            actual["sintoma"] += " " + c1
        prev_col1_vacia = not c1.strip()

        # Parejas causa -> accion
        if actual is not None:
            if c2 and c2[:1].isupper():
                par = {"causa": c2, "accion": c3}
                actual["pares"].append(par)
            elif par is not None:
                if c2:
                    par["causa"]  += " " + c2
                if c3:
                    par["accion"] += " " + c3
            elif c2 or c3:
                par = {"causa": c2, "accion": c3}
                actual["pares"].append(par)

    salida = []
    for b in bloques:
        s = re.sub(r"\s+", " ", b["sintoma"]).strip()
        if not s:
            continue
        items = []
        for p in b["pares"]:
            c = re.sub(r"\s+", " ", p["causa"]).strip()
            a = re.sub(r"\s+", " ", p["accion"]).strip().lstrip("-").strip()
            if c and a:
                items.append(f"{c} → {a}")
            elif c:
                items.append(c)
            elif a:
                items.append(a)
        if items:
            cuerpo = " ".join(f"{i + 1}) {t}." for i, t in enumerate(items))
            salida.append(f"Sintoma: {s}. Causas posibles y acciones: {cuerpo}")
        else:
            salida.append(f"Sintoma: {s}.")
    return salida


def _lineas_planas(lineas: list) -> list:
    """Para paginas tipo tabla que NO son de averias: cada linea como texto, sin
    etiquetar sintomas. Evita falsos positivos tipo 'Sintoma: WS CONTROLLER'."""
    salida = []
    for _y, celdas in lineas:
        texto = re.sub(r"\s+", " ", " ".join(t for _, t in celdas)).strip()
        if len(texto.split()) >= 2:
            salida.append(texto)
    return salida


def _filas_por_posicion(pagina) -> list:
    """Extrae filas de una pagina con tabla.
    - Tabla de averias (tiene SINTOMA + CAUSA) -> reconstruccion por columnas.
    - Cualquier otra -> lineas planas sin etiquetar."""
    try:
        words = pagina.get_text("words")
    except Exception:
        return []
    if not words:
        return []
    lineas = _agrupar_en_lineas(words)
    if not lineas:
        return []

    if _es_pagina_averias(pagina):
        col_starts = _detectar_columnas(lineas)
        filas = _reconstruir_tabla_averias(lineas, col_starts)
        if filas:
            return filas
    return _lineas_planas(lineas)


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
        # Cada síntoma de tabla de averías va en su PROPIO chunk: así el embedding
        # queda enfocado en ese síntoma y el retrieval lo encuentra. Antes el síntoma
        # se mezclaba con texto vecino en un chunk de ~200 palabras y se "diluía"
        # (por eso "el compresor no arranca" a veces no se encontraba).
        if bloque["texto"].startswith("Sintoma:"):
            if buffer_palabras:
                _flush(buffer_palabras, buffer_pagina, buffer_seccion)
                buffer_palabras = []
            sec = _obtener_seccion_para_pagina(bloque["pagina"], secciones)
            prefijo = f"[Seccion: {sec}]\n" if sec else ""
            chunks.append({"texto": prefijo + bloque["texto"], "pagina": bloque["pagina"], "seccion": sec})
            continue

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

    # Invalidar el caché semántico viejo: si el manual se reindexó, las respuestas
    # cacheadas pueden estar obsoletas (antes el caché sobrevivía al reindex y
    # seguía sirviendo respuestas viejas).
    try:
        cliente.delete_collection("cache__" + col_name)
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
                    model=LLM_MODEL,
                    prompt=(
                        "/no_think\nTranslate to Spanish. Keep numbers, units and model names. "
                        "Output only the translation:\n\n" + chunk["texto"][:600]
                    ),
                    stream=False,
                    keep_alive=LLM_KEEP_ALIVE,
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
        # count() es suficiente para saber si hay chunks. Antes se hacia ademas
        # un embedding de prueba con Ollama en CADA request (lento e innecesario).
        return coleccion.count() > 0
    except Exception:
        return False
