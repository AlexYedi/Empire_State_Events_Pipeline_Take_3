#!/usr/bin/env python3
"""
build_2b_canonical_v2.py
========================
MI data-layer consolidation — Increment 2b (YED-130 / ADR-4). Builds the reconciled graph
in the parallel schema `canonical_v2` (expand-contract). This script does the DATA build for
AC2b.2 (theme dimension) + AC2b.1 (IRL event re-ingest). The compute rewrite (AC2b.3) + the
atomic swap run in later steps. NOTHING here touches live `public`; canonical_v2 is separate.

RUN ORDER: apply migrations 0005 + 0006 first (they create canonical_v2's tables + enums),
then run this. Idempotent — safe to re-run.

WHAT IT WRITES (all into canonical_v2, all idempotent):
  A. copy public.{company,person,topic} -> canonical_v2.*            (structure-identical)
  B. carry the 30 curated clusters  topic_intelligence.topic_cluster -> canonical_v2.topic_cluster
  C. assign canonical_v2.topic.cluster_id via topic_intelligence.topics + topic_crosswalk
  D. re-ingest IRL events   gtm signal.events   -> canonical_v2.event (kind='attended')
  E. re-ingest the graph    gtm signal.relations-> canonical_v2.event_entity (+ person.company_id)

SOURCES (read):
  * Twin (psql): public.{company,person,topic}; topic_intelligence.{topic_cluster, topics,
      topic_crosswalk, entity_crosswalk}. (Clusters were carried in Increment 1 — no spine
      round-trip needed for the theme dimension.)
  * gtm spine (REST GET, Accept-Profile: signal): signal.events, signal.relations. These were
      NOT carried, so the spine is the only source. env SUPABASE_SPINE_URL/SERVICE_KEY.

EDGE MAPPING (spec §2 — supabase/specs/2b_relations_to_event_entity_mapping.md):
  tagged_topic (event->topic)                 -> event_entity(entity_type='topic', role='tagged_topic')
  speaker_at / host_of / panelist_at (ent->ev)-> event_entity(entity_type='person', role=speaker/host/panelist)
  attended (ent->ev)                          -> event_entity(entity_type='person', role='attendee')
  works_at (person->company)                  -> canonical_v2.person.company_id  (NOT an edge; fill-if-null)
  co_event / related_topic                    -> dropped (not consumed by the compute)
  Re-key gtm ids -> Empire ids via topic_crosswalk / entity_crosswalk. gtm events -> canonical_v2
  events by metadata.gtm_event_id. Unresolved edges are counted + reported (zero-orphan gate).

TARGET (write): the Phantom Test Case DB (twin) via psql. The Empire prod DB is touched ONLY
after the full rehearsal + proven rollback (ADR-4 §6). The canonical guard blocks prod unless
MI_ALLOW_CANONICAL=1.

Env required:  PHANTOM_TEST_DB_PASSWORD (or PGPASSWORD); SUPABASE_SPINE_URL, SUPABASE_SPINE_SERVICE_KEY
Env optional:  TWIN_DB_HOST (default db.ytfzzsxcxxbejnowmkmk.supabase.co), TWIN_DB_PORT (5432),
               TWIN_DB_USER (postgres), TWIN_DB_NAME (postgres), PSQL_BIN

Usage:  python build_2b_canonical_v2.py --dry-run   # read + print counts, NO writes
        python build_2b_canonical_v2.py             # build (idempotent)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

SOURCE_MARK = "increment_2b_gtm"
PSQL_BIN = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")

# spec §2 role/kind mapping
SPEAKER_ROLE = {"speaker_at": "speaker", "host_of": "host", "panelist_at": "panelist"}
EVENT_KIND = "attended"  # spec §5 (grounded in the existing taxonomy)


# ---------------------------------------------------------------- normalization
def dehyph(s: str | None) -> str:
    return re.sub(r"-", "", (s or "")).lower()


def rehyph(s: str | None) -> str | None:
    h = re.sub(r"-", "", (s or "")).lower()
    if len(h) != 32 or not re.fullmatch(r"[0-9a-f]{32}", h):
        return s
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def sql_str(v) -> str:
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


# ---------------------------------------------------------------- env / conn
def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.exit(f"ERROR: required environment variable {name} is not set.")
    return val


def _conn_str() -> str:
    host = os.environ.get("TWIN_DB_HOST", "db.ytfzzsxcxxbejnowmkmk.supabase.co")
    port = os.environ.get("TWIN_DB_PORT", "5432")
    user = os.environ.get("TWIN_DB_USER", "postgres")
    name = os.environ.get("TWIN_DB_NAME", "postgres")
    if ("canonical" in host or "oicikjyzmxqfomrrqkvf" in host) and os.environ.get("MI_ALLOW_CANONICAL") != "1":
        sys.exit("REFUSING: target host looks like the Empire prod DB. 2b rehearses on the "
                 "Phantom Test Case DB first; set MI_ALLOW_CANONICAL=1 only after the rehearsal "
                 "gate — incl. a PROVEN rollback — is green (ADR-4 §6).")
    return f"host={host} port={port} user={user} dbname={name} sslmode=require"


def _pgenv() -> dict:
    env = dict(os.environ)
    if "PGPASSWORD" not in env:
        env["PGPASSWORD"] = _require_env("PHANTOM_TEST_DB_PASSWORD")
    return env


def psql_read(sql: str) -> list[list[str]]:
    out = subprocess.check_output(
        [PSQL_BIN, _conn_str(), "-tAF", "\t", "-c", sql], env=_pgenv()
    ).decode()
    return [line.split("\t") for line in out.splitlines() if line]


def psql_exec(sql: str) -> None:
    p = subprocess.run(
        [PSQL_BIN, _conn_str(), "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"],
        input=sql.encode(), env=_pgenv(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        sys.exit(f"ERROR psql exec failed:\n{p.stderr.decode('utf-8','replace')}")


# ---------------------------------------------------------------- spine REST
def _spine_get(path: str) -> list[dict]:
    base = _require_env("SUPABASE_SPINE_URL").rstrip("/")
    key = _require_env("SUPABASE_SPINE_SERVICE_KEY")
    req = urllib.request.Request(base + "/rest/v1/" + path, headers={
        "apikey": key, "Authorization": f"Bearer {key}",
        "Accept-Profile": "signal", "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ERROR fetching spine {path!r}: {e}")


def fetch_events() -> list[dict]:
    return _spine_get("events?select=event_id,event_slug,title,event_date,venue,"
                      "event_status,source_record_id&limit=5000")


def fetch_relations() -> list[dict]:
    return _spine_get("relations?select=from_type,from_id,to_type,to_id,relation_type,"
                      "is_active&is_active=eq.true&limit=5000")


# ---------------------------------------------------------------- A/B/C: pure-SQL copy + clusters
def build_entities_and_clusters() -> None:
    """Copy public entities into canonical_v2, carry the clusters, assign topic.cluster_id.
       All same-database joins — idempotent."""
    psql_exec("""
