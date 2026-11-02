@echo off
setlocal enabledelayedexpansion
title Push Yahoo Order Manager to GitHub

echo ====================================================================
echo   Yahoo Mail Order Extraction - Push to Your GitHub Account
echo ====================================================================
echo.
echo [STEP 1] Go to https://github.com/new in your browser.
echo [STEP 2] Enter repository name (e.g. yahoo-order-manager).
echo [STEP 3] Choose Public or Private.
echo [STEP 4] DO NOT check "Add a README" or ".gitignore" (Keep it empty).
echo [STEP 5] Click "Create repository".
echo.
echo ====================================================================
echo.
set /p REPO_URL="Paste your GitHub Repository URL here (e.g. https://github.com/your-username/yahoo-order-manager.git): "

if "!REPO_URL!"=="" (
    echo [ERROR] No URL entered! Exiting.
    pause
    exit /b 1
)

echo.
echo [INFO] Configuring remote origin...
git remote remove origin >nul 2>&1
git remote add origin !REPO_URL!
git branch -M main

echo [INFO] Pushing code to GitHub...
echo (If a browser or login prompt appears, please sign in to authorize)
echo.
git push -u origin main

if %errorLevel% equ 0 (
    echo.
    echo ====================================================================
    echo   [SUCCESS] Code successfully pushed to your GitHub repository!
    echo ====================================================================
    echo.
    echo Next Step: Go to https://render.com or https://railway.app
    echo and connect this GitHub repository for 24/7 Free Cloud Hosting!
    echo.
) else (
    echo.
    echo [ERROR] Failed to push. Please check your GitHub URL and credentials.
    echo.
)

pause
