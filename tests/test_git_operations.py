"""
Git 操作单元测试

测试 git_operations 模块的 Git 操作功能。
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from git import Repo, GitCommandError, InvalidGitRepositoryError
from git.exc import GitError

from github_auto_sync.git_operations import (
    init_repo,
    add_remote,
    commit,
    push,
    pull,
    get_status,
    get_current_branch,
    create_branch,
    checkout_branch,
    clone_repo,
    has_uncommitted_changes,
    get_last_commit,
    is_git_repository,
    get_remotes,
    remove_remote,
    fetch,
    checkout_ours,
    checkout_theirs,
    GitOperationError,
)


# =============================================================================
# 仓库初始化测试
# =============================================================================


class TestInitRepo:
    """仓库初始化测试"""
    
    def test_init_repo_success(self, temp_dir: Path):
        """测试成功初始化仓库"""
        repo_path = temp_dir / "new-repo"
        
        repo = init_repo(str(repo_path))
        
        assert isinstance(repo, Repo)
        assert (repo_path / ".git").exists()
    
    def test_init_repo_existing_directory(self, temp_dir: Path):
        """测试在现有目录初始化仓库"""
        repo_path = temp_dir / "existing-dir"
        repo_path.mkdir()
        (repo_path / "file.txt").write_text("content")
        
        repo = init_repo(str(repo_path))
        
        assert isinstance(repo, Repo)
        assert (repo_path / ".git").exists()
    
    @patch("github_auto_sync.git_operations.Repo.init")
    def test_init_repo_git_error(self, mock_init, temp_dir: Path):
        """测试初始化仓库 Git 错误"""
        mock_init.side_effect = GitError("Init failed")
        
        with pytest.raises(GitOperationError, match="Failed to initialize"):
            init_repo(str(temp_dir / "repo"))


# =============================================================================
# 远程操作测试
# =============================================================================


class TestAddRemote:
    """添加远程测试"""
    
    def test_add_remote_success(self, mock_git_repo: Path):
        """测试成功添加远程"""
        add_remote(str(mock_git_repo), "origin", "https://github.com/user/repo.git")
        
        repo = Repo(str(mock_git_repo))
        remotes = [r.name for r in repo.remotes]
        assert "origin" in remotes
    
    def test_add_remote_update_existing(self, mock_git_repo: Path):
        """测试更新现有远程"""
        # 先添加一个远程
        add_remote(str(mock_git_repo), "origin", "https://github.com/user/old.git")
        
        # 更新远程 URL
        add_remote(str(mock_git_repo), "origin", "https://github.com/user/new.git")
        
        repo = Repo(str(mock_git_repo))
        origin = repo.remote("origin")
        urls = list(origin.urls)
        assert "https://github.com/user/new.git" in urls
    
    def test_add_remote_invalid_repo(self, temp_dir: Path):
        """测试在无效仓库添加远程"""
        with pytest.raises(GitOperationError, match="Invalid git repository"):
            add_remote(str(temp_dir), "origin", "https://github.com/user/repo.git")


class TestRemoveRemote:
    """移除远程测试"""
    
    def test_remove_remote_success(self, mock_git_repo: Path):
        """测试成功移除远程"""
        add_remote(str(mock_git_repo), "origin", "https://github.com/user/repo.git")
        
        remove_remote(str(mock_git_repo), "origin")
        
        repo = Repo(str(mock_git_repo))
        remotes = [r.name for r in repo.remotes]
        assert "origin" not in remotes
    
    def test_remove_remote_not_exists(self, mock_git_repo: Path):
        """测试移除不存在的远程"""
        with pytest.raises(GitOperationError, match="does not exist"):
            remove_remote(str(mock_git_repo), "nonexistent")


class TestGetRemotes:
    """获取远程列表测试"""
    
    def test_get_remotes_empty(self, mock_git_repo: Path):
        """测试获取空远程列表"""
        remotes = get_remotes(str(mock_git_repo))
        
        assert remotes == []
    
    def test_get_remotes_with_remotes(self, mock_git_repo: Path):
        """测试获取远程列表"""
        add_remote(str(mock_git_repo), "origin", "https://github.com/user/repo.git")
        add_remote(str(mock_git_repo), "upstream", "https://github.com/upstream/repo.git")
        
        remotes = get_remotes(str(mock_git_repo))
        
        assert len(remotes) == 2
        remote_names = [r["name"] for r in remotes]
        assert "origin" in remote_names
        assert "upstream" in remote_names


# =============================================================================
# 提交操作测试
# =============================================================================


class TestCommit:
    """提交测试"""
    
    def test_commit_all_changes(self, mock_git_repo: Path):
        """测试提交所有变更"""
        # 创建新文件
        (mock_git_repo / "new_file.py").write_text("print('hello')")
        
        commit(str(mock_git_repo), "Add new file")
        
        repo = Repo(str(mock_git_repo))
        assert not repo.is_dirty(untracked_files=True)
        assert repo.head.commit.message == "Add new file"
    
    def test_commit_specific_files(self, mock_git_repo: Path):
        """测试提交特定文件"""
        (mock_git_repo / "file1.py").write_text("content1")
        (mock_git_repo / "file2.py").write_text("content2")
        
        commit(str(mock_git_repo), "Add file1", files=["file1.py"])
        
        repo = Repo(str(mock_git_repo))
        # file1 应该已提交，file2 应该还在未跟踪状态
        assert "file1.py" not in repo.untracked_files
    
    def test_commit_no_changes(self, mock_git_repo: Path):
        """测试无变更时提交"""
        with pytest.raises(GitOperationError, match="No changes to commit"):
            commit(str(mock_git_repo), "Empty commit")
    
    def test_commit_nonexistent_file(self, mock_git_repo: Path):
        """测试提交不存在的文件"""
        with pytest.raises(GitOperationError, match="File does not exist"):
            commit(str(mock_git_repo), "Commit", files=["nonexistent.py"])


# =============================================================================
# 推送拉取测试
# =============================================================================


class TestPush:
    """推送测试"""
    
    @patch("github_auto_sync.git_operations.Repo")
    def test_push_success(self, mock_repo_class, mock_git_repo: Path):
        """测试成功推送"""
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_push_info = MagicMock()
        mock_push_info.flags = 0  # 无错误
        mock_remote.push.return_value = [mock_push_info]
        mock_repo.remotes = [mock_remote]
        mock_remote.name = "origin"
        mock_repo.remote.return_value = mock_remote
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo
        
        # 使用 mock 路径
        push("/fake/path", "origin", "main")
        
        mock_remote.push.assert_called_once()
    
    def test_push_remote_not_exists(self, mock_git_repo: Path):
        """测试推送到不存在的远程"""
        with pytest.raises(GitOperationError, match="does not exist"):
            push(str(mock_git_repo), "nonexistent", "main")


class TestPull:
    """拉取测试"""
    
    @patch("github_auto_sync.git_operations.Repo")
    def test_pull_success(self, mock_repo_class):
        """测试成功拉取"""
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_pull_info = MagicMock()
        mock_pull_info.flags = 0
        mock_remote.pull.return_value = [mock_pull_info]
        mock_repo.remotes = [mock_remote]
        mock_remote.name = "origin"
        mock_repo.remote.return_value = mock_remote
        mock_repo.active_branch.name = "main"
        mock_repo_class.return_value = mock_repo
        
        pull("/fake/path", "origin", "main")
        
        mock_remote.pull.assert_called_once()
    
    def test_pull_remote_not_exists(self, mock_git_repo: Path):
        """测试从不存在的远程拉取"""
        with pytest.raises(GitOperationError, match="does not exist"):
            pull(str(mock_git_repo), "nonexistent", "main")


class TestFetch:
    """获取测试"""
    
    @patch("github_auto_sync.git_operations.Repo")
    def test_fetch_success(self, mock_repo_class):
        """测试成功获取"""
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_repo.remotes = [mock_remote]
        mock_remote.name = "origin"
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo
        
        fetch("/fake/path", "origin")
        
        mock_remote.fetch.assert_called_once()


# =============================================================================
# 状态查询测试
# =============================================================================


class TestGetStatus:
    """获取状态测试"""
    
    def test_get_status_clean(self, mock_git_repo: Path):
        """测试获取干净状态"""
        status = get_status(str(mock_git_repo))
        
        assert status["is_dirty"] is False
        assert status["untracked_files"] == []
        assert status["current_branch"] == "main"
    
    def test_get_status_with_untracked(self, mock_git_repo: Path):
        """测试获取有未跟踪文件的状态"""
        (mock_git_repo / "untracked.py").write_text("content")
        
        status = get_status(str(mock_git_repo))
        
        assert status["is_dirty"] is True
        assert "untracked.py" in status["untracked_files"]
    
    def test_get_status_invalid_repo(self, temp_dir: Path):
        """测试获取无效仓库状态"""
        with pytest.raises(GitOperationError, match="Invalid git repository"):
            get_status(str(temp_dir))


class TestHasUncommittedChanges:
    """检查未提交变更测试"""
    
    def test_has_changes_true(self, mock_git_repo: Path):
        """测试有未提交变更"""
        (mock_git_repo / "new_file.py").write_text("content")
        
        result = has_uncommitted_changes(str(mock_git_repo))
        
        assert result is True
    
    def test_has_changes_false(self, mock_git_repo: Path):
        """测试无未提交变更"""
        result = has_uncommitted_changes(str(mock_git_repo))
        
        assert result is False


class TestGetLastCommit:
    """获取最后提交测试"""
    
    def test_get_last_commit(self, mock_git_repo: Path):
        """测试获取最后提交"""
        commit_info = get_last_commit(str(mock_git_repo))
        
        assert commit_info is not None
        assert "hash" in commit_info
        assert "short_hash" in commit_info
        assert "message" in commit_info
        assert commit_info["message"] == "Initial commit"
    
    def test_get_last_commit_no_commits(self, temp_dir: Path):
        """测试获取无提交的仓库"""
        # 初始化新仓库但不提交
        repo = Repo.init(temp_dir)
        
        commit_info = get_last_commit(str(temp_dir))
        
        assert commit_info is None


# =============================================================================
# 分支管理测试
# =============================================================================


class TestGetCurrentBranch:
    """获取当前分支测试"""
    
    def test_get_current_branch(self, mock_git_repo: Path):
        """测试获取当前分支"""
        branch = get_current_branch(str(mock_git_repo))
        
        assert branch == "main"
    
    def test_get_current_branch_detached(self, temp_dir: Path):
        """测试获取分离头指针状态"""
        # 初始化并创建分离头指针
        repo = Repo.init(temp_dir)
        (temp_dir / "file.txt").write_text("content")
        repo.index.add(["file.txt"])
        repo.index.commit("Initial")
        
        # 分离头指针
        repo.head.reference = repo.head.commit
        
        branch = get_current_branch(str(temp_dir))
        
        assert branch is None


class TestCreateBranch:
    """创建分支测试"""
    
    def test_create_branch_success(self, mock_git_repo: Path):
        """测试成功创建分支"""
        create_branch(str(mock_git_repo), "feature-branch")
        
        repo = Repo(str(mock_git_repo))
        branch_names = [b.name for b in repo.branches]
        assert "feature-branch" in branch_names
    
    def test_create_branch_and_checkout(self, mock_git_repo: Path):
        """测试创建分支并检出"""
        create_branch(str(mock_git_repo), "feature-branch", checkout=True)
        
        repo = Repo(str(mock_git_repo))
        assert repo.active_branch.name == "feature-branch"
    
    def test_create_branch_already_exists(self, mock_git_repo: Path):
        """测试创建已存在的分支"""
        create_branch(str(mock_git_repo), "feature-branch")
        
        with pytest.raises(GitOperationError, match="already exists"):
            create_branch(str(mock_git_repo), "feature-branch")


class TestCheckoutBranch:
    """检出分支测试"""
    
    def test_checkout_branch_success(self, mock_git_repo: Path):
        """测试成功检出分支"""
        create_branch(str(mock_git_repo), "feature-branch")
        
        checkout_branch(str(mock_git_repo), "feature-branch")
        
        repo = Repo(str(mock_git_repo))
        assert repo.active_branch.name == "feature-branch"
    
    def test_checkout_branch_not_exists(self, mock_git_repo: Path):
        """测试检出不存在的分支"""
        with pytest.raises(GitOperationError, match="does not exist"):
            checkout_branch(str(mock_git_repo), "nonexistent-branch")


# =============================================================================
# 克隆测试
# =============================================================================


class TestCloneRepo:
    """克隆仓库测试"""
    
    @patch("github_auto_sync.git_operations.Repo.clone_from")
    def test_clone_repo_success(self, mock_clone, temp_dir: Path):
        """测试成功克隆仓库"""
        mock_repo = MagicMock()
        mock_clone.return_value = mock_repo
        
        dest = temp_dir / "cloned"
        repo = clone_repo("https://github.com/user/repo.git", str(dest))
        
        assert repo == mock_repo
        mock_clone.assert_called_once_with("https://github.com/user/repo.git", str(dest))
    
    @patch("github_auto_sync.git_operations.Repo.clone_from")
    def test_clone_repo_with_branch(self, mock_clone, temp_dir: Path):
        """测试克隆特定分支"""
        mock_repo = MagicMock()
        mock_clone.return_value = mock_repo
        
        dest = temp_dir / "cloned"
        clone_repo("https://github.com/user/repo.git", str(dest), branch="develop")
        
        mock_clone.assert_called_once_with(
            "https://github.com/user/repo.git",
            str(dest),
            branch="develop",
            single_branch=True
        )
    
    @patch("github_auto_sync.git_operations.Repo.clone_from")
    def test_clone_repo_error(self, mock_clone, temp_dir: Path):
        """测试克隆错误"""
        mock_clone.side_effect = GitCommandError("clone", "Failed")
        
        with pytest.raises(GitOperationError, match="Failed to clone"):
            clone_repo("https://github.com/user/repo.git", str(temp_dir / "cloned"))


# =============================================================================
# 仓库检查测试
# =============================================================================


class TestIsGitRepository:
    """检查 Git 仓库测试"""
    
    def test_is_git_repository_true(self, mock_git_repo: Path):
        """测试是 Git 仓库"""
        result = is_git_repository(str(mock_git_repo))
        
        assert result is True
    
    def test_is_git_repository_false(self, temp_dir: Path):
        """测试不是 Git 仓库"""
        result = is_git_repository(str(temp_dir))
        
        assert result is False
    
    def test_is_git_repository_nonexistent(self, temp_dir: Path):
        """测试不存在的路径"""
        result = is_git_repository(str(temp_dir / "nonexistent"))
        
        assert result is False


# =============================================================================
# 冲突解决测试
# =============================================================================


class TestCheckoutOurs:
    """检出我们的版本测试"""
    
    @patch("github_auto_sync.git_operations.Repo")
    def test_checkout_ours_success(self, mock_repo_class):
        """测试成功检出我们的版本"""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        checkout_ours("/fake/path", "conflicted_file.py")
        
        mock_repo.git.checkout.assert_called_once_with("--ours", "conflicted_file.py")
        mock_repo.git.add.assert_called_once_with("conflicted_file.py")


class TestCheckoutTheirs:
    """检出他们的版本测试"""
    
    @patch("github_auto_sync.git_operations.Repo")
    def test_checkout_theirs_success(self, mock_repo_class):
        """测试成功检出他们的版本"""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        checkout_theirs("/fake/path", "conflicted_file.py")
        
        mock_repo.git.checkout.assert_called_once_with("--theirs", "conflicted_file.py")
        mock_repo.git.add.assert_called_once_with("conflicted_file.py")
