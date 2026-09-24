# Spec readiness - {{PROJECT_NAME}}

Filled in Phase 1 (readiness gate), BEFORE any orchestration is configured. This is a **check**, not spec
work: it scores whether the settled spec and architecture are ready to be built. Gaps in *what* to build go back
to the owner's own spec process; the orchestration starts when they are closed.

Score each line 0 (missing) / 1 (partly, or only in someone's head) / 2 (written, specific, testable).
**Gate: every P1 line scores 2, the total is at least 80% of the maximum, and the gap list holds no P1 entry.**

| # | Dimension | Question it answers | Score | Where written |
|---|---|---|---|---|
| 1 | Users and the core job | Who uses it, for what one job, how often? | | |
| 2 | v1 definition of done | What must a real user be able to do on day one? | | |
| 3 | Scope by priority | Every feature tagged P1 / P2 / P3, plus an explicit "not in v1" list (`SCOPE.md`) | | |
| 4 | Acceptance criteria | Each P1 feature: given / when / then, testable by a machine | | |
| 5 | Data | What it stores, where it comes from, identity rules, missing vs zero, volumes | | |
| 6 | Architecture | Stack, repo layout, hosting, database, auth, integrations | | |
| 7 | Environments | local / test / live - names, which is live, how test data is made (synthetic) | | |
| 8 | Security and access | Who may see/do what; secrets handling; threat model for anything public | | |
| 9 | Pre-made decisions | The decisions that would otherwise interrupt the build (see list below) | | |
| 10 | Reserved actions | What only the owner may do (live writes, money, publishing, deleting) | | |
| 11 | Deadlines and demo | Dates that matter; a demo/synthetic mode vs live mode | | |
| 12 | Non-functional | Users at once, response times, backup/restore, uptime expectations | | |

## Build-time decisions to settle now (how to build - not what)
- Who applies database migrations to live, and how they are numbered
- Sequencing of anything reachable from outside (access policy before the endpoint)
- Identity the app and loads run as (attribution is forever)
- Naming: project, lanes, branch pattern, item IDs
- Test data: synthetic generator, where fixtures live
- What "missing" looks like in the UI (never rendered as zero)
- Which third-party data may never be committed or sent to an AI provider

## Gap list (returned to the owner's spec work - must hold no P1 entry before the gate)

| # | What is missing | Blocks (features) | What would make it a 2 | Closed on |
|---|---|---|---|---|

## Assumptions accepted (non-P1 gaps we build around - each is a logged decision)

| # | Assumption | Risk if wrong | Revisit by |
|---|---|---|---|
