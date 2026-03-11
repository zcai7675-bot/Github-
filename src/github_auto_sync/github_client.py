"""
GitHub Auto Sync GitHub API 客户端模块

提供基于 PyGithub 的 GitHub API 客户端封装，支持仓库管理、
用户信息获取等功能，包含完善的错误处理和速率限制感知。
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from github import Github, GithubException, RateLimitExceededException
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.Repository import Repository

from .auth import AuthenticationError, ensure_authenticated, get_auth_token


class GitHubClientError(Exception):
    """GitHub 客户端基础异常"""
    pass


class RepositoryError(GitHubClientError):
    """仓库操作异常"""
    pass


class RepositoryNotFoundError(RepositoryError):
    """仓库不存在异常"""
    pass


class RepositoryAlreadyExistsError(RepositoryError):
    """仓库已存在异常"""
    pass


class RateLimitError(GitHubClientError):
    """API 速率限制异常"""
    pass


class PermissionError(GitHubClientError):
    """权限不足异常"""
    pass


class NetworkError(GitHubClientError):
    """网络连接异常"""
    pass


class GitHubClient:
    """
    GitHub API 客户端封装类

    基于 PyGithub 库提供 GitHub API 的高级封装，支持仓库管理、
    用户信息获取等功能，包含完善的错误处理和速率限制检查。

    Attributes:
        token: GitHub Personal Access Token
        github: PyGithub 客户端实例
        _user: 缓存的认证用户信息

    Examples:
        >>> client = GitHubClient()  # 自动从环境或密钥环获取 token
        >>> client = GitHubClient("ghp_xxxx")  # 使用指定 token
        >>> repos = client.list_repos()
        >>> client.create_repo("my-repo", "描述信息")
    """

    def __init__(self, token: Optional[str] = None):
        """
        初始化 GitHub 客户端

        Args:
            token: GitHub Personal Access Token，如果为 None 则尝试从
                   系统密钥环或环境变量获取

        Raises:
            AuthenticationError: 无法获取有效的 token 时抛出

        Examples:
            >>> client = GitHubClient()  # 使用存储的凭证
            >>> client = GitHubClient("ghp_xxxx")  # 使用指定 token
        """
        if token is None:
            token = get_auth_token()
            if not token:
                raise AuthenticationError(
                    "未提供 GitHub token，且未找到存储的凭证或 GITHUB_TOKEN 环境变量。"
                    "请使用 GitHubClient(token) 提供 token，或先运行认证流程。"
                )

        self.token = token
        self.github = Github(token)
        self._user: Optional[AuthenticatedUser] = None
        self._rate_limit_info: Optional[Dict[str, Any]] = None

    def _handle_github_exception(self, e: GithubException, context: str = "") -> None:
        """
        处理 GitHub API 异常

        将 PyGithub 异常转换为自定义异常类型。

        Args:
            e: PyGithub 异常
            context: 异常上下文信息

        Raises:
            RateLimitError: API 速率限制
            PermissionError: 权限不足
            RepositoryNotFoundError: 仓库不存在
            RepositoryAlreadyExistsError: 仓库已存在
            RepositoryError: 其他仓库错误
            GitHubClientError: 其他 GitHub 错误
        """
        status = e.status if hasattr(e, 'status') else 0
        data = e.data if hasattr(e, 'data') else {}
        message = data.get('message', str(e)) if isinstance(data, dict) else str(e)

        error_msg = f"{context}: {message}" if context else message

        # 速率限制 (403 with rate limit message or 429)
        if status == 403 and 'rate limit' in message.lower():
            reset_time = data.get('rate', {}).get('reset', 0) if isinstance(data, dict) else 0
            raise RateLimitError(
                f"API 速率限制已达上限。{error_msg} "
                f"重置时间: {time.ctime(reset_time) if reset_time else '未知'}"
            )
        elif status == 429:
            raise RateLimitError(f"API 速率限制: {error_msg}")

        # 权限错误 (401, 403)
        elif status == 401:
            raise PermissionError(f"认证失败，请检查 token 是否有效: {error_msg}")
        elif status == 403:
            raise PermissionError(f"权限不足: {error_msg}")

        # 未找到 (404)
        elif status == 404:
            raise RepositoryNotFoundError(f"资源不存在: {error_msg}")

        # 冲突 (422) - 通常表示仓库已存在
        elif status == 422:
            if 'already exists' in message.lower():
                raise RepositoryAlreadyExistsError(f"仓库已存在: {error_msg}")
            raise RepositoryError(f"请求无效: {error_msg}")

        # 其他错误
        else:
            raise GitHubClientError(f"GitHub API 错误 (HTTP {status}): {error_msg}")

    def _get_user(self) -> AuthenticatedUser:
        """
        获取认证用户信息（带缓存）

        Returns:
            AuthenticatedUser 对象

        Raises:
            GitHubClientError: 获取用户信息失败
        """
        if self._user is None:
            try:
                self._user = self.github.get_user()
            except GithubException as e:
                self._handle_github_exception(e, "获取用户信息失败")
        return self._user

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        获取 API 速率限制信息

        Returns:
            包含速率限制信息的字典:
            - limit: 总限制次数
            - remaining: 剩余次数
            - reset: 重置时间戳
            - used: 已使用次数

        Examples:
            >>> client = GitHubClient()
            >>> rate = client.get_rate_limit()
            >>> print(f"剩余: {rate['remaining']}/{rate['limit']}")
        """
        try:
            rate_limit = self.github.get_rate_limit()
            core = rate_limit.core

            self._rate_limit_info = {
                "limit": core.limit,
                "remaining": core.remaining,
                "reset": core.reset.timestamp(),
                "used": core.used,
                "reset_datetime": core.reset,
            }
            return self._rate_limit_info
        except GithubException as e:
            self._handle_github_exception(e, "获取速率限制信息失败")
            return {}

    def check_rate_limit(self, min_remaining: int = 10) -> bool:
        """
        检查 API 速率限制是否充足

        Args:
            min_remaining: 最小剩余次数阈值

        Returns:
            如果剩余次数大于阈值则返回 True

        Raises:
            RateLimitError: 剩余次数不足时抛出

        Examples:
            >>> client = GitHubClient()
            >>> if client.check_rate_limit(5):
            ...     # 执行 API 调用
            ...     pass
        """
        rate_info = self.get_rate_limit()
        remaining = rate_info.get("remaining", 0)

        if remaining < min_remaining:
            reset_time = rate_info.get("reset", 0)
            raise RateLimitError(
                f"API 剩余次数不足: {remaining} < {min_remaining}. "
                f"重置时间: {time.ctime(reset_time) if reset_time else '未知'}"
            )

        return True

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取认证用户详细信息

        Returns:
            包含用户信息的字典:
            - login: 用户名
            - id: 用户 ID
            - name: 显示名称
            - email: 邮箱
            - avatar_url: 头像 URL
            - html_url: GitHub 主页
            - public_repos: 公开仓库数
            - private_repos: 私有仓库数
            - total_repos: 总仓库数

        Examples:
            >>> client = GitHubClient()
            >>> info = client.get_user_info()
            >>> print(f"用户: @{info['login']}, 仓库数: {info['total_repos']}")
        """
        try:
            user = self._get_user()

            return {
                "login": user.login,
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "html_url": user.html_url,
                "bio": user.bio,
                "location": user.location,
                "company": user.company,
                "blog": user.blog,
                "public_repos": user.public_repos,
                "private_repos": user.total_private_repos or 0,
                "total_repos": (user.public_repos or 0) + (user.total_private_repos or 0),
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "type": user.type,
            }
        except GithubException as e:
            self._handle_github_exception(e, "获取用户信息失败")
            return {}

    def list_repos(
        self,
        type_filter: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        visibility: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出用户的所有仓库

        Args:
            type_filter: 仓库类型筛选 (all, owner, member)
            sort: 排序字段 (created, updated, pushed, full_name)
            direction: 排序方向 (asc, desc)
            visibility: 可见性筛选 (all, public, private)，None 表示不过滤

        Returns:
            仓库信息字典列表，每个字典包含:
            - name: 仓库名称
            - full_name: 完整名称 (用户名/仓库名)
            - description: 描述
            - private: 是否私有
            - html_url: GitHub 页面 URL
            - clone_url: Git 克隆 URL
            - ssh_url: SSH 克隆 URL
            - created_at: 创建时间
            - updated_at: 更新时间
            - pushed_at: 最后推送时间
            - stargazers_count: Star 数
            - forks_count: Fork 数
            - language: 主要语言
            - default_branch: 默认分支

        Examples:
            >>> client = GitHubClient()
            >>> repos = client.list_repos()
            >>> for repo in repos:
            ...     print(f"{repo['full_name']}: {repo['description']}")
        """
        try:
            user = self._get_user()

            # 构建参数
            kwargs = {
                "type": type_filter,
                "sort": sort,
                "direction": direction,
            }
            if visibility:
                kwargs["visibility"] = visibility

            repos = user.get_repos(**kwargs)

            result = []
            for repo in repos:
                result.append(self._repo_to_dict(repo))

            return result

        except GithubException as e:
            self._handle_github_exception(e, "列出仓库失败")
            return []

    def _repo_to_dict(self, repo: Repository) -> Dict[str, Any]:
        """
        将 Repository 对象转换为字典

        Args:
            repo: Repository 对象

        Returns:
            仓库信息字典
        """
        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "private": repo.private,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "stargazers_count": repo.stargazers_count,
            "watchers_count": repo.watchers_count,
            "forks_count": repo.forks_count,
            "open_issues_count": repo.open_issues_count,
            "language": repo.language,
            "default_branch": repo.default_branch,
            "size": repo.size,
            "archived": repo.archived,
            "disabled": repo.disabled,
            "topics": repo.topics or [],
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_pages": repo.has_pages,
            "has_downloads": repo.has_downloads,
            "license": repo.license.name if repo.license else None,
        }

    def get_repo(self, name: str, owner: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定仓库的详细信息

        Args:
            name: 仓库名称（可以是 'owner/repo' 格式或仅仓库名）
            owner: 仓库所有者，如果 name 不包含 '/' 则必须提供

        Returns:
            仓库信息字典（格式同 list_repos）

        Raises:
            RepositoryNotFoundError: 仓库不存在
            GitHubClientError: 其他错误

        Examples:
            >>> client = GitHubClient()
            >>> # 使用完整名称
            >>> repo = client.get_repo("username/repo-name")
            >>> # 或分开指定
            >>> repo = client.get_repo("repo-name", "username")
        """
        try:
            # 解析仓库名称
            if "/" in name:
                full_name = name
            elif owner:
                full_name = f"{owner}/{name}"
            else:
                # 使用当前用户作为所有者
                user = self._get_user()
                full_name = f"{user.login}/{name}"

            repo = self.github.get_repo(full_name)
            return self._repo_to_dict(repo)

        except GithubException as e:
            self._handle_github_exception(e, f"获取仓库 '{name}' 失败")
            return {}

    def repo_exists(self, name: str, owner: Optional[str] = None) -> bool:
        """
        检查仓库是否存在

        Args:
            name: 仓库名称（可以是 'owner/repo' 格式或仅仓库名）
            owner: 仓库所有者，如果 name 不包含 '/' 则必须提供

        Returns:
            仓库存在返回 True，否则返回 False

        Examples:
            >>> client = GitHubClient()
            >>> if client.repo_exists("my-repo"):
            ...     print("仓库已存在")
            ... else:
            ...     print("仓库不存在")
        """
        try:
            self.get_repo(name, owner)
            return True
        except RepositoryNotFoundError:
            return False
        except GitHubClientError:
            return False

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = False,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
        allow_rebase_merge: bool = True,
        allow_squash_merge: bool = True,
        allow_merge_commit: bool = True,
        delete_branch_on_merge: bool = False,
        homepage: Optional[str] = None,
        has_issues: bool = True,
        has_wiki: bool = True,
        has_projects: bool = True,
    ) -> Dict[str, Any]:
        """
        创建新仓库

        Args:
            name: 仓库名称（必填）
            description: 仓库描述
            private: 是否私有仓库（默认 True）
            auto_init: 是否自动初始化 README
            gitignore_template: Gitignore 模板名称（如 'Python', 'Node'）
            license_template: 许可证模板（如 'mit', 'apache-2.0'）
            allow_rebase_merge: 是否允许 rebase 合并
            allow_squash_merge: 是否允许 squash 合并
            allow_merge_commit: 是否允许普通合并
            delete_branch_on_merge: 合并后是否删除分支
            homepage: 项目主页 URL
            has_issues: 是否启用 Issues
            has_wiki: 是否启用 Wiki
            has_projects: 是否启用 Projects

        Returns:
            创建的仓库信息字典

        Raises:
            RepositoryAlreadyExistsError: 仓库已存在
            PermissionError: 权限不足
            GitHubClientError: 其他错误

        Examples:
            >>> client = GitHubClient()
            >>> repo = client.create_repo(
            ...     "my-new-repo",
            ...     description="我的新项目",
            ...     private=True,
            ...     auto_init=True,
            ...     gitignore_template="Python"
            ... )
            >>> print(f"创建成功: {repo['html_url']}")
        """
        try:
            user = self._get_user()

            # 检查速率限制
            self.check_rate_limit(5)

            # 构建参数
            kwargs = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": auto_init,
                "allow_rebase_merge": allow_rebase_merge,
                "allow_squash_merge": allow_squash_merge,
                "allow_merge_commit": allow_merge_commit,
                "delete_branch_on_merge": delete_branch_on_merge,
                "has_issues": has_issues,
                "has_wiki": has_wiki,
                "has_projects": has_projects,
            }

            # 可选参数
            if gitignore_template:
                kwargs["gitignore_template"] = gitignore_template
            if license_template:
                kwargs["license_template"] = license_template
            if homepage:
                kwargs["homepage"] = homepage

            repo = user.create_repo(**kwargs)
            return self._repo_to_dict(repo)

        except GithubException as e:
            self._handle_github_exception(e, f"创建仓库 '{name}' 失败")
            return {}

    def delete_repo(self, name: str, owner: Optional[str] = None) -> bool:
        """
        删除仓库

        警告：此操作不可恢复！

        Args:
            name: 仓库名称（可以是 'owner/repo' 格式或仅仓库名）
            owner: 仓库所有者，如果 name 不包含 '/' 则必须提供

        Returns:
            删除成功返回 True

        Raises:
            RepositoryNotFoundError: 仓库不存在
            PermissionError: 权限不足（非仓库所有者）
            GitHubClientError: 其他错误

        Examples:
            >>> client = GitHubClient()
            >>> if client.delete_repo("old-repo"):
            ...     print("仓库已删除")
        """
        try:
            # 解析仓库名称
            if "/" in name:
                full_name = name
            elif owner:
                full_name = f"{owner}/{name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{name}"

            repo = self.github.get_repo(full_name)
            repo.delete()
            return True

        except GithubException as e:
            self._handle_github_exception(e, f"删除仓库 '{name}' 失败")
            return False

    def update_repo(
        self,
        name: str,
        owner: Optional[str] = None,
        description: Optional[str] = None,
        private: Optional[bool] = None,
        homepage: Optional[str] = None,
        has_issues: Optional[bool] = None,
        has_wiki: Optional[bool] = None,
        has_projects: Optional[bool] = None,
        default_branch: Optional[str] = None,
        allow_rebase_merge: Optional[bool] = None,
        allow_squash_merge: Optional[bool] = None,
        allow_merge_commit: Optional[bool] = None,
        delete_branch_on_merge: Optional[bool] = None,
        archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        更新仓库设置

        Args:
            name: 仓库名称（可以是 'owner/repo' 格式或仅仓库名）
            owner: 仓库所有者，如果 name 不包含 '/' 则必须提供
            description: 新的描述
            private: 是否私有
            homepage: 项目主页
            has_issues: 是否启用 Issues
            has_wiki: 是否启用 Wiki
            has_projects: 是否启用 Projects
            default_branch: 默认分支名称
            allow_rebase_merge: 是否允许 rebase 合并
            allow_squash_merge: 是否允许 squash 合并
            allow_merge_commit: 是否允许普通合并
            delete_branch_on_merge: 合并后是否删除分支
            archived: 是否归档仓库

        Returns:
            更新后的仓库信息字典

        Raises:
            RepositoryNotFoundError: 仓库不存在
            PermissionError: 权限不足
            GitHubClientError: 其他错误

        Examples:
            >>> client = GitHubClient()
            >>> repo = client.update_repo(
            ...     "my-repo",
            ...     description="更新后的描述",
            ...     has_wiki=False
            ... )
        """
        try:
            # 解析仓库名称
            if "/" in name:
                full_name = name
            elif owner:
                full_name = f"{owner}/{name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{name}"

            repo = self.github.get_repo(full_name)

            # 构建更新参数
            kwargs = {}
            if description is not None:
                kwargs["description"] = description
            if private is not None:
                kwargs["private"] = private
            if homepage is not None:
                kwargs["homepage"] = homepage
            if has_issues is not None:
                kwargs["has_issues"] = has_issues
            if has_wiki is not None:
                kwargs["has_wiki"] = has_wiki
            if has_projects is not None:
                kwargs["has_projects"] = has_projects
            if default_branch is not None:
                kwargs["default_branch"] = default_branch
            if allow_rebase_merge is not None:
                kwargs["allow_rebase_merge"] = allow_rebase_merge
            if allow_squash_merge is not None:
                kwargs["allow_squash_merge"] = allow_squash_merge
            if allow_merge_commit is not None:
                kwargs["allow_merge_commit"] = allow_merge_commit
            if delete_branch_on_merge is not None:
                kwargs["delete_branch_on_merge"] = delete_branch_on_merge
            if archived is not None:
                kwargs["archived"] = archived

            if kwargs:
                repo.edit(**kwargs)

            return self._repo_to_dict(repo)

        except GithubException as e:
            self._handle_github_exception(e, f"更新仓库 '{name}' 失败")
            return {}

    def get_repo_languages(self, name: str, owner: Optional[str] = None) -> Dict[str, int]:
        """
        获取仓库使用的编程语言统计

        Args:
            name: 仓库名称（可以是 'owner/repo' 格式或仅仓库名）
            owner: 仓库所有者，如果 name 不包含 '/' 则必须提供

        Returns:
            语言名称到代码字节数的映射字典

        Examples:
            >>> client = GitHubClient()
            >>> langs = client.get_repo_languages("my-repo")
            >>> for lang, bytes_count in langs.items():
            ...     print(f"{lang}: {bytes_count} bytes")
        """
        try:
            # 解析仓库名称
            if "/" in name:
                full_name = name
            elif owner:
                full_name = f"{owner}/{name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{name}"

            repo = self.github.get_repo(full_name)
            return dict(repo.get_languages())

        except GithubException as e:
            self._handle_github_exception(e, f"获取仓库 '{name}' 语言统计失败")
            return {}

    def search_repos(
        self,
        query: str,
        sort: str = "updated",
        order: str = "desc",
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        搜索仓库

        Args:
            query: 搜索查询字符串
            sort: 排序字段 (stars, forks, updated)
            order: 排序方向 (asc, desc)
            limit: 返回结果数量限制

        Returns:
            仓库信息字典列表

        Examples:
            >>> client = GitHubClient()
            >>> repos = client.search_repos("machine learning language:python")
            >>> for repo in repos:
            ...     print(f"{repo['full_name']}: {repo['stargazers_count']} stars")
        """
        try:
            results = self.github.search_repositories(query, sort=sort, order=order)

            repos = []
            for i, repo in enumerate(results):
                if i >= limit:
                    break
                repos.append(self._repo_to_dict(repo))

            return repos

        except GithubException as e:
            self._handle_github_exception(e, "搜索仓库失败")
            return []

    def create_release(
        self,
        repo_name: str,
        tag_name: str,
        name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False,
        target_commitish: str = "main",
        owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建 GitHub Release

        Args:
            repo_name: 仓库名称
            tag_name: 标签名称（例如：v1.0.0）
            name: Release 标题
            body: Release 描述（支持 Markdown）
            draft: 是否为草稿
            prerelease: 是否为预发布版本
            target_commitish: 目标分支或提交 SHA
            owner: 仓库所有者，默认为当前用户

        Returns:
            Release 信息字典

        Raises:
            RepositoryNotFoundError: 仓库不存在
            PermissionError: 权限不足

        Examples:
            >>> client = GitHubClient()
            >>> release = client.create_release(
            ...     "my-project",
            ...     "v1.0.0",
            ...     "版本 1.0.0",
            ...     "## 更新内容\\n- 新功能 A\\n- 修复 Bug B"
            ... )
            >>> print(f"Release URL: {release['html_url']}")
        """
        try:
            # 解析仓库名称
            if "/" in repo_name:
                full_name = repo_name
            elif owner:
                full_name = f"{owner}/{repo_name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{repo_name}"

            repo = self.github.get_repo(full_name)

            # 创建 Release
            release = repo.create_git_release(
                tag=tag_name,
                name=name,
                message=body,
                draft=draft,
                prerelease=prerelease,
                target_commitish=target_commitish,
            )

            logger.info(f"Release 创建成功: {release.html_url}")
            return self._release_to_dict(release)

        except GithubException as e:
            self._handle_github_exception(e, f"创建 Release '{tag_name}' 失败")
            return {}

    def upload_release_asset(
        self,
        repo_name: str,
        release_id: int,
        file_path: str,
        label: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        上传文件到 Release

        Args:
            repo_name: 仓库名称
            release_id: Release ID
            file_path: 文件路径
            label: 文件标签（可选）
            owner: 仓库所有者，默认为当前用户

        Returns:
            上传的资源信息字典

        Examples:
            >>> client = GitHubClient()
            >>> asset = client.upload_release_asset(
            ...     "my-project",
            ...     123456,
            ...     "./dist/app.zip",
            ...     "应用程序压缩包"
            ... )
        """
        try:
            # 解析仓库名称
            if "/" in repo_name:
                full_name = repo_name
            elif owner:
                full_name = f"{owner}/{repo_name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{repo_name}"

            repo = self.github.get_repo(full_name)
            release = repo.get_release(release_id)

            # 上传文件
            asset = release.upload_asset(
                path=file_path,
                label=label,
            )

            logger.info(f"文件上传成功: {asset.browser_download_url}")
            return self._asset_to_dict(asset)

        except GithubException as e:
            self._handle_github_exception(e, f"上传文件到 Release 失败")
            return {}

    def list_releases(
        self,
        repo_name: str,
        owner: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        列出仓库的所有 Release

        Args:
            repo_name: 仓库名称
            owner: 仓库所有者，默认为当前用户
            limit: 返回结果数量限制

        Returns:
            Release 信息字典列表

        Examples:
            >>> client = GitHubClient()
            >>> releases = client.list_releases("my-project")
            >>> for release in releases:
            ...     print(f"{release['tag_name']}: {release['name']}")
        """
        try:
            # 解析仓库名称
            if "/" in repo_name:
                full_name = repo_name
            elif owner:
                full_name = f"{owner}/{repo_name}"
            else:
                user = self._get_user()
                full_name = f"{user.login}/{repo_name}"

            repo = self.github.get_repo(full_name)
            releases = repo.get_releases()

            result = []
            for i, release in enumerate(releases):
                if i >= limit:
                    break
                result.append(self._release_to_dict(release))

            return result

        except GithubException as e:
            self._handle_github_exception(e, f"获取 Release 列表失败")
            return []

    def _release_to_dict(self, release) -> Dict[str, Any]:
        """将 Release 对象转换为字典"""
        return {
            "id": release.id,
            "tag_name": release.tag_name,
            "name": release.title,
            "body": release.body,
            "draft": release.draft,
            "prerelease": release.prerelease,
            "html_url": release.html_url,
            "upload_url": release.upload_url,
            "created_at": release.created_at.isoformat() if release.created_at else None,
            "published_at": release.published_at.isoformat() if release.published_at else None,
            "assets": [self._asset_to_dict(asset) for asset in release.get_assets()],
        }

    def _asset_to_dict(self, asset) -> Dict[str, Any]:
        """将 Release Asset 对象转换为字典"""
        return {
            "id": asset.id,
            "name": asset.name,
            "size": asset.size,
            "download_count": asset.download_count,
            "browser_download_url": asset.browser_download_url,
            "label": asset.label,
            "content_type": asset.content_type,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # 关闭底层连接
        if self.github:
            self.github.close()
        return False


# 便捷函数
def create_client(token: Optional[str] = None) -> GitHubClient:
    """
    创建 GitHub 客户端实例的便捷函数

    Args:
        token: GitHub Personal Access Token

    Returns:
        GitHubClient 实例

    Examples:
        >>> client = create_client()
        >>> repos = client.list_repos()
    """
    return GitHubClient(token)


def get_client() -> GitHubClient:
    """
    获取默认 GitHub 客户端实例（使用存储的凭证）

    Returns:
        GitHubClient 实例

    Raises:
        AuthenticationError: 未找到有效凭证

    Examples:
        >>> client = get_client()
        >>> info = client.get_user_info()
    """
    return GitHubClient()


# 导出公共接口
__all__ = [
    # 主要类
    "GitHubClient",
    # 异常类
    "GitHubClientError",
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RateLimitError",
    "PermissionError",
    "NetworkError",
    # 便捷函数
    "create_client",
    "get_client",
]
