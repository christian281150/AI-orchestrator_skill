# Getting started - step by step, no experience needed

This guide takes you from "never used it" to "my first build is running". You don't need to be a
programmer. You need about **1 hour for installing** (once) and **1-2 hours for the first setup** of a project.
Every step says what to do, how to check it worked, and what to do if it didn't.

> [!IMPORTANT]
> This skill **builds** an app whose idea, spec and architecture are already **settled**. It does not help you
> work out what to build. If you are still deciding features, do that first - the skill will stop and tell you
> what's missing otherwise.

**Contents:** [1 Is this for you?](#1-is-this-for-you) · [2 Words you'll meet](#2-words-youll-meet) ·
[3 Pick your path](#3-pick-your-path) · [4 Install the tools](#4-install-the-tools-path-b) ·
[5 Install the skill](#5-install-the-skill) · [6 Prepare your project folder](#6-prepare-your-project-folder) ·
[7 Your profile (optional)](#7-your-profile-optional-but-saves-time) · [8 First run](#8-first-run) ·
[9 Day to day](#9-day-to-day) · [10 Update or remove](#10-update-or-remove) · [11 Troubleshooting](#11-troubleshooting) ·
[12 Help](#12-getting-help)

---

## 1. Is this for you?
Tick all four:
- [ ] You have written down **what the app is for**, **what it must do** (features, with how you'd check each
      one works), and **how it is built** (technology, hosting, storage).
- [ ] You have at least one **AI coding tool** you can use (for example a command-line coding agent from an AI
      provider, with a subscription).
- [ ] You are fine with AI agents writing code into a folder on your computer, with every change saved in
      history so you can go back.
- [ ] You can spend 1-2 hours answering questions for the first setup.

## 2. Words you'll meet
| Word | What it means here |
|---|---|
| **Terminal** | A window where you type commands. Windows: press `Win`, type *Terminal* (or *PowerShell*), Enter. macOS: *Terminal* app. |
| **Folder / repository (repo)** | Your project folder. "Repository" means git keeps a history of every change in it. |
| **git** | The free program that keeps that history. You won't need to use it by hand - the agents do. |
| **commit / branch / main** | A saved change / a separate line of work / the main version of your code. |
| **Python** | A free programming language. The skill's small helper tool (`orch.py`) runs on it. |
| **CLI** (Command Line Interface) | A program you use by typing in the terminal. |
| **AI coding tool / agent** | An AI that reads and writes code, e.g. a CLI coding agent. |
| **Provider** | The company or tool behind an agent. **Lead provider** = the one that plans, reviews and merges. **Build provider** = one that only builds approved plans. |
| **Skill** | A folder of instructions an AI loads when it's useful - this project is one. |
| **Plugin** | A package that installs a skill plus commands like `/orchestrate`. |
| **Lane** | One piece of work, built by one agent on its own branch. |
| **Board** | `PROGRESS.md` - the single list of all work and its status. |

## 3. Pick your path
| Path | You get | Installs | For |
|---|---|---|---|
| **A - Claude app only** | Level 1: the working rules, board, handovers - agents in one chat | none | trying the method, small builds |
| **B - A coding agent on your computer** (recommended) | Levels 1-4: unattended rounds, several AI tools, failover | Git, Python, your AI coding tool | real builds |
| **C - Other agents** | the skill inside any agent that reads `SKILL.md` folders | Node.js (for `npx`) + your agent | if you already use another agent |

**Path A in 3 steps:** download `build-orchestration-setup.zip` from the
[latest release](https://github.com/christian281150/AI-orchestrator_skill/releases/latest) → upload it in the
app's skill settings → in a new chat, attach your spec documents and write *"Set up the build orchestration -
my spec and architecture are attached."* Then continue with [section 8](#8-first-run).

## 4. Install the tools (path B)
Do these once. After each, open a **new** terminal and run the check.

| # | Install | How (Windows) | Check - type this | Good answer |
|---|---|---|---|---|
| 1 | **Git** | Download from git-scm.com, run it, keep all default choices | `git --version` | `git version 2.x` |
| 2 | **Python 3.11 or newer** | Download from python.org. On the first installer screen **tick "Add python.exe to PATH"** | `python --version` | `Python 3.11` or higher |
| 3 | **Your AI coding tool** | Follow its official install page (for example a CLI coding agent), then log in once | e.g. `claude --version` | a version number |
| 4 | *(only path C)* **Node.js** | Download the LTS version from nodejs.org | `node --version` | `v20` or higher |

- **macOS:** Git comes with the Xcode tools (`xcode-select --install`); Python from python.org; use `python3`
  instead of `python` in every command below.
- **Linux:** use your package manager (`sudo apt install git python3`); use `python3`.
- **Tell git who you are** (once): `git config --global user.name "Your Name"` and
  `git config --global user.email "you@example.com"` (for public repos use your git host's no-reply address).
- **Check everything at once** (after section 5): in your coding agent type `/check-setup`, or in the terminal
  `python <skill folder>/scripts/orch.py doctor --tools <your AI tool>`. It lists every problem with the fix
  (`DOCTOR OK` = ready).

## 5. Install the skill
**Path B** - in the terminal:
```text
claude plugin marketplace add christian281150/AI-orchestrator_skill
claude plugin install ai-orchestrator@ai-orchestrator
```
(Inside a running Claude Code session the same works as `/plugin marketplace add ...` and `/plugin install ...`.)
**Check:** `claude plugin list` shows `ai-orchestrator`, and in a session typing `/orch` suggests `/orchestrate`.

**Path C:** `npx skills add christian281150/AI-orchestrator_skill` and pick your agent when asked.

## 6. Prepare your project folder
1. Create an empty folder for the project, e.g. `C:\Projects\my-app` (avoid spaces and cloud-synced folders).
2. Inside it create a folder `docs` with three documents (plain text or Markdown is best):

| File | Must contain | Tiny example |
|---|---|---|
| `docs/idea.md` | who uses it, the one job it does, what "version 1 done" means | "Team members vote on a lunch place; v1 = open poll, vote, see winner" |
| `docs/spec.md` | every feature, and for each: how you'd check it works (given / when / then) | "Given 2-6 places, when I open a poll, then colleagues can vote until 11:30" |
| `docs/architecture.md` | technology, where it runs, where data is stored, how people log in | "Web app, Python backend, SQLite, company login" |

Look at [`examples/lunch-poll`](../examples/lunch-poll) to see what a finished setup looks like.

## 7. Your profile (optional, but saves time)
Your **profile** is your customization file: preferences you answer once and reuse for every project (your
name for commits, how technical the language should be, which AI tools you use, what only you may do...).
Every question the profile answers is skipped in the setup.

- **Easiest:** in your coding agent, type *"Create my AI orchestrator profile and walk me through it."*
- **By hand:** `python <skill folder>/scripts/orch.py profile init`, then open
  `~/.ai-orchestrator/profile.toml` (Windows: `C:\Users\<you>\.ai-orchestrator\profile.toml`) in Notepad.
  Every line has a comment; leave anything empty that you want to be asked.
- **Check it:** `python <skill folder>/scripts/orch.py profile check` → `profile OK`.

All keys: [CONFIGURATION.md](CONFIGURATION.md).

## 8. First run
1. Open a terminal **in your project folder** (Windows: open the folder in Explorer, right-click → *Open in Terminal*).
2. Start your coding agent (e.g. type `claude`, Enter).
3. Type: `/orchestrate docs/` - or just *"My spec and architecture are in docs/ - set up the build orchestration."*

What happens next (you mostly answer questions; each has a **recommended** answer you can simply take):

| Step | What you do | Time |
|---|---|---|
| 0 Prerequisites | confirm where your documents are | 2 min |
| 1 Readiness gate | read the scorecard; if it lists gaps, fix them in your documents and start again | 10-20 min |
| 2 Questionnaire | answer about 10 short rounds (fewer with a profile) | 20-30 min |
| 3-4 Setup | say yes to installs and settings it proposes | 10-20 min |
| 5 Board | read the work plan (waves, priorities) and confirm | 10 min |
| 6 Prove it | watch the checks go green and one trial round | 10-15 min |
| 7 Build | it starts - you can close the window if you chose "unattended" | days |

## 9. Day to day
- **Where are we?** Type `/build-status` in your agent (or open `docs/coordination/PROGRESS.md`).
- **Something waiting for you?** The board's table **"Waiting on the owner"** lists every decision only you can
  make (e.g. anything that touches live systems or money). Answer in the chat; the agent logs it.
- **Pause:** create an empty file `docs/coordination/STOP` (or ask the agent to). The build finishes the current
  round and stops. Delete the file to continue. **Never** close a running round by force - its lanes are lost.
- **Your computer:** unattended builds need it on and **not sleeping** (Windows: Settings → System → Power →
  Sleep: *Never* when plugged in).
- **Local live view** (if you chose it): double-click `tools/scheduling/live-view.cmd` (Windows) - a page that
  refreshes every 30 seconds.

## 10. Update or remove
- **Update:** `claude plugin marketplace update ai-orchestrator` then `claude plugin update ai-orchestrator@ai-orchestrator`.
- **Remove:** `claude plugin uninstall ai-orchestrator@ai-orchestrator`. Your project files stay as they are.
- Claude app: upload the new zip from the latest release; delete the old skill in the skill settings.

## 11. Troubleshooting
| You see | Why | Fix |
|---|---|---|
| `'git' is not recognized` / `'python' is not recognized` | not installed, or the terminal was open during install | install again; for Python **tick "Add to PATH"**; open a **new** terminal |
| `python` opens the Microsoft Store | Windows' placeholder, not real Python | install from python.org with "Add to PATH", or turn off *App execution aliases* for python in Windows settings |
| Not sure what's wrong | - | run `/check-setup` (or `orch.py doctor`) - every problem comes with its fix |
| `/orchestrate` is not suggested | plugin not loaded yet | restart the agent; `claude plugin list` must show `ai-orchestrator` |
| The skill stops at step 0 or 1 | your idea/spec/architecture are missing or have gaps - by design | fix the listed gaps in your documents, then run `/orchestrate` again |
| `PREFLIGHT FAILED` | a setup check is red | each `[FAIL]` line says what's wrong (e.g. a tool not installed); fix it or ask the agent to |
| A commit is refused: "forbidden path" or "possible secret" | the safety hook protected you (a key, password or capture file) | remove the secret from the file; keep secrets in environment variables |
| Build stopped overnight | computer slept, or an AI tool hit its usage limit | set Sleep to *Never*; limits reset on their own - the build continues when they do |
| `BLOCKED.txt` appeared | the same error happened 3 times | open it; ask the agent "why is the build blocked?" |

## 12. Getting help
- **Question or stuck?** [Q&A in Discussions](https://github.com/christian281150/AI-orchestrator_skill/discussions/categories/q-a)
- **Tried it?** Tell me how it went in [Show and tell](https://github.com/christian281150/AI-orchestrator_skill/discussions/categories/show-and-tell) - it really helps.
- **Found a bug?** [Open an issue](https://github.com/christian281150/AI-orchestrator_skill/issues/new/choose).
