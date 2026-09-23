# Reporting - so the owner always knows where the build is, without asking

Every report reads from the board and the decisions log. Nothing reports from memory.

## 1. The board (`PROGRESS.md`) - the truth
- One row per item: ID, item, prio, wave, lane, estimate (agent-hours), deps, status, owner, next/blocker,
  evidence. `done` requires a commit hash (the hook and `board validate` enforce it).
- "Waiting on the owner" table - one batch.
- Session log: one line per round (`ROUND RESULT` line + date).

## 2. The metric
`shipped % = estimated hours of done items / estimated hours of all non-parked items`, reported for **P1**
(the headline) and for everything. In-flight = tasks done / tasks planned from the ledgers. Estimates are
agent-hours from the wave breakdown; re-estimate only with a logged decision (a silently moved estimate makes
the curve lie).

## 3. Dashboard artifact (claude.ai) - updated on a schedule
- An HTML artifact with its own small database (the `db` capability): `meta/dashboard` (items, waves,
  estimates, target) and `snapshots/<YYYY-MM-DD>-am|pm` (one per update). The page draws P1 %, all %,
  items by status, merges per day, blocked items, owner batch. Update by writing a snapshot, never by
  republishing the page.
- A claude.ai scheduled task at e.g. 07:30 and 19:30 runs `python tools/orch.py snapshot --out <file>` on the
  machine (read-only) and writes the snapshot into the artifact's database. Cron is in UTC - convert, and note
  the daylight-saving switch dates. If the data is on a PC, the task needs "require this computer".
- First snapshot: reconstruct history from board commits on main if the build already ran.

## 4. Local live view (optional, not an AI job)
`tools/scheduling/live-view.cmd` / `.sh` -> `orch.py live-view` writes a self-refreshing HTML page every
30 s: supervisor state and round window, P1 and total bars, in-progress rows, blocked, providers at their
limit, fallback lanes waiting for the gate, merges in the last 12 h. Read-only. A claude.ai page cannot read
the PC by itself - only a scheduled AI run can push data to it.

## 5. Handovers
At every session switch and before clearing a chat: `HANDOVER-<n>.md` from the template - into the repo and
the Project. Newest wins; it states what it replaces.

## 6. Owner alerts
- Blocked on the owner -> the board batch; optionally a push notification from the scheduled task when the
  batch is non-empty or `BLOCKED.txt` exists.
- The owner's reply lands as a decision in the log in the same turn.

## 7. Monitoring commands
| Question | Command |
|---|---|
| Is it running, which round, when does the window end? | `<state_dir>/supervisor-state.json` |
| What happened? | tail of `<state_dir>/supervisor.log`, `<state_dir>/rounds/<id>.log` |
| What is ready next? | `python tools/orch.py board ready` |
| Progress numbers | `python tools/orch.py board metrics` / `snapshot` |
| Is the setup healthy? | `python tools/orch.py preflight` |
| Which providers are limited until when? | `<state_dir>/providers.json` |
