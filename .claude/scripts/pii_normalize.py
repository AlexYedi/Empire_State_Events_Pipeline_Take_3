#!/usr/bin/env python3
"""pii_normalize — the normalized-copy PII layer, shared (YED-384, reworked YED-392). PRIVACY-LAYER CODE: changes
need a human read.

spine_client's EMAIL_RE / PHONE_RE are the raw layer and are imported, never copied. This module builds the copies
those patterns are re-run on. Two contracts, each tested on its own (fixtures/pii_probe_corpus.jsonl):

  L3 (shared with the DB, migration 0025 public.no_contact_pii_v2) — the CANONICAL form, nothing else:
    canon(s)    strip every Unicode Default_Ignorable_Code_Point, read the JSON escapes \\n \\t \\r as a space
                (jsonb::text, YED-318), NFKC, fold the UTS-46 dots (。 ． ｡) to '.'
    l3_form(s)  canon(s), then the CLOSED set of '@' spellings (AT_SPELLING_RE: &#64; &#x40; &commat; with or
                without ';', %40, [at] (at) {at} [@]) folded to '@'. EMAIL_RE / PHONE_RE run on this copy.
  L1/L2 (Python only) — everything L3 does, plus heuristics a SQL CHECK deliberately does not promise:
    heuristics(s)  general HTML-entity and percent decoding, ⓐ, <at>, [.] / [dot], `x at y dot z`,
                   `x at y.tld`, spaced `a @ b . c`
    bare 10+ digit runs (a separator-less phone) outside URLs, uuids, ISBN-13s and currency amounts

  normalize(s) -> str               the full Python copy (= heuristics(s)); kept for existing callers
  has_pii(s)  -> bool               raw, L3 form or full copy matches, or a bare digit run
  redact(s)   -> (text, n)          the full copy with every match replaced by [redacted]
  python3 .claude/scripts/pii_normalize.py --selftest
"""
from __future__ import annotations
import html, os, re, sys, unicodedata, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spine_client import EMAIL_RE, PHONE_RE  # noqa: E402  (the raw layer, one source)


# ---------------------------------------------------------------------------------------------------------------
# L3 contract: the canonical form (the DB carries the same steps; check_pii_regex_parity.py pins the literals)
# ---------------------------------------------------------------------------------------------------------------
def _derive_ignorables() -> frozenset[int]:
    """Default_Ignorable_Code_Point, generated from its Unicode definition rather than hand-listed.

    DerivedCoreProperties.txt defines it as
        Other_Default_Ignorable_Code_Point + Cf + Variation_Selector
        - White_Space - FFF9..FFFB - 13430..1343F - Prepended_Concatenation_Mark
    unicodedata exposes the general category but neither property, so this takes
      * every code point of category Cf (format controls: ZWSP/ZWJ, LRM/RLM, bidi embeddings and isolates,
        U+2061..2064 invisible operators, soft hyphen, BOM, Mongolian vowel separator, tags E0001/E0020..E007F);
      * Other_Default_Ignorable_Code_Point, which is not Cf: U+034F CGJ, the Hangul fillers U+115F/U+1160/U+3164/
        U+FFA0, the Khmer inherent vowels U+17B4/U+17B5, U+2065, U+FFF0..FFF8, and E0000..E0FFF (tags + reserved);
      * Variation_Selector: U+180B..180F, FE00..FE0F, E0100..E01EF;
    and does NOT subtract the exceptions. They are Cf format controls (Arabic number signs, interlinear
    annotation, Egyptian format controls) that never belong inside an email or a phone, so stripping them only
    removes hiding places. The result is a superset of DI on the running Python's Unicode version (selftest pins
    Unicode 16.0's own DI list), and no non-ignorable character's NFKC form contains one, so one strip before NFKC
    suffices.
    """
    named = ([0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x2065, 0x3164, 0xFFA0]
             + list(range(0x180B, 0x1810)) + list(range(0xFE00, 0xFE10)) + list(range(0xFFF0, 0xFFF9))
             + list(range(0xE0000, 0xE1000)))                          # E0000..E0FFF also covers E0100..E01EF
    return frozenset({c for c in range(0x110000) if unicodedata.category(chr(c)) == "Cf"} | set(named))


IGNORABLE = _derive_ignorables()
_IGN_TABLE = dict.fromkeys(IGNORABLE)


def _class(cps) -> str:
    """A regex character class over code points, as \\uXXXX / \\UXXXXXXXX ranges (Python re and Postgres ARE both
    read these escapes). The migration carries this class; the parity check verifies it covers IGNORABLE."""
    def esc(x: int) -> str:
        return f"\\u{x:04X}" if x <= 0xFFFF else f"\\U{x:08X}"
    cs, out = sorted(cps), []
    a = b = cs[0]
    for c in cs[1:] + [None]:
        if c is not None and c == b + 1:
            b = c
            continue
        out.append(esc(a) if a == b else f"{esc(a)}-{esc(b)}")
        if c is not None:
            a = b = c
    return "[" + "".join(out) + "]"


