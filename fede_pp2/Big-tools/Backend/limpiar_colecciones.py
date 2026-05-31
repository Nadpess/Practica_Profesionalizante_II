"""
Limpieza de manuales/colecciones de PRUEBA (aprobado por Fede, 2026-05-28).

Elimina:
  - Colecciones ChromaDB: prueba_comp, compresor_de_prueba (+ sus caches).
  - El PDF Prueba_Comp.pdf.
  - La entrada "Prueba Comp" en manuales.json.
NO toca el manual real "Compresor".

Uso (desde la carpeta Backend/, con el venv activado):
    python limpiar_colecciones.py
"""
import json
import os
from api.rag import get_cliente_chroma

COLS_BORRAR = [
    "prueba_comp", "compresor_de_prueba",
    "cache__prueba_comp", "cache__compresor_de_prueba",
]
MANUALES_BORRAR = ["Prueba Comp"]
PDF_DIR       = "data/manuales_pdf"
MANUALES_JSON = "data/manuales.json"


def main():
    cli = get_cliente_chroma()
    existentes = {c.name for c in cli.list_collections()}
    for c in COLS_BORRAR:
        if c in existentes:
            cli.delete_collection(c)
            print(f"[chroma] borrada coleccion: {c}")
        else:
            print(f"[chroma] no existe (ok): {c}")

    with open(MANUALES_JSON, encoding="utf-8") as f:
        manuales = json.load(f)

    quedan = []
    for m in manuales:
        if m["nombre"] in MANUALES_BORRAR:
            ruta = os.path.join(PDF_DIR, m["archivo"])
            if os.path.exists(ruta):
                os.remove(ruta)
                print(f"[pdf] borrado: {m['archivo']}")
            print(f"[manuales.json] quitado: {m['nombre']}")
        else:
            quedan.append(m)

    with open(MANUALES_JSON, "w", encoding="utf-8") as f:
        json.dump(quedan, f, ensure_ascii=False, indent=2)

    print("Listo. Reinicia el backend para recargar la lista de maquinas.")


if __name__ == "__main__":
    main()
