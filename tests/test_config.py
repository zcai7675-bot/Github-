"""
配置模块单元测试

测试 Config 类及其相关功能。
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from github_auto_sync.config import (
    Config,
    RepositoryConfig,
    SyncConfig,
    LoggingConfig,
    NotificationConfig,
    DEFAULT_CONFIG_FILENAME,
    ENV_PREFIX,
    find_config_file,
    init_config,
)


# =============================================================================
# RepositoryConfig 测试
# =============================================================================


class TestRepositoryConfig:
    """RepositoryConfig 类测试"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        
        assert config.name == "test-repo"
        assert config.local_path == "/path/to/repo"
        assert config.remote_url == ""
        assert config.branch == "main"
        assert config.auto_sync is True
        assert ".git/" in config.ignore_patterns
        assert "__pycache__/" in config.ignore_patterns
    
    def test_init_with_custom_values(self):
        """测试自定义值初始化"""
        config = RepositoryConfig(
            name="test-repo",
            local_path="/path/to/repo",
            remote_url="https://github.com/user/repo.git",
            branch="develop",
            auto_sync=False,
            ignore_patterns=["*.log", "temp/"],
        )
        
        assert config.remote_url == "https://github.com/user/repo.git"
        assert config.branch == "develop"
        assert config.auto_sync is False
        assert config.ignore_patterns == ["*.log", "temp/"]
    
    def test_empty_name_raises_error(self):
        """测试空名称抛出错误"""
        with pytest.raises(ValueError, match="Repository name cannot be empty"):
            RepositoryConfig(name="", local_path="/path/to/repo")
    
    def test_empty_local_path_raises_error(self):
        """测试空本地路径抛出错误"""
        with pytest.raises(ValueError, match="local_path cannot be empty"):
            RepositoryConfig(name="test-repo", local_path="")
    
    def test_empty_branch_defaults_to_main(self):
        """测试空分支默认为 main"""
        config = RepositoryConfig(name="test-repo", local_path="/path/to/repo", branch="")
        assert config.branch == "main"


# =============================================================================
# SyncConfig 测试
# =============================================================================


class TestSyncConfig:
    """SyncConfig 类测试"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        config = SyncConfig()
        
        assert config.batch_window == 30
        assert config.max_files_per_commit == 50
        assert config.commit_message_template == "auto-sync: {action} {files} files"
        assert config.auto_push is True
        assert config.auto_pull is True
        assert config.conflict_strategy == "skip"
    
    def test_negative_batch_window_normalized(self):
        """测试负批量窗口被规范化"""
        config = SyncConfig(batch_window=-10)
        assert config.batch_window == 30
    
    def test_zero_max_files_normalized(self):
        """测试零最大文件数被规范化"""
        config = SyncConfig(max_files_per_commit=0)
        assert config.max_files_per_commit == 50
    
    def test_invalid_conflict_strategy_normalized(self):
        """测试无效冲突策略被规范化"""
        config = SyncConfig(conflict_strategy="invalid")
        assert config.conflict_strategy == "skip"
    
    def test_valid_conflict_strategies(self):
        """测试有效冲突策略"""
        for strategy in ["skip", "overwrite", "merge"]:
            config = SyncConfig(conflict_strategy=strategy)
            assert config.conflict_strategy == strategy


# =============================================================================
# LoggingConfig 测试
# =============================================================================


class TestLoggingConfig:
    """LoggingConfig 类测试"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.file == ""
        assert config.color is True
    
    def test_invalid_level_normalized(self):
        """测试无效日志级别被规范化"""
        config = LoggingConfig(level="INVALID")
        assert config.level == "INFO"
    
    def test_valid_levels(self):
        """测试有效日志级别"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            config = LoggingConfig(level=level)
            assert config.level == level
    
    def test_level_case_normalization(self):
        """测试日志级别大小写规范化"""
        config = LoggingConfig(level="debug")
        assert config.level == "DEBUG"


# =============================================================================
# NotificationConfig 测试
# =============================================================================


class TestNotificationConfig:
    """NotificationConfig 类测试"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        config = NotificationConfig()
        
        assert config.on_error is True
        assert config.on_success is False


