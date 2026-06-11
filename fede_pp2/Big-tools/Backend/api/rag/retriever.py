# Backend/api/rag/retriever.py

import re
import ollama
import json
from pathlib import Path

from . import normalizar_nombre_coleccion, get_cliente_chroma, detectar_idioma, LLM_MODEL, LLM_KEEP_ALIVE, LLM_TEMPERATURE
from .cache import buscar_en_cache, guardar_en_cache

N_RESULTADOS       = 6
N_RESULTADOS_FINAL = 4   # fragmentos que se le pasan al LLM (menos = más rápido / menos contexto)

# Filtro de relevancia por distancia coseno (0 = idéntico, mayor = menos parecido).
MARGEN_RELEVANCIA  = 0.30   # se descartan fragmentos peores que (mejor + margen): saca ruido lejano
DIST_SIN_CONTEXTO  = 1.00   # si ni el mejor fragmento baja de esto, no hay contexto útil → no inventar

# Prefijo opcional para desactivar el "razonamiento" de modelos que lo tienen
# (ej. qwen3 → "/no_think\n"). Con modelos sin razonamiento (gemma3) va vacío.
_NO_THINK = ""


# ── Traducción de chunks en inglés ────────────────────────────────────────────

def _traducir_chunks_al_espanol(chunks: list) -> list:
    en_idx = [i for i, c in enumerate(chunks)
              if (c.get("_idioma_resuelto") or detectar_idioma(c.get("texto", ""))) == "en"]
    if not en_idx:
        return chunks
    fragmentos = "\n\n".join(
        f"[{n+1}] {chunks[i]['texto'][:500]}"
        for n, i in enumerate(en_idx)
    )
    prompt = (
        "Translate each numbered excerpt to Spanish. "
        "Keep numbers, units, model names and part codes unchanged. "
        "Reply ONLY with the translations in the same numbered format:\n\n"
        + fragmentos
    )
    try:
        resp = ollama.generate(
            model="llama3.2:3b",
            prompt=prompt,
            stream=False,
            options={
                "num_predict": 150 * len(en_idx),
                "temperature": 0,
                "num_ctx":     min(4096, 800 * len(en_idx)),
            },
        )
        texto_resp = resp.get("response", "").strip()
        resultado  = list(chunks)
        partes     = re.split(r"\[\d+\]", texto_resp)
        partes     = [p.strip() for p in partes if p.strip()]
        for n, traduccion in enumerate(partes):
            if n < len(en_idx):
                resultado[en_idx[n]] = {**chunks[en_idx[n]], "texto": traduccion}
        return resultado
    except Exception:
        return chunks


# ── Query expansion (desactivada) ─────────────────────────────────────────────

def _expandir_query(pregunta: str) -> list[str]:
    return [pregunta]


# ── Embedding ─────────────────────────────────────────────────────────────────

def _embedding(texto: str) -> list:
    try:
        return ollama.embeddings(model="nomic-embed-text", prompt=texto)["embedding"]
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar con Ollama: {e}")


# ── Helpers de idioma ─────────────────────────────────────────────────────────

def _resolver_idioma(chunk: dict) -> str:
    idioma = chunk.get("idioma", "")
    if idioma in ("es", "en", "und"):
        return idioma
    return detectar_idioma(chunk.get("texto", ""))


def _preferir_espanol(chunks: list[dict]) -> list[dict]:
    for c in chunks:
        c["_idioma_resuelto"] = _resolver_idioma(c)

    es_chunks  = [c for c in chunks if c["_idioma_resuelto"] == "es"]
    en_chunks  = [c for c in chunks if c["_idioma_resuelto"] == "en"]
    und_chunks = [c for c in chunks if c["_idioma_resuelto"] == "und"]

    if len(es_chunks) >= 3:
        preferidos = es_chunks + und_chunks
        if len(preferidos) < N_RESULTADOS_FINAL:
            preferidos += en_chunks[:N_RESULTADOS_FINAL - len(preferidos)]
        return preferidos[:N_RESULTADOS_FINAL]

    return chunks


# ── Búsqueda híbrida ──────────────────────────────────────────────────────────

