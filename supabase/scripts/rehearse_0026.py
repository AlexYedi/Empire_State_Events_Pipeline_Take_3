#!/usr/bin/env python3
"""
rehearse_0026.py — prove migration 0026 (claim.source_quote + source_quote_fetched_at; YED-451) on the
Phantom-Test-Case twin before Alex pastes it into prod (invariant 2). Twin-only constants, refusal logic and
probe/snapshot helpers are copied verbatim from rehearse_0025.py (PR #398): scrubbed child env, no override flag.

Gates (all must pass, in order):
  0  preflight     twin reachable; 0025 applied (no_contact_pii_v2 present); 0026 columns absent (else --reset-first)
  1  snapshot A    schema fingerprint + row counts
  2  apply 0026    the migration file verbatim
  3  re-apply      second paste is a clean no-op (fingerprint unchanged)
  4  verify        the file's VERIFY block: every row true
  4b behaviour     (rolled back) 26 words / blank -> _words; plain email and LRM-split email -> _no_pii (the LRM case
                   proves v2, not v1); quote without fetched_at -> _paired; a clean quote + fetched_at passes
  5  rollback      the file's ROLLBACK block verbatim
  6  snapshot C    must EQUAL snapshot A: ROLLBACK PROVEN only if so
  (--leave-applied re-applies 0026 + verify at the end.)

Usage:
  python3 supabase/scripts/rehearse_0026.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0026.py --preflight-only
  python3 supabase/scripts/rehearse_0026.py --execute         # full gate, ends rolled back
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

MIGRATION = os.path.join(SUPA, "migrations", "0026_claim_source_quote.sql")

TABLES = ["public.person", "public.claim", "public.claim_verification", "public.claim_label",
          "public.entity_alias", "public.sweep_query"]
_rels = ",".join(f"'{t}'::regclass" for t in TABLES)
SNAPSHOT_SQL = f"""
select 'cols', md5(coalesce(string_agg(table_name||'.'||column_name||':'||data_type||':'||is_nullable||':'||
         coalesce(column_default,''), '|' order by table_name, column_name), ''))
  from information_schema.columns where table_schema = 'public';
select 'constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||convalidated::text||':'||
         pg_get_constraintdef(oid), '|' order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace = 'public'::regnamespace;
select 'constraint_names', coalesce(string_agg(conrelid::regclass::text||'.'||conname, ',' order by 1), '')
  from pg_constraint where conrelid in ({_rels}) and contype = 'c';
select 'triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname||':'||tgenabled::text||':'||
         tgtype::text||':'||tgfoid::regprocedure::text, '|' order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger where not tgisinternal and tgrelid in ({_rels});
