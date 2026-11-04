@echo off
rem Double-click on Windows. Finds a Python that runs, then hands over to board.py. On a problem the window stays open, so the words can be read.
setlocal
set "HERE=%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "VENV=%HERE%..\..\.venv\Scripts\python.exe"
if exist "%VENV%" (
    "%VENV%" -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        "%VENV%" "%HERE%board.py" desktop
        goto done
    )
)
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    py -3 "%HERE%board.py" desktop
    goto done
)
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    python "%HERE%board.py" desktop
    goto done
)
echo The board needs Python 3.12 or newer, and none was found. Install one from https://www.python.org/downloads/ and start again.
cmd /c exit 1
:done
if errorlevel 1 pause
endlocal
