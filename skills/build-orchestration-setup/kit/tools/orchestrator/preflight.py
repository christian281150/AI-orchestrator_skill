# SPDX-License-Identifier: MIT
"""Preflight: everything a round depends on, checked before round 1 and at every
supervisor start. PASS / WARN / FAIL lines; exit 1 on any FAIL."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import board
from .config import Config
from .providers import VERDICT, codex_used_percent


def _free_ram_gb() -> float | None:
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong)]
            m = MS()
            m.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.avail / 2**30
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 2**20
    except Exception:
        return None
    return None


def run(cfg: Config) -> tuple[int, list[str]]:
    out: list[str] = []
    fails = 0

    def res(ok: bool | None, msg: str):
        nonlocal fails
        tag = "PASS" if ok else ("WARN" if ok is None else "FAIL")
        fails += ok is False
        out.append(f"[{tag}] {msg}")

    res(sys.version_info >= (3, 11), f"python {sys.version.split()[0]} (needs 3.11+)")
    top = subprocess.run(["git", "-C", str(cfg.root), "rev-parse", "--show-toplevel"], capture_output=True)
    res(top.returncode == 0, f"git repository at {cfg.root}")
    if cfg.board.exists():
        rows = board.parse(cfg.board)
        probs = board.validate(rows, cfg.id_pattern)
        res(not probs, f"board {cfg.board.name}: {len(rows)} rows, {len(probs)} problem(s)"
            + ("" if not probs else " - first: " + probs[0]))
    else:
        res(False, f"board missing: {cfg.board}")
    sp = cfg.session_prompt
    res(sp.exists() and VERDICT in sp.read_text(encoding="utf-8"), f"session prompt exists and asks for '{VERDICT}'")
    res(cfg.decisions.exists(), f"decisions log exists: {cfg.decisions.name}")
    res((cfg.root / ".gitattributes").exists(), ".gitattributes present (line endings fixed before the first hash)")
    hp = subprocess.run(["git", "-C", str(cfg.root), "config", "core.hooksPath"], capture_output=True).stdout.decode().strip()
    res(hp == ".githooks" and (cfg.root / ".githooks" / "pre-commit").exists(), f"git hooks wired (core.hooksPath={hp or '-'})")
    if cfg.author_email:
        em = subprocess.run(["git", "-C", str(cfg.root), "config", "user.email"], capture_output=True).stdout.decode().strip()
        res(em.lower() == cfg.author_email.lower(), f"git author email {em or '-'} == configured")
    for p in cfg.providers:
        if not p.enabled:
            continue
        for kind, cmd in (("round", p.round_command), ("build", p.build_command)):
            if cmd:
                res(shutil.which(cmd[0]) is not None, f"provider {p.name}: {kind} command '{cmd[0]}' on PATH")
        if p.native_limit == "codex_rollout":
            used = codex_used_percent()
            res(None if used is None else True, f"provider {p.name}: native usage record "
                + ("not found (text fallback will be used)" if used is None else f"readable, {used:.0f}% used"))
    for name in cfg.required_env:
        res(bool(os.environ.get(name)), f"environment variable {name} is set (value not shown)")
    stripped = {n for p in cfg.providers for n in p.strip_env}
    if stripped:
        out.append(f"[INFO] stripped from build-only providers: {', '.join(sorted(stripped))}")
    from .skills import inventory, named_in_agents
    installed = {i["name"] for i in inventory(cfg.root)}
    for rel in (".claude/agents", ".codex/agents"):
        d = cfg.root / rel
        for f in sorted(d.glob("*.md")) if d.exists() else []:
            if f.read_bytes().startswith(b"\xef\xbb\xbf"):
                res(False, f"{f.name} starts with a byte-order mark (breaks frontmatter)")
    named = [(f, n) for f, ns in named_in_agents(cfg.root).items() for n in ns]
    for f, n in named:
        if n not in installed:
            res(False, f"{Path(f).name} names skill '{n}' - not installed")
    missing = sum(1 for _, n in named if n not in installed)
    res(missing == 0, f"every skill an agent file names is installed - {len(named)} named, {len(named) - missing} present")
    try:
        cfg.state_dir.mkdir(parents=True, exist_ok=True)
        (cfg.state_dir / ".probe").write_text("ok")
        (cfg.state_dir / ".probe").unlink()
        res(True, f"state dir writable: {cfg.state_dir}")
    except OSError as e:
        res(False, f"state dir not writable: {e}")
    try:
        inside = cfg.state_dir.resolve().is_relative_to(cfg.root.resolve())
    except AttributeError:
        inside = str(cfg.state_dir.resolve()).startswith(str(cfg.root.resolve()))
    res(not inside, "state dir is outside the repository")
    status = subprocess.run(["git", "-C", str(cfg.root), "status", "--porcelain"], capture_output=True).stdout.decode()
    res(None if status.strip() else True, "main working tree clean" + ("" if not status.strip() else f" - {len(status.splitlines())} changed path(s)"))
    ram = _free_ram_gb()
    if ram is not None:
        res(True if ram >= 2 else None, f"free RAM {ram:.1f} GB (each parallel lead needs roughly 0.5-1 GB)")
    return fails, out