# =============================================================================
# Config 类测试 - 初始化
# =============================================================================


class TestConfigInitialization:
    """Config 类初始化测试"""
    
    def test_init_with_defaults(self):
        """测试默认初始化"""
        config = Config()
        
        assert config.github == {"token": "", "username": ""}
        assert config.repositories == []
        assert isinstance(config.sync, SyncConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.notifications, NotificationConfig)
        assert config.config_path is None
        assert config.is_loaded is False
    
    def test_init_with_values(self):
        """测试带值初始化"""
        repo_config = RepositoryConfig(name="test", local_path="/path")
        config = Config(
            github={"token": "test-token", "username": "testuser"},
            repositories=[repo_config],
        )
        
        assert config.github["token"] == "test-token"
        assert config.github["username"] == "testuser"
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "test"


# =============================================================================
# Config 类测试 - YAML 加载和保存
# =============================================================================


class TestConfigLoadSave:
    """Config 类加载和保存测试"""
    
    def test_load_from_yaml(self, temp_dir: Path, sample_config_yaml: str):
        """测试从 YAML 文件加载"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text(sample_config_yaml)
        
        config = Config.load(config_path)
        
        assert config.is_loaded is True
        assert config.config_path == config_path
        assert config.github["token"] == "ghp_test_token"
        assert config.github["username"] == "testuser"
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "my-project"
    
    def test_load_file_not_found(self, temp_dir: Path):
        """测试文件不存在时抛出错误"""
        config_path = temp_dir / "nonexistent.yml"
        
        with pytest.raises(FileNotFoundError):
            Config.load(config_path)
    
    def test_load_create_default(self, temp_dir: Path):
        """测试创建默认配置文件"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        
        config = Config.load(config_path, create_default=True)
        
        assert config_path.exists()
        assert config.is_loaded is True
    
    def test_load_invalid_yaml(self, temp_dir: Path):
        """测试无效 YAML 格式"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ValueError, match="Invalid YAML format"):
            Config.load(config_path)
    
    def test_save_to_yaml(self, temp_dir: Path):
        """测试保存到 YAML 文件"""
        config = Config()
        config.github = {"token": "test-token", "username": "testuser"}
        config.repositories = [RepositoryConfig(name="test", local_path="/path")]
        
        config_path = temp_dir / "output.yml"
        config.save(config_path)
        
        assert config_path.exists()
        
        # 验证保存的内容
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        assert data["github"]["token"] == "test-token"
        assert data["repositories"][0]["name"] == "test"
    
    def test_save_uses_loaded_path(self, temp_dir: Path):
        """测试保存使用加载时的路径"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  token: test\n")
        
        config = Config.load(config_path)
        config.github["token"] = "updated"
        config.save()  # 不指定路径
        
        # 重新加载验证
        config2 = Config.load(config_path)
        assert config2.github["token"] == "updated"


# =============================================================================
# Config 类测试 - 环境变量覆盖
# =============================================================================


