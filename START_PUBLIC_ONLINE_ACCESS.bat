@echo off
title Yahoo Order Manager - Public Internet Access (Anywhere in the World)
echo ====================================================================
echo   Yahoo Mail Order Extraction - Public Internet Access Tunnel
echo ====================================================================
echo.
echo [INFO] Generating secure public URL for your dashboard...
echo You and your team can open this link on ANY PC or Mobile phone
echo anywhere in the world without being on the same WiFi!
echo.
echo (Press CTRL+C anytime to stop public sharing)
echo.
call npx -y localtunnel --port 8000
pause
