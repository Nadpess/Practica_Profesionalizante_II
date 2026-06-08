# -*- coding: utf-8 -*-
"""
Big Tools - LANZADOR con interfaz grafica (sin consola).
Levanta el servidor y abre el navegador. NO descarga nada.
Si falta la instalacion, avisa que se corra primero BigTools_Instalar.exe.
Se empaqueta con build_exe.bat (PyInstaller --noconsole).
"""
import os, sys, time, threading, subprocess, urllib.request
import tkinter as tk
from tkinter import ttk


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE     = base_dir()
BACKEND  = os.path.join(BASE, "Backend")
VENV_PY  = os.path.join(BASE, "venv", "Scripts", "python.exe")
MANUALES = os.path.join(BACKEND, "data", "manuales_pdf")
FLAG     = os.path.join(BASE, "Backend", "data", ".setup_ok")
URL      = "http://127.0.0.1:8000"

IS_WIN    = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0
server_proc = None


def instalado():
    return os.path.exists(VENV_PY) and os.path.exists(FLAG)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Big Tools")
        root.geometry("480x300"); root.resizable(False, False); root.configure(bg="#ffffff")

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
                                fg="#8a8a90", bg="#ffffff", wraplength=420, justify="center")
        self.detalle.pack()

        self.boton = tk.Button(root, text="Cerrar", command=self.cerrar, relief="flat",
                               bg="#f0eeee", fg="#1b1b1d", activebackground="#e3e0e0",
                               padx=18, pady=4, font=("Segoe UI", 9))
        self.boton.pack(side="bottom", pady=14)

        root.protocol("WM_DELETE_WINDOW", self.cerrar)
        threading.Thread(target=self.trabajo, daemon=True).start()

    def ui(self, fn): self.root.after(0, fn)

    def set(self, pct, estado=None, detalle=None, color="#1b1b1d"):
        def _():
            self.bar["value"] = pct
            if estado is not None: self.estado.config(text=estado, fg=color)
            if detalle is not None: self.detalle.config(text=detalle)
        self.ui(_)

    def busy(self, on):
        def _():
            if on: self.bar.config(mode="indeterminate"); self.bar.start(14)
            else: self.bar.stop(); self.bar.config(mode="determinate")
        self.ui(_)

    def error(self, titulo, detalle=""):
        self.busy(False); self.set(0, titulo, detalle, color="#c62828")

    def trabajo(self):
        # Verificar instalacion
        self.set(10, "Verificando instalación…")
        if not instalado():
            self.error("Falta instalar",
                       "Abrí primero BigTools_Instalar.exe (una sola vez) y después usá BigTools.exe.")
            return

        # Asegurar carpeta de manuales y avisar si esta vacia
        os.makedirs(MANUALES, exist_ok=True)
        try:
            hay_pdf = any(f.lower().endswith(".pdf") for f in os.listdir(MANUALES))
        except Exception:
            hay_pdf = False

        # Precargar modelo de runtime
        self.set(30, "Preparando el modelo de IA…")
        try:
            subprocess.Popen(["ollama", "run", "qwen2.5:3b", "ok"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=NO_WINDOW)
        except Exception:
            pass

        # Iniciar el servidor
        self.set(55, "Iniciando el servidor…")
        global server_proc
        try:
            server_proc = subprocess.Popen(
                [VENV_PY, "-m", "uvicorn", "app:app", "--port", "8000"],
                cwd=BACKEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW)
        except Exception as e:
            self.error("No se pudo iniciar el servidor", str(e)[:200])
            return

        # Esperar a que responda
        self.set(75, "Esperando el servidor…")
        ok = False
        for _ in range(40):
            try:
                urllib.request.urlopen(URL, timeout=1); ok = True; break
            except Exception:
                if server_proc.poll() is not None:
                    break
                time.sleep(1)
        if not ok:
            self.error("El servidor no respondió", "Revisá que Ollama esté abierto y reintentá.")
            return

        try:
            import webbrowser; webbrowser.open(URL)
        except Exception:
            pass

        aviso = "" if hay_pdf else ("  ·  Aviso: no hay PDFs en Backend\\data\\manuales_pdf\\, "
                                    "la indexación no encontrará manuales.")
        self.set(100, "¡Listo! Big Tools está corriendo ✓",
                 "Se abrió en el navegador. Podés minimizar esta ventana; "
                 "cerrala para detener el sistema." + aviso, color="#1d9e75")

    def cerrar(self):
        global server_proc
        try:
            if server_proc and server_proc.poll() is None:
                server_proc.terminate()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()
