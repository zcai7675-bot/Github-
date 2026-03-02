# JetBrains IDE 集成详细指南

本指南详细介绍如何在 JetBrains 系列 IDE（PyCharm、IntelliJ IDEA、WebStorm 等）中配置 GitHub Auto Sync。

## 目录

- [支持的 IDE](#支持的-ide)
- [快速开始](#快速开始)
- [配置 External Tools](#配置-external-tools)
- [配置快捷键](#配置快捷键)
- [配置示例](#配置示例)
- [高级配置](#高级配置)
- [使用技巧](#使用技巧)
- [故障排除](#故障排除)

## 支持的 IDE

GitHub Auto Sync 支持所有 JetBrains 系列的 IDE：

| IDE | 适用场景 |
|-----|---------|
| PyCharm | Python 开发 |
| IntelliJ IDEA | Java/Kotlin 开发 |
| WebStorm | JavaScript/TypeScript 开发 |
| PhpStorm | PHP 开发 |
| Rider | .NET 开发 |
| GoLand | Go 开发 |
| RubyMine | Ruby 开发 |
| CLion | C/C++ 开发 |
| DataGrip | 数据库开发 |
| Android Studio | Android 开发 |

## 快速开始

### 1. 打开 External Tools 设置

**Windows/Linux:**
1. 按 `Ctrl+Alt+S` 打开设置
2. 导航到 **Tools > External Tools**

**macOS:**
1. 按 `Cmd + ,` 打开设置
2. 导航到 **Tools > External Tools**

### 2. 添加新工具

1. 点击 **+** 按钮（或按 `Alt+Insert`）
2. 填写工具配置
3. 点击 **OK** 保存

### 3. 基本配置示例

| 设置项 | 值 |
|-------|-----|
| Name | `GAS: Sync` |
| Program | `github-auto-sync` |
| Arguments | `sync` |
| Working directory | `$ProjectFileDir$` |

## 配置 External Tools

### 详细配置步骤

#### 步骤 1: 打开设置

```
File > Settings (Windows/Linux)
或
IntelliJ IDEA > Preferences (macOS)
```

#### 步骤 2: 导航到 External Tools

```
Tools > External Tools
```

#### 步骤 3: 创建工具组（可选但推荐）

1. 点击 **+** 添加新工具
2. 在 Name 字段中输入工具名称
3. 建议按功能分组命名：
   - `GAS: Sync` - 同步操作
   - `GAS: Watch` - 监控操作
   - `GAS: Status` - 状态查看

#### 步骤 4: 配置工具属性

**基本配置：**

- **Name**: 工具的显示名称
- **Description**: 工具的描述（可选）
- **Group**: 工具组名称（用于分组显示）

**工具设置：**

- **Program**: 可执行文件路径
  - 使用命令名: `github-auto-sync`
  - 或使用完整路径: `C:\Python311\Scripts\github-auto-sync.exe`

- **Arguments**: 命令参数
  - 示例: `sync`
  - 示例: `sync --initial`
  - 示例: `watch`

- **Working directory**: 工作目录
  - `$ProjectFileDir$` - 项目根目录
  - `$FileDir$` - 当前文件所在目录
  - `$ModuleFileDir$` - 模块根目录

### 常用工具配置

#### 1. 立即同步

```
Name: GAS: Sync Now
Description: 立即同步当前项目到 GitHub
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync
Working directory: $ProjectFileDir$

Advanced Options:
  [x] Synchronize files after execution
  [ ] Open console
```

#### 2. 初始同步

```
Name: GAS: Initial Sync
Description: 执行首次全量同步
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync --initial
Working directory: $ProjectFileDir$

Advanced Options:
  [x] Synchronize files after execution
  [x] Open console
```

#### 3. 启动监控

```
Name: GAS: Start Watch
Description: 启动文件监控自动同步
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: watch
Working directory: $ProjectFileDir$

Advanced Options:
  [x] Synchronize files after execution
  [x] Open console
```

#### 4. 查看状态

```
Name: GAS: Show Status
Description: 显示仓库列表和同步状态
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: list
Working directory: $ProjectFileDir$

Advanced Options:
  [ ] Synchronize files after execution
  [x] Open console
```

#### 5. 初始化配置

```
Name: GAS: Init Config
Description: 初始化项目配置文件
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: init
Working directory: $ProjectFileDir$

Advanced Options:
  [x] Synchronize files after execution
  [x] Open console
```

#### 6. 检查认证

```
Name: GAS: Check Auth
Description: 检查 GitHub 认证状态
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: auth status
Working directory: $ProjectFileDir$

Advanced Options:
  [ ] Synchronize files after execution
  [x] Open console
```

#### 7. 详细同步（调试用）

```
Name: GAS: Verbose Sync
Description: 以详细模式执行同步
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync -v
Working directory: $ProjectFileDir$

Advanced Options:
  [ ] Synchronize files after execution
  [x] Open console
```

### 多仓库配置

对于包含多个仓库的项目，配置多个同步工具：

#### 前端仓库同步

```
Name: GAS: Sync Frontend
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync frontend
Working directory: $ProjectFileDir$
```

#### 后端仓库同步

```
Name: GAS: Sync Backend
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync backend
Working directory: $ProjectFileDir$
```

#### 同步所有仓库

```
Name: GAS: Sync All
Group: GitHub Auto Sync

Program: github-auto-sync
Arguments: sync --all
Working directory: $ProjectFileDir$
```

### 高级选项说明

#### Console 设置

**Open console:**
- 勾选: 执行时自动打开运行工具窗口
- 不勾选: 静默执行，不显示输出

**Console encoding:**
- 建议设置为 `UTF-8` 以正确显示中文

#### Output Filters

配置输出过滤器以在输出中创建可点击的链接：

```
Output filters:
  $FILE_PATH$:$LINE$:$COLUMN$ - 文件路径链接
  https://github.com/\S+ - GitHub 链接
```

## 配置快捷键

### 为 External Tools 分配快捷键

#### 步骤 1: 打开快捷键设置

```
File > Settings > Keymap (Windows/Linux)
或
IntelliJ IDEA > Preferences > Keymap (macOS)
```

#### 步骤 2: 查找 External Tools

1. 在搜索框中输入 `external tools`
2. 展开 **External Tools** 节点
3. 展开 **External Tools** 子节点
4. 找到您创建的工具（如 `GAS: Sync Now`）

#### 步骤 3: 添加快捷键

1. 右键点击工具名称
2. 选择 **Add Keyboard Shortcut**
3. 按下您想要的快捷键组合
4. 点击 **OK** 保存

### 推荐快捷键配置

| 工具 | Windows/Linux | macOS |
|-----|---------------|-------|
| GAS: Sync Now | `Ctrl+Alt+Shift+S` | `Cmd+Option+Shift+S` |
| GAS: Initial Sync | `Ctrl+Alt+Shift+I` | `Cmd+Option+Shift+I` |
| GAS: Start Watch | `Ctrl+Alt+Shift+W` | `Cmd+Option+Shift+W` |
| GAS: Show Status | `Ctrl+Alt+Shift+L` | `Cmd+Option+Shift+L` |
| GAS: Init Config | `Ctrl+Alt+Shift+C` | `Cmd+Option+Shift+C` |
| GAS: Check Auth | `Ctrl+Alt+Shift+A` | `Cmd+Option+Shift+A` |

### 快捷键配置示例

#### 配置同步快捷键

1. 在 Keymap 设置中找到 `GAS: Sync Now`
2. 右键点击，选择 **Add Keyboard Shortcut**
3. 按下 `Ctrl+Alt+Shift+S`
4. 如果出现冲突警告，选择 **Leave** 保留两个绑定，或 **Remove** 移除冲突

#### 配置工具组快捷键

您也可以为整个工具组配置快捷键：

1. 在 Keymap 中找到 **External Tools > GitHub Auto Sync**
2. 右键点击组名
3. 选择 **Add Keyboard Shortcut**
4. 这样可以通过一个快捷键访问组内所有工具

### 使用工具栏按钮

#### 添加工具到工具栏

1. 打开 **View > Appearance > Toolbar**（确保工具栏显示）
2. 打开设置：**File > Settings > Appearance & Behavior > Menus and Toolbars**
3. 在右侧找到 **Main Toolbar** 或其他工具栏
4. 点击 **+** 添加操作
5. 搜索并选择您的 External Tool
6. 点击 **OK** 保存

## 配置示例

### 完整的 External Tools 配置

以下是推荐的完整配置列表：

#### 工具组: GitHub Auto Sync

| 名称 | 程序 | 参数 | 工作目录 | 打开控制台 |
|-----|------|------|---------|-----------|
| GAS: Sync Now | github-auto-sync | sync | $ProjectFileDir$ | 是 |
| GAS: Initial Sync | github-auto-sync | sync --initial | $ProjectFileDir$ | 是 |
| GAS: Start Watch | github-auto-sync | watch | $ProjectFileDir$ | 是 |
| GAS: Stop Watch | github-auto-sync | (手动停止) | $ProjectFileDir$ | 是 |
| GAS: Show Status | github-auto-sync | list | $ProjectFileDir$ | 是 |
| GAS: Init Config | github-auto-sync | init | $ProjectFileDir$ | 是 |
| GAS: Check Auth | github-auto-sync | auth status | $ProjectFileDir$ | 是 |
| GAS: Verbose Sync | github-auto-sync | sync -v | $ProjectFileDir$ | 是 |

### 配置文件位置

JetBrains IDE 的配置存储在以下位置：

**Windows:**
```
%USERPROFILE%\.PyCharm<version>\config\tools\External Tools.xml
%USERPROFILE%\.IntelliJIdea<version>\config\tools\External Tools.xml
```

**macOS:**
```
~/Library/Application Support/JetBrains/PyCharm<version>/tools/External Tools.xml
~/Library/Application Support/JetBrains/IntelliJIdea<version>/tools/External Tools.xml
```

**Linux:**
```
~/.config/JetBrains/PyCharm<version>/tools/External Tools.xml
~/.config/JetBrains/IntelliJIdea<version>/tools/External Tools.xml
```

### 手动编辑配置文件

您也可以直接编辑 XML 配置文件：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<toolSet name="External Tools">
  <tool name="GAS: Sync Now" description="立即同步当前项目" showInMainMenu="false" showInEditor="false" showInProject="false" showInSearchPopup="false" disabled="false" useConsole="true" showConsoleOnStdOut="false" showConsoleOnStdErr="true" synchronizeAfterRun="true">
    <exec>
      <option name="COMMAND" value="github-auto-sync" />
      <option name="PARAMETERS" value="sync" />
      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$" />
    </exec>
  </tool>
  <tool name="GAS: Start Watch" description="启动文件监控" showInMainMenu="false" showInEditor="false" showInProject="false" showInSearchPopup="false" disabled="false" useConsole="true" showConsoleOnStdOut="true" showConsoleOnStdErr="true" synchronizeAfterRun="true">
    <exec>
      <option name="COMMAND" value="github-auto-sync" />
      <option name="PARAMETERS" value="watch" />
      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$" />
    </exec>
  </tool>
</toolSet>
```

## 高级配置

### 配置环境变量

#### 在 External Tool 中设置环境变量

JetBrains IDE 的 External Tools 不直接支持环境变量设置，但可以通过以下方式实现：

**方式 1: 使用包装脚本**

创建 `gas-sync.bat` (Windows) 或 `gas-sync.sh` (Linux/macOS)：

```batch
@echo off
set PYTHONIOENCODING=utf-8
github-auto-sync %*
```

然后在 External Tool 中使用：
```
Program: C:ath	oas-sync.bat
Arguments: sync
```

**方式 2: 使用 Python 模块方式**

```
Program: python
Arguments: -m github_auto_sync sync
Working directory: $ProjectFileDir$
```

### 配置 Before Launch 任务

将同步任务集成到运行配置中：

1. 打开 **Run > Edit Configurations**
2. 选择您的运行配置
3. 在底部找到 **Before launch** 部分
4. 点击 **+** 添加 **External tool**
5. 选择 `GAS: Sync Now`
6. 点击 **OK** 保存

这样每次运行项目前都会自动同步到 GitHub。

### 配置 File Watcher（替代方案）

JetBrains IDE 内置的 File Watcher 可以作为替代方案：

1. 打开 **Settings > Tools > File Watchers**
2. 点击 **+** 添加新的 watcher
3. 配置如下：

```
Name: GitHub Auto Sync
File type: Any
Scope: Project Files
Program: github-auto-sync
Arguments: sync
Output paths to refresh: $ProjectFileDir$
Working directory: $ProjectFileDir$
Auto-save edited files: Before calling
Trigger watcher on auto-save: [x]
```

**注意**: 这种方式会在每次保存文件时触发同步，请谨慎使用。

### 多项目配置

对于多模块项目，可以为每个模块配置独立的同步工具：

#### 模块 1: Frontend

```
Name: GAS: Sync Frontend
Program: github-auto-sync
Arguments: sync frontend
Working directory: $ModuleFileDir$
```

#### 模块 2: Backend

```
Name: GAS: Sync Backend
Program: github-auto-sync
Arguments: sync backend
Working directory: $ModuleFileDir$
```

## 使用技巧

### 1. 快速访问 External Tools

**通过菜单访问：**
```
Tools > External Tools > [工具名称]
```

**通过搜索访问：**
1. 按 `Shift` 两次（Search Everywhere）
2. 输入工具名称
3. 选择并执行

**通过操作搜索访问：**
1. 按 `Ctrl+Shift+A`（Find Action）
2. 输入工具名称
3. 选择并执行

### 2. 使用工具窗口

执行 External Tool 时会打开 **Run** 工具窗口：

- **重新运行**: 点击左侧的重新运行按钮
- **停止**: 点击停止按钮（适用于 watch 模式）
- **滚动锁定**: 点击滚动锁定按钮防止自动滚动
- **清空**: 右键点击输出区域选择 Clear All

### 3. 输出窗口技巧

**复制输出：**
- 选中输出内容
- 右键点击选择 **Copy**
- 或按 `Ctrl+C`

**搜索输出：**
- 按 `Ctrl+F` 在输出中搜索
- 支持正则表达式

**导出输出：**
- 右键点击输出区域
- 选择 **Export Text**

### 4. 与版本控制集成

将同步操作与 Git 操作结合：

1. 打开 **Settings > Version Control > Confirmation**
2. 配置在提交前自动同步（通过 Before Launch 任务）

### 5. 使用宏

创建宏来自动化多个操作：

1. 打开 **Edit > Macros > Start Macro Recording**
2. 执行一系列操作（如保存、同步）
3. 点击 **Stop Macro Recording**
4. 命名并保存宏
5. 为宏分配快捷键

## 故障排除

### 问题 1: 命令未找到

**症状**: 运行工具时提示 `'github-auto-sync' 不是内部或外部命令`

**解决方案**:

1. **确认安装:**
   ```bash
   pip install github-auto-sync
   ```

2. **使用完整路径:**
   ```
   Program: C:ython311criptsithub-auto-sync.exe
   ```

3. **检查 PATH:**
   - 打开系统环境变量设置
   - 确认 Python Scripts 目录在 PATH 中
   - 重启 IDE 使环境变量生效

4. **使用 Python 模块方式:**
   ```
   Program: python
   Arguments: -m github_auto_sync sync
   ```

### 问题 2: 配置文件未找到

**症状**: 错误提示 `未找到配置文件`

**解决方案**:

1. **确认工作目录:**
   ```
   Working directory: $ProjectFileDir$
   ```

2. **初始化配置:**
   - 先运行 `GAS: Init Config` 工具
   - 或手动在终端运行 `github-auto-sync init`

3. **指定配置文件路径:**
   ```
   Arguments: sync --config $ProjectFileDir$/config.yaml
   ```

### 问题 3: 中文乱码

**症状**: 控制台输出中文显示为乱码

**解决方案:**

1. **设置控制台编码:**
   - 打开 **Settings > Editor > File Encodings**
   - 设置 **Global Encoding** 和 **Project Encoding** 为 `UTF-8`
   - 设置 **Console Encoding** 为 `UTF-8`

2. **使用包装脚本设置编码:**

   创建 `gas-wrapper.bat`:
   ```batch
   @echo off
   chcp 65001 >nul
   set PYTHONIOENCODING=utf-8
   github-auto-sync %*
   ```

3. **在 IDE 中设置环境变量:**
   - 打开 **Help > Edit Custom VM Options**
   - 添加: `-Dfile.encoding=UTF-8`
   - 重启 IDE

### 问题 4: Watch 模式无法停止

**症状**: 启动 watch 模式后无法停止

**解决方案:**

1. **使用停止按钮:**
   - 在 Run 工具窗口中点击红色停止按钮

2. **使用快捷键:**
   - 按 `Ctrl+F2` 停止当前运行

3. **通过任务管理器:**
   - Windows: 打开任务管理器，结束 python 进程
   - macOS/Linux: 使用 `kill` 命令结束进程

### 问题 5: 快捷键不生效

**症状**: 配置的快捷键无法触发工具

**解决方案:**

1. **检查快捷键冲突:**
   - 打开 **Settings > Keymap**
   - 找到您的快捷键
   - 查看是否有冲突

2. **使用不同的快捷键:**
   - 尝试使用其他组合键
   - 例如: `Ctrl+Alt+Shift+G`

3. **检查焦点:**
   - 某些快捷键只在特定上下文生效
   - 确保编辑器处于焦点状态

### 问题 6: 权限错误

**症状**: 认证错误或权限不足

**解决方案:**

1. **检查认证状态:**
   - 运行 `GAS: Check Auth` 工具

2. **重新登录:**
   - 在终端运行 `github-auto-sync auth login`

3. **检查 Token 权限:**
   - 确认 GitHub Token 有 `repo` 权限
   - 确认 Token 未过期

### 调试技巧

1. **启用详细输出:**
   - 使用 `GAS: Verbose Sync` 工具
   - 或在 Arguments 中添加 `-v`

2. **检查工作目录:**
   - 在 Arguments 中添加 `&& pwd` (Linux/macOS) 或 `&& cd` (Windows)
   - 确认工作目录正确

3. **测试命令:**
   - 在 IDE 终端中手动运行命令
   - 确认命令可以正常工作

4. **查看事件日志:**
   - 打开 **View > Tool Windows > Event Log**
   - 查看错误详情

## 参考资源

- [JetBrains External Tools 文档](https://www.jetbrains.com/help/idea/settings-tools-external-tools.html)
- [JetBrains 快捷键文档](https://www.jetbrains.com/help/idea/mastering-keyboard-shortcuts.html)
- [PyCharm 官方文档](https://www.jetbrains.com/help/pycharm/)
- [IntelliJ IDEA 官方文档](https://www.jetbrains.com/help/idea/)
- [GitHub Auto Sync 主文档](../README.md)
- [IDE 集成总览](./ide-integration.md)

## 获取帮助

如果在 JetBrains IDE 集成过程中遇到问题：

1. 查看详细指南文档:
   - [IDE 集成总览](./ide-integration.md)
   - [VS Code 集成详细指南](./vscode-integration.md)

2. 运行诊断命令:
   ```bash
   github-auto-sync --version
   github-auto-sync auth status
   github-auto-sync list
   ```

3. 提交 Issue:
   - GitHub Issues: https://github.com/yourusername/github-auto-sync/issues
