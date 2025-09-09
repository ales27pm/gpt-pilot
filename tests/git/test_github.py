import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from core.git.github import (
    _get_repo_owner_and_name,
    clone_repository,
    commit_all,
    create_pull_request,
    push,
    set_pre_commit_hook,
)


def test_clone_repository():
    with patch("subprocess.run") as run:
        clone_repository("https://example.com/repo.git", "/tmp/repo", branch="main")
        run.assert_called_with(
            ["git", "clone", "-b", "main", "https://example.com/repo.git", "/tmp/repo"],
            check=True,
            shell=False,
        )


def test_commit_and_push():
    with patch("subprocess.run") as run:
        commit_all("/tmp/repo", "msg")
        push("/tmp/repo", "main")
    assert run.call_count == 3  # add, commit, push


def test_set_pre_commit_hook(tmp_path: Path):
    repo = tmp_path
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True)
    set_pre_commit_hook(str(repo), "echo test")
    hook_path = hooks_dir / "pre-commit"
    assert hook_path.read_text() == "echo test"
    assert os.access(hook_path, os.X_OK)


def test_create_pull_request():
    with (
        patch("core.git.github._get_repo_owner_and_name", return_value=("owner", "repo")),
        patch("requests.post") as post,
    ):
        response = MagicMock()
        response.json.return_value = {"url": "https://api.github.com/repos/owner/repo/pulls/1"}
        response.raise_for_status.return_value = None
        post.return_value = response
        result = create_pull_request(
            "/tmp/repo",
            branch="feature",
            title="T",
            body="B",
            token="abc",
        )
        assert result["url"].endswith("/pulls/1")
        post.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls",
            json={"title": "T", "body": "B", "head": "feature", "base": "main"},
            headers={"Authorization": "Bearer abc"},
            timeout=10,
        )


@pytest.mark.parametrize("token", [None, ""])
def test_create_pull_request_missing_or_invalid_token(token):
    with (
        patch("core.git.github._get_repo_owner_and_name", return_value=("owner", "repo")),
        patch("requests.post") as post,
    ):
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        post.return_value = response
        with pytest.raises(requests.HTTPError):
            create_pull_request(
                "/tmp/repo",
                branch="feature",
                title="T",
                body="B",
                token=token,
            )
        post.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls",
            json={"title": "T", "body": "B", "head": "feature", "base": "main"},
            headers={},
            timeout=10,
        )


def test_get_repo_owner_and_name(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text('[remote "origin"]\n    url = git@github.com:owner/repo.git\n')
    assert _get_repo_owner_and_name(str(tmp_path)) == ("owner", "repo")


def test_get_repo_owner_and_name_invalid(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config = git_dir / "config"
    config.write_text('[remote "origin"]\n    url = https://example.com/owner/repo.git\n')
    with pytest.raises(ValueError):
        _get_repo_owner_and_name(str(tmp_path))
