"""
文件监控器单元测试

测试 watcher 模块的文件系统监控功能。
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    DirCreatedEvent,
)

from github_auto_sync.watcher import (
    FileWatcher,
    EventHandler,
    FileChangeEvent,
    ChangeType,
    load_gitignore,
    should_ignore,
    watch_directory,
    create_default_ignore_patterns,
)


# =============================================================================
# 加载 .gitignore 测试
# =============================================================================


class TestLoadGitignore:
    """加载 .gitignore 测试"""
    
    def test_load_gitignore_from_file(self, temp_dir: Path):
        """测试从文件加载 .gitignore"""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n# comment\n\n*.log\n")
        
        patterns = load_gitignore(gitignore)
        
        assert "*.pyc" in patterns
        assert "__pycache__/" in patterns
        assert "*.log" in patterns
        assert "# comment" not in patterns  # 注释被跳过
        assert len(patterns) == 3
    
    def test_load_gitignore_from_directory(self, temp_dir: Path):
        """测试从目录加载 .gitignore"""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("node_modules/\n")
        
        patterns = load_gitignore(temp_dir)
        
        assert "node_modules/" in patterns
    
    def test_load_gitignore_not_found(self, temp_dir: Path):
        """测试 .gitignore 不存在"""
        patterns = load_gitignore(temp_dir)
        
        assert patterns == []
    
    def test_load_gitignore_empty_file(self, temp_dir: Path):
        """测试空 .gitignore 文件"""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("")
        
        patterns = load_gitignore(gitignore)
        
        assert patterns == []


# =============================================================================
# 忽略模式测试
# =============================================================================


class TestShouldIgnore:
    """忽略模式测试"""
    
    def test_should_ignore_simple_pattern(self):
        """测试简单模式忽略"""
        patterns = ["*.pyc"]
        
        assert should_ignore("test.pyc", patterns) is True
        assert should_ignore("test.py", patterns) is False
    
    def test_should_ignore_directory_pattern(self):
        """测试目录模式忽略"""
        patterns = ["__pycache__/"]
        
        assert should_ignore("__pycache__", patterns) is True
        assert should_ignore("src/__pycache__", patterns) is True
    
    def test_should_ignore_negation_pattern(self):
        """测试否定模式"""
        patterns = ["*.pyc", "!important.pyc"]
        
        assert should_ignore("test.pyc", patterns) is True
        assert should_ignore("important.pyc", patterns) is False
    
    def test_should_ignore_anchored_pattern(self):
        """测试锚定模式"""
        patterns = ["/build"]
        
        assert should_ignore("build", patterns) is True
        assert should_ignore("src/build", patterns) is False
    
    def test_should_ignore_empty_patterns(self):
        """测试空模式列表"""
        assert should_ignore("any_file.txt", []) is False
    
    def test_should_ignore_nested_path(self):
        """测试嵌套路径"""
        patterns = ["node_modules/"]
        
        assert should_ignore("project/node_modules/package.json", patterns) is True
        assert should_ignore("project/src/main.py", patterns) is False


# =============================================================================
# EventHandler 测试
# =============================================================================


class TestEventHandler:
    """事件处理器测试"""
    
    def test_on_file_created(self):
        """测试文件创建事件"""
        callback = Mock()
        handler = EventHandler(callback)
        
        event = FileCreatedEvent("/path/to/file.txt")
        handler.on_any_event(event)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert isinstance(args, FileChangeEvent)
        assert args.path == "/path/to/file.txt"
        assert args.change_type == ChangeType.CREATED
        assert args.is_directory is False
    
    def test_on_file_modified(self):
        """测试文件修改事件"""
        callback = Mock()
        handler = EventHandler(callback)
        
        event = FileModifiedEvent("/path/to/file.txt")
        handler.on_any_event(event)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert args.change_type == ChangeType.MODIFIED
    
    def test_on_file_deleted(self):
        """测试文件删除事件"""
        callback = Mock()
        handler = EventHandler(callback)
        
        event = FileDeletedEvent("/path/to/file.txt")
        handler.on_any_event(event)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert args.change_type == ChangeType.DELETED
    
    def test_on_file_moved(self):
        """测试文件移动事件"""
        callback = Mock()
        handler = EventHandler(callback)
        
        event = FileMovedEvent("/path/old.txt", "/path/new.txt")
        handler.on_any_event(event)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert args.change_type == ChangeType.MOVED
        assert args.path == "/path/new.txt"
        assert args.src_path == "/path/old.txt"
    
    def test_on_directory_created(self):
        """测试目录创建事件"""
        callback = Mock()
        handler = EventHandler(callback)
        
        event = DirCreatedEvent("/path/to/dir")
        handler.on_any_event(event)
        
        callback.assert_called_once()
        args = callback.call_args[0][0]
        assert args.is_directory is True
    
    def test_ignored_event(self):
        """测试被忽略的事件"""
        callback = Mock()
        handler = EventHandler(callback, ignore_patterns=["*.pyc"])
        
        event = FileCreatedEvent("/path/to/test.pyc")
        handler.on_any_event(event)
        
        callback.assert_not_called()
    
    def test_callback_error_handling(self):
        """测试回调错误处理"""
        callback = Mock(side_effect=Exception("Callback error"))
        handler = EventHandler(callback)
        
        event = FileCreatedEvent("/path/to/file.txt")
        # 不应抛出异常
        handler.on_any_event(event)
        
        callback.assert_called_once()


# =============================================================================
# FileChangeEvent 测试
# =============================================================================


class TestFileChangeEvent:
    """文件变更事件测试"""
    
    def test_event_equality(self):
        """测试事件相等性"""
        event1 = FileChangeEvent("/path/file.txt", ChangeType.CREATED)
        event2 = FileChangeEvent("/path/file.txt", ChangeType.CREATED)
        event3 = FileChangeEvent("/path/file.txt", ChangeType.MODIFIED)
        
        assert event1 == event2
        assert event1 != event3
    
    def test_event_hash(self):
        """测试事件哈希"""
        event1 = FileChangeEvent("/path/file.txt", ChangeType.CREATED)
        event2 = FileChangeEvent("/path/file.txt", ChangeType.CREATED)
        
        assert hash(event1) == hash(event2)
    
    def test_event_repr(self):
        """测试事件字符串表示"""
        event = FileChangeEvent("/path/file.txt", ChangeType.CREATED)
        
        assert "CREATED" in repr(event)
        assert "file" in repr(event)
        assert "/path/file.txt" in repr(event)
    
    def test_moved_event_repr(self):
        """测试移动事件字符串表示"""
        event = FileChangeEvent(
            "/path/new.txt",
            ChangeType.MOVED,
            src_path="/path/old.txt"
        )
        
        assert "MOVED" in repr(event)
        assert "old.txt -> new.txt" in repr(event)


# =============================================================================
# FileWatcher 初始化测试
# =============================================================================


class TestFileWatcherInitialization:
    """FileWatcher 初始化测试"""
    
    def test_init_with_defaults(self, temp_dir: Path):
        """测试默认初始化"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        assert watcher.path == temp_dir.resolve()
        assert watcher.callback == callback
        assert watcher.batch_window == 5.0
        assert watcher.debounce_interval == 0.5
        assert ".git/" in watcher.ignore_patterns
    
    def test_init_with_custom_values(self, temp_dir: Path):
        """测试自定义值初始化"""
        callback = Mock()
        watcher = FileWatcher(
            temp_dir,
            callback,
            ignore_patterns=["*.log"],
            batch_window=10.0,
            debounce_interval=1.0,
            use_gitignore=False,
        )
        
        assert watcher.batch_window == 10.0
        assert watcher.debounce_interval == 1.0
        assert "*.log" in watcher.ignore_patterns
    
    def test_init_loads_gitignore(self, temp_dir: Path):
        """测试初始化时加载 .gitignore"""
        gitignore = temp_dir / ".gitignore"
        gitignore.write_text("*.pyc\n")
        
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        assert "*.pyc" in watcher.ignore_patterns
    
    def test_init_path_not_exists(self, temp_dir: Path):
        """测试路径不存在"""
        nonexistent = temp_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            FileWatcher(nonexistent, Mock())
    
    def test_init_path_not_directory(self, temp_dir: Path):
        """测试路径不是目录"""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")
        
        with pytest.raises(NotADirectoryError):
            FileWatcher(file_path, Mock())


