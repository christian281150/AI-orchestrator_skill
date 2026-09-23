# Scope and priorities - {{PROJECT_NAME}}

Priority decides order. The coordinator never starts P2 while a ready P1 item exists, and never P3 while a
ready P2 exists. The dashboard's headline metric is P1 progress.

| Prio | Meaning | Rule |
|---|---|---|
| **P1** | v1 cannot go live without it - the core loop and what it needs | Acceptance criteria written; no open questions |
| **P2** | v1 should have it; users notice if missing | Planned after P1 is merged or while P1 waits on the owner |
| **P3** | Later. Nice to have, or needs learning from real use first | Not planned until P1 and P2 are done; parked items live here |

## v1 in one sentence
{{TODO: "A <user> can <core job> from <start> to <result> without <current pain>."}}

## Features

| Feature | Prio | Acceptance criteria (given / when / then) | Spec section | Items (IDs) |
|---|---|---|---|---|
| {{TODO}} | P1 | | | |

## Explicitly NOT in v1
(Writing this down is what stops agents - and the owner - from drifting into it.)
- {{TODO}}

## Parked (with the reason and the trigger to un-park)

| Item | Why parked | Un-park when |
|---|---|---|
