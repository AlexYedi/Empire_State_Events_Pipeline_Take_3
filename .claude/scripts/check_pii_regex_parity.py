#!/usr/bin/env python3
"""PII regex parity: the Postgres backstop must carry spine's regexes verbatim.

The DB backstop proposal (docs/adr/proposals/pii-db-check.sql) promises to
mirror spine_client.py's EMAIL_RE / PHONE_RE — "same shapes, not a second
dialect" (pii-regex-set.md). Nothing enforced that: a literal that differed
from spine only in group order passed the first review unnoticed (YED-279
review follow-up). This check extracts both sets of literals and fails on any
difference, so drift fails CI instead of relying on a reviewer catching it.

TEMPORARY TOLERANCE — remove once PR #250 (A2 leading-1 phone prefix) merges:
spine on main still predates A2's (?:1[\\s.-])? prefix while the SQL already
carries #250's final shape. The check accepts exactly that one pending delta
(prefix inserted immediately after the lookbehind, per #250) and nothing
else; every other difference fails.

Stdlib only. Run with --selftest to exercise the extraction and tolerance
logic against embedded fixtures.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SPINE = os.path.join(REPO, ".claude", "scripts", "spine_client.py")
SQL = os.path.join(REPO, "docs", "adr", "proposals", "pii-db-check.sql")

# spine_client.py on main, pre-A2: the lookbehind is immediately followed by
# the +country group. PR #250 inserts (?:1[\s.-])? between the two.
A2_PRE = r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?"
A2_POST = r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?"


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


def phone_parity(spine_phone: str, sql_phone: str) -> str | None:
    """'exact', 'pending-a2' (the one tolerated pre-#250-merge delta), or None."""
    if spine_phone == sql_phone:
        return "exact"
    if spine_phone.startswith(A2_PRE) and sql_phone == A2_POST + spine_phone[len(A2_PRE):]:
        return "pending-a2"
    return None


def run(spine_src: str, sql_src: str) -> tuple[list[str], list[str]]:
    """(drifts, notices). Empty drifts = parity holds; notices are non-blocking
    (currently only the PENDING-A2 tolerance, which must NOT fail CI before
    #250 merges — that is the state the tolerance exists to allow)."""
    spine_email, spine_phone = extract_spine(spine_src)
    sql_email, sql_phone = extract_sql(sql_src)
    drifts, notices = [], []
    if sql_email != spine_email:
        drifts.append("EMAIL shape drifted:\n  spine: %s\n  sql:   %s" % (spine_email, sql_email))
    state = phone_parity(spine_phone, sql_phone)
    if state is None:
        drifts.append("PHONE shape drifted:\n  spine: %s\n  sql:   %s" % (spine_phone, sql_phone))
    elif state == "pending-a2":
        notices.append("PENDING-A2 tolerance used (phone matches spine + PR #250 prefix). Remove the tolerance from check_pii_regex_parity.py once #250 merges — parity is then expected to be exact.")
    return drifts, notices


# ---------------------------------------------------------------------------
# Selftest: extraction and tolerance logic against embedded fixtures.
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
        '    r"(?<![\\w.+-])(?:\\+\\d{1,3}[\\s.-]?)?(?:\\(\\d{3}\\)|\\d{3})[\\s.-]\\d{3}[\\s.-]\\d{4}(?![\\w])"   # c1\n'
        '    r"|(?<![\\w.])\\+\\d{10,15}(?![\\w])"                                                          # c2\n'
        ")\n"
    )
    email_py, phone_py = extract_spine(spine_src)
    ck("spine email literal extracted", email_py == r"(?<![\w/])[A-Z]+(?![\w])")
    ck("spine phone literals concatenated", phone_py == r'(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])')

    sql_src = (
        '  email_re text := $re$(?<![\\w/])[A-Z]+(?![\\w])$re$;\n'
        '  phone_re text := $re$(?<![\\w.+-])(?:\\+\\d{1,3}[\\s.-]?)?(?:\\(\\d{3}\\)|\\d{3})[\\s.-]\\d{3}[\\s.-]\\d{4}(?![\\w])|(?<![\\w.])\\+\\d{10,15}(?![\\w])$re$;\n'
    )
    drifts, notices = run(spine_src, sql_src)
    ck("identical shapes -> no drift", drifts == [] and notices == [])

    a2_sql = sql_src.replace(
        r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?",
        r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?",
    )
    drifts, notices = run(spine_src, a2_sql)
    ck("pre-A2 spine + #250-prefixed sql -> exactly the tolerated delta", drifts == [] and len(notices) == 1 and notices[0].startswith("PENDING-A2"))

    wrong_order = a2_sql.replace(
        r"(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})",
        r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:1[\s.-])?(?:\(\d{3}\)|\d{3})",
    )
    drifts, _ = run(spine_src, wrong_order)
    ck("prefix on the wrong side of +country -> drift", len(drifts) == 1 and drifts[0].startswith("PHONE"))

    drifted_email = sql_src.replace(r"[A-Z]+", r"[A-Z]+?")
    drifts, _ = run(spine_src, drifted_email)
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
    drifts, notices = run(spine_src, sql_src)
    if drifts:
        print("check_pii_regex_parity: pii-db-check.sql does not match spine_client.py")
        for d in drifts:
            print("  " + d)
        sys.exit(1)
    spine_email, spine_phone = extract_spine(spine_src)
    sql_email, sql_phone = extract_sql(sql_src)
    state = phone_parity(spine_phone, sql_phone)
    print(
        "check_pii_regex_parity: shapes match spine_client.py (EMAIL exact; PHONE %s)"
        % state
    )
