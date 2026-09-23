import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build-orchestration-setup" / "kit" / "tools"))


def sh(cwd, *args):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.fixture
def repo(tmp_path):
    """A git repo initialised with the kit, a valid config pointing state_dir into tmp."""
    from orchestrator.init_kit import init
    r = tmp_path / "app"
    r.mkdir()
    sh(r, "git", "init", "-q", "-b", "main")
    init(r, {"PROJECT_NAME": "demo", "AUTHOR_NAME": "Test Owner", "AUTHOR_EMAIL": "owner@example.com",
             "MAIN_BRANCH": "main"})
    cfg = (r / "orchestration.toml").read_text()
    cfg = cfg.replace('state_dir = "~/.agent-build/demo"', f'state_dir = "{(tmp_path / "state").as_posix()}"')
    cfg = cfg.replace('worktrees_dir = "../demo-wt"', f'worktrees_dir = "{(tmp_path / "wt").as_posix()}"')
    (r / "orchestration.toml").write_text(cfg)
    sh(r, "git", "add", "-A")
    sh(r, "git", "commit", "-q", "-m", "kit")
    return r
