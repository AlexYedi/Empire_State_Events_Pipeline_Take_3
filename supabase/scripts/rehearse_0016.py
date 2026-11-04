#!/usr/bin/env python3
"""
rehearse_0016.py — prove migration 0016 (MI semantic layer, ADR-13) on the Phantom-Test-Case
twin before Alex pastes it into prod (CLAUDE.md invariant 2). Shape copied from rehearse_s1a.py.

The verify checks and the rollback are NOT separate files: they are parsed out of the
migration's own `-- VERIFY:BEGIN/END`, `-- VERIFY_TWIN:BEGIN/END` and `-- ROLLBACK:BEGIN/END`
blocks, so the file Alex pastes and the file this script proves are the same bytes.
VERIFY is read-only (it is also what Alex runs on prod). VERIFY_TWIN is behavioural and twin-only:
it exercises the topic -> membership sync triggers inside a transaction that is rolled back.
Checks named info_* are informational: printed, never gating.

Gates (all must pass, in order):
  0  preflight     twin reachable; prerequisites present (public.topic cluster columns,
                   topic_intelligence.topic_cluster, public.claim, 0012's compute function,
                   pipeline_writer + postgres SET grant); no 0016 objects yet (else --reset-first);
                   baseline nightly compute DRY-RUN (read-only) so a red chain later is attributable
  1  snapshot A    schema fingerprint (public, topic_intelligence, mi) + row counts BEFORE
  2  apply 0016
  3  re-apply      a second paste must be a clean no-op (fingerprint + counts unchanged,
                   including row counts of the four tables 0016 creates)
  4  verify        every check in VERIFY + VERIFY_TWIN returns t (info_* rows printed only)
  5  negative      planted faults, each one alone; verify MUST fail on the named check;
     control       re-applying 0016 must restore a passing verify:
                     5a drop the one-open-row index      -> membership_one_open_index
                     5b grant EXECUTE on mi_slice to anon -> mi_slice_exec_denied
                     5c drop the topic UPDATE sync trigger -> trig_reassign_parity
  6  nightly chain (lesson L7) topic_intel_compute.py --apply against the twin, then
                   healthcheck_2b.py; both must exit 0 with 0016 applied
  7  rollback      the ROLLBACK block
  8  snapshot C    must EQUAL snapshot A (fingerprint and every public count). The chain's own
                   writes to topic_intelligence.{topic_trend,topic_pair_metric,ingestion_run}
                   are data, not schema, and are reported, not compared.
  9  (optional)    --leave-applied re-applies 0016 + verify, leaving the twin in the 0016 state

HARD REFUSAL: this script only ever connects to the twin's session pooler, as the twin's tenant
user, with the twin's password. Host and user are constants (no env overrides) and are checked
before every connection. Child processes (the nightly chain) get an environment scrubbed of
every variable that names or holds prod material. There is no override flag.

Default is --dry-run: print the plan from the migration file and exit, with NO connection.

Usage:
  python supabase/scripts/rehearse_0016.py                     # dry run: plan only, no connection
  python supabase/scripts/rehearse_0016.py --preflight-only    # connect, preflight, stop
  python supabase/scripts/rehearse_0016.py --execute           # full gate, ends rolled back
  python supabase/scripts/rehearse_0016.py --execute --leave-applied
  python supabase/scripts/rehearse_0016.py --execute --reset-first   # after an interrupted run

Env: PHANTOM_TEST_DB_PASSWORD (from .env or the environment; never printed). PSQL_BIN optional.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")
PY = sys.executable

TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
TWIN_HOST = "aws-1-us-east-2.pooler.supabase.com"
TWIN_USER = f"postgres.{TWIN_REF}"
TWIN_CONN = (f"host={TWIN_HOST} port=5432 user={TWIN_USER} dbname=postgres "
             "sslmode=require connect_timeout=30")
PROD_SECRET_KEYS = {"MARKET_INTEL_SUPABASE_DB_PASSWORD", "SUPABASE_API_KEY", "MI_SUPABASE_URL",
                    "MI_SUPABASE_ANON_KEY", "MI_DB_DSN", "DATABASE_URL", "PGHOST", "PGUSER",
                    "PGSERVICE", "PGPASSFILE"}

MIGRATION = os.path.join(SUPA, "migrations", "0016_mi_semantic_layer.sql")
COMPUTE = os.path.join(HERE, "topic_intel_compute.py")
HEALTHCHECK = os.path.join(HERE, "healthcheck_2b.py")

FAULTS = [
    ("5a", "drop index public.topic_cluster_membership_one_open_uq;",
     "membership_one_open_index"),
    ("5b", "grant execute on function public.mi_slice(text, jsonb) to anon;",
     "mi_slice_exec_denied"),
    ("5c", "drop trigger topic_membership_sync_upd on public.topic;",
     "trig_reassign_parity"),
]

SCHEMAS = "('public','topic_intelligence','mi')"
COUNT_TABLES = ["public.company", "public.person", "public.topic", "public.event",
                "public.event_entity", "public.claim", "public.claim_entity", "public.documents",
                "topic_intelligence.topic_cluster"]
# The four tables 0016 creates: counted after apply so the re-apply no-op is checked on the rows
# themselves (seed not duplicated, registry not re-inserted), not only on the schema fingerprint.
NEW_TABLES = ["public.topic_cluster_membership", "public.company_segment_history",
              "public.lane_registry", "public.lane_run"]
NEW_COUNTS_SQL = "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in NEW_TABLES)
# ADR-13's one assigned_by vocabulary (must match the CHECK in 0016 and the sync trigger).
ASSIGNED_BY_VOCAB = ("bootstrap", "llm", "embedding_auto", "session", "human", "merge")

CHAIN_TABLES = ["topic_intelligence.topic_trend", "topic_intelligence.topic_pair_metric",
                "topic_intelligence.ingestion_run"]

# Fingerprint of everything 0016 could touch: schemas + their ACLs, columns, constraints,
# indexes, triggers, functions (+ ACL, definer, config), relations (+ RLS, ACL), policies.
SNAPSHOT_SQL = f"""
select 'schemas', md5(coalesce(string_agg(nspname||':'||coalesce(nspacl::text,''), '|' order by nspname), ''))
  from pg_namespace where nspname in {SCHEMAS};
