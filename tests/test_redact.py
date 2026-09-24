"""The scanner must find what it is meant to find (a check that cannot go red is not a check).

All values below are FAKE and assembled at runtime, so this file itself contains nothing that
secret scanners (GitHub push protection, the kit's own pre-commit hook) would flag:
- the IP is from TEST-NET-3, a documentation-only range (RFC 5737)
- .test is a reserved top-level domain (RFC 2606)
- the key is the provider prefix plus filler, never a real credential
"""
from orchestrator import redact

FAKE_IP = ".".join(["203", "0", "113", "9"])
FAKE_EMAIL = "jane.doe" + "@" + "acme.test"
FAKE_KEY = "sk-" + "ant-" + "x" * 26


def test_control_and_clean_text():
    text = "def f():\n    return 1\ncontact: someone@example.com\nhost 127.0.0.1\n"
    assert redact.control(text)          # a planted fake secret is found
    assert redact.scan(text) == []       # allow-listed example values are not


def test_finds_and_redacts():
    text = f"server {FAKE_IP}\nuser {FAKE_EMAIL}\napi_key = {FAKE_KEY}\nclient Acme"
    names = {h[1] for h in redact.scan(text, ["Acme"])}
    assert {"ipv4", "email", "anthropic-key", "term:Acme"} <= names
    out = redact.redact(text, ["Acme"])
    assert redact.scan(out, ["Acme"]) == []