begin;
-- A. copy public entities/topics -> canonical_v2 (structure-identical; skip existing)
insert into canonical_v2.company select * from public.company on conflict (id) do nothing;
insert into canonical_v2.person  select * from public.person  on conflict (id) do nothing;
-- topic gained cluster_* columns in 0006, so enumerate the shared (public) columns explicitly:
insert into canonical_v2.topic (id, name, description, notion_page_id, source, relevance_score,
                                last_engaged_at, engagement_count, metadata, created_at, updated_at)
  select id, name, description, notion_page_id, source, relevance_score,
         last_engaged_at, engagement_count, metadata, created_at, updated_at
  from public.topic
  on conflict (id) do nothing;

-- B. carry the 30 curated clusters verbatim (same cluster_id UUIDs)
insert into canonical_v2.topic_cluster select * from topic_intelligence.topic_cluster
  on conflict (cluster_id) do nothing;

-- C. assign canonical_v2.topic.cluster_id via the carried assignments + the topic crosswalk
update canonical_v2.topic ct
   set cluster_id = ti.cluster_id,
       cluster_assignment_confidence = ti.cluster_assignment_confidence,
       cluster_assigned_by = ti.cluster_assigned_by
  from topic_intelligence.topics ti
  join topic_intelligence.topic_crosswalk xw on xw.gtm_topic_id = ti.topic_id
 where ct.id = xw.empire_topic_id and ti.cluster_id is not null;
