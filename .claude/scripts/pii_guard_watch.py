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
  --local-shapes       Local-only (refuses under CI): shape signatures of the hits, computed in SQL
                       (digit -> 9, letter -> a, <=40 chars), never raw text. For a human looking at F2.
  --evaluate           Reads the shadow JSON + the refusal telemetry (.claude/.state/pii-refusals.jsonl,
                       written by spine_client) and computes triggers F1-F6. Prints a table + a JSON verdict.
                       --no-telemetry (CI) marks the telemetry legs INSUFFICIENT (no telemetry in CI).
  --selftest           Offline fixtures for every trigger at FIRE / INSUFFICIENT / quiet, the Wilson bound,
                       the alternative splitter, the variant patterns, and the counts-only SQL guarantee.

Exit codes: 0 = no trigger fired (PASS or INSUFFICIENT) · 2 = at least one FIRE · 3 = REVIEW only ·
1 = error or selftest failure. INSUFFICIENT means "below the minimum n: no information", never PASS.

Patterns: LIVE is spine_client.PHONE_RE as it stands, read at runtime and passed into the SQL as a
dollar-quoted literal (the DB backstop carries the same text verbatim, so it is valid ARE). ALT3 is
LIVE's third alternative once #277 is merged; until then it is #277's candidate, carried below.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import spine_client as sc  # noqa: E402  (PHONE_RE / EMAIL_RE / split_alternatives / OK_SAMPLE_EVERY)

sys.path.insert(0, os.path.join(ROOT, "supabase", "scripts"))
import topic_intel_compute as tic  # noqa: E402  (the YED-312 read-only guard: ro_q, ro_argv, RO_ASSERT)

SHADOW_OUT = os.path.join(ROOT, ".claude", ".state", "pii-shadow.json")
TELEMETRY = sc.TELEMETRY_PATH

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
# Classifiers, applied in SQL to the FIRST alt-3 / email match in a row (counts only). Postgres-only syntax
# (\m \M word bounds, \uXXXX for the euro / pound / yen signs so the SQL stays ASCII); never compiled in Python.
PROSE_AFTER = (r"[%$\u20ac\u00a3\u00a5]|\m(usd|eur|gbp|k|m|bn|b|x|pp|bps|pts|percent|pct|ms|sec|gb|mb|tb|km|kg"
               r"|users|people|customers)\M")
PROSE_BEFORE = (r"\m(revenue|growth|grew|delta|up|down|shares|users|arr|mrr|yoy|qoq|increase|decrease|rose"
                r"|fell|gain|loss)\M")
ALL_THREES = r"^\+\d{1,3}(?:[\s.]\d{3})+$"
EMAIL_ASSET_CODE = (r"\.(png|jpe?g|gif|svg|webp|ico|css|js|mjs|ts|tsx|py|rb|go|json|ya?ml|toml|md|pdf|mp4|mov"
                    r"|zip|lock)$|@[0-9]+x\.|@[0-9]+(\.[0-9]+)+|^git@|@(example|test|domain|email)\.(com|org|net)$")


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
            "loose": LOOSE_RE, "email": sc.EMAIL_RE.pattern, "email_allow": sc.EMAIL_ALLOWLIST_RE.pattern}


# --------------------------------------------------------------------------- the shadow SQL
# (label, table, text expression). to_jsonb(x) = the whole row as text, every column included.
CORPUS = [
    ("claim.claim_text", "public.claim", "x.claim_text"),
    ("claim.quote", "public.claim", "x.quote"),
    ("claim.metadata", "public.claim", "x.metadata::text"),
    ("documents.title", "public.documents", "x.title"),
    ("documents.metadata", "public.documents", "x.metadata::text"),
    ("person.row", "public.person", "to_jsonb(x)::text"),
    ("company.row", "public.company", "to_jsonb(x)::text"),
    ("event.row", "public.event", "to_jsonb(x)::text"),
    ("topic.row", "public.topic", "to_jsonb(x)::text"),
]
COUNT_FIELDS = ["n_rows", "live", "alt1", "alt2", "alt3", "variant_b", "variant_c", "loose", "loose_not_live",
                "email", "email_asset_code", "numeric_prose"]


def _lit(p: str) -> str:
    if "$re$" in p:
        raise SystemExit("pii_guard_watch: a pattern contains the $re$ quote tag")
    return f"$re$({p})$re$"   # outer group: a top-level | can never escape into the SQL around it


