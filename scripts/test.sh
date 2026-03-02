#!/bin/bash
# Test script for GitHub Auto Sync (Linux/macOS)

set -e  # Exit on error

echo "========================================"
echo "GitHub Auto Sync - Test Script"
echo "========================================"

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo "Using Python: $PYTHON"

echo ""
echo "Installing test dependencies..."
$PYTHON -m pip install pytest pytest-cov

echo ""
echo "Running tests..."
$PYTHON -m pytest -v

echo ""
echo "========================================"
echo "Test run completed!"
echo "========================================"
