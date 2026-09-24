"""Keeper passes with stand-in providers: which tool is started when."""
import json
import sys
import time
from pathlib import Path

from orchestrator import keeper, supervisor
from orchestrator.config import load
from orchestrator.gap import knowledge_gap
from conftest import sh

BOARD = """| ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| W0-1 | Repo | P1 | 0 | infra | 4 | - | done | | | abc1234 |
| W1-1 | Approved | P1 | 1 | backend | 8 | W0-1 | plan-approved | | | |
| W1-2 | Open A | P1 | 1 | backend | 3 | W0-1 | open | | | |
| W1-3 | Open B | P2 | 1 | frontend | 3 | W0-1 | open | | | |
| W1-4 | Open DB | P1 | 1 | db | 3 | W0-1 | open | | | |
"""
USAGE = r'''
import sys, pathlib; print(pathlib.Path(sys.argv[1]).read_text())
'''
WORK = r'''
import sys, pathlib
pathlib.Path(sys.argv[1]).write_text(" ".join(sys.argv[2:]))
print("ok")
'''


def setup(repo, tmp_path, lead_usage, cloud_usage, idle_planning=True):
    py = Path(sys.executable).as_posix()
    (tmp_path / "usage.py").write_text(USAGE)
    (tmp_path / "work.py").write_text(WORK)
    (tmp_path / "lead.json").write_text(json.dumps(lead_usage))
    (tmp_path / "cloud.json").write_text(json.dumps(cloud_usage))
    t = lambda n: (tmp_path / n).as_posix()  # noqa: E731
    head = (repo / "orchestration.toml").read_text().split("[keeper]")[0]   # replace the template keeper + providers
    head += f'''
[keeper]
idle_planning = {"true" if idle_planning else "false"}
cloud_steady = 1
cloud_accelerate_max = 2

[[providers]]
name = "claude"
priority = 1
roles = ["coordinator", "plan", "review", "merge"]
round_command = ["{py}", "{t('work.py')}", "{t('round.out')}"]
usage_command = ["{py}", "{t('usage.py')}", "{t('lead.json')}"]
native_limit_threshold = 97

[[providers]]
name = "codex"
priority = 2
roles = ["build", "plan"]
build_command = ["{py}", "{t('work.py')}", "{{worktree}}/built.txt", "{{item}}"]
plan_command = ["{py}", "{t('work.py')}", "{{worktree}}/plan.txt", "{{item}}"]
max_parallel = 2

[[providers]]
name = "cloud"
kind = "cloud"
priority = 3
roles = ["plan"]
plan_command = ["{py}", "{t('work.py')}", "{t('cloud.out')}", "{{todo}}"]
usage_command = ["{py}", "{t('usage.py')}", "{t('cloud.json')}"]
max_parallel = 3
'''
    (repo / "orchestration.toml").write_text(head)
    (repo / "docs/coordination/PROGRESS.md").write_text(BOARD)
    (repo / "docs/coordination/ledgers/W1-1").mkdir(parents=True)
    (repo / "docs/coordination/ledgers/W1-1/build-brief.md").write_text("build it")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "setup")
    return load(repo / "orchestration.toml")


def wait_all(cfg):
    for m in supervisor.load_markers(cfg):
        for _ in range(100):
            if not supervisor._alive(int(m["pid"])):
                break
            time.sleep(0.05)


def test_lead_limited_builds_and_accelerates_cloud(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 99}, {"credit_left": 200})
    actions = "\n".join(keeper.run_once(cfg))
    assert "build lane started: W1-1" in actions               # approved plan -> build provider
    assert "idle planning: W1-2 on codex" in actions           # codex has a free slot and nothing else to build
    assert "cloud planner on cloud (accelerate): W1-3" in actions   # lead limited -> cloud takes what is left
    assert "W1-4" not in actions                               # db lane is never auto-planned


def test_lead_ok_no_round_steady_cloud_and_idle_planning(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 20}, {"credit_left": 200})
    (repo / "docs/coordination/ledgers/W1-1/build-brief.md").unlink()   # nothing approved to build
    sh(repo, "git", "commit", "-qam", "no brief")
    actions = "\n".join(keeper.run_once(cfg))
    assert "idle planning: W1-2 on codex" in actions
    assert actions.count("cloud planner on cloud (steady)") == 1       # steady = 1 while the queue is low
    assert "W1-4" not in actions


def test_credit_floor_blocks_cloud(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 99}, {"credit_left": 2}, idle_planning=False)
    actions = "\n".join(keeper.run_once(cfg))
    assert "below floor" in actions and "cloud planner" not in actions


def test_handback_when_lead_recovers(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 99}, {"credit_left": 200}, idle_planning=False)
    keeper.run_once(cfg)                                      # accelerate: 2 cloud sessions
    long_run = r'''import time; time.sleep(3)'''
    (tmp_path / "sleep.py").write_text(long_run)
    for m in supervisor.load_markers(cfg):                  # keep the cloud sessions "running"
        if m["kind"] == "cloud":
            proc = supervisor.run_logged([sys.executable, str(tmp_path / "sleep.py")], repo, {}, tmp_path / "x.log",
                                         None, detach=True)
            m["pid"] = proc.pid
            keeper._write_marker(Path(m["_file"]), m)
    (tmp_path / "lead.json").write_text(json.dumps({"five_hour_pct": 30}))
    (cfg.state_dir / "providers.json").unlink(missing_ok=True)
    actions = "\n".join(keeper.run_once(cfg))
    assert "HANDBACK written" in actions
    assert (repo / "docs/coordination/cloud-handback.txt").read_text().startswith("HANDBACK")
    assert "chore(keeper): cloud handback" in sh(repo, "git", "log", "-1", "--format=%s")


def test_restart_after_limit_capped_per_day(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 99}, {"credit_left": 0}, idle_planning=False)
    keeper.run_once(cfg)
    wait_all(cfg)
    m = next(m for m in supervisor.load_markers(cfg) if m.get("item") == "W1-1")
    Path(m["log"]).write_text("working\nusage limit reached, try again in 1h\n")
    for n in range(1, 5):
        actions = "\n".join(keeper.restart_stopped(cfg, keeper.ProviderState(cfg), "2026-09-24"))
        wait_all(cfg)
        Path(m["log"]).write_text("usage limit reached, try again in 1h\n")
        assert ("restarted" in actions) == (n <= 3)


def test_gap_lists_foreign_plans_until_reconciled(repo, tmp_path):
    cfg = setup(repo, tmp_path, {"five_hour_pct": 10}, {"credit_left": 0}, idle_planning=False)
    led = repo / "docs/coordination/ledgers/W1-2"
    led.mkdir(parents=True)
    (led / "plan.md").write_text("# Plan\n**Authored-by:** codex\n")
    items, reviewers = knowledge_gap(cfg)
    assert [i["item"] for i in items] == ["W1-2"] and reviewers == 1
    assert items[0]["needs"] == ["reconcile-review.md", "gap-summary.md", "plan.claude.md", "reconcile.md"]
    for n in items[0]["needs"]:
        (led / n).write_text("x")
    assert knowledge_gap(cfg) == ([], 0)
