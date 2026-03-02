#!/bin/bash
# Install script for GitHub Auto Sync (Linux/macOS)

set -e  # Exit on error

echo "========================================"
echo "GitHub Auto Sync - Install Script"
echo "========================================"

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
echo "Using Python: $PYTHON"

echo ""
echo "Installing GitHub Auto Sync in development mode..."
$PYTHON -m pip install -e .

echo ""
echo "========================================"
echo "Installation completed!"
echo "You can now use 'github-auto-sync' or 'gas' command"
echo "========================================"
