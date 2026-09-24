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


RECORD = """| # | Question | Chosen | Not taken | Date |
|---|---|---|---|---|
| 1.3 | Owner vocabulary | not from an IT background - spell out abbreviations | technical | |
| 2.4 | Adoption level (1-4) | 3 - multi-provider (recommended) | 2, 4 | |
| 3.2 | Lead provider | tool-a (its CLI) | | |
| 3.3 | Build providers | tool-b, tool-c | | |
| 5.2 | Thinking-role models | the big one for planning, the small one for relays | | |
| 8.1 | Autonomy | decide and log | ask | |
| 8.3 | Git model | feature branches per lane | | |
"""


def test_learn_fills_only_empty_values_and_never_overwrites(tmp_path):
    record = write(tmp_path / "orchestration-config.md", RECORD)
    target = write(tmp_path / ".ai-orchestrator/profile.toml",
                   profile.TEMPLATE.read_text().replace('autonomy = ""  ', 'autonomy = "ask"'))
    before = target.read_text()
    plan = profile.learn(record, target)                     # dry run: shows, writes nothing
    assert target.read_text() == before
    assert any("adoption_level = 3" in x for x in plan["add"])
    assert any("autonomy" in x and 'yours "ask" kept' in x for x in plan["kept_yours"])
    assert any("thinking" in x for x in plan["not_learned"])  # free text is never guessed
    assert any("git_model" in x for x in plan["not_learned"])  # "feature branches" is not an allowed value

    profile.learn(record, target, write=True)
    prof = profile.load(home=tmp_path)[0]
    assert prof["defaults"]["adoption_level"] == 3 and prof["owner"]["vocabulary"] == "plain"
    assert prof["tools"]["lead"] == "tool-a" and prof["tools"]["build"] == ["tool-b", "tool-c"]
    assert prof["defaults"]["autonomy"] == "ask"             # the owner's own value survived
    assert profile.check(prof) == []
    assert "# 0 ask | 1 rituals" in target.read_text()        # comments kept


def test_learn_creates_the_profile_when_missing(tmp_path):
    record = write(tmp_path / "rec.md", RECORD)
    target = tmp_path / "home" / ".ai-orchestrator" / "profile.toml"
    profile.learn(record, target, write=True)
    assert target.exists() and "tool-a" in target.read_text()