# =============================================================================
# FileWatcher 事件处理测试
# =============================================================================


class TestFileWatcherEventHandling:
    """FileWatcher 事件处理测试"""
    
    def test_on_file_event_adds_to_pending(self, temp_dir: Path):
        """测试文件事件添加到待处理"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback, batch_window=60.0)
        watcher._running = True
        
        event = FileChangeEvent(str(temp_dir / "file.txt"), ChangeType.CREATED)
        watcher._on_file_event(event)
        
        assert len(watcher._pending_events) == 1
        assert str(temp_dir / "file.txt") in watcher._pending_events
    
    def test_on_file_event_debounce(self, temp_dir: Path):
        """测试事件防抖"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback, debounce_interval=1.0)
        watcher._running = True
        
        file_path = str(temp_dir / "file.txt")
        
        # 第一个事件
        event1 = FileChangeEvent(file_path, ChangeType.CREATED)
        watcher._on_file_event(event1)
        
        # 在防抖间隔内的第二个事件
        event2 = FileChangeEvent(file_path, ChangeType.MODIFIED)
        watcher._on_file_event(event2)
        
        # 应该只有一个事件，保留创建类型
        assert len(watcher._pending_events) == 1
        assert watcher._pending_events[file_path].change_type == ChangeType.CREATED
    
    def test_flush_events_calls_callback(self, temp_dir: Path):
        """测试刷新事件调用回调"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        watcher._running = True
        
        event = FileChangeEvent(str(temp_dir / "file.txt"), ChangeType.CREATED)
        watcher._on_file_event(event)
        watcher._flush_events()
        
        callback.assert_called_once()
        events = callback.call_args[0][0]
        assert len(events) == 1
    
    def test_flush_events_empty_pending(self, temp_dir: Path):
        """测试刷新空待处理事件"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        watcher._flush_events()
        
        callback.assert_not_called()


