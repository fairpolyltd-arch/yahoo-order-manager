@echo off
title Allow Network Access - Port 8000
echo ====================================================================
echo   Configuring Windows Firewall to allow port 8000 for LAN Access
echo ====================================================================
echo.

:: Check for Administrator elevation
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c netsh advfirewall firewall add rule name=\"YahooOrderManager Port 8000\" dir=in action=allow protocol=TCP localport=8000 & pause' -Verb RunAs"
    exit /b
)

netsh advfirewall firewall add rule name="YahooOrderManager Port 8000" dir=in action=allow protocol=TCP localport=8000
echo.
echo [SUCCESS] Port 8000 is now open! Other PCs and mobile phones on this WiFi can connect.
echo.
pause
