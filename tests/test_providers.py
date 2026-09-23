import json
from datetime import datetime

from orchestrator.config import Provider
from orchestrator.providers import detect_limit, parse_reset, codex_used_percent

P = Provider(name="x", priority=1, roles=["coordinator"])
NOW = datetime(2026, 9, 23, 22, 0)


def test_false_alarm_quoted_text_is_ignored_when_verdict_present():
    log = "reading board: 'usage limit reached, try again at 21:47'\n" + "work\n" * 5 + "ROUND RESULT: ok, merged 2"
    assert not detect_limit(P, 0, log).limited


def test_false_alarm_outside_tail_is_ignored():
    log = "usage limit reached\n" + "line\n" * 100
    assert not detect_limit(P, 1, log).limited


def test_real_limit_in_tail():
    log = "work\n" * 10 + "Claude usage limit reached. Your limit will reset at 3pm"
    v = detect_limit(P, 1, log, NOW)
    assert v.limited and v.reset_at == datetime(2026, 9, 24, 15, 0)


def test_parse_reset_forms():
    assert parse_reset("try again in 2h 5m", NOW) == datetime(2026, 9, 24, 0, 5)
    assert parse_reset("resets 23:30", NOW) == datetime(2026, 9, 23, 23, 30)
    assert parse_reset("resets Sep 27, 1pm", NOW) == datetime(2026, 9, 27, 13, 0)
    assert parse_reset("nothing here", NOW) is None


def test_codex_native_record(tmp_path, monkeypatch):
    d = tmp_path / "sessions" / "2026" / "09"
    d.mkdir(parents=True)
    rec = {"type": "event_msg", "payload": {"type": "token_count", "rate_limits": {
        "primary": {"used_percent": 12.0}, "secondary": {"used_percent": 78.0}}}}
    (d / "rollout-1.jsonl").write_text("{}\n" + json.dumps(rec) + "\n")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    assert codex_used_percent() == 78.0
    p = Provider(name="codex", priority=2, roles=["build"], native_limit="codex_rollout")
    v = detect_limit(p, 3, "usage limit reached, try again at 21:47")
    assert not v.limited and "decides" in v.reason        # the record wins over log text
    rec["payload"]["rate_limits"]["secondary"]["used_percent"] = 98.0
    (d / "rollout-1.jsonl").write_text(json.dumps(rec) + "\n")
    assert detect_limit(p, 0, "").limited
