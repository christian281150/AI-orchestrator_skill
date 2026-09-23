# Contributing

- One concern per pull request. Tests with every behaviour change (`pytest tests`), and every new check must
  be shown going red on a broken input.
- The toolkit stays standard-library Python 3.11+. No new dependencies.
- A new lesson goes into `references/08-lessons-learned.md` with what it cost and what now prevents it.
- CLI flags and usage-record formats of AI providers change: say which CLI version you verified against.
- Never commit real data, captures, credentials or anything identifying a client.
