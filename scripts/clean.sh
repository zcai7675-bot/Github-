#!/bin/bash
# Clean script for GitHub Auto Sync (Linux/macOS)

echo "========================================"
echo "GitHub Auto Sync - Clean Script"
echo "========================================"

echo "Cleaning build artifacts..."

# Remove directories
[ -d "build" ] && echo "Removing build/ directory..." && rm -rf build/
[ -d "dist" ] && echo "Removing dist/ directory..." && rm -rf dist/
[ -d ".eggs" ] && echo "Removing .eggs/ directory..." && rm -rf .eggs/
[ -d ".pytest_cache" ] && echo "Removing .pytest_cache/ directory..." && rm -rf .pytest_cache/
[ -d ".mypy_cache" ] && echo "Removing .mypy_cache/ directory..." && rm -rf .mypy_cache/
[ -d "htmlcov" ] && echo "Removing htmlcov/ directory..." && rm -rf htmlcov/

# Remove egg-info directories
for dir in *.egg-info; do
    [ -d "$dir" ] && echo "Removing $dir/ directory..." && rm -rf "$dir"
done

# Remove files
[ -f ".coverage" ] && echo "Removing .coverage file..." && rm -f .coverage
[ -f "coverage.xml" ] && echo "Removing coverage.xml file..." && rm -f coverage.xml

# Remove Python cache files
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Removing .pyc files..."
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "Removing .pyo files..."
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo "Removing .pyd files..."
find . -type f -name "*.pyd" -delete 2>/dev/null || true

echo ""
echo "========================================"
echo "Clean complete!"
echo "========================================"
