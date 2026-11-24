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

import ast
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


def _flags(node: ast.expr | None, name: str) -> int:
    """re.compile flags written as re.X names joined by |, as an int (0 when absent)."""
    if node is None:
        return 0
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _flags(node.left, name) | _flags(node.right, name)
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "re" \
            and isinstance(getattr(re, node.attr, None), re.RegexFlag):
        return int(getattr(re, node.attr))
    raise SystemExit(f"check_pii_regex_parity: {name} flags are not plain re.X names")


def compiled_literal(src: str, name: str, flags: int = 0) -> str:
    """The pattern string of the module-level `NAME = re.compile(<str constant>[, flags])`, parsed with ast.

    YED-316: the old line scan stopped at the first line ending in ')', so a comment like '(E.164 compact)'
    truncated PHONE_RE and parity could pass against a truncated pattern. The parser folds implicit and
    parenthesized multi-line concatenation into one constant; anything not resolvable to a constant, a
    second assignment, or flags other than `flags` fails loud."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise SystemExit(f"check_pii_regex_parity: cannot parse source for {name}: {e}")
    calls = [s.value for s in tree.body if isinstance(s, ast.Assign)
             and [t.id for t in s.targets if isinstance(t, ast.Name)] == [name] and len(s.targets) == 1]
    if len(calls) != 1:
        raise SystemExit(f"check_pii_regex_parity: expected one module-level {name} assignment, found {len(calls)}")
    call = calls[0]
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "compile"
            and isinstance(call.func.value, ast.Name) and call.func.value.id == "re"):
        raise SystemExit(f"check_pii_regex_parity: {name} is not assigned a re.compile(...) call")
    kw = {k.arg: k.value for k in call.keywords}
    if not call.args or len(call.args) > 2 or set(kw) - {"flags"} or (len(call.args) == 2 and kw):
        raise SystemExit(f"check_pii_regex_parity: {name} re.compile(...) arguments are not (pattern[, flags])")
    pat = call.args[0]
    if not (isinstance(pat, ast.Constant) and isinstance(pat.value, str)):
        raise SystemExit(f"check_pii_regex_parity: {name} pattern does not resolve to a string constant "
                         f"(got {type(pat).__name__}); parity cannot be checked")
    got = _flags(call.args[1] if len(call.args) == 2 else kw.get("flags"), name)
    if got != flags:
        raise SystemExit(f"check_pii_regex_parity: {name} flags are {re.RegexFlag(got)!r}, expected {re.RegexFlag(flags)!r}")
    return pat.value


def extract_spine(src: str) -> tuple[str, str]:
    """(EMAIL_RE, PHONE_RE) pattern strings from spine_client.py."""
    return compiled_literal(src, "EMAIL_RE"), compiled_literal(src, "PHONE_RE")


def extract_sql(src: str) -> tuple[str, str]:
    """(email_re, phone_re) from the $re$-dollar-quoted plpgsql literals."""
    email = re.search(r"^\s*email_re text := \$re\$(.+?)\$re\$;", src, re.M)
    phone = re.search(r"^\s*phone_re text := \$re\$(.+?)\$re\$;", src, re.M)
    if not email or not phone:
        raise SystemExit("check_pii_regex_parity: could not find $re$-quoted email_re/phone_re in pii-db-check.sql — has the file moved or changed shape?")
    return email.group(1), phone.group(1)


def extract_extra(spine_src: str, norm_src: str) -> tuple[str, str, str]:
    """(EMAIL_ALLOWLIST_RE, AT_SPELLING_RE, JSON_WS_RE) literals from spine_client.py / pii_normalize.py."""
    return (compiled_literal(spine_src, "EMAIL_ALLOWLIST_RE", re.I), compiled_literal(norm_src, "AT_SPELLING_RE", re.I),
            compiled_literal(norm_src, "JSON_WS_RE"))


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

    # YED-316: the extractor parses the pattern with ast, not "up to the first line ending in ')'".
    parened = spine_src.replace("# c1", "# 555-123-4567 (US)").replace("# c2", "# +15551234567 (E.164 compact)")
    ck("(a) comment ending in ')' on a middle line -> full pattern extracted", extract_spine(parened)[1] == phone_py)
    swapped = sql_src.replace(phone_py, phone_py.rsplit("|", 1)[1] + "|" + phone_py.rsplit("|", 1)[0])
    d = run(parened, swapped)
    ck("(b) reordered alternatives vs the backstop -> drift", len(d) == 1 and d[0].startswith("PHONE"))
    truncated = sql_src.replace(phone_py, phone_py.rsplit("|", 1)[0])   # what the old line scan read from `parened`
    d = run(parened, truncated)
    ck("(c) backstop holds only the truncated client pattern -> drift", len(d) == 1 and d[0].startswith("PHONE"))
    ck("(d) non-constant pattern (name + concatenation) -> fails loud",
       _raises(lambda: extract_spine(spine_src.replace('PHONE_RE = re.compile(\n', 'PHONE_RE = re.compile(SUFFIX +\n'))))
    ck("(d) pattern from a variable -> fails loud", _raises(lambda: extract_spine('EMAIL_RE = re.compile(r"x")\nPHONE_RE = re.compile(P)\n')))
    ck("allowlist without its re.I flag -> fails loud",
       _raises(lambda: extract_extra('EMAIL_ALLOWLIST_RE = re.compile(r"^x@")\n',
                                     'AT_SPELLING_RE = re.compile(r"%40", re.I)\nJSON_WS_RE = re.compile(r"y")\n')))

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
