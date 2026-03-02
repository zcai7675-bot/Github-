"""
pytest 配置和 fixtures

提供测试所需的共享 fixtures 和配置。
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock

import pytest


# =============================================================================
# 路径 Fixtures
# =============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """创建临时文件"""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("test content")
    yield file_path


@pytest.fixture
def sample_repo_dir(temp_dir: Path) -> Path:
    """创建示例仓库目录结构"""
    # 创建一些文件和子目录
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "main.py").write_text("print('hello')")
    (temp_dir / "src" / "utils.py").write_text("def helper(): pass")
    (temp_dir / "tests").mkdir()
    (temp_dir / "tests" / "test_main.py").write_text("def test_main(): pass")
    (temp_dir / "README.md").write_text("# Test Project")
    return temp_dir


# =============================================================================
# Git Fixtures
# =============================================================================


@pytest.fixture
def mock_git_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """创建模拟的 git 仓库"""
    import subprocess
    
    # 初始化 git 仓库
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_dir, check=True, capture_output=True
    )
    
    # 创建初始提交
    (temp_dir / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_dir, check=True, capture_output=True
    )
    
    yield temp_dir


# =============================================================================
# GitHub API Fixtures
# =============================================================================


@pytest.fixture
def mock_github_token() -> str:
    """返回模拟的 GitHub token"""
    return "ghp_test_token_123456789012345678901234567890123456"


@pytest.fixture
def mock_github_user() -> dict:
    """返回模拟的 GitHub 用户信息"""
    return {
        "login": "testuser",
        "id": 123456,
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://avatars.githubusercontent.com/u/123456",
        "html_url": "https://github.com/testuser",
        "bio": "Test bio",
        "location": "Test City",
        "company": "Test Company",
        "blog": "https://testuser.github.io",
        "public_repos": 10,
        "private_repos": 5,
        "total_repos": 15,
        "followers": 100,
        "following": 50,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "type": "User",
    }


@pytest.fixture
def mock_github_repo() -> dict:
    """返回模拟的 GitHub 仓库信息"""
    return {
        "name": "test-repo",
        "full_name": "testuser/test-repo",
        "description": "Test repository",
        "private": True,
        "html_url": "https://github.com/testuser/test-repo",
        "clone_url": "https://github.com/testuser/test-repo.git",
        "ssh_url": "git@github.com:testuser/test-repo.git",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-06-01T00:00:00Z",
        "pushed_at": "2023-06-01T00:00:00Z",
        "stargazers_count": 10,
        "watchers_count": 10,
        "forks_count": 5,
        "open_issues_count": 2,
        "language": "Python",
        "default_branch": "main",
        "size": 1024,
        "archived": False,
        "disabled": False,
        "topics": ["python", "testing"],
        "has_issues": True,
        "has_wiki": True,
        "has_pages": False,
        "has_downloads": True,
        "license": "MIT",
    }


@pytest.fixture
def mock_rate_limit() -> dict:
    """返回模拟的 API 速率限制信息"""
    return {
        "limit": 5000,
        "remaining": 4990,
        "reset": 1234567890,
        "used": 10,
    }


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def sample_config_dict() -> dict:
    """返回示例配置字典"""
    return {
        "github": {
            "token": "ghp_test_token",
            "username": "testuser",
        },
        "repositories": [
            {
                "name": "my-project",
                "local_path": "./my-project",
                "remote_url": "",
                "branch": "main",
                "auto_sync": True,
                "ignore_patterns": [
                    ".git/",
                    "__pycache__/",
                    "*.pyc",
                ],
            }
        ],
        "sync": {
            "batch_window": 30,
            "max_files_per_commit": 50,
            "commit_message_template": "auto-sync: {action} {files} files",
            "auto_push": True,
            "auto_pull": True,
            "conflict_strategy": "skip",
        },
        "logging": {
            "level": "INFO",
            "file": "",
            "color": True,
        },
        "notifications": {
            "on_error": True,
            "on_success": False,
        },
    }


@pytest.fixture
def sample_config_yaml() -> str:
    """返回示例配置 YAML 字符串"""
    return """