IGNORABLE_CLASS = _class(IGNORABLE)
UTS46_DOTS = {0x3002: ".", 0xFF0E: ".", 0xFF61: "."}                    # 。 ． ｡ (UTS-46 label separators)
# The closed set of '@' spellings L3 folds (flags: re.I here, 'gi' in SQL). Whitespace is bounded so a long
# whitespace run cannot backtrack quadratically. Byte-identical to at_re in migration 0025.
AT_SPELLING_RE = re.compile(r"\s{0,3}[\[\(\{]\s{0,3}(?:at|@)\s{0,3}[\]\)\}]\s{0,3}|&(?:#0*64|#x0*40|commat);?|%40", re.I)
# YED-318: jsonb::text writes a newline / tab / CR inside a value as the two characters `\n` `\t` `\r`, so
# `call\n555-123-0100` reached PHONE_RE with no separator. Those escapes read as a space. Byte-identical to
# esc_re in migration 0025.
JSON_WS_RE = re.compile(r"\\[ntr]")


def canon(s: str) -> str:
    """L3's canonical form: strip default-ignorables, JSON whitespace escapes -> ' ', NFKC, fold UTS-46 dots."""
    t = JSON_WS_RE.sub(" ", (s or "").translate(_IGN_TABLE))
    return unicodedata.normalize("NFKC", t).translate(UTS46_DOTS)


def l3_form(s: str) -> str:
    """Exactly the copy public.no_contact_pii_v2 matches EMAIL_RE / PHONE_RE against (besides the raw text)."""
    return AT_SPELLING_RE.sub("@", canon(s))


# ---------------------------------------------------------------------------------------------------------------
# L1/L2 only: heuristics. NOT in the DB contract (a CHECK that guessed at prose would block real rows).
# ---------------------------------------------------------------------------------------------------------------
AT_GLYPH = re.compile(r"[\u24D0\u24B6]")                               # ⓐ Ⓐ: NFKC folds them to a plain 'a'
AT_FORM = re.compile(r"\s{0,3}(?:[\[\(\{]\s{0,3}at\s{0,3}[\]\)\}]|<\s{0,3}(?:at|@)\s{0,3}>)\s{0,3}", re.I)
DOT_FORM = re.compile(r"\s{0,3}(?:[\[\(\{<]\s{0,3}(?:dot|\.)\s{0,3}[\]\)\}>])\s{0,3}", re.I)
# Every run-start below is a negative lookbehind over the run's own class, not \b: \b fires at every position
# inside `a.a.a…` / `1-1-1…`, and each start rescans the run (quadratic on a 100k-char value).
WORD_FORM = re.compile(r"(?<![a-z0-9._%+-])([a-z0-9._%+-]+)\s+at\s+([a-z0-9-]+)\s+dot\s+([a-z]{2,})\b", re.I)
# `dana at example.com`. Prose puts a domain after "at" too ("launched at techcrunch.com"), so the word before
# "at" must not be one of the common prose heads below, and a domain followed by a path is a link, not a mailbox.
WORD_AT = re.compile(r"(?<![a-z0-9._%+-])([a-z0-9][a-z0-9._%+-]*)\s+at\s+((?:[a-z0-9-]+\.)+[a-z]{2,})\b(?![/\w]|\.\w)", re.I)
_PROSE_HEADS = frozenset(
    "is are was were be been being am it this that these those there here who which we they you he she i me us "
    "him her them team teams staff people folks someone everyone anyone launched announced presented published "
    "posted shared spoke speaking speaks talk talks talked live lives available found work works worked working "
    "based located hosted held open opened booth demo demos read more look looking see seen visit visiting "
    "apply applied join joined online us engineers engineer role roles jobs job hiring".split())
# Unicode dash punctuation (category Pd, generated) plus U+2212 MINUS, folded to '-' in the full copy only:
# PHONE_RE already takes them as separators, and notion_export's private-title check reads 'Off-the-record'.
DASHES = {c: '-' for c in range(0x110000) if unicodedata.category(chr(c)) == 'Pd' or c == 0x2212}
SPACED_AT = re.compile(r"\s{0,3}@\s{0,3}")
SPACED_DOT = re.compile(r"(?<=\w)\s{1,3}\.\s{0,3}(?=\w)")              # 'fakeco . test' -> 'fakeco.test'
BARE_DIGITS = re.compile(r"(?<!\d)\d{10,}(?!\d)")
# Spans where a long digit run is an identifier, not a phone: URLs with or without a scheme, uuids, Notion's
# undashed 32-hex ids.
PROTECTED = re.compile(r"https?://[^\s<>\]\)]+|(?<![a-z0-9.-])(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s<>\]\)]*"
                       r"|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{32}\b", re.I)
_CURRENCY = "$€£¥₹"


