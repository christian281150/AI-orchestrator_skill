# Notice

**AI-orchestrator_skill** - Copyright (c) 2026 christian281150 and contributors.
Licensed under the MIT License (see [LICENSE](LICENSE)).

## Third-party code
None is bundled. The toolkit (`skills/build-orchestration-setup/scripts/`) uses the Python standard library
only. The GitHub Actions workflows reference third-party actions by version; they run on GitHub, not in the
distributed skill.

## Trademarks and affiliation
Claude and Claude Code are trademarks of Anthropic, PBC. Codex is a trademark of OpenAI. Gemini is a trademark
of Google LLC. Cursor, GitHub and other product names are trademarks of their respective owners. They are
named only to describe compatibility. This project is independent and is **not affiliated with, endorsed by,
or sponsored by** any of them.

## No warranty
The skill instructs AI agents to change code, run commands and use paid services on your behalf. You stay
responsible for what runs on your machines and accounts: review the reserved-actions list, the provider
commands and the permissions before running a build unattended. See [SECURITY.md](SECURITY.md).
