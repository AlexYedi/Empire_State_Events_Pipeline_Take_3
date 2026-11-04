#!/usr/bin/env python3
"""
healthcheck_2b.py
=================
POST-SWAP nightly health check for the consolidated MI graph (YED-130 Increment 2b).
Originally a throwaway N-night watch; since YED-230 (2026-09-28) it is the standing post-write
check of the nightly compute (topic_intel_compute.py imports its reference + comparator, so the
compute's parity gate and this check share one definition of "correct").

Reads the LIVE schemas (public + topic_intelligence) — NOT canonical_v2 (empty post-swap).
Five layers, all read-only:
  1. Independent recompute (pure Python, from public.event/event_entity/topic) must AGREE
     row-for-row with the stored topic_intelligence.topic_trend / topic_pair_metric.
  2. The 8 structural invariants (canonical order, no-orphan, conservation, kind isolation,
     score/flag consistency, bridge integrity).
  3. Read-path probe (optional): anon REST reaches signal_read (serves data) and the raw base
     table is BLOCKED — the k>=5 suppression can't be bypassed.
  4. PII column audit (YED-297): any column named in spine_client.FORBIDDEN_COLUMNS, in any
     non-platform schema, is a FLAG (non-fatal); it FAILS the run only when EXPOSED (it holds
     values AND anon/authenticated can read it). `--pii-audit-only` runs just this layer.
  5. Lane freshness (market-lens-and-slices §3/§7, YED-304 Phase A): the lane_run run ledger
     (migration 0016) flags a lane silent at >=7 days and FAILs at >=14 days (days_stale >= 7 is
     a FLAG, >= 14 is a FAIL — matching the contract pinned in 0016); a lane registered in
     lane_registry with no ledger rows FAILs outright; and §3.3 rule 4's coverage check flags a
     lane whose latest 2 runs wrote nothing (items_written=0), failing at 3. Until 0016 exists
     these halves SKIP (non-fatal). Beside them, the role_posted stall check FAILs when
     public.event has no role_posted row in the last 14 days (the L10 lesson: 183 role_posted
     rows, none since 2026-09-23, nothing alerted) and SKIPs when the table has no role_posted
     rows at all (empty twin). NOTE: the role_posted half is a WARNING, not fatal — Alex's
     2026-11-04 ruling (YED-322, Linear tracker): flip it back to fatal once lane 1 (PR #271)
     has run on schedule twice AND role_posted freshness is under 7 days. The lane_run ledger,
     registry and coverage halves of this layer stay fatal.

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

# Lane freshness (market-lens-and-slices §7): FLAG at >=7 days stale, FAIL at >=14 — the contract
# pinned in migration 0016. A lane with no runs at all has been dead since it was registered —
# FAIL, never silent. Beside freshness, §3.3 rule 4's coverage metric: a lane whose latest runs
# all wrote nothing (items_written=0) flags at 2 consecutive zero-write runs, fails at 3.
FLAG_DAYS, FAIL_DAYS = 7, 14
ROLE_POSTED = "role_posted"
# Migration 0016 owns the lane_run DDL; the fixture pins the column shape this layer expects.
LANE_RUN_COLUMNS = ("lane", "started_at", "items_seen", "items_written", "items_refused", "credits_spent")
FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "fixtures", "lane_run_freshness.json")

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


# ---------------------------------------------------------------- layer 4: lane freshness

def classify_freshness(last_run, today):
    """Pure classifier: last_run (date or None) -> 'ok' | 'flag' | 'fail' (§7: >=7d FLAG, >=14d FAIL)."""
    if last_run is None:
        return "fail"
    days = (today - last_run).days
    return "ok" if days < FLAG_DAYS else "flag" if days < FAIL_DAYS else "fail"


def classify_coverage(items_written):
    """Pure §3.3 rule 4: count NEWEST-first consecutive zero-write runs — 2 -> 'flag', 3+ -> 'fail'."""
    zeros = 0
    for written in (items_written or []):
        if written == 0:
            zeros += 1
        else:
            break
    return "ok" if zeros < 2 else "flag" if zeros == 2 else "fail"


def never_ran(registered, last_runs):
    """Pure: registered lanes with no ledger rows (the 'never ran -> FAIL' signal). None registry -> []."""
    return sorted(set(registered or []) - set(last_runs or {}))


def registered_lanes() -> list[str] | None:
    """Lane ids from public.lane_registry (migration 0016), or None while it doesn't exist."""
    if not q("select to_regclass('public.lane_registry') is not null;")[0][0] == "t":
        return None
    cols = {r[0] for r in q("""select column_name from information_schema.columns
                               where table_schema='public' and table_name='lane_registry';""")}
    if "lane" not in cols:
        return None
    return [r[0] for r in q("select lane from public.lane_registry;")]


