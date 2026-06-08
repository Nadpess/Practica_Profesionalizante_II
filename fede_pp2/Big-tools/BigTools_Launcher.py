# -*- coding: utf-8 -*-
"""
Big Tools - Lanzador con interfaz grafica (sin consola).
- Muestra una ventana con barra de progreso y mensajes.
- Bandera de instalacion: si ya esta todo, NO vuelve a descargar.
- Verifica Python y Ollama, crea el entorno, instala dependencias,
  descarga los modelos, levanta el servidor y abre el navegador.
Se empaqueta como .exe con build_exe.bat (PyInstaller --noconsole).
"""
import os
import sys
import time
import threading
import subprocess
import urllib.request
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------- rutas
def base_dir():
    # Carpeta donde esta el .exe (o el .py si se corre suelto)
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE       = base_dir()
BACKEND    = os.path.join(BASE, "Backend")
REQS       = os.path.join(BASE, "requirements.txt")
VENV_PY    = os.path.join(BASE, "venv", "Scripts", "python.exe")  # Windows
MANUALES   = os.path.join(BACKEND, "data", "manuales_pdf")
FLAG       = os.path.join(BASE, "Backend", "data", ".setup_ok")   # bandera
FLAG_VER   = "v4.0"   # si cambia, fuerza reinstalacion
MODELOS    = ["qwen2.5:3b", "qwen2.5:7b", "nomic-embed-text"]
URL        = "http://127.0.0.1:8000"

IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0   # CREATE_NO_WINDOW

server_proc = None


