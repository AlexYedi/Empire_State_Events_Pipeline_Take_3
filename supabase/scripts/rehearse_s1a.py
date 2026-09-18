#!/usr/bin/env python3
"""
rehearse_s1a.py — prove migration 0009 (Knowledge Substrate S1a, ADR-10) on the
Phantom-Test-Case twin before anyone pastes it into prod.

Spec: supabase/SUBSTRATE_S1A_REHEARSAL_RUNBOOK.md · ADR-10 · review
.claude/notes/knowledge-substrate-review-2026-09-18.md (finding 1).

The gate this script enforces (all must pass, in order):
  0  preflight   twin reachable; prerequisites present (documents / doc_chunks /
                 doc_claims / event_kind_enum incl. 'reference' / set_updated_at /
                 vector); twin counts compared to prod (read-only REST) for currency
  1  snapshot A  row counts + schema fingerprint BEFORE
  2  apply 0009
  3  re-apply    a second paste must be a clean no-op (review finding 1c)
  4  verify      staging/s1a_verify.sql must print PASS
  5  negative    plant a fault (drop the one-current-row index); verify MUST fail;
     control     re-apply 0009 restores it; verify passes again
  6  rollback    staging/s1a_rollback.sql
  7  snapshot C  must EQUAL snapshot A — fingerprint and every count (the rollback
                 is PROVEN only if this holds)
  8  (optional)  --leave-applied re-applies 0009 + verify, leaving the twin in the
                 S1a state for substrate.py development

HARD REFUSAL: this script never touches prod (oicikjyzmxqfomrrqkvf). Prod DDL is
Alex's SQL-Editor paste (ADR-10 decision 4). There is no override flag.

Usage:
  python supabase/scripts/rehearse_s1a.py --preflight-only
  python supabase/scripts/rehearse_s1a.py                    # full gate, ends rolled back
  python supabase/scripts/rehearse_s1a.py --leave-applied    # full gate, ends in S1a state
  python supabase/scripts/rehearse_s1a.py --prepare-twin     # apply the doc-KB prerequisites to the twin first
"""
import argparse, json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")
TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
TWIN_HOST = os.environ.get("TWIN_DB_HOST", f"db.{TWIN_REF}.supabase.co")
TWIN_CONN = (f"host={TWIN_HOST} port={os.environ.get('TWIN_DB_PORT', '5432')} "
             f"user={os.environ.get('TWIN_DB_USER', 'postgres')} dbname=postgres "
             "sslmode=require connect_timeout=30")

MIGRATION = os.path.join(SUPA, "migrations", "0009_substrate_s1a_additive.sql")
MIGRATION_S2 = os.path.join(SUPA, "migrations", "0010_substrate_s2_retrieval.sql")
S2_SMOKE = ("select jsonb_typeof(public.entity_neighborhood(array[(select id from public.company limit 1)])) "
            "= 'object' as neighborhood_ok;")
VERIFY    = os.path.join(SUPA, "staging", "s1a_verify.sql")
ROLLBACK  = os.path.join(SUPA, "staging", "s1a_rollback.sql")
PREREQS   = [os.path.join(REPO, ".claude", "references", f)
             for f in ("doc-kb-schema.sql", "doc-kb-migration-a5.sql", "doc-kb-migration-b1.sql")]

COUNT_TABLES = ["company", "person", "topic", "event", "event_entity", "documents", "doc_chunks", "doc_claims"]

# Fingerprint of the public schema. The three deliberate S1a widenings are
# normalised out, so "after rollback" can be compared byte-for-byte with "before".
SNAPSHOT_SQL = """
select 'cols', md5(coalesce(string_agg(
         table_name||'.'||column_name||':'||data_type||':'||
         case when table_name='documents' and column_name='blob_key' then '*' else is_nullable end||':'||
         coalesce(column_default,''), '|' order by table_name, column_name), ''))
  from information_schema.columns where table_schema='public';
select 'constraints', md5(coalesce(string_agg(
         conrelid::regclass::text||'.'||conname||':'||pg_get_constraintdef(oid), '|'
         order by conrelid::regclass::text, conname), ''))
  from pg_constraint
 where connamespace='public'::regnamespace
   and conname not in ('event_kind_enum','documents_source_type_check');
select 'indexes', md5(coalesce(string_agg(indexname||':'||indexdef, '|' order by indexname), ''))
  from pg_indexes where schemaname='public';
select 'triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname, '|'
         order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger where not tgisinternal
   and tgrelid in (select oid from pg_class where relnamespace='public'::regnamespace);
select 'functions', md5(coalesce(string_agg(p.oid::regprocedure::text, '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p where p.pronamespace = 'public'::regnamespace;
select 'tables', string_agg(table_name, ',' order by table_name)
  from information_schema.tables where table_schema='public' and table_type='BASE TABLE';
""" + "\n".join(f"select 'count.{t}', count(*)::text from public.{t};" for t in COUNT_TABLES) + """
select 'kinds', string_agg(kind||'='||n, ',' order by kind)
  from (select kind, count(*) n from public.event group by kind) k;
"""

