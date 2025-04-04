@echo off
REM Este archivo permite ejecutar la aplicación sin mostrar la ventana de comandos
REM Es ideal para crear un acceso directo en el escritorio

start "" /min cmd /c "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python gui.py && call .venv\Scripts\deactivate.bat"