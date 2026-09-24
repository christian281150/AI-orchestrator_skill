# Running for days: pacing, a watchdog, restart reconciliation, cloud helpers

Phases 0-7 get a build running. This chapter keeps it running for days, across usage limits,
restarts, a second provider and cloud sessions, without wasting allowance or doing work twice. Each section gives
the problem, the rule, how to wire it, and the **control** that proves it works: a check that can go red.

Words used here:
- **Lead provider**: plans, reviews and merges.
- **Build provider**: implements approved plans on its own branch.
- **Cloud helper**: a hosted agent session (for example a cloud coding session) that clones the repository.
- **Ready work**: approved plans not yet built, plus fix briefs not yet answered.

---

## 1. Plan just in time; fixes go to the cheaper builder

**Problem.** Planning costs the lead provider's allowance. A plan that waits days unbuilt spent that allowance too
early and goes stale. Planning too late leaves builders idle.

**Rule.** Pace planning by the builders' runway.
- `CAP`: build lanes allowed now. It can be lower while the lead provider is also running (shared RAM and CPU)
  and higher when the lead provider is limited or idle.
- `READY`: approved plans not yet built, plus fix briefs not yet answered.
- **Plan only while `READY < CAP / 2`.** A plan takes 30-45 minutes, so planning starts while the lanes still
  have work, not once they idle.
- The lead provider's allowance is spent in this order:
  1. gating and reviewing finished work
  2. planning, only while the runway says so
  3. building what the build provider cannot (live steps, owner decisions)

**Fixes.** A fix is bounded rework on an unmerged branch: a reviewer finding, a merge-gate finding, or a
"done with concerns" verdict. It needs no live access, credentials, schema number or owner decision.
- The reviewer that finds it writes `ledgers/<ID>/fix-brief.md`: findings, files, the verifies that must pass.
- A **build-provider fix lane** implements the fixes. Its own reviewer checks them, and it answers with
  `fix-done.txt` carrying the brief's hash.
- The lead provider then runs **only the merge gate**. It does not re-do the review.
- Small safe repair items (docs, tooling; no live, no schema) may be planned *and* built by an idle build provider
  on its thinking tier. Such plans are marked `Plan author: <build provider>` and reconciled (section 3) before merge.

**Control.** A dummy fix brief raises `READY` by 1. When the cap is full, the fix lane waits; once a lane frees, it starts.

## 2. A watchdog that does not depend on the orchestrator

**Problem.** The supervisor runs rounds. While the lead provider is limited, crashed or between rounds, nobody
restarts stopped build lanes, uses free build capacity, or notices that allowance came back.

**Rule.** A small **watchdog** runs on the OS (Operating System) scheduler every ~10 minutes, independent of rounds.
It does only mechanical work and never merges. On every tick it:
1. snapshots what the lead provider has seen (branch heads, time) while a round runs (for section 3)
2. restarts build lanes that stopped on an allowance limit or a memory guard, with their original arguments,
   at most a few times a day per item
3. starts build lanes for approved plans when no round runs or the lead provider is limited
4. starts fix lanes (section 1)
5. lets idle build providers plan safe repair items (section 1), only where no plan exists and nobody claimed the row
6. paces cloud helpers (section 4)
7. keeps its own helpers alive (for example the job that fetches cloud work back)
8. puts the agent memory file into every worktree (build-provider worktrees often lack it, and a
   consistency hook then refuses every commit)
9. ends tool processes that have hung for longer than a limit (see section 5)

It claims board rows only through the guarded commit (`safe-commit`). A claim counts only once the commit landed (section 6).

**Control.** Run the watchdog in dry-run mode: it logs what it would start and changes nothing. Then run a first
real tick: the result code is 0, and the lanes it started are still alive after the tick ends.

## 3. Restart reconciliation: never assume you continue where you stopped

**Problem.** While the lead provider was away, build lanes and cloud helpers kept working. A restarted
orchestrator that trusts its last memory re-plans done work, merges unreviewed code, or loses a build provider's plan.

**Rule.** First thing every round, before any dispatch:
1. **Measure the knowledge gap.** Fetch origin (so cloud-helper pushes are local), then compare every branch head
   with the watchdog's last snapshot. Add every lane started without the orchestrator (markers, status files) and
   every cloud-helper session. Print one row per touched item and a reviewer count, `REVIEWERS = min(5, max(1, ceil(items / 2)))`.
2. **Review:** dispatch that many reviewers, each owning at most two items. Per item, write a reconcile review
   (per task: keep / fix / redo, with evidence). Fixes become fix briefs (section 1).
3. **Plans written by the build provider** get three steps:
   - (a) A **gap summary**: the plan against the deliverable, and the plan against the item's done-when.
   - (b) In parallel, a **blind re-plan**: a planner in a fresh context that never sees the build provider's plan,
     the diff, or (a). It writes `plans/<ID>.lead.md` from the item text and context only.
   - (c) An **arbiter** compares both plans with (a) and decides which work is kept, adapted or discarded, and the
     shortest path to done. The adopted plan becomes the plan of record; the other is kept beside it.
4. Plans written by cloud helpers of the lead provider are lead plans already reviewed: they get step 2 only.
5. Delete the item's markers once it is reconciled. Only then does it join the normal flow.

