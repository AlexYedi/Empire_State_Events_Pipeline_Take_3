#!/usr/bin/env python3
"""
topic_intel_compute.py — run (or preview) the live topic-intelligence compute (YED-230 / YED-131).

The compute itself is SQL: topic_intelligence.compute_topic_intelligence() from
supabase/migrations/0012_topic_intelligence_live_compute.sql (the 0008 math, repointed at the
post-swap schemas). This script is the thin driver around it.

  --dry-run (default)  READ-ONLY. Executes the migration file's own trend/pair SELECTs (parsed out
                       of 0012, with the loop variables bound to literals), each query in its own
                       BEGIN READ ONLY transaction whose read-only state is asserted before the
                       query runs (fail closed; see "read-only guard"), then diffs the result against
                         (a) healthcheck_2b.py's independent Python reference  <- the acceptance gate
                         (b) the stored topic_intelligence snapshot            <- informational
                       Works BEFORE 0012 is applied (it never calls the function). No writes.
  --apply              Runs the dry-run gate first; only if it is clean (0 mismatches vs the
                       reference) does it `set role pipeline_writer` and call the function.
                       Requires 0012 to be applied.

Exit 0 = clean (dry-run) / written (apply). Non-zero = mismatch, or the write failed.

Env: MI_DB_DSN (libpq conninfo/URI), optional PSQL_BIN — the same as healthcheck_2b.py, whose
     psql wrapper and reference implementation are imported so the two can never drift apart.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIGRATION = HERE.parent / "migrations" / "0012_topic_intelligence_live_compute.sql"
sys.path.insert(0, str(HERE))
import healthcheck_2b as hc  # noqa: E402  (shared psql wrapper + reference recompute + comparator)

TREND_FIELDS = ("event_count", "distinct_speaker_count", "prior_event_count", "trend_label", "is_low_confidence")
PAIR_FIELDS = ("cooccurrence_event_count", "bridge_person_count", "intersection_score", "is_new_pair",
               "first_cooccurred_on")


# ------------------------------------------------------------------ parse the migration's SELECTs
def migration_selects() -> dict[str, tuple[list[str], str]]:
    """{table: (insert column list, SELECT text)} straight out of 0012's function body."""
    sql = MIGRATION.read_text()
    body = sql[sql.index("as $fn$") + len("as $fn$"): sql.rindex("$fn$;")]
    body = re.sub(r"--[^\n]*", "", body)  # strip comments so nothing in prose can confuse the parse
    out = {}
    for m in re.finditer(r"insert into topic_intelligence\.(topic_trend|topic_pair_metric)\s*\((.*?)\)\s*(with .*?);",
                         body, re.S):
        cols = [c.strip() for c in m.group(2).split(",")]
        out[m.group(1)] = (cols, m.group(3))
    if set(out) != {"topic_trend", "topic_pair_metric"}:
        sys.exit(f"ERROR: could not parse both compute SELECTs out of {MIGRATION.name} (got {sorted(out)})")
    return out


def bind(select: str, as_of: dt.date, window_type: str, days: int | None) -> str:
    """Bind the plpgsql loop variables exactly as the function's FOR loop does."""
    lit = {
        r"\bw\.window_type\b": f"'{window_type}'::text",
        r"\bw\.days\b": "null::int" if days is None else f"{days}::int",
        r"\bp_as_of\b": f"'{as_of.isoformat()}'::date",
        r"\bv_run_id\b": "null::uuid",
    }
    for pat, val in lit.items():
        select = re.sub(pat, val, select)
    return select


