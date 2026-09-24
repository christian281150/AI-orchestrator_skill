# Usage limits, automatic restart, and switching providers

Subscriptions have 5-hour and weekly windows. An unattended build hits them. Without a plan, the build
stops at the first limit and sits idle until someone notices. With one, it degrades gracefully: other
providers keep building, the merge gate catches up when it is back, and nothing unreviewed reaches main.

## The provider registry - `orchestration.toml [[providers]]`
Each provider has a priority (lower = preferred), roles, commands and a limit detector:

| Role | Meaning | Who should have it |
|---|---|---|
| `coordinator` | may run a round | the lead provider; a second only if you trust it to merge |
| `merge` | may put code on main | as few as possible - one is best |
| `plan`, `review` | may write/approve plans | thinking-tier providers |
| `build` | may implement an approved plan on its own branch | any provider |

## Detection - how the supervisor knows a limit was hit
1. **The provider's own record decides when it exists.** (Example: Codex writes rate-limit usage into its
   session files; the kit reads it: `native_limit = "codex_rollout"`, threshold 97%. Add a reader for any
   other provider that keeps such a record - `providers.py`.)
2. **Text fallback, restricted:** only the last N lines of the round log (default 30), and only when the run
   exited non-zero or never printed its `ROUND RESULT:` verdict.
   Why: matching anywhere in the log once raised a false "limit hit" - the agent had read a board line
   quoting an old limit message. The build stopped for nothing and the board was "corrected" with a false
   line.
3. **Reset time** parsed from the message ("resets at 3pm", "try again in 2h 5m", "resets Sep 27, 1pm");
   when none is found, re-probe every `reprobe_minutes`.
4. Optional `status_command` per provider: exit 0 = available. Use it if the CLI offers a cheap check.
5. Operator override: delete the provider's entry in `<state_dir>/providers.json`; it is re-read each pass.

## The failover chain (what the supervisor does, pass by pass)
1. Pick the highest-priority provider with `coordinator` that is available -> run a round.
2. Round ends with a limit -> mark that provider limited until its reset -> immediately try the next pass.
3. No coordinator available -> if `fallback_when_limited`: for every available `build` provider, start up to
   `max_parallel` **fallback lanes** for board rows that are `plan-approved`, unowned, and have a
   `ledgers/<ID>/build-brief.md`. Each gets its own worktree and branch `feat/<lane>-<ID>-<provider>`. A
   marker file (outside the repo) records it; the repo and board are not touched.
4. Sleep until the earliest reset (capped at the re-probe interval), then loop.
5. When a merge-gate provider is back, the round prompt lists the finished fallback lanes and requires them to
   be gated **before any new dispatch**: run the plan's verifies, one task reviewer, merge or reject, print
   `GATED: <ID> accepted|rejected <reason>`. The supervisor archives the marker.
6. Same failure N times in a row (not a limit) -> stop, write `BLOCKED.txt`. Never loop on a broken setup.

**Automatic restart:** the supervisor is started by the OS scheduler at logon and restarted on failure; it
re-execs itself between rounds when its code or config changed; a `STOP` file ends it cleanly between rounds.

**The keeper** (`orch.py keeper`, every ~10 minutes, independent of rounds) closes the remaining gaps: it restarts
lanes that stopped on a limit (capped per day), starts build lanes whenever no round runs, lets an idle build
provider plan one safe item, and runs cloud planners in steady / accelerate / handback mode on their own credit.
Which tool gets which work, and why: `10-tool-routing.md`. Work done by anyone but the lead is reconciled at the
start of the next round (`orch.py gap`).

## What makes fallback safe
- Build providers only build **plans the lead provider's planner and reviewer already approved**, from a
  self-contained brief. They never plan, never merge, never touch the board, the decisions log, live
  systems or credentials (`strip_env`).
- One merge gate. Code from three providers reaching main through one reviewer is manageable; three merge
  gates is not.
- Planning lanes keep a stock of approved plans so fallback builders have work when the limit hits.

## Allowance management
- Threshold stop at ~97%: finish running work, start nothing new, flag it on the board.
- Manual resets (some plans include one): the owner applies them; the build never does.
- Measure burn: e.g. one external lane ~1 allowance point per ~35 min -> ten lanes ~15-20 points/hour. Put
  the measured rate in the handover; plan parallelism against it.
- Cheapest adequate model per role; the top tier of any provider is for critical decisions, not a default.

## Chat-only providers (no CLI): the "desk" pattern
A web chat model can still build a well-specified item as an experiment:
1. Throwaway branch and worktree; never main, never the board, never live, no credentials.
2. A desk session writes each wave's prompt as a file: self-contained (paste every file to change, the
   interfaces, the spec paragraphs), with a strict answer format (every file complete, tests, assumptions,
   questions).
3. **Redact before it leaves:** `orch.py redact control <file>` (a planted fake secret must be found), then
   `orch.py redact scan <file>` must show 0 hits. Server addresses, domains, project ids, names, keys.
4. The owner pastes the prompt, saves the full answer to a file; the desk extracts files by script (never
   by retyping), applies, runs tests, reviews as a task reviewer would. Max 2 fix rounds per wave.
5. An evaluation report decides whether the branch enters the real pipeline.

## Verify per CLI version (flags change)
- The exact headless command and permission flags (`<cli> --help`).
- Where it writes usage records, and their format (preflight reports whether the record is readable).
- Background-work ceiling in headless mode, and the env var that raises it.
- Whether it spawns its own helpers.
- Whether its sandbox works on your OS (on one Windows setup the sandbox broke every command; the fix was
  full access with credentials stripped - name that residual risk in the handover).
