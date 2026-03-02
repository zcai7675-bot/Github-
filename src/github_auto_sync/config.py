"""
GitHub Auto Sync 配置管理模块

提供 YAML 配置文件管理、环境变量支持、配置验证和模板生成功能。
"""

import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


# 默认配置文件名
DEFAULT_CONFIG_FILENAME = ".github-auto-sync.yml"

# 环境变量前缀
ENV_PREFIX = "GITHUB_"

# 默认配置模板
DEFAULT_CONFIG_TEMPLATE = """# GitHub Auto Sync 配置文件
# 文档: https://github.com/yourusername/github-auto-sync/blob/main/docs/config.md

# GitHub 认证配置
github:
  # GitHub Personal Access Token
  # 可以通过环境变量 GITHUB_TOKEN 设置（推荐，更安全）
  token: ""
  
  # GitHub 用户名
  # 可以通过环境变量 GITHUB_USERNAME 设置
  username: ""

# 仓库配置列表
repositories:
  - name: "my-project"
    # 本地文件夹路径（绝对路径或相对于配置文件的路径）
    local_path: "./my-project"
    
    # GitHub 远程仓库 URL（可选，留空则使用本地 git remote）
    # 支持 HTTPS 和 SSH 格式
    remote_url: ""
    
    # 默认分支
    branch: "main"
    
    # 是否启用自动同步
    auto_sync: true
    
    # 忽略的文件模式（支持 glob 语法）
    ignore_patterns:
      - ".git/"
      - "__pycache__/"
      - "*.pyc"
      - "*.log"
      - ".DS_Store"
      - "node_modules/"
      - ".env"
      - ".venv/"
      - "*.tmp"
      - "*.temp"

# 同步设置
sync:
  # 批量同步窗口时间（秒）
  # 在窗口时间内发生的多个文件变更会被合并为一个提交
  batch_window: 30
  
  # 每次提交的最大文件数
  # 超过此数量的文件会被拆分为多个提交
  max_files_per_commit: 50
  
  # 提交消息模板
  # 可用变量: {action} (操作类型), {files} (文件数量), {timestamp} (时间戳)
  commit_message_template: "auto-sync: {action} {files} files"
  
  # 是否自动推送
  auto_push: true
  
  # 是否在同步前拉取远程更新
  auto_pull: true
  
  # 冲突解决策略: "skip", "overwrite", "merge"
  conflict_strategy: "skip"
  
  # 是否使用 AI 生成提交描述
  # 启用后，AI 会分析代码变更并生成有意义的提交描述
  # 禁用则使用上面的 commit_message_template 模板
  use_ai_description: false
  
  # AI 描述生成设置（当 use_ai_description 为 true 时生效）
  ai_description:
    # 描述语言: "auto" (自动检测), "zh" (中文), "en" (英文)
    language: "auto"
    
    # 是否包含详细变更列表
    include_details: true
    
    # 最大描述长度（字符数）
    max_length: 500

# 日志设置
logging:
  # 日志级别: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  
  # 日志文件路径（可选，留空则只输出到控制台）
  file: ""
  
  # 是否启用彩色输出
  color: true

# 通知设置（可选）
notifications:
  # 同步失败时是否发送通知
  on_error: true
  
  # 同步成功时是否发送通知
  on_success: false
"""


@dataclass
class RepositoryConfig:
    """仓库配置类"""
    
    name: str
    local_path: str
    remote_url: str = ""
    branch: str = "main"
    auto_sync: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: [
        ".git/",
        "__pycache__/",
        "*.pyc",
        "*.log",
        ".DS_Store",
        "node_modules/",
        ".env",
        ".venv/",
        "*.tmp",
        "*.temp",
    ])
    
    def __post_init__(self) -> None:
        """验证并规范化配置"""
        if not self.name:
            raise ValueError("Repository name cannot be empty")
        if not self.local_path:
            raise ValueError(f"Repository '{self.name}' local_path cannot be empty")
        if not self.branch:
            self.branch = "main"


