"""
GitHub 客户端单元测试

测试 github_client 模块的 API 客户端功能。
"""

from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from github import GithubException

from github_auto_sync.github_client import (
    GitHubClient,
    GitHubClientError,
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RateLimitError,
    PermissionError,
    create_client,
    get_client,
)
from github_auto_sync.auth import AuthenticationError


# =============================================================================
# 客户端初始化测试
# =============================================================================


class TestGitHubClientInitialization:
    """GitHubClient 初始化测试"""
    
    def test_init_with_token(self, mock_github):
        """测试使用 token 初始化"""
        client = GitHubClient("ghp_test_token")
        
        assert client.token == "ghp_test_token"
        mock_github.assert_called_once_with("ghp_test_token")
    
    def test_init_without_token_uses_stored(self, mock_github):
        """测试无 token 时使用存储的凭证"""
        with patch("github_auto_sync.github_client.get_auth_token") as mock_get_token:
            mock_get_token.return_value = "stored-token"
            
            client = GitHubClient()
            
            assert client.token == "stored-token"
    
    def test_init_without_token_raises_error(self, mock_github):
        """测试无 token 可用时抛出错误"""
        with patch("github_auto_sync.github_client.get_auth_token") as mock_get_token:
            mock_get_token.return_value = None
            
            with pytest.raises(AuthenticationError):
                GitHubClient()


# =============================================================================
# 速率限制测试
# =============================================================================


