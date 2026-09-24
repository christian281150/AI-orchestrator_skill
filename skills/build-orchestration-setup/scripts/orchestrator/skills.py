# SPDX-License-Identifier: MIT
"""Skill inventory: what is installed for which engine, and which skills the agent
files name that are missing. Works before `init` (no config needed)."""
from __future__ import annotations

import re
from pathlib import Path

ENGINE_DIRS = {  # engine -> skill folders, relative to the repo root or the home directory
    "claude": [".claude/skills"],
    "codex/agents": [".agents/skills", ".codex/skills"],
}
AGENT_DIRS = [".claude/agents", ".codex/agents"]


def skill_dirs(root: Path, extra: list[str] | None = None) -> list[tuple[str, Path]]:
    out = []
    for engine, rels in ENGINE_DIRS.items():
        for rel in rels:
            out.append((engine, root / rel))
            out.append((engine, Path.home() / rel))
    for e in extra or []:
        out.append(("extra", Path(e).expanduser()))
    seen, uniq = set(), []
    for eng, d in out:
        if d.resolve() not in seen:
            seen.add(d.resolve())
            uniq.append((eng, d))
    return uniq


def _description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^description:\s*(.*)$", text, re.M)
    if not m:
        return ""
    val = m.group(1).strip()
    if val in ("|", ">", "|-", ">-", ""):   # YAML block scalar: take the indented lines that follow
        rest = text[m.end():].splitlines()[1:]
        val = " ".join(line.strip() for line in rest[:3] if line.startswith((" ", "\t")))
    return val.strip("'\"")[:140]


def inventory(root: Path, extra: list[str] | None = None) -> list[dict]:
    items = []
    for engine, d in skill_dirs(root, extra):
        if not d.exists():
            continue
        for sk in sorted(d.rglob("SKILL.md")):
            items.append({"name": sk.parent.name, "engine": engine, "where": str(sk.parent),
                          "description": _description(sk)})
    return items


def named_in_agents(root: Path) -> dict[str, list[str]]:
    """agent file -> skills it names (frontmatter `skills: [a, b]` or a YAML list)."""
    out = {}
    for rel in AGENT_DIRS:
        d = root / rel
        for f in sorted(d.glob("*.md")) if d.exists() else []:
            text = f.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
            m = re.search(r"^skills:\s*\[(.*?)\]", text, re.M) or re.search(r"^skills:\s*\n((?:\s+-\s+.+\n)+)", text, re.M)
            names = [s.strip(" -'\"\n") for s in re.split(r"[,\n]", m.group(1))] if m else []
            out[str(f.relative_to(root))] = [n for n in names if n]
    return out


def report(root: Path, extra: list[str] | None = None) -> tuple[list[str], int]:
    inv = inventory(root, extra)
    lines = [f"Installed skills ({len(inv)}):"]
    by_name: dict[str, list[str]] = {}
    for s in inv:
        by_name.setdefault(s["name"], []).append(s["engine"])
    for s in inv:
        lines.append(f"  {s['name']:<34} [{s['engine']}] {s['description']}")
    missing = 0
    named = named_in_agents(root)
    if named:
        lines.append("Named by agent files:")
        for f, names in named.items():
            for n in names:
                ok = n in by_name
                missing += not ok
                engines = f" (engines: {', '.join(sorted(set(by_name[n])))})" if ok else ""
                lines.append(f"  {'ok     ' if ok else 'MISSING'} {n:<30} <- {f}{engines}")
    lines.append(f"{missing} named skill(s) missing")
    return lines, missing
