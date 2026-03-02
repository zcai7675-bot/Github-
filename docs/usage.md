# GitHub Auto Sync 使用指南

本文档提供了 GitHub Auto Sync 的详细使用说明，包括安装、配置、CLI 命令和常见工作流。

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [配置指南](#配置指南)
- [CLI 命令](#cli-命令)
- [常见工作流](#常见工作流)

---

## 安装

### 系统要求

- Python 3.8 或更高版本
- Git 2.0 或更高版本
- 有效的 GitHub 账号

### 安装方式

#### 方式一：通过 pip 安装（推荐）

```bash
pip install github-auto-sync
```

#### 方式二：从源码安装

```bash
git clone https://github.com/yourusername/github-auto-sync.git
cd github-auto-sync
pip install -e .
```

#### 方式三：使用 requirements.txt

```bash
pip install -r requirements.txt
```

### 验证安装

```bash
github-auto-sync --version
```

---

## 快速开始

### 1. 初始化配置

在项目目录中运行：

```bash
github-auto-sync init
```

这将创建一个 `.github-auto-sync.yml` 配置文件。

### 2. 配置 GitHub Token

编辑配置文件，添加你的 GitHub Token：

```yaml
github:
  token: "ghp_your_token_here"
  username: "your_username"
```

或者通过环境变量设置：

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_USERNAME="your_username"
```

### 3. 配置仓库

在配置文件中添加要同步的仓库：

```yaml
repositories:
  - name: "my-project"
    local_path: "./my-project"
    remote_url: "https://github.com/yourusername/my-project.git"
    branch: "main"
    auto_sync: true
```

或者使用 CLI 命令添加：

```bash
github-auto-sync config add-repo -n my-project -p ./my-project -r https://github.com/yourusername/my-project.git
```

### 4. 认证

```bash
github-auto-sync auth login
```

### 5. 执行初始同步

```bash
github-auto-sync sync my-project --initial
```

### 6. 启动自动监控

```bash
github-auto-sync watch my-project
```

---

## 配置指南

### 配置文件结构

`.github-auto-sync.yml` 文件包含以下主要部分：

```yaml
# GitHub 认证配置
github:
  token: ""
  username: ""

# 仓库配置列表
repositories:
  - name: ""
    local_path: ""
    remote_url: ""
    branch: "main"
    auto_sync: true
    ignore_patterns: []

# 同步设置
sync:
  batch_window: 30
  max_files_per_commit: 50
  commit_message_template: "auto-sync: {action} {files} files"
  auto_push: true
  auto_pull: true
  conflict_strategy: "skip"

# 日志设置
logging:
  level: "INFO"
  file: ""
  color: true

# 通知设置
notifications:
  on_error: true
  on_success: false
```

### 配置项详解

#### GitHub 认证配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `github.token` | string | `""` | GitHub Personal Access Token |
| `github.username` | string | `""` | GitHub 用户名 |

**环境变量覆盖：**
- `GITHUB_TOKEN` - 覆盖 `github.token`
- `GITHUB_USERNAME` - 覆盖 `github.username`

#### 仓库配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | string | 必填 | 仓库名称（唯一标识） |
| `local_path` | string | 必填 | 本地文件夹路径 |
| `remote_url` | string | `""` | 远程仓库 URL（可选） |
| `branch` | string | `"main"` | 默认分支 |
| `auto_sync` | boolean | `true` | 是否启用自动同步 |
| `ignore_patterns` | list | 默认列表 | 忽略的文件模式 |

**默认忽略模式：**
- `.git/`, `__pycache__/`, `node_modules/`
- `*.pyc`, `*.log`, `.DS_Store`
- `.env`, `.venv/`, `*.tmp`, `*.temp`

#### 同步设置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `batch_window` | int | `30` | 批处理时间窗口（秒） |
| `max_files_per_commit` | int | `50` | 每次提交的最大文件数 |
| `commit_message_template` | string | `"auto-sync: {action} {files} files"` | 提交消息模板 |
| `auto_push` | boolean | `true` | 是否自动推送 |
| `auto_pull` | boolean | `true` | 是否自动拉取 |
| `conflict_strategy` | string | `"skip"` | 冲突解决策略 |
| `use_ai_description` | boolean | `false` | 是否使用 AI 生成提交描述 |
| `ai_description` | object | 见下文 | AI 描述生成配置 |

**冲突解决策略：**
- `skip` - 跳过冲突文件
- `overwrite` - 使用本地版本覆盖
- `merge` - 保留冲突，需要手动解决

**提交消息模板变量：**
- `{action}` - 操作类型（initial/incremental）
- `{files}` - 文件数量
- `{timestamp}` - 时间戳

#### AI 描述生成配置

当 `use_ai_description` 设置为 `true` 时，AI 会分析代码变更并生成有意义的提交描述，替代简单的模板消息。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ai_description.language` | string | `"auto"` | 描述语言（auto/zh/en） |
| `ai_description.include_details` | boolean | `true` | 是否包含详细变更列表 |
| `ai_description.max_length` | int | `500` | 最大描述长度（字符） |

**启用 AI 描述示例：**

```yaml
sync:
  use_ai_description: true
  ai_description:
    language: "zh"        # 使用中文生成描述
    include_details: true # 包含详细变更列表
    max_length: 500       # 最大 500 字符
```

**AI 生成的提交描述示例：**

```
[功能] 实现用户认证系统

- 添加用户登录和注册功能
- 实现密码加密存储
- 集成 JWT Token 认证
```

对比默认模板：
```
auto-sync: update 5 files
```

**注意：** AI 描述功能需要配合 `.trae/skills/code-describer/SKILL.md` 使用，AI 助手会根据此 SKILL 生成准确的代码描述。

#### 日志设置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `logging.level` | string | `"INFO"` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `logging.file` | string | `""` | 日志文件路径（可选） |
| `logging.color` | boolean | `true` | 是否启用彩色输出 |

#### 通知设置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `notifications.on_error` | boolean | `true` | 同步失败时发送通知 |
| `notifications.on_success` | boolean | `false` | 同步成功时发送通知 |

### 环境变量

以下环境变量可以覆盖配置文件中的设置：

| 环境变量 | 覆盖的配置项 |
|----------|--------------|
| `GITHUB_TOKEN` | `github.token` |
| `GITHUB_USERNAME` | `github.username` |
| `GITHUB_BATCH_WINDOW` | `sync.batch_window` |
| `GITHUB_MAX_FILES` | `sync.max_files_per_commit` |
| `GITHUB_AUTO_PUSH` | `sync.auto_push` |
| `GITHUB_AUTO_PULL` | `sync.auto_pull` |
| `GITHUB_LOG_LEVEL` | `logging.level` |
| `GITHUB_LOG_FILE` | `logging.file` |

---

## CLI 命令

### 全局选项

```bash
github-auto-sync [OPTIONS] COMMAND [ARGS]...

选项:
  -c, --config PATH  配置文件路径
  -v, --verbose      启用详细输出
  --version          显示版本信息
  --help             显示帮助信息
```

### init - 初始化配置

创建默认的配置文件。

```bash
github-auto-sync init [OPTIONS]

选项:
  -p, --path PATH  配置文件保存路径
  -f, --force      强制覆盖已存在的配置文件
```

**示例：**

```bash
# 在当前目录创建配置
github-auto-sync init

# 指定路径创建配置
github-auto-sync init -p ./config.yml

# 强制覆盖现有配置
github-auto-sync init -f
```

### auth - 认证管理

管理 GitHub 认证。

#### auth login - 登录

```bash
github-auto-sync auth login [OPTIONS]

选项:
  -t, --token TEXT      GitHub Personal Access Token
  -u, --username TEXT   GitHub 用户名
  --no-store           不保存凭证到系统密钥环
```

**示例：**

```bash
# 交互式登录
github-auto-sync auth login

# 使用 token 登录
github-auto-sync auth login -t ghp_xxxxxx

# 使用 token 和用户名登录
github-auto-sync auth login -t ghp_xxxxxx -u myusername
```

#### auth logout - 登出

```bash
github-auto-sync auth logout
```

#### auth status - 查看认证状态

```bash
github-auto-sync auth status
```

**示例输出：**

```
✓ 已认证
  用户名: your_username
  Token: ghp_xxxxxx...
ℹ Token 有效 (用户: @your_username)
```

### sync - 同步

将本地文件夹同步到 GitHub。

```bash
github-auto-sync sync [REPOSITORY] [OPTIONS]

参数:
  REPOSITORY  仓库名称（可选，默认使用第一个配置的仓库）

选项:
  -i, --initial   执行初始同步（全量上传）
  -d, --dry-run   试运行模式（不实际执行操作）
  --all          同步所有配置的仓库
```

**示例：**

```bash
# 同步默认仓库
github-auto-sync sync

# 同步指定仓库
github-auto-sync sync my-project

# 初始同步
github-auto-sync sync my-project --initial

# 试运行
github-auto-sync sync my-project --dry-run

# 同步所有仓库
github-auto-sync sync --all
```

### watch - 监控并自动同步

监控文件夹变更并自动同步。

```bash
github-auto-sync watch [REPOSITORY] [OPTIONS]

参数:
  REPOSITORY  仓库名称（可选）

选项:
  --interval FLOAT  批处理时间窗口（秒）
```

**示例：**

```bash
# 监控默认仓库
github-auto-sync watch

# 监控指定仓库
github-auto-sync watch my-project

# 设置批处理窗口为 10 秒
github-auto-sync watch my-project --interval 10
```

**停止监控：** 按 `Ctrl+C`

### list - 列出仓库

显示所有配置的仓库。

```bash
github-auto-sync list [OPTIONS]

选项:
  --json  以 JSON 格式输出
```

**示例：**

```bash
# 表格格式输出
github-auto-sync list

# JSON 格式输出
github-auto-sync list --json
```

**示例输出：**

```
名称        | 本地路径           | 分支  | 自动同步
------------------------------------------------
my-project  | ./my-project       | main  | 是
another     | /path/to/another   | dev   | 否

ℹ 共 2 个仓库
```

### config - 配置管理

管理配置文件。

#### config get - 获取配置项

```bash
github-auto-sync config get KEY

参数:
  KEY  配置项键名（支持点号访问，如 github.token）
```

**示例：**

```bash
github-auto-sync config get github.token
github-auto-sync config get sync.batch_window
```

#### config set - 设置配置项

```bash
github-auto-sync config set KEY VALUE

参数:
  KEY    配置项键名
  VALUE  配置项值
```

**示例：**

```bash
github-auto-sync config set github.token ghp_xxxxxx
github-auto-sync config set sync.auto_push true
github-auto-sync config set sync.batch_window 60
```

#### config add-repo - 添加仓库

```bash
github-auto-sync config add-repo [OPTIONS]

选项:
  -n, --name TEXT       仓库名称（必填）
  -p, --path PATH       本地路径（必填）
  -r, --remote TEXT     远程仓库 URL
  -b, --branch TEXT     默认分支（默认：main）
  --no-auto-sync       禁用自动同步
```

**示例：**

```bash
# 添加基本仓库配置
github-auto-sync config add-repo -n my-project -p ./my-project

# 添加完整仓库配置
github-auto-sync config add-repo -n my-project -p ./my-project -r https://github.com/user/repo.git -b main
```

#### config remove-repo - 移除仓库

```bash
github-auto-sync config remove-repo NAME

参数:
  NAME  仓库名称
```

**示例：**

```bash
github-auto-sync config remove-repo my-project
```

#### config show - 显示完整配置

```bash
github-auto-sync config show
```

### repo - 仓库管理

管理 GitHub 上的仓库。

#### repo create - 创建仓库

```bash
github-auto-sync repo create NAME [OPTIONS]

参数:
  NAME  仓库名称

选项:
  -d, --description TEXT    仓库描述
  --public                  创建公开仓库（默认私有）
  --auto-init               自动初始化 README
  --gitignore TEXT          Gitignore 模板（如 Python, Node）
  --license TEXT            许可证模板（如 mit, apache-2.0）
```

**示例：**

```bash
# 创建私有仓库
github-auto-sync repo create my-new-repo

# 创建公开仓库
github-auto-sync repo create my-new-repo --public

# 创建带描述的仓库
github-auto-sync repo create my-new-repo -d "我的新项目"

# 创建带 gitignore 和许可证的仓库
github-auto-sync repo create my-new-repo --gitignore Python --license mit
```

#### repo delete - 删除仓库

```bash
github-auto-sync repo delete NAME

参数:
  NAME  仓库名称

警告：此操作不可恢复！
```

**示例：**

```bash
github-auto-sync repo delete my-repo
```

#### repo list - 列出远程仓库

```bash
github-auto-sync repo list [OPTIONS]

选项:
  -n, --limit INTEGER  显示数量限制（默认：30）
  --json               以 JSON 格式输出
```

**示例：**

```bash
# 列出前 30 个仓库
github-auto-sync repo list

# 列出前 10 个仓库
github-auto-sync repo list -n 10

# JSON 格式输出
github-auto-sync repo list --json
```

---

## 常见工作流

### 工作流 1：新项目初始化

将现有本地项目同步到 GitHub：

```bash
# 1. 进入项目目录
cd /path/to/my-project

# 2. 初始化配置
github-auto-sync init

# 3. 编辑配置，添加 GitHub Token
github-auto-sync config set github.token ghp_xxxxxx

# 4. 添加仓库配置
github-auto-sync config add-repo -n my-project -p . --no-auto-sync

# 5. 登录 GitHub
github-auto-sync auth login

# 6. 在 GitHub 上创建仓库
github-auto-sync repo create my-project --private

# 7. 执行初始同步
github-auto-sync sync my-project --initial

# 8. 启动自动监控
github-auto-sync watch my-project
```

### 工作流 2：多仓库管理

管理多个项目的同步：

```bash
# 1. 创建共享配置
github-auto-sync init -p ~/.config/github-auto-sync/config.yml

# 2. 添加多个仓库
github-auto-sync config add-repo -n project-a -p ~/projects/project-a
github-auto-sync config add-repo -n project-b -p ~/projects/project-b
github-auto-sync config add-repo -n project-c -p ~/projects/project-c

# 3. 同步所有仓库
github-auto-sync sync --all

# 4. 监控特定仓库
github-auto-sync watch project-a
```

### 工作流 3：团队协作

在团队环境中使用：

```bash
# 1. 使用环境变量设置凭证（避免将 token 写入配置文件）
export GITHUB_TOKEN="ghp_xxxxxx"
export GITHUB_USERNAME="team-member"

# 2. 验证认证
github-auto-sync auth status

# 3. 启用自动拉取以获取远程更新
github-auto-sync config set sync.auto_pull true

# 4. 设置冲突解决策略为 merge（手动解决冲突）
github-auto-sync config set sync.conflict_strategy merge

# 5. 启动监控
github-auto-sync watch my-project
```

### 工作流 4：CI/CD 集成

在 CI/CD 管道中使用：

```bash
# 1. 设置环境变量
export GITHUB_TOKEN="${{ secrets.GITHUB_TOKEN }}"

# 2. 使用试运行模式验证配置
github-auto-sync sync --all --dry-run

# 3. 执行同步
github-auto-sync sync --all
```

### 工作流 5：备份工作流

将重要文件夹自动备份到 GitHub：

```yaml
# .github-auto-sync.yml
repositories:
  - name: "documents-backup"
    local_path: "~/Documents/Important"
    branch: "main"
    auto_sync: true
    ignore_patterns:
      - "*.tmp"
      - "*.cache"

sync:
  batch_window: 300  # 5 分钟批处理窗口
  auto_push: true
  commit_message_template: "backup: {timestamp}"
```

```bash
# 启动后台监控
nohup github-auto-sync watch documents-backup > backup.log 2>&1 &
```

---

## 提示和最佳实践

1. **安全性**：使用环境变量或系统密钥环存储 GitHub Token，避免将敏感信息写入配置文件
2. **批处理窗口**：根据项目大小和文件变更频率调整 `batch_window`，减少不必要的提交
3. **忽略模式**：合理配置 `ignore_patterns`，避免同步临时文件和依赖目录
4. **冲突处理**：团队协作时建议使用 `merge` 策略，手动解决冲突
5. **日志级别**：开发时使用 `DEBUG` 级别，生产环境使用 `INFO` 或 `WARNING`
6. **自动同步**：对于频繁变更的项目启用 `auto_sync`，对于稳定项目使用手动同步

---

## 获取帮助

- 查看命令帮助：`github-auto-sync --help`
- 查看子命令帮助：`github-auto-sync <command> --help`
- 查看故障排除指南：[troubleshooting.md](./troubleshooting.md)