def _pg_int_array(s):
    """psql -A renders int[] as '{5,3,0}' — parse to a list of ints (empty array -> [])."""
    return [int(w) for w in (s or "{}").strip().strip("{}").split(",") if w != ""]


def lane_zero_write_runs() -> dict[str, list[int]]:
    """Newest-first items_written for each lane's last 3 lane_run rows (empty pre-0016)."""
    if not q("select to_regclass('public.lane_run') is not null;")[0][0] == "t":
        return {}
    return {lane: _pg_int_array(ws) for lane, ws in q("""select lane, array_agg(items_written order by rn desc) from (
        select lane, items_written, row_number() over (partition by lane order by started_at desc) rn
        from public.lane_run) t where rn <= 3 group by lane;""")}


def lane_run_last_runs() -> dict[str, dt.date] | None:
    """Latest run per lane from public.lane_run, or None while migration 0016 hasn't created it."""
    if not q("select to_regclass('public.lane_run') is not null;")[0][0] == "t":
        return None
    cols = {r[0] for r in q("""select column_name from information_schema.columns
                               where table_schema='public' and table_name='lane_run';""")}
    if not {"lane", "started_at"} <= cols:
        return None
    out = {}
    for lane, d in q(f"select lane, max(started_at)::date::text from public.lane_run group by lane;"):
        out[lane] = dt.date.fromisoformat(d) if d else None
    return out


def lane_freshness(today) -> list[str]:
    """Layer 4a — lane_run staleness + §3.3 rule 4 coverage + registry cross-check. Fatal FAILs returned."""
    fails = []
    last_runs = lane_run_last_runs()
    if last_runs is None:
        print("  [SKIP] lane_run ledger (migration 0016 not applied yet)")
        return fails
    registry = registered_lanes()
    if registry is None:
        print("  [SKIP] lane_registry cross-check (table not in 0016 yet) — never-ran lanes stay invisible")
    for lane in never_ran(registry, last_runs):
        print(f"  [FAIL] lane {lane}: registered in lane_registry but has no lane_run rows")
        fails.append(f"lane {lane} registered but never ran")
    if not last_runs:
        if registry is None:
            print("  [SKIP] lane_run ledger exists but is empty (no lane has run yet)")
        return fails
    zero_runs = lane_zero_write_runs()
    for lane in sorted(last_runs):
        status = classify_freshness(last_runs[lane], today)
        cov = classify_coverage(zero_runs.get(lane, []))
        cov_note = (f"; coverage {cov}: last {len(zero_runs.get(lane, []))} run(s), "
                    f"items_written={zero_runs.get(lane, [])}" if zero_runs.get(lane) is not None else "")
        stale = "?" if last_runs[lane] is None else str((today - last_runs[lane]).days)
        print(f"  [{'FAIL' if status == 'fail' else 'WARN' if status == 'flag' else 'PASS'}] "
              f"lane {lane}: last run {last_runs[lane] or 'never'} ({stale}d stale{cov_note})")
        if status == "fail":
            fails.append(f"lane {lane} silent >={FAIL_DAYS}d")
        if cov == "fail":
            fails.append(f"lane {lane} items_written=0 for 3 consecutive runs")
        elif cov == "flag":
            print(f"  [WARN] lane {lane}: items_written=0 for 2 consecutive runs (flag, non-fatal)")
    return fails


