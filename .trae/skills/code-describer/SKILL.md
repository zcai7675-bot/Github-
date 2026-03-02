---
name: "code-describer"
description: "Analyzes code changes and generates meaningful commit messages for GitHub uploads. Invoke when user is syncing code to GitHub and needs semantic commit descriptions instead of generic timestamps."
---

# Code Describer

This skill analyzes code files and generates meaningful, semantic commit messages for GitHub Auto Sync operations.

## When to Invoke

Invoke this skill when:
- User runs `github-auto-sync sync` or `github-auto-sync watch`
- Configuration has `use_ai_description: true` enabled
- There are file changes to be committed
- User needs meaningful commit messages instead of "Auto-sync: timestamp"

## Analysis Process

### 1. Read Changed Files
Read the content of modified/added files to understand:
- File purpose and functionality
- New features or changes
- Bug fixes or improvements
- Refactoring or structural changes

### 2. Identify Code Patterns
Look for:
- **New features**: New functions, classes, modules
- **Bug fixes**: Error handling, corrections, patches
- **Refactoring**: Code restructuring, optimization
- **Documentation**: Comments, README updates
- **Configuration**: Config files, settings changes
- **Tests**: Test files, test cases

### 3. Categorize Changes
Classify changes into categories:
- `[功能]` - New features or functionality
- `[修复]` - Bug fixes
- `[重构]` - Code refactoring
- `[文档]` - Documentation updates
- `[配置]` - Configuration changes
- `[测试]` - Test-related changes
- `[优化]` - Performance improvements
- `[样式]` - UI/styling changes
- `[依赖]` - Dependency updates

## Commit Message Format

```
[类别] 简短描述（不超过50字）

- 详细说明点1
- 详细说明点2
- 详细说明点3
```

### Format Rules
1. **First line**: Category tag + brief summary (max 50 chars)
2. **Body**: Bullet points describing specific changes
3. **Language**: Use the same language as the codebase (Chinese for Chinese projects, English for English projects)
4. **Tone**: Professional and descriptive

## Examples

### Example 1: New Feature
**Files changed**: `auth.py`, `login.html`, `user_model.py`

**Generated description**:
```
[功能] 实现用户认证系统

- 添加用户登录和注册功能
- 实现密码加密存储
- 集成 JWT Token 认证
- 添加登录状态验证中间件
```

### Example 2: Bug Fix
**Files changed**: `database.py`, `config.yaml`

**Generated description**:
```
[修复] 解决数据库连接超时问题

- 添加数据库连接池配置
- 优化连接重试机制
- 增加连接超时异常处理
```

### Example 3: Refactoring
**Files changed**: `api_routes.py`, `middleware.py`

**Generated description**:
```
[重构] 重构 API 路由和中间件结构

- 统一错误处理格式
- 添加请求验证中间件
- 优化路由组织方式
```

### Example 4: Documentation
**Files changed**: `README.md`, `docs/api.md`

**Generated description**:
```
[文档] 更新 API 文档和使用说明

- 添加新的 API 端点文档
- 更新安装和配置说明
- 添加使用示例代码
```

## Implementation Guide

When generating commit descriptions:

1. **Analyze file extensions** to determine file types:
   - `.py` - Python code
   - `.js/.ts` - JavaScript/TypeScript
   - `.html/.css` - Frontend
   - `.md` - Documentation
   - `.yaml/.json` - Configuration

2. **Look for keywords** in code:
   - `def`, `class`, `function` - New functionality
   - `fix`, `bug`, `error` - Bug fixes
   - `refactor`, `restructure` - Refactoring
   - `test`, `spec` - Testing
   - `doc`, `comment` - Documentation

3. **Consider file paths**:
   - `src/` or `app/` - Core functionality
   - `tests/` or `test/` - Testing
   - `docs/` - Documentation
   - `config/` or root config files - Configuration

4. **Handle multiple files**:
   - Group related changes
   - Focus on the main purpose
   - Don't list every single file

## Fallback Behavior

If AI description generation fails or is disabled:
- Fall back to template: `"Auto-sync: {timestamp}"`
- Log the failure reason
- Continue with the sync operation

## Privacy Note

When analyzing code:
- Do not send code to external services
- Analyze locally within the IDE
- Respect `.gitignore` patterns
- Skip sensitive files (credentials, tokens, etc.)
