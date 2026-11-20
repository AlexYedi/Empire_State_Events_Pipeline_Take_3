#!/usr/bin/env python3
"""
rehearse_0027.py — prove migration 0027 (retire schema pre2b + drop FK topic_intelligence.topics.topics_cluster_id_fkey;
YED-298) on the Phantom-Test-Case twin before Alex pastes it into prod (invariant 2). The YED-311 policy/grant part is
HELD (see the migration header), so this harness also proves those policies and grants are left unchanged.
Twin-only constants and refusal logic are byte-identical to rehearse_0025.py (scrubbed child env, no override flag).

Gates (all must pass, in order):
  0  preflight     twin reachable; pre2b present with the FK (else --reset-first restores it from the export);
                   prints staging/0027_verify.sql step 0 (exact counts + row md5) for comparison with prod
  1  snapshot A    fingerprint: pre2b rels/ACL/RLS/columns/constraints/indexes/policies/triggers + per-table row md5;
                   topic_intelligence constraints/policies/ACLs + topics md5; public schema (0025/0026 objects)
  1a cold export   pg_dump --schema=pre2b from the twin into the export path (mode 600; never in git)
  1b guard probes  (rolled back) the migration's PART 1 must REFUSE when (i) a view outside pre2b reads
                   pre2b.person, (ii) a function outside pre2b names pre2b in its body; and pass on the clean twin
  2  apply 0027    the migration file verbatim
  3  re-apply      second paste is a clean no-op (fingerprint unchanged)
  4  verify        staging/0027_verify.sql step 1: every row ok = t
  4b roles         as service_role and as anon, row count (or 'denied') on both signal_read views and the 3 live
                   base tables must equal the gate-1 baseline (anon on the views = the gtm-os-hub /signal read path;
                   service_role is denied on the views by 0002's grants, before and after)
  5  rollback      psql -1 -f <export>, then re-add topics_cluster_id_fkey
  6  snapshot C    must EQUAL snapshot A: ROLLBACK PROVEN only if so
  (--leave-applied re-applies 0027 + verify at the end.)

Usage:
  python3 supabase/scripts/rehearse_0027.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0027.py --preflight-only
  python3 supabase/scripts/rehearse_0027.py --execute         # full gate, ends rolled back
  python3 supabase/scripts/rehearse_0027.py --execute --reset-first
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "/opt/homebrew/opt/libpq/bin/psql")

TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
TWIN_HOST = "aws-1-us-east-2.pooler.supabase.com"
TWIN_USER = f"postgres.{TWIN_REF}"
TWIN_CONN = (f"host={TWIN_HOST} port=5432 user={TWIN_USER} dbname=postgres "
             "sslmode=require connect_timeout=30")
PROD_SECRET_KEYS = {"MARKET_INTEL_SUPABASE_DB_PASSWORD", "SUPABASE_API_KEY", "MI_SUPABASE_URL",
                    "MI_SUPABASE_ANON_KEY", "MI_DB_DSN", "DATABASE_URL", "PGHOST", "PGUSER",
                    "PGSERVICE", "PGPASSFILE"}

PG_DUMP = os.environ.get("PG_DUMP_BIN", "/opt/homebrew/opt/libpq/bin/pg_dump")
MIGRATION = os.path.join(SUPA, "migrations", "0027_retire_pre2b.sql")
VERIFY = os.path.join(SUPA, "staging", "0027_verify.sql")
EXPORT_DEFAULT = "/private/tmp/claude-501/pre2b_export/pre2b_export.sql"
PRE2B_TABLES = ["company", "event", "event_entity", "ingestion_run", "person", "topic",
                "topic_cluster", "topic_pair_metric", "topic_trend"]
FK_RESTORE = ("alter table topic_intelligence.topics add constraint topics_cluster_id_fkey "
              "foreign key (cluster_id) references pre2b.topic_cluster(cluster_id);")

ROW_MD5 = ("select 'rows.'||n.nspname||'.'||c.relname, (xpath('/row/h/text()', query_to_xml(format("
           "'select count(*)||'':''||md5(coalesce(string_agg(x::text, ''|'' order by x::text), '''')) as h "
           "from %I.%I x', n.nspname, c.relname), false, true, '')))[1]::text "
           "from pg_class c join pg_namespace n on n.oid = c.relnamespace "
           "where (n.nspname = 'pre2b' and c.relkind = 'r') "
           "   or (n.nspname = 'topic_intelligence' and c.relname = 'topics');")
SNAPSHOT_SQL = """
select 'pre2b.ns', coalesce((select nspowner::regrole::text||':'||coalesce(nspacl::text,'') from pg_namespace
         where nspname = 'pre2b'), 'ABSENT');
