from orchestrator import doctor


def fake_which(installed):
    return lambda name: f"/bin/{name}" if name in installed else None


def fake_runner(cmd):
    if cmd[:2] == ["git", "--version"]:
        return 0, "git version 2.45.0"
    if cmd[:3] == ["git", "config", "--global"]:
        return 0, "Owner" if cmd[3] == "user.name" else "owner@example.com"
    return 0, f"{cmd[0]} 1.0.0"


def test_ready_machine_is_green(tmp_path):
    fails, lines = doctor.run(["tool-a"], tmp_path / "app", home=tmp_path,
                              which=fake_which({"git", "tool-a", "python"}), runner=fake_runner, py_version=(3, 12))
    assert fails == 0, lines
    assert any("AI tool 'tool-a' runs" in ln for ln in lines)


def test_goes_red_with_a_fix_for_each_problem(tmp_path):
    synced = tmp_path / "OneDrive" / "my app"
    fails, lines = doctor.run(["tool-a"], synced, home=tmp_path,
                              which=fake_which({"python"}), runner=fake_runner, py_version=(3, 9))
    text = "\n".join(lines)
    assert fails == 3                                    # old python, no git, tool missing
    assert "[FAIL] Python 3.9" in text and "[FAIL] Git not found" in text and "'tool-a' not found" in text
    assert "cloud-synced" in text and "contains spaces" in text
    assert text.count("Fix:") >= 5                       # every problem says what to do


def test_uses_profile_tools_when_none_named(tmp_path):
    (tmp_path / ".ai-orchestrator").mkdir()
    (tmp_path / ".ai-orchestrator" / "profile.toml").write_text('[tools]\nlead = "tool-a"\nbuild = ["tool-b"]\n')
    fails, lines = doctor.run(None, None, home=tmp_path, which=fake_which({"git", "tool-a"}),
                              runner=fake_runner, py_version=(3, 12))
    assert fails == 1 and any("'tool-b' not found" in ln for ln in lines)