class TestConfigEnvOverride:
    """Config 类环境变量覆盖测试"""
    
    def test_env_token_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 token"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  token: config-token\n")
        
        os.environ[f"{ENV_PREFIX}TOKEN"] = "env-token"
        
        config = Config.load(config_path)
        
        assert config.github["token"] == "env-token"
    
    def test_env_username_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 username"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  username: config-user\n")
        
        os.environ[f"{ENV_PREFIX}USERNAME"] = "env-user"
        
        config = Config.load(config_path)
        
        assert config.github["username"] == "env-user"
    
    def test_env_batch_window_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 batch_window"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("sync:\n  batch_window: 10\n")
        
        os.environ[f"{ENV_PREFIX}BATCH_WINDOW"] = "60"
        
        config = Config.load(config_path)
        
        assert config.sync.batch_window == 60
    
    def test_env_max_files_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 max_files_per_commit"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("sync:\n  max_files_per_commit: 10\n")
        
        os.environ[f"{ENV_PREFIX}MAX_FILES"] = "100"
        
        config = Config.load(config_path)
        
        assert config.sync.max_files_per_commit == 100
    
    def test_env_auto_push_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 auto_push"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("sync:\n  auto_push: true\n")
        
        os.environ[f"{ENV_PREFIX}AUTO_PUSH"] = "false"
        
        config = Config.load(config_path)
        
        assert config.sync.auto_push is False
    
    def test_env_log_level_override(self, temp_dir: Path, clean_env):
        """测试环境变量覆盖 log_level"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("logging:\n  level: INFO\n")
        
        os.environ[f"{ENV_PREFIX}LOG_LEVEL"] = "DEBUG"
        
        config = Config.load(config_path)
        
        assert config.logging.level == "DEBUG"
    
    def test_disable_env_override(self, temp_dir: Path, clean_env):
        """测试禁用环境变量覆盖"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  token: config-token\n")
        
        os.environ[f"{ENV_PREFIX}TOKEN"] = "env-token"
        
        config = Config.load(config_path, use_env=False)
        
        assert config.github["token"] == "config-token"


# =============================================================================
# Config 类测试 - 配置验证
# =============================================================================