select 'pre2b.rels', md5(coalesce(string_agg(relname||':'||relkind::text||':'||relowner::regrole::text||':'||
         coalesce(relacl::text,'')||':'||relrowsecurity::text||':'||relforcerowsecurity::text, '|' order by relname), ''))
  from pg_class where relnamespace = to_regnamespace('pre2b');
select 'pre2b.cols', md5(coalesce(string_agg(table_name||'.'||column_name||':'||data_type||':'||is_nullable||':'||
         coalesce(column_default,''), '|' order by table_name, column_name), ''))
  from information_schema.columns where table_schema = 'pre2b';
select 'pre2b.constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||convalidated::text||':'||
         pg_get_constraintdef(oid), '|' order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace = to_regnamespace('pre2b');
select 'pre2b.indexes', md5(coalesce(string_agg(indexname||':'||indexdef, '|' order by indexname), ''))
  from pg_indexes where schemaname = 'pre2b';
select 'pre2b.policies', md5(coalesce(string_agg(tablename||'.'||policyname||':'||permissive||':'||roles::text||':'||
         cmd||':'||coalesce(qual,'')||':'||coalesce(with_check,''), '|' order by tablename, policyname), ''))
  from pg_policies where schemaname = 'pre2b';
select 'pre2b.triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname||':'||tgenabled::text,
         '|' order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger where not tgisinternal and tgrelid in (select oid from pg_class where relnamespace = to_regnamespace('pre2b'));
select 'ti.constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||convalidated::text||':'||
         pg_get_constraintdef(oid), '|' order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace = 'topic_intelligence'::regnamespace;
select 'ti.fk', coalesce((select pg_get_constraintdef(oid)||' valid='||convalidated::text from pg_constraint
         where conname = 'topics_cluster_id_fkey'), 'ABSENT');
select 'ti.policies', md5(coalesce(string_agg(tablename||'.'||policyname||':'||permissive||':'||roles::text||':'||
         cmd||':'||coalesce(qual,'')||':'||coalesce(with_check,''), '|' order by tablename, policyname), ''))
  from pg_policies where schemaname = 'topic_intelligence';
select 'ti.acl', md5(coalesce(string_agg(relname||':'||coalesce(relacl::text,'')||':'||relrowsecurity::text,
         '|' order by relname), ''))
  from pg_class where relnamespace = 'topic_intelligence'::regnamespace;
select 'public.cols', md5(coalesce(string_agg(table_name||'.'||column_name||':'||data_type||':'||is_nullable||':'||
         coalesce(column_default,''), '|' order by table_name, column_name), ''))
  from information_schema.columns where table_schema = 'public';
select 'public.constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||convalidated::text||':'||
         pg_get_constraintdef(oid), '|' order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace = 'public'::regnamespace;
