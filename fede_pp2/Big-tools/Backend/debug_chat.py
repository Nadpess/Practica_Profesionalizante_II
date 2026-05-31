"""
Reproduce EXACTAMENTE lo que hace el chat (consulta libre conversacional):
mismo generador que el endpoint /api/rag/consulta/conversacional.
Muestra las páginas del evento 'meta' (las "fuentes") y la respuesta del LLM.

Uso (desde Backend/, Ollama levantado):
    python debug_chat.py
    python debug_chat.py "Compresor" "el compresor no arranca"
"""
import sys, json
from api.rag.retriever import buscar_chunks, generar_respuesta_stream_conversacional

MAQ   = sys.argv[1] if len(sys.argv) > 1 else "Compresor"
QUERY = sys.argv[2] if len(sys.argv) > 2 else "el compresor no arranca"

# Cross-check: qué páginas trae buscar_chunks directamente
chunks = buscar_chunks(MAQ, QUERY)
print("buscar_chunks ->", [c["pagina"] for c in chunks])

# Ahora el camino REAL del chat (historial vacío = primera consulta)
meta = None
ans  = []
for ev in generar_respuesta_stream_conversacional(MAQ, QUERY, []):
    if not ev.startswith("data: "):
        continue
    try:
        d = json.loads(ev[6:])
    except Exception:
        continue
    t = d.get("tipo")
    if t == "meta":
        meta = d
    elif t == "token":
        ans.append(d.get("texto", ""))
    elif t == "respuesta_completa":
        if not ans:
            ans.append(d.get("texto", ""))

print("\nMETA del chat:")
if meta:
    print("  paginas (fuentes):", meta.get("paginas"))
    print("  confianza:", meta.get("confianza"))
    print("  secciones:", meta.get("secciones"))
    print("  desde_cache:", meta.get("desde_cache", False))
else:
    print("  (no se emitió evento meta)")

print("\nRESPUESTA del LLM:\n", "".join(ans)[:900])
