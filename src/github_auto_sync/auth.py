"""
GitHub Auto Sync 认证模块

提供 GitHub Token 管理、安全凭证存储和认证状态检查功能。
支持 keyring 安全存储和 .env 文件加载。
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple

import keyring
import requests
from dotenv import load_dotenv


# 服务名称常量
SERVICE_NAME = "github-auto-sync"
USERNAME_KEY = "username"
TOKEN_KEY = "token"

# GitHub API 基础 URL
GITHUB_API_URL = "https://api.github.com"


class AuthenticationError(Exception):
    """认证错误异常"""
    pass


class TokenValidationError(Exception):
    """Token 验证错误异常"""
    pass


def load_dotenv(dotenv_path: Optional[Path] = None) -> bool:
    """
    从 .env 文件加载环境变量

    加载 .env 文件中的环境变量到当前进程环境。
    支持 GITHUB_TOKEN 和 GITHUB_USERNAME 变量。

    Args:
        dotenv_path: .env 文件路径，默认为当前目录的 .env 文件

    Returns:
        是否成功加载 .env 文件

    Examples:
        >>> load_dotenv()  # 加载当前目录的 .env
        True
        >>> load_dotenv(Path("/path/to/.env"))  # 加载指定路径
        True
    """
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
    else:
        dotenv_path = Path(dotenv_path)

    if not dotenv_path.exists():
        return False

    load_dotenv(dotenv_path=str(dotenv_path), override=True)
    return True


def validate_token(token: str) -> Tuple[bool, str]:
    """
    验证 GitHub Token 的有效性

    通过调用 GitHub API 验证 token 是否有效，
    并返回 token 关联的用户信息。

    Args:
        token: GitHub Personal Access Token

    Returns:
        (是否有效, 用户信息或错误消息)

    Raises:
        TokenValidationError: 验证过程中发生网络错误

    Examples:
        >>> valid, info = validate_token("ghp_xxxxxxxx")
        >>> if valid:
        ...     print(f"Token 有效，用户: {info}")
        ... else:
        ...     print(f"验证失败: {info}")
    """
    if not token:
        return False, "Token 不能为空"

    # 基本格式检查
    if not _is_valid_token_format(token):
        return False, "Token 格式不正确"

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(
            f"{GITHUB_API_URL}/user",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            username = data.get("login", "")
            return True, username
        elif response.status_code == 401:
            return False, "Token 无效或已过期"
        elif response.status_code == 403:
            return False, "API 速率限制或 Token 权限不足"
        else:
            return False, f"验证失败: HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        raise TokenValidationError("验证超时，请检查网络连接")
    except requests.exceptions.ConnectionError:
        raise TokenValidationError("网络连接错误，无法连接到 GitHub")
    except requests.exceptions.RequestException as e:
        raise TokenValidationError(f"验证请求失败: {e}")


def _is_valid_token_format(token: str) -> bool:
    """
    检查 Token 格式是否有效

    GitHub 支持多种 token 格式：
    - Classic: ghp_xxxxxxxx (40 位十六进制)
    - Fine-grained: github_pat_xxx
    - OAuth: gho_xxxxxxxx
    - User-to-server: ghu_xxxxxxxx
    - Server-to-server: ghs_xxxxxxxx
    - Refresh: ghr_xxxxxxxx

    Args:
        token: 要检查的 token

    Returns:
        格式是否有效
    """
    if not token or len(token) < 10:
        return False

    # 支持的 token 前缀
    valid_prefixes = (
        "ghp_",  # Personal access token (classic)
        "github_pat_",  # Fine-grained personal access token
        "gho_",  # OAuth access token
        "ghu_",  # User-to-server token
        "ghs_",  # Server-to-server token
        "ghr_",  # Refresh token
    )

    # 检查前缀
    if any(token.startswith(prefix) for prefix in valid_prefixes):
        return True

    # 旧版 token 格式（40 位十六进制）
    if re.match(r"^[a-f0-9]{40}$", token):
        return True

    return False


def authenticate(
    token: Optional[str] = None,
    username: Optional[str] = None,
    store: bool = True,
) -> Tuple[bool, str]:
    """
    使用 GitHub Token 进行认证

    验证 token 的有效性，并可选地将凭证安全存储到系统密钥环。

    Args:
        token: GitHub Personal Access Token，如果为 None 则尝试从环境变量获取
        username: GitHub 用户名，如果为 None 则从 API 响应获取
        store: 是否将凭证存储到系统密钥环

    Returns:
        (是否成功, 消息)

    Raises:
        AuthenticationError: 认证过程中发生错误

    Examples:
        >>> success, msg = authenticate("ghp_xxxxxxxx")
        >>> print(msg)
        认证成功: 用户 @username

        >>> success, msg = authenticate()  # 从环境变量获取
        >>> if not success:
        ...     print("认证失败，请提供 token")
    """
    # 如果未提供 token，尝试从环境变量获取
    if token is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return False, "未提供 token，且未找到 GITHUB_TOKEN 环境变量"

    # 验证 token
    try:
        valid, info = validate_token(token)
        if not valid:
            return False, f"Token 验证失败: {info}"
    except TokenValidationError as e:
        raise AuthenticationError(f"认证失败: {e}")

    # 如果未提供 username，使用 API 返回的用户名
    if username is None:
        username = info

    # 存储凭证
    if store:
        try:
            _store_credentials(username, token)
        except Exception as e:
            return False, f"认证成功，但存储凭证失败: {e}"

    return True, f"认证成功: 用户 @{username}"


def get_stored_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    从系统密钥环获取存储的凭证

    Returns:
        (username, token) 元组，如果未找到则返回 (None, None)

    Examples:
        >>> username, token = get_stored_credentials()
        >>> if token:
        ...     print(f"找到存储的凭证: @{username}")
        ... else:
        ...     print("未找到存储的凭证")
    """
    try:
        username = keyring.get_password(SERVICE_NAME, USERNAME_KEY)
        token = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
        return username, token
    except Exception:
        return None, None


