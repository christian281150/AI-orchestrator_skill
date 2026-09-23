from orchestrator.skills import inventory, report


def test_inventory_and_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    root = tmp_path / "repo"
    sk = root / ".claude/skills/tdd"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text("---\nname: tdd\ndescription: |\n  Test first.\n---\n")
    cx = root / ".agents/skills/tdd"
    cx.mkdir(parents=True)
    (cx / "SKILL.md").write_text("---\nname: tdd\ndescription: Test first.\n---\n")
    ag = root / ".claude/agents"
    ag.mkdir(parents=True)
    (ag / "implementer.md").write_text("---\nname: implementer\nskills: [tdd, project-db]\n---\n")
    inv = inventory(root)
    assert {(i["name"], i["engine"]) for i in inv} == {("tdd", "claude"), ("tdd", "codex/agents")}
    assert inv[0]["description"] == "Test first."
    lines, missing = report(root)
    text = "\n".join(lines)
    assert missing == 1 and "MISSING project-db" in text and "ok      tdd" in text
