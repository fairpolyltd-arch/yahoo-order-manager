@echo off
title Install Yahoo Order Manager Auto-Start
echo ====================================================================
echo   Adding Yahoo Mail Order Manager to Windows Startup
echo ====================================================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET_BAT=%~dp0START_APP.bat"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%STARTUP_DIR%\YahooOrderManager.lnk'); $Shortcut.TargetPath = '%TARGET_BAT%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Save()"

echo [SUCCESS] Auto-start shortcut created in Windows Startup!
echo Yahoo Order Manager will now start automatically whenever your computer turns on.
echo.
pause
