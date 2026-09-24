# SPDX-License-Identifier: MIT
"""Copy the kit (assets/templates + scripts) into a target repository. Never overwrites an
existing file unless --force; reports every file it wrote or skipped."""
from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]      # skills/build-orchestration-setup
TEXT_SUFFIXES = {".md", ".toml", ".json", ".py", ".txt", ".yml", ".yaml", ".sh", ".service", ".plist", ".ps1", ".cmd", ".bat", ""}
CRLF_SUFFIXES = {".ps1", ".cmd", ".bat"}   # Windows shells; everything else LF


def init(target: str | Path, values: dict[str, str], force: bool = False) -> list[str]:
    target = Path(target).resolve()
    target.mkdir(parents=True, exist_ok=True)
    report: list[str] = []
    for src_root, dst_root in ((SKILL_ROOT / "assets" / "templates", target), (SKILL_ROOT / "scripts", target / "tools")):
        for src in sorted(src_root.rglob("*")):
            if src.is_dir() or "__pycache__" in src.parts:
                continue
            dst = dst_root / src.relative_to(src_root)
            if dst.exists() and not force:
                report.append(f"skipped (exists): {dst.relative_to(target)}")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix in TEXT_SUFFIXES:
                text = src.read_text(encoding="utf-8")
                for k, v in values.items():
                    text = text.replace("{{" + k + "}}", v)
                nl = "\r\n" if src.suffix in CRLF_SUFFIXES else "\n"
                with open(dst, "w", encoding="utf-8", newline=nl) as fh:   # UTF-8, no BOM
                    fh.write(text)
            else:
                shutil.copy2(src, dst)
            if dst.parent.name == ".githooks" or dst.suffix == ".sh":
                dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            report.append(f"wrote: {dst.relative_to(target)}")
    if (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "config", "core.hooksPath", ".githooks"], check=False)
        report.append("git config core.hooksPath .githooks")
        if values.get("AUTHOR_NAME"):
            subprocess.run(["git", "-C", str(target), "config", "user.name", values["AUTHOR_NAME"]], check=False)
        if values.get("AUTHOR_EMAIL"):
            subprocess.run(["git", "-C", str(target), "config", "user.email", values["AUTHOR_EMAIL"]], check=False)
    else:
        report.append("NOTE: target is not a git repository yet - run `git init -b main`, then re-run init")
    return report


def unfilled(target: str | Path) -> list[str]:
    """Placeholders still to be filled by the setup session."""
    hits = []
    for f in Path(target).rglob("*"):
        if f.is_file() and f.suffix in {".md", ".toml"} and ".git" not in f.parts:
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if "{{" in line and "}}" in line:
                    hits.append(f"{f.relative_to(target)}:{n}: {line.strip()[:90]}")
    return hits

