# Backend/api/rag/sesiones.py
"""
Gestor de sesiones conversacionales para el RAG.
Mantiene el historial de cada conversación en memoria.
Las sesiones expiran automáticamente después de 30 minutos de inactividad.
"""

import uuid
import time
import threading
from typing import List, Dict, Optional

EXPIRY_SECONDS = 1800   # 30 minutos
MAX_MENSAJES   = 20     # máximo de mensajes en el historial (evita prompts infinitos)

_sesiones: Dict[str, dict] = {}
_lock = threading.Lock()


# ── CRUD de sesiones ──────────────────────────────────────────────────────────

def crear_sesion(nombre_maquina: str, contexto: str = "") -> str:
    """Crea una nueva sesión y retorna el session_id.
    'contexto' = ancla fija del diagnóstico previo (síntoma/causa/solución del SE),
    que se mantiene siempre en el prompt para que el chat sea contextual."""
    session_id = str(uuid.uuid4())
    with _lock:
        _sesiones[session_id] = {
            "maquina":        nombre_maquina,
            "mensajes":       [],
            "contexto":       contexto,   # ancla fija (no se resume nunca)
            "resumen":        "",          # resumen rodante de los turnos viejos
            "ultimo_acceso":  time.time(),
        }
    return session_id


def obtener_sesion(session_id: str) -> Optional[dict]:
    """Retorna la sesión o None si no existe / expiró."""
    with _lock:
        sesion = _sesiones.get(session_id)
        if not sesion:
            return None
        if time.time() - sesion["ultimo_acceso"] > EXPIRY_SECONDS:
            del _sesiones[session_id]
            return None
        sesion["ultimo_acceso"] = time.time()
        return dict(sesion)


def agregar_mensaje(session_id: str, role: str, content: str):
    """
    Agrega un mensaje al historial.
    role: 'user' | 'assistant'
    """
    with _lock:
        sesion = _sesiones.get(session_id)
        if not sesion:
            return
        sesion["mensajes"].append({
            "role":    role,
            "content": content,
            "ts":      time.time(),
        })
        # Recortar historial si supera el máximo (mantener los más recientes)
        if len(sesion["mensajes"]) > MAX_MENSAJES:
            sesion["mensajes"] = sesion["mensajes"][-MAX_MENSAJES:]
        sesion["ultimo_acceso"] = time.time()


def obtener_historial(session_id: str) -> List[dict]:
    """Retorna la lista de mensajes de la sesión."""
    sesion = obtener_sesion(session_id)
    return sesion["mensajes"] if sesion else []


def fijar_resumen(session_id: str, resumen: str, mantener_ultimos: int = 4):
    """Guarda el resumen rodante y deja solo los últimos N mensajes literales
    (los viejos quedan comprimidos en el resumen → no se pierde la ventana de contexto)."""
    with _lock:
        sesion = _sesiones.get(session_id)
        if not sesion:
            return
        sesion["resumen"] = resumen
        sesion["mensajes"] = sesion["mensajes"][-mantener_ultimos:]
        sesion["ultimo_acceso"] = time.time()


def limpiar_sesion(session_id: str):
    """Elimina una sesión manualmente (botón 'Nueva conversación')."""
    with _lock:
        _sesiones.pop(session_id, None)


def limpiar_expiradas():
    """Limpia todas las sesiones expiradas. Llamar periódicamente."""
    ahora = time.time()
    with _lock:
        expiradas = [
            sid for sid, s in _sesiones.items()
            if ahora - s["ultimo_acceso"] > EXPIRY_SECONDS
        ]
        for sid in expiradas:
            del _sesiones[sid]
