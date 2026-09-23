# SPDX-License-Identifier: MIT
"""The unattended supervisor: one coordinator round after another, with provider
failover when a usage limit is hit.

Loop (each pass):
  1. Code or config changed since launch?  -> re-exec itself (rule changes land
     between rounds without anyone killing anything).
  2. STOP file present?                     -> exit cleanly.
  3. Best available provider with the 'coordinator' role (by priority):
       run one round -> classify result -> push -> pause -> next pass.
  4. No coordinator available (all limited):
       if enabled, start fallback BUILD lanes on providers that are still
       available, but only for items whose plan is already approved and that
       have a build brief. They work on their own branches; nothing reaches
       main until a 'merge' provider gates them in a later round.
       Then sleep until the earliest reset (or the re-probe interval).
Never kills a running round except at the hard cap (max_round_minutes):
killing a coordinator takes all of its running leads with it.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from . import board
from .config import Config, Provider, load
from .providers import VERDICT, ProviderState, detect_limit

PKG_DIR = Path(__file__).resolve().parent


# ----------------------------------------------------------------- helpers
def log(cfg: Config, msg: str) -> None:
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    with open(cfg.state_dir / "supervisor.log", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def write_state(cfg: Config, **kw) -> None:
    kw["updated"] = datetime.now().isoformat(timespec="seconds")
    (cfg.state_dir / "supervisor-state.json").write_text(json.dumps(kw, indent=2), encoding="utf-8")


def fingerprint(config_path: Path) -> dict[str, float]:
    files = list(PKG_DIR.glob("*.py")) + [config_path]
    return {str(f): f.stat().st_mtime for f in files if f.exists()}


def provider_env(p: Provider) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in set(p.strip_env)}
    env.update(p.env)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def fill(cmd: list[str], values: dict[str, str]) -> list[str]:
    return [re.sub(r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), c) for c in cmd]


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def run_logged(cmd: list[str], cwd: Path, env: dict, log_path: Path, timeout_s: float | None,
               detach: bool = False) -> subprocess.Popen | int:
    """Run cmd with stdout+stderr to log_path (UTF-8). Returns exit code, or the
    Popen when detach=True. Uses a new process group so the whole tree can be
    stopped at the hard cap."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(log_path, "ab")
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdout=fh, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, **kw)
    if detach:
        return proc
    try:
        return proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.wait()
        return -9
    finally:
        fh.close()


def git(cfg: Config, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cfg.root), *args], capture_output=True)


