@echo off

REM Check if .venv exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing requirements...
    .venv\Scripts\pip install -r requirements.txt
)

REM Activate .venv if not already active
if "%VIRTUAL_ENV%"=="" (
    call .venv\Scripts\activate.bat
)

REM Run FastAPI via uvicorn (API at http://127.0.0.1:8000, docs at /docs)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