@dataclass
class AIDescriptionConfig:
    """AI 描述生成配置类"""
    
    language: str = "auto"  # "auto", "zh", "en"
    include_details: bool = True
    max_length: int = 500
    
    def __post_init__(self) -> None:
        """验证并规范化配置"""
        valid_languages = ["auto", "zh", "en", "zh-cn", "zh-tw", "en-us", "en-gb"]
        if self.language.lower() not in valid_languages:
            self.language = "auto"
        if self.max_length < 100:
            self.max_length = 100
        if self.max_length > 2000:
            self.max_length = 2000


@dataclass
class SyncConfig:
    """同步设置配置类"""
    
    batch_window: int = 30
    max_files_per_commit: int = 50
    commit_message_template: str = "auto-sync: {action} {files} files"
    auto_push: bool = True
    auto_pull: bool = True
    conflict_strategy: str = "skip"
    use_ai_description: bool = False
    ai_description: AIDescriptionConfig = field(default_factory=AIDescriptionConfig)
    
    def __post_init__(self) -> None:
        """验证并规范化配置"""
        if self.batch_window < 0:
            self.batch_window = 30
        if self.max_files_per_commit < 1:
            self.max_files_per_commit = 50
        if self.conflict_strategy not in ("skip", "overwrite", "merge"):
            self.conflict_strategy = "skip"
        # 确保 ai_description 是 AIDescriptionConfig 实例
        if isinstance(self.ai_description, dict):
            self.ai_description = AIDescriptionConfig(**self.ai_description)