def role_posted_warns(status: str) -> list[str]:
    """Pure helper — the YED-322 warn verdict. Alex's 2026-11-04 ruling: a stale role_posted lane
    WARNs (non-fatal) until lane 1 (PR #271) has run on schedule twice AND role_posted freshness
    is under 7 days; then flip it back to fatal. The lane_run ledger/registry/coverage halves of
    layer 5 stay fatal regardless."""
    return [f"{ROLE_POSTED} lane silent (>= {FAIL_DAYS}d) — warning until YED-322 flips it fatal"] \
        if status == "fail" else []


def role_posted_freshness(today) -> list[str]:
    """Layer 4b — the role_posted stall (L10). Non-fatal by Alex's 2026-11-04 ruling (YED-322):
    a stall >= FAIL_DAYS prints a WARNING instead of failing the run; flip back to fatal once
    lane 1 (PR #271) has run on schedule twice AND role_posted freshness is under 7 days."""
    total = int(q(f"select count(*) from {EV} where kind='{ROLE_POSTED}';")[0][0])
    if total == 0:
        print(f"  [SKIP] {ROLE_POSTED} stall check (no {ROLE_POSTED} events in the table at all)")
        return []
    last = q(f"select max(event_date)::date::text from {EV} where kind='{ROLE_POSTED}';")[0][0]
    status = classify_freshness(dt.date.fromisoformat(last) if last else None, today)
    stale = (today - dt.date.fromisoformat(last)).days if last else -1
    print(f"  [{'WARN' if status == 'fail' else 'PASS'}] {ROLE_POSTED} stall: "
          f"{total} events, last {last} ({stale}d ago)")
    return role_posted_warns(status)


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


# ---------------------------------------------------------------- PII column audit (YED-297)
# Platform-owned schemas that legitimately carry contact columns (auth.users.email/phone) or are
# not ours to audit. Everything else in the database is in scope, which is how the 2026-11-02
# audit found pre2b.person.email outside the Phase-2 backstop's reach.
PII_AUDIT_EXCLUDED_SCHEMAS = (
    "auth", "storage", "pg_catalog", "information_schema", "pg_toast", "realtime", "vault",
    "extensions", "graphql", "graphql_public", "supabase_functions", "supabase_migrations",
    "net", "pgsodium", "pgsodium_masks", "cron",
)
API_ROLES = ("anon", "authenticated")