select 'functions', md5(coalesce(string_agg(p.oid::regprocedure::text||':'||coalesce(p.proacl::text,'')||':'||
         p.prosecdef::text||':'||p.provolatile::text||':'||coalesce(array_to_string(p.proconfig, ','),'')||':'||
         md5(p.prosrc)||':'||md5(coalesce(obj_description(p.oid, 'pg_proc'), '')), '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p where p.pronamespace = 'public'::regnamespace;
select 'fn.assert_no_contact_pii', md5(prosrc)||' cfg='||coalesce(array_to_string(proconfig, ','),'')
  from pg_proc where oid = 'public.assert_no_contact_pii()'::regprocedure;
select 'fn.v2_present', (to_regprocedure('public.no_contact_pii_v2(text)') is not null)::text;
""" + "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in TABLES)


def probe_sql(stmt: str, label: str, want: str) -> str:
    """want: 'allowed' | 'trigger' (ADR-9 raise) | 'check:<conname>'. Always rolled back."""
    if want == "allowed":
        body = f"  {stmt};\n"
    elif want == "trigger":
        body = (f"  begin\n    {stmt};\n    raise exception 'FAIL[{label}]: allowed';\n"
                f"  exception when raise_exception then\n"
                f"    if sqlerrm like 'FAIL[%' or sqlerrm !~ 'ADR-9' then raise; end if;\n  end;\n")
    else:
        con = want.split(":", 1)[1]
        body = (f"  begin\n    {stmt};\n    raise exception 'FAIL[{label}]: allowed';\n"
                f"  exception when check_violation then\n    get stacked diagnostics c = constraint_name;\n"
                f"    if c <> '{con}' then raise exception 'FAIL[{label}]: wrong constraint %', c; end if;\n  end;\n")
    return f"begin;\ndo $p$ declare c text; begin\n{body}end $p$;\nrollback;\n"


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


def run_file(path: str, label: str) -> bool:
    p = psql(["-f", path], check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    if not ok:
        sys.stderr.write(p.stderr[-1500:])
    return ok


def run_probe(stmt: str, label: str, want: str) -> bool:
    p = psql([], stdin=probe_sql(stmt, label, want), check=False)
    ok = p.returncode == 0
    print(f"  {'PASS' if ok else 'FAIL'} {label} (want {want})")
    if not ok:
        sys.stderr.write("    " + p.stderr.strip()[-600:] + "\n")
    return ok


def snapshot() -> dict:
    return kv(SNAPSHOT_SQL)


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def print_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")


PREFLIGHT_SQL = """
select 'v2_present', (to_regprocedure('public.no_contact_pii_v2(text)') is not null)::text;
select 'cols_0026', (select count(*) from information_schema.columns where table_schema = 'public'
       and table_name = 'claim' and column_name in ('source_quote', 'source_quote_fetched_at'))::text;
select 'claims', count(*)::text from public.claim;
"""

ROW = "where id = (select id from public.claim order by id limit 1)"
PROBES = [
    (f"update public.claim set source_quote = repeat('w ', 26), source_quote_fetched_at = now() {ROW}",
     "26 words", "check:claim_source_quote_words"),
    (f"update public.claim set source_quote = '   ', source_quote_fetched_at = now() {ROW}",
     "blank quote", "check:claim_source_quote_words"),
    (f"update public.claim set source_quote = 'mail dana@example.com', source_quote_fetched_at = now() {ROW}",
     "plain email", "check:claim_source_quote_no_pii"),
    (f"update public.claim set source_quote = U&'mail dana@exa\\200Emple.c\\200Eom', source_quote_fetched_at = now() {ROW}",
     "LRM-split email (v2 only)", "check:claim_source_quote_no_pii"),
    (f"update public.claim set source_quote = 'ok quote' {ROW}",
     "quote without fetched_at", "check:claim_source_quote_paired"),
    (f"update public.claim set source_quote = 'revenue grew 40 percent in 2025', source_quote_fetched_at = now() {ROW}",
     "clean quote + fetched_at", "allowed"),
]


def block(tag: str) -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(rf"-- {tag}:BEGIN\n(.*?)-- {tag}:END", text, re.S)
    if not m:
        sys.exit(f"{tag} block missing from {MIGRATION}")
    return "\n".join(re.sub(r"^--\s?", "", l) for l in m.group(1).splitlines())


def verify() -> bool:
    rows = [r.split("\t") for r in psql(["-tA", "-F", "\t"], stdin=block("VERIFY").rstrip().rstrip(";") + ";").stdout.splitlines() if r]
    bad = [r[0] for r in rows if r[-1] != "true"]
    print(f"  {'PASS' if rows and not bad else 'FAIL'} verify: {len(rows) - len(bad)}/{len(rows)} true {bad or ''}")
    return bool(rows) and not bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--reset-first", action="store_true")
    ap.add_argument("--leave-applied", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(MIGRATION):
        sys.exit(f"missing {MIGRATION}")
    block("VERIFY"), block("ROLLBACK")
    refuse_non_twin()
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}")
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    print("  " + " ".join(f"{k}={v}" for k, v in pf.items()))
    if pf.get("v2_present") != "true":
        print("  FAIL 0025 not on the twin: run rehearse_0025.py --execute --leave-applied first")
        return 1
    if pf.get("cols_0026") != "0":
        if not a.reset_first:
            print("  FAIL 0026 columns already on the twin: rerun with --reset-first")
            return 1
        if psql([], stdin=block("ROLLBACK"), check=False).returncode != 0:
            print("  FAIL reset rollback")
            return 1
        print("  OK  reset: rollback block")
    if int(pf.get("claims", "0")) == 0:
        print("  FAIL twin has no claims; the probes need one row")
        return 1
    if a.preflight_only:
        print("PREFLIGHT OK")
        return 0

    ok = True
    print("[1] snapshot A")
    A = snapshot()
    print("[2] apply 0026")
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
    print("[4] verify (VERIFY block)")
    ok &= verify()
    print("[4b] behaviour (rolled back)")
    for stmt, label, want in PROBES:
        ok &= run_probe(stmt, label, want)
    print("[5] rollback (ROLLBACK block)")
    p = psql([], stdin=block("ROLLBACK"), check=False)
    print(f"  {'OK ' if p.returncode == 0 else 'ERR'} rollback")
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-1500:])
        return 1
    print("[6] snapshot C == snapshot A")
    d = diff(A, snapshot())
    print(f"  {'PASS ROLLBACK PROVEN' if not d else 'FAIL rollback did not restore snapshot A'}")
    print_diff(d)
    ok &= not d
    if a.leave_applied and ok:
        print("[7] leave applied")
        ok &= run_file(MIGRATION, "apply") and verify()
    print(f"\nREHEARSAL 0026: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
