# Board - lunch-poll

## Items

| ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| W0-1 | Repo, CI, test harness, synthetic members | P1 | 0 | infra | 3 | - | done | | | merged 4f2a9c1, 18 passed |
| W0-2 | Storage: polls, places, votes | P1 | 0 | backend | 2 | W0-1 | plan-approved | | Codex-eligible | |
| W0-3 | Sign-in with company account (tier 3) | P1 | 0 | backend | 4 | W0-1 | in-progress | lead-backend-1 | plan review round 2 | |
| W1-1 | Open a poll (2-6 places) | P1 | 1 | backend | 3 | W0-2 | open | | | |
| W1-2 | Vote once, replace on re-vote | P1 | 1 | backend | 2 | W0-2 | open | | | |
| W1-3 | Post result to team chat at close | P1 | 1 | backend | 3 | W1-1, W1-2 | blocked | | owner: chat webhook secret | |
| W1-4 | Poll page (open, vote, see result) | P1 | 1 | frontend | 4 | W1-1 | open | | | |
| W2-1 | Favourite places | P2 | 2 | backend | 2 | W1-3 | open | | | |
| W3-1 | Weekly stats | P3 | 3 | backend | 3 | W1-3 | parked | | un-park when 3 people ask | |

## Waiting on the owner (one batch)

| # | What it would do | Why now | If it waits | Blocked behind it |
|---|---|---|---|---|
| 1 | Set `LUNCH_CHAT_WEBHOOK` as a user environment variable | W1-3 needs a test post | W1-3 stays blocked; nothing else | W1-3 |
