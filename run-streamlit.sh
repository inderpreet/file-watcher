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

# Run Streamlit (UI at http://localhost:8501)
streamlit run src/streamlit_app.py --server.port 8501
