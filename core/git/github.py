"""Helpers for working with Git repositories and the GitHub API."""

from __future__ import annotations

import os
import re
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
    def _get_repo_owner_and_name(repo_path: str) -> tuple[str, str, str]:
        """Return (host, owner, name) for repository at ``repo_path``."""

        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        url = result.stdout.strip()

        host = ""
        path = ""
        if url.startswith("git@"):
            # SSH format: git@host:owner/repo(.git)
            try:
                _, rest = url.split("@", 1)
                host, path = rest.split(":", 1)
            except ValueError as e:
                raise ValueError(f"Unsupported remote URL format: {url}") from e
        else:
            # HTTPS format: https://host/owner/repo(.git)
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or ""
            path = parsed.path.lstrip("/")

        if path.endswith(".git"):
            path = path[:-4]
        owner, name = path.split("/", 1)
        return host, owner, name

    if not remote_url:
        raise ValueError("Could not find remote URL in git config.")

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
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    payload = {"title": title, "body": body, "head": branch, "base": base}
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
