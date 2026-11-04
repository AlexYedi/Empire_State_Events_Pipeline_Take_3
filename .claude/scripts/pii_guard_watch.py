#!/usr/bin/env python3
"""pii_guard_watch — measure the spine PII guard in practice, against pre-registered triggers (YED-320).

YED-319 decided to ship the international-phone alternative (PR #277, YED-309) and measure its
precision in use rather than argue it on paper. This is the measurement. Playbook (what each trigger
means and the pre-armed response): .claude/references/pii-guard-watch.md.

Modes (stdlib only):
  --shadow [--out F]   READ-ONLY count scan of prod spine text, executed IN POSTGRES via psql +
                       MI_DB_DSN. Every query runs inside the YED-312 read-only guard imported from
                       supabase/scripts/topic_intel_compute.py (begin read only -> show
                       transaction_read_only -> DO-block assert -> query -> rollback, ON_ERROR_STOP=1,
                       fail closed). The SQL returns COUNTS ONLY; any non-integer cell aborts the run.
                       Needs Postgres >= 15 (regexp_instr); prod is 17.
  --local-shapes       Local-only (refuses under CI): shape signatures of the hits, computed in SQL
                       (digit -> 9, letter -> a, <=40 chars), never raw text. For a human looking at F2.
  --evaluate           Reads the shadow JSON + the refusal telemetry (.claude/.state/pii-refusals.jsonl,
                       written by spine_client) + the acknowledged F2 baseline (.claude/references/
                       pii-guard-baseline.json) and computes triggers F1-F6. Prints a table + a JSON verdict.
                       --no-telemetry (CI) marks the telemetry legs INSUFFICIENT (no telemetry in CI).
  --selftest           Offline fixtures for every trigger at FIRE / INSUFFICIENT / quiet, the Wilson bound,
                       the alternative splitter, the variant patterns, and the counts-only SQL guarantee.

Exit codes: 0 = no trigger fired (PASS or INSUFFICIENT) · 2 = at least one FIRE · 3 = REVIEW only ·
1 = NOT EVALUATED (shadow missing or older than 8 days), error, or selftest failure.
INSUFFICIENT means "below the minimum n: no information", never PASS.

F2 (YED-326) reviews the DELTA over the acknowledged baseline, so a known-clean scan cannot reopen
REVIEW every week: REVIEW only when a column's loose_not_live / bare_digits_10_11 count exceeds its
acknowledged count, a corpus column is new or no longer scanned, or the baseline is missing,
unparseable or older than 90 days — fail loud, never silently QUIET. Re-baselining means a fresh
hand-check recorded in the file (checked_by / checked_at / method).

Survivorship: once #277 is live, the guard (and the DB backstop) keep alt-3 text and non-allowlisted
emails OUT of prod, so the shadow can measure their precision only pre-merge. Post-merge precision
comes from the refusal telemetry: F1(b) and F5.

Patterns: LIVE is spine_client.PHONE_RE as it stands, read at runtime and passed into the SQL as a
dollar-quoted literal (the DB backstop carries the same text verbatim, so it is valid ARE). ALT3 is
LIVE's third alternative once #277 is merged; until then it is #277's candidate, carried below.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import spine_client as sc  # noqa: E402  (PHONE_RE / EMAIL_RE / split_alternatives / classifier lists)

sys.path.insert(0, os.path.join(ROOT, "supabase", "scripts"))
import topic_intel_compute as tic  # noqa: E402  (the YED-312 read-only guard: ro_q, ro_argv, RO_ASSERT)

SHADOW_OUT = os.path.join(ROOT, ".claude", ".state", "pii-shadow.json")
TELEMETRY = sc.TELEMETRY_PATH
STALE_DAYS = 8                                 # a weekly scan plus a day of slack
BASELINE_PATH = os.path.join(ROOT, ".claude", "references", "pii-guard-baseline.json")
BASELINE_STALE_DAYS = 90                       # a baseline needs a fresh hand-check each quarter (YED-326)
BASELINE_FIELDS = ("loose_not_live", "bare_digits_10_11")

# --------------------------------------------------------------------------- patterns
# PR #277's third alternative, verbatim (YED-309). Used only while LIVE has two alternatives.
CANDIDATE_ALT3 = (r"(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))"
                  r"\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)")
# VARIANT_C's guard: refuse to start a match on a thousands-style run (+CC then 3-digit groups only).
THOUSANDS_GUARD = r"(?!\+\d{1,3}(?:[\s.]\d{3}){2,}(?![\s.-]?\d))"
# LOOSE = the recall detector. 8-15 digits with at most one separator between digits, either after a
# +, 00 or tel: prefix, or crossing at least one separator (a lone 10-digit integer is a timestamp or
# an id, not a phone). ISO dates and plain decimals are excluded so timestamps and scores in
# to_jsonb(row) text don't drown the signal. Written to be valid in both Python re and Postgres ARE.
LOOSE_RE = (r"(?<![\w.+-])(?:(?:\+|00|tel:)\s?\d(?:[\s.()-]?\d){7,14}"
            r"|(?!\d{4}-\d{2}-\d{2})(?!\d+\.\d+(?![\s.()-]?\d))(?=\d{1,7}[\s.()-])\d(?:[\s.()-]?\d){7,14})(?!\d)")
# BARE = the one miss class we know of (A3, YED-183): a separator-less 10/11-digit number. Counted on
# prose columns only (in jsonb rows it is every unix timestamp and id). Valid Python re and ARE.
BARE_RE = r"(?<![\w.+-])\d{10,11}(?!\w|[.,]\d)"
# Classifiers, applied in SQL to the alt-3 match in a row (counts only). Built from the same word lists
# spine_client uses for its in-memory prose_hint. Postgres-only syntax (\m \M word bounds, \uXXXX so the
# SQL stays ASCII); never compiled in Python.
PROSE_AFTER = r"[%$€£¥]|\m(" + "|".join(sc.PROSE_UNITS) + r")\M"
PROSE_BEFORE = r"\m(" + "|".join(sc.PROSE_WORDS) + r")\M"
ALL_THREES = r"^\+\d{1,3}(?:[\s.]\d{3})+$"

# Probe 0 from migration 0017 (PR #277), split by what each string is. The F1 response re-runs it.
PROBE0_REAL = ["+44 20 7946 0958", "+44-20-7946-0958", "+49 (0)30 1234 5678", "call +33 1 99 00 12 34 today",
               "555-123-4567", "+15551234567", "+44 20 7946 0958"]
PROBE0_KNOWN_FP = ["revenue +12 345 678 EUR", "+1 234 567 890 shares"]
PROBE0_NEGATIVE = ["+44 20", "+1.2.3.4.5.6.7", "2026-11-04 12:30:45", "v2.3.4", "+40.7128 -74.0060", "x"]


def patterns(live_phone: str | None = None) -> dict:
    """Every pattern the shadow counts, derived from the LIVE regex so nothing is pasted twice."""
    live = live_phone or sc.PHONE_RE.pattern
    alts = sc.split_alternatives(live)
    if "|".join(alts) != live:
        raise SystemExit("pii_guard_watch: alternative split does not rebuild PHONE_RE — refusing to label")
    alt3 = alts[2] if len(alts) >= 3 else CANDIDATE_ALT3
    if alt3.count("{6,14}") != 1 or not alt3.startswith(r"(?<![\w.+-])\+"):
        raise SystemExit("pii_guard_watch: ALT3 changed shape; VARIANT_B/C cannot be derived — update the watcher")
    return {"live": live, "alt1": alts[0], "alt2": alts[1] if len(alts) > 1 else None, "alt3": alt3,
            "alt3_source": "live" if len(alts) >= 3 else "candidate (PR #277, not yet live)",
            "variant_b": alt3.replace("{6,14}", "{8,14}"),
            "variant_c": r"(?<![\w.+-])" + THOUSANDS_GUARD + alt3[len(r"(?<![\w.+-])"):],
            "loose": LOOSE_RE, "bare": BARE_RE, "email": sc.EMAIL_RE.pattern,
            "email_allow": sc.EMAIL_ALLOWLIST_RE.pattern}


# --------------------------------------------------------------------------- the shadow SQL
# (label, table, text expression, kind). kind: "full" = every count; "prose" = every count plus the
# bare-digits recall count; "bare" = the bare-digits count only (person bio, already inside person.row).
CORPUS = [
    ("claim.claim_text", "public.claim", "x.claim_text", "prose"),
    ("claim.quote", "public.claim", "x.quote", "prose"),
    ("claim.metadata", "public.claim", "x.metadata::text", "full"),
    ("claim.locator", "public.claim", "x.locator::text", "full"),
    ("claim.proposed_entities", "public.claim", "x.proposed_entities::text", "full"),
    ("documents.title", "public.documents", "x.title", "prose"),
    ("documents.author", "public.documents", "x.author", "full"),
    ("documents.external_ref", "public.documents", "x.external_ref", "full"),
    ("documents.metadata", "public.documents", "x.metadata::text", "full"),
    ("doc_chunks.content", "public.doc_chunks", "x.content", "full"),
    ("doc_claims.row", "public.doc_claims", "to_jsonb(x)::text", "full"),
    ("person.bio", "public.person", "to_jsonb(x)->>'bio'", "bare"),
    ("person.row", "public.person", "to_jsonb(x)::text", "full"),
    ("company.row", "public.company", "to_jsonb(x)::text", "full"),
    ("event.row", "public.event", "to_jsonb(x)::text", "full"),
    ("topic.row", "public.topic", "to_jsonb(x)::text", "full"),
]
COUNT_FIELDS = ["n_rows", "live", "alt1", "alt2", "alt3", "variant_b", "variant_c", "loose", "loose_not_live",
                "bare_digits_10_11", "email", "numeric_prose"]


def _lit(p: str) -> str:
    if "$re$" in p:
        raise SystemExit("pii_guard_watch: a pattern contains the $re$ quote tag")
    return f"$re$({p})$re$"   # outer group: a top-level | can never escape into the SQL around it


def column_conditions(pats: dict, kind: str = "full") -> dict:
    """{count field: SQL filter} for one column (None = plain count(*)). Pinned by the selftest."""
    L = {k: _lit(v) for k, v in pats.items() if isinstance(v, str) and k != "alt3_source"}
    c = {
        "n_rows": None,
        "live": f"t ~ {L['live']}",
        "alt1": f"t ~ {L['alt1']}",
        "alt2": f"t ~ {L['alt2']}" if pats["alt2"] else "false",
        "alt3": "a3m is not null",
        "variant_b": f"t ~ {L['variant_b']}",
        "variant_c": f"t ~ {L['variant_c']}",
        "loose": f"t ~ {L['loose']}",
        "loose_not_live": f"t ~ {L['loose']} and not t ~ {L['live']}",
        "bare_digits_10_11": f"t ~ {L['bare']}" if kind in ("prose", "bare") else "false",
        "email": "em is not null",
        # p = regexp_instr's position of the alt-3 match itself (not strpos of its text, which could
        # find an earlier copy that the lookbehind rejected)
        "numeric_prose": ("a3m is not null and (substr(t, p + length(a3m), 12) ~* $re$" + PROSE_AFTER + "$re$"
                          " or substr(t, greatest(p - 20, 1), p - greatest(p - 20, 1)) ~* $re$" + PROSE_BEFORE + "$re$"
                          " or a3m ~ $re$" + ALL_THREES + "$re$)"),
    }
    if kind == "bare":
        c = {k: (v if k in ("n_rows", "bare_digits_10_11") else "false") for k, v in c.items()}
    assert list(c) == COUNT_FIELDS
    return c


def column_sql(table: str, expr: str, pats: dict, kind: str = "full") -> str:
    """One read-only query per corpus column. The final SELECT is count(*) aggregates and nothing else."""
    L = {k: _lit(pats[k]) for k in ("alt3", "email", "email_allow")}
    items = ["count(*)" if c is None else f"count(*) filter (where {c})"
             for c in column_conditions(pats, kind).values()]
    return (f"with src as (select {expr} as t from {table} x),\n"
            f"h as (select t, substring(t from {L['alt3']}) as a3m, regexp_instr(t, {L['alt3']}) as p,\n"
            f"  (select m from (select substring(t from {L['email']}) as m) e where not m ~* {L['email_allow']}) as em\n"
            f"  from src where t is not null)\n"
            f"select {', '.join(items)}\n"
            f"from h z;")


def final_select_items(sql: str) -> list[str]:
    """The top-level items of the query's output SELECT (what psql prints), for the counts-only check."""
    m = re.search(r"\nselect (.*)\nfrom h z;$", sql, re.S)
    if not m:
        return []
    items, depth, start, s = [], 0, 0, m.group(1)
    for i, c in enumerate(s):
        depth += c == "("
        depth -= c == ")"
        if c == "," and depth == 0:
            items.append(s[start:i].strip())
            start = i + 1
    items.append(s[start:].strip())
    return items


