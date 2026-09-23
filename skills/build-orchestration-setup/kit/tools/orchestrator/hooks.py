# SPDX-License-Identifier: MIT
"""Git hooks: pre-commit (forbidden paths, secrets, board consistency, author) and
commit-msg (forbidden trailer lines). Wired by `.githooks/*` -> `orch.py hook <name>`."""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from . import board, redact
from .config import Config

HIGH_CONFIDENCE = {"private-key", "aws-key", "github-token", "anthropic-key", "openai-key", "jwt",
                   "assignment", "conn-string"}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True).stdout.decode("utf-8", "replace")


def pre_commit(cfg: Config) -> list[str]:
    errs: list[str] = []
    staged = [s for s in _git(cfg.root, "diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if s]
    for f in staged:
        for pat in cfg.forbid_paths:
            if fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(Path(f).name, pat):
                errs.append(f"forbidden path staged: {f} (matches '{pat}')")
    diff = _git(cfg.root, "diff", "--cached", "-U0", "--no-color")
    current = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            for _, name, val in redact.scan(line[1:], cfg.redact_terms):
                if name in HIGH_CONFIDENCE or name.startswith("term:"):
                    errs.append(f"possible secret in {current}: {name} '{val[:12]}...'")
    try:
        board_rel = str(cfg.board.relative_to(cfg.root)).replace("\\", "/")
    except ValueError:
        board_rel = ""
    if board_rel in staged:
        errs += [f"board: {p}" for p in board.validate(board.parse(cfg.board), cfg.id_pattern)]
    if cfg.author_email:
        ident = subprocess.run(["git", "-C", str(cfg.root), "var", "GIT_AUTHOR_IDENT"], capture_output=True).stdout.decode()
        if cfg.author_email.lower() not in ident.lower():
            errs.append(f"author is '{ident.split('>')[0]}>', expected <{cfg.author_email}>")
    return errs


def commit_msg(cfg: Config, msg_file: str) -> list[str]:
    text = Path(msg_file).read_text(encoding="utf-8", errors="replace")
    errs = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        for t in cfg.forbid_trailers:
            if t and t.lower() in line.lower():
                errs.append(f"commit message contains forbidden line: '{line.strip()[:80]}'")
    return errs
