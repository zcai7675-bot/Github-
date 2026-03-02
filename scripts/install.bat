@echo off
REM Windows install script for GitHub Auto Sync

echo ========================================
echo GitHub Auto Sync - Install Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo.
echo Installing GitHub Auto Sync in development mode...
pip install -e .

echo.
echo ========================================
echo Installation completed!
echo You can now use 'github-auto-sync' or 'gas' command
echo ========================================
