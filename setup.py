#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Auto Sync 安装脚本

用于构建和分发 GitHub Auto Sync Python 包。
支持 setuptools 和 pyproject.toml 两种构建方式。

使用方法:
    pip install -e .          # 开发模式安装
    pip install -e ".[dev]"   # 安装开发依赖
    python setup.py sdist     # 创建源码分发包
    python setup.py bdist_wheel  # 创建 wheel 包
"""

import os
from setuptools import setup, find_packages

# 项目根目录
here = os.path.abspath(os.path.dirname(__file__))

# 读取 README 文件作为长描述
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "GitHub Auto Sync - 自动同步本地文件夹到 GitHub 仓库的工具"

# 读取 requirements.txt
try:
    with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = [
        "click>=8.0.0",
        "PyGithub>=1.59.0",
        "GitPython>=3.1.0",
        "watchdog>=3.0.0",
        "pyyaml>=6.0",
        "keyring>=24.0.0",
        "python-dotenv>=1.0.0",
    ]

# 读取 CHANGELOG
try:
    with open(os.path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
        changelog = f.read()
except FileNotFoundError:
    changelog = ""

setup(
    # 基本信息
    name="github-auto-sync",
    version="0.1.0",
    author="GitHub Auto Sync Team",
    author_email="support@github-auto-sync.dev",
    maintainer="GitHub Auto Sync Team",
    maintainer_email="support@github-auto-sync.dev",
    
    # 描述信息
    description="自动同步本地文件夹到 GitHub 仓库的工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # 项目链接
    url="https://github.com/yourusername/github-auto-sync",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/github-auto-sync/issues",
        "Source": "https://github.com/yourusername/github-auto-sync",
        "Documentation": "https://github.com/yourusername/github-auto-sync/blob/main/docs/README.md",
        "Changelog": "https://github.com/yourusername/github-auto-sync/blob/main/CHANGELOG.md",
        "Funding": "https://github.com/sponsors/yourusername",
    },
    
    # 包配置
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "github_auto_sync": ["py.typed"],
    },
    
    # 分类器和元数据
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Utilities",
        "Topic :: System :: Archiving :: Backup",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: English",
        "Typing :: Typed",
    ],
    
    # Python 版本要求
    python_requires=">=3.8",
    
    # 依赖
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    
    # 入口点
    entry_points={
        "console_scripts": [
            "github-auto-sync=github_auto_sync.cli:main",
            "gas=github_auto_sync.cli:main",
        ],
    },
    
    # 数据文件
    include_package_data=True,
    zip_safe=False,
    
    # 关键词
    keywords="github git sync automation backup version-control file-watch",
    
    # 平台
    platforms=["any"],
    
    # 许可证
    license="MIT",
    
    # 下载 URL
    download_url="https://github.com/yourusername/github-auto-sync/archive/refs/tags/v0.1.0.tar.gz",
)
