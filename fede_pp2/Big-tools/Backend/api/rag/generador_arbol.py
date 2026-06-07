"""
Generador de árbol de conocimiento (BORRADOR) desde la tabla de averías de un PDF.

Determinístico: solo procesa páginas que tienen un encabezado real
SÍNTOMA / CAUSA / ACCIÓN (tabla de averías). De cada fila arma un nodo del árbol
en el formato que consume el motor (categorias → ramas → atributo/falla/soluciones).

La salida es un BORRADOR pensado para que un humano lo revise, edite y apruebe
antes de que pase a ser parte del sistema experto.
Funciona bien con manuales tipo "tabla de averías" (ej. Compresor). Manuales con
otro formato (luces/parpadeos, códigos de falla) darán pocas/ninguna categoría:
esos necesitan el camino con LLM (a futuro) o carga manual.
"""

import re
import time
import threading
from pathlib import Path

import fitz  # pymupdf

_SECCION_RE = re.compile(
    r"^(secci[oó]n|gu[ií]a de|b[uú]squeda de averias|sintoma\b|s[ií]ntoma\b|"
    r"\d+\.\d+|p[aá]gina|tabla\b|cuadro\b)", re.I)

BORRADORES_DIR = Path(__file__).parent.parent.parent / "data" / "arboles_borrador"


def _es_caps(s: str) -> bool:
    return len(re.sub(r"[^A-Za-zÁÉÍÓÚÑáéíóúñ]", "", s)) >= 3 and s.upper() == s


def _lineas(pagina, tol: int = 4) -> list:
    L: dict = {}
    for w in pagina.get_text("words"):
        x0, y0, txt = w[0], w[1], str(w[4])
        if txt.strip():
            L.setdefault(round(y0 / tol) * tol, []).append((x0, txt))
    return [(y, sorted(L[y], key=lambda c: c[0])) for y in sorted(L)]


def _header_cols(lineas: list):
    """Solo devuelve columnas si hay una línea con SÍNTOMA + CAUSA + ACCIÓN
    (encabezado de tabla de averías real). Si no, None."""
    for _y, celdas in lineas:
        up = " ".join(t for _, t in celdas).upper()
        if (("SINTOMA" in up or "SÍNTOMA" in up) and "CAUSA" in up
                and ("ACCION" in up or "ACCIÓN" in up)):
            cs = [x for x, t in celdas
                  if t.upper().rstrip(":") in ("SINTOMA", "SÍNTOMA", "CAUSA", "ACCION", "ACCIÓN")]
            if len(cs) >= 2:
                return cs
    return None


def _bloques(pagina, col_starts: list) -> list:
    """Reconstruye filas (síntoma + pares causa/acción) de una página de tabla."""
    lineas = _lineas(pagina)
    thresholds = [(col_starts[i] + col_starts[i + 1]) / 2 for i in range(len(col_starts) - 1)]

    def col_de(x):
        for i, t in enumerate(thresholds):
            if x < t:
                return i
        return len(thresholds)

    inicio = 0
    for i, (_y, celdas) in enumerate(lineas):
        up = " ".join(t for _, t in celdas).upper()
        if (("SINTOMA" in up or "SÍNTOMA" in up) and "CAUSA" in up
                and ("ACCION" in up or "ACCIÓN" in up)):
            inicio = i + 1
            break

    bloques, actual, par, prev_vacia = [], None, None, True
    for _y, celdas in lineas[inicio:]:
        cols = [""] * len(col_starts)
        for x, t in celdas:
            cols[col_de(x)] = (cols[col_de(x)] + " " + t).strip()
        c1 = cols[0]
        c2 = cols[1] if len(cols) > 1 else ""
        c3 = cols[2] if len(cols) > 2 else ""
        if _SECCION_RE.match(" ".join(cols).strip()) or _SECCION_RE.match(c1):
            continue
        if _es_caps(c1) and (actual is None or prev_vacia):
            actual = {"sintoma": c1, "pares": []}
            bloques.append(actual)
            par = None
        elif actual is not None and _es_caps(c1):
            actual["sintoma"] += " " + c1
        prev_vacia = not c1.strip()
        if actual is not None:
            if c2 and c2[:1].isupper():
                par = {"causa": c2, "accion": c3}
                actual["pares"].append(par)
            elif par is not None:
                if c2:
                    par["causa"] += " " + c2
                if c3:
                    par["accion"] += " " + c3
            elif c2 or c3:
                par = {"causa": c2, "accion": c3}
                actual["pares"].append(par)
    return bloques


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def extraer_averias(ruta_pdf: str) -> list:
    """Devuelve [{'sintoma': str, 'pares': [{'causa','accion'}]}] de la tabla de averías.
    Fusiona los síntomas '(CONTINUACION)' con el anterior."""
    doc = fitz.open(ruta_pdf)
    crudos = []
    for pagina in doc:
        cs = _header_cols(_lineas(pagina))
        if not cs:
            continue
        for b in _bloques(pagina, cs):
            s = _norm(b["sintoma"])
            pares = [{"causa": _norm(p["causa"]),
                      "accion": _norm(p["accion"]).lstrip("-").strip()}
                     for p in b["pares"] if _norm(p["causa"])]
            if s and pares:
                crudos.append({"sintoma": s, "pares": pares})
    doc.close()

    # Fusionar "(CONTINUACION)" con el síntoma previo
    fusionados = []
    for b in crudos:
        base = re.sub(r"\s*\(continuaci[oó]n\)\s*", "", b["sintoma"], flags=re.I).strip()
        if fusionados and ("continuaci" in b["sintoma"].lower()
                           or re.sub(r"\s*\(continuaci[oó]n\)\s*", "", fusionados[-1]["sintoma"], flags=re.I).strip() == base):
            fusionados[-1]["pares"].extend(b["pares"])
        else:
            fusionados.append({"sintoma": base, "pares": list(b["pares"])})
    return fusionados


