@echo off
REM =============================================
REM Build virtual environment using Python from PATH
REM =============================================

SET VENV_DIR=venv
SET PYTHON_EXE="%VENV_DIR%\Scripts\python.exe"

REM Step 4: Run the program
echo Running Kindle Book Extractor...
%PYTHON_EXE% main.py
pause