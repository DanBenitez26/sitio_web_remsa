@echo off
title REMSA Plásticos - Django

cd /d "%~dp0"

echo ==========================================
echo       REMSA PLASTICOS
echo       Servidor Django
echo ==========================================
echo.
echo Python:
".venv\Scripts\python.exe" --version
echo.
echo Servidor:
echo http://127.0.0.1:8000
echo.
echo Iniciando...
echo.

start "" http://127.0.0.1:8000

".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

pause