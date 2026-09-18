#!/usr/bin/env bash
# Libro start script
# Activates virtual environment and runs the Streamlit app

# Directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Activate virtual environment (assuming it's in PROJECT_DIR/venv)
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo "Virtual environment not found at $PROJECT_DIR/venv"
    echo "Please create one with: python3 -m venv venv"
    echo "Then install requirements: pip install -r requirements.txt"
    exit 1
fi

# Run Streamlit on port 5252
exec streamlit run app.py --server.port 5252