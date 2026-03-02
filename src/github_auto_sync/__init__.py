"""
GitHub Auto Sync - 自动同步本地文件夹到 GitHub 仓库的工具

一个强大的 Python 工具，用于自动监控本地文件夹变化并同步到 GitHub 仓库。
支持文件监控、自动提交、推送和冲突解决等功能。
"""

__version__ = "0.1.0"
__author__ = "GitHub Auto Sync Team"
__email__ = "support@github-auto-sync.dev"
__license__ = "MIT"
__url__ = "https://github.com/yourusername/github-auto-sync"

# 版本信息
VERSION = __version__
VERSION_INFO = tuple(map(int, __version__.split('.')))

# 导出主要类和函数
__all__ = [
    "VERSION",
    "VERSION_INFO",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    # CLI
    "cli",
    "main",
]

# 导入子模块（延迟导入以避免循环依赖）
def _import_auth():
    """延迟导入认证模块"""
    from . import auth
    return auth


def _import_config():
    """延迟导入配置模块"""
    from . import config
    return config


def _import_github_client():
    """延迟导入 GitHub 客户端模块"""
    from . import github_client
    return github_client


def _import_sync():
    """延迟导入同步引擎模块"""
    from . import sync
    return sync


def _import_watcher():
    """延迟导入文件监控模块"""
    from . import watcher
    return watcher


def _import_git_operations():
    """延迟导入 Git 操作模块"""
    from . import git_operations
    return git_operations


def _import_cli():
    """延迟导入 CLI 模块"""
    from . import cli
    return cli


# CLI 入口点
def cli():
    """CLI 入口点"""
    from .cli import cli as _cli
    return _cli()


def main():
    """程序主入口点"""
    from .cli import main as _main
    return _main()
