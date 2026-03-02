# Makefile for GitHub Auto Sync
# 提供常用的开发和构建命令

.PHONY: help install install-dev test lint format type-check clean build upload docs all

# 默认目标
.DEFAULT_GOAL := help

# Python 解释器
PYTHON := python
PIP := pip

# 项目名称
PROJECT_NAME := github-auto-sync
PACKAGE_NAME := github_auto_sync

# 帮助信息
help:
	@echo "GitHub Auto Sync - 可用的命令:"
	@echo ""
	@echo "  make install      - 安装项目 (pip install -e .)"
	@echo "  make install-dev  - 安装开发依赖 (pip install -e .[dev])"
	@echo "  make install-docs - 安装文档依赖 (pip install -e .[docs])"
	@echo "  make test         - 运行测试 (pytest)"
	@echo "  make test-cov     - 运行测试并生成覆盖率报告"
	@echo "  make lint         - 运行代码检查 (flake8)"
	@echo "  make format       - 格式化代码 (black)"
	@echo "  make format-check - 检查代码格式"
	@echo "  make type-check   - 运行类型检查 (mypy)"
	@echo "  make clean        - 清理构建产物"
	@echo "  make build        - 构建分发包 (wheel + sdist)"
	@echo "  make upload       - 上传到 PyPI (twine)"
	@echo "  make upload-test  - 上传到 TestPyPI"
	@echo "  make docs         - 构建文档"
	@echo "  make docs-serve   - 启动文档服务器"
	@echo "  make check        - 运行所有检查 (lint + type-check + test)"
	@echo "  make all          - 清理 + 安装 + 检查 + 构建"
	@echo ""

# 安装命令
install:
	@echo "Installing $(PROJECT_NAME)..."
	$(PIP) install -e .

install-dev:
	@echo "Installing $(PROJECT_NAME) with dev dependencies..."
	$(PIP) install -e ".[dev]"
	@echo "Installing pre-commit hooks..."
	pre-commit install

install-docs:
	@echo "Installing $(PROJECT_NAME) with docs dependencies..."
	$(PIP) install -e ".[docs]"

# 测试命令
test:
	@echo "Running tests..."
	pytest

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=$(PACKAGE_NAME) --cov-report=html --cov-report=term-missing

test-verbose:
	@echo "Running tests (verbose mode)..."
	pytest -vvs

# 代码质量命令
lint:
	@echo "Running flake8..."
	flake8 src/$(PACKAGE_NAME) tests

format:
	@echo "Running black..."
	black src/$(PACKAGE_NAME) tests

format-check:
	@echo "Checking code format with black..."
	black --check src/$(PACKAGE_NAME) tests

type-check:
	@echo "Running mypy..."
	mypy src/$(PACKAGE_NAME)

# 预提交检查
check: format-check lint type-check test
	@echo "All checks passed!"

# 清理命令
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .eggs/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@echo "Clean complete!"

# 构建命令
build: clean
	@echo "Building distribution packages..."
	$(PYTHON) -m build
	@echo "Build complete! Check dist/ directory."

# 上传命令
upload: build
	@echo "Uploading to PyPI..."
	twine check dist/*
	twine upload dist/*

upload-test: build
	@echo "Uploading to TestPyPI..."
	twine check dist/*
	twine upload --repository testpypi dist/*

# 文档命令
docs:
	@echo "Building documentation..."
	cd docs && make html

docs-serve: docs
	@echo "Starting documentation server..."
	cd docs/_build/html && $(PYTHON) -m http.server 8000

docs-clean:
	@echo "Cleaning documentation build..."
	cd docs && make clean

# 完整流程
all: clean install-dev check build
	@echo "All tasks completed!"

# 发布流程
release: clean check build
	@echo "Ready for release!"
	@echo "Run 'make upload' to publish to PyPI."

# Windows 特定命令 (使用 PowerShell)
ifeq ($(OS),Windows_NT)
clean:
	@echo "Cleaning build artifacts (Windows)..."
	@if exist build (rmdir /s /q build)
	@if exist dist (rmdir /s /q dist)
	@if exist *.egg-info (rmdir /s /q *.egg-info)
	@if exist .eggs (rmdir /s /q .eggs)
	@if exist .pytest_cache (rmdir /s /q .pytest_cache)
	@if exist .mypy_cache (rmdir /s /q .mypy_cache)
	@if exist htmlcov (rmdir /s /q htmlcov)
	@if exist .coverage (del .coverage)
	@if exist coverage.xml (del coverage.xml)
	@for /r %%i in (__pycache__) do @if exist "%%i" (rmdir /s /q "%%i" 2>nul)
	@for /r %%i in (*.pyc) do @del "%%i" 2>nul
	@for /r %%i in (*.pyo) do @del "%%i" 2>nul
	@echo "Clean complete!"
endif
