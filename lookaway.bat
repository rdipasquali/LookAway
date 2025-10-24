@echo off
REM LookAway Launcher Script for Windows

cd /d "%~dp0"
set "PYTHON_EXE=%~dp0\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Virtual environment not found. Using system Python.
    set "PYTHON_EXE=python"
)

echo Starting LookAway...
"%PYTHON_EXE%" main.py %*