commit;
""")


# ---------------------------------------------------------------- D: events
def build_events(events: list[dict]) -> dict:
    """Insert IRL events (kind='attended') idempotently; return {gtm_event_id: cv2_event_id}."""
    stmts = ["begin;"]
    for e in events:
        meta = json.dumps({
            "gtm_event_id": e["event_id"],
            "event_slug": e.get("event_slug"),
            "event_status": e.get("event_status"),   # kept for the forward attendance-diff (spec §5.1)
            "venue": e.get("venue"),
        })
        stmts.append(
            "insert into canonical_v2.event (title, kind, event_date, notion_page_id, source, metadata) "
            f"select {sql_str(e.get('title'))}, {sql_str(EVENT_KIND)}, {sql_str(e.get('event_date'))}, "
            f"{sql_str(rehyph(e.get('source_record_id')))}, {sql_str(SOURCE_MARK)}, {sql_str(meta)}::jsonb "
            "where not exists (select 1 from canonical_v2.event "
            f"  where metadata->>'gtm_event_id' = {sql_str(e['event_id'])});"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))

    rows = psql_read(
        "select metadata->>'gtm_event_id', id::text from canonical_v2.event "
        "where metadata->>'gtm_event_id' is not null;"
    )
    return {gid: eid for gid, eid in rows}


# ---------------------------------------------------------------- E: relations -> edges
def build_edges(relations: list[dict], event_map: dict) -> dict:
    """Re-key relations onto canonical_v2.event_entity (+ person.company_id). Idempotent."""
    topic_xw = {gid: eid for gid, eid in psql_read(
        "select gtm_topic_id, empire_topic_id from topic_intelligence.topic_crosswalk;")}
    ent_xw = {gid: (eid, kind) for gid, eid, kind in psql_read(
        "select gtm_entity_id, empire_id, empire_kind from topic_intelligence.entity_crosswalk;")}

    edge_stmts, works_at = ["begin;"], []
    counts = {"tagged_topic": 0, "speaker": 0, "host": 0, "panelist": 0, "attendee": 0,
              "works_at": 0, "skipped_co_event": 0, "skipped_related_topic": 0}
    unresolved = {"event": 0, "topic": 0, "person": 0, "company": 0}

    def add_edge(ev_id, etype, ent_id, role):
        edge_stmts.append(
            "insert into canonical_v2.event_entity (event_id, entity_type, entity_id, role) values ("
            f"{sql_str(ev_id)}, {sql_str(etype)}, {sql_str(ent_id)}, {sql_str(role)}) "
            "on conflict (event_id, entity_type, entity_id, role) do nothing;"
        )

    for r in relations:
        rt = r["relation_type"]
        if rt == "tagged_topic":                                  # event -> topic
            ev = event_map.get(r["from_id"]); tp = topic_xw.get(r["to_id"])
            if ev is None: unresolved["event"] += 1; continue
            if tp is None: unresolved["topic"] += 1; continue
            add_edge(ev, "topic", tp, "tagged_topic"); counts["tagged_topic"] += 1
        elif rt in SPEAKER_ROLE or rt == "attended":              # entity(person) -> event
            role = "attendee" if rt == "attended" else SPEAKER_ROLE[rt]
            ev = event_map.get(r["to_id"]); ent = ent_xw.get(r["from_id"])
            if ev is None: unresolved["event"] += 1; continue
            if ent is None or ent[1] != "person": unresolved["person"] += 1; continue
            add_edge(ev, "person", ent[0], role); counts[role] += 1
        elif rt == "works_at":                                    # person -> company
            per = ent_xw.get(r["from_id"]); co = ent_xw.get(r["to_id"])
            if per is None or per[1] != "person": unresolved["person"] += 1; continue
            if co is None or co[1] != "company": unresolved["company"] += 1; continue
            works_at.append((per[0], co[0])); counts["works_at"] += 1
        elif rt == "co_event":
            counts["skipped_co_event"] += 1
        elif rt == "related_topic":
            counts["skipped_related_topic"] += 1
        # (panelist_at handled via SPEAKER_ROLE above)
    edge_stmts.append("commit;")
    psql_exec("\n".join(edge_stmts))

    # works_at -> person.company_id, FILL-IF-NULL (never clobber an existing Empire assignment)
    if works_at:
        wstmts = ["begin;"]
        for per_id, co_id in works_at:
            wstmts.append(
                f"update canonical_v2.person set company_id = {sql_str(co_id)} "
                f"where id = {sql_str(per_id)} and company_id is null;"
            )
        wstmts.append("commit;")
        psql_exec("\n".join(wstmts))

    return {"counts": counts, "unresolved": unresolved}


# ---------------------------------------------------------------- assertions
def assert_zero_orphan() -> list[str]:
    """Every canonical_v2.event_entity id resolves to a live canonical_v2 row of its type."""
    checks = {
        "event":   "select count(*) from canonical_v2.event_entity ee where not exists "
                   "(select 1 from canonical_v2.event e where e.id=ee.event_id);",
        "topic":   "select count(*) from canonical_v2.event_entity ee where entity_type='topic' "
                   "and not exists (select 1 from canonical_v2.topic t where t.id=ee.entity_id);",
        "person":  "select count(*) from canonical_v2.event_entity ee where entity_type='person' "
                   "and not exists (select 1 from canonical_v2.person p where p.id=ee.entity_id);",
        "company": "select count(*) from canonical_v2.event_entity ee where entity_type='company' "
                   "and not exists (select 1 from canonical_v2.company c where c.id=ee.entity_id);",
    }
    problems = []
    for k, q in checks.items():
        n = int(psql_read(q)[0][0])
        if n:
            problems.append(f"{n} orphan event_entity rows with dangling {k}_id")
    return problems


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Build Increment-2b canonical_v2 graph (clusters + IRL re-ingest).")
    ap.add_argument("--dry-run", action="store_true", help="Read + print counts. No writes.")
    args = ap.parse_args()

    host = os.environ.get("TWIN_DB_HOST", "db.ytfzzsxcxxbejnowmkmk.supabase.co")
    print(f"TARGET (canonical_v2 on): {host}")
    print("Reading IRL graph from the gtm spine (events + relations) ...\n")
    events = fetch_events()
    relations = fetch_relations()

    rel_by_type: dict[str, int] = {}
    for r in relations:
        rel_by_type[r["relation_type"]] = rel_by_type.get(r["relation_type"], 0) + 1

    print("=" * 60)
    print("  SOURCE COUNTS (gtm spine)")
    print("=" * 60)
    print(f"  events ...................... {len(events):>4}   (~59)")
    print(f"  active relations ............ {len(relations):>4}   (~629)")
    for rt in sorted(rel_by_type):
        print(f"    {rt:<16} .......... {rel_by_type[rt]:>4}")
    print("=" * 60)

    if args.dry_run:
        print("\n--dry-run: no writes. (Apply 0005+0006, then re-run without --dry-run.)")
        return 0

    print("\nA/B/C: copy public -> canonical_v2, carry 30 clusters, assign topic.cluster_id ...")
    build_entities_and_clusters()
    cl = psql_read("select count(*) from canonical_v2.topic_cluster;")[0][0]
    assigned = psql_read("select count(*) from canonical_v2.topic where cluster_id is not null;")[0][0]
    print(f"  canonical_v2.topic_cluster : {cl} clusters carried")
    print(f"  canonical_v2.topic         : {assigned} topics assigned to a cluster")

    print("\nD: re-ingest IRL events (kind='attended') ...")
    event_map = build_events(events)
    print(f"  canonical_v2.event         : {len(event_map)} IRL events present")

    print("\nE: re-ingest the graph -> event_entity (+ person.company_id) ...")
    res = build_edges(relations, event_map)
    for role, n in res["counts"].items():
        print(f"    {role:<20} {n:>4}")
    if any(res["unresolved"].values()):
        print("  UNRESOLVED (could not re-key — investigate before trusting the recompute):")
        for k, n in res["unresolved"].items():
            if n:
                print(f"    {k:<20} {n:>4}")

    print("\nAsserting zero-orphan event_entity ...")
    problems = assert_zero_orphan()
    if problems:
        print("  ❌ ORPHANS FOUND:")
        for p in problems:
            print(f"    - {p}")
        sys.exit("Zero-orphan invariant FAILED — do not proceed to the compute rewrite.")
    print("  ✓ zero-orphan: every edge resolves to a live canonical_v2 row.")
    print("\nDone. Next: build topic_cluster-grain compute (AC2b.3) + invariants (AC2b.4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
