#!/bin/bash

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
    echo "Installing requirements..."
    .venv/bin/pip install -r requirements.txt
fi

# Activate .venv if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

# Run FastAPI via uvicorn (API at http://127.0.0.1:8000, docs at /docs)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
