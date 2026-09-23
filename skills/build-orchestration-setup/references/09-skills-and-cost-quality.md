# Skills plan and the cost-quality rules

A skill is packaged know-how an agent loads when a task needs it: how to do test-driven development, how
this project's database may be accessed, how to review for security. Good skills are the cheapest quality
lever in a multi-agent build: an agent that loads a 2-page skill does not spend 30k tokens rediscovering the
same rules - and does not get them wrong in a different way in every lane.

Skills are also a cost: every skill an agent loads sits in its context for the whole task. Ten skills "just in
case" make every call slower and more expensive and dilute the ones that matter. The plan below picks the few
that pay for themselves.

## The skills questionnaire (Phase 2, round "Skills")
Ask with `AskUserQuestion`, recommended option first:

**S1. What do you already have?**
- Scan what is installed and suggest which to use (**recommended**) - run `python tools/orch.py skills`
  (or list the skill folders of every engine in use) and show the inventory
- I will list the skills / plugins I want
- Nothing yet

**S2. Do you already know which task or topic needs which skill?**
- Yes - I'll describe it (take it as the starting point, fill gaps, flag conflicts)
- Partly - use my ideas and propose the rest (**recommended** when they have any ideas)
- No - propose everything

**S3. How should the proposal be optimised?**
- Best quality at the lowest cost: the fewest skills that cover each task type, cheapest adequate model per
  role, deeper review only where risk is high (**recommended**)
- Maximum quality regardless of cost
- Minimal: as few skills as possible, only where a failure was already seen

**S4. Project-specific skills** (the project's own rules, packaged)
- Create them as recurring rules emerge - from decisions, reviews and repeated corrections (**recommended**)
- Write them all up front from the spec
- Never

## How to build the proposal
1. **Task types first, not skills first.** From the wave breakdown, list the kinds of work: planning,
   implementing backend / frontend / data / infrastructure, migrations, tests, debugging, reviewing, security
   review, documentation, release. Each task type is done by a role (see `04-roles-and-pipeline.md`).
2. **Per task type, the smallest set that covers it** - usually 1-3 skills. Sources, in this order:
   installed skills -> skills the owner named -> public collections (process skills such as brainstorming,
   writing and executing plans, test-driven development, systematic debugging, verification before completion,
   requesting/receiving code review, using git worktrees; engineering skills such as backend, frontend, QA,
   DevOps, security) -> a new project skill.
3. **Project skills** capture what is specific to this app and would otherwise be re-explained in every
   dispatch: how to access the database and as which identity; the API contract and how changes propagate;
   how test data is generated; how to verify a migration; evidence standards for money/data. Write them
   from the spec and the decisions log, one topic per skill, 1-3 pages, with the "why" kept.
4. **Name skills only where used.** Each agent file lists the skills its role needs (`skills:` in the
   frontmatter, or the engine's equivalent). A skill named in an agent file must be installed where that
   engine reads skills - `preflight` fails otherwise.
5. **Every engine needs its own copy.** Claude reads `.claude/skills` and `~/.claude/skills`; other engines
   read their own folders (e.g. `.agents/skills`, `~/.agents/skills`). Install to each engine that runs the
   role; keep one source folder and an install script, so copies never drift.
6. **Refresh deliberately.** Public collections change. Pin a version (commit hash) for the build, refresh
   between waves, re-run preflight.

Write the result to `docs/coordination/SKILLS-PLAN.md` (template in the kit), show the owner one screen,
confirm once, then install in Phase 3 and name the skills in the agent files in Phase 4.

## The cost-quality rules (apply to every choice in the build)
| Lever | Rule |
|---|---|
| Model per role | cheapest model that does the role well: top tier for coordinator, planner, reviewers, arbiter; mid tier for implementers, integrator, librarian, docs; small tier for relays and lookups. Another provider's top tier only for critical decisions. |
| Review depth by risk tier | every plan states a risk tier. **Tier 1** (docs, tests, isolated UI) - one reviewer, mid tier. **Tier 2** (normal feature code) - task reviewer on the top tier. **Tier 3** (security, auth, money, data integrity, migrations, anything touching live) - plan review + task review + adversarial security review, top tier, controls shown going red. |
| Planning before building | a reviewed plan is cheap; a wrong build is re-done. Plans also let cheaper providers build. |
| Skills over re-explaining | a rule explained twice in dispatches becomes a project skill. |
| Few skills per agent | only the skills the role uses; each loaded skill costs context on every call. |
| Short rounds | a long-lived coordinator re-reads its growing context every turn; fresh rounds are cheaper. |
| Parallel only where independent | lanes by file ownership; serial where one output is another's input. |
| Stop early, split early | over ~15 files or "and then" twice -> split. A returned split is success. |
| Measure burn | allowance used per lane-hour, per provider; plan parallelism on the measurement. |
| Never pay twice | `check-not-done`, ledgers, same-turn board ticks. The most expensive token is the one spent redoing work. |
