# Changelog

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
