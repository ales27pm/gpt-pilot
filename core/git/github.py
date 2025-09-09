"""Helpers for working with Git repositories and the GitHub API."""

from __future__ import annotations

import os
import subprocess
from typing import Optional

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
        Branch to checkout after cloning.
    """

    cmd = ["git", "clone", repo_url, destination]
    if branch:
        cmd.extend(["-b", branch])
    subprocess.run(cmd, check=True)


def commit_all(repo_path: str, message: str) -> None:
    """Stage all changes in ``repo_path`` and create a commit."""

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_path, check=True)


def push(repo_path: str, branch: str, remote: str = "origin") -> None:
    """Push ``branch`` to ``remote`` for repository at ``repo_path``."""

    subprocess.run(["git", "push", remote, branch], cwd=repo_path, check=True)


def set_pre_commit_hook(repo_path: str, script: str) -> None:
    """Create a pre-commit hook with ``script`` inside ``repo_path``."""

    hooks_dir = os.path.join(repo_path, ".git", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_path = os.path.join(hooks_dir, "pre-commit")
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(hook_path, 0o755)


def _get_repo_owner_and_name(repo_path: str) -> tuple[str, str]:
    """Return (owner, name) for repository at ``repo_path``."""

    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    url = result.stdout.strip()
    if url.startswith("git@"):
        _, path = url.split(":", 1)
    else:
        path = url.split("github.com/")[-1]
    if path.endswith(".git"):
        path = path[:-4]
    owner, name = path.split("/", 1)
    return owner, name


def create_pull_request(
    repo_path: str,
    branch: str,
    title: str,
    body: str,
    token: str,
    base: str = "main",
) -> dict:
    """Create a pull request for ``branch`` against ``base``.

    Parameters
    ----------
    repo_path: str
        Local path to the repository.
    branch: str
        Name of the branch to merge.
    title: str
        Pull request title.
    body: str
        Pull request body content.
    token: str
        GitHub personal access token.
    base: str
        Target branch for the pull request (default ``"main"``).
    """

    owner, name = _get_repo_owner_and_name(repo_path)
    url = f"https://api.github.com/repos/{owner}/{name}/pulls"
    headers = {"Authorization": f"token {token}"} if token else {}
    payload = {"title": title, "body": body, "head": branch, "base": base}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
