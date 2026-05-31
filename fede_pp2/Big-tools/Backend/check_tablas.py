"""
Diagnostico de extraccion de tablas del indexador (nuevo algoritmo por columnas).

Muestra, pagina por pagina con tabla, las filas que el indexador generaria AHORA,
sin necesidad de reindexar. Sirve para validar antes de reindexar de verdad.

Uso (desde la carpeta Backend/, con el venv activado):
    python check_tablas.py "Compresor.pdf" 55 64
    python check_tablas.py "Compresor.pdf"                 # todas las paginas
    python check_tablas.py "HIDROLAVADORA.pdf" 1 99 "NO ARRANCA"

Args: <archivo.pdf> [pag_ini] [pag_fin] [frase_a_buscar]
"""
import sys
import fitz
from api.rag.indexador import _tiene_tabla, _filas_por_posicion, _es_pagina_averias

PDF_DIR = "data/manuales_pdf"


def main():
    if len(sys.argv) < 2:
        print('Uso: python check_tablas.py "<archivo.pdf>" [pag_ini] [pag_fin] [frase]')
        return
    archivo = sys.argv[1]
    pini  = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    pfin  = int(sys.argv[3]) if len(sys.argv) > 3 else 99999
    frase = (sys.argv[4] if len(sys.argv) > 4 else "EL COMPRESOR NO ARRANCA").upper()

    doc = fitz.open(f"{PDF_DIR}/{archivo}")
    print(f"{archivo}: {doc.page_count} paginas\n")

    hits = []
    for n in range(doc.page_count):
        p = n + 1
        if p < pini or p > pfin:
            continue
        pagina = doc[n]
        raw = [b for b in pagina.get_text("blocks") if b[6] == 0 and b[4].strip()]
        if not _tiene_tabla(pagina, raw):
            continue
        averias = _es_pagina_averias(pagina)
        filas = _filas_por_posicion(pagina)
        print(f"===== PAG {p}  (averias={averias}, {len(filas)} filas) =====")
        for f in filas:
            print("  -", f[:300])
            if frase in f.upper():
                hits.append(p)
        print()

    doc.close()
    print(f">>> '{frase}' aparece en paginas: {sorted(set(hits)) or 'NINGUNA'}")


if __name__ == "__main__":
    main()
