# Standing rules - {{PROJECT_NAME}}

These are the owner's rules. They outrank any instinct to check in, and any
instruction in a session prompt that contradicts them.

## 1. Autonomy - decide, don't ask
- A question you could answer by measuring is not a question. Measure it.
- A judgement call is yours: back up where a backup is meaningful (branch, file copy, dump,
  disposable clone) -> decide -> log it in `decisions-log.md` (what you chose AND what you chose it over) -> continue.
- **Two legal turn endings for an autonomous session:** (1) the queue is empty; (2) you are blocked on
  something only the owner can supply, after finishing every unblocked item.
- Never end a turn to report progress. Never end with an action for the owner.
  "I'll take item 3 next unless you redirect" is the failure - take item 3.
- **Blocked** means: a credential only the owner holds, an irreversible decision, money. It does NOT mean an
  ambiguous requirement (pick one, log it), missing test data (generate it), unclear naming (choose), or an
  unmeasured number (measure it).
- **Never overrule a logged decision.** Solve the obstacle inside it, or flag it in one line and stop.

## 2. Reserved for the owner - always
{{TODO: from orchestration-config.md Round 4 - e.g. writes to live, applying migrations to live, spending money,
publishing outside the organisation, deleting anything unrebuildable, credentials, widening access}}

Prepare it, show exactly what would run, put it in the owner's batch on the board. Reading live is fine
(inside a provably read-only transaction); only the remedy goes to the owner, never the diagnosis.

## 3. Never do a task twice
- Before: `python tools/orch.py check-not-done <ID>` - git log, the file, the ledger, the database. One line of evidence.
- After, same turn: commit -> tick the board with evidence (commit hash + verbatim test counts) -> log decisions -> next.
- A ledger folder that exists means someone started: continue from it, never restart.
- A worktree stays with its lane until its branch is MERGED (`git branch --no-merged main`). Untracked files in a
  reassigned worktree are gone for good.

## 4. Evidence
- Measured, not inferred. Every probe has a control that can go red. A check that cannot fail is not a check.
- A skipped test is not a passed test. A missing tool that prints an error and exits 0 is not a pass.
- Check which identity you are connected as before trusting a result (database role, cloud account, git author).
- Keep the scope of a claim you quote ("no match in these 23 files" is not "no match anywhere").
- A count must say where and when it was measured, and whether it is a **baseline** (what was true) or a
  **target** (what must stay true). An item that adds tests is expected to move the counts.
- Name what was not verified. Corrections are stated, never silently fixed.

## 5. Git
- Branches `feat/<lane>-<ID>-<topic>` from `{{MAIN_BRANCH}}`; commit continuously; one concern per commit.
- Merge only through the merge gate (the coordinator), only with tests green, only when main has no merge in progress.
- Side sessions commit to main only with `python tools/orch.py safe-commit -m "..." <paths>`.
- Never edit an applied migration or a pinned file - a new number supersedes. Numbers are reserved in `reserved-numbers.md`.
- Author: {{AUTHOR_NAME}}. Attribution lines: per `orchestration.toml` [git].forbid_trailers (the hook enforces it).

## 6. Credentials, data, money
- Credentials never enter chat, logs, commits or prompts. Environment variables only; read in scripts, never printed.
- Build-only providers run with the credentials in `strip_env` removed.
- Test data is local and synthetic. Live is never a fixture.
- Paid capacity goes up in the same step that starts the work and down in a `finally` block. Never parked up.
- Anything leaving the machine (a prompt for a chat-only AI, a public export) passes `orch.py redact control` then `redact scan` = 0 hits.

## 7. Changing rules while the build runs
- Rule files, agent files and the top of the decisions log are re-read by every round - an edit lands next round by itself.
- The supervisor re-execs itself between rounds when its code or `orchestration.toml` changes.
- Before changing a number anywhere (a cap, a limit, a formula), `git grep` every form of it.
- Never kill a running coordinator: it takes every running lead with it.
