"""
Diagnostico RAG - indices + extraccion de bloques del PDF.
Ejecutar desde la carpeta Backend: python diagnostico_rag.py
"""
import sys, os
sys.path.insert(0, ".")

import chromadb
import fitz

# ── ChromaDB ──────────────────────────────────────────────────────────────────
DB_PATH = "data/vectorstore"
client  = chromadb.PersistentClient(path=DB_PATH)

print("=== Colecciones en el indice ===")
for col in client.list_collections():
    print(f"  • {col.name}  ({col.count()} chunks)")

nombre = input("\nNombre exacto de la coleccion del compresor: ").strip()
col    = client.get_collection(name=nombre)
todos  = col.get(include=["documents", "metadatas"])

paginas_en_indice = sorted({m.get("pagina") for m in todos["metadatas"]})
print(f"\nPaginas en el indice: {paginas_en_indice}")
print(f"Max pagina: {max(paginas_en_indice)}")

# Buscar alrededor de pagina 57 para ver si el contenido de 59 está ahí
print("\n=== Chunks paginas 55-60 en el indice ===")
for doc, meta in zip(todos["documents"], todos["metadatas"]):
    if 55 <= meta.get("pagina", 0) <= 60:
        print(f"  Pag {meta['pagina']} chunk_id={meta.get('chunk_id')}: {repr(doc[:200])}\n")

# ── PDF directo ────────────────────────────────────────────────────────────────
pdf_path = input("\nRuta del PDF del compresor (ej: data/manuales_pdf/compresor.pdf): ").strip()
if not os.path.exists(pdf_path):
    print(f"  No encontrado: {pdf_path}")
    sys.exit(1)

doc = fitz.open(pdf_path)
print(f"\nTotal paginas en el PDF: {doc.page_count}")

print("\n=== Inspeccion paginas 55 a fin del PDF ===")
for num_pag in range(54, min(doc.page_count, doc.page_count)):  # desde 55 (0-indexed=54)
    pagina = doc[num_pag]
    pag_num = num_pag + 1
    bloques_raw = [b for b in pagina.get_text("blocks") if b[6] == 0 and b[4].strip()]
    texto_simple = pagina.get_text("text").strip()

    print(f"\n--- Pagina {pag_num} ---")
    print(f"  Bloques con texto: {len(bloques_raw)}")
    print(f"  Texto plano (primeros 300 chars): {repr(texto_simple[:300])}")

    if bloques_raw:
        n_cortos = sum(1 for b in bloques_raw if len(b[4].split()) < 8)
        tiene_tabla = (n_cortos / max(len(bloques_raw), 1)) > 0.4
        print(f"  Bloques cortos (<8 palabras): {n_cortos}/{len(bloques_raw)}  ->  tiene_tabla={tiene_tabla}")

        # Intentar find_tables
        try:
            tabs = pagina.find_tables()
            print(f"  find_tables(): {len(tabs.tables)} tabla(s) detectada(s)")
            for t in tabs.tables:
                rows = t.extract()
                print(f"    Tabla con {len(rows)} filas:")
                for row in rows[:5]:
                    print(f"      {row}")
        except AttributeError:
            print("  find_tables(): no disponible (PyMuPDF < 1.23)")

doc.close()
print("\nDiagnostico completado.")
