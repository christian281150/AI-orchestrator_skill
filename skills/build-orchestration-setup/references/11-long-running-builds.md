# Running for days - gaps closed in allowance, recovery and races

These are not new concepts: each one closes a gap in the rounds, keeper and failover described in the other
references, found while running real builds for several days. Read this before running a build unattended for
more than a day (adoption levels 3-4). Each rule has the
problem it prevents, the rule, how to wire it, and a **control** - a check that can go red and proves it works.
"Toolkit" says what `scripts/orch.py` already does; everything else is wired in your launcher and watchdog
scripts, with the named config keys as the suggested place. Tool names are examples only.

Contents: A planning just in time · B fix routing · C lane cap by load · D watchdog · E restart reconciliation ·
F cloud helpers · G cloud setup · H machine traps · I race discipline · J usage measurement · Proposals

---

## A. Just-in-time planning
- **Problem:** the lead provider spends its allowance planning far ahead; plans go stale, and later there is no
  allowance left to review and merge what was built.
- **Rule:** plan only while *ready work* (approved plans + open fix briefs) is below **half the build-lane cap**.
  The lead's allowance goes, in this order: 1. gating/review/merge, 2. planning, 3. building what the build
  provider cannot build.
- **Wiring:** `[keeper] queue_low_watermark` = build-lane cap / 2 (toolkit: cloud planners already respect it);
  the coordinator prompt states the order; planning lanes check the count before starting.
- **Control:** with ready work at or above half the cap, a keeper `--dry-run` pass or round log shows *no*
  planning start. Log a line `PLANNING paused (ready X / cap Y)` so this is visible.

## B. Fix routing
- **Problem:** small rework found at review pulls the lead provider into building, spending top-tier allowance on
  easy changes.
- **Rule:** bounded rework becomes a **fix brief** in the item's ledger (`ledgers/<ID>/fix-brief-<n>.md`). A
  build-provider fix lane with its own reviewer does it and answers with `fix-done-<n>.md` whose first line is the
  brief's SHA-256 hash. The lead provider runs only the merge gate.
- **Wiring:** watchdog starts fix lanes for briefs without a matching done file; gate checks the hash.
- **Control:** a `fix-done` with a wrong hash (brief changed after the fix started) is rejected at the gate; test
  it once by editing a brief after its fix lane finished.

## C. Build-lane cap by load
- **Problem:** too many lanes exhaust memory, lanes crash half-way, and the machine stalls everything else.
- **Rule:** cap build lanes by load - lower while lead and build providers run together (example: 5 on 16 GB),
  higher when the lead is limited or idle (example: 10). Every launcher has a **memory guard**: no new starts at
  ~85% of committed memory, refuse at ~90%; memory-refused lanes are retried later, not dropped.
- **Wiring:** `[providers.<x>].max_parallel` for the shared case plus a second cap for "lead limited"; the guard
  inside the launcher script; a `memory-refused` status on the lane marker.
- **Control:** simulate high memory (lower the threshold temporarily): a launch must refuse and the marker must
  read `memory-refused`; the next watchdog pass must retry it.

## D. Watchdog on the OS scheduler
- **Problem:** anything that depends on the orchestrator being alive stops when it stops - lanes stay dead after a
  limit, approved plans wait, nobody notices a hung tool.
