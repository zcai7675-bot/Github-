# GitHub Auto Sync

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitHub Auto Sync 是一个强大的 Python 工具，用于自动监控本地文件夹变化并同步到 GitHub 仓库。

## 功能特性

- **自动文件监控**: 实时监控本地文件夹的变化
- **智能同步**: 自动提交、推送更改到 GitHub
- **冲突解决**: 自动处理合并冲突
- **安全认证**: 支持 GitHub Token 和安全凭证存储
- **灵活配置**: 通过 YAML 配置文件自定义行为
- **命令行工具**: 简洁易用的 CLI 界面

## 安装

### 从 PyPI 安装 (推荐)

```bash
pip install github-auto-sync
```

### 从源码安装

```bash
git clone https://github.com/yourusername/github-auto-sync.git
cd github-auto-sync
pip install -e .
```

## 依赖要求

- Python 3.8+
- Git
- GitHub 账户和 Personal Access Token

## 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| click | >=8.0.0 | CLI 框架 |
| PyGithub | >=1.59.0 | GitHub API 客户端 |
| GitPython | >=3.1.0 | Git 操作 |
| watchdog | >=3.0.0 | 文件系统监控 |
| pyyaml | >=6.0 | YAML 配置解析 |
| keyring | >=24.0.0 | 安全凭证存储 |
| python-dotenv | >=1.0.0 | 环境变量管理 |

## 快速开始

### 1. 配置 GitHub Token

```bash
github-auto-sync configure
```

### 2. 初始化同步项目

```bash
github-auto-sync init /path/to/your/folder
```

### 3. 启动自动同步

```bash
github-auto-sync start
```

## 命令行用法

```bash
# 查看帮助
github-auto-sync --help

# 配置 GitHub Token
github-auto-sync configure --token YOUR_GITHUB_TOKEN

# 初始化项目
github-auto-sync init /path/to/folder --repo username/repo-name

# 启动监控
github-auto-sync start --config ./config.yaml

# 手动同步
github-auto-sync sync

# 查看状态
github-auto-sync status
```

## 配置文件

创建 `config.yaml` 文件:

```yaml
github:
  token: ${GITHUB_TOKEN}
  repo: username/repository
  branch: main

sync:
  watch_path: ./data
  auto_commit: true
  commit_message_template: "Auto sync: {timestamp}"
  ignore_patterns:
    - "*.tmp"
    - ".DS_Store"
    - "__pycache__/"

schedule:
  enabled: false
  interval_minutes: 5
```

## 项目结构

```
github-auto-sync/
├── src/
│   └── github_auto_sync/
│       ├── __init__.py
│       ├── cli.py
│       ├── sync.py
│       ├── config.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   └── test_sync.py
├── docs/
│   └── README.md
├── setup.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black src/
```

### 类型检查

```bash
mypy src/
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 邮箱: support@github-auto-sync.dev
- GitHub Issues: https://github.com/yourusername/github-auto-sync/issues
