# Board - {{PROJECT_NAME}}

Single source of truth for status. Updated in the same commit as the change it describes.
Validate: `python tools/orch.py board validate`. Status values: open, ready, planning, plan-approved,
in-progress, review, done, blocked, parked. `done` needs a commit hash in Evidence.

## Items

| ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| W0-1 | Repository, CI, environments, test harness | P1 | 0 | infra | 4 | - | open | | | |
| W0-2 | Database schema v1 + migration runner | P1 | 0 | db | 6 | W0-1 | open | | | |
| W1-1 | {{TODO: the core loop, end to end}} | P1 | 1 | backend | 8 | W0-2 | open | | | |

## Waiting on the owner (one batch)

| # | What it would do | Why now | If it waits | Blocked behind it |
|---|---|---|---|---|

## Session log (newest first, one line per round)

- 