select 'public.functions', md5(coalesce(string_agg(p.oid::regprocedure::text||':'||coalesce(p.proacl::text,'')||':'||
         md5(p.prosrc), '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p where p.pronamespace = 'public'::regnamespace;
select 'public.claim_source_quote', (select count(*) from information_schema.columns where table_schema = 'public'
         and table_name = 'claim' and column_name in ('source_quote', 'source_quote_fetched_at'))::text;
""" + ROW_MD5

PREFLIGHT_SQL = """
select 'pre2b_present', (to_regnamespace('pre2b') is not null)::text;
select 'fk_present', exists (select 1 from pg_constraint where conname = 'topics_cluster_id_fkey')::text;
select 'v2_present', (to_regprocedure('public.no_contact_pii_v2(text)') is not null)::text;
select 'source_quote_present', exists (select 1 from information_schema.columns where table_schema = 'public'
       and table_name = 'claim' and column_name = 'source_quote')::text;
"""

# guard probes: each plants one outside dependent, runs PART 1, and must see it refused; always rolled back
PROBE_VIEW = "create view public.rehearse_0027_probe as select id from pre2b.person"
PROBE_FN = ("create function public.rehearse_0027_probe() returns bigint language plpgsql as "
            "$f$ begin return (select count(*) from pre2b.person); end $f$")


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
    env = {k: v for k, v in os.environ.items() if k not in PROD_SECRET_KEYS and PROD_REF not in v}
    env.pop("PGOPTIONS", None)
    env.update(PGPASSWORD=twin_password())
    return env


def psql(args: list[str], stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    refuse_non_twin()
    p = subprocess.run([PSQL, TWIN_CONN, "-X", "-v", "ON_ERROR_STOP=1"] + args, input=stdin, text=True,
                       capture_output=True, env=child_env())
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode})")
    return p


def kv(sql: str) -> dict:
    out = psql(["-tA", "-F", "\t"], stdin=sql).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def run_file(path: str, label: str, single_txn: bool = False) -> bool:
    p = psql((["-1"] if single_txn else []) + ["-f", path], check=False)
    ok = p.returncode == 0
    notices = [l.split("NOTICE:", 1)[1].strip() for l in p.stderr.splitlines() if "NOTICE:" in l and "0027" in l]
    print(f"  {'OK ' if ok else 'ERR'} {label}" + (f"  [{' | '.join(notices)}]" if notices else ""))
    if not ok:
        sys.stderr.write(p.stderr[-1500:])
    return ok


def verify_statements() -> list[str]:
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]


def rows(sql: str) -> list[list[str]]:
    return [r.split("\t") for r in psql(["-tA", "-F", "\t"], stdin=sql + ";").stdout.splitlines() if r]


def verify_step0() -> list[list[str]]:
    out = rows(verify_statements()[0])
    for r in out:
        print(f"    {r[0]:<18} n={r[1]:<4} md5={r[2]}")
    return out


def verify_step1() -> bool:
    out = rows(verify_statements()[1])
    bad = [r[0] for r in out if r[-1] != "t"]
    print(f"  {'PASS' if not bad else 'FAIL'} step 1 catalog: {len(out) - len(bad)}/{len(out)} ok {bad or ''}")
    return not bad


def part1_block() -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(r"-- PART 1 -+\n(do \$pre\$.*?\$pre\$;)", text, re.S)
    if not m:
        sys.exit("could not find the PART 1 preflight block in the migration")
    return m.group(1)


def guard_probe(plant: str | None, label: str, want_refusal: str | None) -> bool:
    """Run PART 1 after planting `plant`, inside a rolled-back txn. want_refusal: substring of the expected
    exception, or None for 'must pass'."""
    body = (plant + ";\n") if plant else ""
    p = psql([], stdin=f"begin;\n{body}{part1_block()}\nrollback;\n", check=False)
    if want_refusal is None:
        ok = p.returncode == 0 and "preflight OK" in p.stderr
    else:
        ok = p.returncode != 0 and want_refusal in p.stderr
    tail = (p.stderr.strip().splitlines() or [""])
    msg = next((l for l in tail if "ERROR" in l or "NOTICE" in l), tail[-1])
    print(f"  {'PASS' if ok else 'FAIL'} {label}: {msg.strip()[:220]}")
    return ok


def export_pre2b(path: str) -> bool:
    refuse_non_twin()
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    os.chmod(os.path.dirname(path), 0o700)
    p = subprocess.run([PG_DUMP, "-d", TWIN_CONN, "--schema=pre2b", "--no-publications", "--no-subscriptions",
                        "-f", path], text=True, capture_output=True, env=child_env())
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-1500:])
        print("  FAIL pg_dump")
        return False
    os.chmod(path, 0o600)
    return check_export(path)


def check_export(path: str) -> bool:
    text = open(path, encoding="utf-8").read()
    missing = [t for t in PRE2B_TABLES if f"COPY pre2b.{t} " not in text]
    ok = "CREATE SCHEMA pre2b;" in text and not missing and text.count("CREATE POLICY") == 3
    print(f"  {'PASS' if ok else 'FAIL'} export {path} ({os.path.getsize(path):,} bytes, mode "
          f"{oct(os.stat(path).st_mode & 0o777)}): CREATE SCHEMA, COPY for 9/9 tables"
          f"{'' if not missing else ' MISSING ' + ','.join(missing)}, {text.count('CREATE POLICY')} policies")
    return ok


def rollback(export: str) -> bool:
    if not run_file(export, f"restore pre2b from {export}", single_txn=True):
        return False
    p = psql([], stdin=FK_RESTORE, check=False)
    print(f"  {'OK ' if p.returncode == 0 else 'ERR'} re-add topics_cluster_id_fkey")
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-800:])
    return p.returncode == 0


ROLE_READS = ["signal_read.v_topic_movement", "signal_read.v_topic_intersections",
              "topic_intelligence.topic_cluster", "topic_intelligence.topic_trend", "topic_intelligence.topic_pair_metric"]


def role_reads() -> dict:
    """Row count (or 'denied') per role per relation. service_role has no grant on the signal_read views
    (0002 grants them to anon/authenticated only), so 'denied' there is the pre-0027 baseline, not a failure."""
    out = {}
    for role in ("service_role", "anon"):
        for rel in ROLE_READS:
            p = psql(["-tA"], stdin=f"begin; set local role {role}; select count(*) from {rel}; rollback;", check=False)
            got = [l for l in p.stdout.splitlines() if l.strip().isdigit()]
            out[f"{role}:{rel}"] = got[0] if p.returncode == 0 and got else (
                "denied" if "permission denied" in p.stderr else "ERR " + p.stderr.strip()[-120:])
    return out


def print_reads(r: dict) -> None:
    for k, v in r.items():
        print(f"    {k:<55} {v}")


def snapshot() -> dict:
    return kv(SNAPSHOT_SQL)


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def print_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--reset-first", action="store_true")
    ap.add_argument("--leave-applied", action="store_true")
    ap.add_argument("--export", default=EXPORT_DEFAULT, help="cold export path (outside git)")
    a = ap.parse_args()
    for f in (MIGRATION, VERIFY):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    if os.path.abspath(a.export).startswith(REPO + os.sep):
        sys.exit("REFUSED: the export holds person rows; it must live outside the repo.")
    refuse_non_twin()
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1 block: {len(part1_block())} chars; export {a.export}")
    if len(verify_statements()) != 2:
        sys.exit("verify file must hold exactly 2 statements (step 0, step 1)")
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    print("  " + " ".join(f"{k}={v}" for k, v in pf.items()))
    if pf.get("pre2b_present") != "true":
        if not a.reset_first or not os.path.exists(a.export):
            print("  FAIL pre2b absent on the twin: rerun with --reset-first (needs the export)")
            return 1
        if not rollback(a.export):
            return 1
        pf = kv(PREFLIGHT_SQL)
    if pf.get("fk_present") != "true":
        print("  FAIL topics_cluster_id_fkey absent")
        return 1
    print("  staging/0027_verify.sql step 0 (compare with prod before the paste):")
    step0 = verify_step0()
    if a.preflight_only:
        print("PREFLIGHT OK")
        return 0

    ok = True
    print("[1] snapshot A")
    A = snapshot()
    print("  " + " ".join(f"{k}={v[:12]}" for k, v in A.items() if not k.startswith("rows.")))
    print("  role reads (baseline):")
    reads_a = role_reads()
    print_reads(reads_a)
    if any(reads_a[f"anon:{v}"] in ("0", "denied") for v in ROLE_READS[:2]):
        print("  FAIL anon cannot read the signal_read views before 0027; the 4b comparison would prove nothing")
        return 1
    print("[1a] cold export (pg_dump, twin)")
    if not export_pre2b(a.export):
        return 1
    print("[1b] guard probes (rolled back)")
    ok &= guard_probe(None, "clean twin passes", None)
    ok &= guard_probe(PROBE_VIEW, "outside view on pre2b.person refused", "CASCADE would drop objects outside pre2b")
    ok &= guard_probe(PROBE_FN, "outside function naming pre2b refused", "reference it by name")
    if not ok:
        return 1

    print("[2] apply 0027")
    if not run_file(MIGRATION, "apply"):
        return 1
    B = snapshot()
    print("[3] re-apply (idempotent)")
    if not run_file(MIGRATION, "re-apply"):
        return 1
    d = diff(B, snapshot())
    print(f"  {'PASS' if not d else 'FAIL'} re-apply is a no-op")
    print_diff(d)
    ok &= not d

    print("[4] verify (staging/0027_verify.sql step 1)")
    ok &= verify_step1()
    print("[4b] role reads after apply == baseline (anon = the /signal read path)")
    d = diff(reads_a, role_reads())
    print(f"  {'PASS' if not d else 'FAIL'} every role/relation read unchanged ({len(reads_a)} probes)")
    print_diff(d)
    ok &= not d

    print("[5] rollback")
    if not rollback(a.export):
        return 1
    print("[6] snapshot C == snapshot A")
    d = diff(A, snapshot())
    print(f"  {'PASS ROLLBACK PROVEN' if not d else 'FAIL rollback did not restore snapshot A'}")
    print_diff(d)
    ok &= not d
    after = rows(verify_statements()[0])
    same = after == step0
    print(f"  {'PASS' if same else 'FAIL'} verify step 0 after rollback equals gate 0 (counts + row md5, 10 tables)")
    ok &= same

    if a.leave_applied and ok:
        print("[7] leave applied")
        ok &= run_file(MIGRATION, "apply") and verify_step1()
    print(f"\nREHEARSAL 0027: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
