"""
Limpieza: borra los PDFs y las colecciones de ChromaDB que YA NO corresponden a
los manuales actuales (según data/manuales.json). Deja solo lo vigente.

IMPORTANTE: correr con el backend (uvicorn) APAGADO, para que no haya otro
proceso usando la base de ChromaDB.

Uso (desde la carpeta Backend/, con el venv activado):
    python limpiar_colecciones.py
"""
import json
import os
from api.rag import get_cliente_chroma, normalizar_nombre_coleccion

DATA   = "data"
PDFDIR = os.path.join(DATA, "manuales_pdf")

manuales = json.load(open(os.path.join(DATA, "manuales.json"), encoding="utf8"))
nombres  = [m["nombre"] for m in manuales]
archivos = set(m["archivo"] for m in manuales)

# Colecciones válidas = la de cada manual vigente + su caché
validas = set()
for n in nombres:
    c = normalizar_nombre_coleccion(n)
    validas.add(c)
    validas.add("cache__" + c)

print("=== Colecciones ChromaDB ===")
cli = get_cliente_chroma()
for col in cli.list_collections():
    if col.name in validas:
        print("  conservada:", col.name)
    else:
        cli.delete_collection(col.name)
        print("  BORRADA:   ", col.name)

print("\n=== PDFs en manuales_pdf ===")
for f in sorted(os.listdir(PDFDIR)):
    if f in archivos:
        print("  conservado:", f)
    else:
        os.remove(os.path.join(PDFDIR, f))
        print("  BORRADO:   ", f)

print("\nListo. Reinicia uvicorn y reindexá los manuales desde el panel admin.")
