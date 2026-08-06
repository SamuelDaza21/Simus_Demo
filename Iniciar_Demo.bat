@echo off
REM ============================================
REM  SIMUS.MJN - DEMO (sin BD, sin licencia)
REM  Doble clic para iniciar. Usa la webcam.
REM ============================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [DEMO] No hay entorno virtual. Creandolo e instalando dependencias...
    echo [DEMO] Esto puede tardar unos minutos la primera vez.
    call Instalar_Demo.bat
)

echo [DEMO] Iniciando SIMUS.MJN...
.venv\Scripts\python src\Demo.py

echo.
echo [DEMO] El programa termino.
pause
