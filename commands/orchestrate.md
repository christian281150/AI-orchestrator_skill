---
description: Orchestrate the build of this project with AI agents once idea, spec and architecture are settled - readiness gate, setup questionnaire, skills plan, workspace, lanes, failover, reporting
argument-hint: "[where the settled idea, spec and architecture are]"
---

Use the `build-orchestration-setup` skill and run it from Phase 0.

Where the idea, spec and architecture live: $ARGUMENTS
If that is empty, ask for their location first. Say at the start that this skill builds a settled spec and does
not write or align specs. If any of the three is missing or still under discussion, stop at Phase 0 and explain
what must be settled first.
