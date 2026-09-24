# SPDX-License-Identifier: MIT
"""Command line: python tools/orch.py <command> [...]   (run `-h` for help)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_CFG = "orchestration.toml"


def _cfg(args):
    from .config import load
    return load(args.config)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="orch", description="Agent build orchestration kit")
    ap.add_argument("--config", default=DEFAULT_CFG, help="path to orchestration.toml (default: ./orchestration.toml)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="copy templates + tools into a repository")
    s.add_argument("target")
    s.add_argument("--name", required=True)
    s.add_argument("--author-name", default="")
    s.add_argument("--author-email", default="")
    s.add_argument("--main-branch", default="main")
    s.add_argument("--force", action="store_true")

    sub.add_parser("unfilled", help="list {{PLACEHOLDERS}} still to fill").add_argument("target", nargs="?", default=".")
    s = sub.add_parser("profile", help="your personal customization file: init | show | check | learn")
    s.add_argument("action", choices=["init", "show", "check", "learn"])
    s.add_argument("--from", dest="record", default="docs/coordination/orchestration-config.md",
                   help="learn: the finished questionnaire record")
    s.add_argument("--write", action="store_true", help="learn: apply the listed additions (default: show only)")
    s.add_argument("--project", nargs="?", const=".", default=None,
                   help="use <repo>/.ai-orchestrator.toml (default repo: current folder) instead of the home profile")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("doctor", help="is this computer ready? (before any project exists)")
    s.add_argument("--tools", nargs="*", default=None, help="AI tool commands to check, e.g. claude codex")
    s.add_argument("--project", default=None, help="the project folder you plan to use")
    s = sub.add_parser("usage", help="read an AI tool's allowance from its own record (JSON for usage_command)")
    s.add_argument("tool", choices=["claude", "codex"])
    s.add_argument("--logs", nargs="*", default=[], help="claude: stream-json logs or folders to scan as well")
    s.add_argument("--capture", action="store_true", help="claude: statusline hook - read status JSON from stdin")
    sub.add_parser("preflight", help="check everything a round depends on")
    s = sub.add_parser("skills", help="inventory installed skills per engine; flag skills agent files name but lack")
    s.add_argument("root", nargs="?", default=".")
    s.add_argument("--extra", nargs="*", default=[], help="more skill folders to scan")
    s = sub.add_parser("supervise", help="run rounds unattended (with provider failover)")
    s.add_argument("config_path", nargs="?")
    s.add_argument("--passes", type=int, default=None)
    sub.add_parser("keeper", help="one keeper pass: restarts, build lanes, idle planning, cloud planners")
    sub.add_parser("gap", help="knowledge gap: work the lead did not see, and REVIEWERS=<n>")
    s = sub.add_parser("board", help="validate | ready | metrics")
    s.add_argument("action", choices=["validate", "ready", "metrics"])
    s = sub.add_parser("check-not-done", help="evidence that an item is not already done / owned")
    s.add_argument("item")
    s = sub.add_parser("safe-commit", help="commit only these paths, safely")
    s.add_argument("-m", "--message", required=True)
    s.add_argument("paths", nargs="+")
    s = sub.add_parser("redact", help="scan | apply | control a text file before it leaves the machine")
    s.add_argument("action", choices=["scan", "apply", "control"])
    s.add_argument("file")
    s = sub.add_parser("snapshot", help="read-only progress JSON")
    s.add_argument("--since", default="24 hours ago")
    s.add_argument("--out")
    s = sub.add_parser("live-view", help="write a self-refreshing local HTML status page")
    s.add_argument("--out", default="live-view.html")
    s = sub.add_parser("hook", help="internal: run a git hook")
    s.add_argument("name", choices=["pre-commit", "commit-msg"])
    s.add_argument("arg", nargs="?")
    a = ap.parse_args(argv)

    if a.cmd == "doctor":
        from .doctor import run as doctor
        fails, lines = doctor(a.tools, Path(a.project) if a.project else None)
        print("\n".join(lines))
        print("DOCTOR OK - ready for the first setup" if not fails else f"DOCTOR: {fails} problem(s) to fix first")
        return 1 if fails else 0
    if a.cmd == "usage":
        from . import usage_readers as ur
        if a.capture:
            print(ur.capture_claude(sys.stdin.read()))
            return 0
        logs = [Path(x) for x in a.logs]
        if a.tool == "claude" and Path(a.config).exists():
            state = _cfg(a).state_dir
            logs += [state / "rounds", state / "fallback" / "logs"]
        data = ur.read_claude(logs=logs) if a.tool == "claude" else ur.read_codex()
        print(json.dumps(data))
        return 2 if data["status"] == "unreadable" else 0
    if a.cmd == "profile":
        from . import profile
        if a.action == "init":
            ok, msg = profile.init(Path(a.project).resolve() if a.project else None, force=a.force)
            print(msg)
            return 0 if ok else 1
        if a.action == "learn":
            if not Path(a.record).exists():
                print(f"no questionnaire record at {a.record} - pass --from <orchestration-config.md>")
                return 1
            target = profile.paths(Path(a.project).resolve() if a.project else None)[-1]
            plan = profile.learn(Path(a.record), target, a.write)
            titles = {"add": "will be added (profile was empty)" if not a.write else "added",
                      "same": "already in your profile", "kept_yours": "your value kept - never overwritten",
                      "not_learned": "not learned"}
            print(f"profile: {target}")
            for k, title in titles.items():
                if plan[k]:
                    print(f"{title} ({len(plan[k])}):")
                    print("\n".join("  " + x for x in plan[k]))
            if plan["add"] and not a.write:
                print("nothing written - run again with --write to apply the additions")
            return 0
        prof, used = profile.load(Path(a.project or ".").resolve())
        if a.action == "check":
            probs = profile.check(prof)
            print("\n".join(probs) or f"profile OK ({', '.join(used) or 'no profile file found - everything will be asked'})")
            return 1 if probs else 0
        print("files: " + (", ".join(used) or "none - everything will be asked"))
        ans = profile.answered(prof)
        print(f"questionnaire items answered by the profile ({len(ans)}):")
        for item, v in ans.items():
            print(f"  {item:<5} {v}")
        return 0
    if a.cmd == "init":
        from .init_kit import init
        from .profile import load as load_profile
        owner = load_profile(Path(a.target).resolve())[0].get("owner", {})
        vals = {"PROJECT_NAME": a.name, "AUTHOR_NAME": a.author_name or owner.get("git_author_name", ""),
                "AUTHOR_EMAIL": a.author_email or owner.get("git_author_email", ""), "MAIN_BRANCH": a.main_branch}
        print("\n".join(init(a.target, vals, a.force)))
        return 0
    if a.cmd == "unfilled":
        from .init_kit import unfilled
        hits = unfilled(a.target)
        print("\n".join(hits) or "no placeholders left")
        return 1 if hits else 0
    if a.cmd == "skills":
        from .skills import report
        lines, missing = report(Path(a.root).resolve(), a.extra)
        print("\n".join(lines))
        return 1 if missing else 0
    if a.cmd == "supervise":
        from .supervisor import supervise
        print(supervise(a.config_path or a.config, a.passes))
        return 0
    if a.cmd == "redact":
        from . import redact
        text = Path(a.file).read_text(encoding="utf-8", errors="replace")
        terms = []
        if Path(a.config).exists():
            terms = _cfg(a).redact_terms
        if a.action == "control":
            ok = redact.control(text, terms)
            print("CONTROL PASS: planted fake secret detected" if ok else "CONTROL FAIL: scanner missed the planted secret")
            return 0 if ok else 1
        if a.action == "scan":
            hits = redact.scan(text, terms)
            for n, name, val in hits:
                print(f"line {n}: {name}: {val[:6]}...")
            print(f"{len(hits)} hit(s)")
            return 1 if hits else 0
        out = Path(a.file).with_suffix(".redacted" + Path(a.file).suffix)
        out.write_text(redact.redact(text, terms), encoding="utf-8")
        print(f"wrote {out}; re-run `redact scan` on it - expect 0 hits")
        return 0

    cfg = _cfg(a)
    if a.cmd == "preflight":
        from .preflight import run
        fails, lines = run(cfg)
        print("\n".join(lines))
        print(f"PREFLIGHT {'OK' if not fails else f'FAILED ({fails})'}")
        return 1 if fails else 0
    if a.cmd == "keeper":
        from .keeper import run_once
        actions = run_once(cfg)
        print("\n".join(actions) or "keeper: nothing to do")
        return 0
    if a.cmd == "gap":
        from .gap import report
        lines, n = report(cfg)
        print("\n".join(lines))
        return 0
    if a.cmd == "board":
        from . import board
        rows = board.parse(cfg.board)
        if a.action == "validate":
            probs = board.validate(rows, cfg.id_pattern)
            print("\n".join(probs) or f"board OK ({len(rows)} rows)")
            return 1 if probs else 0
        if a.action == "ready":
            for r in board.ready(rows):
                print(f"{r.id}\t{r.prio}\t{r.wave}\t{r.lane}\t{r.est}h\t{r.status}\t{r.item}")
            return 0
        print(json.dumps({"all": board.metrics(rows), "P1": board.metrics(rows, "P1")}, indent=2))
        return 0
    if a.cmd == "check-not-done":
        from . import board
        done, ev = board.not_done_evidence(cfg.root, a.item, board.parse(cfg.board), cfg.ledgers, cfg.main_branch)
        print("\n".join(ev))
        print("VERDICT: already done or owned - do not start" if done else "VERDICT: not done - safe to start")
        return 1 if done else 0
    if a.cmd == "safe-commit":
        from .safe_commit import safe_commit
        ok, msg = safe_commit(cfg.root, a.message, a.paths)
        print(msg)
        return 0 if ok else 1
    if a.cmd == "snapshot":
        from .snapshot import snapshot
        data = json.dumps(snapshot(cfg, a.since), indent=2)
        if a.out:
            Path(a.out).write_text(data, encoding="utf-8")
        print(data)
        return 0
    if a.cmd == "live-view":
        from .snapshot import live_view
        print(live_view(cfg, Path(a.out)))
        return 0
    if a.cmd == "hook":
        from . import hooks
        errs = hooks.pre_commit(cfg) if a.name == "pre-commit" else hooks.commit_msg(cfg, a.arg)
        for e in errs:
            print(f"[{a.name}] {e}", file=sys.stderr)
        return 1 if errs else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
