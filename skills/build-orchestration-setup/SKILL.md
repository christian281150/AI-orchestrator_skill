---
name: build-orchestration-setup
description: Orchestrates the BUILD of an app with several AI coding tools once idea, spec and architecture are settled - readiness gate, setup questionnaire, skills plan, workspace, parallel lanes, one merge gate, provider failover, reporting. Use when a finished spec should be built by multiple agents (Claude, Codex, others), possibly unattended. Not for writing or aligning specs.
license: MIT
compatibility: Toolkit needs git and Python 3.11+ (standard library only). Works with any agent that loads SKILL.md folders; the unattended supervisor drives any CLI coding agent.
metadata:
  author: christian281150
  version: "1.6.0"
  repository: https://github.com/christian281150/AI-orchestrator_skill
---

# Build Orchestration Setup

## Read this first: what this skill is - and is not
**It is** the process for *building* an app with a team of AI agents: who builds what, with which tool, in
what order, how work is checked, merged, recovered after usage limits, remembered across sessions and reported.

**It is not** a tool to work out *what* to build. It starts only when the **idea, the functional spec (features
and acceptance criteria) and the architecture are settled**. It never writes, refines or aligns specs. If the
spec has gaps, the skill stops and hands back a gap list for the owner's own spec work. Say this plainly to the
user at the start, before anything else.

- **Use it when** a settled spec should be built by several agents (one tool or several) - in parallel,
  possibly unattended - and the owner wants control over build order, cost and what reaches main.
- **Don't use it** for deciding features or architecture, for a single small change, or for a one-file script.

Guiding principle for every proposal: **best quality at the lowest cost** - cheapest adequate model per role,
each tool on the work it does best, review depth by risk, the fewest skills per task, plans before builds,
never pay twice.

## Kit and references
- `references/01-readiness-gate.md` ... `11-long-running-builds.md` - the detail behind each phase (load on demand).
- `assets/templates/` - board, rules, coordinator prompt, engine-neutral roles, skills plan, ledgers, hooks,
  config, schedulers.
- `assets/profile.toml` - the owner's customization file (standing preferences; see Phase 2).
- `scripts/orch.py` - standard-library Python 3.11+ toolkit: `doctor`, `init`, `unfilled`, `profile`, `skills`, `preflight`,
  `supervise`, `keeper`, `gap`, `board`, `check-not-done`, `safe-commit`, `redact`, `snapshot`, `live-view`.

If `references/`, `scripts/` and `assets/` are not next to this file, get them from
`https://github.com/christian281150/AI-orchestrator_skill` (folder `skills/build-orchestration-setup/`), or ask
the user where their copy is. If neither works, generate the files from this file and say so.

## Adapt it - four adoption levels
Everything is optional beyond level 1. Recommend the lowest level that fits; each builds on the one before.

| Level | Adds | Fits |
|---|---|---|
| 1 Rituals | board, decisions log, ledgers, handovers, rules, roles - agents in one chat or CLI session | small builds, first try |
| 2 Unattended | supervisor (rounds, restart, STOP), git hooks, preflight | one provider, runs while you're away |
| 3 Multi-provider | build providers, failover, knowledge-gap reconciliation | two or more AI subscriptions |
| 4 Full | keeper every ~10 min, cloud planners, idle planning, dashboard | long builds, maximum throughput |

## How to talk to the owner
- Ask their technical level; if they are not from an IT background, write every abbreviation with its full
  term on first use - "CLI (Command Line Interface)" - and say what a thing does.
- Questions go through `AskUserQuestion`: max 4 per call, 2-4 options, recommended option first with
  "(Recommended)". Never ask what the documents, the code or the machine can answer - measure it.
- Unattended: take the recommended options, log each as a decision, list the assumptions at the top.
- Provider-neutral wording: **lead provider** (plans, reviews, merges - one), **build providers** (implement
  approved plans), **cloud sessions** (remote, own credit), **chat desk** (no CLI, copy-paste).

---

## Phase 0 - Prerequisites (hard stop)
Ask where these live and read them fully. All three must exist **and be settled**:

| Required | Minimum content |
|---|---|
| Idea / product brief | who uses it, the core job, what "v1 done" looks like |
| Functional spec | features, screens or interfaces, flows, data, acceptance criteria per feature |
| Architecture | stack, repo layout, hosting, storage, auth, integrations, environments |

Missing or still under discussion -> stop, say which, and explain that this skill starts after spec work.
(If the owner has the knowledge but not the documents, they can dictate it for 10-20 minutes and turn the
transcript into spec documents first - outside this skill.)

