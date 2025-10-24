#!/bin/bash
# LookAway Launcher Script for Linux

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
    echo "Using virtual environment Python"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
    echo "Using system Python 3"
elif command -v python &> /dev/null; then
    PYTHON_EXE="python"
    echo "Using system Python"
else
    echo "Error: Python not found!"
    exit 1
fi

echo "Starting LookAway..."
"$PYTHON_EXE" main.py "$@"