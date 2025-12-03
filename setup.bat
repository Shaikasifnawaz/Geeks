@echo off
REM Windows Setup Script for NCAAFB Backend Pipeline

echo ========================================
echo NCAAFB Backend Pipeline - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Setting up environment configuration...
python backend\scripts\create_env.py
if errorlevel 1 (
    echo ERROR: Failed to create .env file
    pause
    exit /b 1
)

echo.
echo [3/3] Setup complete!
echo.
echo Next steps:
echo 1. Make sure PostgreSQL is running
echo 2. Run: python backend\main.py
echo.
pause

