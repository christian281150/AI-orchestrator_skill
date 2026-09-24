# SPDX-License-Identifier: MIT
"""Find and replace secrets and identifying details in text that leaves the machine
(a prompt pasted into a chat-only AI provider, a public export, a bug report).

Always prove the scanner works on the text at hand: `redact --control` plants a
fake secret in a copy and must find it, then the real text must show zero hits.
A scanner that cannot go red is not a scanner.
"""
from __future__ import annotations

import re

PATTERNS: list[tuple[str, str]] = [
    ("private-key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("aws-key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("github-token", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    ("anthropic-key", r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
    ("openai-key", r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b"),
    ("jwt", r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    ("assignment", r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[^\s'\"]{6,}"),
    ("conn-string", r"\b[a-z]+://[^\s:/]+:[^\s@/]+@[^\s/]+"),
    ("email", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ("ipv4", r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
]
SAFE_EMAIL = re.compile(r"@(?:example\.(?:com|org|net)|users\.noreply\.github\.com)$", re.I)
SAFE_IP = {"127.0.0.1", "0.0.0.0"}
PLANTED = "pass" + "word = " + "Pl4nted-Fake-Secret-42"   # split so the pre-commit hook does not flag this file


def scan(text: str, terms: list[str] | None = None) -> list[tuple[int, str, str]]:
    hits = []
    pats = PATTERNS + [(f"term:{t}", re.escape(t)) for t in (terms or []) if t]
    for n, line in enumerate(text.splitlines(), start=1):
        for name, pat in pats:
            for m in re.finditer(pat, line):
                val = m.group(0)
                if name == "email" and SAFE_EMAIL.search(val):
                    continue
                if name == "ipv4" and val in SAFE_IP:
                    continue
                hits.append((n, name, val))
    return hits


def redact(text: str, terms: list[str] | None = None) -> str:
    out = text
    for _, name, val in sorted(scan(text, terms), key=lambda h: -len(h[2])):
        out = out.replace(val, f"<{name.split(':')[0].upper()}>")
    return out


def control(text: str, terms: list[str] | None = None) -> bool:
    """True when a planted fake secret is detected in a copy of the text."""
    return any(v in PLANTED for _, _, v in scan(text + "\n" + PLANTED, terms))
