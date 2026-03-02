# GitHub Auto Sync 贡献指南

感谢您对 GitHub Auto Sync 项目的关注！本文档提供了参与项目开发的指南。

## 目录

- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码风格](#代码风格)
- [测试要求](#测试要求)
- [Pull Request 流程](#pull-request-流程)

---

## 如何贡献

### 贡献方式

您可以通过以下方式参与项目：

1. **报告 Bug**
   - 使用 GitHub Issues 报告问题
   - 提供详细的复现步骤
   - 包含环境信息和错误日志

2. **提交功能请求**
   - 描述您希望添加的功能
   - 解释使用场景和预期行为
   - 如果可能，提供实现思路

3. **改进文档**
   - 修复文档中的错误
   - 添加更多示例和说明
   - 翻译文档到其他语言

4. **提交代码**
   - 修复已知的 Bug
   - 实现新功能
   - 优化性能和代码质量

5. **代码审查**
   - 审查其他贡献者的 Pull Request
   - 提供建设性的反馈

### 行为准则

参与本项目时，请遵守以下准则：

- 尊重所有参与者
- 接受建设性的批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 开发环境设置

### 系统要求

- Python 3.8 或更高版本
- Git 2.0 或更高版本
- 虚拟环境工具（推荐 venv 或 conda）

### 克隆仓库

```bash
# 克隆仓库
git clone https://github.com/yourusername/github-auto-sync.git
cd github-auto-sync

# 添加上游仓库（用于同步更新）
git remote add upstream https://github.com/original/github-auto-sync.git
```

### 创建虚拟环境

**使用 venv：**
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**使用 conda：**
```bash
# 创建环境
conda create -n github-auto-sync python=3.11

# 激活环境
conda activate github-auto-sync
```

### 安装开发依赖

```bash
# 安装项目（可编辑模式）
pip install -e .

# 安装开发依赖
pip install -r requirements-dev.txt
```

`requirements-dev.txt` 包含：
```
# 测试工具
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0

# 代码质量
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0
pylint>=2.17.0

# 文档
sphinx>=6.0.0
sphinx-rtd-theme>=1.2.0

# 调试
ipdb>=0.13.0
ipython>=8.0.0
```

### 验证安装

```bash
# 检查安装
github-auto-sync --version

# 运行测试
pytest --version

# 检查代码格式工具
black --version
isort --version
flake8 --version
mypy --version
```

### 配置 Git

```bash
# 配置用户名和邮箱
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 配置 Git 钩子（可选）
# 安装 pre-commit
pip install pre-commit
pre-commit install
```

### 配置 IDE（推荐）

**VS Code 配置：**

创建 `.vscode/settings.json`：
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

**PyCharm 配置：**
- 设置 Python 解释器为虚拟环境
- 启用 Black 格式化
- 配置 isort 导入排序
- 启用 mypy 类型检查

---

## 代码风格

### Python 代码风格

本项目使用以下工具保持代码风格一致：

#### Black（代码格式化）

```bash
# 格式化所有代码
black src/

# 检查格式（不修改）
black --check src/

# 格式化特定文件
black src/github_auto_sync/config.py
```

配置（`pyproject.toml`）：
```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### isort（导入排序）

```bash
# 排序导入
isort src/

# 检查导入顺序（不修改）
isort --check-only src/

# 显示差异
isort --diff src/
```

配置（`pyproject.toml`）：
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

#### Flake8（代码检查）

```bash
# 检查代码
flake8 src/

# 检查特定文件
flake8 src/github_auto_sync/config.py
```

配置（`setup.cfg`）：
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info,
    .venv,
    venv
```

#### mypy（类型检查）

```bash
# 类型检查
mypy src/

# 显示错误代码
mypy --show-error-codes src/
```

配置（`pyproject.toml`）：
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

### 代码风格规范

#### 命名规范

| 类型 | 命名方式 | 示例 |
|------|----------|------|
| 模块 | 小写 + 下划线 | `config.py`, `github_client.py` |
| 类 | 大驼峰 | `Config`, `GitHubClient` |
| 函数 | 小写 + 下划线 | `load_config()`, `validate_token()` |
| 常量 | 大写 + 下划线 | `DEFAULT_CONFIG_FILENAME`, `GITHUB_API_URL` |
| 变量 | 小写 + 下划线 | `config_path`, `repo_name` |
| 私有成员 | 下划线前缀 | `_config`, `_validate()` |

#### 文档字符串规范

使用 Google 风格的文档字符串：

```python
def example_function(param1: int, param2: str) -> bool:
    """
    简短描述函数的功能。
    
    详细描述函数的行为、使用场景和注意事项。
    可以包含多行文字。
    
    Args:
        param1: 第一个参数的描述
        param2: 第二个参数的描述
        
    Returns:
        返回值的描述
        
    Raises:
        ValueError: 当参数无效时抛出
        TypeError: 当类型不匹配时抛出
        
    Examples:
        >>> example_function(1, "test")
        True
        >>> example_function(0, "test")
        False
    """
    pass
```

#### 类型注解

所有函数都应包含类型注解：

```python
from typing import Dict, List, Optional, Union

def process_data(
    data: Dict[str, Union[str, int]],
    options: Optional[List[str]] = None,
    verbose: bool = False
) -> List[str]:
    """处理数据并返回结果列表。"""
    results: List[str] = []
    # ...
    return results
```

#### 注释规范

```python
# 好的注释：解释为什么，而不是做什么
# 使用二分查找因为列表已排序
index = binary_search(sorted_list, target)

# 不好的注释：重复代码
# 将 x 加 1
x += 1

# 使用 TODO 标记待办事项
# TODO: 优化性能，当前复杂度为 O(n^2)

# 使用 FIXME 标记需要修复的问题
# FIXME: 处理边界情况
```

### 代码组织

#### 模块结构

```python
"""
模块简短描述。

详细描述模块的功能和使用方法。
"""

# 标准库导入
import os
from pathlib import Path
from typing import Dict, List, Optional

# 第三方库导入
import yaml
from click import echo

# 本地导入
from .auth import get_auth_token
from .exceptions import ConfigError

# 常量定义
DEFAULT_CONFIG_FILENAME = ".github-auto-sync.yml"
ENV_PREFIX = "GITHUB_"

# 类定义
class Config:
    """配置类。"""
    pass

# 函数定义
def load_config() -> Config:
    """加载配置。"""
    pass

# 私有函数
def _validate_config(data: Dict) -> bool:
    """验证配置数据（私有函数）。"""
    pass
```

#### 导入排序

```python
# 1. 标准库
import os
import sys
from pathlib import Path
from typing import Dict, List

# 2. 第三方库
import click
import requests
from github import Github

# 3. 本地应用/库
from .auth import authenticate
from .config import Config
from .utils import helper_function
```

---

## 测试要求

### 测试框架

本项目使用 pytest 作为测试框架。

### 测试文件组织

```
tests/
├── __init__.py
├── conftest.py              # pytest 配置和 fixtures
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_auth.py
│   ├── test_github_client.py
│   ├── test_sync.py
│   ├── test_watcher.py
│   └── test_git_operations.py
├── integration/             # 集成测试
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_end_to_end.py
└── fixtures/                # 测试数据
    ├── config_files/
    └── sample_repos/
```

### 编写测试

#### 基本测试结构

```python
# tests/unit/test_config.py
import pytest
from pathlib import Path

from github_auto_sync.config import Config, RepositoryConfig


class TestConfig:
    """Config 类的测试。"""
    
    def test_load_valid_config(self, tmp_path: Path):
        """测试加载有效的配置文件。"""
        # 准备
        config_file = tmp_path / "config.yml"
        config_file.write_text("""
github:
  token: "test_token"
  username: "test_user"
repositories: []
""")
        
        # 执行
        config = Config.load(config_file)
        
        # 验证
        assert config.github["token"] == "test_token"
        assert config.github["username"] == "test_user"
    
    def test_load_missing_config(self):
        """测试加载不存在的配置文件。"""
        with pytest.raises(FileNotFoundError):
            Config.load("/nonexistent/config.yml")
    
    def test_validate_empty_config(self):
        """测试验证空配置。"""
        config = Config()
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("token" in e.lower() for e in errors)
```

#### 使用 Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from unittest.mock import Mock

from github_auto_sync.config import Config, RepositoryConfig


@pytest.fixture
def sample_config() -> Config:
    """提供示例配置。"""
    return Config(
        github={"token": "test_token", "username": "test_user"},
        repositories=[
            RepositoryConfig(
                name="test-repo",
                local_path="/tmp/test-repo",
                branch="main"
            )
        ]
    )


@pytest.fixture
def mock_github_client():
    """提供模拟的 GitHub 客户端。"""
    client = Mock()
    client.get_user_info.return_value = {
        "login": "test_user",
        "id": 12345
    }
    return client


@pytest.fixture
def temp_repo(tmp_path: Path):
    """提供临时仓库目录。"""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    # 初始化 git 仓库
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    
    yield repo_path
    
    # 清理
    import shutil
    shutil.rmtree(repo_path, ignore_errors=True)
```

#### 使用 Mocks

```python
# tests/unit/test_auth.py
from unittest.mock import Mock, patch
import pytest

from github_auto_sync.auth import validate_token, AuthenticationError


class TestAuth:
    """认证模块的测试。"""
    
    @patch("github_auto_sync.auth.requests.get")
    def test_validate_valid_token(self, mock_get):
        """测试验证有效的 token。"""
        # 模拟成功的响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "test_user"}
        mock_get.return_value = mock_response
        
        # 执行
        valid, info = validate_token("ghp_valid_token")
        
        # 验证
        assert valid is True
        assert info == "test_user"
    
    @patch("github_auto_sync.auth.requests.get")
    def test_validate_invalid_token(self, mock_get):
        """测试验证无效的 token。"""
        # 模拟失败的响应
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        # 执行
        valid, info = validate_token("ghp_invalid_token")
        
        # 验证
        assert valid is False
        assert "无效" in info or "invalid" in info.lower()
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_config.py

# 运行特定测试类
pytest tests/unit/test_config.py::TestConfig

# 运行特定测试方法
pytest tests/unit/test_config.py::TestConfig::test_load_valid_config

# 显示详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=src/github_auto_sync --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src/github_auto_sync --cov-report=html

# 只运行失败的测试
pytest --lf

# 在失败时停止
pytest -x

# 并行运行测试（需要 pytest-xdist）
pytest -n auto
```

### 测试覆盖率要求

- 总体覆盖率：>= 80%
- 核心模块覆盖率：>= 90%
- 新代码覆盖率：>= 90%

```bash
# 检查覆盖率
pytest --cov=src/github_auto_sync --cov-fail-under=80
```

### 测试最佳实践

1. **测试名称应该描述行为：**
   ```python
   # 好的测试名
   def test_returns_error_when_token_is_invalid():
       pass
   
   # 不好的测试名
   def test_invalid_token():
       pass
   ```

2. **一个测试只验证一个概念：**
   ```python
   # 好的做法
   def test_config_validates_required_fields():
       config = Config()
       errors = config.validate()
       assert any("token" in e for e in errors)
   
   def test_config_validates_repository_paths():
       config = Config(repositories=[RepositoryConfig(name="", local_path="")])
       errors = config.validate()
       assert any("name" in e for e in errors)
   ```

3. **使用 Arrange-Act-Assert 模式：**
   ```python
   def test_example():
       # Arrange
       input_data = {"key": "value"}
       
       # Act
       result = process_data(input_data)
       
       # Assert
       assert result == expected_output
   ```

4. **避免测试之间的依赖：**
   - 每个测试应该独立运行
   - 使用 fixtures 设置和清理状态
   - 不要依赖测试执行顺序

---

## Pull Request 流程

### 准备工作

1. **创建 Issue（推荐）**
   - 描述要解决的问题或要添加的功能
   - 等待维护者的反馈
   - 确认方案后再开始编码

2. **同步上游代码：**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

3. **创建功能分支：**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/issue-description
   ```

### 分支命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 功能 | `feature/描述` | `feature/add-auto-sync` |
| 修复 | `fix/描述` | `fix/config-loading-error` |
| 文档 | `docs/描述` | `docs/update-api-reference` |
| 重构 | `refactor/描述` | `refactor/simplify-sync-logic` |
| 测试 | `test/描述` | `test/add-watcher-tests` |

### 开发流程

1. **编写代码**
   - 遵循代码风格规范
   - 添加适当的注释和文档字符串
   - 保持代码简洁和可读

2. **编写测试**
   - 为新功能添加测试
   - 确保测试通过
   - 保持或提高代码覆盖率

3. **本地验证**
   ```bash
   # 格式化代码
   black src/ tests/
   isort src/ tests/
   
   # 代码检查
   flake8 src/ tests/
   mypy src/
   
   # 运行测试
   pytest --cov=src/github_auto_sync
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add automatic sync feature
   
   - Implement FileWatcher integration
   - Add batch processing for file changes
   - Update configuration options
   
   Closes #123"
   ```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）：**

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建过程或辅助工具的变动 |

**示例：**

```
feat(sync): add conflict resolution strategies

Add three conflict resolution strategies:
- skip: skip conflicting files
- overwrite: use local version
- merge: manual merge required

Update configuration to support conflict_strategy option.
Add tests for all strategies.

Closes #456
```

```
fix(config): handle missing config file gracefully

Instead of crashing when config file is not found,
show a helpful error message with instructions.

Fixes #789
```

```
docs(api): add examples for SyncManager class

Add comprehensive examples for:
- Initial sync
- Incremental sync
- Auto sync with callbacks
```

### 提交 PR

1. **推送到你的 Fork：**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **创建 Pull Request：**
   - 访问 GitHub 仓库页面
   - 点击 "New Pull Request"
   - 选择你的分支

3. **填写 PR 描述：**
   ```markdown
   ## 描述
   
   简要描述这个 PR 做了什么。
   
   ## 变更类型
   
   - [ ] Bug 修复
   - [ ] 新功能
   - [ ] 文档更新
   - [ ] 性能优化
   - [ ] 代码重构
   
   ## 测试
   
   - [ ] 添加了单元测试
   - [ ] 添加了集成测试
   - [ ] 所有测试通过
   - [ ] 覆盖率没有下降
   
   ## 检查清单
   
   - [ ] 代码遵循项目风格规范
   - [ ] 添加了适当的文档
   - [ ] 更新了 CHANGELOG（如果适用）
   - [ ] 本地测试通过
   
   ## 相关 Issue
   
   Closes #123
   ```

4. **等待审查：**
   - 维护者会审查你的代码
   - 根据反馈进行修改
   - 保持耐心和尊重

### 处理审查反馈

1. **查看反馈：**
   - 认真阅读每一条评论
   - 如果有疑问，可以询问

2. **进行修改：**
   ```bash
   # 修改代码
   # ...
   
   # 提交修改
   git add .
   git commit -m "refactor: address review feedback
   
   - Simplify error handling
   - Add more descriptive variable names
   - Update docstrings"
   
   git push origin feature/your-feature-name
   ```

3. **解决对话：**
   - 在 GitHub 上标记已解决的评论
   - 如果需要，回复解释你的修改

### PR 合并

- PR 需要至少一个维护者的批准
- 所有 CI 检查必须通过
- 使用 "Squash and Merge" 方式合并
- 合并后删除功能分支

---

## 发布流程

### 版本号规范

使用 [语义化版本](https://semver.org/lang/zh-CN/)：

- `MAJOR.MINOR.PATCH`
- MAJOR：不兼容的 API 修改
- MINOR：向下兼容的功能添加
- PATCH：向下兼容的问题修复

### 发布步骤

1. **更新版本号：**
   ```python
   # src/github_auto_sync/__init__.py
   __version__ = "0.2.0"
   ```

2. **更新 CHANGELOG：**
   ```markdown
   ## [0.2.0] - 2024-01-15
   
   ### 新增
   - 添加自动同步功能
   - 支持多仓库管理
   
   ### 修复
   - 修复配置文件解析错误
   
   ### 改进
   - 优化同步性能
   ```

3. **创建 Git Tag：**
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

4. **创建 GitHub Release：**
   - 访问 Releases 页面
   - 点击 "Draft a new release"
   - 选择新创建的 tag
   - 填写发布说明
   - 发布

5. **发布到 PyPI：**
   ```bash
   # 构建
   python -m build
   
   # 上传到 PyPI
   python -m twine upload dist/*
   ```

---

## 获取帮助

如果在贡献过程中遇到问题：

1. **查看文档：**
   - [使用指南](./usage.md)
   - [API 文档](./api.md)
   - [故障排除](./troubleshooting.md)

2. **搜索 Issues：**
   - 查看是否有人遇到过类似问题
   - 参考已解决的 Issue

3. **提问：**
   - 在 Issue 中提问
   - 加入社区讨论

4. **联系维护者：**
   - 发送邮件到 support@github-auto-sync.dev

---

## 许可证

通过贡献代码，您同意您的贡献将在项目的 [MIT 许可证](../LICENSE) 下发布。