def counts_only(sql: str) -> bool:
    items = final_select_items(sql)
    return (len(items) == len(COUNT_FIELDS) and all(re.fullmatch(r"count\(\*\)( filter \(where .*\))?", i, re.S)
                                                    for i in items)
            and "regexp_replace" not in sql)


def shadow(run_query=None, now: dt.datetime | None = None) -> dict:
    """Counts per column. `run_query` defaults to the YED-312 guarded psql runner."""
    run_query = run_query or tic.ro_q
    pats = patterns()
    out = {"generated_at": (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "alt3_source": pats["alt3_source"], "live_alternatives": len(sc.split_alternatives(pats["live"])),
           "columns": {}}
    for label, table, expr, kind in CORPUS:
        sql = column_sql(table, expr, pats, kind)
        if not counts_only(sql):
            raise SystemExit(f"pii_guard_watch: refusing to run {label}: its SELECT is not counts-only")
        rows = run_query(sql)
        if len(rows) != 1 or len(rows[0]) != len(COUNT_FIELDS) or not all(re.fullmatch(r"\d+", c) for c in rows[0]):
            raise SystemExit(f"pii_guard_watch: {label} returned something other than {len(COUNT_FIELDS)} counts "
                             "— aborting (fail closed), output discarded")
        out["columns"][label] = dict(zip(COUNT_FIELDS, map(int, rows[0])))
    out["totals"] = {f: sum(c[f] for c in out["columns"].values()) for f in COUNT_FIELDS}
    return out


def shapes_sql(table: str, expr: str, pats: dict) -> str:
    """--local-shapes only: (kind, shape, count) rows. The mask runs in SQL, so raw text never leaves Postgres."""
    L = {k: _lit(pats[k]) for k in ("alt3", "loose", "live", "email", "bare")}

    def mask(key: str) -> str:
        m = f"substring(t from {L[key]})"
        return (f"left(regexp_replace(regexp_replace(regexp_replace({m}, '[[:digit:]]', '9', 'g'), "
                f"'[[:alpha:]]', 'a', 'g'), '[[:space:]]', ' ', 'g'), 40)")

    return (f"with src as (select {expr} as t from {table} x where {expr} is not null)\n"
            f"select 'alt3', {mask('alt3')}, count(*) from src where t ~ {L['alt3']} group by 2\n"
            f"union all select 'loose_not_live', {mask('loose')}, count(*) from src "
            f"where t ~ {L['loose']} and not t ~ {L['live']} group by 2\n"
            f"union all select 'bare_digits', {mask('bare')}, count(*) from src where t ~ {L['bare']} group by 2\n"
            f"union all select 'email', {mask('email')}, count(*) from src where t ~ {L['email']} group by 2\n"
            f"order by 1, 3 desc;")


def local_shapes(run_query=None) -> int:
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("pii_guard_watch: --local-shapes never runs in CI (shapes stay on this machine)", file=sys.stderr)
        return 1
    run_query = run_query or tic.ro_q
    pats = patterns()
    for label, table, expr, _ in CORPUS:
        for kind, shape, n in run_query(shapes_sql(table, expr, pats)):
            print(f"{label:24} {kind:15} {n:>6}  {shape}")
    return 0


# --------------------------------------------------------------------------- evaluation
Z95 = 1.959963984540054
F1_MIN_N, F1_PROSE_LB = 30, 0.20           # (a) pre-merge shadow: alt-3 hits; LB(numeric_prose / n_alt3)
F1B_MIN_N, F1B_LB = 30, 0.20               # (b) telemetry: alt-3 refusals; LB(prose_hint / n)
F3_WINDOW_DAYS, F3_MULTI_N, F3_BIG_BATCH = 7, 3, 50
F5_MIN_N, F5_LB = 30, 0.20                 # telemetry: email refusals; LB(asset_code / n)
F6_MIN_N, F6_P95_MS = 200, 50.0            # ok_sample records; p95 scan_ms


def wilson_lb(k: int, n: int, z: float = Z95) -> float:
    """Lower bound of the Wilson score interval (Wilson 1927) for k successes in n trials."""
    if n <= 0:
        return 0.0
    p = k / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / (1 + z * z / n))


