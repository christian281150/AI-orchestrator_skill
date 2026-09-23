from orchestrator import preflight
from orchestrator.config import load
from orchestrator.init_kit import init, unfilled


def test_preflight_passes_what_it_should_and_goes_red(repo):
    cfg = load(repo / "orchestration.toml")
    fails, lines = preflight.run(cfg)
    text = "\n".join(lines)
    assert "[PASS] board PROGRESS.md" in text
    assert "[PASS] git hooks wired" in text
    assert "[PASS] session prompt exists" in text
    assert "[PASS] state dir is outside the repository" in text
    # control: break the board -> must go red
    cfg.board.write_text(cfg.board.read_text().replace("| open |", "| wip |", 1))
    _, lines2 = preflight.run(cfg)
    assert any(l.startswith("[FAIL] board") for l in lines2)


def test_preflight_catches_bom_and_missing_skill(repo):
    cfg = load(repo / "orchestration.toml")
    agent = repo / ".claude/agents/planner.md"
    agent.write_text(agent.read_text().replace("skills: []", "skills: [does-not-exist]"))
    (repo / ".claude/agents/bom.md").write_text("﻿---\nname: bom\n---\n", encoding="utf-8")
    _, lines = preflight.run(cfg)
    text = "\n".join(lines)
    assert "names skill 'does-not-exist' - not installed" in text
    assert "byte-order mark" in text


def test_init_never_overwrites_and_lists_placeholders(tmp_path):
    t = tmp_path / "x"
    t.mkdir()
    (t / "CLAUDE.md").write_text("mine")
    rep = init(t, {"PROJECT_NAME": "x"})
    assert "skipped (exists): CLAUDE.md" in rep and (t / "CLAUDE.md").read_text() == "mine"
    assert any("TODO" in h for h in unfilled(t))
