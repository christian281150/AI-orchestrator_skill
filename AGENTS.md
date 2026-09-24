# AGENTS.md - working on this repository

Guidance for AI coding agents (Claude Code, Codex, Cursor, Gemini, ...) that change **this** repository.
(Instructions for agents in a project that *uses* the skill live in `skills/build-orchestration-setup/assets/templates/`.)

## Layout
```
skills/build-orchestration-setup/   the skill - follows the Agent Skills spec (agentskills.io/specification)
  SKILL.md                          lean: phases + pointers; keep under 500 lines / ~5k tokens
  references/NN-topic.md            detail (01 readiness gate ... 11 long-running builds), loaded on demand
  scripts/                          orch.py + orchestrator/ - Python 3.11+ standard library ONLY
  assets/templates/                 files `orch.py init` copies into a user's repository
  assets/profile.toml               the owner's customization file template (`orch.py profile init`)
docs/                               GETTING-STARTED.md (beginners) and CONFIGURATION.md (every key) - update
                                    CONFIGURATION.md whenever a profile or orchestration.toml key changes
commands/                           Claude Code slash commands (markdown + frontmatter)
.claude-plugin/ .codex-plugin/ .cursor-plugin/   plugin manifests - same version everywhere
examples/lunch-poll/                worked example; must stay valid (a test checks it)
tests/                              pytest; stand-in providers, no real AI CLI needed
tools/bump_version.py               the only way to change the version
```

## Commands
```bash
python -m pytest                                   # all tests (Linux, macOS, Windows in CI)
ruff check .                                       # lint (config in pyproject.toml)
skills-ref validate skills/build-orchestration-setup   # Agent Skills reference validator
python tools/bump_version.py 1.4.0                 # bump every version field at once
```

## Rules
0. **Scope:** this skill orchestrates the *build* of a settled spec. Never add features that write, refine or
   align specs - that belongs before this skill.
1. **Stdlib only** in `scripts/`. No dependency may be added.
2. **Provider-neutral.** No text or code may assume one AI vendor. Vendor specifics live in example config and
   clearly marked readers, with the CLI version they were verified against.
3. **Every new check must be shown going red** on a broken input in a test.
4. **No secret-looking literals** in any file, tests included - assemble fake values at runtime
   (see `tests/test_redact.py`). The kit's own pre-commit hook and GitHub push protection would flag them.
5. **Never commit** real data, captures, credentials, client or employer names.
6. **Version** changes only through `tools/bump_version.py`, with a `CHANGELOG.md` entry
   ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/), [SemVer](https://semver.org/)).
7. **Commits:** one concern each; conventional prefixes (`feat:`, `fix:`, `docs:`, `build(deps):`, `chore:`).
   No AI attribution trailers.
8. **Docs claims must be verified.** The README's "Verified and not verified" section is updated whenever a
   claim changes.
