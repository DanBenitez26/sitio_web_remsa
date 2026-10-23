@echo off
REM Exporta la BD local (db.sqlite3) a un fixture limpio en UTF-8 para Render.
REM Se usa -o (no ">") para evitar el UTF-16/BOM de PowerShell que corrompe acentos.
cd /d "%~dp0"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
set DJANGO_ENV=dev
python -Xutf8 manage.py dumpdata --natural-foreign --natural-primary --indent 2 ^
  -e contenttypes -e auth.permission -e admin.logentry -e sessions ^
  -o fixtures\datos_render.json
echo.
echo Listo: fixtures\datos_render.json
pause
