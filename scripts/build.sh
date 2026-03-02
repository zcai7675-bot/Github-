#!/bin/bash
# Build script for GitHub Auto Sync (Linux/macOS)

set -e  # Exit on error

echo "========================================"
echo "GitHub Auto Sync - Build Script"
echo "========================================"

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo "Using Python: $PYTHON"

echo ""
echo "Step 1: Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/ .eggs/
echo "Clean complete!"

echo ""
echo "Step 2: Installing build dependencies..."
$PYTHON -m pip install --upgrade build twine setuptools wheel
echo "Build dependencies installed!"

echo ""
echo "Step 3: Building distribution packages..."
$PYTHON -m build
echo "Build complete!"

echo ""
echo "Step 4: Checking distribution packages..."
twine check dist/*

echo ""
echo "========================================"
echo "Build process completed successfully!"
echo "Distribution files are in dist/ directory"
echo "========================================"
