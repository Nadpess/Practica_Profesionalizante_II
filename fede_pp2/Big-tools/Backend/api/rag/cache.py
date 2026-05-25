# Backend/api/rag/cache.py
"""
Cache semántico de respuestas RAG.

Flujo:
  1. Antes de llamar al LLM → buscar_en_cache(maquina, pregunta)
     - Si hit (distancia < THRESHOLD) → devuelve la respuesta cacheada (sin tocar Ollama)
     - Si miss → None (el llamador llama al LLM normalmente)

  2. Después de generar una respuesta con confianza >= MIN_CONFIANZA_CACHE
     → guardar_en_cache(maquina, pregunta, respuesta, confianza, paginas)

  3. Feedback del técnico:
     → registrar_feedback(maquina, pregunta, positivo)
       - 👍 positivo: sube el score de confianza del entry en cache
       - 👎 negativo: marca el entry para no volver a servirse
"""

import json
import re
from datetime import datetime
from typing import Optional

import ollama

from . import get_cliente_chroma, normalizar_nombre_coleccion

# ── Constantes ────────────────────────────────────────────────────────────────

# Distancia L2 máxima para considerar hit en cache (más bajo = más estricto)
# Con nomic-embed-text: distancias típicas 100-500. Umbral 120 = preguntas muy similares.
CACHE_THRESHOLD     = 120.0
# Solo se cachean respuestas con esta confianza mínima (0-100)
MIN_CONFIANZA_CACHE = 70
# Prefijo de colección para distinguir del índice de manuales
CACHE_PREFIX = "cache__"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nombre_coleccion_cache(nombre_maquina: str) -> str:
    return CACHE_PREFIX + normalizar_nombre_coleccion(nombre_maquina)


def _embedding(texto: str) -> list:
    try:
        return ollama.embeddings(model="nomic-embed-text", prompt=texto)["embedding"]
    except Exception as e:
        raise ConnectionError(f"Ollama no disponible: {e}")


def _get_or_create_cache(nombre_maquina: str):
    cliente = get_cliente_chroma()
    col_name = _nombre_coleccion_cache(nombre_maquina)
    try:
        return cliente.get_collection(name=col_name)
    except Exception:
        return cliente.create_collection(
            name=col_name,
            metadata={"hnsw:space": "l2"}
        )


# ── API pública ───────────────────────────────────────────────────────────────

def buscar_en_cache(nombre_maquina: str, pregunta: str) -> Optional[dict]:
    """
    Busca en el cache semántico.
    Retorna dict con respuesta cacheada, o None si no hay hit.

    El dict tiene las mismas claves que una respuesta RAG normal:
      {respuesta, confianza, paginas, secciones, desde_cache: True}
    """
    try:
        col = _get_or_create_cache(nombre_maquina)
        if col.count() == 0:
            return None

        emb = _embedding(pregunta)
        resultado = col.query(query_embeddings=[emb], n_results=1)

        if not resultado["distances"][0]:
            return None

        distancia = resultado["distances"][0][0]
        if distancia > CACHE_THRESHOLD:
            return None

        meta = resultado["metadatas"][0][0]

        # No servir entradas marcadas como negativas
        if meta.get("thumbs_down", 0) >= 2:
            return None

        return {
            "respuesta":    meta["respuesta"],
            "confianza":    int(meta.get("confianza", 75)),
            "paginas":      json.loads(meta.get("paginas", "[]")),
            "secciones":    json.loads(meta.get("secciones", "[]")),
            "desde_cache":  True,
            "distancia":    round(distancia, 1),
        }

    except Exception:
        return None  # Cache falla → seguir con RAG normal