**Control.** With no snapshot, the gap covers the last 24 h; with a fresh snapshot and nothing changed, it prints `REVIEWERS=0`.

## 4. Cloud helpers: pacing, to-do lists, handback

**Problem.** A cloud helper runs with no local input and may be billed differently from the local subscription.
Started without care, it drains the same allowance as the local build, plans rows twice, or keeps working after
the local build could have done it better (the local side has the full view, the test databases and the environment variables).

**Rules.**
- **Measure how it bills before deciding the pacing.** Read the provider's usage endpoint (section 7) before and after one
  session. Some cloud credits are drawn even while subscription allowance remains; some only after it runs out.
  Pace by what you measured, not by what you assume.
- **One steady helper, plus accelerate helpers.**
  - Steady: at most one helper at a time, only while the runway says plan (section 1).
  - Accelerate: up to N more helpers, only once the local lead provider is at its limit.
  - Stop when the credit falls below a floor.
- **To-do list per session.** Each session gets several rows and works top to bottom. It keeps a status file on
  its own branch: `STARTED`, `DONE`, `BLOCKED`, `HANDBACK`, `END`. It pushes after every line.
- **Handback.** When the local allowance is back, the watchdog commits a `HANDBACK <timestamp>` signal on main.
  - Before each new item, an accelerate session reads the signal. If it is newer than the session's start, the
    session finishes the item it is on, writes `HANDBACK <items not started>`, and stops.
  - The watchdog frees the rows it did not start.
  - Steady sessions ignore the signal.
- **Cloud helpers plan the substantial rows; small safe repairs go to the idle build provider.**
- **Fetch back continuously.** A local job fetches origin every few minutes and fast-forwards local branches that
  a cloud session advanced. It never forces, and it logs diverged branches.

**Setup checklist for cloud sessions (each item cost a failed session):**
1. The repository connection (for example the GitHub app) must exist **before** a session starts. A running
   session never gains credentials; a session started without it cannot push.
2. The environment's **setup script must never fail** (`|| true` on every step, `exit 0` at the end). A failed
   setup script stops the session before it starts.
3. Install the plugin skills the roles name in the setup script. Repository skills come with the clone.
4. **Skills self-check.** The first step of every cloud prompt checks the required skills, writes `SKILLS OK` or
   `SKILLS MISSING <names>` to the status file, and stops only if the core planning skill is missing.
5. A command that launches a cloud session from a script may refuse a non-interactive terminal. If so, start it in
   its own minimised console window.
6. Everything is pushed continuously: a post-commit **and** a post-merge hook (git runs post-commit for ordinary
   commits only; merges need post-merge), so a session always clones current branches.

**Control.** One real steady session end to end: rows claimed → plans pushed → `END` → build lanes started from them.
Then one handback: the signal written → the session stops after its current item → its unstarted rows are free again.

## 5. Machine traps (Windows in particular; check the equivalents on other systems)

1. **A scheduled task ends every process it started when the task ends.** Processes launched from a periodic tick
   die seconds later. → Start long-lived children outside the task: on Windows, create them through WMI
   (`Win32_Process.Create`). Relaunch anything that was started but never wrote its status.
2. **Memory runs out before allowance does.** With about 10 lead lanes and 5 build lanes, commit memory sits near
   90%. → Every launcher has a memory guard (refuse to start at about 90% commit). The watchdog starts nothing
   new at about 85%, and retries memory-refused lanes once it is lower. The owner decides the lane cap by RAM.
3. **Checks in git hooks can hang under memory pressure**, and every commit waits behind them. → Give each hook
   check a time limit (for example 120 s). On a timeout, warn and let the commit through; the next commit runs
   the check again. The watchdog also ends checks older than about 10 minutes.
4. **Wildcard walks over many worktrees are slow** (minutes with hundreds of worktrees). → Check known paths directly.
5. **Argument splitting.** Process launchers split arguments that contain spaces unless they are quoted.
   A script that dies on a bad parameter dies *before* it writes its log. → Quote them, and check that the log appeared.

## 6. Race discipline

1. **A commit counts only when it landed.** "Checks passed" is not "committed"; a ref race can still refuse the commit.
   Read the result, and if the commit did not land, restore the paths the edit touched.
2. **One claim per row.** Every planner (lead, cloud helper, build provider) claims a row on the board before
   starting and never plans a claimed row.
   - A queued build-provider planning lane **yields**: before every start it checks that its claim still stands
     and that no lead plan exists, and drops itself otherwise.
   - The build provider's own prompt starts with the same check.
   - The lead provider may take over a queued lane's row by rewriting the claim, but never while that lane runs.
3. **Guarded commits wait** while a merge is in progress or the trunk is dirty, commit only their own paths,
   and never sweep someone else's staged files.

## 7. Measure usage and credits

- Read allowance from the provider's own record or usage endpoint, never from text in a log. (A log can quote
  another session's "limit reached" message and raise a false alarm.)
- Record, per tick: the short-window and weekly utilisation, and any separate credit bucket (limit, used, remaining).
  Read tokens inside the script and never print them.
- Use the numbers to decide pacing (sections 1 and 4), the cap (section 5), and when to hand back.
- State the measurement with its scope ("one session, one observation") when it contradicts what the owner believes.

**Control.** The meter prints numbers that change when a session runs, and do not change when none runs.