def run(cmd, cwd=None):
    """Ejecuta un comando ocultando cualquier ventana de consola."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          creationflags=NO_WINDOW)


def existe(cmd):
    try:
        subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW)
        return True
    except Exception:
        return False


def ya_instalado():
    if not os.path.exists(VENV_PY):
        return False
    try:
        with open(FLAG, "r", encoding="utf-8") as f:
            return f.read().strip() == FLAG_VER
    except Exception:
        return False


def marcar_instalado():
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    with open(FLAG, "w", encoding="utf-8") as f:
        f.write(FLAG_VER)


# ---------------------------------------------------------------- GUI
class App:
    def __init__(self, root):
        self.root = root
        root.title("Big Tools")
        root.geometry("480x300")
        root.resizable(False, False)
        root.configure(bg="#ffffff")

        tk.Label(root, text="Big Tools", font=("Segoe UI Semibold", 22),
                 fg="#c62828", bg="#ffffff").pack(pady=(26, 0))
        tk.Label(root, text="Asistente de Diagnóstico Técnico", font=("Segoe UI", 10),
                 fg="#6a6a70", bg="#ffffff").pack(pady=(0, 18))

        self.estado = tk.Label(root, text="Iniciando…", font=("Segoe UI", 11),
                               fg="#1b1b1d", bg="#ffffff")
        self.estado.pack(pady=(4, 8))

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
            style.configure("BT.Horizontal.TProgressbar", troughcolor="#f0eeee",
                            background="#c62828", bordercolor="#f0eeee",
                            lightcolor="#c62828", darkcolor="#c62828")
        except Exception:
            pass
        self.bar = ttk.Progressbar(root, length=380, mode="determinate",
                                   maximum=100, style="BT.Horizontal.TProgressbar")
        self.bar.pack(pady=(0, 6))

        self.detalle = tk.Label(root, text="", font=("Segoe UI", 9),
                                fg="#8a8a90", bg="#ffffff", wraplength=420)
        self.detalle.pack()

        self.boton = tk.Button(root, text="Cerrar", command=self.cerrar,
                               relief="flat", bg="#f0eeee", fg="#1b1b1d",
                               activebackground="#e3e0e0", padx=18, pady=4,
                               font=("Segoe UI", 9))
        self.boton.pack(side="bottom", pady=14)

        root.protocol("WM_DELETE_WINDOW", self.cerrar)
        threading.Thread(target=self.trabajo, daemon=True).start()

    # --- helpers de UI (thread-safe) ---
    def ui(self, fn):
        self.root.after(0, fn)

    def set(self, pct, estado=None, detalle=None, color="#1b1b1d"):
        def _():
            self.bar["value"] = pct
            if estado is not None:
                self.estado.config(text=estado, fg=color)
            if detalle is not None:
                self.detalle.config(text=detalle)
        self.ui(_)

    def busy(self, on):
        def _():
            if on:
                self.bar.config(mode="indeterminate"); self.bar.start(14)
            else:
                self.bar.stop(); self.bar.config(mode="determinate")
        self.ui(_)

    def error(self, titulo, detalle=""):
        self.busy(False)
        self.set(0, titulo, detalle, color="#c62828")

    # --- flujo principal ---
    def trabajo(self):
        # 1) Python
        self.set(5, "Verificando Python…")
        if not existe(["python", "--version"]) and not os.path.exists(VENV_PY):
            self.error("Falta Python", "Instalá Python 3.10+ desde python.org "
                       "(marcá 'Add Python to PATH') y volvé a abrir.")
            return

        # 2) Ollama
        self.set(10, "Verificando Ollama…")
        if not existe(["ollama", "--version"]):
            self.error("Falta Ollama", "Instalá Ollama desde ollama.com y volvé a abrir.")
            return

        # 3) Instalacion (solo si la bandera no esta puesta)
        if ya_instalado():
            self.set(80, "Ya está todo instalado ✓", "Saltando la descarga.")
        else:
            self.set(20, "Creando entorno…", "Primera vez: puede tardar unos minutos.")
            self.busy(True)
            r = run(["python", "-m", "venv", "venv"], cwd=BASE)
            self.busy(False)
            if not os.path.exists(VENV_PY):
                self.error("No se pudo crear el entorno", r.stderr[-300:] if r else "")
                return

            self.set(40, "Instalando dependencias…", "Descargando paquetes de Python.")
            self.busy(True)
            run([VENV_PY, "-m", "pip", "install", "--upgrade", "pip"], cwd=BASE)
            r = run([VENV_PY, "-m", "pip", "install", "-r", REQS], cwd=BASE)
            self.busy(False)
            if r and r.returncode != 0:
                self.error("Error instalando dependencias", (r.stderr or "")[-300:])
                return

            etiquetas = {"qwen2.5:3b": "modelo de conversación",
                         "qwen2.5:7b": "modelo de generación de árbol",
                         "nomic-embed-text": "modelo de embeddings (RAG)"}
            base_pct = 55
            for i, m in enumerate(MODELOS):
                self.set(base_pct + i * 8, "Descargando modelos de IA…",
                         f"{m}  ({etiquetas[m]}) — puede tardar.")
                self.busy(True)
                run(["ollama", "pull", m])
                self.busy(False)

            marcar_instalado()
            self.set(80, "Instalación completa ✓")

        # 4) Carpeta de manuales
        os.makedirs(MANUALES, exist_ok=True)

        # 5) Precargar el modelo de runtime (1ra consulta mas rapida)
        self.set(85, "Preparando el modelo de IA…")
        try:
            subprocess.Popen(["ollama", "run", "qwen2.5:3b", "ok"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=NO_WINDOW)
        except Exception:
            pass

        # 6) Iniciar el servidor
        self.set(90, "Iniciando el servidor…")
        global server_proc
        py = VENV_PY if os.path.exists(VENV_PY) else "python"
        try:
            server_proc = subprocess.Popen(
                [py, "-m", "uvicorn", "app:app", "--port", "8000"],
                cwd=BACKEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW)
        except Exception as e:
            self.error("No se pudo iniciar el servidor", str(e))
            return

        # 7) Esperar a que responda y abrir el navegador
        self.set(95, "Esperando el servidor…")
        ok = False
        for _ in range(40):  # ~40 s
            try:
                urllib.request.urlopen(URL, timeout=1)
                ok = True
                break
            except Exception:
                if server_proc.poll() is not None:
                    break
                time.sleep(1)

        if not ok:
            self.error("El servidor no respondió", "Revisá que Ollama esté activo y reintentá.")
            return

        try:
            import webbrowser
            webbrowser.open(URL)
        except Exception:
            pass

        self.set(100, "¡Listo! Big Tools está corriendo ✓",
                 "Se abrió en el navegador. Podés minimizar esta ventana.\n"
                 "Cerrala para detener el sistema.", color="#1d9e75")

    def cerrar(self):
        global server_proc
        try:
            if server_proc and server_proc.poll() is None:
                server_proc.terminate()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
