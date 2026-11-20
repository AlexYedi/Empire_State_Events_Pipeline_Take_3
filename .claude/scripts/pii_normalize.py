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
# No `x at domain.tld` rule (removed 2026-11-20): a shadow scan of 11,839 live rows found 17 hits, all prose
# ("Lead at You.com", "CTO at Arlene.io", "Blogs at miketoscano.com"). A company named for its domain reads
# the same as a mailbox here, so this is an accepted gap; `x at y dot z` (WORD_FORM) stays.
# Unicode dash punctuation (category Pd, generated) plus U+2212 MINUS, folded to '-' in the full copy only:
# PHONE_RE already takes them as separators, and notion_export's private-title check reads 'Off-the-record'.
DASHES = {c: '-' for c in range(0x110000) if unicodedata.category(chr(c)) == 'Pd' or c == 0x2212}
SPACED_AT = re.compile(r"\s{0,3}@\s{0,3}")
SPACED_DOT = re.compile(r"(?<=\w)\s{1,3}\.\s{0,3}(?=\w)")              # 'fakeco . test' -> 'fakeco.test'
# YED-468 (gaps G1-G4 of docs/evidence/yed-299-mutation-2026-11-20.md). Python-only shape folds; the DB CHECK keeps
# them as a documented out-of-contract gap. Each fold only rewrites the copy so EMAIL_RE / PHONE_RE / the bare-digit
# rule can see a contact that its spacing or a glued token hid; none of them is a detector on its own.
# G1: an extension glued to the last digit group ('0100x12', '0958ext.12') is dropped, and a label glued to the
# first digit ('Tel+44 ...', 'Mob07700 ...') gets a space, so each alternative's end / start look-around holds.
# `10x growth` / `x10` are untouched (no digit on both sides); `1920x1080` folds to `1920 `, which is not a phone.
EXT_GLUED = re.compile(r"(?<=\d)(?:x|ext\.?|extn\.?)\s?\d{1,6}(?!\d)", re.I)
LABEL_GLUED = re.compile(r"\b(tel|telephone|phone|ph|mob|mobile|cell|fax|call|whatsapp)\.?(?=\+?\d)", re.I)
# G2: `+CC` then ONE block of 7-12 digits ('+65 60000000') is joined to E.164 compact ('+6560000000'), and
# PHONE_RE's own `\+\d{10,15}` alternative decides. So the floor is the shared one: 10+ digits in total, i.e. a
# 7-9 digit block after a 1-3 digit code. `+12 500 users` (3 digits), `+20 24 points` (two short groups), `+1 more`
# and `+30% YoY` never reach it; a decimal or thousands tail (`+12 3456789.5`, `+1 1234567,8`) or a % is excluded.
CC_ONE_BLOCK = re.compile(r"(?<![\w.+-])\+([1-9]\d{0,2})[\s.-](\d{7,12})(?![\w%]|[.,]\d)")
# G3: 10+ single digits separated by single spaces ('5 5 5 1 2 3 0 1 0 0', with or without a leading '+') are
# joined, so the bare-digit rule or E.164 compact sees them. A run must stop at a digit that is not followed by
# ' <digit>', so `1 2 3 ... 9 10` (a counted list ending on a two-digit number) never matches; `(?<!\d )` is the
# ReDoS guard (one start per run). Under 10 digits (`Q3 2026: 1 2 3`, `Room 5 5 5`) is never touched.
SPACED_DIGITS = re.compile(r"(?<![\w.,])(?<!\d )\+?\d(?: \d){9,}(?!\w| \d)")
# G4: whitespace AFTER the dot of a glued `local@domain. tld` ('dana@example. com'). It runs before SPACED_AT and
# needs a non-delimiter directly before '@', so `@handle. Next sentence` / `Follow @handle. next` (a handle, not a
# mailbox) never fold; the TLD is all lower or all upper case, so `x@y. Next` stays prose. SPACED_DOT itself still
# needs whitespace BEFORE the dot: widening it would fold `Follow@handle.Next` (pinned by the selftest).
GLUED_EMAIL_DOT = re.compile(r"([^\s@<>()\[\]{}\x22\x27,;:/\\]@[\w-]+(?:\.[\w-]+)*)\.\s{1,3}([a-z]{2,24}|[A-Z]{2,24})(?![\w@])")
BARE_DIGITS = re.compile(r"(?<!\d)\d{10,}(?!\d)")
# Spans where a long digit run is an identifier, not a phone: URLs with or without a scheme, uuids, Notion's
# undashed 32-hex ids.
PROTECTED = re.compile(r"https?://[^\s<>\]\)]+|(?<![a-z0-9.-])(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s<>\]\)]*"
                       r"|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{32}\b", re.I)
_CURRENCY = "$€£¥₹"