def preview(as_of: dt.date):
    """Run the migration's SELECTs read-only; return (trend, pairs, problems) in healthcheck's shape."""
    sels = migration_selects()
    trend, pairs, problems = {}, {}, []
    for wtype, days in hc.WINDOWS:
        cols, sel = sels["topic_trend"]
        for r in hc.q(f"select subject_id::text, window_type, event_count, distinct_speaker_count, "
                      f"coalesce(prior_event_count::text,''), trend_label, is_low_confidence, content_hash "
                      f"from ({bind(sel, as_of, wtype, days)}) x({', '.join(cols)});"):
            cid, w, ec, sc, pc, lab, low, h = r
            if (cid, w) in trend:
                problems.append(f"duplicate trend key {(cid, w)}")
            if not h:
                problems.append(f"empty content_hash on trend {(cid, w)}")
            trend[(cid, w)] = {"event_count": int(ec), "distinct_speaker_count": int(sc),
                               "prior_event_count": int(pc) if pc else None,
                               "trend_label": lab, "is_low_confidence": low == "t"}
        cols, sel = sels["topic_pair_metric"]
        # first_cooccurred_on is a DATE column: ::date mirrors the INSERT's assignment cast.
        for r in hc.q(f"select subject_a_id::text, subject_b_id::text, window_type, cooccurrence_event_count, "
                      f"bridge_person_count, intersection_score, is_new_pair, "
                      f"coalesce(first_cooccurred_on::date::text,''), cardinality(bridge_entity_ids) "
                      f"from ({bind(sel, as_of, wtype, days)}) x({', '.join(cols)});"):
            a, b, w, cnt, bcnt, score, isnew, first, card = r
            if (a, b, w) in pairs:
                problems.append(f"duplicate pair key {(a, b, w)}")
            if not a < b:
                problems.append(f"pair order violated {(a, b)}")
            if int(bcnt) != int(card):
                problems.append(f"bridge count != cardinality on {(a, b, w)}")
            pairs[(a, b, w)] = {"cooccurrence_event_count": int(cnt), "bridge_person_count": int(bcnt),
                                "intersection_score": int(float(score)), "is_new_pair": isnew == "t",
                                "first_cooccurred_on": first or None}
    return trend, pairs, problems


# ------------------------------------------------------------------ read-only guard (YED-312)
# Why not PGOPTIONS / SET SESSION: the Supabase pooler (Supavisor, session or transaction mode) does
# not reliably pass startup PGOPTIONS through, and a pooled backend outlives our client, so a
# SESSION-level setting may not apply and could leak onto a backend another client reuses.
# How the script connects decides the fix: hc.q() spawns one psql process (= one connection) per
# query, so there is no shared session to guard once. Instead every dry-run query runs as
#   BEGIN READ ONLY -> SHOW transaction_read_only -> server-side assert -> the SELECT -> ROLLBACK
# inside ONE explicit transaction on ONE connection. A transaction stays on one backend under either
# pooler mode, so the setting we SHOW is the setting the SELECT runs under. What each layer does:
#   1. BEGIN READ ONLY + the DO assert PREVENT writes: the server rejects any write in a read-only
#      txn, and the assert raises before the SELECT if the txn is somehow not read-only
#      (ON_ERROR_STOP makes psql stop there).
#   2. ROLLBACK UNDOES anything that slipped through, whatever SHOW said; a preview commits nothing.
#   3. read_only_verdict() in Python BLOCKS results that are not proven read-only: anything but 'on'
#      as the first output line aborts the run (fail closed) and the rows are discarded.
RO_ASSERT = ("do $$ begin if current_setting('transaction_read_only') <> 'on' then "
             "raise exception 'YED-312 read-only guard: transaction_read_only=%', "
             "current_setting('transaction_read_only'); end if; end $$;")


def read_only_verdict(show_value) -> bool:
    """Pure guard: proceed only if SHOW transaction_read_only returned exactly 'on'."""
    return isinstance(show_value, str) and show_value.strip() == "on"


def ro_argv(psql_bin: str, dsn: str, sql: str) -> list[str]:
    """psql argv for one guarded query. Explicit BEGIN keeps every -c in the same transaction."""
    return [psql_bin, dsn, "-X", "-q", "-tA", "-F", "\t", "-v", "ON_ERROR_STOP=1",
            "-c", "begin read only;",
            "-c", "show transaction_read_only;",
            "-c", RO_ASSERT,
            "-c", sql,
            "-c", "rollback;"]  # a preview has nothing to keep; rollback undoes anything that slipped through


def split_guarded(stdout: str) -> tuple[str | None, list[list[str]]]:
    """First output line is the SHOW value; the rest are the query's rows (hc.q's shape)."""
    lines = [line for line in stdout.splitlines() if line]
    if not lines:
        return None, []
    return lines[0], [line.split("\t") for line in lines[1:]]


