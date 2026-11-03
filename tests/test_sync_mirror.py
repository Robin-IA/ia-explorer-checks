"""sync_mirror.py describes the mirror correctly, including a new, empty one.

Each test builds a throwaway repository with a bare mirror in tmp_path and
points the script at it, so nothing touches the real remotes.
"""

import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import sync_mirror  # noqa: E402


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                   capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    work, bare = tmp_path / "work", tmp_path / "mirror.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    git(tmp_path, "init", "-q", "-b", "main", str(work))
    git(work, "config", "user.email", "t@example.org")
    git(work, "config", "user.name", "t")
    git(work, "commit", "-q", "--allow-empty", "-m", "one")
    git(work, "remote", "add", sync_mirror.MIRROR, str(bare))
    git(work, "fetch", "-q", sync_mirror.MIRROR)
    monkeypatch.setattr(sync_mirror, "ROOT", work)
    return work


def test_empty_mirror_is_named_not_counted(repo):
    assert sync_mirror.mirror_head() is None
    assert sync_mirror.mirror_status() == \
        "mirror is empty, so this is its first push"


def test_mirror_behind_is_counted(repo):
    git(repo, "push", "-q", sync_mirror.MIRROR, "main")
    git(repo, "commit", "-q", "--allow-empty", "-m", "two")
    git(repo, "fetch", "-q", sync_mirror.MIRROR)
    assert sync_mirror.mirror_head() is not None
    assert sync_mirror.mirror_status() == "mirror is 1 commit(s) behind"