def p95(xs: list[float]) -> float:
    s = sorted(xs)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)] if s else 0.0     # nearest-rank


def load_telemetry(path: str) -> tuple[list[dict], int]:
    recs, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                r["_ts"] = dt.datetime.strptime(r["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
                recs.append(r)
            except (ValueError, KeyError, TypeError):
                bad += 1
    return recs, bad


def _v(verdict: str, signal: str, **counts) -> dict:
    return {"verdict": verdict, "signal": signal, "counts": counts}


def _rate(n: int, k: int, min_n: int, lb_max: float, what: str, **counts) -> dict:
    """FIRE / PASS / INSUFFICIENT for a Wilson-bounded share k/n."""
    lb = wilson_lb(k, n)
    if n >= min_n and lb > lb_max:
        return _v("FIRE", f"LB({what}) {lb:.3f} > {lb_max}", **counts)
    if n >= min_n:
        return _v("PASS", f"LB({what}) {lb:.3f} <= {lb_max}", **counts)
    return _v("INSUFFICIENT", f"n {n} < {min_n}", **counts)


def _shadow_problem(shadow_data: dict | None, now: dt.datetime) -> str | None:
    if shadow_data is None:
        return "no shadow scan file"
    try:
        gen = dt.datetime.strptime(shadow_data["generated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (KeyError, TypeError, ValueError):
        return "shadow scan has no readable generated_at"
    if now - gen > dt.timedelta(days=STALE_DAYS):
        return f"shadow scan is stale (generated {shadow_data['generated_at']}, older than {STALE_DAYS} days)"
    return None


def load_baseline(path: str, now: dt.datetime) -> tuple[dict | None, str | None]:
    """Read the acknowledged F2 baseline (YED-326). Returns (data, problem); a problem means
    REVIEW, never QUIET — a baseline that is missing, malformed or stale must fail loud."""
    if not os.path.exists(path):
        return None, f"no baseline file ({os.path.relpath(path, ROOT)})"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("columns"), dict) or not data["columns"]:
            raise ValueError("columns must be a non-empty object")
        if not isinstance(data.get("checked_by"), str) or not data["checked_by"].strip():
            raise ValueError("checked_by must record who hand-checked the counts")
        checked = dt.datetime.strptime(data["checked_at"], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
        for label, cnt in data["columns"].items():
            if (not isinstance(cnt, dict) or set(cnt) != set(BASELINE_FIELDS)
                    or not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in cnt.values())):
                raise ValueError(f"column {label!r} must hold non-negative {'/'.join(BASELINE_FIELDS)} counts")
    except (OSError, ValueError, TypeError) as e:
        return None, f"baseline file malformed: {e}"
    age_days = (now.date() - checked.date()).days   # date arithmetic: checked_at carries no time component
    if age_days > BASELINE_STALE_DAYS:
        return data, (f"baseline is stale (checked {data['checked_at']}, {age_days} days ago, "
                      f"older than {BASELINE_STALE_DAYS}) — re-baseline with a fresh hand-check recorded in the file")
    return data, None


def evaluate(shadow_data: dict | None, telemetry: list[dict] | None, now: dt.datetime,
             no_tel_reason: str = "no telemetry file", post_merge: bool | None = None,
             baseline: dict | None = None, baseline_problem: str | None = None) -> dict:
    if post_merge is None:
        post_merge = len(sc.split_alternatives(sc.PHONE_RE.pattern)) >= 3
    problem = _shadow_problem(shadow_data, now)
    T = None if problem else shadow_data.get("totals")
    scanned = bool(T) and T.get("n_rows", 0) > 0
    no_shadow = "INSUFFICIENT"
    tel_missing = f"INSUFFICIENT ({no_tel_reason})"
    out: dict[str, dict] = {}
    refusals = [r for r in (telemetry or []) if r.get("rule") != "ok_sample"]

    # F1 — alt-3 precision. (a) shadow numeric prose: PRE-MERGE ONLY (post-merge the guard keeps alt-3
    # text out of prod, so the shadow sees survivors only). (b) telemetry: prose_hint share of alt-3 refusals.
    if not scanned:
        leg_a = _v(no_shadow, "pre-merge shadow only: no shadow scan")
    else:
        leg_a = _rate(T["alt3"], T["numeric_prose"], F1_MIN_N, F1_PROSE_LB, "numeric_prose/alt3",
                      n_alt3=T["alt3"], numeric_prose=T["numeric_prose"])
        leg_a["signal"] = "pre-merge shadow only: " + leg_a["signal"]
    if telemetry is None:
        leg_b = _v(tel_missing, "alt-3 refusals need session telemetry")
    else:
        alt3_refusals = [r for r in refusals if r.get("rule") == "phone_alt3"]
        hinted = sum(1 for r in alt3_refusals if r.get("prose_hint") is True)
        leg_b = _rate(len(alt3_refusals), hinted, F1B_MIN_N, F1B_LB, "prose_hint/alt3 refusals",
                      alt3_refusals=len(alt3_refusals), prose_hint=hinted)
    lead = leg_b if post_merge else leg_a          # the leg that can measure precision right now
    f1 = "FIRE" if "FIRE" in (leg_a["verdict"], leg_b["verdict"]) else lead["verdict"]
    out["F1"] = {"verdict": f1, "signal": f"alt-3 precision; deciding leg: {'b telemetry' if post_merge else 'a shadow'}"
                 f" ({'post' if post_merge else 'pre'}-merge)", "legs": {"a_shadow": leg_a, "b_telemetry": leg_b}}

    # F2 — recall: LOOSE or a bare 10/11-digit number in prose finds what LIVE does not. REVIEW, never FIRE.
    # YED-326: the acknowledged baseline (.claude/references/pii-guard-baseline.json) holds the
    # hand-checked per-column counts, so the weekly scan reviews only the DELTA — a column above its
    # acknowledged count, a corpus column that is new or no longer scanned, or a missing /
    # unparseable / stale baseline (fail loud, never silently QUIET). Signals carry totals only:
    # per-column detail (column names) stays in this run's local output, like F4's.
    f2_cols: list[str] = []
    if not scanned:
        out["F2"] = _v(no_shadow, "no shadow scan")
    elif baseline_problem or baseline is None:
        out["F2"] = _v("REVIEW", f"baseline: {baseline_problem or 'no baseline provided'}",
                       current_loose_not_live=T["loose_not_live"], current_bare_digits_10_11=T["bare_digits_10_11"])
    else:
        bcols, cols_now = baseline["columns"], shadow_data["columns"]
        ack_l = sum(bcols[c]["loose_not_live"] for c in bcols)
        ack_b = sum(bcols[c]["bare_digits_10_11"] for c in bcols)
        over = sorted(c for c in cols_now if c in bcols
                      and any(cols_now[c][f] > bcols[c][f] for f in BASELINE_FIELDS))
        new = sorted(c for c in cols_now if c not in bcols)
        gone = sorted(c for c in bcols if c not in cols_now)
        if over or new or gone:
            f2_cols = ([f"{c}: " + ", ".join(f"{f} {bcols[c][f]}->{cols_now[c][f]}" for f in BASELINE_FIELDS
                                             if cols_now[c][f] > bcols[c][f]) for c in over]
                       + [f"new column: {c}" for c in new]
                       + [f"baseline column no longer scanned: {c}" for c in gone])
            out["F2"] = _v("REVIEW", f"{len(over)} column(s) above the acknowledged baseline; "
                           f"{len(new)} new; {len(gone)} no longer scanned",
                           current_loose_not_live=T["loose_not_live"], acknowledged_loose_not_live=ack_l,
                           current_bare_digits_10_11=T["bare_digits_10_11"], acknowledged_bare_digits_10_11=ack_b)
        else:
            out["F2"] = _v("PASS", f"LOOSE-not-LIVE rows {T['loose_not_live']} (acknowledged {ack_l}); "
                           f"bare 10/11-digit rows {T['bare_digits_10_11']} (acknowledged {ack_b})",
                           current_loose_not_live=T["loose_not_live"], acknowledged_loose_not_live=ack_l,
                           current_bare_digits_10_11=T["bare_digits_10_11"], acknowledged_bare_digits_10_11=ack_b)

    # F3 — batch blast radius: refusals that aborted multi-row writes.
    if telemetry is None:
        out["F3"] = _v(tel_missing, "batch refusals need session telemetry")
    else:
        since = now - dt.timedelta(days=F3_WINDOW_DAYS)
        window = [r for r in telemetry if r["_ts"] >= since]
        wref = [r for r in window if r.get("rule") != "ok_sample"]
        multi = sum(1 for r in wref if (r.get("batch_size") or 1) > 1)
        big = sum(1 for r in wref if (r.get("batch_size") or 1) > F3_BIG_BATCH)
        if multi >= F3_MULTI_N or big > 0:
            out["F3"] = _v("FIRE", f"{multi} multi-row refusals (>= {F3_MULTI_N}) or {big} with batch > {F3_BIG_BATCH}",
                           multi_row_refusals_7d=multi, big_batch_refusals_7d=big)
        elif window:
            out["F3"] = _v("PASS", f"{multi} multi-row refusals in {F3_WINDOW_DAYS}d",
                           multi_row_refusals_7d=multi, big_batch_refusals_7d=big)
        else:
            out["F3"] = _v("INSUFFICIENT", f"no guarded writes recorded in {F3_WINDOW_DAYS}d")

    # F4 — bypass: the guard refuses LIVE phones and non-allowlisted emails, so any in prod skipped it.
    f4_cols: list[str] = []
    if not scanned:
        out["F4"] = _v(no_shadow, "no shadow scan")
    else:
        live_hits, email_hits = T["live"], T["email"]
        f4_cols = sorted(c for c, v in shadow_data["columns"].items() if v["live"] > 0 or v["email"] > 0)
        out["F4"] = _v("FIRE" if live_hits > 0 or email_hits > 0 else "PASS",
                       f"LIVE phone hits {live_hits}; non-allowlisted email hits {email_hits}",
                       live=live_hits, email=email_hits, rows_scanned=T["n_rows"])

    # F5 — email precision, from refusals (asset_code computed in memory by spine_client).
    if telemetry is None:
        out["F5"] = _v(tel_missing, "email refusals need session telemetry")
    else:
        emails = [r for r in refusals if r.get("rule") == "email"]
        coded = sum(1 for r in emails if r.get("asset_code") is True)
        out["F5"] = _rate(len(emails), coded, F5_MIN_N, F5_LB, "asset_code/email refusals",
                          email_refusals=len(emails), asset_code=coded)

    # F6 — cost: p95 scan time on the sampled success path (rows req() sent).
    if telemetry is None:
        out["F6"] = _v(tel_missing, "scan timing needs session telemetry")
    else:
        ms = [float(r["scan_ms"]) for r in telemetry if r.get("rule") == "ok_sample" and "scan_ms" in r]
        p = p95(ms)
        if len(ms) >= F6_MIN_N and p > F6_P95_MS:
            out["F6"] = _v("FIRE", f"p95 scan_ms {p:.3f} > {F6_P95_MS}", n_samples=len(ms))
        elif len(ms) >= F6_MIN_N:
            out["F6"] = _v("PASS", f"p95 scan_ms {p:.3f} <= {F6_P95_MS}", n_samples=len(ms))
        else:
            out["F6"] = _v("INSUFFICIENT", f"n_samples {len(ms)} < {F6_MIN_N}", n_samples=len(ms))

    fired = [k for k, v in out.items() if v["verdict"] == "FIRE"]
    review = [k for k, v in out.items() if v["verdict"] == "REVIEW"]
    state = "NOT EVALUATED" if problem else "FIRE" if fired else "REVIEW" if review else "QUIET"
    return {"evaluated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "state": state, "fired": fired, "review": review,
            "not_evaluated_reason": problem,
            "exit_code": 1 if problem else 2 if fired else 3 if review else 0,
            "issue_title": f"PII guard watcher: {state} {' '.join(fired + review)}" if state in ("FIRE", "REVIEW") else "",
            "shadow_generated_at": (shadow_data or {}).get("generated_at"),
            "alt3_source": (shadow_data or {}).get("alt3_source"), "post_merge": post_merge,
            "rows_scanned": T.get("n_rows", 0) if T else 0, "f4_columns": f4_cols,
            "f2_columns": f2_cols, "triggers": out}


def render(verdict: dict) -> str:
    """Table of verdicts + counts. Never shapes, ids or column names (logs and the public issue body)."""
    lines = [f"PII guard watcher — evaluated {verdict['evaluated_at']} — shadow generated "
             f"{verdict['shadow_generated_at'] or 'n/a'} — state {verdict['state']} "
             f"(rows scanned {verdict['rows_scanned']}; alt-3 source: {verdict['alt3_source']})"]
    if verdict["not_evaluated_reason"]:
        lines += ["", f"**NOT EVALUATED: {verdict['not_evaluated_reason']}.** Shadow-based triggers were not computed; "
                  "exit 1. Re-run --shadow first."]
    lines += ["", "| # | Verdict | Signal | Counts |", "|---|---|---|---|"]
    for k, v in verdict["triggers"].items():
        if "legs" in v:
            lines.append(f"| {k} | {v['verdict']} | {v['signal']} | |")
            for leg, lv in v["legs"].items():
                lines.append(f"| {k}.{leg} | {lv['verdict']} | {lv['signal']} | {json.dumps(lv['counts'])} |")
        else:
            sig = v["signal"]
            detail_local = (k == "F4" and v["verdict"] == "FIRE" and verdict.get("f4_columns")) \
                or (k == "F2" and verdict.get("f2_columns"))
            if detail_local:
                sig += "; column detail in the run's local output / Linear"
            lines.append(f"| {k} | {v['verdict']} | {sig} | {json.dumps(v['counts'])} |")
    lines += ["", "INSUFFICIENT = below the minimum n (no information), not a pass. "
              "Playbook: .claude/references/pii-guard-watch.md (YED-320)."]
    return "\n".join(lines)


# --------------------------------------------------------------------------- selftest
def selftest() -> bool:
    results: list[tuple[str, bool]] = []

    def ck(name: str, cond: bool) -> None:
        results.append((name, bool(cond)))

    # Wilson lower bounds against published values (Newcombe 1998, method 3; Wilson 1927).
    ck("wilson LB 5/10 = 0.2366", abs(wilson_lb(5, 10) - 0.2366) < 1e-4)
    ck("wilson LB 10/10 = 0.7225", abs(wilson_lb(10, 10) - 0.7225) < 1e-4)
    ck("wilson LB 0/10 = 0", wilson_lb(0, 10) == 0.0)
    ck("wilson LB 1/29 = 0.0061", abs(wilson_lb(1, 29) - 0.0061) < 1e-4)
    ck("wilson LB n=0 -> 0 (no information)", wilson_lb(0, 0) == 0.0)

    # Splitter + derived patterns: on an explicit 2-alt and the #277 3-alt fixture (holds pre and post merge).
    fx = sc._FIXTURE_3ALT
    ck("splitter: live PHONE_RE parts join back exactly", "|".join(sc.split_alternatives(sc.PHONE_RE.pattern)) == sc.PHONE_RE.pattern)
    ck("splitter: 3-alt fixture -> 3 parts, joins back exactly",
       len(sc.split_alternatives(fx)) == 3 and "|".join(sc.split_alternatives(fx)) == fx)
    ck("candidate ALT3 == the fixture's third alternative (no paste drift)", sc.split_alternatives(fx)[2] == CANDIDATE_ALT3)
    p2, p3, pl = patterns("|".join(sc.split_alternatives(fx)[:2])), patterns(fx), patterns()
    ck("alt3 source: candidate on a 2-alt live, live on a 3-alt live",
       p2["alt3_source"].startswith("candidate") and p3["alt3_source"] == "live" and p3["alt3"] == CANDIDATE_ALT3)
    R = {k: re.compile(v) for k, v in p3.items() if isinstance(v, str) and k not in ("alt3_source",)}
    hit = lambda k, s: bool(R[k].search(s))   # noqa: E731
    ck("alt3 / B / C all hit +44 20 7946 0958", all(hit(k, "+44 20 7946 0958") for k in ("alt3", "variant_b", "variant_c")))
    ck("VARIANT_B drops a 7-digit +3 400 000; alt3 keeps it", hit("alt3", "+3 400 000") and not hit("variant_b", "+3 400 000"))
    ck("VARIANT_C drops thousands-style +1 234 567 890; B keeps it",
       hit("variant_b", "+1 234 567 890 users") and not hit("variant_c", "+1 234 567 890 users"))
    ck("VARIANT_C keeps a real +1 234 567 8901", hit("variant_c", "+1 234 567 8901"))
    alts3 = sc.split_alternatives(fx)
    full_b, full_c = "|".join(alts3[:2] + [p3["variant_b"]]), "|".join(alts3[:2] + [p3["variant_c"]])
    probe0 = PROBE0_REAL + PROBE0_KNOWN_FP + PROBE0_NEGATIVE
    ck("probe 0: #277 matches 7 real + 2 known FP, rejects 6",
       [bool(re.search(fx, s)) for s in probe0] == [True] * 9 + [False] * 6)
    ck("probe 0: VARIANT_B keeps all 7 real, drops 'revenue +12 345 678 EUR' only",
       [bool(re.search(full_b, s)) for s in probe0] == [True] * 7 + [False, True] + [False] * 6)
    ck("probe 0: VARIANT_C keeps all 7 real, drops both known FPs",
       [bool(re.search(full_c, s)) for s in probe0] == [True] * 7 + [False] * 8)
    ck("LOOSE hits intl, national and prefixed numbers",
       all(hit("loose", s) for s in ("+44 20 7946 0958", "020 7946 0958", "0044 20 7946 0958", "tel:+15551234567",
                                    "555-123-4567")))
    ck("LOOSE ignores timestamps, ISO dates, decimals, ids",
       not any(hit("loose", s) for s in ("1757700000", "2026-09-16T22:00:00Z", '{"created_at": "2026-09-16 22:00:00+00"}',
                                        "score 0.87345671", "uuid 3e9d3699-c2db-8163-919f-0a1b2c3d4e5f")))
    ck("LOOSE-not-LIVE catches the national UK number LIVE misses",
       hit("loose", "020 7946 0958") and not re.search(sc.PHONE_RE, "020 7946 0958"))
    ck("BARE hits bare 10/11-digit numbers in prose (the A3 miss class LIVE and LOOSE skip)",
       all(hit("bare", s) for s in ("call 5551234567 now", "ring 15551234567.", "(2125550134)"))
       and not hit("loose", "call 5551234567 now") and not re.search(sc.PHONE_RE, "call 5551234567 now"))
    ck("BARE ignores 9/12 digits, decimals and words",
       not any(hit("bare", s) for s in ("id 555123456", "n 555123456789", "x 5551234567.25", "v5551234567", "a5551234567b")))

    # The shadow SQL: counts only, the pinned conditions, the guarded runner.
    sqls = [column_sql(t, e, p, k) for p in (p2, p3) for _, t, e, k in CORPUS]
    ck("every shadow query's output SELECT is count(*) aggregates only", all(counts_only(s) for s in sqls))
    ck("counts-only check rejects a query that selects text",
       not counts_only(sqls[0].replace("\nselect count(*), ", "\nselect t, count(*), ", 1)))
    ck("counts-only check rejects shape output", not counts_only(sqls[0] + " -- regexp_replace"))
    ck("LIVE regex is passed in verbatim (dollar-quoted)",
       all(f"$re$({sc.PHONE_RE.pattern})$re$" in column_sql(t, e, pl, k) for _, t, e, k in CORPUS if k != "bare"))
    cond = column_conditions(p2)
    ck("loose_not_live = LOOSE and NOT LIVE (pinned)",
       cond["loose_not_live"] == f"t ~ {_lit(LOOSE_RE)} and not t ~ {_lit(p2['live'])}")
    ck("bare_digits only on prose/bare columns; a 'bare' column counts nothing else",
       cond["bare_digits_10_11"] == "false" and column_conditions(p2, "prose")["bare_digits_10_11"] == f"t ~ {_lit(BARE_RE)}"
       and all(v == "false" for k, v in column_conditions(p2, "bare").items() if k not in ("n_rows", "bare_digits_10_11")))
    ck("numeric_prose positions on regexp_instr (the match itself), never strpos",
       all("regexp_instr(t, " in s and "strpos" not in s for s in sqls))
    ck("corpus covers the F4 bypass columns",
       {"doc_chunks.content", "doc_claims.row", "claim.locator", "claim.proposed_entities", "documents.author",
        "documents.external_ref"} <= {c[0] for c in CORPUS})
    ck("shapes SQL masks digits and letters", "'[[:digit:]]', '9'" in shapes_sql("public.claim", "x.quote", p2)
       and "'[[:alpha:]]', 'a'" in shapes_sql("public.claim", "x.quote", p2))
    saved = {k: os.environ.get(k) for k in ("CI", "GITHUB_ACTIONS")}
    os.environ["CI"] = "true"
    ran = []
    with contextlib.redirect_stderr(io.StringIO()):
        rc = local_shapes(run_query=lambda q: ran.append(q) or [])
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    ck("--local-shapes refuses under CI and runs no query", rc == 1 and not ran)

    zero = ["0"] * len(COUNT_FIELDS)
    sh = shadow(run_query=lambda q: [["5"] + zero[1:]])
    ck("shadow parses counts and totals them", sh["totals"]["n_rows"] == 5 * len(CORPUS) and sh["totals"]["live"] == 0)
    try:
        shadow(run_query=lambda q: [["5", "+44 20 7946 0958"] + zero[2:]])
        ck("shadow aborts on a non-integer cell", False)
    except SystemExit:
        ck("shadow aborts on a non-integer cell", True)
    calls, real_ro_q = [], tic.ro_q
    tic.ro_q = lambda q: calls.append(q) or [["1"] + zero[1:]]
    try:
        shadow()                                                  # no runner passed: must use tic.ro_q
    finally:
        tic.ro_q = real_ro_q
    ck("shadow() runs every query through tic.ro_q by default (recorder)", len(calls) == len(CORPUS))
    ck("tic.ro_q is the YED-312 guarded psql (begin read only, assert, rollback)",
       real_ro_q.__module__ == "topic_intel_compute"
       and tic.ro_argv("psql", "dsn", "select 1")[-1] == "rollback;" and "begin read only;" in tic.ro_argv("psql", "d", "x")
       and tic.RO_ASSERT in tic.ro_argv("psql", "d", "x"))

    # Trigger fixtures: FIRE / INSUFFICIENT / quiet for each.
    now = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)
    fresh = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def shad(**t):
        tot = {f: 0 for f in COUNT_FIELDS}
        tot.update({"n_rows": 13086}, **t)
        return {"generated_at": fresh, "alt3_source": "fixture", "columns": {"claim.claim_text": dict(tot)}, "totals": tot}

    def tel(ok=0, ms=1.0, refusals=(), age_days=1):
        ts = now - dt.timedelta(days=age_days)
        recs = [{"rule": "ok_sample", "scan_ms": m, "table": "claim", "_ts": ts}
                for m in (ms if isinstance(ms, list) else [ms] * ok)]
        for r in refusals:
            rule, b = r[0], r[1]
            rec = {"rule": rule, "batch_size": b, "table": "claim", "_ts": ts}
            if len(r) > 2:
                rec["prose_hint" if rule.startswith("phone") else "asset_code"] = r[2]
            recs.append(rec)
        return recs

    def V(s, t, k, post=False, bl=None, bl_problem=None):
        return evaluate(s, t, now, post_merge=post, baseline=bl, baseline_problem=bl_problem)["triggers"][k]["verdict"]

    quiet_tel = tel(ok=250)
    ck("F1 FIRE (pre-merge): 30/40 alt-3 shadow hits are numeric prose", V(shad(alt3=40, numeric_prose=30), quiet_tel, "F1") == "FIRE")
    ck("F1 INSUFFICIENT (pre-merge): 10/10 numeric prose but n < 30", V(shad(alt3=10, numeric_prose=10), None, "F1") == "INSUFFICIENT")
    ck("F1 INSUFFICIENT (pre-merge) even with telemetry: n_alt3 29 < 30 is no information",
       V(shad(alt3=29, numeric_prose=0), quiet_tel, "F1") == "INSUFFICIENT")
    ck("F1 quiet (pre-merge): 2/40 prose", V(shad(alt3=40, numeric_prose=2), quiet_tel, "F1") == "PASS")
    ck("F1 alt-1 refusals never fire F1, prose_hint or not (correct refusals are not a precision problem)",
       V(shad(), tel(refusals=[("phone_alt1", 1, True)] * 60), "F1", post=True) == "INSUFFICIENT")
    ck("F1 FIRE (post-merge): 12/30 alt-3 refusals carry prose_hint (LB 0.246 > 0.20)",
       V(shad(), tel(refusals=[("phone_alt3", 1, True)] * 12 + [("phone_alt3", 1, False)] * 18), "F1", post=True) == "FIRE")
    ck("F1 quiet (post-merge): 10/30 prose_hint (LB 0.192 <= 0.20)",
       V(shad(), tel(refusals=[("phone_alt3", 1, True)] * 10 + [("phone_alt3", 1, False)] * 20), "F1", post=True) == "PASS")
    ck("F1 INSUFFICIENT (post-merge): 29 alt-3 refusals, even if the shadow leg passes",
       V(shad(alt3=40), tel(refusals=[("phone_alt3", 1, True)] * 29), "F1", post=True) == "INSUFFICIENT")
    ck("F1 leg a is labelled pre-merge shadow only",
       evaluate(shad(alt3=40), None, now)["triggers"]["F1"]["legs"]["a_shadow"]["signal"].startswith("pre-merge shadow only"))
    # F2 (YED-326): a DELTA check against the acknowledged baseline.
    def bl_of(s: dict | None, at: str | None = None, extra: dict | None = None) -> dict:
        cols = {c: {f: v[f] for f in BASELINE_FIELDS} for c, v in (s or shad())["columns"].items()}
        if extra:
            cols.update(extra)
        return {"checked_by": "selftest hand-check", "checked_at": at or now.strftime("%Y-%m-%d"), "columns": cols}

    ck("F2 PASS: counts at the acknowledged baseline", V(shad(), None, "F2", bl=bl_of(shad())) == "PASS")
    ck("F2 PASS: counts below the acknowledged baseline (a fall is not a review)",
       V(shad(loose=3, loose_not_live=0), None, "F2",
         bl=bl_of(None, extra={"claim.claim_text": {"loose_not_live": 5, "bare_digits_10_11": 5}})) == "PASS")
    ck("F2 REVIEW: loose_not_live above the acknowledged count",
       V(shad(loose=2, loose_not_live=2), None, "F2", bl=bl_of(shad())) == "REVIEW")
    ck("F2 REVIEW: bare_digits_10_11 above the acknowledged count",
       V(shad(bare_digits_10_11=1), None, "F2", bl=bl_of(shad())) == "REVIEW")
    two_col = shad()
    two_col["columns"]["documents.title"] = dict(two_col["columns"]["claim.claim_text"])
    ck("F2 REVIEW: a new column appears in the scan", V(two_col, None, "F2", bl=bl_of(shad())) == "REVIEW")
    ck("F2 REVIEW: a baseline column is no longer scanned (the corpus shrank)",
       V(shad(), None, "F2", bl=bl_of(None, extra={"legacy.column": {"loose_not_live": 0, "bare_digits_10_11": 0}})) == "REVIEW")
    ck("F2 INSUFFICIENT: no shadow", V(None, None, "F2") == "INSUFFICIENT")
    ck("F2 REVIEW: a missing baseline file fails loud (never silently QUIET)",
       V(shad(), None, "F2", bl_problem="no baseline file (.claude/references/pii-guard-baseline.json)") == "REVIEW")
    ck("F2 REVIEW: no baseline provided fails loud", V(shad(), None, "F2") == "REVIEW")
    ck("F2 REVIEW body stays counts-only (no column names, local output pointed to)",
       "claim.claim_text" not in render(evaluate(shad(loose_not_live=2), None, now, baseline=bl_of(shad())))
       and "column detail in the run's local output / Linear"
       in render(evaluate(shad(loose_not_live=2), None, now, baseline=bl_of(shad()))))

    # load_baseline: fresh/stale boundary and the malformed-file cases (fail loud).
    with tempfile.TemporaryDirectory() as d:
        def write_bl(name: str, obj) -> str:
            p = os.path.join(d, name)
            with open(p, "w") as f:
                (f.write(obj) if isinstance(obj, str) else json.dump(obj, f))
            return p

        def lb(path: str) -> tuple[dict | None, str | None]:
            return load_baseline(path, now)

        good = {"checked_by": "Alex", "checked_at": now.strftime("%Y-%m-%d"),
                "columns": {"claim.claim_text": {"loose_not_live": 1, "bare_digits_10_11": 0}}}
        d90 = dict(good, checked_at=(now - dt.timedelta(days=90)).strftime("%Y-%m-%d"))
        d91 = dict(good, checked_at=(now - dt.timedelta(days=91)).strftime("%Y-%m-%d"))
        ck("load_baseline: a fresh file loads clean", lb(write_bl("good.json", good)) == (good, None))
        ck("load_baseline: exactly 90 days old is not stale", lb(write_bl("d90.json", d90))[1] is None)
        ck("load_baseline: 91 days is stale -> problem naming the re-baseline rule",
           (lb(write_bl("d91.json", d91))[1] or "").startswith("baseline is stale"))
        ck("load_baseline: missing file -> problem (fail loud)", lb(os.path.join(d, "nope.json"))[1] is not None)
        ck("load_baseline: unparseable JSON -> problem", lb(write_bl("bad.json", "{not json"))[1] is not None)
        ck("load_baseline: non-integer counts rejected",
           lb(write_bl("s.json", dict(good, columns={"claim.claim_text": {"loose_not_live": "3", "bare_digits_10_11": 0}})))[1] is not None)
        ck("load_baseline: a missing count field rejected",
           lb(write_bl("m.json", dict(good, columns={"claim.claim_text": {"loose_not_live": 1}})))[1] is not None)
        ck("load_baseline: negative counts rejected",
           lb(write_bl("n.json", dict(good, columns={"claim.claim_text": {"loose_not_live": -1, "bare_digits_10_11": 0}})))[1] is not None)
        ck("load_baseline: an unreadable checked_at rejected",
           lb(write_bl("t.json", dict(good, checked_at="11/04/2026")))[1] is not None)
        ck("load_baseline: an empty checked_by rejected (a re-baseline needs who)",
           lb(write_bl("w.json", dict(good, checked_by="  ")))[1] is not None)
    ck("F3 FIRE: 3 multi-row refusals in 7d", V(None, tel(ok=1, refusals=[("email", 2)] * 3), "F3") == "FIRE")
    ck("F3 FIRE: one refusal in a 51-row batch", V(None, tel(refusals=[("phone_alt1", 51)]), "F3") == "FIRE")
    ck("F3 INSUFFICIENT: no telemetry", V(None, None, "F3").startswith("INSUFFICIENT"))
    ck("F3 INSUFFICIENT: only records older than 7d", V(None, tel(refusals=[("email", 51)], age_days=8), "F3") == "INSUFFICIENT")
    ck("F3 quiet: 2 multi-row refusals, writes recorded", V(None, tel(ok=3, refusals=[("email", 2)] * 2), "F3") == "PASS")
    ck("F4 FIRE: one LIVE phone hit in prod", V(shad(live=1), None, "F4") == "FIRE")
    ck("F4 FIRE: one non-allowlisted email in prod", V(shad(email=1), None, "F4") == "FIRE")
    ck("F4 INSUFFICIENT: no shadow", V(None, None, "F4") == "INSUFFICIENT")
    ck("F4 quiet: 0 hits on 13,086 rows", V(shad(), None, "F4") == "PASS")
    ck("F5 FIRE: 16/40 email refusals asset-shaped (LB 0.264 > 0.20)",
       V(None, tel(refusals=[("email", 1, True)] * 16 + [("email", 1, False)] * 24), "F5") == "FIRE")
    ck("F5 INSUFFICIENT: 10/10 but n < 30", V(None, tel(refusals=[("email", 1, True)] * 10), "F5") == "INSUFFICIENT")
    ck("F5 quiet: 1/40", V(None, tel(refusals=[("email", 1, True)] + [("email", 1, False)] * 39), "F5") == "PASS")
    ck("F5 INSUFFICIENT in CI (telemetry only)", V(shad(email=40), None, "F5").startswith("INSUFFICIENT"))
    ck("F6 FIRE: p95 60ms over 200 samples", V(None, tel(ok=200, ms=60.0), "F6") == "FIRE")
    ck("F6 INSUFFICIENT: 199 samples at 60ms", V(None, tel(ok=199, ms=60.0), "F6") == "INSUFFICIENT")
    ck("F6 quiet: p95 1ms over 200 samples", V(None, tel(ok=200, ms=1.0), "F6") == "PASS")
    ck("F6 boundary: p95 exactly 50ms is not > 50", V(None, tel(ok=200, ms=50.0), "F6") == "PASS")
    ck("F6 p95 not median: 180 at 1ms + 20 at 60ms fires", V(None, tel(ms=[1.0] * 180 + [60.0] * 20), "F6") == "FIRE")

    # Aggregation, exit codes, staleness, CI labelling, the public body.
    fire = evaluate(shad(live=1, loose_not_live=1), None, now, baseline=bl_of(shad()))
    review = evaluate(shad(loose_not_live=1), None, now, baseline=bl_of(shad()))
    quiet = evaluate(shad(), None, now, no_tel_reason="no telemetry in CI", baseline=bl_of(shad()))
    ck("exit 2 on any FIRE; title names every fired/review trigger",
       fire["exit_code"] == 2 and fire["issue_title"] == "PII guard watcher: FIRE F4 F2")
    ck("exit 3 on REVIEW only", review["exit_code"] == 3 and review["issue_title"] == "PII guard watcher: REVIEW F2")
    ck("exit 0 when nothing fired, INSUFFICIENT included", quiet["exit_code"] == 0 and quiet["issue_title"] == "")
    missing = evaluate(None, None, now)
    stale_s = shad()
    stale_s["generated_at"] = (now - dt.timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale = evaluate(stale_s, None, now)
    ck("missing shadow -> NOT EVALUATED, exit 1 (never QUIET)",
       missing["state"] == "NOT EVALUATED" and missing["exit_code"] == 1 and "NOT EVALUATED" in render(missing))
    ck("shadow older than 8 days -> NOT EVALUATED, exit 1, stale counts unused",
       stale["state"] == "NOT EVALUATED" and stale["exit_code"] == 1 and stale["triggers"]["F4"]["verdict"] == "INSUFFICIENT")
    ck("header shows when the shadow was generated", f"shadow generated {fresh}" in render(quiet))
    ck("CI: telemetry legs say 'INSUFFICIENT (no telemetry in CI)'",
       all(quiet["triggers"][k]["verdict"] == "INSUFFICIENT (no telemetry in CI)" for k in ("F3", "F5", "F6"))
       and quiet["triggers"]["F1"]["legs"]["b_telemetry"]["verdict"] == "INSUFFICIENT (no telemetry in CI)")
    body = render(evaluate({**shad(live=1), "columns": {"doc_chunks.content": shad(live=1)["totals"]}}, None, now,
                           baseline=bl_of(shad())))
    ck("the body carries no shape, raw value or column name; F4 FIRE points to local output",
       not re.search(r"\d{3}[\s.-]\d{3}|@|aaa|999|doc_chunks", body)
       and "column detail in the run's local output / Linear" in body)

    # main(): --no-telemetry wins over a telemetry file that would fire. An explicit fixture baseline,
    # so the suite never depends on the repo baseline's age.
    with tempfile.TemporaryDirectory() as d:
        real_now = dt.datetime.now(dt.timezone.utc)
        sh_path, tel_path, bl_path = os.path.join(d, "shadow.json"), os.path.join(d, "tel.jsonl"), \
            os.path.join(d, "baseline.json")
        with open(sh_path, "w") as f:
            json.dump({**shad(), "generated_at": real_now.strftime("%Y-%m-%dT%H:%M:%SZ")}, f)
        with open(bl_path, "w") as f:
            json.dump({"checked_by": "selftest", "checked_at": real_now.strftime("%Y-%m-%d"),
                       "columns": {"claim.claim_text": {"loose_not_live": 0, "bare_digits_10_11": 0}}}, f)
        with open(tel_path, "w") as f:
            for _ in range(3):
                f.write(json.dumps({"ts": real_now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rule": "email", "batch_size": 2}) + "\n")
        runs = {}
        for flag in ([], ["--no-telemetry"]):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                runs[bool(flag)] = main(["--evaluate", "--shadow-json", sh_path, "--telemetry", tel_path,
                                         "--baseline", bl_path] + flag)
        missing_rc = None
        with contextlib.redirect_stdout(io.StringIO()):
            missing_rc = main(["--evaluate", "--shadow-json", os.path.join(d, "nope.json"), "--no-telemetry",
                               "--baseline", bl_path])
        stale_bl = os.path.join(d, "stale-baseline.json")
        with open(stale_bl, "w") as f:
            json.dump({"checked_by": "selftest", "checked_at": (real_now - dt.timedelta(days=91)).strftime("%Y-%m-%d"),
                       "columns": {"claim.claim_text": {"loose_not_live": 0, "bare_digits_10_11": 0}}}, f)
        stale_rc = None
        with contextlib.redirect_stdout(io.StringIO()):
            stale_rc = main(["--evaluate", "--shadow-json", sh_path, "--no-telemetry", "--baseline", stale_bl])
    ck("main(): the telemetry file fires F3 without --no-telemetry (exit 2) and is ignored with it (exit 0)",
       runs == {False: 2, True: 0})
    ck("main(): a missing shadow file exits 1", missing_rc == 1)
    ck("main(): a stale baseline file is REVIEW (exit 3), never silently QUIET", stale_rc == 3)

    bad = [n for n, ok in results if not ok]
    for n, ok in results:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(results) - len(bad)}/{len(results)} pass")
    return not bad


# --------------------------------------------------------------------------- CLI
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--shadow", action="store_true")
    mode.add_argument("--local-shapes", action="store_true")
    mode.add_argument("--evaluate", action="store_true")
    mode.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=SHADOW_OUT, help="--shadow: where the counts JSON goes")
    ap.add_argument("--shadow-json", default=SHADOW_OUT, help="--evaluate: the --shadow output")
    ap.add_argument("--baseline", default=BASELINE_PATH,
                    help="--evaluate: the acknowledged F2 baseline (.claude/references/pii-guard-baseline.json)")
    ap.add_argument("--telemetry", default=TELEMETRY, help="--evaluate: spine_client's refusal telemetry")
    ap.add_argument("--no-telemetry", action="store_true", help="--evaluate in CI: telemetry legs INSUFFICIENT")
    ap.add_argument("--json-out", help="--evaluate: also write the verdict JSON here")
    ap.add_argument("--body-out", help="--evaluate: also write the counts-only issue body here")
    a = ap.parse_args(argv)

    if a.selftest:
        return 0 if selftest() else 1
    if a.local_shapes:
        return local_shapes()
    if a.shadow:
        data = shadow()
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        print(f"shadow scan (read-only, counts only) — generated {data['generated_at']} — alt-3 source: {data['alt3_source']}")
        print(f"{'column':24} " + " ".join(f"{c[:9]:>9}" for c in COUNT_FIELDS))
        for label, c in list(data["columns"].items()) + [("TOTAL", data["totals"])]:
            print(f"{label:24} " + " ".join(f"{c[f]:>9}" for f in COUNT_FIELDS))
        return 0

    shadow_data = None
    if os.path.exists(a.shadow_json):
        with open(a.shadow_json, encoding="utf-8") as f:
            shadow_data = json.load(f)
    telemetry, reason = None, "no telemetry in CI" if a.no_telemetry else "no telemetry file"
    if not a.no_telemetry and os.path.exists(a.telemetry):
        telemetry, bad = load_telemetry(a.telemetry)
        if bad:
            print(f"note: skipped {bad} unreadable telemetry line(s)", file=sys.stderr)
    now_utc = dt.datetime.now(dt.timezone.utc)
    baseline, baseline_problem = load_baseline(a.baseline, now_utc)
    verdict = evaluate(shadow_data, telemetry, now_utc, no_tel_reason=reason,
                       baseline=baseline, baseline_problem=baseline_problem)
    body = render(verdict)
    print(body)
    print("\nverdict-json: " + json.dumps({k: v for k, v in verdict.items() if k not in ("f4_columns", "f2_columns")},
                                          sort_keys=True))
    if verdict["f4_columns"]:
        print("F4 columns (this run's output only, not the issue): " + ", ".join(verdict["f4_columns"]))
    if verdict.get("f2_columns"):
        print("F2 delta detail (this run's output only, not the issue): " + "; ".join(verdict["f2_columns"]))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=1, sort_keys=True)
    if a.body_out:
        with open(a.body_out, "w", encoding="utf-8") as f:
            f.write(body + "\n")
    return verdict["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