class TestRateLimit:
    """速率限制测试"""
    
    def test_get_rate_limit(self, mock_github):
        """测试获取速率限制"""
        client = GitHubClient("test-token")
        
        rate_info = client.get_rate_limit()
        
        assert "limit" in rate_info
        assert "remaining" in rate_info
        assert "reset" in rate_info
        assert "used" in rate_info
    
    def test_check_rate_limit_sufficient(self, mock_github):
        """测试检查速率限制充足"""
        client = GitHubClient("test-token")
        
        result = client.check_rate_limit(min_remaining=10)
        
        assert result is True
    
    def test_check_rate_limit_insufficient(self, mock_github):
        """测试检查速率限制不足"""
        mock_github.return_value.get_rate_limit.return_value = MagicMock(
            core=MagicMock(limit=5000, remaining=5, used=4995)
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(RateLimitError):
            client.check_rate_limit(min_remaining=10)


# =============================================================================
# 用户信息测试
# =============================================================================


class TestUserInfo:
    """用户信息测试"""
    
    def test_get_user_info(self, mock_github):
        """测试获取用户信息"""
        client = GitHubClient("test-token")
        
        info = client.get_user_info()
        
        assert info["login"] == "testuser"
        assert info["id"] == 123456
        assert info["name"] == "Test User"
        assert info["public_repos"] == 10
        assert info["total_repos"] == 15
    
    def test_get_user_info_error(self, mock_github):
        """测试获取用户信息错误"""
        mock_github.return_value.get_user.side_effect = GithubException(
            status=401, data={"message": "Bad credentials"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(PermissionError):
            client.get_user_info()


# =============================================================================
# 仓库列表测试
# =============================================================================


class TestListRepos:
    """仓库列表测试"""
    
    def test_list_repos(self, mock_github):
        """测试列出仓库"""
        # 模拟仓库列表
        mock_repo1 = MagicMock()
        mock_repo1.name = "repo1"
        mock_repo1.full_name = "testuser/repo1"
        mock_repo1.description = "Test repo 1"
        mock_repo1.private = True
        mock_repo1.html_url = "https://github.com/testuser/repo1"
        mock_repo1.clone_url = "https://github.com/testuser/repo1.git"
        mock_repo1.ssh_url = "git@github.com:testuser/repo1.git"
        mock_repo1.created_at = datetime.now()
        mock_repo1.updated_at = datetime.now()
        mock_repo1.pushed_at = datetime.now()
        mock_repo1.stargazers_count = 10
        mock_repo1.watchers_count = 10
        mock_repo1.forks_count = 5
        mock_repo1.open_issues_count = 2
        mock_repo1.language = "Python"
        mock_repo1.default_branch = "main"
        mock_repo1.size = 1024
        mock_repo1.archived = False
        mock_repo1.disabled = False
        mock_repo1.topics = ["python", "testing"]
        mock_repo1.has_issues = True
        mock_repo1.has_wiki = True
        mock_repo1.has_pages = False
        mock_repo1.has_downloads = True
        mock_repo1.license = MagicMock(name="MIT")
        
        mock_user = mock_github.return_value.get_user.return_value
        mock_user.get_repos.return_value = [mock_repo1]
        
        client = GitHubClient("test-token")
        repos = client.list_repos()
        
        assert len(repos) == 1
        assert repos[0]["name"] == "repo1"
        assert repos[0]["full_name"] == "testuser/repo1"
    
    def test_list_repos_with_filters(self, mock_github):
        """测试列出仓库带过滤"""
        mock_user = mock_github.return_value.get_user.return_value
        mock_user.get_repos.return_value = []
        
        client = GitHubClient("test-token")
        repos = client.list_repos(
            type_filter="owner",
            sort="created",
            direction="asc",
            visibility="public"
        )
        
        mock_user.get_repos.assert_called_with(
            type="owner",
            sort="created",
            direction="asc",
            visibility="public"
        )


# =============================================================================
# 仓库操作测试
# =============================================================================


class TestGetRepo:
    """获取仓库测试"""
    
    def test_get_repo_with_full_name(self, mock_github):
        """测试使用完整名称获取仓库"""
        mock_repo = MagicMock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_repo.description = "Test repository"
        mock_repo.private = True
        mock_repo.html_url = "https://github.com/owner/test-repo"
        mock_repo.clone_url = "https://github.com/owner/test-repo.git"
        mock_repo.created_at = datetime.now()
        mock_repo.updated_at = datetime.now()
        mock_repo.pushed_at = datetime.now()
        mock_repo.stargazers_count = 10
        mock_repo.watchers_count = 10
        mock_repo.forks_count = 5
        mock_repo.open_issues_count = 2
        mock_repo.language = "Python"
        mock_repo.default_branch = "main"
        mock_repo.size = 1024
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = []
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        repo = client.get_repo("owner/test-repo")
        
        assert repo["name"] == "test-repo"
        assert repo["full_name"] == "owner/test-repo"
    
    def test_get_repo_with_owner(self, mock_github):
        """测试使用所有者参数获取仓库"""
        mock_repo = MagicMock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "owner/test-repo"
        mock_repo.description = None
        mock_repo.private = False
        mock_repo.html_url = "https://github.com/owner/test-repo"
        mock_repo.clone_url = "https://github.com/owner/test-repo.git"
        mock_repo.ssh_url = "git@github.com:owner/test-repo.git"
        mock_repo.created_at = None
        mock_repo.updated_at = None
        mock_repo.pushed_at = None
        mock_repo.stargazers_count = 0
        mock_repo.watchers_count = 0
        mock_repo.forks_count = 0
        mock_repo.open_issues_count = 0
        mock_repo.language = None
        mock_repo.default_branch = "main"
        mock_repo.size = 0
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        repo = client.get_repo("test-repo", owner="owner")
        
        mock_github.return_value.get_repo.assert_called_with("owner/test-repo")
        assert repo["name"] == "test-repo"
    
    def test_get_repo_not_found(self, mock_github):
        """测试获取不存在的仓库"""
        mock_github.return_value.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(RepositoryNotFoundError):
            client.get_repo("nonexistent/repo")


class TestRepoExists:
    """检查仓库存在测试"""
    
    def test_repo_exists_true(self, mock_github):
        """测试仓库存在"""
        mock_repo = MagicMock()
        mock_repo.name = "existing-repo"
        mock_repo.full_name = "testuser/existing-repo"
        mock_repo.description = None
        mock_repo.private = False
        mock_repo.html_url = ""
        mock_repo.clone_url = ""
        mock_repo.ssh_url = ""
        mock_repo.created_at = None
        mock_repo.updated_at = None
        mock_repo.pushed_at = None
        mock_repo.stargazers_count = 0
        mock_repo.watchers_count = 0
        mock_repo.forks_count = 0
        mock_repo.open_issues_count = 0
        mock_repo.language = None
        mock_repo.default_branch = "main"
        mock_repo.size = 0
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        
        assert client.repo_exists("existing-repo") is True
    
    def test_repo_exists_false(self, mock_github):
        """测试仓库不存在"""
        mock_github.return_value.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )
        
        client = GitHubClient("test-token")
        
        assert client.repo_exists("nonexistent-repo") is False


class TestCreateRepo:
    """创建仓库测试"""
    
    def test_create_repo_success(self, mock_github):
        """测试成功创建仓库"""
        mock_repo = MagicMock()
        mock_repo.name = "new-repo"
        mock_repo.full_name = "testuser/new-repo"
        mock_repo.description = "New repository"
        mock_repo.private = True
        mock_repo.html_url = "https://github.com/testuser/new-repo"
        mock_repo.clone_url = "https://github.com/testuser/new-repo.git"
        mock_repo.ssh_url = "git@github.com:testuser/new-repo.git"
        mock_repo.created_at = datetime.now()
        mock_repo.updated_at = datetime.now()
        mock_repo.pushed_at = datetime.now()
        mock_repo.stargazers_count = 0
        mock_repo.watchers_count = 0
        mock_repo.forks_count = 0
        mock_repo.open_issues_count = 0
        mock_repo.language = None
        mock_repo.default_branch = "main"
        mock_repo.size = 0
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_user = mock_github.return_value.get_user.return_value
        mock_user.create_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        repo = client.create_repo("new-repo", description="New repository")
        
        assert repo["name"] == "new-repo"
        mock_user.create_repo.assert_called_once()
    
    def test_create_repo_already_exists(self, mock_github):
        """测试创建已存在的仓库"""
        mock_user = mock_github.return_value.get_user.return_value
        mock_user.create_repo.side_effect = GithubException(
            status=422, data={"message": "Repository already exists"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(RepositoryAlreadyExistsError):
            client.create_repo("existing-repo")
    
    def test_create_repo_with_options(self, mock_github):
        """测试创建仓库带选项"""
        mock_repo = MagicMock()
        mock_repo.name = "new-repo"
        mock_repo.full_name = "testuser/new-repo"
        mock_repo.description = "Test"
        mock_repo.private = False
        mock_repo.html_url = ""
        mock_repo.clone_url = ""
        mock_repo.ssh_url = ""
        mock_repo.created_at = None
        mock_repo.updated_at = None
        mock_repo.pushed_at = None
        mock_repo.stargazers_count = 0
        mock_repo.watchers_count = 0
        mock_repo.forks_count = 0
        mock_repo.open_issues_count = 0
        mock_repo.language = None
        mock_repo.default_branch = "main"
        mock_repo.size = 0
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_user = mock_github.return_value.get_user.return_value
        mock_user.create_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        client.create_repo(
            name="new-repo",
            description="Test repo",
            private=False,
            auto_init=True,
            gitignore_template="Python",
            license_template="mit",
        )
        
        call_kwargs = mock_user.create_repo.call_args.kwargs
        assert call_kwargs["name"] == "new-repo"
        assert call_kwargs["private"] is False
        assert call_kwargs["auto_init"] is True


class TestDeleteRepo:
    """删除仓库测试"""
    
    def test_delete_repo_success(self, mock_github):
        """测试成功删除仓库"""
        mock_repo = MagicMock()
        mock_repo.delete = MagicMock()
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        result = client.delete_repo("test-repo")
        
        assert result is True
        mock_repo.delete.assert_called_once()
    
    def test_delete_repo_not_found(self, mock_github):
        """测试删除不存在的仓库"""
        mock_github.return_value.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(RepositoryNotFoundError):
            client.delete_repo("nonexistent-repo")
    
    def test_delete_repo_permission_denied(self, mock_github):
        """测试删除仓库权限不足"""
        mock_github.return_value.get_repo.side_effect = GithubException(
            status=403, data={"message": "Forbidden"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(PermissionError):
            client.delete_repo("protected-repo")


class TestUpdateRepo:
    """更新仓库测试"""
    
    def test_update_repo_success(self, mock_github):
        """测试成功更新仓库"""
        mock_repo = MagicMock()
        mock_repo.edit = MagicMock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "testuser/test-repo"
        mock_repo.description = "Updated description"
        mock_repo.private = False
        mock_repo.html_url = ""
        mock_repo.clone_url = ""
        mock_repo.ssh_url = ""
        mock_repo.created_at = None
        mock_repo.updated_at = None
        mock_repo.pushed_at = None
        mock_repo.stargazers_count = 0
        mock_repo.watchers_count = 0
        mock_repo.forks_count = 0
        mock_repo.open_issues_count = 0
        mock_repo.language = None
        mock_repo.default_branch = "main"
        mock_repo.size = 0
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        repo = client.update_repo(
            "test-repo",
            description="Updated description",
            private=False,
            has_wiki=False,
        )
        
        mock_repo.edit.assert_called_once()
        assert repo["name"] == "test-repo"


# =============================================================================
# 语言统计测试
# =============================================================================


class TestGetRepoLanguages:
    """获取仓库语言测试"""
    
    def test_get_repo_languages(self, mock_github):
        """测试获取仓库语言统计"""
        mock_repo = MagicMock()
        mock_repo.get_languages.return_value = {"Python": 5000, "JavaScript": 2000}
        
        mock_github.return_value.get_repo.return_value = mock_repo
        
        client = GitHubClient("test-token")
        languages = client.get_repo_languages("test-repo")
        
        assert languages == {"Python": 5000, "JavaScript": 2000}


# =============================================================================
# 搜索测试
# =============================================================================


class TestSearchRepos:
    """搜索仓库测试"""
    
    def test_search_repos(self, mock_github):
        """测试搜索仓库"""
        mock_repo = MagicMock()
        mock_repo.name = "awesome-project"
        mock_repo.full_name = "user/awesome-project"
        mock_repo.description = "An awesome project"
        mock_repo.private = False
        mock_repo.html_url = "https://github.com/user/awesome-project"
        mock_repo.clone_url = "https://github.com/user/awesome-project.git"
        mock_repo.ssh_url = "git@github.com:user/awesome-project.git"
        mock_repo.created_at = None
        mock_repo.updated_at = None
        mock_repo.pushed_at = None
        mock_repo.stargazers_count = 100
        mock_repo.watchers_count = 100
        mock_repo.forks_count = 50
        mock_repo.open_issues_count = 10
        mock_repo.language = "Python"
        mock_repo.default_branch = "main"
        mock_repo.size = 1024
        mock_repo.archived = False
        mock_repo.disabled = False
        mock_repo.topics = None
        mock_repo.has_issues = True
        mock_repo.has_wiki = True
        mock_repo.has_pages = False
        mock_repo.has_downloads = True
        mock_repo.license = None
        
        mock_github.return_value.search_repositories.return_value = [mock_repo]
        
        client = GitHubClient("test-token")
        repos = client.search_repos("machine learning language:python")
        
        assert len(repos) == 1
        assert repos[0]["name"] == "awesome-project"
    
    def test_search_repos_with_limit(self, mock_github):
        """测试搜索仓库带限制"""
        mock_repos = [MagicMock() for _ in range(10)]
        mock_github.return_value.search_repositories.return_value = mock_repos
        
        client = GitHubClient("test-token")
        repos = client.search_repos("python", limit=5)
        
        assert len(repos) == 5


# =============================================================================
# 上下文管理器测试
# =============================================================================


class TestContextManager:
    """上下文管理器测试"""
    
    def test_context_manager(self, mock_github):
        """测试上下文管理器"""
        with GitHubClient("test-token") as client:
            assert isinstance(client, GitHubClient)
        
        mock_github.return_value.close.assert_called_once()
    
    def test_context_manager_with_exception(self, mock_github):
        """测试上下文管理器带异常"""
        with pytest.raises(ValueError):
            with GitHubClient("test-token") as client:
                raise ValueError("Test exception")
        
        mock_github.return_value.close.assert_called_once()


# =============================================================================
# 便捷函数测试
# =============================================================================


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_create_client(self, mock_github):
        """测试 create_client 函数"""
        client = create_client("test-token")
        
        assert isinstance(client, GitHubClient)
        assert client.token == "test-token"
    
    def test_get_client(self, mock_github):
        """测试 get_client 函数"""
        with patch("github_auto_sync.github_client.get_auth_token") as mock_get_token:
            mock_get_token.return_value = "stored-token"
            
            client = get_client()
            
            assert isinstance(client, GitHubClient)
            assert client.token == "stored-token"


# =============================================================================
# 异常处理测试
# =============================================================================


class TestExceptionHandling:
    """异常处理测试"""
    
    def test_rate_limit_exception(self, mock_github):
        """测试速率限制异常"""
        mock_github.return_value.get_user.side_effect = GithubException(
            status=403, data={"message": "API rate limit exceeded", "rate": {"reset": 1234567890}}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(RateLimitError):
            client.get_user_info()
    
    def test_permission_exception_401(self, mock_github):
        """测试 401 权限异常"""
        mock_github.return_value.get_user.side_effect = GithubException(
            status=401, data={"message": "Bad credentials"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(PermissionError):
            client.get_user_info()
    
    def test_permission_exception_403(self, mock_github):
        """测试 403 权限异常"""
        mock_github.return_value.get_user.side_effect = GithubException(
            status=403, data={"message": "Forbidden"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(PermissionError):
            client.get_user_info()
    
    def test_generic_github_exception(self, mock_github):
        """测试通用 GitHub 异常"""
        mock_github.return_value.get_user.side_effect = GithubException(
            status=500, data={"message": "Internal Server Error"}
        )
        
        client = GitHubClient("test-token")
        
        with pytest.raises(GitHubClientError):
            client.get_user_info()
