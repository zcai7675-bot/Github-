# GitHub Auto Sync IDE 集成指南

本文档介绍如何将 GitHub Auto Sync 集成到各种 IDE 中，以便在开发过程中快速执行同步操作。

## 目录

- [概述](#概述)
- [通用 IDE 集成](#通用-ide-集成)
- [VS Code 集成](#vs-code-集成)
- [JetBrains IDE 集成](#jetbrains-ide-集成)
- [键盘快捷键推荐](#键盘快捷键推荐)

## 概述

GitHub Auto Sync 提供强大的命令行接口 (CLI)，可以与大多数现代 IDE 无缝集成。通过 IDE 集成，您可以：

- **快速同步**: 一键将当前项目同步到 GitHub
- **实时监控**: 在 IDE 内启动文件监控，自动同步变更
- **状态查看**: 快速查看同步状态和仓库信息
- **效率提升**: 无需离开 IDE 即可完成所有同步操作

### 支持的 IDE

| IDE | 集成方式 | 支持程度 |
|-----|---------|---------|
| VS Code | tasks.json + keybindings.json | 完整支持 |
| PyCharm / IntelliJ IDEA / WebStorm | External Tools | 完整支持 |
| Sublime Text | Build System | 基本支持 |
| Vim / Neovim | 自定义命令映射 | 基本支持 |
| Emacs | 自定义函数 | 基本支持 |

## 通用 IDE 集成

任何支持运行外部命令的 IDE 都可以通过以下方式集成 GitHub Auto Sync：

### 基本命令结构

```bash
# 同步当前项目
github-auto-sync sync

# 同步指定仓库
github-auto-sync sync <repository-name>

# 启动监控模式
github-auto-sync watch

# 查看状态
github-auto-sync list
```

### 通用配置步骤

1. **确认安装**: 确保 GitHub Auto Sync 已安装并在系统 PATH 中
   ```bash
   github-auto-sync --version
   ```

2. **初始化配置**: 在项目根目录运行
   ```bash
   github-auto-sync init
   ```

3. **配置 IDE**: 根据您的 IDE 类型，参考以下具体配置指南

### 环境变量配置

在 IDE 中运行 GitHub Auto Sync 时，可能需要配置以下环境变量：

| 变量名 | 说明 | 示例 |
|-------|------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `PATH` | 系统路径，确保能找到 `github-auto-sync` | 包含 Python Scripts 目录 |
| `PYTHONPATH` | Python 模块搜索路径 | 如有需要可配置 |

## VS Code 集成

VS Code 通过 `tasks.json` 和 `keybindings.json` 提供强大的任务系统集成。

### 快速配置

1. 在项目根目录创建 `.vscode/tasks.json`
2. 在 `.vscode/keybindings.json` 中添加快捷键（可选）

详细配置请参考：[VS Code 集成详细指南](./vscode-integration.md)

### 基本 tasks.json 示例

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitHub Auto Sync: Sync Now",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

### 常用任务

| 任务 | 命令 | 用途 |
|-----|------|------|
| 立即同步 | `github-auto-sync sync` | 手动触发同步 |
| 启动监控 | `github-auto-sync watch` | 开始自动监控文件变化 |
| 查看状态 | `github-auto-sync list` | 查看仓库列表和状态 |
| 初始同步 | `github-auto-sync sync --initial` | 首次全量同步 |

## JetBrains IDE 集成

PyCharm、IntelliJ IDEA、WebStorm 等 JetBrains IDE 通过 **External Tools** 功能集成外部命令。

### 快速配置

1. 打开 **Settings/Preferences** (Ctrl+Alt+S)
2. 导航到 **Tools > External Tools**
3. 点击 **+** 添加新工具
4. 配置工具参数

详细配置请参考：[JetBrains 集成详细指南](./jetbrains-integration.md)

### 基本配置示例

**Program**: `github-auto-sync`

**Arguments**: `sync`

**Working directory**: `$ProjectFileDir$`

### 常用工具配置

| 工具名称 | 参数 | 工作目录 |
|---------|------|---------|
| GAS: Sync | `sync` | `$ProjectFileDir$` |
| GAS: Watch | `watch` | `$ProjectFileDir$` |
| GAS: Status | `list` | `$ProjectFileDir$` |
| GAS: Init | `init` | `$ProjectFileDir$` |

## 键盘快捷键推荐

为提高工作效率，建议为常用操作配置键盘快捷键。

### 推荐快捷键方案

#### VS Code 推荐

| 操作 | 快捷键 | 说明 |
|-----|-------|------|
| 立即同步 | `Ctrl+Shift+G, S` | 快速同步当前项目 |
| 启动监控 | `Ctrl+Shift+G, W` | 开始自动监控 |
| 停止监控 | `Ctrl+Shift+G, X` | 停止自动监控 |
| 查看状态 | `Ctrl+Shift+G, L` | 查看仓库列表 |
| 初始同步 | `Ctrl+Shift+G, I` | 执行初始同步 |

#### JetBrains 推荐

| 操作 | 快捷键 | 说明 |
|-----|-------|------|
| 立即同步 | `Ctrl+Alt+Shift+S` | 快速同步当前项目 |
| 启动监控 | `Ctrl+Alt+Shift+W` | 开始自动监控 |
| 查看状态 | `Ctrl+Alt+Shift+L` | 查看仓库列表 |
| 初始化配置 | `Ctrl+Alt+Shift+I` | 初始化项目配置 |

### 自定义快捷键原则

1. **避免冲突**: 确保不与 IDE 默认快捷键冲突
2. **逻辑分组**: 相关操作使用相同前缀，如 `Ctrl+Shift+G`
3. **易于记忆**: 使用有意义的字母，如 S=Sync, W=Watch
4. **双手协调**: 尽量使用双手配合的快捷键，减少手指移动

## 高级配置

### 条件任务执行

#### VS Code 条件任务

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitHub Auto Sync: Conditional Sync",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync"],
      "windows": {
        "command": "github-auto-sync.exe"
      },
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "runOptions": {
        "runOn": "folderOpen"
      }
    }
  ]
}
```

### 多仓库项目配置

对于包含多个仓库的项目：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Sync: Frontend",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "frontend"]
    },
    {
      "label": "Sync: Backend",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "backend"]
    },
    {
      "label": "Sync: All",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "--all"]
    }
  ]
}
```

### 集成到保存操作

#### VS Code 自动同步（保存时）

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Auto Sync on Save",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync"],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

