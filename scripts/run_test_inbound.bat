@echo off
REM Run script for Test Inbound Agent Server (Windows)
REM
REM This script sets up and runs the lightweight test inbound agent server
REM for manual testing without requiring Asterisk or other infrastructure.
REM
REM Usage:
REM   scripts\run_test_inbound.bat [--port PORT] [--client]
REM

echo ======================================
echo Test Inbound Agent - Setup and Run
echo ======================================
echo.

REM Get script directory and project directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Check Python version
echo Checking Python version...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: python not found
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install/upgrade websockets if needed
echo Checking dependencies...
python -c "import websockets" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing websockets library...
    pip install websockets
    echo websockets installed
) else (
    echo websockets already installed
)
echo.

REM Run the test server
echo Starting test inbound agent server...
echo.

REM Pass all arguments to the Python script
python tests\test_inbound_real_conversation.py %*