Then write the **intake summary**: work items found, rough size in agent-hours, dependencies, risk flags
(writes to live, money, credentials, publishing), the machine (OS, RAM - measured), the AI tools and
subscriptions the owner has. Measure the machine with `orch.py doctor --project <repo>` (works before any
config exists); walk a non-technical owner through each FAIL's "Fix:" before going on.

## Phase 1 - Readiness gate (a check, not spec work) -> `references/01-readiness-gate.md`
1. Score `SPEC-READINESS.md` (12 dimensions, 0/1/2), citing where each is written.
2. Gaps become a **gap list** returned to the owner - never proposals for feature content.
3. **Build order:** map the spec's priorities to P1 / P2 / P3 (+ not-in-v1, parked) in `SCOPE.md`; if the spec
   has none, the owner tags them. The coordinator never starts P2 while a ready P1 exists.
4. **Build-time decisions** (how, not what): identities, test data, naming, data that may never reach an AI
   provider, reserved actions.
**Gate:** P1 dimensions all 2, total >= 80%, every P1 feature has acceptance criteria in the spec, no P1 gap.
Fail -> stop and hand over the gap list.

## Phase 2 - Setup questionnaire and skills plan -> `02-questionnaire.md`, `09-skills-and-cost-quality.md`, `10-tool-routing.md`
Ten short rounds, all about *how* to build. Record answers + options not taken in `orchestration-config.md`,
machine settings in `orchestration.toml`.
**First read the owner's profile:** `orch.py profile show --project <repo>` (home `~/.ai-orchestrator/profile.toml`,
project `.ai-orchestrator.toml` wins). Skip every item it answers, list those answers once in the summary for
confirmation, and ask only the rest. `orch.py profile check` must be clean before its values are used.
At the end, run `orch.py profile learn` (shows which answers would fill EMPTY profile values; set values are
never overwritten) and apply it with `--write` on the owner's yes - the next project asks almost nothing.
1. Project and people - project type (decides lanes), who decides, vocabulary, date vs quality vs cost.
2. Where it runs - local CLI + supervisor / cloud sessions / chat-driven / hybrid; OS; involvement;
   **adoption level 1-4**.
3. Providers - tools and subscriptions; the lead provider; build providers; one merge gate.
4. Scale - parallel lead lanes; build lanes; round length (3 h refill window recommended); planning lanes.
5. Cost and quality - optimise for best quality at the lowest cost; model tier per role; budget guard (97%).
6. Skills - scan installed (`orch.py skills`); the owner's ideas per task/topic (yes / partly / no); fewest
   skills per task type; project skills as rules emerge.
7. Limits and failover - build providers continue approved plans while the lead is limited; fallback order;
   automatic restart; chat desk or not.
7b. **Which tool does what** - show the routing table from `10-tool-routing.md` with the owner's tools; cloud
   planners (steady / accelerate / handback); idle build providers planning safe items; keeper.
7c. Running for days - planning pace, fix routing, lane cap by load, watchdog extras (`11-long-running-builds.md`).
8. Guardrails - decide-and-log; reserved actions; git model; commit attribution.
9. Reporting - board in repo; dashboard on a schedule; local live view; handovers and alerts.
10. "Anything the build must never / always do?"
Then build `SKILLS-PLAN.md` (task type -> fewest skills -> source -> engines -> model tier -> why). One-screen
summary, one confirmation.

## Phase 3 - Workspace -> `references/03-workspace-setup.md`
Order matters; the first three are cheap now and expensive later.
1. Folders: repo; lane worktrees as a sibling; run state and data outside the repo.
2. `git init -b main` -> `python <skill>/scripts/orch.py init <repo> --name <app> --author-name ...
   --author-email ...` (templates + tools, never overwrites, hooks, git author). `.gitattributes` before the first hash.
3. Credentials as user-scope environment variables, typed by the owner, never in chat; stripped from build providers.
4. Tools: every CLI logged in; every command in `orchestration.toml` checked against `<cli> --help`; exact interpreters.
5. Skills from `SKILLS-PLAN.md` installed for every engine that runs the role (`orch.py skills`: none missing).
6. Test environment: synthetic data; test database on its own port; "unavailable" counts as a fail.
7. A shared project/memory for chat sessions: first action every session; the repo is the truth.
8. Level 2+: supervisor at logon with restart (`tools/scheduling/`), machine never sleeps; level 4: keeper every
   10 minutes, cloud service connected to the git host **before** cloud sessions start, push on commit.

## Phase 4 - Fill the kit
- `orch.py unfilled` lists every `{{TODO}}` - fill from Phases 1-2.
- `ROLES.md` is the engine-neutral source; render it per engine (`.claude/agents/*.md`, `AGENTS.md`, ...), set
  the model tier, name only planned skills.
