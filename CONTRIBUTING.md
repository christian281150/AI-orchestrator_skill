# Contributing

Thanks for helping. The most valuable contribution is simple: **try it and tell me how it went** in
[Discussions -> Show and tell](https://github.com/christian281150/AI-orchestrator_skill/discussions/categories/show-and-tell).

For code and docs, the bar is the same one the skill sets for agents: **measured, not inferred**.

## Ground rules
- **One concern per pull request.** The subject says what changed; the body says why, what it was chosen over,
  and what it does not cover.
- **Tests with every behaviour change:** `python -m pytest tests -q`. Every new check must be shown going red
  on a broken input (a check that cannot fail is not a check).
- **Standard library only** for the toolkit, Python 3.11+. No new dependencies.
- **Provider-neutral.** Nothing may assume one AI vendor. Provider specifics go into `orchestration.toml`
  examples and `providers.py` readers, clearly marked with the CLI version they were verified against.
- **Skill format** follows the [Agent Skills specification](https://agentskills.io/specification): `name`
  matches the folder, `description` says what and when (max 1024 characters). Keep `SKILL.md` lean; detail goes
  to `references/`.
- **Never commit** real data, captures, credentials, or anything that identifies a client or employer.

## New lessons
A lesson from a real build goes into `skills/build-orchestration-setup/references/08-lessons-learned.md` with
what it cost and what now prevents it - and, where possible, into a kit check or rule.

## Releasing (maintainers)
1. Bump the version in all places the tests check (`tests/test_repo_meta.py` lists them).
2. Add a `CHANGELOG.md` entry.
3. Tag `vX.Y.Z` and push the tag - the release workflow attaches the skill zip for upload to Claude apps.
