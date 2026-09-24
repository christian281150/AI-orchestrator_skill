# Phase 2 - The orchestration questionnaire

Everything asked here is about **how to build**, never about *what* to build - scope, features and
architecture are settled before this skill starts (Phase 1 only checks that).

Ten short rounds, typically 20-30 minutes. Rules:
- `AskUserQuestion`, max 4 questions per call, 2-4 options each, the recommended option first with
  "(Recommended)". The owner can always type their own answer.
- Derive each recommendation from the intake (Phase 0), the spec and the readiness gate - never default
  blindly. Skip any question those already answer, and say which answer you took from where.
- Provider-neutral: nothing here assumes a particular AI vendor. "Lead provider" = the one trusted to plan,
  review and merge; "build providers" = the ones that implement approved plans.
- Unattended owner: take the recommendations, log each as a decision, list the assumptions at the top.
- Record every answer with the options not taken in `docs/coordination/orchestration-config.md`; machine
  settings go into `orchestration.toml` (key in brackets).

## Round 1 - Project and people
**1.1 What kind of project?** web app / mobile app / API or backend service / data pipeline / CLI or library /
other. (Decides the lanes: e.g. web app = backend, frontend, database, infra-docs; data pipeline = ingest,
transform, storage, quality, infra-docs.)
**1.2 Who decides?** one owner (**recommended** for speed) / several approvers - then: who approves what
(live writes, money, releases), and who is asked when they disagree.
**1.3 Technical vocabulary of the owner(s)** - not from an IT background: spell out every abbreviation on
first use and say what a thing does / technical. (Ask; never assume.)
**1.4 What matters more when they conflict?** a fixed date (cut scope, keep quality gates) / quality first
(move the date) / cost first (fewer lanes, cheaper models, longer timeline).

## Round 2 - Where it runs
**2.1 Execution home**
| Option | Choose when | Trade-off |
|---|---|---|
| Local CLI agents on the owner's machine, unattended rounds via the supervisor | long build, local database, many lanes | machine must stay on and awake; RAM limits parallelism |
| Cloud coding sessions, one per lane | machine can be off; repo on a git host; no local-only resources | no local database; merge gate needs its own session |
| Chat-driven (a chat app with subagents) | small build (< ~15 items), owner wants to watch | chat context fills; repo agent files don't load - role text is pasted |
| Hybrid: local rounds build, a chat session monitors (**recommended** for more than a week of work) | | two places to look - START-HERE says which wins |

**2.2 Machine and shell** - Windows + PowerShell / macOS / Linux / cloud only.
**2.3 Human involvement** - unattended, owner approves only reserved actions (**recommended**) / owner
approves each merge wave / interactive pair-building.
**2.4 How much machinery?** (adoption level - start small, add later; every level reuses the one before)
| Level | What runs | Choose when |
|---|---|---|
| 1 Rituals only | board, decisions log, ledgers, handovers, rules - agents in a chat or one CLI session | small build, trying it out |
| 2 Unattended rounds | + supervisor (rounds, restart, STOP file), git hooks, preflight | one provider, runs while you're away |
| 3 Multi-provider | + build providers, failover, knowledge-gap reconciliation | two or more AI subscriptions |
| 4 Full | + keeper every ~10 min, cloud planners (steady / accelerate / handback), idle planning, dashboard | long builds, maximum throughput |
Recommend the lowest level that fits the build; say what the next level would add.

## Round 3 - Providers
**3.1 Which AI coding tools and subscriptions do you have?** (multiSelect) - e.g. Claude Code, OpenAI Codex,
Gemini CLI, an IDE agent (Cursor, Windsurf, Copilot), local models, chat-only models (no CLI). [providers]
**3.2 Lead provider** - plans, reviews and merges. Recommend the strongest reviewer the owner has; one only.
**3.3 Build providers** - which of the others implement approved plans (**recommended**: every CLI-capable
tool the owner pays for - it multiplies build capacity at no extra subscription cost) / lead provider only.
**3.4 Who may merge to main** [roles "merge"] - the lead provider only (**recommended**) / any provider after
review. One merge gate keeps code from several providers coherent.

## Round 4 - Scale and pace
**4.1 Parallel lead lanes per round** - 2-3 (8 GB RAM, cautious budget) / 4-6 (**recommended** start, 16 GB) /
up to 10 (measured headroom, large allowance). Start low; raise after measuring one round's RAM and burn.
**4.2 Build-provider lanes** [providers.<x>.max_parallel] - 0 / up to 3 / up to 5 / up to 10. A relay agent
waiting on each one also holds a lead-provider slot.
**4.3 Round length** [rounds.window_minutes] - 1 h / 3 h refill window, then running lanes finish
(**recommended**) / until the queue is empty. Fresh rounds are cheaper than long-lived coordinators.
**4.4 Planning lanes** - ~2 lead slots write approved plans + build briefs ahead of the builders
(**recommended** when 4.2 > 0) / none.

