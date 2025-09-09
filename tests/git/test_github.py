import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.git.github import (
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
            ["git", "clone", "https://example.com/repo.git", "/tmp/repo", "-b", "main"],
            check=True,
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
    with patch("subprocess.run") as run, patch("requests.post") as post:
        run.return_value = MagicMock(stdout="https://github.com/owner/repo.git\n")
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
            headers={"Authorization": "token abc"},
            timeout=10,
        )
