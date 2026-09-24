---
description: Check this computer is ready for an AI-orchestrated build (Python, Git, your AI tools, project folder) - before any project exists
argument-hint: "[AI tool commands to check, e.g. claude codex]"
---

Use the `build-orchestration-setup` skill's toolkit and run its doctor:
`python <skill folder>/scripts/orch.py doctor --project . --tools $ARGUMENTS`
(leave out `--tools` when no tools were given; the owner's profile names them). On macOS/Linux use `python3`.

Show the output as it is. For every FAIL or WARN line, explain the "Fix:" in plain words, one step at a time,
and offer to run the fix where it is safe (never install software or change system settings without a yes).
Finish with one line: ready for `/orchestrate`, or what is still missing.
