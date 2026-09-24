# SPDX-License-Identifier: MIT
"""The personal profile: standing preferences reused across projects.

Two files, merged in this order (later wins, but only for values that are set):
  1. ~/.ai-orchestrator/profile.toml      (all projects)
  2. <repo>/.ai-orchestrator.toml         (this project)
An empty value ("", 0, [] ) means "ask me" - it never overrides a set value.
"""
from __future__ import annotations

import re
import shutil
import tomllib
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[2] / "assets" / "profile.toml"
HOME_FILE = Path("~/.ai-orchestrator/profile.toml")
PROJECT_FILE = ".ai-orchestrator.toml"

ALLOWED = {
    ("owner", "vocabulary"): {"plain", "technical"},
    ("defaults", "adoption_level"): {1, 2, 3, 4},
    ("defaults", "execution_home"): {"local", "cloud", "chat", "hybrid"},
    ("defaults", "involvement"): {"unattended", "approve-waves", "interactive"},
    ("defaults", "optimise_for"): {"quality-per-cost", "max-quality", "min-cost"},
    ("defaults", "autonomy"): {"decide-and-log", "ask"},
    ("defaults", "git_model"): {"feat-branches", "pr-per-lane", "trunk"},
    ("defaults", "commit_attribution"): {"owner-only", "ai-coauthor-allowed"},
    ("defaults", "planning_pace"): {"just-in-time", "ahead"},
    ("defaults", "fix_routing"): {"build-provider", "lead"},
    ("tools", "cloud_sessions"): {"on", "off"},
    ("tools", "chat_desk"): {"on", "off"},
    ("reporting", "dashboard"): {"twice-daily", "daily", "none"},
    ("reporting", "live_view"): {"on", "off"},
}
PERCENT_KEYS = {("limits", "budget_guard_pct"), ("limits", "memory_no_new_start_pct"), ("limits", "memory_refuse_pct")}
SECRET_HINTS = ("password", "token", "secret", "api_key", "apikey")

# which questionnaire item a profile value answers
ANSWERS = {
    ("owner", "vocabulary"): "1.3", ("defaults", "execution_home"): "2.1", ("defaults", "involvement"): "2.3",
    ("defaults", "adoption_level"): "2.4", ("tools", "lead"): "3.2", ("tools", "build"): "3.3",
    ("defaults", "round_hours"): "4.3", ("defaults", "optimise_for"): "5.1", ("models", "thinking"): "5.2",
    ("models", "doing"): "5.3", ("limits", "budget_guard_pct"): "5.4", ("tools", "chat_desk"): "7.4",
    ("tools", "cloud_sessions"): "7b.2", ("defaults", "planning_pace"): "7c.1", ("defaults", "fix_routing"): "7c.2",
    ("limits", "build_lanes_shared"): "7c.3", ("defaults", "autonomy"): "8.1", ("reserved", "actions"): "8.2",
    ("defaults", "git_model"): "8.3", ("defaults", "commit_attribution"): "8.4", ("reporting", "dashboard"): "9.2",
    ("reporting", "live_view"): "9.3",
}


def _is_set(v) -> bool:
    return v not in ("", 0, [], None)


def paths(repo: Path | None = None, home: Path | None = None) -> list[Path]:
    h = (home or Path.home()) / ".ai-orchestrator" / "profile.toml"
    out = [h]
    if repo is not None:
        out.append(Path(repo) / PROJECT_FILE)
    return out


def load(repo: Path | None = None, home: Path | None = None) -> tuple[dict, list[str]]:
    """Merged profile and the files it came from."""
    merged: dict = {}
    used = []
    for p in paths(repo, home):
        if not p.exists():
            continue
        with open(p, "rb") as fh:
            data = tomllib.load(fh)
        used.append(str(p))
        for section, values in data.items():
            if not isinstance(values, dict):
                continue
            target = merged.setdefault(section, {})
            for k, v in values.items():
                if _is_set(v) or k not in target:
                    target[k] = v
    return merged, used


def check(profile: dict) -> list[str]:
    problems = []
    for (section, key), allowed in ALLOWED.items():
        v = profile.get(section, {}).get(key)
        if _is_set(v) and v not in allowed:
            options = ", ".join(map(str, sorted(allowed, key=str)))
            problems.append(f"[{section}] {key} = {v!r} - allowed: {options} (or empty = ask)")
    for section, key in PERCENT_KEYS:
        v = profile.get(section, {}).get(key)
        if _is_set(v) and not (isinstance(v, (int, float)) and 50 <= v <= 100):
            problems.append(f"[{section}] {key} = {v!r} - use a percentage between 50 and 100 (or 0 = ask)")
    lim = profile.get("limits", {})
    if _is_set(lim.get("memory_no_new_start_pct")) and _is_set(lim.get("memory_refuse_pct")) \
            and lim["memory_no_new_start_pct"] >= lim["memory_refuse_pct"]:
        problems.append("[limits] memory_no_new_start_pct must be lower than memory_refuse_pct")
    for section, values in profile.items():
        for k, v in (values.items() if isinstance(values, dict) else []):
            if any(h in k.lower() for h in SECRET_HINTS) or (isinstance(v, str) and len(v) > 30 and " " not in v
                                                               and any(c.isdigit() for c in v) and "@" not in v
                                                               and "/" not in v):
                problems.append(f"[{section}] {k} looks like a secret - never put credentials in the profile")
    return problems


def answered(profile: dict) -> dict[str, str]:
    """Questionnaire item -> the profile's answer, for every item the profile settles."""
    out = {}
    for (section, key), item in ANSWERS.items():
        v = profile.get(section, {}).get(key)
        if _is_set(v):
            out[item] = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
    def order(item: str):
        m = re.match(r"(\d+)([a-z]?)\.?(\d*)", item)
        return (int(m.group(1)), m.group(2), int(m.group(3) or 0)) if m else (99, item, 0)
    return dict(sorted(out.items(), key=lambda kv: order(kv[0])))


def init(project_repo: Path | None = None, home: Path | None = None, force: bool = False) -> tuple[bool, str]:
    target = (Path(project_repo) / PROJECT_FILE) if project_repo else (home or Path.home()) / ".ai-orchestrator" / "profile.toml"
    if target.exists() and not force:
        return False, f"exists, not overwritten: {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, target)
    return True, f"created {target} - open it in any text editor and fill what you already know"
