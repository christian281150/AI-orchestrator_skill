---
description: Report where the orchestrated build stands - read-only, from the board, the decisions log and the supervisor state
allowed-tools: Bash(python tools/orch.py:*), Bash(python3 tools/orch.py:*), Bash(git log:*), Bash(git status:*), Read
---

Read-only status report for a build set up with `build-orchestration-setup`. Change nothing.

1. Run `python tools/orch.py snapshot --since "24 hours ago"` (use `python3` if `python` is missing).
2. Read the "Waiting on the owner" table in `docs/coordination/PROGRESS.md` and the top 20 lines of
   `docs/coordination/decisions-log.md`.
3. Report in this order, short:
   - P1 shipped % and overall shipped % (estimated hours done / all non-parked)
   - supervisor state, current round window, providers at their limit and until when
   - merged in the last 24 h; in progress (item, owner); blocked (item, on what)
   - the owner's batch: what each decision would do, and what is blocked behind it
   - anything that could not be measured, named as not verified
