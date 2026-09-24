from pathlib import Path

from orchestrator import profile


def write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def test_template_is_valid_and_answers_nothing(tmp_path):
    ok, msg = profile.init(home=tmp_path)
    assert ok and (tmp_path / ".ai-orchestrator/profile.toml").exists()
    prof, used = profile.load(home=tmp_path)
    assert used and profile.check(prof) == [] and profile.answered(prof) == {}
    assert not profile.init(home=tmp_path)[0]                 # never overwrites


def test_project_overrides_home_but_empty_never_overrides(tmp_path):
    write(tmp_path / ".ai-orchestrator/profile.toml", '[owner]\nvocabulary = "plain"\n[defaults]\nadoption_level = 2\n'
          '[tools]\nlead = "tool-a"\nbuild = ["tool-b"]\n')
    repo = tmp_path / "repo"
    write(repo / ".ai-orchestrator.toml", '[defaults]\nadoption_level = 4\n[tools]\nlead = ""\n')
    prof, used = profile.load(repo, home=tmp_path)
    assert len(used) == 2
    assert prof["defaults"]["adoption_level"] == 4           # project wins
    assert prof["tools"]["lead"] == "tool-a"                  # empty project value does not erase the home value
    ans = profile.answered(prof)
    assert ans["1.3"] == "plain" and ans["2.4"] == "4" and ans["3.2"] == "tool-a" and ans["3.3"] == "tool-b"
    assert list(ans) == sorted(ans, key=lambda k: (int(k.split(".")[0].rstrip("bc")), k))


def test_check_goes_red(tmp_path):
    write(tmp_path / ".ai-orchestrator/profile.toml",
          '[defaults]\nadoption_level = 7\n[limits]\nmemory_no_new_start_pct = 95\nmemory_refuse_pct = 90\n'
          '[owner]\napi_' + 'token = "x"\n')
    probs = "\n".join(profile.check(profile.load(home=tmp_path)[0]))
    assert "adoption_level" in probs and "lower than memory_refuse_pct" in probs and "looks like a secret" in probs