@dataclass
class LoggingConfig:
    """日志配置类"""
    
    level: str = "INFO"
    file: str = ""
    color: bool = True
    
    def __post_init__(self) -> None:
        """验证并规范化配置"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.level.upper() not in valid_levels:
            self.level = "INFO"
        else:
            self.level = self.level.upper()


@dataclass
class NotificationConfig:
    """通知配置类"""
    
    on_error: bool = True
    on_success: bool = False


@dataclass
class Config:
    """
    GitHub Auto Sync 主配置类
    
    支持从 YAML 文件加载、环境变量覆盖、配置验证和保存功能。
    """
    
    github: Dict[str, str] = field(default_factory=lambda: {"token": "", "username": ""})
    repositories: List[RepositoryConfig] = field(default_factory=list)
    sync: SyncConfig = field(default_factory=SyncConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    
    # 内部状态
    _config_path: Optional[Path] = field(default=None, repr=False)
    _loaded: bool = field(default=False, repr=False)
    
    @classmethod
    def load(
        cls,
        config_path: Optional[Union[str, Path]] = None,
        use_env: bool = True,
        create_default: bool = False,
    ) -> "Config":
        """
        从配置文件加载配置
        
        Args:
            config_path: 配置文件路径，默认为当前目录的 .github-auto-sync.yml
            use_env: 是否使用环境变量覆盖配置
            create_default: 如果配置文件不存在，是否创建默认配置
            
        Returns:
            Config 实例
            
        Raises:
            FileNotFoundError: 配置文件不存在且 create_default=False
            ValueError: 配置文件格式错误
        """
        if config_path is None:
            config_path = Path.cwd() / DEFAULT_CONFIG_FILENAME
        else:
            config_path = Path(config_path)
        
        # 如果配置文件不存在
        if not config_path.exists():
            if create_default:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
                print(f"Created default config file: {config_path}")
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # 读取 YAML 文件
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in config file: {e}")
        
        if data is None:
            data = {}
        
        # 解析配置
        config = cls._from_dict(data)
        config._config_path = config_path
        config._loaded = True
        
        # 应用环境变量覆盖
        if use_env:
            config._apply_env_variables()
        
        return config
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置实例"""
        config = cls()
        
        # GitHub 配置
        if "github" in data:
            github_data = data["github"]
            config.github = {
                "token": github_data.get("token", ""),
                "username": github_data.get("username", ""),
            }
        
        # 仓库配置列表
        if "repositories" in data:
            config.repositories = [
                RepositoryConfig(**repo_data)
                for repo_data in data["repositories"]
            ]
        
        # 同步设置
        if "sync" in data:
            sync_data = data["sync"]
            config.sync = SyncConfig(**sync_data)
        
        # 日志设置
        if "logging" in data:
            logging_data = data["logging"]
            config.logging = LoggingConfig(**logging_data)
        
        # 通知设置
        if "notifications" in data:
            notif_data = data["notifications"]
            config.notifications = NotificationConfig(**notif_data)
        
        return config
    
    def _apply_env_variables(self) -> None:
        """应用环境变量覆盖配置"""
        # GitHub Token
        token = os.getenv(f"{ENV_PREFIX}TOKEN")
        if token:
            self.github["token"] = token
        
        # GitHub Username
        username = os.getenv(f"{ENV_PREFIX}USERNAME")
        if username:
            self.github["username"] = username
        
        # 其他环境变量映射
        env_mappings = {
            f"{ENV_PREFIX}BATCH_WINDOW": ("sync", "batch_window", int),
            f"{ENV_PREFIX}MAX_FILES": ("sync", "max_files_per_commit", int),
            f"{ENV_PREFIX}AUTO_PUSH": ("sync", "auto_push", lambda x: x.lower() == "true"),
            f"{ENV_PREFIX}AUTO_PULL": ("sync", "auto_pull", lambda x: x.lower() == "true"),
            f"{ENV_PREFIX}LOG_LEVEL": ("logging", "level", str),
            f"{ENV_PREFIX}LOG_FILE": ("logging", "file", str),
        }
        
        for env_var, (section, key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                try:
                    converted_value = converter(value)
                    section_obj = getattr(self, section)
                    setattr(section_obj, key, converted_value)
                except (ValueError, TypeError):
                    pass  # 忽略转换失败的值
    
    def validate(self) -> List[str]:
        """
        验证配置有效性
        
        Returns:
            错误消息列表，空列表表示配置有效
        """
        errors = []
        
        # 验证 GitHub Token
        if not self.github.get("token"):
            errors.append("GitHub token is required (set in config or GITHUB_TOKEN env var)")
        
        # 验证 GitHub Token 格式 (基本检查)
        token = self.github.get("token", "")
        if token and not re.match(r"^gh[ps]_[a-zA-Z0-9]{36}$|^\d+_[a-zA-Z0-9]{40}$", token):
            # GitHub 有多种 token 格式，这里只做基本检查
            pass  # 不强制验证格式，因为 GitHub 可能会更新格式
        
        # 验证仓库配置
        if not self.repositories:
            errors.append("At least one repository must be configured")
        else:
            for i, repo in enumerate(self.repositories):
                if not repo.name:
                    errors.append(f"Repository #{i+1}: name is required")
                if not repo.local_path:
                    errors.append(f"Repository '{repo.name}': local_path is required")
        
        # 验证同步设置
        if self.sync.batch_window < 0:
            errors.append("sync.batch_window must be non-negative")
        if self.sync.max_files_per_commit < 1:
            errors.append("sync.max_files_per_commit must be at least 1")
        if self.sync.conflict_strategy not in ("skip", "overwrite", "merge"):
            errors.append("sync.conflict_strategy must be one of: skip, overwrite, merge")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            "github": self.github,
            "repositories": [
                {
                    "name": repo.name,
                    "local_path": repo.local_path,
                    "remote_url": repo.remote_url,
                    "branch": repo.branch,
                    "auto_sync": repo.auto_sync,
                    "ignore_patterns": repo.ignore_patterns,
                }
                for repo in self.repositories
            ],
            "sync": {
                "batch_window": self.sync.batch_window,
                "max_files_per_commit": self.sync.max_files_per_commit,
                "commit_message_template": self.sync.commit_message_template,
                "auto_push": self.sync.auto_push,
                "auto_pull": self.sync.auto_pull,
                "conflict_strategy": self.sync.conflict_strategy,
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "color": self.logging.color,
            },
            "notifications": {
                "on_error": self.notifications.on_error,
                "on_success": self.notifications.on_success,
            },
        }
    
    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，默认使用加载时的路径或当前目录
        """
        if config_path is None:
            config_path = self._config_path or (Path.cwd() / DEFAULT_CONFIG_FILENAME)
        else:
            config_path = Path(config_path)
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为 YAML
        data = self.to_dict()
        yaml_content = yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        
        # 写入文件
        config_path.write_text(yaml_content, encoding="utf-8")
        self._config_path = config_path
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            updates: 要更新的配置项字典
        """
        # 更新 GitHub 配置
        if "github" in updates:
            self.github.update(updates["github"])
        
        # 更新仓库配置
        if "repositories" in updates:
            self.repositories = [
                RepositoryConfig(**repo_data)
                for repo_data in updates["repositories"]
            ]
        
        # 更新同步设置
        if "sync" in updates:
            for key, value in updates["sync"].items():
                if hasattr(self.sync, key):
                    setattr(self.sync, key, value)
        
        # 更新日志设置
        if "logging" in updates:
            for key, value in updates["logging"].items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        
        # 更新通知设置
        if "notifications" in updates:
            for key, value in updates["notifications"].items():
                if hasattr(self.notifications, key):
                    setattr(self.notifications, key, value)
    
    def get_repository(self, name: str) -> Optional[RepositoryConfig]:
        """
        根据名称获取仓库配置
        
        Args:
            name: 仓库名称
            
        Returns:
            RepositoryConfig 或 None
        """
        for repo in self.repositories:
            if repo.name == name:
                return repo
        return None
    
    def add_repository(self, repo_config: RepositoryConfig) -> None:
        """
        添加仓库配置
        
        Args:
            repo_config: 仓库配置
        """
        # 检查是否已存在同名仓库
        existing = self.get_repository(repo_config.name)
        if existing:
            raise ValueError(f"Repository '{repo_config.name}' already exists")
        
        self.repositories.append(repo_config)
    
    def remove_repository(self, name: str) -> bool:
        """
        移除仓库配置
        
        Args:
            name: 仓库名称
            
        Returns:
            是否成功移除
        """
        for i, repo in enumerate(self.repositories):
            if repo.name == name:
                self.repositories.pop(i)
                return True
        return False
    
    @property
    def config_path(self) -> Optional[Path]:
        """获取配置文件路径"""
        return self._config_path
    
    @property
    def is_loaded(self) -> bool:
        """检查配置是否已从文件加载"""
        return self._loaded
    
    @classmethod
    def generate_template(cls, include_comments: bool = True) -> str:
        """
        生成默认配置模板
        
        Args:
            include_comments: 是否包含注释说明
            
        Returns:
            配置模板字符串
        """
        if include_comments:
            return DEFAULT_CONFIG_TEMPLATE
        else:
            # 生成无注释的简洁版本
            config = cls()
            return yaml.dump(
                config.to_dict(),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )


def find_config_file(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    向上查找配置文件
    
    从指定路径开始，向上级目录查找 .github-auto-sync.yml 文件
    
    Args:
        start_path: 起始路径，默认为当前工作目录
        
    Returns:
        配置文件路径或 None
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)
    
    current = start_path.resolve()
    
    # 如果是文件，从父目录开始
    if current.is_file():
        current = current.parent
    
    # 向上查找
    while current != current.parent:
        config_file = current / DEFAULT_CONFIG_FILENAME
        if config_file.exists():
            return config_file
        current = current.parent
    
    return None


def init_config(
    path: Optional[Union[str, Path]] = None,
    force: bool = False,
) -> Path:
    """
    初始化配置文件
    
    Args:
        path: 配置文件路径，默认为当前目录
        force: 如果文件已存在，是否覆盖
        
    Returns:
        创建的配置文件路径
        
    Raises:
        FileExistsError: 配置文件已存在且 force=False
    """
    if path is None:
        path = Path.cwd() / DEFAULT_CONFIG_FILENAME
    else:
        path = Path(path)
    
    if path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {path}")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    
    return path
