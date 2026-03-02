"""
Git operations module for GitHub Auto Sync.

This module provides a high-level interface for common git operations
using the GitPython library.
"""

import os
from typing import Optional, List, Dict, Any
from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from git.exc import GitError


class GitOperationError(Exception):
    """Custom exception for git operation errors."""
    pass


def init_repo(path: str) -> Repo:
    """
    Initialize a new git repository at the specified path.

    Args:
        path: The directory path where the repository should be initialized.

    Returns:
        The initialized Repo object.

    Raises:
        GitOperationError: If the repository cannot be initialized.
    """
    try:
        os.makedirs(path, exist_ok=True)
        repo = Repo.init(path)
        return repo
    except GitError as e:
        raise GitOperationError(f"Failed to initialize repository at {path}: {e}")
    except OSError as e:
        raise GitOperationError(f"Failed to create directory at {path}: {e}")


def add_remote(path: str, name: str, url: str) -> None:
    """
    Add a remote repository to the git repository.

    Args:
        path: The path to the git repository.
        name: The name of the remote (e.g., 'origin').
        url: The URL of the remote repository.

    Raises:
        GitOperationError: If the remote cannot be added.
    """
    try:
        repo = Repo(path)
        # Check if remote already exists
        if name in [remote.name for remote in repo.remotes]:
            # Remove existing remote
            repo.delete_remote(name)
        repo.create_remote(name, url)
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to add remote '{name}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error while adding remote: {e}")


