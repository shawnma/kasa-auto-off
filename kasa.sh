#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

VENV_DIR="venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "=> Virtual environment not found. Initializing..."
    python3 -m venv "$VENV_DIR"
    
    echo "=> Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    echo "=> Installing dependencies from requirements.txt..."
    # Ensure pip is up to date
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
else
    # Just activate if it exists
    source "$VENV_DIR/bin/activate"
fi

# Pass all arguments passed to this wrapper script straight down into the python script
python kasa_manager.py "$@"
