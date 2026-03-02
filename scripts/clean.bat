@echo off
REM Windows clean script for GitHub Auto Sync

echo ========================================
echo GitHub Auto Sync - Clean Script
echo ========================================

echo Cleaning build artifacts...

if exist build (
    echo Removing build/ directory...
    rmdir /s /q build
)

if exist dist (
    echo Removing dist/ directory...
    rmdir /s /q dist
)

if exist *.egg-info (
    echo Removing *.egg-info directories...
    for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
)

if exist .eggs (
    echo Removing .eggs/ directory...
    rmdir /s /q .eggs
)

if exist .pytest_cache (
    echo Removing .pytest_cache/ directory...
    rmdir /s /q .pytest_cache
)

if exist .mypy_cache (
    echo Removing .mypy_cache/ directory...
    rmdir /s /q .mypy_cache
)

if exist htmlcov (
    echo Removing htmlcov/ directory...
    rmdir /s /q htmlcov
)

if exist .coverage (
    echo Removing .coverage file...
    del .coverage
)

if exist coverage.xml (
    echo Removing coverage.xml file...
    del coverage.xml
)

echo Removing __pycache__ directories...
for /r %%i in (__pycache__) do @if exist "%%i" (
    rmdir /s /q "%%i" 2>nul
)

echo Removing .pyc files...
for /r %%i in (*.pyc) do @del "%%i" 2>nul

echo Removing .pyo files...
for /r %%i in (*.pyo) do @del "%%i" 2>nul

echo.
echo ========================================
echo Clean complete!
echo ========================================
