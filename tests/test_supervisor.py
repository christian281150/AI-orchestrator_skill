"""End-to-end supervisor runs with fake providers (no real AI CLI needed)."""
import json
import sys
import time
from pathlib import Path

from orchestrator import supervisor
from orchestrator.config import load
from conftest import sh

BOARD = """| ID | Item | Prio | Wave | Lane | Est h | Deps | Status | Owner | Next | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| W0-1 | Repo | P1 | 0 | infra | 4 | - | done | | | abc1234 |
| W1-1 | Core loop | P1 | 1 | backend | 8 | W0-1 | plan-approved | | | |
| W1-2 | No brief yet | P1 | 1 | backend | 3 | W0-1 | plan-approved | | | |
"""

FAKE_COORD = r'''
import sys, pathlib
prompt = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
counter = pathlib.Path(sys.argv[2]); n = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(n + 1))
mode = sys.argv[3]
if mode == "limit-first" and n == 0:
    print("working...\nClaude usage limit reached. Your limit will reset at 3pm"); sys.exit(1)
if mode == "fail":
    print("crashed"); sys.exit(1)
pathlib.Path(sys.argv[2] + f".prompt{n}").write_text(prompt, encoding="utf-8")
for line in prompt.splitlines():
    if line.strip().startswith("- W") and "built by" in line:
        print("GATED: " + line.split()[1] + " accepted tests green")
print("ROUND RESULT: ok, merged 0")
'''

FAKE_BUILDER = r'''
import sys, pathlib
wt = pathlib.Path(sys.argv[1]); (wt / "built.txt").write_text(pathlib.Path(sys.argv[2]).read_text())
print("built")
'''


def setup(repo, tmp_path, mode):
    (tmp_path / "coord.py").write_text(FAKE_COORD)
    (tmp_path / "builder.py").write_text(FAKE_BUILDER)
    cfg_text = (repo / "orchestration.toml").read_text()
    head = cfg_text.split("[[providers]]")[0]
    py = Path(sys.executable).as_posix()
    head += f'''
[[providers]]
name = "claude"
priority = 1
roles = ["coordinator", "plan", "review", "build", "merge"]
round_command = ["{py}", "{(tmp_path / 'coord.py').as_posix()}", "{{prompt_file}}", "{(tmp_path / 'count').as_posix()}", "{mode}"]

[[providers]]
name = "codex"
priority = 2
roles = ["build"]
build_command = ["{py}", "{(tmp_path / 'builder.py').as_posix()}", "{{worktree}}", "{{brief_file}}"]
max_parallel = 2
'''
    head = head.replace("push_after_round = true", "push_after_round = false").replace("pause_seconds = 30", "pause_seconds = 0")
    (repo / "orchestration.toml").write_text(head)
    (repo / "docs/coordination/PROGRESS.md").write_text(BOARD)
    led = repo / "docs/coordination/ledgers/W1-1"
    led.mkdir(parents=True)
    (led / "build-brief.md").write_text("build the core loop")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "setup")
    return load(repo / "orchestration.toml")


def test_ok_round(repo, tmp_path):
    cfg = setup(repo, tmp_path, "ok")
    assert supervisor.supervise(str(repo / "orchestration.toml"), max_passes=1, sleep=lambda s: None, reexec=False) == "max-passes"
    state = json.loads((cfg.state_dir / "supervisor-state.json").read_text())
    assert state["state"] == "between rounds" and state["last"] == "ok"


def test_limit_then_fallback_then_gate(repo, tmp_path):
    cfg = setup(repo, tmp_path, "limit-first")

    def fake_sleep(_s):
        # the fallback builder must finish, then the coordinator's limit "resets"
        for m in cfg.state_dir.joinpath("fallback").glob("*.json"):
            pid = json.loads(m.read_text())["pid"]
            for _ in range(100):
                if not supervisor._alive(pid):
                    break
                time.sleep(0.05)
        p = cfg.state_dir / "providers.json"
        p.write_text(json.dumps({}))

    supervisor.supervise(str(repo / "orchestration.toml"), max_passes=3, sleep=fake_sleep, reexec=False)
    log = (cfg.state_dir / "supervisor.log").read_text()
    assert "LIMITED" in log                                   # pass 1: limit detected from the log tail
    assert "fallback lane started: W1-1 on codex" in log      # pass 2: codex builds the approved plan
    assert "W1-2" not in log.split("fallback lane started")[1] if "fallback lane started" in log else True
    wt = cfg.worktrees_dir / "w1-1-codex"
    assert (wt / "built.txt").read_text() == "build the core loop"
    prompt = (tmp_path / "count.prompt1").read_text()
    assert "gate these fallback lanes" in prompt and "W1-1 on branch feat/backend-w1-1-codex" in prompt
    assert "gated fallback lanes: W1-1:accepted" in log       # pass 3: coordinator gated it
    assert (cfg.state_dir / "fallback/gated/W1-1.accepted.json").exists()
    assert not list(cfg.state_dir.joinpath("fallback").glob("*.json"))


def test_stop_file(repo, tmp_path):
    cfg = setup(repo, tmp_path, "ok")
    cfg.stop_file.write_text("stop")
    assert supervisor.supervise(str(repo / "orchestration.toml"), max_passes=5, sleep=lambda s: None, reexec=False) == "stopped"


def test_identical_failures_stop(repo, tmp_path):
    cfg = setup(repo, tmp_path, "fail")
    assert supervisor.supervise(str(repo / "orchestration.toml"), max_passes=10, sleep=lambda s: None, reexec=False) == "blocked"
    assert (cfg.state_dir / "BLOCKED.txt").exists()
    assert int((tmp_path / "count").read_text()) == 3


def test_fingerprint_changes_when_config_changes(repo):
    cfgp = repo / "orchestration.toml"
    a = supervisor.fingerprint(cfgp)
    time.sleep(0.01)
    cfgp.write_text(cfgp.read_text() + "\n# changed\n")
    import os
    os.utime(cfgp, (time.time() + 5, time.time() + 5))
    assert supervisor.fingerprint(cfgp) != a
