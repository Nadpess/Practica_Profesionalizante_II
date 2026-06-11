# Backend/api/rag/rag_routes.py

import json
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse

from api.rag.indexador import indexar_manual, esta_indexado, get_progreso
from api.rag.retriever import generar_respuesta, generar_respuesta_stream, generar_respuesta_stream_conversacional, resumir_conversacion
from api.rag.sesiones import crear_sesion, obtener_historial, obtener_sesion, agregar_mensaje, fijar_resumen, limpiar_sesion, limpiar_expiradas
from api.rag import normalizar_nombre_coleccion

rag_router  = APIRouter(prefix="/api/rag", tags=["RAG"])
MANUALES_DIR  = Path(__file__).parent.parent.parent / "data" / "manuales_pdf"
MANUALES_JSON = Path(__file__).parent.parent.parent / "data" / "manuales.json"


def _leer_manuales() -> list[dict]:
    with open(MANUALES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Indexación ────────────────────────────────────────────────────────────────

@rag_router.post("/indexar/{nombre_maquina}")
def indexar(nombre_maquina: str):
    """
    Inicia la indexación del PDF de una máquina en ChromaDB.
    La operación corre en un thread secundario; usá /progreso/{nombre} para el estado.
    """
    # Evitar indexaciones simultáneas para la misma máquina
    progreso_actual = get_progreso(nombre_maquina)
    if progreso_actual.get("estado") in ("preparando", "indexando"):
        raise HTTPException(
            status_code=409,
            detail="Ya hay una indexación en curso para esta máquina. Esperá a que termine.",
        )

    manuales = _leer_manuales()
    manual   = next((m for m in manuales if m["nombre"] == nombre_maquina), None)

    if not manual:
        raise HTTPException(status_code=404, detail="Manual no encontrado en manuales.json")

    ruta_pdf = MANUALES_DIR / manual["archivo"]
    if not ruta_pdf.exists():
        raise HTTPException(status_code=404, detail=f"Archivo PDF no encontrado: {manual['archivo']}")

    # ── Correr indexación en background ──────────────────────────────────────
    def _run():
        try:
            indexar_manual(nombre_maquina, str(ruta_pdf))
        except ConnectionError as e:
            key = normalizar_nombre_coleccion(nombre_maquina)
            from api.rag.indexador import _set_progreso
            _set_progreso(key, {
                "estado": "error",
                "porcentaje": 0,
                "mensaje": f"❌ Error de conexión con Ollama: {e}",
            })
        except Exception as e:
            key = normalizar_nombre_coleccion(nombre_maquina)
            from api.rag.indexador import _set_progreso
            _set_progreso(key, {
                "estado": "error",
                "porcentaje": 0,
                "mensaje": f"❌ Error inesperado: {e}",
            })

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {
        "success":        True,
        "mensaje":        f"Indexación de '{nombre_maquina}' iniciada.",
        "nombre_maquina": nombre_maquina,
    }


# ── Progreso de indexación ────────────────────────────────────────────────────

@rag_router.get("/progreso/{nombre_maquina}")
def progreso(nombre_maquina: str):
    """Retorna el progreso actual de la indexación de una máquina."""
    return get_progreso(nombre_maquina)


# ── Consulta (sin streaming) ──────────────────────────────────────────────────

@rag_router.post("/consulta")
def consulta(
    nombre_maquina: str = Body(...),
    pregunta:        str = Body(...),
):
    """Consulta RAG estándar (respuesta completa de una vez)."""
    if not esta_indexado(nombre_maquina):
        raise HTTPException(
            status_code=400,
            detail="El manual no está indexado. Llamá primero a /api/rag/indexar",
        )
    try:
        resultado = generar_respuesta(nombre_maquina, pregunta)
        _registrar_stat(nombre_maquina, pregunta)
        return resultado
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta RAG: {e}")


# ── Consulta con streaming (SSE) ──────────────────────────────────────────────

@rag_router.post("/consulta/stream")
def consulta_stream(
    nombre_maquina: str  = Body(...),
    pregunta:       str  = Body(...),
    analisis:       bool = Body(False),
):
    """
    Consulta RAG con streaming token a token.
    El cliente debe consumir el cuerpo como Server-Sent Events.

    analisis=True activa el modo de análisis estructurado con gravedad (🔴/🟡/🟢),
    causa probable, riesgo operacional y pasos de acción.
    Usalo cuando el endpoint se dispara desde 'Profundizar con IA'.
    """
    if not esta_indexado(nombre_maquina):
        raise HTTPException(
            status_code=400,
            detail="El manual no está indexado. Llamá primero a /api/rag/indexar",
        )

    _registrar_stat(nombre_maquina, pregunta)

    return StreamingResponse(
        generar_respuesta_stream(nombre_maquina, pregunta, modo_analisis=analisis),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


# ── Estado general ────────────────────────────────────────────────────────────

@rag_router.get("/estado")
def estado():
    """Muestra qué manuales están indexados."""
    manuales = _leer_manuales()
    return {
        "manuales": [
            {"nombre": m["nombre"], "indexado": esta_indexado(m["nombre"])}
            for m in manuales
        ]
    }


# ── Sesión conversacional ─────────────────────────────────────────────────────

@rag_router.post("/sesion")
def nueva_sesion(
    nombre_maquina: str = Body(..., embed=True),
    contexto:       str = Body("", embed=True),
):
    """Crea una nueva sesión conversacional para una máquina.
    'contexto' (opcional) = resumen del diagnóstico previo del SE, para un chat contextual."""
    limpiar_expiradas()
    session_id = crear_sesion(nombre_maquina, contexto)
    return {"session_id": session_id}


@rag_router.delete("/sesion/{session_id}")
def eliminar_sesion(session_id: str):
    """Elimina una sesión (botón 'Nueva conversación' en el frontend)."""
    limpiar_sesion(session_id)
    return {"ok": True}


@rag_router.post("/consulta/conversacional")
def consulta_conversacional(
    nombre_maquina: str = Body(...),
    pregunta:       str = Body(...),
    session_id:     str = Body(...),
):
    """
    Consulta RAG con memoria de sesión y razonamiento explícito.
    El LLM recibe el historial completo y actúa como agente diagnóstico:
    hace preguntas de seguimiento y cita lo que el técnico mencionó anteriormente.
    """
    if not esta_indexado(nombre_maquina):
        raise HTTPException(
            status_code=400,
            detail="El manual no está indexado. Indexalo desde el panel de administración.",
        )

    # Leer la sesión: ancla del diagnóstico (contexto), resumen rodante e historial.
    sesion        = obtener_sesion(session_id) or {}
    contexto_diag = sesion.get("contexto", "")
    resumen       = sesion.get("resumen", "")
    historial     = list(sesion.get("mensajes", []))

    # Guardar mensaje del usuario en la sesión
    agregar_mensaje(session_id, "user", pregunta)

    _registrar_stat(nombre_maquina, pregunta)

    def _stream_con_guardado():
        """Wrapper que guarda la respuesta y, si la charla creció, comprime lo viejo."""
        for evento_str in generar_respuesta_stream_conversacional(
            nombre_maquina, pregunta, historial, contexto_diag, resumen
        ):
            yield evento_str
            # Detectar el evento con la respuesta completa y guardarla
            if evento_str.startswith("data: "):
                try:
                    import json as _json
                    ev = _json.loads(evento_str[6:])
                    if ev.get("tipo") == "respuesta_completa" and ev.get("texto"):
                        agregar_mensaje(session_id, "assistant", ev["texto"])
                except Exception:
                    pass
        # ── Resumen rodante lazy: solo si la conversación se hizo larga ──────────
        try:
            s2 = obtener_sesion(session_id)
            if s2 and len(s2.get("mensajes", [])) > 8:
                viejos = s2["mensajes"][:-4]
                nuevo  = resumir_conversacion(contexto_diag, resumen, viejos)
                fijar_resumen(session_id, nuevo, 4)
        except Exception:
            pass

    return StreamingResponse(
        _stream_con_guardado(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


# ── Helper interno ────────────────────────────────────────────────────────────

def _registrar_stat(nombre_maquina: str, pregunta: str):
    try:
        from api.stats import stats_manager
        stats_manager.registrar_consulta_rag(nombre_maquina, pregunta)
    except Exception:
        pass  # no interrumpir la consulta por un fallo de stats