def column_sql(table: str, expr: str, pats: dict) -> str:
    """One read-only query per corpus column. The final SELECT is count(*) aggregates and nothing else."""
    L = {k: _lit(v) for k, v in pats.items() if isinstance(v, str) and k != "alt3_source"}
    conds = [
        None,                                                         # n_rows
        f"t ~ {L['live']}",
        f"t ~ {L['alt1']}",
        f"t ~ {L['alt2']}" if pats["alt2"] else "false",
        "a3m is not null",
        f"t ~ {L['variant_b']}",
        f"t ~ {L['variant_c']}",
        f"t ~ {L['loose']}",
        f"t ~ {L['loose']} and not t ~ {L['live']}",
        "em is not null",
        f"em is not null and em ~* $re${EMAIL_ASSET_CODE}$re$",
        ("a3m is not null and (substr(t, p + length(a3m), 12) ~* $re$" + PROSE_AFTER + "$re$"
         " or substr(t, greatest(p - 20, 1), p - greatest(p - 20, 1)) ~* $re$" + PROSE_BEFORE + "$re$"
         " or a3m ~ $re$" + ALL_THREES + "$re$)"),
    ]
    items = ["count(*)" if c is None else f"count(*) filter (where {c})" for c in conds]
    assert len(items) == len(COUNT_FIELDS)
    return (f"with src as (select {expr} as t from {table} x),\n"
            f"h as (select t, substring(t from {L['alt3']}) as a3m,\n"
            f"  (select m from (select substring(t from {L['email']}) as m) e where not m ~* {L['email_allow']}) as em\n"
            f"  from src where t is not null)\n"
            f"select {', '.join(items)}\n"
            f"from (select h.*, strpos(t, a3m) as p from h) z;")


def final_select_items(sql: str) -> list[str]:
    """The top-level items of the query's output SELECT (what psql prints), for the counts-only check."""
    m = re.search(r"\nselect (.*)\nfrom \(select h\.\*", sql, re.S)
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
    for label, table, expr in CORPUS:
        sql = column_sql(table, expr, pats)
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
    L = {k: _lit(pats[k]) for k in ("alt3", "loose", "live", "email")}

    def mask(key: str) -> str:
        m = f"substring(t from {L[key]})"
        return (f"left(regexp_replace(regexp_replace(regexp_replace({m}, '[[:digit:]]', '9', 'g'), "
                f"'[[:alpha:]]', 'a', 'g'), '[[:space:]]', ' ', 'g'), 40)")

    alt3_where = f"t ~ {L['alt3']}"
    gap_where = f"t ~ {L['loose']} and not t ~ {L['live']}"
    email_where = f"t ~ {L['email']}"
    return (f"with src as (select {expr} as t from {table} x where {expr} is not null)\n"
            f"select 'alt3', {mask('alt3')}, count(*) from src where {alt3_where} group by 2\n"
            f"union all select 'loose_not_live', {mask('loose')}, count(*) from src where {gap_where} group by 2\n"
            f"union all select 'email', {mask('email')}, count(*) from src where {email_where} group by 2\n"
            f"order by 1, 3 desc;")


def local_shapes(run_query=None) -> int:
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        print("pii_guard_watch: --local-shapes never runs in CI (shapes stay on this machine)", file=sys.stderr)
        return 1
    run_query = run_query or tic.ro_q
    pats = patterns()
    for label, table, expr in CORPUS:
        for kind, shape, n in run_query(shapes_sql(table, expr, pats)):
            print(f"{label:20} {kind:15} {n:>6}  {shape}")
    return 0


# --------------------------------------------------------------------------- evaluation
Z95 = 1.959963984540054
F1_MIN_N, F1_PROSE_LB = 30, 0.20           # alt-3 hits; LB(numeric_prose / n_alt3)
F1_WRITE_MIN_N, F1_WRITE_LB = 500, 0.005   # approx writes; LB(phone refusals / writes)
F3_WINDOW_DAYS, F3_MULTI_N, F3_BIG_BATCH = 7, 3, 50
F5_MIN_N, F5_LB = 30, 0.20                 # email hits; LB(asset-or-code-shaped / n)
F6_MIN_N, F6_P95_MS = 200, 50.0            # ok_sample records; p95 scan_ms
PHONE_RULES = ("phone_alt1", "phone_alt2", "phone_alt3", "phone_unlabelled")


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


