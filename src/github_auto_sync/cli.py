"""
GitHub Auto Sync CLI 模块

提供命令行界面，支持以下命令：
- init: 初始化配置文件
- auth: 认证管理（登录/登出/状态）
- sync: 同步文件夹到 GitHub
- watch: 监控文件夹并自动同步
- list: 列出配置的仓库
- config: 配置管理
- repo: 仓库管理

使用 Click 框架构建，支持彩色输出和详细日志模式。
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from click import Context, Parameter

from . import __version__
from .auth import (
    AuthenticationError,
    authenticate,
    get_auth_token,
    get_auth_username,
    is_authenticated,
    logout,
    validate_token,
)
from .config import Config, RepositoryConfig, init_config
from .github_client import (
    GitHubClient,
    GitHubClientError,
    PermissionError,
    RateLimitError,
    RepositoryAlreadyExistsError,
    RepositoryNotFoundError,
)
from .sync import SyncManager, SyncStatus, create_sync_manager


# ============================================================================
# 样式和格式化工具
# ============================================================================

class Colors:
    """颜色常量"""
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"
    DIM = "bright_black"


def success(message: str, verbose: bool = False) -> None:
    """打印成功消息"""
    click.secho(f"✓ {message}", fg=Colors.SUCCESS)


def error(message: str, verbose: bool = False) -> None:
    """打印错误消息"""
    click.secho(f"✗ {message}", fg=Colors.ERROR, err=True)


def warning(message: str, verbose: bool = False) -> None:
    """打印警告消息"""
    click.secho(f"⚠ {message}", fg=Colors.WARNING)


def info(message: str, verbose: bool = False) -> None:
    """打印信息消息"""
    click.secho(f"ℹ {message}", fg=Colors.INFO)


def dim(message: str, verbose: bool = False) -> None:
    """打印暗淡消息"""
    click.secho(message, fg=Colors.DIM)


def print_table(headers: List[str], rows: List[List[str]], verbose: bool = False) -> None:
    """打印表格"""
    if not rows:
        info("无数据")
        return

    # 计算列宽
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # 打印表头
    header_line = " | ".join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    )
    click.secho(header_line, fg=Colors.INFO, bold=True)
    click.secho("-" * len(header_line), fg=Colors.DIM)

    # 打印行
    for row in rows:
        line = " | ".join(
            str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
        )
        click.echo(line)


def print_key_value(data: Dict[str, Any], verbose: bool = False) -> None:
    """打印键值对"""
    max_key_len = max(len(k) for k in data.keys())
    for key, value in data.items():
        key_str = f"{key}:".ljust(max_key_len + 1)
        click.secho(f"  {key_str} ", fg=Colors.DIM, nl=False)
        click.echo(value)


# ============================================================================
# 错误处理
# ============================================================================

class CLIError(Exception):
    """CLI 错误异常"""
    pass


def handle_error(e: Exception, verbose: bool = False) -> None:
    """统一错误处理"""
    if isinstance(e, AuthenticationError):
        error(f"认证错误: {e}")
        info("请运行 'github-auto-sync auth login' 进行认证")
    elif isinstance(e, RepositoryNotFoundError):
        error(f"仓库不存在: {e}")
    elif isinstance(e, RepositoryAlreadyExistsError):
        error(f"仓库已存在: {e}")
    elif isinstance(e, RateLimitError):
        error(f"API 速率限制: {e}")
        warning("请稍后重试或检查您的 GitHub API 配额")
    elif isinstance(e, PermissionError):
        error(f"权限不足: {e}")
        warning("请检查您的 GitHub Token 权限")
    elif isinstance(e, GitHubClientError):
        error(f"GitHub API 错误: {e}")
    elif isinstance(e, FileNotFoundError):
        error(f"文件不存在: {e}")
    elif isinstance(e, ValueError):
        error(f"参数错误: {e}")
    else:
        error(f"错误: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)


# ============================================================================
# 上下文对象
# ============================================================================

class CLIContext:
    """CLI 上下文对象"""

    def __init__(self, config_path: Optional[Path] = None, verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose
        self._config: Optional[Config] = None

    def get_config(self, required: bool = True) -> Optional[Config]:
        """获取配置"""
        if self._config is None:
            try:
                self._config = Config.load(self.config_path)
            except FileNotFoundError:
                if required:
                    raise CLIError(
                        "未找到配置文件。请运行 'github-auto-sync init' 初始化配置。"
                    )
                return None
        return self._config

    def log(self, message: str, level: str = "info") -> None:
        """记录日志"""
        if not self.verbose and level == "debug":
            return
        if level == "error":
            error(message, self.verbose)
        elif level == "warning":
            warning(message, self.verbose)
        elif level == "success":
            success(message, self.verbose)
        elif level == "debug":
            dim(f"[DEBUG] {message}", self.verbose)
        else:
            info(message, self.verbose)


# ============================================================================
# 主 CLI 组
# ============================================================================

@click.group()
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(path_type=Path, exists=False),
    help="配置文件路径",
)
@click.option("-v", "--verbose", is_flag=True, help="启用详细输出")
@click.version_option(version=__version__, prog_name="github-auto-sync")
@click.pass_context
def cli(ctx: Context, config_path: Optional[Path], verbose: bool) -> None:
    """
    GitHub Auto Sync - 自动同步本地文件夹到 GitHub

    一个强大的工具，用于自动监控本地文件夹变化并同步到 GitHub 仓库。

    示例:
        github-auto-sync init                    # 初始化配置
        github-auto-sync auth login              # 登录 GitHub
        github-auto-sync sync my-project         # 同步项目
        github-auto-sync watch my-project        # 监控并自动同步
    """
    ctx.obj = CLIContext(config_path=config_path, verbose=verbose)


# ============================================================================
# init 命令
# ============================================================================

@cli.command()
@click.option(
    "-p",
    "--path",
    "config_path",
    type=click.Path(path_type=Path),
    help="配置文件保存路径",
)
@click.option("-f", "--force", is_flag=True, help="强制覆盖已存在的配置文件")
@click.pass_context
def init(ctx: Context, config_path: Optional[Path], force: bool) -> None:
    """
    初始化配置文件

    在当前目录或指定路径创建默认的配置文件。

    示例:
        github-auto-sync init                    # 在当前目录创建配置
        github-auto-sync init -p ./config.yml    # 指定路径创建配置
        github-auto-sync init -f                 # 强制覆盖现有配置
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        path = init_config(path=config_path, force=force)
        success(f"配置文件已创建: {path}")
        info("请编辑配置文件，设置您的 GitHub Token 和仓库信息")
        info("然后运行 'github-auto-sync auth login' 进行认证")
    except FileExistsError as e:
        error(str(e))
        info("使用 -f/--force 选项强制覆盖")
        sys.exit(1)
    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# auth 命令组
