# Scope and priorities - lunch-poll

## v1 in one sentence
A team member can open a lunch poll, colleagues vote once before 11:30, and the winner is posted to the team
chat without anyone counting by hand.

## Features

| Feature | Prio | Acceptance criteria (given / when / then) | Items |
|---|---|---|---|
| Open a poll with 2-6 places | P1 | Given a signed-in member, when they submit 1 or 7 places, then the form refuses with the reason; with 2-6 it opens a poll that closes at 11:30 local time | W1-1 |
| Vote once | P1 | Given an open poll, when a member votes twice, then the second vote replaces the first; the count per place never exceeds the number of members | W1-2 |
| Post the result | P1 | Given the poll closes, then within 1 minute the winner and counts are posted to the configured chat webhook; a tie lists all tied places | W1-3 |
| Sign in with the company account | P1 | Given a non-member email, when they try to sign in, then access is refused | W0-3 |
| Favourite places list | P2 | Given 3 past polls, when opening a new one, then the 5 most-chosen places are offered | W2-1 |
| Weekly stats | P3 | - | W3-1 |

## Explicitly NOT in v1
- Restaurant menus, prices, maps, delivery ordering
- Polls for anything other than lunch
- A mobile app (the web page works on phones)

## Parked
| Item | Why parked | Un-park when |
|---|---|---|
| W3-1 Weekly stats | nobody asked; P1 first | three people ask for it |
