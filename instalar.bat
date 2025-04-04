@echo off
echo ======================================
echo  Instalando RemBG - Eliminador de fondos
echo ======================================
echo.

REM Verificar si Python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no se encuentra en el PATH.
    echo Por favor, instala Python 3.10 o superior desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist .venv (
    echo Creando entorno virtual...
    python -m venv .venv
)

REM Activar entorno virtual
echo Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo ================================================
echo Instalación completada satisfactoriamente!
echo.
echo Ahora puedes ejecutar el programa con ejecutar.bat
echo ================================================
echo.
pause