def commit(path: str, message: str, files: Optional[List[str]] = None) -> None:
    """
    Commit changes to the repository.

    Args:
        path: The path to the git repository.
        message: The commit message.
        files: Optional list of specific files to commit. If None, all changes are committed.

    Raises:
        GitOperationError: If the commit cannot be performed.
    """
    try:
        repo = Repo(path)

        # Check if there are changes to commit
        if not repo.is_dirty(untracked_files=True):
            raise GitOperationError("No changes to commit")

        # Add files
        if files:
            for file in files:
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    repo.git.add(file)
                else:
                    raise GitOperationError(f"File does not exist: {file}")
        else:
            # Add all changes including untracked files
            repo.git.add(A=True)

        # Commit
        repo.index.commit(message)

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to commit changes: {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during commit: {e}")


def push(path: str, remote: str = "origin", branch: Optional[str] = None) -> None:
    """
    Push changes to a remote repository.

    Args:
        path: The path to the git repository.
        remote: The name of the remote to push to (default: 'origin').
        branch: The branch to push. If None, pushes the current branch.

    Raises:
        GitOperationError: If the push cannot be performed.
    """
    try:
        repo = Repo(path)

        # Get the remote
        if remote not in [r.name for r in repo.remotes]:
            raise GitOperationError(f"Remote '{remote}' does not exist")

        remote_obj = repo.remote(remote)

        # Determine branch to push
        if branch is None:
            branch = repo.active_branch.name

        # Push
        push_info = remote_obj.push(refspec=f"{branch}:{branch}")

        # Check for errors in push info
        for info in push_info:
            if info.flags & info.ERROR:
                raise GitOperationError(f"Push failed: {info.summary}")

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to push to remote: {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during push: {e}")


def pull(path: str, remote: str = "origin", branch: Optional[str] = None) -> None:
    """
    Pull changes from a remote repository.

    Args:
        path: The path to the git repository.
        remote: The name of the remote to pull from (default: 'origin').
        branch: The branch to pull. If None, pulls the current branch.

    Raises:
        GitOperationError: If the pull cannot be performed.
    """
    try:
        repo = Repo(path)

        # Get the remote
        if remote not in [r.name for r in repo.remotes]:
            raise GitOperationError(f"Remote '{remote}' does not exist")

        remote_obj = repo.remote(remote)

        # Determine branch to pull
        if branch is None:
            branch = repo.active_branch.name

        # Pull
        pull_info = remote_obj.pull(refspec=branch)

        # Check for errors in pull info
        for info in pull_info:
            if info.flags & info.ERROR:
                raise GitOperationError(f"Pull failed: {info.note}")

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to pull from remote: {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during pull: {e}")


def get_status(path: str) -> Dict[str, Any]:
    """
    Get the status of the repository.

    Args:
        path: The path to the git repository.

    Returns:
        A dictionary containing status information:
        - 'is_dirty': Whether there are uncommitted changes
        - 'untracked_files': List of untracked files
        - 'modified_files': List of modified files
        - 'staged_files': List of staged files
        - 'deleted_files': List of deleted files
        - 'current_branch': Name of the current branch

    Raises:
        GitOperationError: If the status cannot be retrieved.
    """
    try:
        repo = Repo(path)

        # Get untracked files
        untracked = repo.untracked_files

        # Get changed files
        modified = []
        staged = []
        deleted = []

        for item in repo.index.diff(None):  # Compare index to working tree
            if item.change_type == 'D':
                deleted.append(item.a_path)
            else:
                modified.append(item.a_path)

        for item in repo.index.diff(repo.head.commit) if repo.head.is_valid() else []:
            staged.append(item.a_path)

        return {
            'is_dirty': repo.is_dirty(untracked_files=True),
            'untracked_files': untracked,
            'modified_files': modified,
            'staged_files': staged,
            'deleted_files': deleted,
            'current_branch': repo.active_branch.name if repo.head.is_valid() else None
        }

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitError as e:
        raise GitOperationError(f"Failed to get repository status: {e}")


def get_current_branch(path: str) -> Optional[str]:
    """
    Get the name of the current branch.

    Args:
        path: The path to the git repository.

    Returns:
        The name of the current branch, or None if not on a branch.

    Raises:
        GitOperationError: If the branch cannot be determined.
    """
    try:
        repo = Repo(path)
        if repo.head.is_detached:
            return None
        return repo.active_branch.name
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitError as e:
        raise GitOperationError(f"Failed to get current branch: {e}")


def create_branch(path: str, branch_name: str, checkout: bool = False) -> None:
    """
    Create a new branch.

    Args:
        path: The path to the git repository.
        branch_name: The name of the new branch.
        checkout: Whether to checkout the new branch after creation.

    Raises:
        GitOperationError: If the branch cannot be created.
    """
    try:
        repo = Repo(path)

        # Check if branch already exists
        if branch_name in [b.name for b in repo.branches]:
            raise GitOperationError(f"Branch '{branch_name}' already exists")

        # Create branch
        new_branch = repo.create_head(branch_name)

        # Checkout if requested
        if checkout:
            new_branch.checkout()

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to create branch '{branch_name}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during branch creation: {e}")


def checkout_branch(path: str, branch_name: str) -> None:
    """
    Checkout an existing branch.

    Args:
        path: The path to the git repository.
        branch_name: The name of the branch to checkout.

    Raises:
        GitOperationError: If the branch cannot be checked out.
    """
    try:
        repo = Repo(path)

        # Check if branch exists
        if branch_name not in [b.name for b in repo.branches]:
            raise GitOperationError(f"Branch '{branch_name}' does not exist")

        # Checkout branch
        repo.git.checkout(branch_name)

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to checkout branch '{branch_name}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during checkout: {e}")


def clone_repo(url: str, path: str, branch: Optional[str] = None) -> Repo:
    """
    Clone a remote repository.

    Args:
        url: The URL of the remote repository.
        path: The local path where the repository should be cloned.
        branch: The specific branch to clone. If None, clones the default branch.

    Returns:
        The cloned Repo object.

    Raises:
        GitOperationError: If the repository cannot be cloned.
    """
    try:
        if branch:
            repo = Repo.clone_from(url, path, branch=branch, single_branch=True)
        else:
            repo = Repo.clone_from(url, path)
        return repo
    except GitCommandError as e:
        raise GitOperationError(f"Failed to clone repository from {url}: {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during clone: {e}")
    except OSError as e:
        raise GitOperationError(f"Failed to create directory at {path}: {e}")


def has_uncommitted_changes(path: str) -> bool:
    """
    Check if the repository has uncommitted changes.

    Args:
        path: The path to the git repository.

    Returns:
        True if there are uncommitted changes, False otherwise.

    Raises:
        GitOperationError: If the status cannot be determined.
    """
    try:
        repo = Repo(path)
        return repo.is_dirty(untracked_files=True)
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitError as e:
        raise GitOperationError(f"Failed to check for uncommitted changes: {e}")


def get_last_commit(path: str) -> Optional[Dict[str, Any]]:
    """
    Get information about the last commit.

    Args:
        path: The path to the git repository.

    Returns:
        A dictionary containing commit information:
        - 'hash': The commit hash
        - 'short_hash': The short commit hash
        - 'message': The commit message
        - 'author': The author name
        - 'email': The author email
        - 'date': The commit date
        - 'files_changed': List of files changed in the commit
        Or None if there are no commits.

    Raises:
        GitOperationError: If the commit information cannot be retrieved.
    """
    try:
        repo = Repo(path)

        # Check if there are any commits
        if not repo.head.is_valid():
            return None

        commit = repo.head.commit

        # Get files changed in the commit
        files_changed = []
        if commit.parents:
            parent = commit.parents[0]
            files_changed = [item.a_path for item in parent.diff(commit)]
        else:
            # First commit - list all files
            files_changed = list(commit.stats.files.keys())

        return {
            'hash': commit.hexsha,
            'short_hash': commit.hexsha[:7],
            'message': commit.message.strip(),
            'author': commit.author.name,
            'email': commit.author.email,
            'date': commit.committed_datetime,
            'files_changed': files_changed
        }

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitError as e:
        raise GitOperationError(f"Failed to get last commit: {e}")


def is_git_repository(path: str) -> bool:
    """
    Check if the given path is a git repository.

    Args:
        path: The path to check.

    Returns:
        True if the path is a git repository, False otherwise.
    """
    try:
        Repo(path)
        return True
    except (InvalidGitRepositoryError, NoSuchPathError):
        return False


def get_remotes(path: str) -> List[Dict[str, str]]:
    """
    Get a list of configured remotes.

    Args:
        path: The path to the git repository.

    Returns:
        A list of dictionaries containing remote information:
        - 'name': The remote name
        - 'url': The remote URL

    Raises:
        GitOperationError: If the remotes cannot be retrieved.
    """
    try:
        repo = Repo(path)
        remotes = []
        for remote in repo.remotes:
            urls = list(remote.urls)
            remotes.append({
                'name': remote.name,
                'url': urls[0] if urls else None
            })
        return remotes
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitError as e:
        raise GitOperationError(f"Failed to get remotes: {e}")


def remove_remote(path: str, name: str) -> None:
    """
    Remove a remote from the repository.

    Args:
        path: The path to the git repository.
        name: The name of the remote to remove.

    Raises:
        GitOperationError: If the remote cannot be removed.
    """
    try:
        repo = Repo(path)
        if name not in [r.name for r in repo.remotes]:
            raise GitOperationError(f"Remote '{name}' does not exist")
        repo.delete_remote(name)
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to remove remote '{name}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during remote removal: {e}")


def fetch(path: str, remote: str = "origin") -> None:
    """
    Fetch updates from a remote repository.

    Args:
        path: The path to the git repository.
        remote: The name of the remote to fetch from (default: 'origin').

    Raises:
        GitOperationError: If the fetch cannot be performed.
    """
    try:
        repo = Repo(path)

        if remote not in [r.name for r in repo.remotes]:
            raise GitOperationError(f"Remote '{remote}' does not exist")

        remote_obj = repo.remote(remote)
        remote_obj.fetch()

    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to fetch from remote: {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during fetch: {e}")


def checkout_ours(path: str, file_path: str) -> None:
    """
    Checkout our version of a file during merge conflict resolution.

    Args:
        path: The path to the git repository.
        file_path: The path to the file to checkout (relative to repo root).

    Raises:
        GitOperationError: If the checkout cannot be performed.
    """
    try:
        repo = Repo(path)
        # Use git command to checkout ours version
        repo.git.checkout("--ours", file_path)
        # Stage the resolved file
        repo.git.add(file_path)
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to checkout ours for '{file_path}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during checkout: {e}")


def checkout_theirs(path: str, file_path: str) -> None:
    """
    Checkout their version of a file during merge conflict resolution.

    Args:
        path: The path to the git repository.
        file_path: The path to the file to checkout (relative to repo root).

    Raises:
        GitOperationError: If the checkout cannot be performed.
    """
    try:
        repo = Repo(path)
        # Use git command to checkout theirs version
        repo.git.checkout("--theirs", file_path)
        # Stage the resolved file
        repo.git.add(file_path)
    except InvalidGitRepositoryError:
        raise GitOperationError(f"Invalid git repository at {path}")
    except GitCommandError as e:
        raise GitOperationError(f"Failed to checkout theirs for '{file_path}': {e}")
    except GitError as e:
        raise GitOperationError(f"Git error during checkout: {e}")