def buscar_chunks(nombre_maquina: str, pregunta: str) -> list[dict]:
    """
    Búsqueda híbrida: semántica primero, keyword fallback si los scores son débiles.
    El keyword fallback usa la frase completa (no palabras sueltas) para evitar
    falsos positivos. Ej: "el compresor no arranca" → busca "EL COMPRESOR NO ARRANCA"
    en el texto indexado, encontrando filas de tablas de síntomas/averías.
    """
    cliente = get_cliente_chroma()

    try:
        coleccion = cliente.get_collection(name=normalizar_nombre_coleccion(nombre_maquina))
    except Exception:
        return []

    queries = _expandir_query(pregunta)
    n       = min(N_RESULTADOS, coleccion.count())
    vistos  = {}

    # ── 1. Búsqueda semántica ──────────────────────────────────────────────────
    for query in queries:
        emb = _embedding(query)
        try:
            resultados = coleccion.query(query_embeddings=[emb], n_results=n)
        except Exception:
            return []
        for i, doc in enumerate(resultados["documents"][0]):
            score  = resultados["distances"][0][i]
            meta   = resultados["metadatas"][0][i]
            if doc not in vistos or score < vistos[doc]["score"]:
                vistos[doc] = {
                    "texto":   doc,
                    "pagina":  meta["pagina"],
                    "seccion": meta.get("seccion", ""),
                    "idioma":  meta.get("idioma", ""),
                    "score":   score,
                }

    # ── 2. Keyword fallback — frase exacta, SIEMPRE ───────────────────────────
    # Antes solo corría si la semántica era débil; tras un reindex los scores
    # fluctúan y un chunk con la frase exacta (ej. "EL COMPRESOR NO ARRANCA")
    # se podía perder. Ahora siempre se busca la frase exacta y, si aparece,
    # se incluye con buen score → se garantiza su recuperación.
    for variante in [pregunta, pregunta.upper(), pregunta.lower()]:
        try:
            kw = coleccion.get(
                where_document={"$contains": variante},
                include=["documents", "metadatas"],
                limit=4,
            )
            for doc, meta in zip(kw.get("documents", []), kw.get("metadatas", [])):
                if doc not in vistos:
                    vistos[doc] = {
                        "texto":   doc,
                        "pagina":  meta["pagina"],
                        "seccion": meta.get("seccion", ""),
                        "idioma":  meta.get("idioma", ""),
                        "score":   0.28,
                    }
        except Exception:
            pass

    chunks_ordenados = sorted(vistos.values(), key=lambda c: c["score"])
    if not chunks_ordenados:
        return []
    # Filtro de relevancia: si ni el mejor fragmento es razonablemente cercano,
    # no hay contexto útil → devolvemos vacío para no responder con ruido.
    mejor = chunks_ordenados[0]["score"]
    if mejor > DIST_SIN_CONTEXTO:
        return []
    # Descartamos los fragmentos claramente más lejanos que el mejor (menos ruido = más precisión).
    relevantes = [c for c in chunks_ordenados if c["score"] <= mejor + MARGEN_RELEVANCIA]
    return _preferir_espanol(relevantes[:N_RESULTADOS_FINAL * 2])[:N_RESULTADOS_FINAL]


