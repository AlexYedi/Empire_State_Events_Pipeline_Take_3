#!/usr/bin/env python3
"""pii_normalize — the normalized-copy PII layer, shared (YED-384). PRIVACY-LAYER CODE: changes need a human read.

spine_client's EMAIL_RE / PHONE_RE are the raw layer and are imported, never copied (spine_client.py is a guard file
and is not edited here). This module adds what a renderer or a human would decode before reading a contact:
HTML entities, percent-encoding, NFKC compatibility forms, zero-width characters, Unicode dashes, `[at]` / `(dot)` /
`x at y dot z` spellings and spaced-out `a @ b . c`. It also flags bare 10+ digit runs outside URLs and ids.

Ported from PR #320's sweep_manifest.py normalizer (same decodings, same order) plus the whitespace collapse around
`@` / `.`. Self-contained: it depends on spine_client only, so sweep_manifest can import it instead of carrying a copy.

  has_pii(s)  -> bool               raw OR normalized copy matches
  redact(s)   -> (text, n)          the normalized copy with every match replaced by [redacted]
  python3 .claude/scripts/pii_normalize.py --selftest
"""
from __future__ import annotations
import html, os, re, sys, unicodedata, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spine_client import EMAIL_RE, PHONE_RE  # noqa: E402  (the raw layer, one source)

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­᠎"), None)
DASHES = re.compile(r"[‐‑‒–—―−﹘﹣－]")
AT_FORM = re.compile(r"\s*[\[\(\{]\s*at\s*[\]\)\}]\s*", re.I)
DOT_FORM = re.compile(r"\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*", re.I)
WORD_FORM = re.compile(r"\b([a-z0-9._%+-]+)\s+at\s+([a-z0-9-]+)\s+dot\s+([a-z]{2,})\b", re.I)
SPACED_AT = re.compile(r"\s*@\s*")
SPACED_DOT = re.compile(r"(?<=\w)\s+\.\s*(?=\w)")      # 'fakeco . test' -> 'fakeco.test'; 'end. Next' is left alone
LOOSE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
BARE_DIGITS = re.compile(r"(?<!\d)\d{10,}(?!\d)")
# Spans where a long digit run is an identifier, not a phone: URLs, uuids, Notion's undashed 32-hex ids.
PROTECTED = re.compile(r"https?://[^\s<>\]\)]+|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
                       r"|\b[0-9a-f]{32}\b", re.I)


def normalize(s: str) -> str:
    """The copy the second layer reads: every decoding a renderer or a human would apply."""
    t = urllib.parse.unquote(html.unescape(s or ""))
    t = unicodedata.normalize("NFKC", t).translate(ZERO_WIDTH)
    t = DASHES.sub("-", t)
    t = WORD_FORM.sub(r"\1@\2.\3", DOT_FORM.sub(".", AT_FORM.sub("@", t)))
    return SPACED_DOT.sub(".", SPACED_AT.sub("@", t))


def _bare_digit_spans(t: str) -> list[tuple[int, int]]:
    prot = [m.span() for m in PROTECTED.finditer(t)]
    return [m.span() for m in BARE_DIGITS.finditer(t) if not any(a <= m.start() < b for a, b in prot)]


def has_pii(s: str) -> bool:
    n = normalize(s)
    return bool(EMAIL_RE.search(s or "") or PHONE_RE.search(s or "") or LOOSE_EMAIL.search(n)
                or EMAIL_RE.search(n) or PHONE_RE.search(n) or _bare_digit_spans(n))


def redact(s: str) -> tuple[str, int]:
    """Redact on the normalized copy (so a split or obfuscated contact cannot survive), then re-check it."""
    t, hits = normalize(s), 0
    for rx in (LOOSE_EMAIL, EMAIL_RE, PHONE_RE):
        t, k = rx.subn("[redacted]", t)
        hits += k
    for a, b in reversed(_bare_digit_spans(t)):
        t, hits = t[:a] + "[redacted]" + t[b:], hits + 1
    return t, hits


def selftest() -> bool:
    fails = []

    def ok(name, cond):
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)
    for s in ("jane@fakeco.test", "jane [at] fakeco [dot] test", "JANE AT FAKECO DOT TEST", "jane&#64;fakeco.test",
              "jane%40fakeco.test", "ja​ne@fake​co.test", "jane @ fakeco . test", "ｊane@fakeco.test",
              "212-555-0100", "212–555–0100", "212‑555‑0100", "2125550100", "+44 20 7946 0958"):
        ok(f"has_pii {s!r}", has_pii(s))
        ok(f"redact {s!r} leaves nothing", not has_pii(redact(s)[0]) and redact(s)[1] >= 1)
    for s in ("raised $5M in 2026, 3x growth", "https://fakeco.test/p/12345678901", "see aaaaaaaa000000000000000000000001",
              "Q3 2026: 1,200,000 users", "end. Next sentence", "meet at noon"):
        ok(f"no pii {s!r}", not has_pii(s))
    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s)")
    return not fails


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)
