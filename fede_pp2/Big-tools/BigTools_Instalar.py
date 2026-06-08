# -*- coding: utf-8 -*-
"""
Big Tools - INSTALADOR con interfaz grafica (sin consola).
Instala TODAS las dependencias:
  - Si falta Python, lo descarga e instala automaticamente (silencioso, por usuario).
  - Crea el entorno virtual e instala las dependencias de Python.
  - Descarga los 3 modelos de IA (conversacion, arbol, embeddings).
Ollama NO se instala desde aca: si falta, avisa con el link.
Bandera: si ya esta todo instalado, no vuelve a descargar.
Se empaqueta con build_exe.bat (PyInstaller --noconsole).
"""
import os, sys, time, glob, tempfile, threading, subprocess, urllib.request
import tkinter as tk
from tkinter import ttk

def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE     = base_dir()
REQS     = os.path.join(BASE, "requirements.txt")
VENV_PY  = os.path.join(BASE, "venv", "Scripts", "python.exe")
MANUALES = os.path.join(BASE, "Backend", "data", "manuales_pdf")
FLAG     = os.path.join(BASE, "Backend", "data", ".setup_ok")
FLAG_VER = "v4.0"
MODELOS  = [("qwen2.5:3b", "conversación / diagnóstico"),
            ("qwen2.5:7b", "generación del árbol"),
            ("nomic-embed-text", "embeddings (RAG)")]
PY_URL   = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

IS_WIN    = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          creationflags=NO_WINDOW)


def existe(cmd):
    try:
        subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW)
        return True
    except Exception:
        return False


def find_python():
    cands = ["python"]
    la = os.environ.get("LOCALAPPDATA", "")
    pf = os.environ.get("ProgramFiles", "")
    pf86 = os.environ.get("ProgramFiles(x86)", "")
    for root in [os.path.join(la, "Programs", "Python"), pf, pf86]:
        if root:
            cands += glob.glob(os.path.join(root, "Python3*", "python.exe"))
    for c in cands:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, creationflags=NO_WINDOW)
            if r.returncode == 0:
                return c
        except Exception:
            pass
    return None


def ya_instalado():
    if not os.path.exists(VENV_PY):
        return False
    try:
        with open(FLAG, "r", encoding="utf-8") as f:
            return f.read().strip() == FLAG_VER
    except Exception:
        return False


def marcar_ok():
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    with open(FLAG, "w", encoding="utf-8") as f:
        f.write(FLAG_VER)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Big Tools - Instalador")
        root.geometry("500x320"); root.resizable(False, False); root.configure(bg="#ffffff")

        tk.Label(root, text="Big Tools", font=("Segoe UI Semibold", 22),
                 fg="#c62828", bg="#ffffff").pack(pady=(24, 0))
        tk.Label(root, text="Instalador", font=("Segoe UI", 11),
                 fg="#6a6a70", bg="#ffffff").pack(pady=(0, 16))

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
        self.bar = ttk.Progressbar(root, length=400, mode="determinate",
                                   maximum=100, style="BT.Horizontal.TProgressbar")
        self.bar.pack(pady=(0, 6))
        self.detalle = tk.Label(root, text="", font=("Segoe UI", 9),
                                fg="#8a8a90", bg="#ffffff", wraplength=440, justify="center")
        self.detalle.pack()

        self.boton = tk.Button(root, text="Cerrar", command=root.destroy, relief="flat",
                               bg="#f0eeee", fg="#1b1b1d", activebackground="#e3e0e0",
                               padx=18, pady=4, font=("Segoe UI", 9))
        self.boton.pack(side="bottom", pady=14)

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
        # Si ya esta todo, no repetir
        if ya_instalado():
            self.set(100, "Ya está todo instalado ✓",
                     "Podés abrir BigTools.exe para usar el sistema.", color="#1d9e75")
            return

        # 1) Python (instalar si falta)
        self.set(5, "Verificando Python…")
        py = find_python()
        if not py:
            self.set(10, "Descargando Python…", "No estaba instalado. Bajando el instalador oficial.")
            self.busy(True)
            try:
                dest = os.path.join(tempfile.gettempdir(), "python-3.11.9-amd64.exe")
                urllib.request.urlretrieve(PY_URL, dest)
                self.set(15, "Instalando Python…", "Instalación silenciosa (por usuario).")
                subprocess.run([dest, "/quiet", "InstallAllUsers=0", "PrependPath=1",
                                "Include_pip=1", "Include_test=0"], creationflags=NO_WINDOW)
                time.sleep(5)
                py = find_python()
            except Exception as e:
                self.busy(False)
                self.error("No se pudo instalar Python", str(e)[:200] +
                           "  ·  Instalalo a mano desde python.org y reintentá.")
                return
            self.busy(False)
            if not py:
                self.error("Python instalado pero no detectado",
                           "Reiniciá la PC y volvé a abrir el instalador.")
                return
        self.set(25, "Python listo ✓")

        # 2) Ollama (no se instala desde aca)
        self.set(28, "Verificando Ollama…")
        if not existe(["ollama", "--version"]):
            self.error("Falta Ollama",
                       "Instalá Ollama desde ollama.com, dejalo abierto y reintentá. "
                       "(Es el único componente que se instala por separado.)")
            return

        # 3) Entorno virtual
        self.set(35, "Creando entorno…", "Puede tardar un momento.")
        self.busy(True)
        run([py, "-m", "venv", "venv"], cwd=BASE)
        self.busy(False)
        if not os.path.exists(VENV_PY):
            self.error("No se pudo crear el entorno virtual")
            return

        # 4) Dependencias
        self.set(45, "Instalando dependencias…", "Descargando paquetes de Python.")
        self.busy(True)
        run([VENV_PY, "-m", "pip", "install", "--upgrade", "pip"], cwd=BASE)
        r = run([VENV_PY, "-m", "pip", "install", "-r", REQS], cwd=BASE)
        self.busy(False)
        if r and r.returncode != 0:
            self.error("Error instalando dependencias", (r.stderr or "")[-220:])
            return

        # 5) Modelos de IA
        for i, (m, etq) in enumerate(MODELOS):
            self.set(60 + i * 10, "Descargando modelos de IA…",
                     f"{m}  ({etq}) — puede tardar varios minutos.")
            self.busy(True)
            run(["ollama", "pull", m])
            self.busy(False)

        # 6) Carpetas + bandera
        os.makedirs(MANUALES, exist_ok=True)
        marcar_ok()
        self.set(100, "¡Instalación completa! ✓",
                 "Ya podés abrir BigTools.exe para usar el sistema.", color="#1d9e75")


if __name__ == "__main__":
    root = tk.Tk(); App(root); root.mainloop()