class TestConfigValidation:
    """Config 类配置验证测试"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = Config()
        config.github = {"token": "valid-token", "username": "user"}
        config.repositories = [RepositoryConfig(name="test", local_path="/path")]
        
        errors = config.validate()
        
        assert errors == []
        assert config.is_valid() is True
    
    def test_missing_token(self):
        """测试缺少 token"""
        config = Config()
        config.repositories = [RepositoryConfig(name="test", local_path="/path")]
        
        errors = config.validate()
        
        assert any("token is required" in e.lower() for e in errors)
        assert config.is_valid() is False
    
    def test_empty_repositories(self):
        """测试空仓库列表"""
        config = Config()
        config.github = {"token": "valid-token"}
        
        errors = config.validate()
        
        assert any("at least one repository" in e.lower() for e in errors)
    
    def test_invalid_sync_settings(self):
        """测试无效同步设置"""
        config = Config()
        config.github = {"token": "valid-token"}
        config.repositories = [RepositoryConfig(name="test", local_path="/path")]
        config.sync.batch_window = -1
        config.sync.max_files_per_commit = 0
        config.sync.conflict_strategy = "invalid"
        
        errors = config.validate()
        
        assert any("batch_window" in e.lower() for e in errors)
        assert any("max_files_per_commit" in e.lower() for e in errors)
        assert any("conflict_strategy" in e.lower() for e in errors)


# =============================================================================
# Config 类测试 - 仓库配置管理
# =============================================================================


class TestConfigRepositoryManagement:
    """Config 类仓库配置管理测试"""
    
    def test_get_repository_existing(self):
        """测试获取存在的仓库"""
        config = Config()
        config.repositories = [
            RepositoryConfig(name="repo1", local_path="/path1"),
            RepositoryConfig(name="repo2", local_path="/path2"),
        ]
        
        repo = config.get_repository("repo2")
        
        assert repo is not None
        assert repo.name == "repo2"
        assert repo.local_path == "/path2"
    
    def test_get_repository_nonexistent(self):
        """测试获取不存在的仓库"""
        config = Config()
        config.repositories = [RepositoryConfig(name="repo1", local_path="/path1")]
        
        repo = config.get_repository("nonexistent")
        
        assert repo is None
    
    def test_add_repository(self):
        """测试添加仓库"""
        config = Config()
        repo = RepositoryConfig(name="new-repo", local_path="/new/path")
        
        config.add_repository(repo)
        
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "new-repo"
    
    def test_add_duplicate_repository_raises_error(self):
        """测试添加重复仓库抛出错误"""
        config = Config()
        config.repositories = [RepositoryConfig(name="repo1", local_path="/path1")]
        
        with pytest.raises(ValueError, match="already exists"):
            config.add_repository(RepositoryConfig(name="repo1", local_path="/path2"))
    
    def test_remove_repository_existing(self):
        """测试移除存在的仓库"""
        config = Config()
        config.repositories = [
            RepositoryConfig(name="repo1", local_path="/path1"),
            RepositoryConfig(name="repo2", local_path="/path2"),
        ]
        
        result = config.remove_repository("repo1")
        
        assert result is True
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "repo2"
    
    def test_remove_repository_nonexistent(self):
        """测试移除不存在的仓库"""
        config = Config()
        config.repositories = [RepositoryConfig(name="repo1", local_path="/path1")]
        
        result = config.remove_repository("nonexistent")
        
        assert result is False
        assert len(config.repositories) == 1


# =============================================================================
# Config 类测试 - 更新和字典转换
# =============================================================================


class TestConfigUpdateAndConversion:
    """Config 类更新和字典转换测试"""
    
    def test_update_github_config(self):
        """测试更新 GitHub 配置"""
        config = Config()
        config.github = {"token": "old-token", "username": "old-user"}
        
        config.update({"github": {"token": "new-token"}})
        
        assert config.github["token"] == "new-token"
        assert config.github["username"] == "old-user"  # 未更改的保留
    
    def test_update_repositories(self):
        """测试更新仓库列表"""
        config = Config()
        config.repositories = [RepositoryConfig(name="old", local_path="/old")]
        
        config.update({"repositories": [{"name": "new", "local_path": "/new"}]})
        
        assert len(config.repositories) == 1
        assert config.repositories[0].name == "new"
    
    def test_update_sync_settings(self):
        """测试更新同步设置"""
        config = Config()
        
        config.update({"sync": {"batch_window": 60, "auto_push": False}})
        
        assert config.sync.batch_window == 60
        assert config.sync.auto_push is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = Config()
        config.github = {"token": "test-token", "username": "testuser"}
        config.repositories = [RepositoryConfig(name="test", local_path="/path")]
        config.sync.batch_window = 60
        
        data = config.to_dict()
        
        assert data["github"]["token"] == "test-token"
        assert data["repositories"][0]["name"] == "test"
        assert data["sync"]["batch_window"] == 60
    
    def test_generate_template(self):
        """测试生成配置模板"""
        template = Config.generate_template()
        
        assert "github:" in template
        assert "repositories:" in template
        assert "sync:" in template
        assert "logging:" in template
    
    def test_generate_template_without_comments(self):
        """测试生成无注释的配置模板"""
        template = Config.generate_template(include_comments=False)
        
        assert "github:" in template
        assert "#" not in template  # 无注释


# =============================================================================
# 工具函数测试
# =============================================================================


class TestUtilityFunctions:
    """工具函数测试"""
    
    def test_find_config_file_found(self, temp_dir: Path):
        """测试查找配置文件 - 找到"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  token: test\n")
        
        # 在子目录中查找
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        found = find_config_file(subdir)
        
        assert found == config_path
    
    def test_find_config_file_not_found(self, temp_dir: Path):
        """测试查找配置文件 - 未找到"""
        found = find_config_file(temp_dir)
        
        assert found is None
    
    def test_find_config_file_from_file_path(self, temp_dir: Path):
        """测试从文件路径查找配置文件"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("github:\n  token: test\n")
        
        some_file = temp_dir / "some_file.txt"
        some_file.write_text("content")
        
        found = find_config_file(some_file)
        
        assert found == config_path
    
    def test_init_config(self, temp_dir: Path):
        """测试初始化配置"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        
        result = init_config(config_path)
        
        assert result == config_path
        assert config_path.exists()
        content = config_path.read_text()
        assert "github:" in content
    
    def test_init_config_already_exists(self, temp_dir: Path):
        """测试初始化配置 - 文件已存在"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("existing content")
        
        with pytest.raises(FileExistsError):
            init_config(config_path)
    
    def test_init_config_force_overwrite(self, temp_dir: Path):
        """测试初始化配置 - 强制覆盖"""
        config_path = temp_dir / DEFAULT_CONFIG_FILENAME
        config_path.write_text("existing content")
        
        result = init_config(config_path, force=True)
        
        assert result == config_path
        content = config_path.read_text()
        assert "github:" in content