def calcular_confianza(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    mejores  = sorted(chunks, key=lambda c: c["score"])[:3]
    promedio = sum(c["score"] for c in mejores) / len(mejores)
    # Las colecciones de manuales usan distancia coseno (hnsw:space=cosine),
    # cuyo rango es 0-2 (no L2). similitud = 1 - distancia → confianza en %.
    # (Antes se usaba MAX_DIST=400, calibrado para L2, lo que daba ~100% siempre.)
    confianza = max(0, round((1 - promedio) * 100))
    if len(chunks) < 3:
        confianza = round(confianza * 0.8)
    return min(confianza, 100)


# ── Construcción de prompts ───────────────────────────────────────────────────

def _construir_prompt(
    nombre_maquina: str,
    pregunta: str,
    chunks: list,
    modo_analisis: bool = False,
    historial: list = None,
    contexto_diag: str = "",
) -> str:
    def _fmt(c: dict) -> str:
        header = f"[Pág. {c['pagina']}]"
        if c.get("seccion"):
            header += f" {c['seccion']} —"
        return f"{header} {c['texto']}"

    contexto    = "\n\n".join(_fmt(c) for c in chunks)
    archivo_pdf = nombre_maquina.replace(" ", "_") + ".pdf"

    hist_bloque = ""
    if historial:
        lineas = []
        for msg in historial:
            rol = "Técnico" if msg["role"] == "user" else "Asistente"
            lineas.append(f"{rol}: {msg['content']}")
        if lineas:
            hist_bloque = "CONVERSACIÓN PREVIA:\n" + "\n".join(lineas) + "\n\n"

    ctx_diag_bloque = ""
    if contexto_diag:
        ctx_diag_bloque = (
            "CONTEXTO DEL DIAGNÓSTICO PREVIO (el técnico ya pasó por el sistema experto; "
            "respondé sus repreguntas teniendo esto en cuenta):\n" + contexto_diag + "\n\n"
        )

    if modo_analisis:
        return (
            f"Sos el asistente técnico del Sistema Big Tools.\n"
            f"Analizá la falla usando ÚNICAMENTE los fragmentos del manual proporcionados.\n"
            f"Tu respuesta debe estar 100% en español rioplatense. NUNCA respondas en portugués ni en inglés. Si el manual está en inglés, TRADUCÍ cada parte al español.\n"
            f"El que consulta ES el técnico en campo. NUNCA lo remitás a 'un técnico', 'servicio técnico', 'personal calificado/autorizado', 'soporte' ni similares: la solución la ejecuta él con el manual.\n"
            f"NUNCA inventes datos que no estén en los fragmentos.\n"
            f"Si la info no está en el manual: escribí exactamente 'Esta información no se encuentra en el manual indexado. Consultá al administrador para actualizar la base de datos.'\n\n"
            f"FORMATO OBLIGATORIO:\n"
            f"GRAVEDAD: [🔴 CRÍTICO / 🟡 MODERADO / 🟢 MENOR] — [motivo]\n\n"
            f"CAUSA PROBABLE:\n[causa raíz según el manual]\n\n"
            f"RIESGO OPERACIONAL:\n[riesgo de continuar operando sin intervenir]\n\n"
            f"PROCEDIMIENTO:\n1. [paso ejecutable]\n2. [paso ejecutable]\n...\n\n"
            f"REFERENCIA: {archivo_pdf}, Pág. [N]\n\n"
            f"---\n"
            f"{hist_bloque}"
            f"FRAGMENTOS DEL MANUAL ({nombre_maquina}):\n{contexto}\n\n"
            f"FALLA: {pregunta}\n\n"
            f"ANÁLISIS:"
        )

    # ── Rama CONVERSACIONAL: repreguntas tras el diagnóstico (formato libre) ──────
    if contexto_diag:
        return (
            f"Sos el asistente técnico del Sistema Big Tools, conversando con un técnico en campo.\n"
            f"El técnico YA pasó por el diagnóstico guiado y la ampliación; ahora te hace repreguntas sobre ese mismo equipo.\n\n"
            f"DÓNDE ESTAMOS PARADOS (contexto del diagnóstico previo):\n{contexto_diag}\n\n"
            f"REGLAS:\n"
            f"- Respondé la consulta de forma DIRECTA, clara y conversacional, 100% en español rioplatense (NUNCA en portugués ni inglés). SIN formato rígido (nada de 'Causa:/Procedimiento:').\n"
            f"- Apoyate en el contexto de arriba y en los fragmentos del manual. Si el manual está en inglés, traducí.\n"
            f"- El que consulta ES el técnico en campo — nunca lo remitás a 'un técnico' ni al 'servicio técnico'.\n"
            f"- NUNCA inventes datos que no estén en el contexto ni en los fragmentos.\n"
            f"- Si la respuesta no figura en el manual, decilo claramente: 'Eso no figura en el manual indexado.'\n\n"
            f"{hist_bloque}"
            f"FRAGMENTOS DEL MANUAL ({nombre_maquina}):\n{contexto}\n\n"
            f"CONSULTA DEL TÉCNICO: {pregunta}\n\n"
            f"RESPUESTA:"
        )

    return (
        f"Sos el asistente técnico del Sistema Big Tools.\n"
        f"Analizá la consulta y respondé usando ÚNICAMENTE los fragmentos del manual proporcionados.\n\n"
        f"REGLAS:\n"
        f"- Tu respuesta debe estar 100% en español rioplatense. Cero palabras en inglés y NUNCA en portugués.\n"
        f"- Si el manual está en inglés, TRADUCÍ cada paso antes de escribirlo.\n"
        f"  Ejemplo: 'Press and hold the START button' → 'Mantené presionado el botón de arranque'\n"
        f"- Sin saludos. Directo al diagnóstico.\n"
        f"- No hagas preguntas de seguimiento. Con la info disponible, diagnosticá.\n"
        f"- El que consulta ES el técnico en campo — nunca lo remitás a 'un técnico' ni al 'servicio técnico'.\n"
        f"- NUNCA inventes pasos, valores ni procedimientos que no estén en los fragmentos.\n"
        f"- Si el manual lista VARIAS causas posibles para el síntoma (tabla de averías), incluilas TODAS, cada una con su acción correctiva. NO te quedes con la primera.\n"
        f"- Si la solución está en el manual → respondé con el formato de abajo.\n"
        f"- Si no está → escribí exactamente: 'Esta información no se encuentra en el manual indexado. Consultá al administrador para actualizar la base de datos.'\n\n"
        f"FORMATO:\n"
        f"- Si el manual da UNA sola causa:\n"
        f"  Causa: [causa según el manual]\n"
        f"  Procedimiento:\n"
        f"  1. [paso concreto y ejecutable]\n"
        f"  2. [paso concreto y ejecutable]\n"
        f"- Si el manual lista VARIAS causas posibles para el síntoma (tabla de averías), enumeralas TODAS:\n"
        f"  Posibles causas y acciones:\n"
        f"  1. [causa] → [acción correctiva]\n"
        f"  2. [causa] → [acción correctiva]\n"
        f"  ...\n"
        f"Referencia: {archivo_pdf}, Pág. [N]\n\n"
        f"{ctx_diag_bloque}"
        f"{hist_bloque}"
        f"FRAGMENTOS DEL MANUAL ({nombre_maquina}):\n{contexto}\n\n"
        f"CONSULTA: {pregunta}\n\n"
        f"DIAGNÓSTICO:"
    )


# ── Respuesta completa (sin streaming) ───────────────────────────────────────

def generar_respuesta(nombre_maquina: str, pregunta: str, modo_analisis: bool = False) -> dict:
    chunks = buscar_chunks(nombre_maquina, pregunta)
    if not chunks:
        return {
            "respuesta": "No encontré información indexada para esta máquina. "
                         "Asegurate de que el manual esté indexado.",
            "paginas": [],
        }
    paginas = sorted({c["pagina"] for c in chunks})
    prompt  = _construir_prompt(nombre_maquina, pregunta, chunks, modo_analisis)
    try:
        respuesta = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": _NO_THINK + prompt}],
            keep_alive=LLM_KEEP_ALIVE,
            options={"temperature": LLM_TEMPERATURE},
        )
        return {"respuesta": respuesta["message"]["content"], "paginas": paginas}
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar con Ollama: {e}")


