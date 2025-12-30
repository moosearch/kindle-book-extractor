@echo off
REM =============================================
REM Build virtual environment using Python from PATH
REM =============================================

SET VENV_DIR=venv

REM Step 1: Check if Python is available
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found in PATH. Please install Python or add it to PATH.
    exit /b 1
)

REM Step 2: Create virtual environment if it doesn't exist
IF NOT EXIST %VENV_DIR% (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
) ELSE (
    echo Virtual environment already exists.
)

REM Step 3: Install requirements
echo Installing requirements...
%VENV_DIR%\Scripts\python.exe -m pip install --upgrade pip
%VENV_DIR%\Scripts\python.exe -m pip install -r requirements.txt

echo Virtual environment setup complete.
pause