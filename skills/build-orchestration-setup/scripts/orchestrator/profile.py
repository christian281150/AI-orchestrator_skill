# SPDX-License-Identifier: MIT
"""The personal profile: standing preferences reused across projects.

Two files, merged in this order (later wins, but only for values that are set):
  1. ~/.ai-orchestrator/profile.toml      (all projects)
  2. <repo>/.ai-orchestrator.toml         (this project)
An empty value ("", 0, [] ) means "ask me" - it never overrides a set value.
"""
from __future__ import annotations

import json
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


# ---------------------------------------------------------------- learn from a finished setup
CONFIG_RECORD = "docs/coordination/orchestration-config.md"
LIST_KEYS = {("tools", "build"), ("reserved", "actions")}
NUMBER_KEYS = {("defaults", "adoption_level"), ("defaults", "round_hours"), ("limits", "budget_guard_pct"),
               ("limits", "build_lanes_shared")}


def read_answers(record: Path) -> dict[str, str]:
    """Questionnaire item -> 'Chosen' cell from orchestration-config.md."""
    out = {}
    for line in Path(record).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.fullmatch(r"\d+[a-z]?(\.\d+)?", cells[0]) and cells[2]:
            out[cells[0]] = cells[2]
    return out


def _norm(s: str) -> str:
    return re.sub(r"[\s_-]+", " ", s.lower()).strip()


# the questionnaire's own option wording for values whose name differs from it
SYNONYMS = {("owner", "vocabulary"): {"plain": ("spell out", "not from an it", "non technical", "plain language")}}


def parse_answer(section: str, key: str, text: str):
    """The profile value a free-text answer maps to, or None if it is not unambiguous."""
    text = re.sub(r"\((?:recommended|empfohlen)\)", "", text, flags=re.I).strip()
    for value, phrases in SYNONYMS.get((section, key), {}).items():
        if any(ph in _norm(text) for ph in phrases):
            return value
    if (section, key) in NUMBER_KEYS:
        m = re.search(r"\d+(?:\.\d+)?", text)
        if not m:
            return None
        v = float(m.group(0))
        return int(v) if v.is_integer() else v
    allowed = ALLOWED.get((section, key))
    if allowed:
        hits = [a for a in allowed if isinstance(a, str) and re.search(rf"\b{re.escape(_norm(a))}\b", _norm(text))]
        return hits[0] if len(hits) == 1 else None
    if (section, key) in LIST_KEYS:
        items = [re.sub(r"\s*\(.*?\)\s*", " ", x).strip() for x in re.split(r"[,;]|\s\+\s", text)]
        return [x for x in items if x] or None
    value = re.split(r"\s+[(-]", text, maxsplit=1)[0].strip()
    return value if value and " " not in value else None     # one tool/model name, or not learned


def _toml(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_toml(x) for x in v) + "]"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return json.dumps(str(v), ensure_ascii=False)


def _set_line(text: str, section: str, key: str, value) -> str:
    """Replace `key = ...` inside [section], keeping the line's comment; append if missing."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(rf"\s*\[{re.escape(section)}\]", ln)), None)
    if start is None:
        return text.rstrip("\n") + f"\n\n[{section}]\n{key} = {_toml(value)}\n"
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"\s*\[", lines[i])), len(lines))
    for i in range(start + 1, end):
        m = re.match(rf"(\s*{re.escape(key)}\s*=\s*)(.*?)(\s+#.*)?$", lines[i])
        if m:
            new = f"{m.group(1)}{_toml(value)}"
            lines[i] = new + ((" " * max(1, 32 - len(new)) + m.group(3).strip()) if m.group(3) else "")
            return "\n".join(lines) + "\n"
    lines.insert(end, f"{key} = {_toml(value)}")
    return "\n".join(lines) + "\n"


def learn(record: Path, target: Path, write: bool = False) -> dict[str, list[str]]:
    """Plan (and with write=True apply) profile updates from a finished questionnaire.
    Only EMPTY profile values are filled; a value the owner set is never overwritten."""
    answers = read_answers(record)
    current = {}
    if target.exists():
        with open(target, "rb") as fh:
            current = tomllib.load(fh)
    plan: dict[str, list[str]] = {"add": [], "same": [], "kept_yours": [], "not_learned": []}
    updates = []
    for (section, key), item in ANSWERS.items():
        if item not in answers:
            continue
        value = parse_answer(section, key, answers[item])
        label = f"{item:<5} [{section}] {key}"
        if value is not None and check({section: {key: value}}):
            value = None                                          # parsed, but not an allowed value
        if value is None:
            plan["not_learned"].append(f"{label}: '{answers[item]}' is free text - set it by hand if you want it")
            continue
        have = current.get(section, {}).get(key)
        if not _is_set(have):
            plan["add"].append(f"{label} = {_toml(value)}")
            updates.append((section, key, value))
        elif have == value:
            plan["same"].append(f"{label} = {_toml(value)}")
        else:
            plan["kept_yours"].append(f"{label}: yours {_toml(have)} kept (this project chose {_toml(value)})")
    if write and updates:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(TEMPLATE, target)
        text = target.read_text(encoding="utf-8")
        for section, key, value in updates:
            text = _set_line(text, section, key, value)
        target.write_text(text, encoding="utf-8")
    return plan
