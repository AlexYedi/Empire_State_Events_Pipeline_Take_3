#!/usr/bin/env python3
"""
reference_impl_2b.py
====================
MI Increment 2b — the VALIDATION ORACLE (AC2b.4). Spec §6.

The old gtm snapshot + its Python reference are INVALID oracles post-rewrite (different
substrate). So validation is: (1) an INDEPENDENT reference implementation that recomputes
topic_trend + topic_pair_metric from the canonical_v2 event graph in pure Python — a wholly
different code path than the SQL in 0008 — and requires the SQL output to AGREE row-for-row;
plus (2) structural INVARIANTS (symmetry, no self-pairs, zero-orphan, label/score consistency,
kind isolation). If either fails, the recompute is NOT trusted and the swap does not proceed.

Reads canonical_v2 via psql (Phantom Test Case DB by default; canonical guard blocks prod).
Run AFTER `select canonical_v2.compute_topic_intelligence(<as_of>, 'manual');` has populated
topic_trend/topic_pair_metric. The as_of is read back from the output, so the two sides align.

Usage:  python reference_impl_2b.py           # compare ref-impl vs SQL + run invariants
        python reference_impl_2b.py --verbose # print every mismatch
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys

PSQL_BIN = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")
SPEAKER_ROLES = ("speaker", "host", "panelist")
WINDOWS = [("month", 30), ("week", 7), ("all_time", None)]


# ---------------------------------------------------------------- conn (guard mirrors build_2b)
def _conn_str() -> str:
    host = os.environ.get("TWIN_DB_HOST", "db.ytfzzsxcxxbejnowmkmk.supabase.co")
    port = os.environ.get("TWIN_DB_PORT", "5432")
    user = os.environ.get("TWIN_DB_USER", "postgres")
    name = os.environ.get("TWIN_DB_NAME", "postgres")
    if ("canonical" in host or "oicikjyzmxqfomrrqkvf" in host) and os.environ.get("MI_ALLOW_CANONICAL") != "1":
        sys.exit("REFUSING: target host looks like the Empire prod DB. Validate on the Phantom "
                 "Test Case DB; set MI_ALLOW_CANONICAL=1 only after the rehearsal gate is green.")
    return f"host={host} port={port} user={user} dbname={name} sslmode=require"


def _pgenv() -> dict:
    env = dict(os.environ)
    if "PGPASSWORD" not in env:
        pw = os.environ.get("PHANTOM_TEST_DB_PASSWORD")
        if not pw:
            sys.exit("ERROR: PHANTOM_TEST_DB_PASSWORD (or PGPASSWORD) is not set.")
        env["PGPASSWORD"] = pw
    return env


def q(sql: str) -> list[list[str]]:
    out = subprocess.check_output(
        [PSQL_BIN, _conn_str(), "-tAF", "\t", "-c", sql], env=_pgenv()
    ).decode()
    return [line.split("\t") for line in out.splitlines() if line]


# ---------------------------------------------------------------- load the graph
def load_graph():
    """Everything the compute reads — attended events, their topic tags (rolled to cluster),
       and their speaker set — pulled once, then computed independently in Python."""
    cluster_of = {tid: cid for tid, cid in q(
        "select id::text, cluster_id::text from canonical_v2.topic where cluster_id is not null;")}
    ev_date, ev_kind = {}, {}
    for eid, kind, d in q("select id::text, kind, event_date::date::text from canonical_v2.event;"):
        ev_date[eid] = dt.date.fromisoformat(d) if d else None
        ev_kind[eid] = kind
    # tagged_topic edges (role='tagged_topic', entity_type='topic') on ATTENDED events -> clusters
    event_clusters: dict[str, set] = {}
    for eid, tid in q("select event_id::text, entity_id::text from canonical_v2.event_entity "
                      "where entity_type='topic' and role='tagged_topic';"):
        if ev_kind.get(eid) != "attended":
            continue
        cid = cluster_of.get(tid)
        if cid:
            event_clusters.setdefault(eid, set()).add(cid)
    # speaker set (role in speaker/host/panelist, entity_type='person') on ATTENDED events
    event_speakers: dict[str, set] = {}
    for eid, pid in q("select event_id::text, entity_id::text from canonical_v2.event_entity "
                      "where entity_type='person' and role in ('speaker','host','panelist');"):
        if ev_kind.get(eid) != "attended":
            continue
        event_speakers.setdefault(eid, set()).add(pid)
    return ev_date, event_clusters, event_speakers


def _label(ec, prior, is_all_time):
    if ec < 3:
        return "insufficient_data"
    if is_all_time:
        return "steady"
    if prior == 0:
        return "new"
    m = (ec - prior) / max(prior, 1)
    if m >= 0.5:
        return "heating"
    if m <= -0.5:
        return "cooling"
    return "steady"


# ---------------------------------------------------------------- reference recompute (pure python)
def ref_compute(as_of, ev_date, event_clusters, event_speakers):
    trend, pairs = {}, {}
    for wtype, days in WINDOWS:
        lo = None if days is None else as_of - dt.timedelta(days=days)
        plo = None if days is None else as_of - dt.timedelta(days=2 * days)
        phi = lo
        in_win = [e for e, cs in event_clusters.items()
                  if ev_date.get(e) and (lo is None or ev_date[e] >= lo)]

        # --- trend (per cluster) ---
        cl_events: dict[str, set] = {}
        cl_speakers: dict[str, set] = {}
        for e in in_win:
            for c in event_clusters[e]:
                cl_events.setdefault(c, set()).add(e)
                cl_speakers.setdefault(c, set()).update(event_speakers.get(e, set()))
        prior_events: dict[str, set] = {}
        if days is not None:
            for e, cs in event_clusters.items():
                d = ev_date.get(e)
                if d and plo <= d < phi:
                    for c in cs:
                        prior_events.setdefault(c, set()).add(e)
        for c, evs in cl_events.items():
            ec = len(evs)
            prior = len(prior_events.get(c, set())) if days is not None else None
            trend[(c, wtype)] = {
                "event_count": ec,
                "distinct_speaker_count": len(cl_speakers.get(c, set())),
                "prior_event_count": prior,
                "trend_label": _label(ec, prior or 0, days is None),
                "is_low_confidence": (ec < 3) or (wtype == "week"),
            }

        # --- pairs (co-occurrence + bridges) ---
        cooc: dict[tuple, set] = {}
        for e in in_win:
            cs = sorted(event_clusters[e])
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    cooc.setdefault((cs[i], cs[j]), set()).add(e)
        # speaker -> {(cluster, event)} within window, for the two-distinct-events bridge rule
        spk_ce: dict[str, set] = {}
        for e in in_win:
            for c in event_clusters[e]:
                for p in event_speakers.get(e, set()):
                    spk_ce.setdefault(p, set()).add((c, e))
        bridges: dict[tuple, set] = {}
        for p, ces in spk_ce.items():
            by_cluster: dict[str, set] = {}
            for c, e in ces:
                by_cluster.setdefault(c, set()).add(e)
            cls = sorted(by_cluster)
            for i in range(len(cls)):
                for j in range(i + 1, len(cls)):
                    a, b = cls[i], cls[j]
                    # genuine bridge: p speaks at some A-event and some DIFFERENT B-event
                    # (two distinct events — a single dual-tagged event is co-occurrence, not a bridge)
                    if any(ea != eb for ea in by_cluster[a] for eb in by_cluster[b]):
                        bridges.setdefault((a, b), set()).add(p)
        # all-time first co-occurrence date (novelty)
        atf: dict[tuple, dt.date] = {}
        for e, cs in event_clusters.items():
            d = ev_date.get(e)
            if not d:
                continue
            sc = sorted(cs)
            for i in range(len(sc)):
                for j in range(i + 1, len(sc)):
                    key = (sc[i], sc[j])
                    if key not in atf or d < atf[key]:
                        atf[key] = d
        for key in set(cooc) | set(bridges):
            cnt = len(cooc.get(key, set()))
            bcnt = len(bridges.get(key, set()))
            first = atf.get(key)
            is_new = bool(days is not None and first is not None and first >= lo)
            pairs[(key[0], key[1], wtype)] = {
                "cooccurrence_event_count": cnt,
                "bridge_person_count": bcnt,
                "intersection_score": cnt + 2 * bcnt + (2 if is_new else 0),
                "is_new_pair": is_new,
                "first_cooccurred_on": first.isoformat() if first else None,
            }
    return trend, pairs


# ---------------------------------------------------------------- read SQL output
def read_sql_output(as_of_str):
    trend = {}
    for cid, w, ec, sc, pc, lab, low in q(
        "select subject_id::text, window_type, event_count, distinct_speaker_count, "
        "coalesce(prior_event_count::text,''), trend_label, is_low_confidence "
        f"from canonical_v2.topic_trend where as_of_date='{as_of_str}' and subject_level='cluster';"):
        trend[(cid, w)] = {
            "event_count": int(ec), "distinct_speaker_count": int(sc),
            "prior_event_count": (int(pc) if pc else None),
            "trend_label": lab, "is_low_confidence": (low == "t"),
        }
    pairs = {}
    for a, b, w, cnt, bcnt, score, isnew, first in q(
        "select subject_a_id::text, subject_b_id::text, window_type, cooccurrence_event_count, "
        "bridge_person_count, intersection_score, is_new_pair, coalesce(first_cooccurred_on::text,'') "
        f"from canonical_v2.topic_pair_metric where as_of_date='{as_of_str}' and subject_level='cluster';"):
        pairs[(a, b, w)] = {
            "cooccurrence_event_count": int(cnt), "bridge_person_count": int(bcnt),
            "intersection_score": int(float(score)), "is_new_pair": (isnew == "t"),
            "first_cooccurred_on": (first or None),
        }
    return trend, pairs


# ---------------------------------------------------------------- structural invariants (SQL)
def invariants(as_of_str):
    checks = {
        "pair canonical order (a<b, no self-pair)":
            "select count(*) from canonical_v2.topic_pair_metric where subject_a_id >= subject_b_id;",
        "bridge_count == cardinality(array)":
            "select count(*) from canonical_v2.topic_pair_metric "
            "where bridge_person_count <> cardinality(bridge_entity_ids);",
        "trend subject resolves to a cluster (zero-orphan)":
            "select count(*) from canonical_v2.topic_trend tt where not exists "
            "(select 1 from canonical_v2.topic_cluster c where c.cluster_id=tt.subject_id);",
        "pair subjects resolve to clusters (zero-orphan)":
            "select count(*) from canonical_v2.topic_pair_metric pm where "
            "not exists (select 1 from canonical_v2.topic_cluster c where c.cluster_id=pm.subject_a_id) "
            "or not exists (select 1 from canonical_v2.topic_cluster c where c.cluster_id=pm.subject_b_id);",
        "conservation: every trend cluster has >=1 attended tagged event":
            "select count(*) from canonical_v2.topic_trend tt where tt.window_type='all_time' "
            "and not exists (select 1 from canonical_v2.event_entity ee "
            "  join canonical_v2.event e on e.id=ee.event_id "
            "  join canonical_v2.topic t on t.id=ee.entity_id "
            "  where ee.entity_type='topic' and ee.role='tagged_topic' and e.kind='attended' "
            "    and t.cluster_id=tt.subject_id);",
        "kind isolation: no trend row derives from a non-attended-only cluster":
            "select count(*) from canonical_v2.topic_trend tt where tt.window_type='all_time' "
            "and tt.event_count > (select count(distinct e.id) from canonical_v2.event_entity ee "
            "  join canonical_v2.event e on e.id=ee.event_id "
            "  join canonical_v2.topic t on t.id=ee.entity_id "
            "  where ee.entity_type='topic' and ee.role='tagged_topic' and e.kind='attended' "
            "    and t.cluster_id=tt.subject_id);",
        "intersection_score == cooc + 2*bridge + 2*novelty":
            "select count(*) from canonical_v2.topic_pair_metric where intersection_score <> "
            "cooccurrence_event_count + 2*bridge_person_count + (case when is_new_pair then 2 else 0 end);",
        "is_low_confidence == (event_count<3 or week)":
            "select count(*) from canonical_v2.topic_trend where is_low_confidence <> "
            "((event_count < 3) or (window_type='week'));",
    }
    fails = []
    for label, sql in checks.items():
        n = int(q(sql)[0][0])
        print(f"  [{'PASS' if n == 0 else 'FAIL'}] {label}" + ("" if n == 0 else f"  ({n} violations)"))
        if n:
            fails.append(label)
    return fails


# ---------------------------------------------------------------- compare
def compare(ref, sql, grain, keys, verbose):
    mism = 0
    allk = set(ref) | set(sql)
    for k in sorted(allk):
        r, s = ref.get(k), sql.get(k)
        if r is None:
            mism += 1
            if verbose: print(f"    {grain} {k}: in SQL, MISSING from reference")
            continue
        if s is None:
            mism += 1
            if verbose: print(f"    {grain} {k}: in reference, MISSING from SQL")
            continue
        for f in keys:
            if r.get(f) != s.get(f):
                mism += 1
                if verbose: print(f"    {grain} {k}.{f}: ref={r.get(f)} sql={s.get(f)}")
    return mism


def main() -> int:
    ap = argparse.ArgumentParser(description="Increment 2b validation oracle (AC2b.4).")
    ap.add_argument("--verbose", action="store_true", help="print every mismatch")
    args = ap.parse_args()

    rows = q("select max(as_of_date)::text from canonical_v2.topic_trend;")
    as_of_str = rows[0][0] if rows and rows[0][0] else ""
    if not as_of_str:
        sys.exit("ERROR: canonical_v2.topic_trend is empty — run "
                 "select canonical_v2.compute_topic_intelligence(current_date,'manual'); first.")
    as_of = dt.date.fromisoformat(as_of_str)
    print(f"Validating canonical_v2 as of {as_of_str}\n")

    ev_date, ev_clusters, ev_speakers = load_graph()
    ref_trend, ref_pairs = ref_compute(as_of, ev_date, ev_clusters, ev_speakers)
    sql_trend, sql_pairs = read_sql_output(as_of_str)

    print("Reference-impl vs SQL agreement:")
    t_mis = compare(ref_trend, sql_trend, "trend", (
        "event_count", "distinct_speaker_count", "prior_event_count",
        "trend_label", "is_low_confidence"), args.verbose)
    p_mis = compare(ref_pairs, sql_pairs, "pair", (
        "cooccurrence_event_count", "bridge_person_count",
        "intersection_score", "is_new_pair", "first_cooccurred_on"), args.verbose)
    print(f"  trend rows: ref={len(ref_trend)} sql={len(sql_trend)} mismatches={t_mis}")
    print(f"  pair  rows: ref={len(ref_pairs)} sql={len(sql_pairs)} mismatches={p_mis}")

    print("\nStructural invariants:")
    fails = invariants(as_of_str)

    ok = (t_mis == 0 and p_mis == 0 and not fails)
    print("\n" + ("✅ PASS — SQL agrees with the independent reference impl; all invariants hold."
                  if ok else "❌ FAIL — do NOT swap. Investigate the mismatches/violations above "
                             "(re-run with --verbose)."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
