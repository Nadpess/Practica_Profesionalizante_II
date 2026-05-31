"""
Chequea el CACHE semántico (lo que el chat consulta ANTES de buscar en el manual).

Uso (desde Backend/, Ollama levantado):
    python debug_cache.py                         # ver si hay hit de cache
    python debug_cache.py Compresor "el compresor no arranca"
    python debug_cache.py Compresor "el compresor no arranca" --clear   # borrar ese cache
"""
import sys
from api.rag.cache import buscar_en_cache, _nombre_coleccion_cache
from api.rag import get_cliente_chroma

args  = [a for a in sys.argv[1:] if a != "--clear"]
clear = "--clear" in sys.argv
MAQ   = args[0] if len(args) > 0 else "Compresor"
QUERY = args[1] if len(args) > 1 else "el compresor no arranca"

cli  = get_cliente_chroma()
name = _nombre_coleccion_cache(MAQ)

try:
    c = cli.get_collection(name)
    print(f"Cache '{name}': {c.count()} entradas")
except Exception:
    print(f"Cache '{name}': NO existe (vacío) -> el chat haría RAG normal (bien)")

hit = buscar_en_cache(MAQ, QUERY)
if hit:
    print("\n>>> EL CHAT TE SERVIRÍA ESTO DEL CACHE (sin volver a buscar en el manual):")
    print("    páginas:", hit.get("paginas"))
    print("    distancia:", hit.get("distancia"))
    print("    respuesta:", repr(hit["respuesta"][:300]))
    print("\n    >> Si esta respuesta es la vieja/incompleta, ESE es el problema.")
    print("    >> Borralo con:  python debug_cache.py", f'"{MAQ}" "{QUERY}" --clear')
else:
    print("\n>>> No hay hit de cache -> el chat NO usa cache para esta query.")
    print("    (Si igual falla, el problema sería el LLM, no el cache.)")

if clear:
    try:
        cli.delete_collection(name)
        print(f"\n[OK] Cache '{name}' borrado por completo. Probá el chat de nuevo.")
    except Exception as e:
        print("\n[error] no se pudo borrar:", e)
