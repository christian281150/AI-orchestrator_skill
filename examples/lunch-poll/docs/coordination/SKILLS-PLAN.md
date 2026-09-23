# Skills plan - lunch-poll

Principle: best quality at the lowest cost - fewest skills per task type.

| Task type | Role(s) | Skills | Source | Engines | Model tier | Why this, not more |
|---|---|---|---|---|---|---|
| Planning | planner, plan-reviewer | writing-plans | installed (public process skill) | Claude | top | plans are what Codex builds from |
| Backend / frontend implementation | implementer | test-driven-development | installed; **owner idea: "TDD for everything"** | Claude, Codex | mid | one skill covers both lanes at this size |
| Debugging a failing lane | unblocker | systematic-debugging | installed | Claude | small | only loaded when a lane is stuck |
| Review, tier 2 | task-reviewer | requesting-code-review | installed | Claude | top | - |
| Security review, tier 3 (sign-in) | task-reviewer | security review skill | installed; **owner idea** | Claude | top | sign-in is the only tier-3 item |
| Project rules | all | lunch-poll-chat-webhook | project skill, planned | Claude, Codex | - | the webhook rule would otherwise be re-explained in 3 dispatches |

Owner's ideas: "TDD for everything" -> applied to all implementers; "security review on sign-in" -> W0-3 is tier 3.
Deliberately not added: frontend-design, database-design skills - the app has one table and one page.
