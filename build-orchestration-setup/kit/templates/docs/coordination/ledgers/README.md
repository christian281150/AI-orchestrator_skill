# Ledgers - one folder per item (`ledgers/<ID>/`)

A ledger is how a lead, a builder on another provider, or the next round continues without re-deriving
anything. If a ledger exists, the item was started: continue from it, never restart.

Copy `_template/` to `<ID>/`. Files:
- `plan.md` - the planner's plan (max 6 tasks, each with files, done-looks-like, verify command)
- `plan-review-<n>.md` - independent review: APPROVED / CHANGES REQUIRED (max 2 rounds, then the lead rules and logs it)
- `build-brief.md` - self-contained brief a build-only provider can execute (its existence + status
  `plan-approved` makes the item eligible for fallback lanes)
- `progress.md` - task-by-task log: done / verify output / commit