# =============================================================================
# FileWatcher 生命周期测试
# =============================================================================


class TestFileWatcherLifecycle:
    """FileWatcher 生命周期测试"""
    
    @patch("github_auto_sync.watcher.Observer")
    def test_start(self, mock_observer_class, temp_dir: Path):
        """测试启动"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        watcher.start()
        
        assert watcher.is_running() is True
        mock_observer_class.return_value.start.assert_called_once()
    
    def test_start_already_running(self, temp_dir: Path):
        """测试启动已在运行的监控器"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        watcher._running = True
        
        with pytest.raises(RuntimeError, match="already running"):
            watcher.start()
    
    @patch("github_auto_sync.watcher.Observer")
    def test_stop(self, mock_observer_class, temp_dir: Path):
        """测试停止"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        watcher.start()
        watcher.stop()
        
        assert watcher.is_running() is False
        mock_observer_class.return_value.stop.assert_called_once()
    
    def test_stop_not_running(self, temp_dir: Path):
        """测试停止未运行的监控器"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        # 不应抛出异常
        watcher.stop()
    
    @patch("github_auto_sync.watcher.Observer")
    def test_context_manager(self, mock_observer_class, temp_dir: Path):
        """测试上下文管理器"""
        callback = Mock()
        
        with FileWatcher(temp_dir, callback) as watcher:
            assert watcher.is_running() is True
        
        mock_observer_class.return_value.stop.assert_called_once()


# =============================================================================
# FileWatcher 模式管理测试
# =============================================================================


class TestFileWatcherPatternManagement:
    """FileWatcher 模式管理测试"""
    
    def test_add_ignore_pattern(self, temp_dir: Path):
        """测试添加忽略模式"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        watcher.add_ignore_pattern("*.tmp")
        
        assert "*.tmp" in watcher.ignore_patterns
    
    def test_add_duplicate_pattern(self, temp_dir: Path):
        """测试添加重复模式"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback, ignore_patterns=["*.tmp"])
        
        watcher.add_ignore_pattern("*.tmp")
        
        assert watcher.ignore_patterns.count("*.tmp") == 1
    
    def test_remove_ignore_pattern(self, temp_dir: Path):
        """测试移除忽略模式"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback, ignore_patterns=["*.tmp"])
        
        result = watcher.remove_ignore_pattern("*.tmp")
        
        assert result is True
        assert "*.tmp" not in watcher.ignore_patterns
    
    def test_remove_nonexistent_pattern(self, temp_dir: Path):
        """测试移除不存在的模式"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        
        result = watcher.remove_ignore_pattern("*.nonexistent")
        
        assert result is False


# =============================================================================
# FileWatcher 查询测试
# =============================================================================


class TestFileWatcherQueries:
    """FileWatcher 查询测试"""
    
    def test_get_pending_events(self, temp_dir: Path):
        """测试获取待处理事件"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        watcher._running = True
        
        event = FileChangeEvent(str(temp_dir / "file.txt"), ChangeType.CREATED)
        watcher._on_file_event(event)
        
        pending = watcher.get_pending_events()
        
        assert len(pending) == 1
        assert pending[0].path == str(temp_dir / "file.txt")
    
    def test_flush(self, temp_dir: Path):
        """测试手动刷新"""
        callback = Mock()
        watcher = FileWatcher(temp_dir, callback)
        watcher._running = True
        
        event = FileChangeEvent(str(temp_dir / "file.txt"), ChangeType.CREATED)
        watcher._on_file_event(event)
        watcher.flush()
        
        callback.assert_called_once()
        assert len(watcher._pending_events) == 0


# =============================================================================
# 便捷函数测试
# =============================================================================


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    @patch("github_auto_sync.watcher.FileWatcher")
    def test_watch_directory(self, mock_watcher_class, temp_dir: Path):
        """测试 watch_directory 函数"""
        callback = Mock()
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher
        
        result = watch_directory(temp_dir, callback, ignore_patterns=["*.pyc"])
        
        mock_watcher_class.assert_called_once_with(
            path=temp_dir,
            callback=callback,
            ignore_patterns=["*.pyc"],
            batch_window=5.0,
            use_gitignore=True,
        )
        mock_watcher.start.assert_called_once()
        assert result == mock_watcher
    
    def test_create_default_ignore_patterns(self):
        """测试创建默认忽略模式"""
        patterns = create_default_ignore_patterns()
        
        assert ".git/" in patterns
        assert "__pycache__/" in patterns
        assert "*.pyc" in patterns
        assert "node_modules/" in patterns
        assert ".idea/" in patterns
        assert ".vscode/" in patterns
        assert ".DS_Store" in patterns