def evaluate(shadow_data: dict | None, telemetry: list[dict] | None, now: dt.datetime,
             no_tel_reason: str = "no telemetry file") -> dict:
    T = (shadow_data or {}).get("totals")
    scanned = bool(T) and T.get("n_rows", 0) > 0
    no_shadow = "INSUFFICIENT"
    tel_missing = f"INSUFFICIENT ({no_tel_reason})"
    out: dict[str, dict] = {}

    # F1 — alt-3 precision: numeric prose share of alt-3 hits, or the write-refusal rate.
    if not scanned:
        leg_a = _v(no_shadow, "no shadow scan")
    else:
        n, k = T["alt3"], T["numeric_prose"]
        lb = wilson_lb(k, n)
        if n >= F1_MIN_N and lb > F1_PROSE_LB:
            leg_a = _v("FIRE", f"LB(numeric_prose/alt3) {lb:.3f} > {F1_PROSE_LB}", n_alt3=n, numeric_prose=k)
        elif n >= F1_MIN_N:
            leg_a = _v("PASS", f"LB {lb:.3f} <= {F1_PROSE_LB}", n_alt3=n, numeric_prose=k)
        else:
            leg_a = _v("INSUFFICIENT", f"n_alt3 {n} < {F1_MIN_N}", n_alt3=n, numeric_prose=k)
    if telemetry is None:
        leg_b = _v(tel_missing, "write-refusal rate needs session telemetry")
    else:
        oks = sum(1 for r in telemetry if r.get("rule") == "ok_sample")
        refused = sum(1 for r in telemetry if r.get("rule") in PHONE_RULES)
        writes = oks * sc.OK_SAMPLE_EVERY + refused
        lb = wilson_lb(refused, writes)
        approx = f"writes ~= ok_sample x {sc.OK_SAMPLE_EVERY} + refusals (an approximation)"
        if writes >= F1_WRITE_MIN_N and lb > F1_WRITE_LB:
            leg_b = _v("FIRE", f"LB(phone refusals/writes) {lb:.4f} > {F1_WRITE_LB}; {approx}",
                       n_writes=writes, phone_refusals=refused)
        elif writes >= F1_WRITE_MIN_N:
            leg_b = _v("PASS", f"LB {lb:.4f} <= {F1_WRITE_LB}; {approx}", n_writes=writes, phone_refusals=refused)
        else:
            leg_b = _v("INSUFFICIENT", f"n_writes {writes} < {F1_WRITE_MIN_N}; {approx}",
                       n_writes=writes, phone_refusals=refused)
    legs = [leg_a["verdict"], leg_b["verdict"]]
    f1 = "FIRE" if "FIRE" in legs else "PASS" if legs == ["PASS", "PASS"] else "INSUFFICIENT"
    out["F1"] = {"verdict": f1, "signal": "alt-3 precision (numeric prose leg; write-refusal leg)",
                 "legs": {"numeric_prose": leg_a, "write_refusals": leg_b}}

    # F2 — recall: LOOSE finds phone-like text LIVE does not. A human decides, so REVIEW, never FIRE.
    if not scanned:
        out["F2"] = _v(no_shadow, "no shadow scan")
    else:
        gap = T["loose_not_live"]
        out["F2"] = _v("REVIEW" if gap > 0 else "PASS", f"LOOSE-not-LIVE rows {gap}", loose=T["loose"],
                       live=T["live"], loose_not_live=gap)

    # F3 — batch blast radius: refusals that aborted multi-row writes.
    if telemetry is None:
        out["F3"] = _v(tel_missing, "batch refusals need session telemetry")
    else:
        since = now - dt.timedelta(days=F3_WINDOW_DAYS)
        window = [r for r in telemetry if r["_ts"] >= since]
        refusals = [r for r in window if r.get("rule") != "ok_sample"]
        multi = sum(1 for r in refusals if (r.get("batch_size") or 1) > 1)
        big = sum(1 for r in refusals if (r.get("batch_size") or 1) > F3_BIG_BATCH)
        if multi >= F3_MULTI_N or big > 0:
            out["F3"] = _v("FIRE", f"{multi} multi-row refusals (>= {F3_MULTI_N}) or {big} with batch > {F3_BIG_BATCH}",
                           multi_row_refusals_7d=multi, big_batch_refusals_7d=big)
        elif window:
            out["F3"] = _v("PASS", f"{multi} multi-row refusals in {F3_WINDOW_DAYS}d",
                           multi_row_refusals_7d=multi, big_batch_refusals_7d=big)
        else:
            out["F3"] = _v("INSUFFICIENT", f"no guarded writes recorded in {F3_WINDOW_DAYS}d")

    # F4 — bypass: both layers should have refused, so any LIVE hit in prod is a write that skipped the guard.
    if not scanned:
        out["F4"] = _v(no_shadow, "no shadow scan")
    else:
        live_hits = T["live"]
        cols = sorted(c for c, v in shadow_data["columns"].items() if v["live"] > 0)
        out["F4"] = _v("FIRE" if live_hits > 0 else "PASS", f"LIVE hits in prod {live_hits}"
                       + (f" in {', '.join(cols)}" if cols else ""), live=live_hits, rows_scanned=T["n_rows"])

    # F5 — email precision: asset- or code-shaped share of email hits.
    if not scanned:
        out["F5"] = _v(no_shadow, "no shadow scan")
    else:
        n, k = T["email"], T["email_asset_code"]
        lb = wilson_lb(k, n)
        if n >= F5_MIN_N and lb > F5_LB:
            out["F5"] = _v("FIRE", f"LB(asset_or_code/email) {lb:.3f} > {F5_LB}", n_email=n, asset_or_code=k)
        elif n >= F5_MIN_N:
            out["F5"] = _v("PASS", f"LB {lb:.3f} <= {F5_LB}", n_email=n, asset_or_code=k)
        else:
            out["F5"] = _v("INSUFFICIENT", f"n_email {n} < {F5_MIN_N}", n_email=n, asset_or_code=k)

    # F6 — cost: p95 scan time on the sampled success path.
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
    state = "FIRE" if fired else "REVIEW" if review else "QUIET"
    return {"evaluated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "state": state, "fired": fired, "review": review,
            "exit_code": 2 if fired else 3 if review else 0,
            "issue_title": f"PII guard watcher: {state} {' '.join(fired + review)}" if state != "QUIET" else "",
            "alt3_source": (shadow_data or {}).get("alt3_source"),
            "rows_scanned": T.get("n_rows", 0) if T else 0, "triggers": out}


