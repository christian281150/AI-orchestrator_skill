import subprocess

from orchestrator.safe_commit import safe_commit
from conftest import sh


def test_commits_only_named_paths(repo):
    (repo / "a.txt").write_text("a")
    (repo / "b.txt").write_text("b")
    ok, msg = safe_commit(repo, "add a", ["a.txt"])
    assert ok, msg
    assert sh(repo, "git", "show", "--name-only", "--format=", "HEAD").split() == ["a.txt"]
    assert "?? b.txt" in sh(repo, "git", "status", "--porcelain")


def test_refuses_during_merge_and_with_foreign_staging(repo):
    (repo / "a.txt").write_text("a")
    (repo / ".git" / "MERGE_HEAD").write_text("0" * 40)
    ok, msg = safe_commit(repo, "x", ["a.txt"], wait_s=0)
    assert not ok and "MERGE_HEAD" in msg
    (repo / ".git" / "MERGE_HEAD").unlink()
    (repo / "c.txt").write_text("c")
    sh(repo, "git", "add", "c.txt")
    ok, msg = safe_commit(repo, "x", ["a.txt"])
    assert not ok and "already staged" in msg


def test_commit_msg_hook_blocks_attribution(repo):
    (repo / "a.txt").write_text("a")
    sh(repo, "git", "add", "a.txt")
    r = subprocess.run(["git", "commit", "-q", "-m", "feat: a\n\nCo-Authored-By: Claude <x@example.com>"],
                       cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and "forbidden line" in r.stderr
    sh(repo, "git", "commit", "-q", "-m", "feat: a")


def test_pre_commit_blocks_har_and_secret(repo):
    (repo / "capture.har").write_text("{}")
    sh(repo, "git", "add", "-f", "capture.har")
    r = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and "forbidden path" in r.stderr
    sh(repo, "git", "rm", "-q", "--cached", "capture.har")
    (repo / "conf.py").write_text('password = "hunter2hunter2"\n')
    sh(repo, "git", "add", "conf.py")
    r = subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo, capture_output=True, text=True)
    assert r.returncode != 0 and "possible secret" in r.stderr
