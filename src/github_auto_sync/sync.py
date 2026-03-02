"""
GitHub Auto Sync 同步引擎模块

提供完整的同步功能，包括：
- 初始同步（全量上传文件夹到 GitHub）
- 增量同步（仅同步变更文件）
- 批量提交功能
- 同步状态跟踪
- 冲突检测和处理
- 与 FileWatcher 集成实现自动同步
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from . import git_operations
from .config import Config, RepositoryConfig
from .github_client import GitHubClient, GitHubClientError, RepositoryNotFoundError
from .watcher import FileChangeEvent, FileWatcher

# 尝试导入 AI 描述生成功能
try:
    from .ai_description import generate_commit_description, is_ai_description_available
    AI_DESCRIPTION_AVAILABLE = True
except ImportError:
    AI_DESCRIPTION_AVAILABLE = False
    logger.debug("AI description module not available")

# 配置日志
logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """同步状态枚举"""
    NOT_SYNCED = auto()      # 未同步
    SYNCING = auto()         # 同步中
    SYNCED = auto()          # 已同步
    ERROR = auto()           # 同步错误
    CONFLICT = auto()        # 存在冲突
    PAUSED = auto()          # 暂停同步


class SyncAction(Enum):
    """同步操作类型"""
    INITIAL = "initial"           # 初始同步
    INCREMENTAL = "incremental"   # 增量同步
    PULL = "pull"                 # 拉取更新
    PUSH = "push"                 # 推送更新
    COMMIT = "commit"             # 提交变更


@dataclass
class SyncResult:
    """
    同步结果类

    记录同步操作的详细结果信息。

    Attributes:
        success: 是否成功
        status: 同步后的状态
        action: 执行的操作类型
        message: 结果消息
        files_synced: 已同步的文件列表
        files_failed: 同步失败的文件列表
        commit_hash: 提交哈希（如果有）
        timestamp: 同步时间戳
        duration: 同步耗时（秒）
        details: 详细信息的字典
    """
    success: bool = False
    status: SyncStatus = SyncStatus.NOT_SYNCED
    action: Optional[SyncAction] = None
    message: str = ""
    files_synced: List[str] = field(default_factory=list)
    files_failed: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"SyncResult(success={self.success}, "
            f"status={self.status.name}, "
            f"action={self.action.value if self.action else None}, "
            f"files={len(self.files_synced)}, "
            f"duration={self.duration:.2f}s)"
        )


class SyncError(Exception):
    """同步错误基础异常"""
    pass


class SyncConflictError(SyncError):
    """同步冲突异常"""
    pass


class SyncManager:
    """
    同步管理器类

    主要的同步协调器，负责：
    - 初始同步（全量上传）
    - 增量同步（变更文件）
    - 批量提交管理
    - 状态跟踪
    - 冲突检测和处理
    - 自动同步（与 FileWatcher 集成）

    Attributes:
        config: 全局配置
        repo_config: 仓库配置
        github_client: GitHub API 客户端
        file_watcher: 文件监控器（自动同步时使用）
        _status: 当前同步状态
        _last_sync_time: 上次同步时间
        _last_result: 上次同步结果
        _auto_sync_running: 自动同步是否运行中

    Example:
        >>> from github_auto_sync.config import Config
        >>> config = Config.load()
        >>> repo_config = config.get_repository("my-project")
        >>>
        >>> sync_manager = SyncManager(config, repo_config)
        >>> result = sync_manager.initial_sync()
        >>>
        >>> # 启动自动同步
        >>> sync_manager.start_auto_sync()
        >>> # ... 运行一段时间 ...
        >>> sync_manager.stop_auto_sync()
    """

    def __init__(
        self,
        config: Config,
        repo_config: RepositoryConfig,
        dry_run: bool = False,
    ):
        """
        初始化同步管理器

        Args:
            config: 全局配置对象
            repo_config: 仓库配置对象
            dry_run: 是否为试运行模式（不实际执行 git 操作）

        Raises:
            ValueError: 配置无效时抛出
            GitHubClientError: GitHub 客户端初始化失败时抛出
        """
        self.config = config
        self.repo_config = repo_config
        self.dry_run = dry_run

        # 验证配置
        if not self._validate_config():
            raise ValueError(f"Invalid configuration for repository: {repo_config.name}")

        # 初始化 GitHub 客户端
        token = config.github.get("token")
        self.github_client = GitHubClient(token)

        # 文件监控器（延迟初始化）
        self._file_watcher: Optional[FileWatcher] = None

        # 同步状态
        self._status = SyncStatus.NOT_SYNCED
        self._last_sync_time: Optional[datetime] = None
        self._last_result: Optional[SyncResult] = None
        self._auto_sync_running = False

        # 待同步文件队列
        self._pending_files: Set[str] = set()
        self._sync_lock = False

        # 事件回调
        self._on_sync_complete: Optional[Callable[[SyncResult], None]] = None
        self._on_sync_error: Optional[Callable[[SyncError], None]] = None
        self._on_conflict: Optional[Callable[[List[str]], None]] = None

        logger.info(
            f"SyncManager initialized for repository: {repo_config.name} "
            f"(dry_run={dry_run})"
        )

    def _validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.repo_config.name:
            logger.error("Repository name is required")
            return False

        local_path = Path(self.repo_config.local_path).expanduser().resolve()
        if not local_path.exists():
            logger.error(f"Local path does not exist: {local_path}")
            return False

        if not self.config.github.get("token"):
            logger.error("GitHub token is required")
            return False

        return True

    def _get_local_path(self) -> Path:
        """获取本地路径（解析相对路径）"""
        path = Path(self.repo_config.local_path).expanduser()
        if not path.is_absolute():
            # 相对于配置文件的路径
            if self.config.config_path:
                path = self.config.config_path.parent / path
            else:
                path = Path.cwd() / path
        return path.resolve()

    def _ensure_git_repo(self) -> bool:
        """确保本地路径是 git 仓库"""
        local_path = self._get_local_path()

        if git_operations.is_git_repository(local_path):
            return True

        # 初始化 git 仓库
        try:
            logger.info(f"Initializing git repository at: {local_path}")
            if not self.dry_run:
                git_operations.init_repo(local_path)
            return True
        except git_operations.GitOperationError as e:
            logger.error(f"Failed to initialize git repository: {e}")
            return False

    def _ensure_remote(self) -> bool:
        """确保远程仓库配置正确"""
        local_path = self._get_local_path()

        # 获取远程 URL
        remote_url = self.repo_config.remote_url
        if not remote_url:
            # 尝试从 GitHub 获取仓库 URL
            try:
                repo_info = self.github_client.get_repo(self.repo_config.name)
                remote_url = repo_info.get("clone_url")
                logger.info(f"Using remote URL from GitHub: {remote_url}")
            except RepositoryNotFoundError:
                # 仓库不存在，需要创建
                logger.info(f"Repository '{self.repo_config.name}' does not exist on GitHub")
                return False

        # 检查现有远程
        try:
            remotes = git_operations.get_remotes(local_path)
            remote_names = [r["name"] for r in remotes]

            if "origin" in remote_names:
                # 更新现有远程
                existing_url = next(r["url"] for r in remotes if r["name"] == "origin")
                if existing_url != remote_url:
                    logger.info(f"Updating remote URL from {existing_url} to {remote_url}")
                    if not self.dry_run:
                        git_operations.remove_remote(local_path, "origin")
                        git_operations.add_remote(local_path, "origin", remote_url)
            else:
                # 添加新远程
                logger.info(f"Adding remote: origin -> {remote_url}")
                if not self.dry_run:
                    git_operations.add_remote(local_path, "origin", remote_url)

            return True

        except git_operations.GitOperationError as e:
            logger.error(f"Failed to configure remote: {e}")
            return False

    def _create_github_repo(self) -> bool:
        """在 GitHub 上创建仓库"""
        try:
            logger.info(f"Creating GitHub repository: {self.repo_config.name}")
            if self.dry_run:
                logger.info("[DRY RUN] Would create GitHub repository")
                return True

            repo_info = self.github_client.create_repo(
                name=self.repo_config.name,
                description=f"Auto-synced repository for {self.repo_config.name}",
                private=True,
                auto_init=False,
            )

            logger.info(f"GitHub repository created: {repo_info['html_url']}")

            # 配置远程
            remote_url = repo_info.get("clone_url")
            local_path = self._get_local_path()
            git_operations.add_remote(local_path, "origin", remote_url)

            return True

        except Exception as e:
            logger.error(f"Failed to create GitHub repository: {e}")
            return False

    def _check_conflicts(self) -> List[str]:
        """检查是否存在冲突"""
        local_path = self._get_local_path()
        conflicts = []

        try:
            # 获取仓库状态
            status = git_operations.get_status(local_path)

            # 检查未合并的文件（冲突）
            # GitPython 不直接提供冲突文件列表，我们通过检查状态来推断
            if status.get("is_dirty"):
                # 尝试获取更详细的信息
                try:
                    import subprocess
                    result = subprocess.run(
                        ["git", "diff", "--name-only", "--diff-filter=U"],
                        cwd=local_path,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        conflicts = result.stdout.strip().split("\n")
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to check conflicts: {e}")

        return conflicts

    def _handle_conflicts_internal(self, conflicts: List[str]) -> SyncResult:
        """内部冲突处理方法"""
        strategy = self.config.sync.conflict_strategy

        result = SyncResult(
            success=False,
            status=SyncStatus.CONFLICT,
            action=SyncAction.PULL,
            message=f"Merge conflicts detected: {conflicts}",
            files_failed=conflicts,
        )

        if strategy == "skip":
            logger.warning(f"Conflicts detected, skipping sync: {conflicts}")
            result.message = f"Conflicts detected (skipped): {conflicts}"

        elif strategy == "overwrite":
            logger.warning(f"Conflicts detected, using local version: {conflicts}")
            try:
                local_path = self._get_local_path()
                # 使用本地版本解决冲突
                for conflict_file in conflicts:
                    if not self.dry_run:
                        # 检出我们的版本
                        git_operations.checkout_ours(local_path, conflict_file)
                result.success = True
                result.status = SyncStatus.SYNCED
                result.message = f"Conflicts resolved using local version: {conflicts}"
            except Exception as e:
                result.message = f"Failed to resolve conflicts: {e}"

        elif strategy == "merge":
            logger.warning(f"Conflicts detected, manual merge required: {conflicts}")
            result.message = f"Manual merge required for: {conflicts}"

        # 触发冲突回调
        if self._on_conflict:
            try:
                self._on_conflict(conflicts)
            except Exception as e:
                logger.error(f"Error in conflict callback: {e}")

        return result

    def _generate_commit_message(
        self,
        files: Optional[List[str]] = None,
    ) -> str:
        """
        生成提交消息
        
        如果启用了 AI 描述且可用，使用 AI 生成描述；
        否则使用模板生成。
        
        Args:
            files: 变更的文件列表
            
        Returns:
            提交消息字符串
        """
        local_path = self._get_local_path()
        
        # 检查是否启用 AI 描述
        if self.config.sync.use_ai_description and AI_DESCRIPTION_AVAILABLE:
            try:
                logger.debug("Generating AI commit description...")
                ai_config = self.config.sync.ai_description
                
                # 获取变更的文件内容
                changed_files = files or self._get_changed_files()
                
                # 生成 AI 描述
                description = generate_commit_description(
                    repo_path=local_path,
                    changed_files=changed_files,
                    language=ai_config.language,
                    include_details=ai_config.include_details,
                    max_length=ai_config.max_length,
                )
                
                if description:
                    logger.info("AI commit description generated successfully")
                    return description
                else:
                    logger.warning("AI description generation returned empty, falling back to template")
                    
            except Exception as e:
                logger.warning(f"Failed to generate AI description: {e}, falling back to template")
        
        # 使用模板生成
        template = self.config.sync.commit_message_template
        action = "update" if files else "sync"
        file_count = len(files) if files else "all"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return template.format(
            action=action,
            files=file_count,
            timestamp=timestamp,
        )
    
    def _get_changed_files(self) -> List[str]:
        """
        获取变更的文件列表
        
        Returns:
            变更文件路径列表
        """
        local_path = self._get_local_path()
        try:
            status = git_operations.get_status(local_path)
            changed_files = []
            
            # 收集所有变更的文件
            changed_files.extend(status.get("staged_files", []))
            changed_files.extend(status.get("modified_files", []))
            changed_files.extend(status.get("untracked_files", []))
            
            return changed_files
        except Exception as e:
            logger.warning(f"Failed to get changed files: {e}")
            return []

    def _commit_changes(
        self,
        files: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> Optional[str]:
        """
        提交变更

        Args:
            files: 要提交的文件列表，None 表示提交所有变更
            message: 提交消息，None 则自动生成

        Returns:
            提交哈希，如果没有变更则返回 None
        """
        local_path = self._get_local_path()

        # 检查是否有变更
        if not git_operations.has_uncommitted_changes(local_path):
            logger.debug("No changes to commit")
            return None

        # 生成提交消息
        if message is None:
            message = self._generate_commit_message(files)

        try:
            logger.info(f"Committing changes: {message[:50]}...")
            if self.dry_run:
                logger.info(f"[DRY RUN] Would commit with message: {message}")
                return "dry-run-hash"

            git_operations.commit(local_path, message, files)

            # 获取提交哈希
            last_commit = git_operations.get_last_commit(local_path)
            commit_hash = last_commit.get("short_hash") if last_commit else None

            logger.info(f"Changes committed: {commit_hash}")
            return commit_hash

        except git_operations.GitOperationError as e:
            logger.error(f"Failed to commit changes: {e}")
            return None

    def _push_changes(self) -> bool:
        """推送变更到远程"""
        if not self.config.sync.auto_push:
            logger.debug("Auto push is disabled")
            return True

        local_path = self._get_local_path()
        branch = self.repo_config.branch

        try:
            logger.info(f"Pushing to origin/{branch}")
            if self.dry_run:
                logger.info("[DRY RUN] Would push changes")
                return True

            git_operations.push(local_path, "origin", branch)
            logger.info("Changes pushed successfully")
            return True

        except git_operations.GitOperationError as e:
            logger.error(f"Failed to push changes: {e}")
            return False

    def _pull_changes(self) -> SyncResult:
        """拉取远程变更"""
        if not self.config.sync.auto_pull:
            return SyncResult(
                success=True,
                status=self._status,
                action=SyncAction.PULL,
                message="Auto pull is disabled",
            )

        local_path = self._get_local_path()
        branch = self.repo_config.branch

        start_time = time.time()

        try:
            logger.info(f"Pulling from origin/{branch}")
            if self.dry_run:
                logger.info("[DRY RUN] Would pull changes")
                return SyncResult(
                    success=True,
                    status=self._status,
                    action=SyncAction.PULL,
                    message="[DRY RUN] Would pull changes",
                    duration=time.time() - start_time,
                )

            git_operations.pull(local_path, "origin", branch)

            # 检查冲突
            conflicts = self._check_conflicts()
            if conflicts:
                return self._handle_conflicts_internal(conflicts)

            return SyncResult(
                success=True,
                status=self._status,
                action=SyncAction.PULL,
                message="Successfully pulled remote changes",
                duration=time.time() - start_time,
            )

        except git_operations.GitOperationError as e:
            error_msg = str(e)
            # 检查是否是冲突错误
            if "conflict" in error_msg.lower() or "merge" in error_msg.lower():
                conflicts = self._check_conflicts()
                if conflicts:
                    return self._handle_conflicts_internal(conflicts)

            return SyncResult(
                success=False,
                status=SyncStatus.ERROR,
                action=SyncAction.PULL,
                message=f"Failed to pull changes: {e}",
                duration=time.time() - start_time,
            )

    def initial_sync(self) -> SyncResult:
        """
        执行初始同步（全量上传）

        将本地文件夹完整同步到 GitHub 仓库。

        Returns:
            SyncResult 同步结果
        """
        start_time = time.time()
        self._status = SyncStatus.SYNCING

        logger.info(f"Starting initial sync for: {self.repo_config.name}")

        try:
            local_path = self._get_local_path()

            # 1. 确保 git 仓库
            if not self._ensure_git_repo():
                return SyncResult(
                    success=False,
                    status=SyncStatus.ERROR,
                    action=SyncAction.INITIAL,
                    message="Failed to initialize git repository",
                    duration=time.time() - start_time,
                )

            # 2. 检查 GitHub 仓库是否存在
            repo_exists = False
            try:
                self.github_client.get_repo(self.repo_config.name)
                repo_exists = True
            except RepositoryNotFoundError:
                pass

            # 3. 创建 GitHub 仓库（如果不存在）
            if not repo_exists:
                if not self._create_github_repo():
                    return SyncResult(
                        success=False,
                        status=SyncStatus.ERROR,
                        action=SyncAction.INITIAL,
                        message="Failed to create GitHub repository",
                        duration=time.time() - start_time,
                    )

            # 4. 配置远程
            if not self._ensure_remote():
                return SyncResult(
                    success=False,
                    status=SyncStatus.ERROR,
                    action=SyncAction.INITIAL,
                    message="Failed to configure remote",
                    duration=time.time() - start_time,
                )

            # 5. 获取所有文件
            all_files = []
            for root, dirs, files in os.walk(local_path):
                # 过滤忽略的目录
                dirs[:] = [
                    d for d in dirs
                    if not self._should_ignore(os.path.join(root, d))
                ]

                for file in files:
                    file_path = os.path.join(root, file)
                    if not self._should_ignore(file_path):
                        rel_path = os.path.relpath(file_path, local_path)
                        all_files.append(rel_path)

            # 6. 提交所有文件
            if all_files:
                commit_hash = self._commit_changes(
                    files=None,  # 提交所有
                    message=f"Initial sync: add {len(all_files)} files",
                )
            else:
                commit_hash = None

            # 7. 推送
            push_success = self._push_changes()

            duration = time.time() - start_time

            if push_success:
                self._status = SyncStatus.SYNCED
                self._last_sync_time = datetime.now()

                result = SyncResult(
                    success=True,
                    status=SyncStatus.SYNCED,
                    action=SyncAction.INITIAL,
                    message=f"Initial sync completed: {len(all_files)} files synced",
                    files_synced=all_files,
                    commit_hash=commit_hash,
                    duration=duration,
                )
            else:
                self._status = SyncStatus.ERROR
                result = SyncResult(
                    success=False,
                    status=SyncStatus.ERROR,
                    action=SyncAction.INITIAL,
                    message="Initial sync failed: push failed",
                    files_synced=all_files,
                    duration=duration,
                )

            self._last_result = result
            self._trigger_sync_callback(result)
            return result

        except Exception as e:
            self._status = SyncStatus.ERROR
            duration = time.time() - start_time

            result = SyncResult(
                success=False,
                status=SyncStatus.ERROR,
                action=SyncAction.INITIAL,
                message=f"Initial sync failed: {e}",
                duration=duration,
            )

            self._last_result = result
            self._trigger_error_callback(SyncError(f"Initial sync failed: {e}"))
            return result

    def sync_changes(self, files: Optional[List[str]] = None) -> SyncResult:
        """
        执行增量同步

        同步指定的文件或所有变更到 GitHub。

        Args:
            files: 要同步的文件列表，None 表示同步所有变更

        Returns:
            SyncResult 同步结果
        """
        start_time = time.time()
        self._status = SyncStatus.SYNCING

        logger.info(f"Starting incremental sync for: {self.repo_config.name}")

        try:
            local_path = self._get_local_path()

            # 1. 确保 git 仓库和远程配置
            if not self._ensure_git_repo() or not self._ensure_remote():
                return SyncResult(
                    success=False,
                    status=SyncStatus.ERROR,
                    action=SyncAction.INCREMENTAL,
                    message="Failed to ensure git repository and remote",
                    duration=time.time() - start_time,
                )

            # 2. 拉取远程更新（如果启用）
            if self.config.sync.auto_pull:
                pull_result = self._pull_changes()
                if not pull_result.success and pull_result.status == SyncStatus.CONFLICT:
                    self._status = SyncStatus.CONFLICT
                    self._last_result = pull_result
                    return pull_result

            # 3. 提交变更
            commit_hash = self._commit_changes(files)

            if commit_hash is None:
                # 没有变更需要提交
                self._status = SyncStatus.SYNCED
                result = SyncResult(
                    success=True,
                    status=SyncStatus.SYNCED,
                    action=SyncAction.INCREMENTAL,
                    message="No changes to sync",
                    duration=time.time() - start_time,
                )
                self._last_result = result
                return result

            # 4. 推送
            push_success = self._push_changes()

            duration = time.time() - start_time

            if push_success:
                self._status = SyncStatus.SYNCED
                self._last_sync_time = datetime.now()

                result = SyncResult(
                    success=True,
                    status=SyncStatus.SYNCED,
                    action=SyncAction.INCREMENTAL,
                    message="Incremental sync completed successfully",
                    files_synced=files or [],
                    commit_hash=commit_hash,
                    duration=duration,
                )
            else:
                self._status = SyncStatus.ERROR
                result = SyncResult(
                    success=False,
                    status=SyncStatus.ERROR,
                    action=SyncAction.INCREMENTAL,
                    message="Incremental sync failed: push failed",
                    files_failed=files or [],
                    duration=duration,
                )

            self._last_result = result
            self._trigger_sync_callback(result)
            return result

        except Exception as e:
            self._status = SyncStatus.ERROR
            duration = time.time() - start_time

            result = SyncResult(
                success=False,
                status=SyncStatus.ERROR,
                action=SyncAction.INCREMENTAL,
                message=f"Incremental sync failed: {e}",
                duration=duration,
            )

            self._last_result = result
            self._trigger_error_callback(SyncError(f"Incremental sync failed: {e}"))
            return result

    def _should_ignore(self, path: str) -> bool:
        """检查路径是否应该被忽略"""
        from .watcher import should_ignore
        return should_ignore(path, self.repo_config.ignore_patterns)

    def _on_file_changes(self, events: List[FileChangeEvent]) -> None:
        """文件变更回调（用于自动同步）"""
        if not self._auto_sync_running:
            return

        if self._status == SyncStatus.PAUSED:
            logger.debug("Sync is paused, ignoring file changes")
            return

        # 收集需要同步的文件
        files_to_sync = []
        for event in events:
            # 忽略目录变更
            if event.is_directory:
                continue

            # 获取相对路径
            local_path = self._get_local_path()
            try:
                rel_path = os.path.relpath(event.path, local_path)
                if not self._should_ignore(event.path):
                    files_to_sync.append(rel_path)
                    self._pending_files.add(rel_path)
            except ValueError:
                # 路径不在监控目录下
                continue

        if not files_to_sync:
            return

        logger.info(f"Detected {len(files_to_sync)} file changes, triggering sync")

        # 执行同步
        if self._sync_lock:
            logger.debug("Sync already in progress, files queued")
            return

        try:
            self._sync_lock = True
            # 同步所有待处理文件
            all_files = list(self._pending_files)
            self._pending_files.clear()

            result = self.sync_changes(all_files)

            if not result.success:
                # 重新加入队列稍后重试
                self._pending_files.update(all_files)

        finally:
            self._sync_lock = False

    def start_auto_sync(self) -> bool:
        """
        启动自动同步

        启动文件监控器，当检测到文件变更时自动同步。

        Returns:
            是否成功启动
        """
        if self._auto_sync_running:
            logger.warning("Auto sync is already running")
            return True

        if not self.repo_config.auto_sync:
            logger.warning("Auto sync is disabled for this repository")
            return False

        try:
            local_path = self._get_local_path()

            # 创建文件监控器
            self._file_watcher = FileWatcher(
                path=local_path,
                callback=self._on_file_changes,
                ignore_patterns=self.repo_config.ignore_patterns,
                batch_window=self.config.sync.batch_window,
                use_gitignore=True,
            )

            self._file_watcher.start()
            self._auto_sync_running = True
            self._status = SyncStatus.SYNCED

            logger.info(f"Auto sync started for: {self.repo_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to start auto sync: {e}")
            self._status = SyncStatus.ERROR
            return False

    def stop_auto_sync(self) -> None:
        """停止自动同步"""
        if not self._auto_sync_running:
            return

        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None

        self._auto_sync_running = False
        logger.info(f"Auto sync stopped for: {self.repo_config.name}")

    def is_auto_sync_running(self) -> bool:
        """检查自动同步是否正在运行"""
        return self._auto_sync_running

    def get_status(self) -> SyncStatus:
        """获取当前同步状态"""
        return self._status

    def get_last_result(self) -> Optional[SyncResult]:
        """获取上次同步结果"""
        return self._last_result

    def get_last_sync_time(self) -> Optional[datetime]:
        """获取上次同步时间"""
        return self._last_sync_time

    def pause(self) -> None:
        """暂停同步"""
        self._status = SyncStatus.PAUSED
        logger.info(f"Sync paused for: {self.repo_config.name}")

    def resume(self) -> None:
        """恢复同步"""
        if self._last_result and not self._last_result.success:
            self._status = SyncStatus.ERROR
        else:
            self._status = SyncStatus.SYNCED
        logger.info(f"Sync resumed for: {self.repo_config.name}")

    def handle_conflicts(self, strategy: Optional[str] = None) -> SyncResult:
        """
        处理合并冲突

        Args:
            strategy: 冲突解决策略，None 使用配置中的策略

        Returns:
            SyncResult 处理结果
        """
        conflicts = self._check_conflicts()

        if not conflicts:
            return SyncResult(
                success=True,
                status=self._status,
                message="No conflicts detected",
            )

        # 临时使用指定策略
        original_strategy = self.config.sync.conflict_strategy
        if strategy:
            self.config.sync.conflict_strategy = strategy

        try:
            result = self._handle_conflicts_internal(conflicts)

            # 如果冲突解决成功，尝试继续同步
            if result.success and strategy == "overwrite":
                # 提交解决后的文件
                commit_hash = self._commit_changes(
                    files=conflicts,
                    message="Resolve conflicts using local version",
                )
                if commit_hash:
                    self._push_changes()
                    result.commit_hash = commit_hash

            return result

        finally:
            self.config.sync.conflict_strategy = original_strategy

    def set_callbacks(
        self,
        on_sync_complete: Optional[Callable[[SyncResult], None]] = None,
        on_sync_error: Optional[Callable[[SyncError], None]] = None,
        on_conflict: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        """
        设置事件回调函数

        Args:
            on_sync_complete: 同步完成回调
            on_sync_error: 同步错误回调
            on_conflict: 冲突检测回调
        """
        self._on_sync_complete = on_sync_complete
        self._on_sync_error = on_sync_error
        self._on_conflict = on_conflict

    def _trigger_sync_callback(self, result: SyncResult) -> None:
        """触发同步完成回调"""
        if self._on_sync_complete:
            try:
                self._on_sync_complete(result)
            except Exception as e:
                logger.error(f"Error in sync complete callback: {e}")

    def _trigger_error_callback(self, error: SyncError) -> None:
        """触发错误回调"""
        if self._on_sync_error:
            try:
                self._on_sync_error(error)
            except Exception as e:
                logger.error(f"Error in sync error callback: {e}")

    def force_sync(self) -> SyncResult:
        """
        强制同步

        忽略当前状态，强制执行同步。

        Returns:
            SyncResult 同步结果
        """
        self._status = SyncStatus.NOT_SYNCED
        return self.sync_changes()

    def get_pending_files(self) -> List[str]:
        """获取待同步的文件列表"""
        return list(self._pending_files)

    def clear_pending_files(self) -> None:
        """清空待同步文件队列"""
        self._pending_files.clear()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_auto_sync()
        return False


def sync_repository(
    repo_config: RepositoryConfig,
    config: Optional[Config] = None,
    initial: bool = False,
    dry_run: bool = False,
) -> SyncResult:
    """
    同步仓库的便捷函数

    Args:
        repo_config: 仓库配置
        config: 全局配置，None 则创建默认配置
        initial: 是否执行初始同步
        dry_run: 是否为试运行模式

    Returns:
        SyncResult 同步结果

    Example:
        >>> from github_auto_sync.config import RepositoryConfig
        >>> repo_config = RepositoryConfig(
        ...     name="my-project",
        ...     local_path="/path/to/project",
        ... )
        >>> result = sync_repository(repo_config, initial=True)
        >>> print(f"Sync success: {result.success}")
    """
    if config is None:
        config = Config()

    manager = SyncManager(config, repo_config, dry_run=dry_run)

    if initial:
        return manager.initial_sync()
    else:
        return manager.sync_changes()


def create_sync_manager(
    config: Config,
    repo_name: str,
    dry_run: bool = False,
) -> SyncManager:
    """
    创建同步管理器的工厂函数

    Args:
        config: 全局配置
        repo_name: 仓库名称
        dry_run: 是否为试运行模式

    Returns:
        SyncManager 实例

    Raises:
        ValueError: 找不到指定名称的仓库配置

    Example:
        >>> from github_auto_sync.config import Config
        >>> config = Config.load()
        >>> manager = create_sync_manager(config, "my-project")
        >>> result = manager.initial_sync()
    """
    repo_config = config.get_repository(repo_name)
    if repo_config is None:
        raise ValueError(f"Repository '{repo_name}' not found in configuration")

    return SyncManager(config, repo_config, dry_run=dry_run)


# 导出公共接口
__all__ = [
    # 枚举
    "SyncStatus",
    "SyncAction",
    # 数据类
    "SyncResult",
    # 异常
    "SyncError",
    "SyncConflictError",
    # 主类
    "SyncManager",
    # 便捷函数
    "sync_repository",
    "create_sync_manager",
]