def _store_credentials(username: str, token: str) -> None:
    """
    将凭证存储到系统密钥环

    Args:
        username: GitHub 用户名
        token: GitHub Token

    Raises:
        Exception: 存储失败时抛出
    """
    keyring.set_password(SERVICE_NAME, USERNAME_KEY, username)
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def is_authenticated() -> bool:
    """
    检查用户是否已认证

    检查系统密钥环中是否存在有效的凭证。

    Returns:
        是否已认证

    Examples:
        >>> if is_authenticated():
        ...     print("用户已认证")
        ... else:
        ...     print("请先认证")
    """
    username, token = get_stored_credentials()
    return bool(token)


def logout() -> bool:
    """
    清除存储的凭证（登出）

    从系统密钥环中删除存储的 GitHub 凭证。

    Returns:
        是否成功清除

    Examples:
        >>> if logout():
        ...     print("已成功登出")
        ... else:
        ...     print("登出失败或没有存储的凭证")
    """
    try:
        # 删除存储的凭证
        keyring.delete_password(SERVICE_NAME, USERNAME_KEY)
        keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
        return True
    except keyring.errors.PasswordDeleteError:
        # 凭证不存在
        return True
    except Exception:
        return False


def get_auth_token() -> Optional[str]:
    """
    获取当前有效的认证 token

    按以下优先级获取 token：
    1. 系统密钥环中存储的 token
    2. 环境变量 GITHUB_TOKEN

    Returns:
        有效的 token 或 None

    Examples:
        >>> token = get_auth_token()
        >>> if token:
        ...     headers = {"Authorization": f"Bearer {token}"}
    """
    # 首先尝试从密钥环获取
    _, token = get_stored_credentials()
    if token:
        return token

    # 然后尝试从环境变量获取
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    return None


