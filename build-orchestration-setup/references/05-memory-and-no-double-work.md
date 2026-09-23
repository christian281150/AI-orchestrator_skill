# Memory, continuity, and never doing a task twice

AI sessions forget. Each round, each chat, each subagent starts from what is written down. Most of the
waste in a multi-agent build is not bad code - it is **work redone, work lost, and questions re-asked**
because the state lived in a context window that ended. This file is the system that prevents it.

## The layers - each fact has exactly one home

| Layer | Holds | Written by | Trust |
|---|---|---|---|
| The repository (code, git log, the database as measured) | what is true | everyone | highest - measure it |
| `PROGRESS.md` - the board | status of every item, owner batch, one log line per round | coordinator, leads | status only lives here |
| `decisions-log.md` | closed questions: chosen, over what, why | anyone deciding | append-only, newest first |
| `ledgers/<ID>/` | one item's plan, reviews, task progress | the item's lead | continue from it, never restart |
| `HANDOVER-<n>.md` | what was running, what changed, what waits on the owner | the session that ends | newest wins |
| `RULES.md`, agent files, `SESSION-PROMPT.md` | how to work | owner + monitoring session | re-read every round |
| Spec, `SCOPE.md`, architecture | what to build, in what order | clarity phase | design intent |
| claude.ai Project + memory | how the owner wants to be worked with; the handovers | chat sessions | never status |

**Status never lives in a document.** A status line anywhere but the board is a timestamped measurement,
and it will be wrong within hours. (Real case: a doc said "buy the domain" hours after the domain went live -
the next session told the owner to buy it again.)

## The rituals

**Start of every session / round (about 2 minutes)** - `START-HERE.md` section 1: newest handover -> git
log and status -> board -> top of the decisions log -> supervisor state. Measure, don't trust.

**Before any task** - `python tools/orch.py check-not-done <ID>`: board row and owner, commits on main that
mention the ID, branches (merged or not), ledger. One line of evidence it is not already done or owned.
"It looked open" is not evidence.

**After any task, same turn** - commit -> tick the board with evidence (commit hash, verbatim test counts)
-> log decisions (what you chose it over) -> next task. Not at the end of the session: now.

**When you change the world, change the document in the same commit.** Infrastructure changed? The doc
that describes it changes in the same turn. The work is not done until the document is true.

**End of a session (or before clearing a chat)** - write `HANDOVER-<n+1>.md` from the template: running
state as measured, model setup, changes with commits, waiting on the owner, known issues, not verified,
lessons. Save it to the repo AND the Project.

## Rules that stop re-work and lost work
- **Decisions are closed.** Re-open only with a stated reason. Half the log's value is stopping the next
  session from re-litigating. Record the option not taken.
- **Never overrule a logged decision** to get past an obstacle. Solve it inside the decision, or flag it in
  one line and wait. (Real case: a session silently switched the runtime against a logged decision while
  asking the owner trivial questions one by one - the owner's most expensive interruption of the build.)
- **Corrections are new entries**, naming what they correct. Never silently fix a number.
- **A ledger that exists means someone started.** Continue from it.
- **A worktree belongs to its lane until the branch is merged** (`git branch --no-merged main`). Untracked
  files in a reassigned worktree are gone - no reflog, they were never objects. Commit early.
- **Uncommitted work is unrecoverable work.** Commit continuously on the lane branch; the owner must be able
  to jump back to any point.
- **One writer per file.** File ownership by lane; side sessions commit only through `safe-commit`.
- **Counts carry their scope and time.** "2340 passed" on a branch tip is not the trunk. And a count copied
  into the next item's done-when silently changes from *what was true* (baseline) to *what must stay true*
  (target) - say which; an item that adds tests is expected to move the counts.
- **Quote a claim with its scope.** "No reference in these 23 files" became "nothing anywhere references
  it" - false, because the writer lived in a repository the search never covered.

## Interactive vs autonomous - the rule that stopped a build from stalling
Rules written for a chat ("end with one next action", "restate the state every turn") are a hand-back
protocol. An autonomous session that inherited them stopped every few minutes to report and hand the owner
a task. Scope them:
- **Interactive** (owner waiting in chat): short, action first, state restated, one next action.
- **Autonomous** (working the queue): two legal endings - queue empty, or blocked on the owner after every
  unblocked item is done. Progress goes in commits and the board, not in a turn ending.

## The owner is the bottleneck - design for it
- Batch owner decisions on the board ("Waiting on the owner"): what it would do, why now, what happens if it
  waits, what is blocked behind it. One batch, not a stream.
- A diagnosis never goes on the owner's list; only the remedy does. Read-only investigation of live is the
  agents' job (inside a provably read-only transaction).
- Decide-and-log beats ask: a decision made and disclosed can be reversed; a question asked at 03:00 cannot
  be un-asked.
