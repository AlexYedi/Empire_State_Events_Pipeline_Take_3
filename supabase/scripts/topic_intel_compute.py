#!/usr/bin/env python3
"""
topic_intel_compute.py — run (or preview) the live topic-intelligence compute (YED-230 / YED-131).

The compute itself is SQL: topic_intelligence.compute_topic_intelligence() from
supabase/migrations/0012_topic_intelligence_live_compute.sql (the 0008 math, repointed at the
post-swap schemas). This script is the thin driver around it.

  --dry-run (default)  READ-ONLY. Executes the migration file's own trend/pair SELECTs (parsed out
                       of 0012, with the loop variables bound to literals) inside a read-only
                       session, then diffs the result against
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
import os
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


def dry_run(as_of: dt.date) -> bool:
    os.environ["PGOPTIONS"] = (os.environ.get("PGOPTIONS", "") + " -c default_transaction_read_only=on").strip()
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
    os.environ["PGOPTIONS"] = os.environ["PGOPTIONS"].replace("-c default_transaction_read_only=on", "").strip()
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="write (after a clean dry-run gate)")
    ap.add_argument("--dry-run", action="store_true", help="read-only preview + parity diff (default)")
    ap.add_argument("--as-of", type=dt.date.fromisoformat, default=None,
                    help="snapshot date (default: today, UTC — what the nightly run writes)")
    ap.add_argument("--runtime", default="github_actions",
                    choices=["github_actions", "manual"], help="ingestion_run.runtime label for --apply")
    a = ap.parse_args()
    as_of = a.as_of or dt.datetime.now(dt.timezone.utc).date()
    if a.apply and not a.dry_run:
        return apply(as_of, a.runtime)
    return 0 if dry_run(as_of) else 1


if __name__ == "__main__":
    raise SystemExit(main())
