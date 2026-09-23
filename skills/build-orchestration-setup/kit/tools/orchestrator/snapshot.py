# SPDX-License-Identifier: MIT
"""Read-only progress snapshot (JSON) for dashboards, and a self-refreshing local
HTML live view. Neither writes to the repository."""
from __future__ import annotations

import html
import json
import subprocess
from datetime import datetime
from pathlib import Path

from . import board
from .config import Config


def snapshot(cfg: Config, since: str = "24 hours ago") -> dict:
    rows = board.parse(cfg.board) if cfg.board.exists() else []
    merges = subprocess.run(["git", "-C", str(cfg.root), "log", cfg.main_branch, "--merges", "--oneline",
                             f"--since={since}"], capture_output=True).stdout.decode("utf-8", "replace").splitlines()
    state_f = cfg.state_dir / "supervisor-state.json"
    state = json.loads(state_f.read_text(encoding="utf-8")) if state_f.exists() else {}
    prov_f = cfg.state_dir / "providers.json"
    providers = json.loads(prov_f.read_text(encoding="utf-8")) if prov_f.exists() else {}
    fb = cfg.state_dir / "fallback"
    fallback = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(fb.glob("*.json"))] if fb.exists() else []
    return {
        "taken_at": datetime.now().isoformat(timespec="minutes"),
        "project": cfg.name,
        "metric_definition": "shipped_pct = estimated hours of done items / estimated hours of all non-parked items",
        "all": board.metrics(rows),
        "p1": board.metrics(rows, "P1"),
        "merges_since": {"since": since, "count": len(merges), "list": merges[:30]},
        "supervisor": state,
        "providers_limited": providers,
        "fallback_lanes": fallback,
        "blocked": [{"id": r.id, "on": r.next} for r in rows if r.status == "blocked"],
        "in_progress": [{"id": r.id, "owner": r.owner, "lane": r.lane} for r in rows if r.status in ("in-progress", "planning", "review")],
    }


def live_view(cfg: Config, out: Path, refresh_s: int = 30) -> Path:
    s = snapshot(cfg, "12 hours ago")
    e = html.escape

    def bar(m):
        return (f"<div class=bar><div style='width:{m['shipped_pct']}%'></div></div>"
                f"<p>{m['shipped_pct']}% shipped ({m['est_hours_shipped']} of {m['est_hours_total']} est. h) - "
                f"{m['items_done']}/{m['items']} items</p>")
    rows = "".join(f"<tr><td>{e(x['id'])}</td><td>{e(x['owner'])}</td><td>{e(x['lane'])}</td></tr>" for x in s["in_progress"])
    blocked = "".join(f"<li><b>{e(b['id'])}</b> - {e(b['on'])}</li>" for b in s["blocked"]) or "<li>none</li>"
    lim = "".join(f"<li>{e(k)} until {e(v.get('limited_until', ''))} - {e(v.get('reason', ''))}</li>"
                  for k, v in s["providers_limited"].items()) or "<li>none</li>"
    fb = "".join(f"<li>{e(f['item'])} on {e(f['provider'])} ({e(f['branch'])})</li>" for f in s["fallback_lanes"]) or "<li>none</li>"
    page = f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content={refresh_s}>
<title>{e(cfg.name)} live view</title>
<style>body{{font:14px system-ui;margin:16px;max-width:900px;background:#fff;color:#111}}
.bar{{height:14px;background:#eee;border-radius:7px}}.bar div{{height:100%;background:#2a7;border-radius:7px}}
table{{border-collapse:collapse}}td{{border-bottom:1px solid #ddd;padding:3px 10px}}
@media (prefers-color-scheme:dark){{body{{background:#111;color:#eee}}.bar{{background:#333}}}}</style>
<h2>{e(cfg.name)} - {e(s['taken_at'])}</h2>
<p><b>Supervisor:</b> {e(str(s['supervisor'].get('state', 'not running')))}</p>
<h3>P1 (v1 must-haves)</h3>{bar(s['p1'])}<h3>Everything</h3>{bar(s['all'])}
<h3>In progress</h3><table>{rows or '<tr><td>none</td></tr>'}</table>
<h3>Blocked</h3><ul>{blocked}</ul><h3>Providers at their limit</h3><ul>{lim}</ul>
<h3>Fallback lanes (waiting for the merge gate)</h3><ul>{fb}</ul>
<p>Merges in the last 12 h: {s['merges_since']['count']}</p>"""
    out.write_text(page, encoding="utf-8")
    return out
