#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Set the project version in every place that carries it. Usage: python tools/bump_version.py 1.4.0"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "build-orchestration-setup"
JSON_FILES = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"]


def bump(new: str, root: Path = ROOT) -> list[str]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        raise SystemExit(f"not a semantic version: {new}")
    skill = root / SKILL.relative_to(ROOT)
    changed = []
    for rel in JSON_FILES:
        p = root / rel
        data = json.loads(p.read_text(encoding="utf-8"))
        data["version"] = new
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed.append(rel)
    mk = root / ".claude-plugin/marketplace.json"
    data = json.loads(mk.read_text(encoding="utf-8"))
    for plugin in data["plugins"]:
        plugin["version"] = new
    mk.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    changed.append(".claude-plugin/marketplace.json")
    edits = [
        (skill / "SKILL.md", r'(\n  version: ")[^"]+(")', rf"\g<1>{new}\g<2>"),
        (skill / "scripts/orchestrator/__init__.py", r'(__version__ = ")[^"]+(")', rf"\g<1>{new}\g<2>"),
        (root / "CITATION.cff", r"(?m)^(version: ).+$", rf"\g<1>{new}"),
        (root / "CITATION.cff", r"(?m)^(date-released: ).+$", rf"\g<1>{date.today().isoformat()}"),
    ]
    for path, pattern, repl in edits:
        text = path.read_text(encoding="utf-8")
        new_text, n = re.subn(pattern, repl, text, count=1)
        if n != 1:
            raise SystemExit(f"version field not found in {path}")
        path.write_text(new_text, encoding="utf-8")
        changed.append(str(path.relative_to(root)))
    if not re.search(rf"(?m)^## {re.escape(new)} ", (root / "CHANGELOG.md").read_text(encoding="utf-8")):
        changed.append(f"REMINDER: add a '## {new} - {date.today().isoformat()}' entry to CHANGELOG.md")
    return changed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print("\n".join(bump(sys.argv[1])))
