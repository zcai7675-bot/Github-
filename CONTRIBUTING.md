# 贡献指南

感谢您对 GitHub Auto Sync 项目的关注！我们欢迎并感谢您的贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 GitHub Issues 提交：

1. 检查是否已有类似的问题
2. 如果没有，创建一个新的 Issue
3. 使用清晰的标题和详细的描述
4. 如果是 bug，请提供复现步骤和环境信息

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/yourusername/github-auto-sync.git
   cd github-auto-sync
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **安装开发依赖**
   ```bash
   pip install -e ".[dev]"
   ```

4. **进行修改**
   - 遵循现有的代码风格
   - 添加必要的测试
   - 更新相关文档

5. **运行测试**
   ```bash
   pytest
   ```

6. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

7. **推送到您的 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建 Pull Request**

## 开发规范

### 代码风格

- 使用 [Black](https://black.readthedocs.io/) 进行代码格式化
- 使用 [Flake8](https://flake8.pycqa.org/) 进行代码检查
- 使用 [MyPy](https://mypy.readthedocs.io/) 进行类型检查

### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响代码功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat: 添加自动同步间隔配置
fix: 修复配置文件解析错误
docs: 更新 README 安装说明
```

### 测试要求

- 所有新功能必须包含测试
- 测试覆盖率应保持在 80% 以上
- 使用 pytest 编写测试

### 文档要求

- 更新 README.md 中的相关说明
- 为新功能添加使用示例
- 更新 CHANGELOG.md

## 开发环境设置

### 使用 Makefile (推荐)

```bash
# 安装开发依赖
make install-dev

# 运行所有检查
make check

# 格式化代码
make format

# 运行测试
make test
```

### 使用脚本 (Windows)

```bash
# 安装
scripts\install.bat

# 测试
scripts\test.bat

# 清理
scripts\clean.bat

# 构建
scripts\build.bat
```

### 使用脚本 (Linux/macOS)

```bash
# 安装
./scripts/install.sh

# 测试
./scripts/test.sh

# 清理
./scripts/clean.sh

# 构建
./scripts/build.sh
```

## 代码审查流程

1. 所有代码变更必须通过 Pull Request
2. 至少需要一名维护者的审查批准
3. 所有 CI 检查必须通过
4. 代码必须符合项目风格指南

## 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建发布标签
4. 构建并上传到 PyPI

## 行为准则

- 尊重所有参与者
- 欢迎新手，耐心解答问题
- 专注于建设性的讨论
- 不接受任何形式的骚扰

## 获取帮助

- 查看 [文档](docs/README.md)
- 在 GitHub Discussions 中提问
- 加入我们的社区讨论

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。
