#!/usr/bin/env python3
"""
build_2a_link.py
================
MI data-layer consolidation — Increment 2a (YED-130 / ADR-4). LINK layer. ADDITIVE.

Computes the two deterministic crosswalks that link Increment-1's carried
topic-intelligence (keyed to gtm UUIDs) to Empire's own `public` graph, then writes
them + the handful of net-new additive inserts to the TARGET. No recompute, nothing
destructive: no UPDATE/DELETE of any pre-existing `public` row.

WHAT IT WRITES (all idempotent — safe to re-run):
  * topic_intelligence.topic_crosswalk : 170 rows (145 notion_id + 25 inserted)
  * public.topic                       : 25 net-new gtm-only topics (INSERT only)
  * topic_intelligence.entity_crosswalk: 396 rows (383 notion_id + 12 exact_name + 1 inserted)
  * public.company / public.person     : 1 net-new entity (INSERT only)
  * topic_intelligence.merge_map       : 12 rows (the exact-name recoveries)

SOURCES (read):
  * gtm TOPIC side  : the TWIN via psql  — topic_intelligence.topics
                      (carried snapshot of the spine, keyed to gtm UUIDs; self-contained
                       on the twin, so no spine round-trip needed for topics).
  * gtm ENTITY side : the gtm spine via REST GET — signal.entities (NOT carried onto
                      the twin, so this is the only source). Header Accept-Profile: signal.
                      env: SUPABASE_SPINE_URL / SUPABASE_SPINE_SERVICE_KEY  (gtm-os/.env)
  * Empire side     : the TWIN via psql — public.topic / public.company / public.person.

TARGET (write): the TWIN via psql. Connection from env (see below). Rehearsal target is
the disposable staging twin ytfzzsxcxxbejnowmkmk; the canonical project is touched ONLY
after the full rehearsal gate is green (ADR-4 §6). NEVER touch canonical here.

THE MEASURED CROSSWALK (probe / ADR-4 — reproduced by this script, not trusted blindly):
  TOPICS  : gtm topics.source_record_id == Empire public.topic.notion_page_id, but gtm
            de-hyphenated + Empire hyphenated. De-hyphenate BOTH, lowercase, join.
            -> 145 join 1:1 ; 25 gtm-only (insert) ; 13 Empire-only (unlinked) ;
               2 Empire topics NULL notion_page_id (flag for backfill — cannot join).
  ENTITIES: gtm source_record_id (de-hyph) ↔ Empire notion_page_id (de-hyph), per kind.
            -> 383 join 1:1 by notion id ; of the 13 leftovers, 12 exact-match an existing
               Empire row by name (false splits — same real entity, different Notion page →
               recover + record in merge_map) ; 1 genuinely new (insert).
            NEVER fuzzy-match. Exact name = lower(collapse-whitespace(name)) on BOTH sides,
            using the gtm DISPLAY name (gtm's stored `normalized_name` over-strips
            punctuation — e.g. "Cursor (Anysphere)" -> "cursor anysphere" — which would
            miss two legitimate exact matches; display-name-vs-name is the faithful key).

Secrets: ALL keys/passwords read from the environment at runtime. Nothing hardcoded, and
no PII is written to disk — the crosswalk/merge_map payloads are UUIDs + de-identified
evidence; the only names written are topic labels + the one net-new company name (INSERTs).

Env required:
  PHANTOM_TEST_DB_PASSWORD   (or PGPASSWORD)   — twin postgres password
  SUPABASE_SPINE_URL, SUPABASE_SPINE_SERVICE_KEY  — gtm spine REST (entities)
Env optional:
  TWIN_DB_HOST (default db.ytfzzsxcxxbejnowmkmk.supabase.co), TWIN_DB_PORT (5432),
  TWIN_DB_USER (postgres), TWIN_DB_NAME (postgres), PSQL_BIN (/opt/homebrew/opt/libpq/bin/psql)

Usage:
  python build_2a_link.py --dry-run   # compute + print counts, NO writes
  python build_2a_link.py             # compute + write (idempotent)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

SOURCE_MARK = "increment_2a_gtm"   # public.topic/company.source stamp for the additive inserts

PSQL_BIN = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")


# ---------------------------------------------------------------- normalization
def dehyph(s: str | None) -> str:
    """De-hyphenate + lowercase a notion id (the deterministic join key)."""
    return re.sub(r"-", "", (s or "")).lower()


def norm_name(s: str | None) -> str:
    """Exact-name key: lowercase + collapse internal whitespace. NOT fuzzy."""
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def rehyph(s: str | None) -> str | None:
    """Re-hyphenate a 32-hex notion id into Empire's 8-4-4-4-12 stored format."""
    h = re.sub(r"-", "", (s or "")).lower()
    if len(h) != 32 or not re.fullmatch(r"[0-9a-f]{32}", h):
        return s  # leave anything non-canonical untouched
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def sql_str(v) -> str:
    """Literal for psql -f: NULL, or single-quoted with doubled quotes (std strings)."""
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
        sys.exit("REFUSING: target host looks like canonical. 2a rehearses on the twin first; "
                 "set MI_ALLOW_CANONICAL=1 to apply to canonical (only after the twin rehearsal is green).")
    return f"host={host} port={port} user={user} dbname={name} sslmode=require"