# ============================================================================

@cli.group()
def auth() -> None:
    """认证管理（登录/登出/状态）"""
    pass


@auth.command(name="login")
@click.option("-t", "--token", help="GitHub Personal Access Token")
@click.option("-u", "--username", help="GitHub 用户名")
@click.option("--no-store", is_flag=True, help="不保存凭证到系统密钥环")
@click.pass_context
def auth_login(
    ctx: Context, token: Optional[str], username: Optional[str], no_store: bool
) -> None:
    """
    登录 GitHub

    使用 GitHub Token 进行认证。如果不提供 token，将提示输入。

    示例:
        github-auto-sync auth login
        github-auto-sync auth login -t ghp_xxxxxx
        github-auto-sync auth login -t ghp_xxxxxx -u myusername
    """
    cli_ctx: CLIContext = ctx.obj

    # 如果没有提供 token，提示输入
    if not token:
        token = click.prompt("请输入 GitHub Token", hide_input=True)

    if not token:
        error("Token 不能为空")
        sys.exit(1)

    try:
        # 验证 token
        cli_ctx.log("正在验证 token...", "info")
        valid, info = validate_token(token)

        if not valid:
            error(f"Token 验证失败: {info}")
            sys.exit(1)

        # 如果没有提供用户名，使用 API 返回的用户名
        if not username:
            username = info

        # 执行认证
        store = not no_store
        success_flag, message = authenticate(token, username, store=store)

        if success_flag:
            success(message)
            if not store:
                info("凭证未保存到系统密钥环，仅在当前会话有效")
        else:
            error(message)
            sys.exit(1)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@auth.command(name="logout")
