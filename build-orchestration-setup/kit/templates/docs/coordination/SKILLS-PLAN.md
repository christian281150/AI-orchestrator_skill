# Skills plan - {{PROJECT_NAME}}

Built in Phase 2 (skills round). Principle chosen: {{TODO: best quality at lowest cost | max quality | minimal}}.
Inventory: `python tools/orch.py skills`. Every skill named here is installed for every engine that runs the
role (`preflight` checks it). Change this file -> log the decision -> update the agent files in the same commit.

## Task types -> skills

| Task type | Role(s) | Skills (fewest that cover it) | Source (installed / owner / public / project) | Engines | Model tier | Why this, not more |
|---|---|---|---|---|---|---|
| Planning | planner, plan-reviewer | | | | top | |
| Backend implementation | implementer | | | | mid | |
| Frontend implementation | implementer | | | | mid | |
| Database / migrations | implementer, task-reviewer | | | | mid / top | |
| Debugging a failing lane | unblocker, lead | | | | small / top | |
| Review (tier 2) | task-reviewer | | | | top | |
| Security review (tier 3) | task-reviewer | | | | top | |
| Documentation | documentarian | | | | mid | |

## Project skills (this app's own rules)

| Skill | Covers | Written from | Status (planned / written / installed) |
|---|---|---|---|
| {{PROJECT_NAME}}-data-access | identities, connections, what may be read/written where | spec + decisions | planned |

## Owner's ideas (as given, and what was done with each)
- 

## Installed where
| Engine | Skill folder(s) | Install command | Pinned version |
|---|---|---|---|
