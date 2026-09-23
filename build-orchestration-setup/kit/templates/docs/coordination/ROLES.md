# Roles - engine-neutral definitions

Defined once here; rendered into each engine's own format (Claude: `.claude/agents/*.md`; Codex and others:
`AGENTS.md` sections or their agent files). When a role changes, change it here and re-render every engine's
copy in the same commit.

| Role | Tier | Does | Never | Skills (from SKILLS-PLAN.md) | Engines allowed |
|---|---|---|---|---|---|
| Coordinator | top | picks items, dispatches, merge gate, keeps the board honest | writes product code | | lead provider only |
| Lane lead | top | one item end to end in its own worktree | edits another lane's files | | |
| Librarian | mid | exact paths, signatures, facts (fact vs inference) | changes anything | | |
| Planner | top | plan, max 6 tasks, each with files, done-looks-like, verify, risk tier | invents names | | |
| Plan reviewer | top | adversarial plan review: APPROVED / CHANGES REQUIRED | approves without evidence | | |
| Implementer | mid | one task: failing test first, smallest change, verify, commit | weakens a test | | any build provider |
| Integrator | mid | merges main into the lane branch, full suite, verbatim counts | merges into main | | |
| Task reviewer | top | tries to break the work; breaks the control to see red | says "looks fine" | | |
| Arbiter | top | settles disputes, logs the ruling | overrules a logged decision | | |
| Unblocker | small | names the likely cause and the smallest test | implements | | |
| Documentarian | mid | makes the repo readable; no status in docs | changes behaviour | | |
| Relay | smallest | starts an external build lane, waits, relays | anything else | | |
