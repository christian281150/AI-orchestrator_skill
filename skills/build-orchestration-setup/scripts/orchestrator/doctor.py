# SPDX-License-Identifier: MIT
"""Doctor: is this computer ready - BEFORE any project exists?

`preflight` needs an orchestration.toml; beginners get stuck one step earlier
("python is not recognized", git without a name, the AI tool not on PATH).
Every FAIL and WARN line comes with a plain-language fix. Exit 1 on any FAIL.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from collections.abc import Callable

# Only used to list what is already installed when the owner named no tool - never assumed.
COMMON_AGENT_CLIS = ("claude", "codex", "gemini", "cursor-agent", "aider", "opencode")
CLOUD_SYNC_HINTS = ("onedrive", "dropbox", "icloud", "google drive", "googledrive", "box sync")


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.returncode, (r.stdout or r.stderr).decode("utf-8", "replace").strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def run(tools: list[str] | None = None, project: Path | None = None, home: Path | None = None,
        which: Callable[[str], str | None] = shutil.which,
        runner: Callable[[list[str]], tuple[int, str]] = _run,
        py_version: tuple[int, int] = sys.version_info[:2]) -> tuple[int, list[str]]:
    out: list[str] = []
    fails = 0

    def res(ok: bool | None, msg: str, fix: str = "") -> None:
        nonlocal fails
        tag = "PASS" if ok else ("WARN" if ok is None else "FAIL")
        fails += ok is False
        out.append(f"[{tag}] {msg}")
        if fix and ok is not True:
            out.append(f"       Fix: {fix}")

    # Python
    res(py_version >= (3, 11), f"Python {py_version[0]}.{py_version[1]} (needs 3.11 or newer)",
        "install Python 3.11+ from python.org; on Windows tick 'Add python.exe to PATH', then open a NEW terminal")
    py = which("python") or ""
    if os.name == "nt" and "windowsapps" in py.lower():
        res(None, "'python' points to the Microsoft Store placeholder",
            "install from python.org with 'Add to PATH', or turn off the python 'App execution aliases' in Windows settings")

    # Git
    if which("git"):
        code, ver = runner(["git", "--version"])
        res(code == 0, f"Git installed ({ver or 'version unknown'})", "reinstall Git from git-scm.com with the default choices")
        for key, example in (("user.name", '"Your Name"'), ("user.email", '"you@example.com"')):
            code, val = runner(["git", "config", "--global", key])
            res(True if code == 0 and val else None, f"git {key} set" + (f" ({val})" if val else ""),
                f"git config --global {key} {example} (public repositories: use your git host's no-reply address)")
    else:
        res(False, "Git not found on PATH", "install Git from git-scm.com with the default choices, then open a NEW terminal")

    # Profile (optional)
    from . import profile as prof_mod
    prof, used = prof_mod.load(project, home)
    if used:
        probs = prof_mod.check(prof)
        res(not probs, f"profile readable ({len(used)} file(s))" + (f" - {probs[0]}" if probs else ""),
            "open the profile in a text editor and fix the line named above (`orch.py profile check` lists all)")
    else:
        out.append("[INFO] no profile yet - optional; `orch.py profile init` creates one")

    # AI tools
    named = list(tools or [])
    if not named:
        t = prof.get("tools", {})
        named = [x for x in [t.get("lead", "")] + list(t.get("build", []) or []) if x]
    if not named:
        found = [c for c in COMMON_AGENT_CLIS if which(c)]
        res(None, "no AI tool named" + (f" - found on PATH: {', '.join(found)}" if found else ""),
            "run `orch.py doctor --tools <your tool>` or set [tools] lead/build in your profile")
    for tool in dict.fromkeys(named):
        if not which(tool):
            res(False, f"AI tool '{tool}' not found on PATH",
                f"install '{tool}' from its official page, log in once, then open a NEW terminal")
            continue
        code, ver = runner([tool, "--version"])
        first = ver.splitlines()[0][:80] if ver else ""
        res(True if code == 0 else None, f"AI tool '{tool}' runs" + (f" ({first})" if first else ""),
            f"run `{tool} --version` yourself; if it asks you to log in, do that once")

    # Project folder (optional)
    if project is not None:
        p = str(Path(project).resolve())
        synced = next((h for h in CLOUD_SYNC_HINTS if h in p.lower()), "")
        res(None if synced else True, f"project folder {p}" + (f" is inside a cloud-synced folder ({synced})" if synced else ""),
            "use a plain local folder such as C:\\Projects\\my-app - sync tools lock and duplicate files mid-build")
        if re.search(r"\s", p):
            res(None, "project path contains spaces", "some tools and scripts break on spaces - prefer e.g. C:\\Projects\\my-app")

    # Machine
    base = Path(home or Path.home())
    try:
        free_gb = shutil.disk_usage(base).free / 2**30
        res(True if free_gb >= 5 else None, f"free disk {free_gb:.0f} GB",
            "free at least 5 GB - each lane working copy and its logs take space")
    except OSError:
        pass
    from .preflight import _free_ram_gb
    ram = _free_ram_gb()
    if ram is not None:
        res(True if ram >= 4 else None, f"free memory {ram:.1f} GB",
            "close other programs, or plan fewer parallel lanes (profile [limits])")
    return fails, out
