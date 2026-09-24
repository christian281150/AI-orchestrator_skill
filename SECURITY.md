# Security

## Reporting a vulnerability
Please **do not open a public issue**. Use GitHub's private reporting instead:
**Security -> Report a vulnerability** on this repository. You will get an answer within 7 days. Include the
version (`skills/build-orchestration-setup/scripts/orchestrator/__init__.py`), your OS, the agent CLI(s) and
a minimal reproduction.

## Supported versions
The latest minor release receives fixes.

## Security model - what to know before running a build unattended
- **Agents act with your permissions.** The supervisor starts CLI coding agents with the commands in
  `orchestration.toml`. Review those commands and each CLI's permission flags; start with the narrowest
  permission mode that lets the build work (`.claude/settings.json` in the kit has an allow/deny list).
- **Credentials** belong in user-scope environment variables, never in files, prompts or chat. List the names
  in `[safety].required_env`; remove them from build-only providers with `strip_env`. Values may still be
  readable elsewhere on the machine (keychain, registry) - treat build-provider machines accordingly.
- **Reserved actions** (writes to live systems, money, publishing, deleting, credentials) are never done by
  agents under the default rules; they are queued for the owner. Keep that list complete.
- **Git hooks** block captures (`*.har`), keys, `.env` files, data folders and secret-looking strings in added
  lines. They are a safety net, not a guarantee.
- **Anything leaving the machine** (prompts for chat-only models, public exports) should pass
  `orch.py redact control` (a planted fake secret must be found) and then `orch.py redact scan` with zero hits.
- **Run state** (logs, prompts, markers) lives outside the repository in `state_dir`; logs can contain
  whatever agents printed - keep that folder private.
