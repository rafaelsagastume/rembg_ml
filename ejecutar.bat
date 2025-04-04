@echo off
echo ==================================
echo  Iniciando RemBG - Eliminador de fondos
echo ==================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Ejecutar la aplicación
python gui.py

REM Desactivar entorno virtual al salir
call .venv\Scripts\deactivate.bat