def _construir_categorias(bloques: list, referencia: str) -> list:
    """De [{'sintoma', 'pares':[{'causa','accion'}]}] arma las categorías del motor.
    1 causa → hoja directa; varias → pregunta con ramas."""
    categorias = []
    for b in bloques:
        sintoma = (b.get("sintoma") or "").strip()
        pares = [p for p in b.get("pares", []) if (p.get("causa") or "").strip()]
        if not sintoma or not pares:
            continue
        if len(pares) == 1:
            p = pares[0]
            categorias.append({
                "categoria": sintoma,
                "falla": p["causa"],
                "soluciones": [p["accion"]] if p.get("accion") else [],
                "referencia": referencia,
            })
        else:
            categorias.append({
                "categoria": sintoma,
                "pregunta": "¿Cuál de estas causas corresponde? (verificá en el equipo)",
                "ramas": [{
                    "atributo": p["causa"],
                    "falla": p["causa"],
                    "soluciones": [p["accion"]] if p.get("accion") else [],
                    "referencia": referencia,
                } for p in pares],
            })
    return categorias


def generar_arbol_borrador(ruta_pdf: str, referencia: str) -> dict:
    """Camino A (determinístico): árbol desde la tabla SÍNTOMA/CAUSA/ACCIÓN."""
    return {"categorias": _construir_categorias(extraer_averias(ruta_pdf), referencia)}


# ══════════════════════════════════════════════════════════════════════════════
#  CAMINO B — generación con LLM (para manuales SIN tabla SÍNTOMA/CAUSA/ACCIÓN)
#  Lee las páginas de diagnóstico del PDF y le pide el árbol al modelo local.
#  El 3B no es 100% confiable → el resultado es un BORRADOR que un humano valida.
# ══════════════════════════════════════════════════════════════════════════════

# Términos FUERTES de diagnóstico (pesan más) vs términos débiles/ambiguos.
_KW_FUERTE = (
    "averia", "avería", "falla", "fallo", "diagnos", "codigo de falla",
    "código de falla", "sintoma", "síntoma", "correctiv", "parpade",
    "luz testigo", "troubleshoot", "remedy", "busqueda de averias",
    "guia de averias", "causa probable",
)
_KW_DEBIL = ("problema", "solucion", "solución", "indicador", "codigo", "código")


def _texto_diagnostico_pdf(ruta_pdf: str, max_chars: int = 6500) -> str:
    """Extrae el texto de las páginas más relacionadas con diagnóstico/averías.
    Prioriza páginas con términos fuertes (averías, códigos de falla, parpadeos)
    y exige al menos uno, para no traer páginas de seguridad/introducción."""
    doc = fitz.open(ruta_pdf)
    paginas = []
    for n, pg in enumerate(doc):
        t = pg.get_text("text")
        low = t.lower()
        fuerte = sum(low.count(k) for k in _KW_FUERTE)
        debil = sum(low.count(k) for k in _KW_DEBIL)
        if fuerte >= 1 and (2 * fuerte + debil) >= 4:
            paginas.append((2 * fuerte + debil, n + 1, t))
    doc.close()
    paginas.sort(reverse=True)  # primero las más "de averías"
    out, total = [], 0
    for _score, pag, t in paginas:
        out.append(f"[Pág. {pag}]\n{t}")
        total += len(t)
        if total >= max_chars:
            break
    return "\n\n".join(out)[:max_chars]


