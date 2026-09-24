# Which tool when - routing work across AI tools

The rule behind every row: **each tool gets the work it does best at the lowest cost, the lead provider sees
everything before it reaches main, and nothing waits for a human that a tool could do.** Replace the example
names with your own tools; the shape stays the same.

Terms: **lead provider** = the one tool you trust to plan, review and merge (e.g. Claude Code).
**Build provider** = a CLI agent that implements approved plans (e.g. Codex). **Cloud sessions** = remote
agent sessions that run without your machine, usually on a separate credit. **Chat desk** = a model with no
CLI, driven by copy-paste. **Supervisor** = the round loop. **Keeper** = a short scheduled pass every ~10 minutes.

## Routing table

| Work | Default tool | When that is busy or limited | Never |
|---|---|---|---|
| Deciding scope, features, architecture | **not this skill** - you, with whatever you use for specs | - | agents inventing requirements |
| Coordinating a round, merge gate, arbitration | lead provider, local, top model tier | wait: the keeper keeps others working | a second merge gate |
| Planning an item (plan + build brief) | lead provider's planner + plan reviewer | cloud planners (steady / accelerate), or an idle build provider for *safe* items | unreconciled foreign plans reaching main |
| Implementing an approved plan | build provider, cheaper tier (saves the lead's allowance) | lead provider's implementers | building without an approved plan |
| Easier work and fixes | build provider | lead provider | spending the top tier on it |
| Security, auth, money, data integrity, migrations, anything live (risk tier 3) | lead provider, top tier, adversarial review | wait | auto-planning by another provider; cloud sessions |
| Needs your machine (local database, secrets, LAN, files) | local tools only | wait | cloud sessions (they cannot see it) |
| Needs only the repository | any provider; cloud eligible | cloud planners | - |
| Trying a model that has no CLI | chat desk on a throwaway branch, redacted prompts, max 2 fix rounds | - | main, the board, live, credentials |
| Watching the build, changing rules | a monitoring chat session | - | lane work in that session; killing a running round |
| Status for you | scheduled snapshot -> dashboard; local live view | - | an AI polling in a loop |
| Keeping it all running | OS scheduler: supervisor at logon, keeper every ~10 min | - | a human restarting things |
| Writes to live, money, publishing, deleting | **you** (reserved actions) | - | any agent |

## What the keeper does, every pass
1. **Restart** lanes that stopped on a usage limit - same command, at most `restart_max_per_day` per item.
2. **Build lanes** for `plan-approved` rows with a build brief whenever no round runs or the lead is limited.
3. **Idle planning:** a build provider with nothing to build plans one safe open item (never `unsafe_lanes`,
   never one already planned). The plan is marked `Authored-by: <provider>` and gets reconciled.
4. **Cloud planners** (`kind = "cloud"`):
   - *steady* - `cloud_steady` sessions while the lead has capacity and approved plans run low (< `queue_low_watermark`);
   - *accelerate* - up to `cloud_accelerate_max` once the lead is limited;
   - *handback* - when the lead's 5-hour usage is back below `handback_below_pct`, the keeper writes `HANDBACK`
     to the handback file; extra sessions finish their current item, hand the rest back, and stop;
   - never below `cloud_credit_floor`.
5. Nothing merges and nothing writes to the repository except the handback file (through safe-commit).

## Reconciliation - the price of using several tools
Work the lead did not see is a knowledge gap. Every round starts with `orch.py gap`, which lists it and prints
`REVIEWERS=<n>` (1-5). Per item a reviewer writes `reconcile-review.md`. For a plan written by another provider:
`gap-summary.md` (what it assumes that is unverified), a **blind** re-plan by the lead (`plan.<lead>.md`, written
without reading the other plan) and an arbiter's `reconcile.md` deciding which plan is built. Different tools
plan differently; the blind re-plan is what catches it.

## Capacity and allowance - measure, then plan
- **Separate buckets.** A local subscription (5-hour and weekly windows), a cloud credit and a build provider's
  weekly allowance run out independently. Give each a `usage_command` that prints JSON, and let thresholds decide.
- **Measure burn before scaling.** Example from a real build: one build provider with 5-6 lanes used ~2.5
  percentage points of its weekly allowance per 5 minutes - it would have emptied in about 3 hours.
- **Prefer the lead running longer:** push easier work and fixes to the build provider.
- **RAM caps parallelism,** not the tools: e.g. 5 build lanes while the lead runs, up to 10 when the lead is
  drained. Measure your machine.
- **Long sessions get expensive:** let build CLIs auto-compact around ~100k tokens; keep rounds short.

## Practical gotchas (paid for)
- Cloud sessions only see what is **pushed**: push on commit/merge (hooks) so they never plan against stale code.
- Cloud sessions can push only if the git host was connected to the cloud service **before** the session started;
  older sessions stay credential-less - don't reuse them.
- A session that refuses to hand its work over costs a re-plan - keep plans in the repo (ledgers), never only in
  a session.
- Shell arguments with spaces get split by some process launchers (e.g. PowerShell `Start-Process
  -ArgumentList`) - quote them explicitly.
- Chat desks: the owner pastes prompts and saves answers to files; extract code by script, never by retyping.