def heuristics(s: str) -> str:
    """The full Python copy (Python-only): L3's steps plus general decoding and the obfuscation word forms."""
    t = canon(AT_GLYPH.sub("@", s or ""))                               # ⓐ before NFKC turns it into 'a'
    t = canon(urllib.parse.unquote(html.unescape(t)))                   # a decoded &#xFF20; needs NFKC again
    t = AT_SPELLING_RE.sub("@", t).translate(DASHES)
    t = DOT_FORM.sub(".", AT_FORM.sub("@", t))
    t = WORD_FORM.sub(r"\1@\2.\3", t)
    t = LABEL_GLUED.sub(r"\1 ", EXT_GLUED.sub(" ", t))                  # YED-468 G1
    t = CC_ONE_BLOCK.sub(r"+\1\2", t)                                    # YED-468 G2
    t = SPACED_DIGITS.sub(lambda m: m.group(0).replace(" ", ""), t)      # YED-468 G3
    t = GLUED_EMAIL_DOT.sub(r"\1.\2", t)                                 # YED-468 G4 (before SPACED_AT)
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
              "dana[@]example[.]com", "danaⓐexample.com", "dana&commat;example.com",
              # YED-299 mutation pass (docs/evidence/yed-299-mutation-2026-11-20.md): one per surviving mutant
              "dana<at>example.com", "dana at example dot io", "dana @example.com", "dana@example .com",
              "ref 5551230100999 now", "ring x.y/5551230100", "a..b.test/5551230100", "cost $   5551230100"):
        ok(f"has_pii {s!r}", has_pii(s))
        ok(f"redact {s!r} leaves nothing", not has_pii(redact(s)[0]) and redact(s)[1] >= 1)
    for s in ("raised $5M in 2026, 3x growth", "https://fakeco.test/p/12345678901", "see aaaaaaaa000000000000000000000001",
              "Q3 2026: 1,200,000 users", "end. Next sentence", "meet at noon", "the team at openai.com",
              "ISBN 9780134685991", "linkedin.com/in/x-1234567890", "Pets dot com", "x.com/a/status/1856212345678901234",
              # YED-299: a checksum whose odd-digit sum is not 0 mod 10, a hex id opening on 10 digits, the 2-space
              # currency window, a 9-digit run, a query-string URL, a 2-letter TLD path, a dashed uuid's 12-digit tail
              "ISBN 9780306406157", "notion id 1234567890abcdef1234567890abcdef", "cost $  5551230100",
              "order 123456789 shipped", "see https://fakeco.test?ref=12345678901", "fakeco.io/p/12345678901",
              "ref 550e8400-e29b-41d4-a716-446655440000"):
        ok(f"no pii {s!r}", not has_pii(s))
    # YED-468: gaps G1-G4 closed in the full copy (Python-only; the shared PHONE_RE / EMAIL_RE are unchanged)
    for s in ("call 555-123-0100x12", "+44 20 7946 0958x12", "call 555-123-0100ext12", "call 555-123-0100ext.12",
              "+44 20 7946 0958EXT 12", "Tel+44 20 7946 0958", "Tel.+44 20 7946 0958", "Mob07700 900123",
              "Phone555-123-0100", "+65 60000000", "+33 639981234", "+65.60000000", "5 5 5 1 2 3 0 1 0 0",
              "+4 4 2 0 7 9 4 6 0 9 5 8", "dana@example. com", "DANA@EXAMPLE. COM", "dana@mail.example.  co."):
        ok(f"has_pii {s!r} (YED-468)", has_pii(s))
        ok(f"redact {s!r} leaves nothing (YED-468)", not has_pii(redact(s)[0]) and redact(s)[1] >= 1)
    for s in ("Q3 2026: 1 2 3", "scores 1 2 3 4 5 6 7 8 9", "1 2 3 4 5 6 7 8 9 10", "Room 5 5 5", "version 2. 0",
              "Series A at 3x. com-like", "Lead at You.com", "2026-11-20T10:00:00Z", "at 10:00:00 sharp", "+1 more",
              "+30% YoY", "$5M at 3x", "x10", "10x growth", "1920x1080 render", "email us at the booth. Come by",
              "@handle. Next sentence", "Follow @handle. next sentence", "Follow@handle. Next", "+20 24 points",
              "+12 500 users", "+1 2345678", "+1 1,000,000 users", "+10 1234567% lift", "Phone 15 launch",
              "mobile 5G", "ISBN 978-0-306-40615-7"):
        ok(f"no pii {s!r} (YED-468)", not has_pii(s))
    # YED-468 boundaries (mutation pass over the new folds): 1-digit extension, 1-digit / 3-digit country code with a
    # 9 / 7-digit block (the 10-digit floor exactly), a 2-letter TLD in either case; and, allowed, a % tail, a run
    # that starts mid-token, a run whose first digit follows another digit group
    for s in ("call 555-123-0100x1", "+7 495000000", "+354 1234567", "dana@example. io", "DANA@EXAMPLE. IO"):
        ok(f"has_pii {s!r} (YED-468 bound)", has_pii(s))
    for s in ("+12 34567890% lift", "cells A1 2 3 4 5 6 7 8 9 0", "rank 12 3 4 5 6 7 8 9 0 1 2"):
        ok(f"no pii {s!r} (YED-468 bound)", not has_pii(s))
    ok("YED-468 G2: +CC + one block folds to E.164 compact, and PHONE_RE's 10-digit floor decides",
       "+6560000000" in heuristics("+65 60000000") and not PHONE_RE.search(heuristics("+1 2345678")))
    ok("YED-468 G4: SPACED_DOT still needs whitespace BEFORE the dot (a handle is not a mailbox)",
       heuristics("Follow @handle. Next") == "Follow@handle. Next")
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
