@echo off
title Yahoo Mail Order Management System
echo ==================================================================
echo   Starting Yahoo Mail Order Extraction & Management System...
echo ==================================================================
echo.

cd /d "%~dp0"
start "" http://localhost:8000
python run_backend.py
pause
