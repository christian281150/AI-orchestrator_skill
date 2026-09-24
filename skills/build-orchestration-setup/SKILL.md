---
name: build-orchestration-setup
description: Set up and run a multi-agent software build for any app and any AI coding tools - spec clarity, questionnaire, skills plan, workspace, lanes, failover, reporting - once idea, spec and architecture exist. Use when the user wants several AI agents (Claude, Codex, others) to build an app from a spec in parallel, unattended, without repeated work.
license: MIT
compatibility: Toolkit needs git and Python 3.11+ (standard library only). Works with any agent that loads SKILL.md folders; the unattended supervisor drives any CLI coding agent.
metadata:
  author: christian281150
  version: "1.2.1"
  repository: https://github.com/christian281150/agent-build-orchestrator
---

# Build Orchestration Setup

Turns an app that has an idea, a spec and an architecture into a running, self-reporting multi-agent build,
for any project type and any mix of AI coding tools:
- the spec is made unambiguous and prioritised
- the owner chooses how it runs, through a guided questionnaire
- skills are planned per task type
- the workspace is prepared
- agents never do a task twice and never lose state
- the build restarts itself and switches providers on usage limits
- reporting lets the owner see where the build is without asking

It does NOT write the idea, the spec or the architecture. It starts where those end.

Guiding principle for every proposal: **best quality at the lowest cost**. Use the cheapest adequate model per
role, review depth by risk, the fewest skills that cover each task, plans before builds, and never pay twice.

## Kit and references
This skill ships with a kit and reference files:
- `references/01-spec-clarity.md` ... `09-skills-and-cost-quality.md`: the detail behind each phase.
- `kit/templates/`: board, rules, coordinator prompt, engine-neutral roles, skills plan, ledgers, hooks,
  config and schedulers.
- `kit/tools/orch.py`: a toolkit of standard-library Python 3.11+ commands:
  - `init`, `unfilled`, `skills`, `preflight`
  - `supervise` (rounds and failover)
  - `board`, `check-not-done`, `safe-commit`
  - `redact`, `snapshot`, `live-view`

If `references/` and `kit/` are not next to this file, get them from the public repository
`https://github.com/christian281150/agent-build-orchestrator` (folder `skills/build-orchestration-setup/`), or ask
the user where their copy is. If neither is possible, generate the files from this file and say so.

## How to talk to the owner
- Ask their technical level; never assume it. If they are not from an IT background, write every
  abbreviation with its full term in brackets on first use ("CLI (Command Line Interface)") and say what a
  thing does, not only its name.
- Put questions through `AskUserQuestion`: max 4 per call, 2-4 options, the recommended option first with
  "(Recommended)". Never ask what the documents, the code or the machine can answer. Measure instead.
- If the owner is away, take the recommended options, log each one as a decision, and list the assumptions at the top.
- Stay provider-neutral. The **lead provider** plans, reviews and merges. **Build providers** implement approved plans.
  Which tools fill which role is the owner's choice.

---

## Phase 0 - Gate: prerequisites (hard stop)
Ask where these live and read them fully:

| Required | Minimum content |
|---|---|
| Idea / product brief | who uses it, the core job, what "v1 done" looks like |
| Functional spec | features, screens or interfaces, flows, data, acceptance criteria per feature |
| Architecture | stack, repo layout, hosting, storage, auth, integrations, environments |

If a required one is missing, stop and name it. Offer dictation: the owner talks it through for 10-20
minutes with speech-to-text, and you turn the transcript into the document.

Then write the **intake summary**:
- the work items found, their rough size in agent-hours, and their dependencies
- risk flags: writes to live, money, credentials, publishing
- the machine: OS and RAM, measured
- the AI tools and subscriptions the owner has

## Phase 1 - Clarity sprint (spend the time here) -> `references/01-spec-clarity.md`
Every ambiguity left now comes back later as wrong code, a question at 3 a.m., or two lanes guessing differently.
1. Readiness scorecard: fill `SPEC-READINESS.md` (12 dimensions, each scored 0/1/2).
2. Ambiguity hunt: go feature by feature, one question at a time, each with a recommended answer. Write every
   answer into the spec in the same turn. Log each decision with the option not taken.
3. Prioritise in `SCOPE.md`:
   - **P1**: the core job fails without it
   - **P2**: users notice if it's missing
   - **P3**: later
   - a **not-in-v1** list
   - **parked** items, each with the trigger that un-parks it

   If P1 is more than about 40% of the hours, offer cuts.
