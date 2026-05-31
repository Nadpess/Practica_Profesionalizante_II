@echo off
chcp 65001 >nul
title Big Tools
cd /d "%~dp0Backend"

REM --- Activar el entorno virtual si existe (probamos ubicaciones comunes) ---
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist "..\venv\Scripts\activate.bat" (
    call "..\venv\Scripts\activate.bat"
) else if exist "api\venv\Scripts\activate.bat" (
    call "api\venv\Scripts\activate.bat"
)

REM --- Precargar el modelo en la GPU para que la 1ra consulta sea rapida ---
echo Precargando el modelo de IA...
start "" /b cmd /c "ollama run qwen2.5:3b ok >nul 2>&1"

REM --- Abrir el navegador unos segundos despues (cuando el server este listo) ---
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000"

REM --- Iniciar el backend ---
echo.
echo  Big Tools iniciando en http://127.0.0.1:8000
echo  (cerra esta ventana o Ctrl+C para apagar)
echo.
python -m uvicorn app:app --port 8000

pause
