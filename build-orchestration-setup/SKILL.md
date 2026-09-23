---
name: build-orchestration-setup
description: Set up and run a multi-agent app build (Claude/Codex/other lanes, coordinator, board, failover, dashboard, handovers) via a guided questionnaire, once idea, spec and architecture exist.
---

# Build Orchestration Setup

Turns an app that has an idea, a spec and an architecture into a running, self-reporting multi-agent build:
spec made unambiguous and prioritised, workspace prepared, providers and models chosen, agents that never do
a task twice and never lose state, automatic restart and provider failover on usage limits, and reporting the
owner can read without asking.

It does NOT write the idea, the spec or the architecture. It starts where those end.

## Kit and references
This skill ships with a kit (templates + a stdlib-only Python tool, `orch.py`) and reference files:
- `references/01-spec-clarity.md` ... `08-lessons-learned.md` - the detail behind each phase below
- `kit/templates/` - board, rules, session prompt, agent roles, hooks, config, schedulers
- `kit/tools/orch.py` - `init`, `preflight`, `supervise` (rounds + failover), `board`, `check-not-done`,
  `safe-commit`, `redact`, `snapshot`, `live-view`

If `references/` and `kit/` are not next to this file, get them from the public repository
`https://github.com/christian281150/agent-build-orchestrator` (folder `build-orchestration-setup/`), or ask
the user where their copy is. If neither is possible, generate the files from the descriptions in this file
and the phase notes, and say that you did.

## How to talk to the owner
- Ask before assuming their technical level. If they are not from an IT background: write every
  abbreviation with its full term in brackets on first use - "CLI (Command Line Interface)" - and say what a
  thing does, not only its name.
- Questions go through `AskUserQuestion`: max 4 per call, 2-4 options, the recommended option first with
  "(Recommended)". Never ask what the documents or the code can answer.
- Unattended: take the recommended options, log each as a decision, state the assumptions at the top.

---

## Phase 0 - Gate: prerequisites (hard stop)
Ask where these live; read them fully.

| Required | Minimum content |
|---|---|
| Idea / product brief | who uses it, the core job, what "v1 done" looks like |
| Functional spec | features, screens, flows, data, acceptance criteria per feature |
| Architecture | stack, repo layout, hosting, database, auth, integrations, environments |

Missing a required one -> stop. Name it. Offer dictation: the owner talks it through for 10-20 minutes with
speech-to-text, you turn the transcript into the document. Do not run later phases on a missing spec.

Then write the **intake summary**: work items found, rough size in agent-hours, dependencies, risk flags
(writes to live, money, credentials, publishing), the machine (OS, RAM), subscriptions the owner has.

## Phase 1 - Clarity sprint (spend the time here)  -> `references/01-spec-clarity.md`
Every ambiguity left now comes back as wrong code, a 3 a.m. question, or two lanes guessing differently.
1. Readiness scorecard: fill `SPEC-READINESS.md` (12 dimensions, 0/1/2).
2. Ambiguity hunt: feature by feature, one question at a time with a recommended answer; write each answer
   into the spec in the same turn; decisions into the decisions log with the option not taken.
3. Prioritise in `SCOPE.md`: **P1** (the core job fails without it), **P2** (users notice), **P3** (later),
   an explicit **not-in-v1** list, and **parked** items with an un-park trigger. If P1 is more than ~40% of
   the hours, offer cuts.
4. Acceptance criteria (given / when / then) for every P1 feature.
5. Pre-made decisions (auth, hosting, database, identities, naming, test data, how "missing" shows, data that
   may never leave).
6. Reserved actions - what only the owner may do.
**Gate:** P1 dimensions all 2, total >= 80%, P1 open questions empty, not-in-v1 list exists, reserved agreed.

## Phase 2 - Questionnaire  -> `references/02-questionnaire.md`
Seven rounds; record answers + options not taken in `orchestration-config.md`, machine settings in
`orchestration.toml`.
1. **Where and who** - execution home (local CLI + supervisor / cloud sessions / chat-driven / hybrid);
   engines (Claude only / Claude plans+merges, others build approved plans / other-heavy); OS; human
   involvement.
2. **Scale** - parallel Claude leads (2-3 / 4-6 / up to 10); external build lanes; round length (3 h refill
   window recommended); planning lanes ahead of builders.
3. **Models** - thinking roles, doing roles, other providers' tiers (never the top tier by default); budget
   guard (stop new work at 97%).
4. **Limits and failover** - on a limit: others keep building approved plans, merge gate catches up
   (recommended) / pause / switch coordinator; fallback order; who may merge (one gate); chat-only providers
   as a redacted copy-paste desk or not at all.
5. **Guardrails** - decide-and-log vs ask; reserved actions (multiSelect); git model; commit attribution.
6. **Reporting** - board in repo; dashboard artifact on a schedule; local live view; handovers and alerts.
7. **The owner** - technical vocabulary; anything the build must never / always do.
Show a one-screen summary, get one confirmation.

## Phase 3 - Workspace setup  -> `references/03-workspace-setup.md`
Order matters - the first three are cheap now and expensive later:
1. Folder layout: repo; worktrees as a sibling folder; run state and data outside the repo.
2. `git init -b main` -> `python <skill>/kit/tools/orch.py init <repo> --name <app> --author-name ...
   --author-email ...` (copies templates + tools, never overwrites, wires hooks, sets the git author).
   `.gitattributes` before the first hash; `.gitignore` covers secrets, captures, data, run state.
