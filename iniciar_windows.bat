@echo off
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python manage.py migrate
if errorlevel 1 (
  echo.
  echo ERROR: no se pudo conectar a PostgreSQL. Verifica que este encendido,
  echo que exista la base psps_sqa y las variables POSTGRES_* (ver docs/06).
  pause
  exit /b 1
)
start "" http://127.0.0.1:8000
.venv\Scripts\python manage.py runserver
pause