# SPDX-License-Identifier: MIT
"""The keeper: a short, idempotent pass run by the OS scheduler every few minutes (default 10),
independent of whether a coordinator round is running. It keeps every provider busy with the work
it is allowed to do - and nothing else:

1. Restart build/plan lanes that stopped on a usage limit (same command, max N per item per day).
2. Build lanes: when no round runs or the lead provider is limited, start build lanes for
   `plan-approved` rows with a build brief (same rule as the supervisor's fallback).
3. Idle planning: a build provider with nothing to build may PLAN one safe open item (never a lane in
   `unsafe_lanes`, never one already planned). Its plan is reconciled by the lead later (see gap.py).
4. Cloud planners (kind = "cloud", own credit):
   - steady:     `cloud_steady` sessions while the lead has capacity and approved plans run low;
   - accelerate: up to `cloud_accelerate_max` once the lead provider is limited;
   - handback:   when the lead is back below `handback_below_pct`, write HANDBACK so extra sessions
                 finish their current item and return the rest;
   - never below `cloud_credit_floor`.
Nothing here merges, and nothing writes to the repository except the HANDBACK file (via safe-commit).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import board
from .config import Config, Provider
from .providers import ProviderState, detect_limit, usage
from .safe_commit import safe_commit
from .supervisor import (_alive, eligible_for_fallback, fill, git, load_markers, log, markers_dir, provider_env,
                         run_logged, start_fallback_lanes)


def round_running(cfg: Config) -> bool:
    f = cfg.state_dir / "supervisor-state.json"
    if not f.exists():
        return False
    st = json.loads(f.read_text(encoding="utf-8"))
    return str(st.get("state", "")).startswith("round") and _alive(int(st.get("supervisor_pid", 0) or 0))


def _write_marker(path: Path, data: dict) -> None:
    data = {k: v for k, v in data.items() if not k.startswith("_") and k != "running"}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def restart_stopped(cfg: Config, state: ProviderState, today: str) -> list[str]:
    done = []
    for m in load_markers(cfg):
        if m["running"] or not m.get("command") or not m.get("log"):
            continue
        try:
            p = cfg.provider(m["provider"])
        except KeyError:
            continue
        text = Path(m["log"]).read_text(encoding="utf-8", errors="replace") if Path(m["log"]).exists() else ""
        if not detect_limit(p, None, text).limited:
            continue                                   # finished or failed for another reason: the gate decides
        restarts = m.get("restarts", {})
        if restarts.get(today, 0) >= p.restart_max_per_day or not state.available(p):
            continue
        proc = run_logged(m["command"], Path(m.get("worktree") or cfg.root), provider_env(p), Path(m["log"]), None,
                          detach=True)
        restarts[today] = restarts.get(today, 0) + 1
        m.update(pid=proc.pid, restarts=restarts)
        _write_marker(Path(m["_file"]), m)
        done.append(f"restarted {m.get('item') or m.get('items')} on {p.name} ({restarts[today]}/{p.restart_max_per_day} today)")
    return done


def planning_candidates(cfg: Config, exclude: set[str]) -> list[board.Row]:
    rows = board.parse(cfg.board)
    taken = exclude | {i for m in load_markers(cfg) for i in ([m.get("item")] + m.get("items", [])) if i}
    return [r for r in board.ready(rows)
            if r.status in ("open", "ready") and not r.owner and r.prio in ("P1", "P2", "")
            and r.lane not in cfg.keeper.unsafe_lanes and r.id not in taken
            and not (cfg.ledgers / r.id / "plan.md").exists()]


def idle_planning(cfg: Config, state: ProviderState) -> list[str]:
    if not cfg.keeper.idle_planning or eligible_for_fallback(cfg):
        return []
    done = []
    for p in cfg.by_priority("build"):
        if p.kind != "local" or not p.plan_command or not state.available(p):
            continue
        if sum(1 for m in load_markers(cfg) if m["provider"] == p.name and m["running"]) >= p.max_parallel:
            continue
        cands = planning_candidates(cfg, set())
        if not cands:
            break
        row = cands[0]
        branch = f"feat/{row.lane or 'lane'}-{row.id}-{p.name}-plan".lower()
        wt = cfg.worktrees_dir / f"{row.id}-{p.name}-plan".lower()
        if not wt.exists() and git(cfg, "worktree", "add", "-b", branch, str(wt), cfg.main_branch).returncode != 0:
            continue
        values = {"item": row.id, "worktree": str(wt), "branch": branch, "todo": row.id}
        logf = cfg.state_dir / "fallback" / "logs" / f"{row.id}-{p.name}-plan.log"
        cmd = fill(p.plan_command, values)
        proc = run_logged(cmd, wt, provider_env(p), logf, None, detach=True)
        _write_marker(markers_dir(cfg) / f"{row.id}.json", {
            "item": row.id, "kind": "plan", "provider": p.name, "pid": proc.pid, "branch": branch, "worktree": str(wt),
            "command": cmd, "log": str(logf), "started": datetime.now().isoformat(timespec="seconds")})
        done.append(f"idle planning: {row.id} on {p.name} (plan only, reconciled by the lead later)")
        break                                          # one at a time
    return done


def cloud_planners(cfg: Config, state: ProviderState, lead: Provider, lead_limited: bool) -> list[str]:
    k = cfg.keeper
    done = []
    queue = len(eligible_for_fallback(cfg))
    for p in [p for p in cfg.providers if p.enabled and p.kind == "cloud" and p.plan_command]:
        running = [m for m in load_markers(cfg) if m["provider"] == p.name and m["running"]]
        u = usage(p, cfg.root)
        credit = u.get("credit_left")
        if lead_limited:
            target = k.cloud_accelerate_max
        else:
            target = k.cloud_steady if queue < k.queue_low_watermark else 0
            lead_u = usage(lead, cfg.root).get("five_hour_pct")
            if len(running) > k.cloud_steady and isinstance(lead_u, (int, float)) and lead_u < k.handback_below_pct:
                done += handback(cfg, f"{lead.name} back at {lead_u:.0f}% (5-hour)")
        if isinstance(credit, (int, float)) and credit < k.cloud_credit_floor:
            if len(running) < target:
                done.append(f"cloud {p.name}: credit {credit} below floor {k.cloud_credit_floor} - not launching")
            continue
        cands = [r.id for r in planning_candidates(cfg, set())]
        n = min(max(0, target - len(running)), len(cands))
        for i in range(n):                         # split the candidates evenly into n to-do lists
            todo = cands[i::n][:3]
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            logf = cfg.state_dir / "fallback" / "logs" / f"cloud-{p.name}-{stamp}.log"
            cmd = fill(p.plan_command, {"todo": ", ".join(todo), "item": todo[0]})
            proc = run_logged(cmd, cfg.root, provider_env(p), logf, None, detach=True)
            _write_marker(markers_dir(cfg) / f"cloud-{p.name}-{stamp}.json", {
                "items": todo, "kind": "cloud", "provider": p.name, "pid": proc.pid, "command": cmd, "log": str(logf),
                "mode": "accelerate" if lead_limited else "steady", "started": datetime.now().isoformat(timespec="seconds")})
            done.append(f"cloud planner on {p.name} ({'accelerate' if lead_limited else 'steady'}): {', '.join(todo)}")
    return done


def handback(cfg: Config, reason: str) -> list[str]:
    f = cfg.root / cfg.keeper.handback_file
    if f.exists() and f.read_text(encoding="utf-8").startswith("HANDBACK"):
        return []
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"HANDBACK {datetime.now().isoformat(timespec='minutes')} - {reason}\n"
                 "Cloud sessions in accelerate mode: finish the current item, hand the rest back, stop.\n",
                 encoding="utf-8")
    ok, msg = safe_commit(cfg.root, "chore(keeper): cloud handback", [cfg.keeper.handback_file], wait_s=60)
    return [f"HANDBACK written ({reason}); commit: {msg}"]


def run_once(cfg: Config) -> list[str]:
    state = ProviderState(cfg)
    today = datetime.now().date().isoformat()
    leads = cfg.by_priority("coordinator")
    lead = leads[0]
    lead_limited = not state.available(lead)
    running_round = round_running(cfg)
    actions = restart_stopped(cfg, state, today)
    if lead_limited or not running_round:
        actions += [f"build lane started: {i}" for i in start_fallback_lanes(cfg, state)]
    actions += idle_planning(cfg, state)
    actions += cloud_planners(cfg, state, lead, lead_limited)
    summary = {"at": datetime.now().isoformat(timespec="seconds"), "lead": lead.name, "lead_limited": lead_limited,
               "round_running": running_round, "actions": actions}
    (cfg.state_dir / "keeper-state.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for a in actions:
        log(cfg, f"keeper: {a}")
    return actions
