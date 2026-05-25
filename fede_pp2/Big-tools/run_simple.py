"""
run_simple.py
Script Python para iniciar el backend y abrir el frontend automáticamente.
Funciona en Windows, Linux y Mac.
"""

import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def print_banner():
    """Muestra el banner de inicio."""
    print("=" * 50)
    print("    Big Tools - Sistema Experto")
    print("=" * 50)
    print()

def check_python():
    """Verifica que Python esté instalado."""
    print("[1/4] Verificando Python...")
    print(f"✓ Python {sys.version.split()[0]} detectado")
    print()

def install_dependencies():
    """Instala las dependencias necesarias."""
    print("[2/4] Verificando dependencias...")
    try:
        import fastapi
        import uvicorn
        print("✓ Dependencias verificadas correctamente")
    except ImportError:
        print("⚠ Instalando dependencias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencias instaladas")
    print()

def start_backend():
    """Inicia el servidor backend."""
    print("[3/4] Iniciando Backend (FastAPI)...")
    print("Backend ejecutándose en: http://127.0.0.1:8000")
    print()
    
    # Cambiar al directorio Backend
    backend_path = Path(__file__).parent / "Backend"
    
    # Iniciar uvicorn usando python -m
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(backend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    return process

def open_frontend():
    """Abre el frontend en el navegador."""
    print("[4/4] Abriendo Frontend en el navegador...")
    print()
    
    # Esperar 3 segundos para que el backend inicie completamente
    time.sleep(3)
    
    # Ruta al archivo index.html
    # Abrir en el navegador usando el servidor FastAPI
    webbrowser.open("http://127.0.0.1:8000/")
    
    print("=" * 50)
    print("  Sistema iniciado correctamente!")
    print("=" * 50)
    print()
    print("  - Backend (API): http://127.0.0.1:8000")
    print("  - Frontend (Chatbot): Frontend/index.html")
    print("  - Dashboard Admin: Frontend/admin.html")
    print()
    print("  Credenciales de Admin:")
    print("    Usuario: admin")
    print("    Contraseña: 1234")
    print()
    print("=" * 50)
    print()
    print("Presiona Ctrl+C para detener el sistema...")
    print()

def main():
    """Función principal."""
    try:
        print_banner()
        check_python()
        install_dependencies()
        
        # Iniciar backend
        backend_process = start_backend()
        
        # Abrir frontend
        open_frontend()
        
        # Mantener el script corriendo
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n\n⚠ Deteniendo el sistema...")
            backend_process.terminate()
            backend_process.wait()
            print("✓ Sistema detenido correctamente.")
            print()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPor favor, verifica que todas las dependencias estén instaladas:")
        print("  pip install -r requirements.txt")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()

