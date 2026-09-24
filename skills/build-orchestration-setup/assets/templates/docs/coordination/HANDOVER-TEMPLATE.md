# HANDOVER <n> - <from session> -> <next session> (<date time, timezone>)

Read this before anything else in a new session. It replaces HANDOVER-<n-1>. The live truth is the
repository: re-measure before quoting any number below.

## 1. What is running right now (measured at <time>)
- Supervisor: <state>, round <id> started <time>, window ends <time>
- Leads / lanes: <ID - lead - state>, ...
- Fallback lanes waiting for the merge gate: <ID - provider - branch>
- Board: <n> done, <n> in progress, <n> open, <n> blocked, <n> parked. P1 shipped: <x>%
- Provider limits: <provider - % used - resets at>

## 2. Model and provider setup
| Role | Provider / model |
|---|---|

## 3. Changes made in this session (all committed, all in decisions-log)
1. <change> - commit <hash> - decision "<title>" - not taken: <option>

## 4. Waiting on the owner (his decisions only)
1. <what it does> - why now - if it waits - blocked behind it

## 5. Known issues, not fixed
- <issue> - impact - workaround

## 6. Not verified
- <claim> - why it could not be checked

## 7. Lessons paid for this session
- <lesson> -> added to RULES.md / lessons file? <yes/no>
