from orchestrator import redact


def test_control_and_scan():
    text = "def f():\n    return 1\ncontact: someone@example.com\nhost 127.0.0.1\n"
    assert redact.control(text)
    assert redact.scan(text) == []


def test_finds_and_redacts():
    text = "server 203.0.113.9\nuser jane.doe@acme-corp.de\napi_key = sk-ant-abcdefghijklmnopqrstuvwxyz\nclient Acme"
    names = {h[1] for h in redact.scan(text, ["Acme"])}
    assert {"ipv4", "email", "anthropic-key", "term:Acme"} <= names
    out = redact.redact(text, ["Acme"])
    assert redact.scan(out, ["Acme"]) == []
