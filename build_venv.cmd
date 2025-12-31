@echo off
REM =============================================
REM Build virtual environment using Python from PATH
REM =============================================

REM Get the directory of this script
SET SCRIPT_DIR=%~dp0

SET PROJECT_ROOT=%SCRIPT_DIR%
SET VENV_DIR=%PROJECT_ROOT%\venv
SET REQUIREMENTS_FILE=%PROJECT_ROOT%\requirements.txt

REM Step 1: Check if Python is available
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found in PATH. Please install Python or add it to PATH.
    exit /b 1
)

REM Step 2: Create virtual environment if it doesn't exist
IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment at %VENV_DIR% 
    python -m venv "%VENV_DIR%"
) ELSE (
    echo Virtual environment already exists at %VENV_DIR%.
)

REM Step 3: Install requirements
echo Installing/upgrading requirements...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQUIREMENTS_FILE%"

echo Virtual environment setup complete.
pause