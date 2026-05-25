# Backend/api/rag/se_dinamico.py
import json
import re
import ollama

from . import get_cliente_chroma, normalizar_nombre_coleccion
from .retriever import buscar_chunks, _embedding

MAX_PASOS        = 3
N_CHUNKS_SE      = 4
OPCIONES_DEFECTO = ["Si", "No", "No se / No lo verifique"]

LLM_OPTIONS = {
    "num_predict": 350,
    "temperature": 0.05,
    "num_ctx":     2048,
}


def _fmt_chunk(c: dict) -> str:
    header = f"[Pag. {c['pagina']}]"
    if c.get("seccion"):
        header += f" [{c['seccion']}]"
    return f"{header} {c['texto'][:400]}"


def _parsear_respuesta_llm(texto: str) -> dict:
    texto = texto.strip()

    if re.search(r'DIAGNOSTICO\s*:', texto, re.IGNORECASE):
        partes = re.split(r'DIAGNOSTICO\s*:', texto, flags=re.IGNORECASE, maxsplit=1)
        diagnostico = partes[1].strip() if len(partes) > 1 else texto
        return {"tipo": "diagnostico", "texto": diagnostico, "opciones": []}

    if re.search(r'PREGUNTA\s*:', texto, re.IGNORECASE):
        partes = re.split(r'PREGUNTA\s*:', texto, flags=re.IGNORECASE, maxsplit=1)
        resto  = partes[1].strip() if len(partes) > 1 else texto
        lineas = resto.split("\n")
        pregunta_txt = lineas[0].strip().rstrip("?") + "?"
        opciones = []
        for linea in lineas[1:]:
            linea = linea.strip()
            if re.match(r'^[-*]|^\d+[.)]\s|^[a-zA-Z][.)]\s', linea):
                opcion = re.sub(r'^[-*\d.)a-zA-Z]+\s*', '', linea).strip()
                if opcion:
                    opciones.append(opcion)
        if not opciones:
            opciones = OPCIONES_DEFECTO
        return {"tipo": "pregunta", "texto": pregunta_txt, "opciones": opciones[:4]}

    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    if not lineas:
        return {"tipo": "error", "texto": "No se pudo generar una respuesta.", "opciones": []}

    if lineas[0].endswith("?"):
        opciones = []
        for linea in lineas[1:]:
            if re.match(r'^[-*]|^\d+[.)]\s', linea):
                opcion = re.sub(r'^[-*\d.)]+\s*', '', linea).strip()
                if opcion:
                    opciones.append(opcion)
        return {
            "tipo":     "pregunta",
            "texto":    lineas[0],
            "opciones": opciones[:4] if opciones else OPCIONES_DEFECTO,
        }

    return {"tipo": "diagnostico", "texto": texto, "opciones": []}


def iniciar_diagnostico(nombre_maquina: str) -> dict:
    try:
        cliente   = get_cliente_chroma()
        col_name  = normalizar_nombre_coleccion(nombre_maquina)
        coleccion = cliente.get_collection(name=col_name)
        todos = coleccion.get(include=["metadatas"])
        secciones_raw = set()
        for meta in todos["metadatas"]:
            sec = meta.get("seccion", "").strip()
            if sec and len(sec) > 3:
                secciones_raw.add(sec)
        keywords = ["falla", "error", "problema", "solucion", "trouble", "fault",
                    "manten", "repair", "diagnos", "averia", "defect", "warning"]
        secciones_relevantes = [
            s for s in secciones_raw
            if any(kw in s.lower() for kw in keywords)
        ]
        if len(secciones_relevantes) >= 3:
            opciones = sorted(secciones_relevantes)[:6]
            return {
                "tipo":     "inicio",
                "mensaje":  f"Cual es el problema con {nombre_maquina}?",
                "opciones": opciones,
                "fuente":   "indice",
            }
    except Exception:
        pass

    try:
        chunks_muestra = buscar_chunks(nombre_maquina, "falla error problema mantenimiento")[:N_CHUNKS_SE]
        contexto = "\n".join(_fmt_chunk(c) for c in chunks_muestra) if chunks_muestra else "(sin contexto)"
        prompt = (
            f"Sos un tecnico experto en {nombre_maquina}.\n"
            f"Genera exactamente 4 categorias de sintomas/problemas comunes.\n"
            f"Formato ESTRICTO:\n"
            f"PREGUNTA: Cual es el sintoma principal?\n"
            f"OPCIONES:\n"
            f"- [categoria 1]\n"
            f"- [categoria 2]\n"
            f"- [categoria 3]\n"
            f"- [categoria 4]\n\n"
            f"CONTEXTO:\n{contexto}"
        )
        resp = ollama.generate(model="llama3.2:3b", prompt=prompt, stream=False, options=LLM_OPTIONS)
        parsed = _parsear_respuesta_llm(resp["response"])
        if parsed["tipo"] == "pregunta" and parsed["opciones"]:
            return {
                "tipo":     "inicio",
                "mensaje":  parsed["texto"],
                "opciones": parsed["opciones"],
                "fuente":   "llm",
            }
    except Exception:
        pass

    return {
        "tipo":     "inicio",
        "mensaje":  f"Cual es el sintoma principal en {nombre_maquina}?",
        "opciones": [
            "No enciende / no arranca",
            "Ruido inusual o vibracion",
            "Sobrecalentamiento",
            "Perdida de potencia o rendimiento",
            "Fuga (aceite, agua, combustible)",
            "Otro sintoma",
        ],
        "fuente": "generico",
    }