@click.confirmation_option(
    prompt="确定要登出并清除保存的凭证吗？",
    help="自动确认登出操作",
)
@click.pass_context
def auth_logout(ctx: Context) -> None:
    """
    登出 GitHub

    清除保存在系统密钥环中的凭证。

    示例:
        github-auto-sync auth logout
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        if logout():
            success("已成功登出")
        else:
            warning("登出完成，但清除凭证时出现问题")
    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@auth.command(name="status")
@click.pass_context
def auth_status(ctx: Context) -> None:
    """
    查看认证状态

    显示当前认证状态和用户信息。

    示例:
        github-auto-sync auth status
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        if not is_authenticated():
            warning("未认证")
            info("请运行 'github-auto-sync auth login' 进行认证")
            sys.exit(1)

        username = get_auth_username()
        token = get_auth_token()

        success("已认证")
        print_key_value({
            "用户名": username or "未知",
            "Token": f"{token[:10]}..." if token and len(token) > 10 else "***",
        })

        # 验证 token 有效性
        try:
            valid, info = validate_token(token) if token else (False, "无 token")
            if valid:
                info(f"Token 有效 (用户: @{info})")
            else:
                warning(f"Token 可能已失效: {info}")
        except Exception as e:
            warning(f"无法验证 token: {e}")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# sync 命令
# ============================================================================

@cli.command()
@click.argument("repository", required=False)
@click.option("-i", "--initial", is_flag=True, help="执行初始同步（全量上传）")
@click.option("-d", "--dry-run", is_flag=True, help="试运行模式（不实际执行操作）")
@click.option("--all", "sync_all", is_flag=True, help="同步所有配置的仓库")
@click.pass_context
def sync(
    ctx: Context,
    repository: Optional[str],
    initial: bool,
    dry_run: bool,
    sync_all: bool,
) -> None:
    """
    同步文件夹到 GitHub

    将本地文件夹的变更同步到 GitHub 仓库。

    示例:
        github-auto-sync sync                      # 同步默认仓库
        github-auto-sync sync my-project           # 同步指定仓库
        github-auto-sync sync my-project --initial # 初始同步
        github-auto-sync sync --all                # 同步所有仓库
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        config = cli_ctx.get_config(required=True)

        if sync_all:
            # 同步所有仓库
            if not config.repositories:
                error("配置中没有仓库")
                sys.exit(1)

            for repo_config in config.repositories:
                _sync_single_repo(cli_ctx, config, repo_config, initial, dry_run)
        else:
            # 同步单个仓库
            if not repository and config.repositories:
                # 如果没有指定仓库，使用第一个
                repository = config.repositories[0].name
                cli_ctx.log(f"使用默认仓库: {repository}", "info")

            if not repository:
                error("请指定仓库名称或使用 --all 同步所有仓库")
                sys.exit(1)

            repo_config = config.get_repository(repository)
            if not repo_config:
                error(f"未找到仓库配置: {repository}")
                info("请使用 'github-auto-sync list' 查看可用仓库")
                sys.exit(1)

            _sync_single_repo(cli_ctx, config, repo_config, initial, dry_run)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


def _sync_single_repo(
    cli_ctx: CLIContext,
    config: Config,
    repo_config: RepositoryConfig,
    initial: bool,
    dry_run: bool,
) -> None:
    """同步单个仓库"""
    info(f"正在同步仓库: {repo_config.name}")

    if dry_run:
        warning("试运行模式 - 不会实际执行任何操作")

    try:
        manager = SyncManager(config, repo_config, dry_run=dry_run)

        if initial:
            result = manager.initial_sync()
        else:
            result = manager.sync_changes()

        if result.success:
            success(f"同步成功: {result.message}")
            if result.commit_hash:
                info(f"提交: {result.commit_hash}")
            if result.files_synced:
                info(f"同步文件数: {len(result.files_synced)}")
        else:
            error(f"同步失败: {result.message}")
            if result.files_failed:
                error(f"失败文件: {', '.join(result.files_failed)}")

    except Exception as e:
        raise CLIError(f"同步仓库 '{repo_config.name}' 失败: {e}")


# ============================================================================
# watch 命令
# ============================================================================

@cli.command()
@click.argument("repository", required=False)
@click.option("--interval", type=float, help="批处理时间窗口（秒）")
@click.pass_context
def watch(ctx: Context, repository: Optional[str], interval: Optional[float]) -> None:
    """
    监控文件夹并自动同步

    启动文件监控器，当检测到文件变更时自动同步到 GitHub。

    按 Ctrl+C 停止监控。

    示例:
        github-auto-sync watch              # 监控默认仓库
        github-auto-sync watch my-project   # 监控指定仓库
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        config = cli_ctx.get_config(required=True)

        if not repository and config.repositories:
            repository = config.repositories[0].name
            cli_ctx.log(f"使用默认仓库: {repository}", "info")

        if not repository:
            error("请指定仓库名称")
            sys.exit(1)

        repo_config = config.get_repository(repository)
        if not repo_config:
            error(f"未找到仓库配置: {repository}")
            sys.exit(1)

        info(f"正在启动监控: {repo_config.name}")
        info(f"监控路径: {repo_config.local_path}")
        info("按 Ctrl+C 停止监控")

        # 创建同步管理器
        manager = SyncManager(config, repo_config)

        # 先执行一次同步
        result = manager.sync_changes()
        if result.success:
            success("初始同步完成")
        else:
            warning(f"初始同步: {result.message}")

        # 启动自动同步
        if not manager.start_auto_sync():
            error("启动监控失败")
            sys.exit(1)

        success("监控已启动，等待文件变更...")

        # 保持运行直到用户中断
        try:
            import time
            while manager.is_auto_sync_running():
                time.sleep(1)
        except KeyboardInterrupt:
            info("\n正在停止监控...")
            manager.stop_auto_sync()
            success("监控已停止")

    except KeyboardInterrupt:
        info("\n已取消")
    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# list 命令