def get_auth_username() -> Optional[str]:
    """
    获取当前认证的用户名

    按以下优先级获取用户名：
    1. 系统密钥环中存储的用户名
    2. 环境变量 GITHUB_USERNAME

    Returns:
        用户名或 None

    Examples:
        >>> username = get_auth_username()
        >>> print(f"当前用户: @{username}")
    """
    # 首先尝试从密钥环获取
    username, _ = get_stored_credentials()
    if username:
        return username

    # 然后尝试从环境变量获取
    username = os.getenv("GITHUB_USERNAME")
    if username:
        return username

    return None


def ensure_authenticated() -> str:
    """
    确保用户已认证并返回 token

    如果用户未认证，抛出 AuthenticationError。

    Returns:
        有效的 GitHub token

    Raises:
        AuthenticationError: 用户未认证

    Examples:
        >>> try:
        ...     token = ensure_authenticated()
        ...     # 使用 token 进行 API 调用
        ... except AuthenticationError as e:
        ...     print(f"请先认证: {e}")
    """
    token = get_auth_token()
    if not token:
        raise AuthenticationError(
            "未找到有效的 GitHub token。请运行认证命令或设置 GITHUB_TOKEN 环境变量。"
        )
    return token


def get_auth_headers() -> dict:
    """
    获取带有认证信息的 HTTP 请求头

    Returns:
        包含 Authorization 头的字典

    Raises:
        AuthenticationError: 用户未认证

    Examples:
        >>> headers = get_auth_headers()
        >>> response = requests.get(url, headers=headers)
    """
    token = ensure_authenticated()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


class AuthContext:
    """
    认证上下文管理器

    用于在代码块中临时使用特定的认证信息。

    Examples:
        >>> with AuthContext("ghp_xxxx", "username"):
        ...     # 在此代码块中使用指定的认证
        ...     headers = get_auth_headers()
        ...
        >>> # 代码块结束后恢复之前的认证
    """

    def __init__(
        self,
        token: Optional[str] = None,
        username: Optional[str] = None,
        use_env: bool = True,
    ):
        """
        初始化认证上下文

        Args:
            token: GitHub token，如果为 None 则尝试从环境变量获取
            username: GitHub 用户名
            use_env: 是否允许从环境变量获取 token
        """
        self.token = token
        self.username = username
        self.use_env = use_env
        self._original_token = None
        self._original_username = None

    def __enter__(self):
        """进入上下文，设置临时认证信息"""
        # 保存当前的 token
        self._original_token = os.getenv("GITHUB_TOKEN")
        self._original_username = os.getenv("GITHUB_USERNAME")

        # 设置新的 token
        if self.token:
            os.environ["GITHUB_TOKEN"] = self.token
        elif not self.use_env:
            # 如果不使用环境变量，清除环境变量中的 token
            os.environ.pop("GITHUB_TOKEN", None)

        if self.username:
            os.environ["GITHUB_USERNAME"] = self.username

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，恢复原始认证信息"""
        # 恢复原始的 token
        if self._original_token is not None:
            os.environ["GITHUB_TOKEN"] = self._original_token
        else:
            os.environ.pop("GITHUB_TOKEN", None)

        # 恢复原始的用户名
        if self._original_username is not None:
            os.environ["GITHUB_USERNAME"] = self._original_username
        else:
            os.environ.pop("GITHUB_USERNAME", None)

        return False


# 导出公共接口
__all__ = [
    # 主要函数
    "authenticate",
    "get_stored_credentials",
    "validate_token",
    "is_authenticated",
    "logout",
    "load_dotenv",
    # 辅助函数
    "get_auth_token",
    "get_auth_username",
    "ensure_authenticated",
    "get_auth_headers",
    # 类
    "AuthContext",
    # 异常
    "AuthenticationError",
    "TokenValidationError",
    # 常量
    "SERVICE_NAME",
    "GITHUB_API_URL",
]
