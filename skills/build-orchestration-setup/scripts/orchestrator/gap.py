# SPDX-License-Identifier: MIT
"""Knowledge gap: work the lead provider did not see - built or planned by another provider
(build lanes, cloud sessions, chat desks) - that must be reconciled before new work starts.

Rule (run first in every round): for each item listed, a reviewer writes `reconcile-review.md` in the
item's ledger. For plans authored by a non-lead provider, additionally:
  (a) `gap-summary.md`       - what the plan assumes that the lead has not verified
  (b) `plan.<lead>.md`       - a BLIND re-plan by the lead (written without reading the other plan)
  (c) `reconcile.md`         - an arbiter's comparison and ruling, which plan is built
Items stay listed until those files exist.
"""
from __future__ import annotations

import json
import math
import re

from .config import Config


def lead_name(cfg: Config) -> str:
    leads = cfg.by_priority("merge") or cfg.by_priority("coordinator")
    return leads[0].name if leads else ""


def knowledge_gap(cfg: Config) -> tuple[list[dict], int]:
    lead = lead_name(cfg)
    items: dict[str, dict] = {}
    # 1. lanes other providers ran (gated or not) that have no reconcile review yet
    for folder in (cfg.state_dir / "fallback", cfg.state_dir / "fallback" / "gated"):
        for f in sorted(folder.glob("*.json")) if folder.exists() else []:
            m = json.loads(f.read_text(encoding="utf-8"))
            for item in [m.get("item")] + m.get("items", []):
                if not item or (cfg.ledgers / item / "reconcile-review.md").exists():
                    continue
                items.setdefault(item, {"item": item, "why": f"{m.get('kind', 'build')} lane on {m.get('provider')}",
                                        "needs": ["reconcile-review.md"]})
    # 2. plans authored by a non-lead provider
    if cfg.ledgers.exists():
        for plan in sorted(cfg.ledgers.glob("*/plan.md")):
            item = plan.parent.name
            if item.startswith("_"):
                continue
            m = re.search(r"(?im)^\*{0,2}authored-by:\*{0,2}\s*([\w.-]+)", plan.read_text(encoding="utf-8"))
            author = m.group(1).lower() if m else lead
            if author == lead.lower():
                continue
            needs = [n for n in ("reconcile-review.md", "gap-summary.md", f"plan.{lead}.md", "reconcile.md")
                     if not (plan.parent / n).exists()]
            if needs:
                items[item] = {"item": item, "why": f"plan authored by {author}", "needs": needs}
    listed = sorted(items.values(), key=lambda d: d["item"])
    reviewers = min(5, max(1, math.ceil(len(listed) / 2))) if listed else 0
    return listed, reviewers


def report(cfg: Config) -> tuple[list[str], int]:
    listed, reviewers = knowledge_gap(cfg)
    lines = [f"REVIEWERS={reviewers}"]
    lines += [f"{g['item']}\t{g['why']}\tneeds: {', '.join(g['needs'])}" for g in listed]
    return lines, len(listed)