github:
  token: "ghp_test_token"
  username: "testuser"

repositories:
  - name: "my-project"
    local_path: "./my-project"
    remote_url: ""
    branch: "main"
    auto_sync: true
    ignore_patterns:
      - ".git/"
      - "__pycache__/"
      - "*.pyc"

sync:
  batch_window: 30
  max_files_per_commit: 50
  commit_message_template: "auto-sync: {action} {files} files"
  auto_push: true
  auto_pull: true
  conflict_strategy: "skip"

logging:
  level: "INFO"
  file: ""
  color: true

notifications:
  on_error: true
  on_success: false
"""


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_keyring() -> Generator[MagicMock, None, None]:
    """模拟 keyring 模块"""
    with pytest.mock.patch("github_auto_sync.auth.keyring") as mock:
        mock.get_password.return_value = None
        mock.set_password.return_value = None
        mock.delete_password.return_value = None
        yield mock


@pytest.fixture
def mock_requests() -> Generator[MagicMock, None, None]:
    """模拟 requests 模块"""
    with pytest.mock.patch("github_auto_sync.auth.requests") as mock:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock.get.return_value = mock_response
        yield mock


@pytest.fixture
def mock_github() -> Generator[MagicMock, None, None]:
    """模拟 PyGithub 模块"""
    with pytest.mock.patch("github_auto_sync.github_client.Github") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # 模拟用户
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_user.id = 123456
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.avatar_url = "https://avatars.githubusercontent.com/u/123456"
        mock_user.html_url = "https://github.com/testuser"
        mock_user.public_repos = 10
        mock_user.total_private_repos = 5
        mock_user.followers = 100
        mock_user.following = 50
        
        mock_instance.get_user.return_value = mock_user
        mock_instance.get_rate_limit.return_value = MagicMock(
            core=MagicMock(limit=5000, remaining=4990, used=10)
        )
        
        yield mock


@pytest.fixture
def mock_repo() -> MagicMock:
    """模拟 GitPython Repo 对象"""
    mock = MagicMock()
    mock.is_dirty.return_value = False
    mock.untracked_files = []
    mock.active_branch.name = "main"
    mock.head.is_valid.return_value = True
    mock.head.is_detached = False
    
    # 模拟提交
    mock_commit = MagicMock()
    mock_commit.hexsha = "abc123def456"
    mock_commit.message = "Test commit"
    mock_commit.author.name = "Test User"
    mock_commit.author.email = "test@example.com"
    mock.head.commit = mock_commit
    
    # 模拟远程
    mock_remote = MagicMock()
    mock_remote.name = "origin"
    mock_remote.urls = ["https://github.com/testuser/test-repo.git"]
    mock.remotes = [mock_remote]
    
    # 模拟分支
    mock_branch = MagicMock()
    mock_branch.name = "main"
    mock.branches = [mock_branch]
    
    return mock


@pytest.fixture
def mock_observer() -> Generator[MagicMock, None, None]:
    """模拟 watchdog Observer"""
    with pytest.mock.patch("github_auto_sync.watcher.Observer") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """清理环境变量的 fixture"""
    # 保存原始环境变量
    original_env = {
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
        "GITHUB_USERNAME": os.environ.get("GITHUB_USERNAME"),
        "GITHUB_BATCH_WINDOW": os.environ.get("GITHUB_BATCH_WINDOW"),
        "GITHUB_LOG_LEVEL": os.environ.get("GITHUB_LOG_LEVEL"),
    }
    
    # 清除测试相关的环境变量
    for key in original_env:
        if key in os.environ:
            del os.environ[key]
    
    yield
    
    # 恢复原始环境变量
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


# =============================================================================
# pytest 配置
# =============================================================================


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 自动标记单元测试
        if "test_" in item.nodeid and not any(
            marker.name in ["integration", "slow"] for marker in item.own_markers
        ):
            item.add_marker(pytest.mark.unit)
