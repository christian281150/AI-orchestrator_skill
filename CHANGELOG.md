# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## 1.3.0 - 2026-09-24
### Added
- `references/10-runtime-resilience.md`: running for days - plan just in time by the build-lane runway, fixes to a
  build-provider fix lane, a watchdog independent of rounds, restart reconciliation (knowledge gap, reviewers, blind
  re-plan), cloud helpers (measured billing, steady and accelerate helpers, to-do lists, handback, setup checklist),
  machine traps (scheduled-task children, memory, hook-check time limits), race discipline, usage and credit measurement.
- Questionnaire items 4.5, 4.6, 5.5, 7.5, 7.6, 7.7; lessons 39-48; pointers in SKILL.md (Phase 7, start ritual).
### Fixed
- `CITATION.cff`: `cff-version` is the format version (1.2.0), not the release version.

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