PREFLIGHT_SQL = """
select 'has.documents',  (to_regclass('public.documents')  is not null)::text;
select 'has.doc_chunks', (to_regclass('public.doc_chunks') is not null)::text;
select 'has.doc_claims', (to_regclass('public.doc_claims') is not null)::text;
select 'has.set_updated_at', (count(*) > 0)::text from pg_proc where proname='set_updated_at';
select 'has.vector', (count(*) > 0)::text from pg_extension where extname='vector';
select 'kind_check', coalesce((select pg_get_constraintdef(oid) from pg_constraint
                                where conname='event_kind_enum' limit 1), 'MISSING');
"""


def load_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v.strip().strip('"').strip("'")
    return env


ENV = load_env(os.path.join(REPO, ".env"))


def refuse_prod():
    if PROD_REF in TWIN_CONN or TWIN_REF not in TWIN_CONN:
        sys.exit(f"REFUSED: target must be the twin ({TWIN_REF}). This script never touches prod.")


def psql(args, stdin=None, check=True):
    pw = ENV.get("PHANTOM_TEST_DB_PASSWORD") or os.environ.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set (.env). Is .env symlinked into this worktree?")
    env = dict(os.environ, PGPASSWORD=pw)
    p = subprocess.run([PSQL, TWIN_CONN, "-v", "ON_ERROR_STOP=1"] + args,
                       input=stdin, text=True, capture_output=True, env=env)
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode}) on {args}")
    return p


