"""
Diagnostico de retrieval: muestra que hay indexado y que recupera la busqueda.

Uso (desde Backend/, con el venv y el backend NO hace falta que este corriendo,
pero si Ollama tiene que estar levantado porque la busqueda usa embeddings):
    python debug_query.py
    python debug_query.py "Compresor" "el compresor no arranca"
"""
import sys
from api.rag.retriever import buscar_chunks
from api.rag import get_cliente_chroma, normalizar_nombre_coleccion

MAQ   = sys.argv[1] if len(sys.argv) > 1 else "Compresor"
QUERY = sys.argv[2] if len(sys.argv) > 2 else "el compresor no arranca"
FRASE = "EL COMPRESOR NO ARRANCA"

# 1) ¿Quedó indexado un chunk con la frase? (verifica que el reindex tomó el código nuevo)
try:
    col = get_cliente_chroma().get_collection(normalizar_nombre_coleccion(MAQ))
    todos = col.get(include=["documents", "metadatas"])
    con_frase = [(m.get("pagina"), d) for d, m in zip(todos["documents"], todos["metadatas"])
                 if FRASE in d.upper()]
    print(f"Colección '{normalizar_nombre_coleccion(MAQ)}': {col.count()} chunks")
    print(f"Chunks que contienen '{FRASE}': {len(con_frase)}")
    for p, d in con_frase:
        print(f"  [pag {p}] {d[:140]}")
        enfocado = d.strip().startswith("Sintoma:") or d.strip().startswith("[Seccion")
        print(f"      -> ¿chunk enfocado (empieza con Sintoma/Seccion)? {enfocado}")
except Exception as e:
    print("ERROR leyendo la colección:", e)

# 2) ¿Qué recupera la búsqueda para la query?
print(f"\nbuscar_chunks('{MAQ}', '{QUERY}') ->")
try:
    chunks = buscar_chunks(MAQ, QUERY)
    if not chunks:
        print("  (no recuperó nada)")
    for c in chunks:
        marca = "  <== AQUÍ" if FRASE in c["texto"].upper() else ""
        print(f"  [pag {c['pagina']}] score={round(c.get('score', 0), 3)} :: {c['texto'][:90]}{marca}")
except Exception as e:
    print("ERROR en buscar_chunks:", e)
