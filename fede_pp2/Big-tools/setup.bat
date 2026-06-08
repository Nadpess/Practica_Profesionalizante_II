@echo off
chcp 65001 >nul
title Big Tools - Instalacion (correr una sola vez)
cd /d "%~dp0"

echo ==========================================================
echo   Big Tools - Instalacion
echo   Requisitos: Python 3.10+ y Ollama instalados
echo   (Python: https://www.python.org/  -  Ollama: https://ollama.com)
echo ==========================================================
echo.

REM --- 1) Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Instalalo desde https://www.python.org/ y marca "Add Python to PATH".
    pause
    exit /b 1
)
echo [OK] Python detectado.

REM --- 2) Verificar Ollama ---
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama no esta instalado.
    echo Instalalo desde https://ollama.com y volve a correr este script.
    pause
    exit /b 1
)
echo [OK] Ollama detectado.
echo.

echo === [1/4] Creando entorno virtual de Python ===
if not exist "venv\Scripts\activate.bat" python -m venv venv
call venv\Scripts\activate.bat

echo.
echo === [2/4] Instalando dependencias de Python ===
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

echo.
echo === [3/4] Descargando modelos de IA (una sola vez, requiere internet) ===
echo  - qwen2.5:3b ........ conversacion / diagnostico en tiempo real
ollama pull qwen2.5:3b
echo  - qwen2.5:7b ........ generacion automatica del arbol de decision
ollama pull qwen2.5:7b
echo  - nomic-embed-text .. embeddings para buscar en los manuales (RAG)
ollama pull nomic-embed-text

echo.
echo === [4/4] Preparando carpetas de datos ===
if not exist "Backend\data\manuales_pdf" mkdir "Backend\data\manuales_pdf"

REM --- Avisar si la carpeta de manuales esta vacia ---
dir /b "Backend\data\manuales_pdf\*.pdf" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO IMPORTANTE] La carpeta Backend\data\manuales_pdf\ esta VACIA.
    echo Los PDF no viajan con el repositorio (estan en .gitignore por su peso).
    echo Copia los manuales en esa carpeta con los nombres EXACTOS que figuran
    echo en Backend\data\manuales.json (por ejemplo: Hidrolavadora_Karcher.pdf).
    echo Sin esos archivos, la indexacion va a decir "archivo no encontrado".
)

echo.
echo ==========================================================
echo   Listo. Para usar el programa ejecuta:  iniciar.bat
echo ==========================================================
pause
