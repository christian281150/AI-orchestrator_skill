# Roles, lanes, pipeline, rounds

## Roles (agent files in `.claude/agents/`, Codex equivalents in `.codex/agents/`)

| Role | Tier | Does | Never |
|---|---|---|---|
| Coordinator (the round itself) | thinking | picks items, dispatches leads, merge gate, keeps the board honest | writes product code |
| Lane lead | thinking | one item end to end in its own worktree | edits another lane's files |
| Librarian | doing | exact paths, signatures, facts for the planner (fact vs inference) | changes anything |
| Planner | thinking | plan, max 6 tasks, each with files, done-looks-like, verify command | invents a table/column/endpoint |
| Plan reviewer | thinking | independent adversarial review: APPROVED / CHANGES REQUIRED | approves without evidence |
| Implementer | doing | one task: failing test first, smallest complete change, verify, commit | weakens a test |
| Integrator | doing | merges main INTO the lane branch, full suite, verbatim counts | merges into main |
| Task reviewer | thinking | tries to break each finished task; breaks the control to see red | says "looks fine" |
| Arbiter | thinking | settles disputes, logs the ruling | overrules a logged decision |
| Unblocker | small/fast | names the likely cause of a stuck lane and the smallest test | implements |
| Documentarian | doing | makes the repo readable; no status in docs | changes behaviour |
| Relay (per external build lane) | smallest | starts an external provider's lane, waits, relays | anything else |

## Lanes = file ownership
A file belongs to exactly one lane (e.g. backend / database-migrations / frontend / infra-docs). Another lane
needing a change there sends a request through the coordinator. The seam between backend and frontend is a
contract (schema + generated client); a contract change is announced before it lands. Two sessions or two
lanes editing one working tree is how conflicts and lost work happen - one worktree per lane.

## Dispatch shape - every dispatch, in this order
1. The single outcome, and how the receiver knows it is met.
2. Files it may change, and must not.
3. What to read first, by path.
4. Constraints not obvious from the code.
5. The report shape: what now works / files + reason / verbatim test counts / not done / found but not
   fixed (file:line) / not verified.
Never "look at X and improve it". A task that failed twice for the same reason was described wrongly -
back to the planner, not a third attempt.

## Pipeline per item
1. Row is `ready` (dependencies `done`), `check-not-done` gives a clean verdict.
2. Lead -> librarian (if context is missing) -> planner -> plan reviewer. Max 2 review rounds, then the lead
   rules and logs the ruling in the ledger.
3. Build: implementers per task (Claude), or an external build lane from `build-brief.md`.
4. Task reviewer per task.
5. Integrator: main merged into the branch, full suite green, counts verbatim (skips explained).
6. Coordinator merge gate -> `git merge --no-ff` -> board `done` with commit hash + counts -> decisions logged.

**Planning lanes:** ~2 slots write `PLAN ONLY` (plan approved + self-contained `build-brief.md`), row status
`plan-approved`. Builders on other providers take those first. Pause planning while 10+ approved plans wait.

## Sizing
- Budget per lead including helpers: ~150k tokens. More than ~15 files or "and then" twice -> split.
- Helper cap per round (e.g. `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) and the per-lead helper budget:
  `max(1, floor((helper_cap - leads - relays) / leads))`. Change the cap -> `git grep` every place the number
  or the formula appears.
- RAM: measure one round before raising parallelism. 10 leads on 16 GB ran near the memory limit.

## Rounds
- Each round is a fresh process with empty context; the board carries state between rounds.
- A coordinator's context grows every turn and every turn re-reads it all: measured 25k -> 129k tokens over
  100 turns, ~11M tokens in one long round, against ~25k to start a new round. **Short rounds (one wave, or a
  2-3 h refill window) are cheaper and keep every agent inside its designed band.**
- The round refills lanes until the window ends, then starts nothing new and lets running leads finish.
- Background work: in print/headless mode some CLIs stop background work after a ceiling (one CLI: 600 s by
  default) - set the ceiling env var, or dispatch in the foreground. A background *agent* keeps a headless
  round alive; a background *shell command* may not. Verify on your version.
- Never kill a running coordinator - its leads die with it and their work comes back half-done. Rule files
  and agent files are re-read at every round start; the supervisor re-execs itself between rounds when its
  code or config changes. So an edit lands by itself one round later.
- Some external agents spawn their own helpers - count them in RAM planning.
