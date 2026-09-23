# agent-build-orchestrator

A Claude skill plus a small toolkit for running a **multi-agent software build** - Claude, Codex and other
AI coding agents working in parallel lanes - from a finished spec to shipped code, without the usual waste:
work done twice, state lost between sessions, builds stalled on usage limits, and an owner interrupted at 3 a.m.

It is distilled from a real multi-week build (up to 10 parallel Claude leads plus Codex lanes on one PC,
a chat session monitoring). Every rule in it paid for itself at least once. The list is in
[`references/08-lessons-learned.md`](build-orchestration-setup/references/08-lessons-learned.md).

## What you need before it makes sense
An **idea**, a **functional spec** and an **architecture**. The skill does not write those. It starts
where they end - and it first makes the spec *buildable*: unambiguous, prioritised (P1 / P2 / P3,
not-in-v1), with acceptance criteria for every must-have.

## What it does
| Phase | Result |
|---|---|
| 0 Gate | refuses to start without idea + spec + architecture (offers dictation to create them) |
| 1 Clarity sprint | readiness scorecard, ambiguity hunt one question at a time, P1/P2/P3 + not-in-v1, acceptance criteria, pre-made decisions, owner-reserved actions |
| 2 Questionnaire | 7 short rounds: where it runs (local / cloud / chat / hybrid), which providers, how many lanes, which models, what happens on a usage limit, guardrails, reporting |
| 3 Workspace | folder layout, git with line endings / hooks / author fixed first, credentials as env vars, tools, test environment, claude.ai Project, schedulers |
| 4-5 Kit + board | board, rules, coordinator prompt, 10 agent roles, ledgers, config - filled from your answers; waves of work items with estimates |
| 6 Prove it | preflight (every check can go red), hook controls, one dry round |
| 7 Run | unattended rounds with automatic restart and provider failover |
| 8 Report | board, decisions log, dashboard metric, local live view, handovers |

## How failover works
```
round on Claude ──ok──► push ─► next round
      │
   usage limit (detected from the provider's own record, or the log tail - never quoted text)
      ▼
Claude marked limited until its reset ─► Codex / Gemini / ... build APPROVED plans
                                         on their own branches (never main)
      ▼
sleep until earliest reset ─► next Claude round gates those branches FIRST
                              (review, verify, merge or reject) ─► normal work
```
One merge gate. External providers never plan, merge, touch the board, live systems or credentials.

## Install the skill
- **Claude Code:** copy `build-orchestration-setup/` into `~/.claude/skills/` (all projects) or
  `<repo>/.claude/skills/` (one project).
- **claude.ai / Claude desktop / Cowork:** zip the `build-orchestration-setup/` folder and upload it as a
  skill in the app's skill settings.
- **Other agents that read `SKILL.md` folders:** copy the folder to their skills directory.

Then ask: *"Set up the build orchestration for my app - spec is in docs/spec.md"*.

## Use the toolkit directly
Python 3.11+, standard library only.
```bash
git init -b main my-app
python build-orchestration-setup/kit/tools/orch.py init my-app --name my-app \
       --author-name "Your Name" --author-email you@example.com
cd my-app
python tools/orch.py unfilled          # what the setup still has to fill in
python tools/orch.py preflight         # PASS / WARN / FAIL for everything a round depends on
python tools/orch.py board ready       # what can start now, P1 first
python tools/orch.py check-not-done W1-1
python tools/orch.py supervise         # unattended rounds (after preflight passes)
```
| Command | Does |
|---|---|
| `init <repo>` | copy templates + tools, never overwrite, wire git hooks, set author |
| `unfilled` | list `{{TODO}}` placeholders |
| `preflight` | board valid, hooks wired, author, provider CLIs on PATH, skills installed, env vars present, state dir outside repo, RAM |
| `supervise` | the round loop with limit detection, fallback lanes, re-exec on change, STOP file, stop after 3 identical failures |
| `board validate / ready / metrics` | consistency (done needs a commit hash), next work by priority, shipped % |
| `check-not-done <ID>` | evidence an item is not already done or owned (board, git log, branches, ledger) |
| `safe-commit -m msg <paths>` | commit only these paths; waits while a merge is in progress |
| `redact control / scan / apply <file>` | proven secret scan before anything leaves the machine |
| `snapshot` / `live-view` | read-only progress JSON / self-refreshing local HTML status page |

## Verified and not verified
- **Verified:** `pytest tests` - unit tests and end-to-end supervisor runs with fake providers (a limit hit,
  fallback build on another provider, the gate in the next round, STOP, repeated-failure stop), hook
  controls, safe-commit during a merge, preflight going red on a broken board, a missing skill and a
  byte-order mark. Run locally on Linux; the CI workflow runs the same suite on Linux, macOS and Windows.
- **Not verified by the tests:** the real Claude / Codex / Gemini CLIs (flags and usage-record formats change
  between versions - check every command in `orchestration.toml` against `<cli> --help`), and the OS scheduler
  templates in `tools/scheduling/`.

## Repository layout
```
build-orchestration-setup/     the skill (install this folder)
  SKILL.md                     the phases
  references/                  01-spec-clarity ... 08-lessons-learned
  kit/templates/               copied into your repo by `init`
  kit/tools/orch.py            the toolkit (stdlib Python)
tests/                         pytest suite
```

## License
MIT - see [LICENSE](LICENSE).