def siguiente_paso(
    nombre_maquina:    str,
    historial_se:      list,
    respuesta_usuario: str,
) -> dict:
    paso_actual = len([h for h in historial_se if h["rol"] == "usuario"]) + 1

    camino = " ".join(h["texto"] for h in historial_se if h["rol"] == "usuario") + " " + respuesta_usuario
    camino_legible = camino.strip()

    chunks  = buscar_chunks(nombre_maquina, camino_legible)[:N_CHUNKS_SE]
    contexto = "\n\n".join(_fmt_chunk(c) for c in chunks) if chunks else "(sin informacion)"

    hist_texto = ""
    for h in historial_se:
        prefijo = "Tecnico" if h["rol"] == "usuario" else "Sistema"
        hist_texto += f"{prefijo}: {h['texto']}\n"
    hist_texto += f"Tecnico: {respuesta_usuario}"

    if paso_actual >= MAX_PASOS:
        instruccion = (
            "Con la informacion disponible, emiti el DIAGNOSTICO FINAL ahora. "
            "Incluye: causa raiz, pasos concretos de solucion y pagina del manual si esta disponible."
        )
        formato = "DIAGNOSTICO: [causa raiz] — Solucion: [pasos a seguir] — Ref: pag. [N]"
    else:
        instruccion = (
            f"Paso {paso_actual} de maximo {MAX_PASOS}.\n"
            "REGLA CRITICA sobre las OPCIONES: deben ser CONDICIONES OBSERVABLES o ESTADOS DE LA MAQUINA.\n"
            "El tecnico responde lo que VE o lo que YA verifico — NO lo que va a hacer.\n"
            "CORRECTO: 'Si, el filtro esta visiblemente sucio' / 'No, el filtro se ve limpio'\n"
            "INCORRECTO (nunca uses esto como opcion): 'Reemplazar el filtro' / 'Limpiar el componente'\n\n"
            "Si el sintoma reportado ya identifica claramente la causa -> da el DIAGNOSTICO directamente.\n"
            "Si necesitas confirmar una condicion -> hace UNA pregunta diagnostica con 2-3 opciones observables."
        )
        formato = (
            "Si preguntas:\n"
            "PREGUNTA: [pregunta sobre lo que el tecnico observa o ya verifico]\n"
            "OPCIONES:\n"
            "- [condicion observable A]\n"
            "- [condicion observable B]\n"
            "- [condicion observable C]\n\n"
            "Si diagnosticas:\n"
            "DIAGNOSTICO: [causa raiz] — Solucion: [pasos ejecutables] — Ref: pag. [N]"
        )

    prompt = (
        f"Sos un ingeniero tecnico senior diagnosticando una falla en {nombre_maquina}.\n"
        f"El que usa esto ES el tecnico de campo — NUNCA lo remitas a 'consultar a un tecnico'.\n"
        f"Usa SOLO la informacion del manual. No inventes datos.\n\n"
        f"HISTORIAL:\n{hist_texto}\n\n"
        f"FRAGMENTOS DEL MANUAL:\n{contexto}\n\n"
        f"{instruccion}\n\n"
        f"Responde en espanol con este formato exacto:\n"
        f"{formato}"
    )

    try:
        resp = ollama.generate(model="llama3.2:3b", prompt=prompt, stream=False, options=LLM_OPTIONS)
        parsed = _parsear_respuesta_llm(resp["response"])
        if parsed["tipo"] == "diagnostico" and chunks:
            paginas = sorted({c["pagina"] for c in chunks})
            parsed["paginas"] = paginas
        return parsed
    except Exception as e:
        return {
            "tipo":     "error",
            "texto":    f"Error al generar el siguiente paso: {e}",
            "opciones": [],
        }
