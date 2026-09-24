# SPDX-License-Identifier: MIT
"""Ready-made usage readers: how full is each AI tool's allowance, read from the tool's OWN record.

Output contract (printed as JSON by `orch.py usage <tool>`, consumed via `usage_command`):
  {"status": "ok", "five_hour_pct": 42.0, "weekly_pct": 10.0, "five_hour_resets_at": "...", ...}
  {"status": "no-data", "reason": "..."}      nothing recorded yet -> log-tail detection decides, as before
  {"status": "unreadable", "reason": "..."}   a record exists but its format is not understood ->
                                               the provider starts NO new work (fail closed) until it reads again
A window whose reset time has passed counts as 0 %.

Vendor specifics live here, each with the CLI version it was checked against (VERIFIED_WITH).
Formats change between versions: the tests pin sample records, `preflight` shows the live reading.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path

VERIFIED_WITH = {
    "claude": "Claude Code 2.1.281 - statusline input `rate_limits` and stream-json `rate_limit_event`",
    "codex": "Codex CLI session records `rate_limits` (format observed in 2026 builds; re-check on your version)",
}
USAGE_DIR = Path("~/.ai-orchestrator/usage")


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(UTC)


def _ts(epoch) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(epoch), UTC)
    except (TypeError, ValueError, OSError):
        return None


def _result(tool: str, source: str, captured: datetime, windows: dict, now: datetime) -> dict:
    """windows: {"five_hour": (pct, resets_at|None), "weekly": (...)} -> contract dict."""
    out = {"status": "ok", "reader": tool, "source": source, "verified_with": VERIFIED_WITH[tool],
           "captured_at": captured.isoformat(timespec="seconds"),
           "age_minutes": max(0, round((now - captured).total_seconds() / 60))}
    for name, (pct, reset) in windows.items():
        key = "weekly" if name == "weekly" else "five_hour"
        if reset is not None and reset <= now:
            pct = 0.0                                    # window has reset since the reading
        out[f"{key}_pct"] = round(float(pct), 1)
        out[f"{key}_resets_at"] = reset.isoformat(timespec="seconds") if reset else None
    return out


# ---------------------------------------------------------------- Claude Code
def _claude_statusline_windows(data: dict) -> dict | None:
    rl = data.get("rate_limits")
    if rl is None:
        return None
    if not isinstance(rl, dict):
        raise ValueError("rate_limits is not an object")
    wins = {}
    for src, dst in (("five_hour", "five_hour"), ("seven_day", "weekly")):
        w = rl.get(src)
        if w is None:
            continue
        pct = w.get("used_percentage") if isinstance(w, dict) else None
        if not isinstance(pct, (int, float)):
            raise ValueError(f"rate_limits.{src}.used_percentage missing or not a number")
        wins[dst] = (float(pct), _ts(w.get("resets_at")))
    if not wins:
        raise ValueError("rate_limits has no five_hour / seven_day window")
    return wins


def capture_claude(stdin_text: str, usage_dir: Path | None = None, now: datetime | None = None) -> str:
    """Statusline hook: Claude Code pipes its status JSON in; keep the rate limits, print a short line."""
    now = _now(now)
    d = Path(usage_dir or USAGE_DIR).expanduser()
    try:
        data = json.loads(stdin_text or "{}")
        wins = _claude_statusline_windows(data)
    except (json.JSONDecodeError, ValueError, AttributeError):
        return "usage: unreadable"
    if not wins:
        return ""
    d.mkdir(parents=True, exist_ok=True)
    rec = {"captured_at": now.isoformat(timespec="seconds"),
           "rate_limits": data["rate_limits"]}
    tmp = d / "claude.json.tmp"
    tmp.write_text(json.dumps(rec), encoding="utf-8")
    os.replace(tmp, d / "claude.json")
    parts = [f"5h {wins['five_hour'][0]:.0f}%" if "five_hour" in wins else "",
             f"week {wins['weekly'][0]:.0f}%" if "weekly" in wins else ""]
    return " · ".join(p for p in parts if p)


def _claude_events(log: Path) -> list[dict]:
    events = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if '"rate_limit_event"' not in line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "rate_limit_event":
            events.append(obj.get("rate_limit_info"))
    return events


def _claude_event_windows(info) -> dict:
    if not isinstance(info, dict):
        raise ValueError("rate_limit_info is not an object")
    wins = {}
    uw = info.get("unifiedWindows")
    if isinstance(uw, dict):
        for src, dst in (("five_hour", "five_hour"), ("seven_day", "weekly")):
            w = uw.get(src)
            if isinstance(w, dict) and isinstance(w.get("utilization"), (int, float)):
                wins[dst] = (float(w["utilization"]) * 100, _ts(w.get("resetsAt")))
    kind = info.get("rateLimitType")
    dst = {"five_hour": "five_hour", "seven_day": "weekly"}.get(kind or "")
    if dst and dst not in wins:
        if info.get("status") == "rejected":
            wins[dst] = (100.0, _ts(info.get("resetsAt")))
        elif isinstance(info.get("utilization"), (int, float)):
            wins[dst] = (float(info["utilization"]) * 100, _ts(info.get("resetsAt")))
    if not wins and info.get("status") not in ("allowed", "allowed_warning", "rejected"):
        raise ValueError("rate_limit_info has no status and no window")
    return wins


def read_claude(usage_dir: Path | None = None, logs: list[Path] | None = None, now: datetime | None = None) -> dict:
    now = _now(now)
    candidates: list[tuple[datetime, str, dict]] = []
    cap = Path(usage_dir or USAGE_DIR).expanduser() / "claude.json"
    if cap.exists():
        try:
            rec = json.loads(cap.read_text(encoding="utf-8"))
            wins = _claude_statusline_windows(rec)
            when = datetime.fromisoformat(rec["captured_at"])
        except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError) as e:
            return {"status": "unreadable", "reader": "claude", "reason": f"{cap}: {e}"}
        if wins:
            candidates.append((when, "statusline", wins))
    files: list[Path] = []
    for d in logs or []:
        d = Path(d)
        files += [d] if d.is_file() else sorted(d.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    for f in files:
        events = _claude_events(f)
        if not events:
            continue
        try:
            wins = _claude_event_windows(events[-1])
        except ValueError as e:
            return {"status": "unreadable", "reader": "claude", "reason": f"{f.name}: {e}"}
        if wins:
            candidates.append((datetime.fromtimestamp(f.stat().st_mtime, UTC), "stream-json", wins))
    if not candidates:
        return {"status": "no-data", "reader": "claude",
                "reason": "no statusline capture and no stream-json rate_limit_event yet"}
    when, source, wins = max(candidates, key=lambda c: c[0])
    return _result("claude", source, when, wins, now)


# ---------------------------------------------------------------- Codex
def _codex_windows(rl) -> dict:
    if not isinstance(rl, dict):
        raise ValueError("rate_limits is not an object")
    wins = {}
    for slot, default in (("primary", "five_hour"), ("secondary", "weekly")):
        w = rl.get(slot)
        if w is None:
            continue
        if not isinstance(w, dict) or not isinstance(w.get("used_percent"), (int, float)):
            raise ValueError(f"rate_limits.{slot}.used_percent missing or not a number")
        minutes = w.get("window_minutes")
        name = default if not isinstance(minutes, (int, float)) else ("five_hour" if minutes <= 360 else "weekly")
        wins[name] = (float(w["used_percent"]), w.get("resets_at"), w.get("resets_in_seconds"))
    if not wins:
        raise ValueError("rate_limits has neither primary nor secondary")
    return wins


def read_codex(codex_home: str | Path | None = None, now: datetime | None = None) -> dict:
    now = _now(now)
    home = Path(codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    if not home.exists():
        return {"status": "no-data", "reader": "codex", "reason": f"no session records in {home}"}
    files = sorted(home.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    for f in files:
        for line in reversed(f.read_text(encoding="utf-8", errors="replace").splitlines()):
            if '"rate_limits"' not in line:
                continue
            try:
                obj = json.loads(line)
                rl = _find(obj, "rate_limits")
                if rl is None:                        # e.g. API-key login: no plan windows reported
                    continue
                raw = _codex_windows(rl)
            except (json.JSONDecodeError, ValueError) as e:
                return {"status": "unreadable", "reader": "codex", "reason": f"{f.name}: {e}"}
            try:
                when = datetime.fromisoformat(str(obj.get("timestamp", "")).replace("Z", "+00:00"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=UTC)
            except ValueError:
                when = datetime.fromtimestamp(f.stat().st_mtime, UTC)
            wins = {}
            for name, (pct, at, in_s) in raw.items():
                reset = _ts(at) if at is not None else None
                if reset is None and isinstance(in_s, (int, float)):
                    reset = _ts(when.timestamp() + in_s)
                wins[name] = (pct, reset)
            return _result("codex", "session-record", when, wins, now)
    return {"status": "no-data", "reader": "codex", "reason": "no rate_limits in the newest session records"}


def _find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find(v, key)
            if r is not None:
                return r
    return None


READERS = {"claude": read_claude, "codex": read_codex}
