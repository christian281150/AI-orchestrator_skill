# SPDX-License-Identifier: MIT
"""Provider availability: usage-limit detection, reset parsing, and a small state file.

Lesson built in: a limit is decided by the provider's OWN record when one exists.
Text matching is a fallback, restricted to the last N lines of the log, and only
counts when the run exited non-zero or never printed its ROUND RESULT verdict.
(Matching anywhere in a log produced a false 'limit hit' when the agent had
merely read a board line quoting an old limit message.)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .config import Config, Provider

VERDICT = "ROUND RESULT:"
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DEFAULT_LIMIT_PATTERNS = [
    r"usage limit reached", r"limit (?:will )?reset", r"rate[_ ]limit(?:ed| reached| exceeded)",
    r"you've hit your (?:usage )?limit", r"try again (?:at|in)", r"quota exceeded",
]


@dataclass
class LimitVerdict:
    limited: bool
    reason: str
    reset_at: datetime | None = None


def parse_reset(text: str, now: datetime | None = None) -> datetime | None:
    now = now or datetime.now()
    for m in re.finditer(r"\b(?:in|after)\s+(?:(\d+)\s*h(?:ours?|rs?)?)?\s*(?:(\d+)\s*m(?:in(?:utes?|s)?)?)?\b", text, re.I):
        if m.group(1) or m.group(2):
            return now + timedelta(hours=int(m.group(1) or 0), minutes=int(m.group(2) or 0))
    m = re.search(r"(?:resets?|try again)\s+(?:at\s+)?(?:on\s+)?(?:([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(?:at\s+)?)?"
                  r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text, re.I)
    if m:
        mon, day = (m.group(1) or "").lower()[:3], m.group(2)
        h, mi, ampm = int(m.group(3)), int(m.group(4) or 0), (m.group(5) or "").lower()
        if ampm == "pm" and h < 12:
            h += 12
        if ampm == "am" and h == 12:
            h = 0
        if h > 23 or mi > 59:
            return None
        if mon in MONTHS and day:
            cand = datetime(now.year, MONTHS[mon], int(day), h, mi)
            return cand if cand > now else cand.replace(year=now.year + 1)
        cand = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        if cand <= now:
            cand += timedelta(days=1)
        return cand
    return None


def codex_used_percent(codex_home: str | None = None) -> float | None:
    """Newest Codex session record's rate-limit usage (max of its windows), or None.
    Format observed in 2026 CLI builds; verify on your version (`preflight` reports it)."""
    home = Path(codex_home or os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    if not home.exists():
        return None
    files = sorted(home.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    for f in files:
        for line in reversed(f.read_text(encoding="utf-8", errors="replace").splitlines()):
            if "rate_limits" not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            rl = _find_key(obj, "rate_limits")
            if isinstance(rl, dict):
                vals = [w.get("used_percent") for w in rl.values() if isinstance(w, dict)]
                vals = [float(v) for v in vals if isinstance(v, (int, float))]
                if vals:
                    return max(vals)
    return None


def _find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_key(v, key)
            if r is not None:
                return r
    return None


def detect_limit(p: Provider, exit_code: int | None, log_text: str, now: datetime | None = None) -> LimitVerdict:
    if p.native_limit == "codex_rollout":
        used = codex_used_percent()
        if used is not None:
            if used >= p.native_limit_threshold:
                return LimitVerdict(True, f"native record: {used:.0f}% used", None)
            return LimitVerdict(False, f"native record: {used:.0f}% used (decides; log text ignored)")
    tail = "\n".join(log_text.splitlines()[-p.limit_tail_lines:])
    has_verdict = VERDICT in log_text
    if exit_code == 0 and has_verdict:
        return LimitVerdict(False, "exit 0 with verdict")
    for pat in (p.limit_patterns or DEFAULT_LIMIT_PATTERNS):
        m = re.search(pat, tail, re.I)
        if m:
            line = next((ln for ln in tail.splitlines() if re.search(pat, ln, re.I)), m.group(0))
            return LimitVerdict(True, f"log tail: {line.strip()[:160]}", parse_reset(line, now))
    return LimitVerdict(False, "no limit signal")


def usage(p: Provider, cwd: Path | None = None) -> dict:
    """Run the provider's usage_command (if any) and return its JSON, e.g.
    {"five_hour_pct": 42, "weekly_pct": 10, "credit_left": 233.5}. {} when no command is configured.
    A command that fails or prints no JSON object yields {"status": "unreadable", ...}."""
    if not p.usage_command:
        return {}
    try:
        cmd = [sys.executable if x == "{python}" else x for x in p.usage_command]
        r = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=60)
        data = json.loads(r.stdout.decode("utf-8", "replace") or "null")
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"status": "unreadable", "reason": f"usage_command failed: {e}"}
    except json.JSONDecodeError:
        return {"status": "unreadable", "reason": "usage_command printed no JSON"}
    return data if isinstance(data, dict) else {"status": "unreadable", "reason": "usage_command printed no JSON object"}


def over_threshold(p: Provider, u: dict) -> str:
    if u.get("status") == "unreadable" and p.usage_fail_closed:
        return f"usage unreadable ({u.get('reason', '?')}) - no new work until it reads again"
    for key in ("five_hour_pct", "weekly_pct"):
        v = u.get(key)
        if isinstance(v, (int, float)) and v >= p.native_limit_threshold:
            return f"usage meter {key}={v:.0f}%"
    return ""


class ProviderState:
    """limited_until per provider, persisted in <state_dir>/providers.json."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.path = cfg.state_dir / "providers.json"
        self.reload()

    def reload(self) -> None:
        """Re-read from disk each pass, so an operator can clear a limit by editing the file."""
        self.data: dict[str, dict] = {}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def mark_limited(self, name: str, until: datetime | None, reason: str, now: datetime | None = None) -> None:
        now = now or datetime.now()
        until = until or now + timedelta(minutes=self.cfg.reprobe_minutes)
        self.data[name] = {"limited_until": until.isoformat(timespec="seconds"), "reason": reason}
        self.save()

    def clear(self, name: str) -> None:
        if self.data.pop(name, None) is not None:
            self.save()

    def limited_until(self, name: str) -> datetime | None:
        v = self.data.get(name, {}).get("limited_until")
        return datetime.fromisoformat(v) if v else None

    def available(self, p: Provider, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        until = self.limited_until(p.name)
        if until and until > now:
            return False
        if p.status_command:
            r = subprocess.run(p.status_command, capture_output=True, cwd=self.cfg.root)
            if r.returncode != 0:
                self.mark_limited(p.name, None, "status probe non-zero", now)
                return False
        if p.native_limit == "codex_rollout":
            used = codex_used_percent()
            if used is not None and used >= p.native_limit_threshold:
                self.mark_limited(p.name, None, f"native record {used:.0f}%", now)
                return False
        reason = over_threshold(p, usage(p, self.cfg.root))
        if reason:
            self.mark_limited(p.name, None, reason, now)
            return False
        return True

    def earliest_reset(self, now: datetime | None = None) -> datetime | None:
        now = now or datetime.now()
        times = [self.limited_until(p.name) for p in self.cfg.providers if p.enabled]
        times = [t for t in times if t and t > now]
        return min(times) if times else None