def ro_q(sql: str) -> list[list[str]]:
    """Drop-in for hc.q during the dry run: same rows, but only from a verified read-only txn."""
    out = subprocess.run(ro_argv(hc.PSQL_BIN, hc._dsn(), sql), capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"ERROR: dry-run query failed or the read-only guard tripped — aborting, nothing run "
                 f"outside a read-only transaction.\n{out.stderr.strip()}")
    show, rows = split_guarded(out.stdout)
    if not read_only_verdict(show):
        sys.exit(f"ERROR: read-only guard: SHOW transaction_read_only returned {show!r}, not 'on'. "
                 "Aborting the dry run (fail closed); its results are discarded.")
    return rows


def dry_run(as_of: dt.date) -> bool:
    # Every hc.q call below (preview, load_graph, read_sql_output) is routed through ro_q for the
    # duration of the dry run only; restored in `finally` so --apply's write never inherits it.
    real_q, hc.q = hc.q, ro_q
    try:
        return _dry_run(as_of)
    finally:
        hc.q = real_q


def _dry_run(as_of: dt.date) -> bool:
    print(f"topic-intel compute DRY RUN (read-only) — as_of {as_of}  [source: {MIGRATION.name}]\n")

    port_t, port_p, problems = preview(as_of)
    ev_date, ev_clusters, ev_speakers = hc.load_graph()
    ref_t, ref_p = hc.ref_compute(as_of, ev_date, ev_clusters, ev_speakers)

    print("(a) ported SQL vs healthcheck reference — ACCEPTANCE (must be 0):")
    t_mis = hc.compare(ref_t, port_t, "trend", TREND_FIELDS)
    p_mis = hc.compare(ref_p, port_p, "pair", PAIR_FIELDS)
    print(f"  trend: ref={len(ref_t)} port={len(port_t)} mismatches={t_mis}")
    print(f"  pair : ref={len(ref_p)} port={len(port_p)} mismatches={p_mis}")
    for p in problems:
        print(f"  [FAIL] {p}")

    rows = hc.q(f"select coalesce(max(as_of_date)::text,'') from {hc.TT};")
    stored_as_of = rows[0][0] if rows else ""
    print(f"\n(b) ported SQL vs STORED snapshot (as_of {stored_as_of or 'none'}) — informational, what a write changes:")
    if stored_as_of:
        st_t, st_p = hc.read_sql_output(stored_as_of)
        for name, port, st in (("trend", port_t, st_t), ("pair", port_p, st_p)):
            added, dropped = set(port) - set(st), set(st) - set(port)
            changed = sum(1 for k in set(port) & set(st) if port[k] != st[k])
            print(f"  {name}: stored={len(st)} new={len(port)}  +{len(added)} added  -{len(dropped)} gone  "
                  f"~{changed} changed")

    ok = t_mis == 0 and p_mis == 0 and not problems
    print("\n" + ("✅ PARITY — the ported compute reproduces the health-check reference exactly."
                  if ok else "❌ MISMATCH — do not write; the port and the reference disagree."))
    return ok


def apply(as_of: dt.date, runtime: str) -> int:
    if not dry_run(as_of):
        print("REFUSING to write: dry-run gate is not clean.")
        return 1
    print(f"\nWriting via pipeline_writer: compute_topic_intelligence('{as_of}', '{runtime}') …")
    out = subprocess.run(
        [hc.PSQL_BIN, hc._dsn(), "-v", "ON_ERROR_STOP=1", "-tA",
         "-c", "set role pipeline_writer;",
         "-c", f"select topic_intelligence.compute_topic_intelligence('{as_of.isoformat()}'::date, '{runtime}');"],
        capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stderr.strip() or "psql failed")
        return 1
    print(f"  ingestion_run {out.stdout.strip().splitlines()[-1]} — success")
    return 0


