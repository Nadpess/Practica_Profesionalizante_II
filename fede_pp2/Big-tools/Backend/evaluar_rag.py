# -*- coding: utf-8 -*-
"""
Evaluación OFFLINE del RAG — mide el rendimiento de la recuperación.

Métricas que reporta:
  - hit-rate@k : % de casos donde la página esperada quedó entre los fragmentos recuperados.
  - distancia  : qué tan cerca (coseno, 0 = idéntico) está el mejor fragmento recuperado.
  - confianza  : el % de confianza que calcula el sistema (1 - distancia).
  - cobertura  : % de casos en los que el sistema encontró contexto (no respondió "no figura").

Cómo usar (con el entorno y Ollama activos, desde la carpeta Backend/):
    python evaluar_rag.py

Editá data/eval_rag.json con tus casos de prueba. Cada caso:
    {"maquina": "Compresor Sullair", "pregunta": "el compresor no arranca", "paginas_esperadas": [12, 31]}
Si dejás "paginas_esperadas": [] no se mide hit-rate de ese caso (solo distancia y cobertura).
Los manuales tienen que estar indexados.
"""
import json
from pathlib import Path

from api.rag.retriever import buscar_chunks, calcular_confianza

SET = Path(__file__).parent / "data" / "eval_rag.json"


def main():
    if not SET.exists():
        print(f"No existe el set de prueba: {SET}")
        return
    casos = json.loads(SET.read_text(encoding="utf-8"))
    if not casos:
        print("El set de prueba está vacío. Cargá casos en data/eval_rag.json.")
        return

    print("=" * 78)
    print(" EVALUACIÓN RAG — Big Tools")
    print("=" * 78)

    hits = 0
    con_esperadas = 0
    con_contexto = 0
    dists = []
    confs = []

    for caso in casos:
        maquina = caso.get("maquina", "")
        pregunta = caso.get("pregunta", "")
        esperadas = caso.get("paginas_esperadas", []) or []

        chunks = buscar_chunks(maquina, pregunta)
        pags = sorted({c["pagina"] for c in chunks})
        best = min((c["score"] for c in chunks), default=None)
        conf = calcular_confianza(chunks)
        respondio = len(chunks) > 0

        if respondio:
            con_contexto += 1
            dists.append(best)
            confs.append(conf)

        hit = None
        if esperadas:
            con_esperadas += 1
            hit = any(p in pags for p in esperadas)
            if hit:
                hits += 1

        marca = "—" if hit is None else ("OK " if hit else "NO ")
        best_str = f"{best:.3f}" if best is not None else "  -  "
        print(f"\n[{marca}] {maquina}  ·  \"{pregunta}\"")
        print(f"      páginas recuperadas: {pags or '(ninguna)'}"
              + (f"  ·  esperadas: {esperadas}" if esperadas else ""))
        print(f"      distancia mejor fragmento: {best_str}  ·  confianza: {conf}%")

    print("\n" + "=" * 78)
    print(" RESUMEN")
    print("=" * 78)
    print(f"  Casos evaluados:            {len(casos)}")
    if con_esperadas:
        print(f"  hit-rate@k (página correcta): {hits}/{con_esperadas} = {100*hits/con_esperadas:.0f}%")
    else:
        print("  hit-rate@k: (cargá 'paginas_esperadas' en los casos para medirlo)")
    print(f"  Cobertura (encontró contexto): {con_contexto}/{len(casos)} = {100*con_contexto/len(casos):.0f}%")
    if dists:
        print(f"  Distancia promedio (mejor fragmento): {sum(dists)/len(dists):.3f}  (más bajo = mejor)")
        print(f"  Confianza promedio:                   {sum(confs)/len(confs):.0f}%")
    print("=" * 78)


if __name__ == "__main__":
    main()
