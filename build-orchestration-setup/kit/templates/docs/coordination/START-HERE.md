# START HERE - every session, every agent, before the first action

Project: **{{PROJECT_NAME}}**. This file does not hold status. Status lives on the board.

## 1. The start ritual (no exceptions, about 2 minutes)

1. Read the newest `HANDOVER-*.md` (if any) - it says what was running and what changed.
2. **Measure, don't trust.** The repository is the source of truth:
   - `git log --oneline -15` and `git status --short`
   - `PROGRESS.md` (the board) and the top of `decisions-log.md` (newest first)
   - the supervisor state: `<state_dir>/supervisor-state.json` and the tail of `supervisor.log`
3. Before starting ANY item: `python tools/orch.py check-not-done <ID>` - one line of evidence it is not
   already done or owned. "It looked open" is not evidence.

## 2. Document precedence - newest wins, and this table names the winner

| Rank | Source | Trust it for |
|---|---|---|
| 1 | the repository itself (code, git log, database as measured) | what is true now |
| 2 | `PROGRESS.md` | status of every item |
| 3 | `decisions-log.md` | anything another document calls "open" |
| 4 | newest `HANDOVER-*.md` | what was running, what changed, what waits on the owner |
| 5 | `RULES.md`, `SESSION-PROMPT.md`, agent files | how to work |
| 6 | `SCOPE.md`, spec, architecture | what to build and in what order |
| 7 | anything older | design intent only - its status lines are stale |

A status line in a document is a timestamped measurement, never a fact about now.
When you change the world, change the document that describes it in the same commit.

## 3. Where things are

| What | Where |
|---|---|
| Board, decisions, rules, prompts, ledgers | `docs/coordination/` |
| Orchestration settings | `orchestration.toml` (repo root) |
| Tools (supervisor, preflight, board checks, safe-commit, redact) | `tools/orch.py` |
| Run state, logs, fallback markers | `state_dir` in `orchestration.toml` - outside the repo |
| Lane worktrees | `worktrees_dir` in `orchestration.toml` |
| Data | {{TODO: data location - outside the repo}} |
| Environments | {{TODO: local / test / live - names, and which one is "live"}} |
| Credentials | environment variables only - names in `orchestration.toml` [safety].required_env |

## 4. Which session are you?

- **Interactive** (the owner is in the chat and waiting): answer, then stop. Action first, short.
- **Autonomous** (you were started to work the queue): `RULES.md` section 1 applies. Two legal turn endings only.
- **Monitoring** (a chat that watches the unattended build): adjust rules, never do lane work unless asked,
  never kill a running coordinator.
