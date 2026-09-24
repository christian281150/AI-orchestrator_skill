# Phase 1 - Readiness gate: is the spec ready to be built?

## This skill does not write, refine or align specs
It starts **after** the idea, the functional spec and the architecture are settled. Phase 1 only checks that
they are ready to be handed to a team of agents - it does not help decide what to build. If the check finds
gaps in *what* to build, the answer is a gap list that goes back to the owner's own spec work (with whatever
tools and people they use for that). Then the owner comes back and the gate runs again.

Why so strict: agents are fast at building and bad at guessing. A gap left in the spec returns as wrong code, a
question to the owner at 3 a.m., or two lanes guessing differently. Mixing "decide what to build" into the build
also blurs who decides - the owner decides scope; the orchestration executes it.

## Step 1 - Readiness scorecard (about 15 minutes, read-only)
Fill `docs/coordination/SPEC-READINESS.md` (template in `assets/templates/`). Score each of the 12 dimensions:
0 = missing, 1 = partly or only in someone's head, 2 = written, specific and testable. Cite where each is written.

## Step 2 - Gap list, not a spec workshop
For every dimension below 2, write one line: what is missing, which features it blocks, what would make it a 2.
Examples of gaps: "Feature X has no acceptance criteria"; "who may delete a record is not defined"; "the
architecture names no hosting target". Do **not** propose feature content, flows or designs to fill them.

## Step 3 - Build order (this *is* orchestration work)
Priorities decide the order agents build in. If the spec already carries priorities, map them. If it does not,
ask the owner to tag each feature - this is a build-order decision, not a spec change:
- **P1** - v1 cannot go live without it (test: *if this is missing on day one, does the core job fail?*)
- **P2** - v1 should have it
- **P3** - later
- plus the spec's own **not-in-v1** list, and **parked** items with the trigger that un-parks them.
Record it in `SCOPE.md`. The coordinator never starts P2 while a ready P1 exists; the dashboard headline is P1.

## Step 4 - Build-time decisions (also orchestration work)
Some decisions are about *how* to build, not *what*: which identity loads and scripts run as, test data
(synthetic, where it lives), naming of lanes/branches/IDs, which data may never be sent to an AI provider, what
only the owner may do (reserved actions). Settle these now so they cannot stop the build later. Anything that
changes *what* the product does is a gap for Step 2, not a decision here.

## The gate
Proceed to Phase 2 only when:
- every P1 dimension scores 2 and the total is at least 80%,
- every P1 feature has acceptance criteria **in the spec**,
- the gap list has no P1 entries,
- build order (P1/P2/P3, not-in-v1) and reserved actions are recorded.

If the gate fails: stop, hand the owner the gap list, and end the phase. Non-P1 gaps may proceed as logged
assumptions, each with a revisit date - they are built last and re-checked before they start.

If the owner has the knowledge but not the documents, they can dictate it (10-20 minutes of speech-to-text)
and turn the transcript into spec documents **before** starting this skill.
