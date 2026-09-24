"""Usage readers against pinned sample records.

The sample shapes follow the formats named in usage_readers.VERIFIED_WITH. When a tool changes its
format, the reader must report "unreadable" (and the provider starts no new work) - never a guess.
"""
import json
import os
import sys
from datetime import datetime, timedelta, UTC

from orchestrator import usage_readers as ur
from orchestrator.config import Provider
from orchestrator.providers import over_threshold, usage

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
LATER = int((NOW + timedelta(hours=2)).timestamp())
EARLIER = int((NOW - timedelta(minutes=5)).timestamp())


def statusline(five=42.0, week=10.0, week_reset=LATER):
    return json.dumps({"model": {"display_name": "any"}, "rate_limits": {
        "five_hour": {"used_percentage": five, "resets_at": LATER},
        "seven_day": {"used_percentage": week, "resets_at": week_reset}}})


def test_claude_statusline_capture_then_read(tmp_path):
    line = ur.capture_claude(statusline(week_reset=EARLIER), tmp_path, NOW)
    assert line == "5h 42% · week 10%"
    r = ur.read_claude(tmp_path, now=NOW + timedelta(minutes=3))
    assert r["status"] == "ok" and r["source"] == "statusline" and r["age_minutes"] == 3
    assert r["five_hour_pct"] == 42.0
    assert r["weekly_pct"] == 0.0                       # its window reset after the reading


def test_claude_no_subscription_writes_nothing(tmp_path):
    assert ur.capture_claude(json.dumps({"model": {}}), tmp_path, NOW) == ""
    assert ur.read_claude(tmp_path, now=NOW)["status"] == "no-data"


def test_claude_stream_json_event_newer_than_capture_wins(tmp_path):
    ur.capture_claude(statusline(), tmp_path, NOW - timedelta(hours=1))
    log = tmp_path / "rounds" / "r1.log"
    log.parent.mkdir()
    ev = {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed_warning", "rateLimitType": "five_hour",
          "resetsAt": LATER, "unifiedWindows": {"five_hour": {"utilization": 0.91, "resetsAt": LATER},
                                                "seven_day": {"utilization": 0.3, "resetsAt": LATER}}}}
    log.write_text("plain text line\n" + json.dumps(ev) + "\n")
    os.utime(log, (NOW.timestamp(), NOW.timestamp()))
    r = ur.read_claude(tmp_path, [log.parent], NOW)
    assert r["source"] == "stream-json" and r["five_hour_pct"] == 91.0 and r["weekly_pct"] == 30.0


def test_claude_rejected_event_means_full(tmp_path):
    log = tmp_path / "r.log"
    log.write_text(json.dumps({"type": "rate_limit_event", "rate_limit_info": {
        "status": "rejected", "rateLimitType": "seven_day", "resetsAt": LATER}}) + "\n")
    assert ur.read_claude(tmp_path / "none", [log], NOW)["weekly_pct"] == 100.0


def test_codex_session_record(tmp_path):
    d = tmp_path / "sessions" / "2026" / "09"
    d.mkdir(parents=True)
    rec = {"timestamp": "2026-09-24T11:50:00Z", "type": "event_msg", "payload": {"type": "token_count", "rate_limits": {
        "primary": {"used_percent": 12.0, "window_minutes": 300, "resets_in_seconds": 3600},
        "secondary": {"used_percent": 78.0, "window_minutes": 10080, "resets_at": LATER}}}}
    (d / "rollout-1.jsonl").write_text('{"payload": {"rate_limits": null}}\n' + json.dumps(rec) + "\n")
    r = ur.read_codex(tmp_path, NOW)
    assert r["status"] == "ok" and r["five_hour_pct"] == 12.0 and r["weekly_pct"] == 78.0 and r["age_minutes"] == 10
    assert r["five_hour_resets_at"] == "2026-09-24T12:50:00+00:00"


def test_codex_api_key_login_is_no_data_not_a_block(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    (d / "rollout-1.jsonl").write_text('{"payload": {"rate_limits": null}}\n')
    assert ur.read_codex(tmp_path, NOW)["status"] == "no-data"


def test_format_change_goes_red_and_fails_closed(tmp_path):
    # Claude renamed a field
    changed = statusline().replace("used_percentage", "percent_used")
    assert ur.capture_claude(changed, tmp_path, NOW) == "usage: unreadable"
    (tmp_path / "claude.json").write_text(json.dumps({"captured_at": NOW.isoformat(),
                                                      "rate_limits": json.loads(changed)["rate_limits"]}))
    assert ur.read_claude(tmp_path, now=NOW)["status"] == "unreadable"
    # Codex renamed a field
    d = tmp_path / "codex" / "sessions"
    d.mkdir(parents=True)
    (d / "rollout-1.jsonl").write_text(json.dumps({"rate_limits": {"primary": {"pct": 5}}}) + "\n")
    assert ur.read_codex(tmp_path / "codex", NOW)["status"] == "unreadable"


def test_provider_starts_no_new_work_when_meter_is_unreadable(tmp_path):
    garbage = [sys.executable, "-c", "print('not json')"]
    closed = Provider(name="a", priority=1, roles=["build"], usage_command=garbage)
    assert usage(closed, tmp_path)["status"] == "unreadable"
    assert "no new work" in over_threshold(closed, usage(closed, tmp_path))
    opened = Provider(name="b", priority=1, roles=["build"], usage_command=garbage, usage_fail_closed=False)
    assert over_threshold(opened, usage(opened, tmp_path)) == ""
    ok = Provider(name="c", priority=1, roles=["build"],
                  usage_command=[sys.executable, "-c", "print('{\"status\": \"no-data\"}')"])
    assert over_threshold(ok, usage(ok, tmp_path)) == ""      # nothing recorded yet is not a block