def kv(sql):
    out = psql(["-tA", "-F", "\t", "-c", sql]).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def run_file(path, label):
    p = psql(["-f", path], check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    return ok, p


def verify(expect_pass=True):
    p = psql(["-f", VERIFY], check=False)
    text = p.stdout + p.stderr
    passed = p.returncode == 0 and "S1a VERIFY: PASS" in text
    line = next((l for l in text.splitlines() if "S1a VERIFY" in l or "FAIL:" in l), text.strip()[-300:])
    print(f"  verify -> {'PASS' if passed else 'FAIL'} :: {line.strip()}")
    return passed, text


def prod_counts():
    key = ENV.get("SUPABASE_API_KEY")
    if not key:
        return {}
    out = {}
    for t in COUNT_TABLES:
        req = urllib.request.Request(f"https://{PROD_REF}.supabase.co/rest/v1/{t}?select=id",
                                     headers={"apikey": key, "Authorization": f"Bearer {key}",
                                              "Prefer": "count=exact", "Range": "0-0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                out[t] = r.headers.get("content-range", "?/?").split("/")[-1]
        except Exception as e:  # prod read is advisory only
            out[t] = f"err:{type(e).__name__}"
    return out


def diff(a, b):
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--prepare-twin", action="store_true",
                    help="apply doc-KB prerequisites (doc-kb-schema, a5, b1) to the twin if missing")
    ap.add_argument("--leave-applied", action="store_true")
    ap.add_argument("--reset-first", action="store_true",
                    help="run staging/s1a_rollback.sql before snapshot A (after an interrupted rehearsal); "
                         "idempotent — every statement is 'if exists'")
    a = ap.parse_args()
    refuse_prod()
    if a.reset_first:
        print("[-] reset: rolling back any partial S1a/S2 state first")
        if not run_file(ROLLBACK, "s1a_rollback.sql (reset)")[0]:
            sys.exit("reset failed")

    print(f"TARGET twin: {TWIN_HOST}")
    print("\n[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:22s} {v}")
    missing = [k for k in ("has.documents", "has.doc_chunks", "has.doc_claims", "has.set_updated_at", "has.vector")
               if pf.get(k) != "true"] + ([] if "reference" in pf.get("kind_check", "") else ["kind 'reference'"])
    if missing and a.prepare_twin:
        print(f"  preparing twin — applying doc-KB prerequisites for: {missing}")
        for f in PREREQS:
            ok, p = run_file(f, os.path.basename(f))
            if not ok:
                sys.stderr.write(p.stderr[-1500:])
                sys.exit("prerequisite failed")
        pf = kv(PREFLIGHT_SQL)
        missing = [k for k in ("has.documents", "has.doc_chunks", "has.doc_claims", "has.set_updated_at", "has.vector")
                   if pf.get(k) != "true"] + ([] if "reference" in pf.get("kind_check", "") else ["kind 'reference'"])
    if missing:
        sys.exit(f"PREFLIGHT FAIL — twin lacks prerequisites: {missing}. Re-run with --prepare-twin.")

    twin = kv(SNAPSHOT_SQL)
    prod = prod_counts()
    print("  currency (twin vs prod, read-only):")
    stale = False
    for t in COUNT_TABLES:
        tv, pv = twin.get(f"count.{t}"), prod.get(t, "?")
        flag = "" if tv == pv else "   <- differs"
        stale |= bool(flag)
        print(f"    {t:14s} twin={tv:>6}  prod={pv:>6}{flag}")
    if stale:
        print("  NOTE: twin data differs from prod. The migration is schema-only, so the gate is still "
              "meaningful; refresh with supabase/scripts/load_twin.py for full fidelity.")
    if a.preflight_only:
        return

    print("\n[1] snapshot A (before)")
    snap_a = kv(SNAPSHOT_SQL)
    print(f"  tables: {snap_a.get('tables')}")

    print("\n[2] apply 0009")
    if not run_file(MIGRATION, "0009_substrate_s1a_additive.sql")[0]:
        sys.exit("GATE FAIL at step 2")

    print("\n[3] re-apply 0009 (must be a clean no-op)")
    snap_b1 = kv(SNAPSHOT_SQL)
    if not run_file(MIGRATION, "0009 second paste")[0]:
        sys.exit("GATE FAIL at step 3 — S1a is not re-runnable")
    d = diff(snap_b1, kv(SNAPSHOT_SQL))
    if d:
        sys.exit(f"GATE FAIL at step 3 — second paste changed state: {d}")
    print("  OK  state identical after second paste")

    print("\n[4] verify")
    if not verify()[0]:
        sys.exit("GATE FAIL at step 4")

    print("\n[5] negative control — plant a fault, verify must catch it")
    psql(["-c", "drop index public.documents_external_ref_current_uq;"])
    caught, text = verify()
    if caught or "is_current" not in text:
        sys.exit("GATE FAIL at step 5 — verify did not catch the planted fault; the gate is not a gate")
    print("  OK  fault caught")
    run_file(MIGRATION, "0009 restore after fault")
    if not verify()[0]:
        sys.exit("GATE FAIL at step 5 — re-apply did not restore a passing state")

    print("\n[5b] apply 0010 (S2 retrieval RPCs) + smoke")
    if not run_file(MIGRATION_S2, "0010_substrate_s2_retrieval.sql")[0]:
        sys.exit("GATE FAIL at step 5b — S2 did not apply")
    if not run_file(MIGRATION_S2, "0010 second paste")[0]:
        sys.exit("GATE FAIL at step 5b — S2 is not re-runnable")
    smoke = psql(["-tA", "-c", S2_SMOKE]).stdout.strip()
    if smoke != "t":
        sys.exit(f"GATE FAIL at step 5b — entity_neighborhood smoke returned {smoke!r}")
    print("  OK  entity_neighborhood returns an object")

    print("\n[6] rollback (S2 functions + S1a)")
    if not run_file(ROLLBACK, "s1a_rollback.sql")[0]:
        sys.exit("GATE FAIL at step 6")

    print("\n[7] snapshot C must equal snapshot A")
    snap_c = kv(SNAPSHOT_SQL)
    d = diff(snap_a, snap_c)
    if d:
        for k, (x, y) in d.items():
            print(f"  DIFF {k}: before={x} after={y}")
        sys.exit("GATE FAIL at step 7 — rollback is NOT proven")
    print("  OK  schema fingerprint + all counts identical — ROLLBACK PROVEN")

    if a.leave_applied:
        print("\n[8] re-apply for development (--leave-applied)")
        run_file(MIGRATION, "0009")
        run_file(MIGRATION_S2, "0010")
        if not verify()[0]:
            sys.exit("re-apply verify failed")

    print("\nS1a + S2 REHEARSAL: GREEN — safe for Alex to paste 0009 then 0010 into prod (The-Prod-Brain) "
          "and then run staging/s1a_verify.sql there.")


if __name__ == "__main__":
    main()
