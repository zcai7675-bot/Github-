# VS Code 集成详细指南

本指南详细介绍如何在 Visual Studio Code 中配置 GitHub Auto Sync，包括 tasks.json 配置、快捷键设置和高级用法。

## 目录

- [快速开始](#快速开始)
- [配置 tasks.json](#配置-tasksjson)
- [配置 keybindings.json](#配置-keybindingsjson)
- [完整配置示例](#完整配置示例)
- [高级配置](#高级配置)
- [使用技巧](#使用技巧)
- [故障排除](#故障排除)

## 快速开始

### 1. 创建配置目录

在项目根目录创建 `.vscode` 文件夹：

```bash
mkdir .vscode
```

### 2. 创建基本配置

创建 `.vscode/tasks.json` 文件：

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
      },
      "problemMatcher": []
    }
  ]
}
```

### 3. 运行任务

- 按 `Ctrl+Shift+P` 打开命令面板
- 输入 `Run Task` 并选择
- 选择 `GitHub Auto Sync: Sync Now`

## 配置 tasks.json

### 任务配置详解

#### 基础同步任务

```json
{
  "label": "GitHub Auto Sync: Sync Now",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["sync"],
  "options": {
    "cwd": "${workspaceFolder}"
  },
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared",
    "showReuseMessage": true,
    "clear": false
  },
  "problemMatcher": []
}
```

**配置说明：**

| 属性 | 说明 | 示例值 |
|-----|------|-------|
| `label` | 任务显示名称 | `"GitHub Auto Sync: Sync Now"` |
| `type` | 任务类型 | `"shell"` |
| `command` | 执行的命令 | `"github-auto-sync"` |
| `args` | 命令参数 | `["sync"]` |
| `options.cwd` | 工作目录 | `"${workspaceFolder}"` |
| `group` | 任务分组 | `"build"` |
| `presentation.reveal` | 输出面板显示方式 | `"always"` / `"silent"` / `"never"` |
| `presentation.panel` | 输出面板模式 | `"shared"` / `"dedicated"` / `"new"` |

#### 带参数的同步任务

```json
{
  "label": "GitHub Auto Sync: Sync with Verbose",
  "type": "shell",
  "command": "github-auto-sync",
  "args": [
    "sync",
    "-v"
  ],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared"
  }
}
```

#### 初始同步任务

```json
{
  "label": "GitHub Auto Sync: Initial Sync",
  "type": "shell",
  "command": "github-auto-sync",
  "args": [
    "sync",
    "--initial"
  ],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared"
  }
}
```

#### 监控模式任务

```json
{
  "label": "GitHub Auto Sync: Start Watch",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["watch"],
  "isBackground": true,
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "dedicated"
  },
  "problemMatcher": {
    "pattern": {
      "regexp": "."
    },
    "background": {
      "activeOnStart": true,
      "beginsPattern": ".*正在启动监控.*",
      "endsPattern": ".*监控已启动.*"
    }
  }
}
```

**注意：** `isBackground: true` 表示这是一个后台任务，VS Code 不会等待它完成。

#### 查看状态任务

```json
{
  "label": "GitHub Auto Sync: Show Status",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["list"],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared",
    "clear": true
  }
}
```

#### 初始化配置任务

```json
{
  "label": "GitHub Auto Sync: Init Config",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["init"],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared"
  }
}
```

#### 认证任务

```json
{
  "label": "GitHub Auto Sync: Check Auth",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["auth", "status"],
  "group": "build",
  "presentation": {
    "echo": true,
    "reveal": "always",
    "focus": false,
    "panel": "shared",
    "clear": true
  }
}
```

### 多仓库配置

对于包含多个仓库的项目：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Sync: Frontend",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "frontend"],
      "group": "build"
    },
    {
      "label": "Sync: Backend",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "backend"],
      "group": "build"
    },
    {
      "label": "Sync: Documentation",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "docs"],
      "group": "build"
    },
    {
      "label": "Sync: All Repositories",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "--all"],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

### 条件任务配置

#### 平台特定配置

```json
{
  "label": "GitHub Auto Sync: Sync (Cross-platform)",
  "type": "shell",
  "windows": {
    "command": "github-auto-sync.exe",
    "args": ["sync"]
  },
  "linux": {
    "command": "github-auto-sync",
    "args": ["sync"]
  },
  "osx": {
    "command": "github-auto-sync",
    "args": ["sync"]
  },
  "group": "build"
}
```

#### 使用完整路径

如果 `github-auto-sync` 不在 PATH 中：

```json
{
  "label": "GitHub Auto Sync: Sync (Full Path)",
  "type": "shell",
  "command": "python",
  "args": [
    "-m",
    "github_auto_sync",
    "sync"
  ],
  "options": {
    "env": {
      "PYTHONPATH": "${workspaceFolder}/src"
    }
  },
  "group": "build"
}
```

## 配置 keybindings.json

### 打开键盘快捷键配置

1. 按 `Ctrl+K Ctrl+S` 打开键盘快捷键设置
2. 点击右上角的图标打开 `keybindings.json`
3. 或者手动创建 `.vscode/keybindings.json`

### 基础快捷键配置

```json
[
  {
    "key": "ctrl+shift+g s",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Sync Now",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g w",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Start Watch",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g l",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Show Status",
    "when": "editorTextFocus"
  }
]
```

### 完整快捷键配置

```json
[
  {
    "key": "ctrl+shift+g s",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Sync Now",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g i",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Initial Sync",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g w",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Start Watch",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g x",
    "command": "workbench.action.tasks.terminate",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g l",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Show Status",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g c",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Init Config",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g a",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Check Auth",
    "when": "editorTextFocus"
  }
]
```

### 快捷键说明

| 快捷键 | 功能 | 说明 |
|-------|------|------|
| `Ctrl+Shift+G, S` | 立即同步 | 快速同步当前项目 |
| `Ctrl+Shift+G, I` | 初始同步 | 执行首次全量同步 |
| `Ctrl+Shift+G, W` | 启动监控 | 开始自动监控文件变化 |
| `Ctrl+Shift+G, X` | 停止任务 | 终止当前运行的任务 |
| `Ctrl+Shift+G, L` | 查看状态 | 显示仓库列表和状态 |
| `Ctrl+Shift+G, C` | 初始化配置 | 创建配置文件 |
| `Ctrl+Shift+G, A` | 检查认证 | 查看认证状态 |

### 使用 Chord 快捷键

VS Code 支持 chord 快捷键（组合键序列）：

```json
[
  {
    "key": "ctrl+shift+g s",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Sync Now"
  }
]
```

按下 `Ctrl+Shift+G`，释放后再按 `S`。

## 完整配置示例

### 推荐的完整 tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitHub Auto Sync: Sync Now",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared",
        "showReuseMessage": true,
        "clear": false
      },
      "problemMatcher": []
    },
    {
      "label": "GitHub Auto Sync: Initial Sync",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "--initial"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "GitHub Auto Sync: Start Watch",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["watch"],
      "isBackground": true,
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "dedicated"
      },
      "problemMatcher": {
        "pattern": {
          "regexp": "."
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": ".*正在启动监控.*",
          "endsPattern": ".*监控已启动.*"
        }
      }
    },
    {
      "label": "GitHub Auto Sync: Show Status",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["list"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared",
        "clear": true
      }
    },
    {
      "label": "GitHub Auto Sync: Init Config",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["init"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "GitHub Auto Sync: Check Auth",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["auth", "status"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared",
        "clear": true
      }
    },
    {
      "label": "GitHub Auto Sync: Verbose Sync",
      "type": "shell",
      "command": "github-auto-sync",
      "args": ["sync", "-v"],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONIOENCODING": "utf-8"
        }
      },
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

### 推荐的完整 keybindings.json

```json
[
  {
    "key": "ctrl+shift+g s",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Sync Now",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g i",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Initial Sync",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g w",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Start Watch",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g x",
    "command": "workbench.action.tasks.terminate",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g l",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Show Status",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g c",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Init Config",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g a",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Check Auth",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+g v",
    "command": "workbench.action.tasks.runTask",
    "args": "GitHub Auto Sync: Verbose Sync",
    "when": "editorTextFocus"
  }
]
```

## 高级配置

### 自动保存时同步

结合 **Run on Save** 扩展实现保存时自动同步：

1. 安装 [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) 扩展

2. 在 `settings.json` 中添加：

```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": ".*",
        "cmd": "github-auto-sync sync"
      }
    ]
  }
}
```

### 任务依赖配置

配置任务依赖关系，确保按顺序执行：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitHub Auto Sync: Full Setup",
      "dependsOn": [
        "GitHub Auto Sync: Check Auth",
        "GitHub Auto Sync: Init Config",
        "GitHub Auto Sync: Initial Sync"
      ],
      "dependsOrder": "sequence",
      "group": "build"
    }
  ]
}
```

