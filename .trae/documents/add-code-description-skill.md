# 添加代码描述生成 SKILL 的计划

## 目标
创建一个 SKILL，让 AI 在协助用户将代码上传到 GitHub 时，能够：
1. 分析代码文件的功能和用途
2. 生成有意义的提交描述（commit message）
3. 替代简单的 "Auto-sync: timestamp" 格式

## 实现步骤

### 步骤 1: 创建 SKILL 目录结构
- 创建 `.trae/skills/code-describer/` 目录
- 在该目录下创建 `SKILL.md` 文件

### 步骤 2: 编写 SKILL.md 内容
SKILL 需要包含：
- **Frontmatter**: name 和 description
- **触发条件**: 何时调用此 SKILL
- **分析指南**: 如何分析代码功能
- **描述格式**: 生成的描述格式规范
- **示例**: 提供具体的示例说明

### 步骤 3: SKILL 核心功能
SKILL 应该指导 AI：
1. **代码分析**: 读取变更的文件内容
2. **功能识别**: 识别代码的主要功能、模块、类、函数
3. **变更总结**: 总结本次变更的核心内容
4. **描述生成**: 生成简洁、有意义的提交描述

### 步骤 4: 集成到现有工作流
- 修改 `sync.py` 模块，添加调用 AI 生成描述的选项
- 在配置文件中添加 `use_ai_description` 选项
- 保持向后兼容（默认使用模板描述）

### 步骤 5: 测试验证
- 测试 SKILL 是否能正确触发
- 验证生成的描述质量
- 确保不影响现有功能

## SKILL 设计草案

### 触发条件
- 用户执行 `github-auto-sync sync` 或 `github-auto-sync watch`
- 配置中启用了 `use_ai_description: true`
- 有文件变更需要提交

### 描述格式示例
```
[功能] 添加用户认证模块
- 实现登录/注册功能
- 添加密码加密
- 集成 JWT Token

[修复] 修复数据库连接超时问题
- 添加连接池配置
- 优化查询性能

[重构] 重构 API 路由结构
- 统一错误处理
- 添加请求验证中间件
```

## 文件变更计划

### 新增文件
1. `.trae/skills/code-describer/SKILL.md` - SKILL 定义文件

### 修改文件
1. `src/github_auto_sync/config.py` - 添加 `use_ai_description` 配置项
2. `src/github_auto_sync/sync.py` - 集成 AI 描述生成功能
3. `docs/usage.md` - 更新文档，说明 AI 描述功能

## 预期效果

用户使用流程：
```bash
# 1. 启用 AI 描述功能
github-auto-sync config set sync.use_ai_description true

# 2. 同步代码
github-auto-sync sync

# 3. GitHub 上的提交信息显示：
# [功能] 实现用户登录功能
# - 添加登录表单验证
# - 集成会话管理
# - 添加错误提示
```

而不是：
```
Auto-sync: 2024-01-15 10:30:45
```

## 注意事项

1. **性能考虑**: AI 分析可能需要时间，对于大量文件变更需要优化
2. **隐私安全**: 确保不会将敏感代码发送到外部服务
3. **用户控制**: 提供开关让用户选择是否使用 AI 描述
4. **回退机制**: AI 生成失败时回退到模板描述
