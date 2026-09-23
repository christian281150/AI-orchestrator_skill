# Example: "Lunch Poll" - a filled-in setup

A deliberately small app, so the whole setup fits on a few screens. It shows what the skill produces after
Phases 1-5: the scope with priorities, the questionnaire answers, the skills plan, the provider config and the
first board. Nothing here is real data.

**The app:** a team of 20 votes on where to have lunch. Someone opens a poll with 2-6 places, people vote once
until 11:30, the result is posted to the team chat.

| File | Phase | What to look at |
|---|---|---|
| `docs/coordination/SCOPE.md` | 1 | P1 vs P2 vs P3, the not-in-v1 list, acceptance criteria |
| `docs/coordination/orchestration-config.md` | 2 | every answer with the option not taken |
| `docs/coordination/SKILLS-PLAN.md` | 2 | task types -> fewest skills, with owner ideas marked |
| `orchestration.toml` | 4 | Claude as lead provider, Codex as build provider, failover on |
| `docs/coordination/PROGRESS.md` | 5 | waves, estimates, dependencies, one item already done |

Try the toolkit against it (from the repository root):
```bash
python skills/build-orchestration-setup/kit/tools/orch.py --config examples/lunch-poll/orchestration.toml board ready
python skills/build-orchestration-setup/kit/tools/orch.py --config examples/lunch-poll/orchestration.toml board metrics
```