def selftest() -> int:
    """Offline check of the read-only guard (stdlib only, never touches a DB)."""
    fails = []

    def check(name, cond):
        print(f"  [{'ok' if cond else 'FAIL'}] {name}")
        if not cond:
            fails.append(name)

    for val, want in (("on", True), ("on\n", True), ("off", False), ("", False), (None, False),
                      ("ON", False), ("true", False), ("garbage", False), ("on off", False)):
        check(f"verdict({val!r}) -> {'proceed' if want else 'abort'}", read_only_verdict(val) is want)

    show, rows = split_guarded("on\nabc\t1\n\nxyz\t2\n")
    check("split: SHOW line separated from rows", show == "on" and rows == [["abc", "1"], ["xyz", "2"]])
    check("split: empty output -> no SHOW value (abort)", split_guarded("") == (None, []))
    check("split: SHOW-only output -> zero rows", split_guarded("on\n") == ("on", []))

    argv = ro_argv("psql", "dsn", "select 1;")
    cmds = [argv[i + 1] for i, a in enumerate(argv) if a == "-c"]
    check("argv: begin read only -> show -> assert -> query -> rollback",
          cmds == ["begin read only;", "show transaction_read_only;", RO_ASSERT, "select 1;", "rollback;"])
    check("argv: final command is rollback;", cmds[-1] == "rollback;")
    check("argv: ON_ERROR_STOP set (assert halts before the query)", "ON_ERROR_STOP=1" in argv)
    check("argv: no session-level setting (pooler-safe)", not any("session" in c.lower() for c in cmds))
    check("RO_ASSERT: raises when transaction_read_only <> 'on'",
          "current_setting('transaction_read_only') <> 'on'" in RO_ASSERT and "raise exception" in RO_ASSERT)

    # ro_q wiring: fake psql via subprocess.run. hc.q and subprocess.check_output are booby-trapped
    # so a ro_q that bypasses the guard goes red instead of reaching a real psql/DB.
    def bypass(*_a, **_k):
        raise AssertionError("ro_q bypassed the guard")

    real_run, real_co, real_dsn, real_hq = subprocess.run, subprocess.check_output, hc._dsn, hc.q
    hc._dsn, hc.q, subprocess.check_output = (lambda: "dsn"), bypass, bypass

    def ro_q_with(returncode, stdout):
        subprocess.run = lambda argv, **_k: subprocess.CompletedProcess(argv, returncode, stdout, "boom")
        try:
            return "rows", ro_q("select 1;")
        except SystemExit as e:
            return "exit", e.code
        except AssertionError as e:
            return "bypass", str(e)

    try:
        # SHOW said 'on' and partial rows printed, then psql failed: only the returncode check catches it.
        kind, val = ro_q_with(3, "on\nabc\t1\n")
        check("ro_q: psql returncode 3 (even after SHOW 'on') -> exits non-zero",
              kind == "exit" and val not in (0, None))
        for first in ("off", "BEGIN", ""):
            kind, val = ro_q_with(0, f"{first}\nabc\t1\n")
            check(f"ro_q: first line {first!r} -> exits non-zero", kind == "exit" and val not in (0, None))
        kind, val = ro_q_with(0, "on\nabc\t1\nxyz\t2\n")
        check("ro_q: 'on' + rows -> returns only the rows",
              kind == "rows" and val == [["abc", "1"], ["xyz", "2"]])
    finally:
        subprocess.run, subprocess.check_output, hc._dsn, hc.q = real_run, real_co, real_dsn, real_hq

    # Swap the real body for a probe that reports which q it sees; no query is issued.
    global _dry_run
    real_body, real_q = _dry_run, hc.q
    _dry_run = lambda as_of: hc.q is ro_q  # noqa: E731
    try:
        check("dry_run routes every hc.q call through ro_q", dry_run(dt.date(2026, 1, 1)) is True)
        check("dry_run restores hc.q afterwards (--apply does not inherit the guard)", hc.q is real_q)
    finally:
        _dry_run, hc.q = real_body, real_q

    print(f"\nselftest: {'PASS' if not fails else f'FAIL ({len(fails)})'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true", help="offline check of the read-only guard; no DB")
    ap.add_argument("--apply", action="store_true", help="write (after a clean dry-run gate)")
    ap.add_argument("--dry-run", action="store_true", help="read-only preview + parity diff (default)")
    ap.add_argument("--as-of", type=dt.date.fromisoformat, default=None,
                    help="snapshot date (default: today, UTC — what the nightly run writes)")
    ap.add_argument("--runtime", default="github_actions",
                    choices=["github_actions", "manual"], help="ingestion_run.runtime label for --apply")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    as_of = a.as_of or dt.datetime.now(dt.timezone.utc).date()
    if a.apply and not a.dry_run:
        return apply(as_of, a.runtime)
    return 0 if dry_run(as_of) else 1


if __name__ == "__main__":
    raise SystemExit(main())