4. Acceptance criteria (given / when / then) for every P1 feature.
5. Pre-made decisions: auth, hosting, storage, identities, naming, test data, how "missing" is shown, and which data may never leave.
6. Reserved actions: what only the owner (or which approver) may do.

**Gate:** every P1 dimension scores 2, the total is at least 80%, the P1 open questions are empty, the not-in-v1
list exists, and the reserved actions are agreed.

## Phase 2 - Questionnaire and skills plan -> `references/02-questionnaire.md`, `09-skills-and-cost-quality.md`
Nine short rounds. Record the answers, with the options not taken, in `orchestration-config.md`. Machine
settings go in `orchestration.toml`.
1. **Project and people**: project type (decides the lanes); who decides; the owner's vocabulary; date vs quality vs cost.
2. **Where it runs**: local CLI agents with the supervisor, cloud sessions, chat-driven, or hybrid; the OS; how involved the owner is.
3. **Providers**: which tools and subscriptions exist; the lead provider; the build providers; who may merge (one gate).
4. **Scale**: parallel lead lanes; build-provider lanes; round length (a 3 h refill window is recommended); planning lanes.
5. **Cost and quality**: what to optimise for (best quality at the lowest cost is recommended); model tier per role; budget guard (97%).
6. **Skills**:
   - What is already installed? Scan it with `orch.py skills`.
   - Does the owner already know which task or topic needs which skill? Yes / partly (use their ideas and
     propose the rest) / no (propose everything).
   - What to optimise the proposal for: the fewest skills per task type at the best quality per cost is recommended.
   - Project-specific skills: create them as recurring rules emerge.
7. **Limits and failover**: what happens on a lead-provider limit (build providers continue on approved plans, and the gate
   catches up); fallback order; automatic restart; chat-only models (a redacted desk, or not at all).
8. **Guardrails**: decide-and-log vs ask; reserved actions; git model; commit attribution.
9. **Reporting**: the board in the repo; a dashboard on a schedule; a local live view; handovers and alerts.

Closing question: "Anything the build must never do, or must always do?"

Then **build the skills plan** in `SKILLS-PLAN.md`:
- List the task types from the waves.
- Give each the fewest skills that cover it. Sources, in order: already installed, the owner's ideas, public
  collections, then a new project skill.
- For each, record the engines it must be installed for, the model tier, and one line on why this and not more.
- Plan project skills for the app's own rules: data access and identities, the API contract, test data,
  migration checks.

Show a one-screen summary of every answer plus the skills plan, then get one confirmation.

## Phase 3 - Workspace setup -> `references/03-workspace-setup.md`
Order matters. The first three steps are cheap now and expensive later.
1. Folder layout: the repo; lane worktrees in a sibling folder; run state and data outside the repo.
2. Run `git init -b main`, then `python <skill>/kit/tools/orch.py init <repo> --name <app> --author-name ... --author-email ...`.
   `init` copies templates and tools, never overwrites, wires the hooks and sets the git author.
   `.gitattributes` must exist before the first hash.
3. Credentials go in user-scope environment variables, typed by the owner and never in chat, one per identity.
   Strip them from build providers.
4. Tools: every provider CLI logged in, and every command in `orchestration.toml` checked against
   `<cli> --help` for the installed version. Use the exact interpreter paths.
5. Skills: install everything in `SKILLS-PLAN.md` for every engine that runs the role, from one source folder
   with pinned versions. `orch.py skills` must show none missing.
6. Test environment: synthetic data; a test database on its own port; a strict mode where "unavailable" counts as a fail.
7. A shared Project or memory for chat sessions, with the instructions template: first action every session,
   and the repo is the truth.
8. Scheduling (unattended): the supervisor starts at logon and restarts on failure (`tools/scheduling/`); the machine never
   sleeps while plugged in; the dashboard updates on a scheduled task.

## Phase 4 - Fill the kit
- `orch.py unfilled` lists every `{{TODO}}`. Fill each one from Phases 1-2.
- `ROLES.md` is the engine-neutral source. Render it into each engine's format: `.claude/agents/*.md`, and
  `AGENTS.md` or agent files for other engines. Set the model tier per role and name only the planned skills.
- `RULES.md` section 2 holds the reserved actions. `SESSION-PROMPT.md` holds the number of lanes and whether planning lanes are on.
- `orchestration.toml` holds:
  - providers, with priorities, roles, commands and `max_parallel`
  - `strip_env` and the thresholds
  - the round window
  - the forbidden trailers
  - the redact terms
- Commit on `feat/orchestration-setup`. Merge when preflight passes.

