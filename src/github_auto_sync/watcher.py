"""
GitHub Auto Sync 文件系统监控模块

提供基于 watchdog 的文件系统监控功能，支持：
- 递归目录监控
- 文件变更事件处理（创建、修改、删除）
- 忽略模式匹配（支持 .gitignore 和自定义模式）
- 变更批处理机制
- 防抖处理
- 事件回调系统
"""

import fnmatch
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Union

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

# 配置日志
logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """文件变更类型"""
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()
    MOVED = auto()


@dataclass
class FileChangeEvent:
    """
    文件变更事件类
    
    表示单个文件或目录的变更事件。
    
    Attributes:
        path: 文件或目录的路径
        change_type: 变更类型
        is_directory: 是否为目录
        src_path: 移动事件的源路径（仅 MOVED 类型有效）
        timestamp: 事件发生的时间戳
    """
    path: str
    change_type: ChangeType
    is_directory: bool = False
    src_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def __hash__(self) -> int:
        """用于集合去重"""
        return hash((self.path, self.change_type, self.is_directory))
    
    def __eq__(self, other: object) -> bool:
        """相等性比较"""
        if not isinstance(other, FileChangeEvent):
            return NotImplemented
        return (
            self.path == other.path
            and self.change_type == other.change_type
            and self.is_directory == other.is_directory
        )
    
    def __repr__(self) -> str:
        """字符串表示"""
        type_str = self.change_type.name
        dir_str = "dir" if self.is_directory else "file"
        if self.change_type == ChangeType.MOVED and self.src_path:
            return f"FileChangeEvent({type_str}, {dir_str}: {self.src_path} -> {self.path})"
        return f"FileChangeEvent({type_str}, {dir_str}: {self.path})"


# 事件类型映射
EVENT_TYPE_MAPPING = {
    FileCreatedEvent: ChangeType.CREATED,
    DirCreatedEvent: ChangeType.CREATED,
    FileModifiedEvent: ChangeType.MODIFIED,
    DirModifiedEvent: ChangeType.MODIFIED,
    FileDeletedEvent: ChangeType.DELETED,
    DirDeletedEvent: ChangeType.DELETED,
    FileMovedEvent: ChangeType.MOVED,
    DirMovedEvent: ChangeType.MOVED,
}


def load_gitignore(path: Union[str, Path]) -> List[str]:
    """
    加载 .gitignore 文件中的忽略模式
    
    Args:
        path: .gitignore 文件路径或包含 .gitignore 的目录路径
        
    Returns:
        忽略模式列表
    """
    gitignore_path = Path(path)
    
    # 如果传入的是目录，追加 .gitignore 文件名
    if gitignore_path.is_dir():
        gitignore_path = gitignore_path / ".gitignore"
    
    patterns: List[str] = []
    
    if not gitignore_path.exists():
        logger.debug(f".gitignore file not found: {gitignore_path}")
        return patterns
    
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                # 去除行首空格（gitignore 规范）
                line = line.lstrip()
                if line:
                    patterns.append(line)
    except Exception as e:
        logger.warning(f"Failed to load .gitignore from {gitignore_path}: {e}")
    
    logger.debug(f"Loaded {len(patterns)} patterns from {gitignore_path}")
    return patterns


def should_ignore(path: Union[str, Path], patterns: List[str]) -> bool:
    """
    检查路径是否应该被忽略
    
    支持 glob 模式匹配，包括：
    - 标准 glob 模式: *.pyc, __pycache__/
    - 目录匹配: dir/, dir/**
    - 否定模式: !important.pyc
    - 锚定路径: /build
    
    Args:
        path: 要检查的文件或目录路径
        patterns: 忽略模式列表
        
    Returns:
        是否应该忽略
    """
    if not patterns:
        return False
    
    path = Path(path)
    path_str = str(path)
    path_parts = path.parts
    filename = path.name
    
    # 跟踪否定模式
    ignored = False
    
    for pattern in patterns:
        pattern = pattern.strip()
        
        # 处理否定模式
        is_negation = pattern.startswith("!")
        if is_negation:
            pattern = pattern[1:]
        
        # 去除前导斜杠进行路径匹配
        is_anchored = pattern.startswith("/")
        if is_anchored:
            pattern = pattern[1:]
        
        # 检查是否匹配
        matched = False
        
        # 1. 直接文件名匹配
        if fnmatch.fnmatch(filename, pattern):
            matched = True
        # 2. 完整路径匹配（锚定模式）
        elif is_anchored and fnmatch.fnmatch(path_str, pattern):
            matched = True
        # 3. 任意路径部分匹配
        elif not is_anchored:
            # 检查路径的任何部分是否匹配
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern.rstrip("/")):
                    matched = True
                    break
            # 检查完整路径匹配
            if not matched and fnmatch.fnmatch(path_str, f"*/{pattern}"):
                matched = True
        
        # 处理目录模式（以 / 结尾）
        if pattern.endswith("/") and path.is_dir():
            dir_pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(filename, dir_pattern):
                matched = True
        
        # 应用匹配结果
        if matched:
            if is_negation:
                ignored = False
            else:
                ignored = True
    
    return ignored