def guardar_en_cache(
    nombre_maquina: str,
    pregunta:       str,
    respuesta:      str,
    confianza:      int,
    paginas:        list,
    secciones:      Optional[list] = None,
) -> bool:
    """
    Guarda una respuesta en el cache si supera el umbral de confianza.
    Retorna True si se guardó.
    """
    if confianza < MIN_CONFIANZA_CACHE:
        return False
    if not respuesta or not respuesta.strip():
        return False

    try:
        col     = _get_or_create_cache(nombre_maquina)
        emb     = _embedding(pregunta)
        doc_id  = f"cache_{abs(hash(pregunta.lower().strip()))}"

        # Si ya existe una entrada muy similar, actualizarla en vez de duplicar
        existing = col.query(query_embeddings=[emb], n_results=1)
        if existing["distances"][0] and existing["distances"][0][0] < CACHE_THRESHOLD * 0.5:
            col.delete(ids=[existing["ids"][0][0]])

        col.add(
            ids=[doc_id],
            embeddings=[emb],
            documents=[pregunta],
            metadatas=[{
                "respuesta":    respuesta[:3000],   # limitar tamaño
                "confianza":    confianza,
                "paginas":      json.dumps(paginas),
                "secciones":    json.dumps(secciones or []),
                "thumbs_up":    0,
                "thumbs_down":  0,
                "timestamp":    datetime.now().isoformat(),
                "maquina":      nombre_maquina,
            }]
        )
        return True
    except Exception:
        return False


def registrar_feedback(
    nombre_maquina: str,
    pregunta:       str,
    positivo:       bool,
    respuesta:      str  = "",
    confianza:      int  = 75,
    paginas:        list = None,
    secciones:      list = None,
) -> bool:
    """
    Registra feedback de un técnico sobre una respuesta.
    - 👍 positivo=True: guarda/refuerza en cache
    - 👎 positivo=False: penaliza la entrada en cache
    """
    try:
        col = _get_or_create_cache(nombre_maquina)
        emb = _embedding(pregunta)

        existing = col.query(query_embeddings=[emb], n_results=1)
        hay_entry = (
            existing["distances"][0]
            and existing["distances"][0][0] < CACHE_THRESHOLD
        )

        if positivo:
            if hay_entry:
                # Reforzar entry existente: sube confianza + thumbs_up
                entry_id = existing["ids"][0][0]
                meta     = existing["metadatas"][0][0]
                col.update(
                    ids=[entry_id],
                    metadatas=[{
                        **meta,
                        "thumbs_up":  meta.get("thumbs_up", 0) + 1,
                        "confianza":  min(100, int(meta.get("confianza", 75)) + 5),
                    }]
                )
            elif respuesta:
                # No estaba en cache → guardarlo ahora (feedback positivo fuerza el guardado)
                guardar_en_cache(
                    nombre_maquina, pregunta, respuesta,
                    confianza=max(confianza, MIN_CONFIANZA_CACHE),
                    paginas=paginas or [],
                    secciones=secciones or [],
                )
        else:
            if hay_entry:
                # Penalizar: incrementar thumbs_down
                entry_id = existing["ids"][0][0]
                meta     = existing["metadatas"][0][0]
                nuevo_td = meta.get("thumbs_down", 0) + 1
                col.update(
                    ids=[entry_id],
                    metadatas=[{**meta, "thumbs_down": nuevo_td}]
                )
        return True

    except Exception:
        return False


def stats_cache(nombre_maquina: str) -> dict:
    """Retorna estadísticas del cache de una máquina (para el panel admin)."""
    try:
        col   = _get_or_create_cache(nombre_maquina)
        total = col.count()
        if total == 0:
            return {"total": 0, "thumbs_up": 0, "thumbs_down": 0}

        # Obtener todos los metadatos
        todos = col.get(include=["metadatas"])
        tu = sum(m.get("thumbs_up", 0)   for m in todos["metadatas"])
        td = sum(m.get("thumbs_down", 0) for m in todos["metadatas"])
        return {"total": total, "thumbs_up": tu, "thumbs_down": td}
    except Exception:
        return {"total": 0, "thumbs_up": 0, "thumbs_down": 0}