# ============================================================================

@cli.command(name="list")
@click.option("--json", "output_json", is_flag=True, help="以 JSON 格式输出")
@click.pass_context
def list_repos(ctx: Context, output_json: bool) -> None:
    """
    列出配置的仓库

    显示所有已配置的仓库信息。

    示例:
        github-auto-sync list
        github-auto-sync list --json
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        config = cli_ctx.get_config(required=True)

        if not config.repositories:
            warning("配置中没有仓库")
            info("使用 'github-auto-sync config add-repo' 添加仓库")
            return

        if output_json:
            import json
            data = [
                {
                    "name": repo.name,
                    "local_path": repo.local_path,
                    "remote_url": repo.remote_url,
                    "branch": repo.branch,
                    "auto_sync": repo.auto_sync,
                }
                for repo in config.repositories
            ]
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            headers = ["名称", "本地路径", "分支", "自动同步"]
            rows = [
                [
                    repo.name,
                    repo.local_path,
                    repo.branch,
                    "是" if repo.auto_sync else "否",
                ]
                for repo in config.repositories
            ]
            print_table(headers, rows, cli_ctx.verbose)
            info(f"共 {len(config.repositories)} 个仓库")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# config 命令组
# ============================================================================

@cli.group()
def config() -> None:
    """配置管理（get/set/add-repo/remove-repo）"""
    pass


@config.command(name="get")
@click.argument("key")
@click.pass_context
def config_get(ctx: Context, key: str) -> None:
    """
    获取配置项

    支持使用点号访问嵌套配置，如：github.token、sync.auto_push

    示例:
        github-auto-sync config get github.token
        github-auto-sync config get sync.batch_window
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        cfg = cli_ctx.get_config(required=True)

        # 解析键路径
        keys = key.split(".")
        value = cfg.to_dict()

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            elif isinstance(value, list) and k.isdigit():
                idx = int(k)
                if 0 <= idx < len(value):
                    value = value[idx]
                else:
                    error(f"索引越界: {k}")
                    sys.exit(1)
            else:
                error(f"配置项不存在: {key}")
                sys.exit(1)

        click.echo(value)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@config.command(name="set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: Context, key: str, value: str) -> None:
    """
    设置配置项

    支持使用点号访问嵌套配置。

    示例:
        github-auto-sync config set github.token ghp_xxxxxx
        github-auto-sync config set sync.auto_push true
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        cfg = cli_ctx.get_config(required=True)

        # 尝试转换值类型
        converted_value: Any = value
        if value.lower() == "true":
            converted_value = True
        elif value.lower() == "false":
            converted_value = False
        elif value.isdigit():
            converted_value = int(value)

        # 解析键路径
        keys = key.split(".")
        data = cfg.to_dict()

        # 导航到目标位置
        target = data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # 设置值
        target[keys[-1]] = converted_value

        # 更新配置
        cfg.update(data)
        cfg.save()

        success(f"配置已更新: {key} = {converted_value}")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@config.command(name="add-repo")
@click.option("-n", "--name", required=True, help="仓库名称")
@click.option("-p", "--path", "local_path", required=True, help="本地路径")
@click.option("-r", "--remote", "remote_url", help="远程仓库 URL")
@click.option("-b", "--branch", default="main", help="默认分支")
@click.option("--no-auto-sync", is_flag=True, help="禁用自动同步")
@click.pass_context
def config_add_repo(
    ctx: Context,
    name: str,
    local_path: str,
    remote_url: Optional[str],
    branch: str,
    no_auto_sync: bool,
) -> None:
    """
    添加仓库配置

    示例:
        github-auto-sync config add-repo -n my-project -p ./my-project
        github-auto-sync config add-repo -n my-project -p ./my-project -r https://github.com/user/repo.git
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        cfg = cli_ctx.get_config(required=True)

        # 检查是否已存在
        if cfg.get_repository(name):
            error(f"仓库 '{name}' 已存在")
            sys.exit(1)

        # 解析本地路径
        path = Path(local_path).expanduser().resolve()
        if not path.exists():
            warning(f"路径不存在: {path}")
            if not click.confirm("是否继续？"):
                info("已取消")
                return

        # 创建仓库配置
        repo_config = RepositoryConfig(
            name=name,
            local_path=str(path),
            remote_url=remote_url or "",
            branch=branch,
            auto_sync=not no_auto_sync,
        )

        cfg.add_repository(repo_config)
        cfg.save()

        success(f"仓库已添加: {name}")
        info(f"本地路径: {path}")
        if remote_url:
            info(f"远程 URL: {remote_url}")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@config.command(name="remove-repo")
@click.argument("name")
@click.confirmation_option(prompt="确定要删除此仓库配置吗？")
@click.pass_context
def config_remove_repo(ctx: Context, name: str) -> None:
    """
    移除仓库配置

    示例:
        github-auto-sync config remove-repo my-project
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        cfg = cli_ctx.get_config(required=True)

        if not cfg.get_repository(name):
            error(f"仓库 '{name}' 不存在")
            sys.exit(1)

        if cfg.remove_repository(name):
            cfg.save()
            success(f"仓库已移除: {name}")
        else:
            error(f"移除仓库失败: {name}")
            sys.exit(1)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@config.command(name="show")
@click.pass_context
def config_show(ctx: Context) -> None:
    """
    显示完整配置

    示例:
        github-auto-sync config show
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        cfg = cli_ctx.get_config(required=True)

        import yaml

        click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False, allow_unicode=True))

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# repo 命令组
# ============================================================================

