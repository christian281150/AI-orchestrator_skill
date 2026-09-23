# SPDX-License-Identifier: MIT
"""Commit ONLY the named paths to the current branch, safely, while other agents
are working in the same repository.

Lesson built in: a plain `git commit` from a side session once concluded the
coordinator's half-finished merge, conflict markers included. This waits until
no merge/rebase is in progress, refuses if anything else is already staged,
commits only the given paths, and on failure unstages path by path (a single
`git restore` over a list containing one new file fails for the whole list).
It never touches the working tree of other paths.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True)


def _busy(root: Path) -> str | None:
    gd = _git(root, "rev-parse", "--git-dir").stdout.decode().strip()
    gdir = Path(gd) if Path(gd).is_absolute() else root / gd
    for n in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply"):
        if (gdir / n).exists():
            return n
    return None


def safe_commit(root: str | Path, message: str, paths: list[str], wait_s: int = 600, poll_s: float = 5) -> tuple[bool, str]:
    root = Path(root).resolve()
    if not paths:
        return False, "no paths given - refusing to commit everything"
    deadline = time.monotonic() + wait_s
    while (b := _busy(root)) is not None:
        if time.monotonic() > deadline:
            return False, f"gave up: {b} still present after {wait_s}s (someone is merging)"
        time.sleep(poll_s)
    pre = set(_git(root, "diff", "--cached", "--name-only").stdout.decode("utf-8", "replace").split())
    if pre:
        return False, f"refusing: other paths already staged by someone else: {sorted(pre)[:10]}"
    for p in paths:
        r = _git(root, "add", "--", p)
        if r.returncode != 0:
            _unstage(root, paths)
            return False, f"git add {p} failed: {r.stderr.decode(errors='replace').strip()}"
    staged = set(_git(root, "diff", "--cached", "--name-only").stdout.decode("utf-8", "replace").split())
    if not staged:
        return False, "nothing to commit in the given paths"
    if _busy(root):   # a merge started between our check and now
        _unstage(root, paths)
        return False, "a merge started meanwhile - unstaged, try again"
    r = _git(root, "commit", "-m", message, "--", *paths)
    if r.returncode != 0:
        _unstage(root, paths)
        return False, "commit refused (hook?): " + (r.stdout + r.stderr).decode(errors="replace").strip()[-800:]
    sha = _git(root, "rev-parse", "--short", "HEAD").stdout.decode().strip()
    return True, f"committed {sha}: {len(staged)} path(s)"


def _unstage(root: Path, paths: list[str]) -> None:
    for p in paths:   # path by path: one bad path must not block the rest
        if _git(root, "restore", "--staged", "--", p).returncode != 0:
            _git(root, "rm", "--cached", "-q", "--", p)
