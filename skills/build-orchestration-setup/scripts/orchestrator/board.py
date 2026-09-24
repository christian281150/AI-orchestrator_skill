# SPDX-License-Identifier: MIT
"""The board (PROGRESS.md): parse, validate, pick ready work, measure progress,
and the 'never do a task twice' check.

Board format: the first markdown table whose header has an ID and a Status column.
Recognised columns (case-insensitive, order free):
  ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import PRIORITIES, STATUSES

COMMIT_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
_ALIASES = {
    "id": "id", "item": "item", "title": "item", "prio": "prio", "priority": "prio",
    "wave": "wave", "lane": "lane", "est h": "est", "est": "est", "estimate": "est",
    "deps": "deps", "depends on": "deps", "status": "status", "owner": "owner",
    "next": "next", "next / blocker": "next", "blocker": "next", "evidence": "evidence",
}


@dataclass
class Row:
    line: int
    id: str
    item: str = ""
    prio: str = ""
    wave: str = ""
    lane: str = ""
    est: float = 0.0
    deps: list[str] = field(default_factory=list)
    status: str = ""
    owner: str = ""
    next: str = ""
    evidence: str = ""


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse(path: str | Path) -> list[Row]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    rows: list[Row] = []
    header: list[str] | None = None
    for i, line in enumerate(lines, start=1):
        if not line.strip().startswith("|"):
            if rows:
                break          # end of the first board table
            header = None      # a non-board table ended; keep looking
            continue
        cells = _cells(line)
        if header is None:
            keys = [_ALIASES.get(c.lower().strip("* "), "") for c in cells]
            if "id" in keys and "status" in keys:
                header = keys
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue           # separator row
        rec = dict(zip(header, cells, strict=False))   # short rows are allowed
        est_raw = rec.get("est", "").replace(",", ".")
        try:
            est = float(re.findall(r"[\d.]+", est_raw)[0]) if est_raw else 0.0
        except (IndexError, ValueError):
            est = 0.0
        deps = [d.strip() for d in re.split(r"[,\s]+", rec.get("deps", "")) if d.strip() and d.strip() != "-"]
        rows.append(Row(line=i, id=rec.get("id", "").strip("` "), item=rec.get("item", ""),
                        prio=rec.get("prio", "").upper(), wave=rec.get("wave", ""), lane=rec.get("lane", ""),
                        est=est, deps=deps, status=rec.get("status", "").lower().strip("` "),
                        owner=rec.get("owner", ""), next=rec.get("next", ""), evidence=rec.get("evidence", "")))
    return rows


def validate(rows: list[Row], id_pattern: str) -> list[str]:
    problems: list[str] = []
    pat = re.compile(id_pattern)
    ids = [r.id for r in rows]
    known = set(ids)
    if not rows:
        problems.append("board has no item rows - is the table header 'ID | ... | Status'?")
    for r in rows:
        where = f"line {r.line} ({r.id or '?'})"
        if not pat.match(r.id):
            problems.append(f"{where}: id does not match {id_pattern}")
        if ids.count(r.id) > 1:
            problems.append(f"{where}: duplicate id")
        if r.status not in STATUSES:
            problems.append(f"{where}: unknown status '{r.status}' (allowed: {', '.join(STATUSES)})")
        if r.prio and r.prio not in PRIORITIES:
            problems.append(f"{where}: unknown priority '{r.prio}' (allowed: {', '.join(PRIORITIES)})")
        if r.status == "done" and not COMMIT_RE.search(r.evidence):
            problems.append(f"{where}: done without evidence (needs a commit hash in Evidence)")
        if r.status in ("in-progress", "planning", "review") and not r.owner:
            problems.append(f"{where}: {r.status} without an owner")
        if r.status == "blocked" and not r.next:
            problems.append(f"{where}: blocked without saying on what (Next column)")
        for d in r.deps:
            if d not in known:
                problems.append(f"{where}: depends on unknown id {d}")
    return sorted(set(problems), key=problems.index)


def ready(rows: list[Row]) -> list[Row]:
    done = {r.id for r in rows if r.status == "done"}
    cand = [r for r in rows if r.status in ("open", "ready", "plan-approved") and all(d in done for d in r.deps)]
    prio_rank = {p: i for i, p in enumerate(PRIORITIES)}
    return sorted(cand, key=lambda r: (prio_rank.get(r.prio, 9), r.wave, r.id))


def metrics(rows: list[Row], prio: str | None = None) -> dict:
    scope = [r for r in rows if r.status != "parked" and (prio is None or r.prio == prio)]
    total = sum(r.est for r in scope)
    shipped = sum(r.est for r in scope if r.status == "done")
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    return {
        "scope": prio or "all",
        "items": len(scope),
        "items_done": sum(1 for r in scope if r.status == "done"),
        "est_hours_total": round(total, 1),
        "est_hours_shipped": round(shipped, 1),
        "shipped_pct": round(100 * shipped / total, 1) if total else 0.0,
        "by_status": by_status,
    }


def _git(root: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    return out.stdout.decode("utf-8", errors="replace")   # never the console code page


def not_done_evidence(root: Path, item_id: str, rows: list[Row], ledgers: Path, main: str = "main") -> tuple[bool, list[str]]:
    """Return (looks_already_done, evidence_lines). Run before starting any item."""
    ev: list[str] = []
    done = False
    row = next((r for r in rows if r.id == item_id), None)
    if row is None:
        ev.append(f"board: no row {item_id}")
    else:
        ev.append(f"board: {item_id} status={row.status} owner={row.owner or '-'} evidence={row.evidence or '-'}")
        if row.status == "done":
            done = True
        if row.status in ("in-progress", "planning", "review") and row.owner:
            ev.append(f"board: already owned by {row.owner} - do not start a second copy")
            done = True
    log = _git(root, "log", main, "--oneline", "--fixed-strings", f"--grep={item_id}", "-n", "20").strip()
    ev.append(f"git log {main} mentioning {item_id}: " + (f"{len(log.splitlines())} commit(s)" if log else "none"))
    branches = [b.strip(" *+") for b in _git(root, "branch", "--list", f"*{item_id}*").splitlines() if b.strip()]
    if branches:
        unmerged = set(b.strip(" *+") for b in _git(root, "branch", "--no-merged", main).splitlines())
        for b in branches:
            ev.append(f"branch {b}: {'NOT merged' if b in unmerged else 'merged'} into {main}")
    ledger = Path(ledgers) / item_id
    if ledger.exists():
        files = sorted(p.name for p in ledger.rglob("*") if p.is_file())
        ev.append(f"ledger {ledger}: {len(files)} file(s) - continue from it, do not restart")
    return done, ev