### 输入变量配置

使用输入变量动态指定参数：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitHub Auto Sync: Sync Specific Repo",
      "type": "shell",
      "command": "github-auto-sync",
      "args": [
        "sync",
        "${input:repoName}"
      ],
      "group": "build"
    }
  ],
  "inputs": [
    {
      "id": "repoName",
      "description": "选择要同步的仓库",
      "default": "default",
      "type": "pickString",
      "options": [
        "frontend",
        "backend",
        "docs",
        "default"
      ]
    }
  ]
}
```

### 复合启动配置

在 `.vscode/launch.json` 中集成：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch with Sync",
      "type": "node",
      "request": "launch",
      "preLaunchTask": "GitHub Auto Sync: Sync Now",
      "program": "${workspaceFolder}/app.js"
    }
  ]
}
```

## 使用技巧

### 1. 任务快速访问

- 按 `Ctrl+Shift+P` 打开命令面板
- 输入 `task` 查看所有任务相关命令
- 常用命令：
  - `Tasks: Run Task` - 运行任务
  - `Tasks: Restart Running Task` - 重启任务
  - `Tasks: Terminate Task` - 终止任务
  - `Tasks: Show Running Tasks` - 显示运行中的任务

### 2. 默认构建任务

设置默认构建任务，使用 `Ctrl+Shift+B` 快速执行：

