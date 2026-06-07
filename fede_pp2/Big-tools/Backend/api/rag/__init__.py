"""
Módulo RAG — Big Tools
Utilidades compartidas entre indexador y retriever.
"""

import re
import chromadb
from pathlib import Path
from typing import Optional

# ── Modelo LLM local (Ollama) ─────────────────────────────────────────────────
# Punto ÚNICO para cambiar de modelo en todo el sistema (chat, análisis, traducción).
# Para probar otro: `ollama pull <modelo>` y cambiar esta línea.
LLM_MODEL = "qwen2.5:3b"  # 3B, SIN razonamiento, entra 100% en GPU de 4 GB (rápido)
# Modelo para GENERAR árboles de conocimiento (tarea de admin, una sola vez).
# Puede ser uno más grande/lento (ej. "qwen2.5:7b") porque no es runtime. Por
# defecto usa el mismo que el runtime para no tener que descargar otro.
LLM_MODEL_GEN = "qwen2.5:7b"  # modelo más grande para generar árboles (mejor calidad)
# Tiempo que Ollama mantiene el modelo cargado en memoria entre consultas
# (evita la demora de recargarlo en cada pregunta).
LLM_KEEP_ALIVE = "30m"

# ── Detección de idioma (sin dependencias externas) ──────────────────────────
# Palabras funcionales de alta frecuencia que distinguen español vs inglés.
# Son suficientemente distintas entre idiomas para clasificar con buena precisión.
_ES_PALABRAS = frozenset([
    "de", "la", "el", "en", "con", "del", "los", "las", "para", "por",
    "que", "una", "un", "es", "al", "se", "más", "como", "pero", "su",
    "sus", "lo", "le", "y", "o", "a", "no", "si", "ya", "muy", "hay",
    "cuando", "este", "esta", "estos", "estas", "ser", "estar", "tiene",
    "tienen", "puede", "pueden", "también", "así", "sobre", "entre",
    "después", "antes", "sin", "hasta", "cada", "todo", "todos",
])

_EN_PALABRAS = frozenset([
    "the", "and", "of", "to", "in", "is", "it", "for", "with", "as",
    "that", "are", "this", "be", "was", "were", "or", "not", "by", "at",
    "but", "from", "have", "has", "do", "does", "will", "would", "can",
    "if", "when", "your", "you", "we", "they", "their", "an", "which",
    "all", "been", "its", "on", "also", "into", "than", "then", "use",
    "using", "make", "check", "ensure", "make", "should", "must",
])


def detectar_idioma(texto: str) -> str:
    """
    Detecta si el texto es principalmente español ('es'), inglés ('en')
    o indeterminado ('und').
    Usa conteo de palabras funcionales — sin dependencias externas.
    """
    palabras = re.sub(r"[^a-z]", " ", texto.lower()).split()
    if len(palabras) < 8:
        return "und"
    es = sum(1 for p in palabras if p in _ES_PALABRAS)
    en = sum(1 for p in palabras if p in _EN_PALABRAS)
    total_matches = es + en
    if total_matches == 0:
        return "und"
    ratio = es / total_matches
    if ratio >= 0.55:
        return "es"
    if ratio <= 0.45:
        return "en"
    return "und"

VECTORSTORE_PATH = str(Path(__file__).parent.parent.parent / "data" / "vectorstore")

# ── Singleton ChromaDB ────────────────────────────────────────────────────────
_cliente_chroma: Optional[chromadb.PersistentClient] = None


def get_cliente_chroma() -> chromadb.PersistentClient:
    """Devuelve el cliente ChromaDB (una sola instancia por proceso)."""
    global _cliente_chroma
    if _cliente_chroma is None:
        Path(VECTORSTORE_PATH).mkdir(parents=True, exist_ok=True)
        _cliente_chroma = chromadb.PersistentClient(path=VECTORSTORE_PATH)
    return _cliente_chroma


# ── Normalización de nombres ──────────────────────────────────────────────────
def normalizar_nombre_coleccion(nombre: str) -> str:
    """
    Convierte un nombre de máquina a formato válido para ChromaDB.
    ChromaDB solo acepta [a-zA-Z0-9._-], sin espacios ni tildes.

    Ejemplos:
        "Motor Cummins"             → "motor_cummins"
        "Hidrolavadora Kärcher"     → "hidrolavadora_karcher"
        "Generador Generac Guardian"→ "generador_generac_guardian"
    """
    nombre = nombre.lower()
    nombre = nombre.replace(" ", "_")
    nombre = (
        nombre
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        .replace("ä", "a").replace("ö", "o").replace("ü", "u")
    )
    nombre = re.sub(r"[^a-zA-Z0-9._-]", "", nombre)
    return nombre