# ── Referencia de página (solo la del/los fragmento(s) más relevante(s)) ──────

def _ref_paginas(chunks: list) -> str:
    """Texto de referencia con la(s) página(s) del fragmento MÁS relevante, no de
    todos los recuperados (evita listar páginas de ruido como '7, 11, 17, 45, 59')."""
    if not chunks:
        return ""
    mejor = min(c.get("score", 1.0) for c in chunks)
    pags  = sorted({c["pagina"] for c in chunks if c.get("score", 1.0) <= mejor + 0.08})
    if not pags:
        return ""
    etq = "Pág. " if len(pags) == 1 else "Págs. "
    return "\n\n📄 En el manual, revisá la " + etq + ", ".join(str(p) for p in pags) + "."


# ── Respuesta con streaming (SSE) ─────────────────────────────────────────────

def generar_respuesta_stream(nombre_maquina: str, pregunta: str, modo_analisis: bool = False):
    chunks    = buscar_chunks(nombre_maquina, pregunta)
    paginas   = sorted({c["pagina"] for c in chunks})
    confianza = calcular_confianza(chunks)
    secciones = list(dict.fromkeys(c["seccion"] for c in chunks if c.get("seccion")))

    yield f"data: {json.dumps({'tipo': 'meta', 'paginas': paginas, 'confianza': confianza, 'secciones': secciones})}\n\n"

    if not chunks:
        yield f"data: {json.dumps({'tipo': 'token', 'texto': 'No encontré información relevante en el manual para esta consulta.'})}\n\n"
        yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
        return

    prompt = _construir_prompt(nombre_maquina, pregunta, chunks, modo_analisis)
    yield f"data: {json.dumps({'tipo': 'inicio_stream'})}\n\n"

    try:
        for chunk in ollama.generate(
            model=LLM_MODEL,
            prompt=_NO_THINK + prompt,
            stream=True,
            keep_alive=LLM_KEEP_ALIVE,
            options={"num_predict": 800, "temperature": LLM_TEMPERATURE, "num_ctx": 4096}
        ):
            token = chunk.get("response", "")
            if token:
                yield f"data: {json.dumps({'tipo': 'token', 'texto': token})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'tipo': 'error', 'mensaje': str(e)})}\n\n"

    _ref = _ref_paginas(chunks)
    if _ref:
        yield f"data: {json.dumps({'tipo': 'token', 'texto': _ref})}\n\n"

    yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"


# ── Resumen rodante de la conversación (para no perder la ventana de contexto) ─