def merge_in_progress(cfg: Config) -> bool:
    gd = git(cfg, "rev-parse", "--git-dir").stdout.decode().strip()
    gdir = (cfg.root / gd) if gd and not Path(gd).is_absolute() else Path(gd)
    return any((gdir / n).exists() for n in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge"))


# ----------------------------------------------------------------- fallback lanes
def _alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True).stdout.decode(errors="replace")
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def markers_dir(cfg: Config) -> Path:
    d = cfg.state_dir / "fallback"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_markers(cfg: Config) -> list[dict]:
    out = []
    for f in sorted(markers_dir(cfg).glob("*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        m["_file"] = str(f)
        m["running"] = _alive(int(m.get("pid", 0))) if m.get("pid") else False
        out.append(m)
    return out


def eligible_for_fallback(cfg: Config) -> list[board.Row]:
    rows = board.parse(cfg.board)
    taken = {m["item"] for m in load_markers(cfg)}
    return [r for r in board.ready(rows)
            if r.status == "plan-approved" and not r.owner and r.id not in taken
            and (cfg.ledgers / r.id / "build-brief.md").exists()]


def start_fallback_lanes(cfg: Config, state: ProviderState, now: datetime | None = None) -> list[str]:
    started: list[str] = []
    for p in cfg.by_priority("build"):   # a limited coordinator is simply unavailable here
        if not p.build_command or not state.available(p, now):
            continue
        running = sum(1 for m in load_markers(cfg) if m["provider"] == p.name and m["running"])
        for row in eligible_for_fallback(cfg):
            if running >= p.max_parallel:
                break
            branch = f"feat/{row.lane or 'lane'}-{row.id}-{p.name}".lower()
            wt = cfg.worktrees_dir / f"{row.id}-{p.name}".lower()
            if not wt.exists():
                r = git(cfg, "worktree", "add", "-b", branch, str(wt), cfg.main_branch)
                if r.returncode != 0:
                    log(cfg, f"fallback {row.id}: worktree add failed: {r.stderr.decode(errors='replace').strip()}")
                    continue
            brief = cfg.ledgers / row.id / "build-brief.md"
            values = {"worktree": str(wt), "brief_file": str(brief), "item": row.id, "branch": branch,
                      "brief": brief.read_text(encoding="utf-8")}
            proc = run_logged(fill(p.build_command, values), wt, provider_env(p),
                              cfg.state_dir / "fallback" / "logs" / f"{row.id}-{p.name}.log", None, detach=True)
            (markers_dir(cfg) / f"{row.id}.json").write_text(json.dumps({
                "item": row.id, "provider": p.name, "pid": proc.pid, "branch": branch, "worktree": str(wt),
                "started": datetime.now().isoformat(timespec="seconds")}, indent=2), encoding="utf-8")
            running += 1
            started.append(row.id)
            log(cfg, f"fallback lane started: {row.id} on {p.name} (branch {branch}, pid {proc.pid})")
            time.sleep(0.2)
    return started


# ----------------------------------------------------------------- rounds
def round_prompt(cfg: Config, round_id: str, provider: Provider, window_end: datetime) -> str:
    base = cfg.session_prompt.read_text(encoding="utf-8")
    finished = [m for m in load_markers(cfg) if not m["running"]]
    running = [m for m in load_markers(cfg) if m["running"]]
    lines = [base, "", "---", "## Supervisor context for this round",
             f"- Round id: {round_id}; runtime: {provider.name}",
             f"- Refill lanes until {window_end:%Y-%m-%d %H:%M}, then start nothing new and let running leads finish.",
             f"- Finish with one line starting `{VERDICT}` (e.g. `{VERDICT} ok, merged 3, blocked 1`)."]
    if finished:
        lines.append("- FIRST, before any new dispatch: gate these fallback lanes built while you were "
                     "unavailable (review, run their verifies, merge or reject). Print one line per lane: "
                     "`GATED: <item> accepted|rejected <reason>`.")
        lines += [f"  - {m['item']} on branch {m['branch']} (built by {m['provider']})" for m in finished]
    if running:
        lines.append("- Still running fallback lanes (do not dispatch these items): "
                     + ", ".join(m["item"] for m in running))
    return "\n".join(lines) + "\n"


def archive_gated(cfg: Config, round_log: str) -> list[str]:
    gated = re.findall(r"^\s*GATED:\s*(\S+)\s+(accepted|rejected)", round_log, re.M | re.I)
    done_dir = markers_dir(cfg) / "gated"
    done_dir.mkdir(exist_ok=True)
    out = []
    for item, verdict in gated:
        f = markers_dir(cfg) / f"{item}.json"
        if f.exists():
            f.rename(done_dir / f"{item}.{verdict.lower()}.json")
            out.append(f"{item}:{verdict.lower()}")
    return out


def run_round(cfg: Config, p: Provider, state: ProviderState, now: datetime | None = None) -> str:
    now = now or datetime.now()
    round_id = now.strftime("%Y%m%d-%H%M%S") + f"-{p.name}"
    window_end = now + timedelta(minutes=cfg.window_minutes)
    prompt = round_prompt(cfg, round_id, p, window_end)
    rdir = cfg.state_dir / "rounds"
    rdir.mkdir(parents=True, exist_ok=True)
    pfile = rdir / f"{round_id}.prompt.md"
    pfile.write_text(prompt, encoding="utf-8")
    log_path = rdir / f"{round_id}.log"
    write_state(cfg, state=f"round {round_id} running", provider=p.name, round=round_id,
                window_end=window_end.isoformat(timespec="minutes"))
    log(cfg, f"round {round_id} start on {p.name}")
    code = run_logged(fill(p.round_command, {"prompt": prompt, "prompt_file": str(pfile), "round_id": round_id}),
                      cfg.root, provider_env(p), log_path, cfg.max_round_minutes * 60)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    verdict = detect_limit(p, code, text)
    gated = archive_gated(cfg, text)
    if gated:
        log(cfg, f"gated fallback lanes: {', '.join(gated)}")
    if verdict.limited:
        state.mark_limited(p.name, verdict.reset_at, verdict.reason)
        log(cfg, f"round {round_id}: {p.name} LIMITED ({verdict.reason}); until {state.limited_until(p.name)}")
        return "limited"
    state.clear(p.name)
    if code == -9:
        log(cfg, f"round {round_id}: hard cap {cfg.max_round_minutes} min reached, round stopped")
        return "timeout"
    if code != 0 or VERDICT not in text:
        log(cfg, f"round {round_id}: exit {code}, verdict {'present' if VERDICT in text else 'missing'}")
        return f"error:exit{code}"
    log(cfg, f"round {round_id}: ok - " + text[text.rfind(VERDICT):].splitlines()[0])
    return "ok"


def push_if_clean(cfg: Config) -> None:
    if not cfg.push_after_round:
        return
    if merge_in_progress(cfg):
        log(cfg, "push skipped: merge in progress")
        return
    if git(cfg, "remote").stdout.strip() == b"":
        return
    r = git(cfg, "push", "origin", cfg.main_branch)
    log(cfg, f"push {cfg.main_branch}: exit {r.returncode}")


# ----------------------------------------------------------------- main loop
def supervise(config_path: str, max_passes: int | None = None,
              sleep: Callable[[float], None] = time.sleep, reexec: bool = True) -> str:
    config_path = str(Path(config_path).resolve())
    cfg = load(config_path)
    state = ProviderState(cfg)
    fp = fingerprint(Path(config_path))
    failures: list[str] = []
    passes = 0
    log(cfg, f"supervisor start (pid {os.getpid()}) for {cfg.name}")
    while max_passes is None or passes < max_passes:
        passes += 1
        state.reload()
        if reexec and fingerprint(Path(config_path)) != fp:
            log(cfg, "code or config changed - re-exec between rounds")
            os.execv(sys.executable, [sys.executable, str(PKG_DIR.parent / "orch.py"), "supervise", config_path])
        if cfg.stop_file.exists():
            write_state(cfg, state="stopped (STOP file)")
            log(cfg, "STOP file present - exiting")
            return "stopped"
        coord = next((p for p in cfg.by_priority("coordinator") if state.available(p)), None)
        if coord is not None:
            result = run_round(cfg, coord, state)
            if result.startswith("error") or result == "timeout":
                failures.append(result)
                if len(failures) >= cfg.max_identical_failures and len(set(failures[-cfg.max_identical_failures:])) == 1:
                    msg = f"{cfg.max_identical_failures} identical failures ({result}) - stopping; see rounds/*.log"
                    (cfg.state_dir / "BLOCKED.txt").write_text(msg + "\n", encoding="utf-8")
                    write_state(cfg, state="blocked", reason=msg)
                    log(cfg, msg)
                    return "blocked"
            else:
                failures.clear()
            if result != "limited":
                push_if_clean(cfg)
                write_state(cfg, state="between rounds", last=result)
                sleep(cfg.pause_seconds)
            continue
        # every coordinator is limited
        started = start_fallback_lanes(cfg, state) if cfg.fallback_when_limited else []
        wake = state.earliest_reset()
        cap = datetime.now() + timedelta(minutes=cfg.reprobe_minutes)
        wake = min(wake, cap) if wake else cap
        write_state(cfg, state="all coordinators limited", wake=wake.isoformat(timespec="minutes"),
                    fallback_started=started, fallback_running=[m["item"] for m in load_markers(cfg) if m["running"]])
        log(cfg, f"no coordinator available; fallback started {started or 'none'}; sleeping until {wake:%H:%M}")
        sleep(max(5.0, (wake - datetime.now()).total_seconds()))
    return "max-passes"
