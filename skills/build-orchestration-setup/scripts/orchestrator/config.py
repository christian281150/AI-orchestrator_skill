# SPDX-License-Identifier: MIT
"""Load and validate orchestration.toml. Standard library only (Python >= 3.11)."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("open", "ready", "planning", "plan-approved", "in-progress",
            "review", "done", "blocked", "parked")
PRIORITIES = ("P1", "P2", "P3")
ROLES = ("coordinator", "plan", "review", "build", "merge")


@dataclass
class Provider:
    name: str
    priority: int
    roles: list[str]
    round_command: list[str] = field(default_factory=list)   # runs a coordinator round
    build_command: list[str] = field(default_factory=list)   # builds one approved plan
    status_command: list[str] = field(default_factory=list)  # optional probe; exit 0 = available
    limit_patterns: list[str] = field(default_factory=list)
    limit_tail_lines: int = 30
    native_limit: str = ""            # "" | "codex_rollout"
    native_limit_threshold: float = 97.0
    max_parallel: int = 1
    strip_env: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    kind: str = "local"               # local CLI | cloud (remote sessions, own credit) | chat (copy-paste desk)
    plan_command: list[str] = field(default_factory=list)   # plans one item ({item} {worktree} {branch} {todo})
    usage_command: list[str] = field(default_factory=list)  # prints JSON: five_hour_pct, weekly_pct, credit_left
    restart_max_per_day: int = 3

    def can(self, role: str) -> bool:
        return self.enabled and role in self.roles


@dataclass
class Keeper:
    interval_minutes: int = 10
    queue_low_watermark: int = 5       # approved plans waiting; below this, planners are topped up
    cloud_steady: int = 1              # cloud planners while the lead provider has capacity
    cloud_accelerate_max: int = 3      # cloud sessions in total once the lead provider is limited
    handback_below_pct: float = 50.0   # lead usage (5-hour) below this -> accelerate sessions hand back
    cloud_credit_floor: float = 5.0    # never launch a cloud session below this credit
    idle_planning: bool = True         # an idle build provider may plan one safe open item
    unsafe_lanes: list[str] = field(default_factory=lambda: ["db", "infra", "security"])
    handback_file: str = "docs/coordination/cloud-handback.txt"


@dataclass
class Config:
    root: Path
    name: str
    main_branch: str
    board: Path
    decisions: Path
    session_prompt: Path
    ledgers: Path
    stop_file: Path
    state_dir: Path
    worktrees_dir: Path
    id_pattern: str
    window_minutes: int
    max_round_minutes: int
    pause_seconds: int
    reprobe_minutes: int
    push_after_round: bool
    fallback_when_limited: bool
    max_identical_failures: int
    author_name: str
    author_email: str
    forbid_trailers: list[str]
    forbid_paths: list[str]
    required_env: list[str]
    redact_terms: list[str]
    providers: list[Provider]
    keeper: Keeper = field(default_factory=Keeper)

    def provider(self, name: str) -> Provider:
        for p in self.providers:
            if p.name == name:
                return p
        raise KeyError(name)

    def by_priority(self, role: str) -> list[Provider]:
        return sorted((p for p in self.providers if p.can(role)), key=lambda p: p.priority)


def _path(root: Path, value: str) -> Path:
    p = Path(os.path.expandvars(os.path.expanduser(value)))
    return p if p.is_absolute() else (root / p)


def load(path: str | os.PathLike) -> Config:
    path = Path(path).resolve()
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    proj = raw.get("project", {})
    root = _path(path.parent, proj.get("repo", "."))
    name = proj.get("name", root.name)
    rounds = raw.get("rounds", {})
    git = raw.get("git", {})
    safety = raw.get("safety", {})
    providers = []
    for p in raw.get("providers", []):
        bad = [r for r in p.get("roles", []) if r not in ROLES]
        if bad:
            raise ValueError(f"provider {p.get('name')}: unknown roles {bad}")
        providers.append(Provider(
            name=p["name"], priority=int(p.get("priority", 99)), roles=list(p.get("roles", [])),
            round_command=list(p.get("round_command", [])), build_command=list(p.get("build_command", [])),
            status_command=list(p.get("status_command", [])), limit_patterns=list(p.get("limit_patterns", [])),
            limit_tail_lines=int(p.get("limit_tail_lines", 30)), native_limit=p.get("native_limit", ""),
            native_limit_threshold=float(p.get("native_limit_threshold", 97.0)),
            max_parallel=int(p.get("max_parallel", 1)), strip_env=list(p.get("strip_env", [])),
            env={k: str(v) for k, v in p.get("env", {}).items()},
            kind=p.get("kind", "local"), plan_command=list(p.get("plan_command", [])),
            usage_command=list(p.get("usage_command", [])), restart_max_per_day=int(p.get("restart_max_per_day", 3)),
            enabled=bool(p.get("enabled", True))))
    bad_kind = [p.name for p in providers if p.kind not in ("local", "cloud", "chat")]
    if bad_kind:
        raise ValueError(f"providers with unknown kind (local | cloud | chat): {bad_kind}")
    if not any(p.can("coordinator") for p in providers):
        raise ValueError("no enabled provider has the 'coordinator' role")
    if not any(p.can("merge") for p in providers):
        raise ValueError("no enabled provider has the 'merge' role - something must gate main")
    state_default = f"~/.agent-build/{name}"
    return Config(
        root=root, name=name, main_branch=proj.get("main_branch", "main"),
        board=_path(root, proj.get("board", "docs/coordination/PROGRESS.md")),
        decisions=_path(root, proj.get("decisions", "docs/coordination/decisions-log.md")),
        session_prompt=_path(root, proj.get("session_prompt", "docs/coordination/SESSION-PROMPT.md")),
        ledgers=_path(root, proj.get("ledgers", "docs/coordination/ledgers")),
        stop_file=_path(root, proj.get("stop_file", "docs/coordination/STOP")),
        state_dir=_path(root, proj.get("state_dir", state_default)),
        worktrees_dir=_path(root, proj.get("worktrees_dir", f"../{name}-wt")),
        id_pattern=proj.get("id_pattern", r"^(W\d+-\d+|F\d+)$"),
        window_minutes=int(rounds.get("window_minutes", 180)),
        max_round_minutes=int(rounds.get("max_round_minutes", 330)),
        pause_seconds=int(rounds.get("pause_seconds", 30)),
        reprobe_minutes=int(rounds.get("reprobe_minutes", 15)),
        push_after_round=bool(rounds.get("push_after_round", True)),
        fallback_when_limited=bool(rounds.get("fallback_when_limited", True)),
        max_identical_failures=int(rounds.get("max_identical_failures", 3)),
        author_name=git.get("author_name", ""), author_email=git.get("author_email", ""),
        forbid_trailers=list(git.get("forbid_trailers", [])),
        forbid_paths=list(safety.get("forbid_paths", ["*.har", "*.pem", ".env", ".env.*", "data/**"])),
        required_env=list(safety.get("required_env", [])),
        redact_terms=list(safety.get("redact_terms", [])),
        providers=providers,
        keeper=Keeper(**{k: v for k, v in raw.get("keeper", {}).items() if k in Keeper.__dataclass_fields__}),
    )