```json
{
  "label": "GitHub Auto Sync: Sync Now",
  "type": "shell",
  "command": "github-auto-sync",
  "args": ["sync"],
  "group": {
    "kind": "build",
    "isDefault": true
  }
}
```

### 3. 状态栏显示

安装 [Status Bar Tasks](https://marketplace.visualstudio.com/items?itemName=GuardRex.status-bar-tasks) 扩展，在状态栏显示常用任务按钮。

### 4. 输出面板管理

- `panel: "shared"` - 所有任务共享一个面板
- `panel: "dedicated"` - 每个任务有独立面板
- `panel: "new"` - 每次运行创建新面板

### 5. 任务过滤

在 `settings.json` 中配置任务过滤：

```json
{
  "task.quickOpen.showAll": true,
  "task.quickOpen.skip": false
}
```

## 故障排除

### 问题 1: 命令未找到

**症状**: `github-auto-sync: command not found`

**解决方案**:

1. 确认已安装 GitHub Auto Sync：
   ```bash
   pip install github-auto-sync
   ```

2. 在 tasks.json 中使用完整路径：
   ```json
   {
     "command": "C:\\Python311\\Scripts\\github-auto-sync.exe"
   }
   ```

3. 或使用 Python 模块方式：
   ```json
   {
     "command": "python",
     "args": ["-m", "github_auto_sync", "sync"]
   }
   ```

### 问题 2: 配置文件未找到

**症状**: `未找到配置文件。请运行 'github-auto-sync init' 初始化配置。`

**解决方案**:

1. 确保工作目录正确：
   ```json
   {
     "options": {
       "cwd": "${workspaceFolder}"
     }
   }
   ```

2. 指定配置文件路径：
   ```json
   {
     "args": ["sync", "--config", "${workspaceFolder}/config.yaml"]
   }
   ```

### 问题 3: 中文乱码

**症状**: 终端输出中文显示为乱码

**解决方案**:

在 tasks.json 中设置环境变量：

```json
{
  "options": {
    "env": {
      "PYTHONIOENCODING": "utf-8",
      "LANG": "zh_CN.UTF-8"
    }
  }
}
```

Windows 系统可能需要：

```json
{
  "options": {
    "shell": {
      "executable": "cmd.exe",
      "args": ["/c", "chcp", "65001", ">nul", "&&"]
    }
  }
}
```

### 问题 4: 后台任务无法停止

**症状**: 监控任务启动后无法通过常规方式停止

**解决方案**:

1. 使用 `workbench.action.tasks.terminate` 命令
2. 在终端面板中点击垃圾桶图标
3. 使用快捷键 `Ctrl+Shift+G, X`

### 问题 5: 快捷键冲突

**症状**: 配置的快捷键不生效

**解决方案**:

1. 检查快捷键冲突：
   - 打开 `Ctrl+K Ctrl+S`
   - 搜索您的快捷键
   - 查看是否有冲突

2. 使用不同的快捷键组合：
   ```json
   {
     "key": "ctrl+alt+shift+s"
   }
   ```

3. 添加 `when` 条件限制触发场景：
   ```json
   {
     "when": "editorTextFocus && !editorReadonly"
   }
   ```

### 调试技巧

1. **查看任务输出**: 确保 `presentation.reveal` 设置为 `"always"`

2. **启用详细日志**: 在命令后添加 `-v` 参数

3. **检查环境变量**: 在任务中添加：
   ```json
   {
     "args": ["auth", "status"]
   }
   ```

4. **手动测试命令**: 在 VS Code 终端中手动运行命令，确认可以正常工作

## 参考资源

- [VS Code 任务系统官方文档](https://code.visualstudio.com/docs/editor/tasks)
- [VS Code 变量参考](https://code.visualstudio.com/docs/editor/variables-reference)
- [VS Code 快捷键配置](https://code.visualstudio.com/docs/getstarted/keybindings)
- [GitHub Auto Sync 主文档](../README.md)
- [IDE 集成总览](./ide-integration.md)
