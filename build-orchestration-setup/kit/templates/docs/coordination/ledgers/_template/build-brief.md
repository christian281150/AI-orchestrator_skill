# Build brief - <ID> <item>   (for a build-only provider; self-contained)

You build exactly this approved plan on branch `<branch>` in `<worktree>`. You do not merge. You do not
push to main. You do not touch the board, the decisions log, live systems, or credentials.

1. Read, in order: <paths>
2. Tasks (from plan.md, approved <date>): <copy the task table>
3. For each task: failing test first, smallest complete change, run its verify command, commit
   (one task per commit, author per repo config, no attribution lines).
4. Finish by writing `docs/coordination/ledgers/<ID>/progress.md`: per task - done / verify output verbatim /
   commit hash; then "Not done" and "Found but not fixed (file:line)". Empty lists mean you did not look.
