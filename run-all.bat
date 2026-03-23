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

REM Run both API and Streamlit via master script
python scripts\run_all.py