def _pgenv() -> dict:
    env = dict(os.environ)
    if "PGPASSWORD" not in env:
        env["PGPASSWORD"] = _require_env("PHANTOM_TEST_DB_PASSWORD")
    return env


# ---------------------------------------------------------------- psql helpers
def psql_read(sql: str) -> list[list[str]]:
    out = subprocess.check_output(
        [PSQL_BIN, _conn_str(), "-tAF", "\t", "-c", sql], env=_pgenv()
    ).decode()
    return [line.split("\t") for line in out.splitlines() if line]


def psql_exec(sql: str) -> None:
    """Run a SQL script (may be a transaction) via stdin, stop on first error."""
    p = subprocess.run(
        [PSQL_BIN, _conn_str(), "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"],
        input=sql.encode(), env=_pgenv(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        sys.exit(f"ERROR psql exec failed:\n{p.stderr.decode('utf-8','replace')}")


# ---------------------------------------------------------------- spine REST
def fetch_spine_entities() -> list[dict]:
    base = _require_env("SUPABASE_SPINE_URL").rstrip("/")
    key = _require_env("SUPABASE_SPINE_SERVICE_KEY")
    url = (base + "/rest/v1/entities"
           "?select=entity_id,entity_type,display_name,source_record_id&limit=2000")
    req = urllib.request.Request(url, headers={
        "apikey": key, "Authorization": f"Bearer {key}",
        "Accept-Profile": "signal", "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ERROR fetching spine entities: {e}")


# ---------------------------------------------------------------- topic crosswalk
def compute_topics():
    gtm = psql_read(
        "select topic_id, coalesce(source_record_id,''), display_name "
        "from topic_intelligence.topics order by topic_id;"
    )
    emp = psql_read(
        "select id, coalesce(notion_page_id,''), name from public.topic order by id;"
    )
    emp_by_notion = {}
    for eid, npid, _name in emp:
        if npid:
            emp_by_notion.setdefault(dehyph(npid), eid)

    linked, gtm_only = [], []
    for tid, srid, dname in gtm:
        k = dehyph(srid) if srid else ""
        if k and k in emp_by_notion:
            linked.append((tid, emp_by_notion[k]))
        else:
            gtm_only.append((tid, srid, dname))
    return gtm, emp, linked, gtm_only


def write_topics(linked, gtm_only) -> dict:
    """Insert the 25 gtm-only topics (idempotent), upsert all 170 crosswalk rows.
       Returns {gtm_topic_id: empire_topic_id} for the inserted 25."""
    stmts = ["begin;"]
    for _tid, srid, dname in gtm_only:
        npid = rehyph(srid)
        # idempotent insert: skip if this notion id OR this name already lives in public.topic
        stmts.append(
            "insert into public.topic (name, notion_page_id, source) "
            f"select {sql_str(dname)}, {sql_str(npid)}, {sql_str(SOURCE_MARK)} "
            "where not exists (select 1 from public.topic "
            f"  where notion_page_id = {sql_str(npid)} or lower(name) = lower({sql_str(dname)}));"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))

    # resolve inserted ids by notion id (re-hyphenated), fallback lower(name)
    inserted_map = {}
    for tid, srid, dname in gtm_only:
        npid = rehyph(srid)
        rows = psql_read(
            "select id from public.topic where notion_page_id = "
            f"{sql_str(npid)} or lower(name) = lower({sql_str(dname)}) limit 1;"
        )
        if not rows:
            sys.exit(f"ERROR: could not resolve inserted public.topic for gtm topic {tid}")
        inserted_map[tid] = rows[0][0]

    # upsert topic_crosswalk (145 notion_id + 25 inserted = 170)
    stmts = ["begin;"]
    for tid, eid in linked:
        stmts.append(
            "insert into topic_intelligence.topic_crosswalk "
            "(gtm_topic_id, empire_topic_id, method, confidence, note) values ("
            f"{sql_str(tid)}, {sql_str(eid)}, 'notion_id', 1.0, "
            "'linked 1:1 to pre-existing public.topic by de-hyphenated notion_page_id') "
            "on conflict (gtm_topic_id) do update set empire_topic_id=excluded.empire_topic_id, "
            "method=excluded.method, confidence=excluded.confidence, note=excluded.note;"
        )
    for tid, srid, dname in gtm_only:
        stmts.append(
            "insert into topic_intelligence.topic_crosswalk "
            "(gtm_topic_id, empire_topic_id, method, confidence, note) values ("
            f"{sql_str(tid)}, {sql_str(inserted_map[tid])}, 'inserted', 1.0, "
            "'gtm-only topic inserted into public.topic (increment 2a additive)') "
            "on conflict (gtm_topic_id) do update set empire_topic_id=excluded.empire_topic_id, "
            "method=excluded.method, confidence=excluded.confidence, note=excluded.note;"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))
    return inserted_map


# ---------------------------------------------------------------- entity crosswalk
def compute_entities(ents):
    comp = psql_read("select id, name, coalesce(notion_page_id,'') from public.company order by id;")
    pers = psql_read("select id, name, coalesce(notion_page_id,'') from public.person order by id;")

    def build(rows):
        by_notion, by_name = {}, {}
        for eid, name, npid in rows:
            if npid:
                by_notion.setdefault(dehyph(npid), eid)
            by_name.setdefault(norm_name(name), eid)
        return by_notion, by_name

    emp = {"company": build(comp), "person": build(pers)}

    notion, exact_name, new = [], [], []
    for e in ents:
        kind = e["entity_type"]
        if kind not in emp:
            sys.exit(f"ERROR: unexpected entity_type {kind!r}")
        by_notion, by_name = emp[kind]
        k = dehyph(e.get("source_record_id"))
        if k and k in by_notion:
            notion.append((e["entity_id"], kind, by_notion[k]))
        else:
            nm = by_name.get(norm_name(e.get("display_name")))
            if nm is not None:
                exact_name.append((e["entity_id"], kind, nm,
                                   e.get("source_record_id"), norm_name(e.get("display_name"))))
            else:
                new.append((e["entity_id"], kind, e.get("display_name"), e.get("source_record_id")))
    return emp, notion, exact_name, new


def write_entities(notion, exact_name, new) -> dict:
    """Insert the net-new entities (idempotent), upsert entity_crosswalk + merge_map.
       Returns {gtm_entity_id: empire_id} for the inserted ones."""
    inserted_map = {}
    stmts = ["begin;"]
    for _gid, kind, name, srid in new:
        npid = rehyph(srid)
        tbl = "public.company" if kind == "company" else "public.person"
        stmts.append(
            f"insert into {tbl} (name, notion_page_id, source) "
            f"select {sql_str(name)}, {sql_str(npid)}, {sql_str(SOURCE_MARK)} "
            f"where not exists (select 1 from {tbl} "
            f"  where notion_page_id = {sql_str(npid)} or lower(name) = lower({sql_str(name)}));"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))

    for gid, kind, name, srid in new:
        npid = rehyph(srid)
        tbl = "public.company" if kind == "company" else "public.person"
        rows = psql_read(
            f"select id from {tbl} where notion_page_id = {sql_str(npid)} "
            f"or lower(name) = lower({sql_str(name)}) limit 1;"
        )
        if not rows:
            sys.exit(f"ERROR: could not resolve inserted {tbl} for gtm entity {gid}")
        inserted_map[gid] = rows[0][0]

    stmts = ["begin;"]
    # 383 notion_id
    for gid, kind, eid in notion:
        stmts.append(
            "insert into topic_intelligence.entity_crosswalk "
            "(gtm_entity_id, empire_id, empire_kind, method, confidence) values ("
            f"{sql_str(gid)}, {sql_str(eid)}, {sql_str(kind)}, 'notion_id', 1.0) "
            "on conflict (gtm_entity_id) do update set empire_id=excluded.empire_id, "
            "empire_kind=excluded.empire_kind, method=excluded.method, confidence=excluded.confidence;"
        )
    # 12 exact_name
    for gid, kind, eid, _srid, _nm in exact_name:
        stmts.append(
            "insert into topic_intelligence.entity_crosswalk "
            "(gtm_entity_id, empire_id, empire_kind, method, confidence) values ("
            f"{sql_str(gid)}, {sql_str(eid)}, {sql_str(kind)}, 'exact_name', 0.90) "
            "on conflict (gtm_entity_id) do update set empire_id=excluded.empire_id, "
            "empire_kind=excluded.empire_kind, method=excluded.method, confidence=excluded.confidence;"
        )
    # 1 inserted
    for gid, kind, _name, _srid in new:
        stmts.append(
            "insert into topic_intelligence.entity_crosswalk "
            "(gtm_entity_id, empire_id, empire_kind, method, confidence) values ("
            f"{sql_str(gid)}, {sql_str(inserted_map[gid])}, {sql_str(kind)}, 'inserted', NULL) "
            "on conflict (gtm_entity_id) do update set empire_id=excluded.empire_id, "
            "empire_kind=excluded.empire_kind, method=excluded.method, confidence=excluded.confidence;"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))

    # merge_map: one row per exact-name recovery (12). evidence is de-identified (no names).
    # A recovery whose surviving Empire row is ALSO the target of a notion match is a genuine
    # gtm-internal duplicate ("false split") — flagged in evidence.collides_with_notion.
    notion_targets = {(kind, eid) for _gid, kind, eid in notion}
    stmts = ["begin;"]
    for gid, kind, eid, srid, nm in exact_name:
        collides = (kind, eid) in notion_targets
        evidence = json.dumps({
            "match": "exact_normalized_name",
            "empire_kind": kind,
            "gtm_source_record_id": srid,
            "collides_with_notion_match": collides,
            "reversible": True,
        })
        stmts.append(
            "insert into topic_intelligence.merge_map "
            "(surviving_id, merged_gtm_id, empire_kind, notion_page_id, method, confidence, evidence) "
            "values ("
            f"{sql_str(eid)}, {sql_str(gid)}, {sql_str(kind)}, {sql_str(rehyph(srid))}, "
            f"'exact_name', 0.90, {sql_str(evidence)}::jsonb) "
            "on conflict (merged_gtm_id) do update set surviving_id=excluded.surviving_id, "
            "empire_kind=excluded.empire_kind, notion_page_id=excluded.notion_page_id, "
            "method=excluded.method, confidence=excluded.confidence, evidence=excluded.evidence;"
        )
    stmts.append("commit;")
    psql_exec("\n".join(stmts))
    return inserted_map


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Build Increment-2a crosswalks + additive inserts.")
    ap.add_argument("--dry-run", action="store_true", help="Compute + print counts. No writes.")
    args = ap.parse_args()

    print(f"TARGET (twin): {os.environ.get('TWIN_DB_HOST', 'db.ytfzzsxcxxbejnowmkmk.supabase.co')}")
    print("Computing crosswalks from live data (twin topics/Empire + spine entities)...\n")

    gtm_topics, emp_topics, linked, gtm_only = compute_topics()
    ents = fetch_spine_entities()
    _emp, notion, exact_name, new = compute_entities(ents)

    empire_only = sum(
        1 for eid, npid, _n in emp_topics
        if npid and dehyph(npid) not in {dehyph(t[1]) for t in gtm_topics if t[1]}
    )
    empire_null_notion = sum(1 for _eid, npid, _n in emp_topics if not npid)

    print("=" * 60)
    print("  COMPUTED COUNTS (vs probe expectation)")
    print("=" * 60)
    print(f"  gtm topics total ............ {len(gtm_topics):>4}   (170)")
    print(f"    linked by notion_id ....... {len(linked):>4}   (145)")
    print(f"    gtm-only -> insert ........ {len(gtm_only):>4}   ( 25)")
    print(f"    Empire-only (unlinked) .... {empire_only:>4}   ( 13)")
    print(f"    Empire NULL notion (flag).. {empire_null_notion:>4}   (  2)")
    print(f"  gtm entities total .......... {len(ents):>4}   (396)")
    print(f"    linked by notion_id ....... {len(notion):>4}   (383)")
    print(f"    recovered by exact_name ... {len(exact_name):>4}   ( 12)")
    print(f"    genuinely new -> insert ... {len(new):>4}   (  1)")
    print("=" * 60)

    if args.dry_run:
        print("\n--dry-run: no writes performed.")
        return 0

    print("\nWriting (idempotent)...")
    t_ins = write_topics(linked, gtm_only)
    print(f"  public.topic          : +{len(t_ins)} gtm-only inserted (idempotent)")
    print(f"  topic_crosswalk       : {len(linked) + len(gtm_only)} rows upserted")
    e_ins = write_entities(notion, exact_name, new)
    print(f"  public.company/person : +{len(e_ins)} net-new inserted (idempotent)")
    print(f"  entity_crosswalk      : {len(notion) + len(exact_name) + len(new)} rows upserted")
    print(f"  merge_map             : {len(exact_name)} rows upserted")
    print("\nDone. Run the validation assertions in supabase/APPLY.md / the runner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