def _forbidden_columns() -> list[str]:
    """Single source of truth: spine_client.FORBIDDEN_COLUMNS (imports without env or side effects)."""
    import importlib.util
    path = os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "scripts", "spine_client.py")
    spec = importlib.util.spec_from_file_location("spine_client", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return sorted(mod.FORBIDDEN_COLUMNS)


def pii_column_audit() -> tuple[list[str], list[str]]:
    """Decision YED-297 (Alex, 2026-11-03): a forbidden contact-PII column that merely EXISTS is a
    FLAG; it is a FAIL only when EXPOSED, meaning it holds values AND anon/authenticated can read it
    (schema USAGE + column SELECT, and for tables, RLS off or a SELECT/ALL policy covering the role).
    Read-only: counts and catalog lookups, never the values themselves. Returns (flags, fails)."""
    cols = ", ".join(f"'{c}'" for c in _forbidden_columns())
    excluded = ", ".join(f"'{s}'" for s in PII_AUDIT_EXCLUDED_SCHEMAS)
    roles = ", ".join(f"'{r}'" for r in API_ROLES)
    sql = f"""
-- pg_attribute, not information_schema.columns: the latter omits materialized views and hides
-- objects the connecting role lacks privileges on; the catalog sees every relation.
with hits as (
  select n.nspname::text s, cl.relname::text t, a.attname::text col, cl.oid::regclass rel
    from pg_attribute a
    join pg_class cl on cl.oid = a.attrelid
    join pg_namespace n on n.oid = cl.relnamespace
   where cl.relkind in ('r', 'p', 'v', 'm', 'f')
     and a.attnum > 0 and not a.attisdropped
     and lower(a.attname) in ({cols})
     and n.nspname not in ({excluded})
     and n.nspname not like 'pg\\_temp%' and n.nspname not like 'pg\\_toast%'
)
select h.s, h.t, h.col,
  (xpath('/row/n/text()', query_to_xml(format(
     'select count(*) as n from %I.%I where %I is not null and %I::text <> %L',
     h.s, h.t, h.col, h.col, ''), false, true, '')))[1]::text as populated,
  coalesce((select string_agg(r, ',' order by r) from unnest(array[{roles}]) r
     where has_schema_privilege(r, h.s, 'USAGE')
       and has_column_privilege(r, h.rel, h.col, 'SELECT')
       and (cl.relkind not in ('r', 'p') or not cl.relrowsecurity
            or exists (select 1 from pg_policies p
                        where p.schemaname = h.s and p.tablename = h.t
                          and p.cmd in ('SELECT', 'ALL')
                          and (r = any(p.roles) or 'public' = any(p.roles))))), '') as readable_by
  from hits h join pg_class cl on cl.oid = h.rel
 order by 1, 2, 3;"""
    flags, fails = [], []
    rows = q(sql)
    if not rows:
        print("  [PASS] no forbidden contact-PII columns outside platform schemas")
        return flags, fails
    for s, t, col, populated, readable_by in rows:
        n = int(populated or 0)
        where = f"{s}.{t}.{col}"
        if n and readable_by:
            print(f"  [FAIL] {where}: {n} populated row(s), readable by {readable_by} (EXPOSED)")
            fails.append(where)
        else:
            why = (f"{n} populated row(s), not API-readable" if n
                   else "empty" + (f", readable by {readable_by}" if readable_by else ", not API-readable"))
            print(f"  [FLAG] {where}: {why}. Drop the column (CLAUDE.md invariant 1 / ADR-9)")
            flags.append(where)
    return flags, fails


# ---------------------------------------------------------------- selftest (offline, no DB)

def _selftest() -> int:
    """Offline: validate the lane_run fixture's shape + classification, and the FLAG/FAIL edges."""
    ok = n = 0

    def ck(name, cond):
        nonlocal ok, n
        n += 1
        ok += bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    with open(FIXTURE) as fh:
        fx = json.load(fh)
    ck("fixture has as_of, expected_lane_run_columns, registered_lanes, never_ran_expected, rows, role_posted",
       all(k in fx for k in ("as_of", "expected_lane_run_columns", "registered_lanes",
                             "never_ran_expected", "rows", "role_posted")))
    ck("fixture's expected lane_run columns match this script's probe shape",
       tuple(fx.get("expected_lane_run_columns", ())) == LANE_RUN_COLUMNS)
    as_of = dt.date.fromisoformat(fx["as_of"])
    blob = json.dumps(fx)
    ck("fixture carries no email/phone (ADR-9 negative check)",
       "@" not in blob and not any(tok.isdigit() and len(tok) >= 7 for tok in
                                   blob.replace("-", " ").replace(".", " ").split()))
    for row in fx["rows"]:
        got = classify_freshness(dt.date.fromisoformat(row["last_run"]), as_of)
        ck(f"lane {row['lane']} (last {row['last_run']}) -> {row['expected_status']}",
           got == row["expected_status"])
        cov = classify_coverage(row.get("recent_runs_items_written", []))
        ck(f"lane {row['lane']} coverage {row.get('recent_runs_items_written')} -> {row['expected_coverage']}",
           cov == row["expected_coverage"])
    ck("never_ran(registry, ledger) matches fixture expectation",
       never_ran(fx["registered_lanes"], {r["lane"] for r in fx["rows"]}) == sorted(fx["never_ran_expected"]))
    rp = fx["role_posted"]
    got = classify_freshness(dt.date.fromisoformat(rp["last_event_date"]), as_of)
    ck(f"role_posted (last {rp['last_event_date']}) -> {rp['expected_status']}", got == rp["expected_status"])
    # YED-322 warn path: a fail-grade role_posted stall emits a warning and nothing else — it
    # must never reach the fatal gate (fresh_fails), while ok/flag stay silent.
    ck("fail-grade role_posted stall -> warning emitted (non-fatal, YED-322)",
       role_posted_warns("fail") != [])
    ck("ok/flag role_posted -> no warning", role_posted_warns("ok") == [] and role_posted_warns("flag") == [])

    # Threshold edges pinned exactly (0016 contract): ok through day 6, flag days 7-13, fail from day 14 or never-run.
    for delta, want in ((0, "ok"), (FLAG_DAYS - 1, "ok"), (FLAG_DAYS, "flag"),
                        (FAIL_DAYS - 1, "flag"), (FAIL_DAYS, "fail")):
        ck(f"day {delta:>2} stale -> {want}", classify_freshness(as_of - dt.timedelta(days=delta), as_of) == want)
    ck("never ran -> fail", classify_freshness(None, as_of) == "fail")
    # Coverage edges: consecutive NEWEST-first zero-write runs — 1 ok, 2 flag, 3 fail, none ok.
    for hist, want in (((5, 5, 5), "ok"), ((0, 5, 5), "ok"), ((0, 0, 5), "flag"), ((0, 0, 0), "fail"), ((), "ok")):
        ck(f"coverage {list(hist)} -> {want}", classify_coverage(list(hist)) == want)

    print(f"healthcheck_2b --selftest: {ok}/{n} passed")
    return 0 if ok == n else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Post-swap MI 2b health check (read-only).")
    ap.add_argument("--pii-audit-only", action="store_true",
                    help="run only the YED-297 PII column audit (exit 1 only on an EXPOSED column)")
    ap.add_argument("--selftest", action="store_true",
                    help="offline: validate the lane_run freshness fixture + threshold edges (no DB)")
    args = ap.parse_args()
    if args.pii_audit_only:
        print("PII column audit (YED-297):")
        _, pii_fails = pii_column_audit()
        return 1 if pii_fails else 0
    if args.selftest:
        return _selftest()
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
    print("\nRead-path probe (non-fatal — checks the watch's own anon-key path, not graph health):")
    probe_fails = read_path_probe()
    print("\nPII column audit (YED-297 — FLAG if a forbidden column exists, FAIL only if EXPOSED):")
    pii_flags, pii_fails = pii_column_audit()

    print("\nLane freshness (lane_run ledger fatal; role_posted stall warns until YED-322 — §3/§7):")
    fresh_fails = lane_freshness(as_of)
    rp_warns = role_posted_freshness(as_of)

    # FATAL = graph coherence (independent recompute + invariants) + an EXPOSED contact-PII column
    # + lane_run freshness (ledger/registry/coverage). The role_posted stall is a WARNING by Alex's
    # 2026-11-04 ruling (YED-322): flip it back to fatal once lane 1 (PR #271) has run on schedule
    # twice AND role_posted freshness is under 7 days. The read-path probe and PII flags are also
    # secondary signals reported as WARNINGS, so an anon-key/config hiccup or an empty legacy
    # column can't masquerade as a failure.
    graph_ok = (t_mis == 0 and p_mis == 0 and not inv_fails)
    ok = graph_ok and not pii_fails and not fresh_fails
    if probe_fails:
        print("  ⚠️  read-path probe warnings (non-fatal): " + "; ".join(probe_fails))
    if pii_flags:
        print("  ⚠️  PII column flags (non-fatal): " + "; ".join(pii_flags))
    if rp_warns:
        print("  ⚠️  role_posted stall (non-fatal until YED-322 flips it): " + "; ".join(rp_warns))
    if fresh_fails:
        print("  🚨 lane freshness FAIL: " + "; ".join(fresh_fails))
    if ok:
        print("\n✅ PASS — graph coherent, invariants hold, no exposed contact PII, lane_run ledger fresh."
              + (" (warnings above)" if probe_fails or pii_flags or rp_warns else " read path healthy."))
    else:
        if not graph_ok:
            print("\n❌ FAIL — graph incoherence above. pre2b rollback remains available.")
        if pii_fails:
            print("\n❌ FAIL — EXPOSED contact PII: " + "; ".join(pii_fails)
                  + ". API-readable email/phone values break CLAUDE.md invariant 1. Revoke or drop now.")
        if fresh_fails:
            print("\n❌ FAIL — lane staleness: " + "; ".join(fresh_fails)
                  + ". A dead lane is an L1–L3/L10 failure; see the lane freshness section above.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
