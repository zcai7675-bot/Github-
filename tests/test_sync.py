"""
同步引擎单元测试

测试 sync 模块的同步功能。
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from github_auto_sync.sync import (
    SyncManager,
    SyncResult,
    SyncStatus,
    SyncAction,
    SyncError,
    SyncConflictError,
    sync_repository,
    create_sync_manager,
)
from github_auto_sync.config import Config, RepositoryConfig
from github_auto_sync.watcher import FileChangeEvent, ChangeType


# =============================================================================
# SyncResult 测试
# =============================================================================


class TestSyncResult:
    """同步结果测试"""
    
    def test_default_init(self):
        """测试默认初始化"""
        result = SyncResult()
        
        assert result.success is False
        assert result.status == SyncStatus.NOT_SYNCED
        assert result.action is None
        assert result.message == ""
        assert result.files_synced == []
        assert result.files_failed == []
        assert result.commit_hash is None
        assert isinstance(result.timestamp, datetime)
        assert result.duration == 0.0
        assert result.details == {}
    
    def test_custom_init(self):
        """测试自定义初始化"""
        result = SyncResult(
            success=True,
            status=SyncStatus.SYNCED,
            action=SyncAction.INITIAL,
            message="Sync completed",
            files_synced=["file1.py", "file2.py"],
            commit_hash="abc123",
            duration=5.5,
        )
        
        assert result.success is True
        assert result.status == SyncStatus.SYNCED
        assert result.action == SyncAction.INITIAL
        assert result.message == "Sync completed"
        assert result.files_synced == ["file1.py", "file2.py"]
        assert result.commit_hash == "abc123"
        assert result.duration == 5.5
    
    def test_repr(self):
        """测试字符串表示"""
        result = SyncResult(
            success=True,
            status=SyncStatus.SYNCED,
            action=SyncAction.INCREMENTAL,
            duration=2.5,
        )
        
        repr_str = repr(result)
        
        assert "success=True" in repr_str
        assert "SYNCED" in repr_str
        assert "incremental" in repr_str
        assert "2.50s" in repr_str


# =============================================================================
# SyncManager 初始化测试
# =============================================================================


class TestSyncManagerInitialization:
    """SyncManager 初始化测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_init_with_valid_config(self, mock_github_client):
        """测试使用有效配置初始化"""
        config = Config()
        config.github = {"token": "test-token", "username": "testuser"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        
        manager = SyncManager(config, repo_config)
        
        assert manager.config == config
        assert manager.repo_config == repo_config
        assert manager.dry_run is False
        assert manager.get_status() == SyncStatus.NOT_SYNCED
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_init_dry_run(self, mock_github_client):
        """测试 dry run 模式初始化"""
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        
        manager = SyncManager(config, repo_config, dry_run=True)
        
        assert manager.dry_run is True
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_init_invalid_config_no_token(self, mock_github_client):
        """测试无效配置 - 无 token"""
        config = Config()
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            SyncManager(config, repo_config)


# =============================================================================
# SyncManager 状态管理测试
# =============================================================================


class TestSyncManagerStatus:
    """SyncManager 状态管理测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_get_status(self, mock_github_client):
        """测试获取状态"""
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        manager = SyncManager(config, repo_config)
        
        status = manager.get_status()
        
        assert status == SyncStatus.NOT_SYNCED
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_get_last_result(self, mock_github_client):
        """测试获取上次结果"""
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        manager = SyncManager(config, repo_config)
        
        result = manager.get_last_result()
        
        assert result is None
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_get_last_sync_time(self, mock_github_client):
        """测试获取上次同步时间"""
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        manager = SyncManager(config, repo_config)
        
        sync_time = manager.get_last_sync_time()
        
        assert sync_time is None
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_pause_and_resume(self, mock_github_client):
        """测试暂停和恢复"""
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path="/path/to/repo")
        manager = SyncManager(config, repo_config)
        
        manager.pause()
        assert manager.get_status() == SyncStatus.PAUSED
        
        manager.resume()
        assert manager.get_status() == SyncStatus.SYNCED


# =============================================================================
# SyncManager 初始同步测试
# =============================================================================


class TestSyncManagerInitialSync:
    """SyncManager 初始同步测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_initial_sync_success(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试初始同步成功"""
        # 设置模拟
        mock_git_ops.is_git_repository.return_value = False
        mock_git_ops.init_repo.return_value = MagicMock()
        mock_git_ops.has_uncommitted_changes.return_value = True
        mock_git_ops.get_last_commit.return_value = {"short_hash": "abc123"}
        mock_git_ops.get_remotes.return_value = []
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.side_effect = Exception("Not found")
        mock_github_instance.create_repo.return_value = {
            "clone_url": "https://github.com/user/test-repo.git"
        }
        mock_github_client.return_value = mock_github_instance
        
        # 创建配置
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        result = manager.initial_sync()
        
        assert isinstance(result, SyncResult)
        assert result.action == SyncAction.INITIAL
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_initial_sync_dry_run(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试初始同步 dry run 模式"""
        mock_git_ops.is_git_repository.return_value = True
        mock_git_ops.has_uncommitted_changes.return_value = False
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = {"clone_url": "https://github.com/user/test-repo.git"}
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config, dry_run=True)
        result = manager.initial_sync()
        
        assert isinstance(result, SyncResult)
        assert result.action == SyncAction.INITIAL


# =============================================================================
# SyncManager 增量同步测试
# =============================================================================


class TestSyncManagerIncrementalSync:
    """SyncManager 增量同步测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_sync_changes_no_changes(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试增量同步 - 无变更"""
        mock_git_ops.is_git_repository.return_value = True
        mock_git_ops.has_uncommitted_changes.return_value = False
        mock_git_ops.get_remotes.return_value = [{"name": "origin", "url": "https://github.com/user/repo.git"}]
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = {"clone_url": "https://github.com/user/repo.git"}
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        config.sync.auto_pull = False
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        result = manager.sync_changes()
        
        assert isinstance(result, SyncResult)
        assert result.action == SyncAction.INCREMENTAL
        assert "No changes" in result.message or result.success
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_sync_changes_with_files(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试增量同步指定文件"""
        mock_git_ops.is_git_repository.return_value = True
        mock_git_ops.has_uncommitted_changes.return_value = True
        mock_git_ops.get_last_commit.return_value = {"short_hash": "abc123"}
        mock_git_ops.get_remotes.return_value = [{"name": "origin", "url": "https://github.com/user/repo.git"}]
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = {"clone_url": "https://github.com/user/repo.git"}
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        config.sync.auto_pull = False
        config.sync.auto_push = False
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        result = manager.sync_changes(files=["file1.py", "file2.py"])
        
        assert isinstance(result, SyncResult)
        assert result.action == SyncAction.INCREMENTAL


# =============================================================================
# SyncManager 自动同步测试
# =============================================================================


class TestSyncManagerAutoSync:
    """SyncManager 自动同步测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.FileWatcher")
    def test_start_auto_sync(self, mock_file_watcher, mock_github_client, temp_dir: Path):
        """测试启动自动同步"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir), auto_sync=True)
        
        manager = SyncManager(config, repo_config)
        result = manager.start_auto_sync()
        
        assert result is True
        assert manager.is_auto_sync_running() is True
        mock_file_watcher.return_value.start.assert_called_once()
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_start_auto_sync_disabled(self, mock_github_client, temp_dir: Path):
        """测试启动禁用的自动同步"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir), auto_sync=False)
        
        manager = SyncManager(config, repo_config)
        result = manager.start_auto_sync()
        
        assert result is False
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.FileWatcher")
    def test_stop_auto_sync(self, mock_file_watcher, mock_github_client, temp_dir: Path):
        """测试停止自动同步"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir), auto_sync=True)
        
        manager = SyncManager(config, repo_config)
        manager.start_auto_sync()
        manager.stop_auto_sync()
        
        assert manager.is_auto_sync_running() is False
        mock_file_watcher.return_value.stop.assert_called_once()


# =============================================================================
# SyncManager 文件变更处理测试
# =============================================================================


class TestSyncManagerFileChanges:
    """SyncManager 文件变更处理测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_on_file_changes(self, mock_github_client, temp_dir: Path):
        """测试文件变更回调"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir), auto_sync=True)
        
        manager = SyncManager(config, repo_config)
        manager._auto_sync_running = True
        
        # 创建文件变更事件
        events = [
            FileChangeEvent(str(temp_dir / "file1.py"), ChangeType.CREATED),
            FileChangeEvent(str(temp_dir / "file2.py"), ChangeType.MODIFIED),
        ]
        
        # 调用文件变更处理
        with patch.object(manager, 'sync_changes') as mock_sync:
            mock_sync.return_value = SyncResult(success=True, status=SyncStatus.SYNCED)
            manager._on_file_changes(events)
            
            # 验证 sync_changes 被调用
            mock_sync.assert_called_once()


# =============================================================================
# SyncManager 冲突处理测试
# =============================================================================


class TestSyncManagerConflicts:
    """SyncManager 冲突处理测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_handle_conflicts_no_conflicts(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试处理冲突 - 无冲突"""
        mock_git_ops.is_git_repository.return_value = True
        
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        
        with patch.object(manager, '_check_conflicts', return_value=[]):
            result = manager.handle_conflicts()
            
            assert result.success is True
            assert "No conflicts" in result.message
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_handle_conflicts_skip_strategy(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试处理冲突 - skip 策略"""
        mock_git_ops.is_git_repository.return_value = True
        
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        config.sync.conflict_strategy = "skip"
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        
        with patch.object(manager, '_check_conflicts', return_value=["conflicted_file.py"]):
            result = manager.handle_conflicts()
            
            assert result.success is False
            assert result.status == SyncStatus.CONFLICT
            assert "skipped" in result.message


# =============================================================================
# SyncManager 回调测试
# =============================================================================


class TestSyncManagerCallbacks:
    """SyncManager 回调测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_set_callbacks(self, mock_github_client, temp_dir: Path):
        """测试设置回调"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        
        on_sync_complete = Mock()
        on_sync_error = Mock()
        on_conflict = Mock()
        
        manager.set_callbacks(
            on_sync_complete=on_sync_complete,
            on_sync_error=on_sync_error,
            on_conflict=on_conflict,
        )
        
        # 触发同步完成回调
        result = SyncResult(success=True)
        manager._trigger_sync_callback(result)
        on_sync_complete.assert_called_once_with(result)


# =============================================================================
# SyncManager 待处理文件测试
# =============================================================================


class TestSyncManagerPendingFiles:
    """SyncManager 待处理文件测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_get_pending_files(self, mock_github_client, temp_dir: Path):
        """测试获取待处理文件"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        manager._pending_files = {"file1.py", "file2.py"}
        
        pending = manager.get_pending_files()
        
        assert "file1.py" in pending
        assert "file2.py" in pending
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_clear_pending_files(self, mock_github_client, temp_dir: Path):
        """测试清空待处理文件"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        
        manager = SyncManager(config, repo_config)
        manager._pending_files = {"file1.py", "file2.py"}
        
        manager.clear_pending_files()
        
        assert len(manager._pending_files) == 0


# =============================================================================
# SyncManager 上下文管理器测试
# =============================================================================


class TestSyncManagerContextManager:
    """SyncManager 上下文管理器测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.FileWatcher")
    def test_context_manager(self, mock_file_watcher, mock_github_client, temp_dir: Path):
        """测试上下文管理器"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir), auto_sync=True)
        
        with SyncManager(config, repo_config) as manager:
            assert isinstance(manager, SyncManager)


# =============================================================================
# 便捷函数测试
# =============================================================================


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    @patch("github_auto_sync.sync.GitHubClient")
    @patch("github_auto_sync.sync.git_operations")
    def test_sync_repository(self, mock_git_ops, mock_github_client, temp_dir: Path):
        """测试 sync_repository 函数"""
        mock_git_ops.is_git_repository.return_value = True
        mock_git_ops.has_uncommitted_changes.return_value = False
        mock_git_ops.get_remotes.return_value = [{"name": "origin", "url": "https://github.com/user/repo.git"}]
        
        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = {"clone_url": "https://github.com/user/repo.git"}
        mock_github_client.return_value = mock_github_instance
        
        repo_config = RepositoryConfig(name="test-repo", local_path=str(temp_dir))
        config = Config()
        config.github = {"token": "test-token"}
        config.sync.auto_pull = False
        
        result = sync_repository(repo_config, config, initial=False)
        
        assert isinstance(result, SyncResult)
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_create_sync_manager(self, mock_github_client, temp_dir: Path):
        """测试 create_sync_manager 函数"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        config.repositories = [RepositoryConfig(name="test-repo", local_path=str(temp_dir))]
        
        manager = create_sync_manager(config, "test-repo")
        
        assert isinstance(manager, SyncManager)
        assert manager.repo_config.name == "test-repo"
    
    @patch("github_auto_sync.sync.GitHubClient")
    def test_create_sync_manager_not_found(self, mock_github_client, temp_dir: Path):
        """测试 create_sync_manager 仓库不存在"""
        mock_github_instance = MagicMock()
        mock_github_client.return_value = mock_github_instance
        
        config = Config()
        config.github = {"token": "test-token"}
        config.repositories = []
        
        with pytest.raises(ValueError, match="not found"):
            create_sync_manager(config, "nonexistent-repo")
