@echo off
chcp 65001 >nul
title Big Tools - Generar los .exe
cd /d "%~dp0"

echo ==========================================================
echo   Big Tools - Generar los ejecutables (sin consola)
echo   Genera:  BigTools_Instalar.exe  y  BigTools.exe
echo   (correr en Windows, una sola vez)
echo ==========================================================
echo.

REM --- Verificar Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    pause
    exit /b 1
)

echo [1/3] Instalando PyInstaller (si falta)...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] No se pudo instalar PyInstaller.
    pause
    exit /b 1
)

echo.
echo [2/3] Generando BigTools_Instalar.exe (instalador)...
python -m PyInstaller --noconsole --onefile --name BigTools_Instalar ^
    --icon "docs\assets\logo.ico" ^
    BigTools_Instalar.py

echo.
echo [3/3] Generando BigTools.exe (lanzador)...
python -m PyInstaller --noconsole --onefile --name BigTools ^
    --icon "docs\assets\logo.ico" ^
    BigTools.py

echo.
if exist "dist\BigTools.exe" if exist "dist\BigTools_Instalar.exe" (
    echo ==========================================================
    echo   LISTO. Los ejecutables quedaron en la carpeta  dist\
    echo     - dist\BigTools_Instalar.exe   (instalar, una sola vez)
    echo     - dist\BigTools.exe            (levantar el sistema)
    echo.
    echo   Copia AMBOS a la carpeta del proyecto
    echo   (al lado de Backend\ y requirements.txt).
    echo ==========================================================
) else (
    echo [ERROR] No se generaron los .exe. Revisa los mensajes de arriba.
)
pause
