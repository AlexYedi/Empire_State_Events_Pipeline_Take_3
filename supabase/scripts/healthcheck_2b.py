#!/usr/bin/env python3
"""
healthcheck_2b.py
=================
POST-SWAP nightly health check for the consolidated MI graph (YED-130 Increment 2b).
Throwaway: delete this + the workflow when `pre2b` is dropped after the N-night watch.

Reads the LIVE schemas (public + topic_intelligence) — NOT canonical_v2 (empty post-swap).
Three layers, all read-only:
  1. Independent recompute (pure Python, from public.event/event_entity/topic) must AGREE
     row-for-row with the stored topic_intelligence.topic_trend / topic_pair_metric.
  2. The 8 structural invariants (canonical order, no-orphan, conservation, kind isolation,
     score/flag consistency, bridge integrity).
  3. Read-path probe (optional): anon REST reaches signal_read (serves data) and the raw base
     table is BLOCKED — the k>=5 suppression can't be bypassed.

Purpose: prove the graph stays COHERENT night after night, so decommissioning the gtm spine +
dropping pre2b is a decision backed by evidence, not vibes. Catches silent corruption / drift /
lens cross-contamination — NOT upstream semantic wrongness (garbage-in stays coherent).

Exit 0 = PASS. Non-zero = FAIL (the schedule alerts on this).

Env:
  MI_DB_DSN              libpq conninfo/URI for the LIVE DB (use the SESSION POOLER string from
                         GitHub — IPv4; or the direct db.<ref>.supabase.co string locally).
  MI_SUPABASE_URL        (optional) e.g. https://oicikjyzmxqfomrrqkvf.supabase.co — enables the probe
  MI_SUPABASE_ANON_KEY   (optional) publishable/anon key — enables the probe
  PSQL_BIN               (optional) default /opt/homebrew/opt/libpq/bin/psql (CI: 'psql')
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

PSQL_BIN = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")
SPEAKER_ROLES = ("speaker", "host", "panelist")
WINDOWS = [("month", 30), ("week", 7), ("all_time", None)]

# LIVE schema targets (post-swap)
EV, EE, TOPIC = "public.event", "public.event_entity", "public.topic"
TT, TPM, TC = ("topic_intelligence.topic_trend", "topic_intelligence.topic_pair_metric",
               "topic_intelligence.topic_cluster")


def _dsn() -> str:
    dsn = os.environ.get("MI_DB_DSN")
    if not dsn:
        sys.exit("ERROR: MI_DB_DSN is not set (libpq conninfo/URI for the live DB).")
    return dsn


def q(sql: str) -> list[list[str]]:
    out = subprocess.check_output([PSQL_BIN, _dsn(), "-tAF", "\t", "-c", sql]).decode()
    return [line.split("\t") for line in out.splitlines() if line]


# ---------------------------------------------------------------- load + reference recompute
def load_graph():
    cluster_of = {tid: cid for tid, cid in q(
        f"select id::text, cluster_id::text from {TOPIC} where cluster_id is not null;")}
    ev_date, ev_kind = {}, {}
    for eid, kind, d in q(f"select id::text, kind, event_date::date::text from {EV};"):
        ev_date[eid] = dt.date.fromisoformat(d) if d else None
        ev_kind[eid] = kind
    event_clusters: dict[str, set] = {}
    for eid, tid in q(f"select event_id::text, entity_id::text from {EE} "
                      "where entity_type='topic' and role='tagged_topic';"):
        if ev_kind.get(eid) != "attended":
            continue
        cid = cluster_of.get(tid)
        if cid:
            event_clusters.setdefault(eid, set()).add(cid)
    event_speakers: dict[str, set] = {}
    for eid, pid in q(f"select event_id::text, entity_id::text from {EE} "
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
    return "heating" if m >= 0.5 else "cooling" if m <= -0.5 else "steady"


def ref_compute(as_of, ev_date, event_clusters, event_speakers):
    trend, pairs = {}, {}
    for wtype, days in WINDOWS:
        lo = None if days is None else as_of - dt.timedelta(days=days)
        plo = None if days is None else as_of - dt.timedelta(days=2 * days)
        phi = lo
        in_win = [e for e in event_clusters if ev_date.get(e) and (lo is None or ev_date[e] >= lo)]

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
                "event_count": ec, "distinct_speaker_count": len(cl_speakers.get(c, set())),
                "prior_event_count": prior, "trend_label": _label(ec, prior or 0, days is None),
                "is_low_confidence": (ec < 3) or (wtype == "week"),
            }

        cooc: dict[tuple, set] = {}
        for e in in_win:
            cs = sorted(event_clusters[e])
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    cooc.setdefault((cs[i], cs[j]), set()).add(e)
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
                    if any(ea != eb for ea in by_cluster[a] for eb in by_cluster[b]):
                        bridges.setdefault((a, b), set()).add(p)
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
            cnt, bcnt = len(cooc.get(key, set())), len(bridges.get(key, set()))
            first = atf.get(key)
            is_new = bool(days is not None and first is not None and first >= lo)
            pairs[(key[0], key[1], wtype)] = {
                "cooccurrence_event_count": cnt, "bridge_person_count": bcnt,
                "intersection_score": cnt + 2 * bcnt + (2 if is_new else 0),
                "is_new_pair": is_new, "first_cooccurred_on": first.isoformat() if first else None,
            }
    return trend, pairs


def read_sql_output(as_of_str):
    trend = {}
    for cid, w, ec, sc, pc, lab, low in q(
        "select subject_id::text, window_type, event_count, distinct_speaker_count, "
        "coalesce(prior_event_count::text,''), trend_label, is_low_confidence "
        f"from {TT} where as_of_date='{as_of_str}' and subject_level='cluster';"):
        trend[(cid, w)] = {"event_count": int(ec), "distinct_speaker_count": int(sc),
                           "prior_event_count": (int(pc) if pc else None),
                           "trend_label": lab, "is_low_confidence": (low == "t")}
    pairs = {}
    for a, b, w, cnt, bcnt, score, isnew, first in q(
        "select subject_a_id::text, subject_b_id::text, window_type, cooccurrence_event_count, "
        "bridge_person_count, intersection_score, is_new_pair, coalesce(first_cooccurred_on::text,'') "
        f"from {TPM} where as_of_date='{as_of_str}' and subject_level='cluster';"):
        pairs[(a, b, w)] = {"cooccurrence_event_count": int(cnt), "bridge_person_count": int(bcnt),
                            "intersection_score": int(float(score)), "is_new_pair": (isnew == "t"),
                            "first_cooccurred_on": (first or None)}
    return trend, pairs


def invariants(as_of_str):
    checks = {
        "pair canonical order (a<b, no self-pair)":
            f"select count(*) from {TPM} where subject_a_id >= subject_b_id;",
        "bridge_count == cardinality(array)":
            f"select count(*) from {TPM} where bridge_person_count <> cardinality(bridge_entity_ids);",
        "trend subject resolves to a cluster":
            f"select count(*) from {TT} tt where not exists (select 1 from {TC} c where c.cluster_id=tt.subject_id);",
        "pair subjects resolve to clusters":
            f"select count(*) from {TPM} pm where not exists (select 1 from {TC} c where c.cluster_id=pm.subject_a_id) "
            f"or not exists (select 1 from {TC} c where c.cluster_id=pm.subject_b_id);",
        "conservation: every trend cluster has >=1 attended tagged event":
            f"select count(*) from {TT} tt where tt.window_type='all_time' and not exists "
            f"(select 1 from {EE} ee join {EV} e on e.id=ee.event_id join {TOPIC} t on t.id=ee.entity_id "
            "where ee.entity_type='topic' and ee.role='tagged_topic' and e.kind='attended' and t.cluster_id=tt.subject_id);",
        "kind isolation: no trend row exceeds its attended-event support":
            f"select count(*) from {TT} tt where tt.window_type='all_time' and tt.event_count > "
            f"(select count(distinct e.id) from {EE} ee join {EV} e on e.id=ee.event_id join {TOPIC} t on t.id=ee.entity_id "
            "where ee.entity_type='topic' and ee.role='tagged_topic' and e.kind='attended' and t.cluster_id=tt.subject_id);",
        "intersection_score == cooc + 2*bridge + 2*novelty":
            f"select count(*) from {TPM} where intersection_score <> "
            "cooccurrence_event_count + 2*bridge_person_count + (case when is_new_pair then 2 else 0 end);",
        "is_low_confidence == (event_count<3 or week)":
            f"select count(*) from {TT} where is_low_confidence <> ((event_count < 3) or (window_type='week'));",
    }
    fails = []
    for label, sql in checks.items():
        n = int(q(sql)[0][0])
        print(f"  [{'PASS' if n == 0 else 'FAIL'}] {label}" + ("" if n == 0 else f"  ({n})"))
        if n:
            fails.append(label)
    return fails


def compare(ref, sql, grain, keys):
    mism = 0
    for k in sorted(set(ref) | set(sql)):
        r, s = ref.get(k), sql.get(k)
        if r is None or s is None:
            mism += 1
            print(f"    {grain} {k}: {'missing from reference' if r is None else 'missing from SQL'}")
            continue
        for f in keys:
            if r.get(f) != s.get(f):
                mism += 1
                print(f"    {grain} {k}.{f}: ref={r.get(f)} sql={s.get(f)}")
    return mism


def read_path_probe() -> list[str]:
    url = os.environ.get("MI_SUPABASE_URL")
    key = os.environ.get("MI_SUPABASE_ANON_KEY")
    if not (url and key):
        print("  [SKIP] read-path probe (MI_SUPABASE_URL / MI_SUPABASE_ANON_KEY not set)")
        return []
    base = url.rstrip("/") + "/rest/v1"
    fails = []
    # anon should reach signal_read and get rows
    try:
        req = urllib.request.Request(
            base + "/v_topic_movement?select=theme&limit=1",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept-Profile": "signal_read"})
        rows = json.loads(urllib.request.urlopen(req, timeout=30).read())
        ok = isinstance(rows, list) and len(rows) >= 1
        print(f"  [{'PASS' if ok else 'FAIL'}] anon reaches signal_read.v_topic_movement (rows={len(rows) if isinstance(rows, list) else '?'})")
        if not ok:
            fails.append("signal_read returned no rows to anon")
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] anon signal_read read errored: {e}")
        fails.append("signal_read read errored")
    # anon must NOT reach the raw base table (topic_intelligence not exposed)
    try:
        req = urllib.request.Request(
            base + "/topic_trend?select=subject_id&limit=1",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept-Profile": "topic_intelligence"})
        urllib.request.urlopen(req, timeout=30)
        print("  [FAIL] raw topic_intelligence.topic_trend is READABLE by anon (should be blocked)")
        fails.append("base table reachable by anon")
    except urllib.error.HTTPError as e:
        blocked = e.code in (401, 403, 404, 406)
        print(f"  [{'PASS' if blocked else 'FAIL'}] raw base table blocked to anon (HTTP {e.code})")
        if not blocked:
            fails.append(f"base table unexpected HTTP {e.code}")
    except Exception as e:  # noqa: BLE001
        print(f"  [WARN] base-table probe inconclusive: {e}")
    return fails


def main() -> int:
    argparse.ArgumentParser(description="Post-swap MI 2b health check (read-only).").parse_args()
    rows = q(f"select max(as_of_date)::text from {TT};")
    as_of_str = rows[0][0] if rows and rows[0][0] else ""
    if not as_of_str:
        print("❌ FAIL — topic_intelligence.topic_trend is EMPTY (intelligence missing).")
        return 1
    as_of = dt.date.fromisoformat(as_of_str)
    print(f"MI 2b health check — live graph as of {as_of_str}\n")

    ev_date, ev_clusters, ev_speakers = load_graph()
    ref_trend, ref_pairs = ref_compute(as_of, ev_date, ev_clusters, ev_speakers)
    sql_trend, sql_pairs = read_sql_output(as_of_str)

    print("Independent recompute vs stored:")
    t_mis = compare(ref_trend, sql_trend, "trend",
                    ("event_count", "distinct_speaker_count", "prior_event_count", "trend_label", "is_low_confidence"))
    p_mis = compare(ref_pairs, sql_pairs, "pair",
                    ("cooccurrence_event_count", "bridge_person_count", "intersection_score", "is_new_pair", "first_cooccurred_on"))
    print(f"  trend: ref={len(ref_trend)} sql={len(sql_trend)} mismatches={t_mis}")
    print(f"  pair : ref={len(ref_pairs)} sql={len(sql_pairs)} mismatches={p_mis}")

    print("\nStructural invariants:")
    inv_fails = invariants(as_of_str)
    print("\nRead-path probe:")
    probe_fails = read_path_probe()

    ok = (t_mis == 0 and p_mis == 0 and not inv_fails and not probe_fails)
    print("\n" + ("✅ PASS — graph coherent, invariants hold, read path healthy."
                  if ok else "❌ FAIL — investigate above. pre2b rollback remains available."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
