@echo off
if not exist "%~dp0.venv" (
    echo Creating virtual environment...
    python -m venv "%~dp0.venv"
    echo Installing dependencies...
    "%~dp0.venv\Scripts\pip" install -r "%~dp0requirements.txt"
)
"%~dp0.venv\Scripts\python.exe" "%~dp0soundboard.py"
pause
