# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## 1.5.0 - 2026-09-24
Gap-closing release: nothing new in concept - it fills gaps in the existing rounds, keeper and failover that
showed up while running builds for several days.
### Added
- `references/11-long-running-builds.md`: ten gaps closed for multi-day unattended builds - just-in-time planning,
  fix routing, build-lane cap by load with a memory guard, watchdog duties, restart reconciliation, cloud helpers,
  cloud setup checklist, machine traps, race discipline, usage measurement - each with problem, rule, wiring and a
  control that can go red; plus five clearly marked proposals (history secret scan, stale handovers, a second
  machine, disk space, clock changes).
- Questionnaire round 7c (planning pace, fix routing, lane cap by load, watchdog extras); matching rows in
  `orchestration-config.md`.
- Lessons 45-49 (numbering shifted; 50 in total).
### Changed
- SKILL.md points to the new reference; no other behaviour changed. Documentation-only release: rules the toolkit
  does not automate yet are marked as wired in the owner's launcher/watchdog scripts.

## 1.4.0 - 2026-09-24
### Changed
- **Repository renamed to `AI-orchestrator_skill`**; plugin and marketplace are now `ai-orchestrator`
  (`/plugin install ai-orchestrator@ai-orchestrator`). Old GitHub links redirect; reinstall the plugin once.
- **Positioning made explicit:** the skill orchestrates the *build* of a settled spec and never writes, refines or
  aligns specs. Phase 1 is now a **readiness gate** (a check that returns a gap list), reference renamed to
  `01-readiness-gate.md`; the old "clarity sprint" is gone.
- README rewritten for visibility: "Get the skill" table up front, adoption levels, which-tool-when, personal note.
### Added
- **Which tool when:** `references/10-tool-routing.md` and questionnaire round 7b - lead provider, build
  providers, cloud sessions, chat desks, supervisor, keeper, and the owner, each on the work it does best.
- **Keeper** (`orch.py keeper`, scheduled every ~10 min): restarts limit-stopped lanes (capped per day), build
  lanes when no round runs, idle planning of safe items by build providers, cloud planners with steady /
  accelerate / handback rules and a credit floor. Scheduler templates for Windows, systemd and launchd.
- **Knowledge-gap reconciliation** (`orch.py gap`, also injected into every round prompt): work the lead did not
  see, `REVIEWERS=<n>`, and for foreign plans a gap summary, a blind lead re-plan and an arbiter's ruling.
  Plans carry `Authored-by:`.
- Provider `kind` (local / cloud / chat), `plan_command`, `usage_command` (JSON usage meter), `restart_max_per_day`.
- **Adoption levels 1-4** in the skill, README and questionnaire.
- Discussions: category forms for *Show and tell* ("I tried it"), *Ideas*, *Q&A*; the issue chooser links there.
- Lessons 39-45 (build-provider burn rate, cloud planners, foreign plans, pushing for cloud sessions, plans only in
  the repository, keeping spec work out of the build, argument splitting).
### Fixed
- The supervisor no longer sees its own finished child processes as still running (zombie reaping).

## 1.3.0 - 2026-09-24
### Changed
- Skill folder follows the Agent Skills layout: `scripts/` (toolkit, was `kit/tools/`) and `assets/templates/`
  (was `kit/templates/`). `orch.py init` output in your repository is unchanged (`tools/` + templates).
- Workflows: actions pinned to commit SHAs, least-privilege `permissions`, superseded runs cancelled.
- Dependabot groups all action updates into one monthly pull request.
### Added
- CI: `ruff` lint, the Agent Skills reference validator (`skills-ref validate`), manifest JSON check, and a
  test matrix of Python 3.11 and 3.13 on Linux, macOS and Windows.
- Releases: `SHA256SUMS.txt` and a signed build-provenance attestation for the skill zip.
- `AGENTS.md` (+ `CLAUDE.md` import) with contributor rules for AI agents working on this repository.
- `tools/bump_version.py` - one command sets the version in every manifest, the skill, the toolkit and CITATION.
- `pyproject.toml` with ruff and pytest settings (tooling only; the toolkit stays dependency-free).
- README: `npx skills` install and use-without-installing, release verification (checksum + attestation).

## 1.2.1 - 2026-09-24
### Changed
- Test fixtures no longer contain secret-looking literals: fake IP (documentation range), email (reserved
  `.test` domain), API key and password are assembled at runtime, so secret scanners do not flag the repository.

## 1.2.0 - 2026-09-24
### Added
- Installable plugin: `.claude-plugin/` (plugin + marketplace), `.codex-plugin/`, `.cursor-plugin/` manifests;
  skill moved to `skills/build-orchestration-setup/`.
- Commands `/orchestrate` and `/build-status`.
- Agent Skills frontmatter: `license`, `compatibility`, `metadata` (author, version, repository).
- Worked example `examples/lunch-poll/`.
- Governance: NOTICE (trademarks, no third-party code), SECURITY (private reporting, security model),
  CODE_OF_CONDUCT (Contributor Covenant 2.1), CITATION.cff, issue and PR templates, Dependabot for Actions.
- Release workflow: tagging `v*` runs the tests and attaches the skill zip to a GitHub release.
- Tests for manifest validity, one version everywhere, skill format, the example; SPDX headers in the toolkit.
### Changed
- README rewritten: install per tool, how it works, failover diagram, philosophy, compatibility, FAQ.

## 1.1.0 - 2026-09-24
- Provider-neutral throughout: lead provider vs build providers; engine-neutral `ROLES.md` rendered per tool.
- Skills plan: questionnaire round (scan installed, owner's ideas, propose the rest, project skills),
  `SKILLS-PLAN.md`, `orch.py skills` inventory, preflight reuses it.
- Cost-quality rules (`references/09`): model tier per role, review depth by risk tier (1/2/3), few skills
  per agent; risk tier in the plan template.
- Questionnaire extended to 9 rounds (project type, approvers, date vs quality vs cost).

## 1.0.0 - 2026-09-24
- Skill: gate, clarity sprint (readiness scorecard, P1/P2/P3, acceptance criteria), 7-round questionnaire,
  workspace setup, kit fill, wave breakdown, preflight, run, report.
- Toolkit `orch.py`: init, unfilled, preflight, supervise (rounds, provider failover, fallback lanes, gate,
  re-exec, STOP, blocked-after-N), board validate/ready/metrics, check-not-done, safe-commit, redact,
  snapshot, live-view, git hooks.
- Templates: board, decisions log, rules, coordinator prompt, 10 agent roles, ledgers, handover, scope,
  spec readiness, config, schedulers for Windows/macOS/Linux.
