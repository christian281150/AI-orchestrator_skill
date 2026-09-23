# Phase 2 - The orchestration questionnaire

Seven rounds, max 4 questions per `AskUserQuestion` call, 2-4 options each, the recommended option first
with "(Recommended)". Derive the recommendation from the intake (Phase 0) and the spec - do not default
blindly. Skip any question the spec already answers. Unattended? Take the recommendations and log each as a
decision. Record every answer, with the options not taken, in `docs/coordination/orchestration-config.md`,
and the machine-readable part in `orchestration.toml` (key shown in brackets).

## Round 1 - Where and who

**1.1 Execution home** - where do the agents run?
| Option | Choose when | Trade-off |
|---|---|---|
| Local CLI (Command Line Interface) on the owner's PC, unattended rounds via the supervisor | long build, local database, many parallel lanes, Windows/Mac tooling | PC must stay on and awake; RAM limits parallelism |
| Cloud coding sessions (e.g. Claude Code on the web), one per lane | PC can be off; repo on GitHub; no local-only resources | no local database; each session is separate; merge gate needs its own session |
| Chat-driven (Cowork / claude.ai with subagents) | small build (< ~15 items), owner wants to watch | chat context fills up; agent files in the repo don't load - role text is pasted |
| Hybrid: local rounds build, a chat session monitors and adjusts rules | the default for anything larger than a week | two places to look - START-HERE says which wins |

**1.2 Engines** [providers]
- Claude only
- Claude plans, reviews and merges; Codex (and/or others) build approved plans (**recommended** when the
  owner has both subscriptions: doubles build capacity, keeps one merge gate)
- Codex-heavy: Claude only reviews and merges

**1.3 Machine and shell** - Windows + PowerShell / macOS / Linux / cloud only. (Decides scheduler template,
encoding traps, path style.)

**1.4 Human involvement** - unattended rounds, owner approves only reserved actions (**recommended**) /
owner approves each merge wave / interactive pair-building.

## Round 2 - Scale and pace

**2.1 Parallel Claude leads per round** [SESSION-PROMPT N, providers.claude.max_parallel]
2-3 (8 GB RAM, cautious budget) / 4-6 (**recommended** start, 16 GB) / up to 10 (16+ GB, measured headroom,
large weekly allowance). Start lower and raise after measuring RAM and allowance burn for one round.

**2.2 Build lanes on other providers** [providers.<x>.max_parallel] - 0 / up to 3 / up to 5 / up to 10.
Each one also holds a Claude slot if a Claude relay agent waits on it.

**2.3 Round length** [rounds.window_minutes] - 1 h / 3 h refill window, then running leads finish
(**recommended**) / until the queue is empty. Short rounds are cheaper: a coordinator's context grows every
turn and every turn re-reads all of it; a fresh round costs a small fixed amount.

**2.4 Planning lanes** - reserve ~2 Claude slots to write approved plans + build briefs ahead of the
builders, so other providers never idle (**recommended** when 2.2 > 0) / no planning lanes.

## Round 3 - Models and cost (cheapest adequate model per role)

**3.1 Thinking roles** (coordinator, lead, planner, plan reviewer, task reviewer, arbiter)
Top tier everywhere / top tier for coordinator + reviewers, mid tier for leads (**recommended** for cost) /
mid tier everywhere.

**3.2 Doing roles** (implementer, integrator, librarian, documentarian) - mid tier (**recommended**) /
small tier for trivial tasks / same as thinking roles.

**3.3 Other providers' tiers** - mid tier for build, small tier for lookups; the provider's top tier never
by default (critical decisions only).

**3.4 Budget guard** [native_limit_threshold] - stop starting new work at 97% of a provider's allowance and
flag it (**recommended**) / alert only / none.

Verify current model names and CLI aliases at setup (`<cli> --help`). Prefer aliases in agent files so a
CLI update moves the models without editing every file.

## Round 4 - Usage limits and failover  (see `06-provider-failover.md`)

**4.1 When the lead provider hits its limit** [rounds.fallback_when_limited]
- Other providers keep building approved plans on their own branches; the merge gate reviews them first
  thing when it is back (**recommended**)
- Everything pauses until the limit resets
- Switch the coordinator role to another provider (only if that provider is trusted to merge)

**4.2 Fallback order** [providers.priority] - e.g. Claude -> Codex -> Gemini. Ask which subscriptions exist.

**4.3 Who may merge to main** [roles "merge"] - only the lead provider (**recommended**) / any provider
with passing review.

**4.4 Chat-only providers** (no CLI - e.g. a web chat): use them as a copy-paste "desk" on a throwaway
branch, prompts redacted, never main (**recommended** only as an experiment) / not at all.

## Round 5 - Guardrails

**5.1 Autonomy** - decide and log: back up -> decide -> log what was chosen and over what -> continue
(**recommended**) / ask on judgement calls.

**5.2 Reserved for the owner** (multiSelect) - writes to live incl. applying migrations; spending money;
publishing outside the organisation; deleting anything unrebuildable; credentials; widening access
policies; merge to main; push. (Pre-fill from Phase 1 step 6.)

**5.3 Git model** - `feat/<lane>-<ID>` branches from main, continuous commits, one merge gate, merge when
tests pass (**recommended**) / pull request per lane with human review / trunk-based small commits.

**5.4 Commit attribution** [git.forbid_trailers] - the owner's name only, no AI trailer lines (hook
enforces) / AI co-author lines allowed.

## Round 6 - Reporting

**6.1 Board** - markdown board in the repo, `PROGRESS.md` (**recommended**: every agent and every provider
can read and write it, it versions with the code) / GitHub Issues/Projects / external tracker.

**6.2 Dashboard** - claude.ai artifact updated by a scheduled task twice a day (**recommended**) / once a
day / none.

**6.3 Local live view** - self-refreshing HTML page on the PC (round, leads, lanes, limits, blocked) - yes
/ no.

**6.4 Handovers and alerts** - a handover doc at every session switch + one batched owner list on the board
(**recommended**) / plus a push notification when something is blocked on the owner / weekly summary only.

## Round 7 - The owner

**7.1 Technical vocabulary** - not from an IT background: spell out every abbreviation on first use and say
what a thing does (**ask, don't assume**) / technical - normal vocabulary.

**7.2 Open question** - "Anything the build must never do, or must always do, that isn't covered?"

## After the questionnaire
Show a one-screen summary table of the answers. One confirmation. Then generate (Phase 4).
