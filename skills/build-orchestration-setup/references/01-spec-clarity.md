# Phase 1 - Clarity sprint: make the spec buildable before anything is configured

## Why this phase exists

Agents are fast at building and bad at guessing what you meant. Every ambiguity left in the spec comes
back later in one of three expensive forms:

1. **An agent guesses** -> builds the wrong thing -> review catches it (or doesn't) -> rework.
2. **An agent stops and asks** -> the build waits on the owner, often at night. A question asked at
   03:00 is an hour of the owner's night, and the other lanes pile up behind it.
3. **Two agents guess differently** -> conflicting code in two lanes -> an arbiter, a merge fight, a
   decisions-log entry that should have been a spec line.

Rule of thumb from a real multi-week build: an hour of clarity work before round 1 saved several
agent-hours and at least one owner interruption per open question. Spend the time here.

## Inputs
- Idea / product brief, functional spec, architecture (the three prerequisites from Phase 0)
- Anything else: sketches, sample data (shape only, never licensed data), notes, recordings

If the owner has the knowledge but not the documents: **dictation**. Ask them to talk through the
product for 10-20 minutes with speech-to-text - who uses it, the one job it does, what a good day with
it looks like, what must never happen. Turn the transcript into the documents, then run this phase.

## Step 1 - Readiness scorecard (15 min)
Fill `docs/coordination/SPEC-READINESS.md` (template in the kit). Score each of the 12 dimensions
0 / 1 / 2. Show the owner the scorecard - the zeros and ones are the agenda for step 2.

## Step 2 - Ambiguity hunt (the main work, 30-120 min)
Walk the spec feature by feature. For each, ask the questions below that the spec does not already
answer. Rules:
- **One question at a time**, with your recommended answer and a one-line reason. Use
  `AskUserQuestion` (2-4 options, recommended first). The owner can always type their own.
- **Never ask what the documents or the code can answer.** Read first; ask only the residue.
- Write every answer into the spec (not only into the chat) in the same turn.
- Answers that are decisions go into `decisions-log.md` with the option not taken.

Question bank (pick what applies):
| Area | Questions |
|---|---|
| Core job | Who exactly? What triggers their use? What is the output they take away? How do they do it today? |
| Data | Where does each field come from? What identifies a record? Can it be missing, and how is missing shown (never as zero)? Who may change it, and is history kept? Licensed / third-party data: may it be committed, sent to an AI provider, shown to whom? |
| Flows | What happens on error? On a conflict between two users? On a partial load? What is undoable? |
| Access | Who logs in, how, from which devices? What can each role see and do? How is someone removed? |
| Environments | What is "live"? Is there a demo mode on synthetic data? Who may write to live? |
| Scale | How many users at once, how much data, how fast must it respond? |
| Done | For each feature: what would a machine check to say it works (given / when / then)? |
| Boundaries | What must it never do? What is explicitly not in v1? |

## Step 3 - Prioritise (20-40 min)
Tag every feature in `SCOPE.md`:
- **P1** - v1 cannot go live without it. Test: *if this is missing on day one, does the core job fail?*
  If yes, P1. If the user can work around it for two weeks, it is not P1.
- **P2** - v1 should have it; users notice if missing.
- **P3** - later, or needs learning from real use first.
- **Not in v1** - write the list. It is what stops scope drift, for agents and for the owner.
- **Parked** - with the reason and the trigger that un-parks it.

Challenge the P1 list once: if more than ~40% of estimated hours are P1, the v1 is probably too big.
Offer the owner a cut: which P1s could be P2 with a manual workaround?

The coordinator enforces this order: no P2 while a ready P1 exists, no P3 while a ready P2 exists.
The dashboard headline is P1 progress.

## Step 4 - Acceptance criteria for every P1 feature
Given / when / then, specific enough that a test can be written from it without asking anyone.
Example: *Given a signed-in reviewer and a company with no revenue figure, when they open the company
page, then the revenue cell shows "not reported" (not 0) and the export writes an empty cell.*

## Step 5 - Pre-made decisions
Go through the "Decisions to make now" list in `SPEC-READINESS.md`. Each one left open will stop the
build later - usually at the worst moment. Decide now, log it, write it into the spec.

## Step 6 - Reserved actions
Agree what only the owner may do (writes to live, applying migrations to live, money, publishing,
deleting anything unrebuildable, credentials, widening access). These become `RULES.md` section 2 and
the "Waiting on the owner" table on the board. Everything not on this list, agents decide and log.

## Gate - do not start Phase 2 until
- every P1 dimension in the scorecard is 2, the total is >= 80%,
- every P1 feature has acceptance criteria,
- the P1 open-questions table is empty,
- the not-in-v1 list exists,
- reserved actions are agreed.

Non-P1 gaps may proceed as logged assumptions ("Assumptions accepted" table), each with a revisit date.