配合 VS Code 的 **Run on Save** 扩展使用。

## 故障排除

### 常见问题

#### 1. 命令未找到

**症状**: IDE 报告 `github-auto-sync: command not found`

**解决方案**:
- 确认 GitHub Auto Sync 已正确安装: `pip install github-auto-sync`
- 检查 Python Scripts 目录是否在系统 PATH 中
- 在 IDE 中配置完整路径: `C:\Python311\Scripts\github-auto-sync.exe`

#### 2. 配置文件未找到

**症状**: 错误提示 `未找到配置文件`

**解决方案**:
- 确保已在项目根目录运行 `github-auto-sync init`
- 在 IDE 任务中指定配置文件路径: `--config ./config.yaml`
- 检查工作目录设置是否正确

#### 3. 权限错误

**症状**: 认证错误或权限不足

**解决方案**:
- 运行 `github-auto-sync auth login` 进行认证
- 检查 GitHub Token 权限是否足够
- 确认 Token 未过期

#### 4. 终端输出乱码

**症状**: 中文显示为乱码

**解决方案**:
- 在 VS Code 的 tasks.json 中添加: `"options": { "env": { "PYTHONIOENCODING": "utf-8" } }`
- 在 JetBrains IDE 中设置环境变量 `PYTHONIOENCODING=utf-8`

### 调试技巧

1. **启用详细输出**: 在命令后添加 `-v` 或 `--verbose` 参数
2. **检查工作目录**: 确保任务在正确的目录下执行
3. **测试命令**: 在 IDE 终端中手动运行命令，确认可以正常工作
4. **查看输出面板**: 使用 IDE 的输出面板查看详细错误信息

## 最佳实践

### 1. 项目结构建议

```
project/
├── .vscode/
│   ├── tasks.json          # VS Code 任务配置
│   └── keybindings.json    # 快捷键配置
├── .idea/
│   └── externalTools.xml   # JetBrains 外部工具配置
├── github-auto-sync.yaml   # 同步配置文件
├── src/
└── README.md
```

### 2. 版本控制建议

- 将 IDE 配置文件提交到版本控制，方便团队共享
- 在 `.gitignore` 中排除个人特定的配置
- 提供示例配置文件供团队成员参考

### 3. 团队协作

- 统一团队的快捷键配置，提高协作效率
- 在项目的 README 中说明 IDE 集成方式
- 为新人提供配置向导文档

## 参考文档

- [VS Code 任务系统文档](https://code.visualstudio.com/docs/editor/tasks)
- [VS Code 快捷键配置](https://code.visualstudio.com/docs/getstarted/keybindings)
- [JetBrains External Tools](https://www.jetbrains.com/help/idea/settings-tools-external-tools.html)
- [GitHub Auto Sync CLI 文档](../README.md)

## 获取帮助

如果在 IDE 集成过程中遇到问题：

1. 查看详细指南文档:
   - [VS Code 集成详细指南](./vscode-integration.md)
   - [JetBrains 集成详细指南](./jetbrains-integration.md)

2. 运行诊断命令:
   ```bash
   github-auto-sync --version
   github-auto-sync auth status
   github-auto-sync list
   ```

3. 提交 Issue:
   - GitHub Issues: https://github.com/yourusername/github-auto-sync/issues
