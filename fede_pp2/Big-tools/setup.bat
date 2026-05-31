@echo off
chcp 65001 >nul
title Big Tools - Instalacion (correr una sola vez)
cd /d "%~dp0"

echo ==========================================================
echo   Big Tools - Instalacion
echo   Requisitos previos: Python 3.10+ y Ollama ya instalados
echo   (Ollama: https://ollama.com)
echo ==========================================================
echo.

echo === [1/3] Creando entorno virtual de Python ===
python -m venv venv
call venv\Scripts\activate.bat

echo === [2/3] Instalando dependencias de Python ===
python -m pip install --upgrade pip
pip install -r requirements.txt

echo === [3/3] Descargando modelos de IA (necesita internet, una sola vez) ===
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

echo.
echo ==========================================================
echo   Listo. Para usar el programa, ejecuta:  iniciar.bat
echo ==========================================================
pause