## Phase 5 - Wave breakdown -> the board
IDs are `W<wave>-<n>`; fixes are `F<n>`. Each row has: item, prio, wave, lane, estimate (agent-hours), deps and status. Each
plan later states a **risk tier** (1 docs/tests, 2 normal code, 3 security/money/data/live), which sets the
review depth and the reviewer model.
- Wave 0: foundations (repo, CI (continuous integration), environments, storage, auth, test harness, synthetic data).
- Wave 1: the core loop, end to end (all P1).
- Waves 2-3: breadth, by priority.
- Wave 4: hardening (security review, performance, backup and restore).
- Go-live: the reserved actions, batched for the owner.

Split an item that touches more than about 15 files or needs "and then" twice. Name the critical path. `orch.py board validate` must pass.

## Phase 6 - Prove it
- `orch.py preflight` shows all PASS; explain every WARN.
- Hook controls: a staged capture file and a fake secret must both be refused.
- Run one dry round on a trivial P1 item.
- Paste the verbatim results into `HANDOVER-1.md`.

## Phase 7 - Run -> `references/04-roles-and-pipeline.md`, `06-provider-failover.md`
- **Local unattended**: the OS scheduler starts `orch.py supervise`. Each pass:
  1. If the code or config changed, re-exec.
  2. If a STOP file exists, exit.
  3. The best available coordinator-capable provider runs one round. It refills lanes until the window ends,
     then lets them finish, and ends with `ROUND RESULT:`.
  4. Classify the round as ok, limited or error. Push, then go to the next pass.

  If every coordinator is limited, build providers take the `plan-approved` rows that have a `build-brief.md`.
  Each works on its own branch and never on main. The supervisor sleeps until the earliest reset. The next round
  gates that work first (`GATED: <ID> accepted|rejected`). The same failure three times in a row stops the
  supervisor with `BLOCKED.txt`.
- **Cloud sessions**: one session per lane, one merge-gate session, the board in the repo.
- **Chat-driven**: the chat is the coordinator. Dispatch each role with its role text and the shared protocol pasted in.
- **Monitoring chat**: adjusts rules, never kills a running coordinator, and commits only via `safe-commit`.

Pipeline per item:
1. check-not-done
2. librarian
3. planner, with risk tier and skills
4. plan reviewer (max 2 rounds)
5. build
6. task reviewer (depth by tier)
7. integrator
8. merge gate
9. board set to `done` with the commit and test counts; decisions logged

## Phase 8 - Report -> `references/07-reporting.md`
- The board is the truth, with the decisions log beside it.
- Metric: the estimated hours of done items divided by the hours of all non-parked items. P1 is the headline.
- A dashboard fed by a scheduled read-only `snapshot`.
- Optionally, a local live view.
- A handover at every session switch.
- The owner's decisions as one batch on the board.

## Standing rules for every agent -> `references/05-memory-and-no-double-work.md`
- Start ritual: newest handover, then git log and status, then the board, then decisions, then supervisor state. Measure; don't trust.
- Before any item, run `check-not-done <ID>`. After it, in the same turn: commit, update the board with evidence, log decisions, move on.
- Status lives only on the board. When you change the world, change the document in the same commit.
- Decisions are closed. Never overrule a logged decision: solve the problem inside it, or flag it in one line.
- Autonomous work has two legal endings: the queue is empty, or it is blocked on the owner after everything unblocked is done.
- Evidence: measured, with a control that can go red. Check the connected identity. Put a scope and a time on every count.
  Name what was not verified. State corrections.
- One worktree per lane until it is merged. Commit continuously. Side sessions use `safe-commit`.
- Credentials never go in chat, logs, commits or prompts. Anything leaving the machine goes through a proven scanner.
- A rule explained twice becomes a project skill.
- Read `references/08-lessons-learned.md` once before Phase 4.

## Done means
- The clarity gate is passed: `SPEC-READINESS.md`, and `SCOPE.md` with P1/P2/P3 and not-in-v1.
- `orchestration-config.md`, `SKILLS-PLAN.md` and `orchestration.toml` are filled; `unfilled` and `skills` report nothing missing.
- Roles are rendered for every engine in use; the board is populated and valid; the critical path is named.
- Preflight is all PASS (verbatim), the hook controls go red, and one dry round is green.
- The supervisor is scheduled (or the sessions are set up), the dashboard is live, and `HANDOVER-1.md` is saved.
- Final report: what exists, how the build starts and stops, what is reserved for the owner, and what was not verified.
