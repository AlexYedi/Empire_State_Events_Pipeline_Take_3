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

Stdlib only. Run with --selftest to exercise the extraction and comparison
logic against embedded fixtures.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SPINE = os.path.join(REPO, ".claude", "scripts", "spine_client.py")
SQL = os.path.join(REPO, "docs", "adr", "proposals", "pii-db-check.sql")


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


def run(spine_src: str, sql_src: str) -> list[str]:
    """Return a list of drift descriptions; empty list means parity."""
    spine_email, spine_phone = extract_spine(spine_src)
    sql_email, sql_phone = extract_sql(sql_src)
    drifts = []
    if sql_email != spine_email:
        drifts.append("EMAIL shape drifted:\n  spine: %s\n  sql:   %s" % (spine_email, sql_email))
    if sql_phone != spine_phone:
        drifts.append("PHONE shape drifted:\n  spine: %s\n  sql:   %s" % (spine_phone, sql_phone))
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

    print(f"\n{ok}/{n} passed")
    return 0 if ok == n else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    with open(SPINE, encoding="utf-8") as f:
        spine_src = f.read()
    with open(SQL, encoding="utf-8") as f:
        sql_src = f.read()
    drifts = run(spine_src, sql_src)
    if drifts:
        print("check_pii_regex_parity: pii-db-check.sql does not match spine_client.py")
        for d in drifts:
            print("  " + d)
        sys.exit(1)
    print("check_pii_regex_parity: shapes match spine_client.py (EMAIL exact; PHONE exact)")
