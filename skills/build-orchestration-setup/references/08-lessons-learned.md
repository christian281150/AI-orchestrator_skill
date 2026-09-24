# Lessons paid for

From a multi-week build run by up to 10 parallel lead lanes (Claude) plus build lanes on a second provider
(Codex) on one Windows PC, with a chat session monitoring. The lessons are provider-neutral. Each lesson cost at least one broken round, a lost afternoon, or an owner
interruption. Each is built into the kit where it can be; the rest are rules.

## Process and memory
1. **Status in documents rots within hours.** A doc told the owner to buy a domain that had been live for
   hours. -> Status only on the board; docs carry rules and design; precedence table in START-HERE.
2. **Chat rules made the autonomous build stall.** "End with one next action" turned every agent into a
   hand-back. -> Separate interactive and autonomous contracts.
3. **Re-litigated decisions.** Without "chosen over what", the next session reopened closed questions. ->
   Decisions log with the option not taken.
4. **A session overruled a logged decision** to get past an obstacle, then asked the owner trivial details
   one by one. -> Solve inside the decision or flag it in one line; never both override and interrogate.
5. **Work done twice.** -> `check-not-done` before every item; ledgers; same-turn board ticks.
6. **Untracked files lost** when a worktree was reassigned before its branch merged. -> Worktree stays with
   its lane until merged; commit continuously.
7. **Two sessions, one working tree** -> git conflicts. -> One worktree per lane, file ownership.
8. **Counts quoted out of scope** ("branch tip" quoted as "trunk"; "23 files" quoted as "anywhere"). ->
   Every count says where and when; baseline vs target.
9. **The owner as bottleneck.** -> Batch his decisions; decide-and-log everything else.

## Evidence and tests
10. **A check that cannot go red is not a check.** A build gate passed on a stale directory; a suite's green
    depended on which credential variable happened to be set. -> Every probe has a control.
11. **Skips hid a regression.** 509 skipped database tests - including the suite that would have caught it.
    -> A strict mode where "infrastructure unavailable" fails; skip summary printed on every run.
12. **Missing tool, exit 0.** A Python without pytest printed "No module named pytest" and exited 0. -> Use the
    exact interpreter; treat unexpected output as failure.
13. **Wrong identity.** A load ran as the admin role instead of the app role and stamped 14,175 rows with
    unusable attribution. -> Check the connected identity before trusting any result.
14. **A probe that rejects everything proves nothing.** A permission "regression" was the test running as the
    wrong user - caught only because a control table was rejected too.
15. **Line endings broke a checksum** on unchanged content (hashed during a line-ending window). -> Fix
    `.gitattributes` before the first hash.
16. **Test defaults pointing at the general local server.** -> Test port separate; a guard test fails if any
    test defaults elsewhere.

## Orchestration mechanics
17. **Killing the coordinator killed every lead**; their work came back half-done. -> Never kill a round; STOP
    file between rounds; hard cap only.
18. **A side session's plain `git commit` concluded the coordinator's half-done merge**, conflict markers
    included. -> `safe-commit`: waits for no merge, commits only its paths.
19. **A failed restore left main dirty**: one `git checkout -- <list>` with a new file in the list failed for
    the whole list. -> Restore path by path.
20. **Headless mode killed background work after 600 s**; two rounds died before it was found. -> Raise the
    ceiling env var or dispatch in the foreground.
21. **Long rounds are expensive**: context 25k -> 129k over 100 turns, ~11M tokens in one round, vs ~25k to
    start a new one. -> One wave / 2-3 h per round.
22. **The supervisor script is read once at launch**; a rule change in it silently did not apply. -> Re-exec
    between rounds on change.
23. **Changing a cap missed the formula that used it.** -> `git grep` every form of a number before changing it.
24. **A test id that didn't match the board's id pattern silently matched nothing.** -> Validate ids.
25. **False "usage limit" from log text** the agent had merely read. -> Provider's own record decides; tail only.
26. **Skills promised in agent files weren't installed** (12 of them). -> Preflight checks every named skill.
27. **10 leads on 16 GB RAM ran at the edge.** -> Measure one round before raising parallelism.
28. **External agents spawn their own helpers.** -> Count them in RAM and allowance planning.
29. **A build provider emptied its weekly allowance in hours** (~2.5 points per 5 minutes with 5-6 lanes). ->
    Measure burn per provider before scaling; usage meters with thresholds; route easier work to it deliberately.
30. **Everything stopped while the lead was limited**, although cloud credit sat unused. -> Cloud planners with
    steady / accelerate / handback rules and a credit floor; a keeper independent of rounds.
31. **Plans from another tool looked fine and weren't.** -> Knowledge-gap check every round; blind re-plan by the
    lead and an arbiter before a foreign plan is built.
32. **Cloud sessions planned against stale code, or could not push.** -> Push on commit/merge; connect the git host
    to the cloud service before starting sessions; never reuse sessions started without it.
33. **A session refused to hand its work over; the plan was lost.** -> Plans live in the repository (ledgers),
    never only inside a session.
34. **Mixing "what to build" into the build** blurred who decides and produced questions mid-run. -> This skill
    starts only when the spec is settled; the readiness gate returns gaps instead of filling them.

## Windows specifics
35. PowerShell 5.1: `>` writes UTF-16; `Set-Content -Encoding UTF8` adds a byte-order mark (breaks agent
    frontmatter); native arguments lose double quotes; `*>` with `ErrorActionPreference=Stop` turns stderr
    into a fatal error. -> The kit is Python; write UTF-8 without BOM; use `Start-Process` redirects.
36. The console code page (cp1252) broke tools reading git output. -> Always decode git output as UTF-8.
37. Command lines over ~8k characters fail. -> Pass prompts as files.
38. A remote tool call times out after ~60 s. -> Start long jobs detached and poll.
39. Never run a file edit and its commit in the same parallel batch - the commit can take the old version.
40. PowerShell `Start-Process -ArgumentList` splits arguments that contain spaces - quote them explicitly.

## Infrastructure and safety
41. **Blast radius decides hosting.** A breach of a tunnel ending on a personal PC reaches everything on it; on
    a small VM it reaches a server rebuilt in 20 minutes.
42. **Sequencing, not attackers:** configure the access policy before the endpoint is reachable.
43. **Paid capacity left scaled up** costs money for nothing. -> Up in the step that starts the load, down in a
    `finally`.
44. **External build agents with full access** (sandbox broken on the OS): credentials stripped from their
    environment, residual risk named in the handover.
45. **Data leaving the machine**: redact with a proven scanner (planted secret found, then zero hits).
