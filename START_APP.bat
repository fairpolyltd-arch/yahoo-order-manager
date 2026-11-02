@echo off
setlocal enabledelayedexpansion
title Yahoo Mail Order Management System
cd /d "%~dp0"

echo ==================================================================
echo   Starting Yahoo Mail Order Extraction & Management System...
echo ==================================================================
echo.

:: 1. Check if server is already running on port 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Server is already running on port 8000!
    echo Opening dashboard in your browser...
    start "" http://localhost:8000
    timeout /t 3 >nul
    exit /b 0
)

:: 2. Find local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "RAW_IP=%%a"
    set "LOCAL_IP=!RAW_IP: =!"
    goto :found_ip
)
:found_ip
if "!LOCAL_IP!"=="" set "LOCAL_IP=127.0.0.1"

echo [INFO] Local PC URL:       http://localhost:8000
echo [INFO] Mobile/Network URL: http://!LOCAL_IP!:8000
echo.
echo Starting backend server process...

:: 3. Launch browser after 2 seconds in parallel
powershell -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8000'" >nul 2>&1 &

:: 4. Start Python backend
python run_backend.py
pause
