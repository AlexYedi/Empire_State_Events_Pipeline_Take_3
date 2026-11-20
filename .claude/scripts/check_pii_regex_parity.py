#!/usr/bin/env python3
"""PII regex parity: the Postgres backstop must carry spine's regexes verbatim.

The DB backstop proposal (docs/adr/proposals/pii-db-check.sql) promises to
mirror spine_client.py's EMAIL_RE / PHONE_RE — "same shapes, not a second
dialect" (pii-regex-set.md). Nothing enforced that: a literal that differed
from spine only in group order passed the first review unnoticed (YED-279
review follow-up). This check extracts both sets of literals and fails on any
difference, so drift fails CI instead of relying on a reviewer catching it.

PR #250 (A2 leading-1 phone prefix) merged as 63138ef, so both shapes are
compared byte-for-byte with no pending deltas.

YED-392 rework: a site may also carry allow_re (spine EMAIL_ALLOWLIST_RE), at_re (pii_normalize
AT_SPELLING_RE, the closed '@' spellings), esc_re (pii_normalize JSON_WS_RE, YED-318) and ign_re (the
default-ignorable class). The first three are
compared byte for byte; ign_re must COVER pii_normalize.IGNORABLE as derived on the running Python (the
pinned class was generated on a newer Unicode, so it may hold more, never less).

Stdlib + this directory. Run with --selftest to exercise the extraction and comparison logic against
embedded fixtures.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SPINE = os.path.join(REPO, ".claude", "scripts", "spine_client.py")
SQL = os.path.join(REPO, "docs", "adr", "proposals", "pii-db-check.sql")
# Every DB site that carries the CURRENT literals. 0025 (YED-392/324): public.no_contact_pii_v2(), which backs
# every free-text CHECK and the person trigger. 0022's no_contact_pii_v1() is VERSIONED (never replaced), so it
# keeps the pre-0025 shapes by design and is not a parity site; its sites also carry v2 CHECKs from 0025.
SQL_SITES = [SQL, os.path.join(REPO, "supabase", "migrations", "0025_pii_backstop_normalized.sql")]


def extract_spine(src: str) -> tuple[str, str]:
    """(EMAIL_RE, PHONE_RE) as concatenated from the re.compile literals."""
    email = re.search(r'EMAIL_RE = re\.compile\(r"([^"]+)"\)', src)
    phone_block = re.search(r"PHONE_RE = re\.compile\((.*?)\)\n", src, re.S)
    if not email or not phone_block:
        raise SystemExit("check_pii_regex_parity: could not find EMAIL_RE/PHONE_RE in spine_client.py — has the definition changed shape?")
    phone = "".join(re.findall(r'r"([^"]+)"', phone_block.group(1)))
    if not phone:
        raise SystemExit("check_pii_regex_parity: PHONE_RE compile block contains no raw-string literals")
    return email.group(1), phone


def extract_sql(src: str) -> tuple[str, str]:
    """(email_re, phone_re) from the $re$-dollar-quoted plpgsql literals."""
    email = re.search(r"^\s*email_re text := \$re\$(.+?)\$re\$;", src, re.M)
    phone = re.search(r"^\s*phone_re text := \$re\$(.+?)\$re\$;", src, re.M)
    if not email or not phone:
        raise SystemExit("check_pii_regex_parity: could not find $re$-quoted email_re/phone_re in pii-db-check.sql — has the file moved or changed shape?")
    return email.group(1), phone.group(1)


def extract_extra(spine_src: str, norm_src: str) -> tuple[str, str, str]:
    """(EMAIL_ALLOWLIST_RE, AT_SPELLING_RE, JSON_WS_RE) literals from spine_client.py / pii_normalize.py."""
    allow = re.search(r'EMAIL_ALLOWLIST_RE = re\.compile\(r"([^"]+)", re\.I\)', spine_src)
    at = re.search(r'AT_SPELLING_RE = re\.compile\(r"([^"]+)", re\.I\)', norm_src)
    esc = re.search(r'JSON_WS_RE = re\.compile\(r"([^"]+)"\)', norm_src)
    if not allow or not at or not esc:
        raise SystemExit("check_pii_regex_parity: could not find EMAIL_ALLOWLIST_RE / AT_SPELLING_RE — has the definition changed shape?")
    return allow.group(1), at.group(1), esc.group(1)


def class_codepoints(cls: str) -> set[int]:
    """Code points of a [..] class written only as \\uXXXX / \\UXXXXXXXX singletons and ranges."""
    esc = r"\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8}"
    body = cls[1:-1] if cls.startswith("[") and cls.endswith("]") else None
    toks = re.findall(rf"({esc})(?:-({esc}))?", body or "")
    if body is None or "".join(a + ("-" + b if b else "") for a, b in toks) != body:
        raise SystemExit("check_pii_regex_parity: ign_re is not a plain class of \\u / \\U escapes")
    out = set()
    for a, b in toks:
        lo = int(a[2:], 16)
        out.update(range(lo, int(b[2:], 16) + 1) if b else (lo,))
    return out


def lits(sql_src: str, name: str) -> list[str]:
    return re.findall(rf"^\s*{name} text := \$re\$(.+?)\$re\$;", sql_src, re.M)


def run(spine_src: str, sql_src: str, extra: tuple[str, str, str] | None = None, ignorable: set[int] | None = None) -> list[str]:
    """Return a list of drift descriptions; empty list means parity. `extra` = (allow, at, esc) literals and
    `ignorable` = the Python default-ignorable set; a site that carries allow_re / at_re / ign_re is checked
    against them (and fails loud when they were not supplied)."""
    spine_email, spine_phone = extract_spine(spine_src)
    extract_sql(sql_src)   # fails loud when a site has no literals at all
    # Every literal in the file, not only the first: a site may define more than one function (0025 does).
    drifts = []
    for sql_email in re.findall(r"^\s*email_re text := \$re\$(.+?)\$re\$;", sql_src, re.M):
        if sql_email != spine_email:
            drifts.append("EMAIL shape drifted:\n  spine: %s\n  sql:   %s" % (spine_email, sql_email))
    for sql_phone in re.findall(r"^\s*phone_re text := \$re\$(.+?)\$re\$;", sql_src, re.M):
        if sql_phone != spine_phone:
            drifts.append("PHONE shape drifted:\n  spine: %s\n  sql:   %s" % (spine_phone, sql_phone))
    for name, idx, label in (("allow_re", 0, "EMAIL_ALLOWLIST"), ("at_re", 1, "AT_SPELLING"), ("esc_re", 2, "JSON_WS")):
        for lit in lits(sql_src, name):
            if extra is None:
                drifts.append(f"{label}: site carries {name} but no Python literal was supplied")
            elif lit != extra[idx]:
                drifts.append("%s shape drifted:\n  python: %s\n  sql:    %s" % (label, extra[idx], lit))
    for lit in lits(sql_src, "ign_re"):
        missing = sorted((ignorable or set()) - class_codepoints(lit)) if ignorable is not None else None
        if missing is None:
            drifts.append("IGNORABLE: site carries ign_re but no Python set was supplied")
        elif missing:
            drifts.append("IGNORABLE class misses %d code point(s) pii_normalize strips, e.g. %s"
                          % (len(missing), ", ".join("U+%04X" % c for c in missing[:8])))
    return drifts


# ---------------------------------------------------------------------------
# Selftest: extraction and comparison logic against embedded fixtures.
# ---------------------------------------------------------------------------
def selftest() -> int:
    ok, n = 0, 0

    def ck(desc: str, cond: bool) -> None:
        nonlocal ok, n
        n += 1
        ok += cond
        print(("  ✓ " if cond else "  ✗ ") + desc)

    spine_src = (
        'EMAIL_RE = re.compile(r"(?<![\\w/])[A-Z]+(?![\\w])")\n'
        "PHONE_RE = re.compile(\n"
        '    r"(?<![\\w.+-])(?:1[\\s.-])?(?:\\+\\d{1,3}[\\s.-]?)?(?:\\(\\d{3}\\)|\\d{3})[\\s.-]\\d{3}[\\s.-]\\d{4}(?![\\w])"   # c1\n'
        '    r"|(?<![\\w.])\\+\\d{10,15}(?![\\w])"                                                          # c2\n'
        ")\n"
    )
    email_py, phone_py = extract_spine(spine_src)
    ck("spine email literal extracted", email_py == r"(?<![\w/])[A-Z]+(?![\w])")
    ck("spine phone literals concatenated", phone_py == r'(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])')

    sql_src = (
        '  email_re text := $re$(?<![\\w/])[A-Z]+(?![\\w])$re$;\n'
        '  phone_re text := $re$(?<![\\w.+-])(?:1[\\s.-])?(?:\\+\\d{1,3}[\\s.-]?)?(?:\\(\\d{3}\\)|\\d{3})[\\s.-]\\d{3}[\\s.-]\\d{4}(?![\\w])|(?<![\\w.])\\+\\d{10,15}(?![\\w])$re$;\n'
    )
    drifts = run(spine_src, sql_src)
    ck("identical shapes -> no drift", drifts == [])

    wrong_order = sql_src.replace(
        r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})",
        r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:1[\s.-])?(?:\(\d{3}\)|\d{3})",
    )
    drifts = run(spine_src, wrong_order)
    ck("prefix on the wrong side of +country -> drift", len(drifts) == 1 and drifts[0].startswith("PHONE"))

    no_prefix = sql_src.replace(
        r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})",
        r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})",
    )
    drifts = run(spine_src, no_prefix)
    ck("missing A2 prefix -> drift", len(drifts) == 1 and drifts[0].startswith("PHONE"))

    drifted_email = sql_src.replace(r"[A-Z]+", r"[A-Z]+?")
    drifts = run(spine_src, drifted_email)
    ck("email drift detected", len(drifts) == 1 and drifts[0].startswith("EMAIL"))

    # A site with two functions (0025): a drift in the SECOND literal must not hide behind a matching first.
    two_sites = sql_src + drifted_email
    drifts = run(spine_src, two_sites)
    ck("drift in a second email_re literal is detected", len(drifts) == 1 and drifts[0].startswith("EMAIL"))
    drifts = run(spine_src, sql_src + sql_src)
    ck("two matching literal pairs: parity", drifts == [])

    # YED-392 rework: allow_re / at_re byte parity, ign_re coverage.
    extra = ("^(?:noreply)@", r"%40", r"\\[ntr]")
    bs = chr(92)
    site = sql_src + "  allow_re text := $re$^(?:noreply)@$re$;\n  at_re text := $re$%40$re$;\n" \
        + "  esc_re text := $re$" + bs + bs + "[ntr]$re$;\n" \
        + "  ign_re text := $re$[" + bs + "u200B-" + bs + "u200F" + bs + "U000E0001]$re$;\n"
    ck("allow_re / at_re / ign_re in parity -> no drift", run(spine_src, site, extra, {0x200B, 0x200E, 0xE0001}) == [])
    d = run(spine_src, site, ("^(?:no-reply)@", r"%40", extra[2]), {0x200B})
    ck("allow_re drift detected", len(d) == 1 and d[0].startswith("EMAIL_ALLOWLIST"))
    d = run(spine_src, site, extra[:2] + (r"\\[nt]",), {0x200B})
    ck("esc_re drift detected (YED-318: \\r dropped)", len(d) == 1 and d[0].startswith("JSON_WS"))
    d = run(spine_src, site, extra, {0x200B, 0x2060})
    ck("ign_re missing a Python ignorable -> drift", len(d) == 1 and d[0].startswith("IGNORABLE") and "U+2060" in d[0])
    d = run(spine_src, site)
    ck("site with allow_re/at_re/esc_re/ign_re but no Python values -> fails loud", len(d) == 4)
    ck("ign_re with a stray literal character is rejected",
       _raises(lambda: class_codepoints("[" + bs + "u200Bx]")))

    print(f"\n{ok}/{n} passed")
    return 0 if ok == n else 1


def _raises(fn) -> bool:
    try:
        fn()
    except SystemExit:
        return True
    return False


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    with open(SPINE, encoding="utf-8") as f:
        spine_src = f.read()
    with open(os.path.join(HERE, "pii_normalize.py"), encoding="utf-8") as f:
        extra = extract_extra(spine_src, f.read())
    sys.path.insert(0, HERE)
    from pii_normalize import IGNORABLE  # noqa: E402
    failed = False
    for site in SQL_SITES:
        with open(site, encoding="utf-8") as f:
            sql_src = f.read()
        drifts = run(spine_src, sql_src, extra, set(IGNORABLE))
        rel = os.path.relpath(site, REPO)
        if drifts:
            failed = True
            print(f"check_pii_regex_parity: {rel} does not match spine_client.py")
            for d in drifts:
                print("  " + d)
        else:
            extras = [n for n in ("allow_re", "at_re", "esc_re", "ign_re") if lits(sql_src, n)]
            print(f"check_pii_regex_parity: {rel} matches spine_client.py (EMAIL exact; PHONE exact"
                  + (f"; {', '.join(extras)} checked" if extras else "") + ")")
    sys.exit(1 if failed else 0)