select 'cols', md5(coalesce(string_agg(table_schema||'.'||table_name||'.'||column_name||':'||data_type||':'||
         is_nullable||':'||coalesce(column_default,''), '|' order by table_schema, table_name, column_name), ''))
  from information_schema.columns where table_schema in {SCHEMAS};
select 'constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||pg_get_constraintdef(oid), '|'
         order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace in (select oid from pg_namespace where nspname in {SCHEMAS});
select 'indexes', md5(coalesce(string_agg(schemaname||'.'||indexname||':'||indexdef, '|' order by schemaname, indexname), ''))
  from pg_indexes where schemaname in {SCHEMAS};
select 'triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname, '|' order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger where not tgisinternal
   and tgrelid in (select c.oid from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname in {SCHEMAS});
select 'functions', md5(coalesce(string_agg(p.oid::regprocedure::text||':'||coalesce(p.proacl::text,'')||':'||p.prosecdef||':'||
         coalesce(array_to_string(p.proconfig, ','),''), '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in {SCHEMAS};
select 'relations', md5(coalesce(string_agg(n.nspname||'.'||c.relname||':'||c.relkind||':'||c.relrowsecurity||':'||
         coalesce(c.relacl::text,''), '|' order by n.nspname, c.relname), ''))
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in {SCHEMAS} and c.relkind in ('r','v','m','p');
select 'policies', md5(coalesce(string_agg(schemaname||'.'||tablename||'.'||policyname, '|' order by 1), ''))
  from pg_policies where schemaname in {SCHEMAS};
select 'tables', string_agg(n.nspname||'.'||c.relname, ',' order by n.nspname, c.relname)
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in {SCHEMAS} and c.relkind = 'r';
""" + "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in COUNT_TABLES)

CHAIN_COUNTS_SQL = "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in CHAIN_TABLES)

PREFLIGHT_SQL = """
select 'has.topic.cluster_id', (count(*) = 3)::text from information_schema.columns
 where table_schema='public' and table_name='topic'
   and column_name in ('cluster_id','cluster_assignment_confidence','cluster_assigned_by');
select 'has.topic_cluster', (to_regclass('topic_intelligence.topic_cluster') is not null)::text;
select 'has.claim', (to_regclass('public.claim') is not null)::text;
select 'has.compute_0012', (to_regprocedure('topic_intelligence.compute_topic_intelligence(date,text)') is not null)::text;
select 'has.pipeline_writer', (count(*) = 1)::text from pg_roles where rolname = 'pipeline_writer';
select 'has.postgres_set_pw', (count(*) > 0)::text from pg_auth_members am
  join pg_roles r on r.oid = am.roleid join pg_roles m on m.oid = am.member
 where r.rolname = 'pipeline_writer' and m.rolname = 'postgres' and am.set_option;
select 'has.service_role', (count(*) = 1)::text from pg_roles where rolname = 'service_role';
select 'clean.no_mi', (to_regnamespace('mi') is null)::text;
select 'clean.no_membership', (to_regclass('public.topic_cluster_membership') is null)::text;
select 'clean.no_sync_trigger', (count(*) = 0)::text from pg_trigger
 where tgrelid = 'public.topic'::regclass and tgname like 'topic_membership_sync%';
select 'clean.no_signal_type', (count(*) = 0)::text from information_schema.columns
 where table_schema='public' and table_name='event' and column_name='signal_type';
select 'info.assigned_live_topics', count(*)::text from public.topic
 where cluster_id is not null and not coalesce(metadata ? 'merged_into', false);
select 'info.assigned_by_values', coalesce(string_agg(distinct coalesce(cluster_assigned_by, '<null>'), ','), '')
  from public.topic where cluster_id is not null;
"""
REQUIRED = ["has.topic.cluster_id", "has.topic_cluster", "has.claim", "has.compute_0012",
            "has.pipeline_writer", "has.postgres_set_pw", "has.service_role"]
CLEAN = ["clean.no_mi", "clean.no_membership", "clean.no_sync_trigger", "clean.no_signal_type"]


# ----------------------------------------------------------------------------- file parsing
def read_migration() -> str:
    with open(MIGRATION, encoding="utf-8") as fh:
        return fh.read()


def commented_block(src: str, tag: str) -> str:
    m = re.search(rf"^-- {tag}:BEGIN\n(.*?)^-- {tag}:END", src, re.S | re.M)
    if not m:
        sys.exit(f"migration has no -- {tag}:BEGIN/END block")
    return "\n".join(line[3:] if line.startswith("-- ") else line.lstrip("-")
                     for line in m.group(1).splitlines())


def verify_names(sql: str) -> list[str]:
    return re.findall(r"^select '([a-z0-9_]+)'", sql, re.M)


# ----------------------------------------------------------------------------- env + psql
def load_env(path: str) -> dict:
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(os.path.join(REPO, ".env"))


def refuse_non_twin(conninfo: str = TWIN_CONN) -> None:
    host = re.search(r"\bhost=(\S+)", conninfo)
    user = re.search(r"\buser=(\S+)", conninfo)
    if (PROD_REF in conninfo or not host or host.group(1) != TWIN_HOST
            or not user or user.group(1) != TWIN_USER):
        sys.exit(f"REFUSED: target must be the twin pooler {TWIN_HOST} as {TWIN_USER}. "
                 "This script never touches prod.")


def twin_password() -> str:
    pw = ENV.get("PHANTOM_TEST_DB_PASSWORD") or os.environ.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set (.env). Is .env symlinked into this worktree?")
    prod_pw = ENV.get("MARKET_INTEL_SUPABASE_DB_PASSWORD") or os.environ.get("MARKET_INTEL_SUPABASE_DB_PASSWORD")
    if prod_pw and pw == prod_pw:
        sys.exit("REFUSED: the twin password equals the prod password; refusing to guess which DB this is.")
    return pw


def child_env() -> dict:
    """os.environ minus anything that names or holds prod material, plus the twin target."""
    env = {k: v for k, v in os.environ.items()
           if k not in PROD_SECRET_KEYS and PROD_REF not in v}
    env.pop("PGOPTIONS", None)
    env.update(PGPASSWORD=twin_password(), MI_DB_DSN=TWIN_CONN, PSQL_BIN=PSQL)
    return env


def psql(args: list[str], stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    refuse_non_twin()
    p = subprocess.run([PSQL, TWIN_CONN, "-X", "-v", "ON_ERROR_STOP=1"] + args,
                       input=stdin, text=True, capture_output=True, env=child_env())
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode})")
    return p


def kv(sql: str) -> dict:
    out = psql(["-tA", "-F", "\t"], stdin=sql).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def run_sql(sql: str, label: str) -> bool:
    p = psql([], stdin=sql, check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        sys.stderr.write(p.stderr[-1500:])
    return ok


def apply(label: str) -> bool:
    refuse_non_twin()
    p = subprocess.run([PSQL, TWIN_CONN, "-X", "-v", "ON_ERROR_STOP=1", "-f", MIGRATION],
                       text=True, capture_output=True, env=child_env())
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        sys.stderr.write(p.stderr[-1500:])
    return ok


def verify(verify_sql: str, expected: list[str]) -> tuple[bool, list[str]]:
    p = psql(["-tA", "-F", "\t"], stdin=verify_sql, check=False)
    got = dict(line.split("\t", 1) for line in p.stdout.splitlines() if "\t" in line)
    for n in expected:
        if n.startswith("info_"):
            print(f"  info  {n} = {got.get(n, '<missing>')}")
    failed = [n for n in expected if not n.startswith("info_") and got.get(n) != "t"]
    if p.returncode != 0:
        failed.append(f"<psql error: {p.stderr.strip().splitlines()[-1] if p.stderr.strip() else p.returncode}>")
    gated = [n for n in expected if not n.startswith("info_")]
    print(f"  verify -> {'PASS' if not failed else 'FAIL'} ({len(gated) - len([f for f in failed if not f.startswith('<')])}/{len(gated)})"
          + (f" :: failed {failed}" if failed else ""))
    return not failed, failed


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def run_child(script: str, args: list[str], label: str) -> bool:
    refuse_non_twin(child_env()["MI_DB_DSN"])
    p = subprocess.run([PY, script] + args, text=True, capture_output=True, env=child_env(), cwd=REPO)
    tail = (p.stdout + p.stderr).strip().splitlines()[-6:]
    print(f"  {'OK ' if p.returncode == 0 else 'ERR'} {label} (rc={p.returncode})")
    for line in tail:
        print(f"      {line}")
    return p.returncode == 0


# ----------------------------------------------------------------------------- plan
def plan(src: str, verify_sql: str, rollback_sql: str) -> None:
    sha = hashlib.sha256(src.encode()).hexdigest()[:16]
    names = verify_names(verify_sql)
    print("rehearse_0016 — DRY RUN (no connection made)\n")
    print(f"  target           twin {TWIN_REF} via {TWIN_HOST} as {TWIN_USER} (hard-coded; prod refused)")
    print(f"  migration        {os.path.relpath(MIGRATION, REPO)}  sha256:{sha}…  {len(src.splitlines())} lines")
    print(f"  verify checks    {len(names)}: {', '.join(names)}")
    print(f"  rollback stmts   {len([l for l in rollback_sql.splitlines() if l.strip()])}")
    print("  planted faults   " + "; ".join(f"{s} {sql.strip()} -> must fail {n}" for s, sql, n in FAULTS))
    print(f"  nightly chain    {os.path.relpath(COMPUTE, REPO)} --apply --runtime manual ; "
          f"{os.path.relpath(HEALTHCHECK, REPO)}  (MI_DB_DSN = twin, prod env scrubbed)")
    print("\n  steps: 0 preflight · 1 snapshot A · 2 apply · 3 re-apply no-op · 4 verify · "
          "5 planted faults + restore · 6 nightly chain · 7 rollback · 8 snapshot C == A")
    print("\n  run with --execute to perform it (twin only).")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Rehearse migration 0016 on the twin.")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only (default)")
    ap.add_argument("--execute", action="store_true", help="run the full gate against the twin")
    ap.add_argument("--preflight-only", action="store_true", help="connect, run preflight, stop")
    ap.add_argument("--leave-applied", action="store_true", help="end in the 0016 state (with --execute)")
    ap.add_argument("--reset-first", action="store_true",
                    help="run the ROLLBACK block before preflight (after an interrupted run); idempotent")
    a = ap.parse_args()

    src = read_migration()
    verify_sql = commented_block(src, "VERIFY") + "\n" + commented_block(src, "VERIFY_TWIN")
    rollback_sql = commented_block(src, "ROLLBACK")
    expected = verify_names(verify_sql)
    if not expected:
        sys.exit("VERIFY block parsed to zero checks")

    if not (a.execute or a.preflight_only) or a.dry_run:
        plan(src, verify_sql, rollback_sql)
        return 0

    refuse_non_twin()
    print(f"TARGET twin: {TWIN_HOST} as {TWIN_USER}")
    if a.reset_first:
        print("\n[-] reset: running the ROLLBACK block first")
        if not run_sql(rollback_sql, "rollback (reset)"):
            sys.exit("reset failed")

    print("\n[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:28s} {v}")
    missing = [k for k in REQUIRED if pf.get(k) != "true"]
    if missing:
        sys.exit(f"PREFLIGHT FAIL — twin lacks prerequisites: {missing}")
    dirty = [k for k in CLEAN if pf.get(k) != "true"]
    if dirty:
        sys.exit(f"PREFLIGHT FAIL — twin already has 0016 objects {dirty}; re-run with --reset-first")
    seen = [v for v in pf.get("info.assigned_by_values", "").split(",") if v]
    outside = [v for v in seen if v != "<null>" and v not in ASSIGNED_BY_VOCAB]
    if outside:
        sys.exit(f"PREFLIGHT FAIL — topic.cluster_assigned_by values outside the ADR-13 vocabulary "
                 f"{ASSIGNED_BY_VOCAB}: {outside}. The seed (and every later topic write, via the sync "
                 "trigger) would raise. Widen the vocabulary in 0016 + ADR-13, or fix the rows, first.")
    if pf.get("info.assigned_live_topics", "0") == "0":
        sys.exit("PREFLIGHT FAIL — twin has no assigned topics; the seed and theme_as_of checks would be "
                 "vacuous. Refresh with supabase/scripts/load_twin.py first.")
    print("  baseline nightly compute (dry-run, read-only):")
    baseline_ok = run_child(COMPUTE, ["--dry-run"], "topic_intel_compute.py --dry-run (before 0016)")
    if not baseline_ok:
        print("  NOTE: the chain is already red on the twin BEFORE 0016; step 6 cannot attribute a failure.")
    if a.preflight_only:
        return 0

    print("\n[1] snapshot A (before)")
    snap_a = kv(SNAPSHOT_SQL)
    print(f"  tables: {snap_a.get('tables')}")

    print("\n[2] apply 0016")
    if not apply("0016_mi_semantic_layer.sql"):
        sys.exit("GATE FAIL at step 2")

    print("\n[3] re-apply 0016 (must be a clean no-op)")
    snap_b1 = {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS_SQL)}
    print("  new-table counts after first apply: " +
          ", ".join(f"{k.split('.', 1)[1]}={v}" for k, v in snap_b1.items() if k.startswith("count.public.") and
                    k.split(".", 1)[1] in NEW_TABLES))
    if not apply("0016 second paste"):
        sys.exit("GATE FAIL at step 3 — 0016 is not re-runnable")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS_SQL)})
    if d:
        sys.exit(f"GATE FAIL at step 3 — second paste changed state: {d}")
    print("  OK  state identical after second paste")

    print("\n[4] verify")
    if not verify(verify_sql, expected)[0]:
        sys.exit("GATE FAIL at step 4")

    print("\n[5] negative controls — plant a fault, verify must catch it, re-apply must restore")
    for step, fault_sql, must_fail in FAULTS:
        print(f"  [{step}] plant: {fault_sql}")
        psql([], stdin=fault_sql)
        ok, failed = verify(verify_sql, expected)
        if ok or must_fail not in failed:
            sys.exit(f"GATE FAIL at step {step} — verify did not flag {must_fail}; the gate is not a gate")
        print(f"  OK  fault caught by {must_fail}")
        if not apply(f"0016 restore after {step}") or not verify(verify_sql, expected)[0]:
            sys.exit(f"GATE FAIL at step {step} — re-apply did not restore a passing state")

    print("\n[6] full nightly chain on the twin (lesson L7)")
    chain_before = kv(CHAIN_COUNTS_SQL)
    if not run_child(COMPUTE, ["--apply", "--runtime", "manual"], "topic_intel_compute.py --apply"):
        sys.exit("GATE FAIL at step 6 — nightly compute failed with 0016 applied"
                 + ("" if baseline_ok else " (it was already red before 0016)"))
    if not run_child(HEALTHCHECK, [], "healthcheck_2b.py"):
        sys.exit("GATE FAIL at step 6 — health check failed with 0016 applied")
    print(f"  chain writes (data, informational): {diff(chain_before, kv(CHAIN_COUNTS_SQL)) or 'none'}")
    if not verify(verify_sql, expected)[0]:
        sys.exit("GATE FAIL at step 6 — verify regressed after the nightly chain")

    print("\n[7] rollback")
    if not run_sql(rollback_sql, "ROLLBACK block"):
        sys.exit("GATE FAIL at step 7")

    print("\n[8] snapshot C must equal snapshot A")
    d = diff(snap_a, kv(SNAPSHOT_SQL))
    if d:
        for k, (x, y) in d.items():
            print(f"  DIFF {k}: before={x} after={y}")
        sys.exit("GATE FAIL at step 8 — rollback is NOT proven")
    print("  OK  schema fingerprint + all counts identical — ROLLBACK PROVEN")

    if a.leave_applied:
        print("\n[9] re-apply for development (--leave-applied)")
        if not apply("0016") or not verify(verify_sql, expected)[0]:
            sys.exit("re-apply verify failed")

    print("\n0016 REHEARSAL: GREEN — safe for Alex to paste 0016 into prod (The-Prod-Brain), then run the "
          "VERIFY block there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
