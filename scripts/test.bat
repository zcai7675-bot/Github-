@echo off
REM Windows test script for GitHub Auto Sync

echo ========================================
echo GitHub Auto Sync - Test Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo.
echo Installing test dependencies...
pip install pytest pytest-cov

echo.
echo Running tests...
pytest -v

echo.
echo ========================================
echo Test run completed!
echo ========================================