## Round 5 - Cost and quality  (see `09-skills-and-cost-quality.md`)
**5.1 Optimise for** - best quality at the lowest cost (**recommended**: cheapest adequate model per role,
review depth by risk tier, few skills per agent) / maximum quality regardless of cost / minimum cost.
**5.2 Thinking roles** (coordinator, lead, planner, reviewers, arbiter) - top tier / top tier for coordinator
and reviewers, mid tier for leads (**recommended**) / mid tier everywhere.
**5.3 Doing roles** (implementer, integrator, librarian, documentarian) - mid tier (**recommended**) / small
tier for trivial tasks / same as thinking. Any provider's most expensive tier: never by default.
**5.4 Budget guard** [native_limit_threshold] - stop starting new work at 97% of an allowance and flag it
(**recommended**) / alert only / none.

## Round 6 - Skills  (see `09-skills-and-cost-quality.md`)
**6.1 What do you already have?** - scan installed skills and suggest (**recommended**; run
`python <skill>/scripts/orch.py skills <repo>`) / I'll list them / nothing yet.
**6.2 Do you know which task or topic needs which skill?** - yes, I'll describe it / partly - use my ideas and
propose the rest (**recommended** when they have any) / no - propose everything.
**6.3 How should the proposal be optimised?** - fewest skills that cover each task type at the best quality
per cost (**recommended**) / maximum coverage / minimal - only where a failure was seen.
**6.4 Project-specific skills** - create them as recurring rules emerge (**recommended**) / all up front from
the spec / never.
Then build `SKILLS-PLAN.md` (task type -> skills -> source -> engines -> model tier -> why), show one screen,
confirm once.

## Round 7 - Usage limits and failover  (see `06-provider-failover.md`)
**7.1 When the lead provider hits its limit** [rounds.fallback_when_limited] - build providers keep building
approved plans on their own branches; the merge gate reviews them first when it is back (**recommended**) /
everything pauses / another provider takes over the coordinator role (only if trusted to merge).
**7.2 Fallback order** [providers.priority] - e.g. lead -> build provider A -> B.
**7.3 Automatic restart** - OS scheduler starts the supervisor at logon and restarts it on failure; re-exec
between rounds on rule changes (**recommended**) / manual start.
**7.4 Chat-only models** - use as a redacted copy-paste "desk" on a throwaway branch, never main (experiment
only) / not at all (**recommended** unless the owner wants to test one).

## Round 7b - Which tool does what  (see `10-tool-routing.md`; levels 3-4)
Show the routing table from `10-tool-routing.md` filled with the owner's tools, then:
**7b.1 Routing** - keep the default routing (**recommended**) / adjust rows (ask which).
**7b.2 Cloud sessions for planning** (separate credit) - steady 1, accelerate up to 3 when the lead is limited,
hand back when it recovers (**recommended** if the owner has cloud credit) / off.
**7b.3 Idle build providers plan safe items** - yes, the lead reconciles every foreign plan with a blind re-plan
(**recommended**) / no, only the lead plans.
**7b.4 Keeper** - scheduled pass every ~10 minutes (**recommended** for level 4) / supervisor only.

## Round 8 - Guardrails
**8.1 Autonomy** - decide and log: back up -> decide -> log chosen and not chosen -> continue
(**recommended**) / ask on judgement calls.
**8.2 Reserved for the owner** (multiSelect) - writes to live incl. applying migrations; spending money;
publishing outside the organisation; deleting anything unrebuildable; credentials; widening access; merge to
main; push. (Pre-fill from the readiness gate.)
**8.3 Git model** - `feat/<lane>-<ID>` branches, continuous commits, one merge gate, merge when tests pass
(**recommended**) / pull request per lane with human review / trunk-based small commits.
**8.4 Commit attribution** [git.forbid_trailers] - the owner's name only, AI trailer lines blocked by a hook /
AI co-author lines allowed.

## Round 9 - Reporting
**9.1 Board** - markdown board in the repo (**recommended**: every agent of every provider can read and write
it; it versions with the code) / issue tracker / external tool.
**9.2 Dashboard** - hosted page updated by a scheduled task twice a day (**recommended**) / once a day / none.
**9.3 Local live view** - self-refreshing status page on the machine - yes / no.
**9.4 Handovers and alerts** - handover doc at every session switch + one batched owner list on the board
(**recommended**) / plus a push notification when blocked on the owner / weekly summary only.

**Closing question (Round 10):** "Anything the build must never do, or must always do, that isn't covered?"

## After the questionnaire
One-screen summary table of all answers -> one confirmation -> Phase 3.
