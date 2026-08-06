@echo off
REM ============================================
REM  SIMUS.MJN - Instalacion del DEMO
REM  Crea el entorno virtual e instala las
REM  dependencias minimas. Luego usa
REM  Iniciar_Demo.bat para arrancar.
REM ============================================
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo [DEMO] El entorno virtual ya existe. Reinstalando dependencias...
    goto instalar
)

echo [DEMO] Buscando Python compatible (3.10 / 3.11 / 3.12)...
set "PY_CMD="
for %%V in (3.12 3.11 3.10) do (
    if not defined PY_CMD (
        py -%%V --version >nul 2>&1 && set "PY_CMD=py -%%V"
    )
)
if not defined PY_CMD (
    py --version >nul 2>&1 && set "PY_CMD=py"
)

if not defined PY_CMD (
    echo [ERROR] No se encontro Python instalado.
    echo         Instala Python 3.10, 3.11 o 3.12 desde:
    echo         https://www.python.org/downloads/
    echo         En el instalador marca "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [DEMO] Creando entorno virtual con %PY_CMD%...
%PY_CMD% -m venv .venv
if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

:instalar
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r requirements_demo.txt

echo.
echo [DEMO] Instalacion completada. Ejecuta Iniciar_Demo.bat para usar el demo.
pause