3. Credentials as user-scope environment variables, typed by the owner, never in chat; one per identity;
   names in `[safety].required_env`; stripped from build-only providers.
4. Tools and versions: provider CLIs logged in; every command in `orchestration.toml` checked against
   `<cli> --help`; the exact Python interpreter; skills that agent files name installed.
5. Test environment: synthetic data; test database on its own port; strict mode where "unavailable" fails.
6. claude.ai Project with the instructions template (first action every session; the repo is the truth).
7. Scheduling (unattended): supervisor at logon with restart on failure (`tools/scheduling/`), PC never
   sleeps while plugged in, dashboard scheduled task.

## Phase 4 - Fill the kit
- `python tools/orch.py unfilled` lists every `{{TODO}}`; fill each from Phases 1-2.
- `RULES.md` section 2 = reserved actions. `SESSION-PROMPT.md` = N leads, planning lanes on/off.
- Agent files: set `model:` per role from Round 3 (aliases, not versions); `skills:` only if installed.
- `orchestration.toml`: providers, priorities, roles, commands, `max_parallel`, `strip_env`, thresholds,
  round window, forbidden trailers, redact terms (server names, domains, client names).
- Commit on `feat/orchestration-setup`, merge when preflight passes.

## Phase 5 - Wave breakdown -> the board
IDs `W<wave>-<n>`, fixes `F<n>`. Each row: item, **prio**, wave, lane, estimate (agent-hours), deps, status.
- Wave 0 foundations (repo, CI, environments, schema, auth, test harness, synthetic data)
- Wave 1 the core loop end to end (all P1)
- Waves 2-3 breadth by priority; Wave 4 hardening (security review, performance, backup/restore rehearsal)
- Go-live: reserved actions batched for the owner
Size rule: > ~15 files or "and then" twice -> split. Mark the critical path; say how many items it blocks.
`python tools/orch.py board validate` must pass.

## Phase 6 - Prove it
`python tools/orch.py preflight` -> all PASS (explain each WARN). Hook controls: a staged `.har` and a
fake secret must be refused. One dry round on a trivial P1 item. Paste verbatim results into `HANDOVER-1.md`.

## Phase 7 - Run  -> `references/04-roles-and-pipeline.md`, `06-provider-failover.md`
- **Local unattended:** the OS scheduler starts `orch.py supervise`. Each pass: re-exec if code/config
  changed -> STOP file? exit -> best available coordinator runs one round (refill until the window ends, then
  let leads finish, end with `ROUND RESULT:`) -> classify (ok / limited / error) -> push -> next.
  All coordinators limited -> fallback build lanes on other providers for `plan-approved` rows with a
  `build-brief.md` (own branch, never main) -> sleep until the earliest reset -> the next round gates them
  first (`GATED: <ID> accepted|rejected`). Same failure 3x -> stop with `BLOCKED.txt`.
- **Cloud sessions:** one session per lane on its branch; one merge-gate session; board in the repo;
  scheduled tasks start rounds.
- **Chat-driven:** the chat is the coordinator; dispatch roles with the Agent tool, pasting role text + the
  shared protocol (repo agent files don't load in chat).
- **Monitoring chat:** adjusts rules, never kills a running coordinator, commits only via `safe-commit`.
Pipeline per item: check-not-done -> librarian -> planner -> plan reviewer (max 2 rounds) -> build ->
task reviewer -> integrator -> merge gate -> board `done` with commit + counts -> decisions logged.

## Phase 8 - Report  -> `references/07-reporting.md`
Board (truth) + decisions log; metric = estimated hours of done items / all non-parked, headline P1;
dashboard artifact fed by a scheduled read-only `snapshot`; optional local live view; a handover at every
session switch; owner decisions as one batch on the board.

## Standing rules for every agent  -> `references/05-memory-and-no-double-work.md`
- Start ritual: newest handover -> git log/status -> board -> decisions -> supervisor state. Measure, don't trust.
- Before any item: `check-not-done <ID>`. After it, same turn: commit -> board with evidence -> decisions -> next.
- Status only on the board. When you change the world, change the document in the same commit.
- Decisions are closed; never overrule a logged one - solve inside it or flag it in one line.
- Two legal endings for autonomous work: queue empty, or blocked on the owner after everything unblocked.
- Evidence: measured, a control that can go red, the connected identity checked, scope and time on every
  count, "not verified" named, corrections stated.
- One worktree per lane until merged; commit continuously; side sessions use `safe-commit`.
- Credentials never in chat, logs, commits or prompts; anything leaving the machine is redacted with a
  proven scanner.
- Lessons: `references/08-lessons-learned.md` - read it once before Phase 4.

## Done means
- Clarity gate passed (`SPEC-READINESS.md`, `SCOPE.md` with P1/P2/P3 and not-in-v1)
- `orchestration-config.md` and `orchestration.toml` filled; `unfilled` reports nothing
- Board populated and valid; critical path named
- Preflight all PASS (verbatim), hook controls red, one dry round green
- Supervisor scheduled (or sessions set up), dashboard live, `HANDOVER-1.md` in repo and Project
- Final report: what exists, how the build starts and stops, what is reserved for the owner, what was not verified
