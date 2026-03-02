@echo off
REM Windows build script for GitHub Auto Sync

echo ========================================
echo GitHub Auto Sync - Build Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo.
echo Step 1: Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.egg-info rmdir /s /q *.egg-info
if exist .eggs rmdir /s /q .eggs
echo Clean complete!

echo.
echo Step 2: Installing build dependencies...
pip install --upgrade build twine setuptools wheel
echo Build dependencies installed!

echo.
echo Step 3: Building distribution packages...
python -m build
echo Build complete!

echo.
echo Step 4: Checking distribution packages...
twine check dist/*

echo.
echo ========================================
echo Build process completed successfully!
echo Distribution files are in dist/ directory
echo ========================================
