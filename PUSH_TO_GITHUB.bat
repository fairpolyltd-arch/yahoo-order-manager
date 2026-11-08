@echo off
title Push Yahoo Order Manager to GitHub (fairpolyltd-arch)
cd /d "%~dp0"

echo ====================================================================
echo   Pushing Yahoo Order Manager to GitHub: fairpolyltd-arch
echo ====================================================================
echo.

git remote remove origin >nul 2>&1
git remote add origin https://github.com/fairpolyltd-arch/yahoo-order-manager.git
git branch -M main

echo [INFO] Pushing code to GitHub...
echo.
echo NOTE: A browser window will open asking you to sign in to GitHub.
echo Make sure you sign in as: fairpolyltd-arch
echo.
git push -u origin main

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo   [SUCCESS] Code successfully pushed to your GitHub repository!
    echo   View online: https://github.com/fairpolyltd-arch/yahoo-order-manager
    echo ====================================================================
    echo.
    echo Next: Go to https://render.com to deploy and make it live 24/7!
    echo.
) else (
    echo.
    echo [NOTE] If permission was denied, make sure you are logged into:
    echo        https://github.com as "fairpolyltd-arch" in your browser!
    echo.
)

pause
