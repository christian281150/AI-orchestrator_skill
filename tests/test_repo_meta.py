"""Repository hygiene: manifests valid, one version everywhere, skill follows the Agent Skills format."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "build-orchestration-setup"


def _version_init():
    return re.search(r'__version__ = "([^"]+)"', (SKILL / "scripts/orchestrator/__init__.py").read_text()).group(1)


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    return text.split("---\n", 2)[1]


def test_manifests_are_valid_json_and_versions_agree():
    v = _version_init()
    found = {}
    for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"):
        data = json.loads((ROOT / rel).read_text())
        assert data["name"] == "ai-orchestrator" and data["license"] == "MIT"
        found[rel] = data["version"]
    mk = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    found["marketplace"] = mk["plugins"][0]["version"]
    assert mk["plugins"][0]["source"] == "./"
    found["SKILL.md"] = re.search(r'version: "([^"]+)"', _frontmatter(SKILL / "SKILL.md")).group(1)
    found["CITATION.cff"] = re.search(r"^version: (\S+)", (ROOT / "CITATION.cff").read_text(), re.M).group(1)
    found["CHANGELOG"] = re.search(r"^## (\S+)", (ROOT / "CHANGELOG.md").read_text(), re.M).group(1)
    assert set(found.values()) == {v}, found


def test_skill_follows_agent_skills_format():
    fm = _frontmatter(SKILL / "SKILL.md")
    name = re.search(r"^name: (\S+)$", fm, re.M).group(1)
    desc = re.search(r"^description: (.+)$", fm, re.M).group(1)
    assert name == SKILL.name and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    assert 0 < len(desc) <= 1024
    assert re.search(r"^license: MIT$", fm, re.M)
    body = (SKILL / "SKILL.md").read_text()
    for ref in set(re.findall(r"references/(\d\d-[a-z0-9-]+\.md)", body)):
        assert (SKILL / "references" / ref).exists(), ref


def test_commands_have_descriptions_and_license_is_mit():
    for cmd in (ROOT / "commands").glob("*.md"):
        assert re.search(r"^description: .+", _frontmatter(cmd), re.M), cmd
    assert "MIT License" in (ROOT / "LICENSE").read_text()
    for py in (SKILL / "scripts").rglob("*.py"):
        assert any("SPDX-License-Identifier: MIT" in line for line in py.read_text().splitlines()[:2]), py


def test_example_project_is_valid():
    import sys
    sys.path.insert(0, str(SKILL / "scripts"))
    from orchestrator import board
    from orchestrator.config import load
    cfg = load(ROOT / "examples/lunch-poll/orchestration.toml")
    rows = board.parse(cfg.board)
    assert board.validate(rows, cfg.id_pattern) == []
    assert [r.id for r in board.ready(rows)] == ["W0-2"]


def test_bump_version_updates_every_field(tmp_path):
    import shutil
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from bump_version import bump
    copy = tmp_path / "repo"
    shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    bump("9.9.9", copy)
    text = "\n".join(p.read_text(encoding="utf-8") for p in [
        copy / ".claude-plugin/plugin.json", copy / ".claude-plugin/marketplace.json", copy / ".codex-plugin/plugin.json",
        copy / ".cursor-plugin/plugin.json", copy / "CITATION.cff", copy / "skills/build-orchestration-setup/SKILL.md",
        copy / "skills/build-orchestration-setup/scripts/orchestrator/__init__.py"])
    assert text.count("9.9.9") == 7 and _version_init() not in text