@cli.group()
def repo() -> None:
    """仓库管理（create/delete）"""
    pass


@repo.command(name="create")
@click.argument("name")
@click.option("-d", "--description", help="仓库描述")
@click.option("--public", is_flag=True, help="创建公开仓库（默认私有）")
@click.option("--auto-init", is_flag=True, help="自动初始化 README")
@click.option("--gitignore", help="Gitignore 模板（如 Python, Node）")
@click.option("--license", "license_template", help="许可证模板（如 mit, apache-2.0）")
@click.pass_context
def repo_create(
    ctx: Context,
    name: str,
    description: Optional[str],
    public: bool,
    auto_init: bool,
    gitignore: Optional[str],
    license_template: Optional[str],
) -> None:
    """
    在 GitHub 上创建仓库

    示例:
        github-auto-sync repo create my-new-repo
        github-auto-sync repo create my-new-repo -d "我的新项目" --public
        github-auto-sync repo create my-new-repo --gitignore Python --license mit
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        client = GitHubClient()

        info(f"正在创建仓库: {name}")

        result = client.create_repo(
            name=name,
            description=description or f"Auto-synced repository: {name}",
            private=not public,
            auto_init=auto_init,
            gitignore_template=gitignore,
            license_template=license_template,
        )

        success(f"仓库创建成功: {result['html_url']}")
        print_key_value({
            "名称": result["full_name"],
            "URL": result["html_url"],
            "克隆 URL": result["clone_url"],
            "私有": "否" if public else "是",
            "默认分支": result["default_branch"],
        })

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@repo.command(name="delete")
@click.argument("name")
@click.confirmation_option(
    prompt="警告：此操作不可恢复！确定要删除此仓库吗？",
    help="自动确认删除操作",
)
@click.pass_context
def repo_delete(ctx: Context, name: str) -> None:
    """
    删除 GitHub 仓库

    警告：此操作不可恢复！

    示例:
        github-auto-sync repo delete my-repo
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        client = GitHubClient()

        warning(f"正在删除仓库: {name}")

        if client.delete_repo(name):
            success(f"仓库已删除: {name}")
        else:
            error(f"删除仓库失败: {name}")
            sys.exit(1)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@repo.command(name="list")
