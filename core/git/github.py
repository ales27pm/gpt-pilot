"""Helpers for working with Git repositories and the GitHub API."""

from __future__ import annotations

import os
import re
import subprocess
from typing import Optional, Tuple

import requests


def clone_repository(repo_url: str, destination: str, branch: Optional[str] = None) -> None:
    """Clone ``repo_url`` into ``destination``.

    Parameters
    ----------
    repo_url: str
        URL of the repository to clone.
    destination: str
        Path where the repository should be cloned.
    branch: Optional[str]
        Branch to checkout after cloning. The ``-b`` flag is inserted before
        the repository URL and destination to satisfy the ``git clone``
        command's argument ordering requirements.
    """

    cmd = ["git", "clone"]
    if branch:
        cmd.extend(["-b", branch])
    cmd.extend([repo_url, destination])
    subprocess.run(cmd, check=True, shell=False)


def commit_all(repo_path: str, message: str) -> None:
    """Stage all changes in ``repo_path`` and create a commit."""

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, shell=False)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_path, check=True, shell=False)


def push(repo_path: str, branch: str, remote: str = "origin") -> None:
    """Push ``branch`` to ``remote`` for repository at ``repo_path``."""

    subprocess.run(["git", "push", remote, branch], cwd=repo_path, check=True, shell=False)


def set_pre_commit_hook(repo_path: str, script: str) -> None:
    """Create a pre-commit hook with ``script`` inside ``repo_path``."""

    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        raise FileNotFoundError(f"No .git directory found in {repo_path}. Is this a valid git repository?")

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)

    hook_path = os.path.join(hooks_dir, "pre-commit")
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(hook_path, os.stat(hook_path).st_mode | 0o111)


def _get_repo_owner_and_name(repo_path: str) -> Tuple[str, str]:
    """Return (owner, name) for repository at ``repo_path``.

    The function reads the ``remote.origin.url`` from the git config and
    extracts owner and repository name if it points to GitHub.
    """

    config_path = os.path.join(repo_path, ".git", "config")
    if not os.path.isfile(config_path):
        raise ValueError("Could not find git config.")

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"url\s*=\s*(.+)", content)
    if not match:
        raise ValueError("Could not find remote URL in git config.")

    remote_url = match.group(1).strip()

    patterns = [
        r"git@github\.com:(?P<owner>[^/]+)/(?P<name>[^/.]+)(\.git)?$",
        r"https://github\.com/(?P<owner>[^/]+)/(?P<name>[^/.]+)(\.git)?$",
        r"ssh://git@github\.com/(?P<owner>[^/]+)/(?P<name>[^/.]+)(\.git)?$",
    ]

    for pattern in patterns:
        match = re.match(pattern, remote_url)
        if match:
            return match.group("owner"), match.group("name")

    raise ValueError(f"Unsupported or non-GitHub remote URL format: {remote_url}")


def create_pull_request(
    repo_path: str,
    branch: str,
    title: str,
    body: str,
    token: str,
    base: str = "main",
) -> dict:
    """Create a pull request for ``branch`` against ``base``."""

    owner, name = _get_repo_owner_and_name(repo_path)
    url = f"https://api.github.com/repos/{owner}/{name}/pulls"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    payload = {"title": title, "body": body, "head": branch, "base": base}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


__all__ = [
    "clone_repository",
    "commit_all",
    "push",
    "set_pre_commit_hook",
    "_get_repo_owner_and_name",
    "create_pull_request",
]
