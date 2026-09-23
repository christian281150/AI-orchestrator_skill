# {{PROJECT_NAME}} - instructions for every Codex (and other non-Claude) agent in this repository

1. Start with `docs/coordination/START-HERE.md`. Then `RULES.md`. They outrank everything below.
2. Status is on `docs/coordination/PROGRESS.md`, decisions in `docs/coordination/decisions-log.md` (newest first).
   Never quote a status from any other document without re-measuring it.
3. Before any item: `python tools/orch.py check-not-done <ID>`. After it, same turn: commit -> board -> decisions log.
4. Work only in your lane's files, in your own worktree, on `feat/<lane>-<ID>-<topic>`. Needing another lane's
   file is a request to the coordinator.
5. Reserved for the owner (never do, prepare and queue instead): see `RULES.md` section 2.
6. Credentials: environment variables only, never printed, never in commits, prompts or chat.
7. Write files as UTF-8 without a byte-order mark and with LF line endings (except .ps1/.cmd).
8. Report: what now works; files changed with one-line reason; verbatim test counts; not done and why;
   found but not fixed with file:line; what was not verified.
9. You are a build-only provider unless told otherwise: you implement an APPROVED plan from
   `docs/coordination/ledgers/<ID>/build-brief.md` on your branch. You never merge, never push to main,
   never edit the board or the decisions log. Claude is the merge gate.
