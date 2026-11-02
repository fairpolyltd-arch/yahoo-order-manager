@echo off
setlocal enabledelayedexpansion
title Yahoo Mail Order Management System - Portable Launcher

echo ====================================================================
echo   Yahoo Mail Order Management & Intelligent Extraction System
echo   Universal One-Click Launcher for Any PC
echo ====================================================================
echo.

cd /d "%~dp0"

:: 1. Check for Python installation
where python >nul 2>&1
if %errorLevel% neq 0 (
    where py >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ERROR] Python is not installed or not in PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo Make sure to check the box "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [1/4] Checking Python environment...
%PYTHON_CMD% --version

:: 2. Check and install dependencies if needed
echo [2/4] Verifying required Python packages...
%PYTHON_CMD% -c "import fastapi, uvicorn, sqlalchemy, pandas" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Installing required dependencies (first time setup)...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo [WARNING] Some dependencies failed to install. Continuing...
    )
) else (
    echo [OK] All dependencies are ready.
)

:: 3. Detect Local Network IP Address
echo [3/4] Detecting Local Network IP Address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "RAW_IP=%%a"
    set "LOCAL_IP=!RAW_IP: =!"
    goto :ip_found
)
:ip_found
if "!LOCAL_IP!"=="" set "LOCAL_IP=127.0.0.1"

echo.
echo ====================================================================
echo   SERVER STARTING SUCCESSFULLY!
echo ====================================================================
echo   - On this PC:           http://localhost:8000
echo   - From Other PCs:       http://!LOCAL_IP!:8000
echo   - From Android Mobile:  http://!LOCAL_IP!:8000
echo ====================================================================
echo.

:: 4. Open browser
start http://localhost:8000

:: 5. Launch Backend
%PYTHON_CMD% run_backend.py
pause
