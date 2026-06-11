@echo off
chcp 65001 >nul
title Big Tools
cd /d "%~dp0"

REM --- Verificar que se haya corrido la instalacion (setup.bat) ---
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual.
    echo Corre primero  setup.bat  (instalacion, una sola vez).
    pause
    exit /b 1
)
call "venv\Scripts\activate.bat"

REM --- Verificar Ollama ---
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama no esta instalado. Instalalo desde https://ollama.com
    pause
    exit /b 1
)

REM --- Asegurar carpeta de manuales y avisar si esta vacia ---
if not exist "Backend\data\manuales_pdf" mkdir "Backend\data\manuales_pdf"
dir /b "Backend\data\manuales_pdf\*.pdf" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] La carpeta Backend\data\manuales_pdf\ esta vacia.
    echo La indexacion no encontrara manuales hasta que copies los PDF ahi
    echo con los nombres que figuran en Backend\data\manuales.json
    echo.
)

REM --- Precargar el modelo en la GPU para que la 1ra consulta sea rapida ---
echo Precargando el modelo de IA...
start "" /b cmd /c "ollama run llama3.2:3b ok >nul 2>&1"

REM --- Abrir el navegador cuando el server este listo ---
start "" cmd /c "timeout /t 6 >nul & start http://127.0.0.1:8000"

REM --- Iniciar el backend ---
echo.
echo  Big Tools iniciando en http://127.0.0.1:8000
echo  (cerra esta ventana o Ctrl+C para apagar)
echo.
cd Backend
python -m uvicorn app:app --port 8000

pause
