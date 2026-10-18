@echo off
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python manage.py migrate
start "" http://127.0.0.1:8000
.venv\Scripts\python manage.py runserver
pause
