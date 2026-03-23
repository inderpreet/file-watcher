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

REM Run Streamlit (UI at http://localhost:8501)
streamlit run src/streamlit_app.py --server.port 8501
