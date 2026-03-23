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

# Run both API and Streamlit via master script
python scripts/run_all.py