@click.option("--limit", "-n", default=30, help="显示数量限制")
@click.option("--json", "output_json", is_flag=True, help="以 JSON 格式输出")
@click.pass_context
def repo_list(ctx: Context, n: int, output_json: bool) -> None:
    """
    列出 GitHub 上的仓库

    示例:
        github-auto-sync repo list
        github-auto-sync repo list -n 10
        github-auto-sync repo list --json
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        client = GitHubClient()

        info("正在获取仓库列表...")

        repos = client.list_repos()[:n]

        if output_json:
            import json

            click.echo(json.dumps(repos, indent=2, ensure_ascii=False))
        else:
            headers = ["名称", "描述", "更新于", "私有"]
            rows = []
            for repo in repos:
                desc = (repo.get("description") or "")[:30]
                if len(desc) == 30:
                    desc += "..."
                updated = repo.get("updated_at", "")[:10] if repo.get("updated_at") else ""
                rows.append([
                    repo["name"],
                    desc,
                    updated,
                    "是" if repo.get("private") else "否",
                ])
            print_table(headers, rows, cli_ctx.verbose)
            info(f"共 {len(repos)} 个仓库")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# Release 命令组
# ============================================================================

@cli.group(name="release")
def release():
    """
    Release 管理命令

    用于创建和管理 GitHub Release

    示例:
        github-auto-sync release create v1.0.0 -n "版本 1.0.0" -b "更新内容"
        github-auto-sync release list
        github-auto-sync release upload v1.0.0 ./dist/app.zip
    """
    pass


@release.command(name="create")
@click.argument("tag")
@click.option("--name", "-n", required=True, help="Release 标题")
@click.option("--body", "-b", required=True, help="Release 描述（支持 Markdown）")
@click.option("--draft", is_flag=True, help="创建为草稿")
@click.option("--prerelease", is_flag=True, help="标记为预发布版本")
@click.option("--target", "-t", default="main", help="目标分支（默认: main）")
@click.option("--repo", "-r", help="仓库名称（默认使用配置中的第一个仓库）")
@click.pass_context
def release_create(
    ctx: Context,
    tag: str,
    name: str,
    body: str,
    draft: bool,
    prerelease: bool,
    target: str,
    repo: Optional[str],
) -> None:
    """
    创建 GitHub Release

    TAG: 标签名称（例如：v1.0.0）

    示例:
        github-auto-sync release create v1.0.0 -n "版本 1.0.0" -b "## 更新内容"
        github-auto-sync release create v1.0.0 -n "测试版" -b "预览版本" --prerelease
        github-auto-sync release create v1.0.0 -n "草稿" -b "未完成" --draft
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        # 获取仓库名称
        if not repo:
            config = cli_ctx.config
            if config.repositories:
                repo = config.repositories[0].name
            else:
                error("未指定仓库名称，请使用 -r 选项或配置默认仓库")
                sys.exit(1)

        client = GitHubClient()

        info(f"正在创建 Release: {tag}")

        release_info = client.create_release(
            repo_name=repo,
            tag_name=tag,
            name=name,
            body=body,
            draft=draft,
            prerelease=prerelease,
            target_commitish=target,
        )

        if release_info:
            success(f"Release 创建成功!")
            info(f"URL: {release_info['html_url']}")
            info(f"ID: {release_info['id']}")
        else:
            error("创建 Release 失败")
            sys.exit(1)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@release.command(name="upload")