def render(verdict: dict) -> str:
    """Table of verdicts + counts. Never shapes or ids (logs and the public issue body use this)."""
    lines = [f"PII guard watcher — {verdict['evaluated_at']} — state {verdict['state']} "
             f"(rows scanned {verdict['rows_scanned']}; alt-3 source: {verdict['alt3_source']})",
             "", "| # | Verdict | Signal | Counts |", "|---|---|---|---|"]
    for k, v in verdict["triggers"].items():
        if "legs" in v:
            lines.append(f"| {k} | {v['verdict']} | {v['signal']} | |")
            for leg, lv in v["legs"].items():
                lines.append(f"| {k}.{leg} | {lv['verdict']} | {lv['signal']} | {json.dumps(lv['counts'])} |")
        else:
            lines.append(f"| {k} | {v['verdict']} | {v['signal']} | {json.dumps(v['counts'])} |")
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

    # Splitter + derived patterns: on the live 2-alt PHONE_RE and on the #277 3-alt fixture.
    live_parts = sc.split_alternatives(sc.PHONE_RE.pattern)
    ck("splitter: live PHONE_RE parts join back exactly", "|".join(live_parts) == sc.PHONE_RE.pattern)
    fx = sc._FIXTURE_3ALT
    ck("splitter: 3-alt fixture -> 3 parts, joins back exactly",
       len(sc.split_alternatives(fx)) == 3 and "|".join(sc.split_alternatives(fx)) == fx)
    ck("candidate ALT3 == the fixture's third alternative (no paste drift)", sc.split_alternatives(fx)[2] == CANDIDATE_ALT3)
    # explicit 2- and 3-alt inputs, so this holds before AND after #277 merges into the live pattern
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
    # Probe 0 (migration 0017, PR #277): the 15 strings the F1 response re-runs. Expected per full pattern.
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

    # The shadow SQL never outputs raw text; the shapes SQL never runs in CI.
    sqls = [column_sql(t, e, p2) for _, t, e in CORPUS] + [column_sql(t, e, p3) for _, t, e in CORPUS]
    ck("every shadow query's output SELECT is count(*) aggregates only", all(counts_only(s) for s in sqls))
    ck("counts-only check rejects a query that selects text",
       not counts_only(sqls[0].replace("\nselect count(*), ", "\nselect t, count(*), ", 1)))
    ck("counts-only check rejects shape output", not counts_only(sqls[0] + " -- regexp_replace"))
    ck("LIVE regex is passed in verbatim (dollar-quoted)", all(f"$re$({sc.PHONE_RE.pattern})$re$" in column_sql(t, e, pl) for _, t, e in CORPUS))
    ck("shapes SQL masks digits and letters", "'[[:digit:]]', '9'" in shapes_sql("public.claim", "x.quote", p2)
       and "'[[:alpha:]]', 'a'" in shapes_sql("public.claim", "x.quote", p2))
    saved = {k: os.environ.get(k) for k in ("CI", "GITHUB_ACTIONS")}
    os.environ["CI"] = "true"
    ran = []
    import contextlib
    import io
    with contextlib.redirect_stderr(io.StringIO()):
        rc = local_shapes(run_query=lambda q: ran.append(q) or [])
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    ck("--local-shapes refuses under CI and runs no query", rc == 1 and not ran)

    # Shadow parsing: integers only, else fail closed.
    zero = ["0"] * len(COUNT_FIELDS)
    sh = shadow(run_query=lambda q: [["5"] + zero[1:]])
    ck("shadow parses counts and totals them", sh["totals"]["n_rows"] == 5 * len(CORPUS) and sh["totals"]["live"] == 0)
    try:
        shadow(run_query=lambda q: [["5", "+44 20 7946 0958"] + zero[2:]])
        ck("shadow aborts on a non-integer cell", False)
    except SystemExit:
        ck("shadow aborts on a non-integer cell", True)
    ck("the runner is the YED-312 guarded psql (begin read only, assert, rollback)",
       tic.ro_q.__module__ == "topic_intel_compute"
       and tic.ro_argv("psql", "dsn", "select 1")[-1] == "rollback;" and "begin read only;" in tic.ro_argv("psql", "d", "x")
       and tic.RO_ASSERT in tic.ro_argv("psql", "d", "x"))

    # Trigger fixtures: FIRE / INSUFFICIENT / quiet for each.
    now = dt.datetime(2026, 11, 4, 12, tzinfo=dt.timezone.utc)

    def shad(**t):
        tot = {f: 0 for f in COUNT_FIELDS}
        tot.update({"n_rows": 13086}, **t)
        return {"alt3_source": "fixture", "columns": {"claim.claim_text": dict(tot)}, "totals": tot}

    def tel(ok=0, ms=1.0, refusals=(), age_days=1):
        ts = now - dt.timedelta(days=age_days)
        recs = [{"rule": "ok_sample", "scan_ms": ms, "table": "claim", "_ts": ts} for _ in range(ok)]
        recs += [{"rule": r, "batch_size": b, "table": "claim", "_ts": ts} for r, b in refusals]
        return recs

    V = lambda s, t, k: evaluate(s, t, now)["triggers"][k]["verdict"]   # noqa: E731
    quiet_tel = tel(ok=250)
    ck("F1 FIRE: 30/40 alt-3 hits are numeric prose", V(shad(alt3=40, numeric_prose=30), quiet_tel, "F1") == "FIRE")
    ck("F1 INSUFFICIENT: 10/10 numeric prose but n < 30 and no telemetry",
       V(shad(alt3=10, numeric_prose=10), None, "F1") == "INSUFFICIENT")
    ck("F1 INSUFFICIENT even when the write leg passes: n_alt3 29 < 30 is no information, not a pass",
       V(shad(alt3=29, numeric_prose=0), quiet_tel, "F1") == "INSUFFICIENT")
    ck("F1 quiet: 2/40 prose, 0 refusals over ~12,500 writes", V(shad(alt3=40, numeric_prose=2), quiet_tel, "F1") == "PASS")
    ck("F1 FIRE via writes: 20 phone refusals over ~520 writes",
       V(shad(alt3=40, numeric_prose=2), tel(ok=10, refusals=[("phone_alt3", 1)] * 20), "F1") == "FIRE")
    ck("F1 write leg INSUFFICIENT below 500 writes",
       evaluate(shad(), tel(ok=5, refusals=[("phone_alt3", 1)] * 20), now)["triggers"]["F1"]["legs"]
       ["write_refusals"]["verdict"] == "INSUFFICIENT")
    ck("F2 REVIEW: 1 LOOSE-not-LIVE row", V(shad(loose=1, loose_not_live=1), None, "F2") == "REVIEW")
    ck("F2 INSUFFICIENT: no shadow", V(None, None, "F2") == "INSUFFICIENT")
    ck("F2 quiet: 0 gap", V(shad(loose=3, live=0, loose_not_live=0), None, "F2") == "PASS")
    ck("F3 FIRE: 3 multi-row refusals in 7d", V(None, tel(ok=1, refusals=[("email", 2)] * 3), "F3") == "FIRE")
    ck("F3 FIRE: one refusal in a 51-row batch", V(None, tel(refusals=[("phone_alt1", 51)]), "F3") == "FIRE")
    ck("F3 INSUFFICIENT: no telemetry", V(None, None, "F3").startswith("INSUFFICIENT"))
    ck("F3 INSUFFICIENT: only records older than 7d", V(None, tel(refusals=[("email", 51)], age_days=8), "F3") == "INSUFFICIENT")
    ck("F3 quiet: 2 multi-row refusals, writes recorded", V(None, tel(ok=3, refusals=[("email", 2)] * 2), "F3") == "PASS")
    ck("F4 FIRE: one LIVE hit in prod", V(shad(live=1), None, "F4") == "FIRE")
    ck("F4 INSUFFICIENT: no shadow", V(None, None, "F4") == "INSUFFICIENT")
    ck("F4 quiet: 0 LIVE hits on 13,086 rows", V(shad(), None, "F4") == "PASS")
    ck("F5 FIRE: 30/40 emails asset- or code-shaped", V(shad(email=40, email_asset_code=30), None, "F5") == "FIRE")
    ck("F5 INSUFFICIENT: 10/10 but n < 30", V(shad(email=10, email_asset_code=10), None, "F5") == "INSUFFICIENT")
    ck("F5 quiet: 1/40", V(shad(email=40, email_asset_code=1), None, "F5") == "PASS")
    ck("F6 FIRE: p95 60ms over 200 samples", V(None, tel(ok=200, ms=60.0), "F6") == "FIRE")
    ck("F6 INSUFFICIENT: 199 samples at 60ms", V(None, tel(ok=199, ms=60.0), "F6") == "INSUFFICIENT")
    ck("F6 quiet: p95 1ms over 200 samples", V(None, tel(ok=200, ms=1.0), "F6") == "PASS")

    # Aggregation, exit codes, CI labelling, and the public body.
    fire = evaluate(shad(live=1, loose_not_live=1), None, now)
    review = evaluate(shad(loose_not_live=1), None, now)
    quiet = evaluate(shad(), None, now, no_tel_reason="no telemetry in CI")
    ck("exit 2 on any FIRE; title names every fired/review trigger",
       fire["exit_code"] == 2 and fire["issue_title"] == "PII guard watcher: FIRE F4 F2")
    ck("exit 3 on REVIEW only", review["exit_code"] == 3 and review["issue_title"] == "PII guard watcher: REVIEW F2")
    ck("exit 0 when nothing fired, INSUFFICIENT included", quiet["exit_code"] == 0 and quiet["issue_title"] == "")
    ck("CI: telemetry legs say 'INSUFFICIENT (no telemetry in CI)'",
       all(quiet["triggers"][k]["verdict"] == "INSUFFICIENT (no telemetry in CI)" for k in ("F3", "F6"))
       and quiet["triggers"]["F1"]["legs"]["write_refusals"]["verdict"] == "INSUFFICIENT (no telemetry in CI)")
    ck("the body carries no shape and no raw value",
       not re.search(r"\d{3}[\s.-]\d{3}|@|aaa|999", render(fire)) and "F4" in render(fire))

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
        print(f"shadow scan (read-only, counts only) — alt-3 source: {data['alt3_source']}")
        print(f"{'column':20} " + " ".join(f"{c[:9]:>9}" for c in COUNT_FIELDS))
        for label, c in list(data["columns"].items()) + [("TOTAL", data["totals"])]:
            print(f"{label:20} " + " ".join(f"{c[f]:>9}" for f in COUNT_FIELDS))
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
    verdict = evaluate(shadow_data, telemetry, dt.datetime.now(dt.timezone.utc), no_tel_reason=reason)
    body = render(verdict)
    print(body)
    print("\nverdict-json: " + json.dumps(verdict, sort_keys=True))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=1, sort_keys=True)
    if a.body_out:
        with open(a.body_out, "w", encoding="utf-8") as f:
            f.write(body + "\n")
    return verdict["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
