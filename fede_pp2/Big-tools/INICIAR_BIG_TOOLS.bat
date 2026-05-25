@echo off
setlocal enabledelayedexpansion
title Big Tools - Sistema Experto
cd /d "%~dp0"

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado
    echo Instala Python desde: https://www.python.org/
    echo Durante la instalación, marca "Add Python to PATH"
    pause
    exit /b 1
)

:: Verificar e instalar dependencias
echo Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

:: Obtener IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP:~1!
    goto :found_ip
)
:found_ip

:: Iniciar servidor
echo.
echo Iniciando servidor...
start /min "Big Tools - Servidor" cmd /k "cd /d %~dp0Backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000"

:: Esperar inicio
echo Esperando inicio del servidor...
timeout /t 8 /nobreak >nul

:: Mostrar información
echo.
echo ========================================
echo    Sistema Big Tools - Activo
echo ========================================
echo URL Local: http://127.0.0.1:8000
if defined LOCAL_IP echo URL Red:   http://%LOCAL_IP%:8000
echo.
echo Credenciales: admin / 1234
echo ========================================
echo.

:: Abrir navegador
start "" "http://127.0.0.1:8000"

echo Sistema iniciado correctamente!
echo.
echo IMPORTANTE: No cierres esta ventana mientras uses el sistema.
echo Para detener el servidor, cierra esta ventana.
echo.
pause

:: Detener servidor al cerrar
taskkill /FI "WINDOWTITLE eq Big Tools - Servidor*" /T /F >nul 2>&1
for /f "tokens=2" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

