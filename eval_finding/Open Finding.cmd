@echo off
setlocal
set "finding_python=%~dp0..\.venv\Scripts\pythonw.exe"
if not exist "%finding_python%" (
    echo The project's Python environment is missing from .venv.
    pause
    exit /b 1
)
start "" "%finding_python%" -B "%~dp0run_finding.py"