class EventHandler(FileSystemEventHandler):
    """
    文件系统事件处理器
    
    继承自 watchdog 的 FileSystemEventHandler，
    将 watchdog 事件转换为 FileChangeEvent 并传递给回调函数。
    """
    
    def __init__(
        self,
        callback: Callable[[FileChangeEvent], None],
        ignore_patterns: Optional[List[str]] = None,
        watch_path: Optional[str] = None,
    ):
        """
        初始化事件处理器
        
        Args:
            callback: 事件回调函数，接收 FileChangeEvent 参数
            ignore_patterns: 忽略模式列表
            watch_path: 监控的根路径（用于相对路径计算）
        """
        self.callback = callback
        self.ignore_patterns = ignore_patterns or []
        self.watch_path = Path(watch_path) if watch_path else None
        self._lock = threading.Lock()
        
        logger.debug(f"EventHandler initialized with {len(self.ignore_patterns)} ignore patterns")
    
    def _should_ignore(self, event: FileSystemEvent) -> bool:
        """检查事件是否应该被忽略"""
        # 检查源路径（对于移动事件）
        if hasattr(event, "src_path") and event.src_path:
            if should_ignore(event.src_path, self.ignore_patterns):
                return True
        
        # 检查目标路径
        if hasattr(event, "dest_path") and event.dest_path:
            if should_ignore(event.dest_path, self.ignore_patterns):
                return True
        
        # 检查普通路径
        if hasattr(event, "src_path"):
            return should_ignore(event.src_path, self.ignore_patterns)
        
        return False
    
    def _create_change_event(self, event: FileSystemEvent) -> Optional[FileChangeEvent]:
        """从 watchdog 事件创建 FileChangeEvent"""
        event_type = type(event)
        
        if event_type not in EVENT_TYPE_MAPPING:
            logger.warning(f"Unknown event type: {event_type}")
            return None
        
        change_type = EVENT_TYPE_MAPPING[event_type]
        
        # 获取路径
        if isinstance(event, (FileMovedEvent, DirMovedEvent)):
            dest_path = getattr(event, "dest_path", event.src_path)
            return FileChangeEvent(
                path=dest_path,
                change_type=change_type,
                is_directory=isinstance(event, (DirCreatedEvent, DirDeletedEvent, DirModifiedEvent, DirMovedEvent)),
                src_path=event.src_path,
            )
        else:
            return FileChangeEvent(
                path=event.src_path,
                change_type=change_type,
                is_directory=isinstance(event, (DirCreatedEvent, DirDeletedEvent, DirModifiedEvent, DirMovedEvent)),
            )
    
    def on_any_event(self, event: FileSystemEvent) -> None:
        """处理任何文件系统事件"""
        # 检查是否应该忽略
        if self._should_ignore(event):
            logger.debug(f"Ignoring event: {event}")
            return
        
        # 创建变更事件
        change_event = self._create_change_event(event)
        if change_event is None:
            return
        
        logger.debug(f"Processing event: {change_event}")
        
        # 调用回调
        try:
            self.callback(change_event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")


class FileWatcher:
    """
    文件监控器类
    
    基于 watchdog 的文件系统监控器，支持：
    - 递归目录监控
    - 文件变更批处理
    - 防抖处理
    - 自定义忽略模式
    - 线程安全操作
    
    Example:
        >>> def on_changes(events):
        ...     for event in events:
        ...         print(f"Changed: {event.path}")
        >>>
        >>> watcher = FileWatcher("/path/to/watch", on_changes)
        >>> watcher.start()
        >>> # ... 运行一段时间 ...
        >>> watcher.stop()
    """
    
    def __init__(
        self,
        path: Union[str, Path],
        callback: Callable[[List[FileChangeEvent]], None],
        ignore_patterns: Optional[List[str]] = None,
        batch_window: float = 5.0,
        debounce_interval: float = 0.5,
        use_gitignore: bool = True,
    ):
        """
        初始化文件监控器
        
        Args:
            path: 要监控的目录路径
            callback: 回调函数，接收 FileChangeEvent 列表
            ignore_patterns: 自定义忽略模式列表
            batch_window: 批处理时间窗口（秒），在此时间内的变更会被合并
            debounce_interval: 防抖间隔（秒），在此时间内的重复变更会被忽略
            use_gitignore: 是否自动加载 .gitignore 文件
        """
        self.path = Path(path).resolve()
        self.callback = callback
        self.batch_window = batch_window
        self.debounce_interval = debounce_interval
        self.use_gitignore = use_gitignore
        
        # 验证路径
        if not self.path.exists():
            raise FileNotFoundError(f"Watch path does not exist: {self.path}")
        if not self.path.is_dir():
            raise NotADirectoryError(f"Watch path is not a directory: {self.path}")
        
        # 初始化忽略模式
        self.ignore_patterns: List[str] = []
        
        # 加载 .gitignore
        if self.use_gitignore:
            gitignore_patterns = load_gitignore(self.path)
            self.ignore_patterns.extend(gitignore_patterns)
        
        # 添加自定义忽略模式
        if ignore_patterns:
            self.ignore_patterns.extend(ignore_patterns)
        
        # 始终忽略 .git 目录
        if ".git/" not in self.ignore_patterns and ".git" not in self.ignore_patterns:
            self.ignore_patterns.append(".git/")
        
        # 监控状态
        self._observer: Optional[Observer] = None
        self._running = False
        self._lock = threading.Lock()
        
        # 批处理和防抖
        self._pending_events: Dict[str, FileChangeEvent] = {}
        self._last_event_time: Dict[str, float] = {}
        self._batch_timer: Optional[threading.Timer] = None
        self._timer_lock = threading.Lock()
        
        logger.info(
            f"FileWatcher initialized for {self.path} "
            f"with batch_window={batch_window}s, "
            f"{len(self.ignore_patterns)} ignore patterns"
        )
    
    def _on_file_event(self, event: FileChangeEvent) -> None:
        """内部事件处理回调"""
        with self._lock:
            if not self._running:
                return
            
            # 防抖检查
            current_time = time.time()
            last_time = self._last_event_time.get(event.path, 0)
            
            if current_time - last_time < self.debounce_interval:
                # 更新事件时间戳，但使用原有事件类型（优先保留创建事件）
                existing_event = self._pending_events.get(event.path)
                if existing_event and existing_event.change_type == ChangeType.CREATED:
                    # 保留创建事件，只更新时间戳
                    event = FileChangeEvent(
                        path=event.path,
                        change_type=ChangeType.CREATED,
                        is_directory=event.is_directory,
                        src_path=event.src_path,
                        timestamp=current_time,
                    )
            
            self._last_event_time[event.path] = current_time
            self._pending_events[event.path] = event
            
            logger.debug(f"Event queued: {event}")
        
        # 重置批处理定时器
        self._reset_batch_timer()
    
    def _reset_batch_timer(self) -> None:
        """重置批处理定时器"""
        with self._timer_lock:
            # 取消现有定时器
            if self._batch_timer is not None:
                self._batch_timer.cancel()
            
            # 创建新定时器
            self._batch_timer = threading.Timer(self.batch_window, self._flush_events)
            self._batch_timer.daemon = True
            self._batch_timer.start()
    
    def _flush_events(self) -> None:
        """刷新待处理的事件"""
        with self._lock:
            if not self._pending_events:
                return
            
            # 复制并清空待处理事件
            events = list(self._pending_events.values())
            self._pending_events.clear()
            
            # 清理旧的时间戳记录
            current_time = time.time()
            self._last_event_time = {
                path: ts for path, ts in self._last_event_time.items()
                if current_time - ts < self.debounce_interval * 2
            }
        
        if events:
            logger.info(f"Flushing {len(events)} batched events")
            try:
                self.callback(events)
            except Exception as e:
                logger.error(f"Error in batch callback: {e}")
    
    def start(self) -> None:
        """
        开始监控
        
        Raises:
            RuntimeError: 如果监控器已经在运行
        """
        with self._lock:
            if self._running:
                raise RuntimeError("FileWatcher is already running")
            
            # 创建事件处理器
            event_handler = EventHandler(
                callback=self._on_file_event,
                ignore_patterns=self.ignore_patterns,
                watch_path=str(self.path),
            )
            
            # 创建并启动观察者
            self._observer = Observer()
            self._observer.schedule(event_handler, str(self.path), recursive=True)
            self._observer.start()
            self._running = True
        
        logger.info(f"FileWatcher started monitoring: {self.path}")
    
    def stop(self) -> None:
        """
        停止监控
        
        会刷新所有待处理的事件后再停止。
        """
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # 取消定时器
            with self._timer_lock:
                if self._batch_timer is not None:
                    self._batch_timer.cancel()
                    self._batch_timer = None
            
            # 停止观察者
            if self._observer is not None:
                self._observer.stop()
                self._observer.join(timeout=5)
                self._observer = None
        
        # 刷新剩余事件
        self._flush_events()
        
        logger.info(f"FileWatcher stopped monitoring: {self.path}")
    
    def is_running(self) -> bool:
        """检查监控器是否正在运行"""
        with self._lock:
            return self._running
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """
        动态添加忽略模式
        
        Args:
            pattern: 要添加的忽略模式
        """
        with self._lock:
            if pattern not in self.ignore_patterns:
                self.ignore_patterns.append(pattern)
                logger.debug(f"Added ignore pattern: {pattern}")
    
    def remove_ignore_pattern(self, pattern: str) -> bool:
        """
        移除忽略模式
        
        Args:
            pattern: 要移除的忽略模式
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if pattern in self.ignore_patterns:
                self.ignore_patterns.remove(pattern)
                logger.debug(f"Removed ignore pattern: {pattern}")
                return True
            return False
    
    def get_pending_events(self) -> List[FileChangeEvent]:
        """
        获取当前待处理的事件
        
        Returns:
            待处理的事件列表
        """
        with self._lock:
            return list(self._pending_events.values())
    
    def flush(self) -> None:
        """立即刷新所有待处理的事件"""
        self._flush_events()
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        return False


# 便捷函数

def watch_directory(
    path: Union[str, Path],
    callback: Callable[[List[FileChangeEvent]], None],
    ignore_patterns: Optional[List[str]] = None,
    batch_window: float = 5.0,
    use_gitignore: bool = True,
) -> FileWatcher:
    """
    便捷函数：创建并启动文件监控器
    
    Args:
        path: 要监控的目录路径
        callback: 回调函数
        ignore_patterns: 忽略模式列表
        batch_window: 批处理时间窗口
        use_gitignore: 是否使用 .gitignore
        
    Returns:
        已启动的 FileWatcher 实例
        
    Example:
        >>> def on_changes(events):
        ...     for e in events:
        ...         print(f"{e.change_type.name}: {e.path}")
        >>>
        >>> watcher = watch_directory("/path/to/watch", on_changes)
        >>> # 使用 watcher.stop() 停止监控
    """
    watcher = FileWatcher(
        path=path,
        callback=callback,
        ignore_patterns=ignore_patterns,
        batch_window=batch_window,
        use_gitignore=use_gitignore,
    )
    watcher.start()
    return watcher


def create_default_ignore_patterns() -> List[str]:
    """
    创建默认的忽略模式列表
    
    Returns:
        默认忽略模式列表
    """
    return [
        # 版本控制
        ".git/",
        ".svn/",
        ".hg/",
        ".bzr/",
        
        # Python
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python/",
        "*.so",
        "*.egg",
        "*.egg-info/",
        ".eggs/",
        ".venv/",
        "venv/",
        "env/",
        ".env/",
        "ENV/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        "dist/",
        "build/",
        
        # Node.js
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        ".npm/",
        ".yarn/",
        ".pnpm-debug.log*",
        
        # IDE
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        "Thumbs.db",
        ".settings/",
        ".project",
        ".classpath",
        
        # 日志和临时文件
        "*.log",
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.cache",
        
        # 其他
        ".github-auto-sync.yml",
    ]