@click.argument("tag")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--label", "-l", help="文件标签")
@click.option("--repo", "-r", help="仓库名称")
@click.pass_context
def release_upload(
    ctx: Context,
    tag: str,
    file_path: str,
    label: Optional[str],
    repo: Optional[str],
) -> None:
    """
    上传文件到 Release

    TAG: 标签名称
    FILE_PATH: 文件路径

    示例:
        github-auto-sync release upload v1.0.0 ./dist/app.zip
        github-auto-sync release upload v1.0.0 ./app.zip -l "应用程序"
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        # 获取仓库名称
        if not repo:
            config = cli_ctx.config
            if config.repositories:
                repo = config.repositories[0].name
            else:
                error("未指定仓库名称，请使用 -r 选项或配置默认仓库")
                sys.exit(1)

        client = GitHubClient()

        # 获取 Release ID
        releases = client.list_releases(repo_name=repo)
        release_id = None
        for r in releases:
            if r["tag_name"] == tag:
                release_id = r["id"]
                break

        if not release_id:
            error(f"未找到 Release: {tag}")
            sys.exit(1)

        info(f"正在上传文件到 Release: {tag}")

        asset = client.upload_release_asset(
            repo_name=repo,
            release_id=release_id,
            file_path=file_path,
            label=label,
        )

        if asset:
            success(f"文件上传成功!")
            info(f"下载链接: {asset['browser_download_url']}")
        else:
            error("上传文件失败")
            sys.exit(1)

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


@release.command(name="list")
@click.option("--repo", "-r", help="仓库名称")
@click.option("--limit", "-n", default=10, help="显示数量限制")
@click.pass_context
def release_list(ctx: Context, repo: Optional[str], n: int) -> None:
    """
    列出 Release

    示例:
        github-auto-sync release list
        github-auto-sync release list -n 20
    """
    cli_ctx: CLIContext = ctx.obj

    try:
        # 检查认证
        if not is_authenticated():
            error("未认证，请先运行 'github-auto-sync auth login'")
            sys.exit(1)

        # 获取仓库名称
        if not repo:
            config = cli_ctx.config
            if config.repositories:
                repo = config.repositories[0].name
            else:
                error("未指定仓库名称，请使用 -r 选项或配置默认仓库")
                sys.exit(1)

        client = GitHubClient()

        info(f"正在获取 Release 列表...")

        releases = client.list_releases(repo_name=repo, limit=n)

        if releases:
            headers = ["标签", "名称", "类型", "发布时间"]
            rows = []
            for r in releases:
                release_type = ""
                if r.get("draft"):
                    release_type = "草稿"
                elif r.get("prerelease"):
                    release_type = "预发布"
                else:
                    release_type = "正式版"

                published = r.get("published_at", "")[:10] if r.get("published_at") else "未发布"

                rows.append([
                    r["tag_name"],
                    r["name"],
                    release_type,
                    published,
                ])
            print_table(headers, rows, cli_ctx.verbose)
            info(f"共 {len(releases)} 个 Release")
        else:
            info("暂无 Release")

    except Exception as e:
        handle_error(e, cli_ctx.verbose)
        sys.exit(1)


# ============================================================================
# 入口点
# ============================================================================

def main() -> None:
    """CLI 入口点"""
    cli()


if __name__ == "__main__":
    main()