def _word_at(m: re.Match) -> str:
    return m.group(0) if m.group(1).lower() in _PROSE_HEADS else f"{m.group(1)}@{m.group(2)}"


def heuristics(s: str) -> str:
    """The full Python copy (Python-only): L3's steps plus general decoding and the obfuscation word forms."""
    t = canon(AT_GLYPH.sub("@", s or ""))                               # ⓐ before NFKC turns it into 'a'
    t = canon(urllib.parse.unquote(html.unescape(t)))                   # a decoded &#xFF20; needs NFKC again
    t = AT_SPELLING_RE.sub("@", t).translate(DASHES)
    t = DOT_FORM.sub(".", AT_FORM.sub("@", t))
    t = WORD_AT.sub(_word_at, WORD_FORM.sub(r"\1@\2.\3", t))
    return SPACED_DOT.sub(".", SPACED_AT.sub("@", t))


def normalize(s: str) -> str:
    """The copy the Python second layer reads (unchanged public name; = heuristics)."""
    return heuristics(s)


def _isbn13(d: str) -> bool:
    return len(d) == 13 and d[:3] in ("978", "979") and sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d)) % 10 == 0


def _bare_digit_spans(t: str) -> list[tuple[int, int]]:
    """Bare 10+ digit runs (Python-only heuristic) outside URLs/ids, valid ISBN-13s and currency amounts."""
    runs = list(BARE_DIGITS.finditer(t))
    prot = [m.span() for m in PROTECTED.finditer(t)] if runs else []
    out = []
    for m in runs:
        if any(a <= m.start() < b for a, b in prot) or _isbn13(m.group(0)):
            continue
        if t[max(0, m.start() - 3):m.start()].rstrip()[-1:] in tuple(_CURRENCY):
            continue
        out.append(m.span())
    return out


def _forms(s: str) -> tuple[str, str, str]:
    return s or "", l3_form(s), normalize(s)


def has_pii(s: str) -> bool:
    raw, l3, n = _forms(s)
    return bool(any(EMAIL_RE.search(f) or PHONE_RE.search(f) for f in (raw, l3, n)) or _bare_digit_spans(n))


def redact(s: str) -> tuple[str, int]:
    """Redact on the full copy (so a split or obfuscated contact cannot survive), then re-check it."""
    t, hits = normalize(s), 0
    for rx in (EMAIL_RE, PHONE_RE):
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
              "jane%40fakeco.test", "ja\u200Bne@fake\u200Bco.test", "jane @ fakeco . test", "ｊane@fakeco.test",
              "212-555-0100", "212–555–0100", "212‑555‑0100", "2125550100", "+44 20 7946 0958",
              "dana@exa\u200Emple.com", "call 555\u200E-123-0100", "dana\u2063@example.com", "nguyễn@example.com",
              "dana at example.com", "dana[@]example[.]com", "danaⓐexample.com", "dana&commat;example.com"):
        ok(f"has_pii {s!r}", has_pii(s))
        ok(f"redact {s!r} leaves nothing", not has_pii(redact(s)[0]) and redact(s)[1] >= 1)
    for s in ("raised $5M in 2026, 3x growth", "https://fakeco.test/p/12345678901", "see aaaaaaaa000000000000000000000001",
              "Q3 2026: 1,200,000 users", "end. Next sentence", "meet at noon", "the team at openai.com",
              "ISBN 9780134685991", "linkedin.com/in/x-1234567890", "Pets dot com", "x.com/a/status/1856212345678901234"):
        ok(f"no pii {s!r}", not has_pii(s))
    ok("canon strips LRM, NFKC folds ＠, UTS-46 dot folds", canon("a\u200E＠b。com") == "a@b.com")
    ok("YED-318: jsonb escapes \\n \\t \\r read as whitespace in the L3 form",
       all(PHONE_RE.search(l3_form('{"note": "call' + e + '555-123-0100"}')) for e in ("\\n", "\\t", "\\r"))
       and not PHONE_RE.search('{"note": "call\\n555-123-0100"}'))
    ok("l3_form folds the closed @ set only", l3_form("a&#x40;b [at] c%40d&commat e") == "a@b@c@d@ e"
       and l3_form("a [dot] b") == "a [dot] b")
    di16 = [(0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180F),
            (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF),
            (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF)]
    ok("IGNORABLE covers Unicode 16.0 Default_Ignorable_Code_Point",
       all(c in IGNORABLE for a, b in di16 for c in range(a, b + 1)))
    ok("IGNORABLE_CLASS compiles and matches exactly IGNORABLE (sampled)",
       all(bool(re.fullmatch(IGNORABLE_CLASS, chr(c))) == (c in IGNORABLE)
           for c in list(IGNORABLE)[:200] + [0x41, 0x20, 0x3000, 0xE1000, 0x1F600]))
    print(f"\n{'OK' if not fails else 'FAILED'}: {len(fails)} failure(s)")
    return not fails


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    print(__doc__)