def _parsear_json_arbol(raw: str, referencia: str) -> dict:
    """Extrae y normaliza el JSON del árbol devuelto por el LLM (tolerante a ruido)."""
    import json
    i, j = raw.find("{"), raw.rfind("}")
    if i < 0 or j < 0:
        return {"categorias": []}
    try:
        d = json.loads(raw[i:j + 1])
    except Exception:
        return {"categorias": []}
    cats = d.get("categorias", []) if isinstance(d, dict) else []

    def _fix(node):
        if not isinstance(node, dict):
            return
        ramas = node.get("ramas")
        if isinstance(ramas, list) and ramas:
            for r in ramas:
                _fix(r)
        else:
            node.pop("ramas", None)
            node.setdefault("soluciones", [])
            if not isinstance(node["soluciones"], list):
                node["soluciones"] = [str(node["soluciones"])]
            node.setdefault("referencia", referencia)
            node.setdefault("falla", node.get("categoria") or node.get("atributo") or "")

    limpio = []
    for c in cats:
        if isinstance(c, dict) and c.get("categoria"):
            _fix(c)
            limpio.append(c)
    return {"categorias": limpio}


def _triples_a_bloques(salida: str) -> list:
    """Parsea líneas 'SÍNTOMA | CAUSA | ACCIÓN' en bloques agrupados por síntoma."""
    bloques, ultimo = [], None
    for ln in salida.splitlines():
        if "|" not in ln:
            continue
        partes = [p.strip(" -•*\t") for p in ln.split("|")]
        sintoma = partes[0].strip()
        causa = partes[1].strip() if len(partes) > 1 else ""
        accion = partes[2].strip() if len(partes) > 2 else ""
        # "NADA"/"N/A"/"ninguna" significan vacío, no son contenido real
        _vacios = ("nada", "n/a", "ninguna", "ninguno", "-", "")
        if accion.lower() in _vacios:
            accion = ""
        if causa.lower() in _vacios:
            causa = ""
        if not sintoma or not causa or sintoma.lower() in ("síntoma", "sintoma", "problema", "falla"):
            continue
        if ultimo and ultimo["sintoma"].lower() == sintoma.lower():
            ultimo["pares"].append({"causa": causa, "accion": accion})
        else:
            ultimo = {"sintoma": sintoma, "pares": [{"causa": causa, "accion": accion}]}
            bloques.append(ultimo)
    return bloques


def generar_arbol_llm(ruta_pdf: str, referencia: str) -> dict:
    """Camino B (local): el modelo EXTRAE los problemas como líneas simples
    'SÍNTOMA | CAUSA | ACCIÓN' (tarea fácil para un modelo chico) y el árbol se
    arma de forma determinística → siempre sale un árbol válido, aunque el
    contenido haya que corregirlo en la validación."""
    import ollama
    from . import LLM_MODEL_GEN, LLM_KEEP_ALIVE

    texto = _texto_diagnostico_pdf(ruta_pdf)
    if not texto.strip():
        return {"categorias": []}

    prompt = (
        "Sos un técnico experto. A partir de estos fragmentos del manual de una máquina, "
        "listá los problemas/fallas del equipo con su causa y qué hacer. UNA LÍNEA por "
        "causa, con este formato EXACTO (tres partes separadas por ' | '):\n"
        "SÍNTOMA | CAUSA | QUÉ HACER\n"
        "Si un mismo síntoma tiene varias causas, repetí el síntoma en varias líneas. "
        "Usá SOLO información de los fragmentos. No pongas encabezados ni texto extra.\n\n"
        "FRAGMENTOS:\n" + texto + "\n\nLISTA:"
    )
    try:
        resp = ollama.generate(
            model=LLM_MODEL_GEN, prompt=prompt, stream=False, keep_alive=LLM_KEEP_ALIVE,
            options={"temperature": 0.1, "num_ctx": 4096, "num_predict": 1500},
        )
        bloques = _triples_a_bloques(resp.get("response", ""))
        return {"categorias": _construir_categorias(bloques, referencia)}
    except Exception:
        return {"categorias": []}


