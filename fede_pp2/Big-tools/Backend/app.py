"""Sistema Experto de Diagnóstico - Big Tools"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router
from pathlib import Path
from api.rag.rag_routes import rag_router

app = FastAPI(
    title="Sistema Experto de Diagnóstico de Máquinas Big Tools",
    description="API para diagnosticar fallas en máquinas y ofrecer posibles soluciones",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(router)
app.include_router(rag_router)

# Configurar archivos estáticos del Frontend
frontend_path = Path(__file__).parent.parent / "Frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Configurar archivos PDF
manuales_path = Path(__file__).parent / "data" / "manuales_pdf"
app.mount("/manuales", StaticFiles(directory=str(manuales_path)), name="manuales")

@app.get("/")
def root():
    """Redirige a la página principal del frontend"""
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/admin")
def admin():
    """Página de administración"""
    return FileResponse(str(frontend_path / "admin.html"))

@app.get("/favicon.ico")
def favicon():
    """Sirve el favicon"""
    favicon_path = frontend_path / "assets" / "img" / "logo_bigtools.png"
    return FileResponse(str(favicon_path))