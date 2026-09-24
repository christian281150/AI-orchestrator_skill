# Configuration - what you can customize, and where

There are **three** files. You only ever *edit* the first two; the third is a record.

| File | Scope | Who writes it | What for |
|---|---|---|---|
| **Profile** `~/.ai-orchestrator/profile.toml` (+ optional `<repo>/.ai-orchestrator.toml`) | **you**, all projects | you, once | your standing preferences; answered questions are skipped in the setup |
| **Project config** `<repo>/orchestration.toml` | **this project**, this machine | the setup (from your answers); you may edit | tools, lanes, rounds, safety, keeper - what the toolkit reads |
| `docs/coordination/orchestration-config.md` | this project | the setup | the record: every answer and the options you did not take |

Both editable files are [TOML](https://toml.io): `key = value`, text in quotes, lists in `[ ]`, `#` starts a
comment. Open them in any text editor. Never put passwords, tokens or keys in either file - credentials live in
environment variables only.

---

## 1. The profile (your customization file)
Template: [`skills/build-orchestration-setup/assets/profile.toml`](../skills/build-orchestration-setup/assets/profile.toml).
Create: `python <skill>/scripts/orch.py profile init` (add `--project` for a per-project file).
Check: `orch.py profile check` · See what it answers: `orch.py profile show`.
Learn from a finished setup: `orch.py profile learn` lists what this project's answers would add, `--write`
applies it. Only **empty** values are filled - a value you set is never overwritten, free text is never guessed.
Empty values (`""`, `0`, `[]`) mean "ask me" and never override a value set in the other profile file.

| Section · key | Values | Answers question | Notes |
|---|---|---|---|
| `owner.name` | text | - | how agents address you |
| `owner.git_author_name` / `git_author_email` | text | - | used by `orch.py init` when you don't pass `--author-*` |
| `owner.vocabulary` | `plain` · `technical` | 1.3 | `plain` = every abbreviation explained |
| `owner.language` | e.g. `en`, `de` | - | language for questions and reports |
| `owner.timezone` | e.g. `UTC` | - | schedules and reports |
| `defaults.execution_home` | `local` · `cloud` · `chat` · `hybrid` | 2.1 | where agents run |
| `defaults.involvement` | `unattended` · `approve-waves` · `interactive` | 2.3 | |
| `defaults.adoption_level` | `1`-`4` | 2.4 | 1 rituals · 2 unattended · 3 multi-provider · 4 full |
| `defaults.round_hours` | number | 4.3 | refill window per round (3 recommended) |
| `defaults.optimise_for` | `quality-per-cost` · `max-quality` · `min-cost` | 5.1 | |
| `defaults.planning_pace` | `just-in-time` · `ahead` | 7c.1 | |
| `defaults.fix_routing` | `build-provider` · `lead` | 7c.2 | |
| `defaults.autonomy` | `decide-and-log` · `ask` | 8.1 | |
| `defaults.git_model` | `feat-branches` · `pr-per-lane` · `trunk` | 8.3 | |
| `defaults.commit_attribution` | `owner-only` · `ai-coauthor-allowed` | 8.4 | |
| `tools.lead` | tool name | 3.2 | plans, reviews, merges - exactly one |
| `tools.build` | list of tool names | 3.3 | build approved plans |
| `tools.cloud_sessions` · `tools.chat_desk` | `on` · `off` | 7b.2 · 7.4 | |
| `models.thinking` · `doing` · `small` | model names your tools accept | 5.2 · 5.3 | cheapest adequate per role |
| `limits.budget_guard_pct` | 50-100 | 5.4 | 97 recommended |
| `limits.build_lanes_shared` · `build_lanes_lead_limited` | numbers | 7c.3 | e.g. 5 and 10 on 16 GB |
| `limits.memory_no_new_start_pct` · `memory_refuse_pct` | 50-100 | 7c.3 | 85 / 90 recommended; first must be lower |
| `reserved.actions` | list | 8.2 | what only you may do |
| `skills.preferred` · `avoid` · `sources` | lists | 6.x | shape the skills plan |
| `reporting.dashboard` | `twice-daily` · `daily` · `none` | 9.2 | |
| `reporting.live_view` | `on` · `off` | 9.3 | |
| `reporting.handover_every_session` | `true` · `false` | 9.4 | |
| `naming.branch_pattern` · `id_pattern` | text | - | defaults `feat/<lane>-<ID>-<topic>`, `W<wave>-<n>` / `F<n>` |

## 2. The project config (`orchestration.toml`)
Written by the setup from your answers; the template with comments is
[`assets/templates/orchestration.toml`](../skills/build-orchestration-setup/assets/templates/orchestration.toml).
After editing, run `python tools/orch.py preflight` - it must stay green.

| Section | Key | Default | Change it when |
|---|---|---|---|
| `[project]` | `name`, `main_branch` | from setup | renaming |
| | `board`, `decisions`, `session_prompt`, `ledgers`, `stop_file` | `docs/coordination/...` | you keep coordination files elsewhere |
| | `state_dir` | `~/.agent-build/<name>` | logs and run state must live on another disk (keep it **outside** the repo) |
| | `worktrees_dir` | `../<name>-wt` | lane working copies should live elsewhere |
| | `id_pattern` | `W<n>-<n>` / `F<n>` | your own item IDs |
| `[rounds]` | `window_minutes` | 180 | shorter rounds = cheaper, more restarts |
| | `max_round_minutes` | 330 | the only time a round is ever stopped |
| | `reprobe_minutes` | 15 | how often a limited tool is re-checked |
| | `push_after_round` | true | no remote, or you push by hand |
| | `fallback_when_limited` | true | build providers should *not* work while the lead is limited |
| | `max_identical_failures` | 3 | stop sooner or later on repeated errors |
| `[git]` | `author_name`, `author_email` | from setup/profile | |
| | `forbid_trailers` | AI attribution lines | empty the list to **allow** AI co-author lines |
| `[safety]` | `forbid_paths` | keys, `.env`, captures, `data/` | more file types must never be committed |
| | `required_env` | `[]` | names (never values) of credentials the build needs |
| | `redact_terms` | `[]` | your server, domain, client names - blocked from commits and outgoing prompts |
| `[keeper]` | `interval_minutes` | 10 | the watchdog pass frequency |
| | `queue_low_watermark` | 5 | plan only while fewer approved plans wait (use half your build-lane cap) |
| | `cloud_steady` / `cloud_accelerate_max` | 1 / 3 | cloud planner counts |
| | `handback_below_pct` / `cloud_credit_floor` | 50 / 5 | when cloud helpers hand back / stop |
| | `idle_planning` / `unsafe_lanes` | true / db, infra, security | which lanes other providers may never plan |
| `[[providers]]` (one block per tool) | `name`, `priority` (lower = preferred) | | adding or removing a tool |
| | `roles` | `coordinator` `plan` `review` `build` `merge` | exactly **one** provider should have `merge` |
| | `kind` | `local` | `cloud` for remote sessions, `chat` for copy-paste models |
| | `round_command` / `build_command` / `plan_command` | examples | always check against `<tool> --help` for your version |
| | `usage_command` | readers for claude and codex | a script printing `{"five_hour_pct": .., "weekly_pct": .., "credit_left": ..}`; ready-made: `["{python}", "tools/orch.py", "usage", "claude"]` (or `"codex"`) - see [usage meters](#4-usage-meters-how-full-is-each-allowance) |
| | `usage_fail_closed` | true | `false` = an unreadable meter is ignored instead of stopping new work (not recommended) |
| | `max_parallel` | 1-5 | lanes this tool may run at once - measure memory first |
| | `strip_env` | `[]` | credential variables this tool must never see |
| | `native_limit_threshold` | 97 | % at which new work stops |
| | `enabled` | true | switch a tool off without deleting it |

## 3. Common customizations (recipes)
| I want to... | Do this |
|---|---|
| see **how full** each allowance is | `python tools/orch.py usage claude` / `codex`; Claude Code needs the status-line line from [section 4](#4-usage-meters-how-full-is-each-allowance) |
| use **only one** AI tool | keep one `[[providers]]` block with all five roles; `fallback_when_limited = false`; profile `adoption_level = 2` |
| **add** a second build tool | copy a build-provider block, change `name`, commands and `priority`; run `preflight` |
| run on a **smaller machine** (8 GB) | `max_parallel = 2` per tool; profile `build_lanes_shared = 2`, `memory_no_new_start_pct = 80` |
| **turn off cloud** helpers | `enabled = false` on the cloud provider; profile `cloud_sessions = "off"` |
| **allow AI co-author** lines | `[git] forbid_trailers = []`; profile `commit_attribution = "ai-coauthor-allowed"` |
| have everything explained in **plain language** | profile `vocabulary = "plain"` |
| **my own naming** | profile `[naming]` + `[project] id_pattern` |
| keep agents away from **production** | list it in profile `[reserved] actions`; add its credential names to `strip_env` for build tools |

## 4. Usage meters: how full is each allowance
The build stops starting new work at `native_limit_threshold` (97 %) - *before* the tool refuses - if it can
read how full the allowance is. `python tools/orch.py usage claude` (or `codex`) prints what it reads:

| Status | Means | Effect |
|---|---|---|
| `ok` | percentages for the 5-hour and weekly windows, reset times, age of the reading | at the threshold: no new work until the reset |
| `no-data` | nothing recorded yet (or a login without plan windows) | no block - the log check decides, as before |
| `unreadable` | a record exists but its format changed (tool update) | **no new work** until it reads again; `preflight` shows it red. Update the skill, or set `usage_fail_closed = false` knowingly |

**Codex** writes its own session records - nothing to set up.

**Claude Code** has no usage file, but passes the usage to its *status line*. Let the status line store it
(once, in `~/.claude/settings.json`; Windows: `C:\Users\<you>\.claude\settings.json`):
```json
{ "statusLine": { "type": "command",
                  "command": "python /full/path/to/your-project/tools/orch.py usage claude --capture" } }
```
The bar then shows `5h 42% · week 10%`, and every refresh saves the reading to
`~/.ai-orchestrator/usage/claude.json`. This replaces an existing status line; if you have your own, pipe its
input into the same command as well. Unattended `claude -p` rounds don't refresh the status line - there the last
reading counts and the log check stays the backstop. Round logs written with `--output-format stream-json
--verbose` are read too.

Checked against: Claude Code 2.1.281, and the Codex session-record format of 2026 builds (not re-checked
against a live Codex install). Each reader states this in its output (`verified_with`).