# ══════════════════════════════════════════════════════════════════════════════
#  GENERACIÓN PÁGINA POR PÁGINA (con progreso) — el camino completo
#  Recorre todo el PDF: tabla si la hay (rápido), si no IA por página. Junta todo,
#  consolida síntomas sinónimos y arma el árbol. Va reportando progreso.
# ══════════════════════════════════════════════════════════════════════════════

_prog: dict = {}
_prog_lock = threading.Lock()


def get_progreso_arbol(clave: str) -> dict:
    with _prog_lock:
        return dict(_prog.get(clave, {"estado": "no_iniciado"}))


def _set_prog(clave: str, datos: dict):
    with _prog_lock:
        _prog[clave] = datos


def _pagina_util(texto: str) -> bool:
    """Salta páginas casi vacías (tapas, separadores)."""
    return len(texto.split()) >= 25


def _llm_lineas_pagina(texto: str) -> str:
    """Le pide al modelo las líneas SÍNTOMA|CAUSA|ACCIÓN de UNA página (o 'NADA')."""
    import ollama
    from . import LLM_MODEL_GEN, LLM_KEEP_ALIVE
    prompt = (
        "Sos un técnico. Te paso UNA página de un manual de una máquina.\n"
        "Si la página describe PROBLEMAS/FALLAS con su causa y solución, listalos. Formato "
        "EXACTO, UNA LÍNEA por causa, tres partes separadas por ' | ':\n"
        "PROBLEMA QUE SE OBSERVA | POR QUÉ PASA (causa) | QUÉ HACER (solución)\n"
        "Ejemplo: El equipo no arranca | Fusible quemado | Reemplazar el fusible\n"
        "REGLAS IMPORTANTES:\n"
        "- El PRIMER campo es el SÍNTOMA observable (ej. 'no arranca', 'pierde presión', "
        "'no calienta', 'hace ruido'). NUNCA pongas una acción ('limpiar...', 'desmontar...') "
        "como síntoma.\n"
        "- Respondé SOLO en español. Si el texto está en inglés, TRADUCILO.\n"
        "- No repitas líneas iguales.\n"
        "- Si la página NO es de resolución de problemas (portada, índice, especificaciones, "
        "seguridad, instalación, garantía), respondé EXACTAMENTE: NADA\n\n"
        "PÁGINA:\n" + texto[:4000] + "\n\nLISTA:"
    )
    try:
        resp = ollama.generate(
            model=LLM_MODEL_GEN, prompt=prompt, stream=False, keep_alive=LLM_KEEP_ALIVE,
            options={"temperature": 0, "num_ctx": 4096, "num_predict": 700},
        )
        return resp.get("response", "")
    except Exception:
        return ""


def _consolidar_sintomas(triples: list) -> list:
    """Una sola llamada al LLM para agrupar síntomas que son el mismo problema
    (ej. 'no enciende' / 'no arranca' / 'no prende' → un nombre común)."""
    sintomas = list(dict.fromkeys(t["sintoma"] for t in triples))
    if len(sintomas) < 2:
        return triples
    import ollama
    from . import LLM_MODEL_GEN, LLM_KEEP_ALIVE
    lista = "\n".join(f"- {s}" for s in sintomas)
    prompt = (
        "Acá hay una lista de síntomas/problemas de una máquina. Algunos son el MISMO "
        "problema dicho distinto (ej. 'no enciende', 'no arranca', 'no prende').\n"
        "Para CADA síntoma de la lista, devolvé una línea con este formato EXACTO:\n"
        "SÍNTOMA ORIGINAL => NOMBRE COMÚN\n"
        "Usá el MISMO 'NOMBRE COMÚN' para los que son el mismo problema. Sin texto extra.\n\n"
        "SÍNTOMAS:\n" + lista + "\n\nMAPEO:"
    )
    try:
        resp = ollama.generate(
            model=LLM_MODEL_GEN, prompt=prompt, stream=False, keep_alive=LLM_KEEP_ALIVE,
            options={"temperature": 0, "num_ctx": 4096, "num_predict": 1200},
        )
        mapa = {}
        for ln in resp.get("response", "").splitlines():
            if "=>" in ln:
                orig, com = ln.split("=>", 1)
                orig = orig.strip(" -•*\t")
                com = com.strip(" -•*\t")
                if orig and com:
                    mapa[orig.lower()] = com
        for t in triples:
            t["sintoma"] = mapa.get(t["sintoma"].lower(), t["sintoma"])
    except Exception:
        pass
    return triples