def resumir_conversacion(contexto_diag: str, resumen_previo: str, mensajes: list) -> str:
    """Comprime los turnos viejos en un resumen breve. Se llama de forma lazy
    (solo cuando la charla se hizo larga). Si falla, devuelve el resumen previo."""
    if not mensajes:
        return resumen_previo
    convo = "\n".join(
        f"{'Técnico' if m.get('role') == 'user' else 'Asistente'}: {m.get('content', '')}"
        for m in mensajes
    )
    prompt = (
        "Resumí de forma breve y concreta esta conversación técnica (qué consultó el "
        "técnico y qué se le respondió), para conservar el contexto sin todo el detalle. "
        "Máximo 4-5 líneas.\n\n"
        + (f"Resumen previo: {resumen_previo}\n\n" if resumen_previo else "")
        + "Conversación:\n" + convo + "\n\nResumen breve:"
    )
    try:
        resp = ollama.generate(
            model=LLM_MODEL, prompt=_NO_THINK + prompt, stream=False, keep_alive=LLM_KEEP_ALIVE,
            options={"temperature": 0, "num_ctx": 4096, "num_predict": 300},
        )
        return resp.get("response", "").strip() or resumen_previo
    except Exception:
        return resumen_previo


# ── Stream conversacional (con memoria de sesión) ─────────────────────────────

def generar_respuesta_stream_conversacional(
    nombre_maquina: str,
    pregunta: str,
    historial: list,
    contexto_diag: str = "",
    resumen: str = "",
):
    # ── 1. Cache semántico ────────────────────────────────────────────────────
    # Sin caché cuando hay contexto de diagnóstico: la respuesta es específica de ese caso.
    es_primera_consulta = (not contexto_diag) and not any(m["role"] == "user" for m in historial)
    if es_primera_consulta:
        hit = buscar_en_cache(nombre_maquina, pregunta)
        if hit:
            yield f"data: {json.dumps({'tipo': 'meta', 'paginas': hit['paginas'], 'confianza': hit['confianza'], 'secciones': hit['secciones'], 'desde_cache': True})}\n\n"
            yield f"data: {json.dumps({'tipo': 'inicio_stream'})}\n\n"
            for palabra in hit["respuesta"].split(" "):
                yield f"data: {json.dumps({'tipo': 'token', 'texto': palabra + ' '})}\n\n"
            yield f"data: {json.dumps({'tipo': 'respuesta_completa', 'texto': hit['respuesta']})}\n\n"
            yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
            return

    # ── 2. RAG normal ─────────────────────────────────────────────────────────
    chunks    = buscar_chunks(nombre_maquina, pregunta)
    paginas   = sorted({c["pagina"] for c in chunks})
    confianza = calcular_confianza(chunks)
    secciones = list(dict.fromkeys(c["seccion"] for c in chunks if c.get("seccion")))

    yield f"data: {json.dumps({'tipo': 'meta', 'paginas': paginas, 'confianza': confianza, 'secciones': secciones})}\n\n"

    if not chunks:
        yield f"data: {json.dumps({'tipo': 'token', 'texto': 'No encontré información relevante en el manual para esta consulta.'})}\n\n"
        yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
        return

    # Ancla del diagnóstico + resumen rodante de los turnos viejos.
    ctx = contexto_diag
    if resumen:
        ctx = (ctx + "\n\n" if ctx else "") + "Resumen de lo ya conversado: " + resumen
    prompt = _construir_prompt(nombre_maquina, pregunta, chunks, False, historial, ctx)

    yield f"data: {json.dumps({'tipo': 'inicio_stream'})}\n\n"

    respuesta_completa = []
    try:
        for chunk in ollama.generate(
            model=LLM_MODEL,
            prompt=_NO_THINK + prompt,
            stream=True,
            keep_alive=LLM_KEEP_ALIVE,
            options={"num_predict": 800, "temperature": LLM_TEMPERATURE, "num_ctx": 4096}
        ):
            token = chunk.get("response", "")
            if token:
                respuesta_completa.append(token)
                yield f"data: {json.dumps({'tipo': 'token', 'texto': token})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'tipo': 'error', 'mensaje': str(e)})}\n\n"
        yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
        return

    texto_final = "".join(respuesta_completa)
    _ref = _ref_paginas(chunks)
    if _ref:
        yield f"data: {json.dumps({'tipo': 'token', 'texto': _ref})}\n\n"
        texto_final += _ref
    yield f"data: {json.dumps({'tipo': 'respuesta_completa', 'texto': texto_final})}\n\n"
    yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"

    # ── 3. Guardar en cache ───────────────────────────────────────────────────
    if es_primera_consulta and confianza >= 50 and texto_final:
        try:
            guardar_en_cache(nombre_maquina, pregunta, texto_final, paginas, confianza, secciones)
        except Exception:
            pass
