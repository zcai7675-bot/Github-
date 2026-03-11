# GitHub Auto Sync

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

GitHub Auto Sync 是一个强大的 Python 工具，用于自动监控本地文件夹变化并同步到 GitHub 仓库。

## 功能特性

- **🔄 自动文件监控**: 实时监控本地文件夹的变化，自动检测文件创建、修改、删除
- **📤 智能同步**: 自动提交、推送更改到 GitHub，支持批量处理和冲突解决
- **🤖 AI 智能描述**: 使用 AI 分析代码变更，生成有意义的提交描述（替代简单的时间戳）
- **📦 Release 管理**: 支持创建 GitHub Release、上传资源文件、管理版本发布
- **🔐 安全认证**: 支持 GitHub Token 认证，Token 安全存储在系统密钥环
- **⚙️ 灵活配置**: 通过 YAML 配置文件自定义行为，支持环境变量覆盖
- **🖥️ 命令行工具**: 简洁易用的 CLI 界面，支持多种命令和选项
- **📝 完整文档**: 提供详细的使用指南、API 文档、IDE 集成指南
- **✅ 全面测试**: 包含单元测试和集成测试，确保代码质量

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

# ========== 认证命令 ==========
# 登录 GitHub
github-auto-sync auth login

# 查看认证状态
github-auto-sync auth status

# 登出
github-auto-sync auth logout

# ========== 配置命令 ==========
# 初始化配置
github-auto-sync init

# 查看配置
github-auto-sync config show

# 设置配置项
github-auto-sync config set sync.auto_push true

# ========== 同步命令 ==========
# 手动同步
github-auto-sync sync

# 同步指定仓库
github-auto-sync sync my-project

# 启动自动监控
github-auto-sync watch

# 监控指定仓库
github-auto-sync watch my-project

# ========== 仓库管理命令 ==========
# 列出仓库
github-auto-sync list

# 创建 GitHub 仓库
github-auto-sync repo create my-repo --description "我的项目"

# 删除仓库
github-auto-sync repo delete my-repo

# ========== Release 管理命令 ==========
# 创建 Release
github-auto-sync release create v1.0.0 \
  -n "版本 1.0.0" \
  -b "## 更新内容\n- 新功能\n- Bug 修复"

# 上传文件到 Release
github-auto-sync release upload v1.0.0 ./dist/app.zip

# 列出 Release
github-auto-sync release list
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

## 项目架构

### 核心模块说明

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| **CLI 界面** | `cli.py` | 提供命令行交互界面，支持 init、auth、sync、watch、list、config、repo、release 等命令 |
| **配置管理** | `config.py` | 管理 YAML 配置文件，支持环境变量覆盖和配置验证 |
| **认证模块** | `auth.py` | 处理 GitHub Token 认证，支持系统密钥环安全存储 |
| **GitHub 客户端** | `github_client.py` | 封装 GitHub API，支持仓库管理、Release 创建和文件上传 |
| **同步引擎** | `sync.py` | 核心同步逻辑，支持初始同步、增量同步和自动同步模式 |
| **文件监控** | `watcher.py` | 基于 watchdog 实现文件系统实时监控，支持忽略模式 |
| **Git 操作** | `git_operations.py` | 封装 Git 命令，支持提交、推送、分支管理等操作 |
| **AI 描述** | `ai_description.py` | 智能生成提交描述，替代简单的模板消息 |

### 项目目录结构

```
github-auto-sync/
├── src/github_auto_sync/       # 核心源代码
│   ├── __init__.py            # 包初始化
│   ├── cli.py                 # CLI 命令行界面
│   ├── config.py              # 配置管理
│   ├── auth.py                # GitHub 认证
│   ├── github_client.py       # GitHub API 客户端
│   ├── sync.py                # 同步引擎
│   ├── watcher.py             # 文件系统监控
│   ├── git_operations.py      # Git 操作封装
│   └── ai_description.py      # AI 描述生成
├── tests/                      # 测试套件
│   ├── test_config.py
│   ├── test_auth.py
│   ├── test_github_client.py
│   ├── test_sync.py
│   ├── test_watcher.py
│   └── test_git_operations.py
├── docs/                       # 文档
│   ├── usage.md               # 使用指南
│   ├── api.md                 # API 文档
│   ├── troubleshooting.md     # 故障排除
│   ├── ide-integration.md     # IDE 集成指南
│   ├── vscode-integration.md  # VS Code 集成
│   └── jetbrains-integration.md # JetBrains 集成
├── .trae/skills/              # AI SKILL
│   └── code-describer/
│       └── SKILL.md           # 代码描述生成 SKILL
├── scripts/                    # 构建脚本
│   ├── build.bat / build.sh
│   ├── install.bat / install.sh
│   ├── test.bat / test.sh
│   └── clean.bat / clean.sh
├── setup.py                   # 安装配置
├── pyproject.toml             # 现代 Python 项目配置
├── requirements.txt           # 依赖列表
├── Makefile                   # 构建命令
├── LICENSE                    # MIT 许可证
└── README.md                  # 项目说明
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