def _clave_norm(s: str) -> str:
    """Clave normalizada para agrupar/deduplicar (sin acentos, sin paréntesis,
    sin puntuación) → fusiona variantes de fraseo y elimina '(repetido)' etc."""
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)             # quita "(repetido)", "(continuación)"
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
           .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _agrupar_triples(triples: list) -> list:
    """Agrupa por síntoma (normalizado) y deduplica causas/acciones repetidas."""
    bloques, idx = [], {}
    for t in triples:
        sintoma = re.sub(r"\s*\(.*?\)\s*", " ", t["sintoma"]).strip() or t["sintoma"]
        key = _clave_norm(sintoma)
        if not key:
            continue
        if key not in idx:
            idx[key] = {"sintoma": sintoma, "pares": [], "_vistos": set()}
            bloques.append(idx[key])
        b = idx[key]
        dk = (_clave_norm(t["causa"]), _clave_norm(t.get("accion", "")))
        if dk[0] and dk not in b["_vistos"]:
            b["_vistos"].add(dk)
            b["pares"].append({"causa": t["causa"], "accion": t.get("accion", "")})
    for b in bloques:
        b.pop("_vistos", None)
    return bloques


def generar_arbol_completo(ruta_pdf: str, referencia: str, clave: str):
    """Orquesta la generación página por página (pensado para correr en un thread).
    El resultado queda en el progreso con estado='completado' y la clave 'arbol'."""
    try:
        doc = fitz.open(ruta_pdf)
        total = doc.page_count
        _set_prog(clave, {"estado": "procesando", "pagina": 0, "total": total,
                          "porcentaje": 0, "segundos_restantes": None,
                          "mensaje": "Leyendo el manual…"})
        triples = []
        tiempos = []
        for n, pg in enumerate(doc):
            t_ini = time.time()
            texto = pg.get_text("text")
            if _pagina_util(texto):
                cs = _header_cols(_lineas(pg))
                if cs:  # página con tabla SÍNTOMA/CAUSA/ACCIÓN → determinístico
                    for b in _bloques(pg, cs):
                        s = _norm(b["sintoma"])
                        for p in b["pares"]:
                            c = _norm(p["causa"])
                            a = _norm(p["accion"]).lstrip("-").strip()
                            if s and c:
                                triples.append({"sintoma": s, "causa": c, "accion": a})
                else:  # cualquier otra página → IA
                    for b in _triples_a_bloques(_llm_lineas_pagina(texto)):
                        for p in b["pares"]:
                            triples.append({"sintoma": b["sintoma"], "causa": p["causa"],
                                            "accion": p.get("accion", "")})
            tiempos.append(time.time() - t_ini)
            prom = sum(tiempos) / len(tiempos)
            _set_prog(clave, {"estado": "procesando", "pagina": n + 1, "total": total,
                              "porcentaje": round((n + 1) / total * 100),
                              "segundos_restantes": round(prom * (total - n - 1)),
                              "mensaje": f"Analizando página {n + 1} de {total}… ({len(triples)} hallazgos)"})
        doc.close()

        _set_prog(clave, {"estado": "procesando", "pagina": total, "total": total,
                          "porcentaje": 99, "segundos_restantes": 3,
                          "mensaje": "Armando el árbol…"})
        arbol = {"categorias": _construir_categorias(_agrupar_triples(triples), referencia)}
        try:
            guardar_borrador(clave, arbol)
        except Exception:
            pass
        _set_prog(clave, {"estado": "completado", "pagina": total, "total": total,
                          "porcentaje": 100, "segundos_restantes": 0,
                          "n_categorias": len(arbol["categorias"]), "arbol": arbol,
                          "mensaje": f"Listo: {len(arbol['categorias'])} categorías. Revisá y aprobá."})
    except Exception as e:
        _set_prog(clave, {"estado": "error", "mensaje": f"Error al generar: {e}"})


def guardar_borrador(clave: str, arbol: dict) -> str:
    """Guarda el borrador en data/arboles_borrador/{clave}.json y devuelve la ruta."""
    import json
    BORRADORES_DIR.mkdir(parents=True, exist_ok=True)
    ruta = BORRADORES_DIR / f"{clave}.json"
    ruta.write_text(json.dumps(arbol, ensure_ascii=False, indent=2), encoding="utf8")
    return str(ruta)
