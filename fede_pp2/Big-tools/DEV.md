# Cómo correr Big Tools (desarrollo)

## Requisitos previos
- Python 3.9+
- [Ollama](https://ollama.com) instalado y corriendo
- Modelos descargados:
  ```
  ollama pull llama3.2:3b
  ollama pull nomic-embed-text
  ```

## Primera vez

```bash
cd Backend
pip install -r ../requirements.txt
```

## Correr el servidor

```bash
cd Backend
uvicorn app:app --reload
```

Abre en el navegador: http://localhost:8000

## Credenciales por defecto

| Usuario | Contraseña | Rol   |
|---------|-----------|-------|
| admin   | admin123  | admin |
| tecnico | tecnico123| user  |

## Indexar manuales

1. Entrá como admin → Panel de administración → tab RAG
2. Subí el PDF con el nombre de la máquina
3. Hacé click en "Indexar"
4. Esperá que llegue al 100% (puede tardar varios minutos)

> **Importante:** hay que re-indexar cada vez que se actualice el indexador.
> El vectorstore (ChromaDB) se genera localmente y no se sube al repo.

## Estructura del proyecto

```
Backend/
  app.py              ← entry point
  api/
    routes.py         ← endpoints SE clásico + feedback + SE dinámico
    rag/
      __init__.py     ← cliente ChromaDB + detección de idioma
      indexador.py    ← extracción PDF + chunking + embeddings
      retriever.py    ← búsqueda semántica + prompts + traducción
      rag_routes.py   ← endpoints RAG (stream, sesión, indexación)
      cache.py        ← cache semántico de respuestas
      se_dinamico.py  ← SE guiado por RAG (manuales sin árbol estático)
      sesiones.py     ← historial conversacional por sesión
Frontend/
  index.html          ← app principal
  css/style.css
  js/main.js
```