- `RULES.md` section 2 = reserved actions; `SESSION-PROMPT.md` = lanes, planning lanes, knowledge-gap rule.
- `orchestration.toml`: providers (kind, priority, roles, commands, `max_parallel`, `strip_env`, `usage_command`),
  `[keeper]`, round window, trailers, redact terms. Drop what the chosen level doesn't use.
- Commit on `feat/orchestration-setup`; merge when preflight passes.

## Phase 5 - Wave breakdown -> the board
IDs `W<wave>-<n>`, fixes `F<n>`; each row: item, prio, wave, lane, estimate (agent-hours), deps, status. Plans
state a **risk tier** (1 docs/tests, 2 normal code, 3 security/money/data/live) and `Authored-by:`.
Wave 0 foundations -> Wave 1 the P1 core loop end to end -> Waves 2-3 by priority -> Wave 4 hardening -> go-live
(reserved actions batched for the owner). Split at ~15 files or "and then" twice. Name the critical path.
`orch.py board validate` must pass.

## Phase 6 - Prove it
`orch.py preflight` all PASS (explain each WARN); hook controls refuse a staged capture and a fake secret; one
dry round on a trivial P1 item; verbatim results into `HANDOVER-1.md`.

## Phase 7 - Run -> `references/04-roles-and-pipeline.md`, `06-provider-failover.md`, `10-tool-routing.md`
- **Supervisor** (level 2+): re-exec on change -> STOP? -> best available coordinator runs one round (refill
  until the window ends, end with `ROUND RESULT:`) -> classify ok / limited / error -> push -> next. All
  coordinators limited -> build providers take approved plans on their own branches; the next round gates them
  first (`GATED: <ID> accepted|rejected`). Same failure 3x -> `BLOCKED.txt`.
- **Keeper** (level 4, every ~10 min): restart limit-stopped lanes (capped per day); build lanes when no round
  runs; idle planning of safe items; cloud planners steady / accelerate / handback above a credit floor.
- **Every round starts with `orch.py gap`**: work the lead did not see -> `REVIEWERS=<n>`; foreign plans get a
  gap summary, a blind lead re-plan and an arbiter's ruling before they are built.
- **Running for days:** just-in-time planning, fix routing, lane cap by load, watchdog, restart reconciliation,
  cloud helpers, machine traps, race discipline, usage measurement -> `references/11-long-running-builds.md`.
- Cloud sessions, chat-driven mode and a monitoring chat: see the references.
Pipeline per item: check-not-done -> librarian -> planner (risk tier, skills, authored-by) -> plan reviewer
(max 2 rounds) -> build -> task reviewer (depth by tier) -> integrator -> merge gate -> board `done` with commit +
counts -> decisions logged.

## Phase 8 - Report -> `references/07-reporting.md`
Board (truth) + decisions log; metric = estimated hours done / all non-parked, P1 headline; dashboard fed by a
scheduled read-only `snapshot`; optional local live view; a handover at every session switch; owner decisions
as one batch on the board.

## Standing rules for every agent -> `references/05-memory-and-no-double-work.md`
- Start ritual: newest handover -> git log/status -> board -> decisions -> supervisor/keeper state. Measure, don't trust.
- Before any item `check-not-done <ID>`; after it, same turn: commit -> board with evidence -> decisions -> next.
- Status only on the board. Change the world -> change the document in the same commit.
- Decisions are closed; never overrule a logged one - solve inside it or flag it in one line.
- Autonomous work ends only when the queue is empty or it is blocked on the owner after everything unblocked.
- Evidence: measured, a control that can go red, connected identity checked, scope and time on every count,
  "not verified" named, corrections stated.
- One worktree per lane until merged; side sessions commit through `safe-commit`.
- Credentials never in chat, logs, commits or prompts; anything leaving the machine passes a proven scanner.
- A rule explained twice becomes a project skill. Read `references/08-lessons-learned.md` once before Phase 4.

## Done means
- Prerequisites settled; readiness gate passed (`SPEC-READINESS.md`, `SCOPE.md` with build order)
- `orchestration-config.md`, `SKILLS-PLAN.md`, `orchestration.toml` filled; `unfilled` and `skills` report nothing missing
- Roles rendered for every engine; board valid; critical path named
- Preflight all PASS, hook controls red, one dry round green
- Supervisor / keeper scheduled for the chosen level, dashboard live, `HANDOVER-1.md` saved
- Final report: what exists, how the build starts and stops, what is reserved for the owner, what was not verified