- **Rule:** a watchdog (the kit's *keeper*), run by the OS scheduler every ~10 minutes and independent of the
  orchestrator, does exactly this and never merges:
  restart limit- and memory-stopped lanes with their original arguments (capped per day); start lanes for
  approved plans when no round runs; start fix lanes (B); let an idle build provider plan small safe items; keep
  helper jobs alive; put the agent memory file (`AGENTS.md` / `CLAUDE.md`) into every worktree; end hung tool
  processes (no log output for N minutes); support **dry-run** (print actions, do nothing).
- **Wiring:** toolkit `orch.py keeper` covers restarts on limit, approved-plan lanes, idle planning, cloud planners;
  add memory-stopped restarts, fix lanes, helper keep-alive, memory-file copy, hang kill and `--dry-run` in your
  wrapper until the toolkit has them.
- **Control:** kill a lane's process by hand -> the next pass restarts it (and stops after the daily cap); in
  dry-run the same pass prints the restart and starts nothing.

## E. Restart reconciliation
- **Problem:** after a restart the orchestrator does not know what happened while it was down - it re-plans done
  work or builds on a plan it never checked.
- **Rule:** every round starts by measuring the knowledge gap: fetch origin; compare branch heads with the
  watchdog's last snapshot; add lanes and cloud sessions started without the orchestrator. Then 1-5 reviewers.
  For plans written by a build provider: gap summary + a **blind re-plan in a fresh context** (a new agent that
  has not seen the other plan) + an arbiter's comparison -> one **adopted plan of record**. Lane markers are
  cleared only after reconciliation.
- **Wiring:** toolkit `orch.py gap` (markers + foreign plans, `REVIEWERS=<n>`, injected into every round prompt);
  add the fetch and the branch-head comparison against the watchdog's snapshot; the arbiter writes `reconcile.md`
  naming the adopted plan.
- **Control:** push a commit to a lane branch from outside the orchestrator -> the next round's gap list must show
  it; a marker must still exist until `reconcile.md` is written.

## F. Cloud helpers
- **Problem:** cloud sessions are paced by guesswork, burn credit in parallel, or keep working after the local
  lead is back - and nobody knows which rows they finished.
- **Rule:**
  - measure how they bill **before** pacing: read the usage endpoint before and after one session;
  - one **steady** helper while the runway (A) says plan; **accelerate** helpers only once the local lead is
    limited; never below a **credit floor**;
  - each session gets a to-do list and writes a status file (`STARTED <ID>`, `DONE <ID>`, `BLOCKED <ID> <why>`,
    `HANDBACK`, `END`), pushed after every line;
  - when local allowance returns, write a **HANDBACK** signal on main: finish the current item, hand the rest back;
    the watchdog frees the unstarted rows;
  - fetch their work back continuously, fast-forward only - never force.
- **Wiring:** toolkit `[keeper]` cloud keys (`cloud_steady`, `cloud_accelerate_max`, `cloud_credit_floor`,
  `handback_below_pct`, `handback_file`); the status file and row freeing in your wrapper.
- **Control:** one measured before/after reading is written down before the first accelerate; a status file
  without `END` after the session ended is flagged; after HANDBACK no unstarted row stays claimed.

## G. Cloud setup checklist
- **Problem:** cloud sessions start without repository access, fail in setup, or run without the skills the
  plan assumes - and nothing says so.
- **Rule:** the repository connection exists **before** a session starts; the environment setup script never
  fails (each step warns, the script exits 0); it installs the plugin skills; the first prompt step is a skills
  self-check; a script-launched session may need its own console window; post-commit **and** post-merge hooks push
  everything, so sessions never plan against stale code.
- **Wiring:** a setup script in the repo; hooks `post-commit` and `post-merge` calling `git push` with a timeout.
- **Control:** a session's first status line is its skills self-check result; run the setup script with one step
  broken on purpose - it must still exit 0 and print the warning.

## H. Machine traps
- **Problem:** the OS scheduler ends everything a task started; a slow hook blocks every commit; walking every
  worktree takes minutes; a lane launched with split arguments never starts - all silently.
- **Rule:** start long-lived children **outside** the scheduled task (on Windows, for example via WMI) and relaunch
  lanes that never wrote a status; give hook checks a time limit (warn and let the commit through on timeout);
  avoid wildcard walks over many worktrees (use explicit lists); quote launcher arguments and **check that the log
  file appeared**.
- **Wiring:** launcher script; hook wrapper with a timeout; watchdog check "log appeared within 60 s".
- **Control:** start a lane from the scheduled task, let the task end - the lane must still run; a lane whose log
  never appears is marked `launch-failed` and retried.

## I. Race discipline
- **Problem:** two planners take the same row, a failed commit leaves main dirty, a guarded commit sweeps someone
  else's staged files.
- **Rule:** a commit counts only when it **landed** (check it is in the log; otherwise restore the edited paths);
  one claim per board row for every planner (Owner column, set through the guarded commit); a queued
  build-provider planning lane **yields** to the lead - it checks its claim and whether a lead plan exists before
  every start; guarded commits never include files someone else staged.
- **Wiring:** toolkit `orch.py safe-commit` (refuses foreign staged files, unstages path by path on failure) and
  `check-not-done`; claim/release via safe-commit in your planners.
- **Control:** stage a foreign file and run safe-commit -> it refuses (a test covers this); start two planners on
  one row -> the second must refuse.

## J. Usage measurement
- **Problem:** a limit read from log text is wrong (quoted text); unmeasured burn makes pacing guesswork; a token
  printed once is in a log for good.
- **Rule:** read allowance from the provider's own record or usage endpoint, never from log text; record the
  short window, the weekly window and any credit bucket on every tick; tokens are read inside scripts and never
  printed.
- **Wiring:** toolkit `usage_command` per provider (JSON), `native_limit` readers; append one line per tick to a
  usage log in the state folder.
- **Control:** a test covers the "quoted limit text is ignored" case; grep the usage log and all logs for token
  prefixes - zero hits.

---

## Proposals - not yet part of the rules
Marked as proposals: useful for multi-day builds, not yet proven in one.

1. **Secrets in public history and commit metadata.** *Problem:* a key or a real email in an old commit is public
   forever once pushed. *Rule:* before a repository goes public, scan the full history (`git log -p --all`) and
   commit metadata; use a no-reply author email. *Wiring:* `orch.py redact scan` over the history dump. *Control:*
   plant a fake key in a throwaway commit - the scan must find it.
2. **Stale handovers.** *Problem:* a new session trusts a handover older than the last day of work. *Rule:* the
   newest handover must be newer than the last N commits on main, or it is marked stale. *Wiring:* a preflight
   warning. *Control:* commit after the handover - preflight warns.
3. **A second machine.** *Problem:* two machines run two watchdogs against one repository and double-start lanes.
   *Rule:* one machine holds a lease (host + expiry) committed on main; the other runs read-only until it takes the
   lease over. *Wiring:* lease file + check in supervisor and watchdog. *Control:* start the watchdog on machine 2 -
   it refuses while the lease is valid.
4. **Disk space.** *Problem:* worktrees and logs fill the disk and every lane fails at once. *Rule:* no new lanes
   below a free-space floor; remove worktrees of merged branches; rotate logs. *Control:* lower the floor - launches
   refuse.
5. **Clock changes.** *Problem:* schedules drift at daylight-saving changes. *Rule:* schedule in UTC and note the
   local-time switch dates in the handover. *Control:* next-run time checked on the switch date.
