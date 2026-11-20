#!/usr/bin/env python3
"""
rehearse_0025.py — prove migration 0025 (PII backstop v2: no_contact_pii_v2, person trigger on v2, nine NOT VALID
CHECKs; YED-392/318/323/324, PR #396) on the Phantom-Test-Case twin before Alex pastes it into prod (invariant 2).
Twin-only constants and refusal logic are byte-identical to rehearse_0024.py (scrubbed child env, no override flag).

Gates (all must pass, in order):
  0  preflight     twin reachable; 0022/0023 tables present; v2 absent (else --reset-first)
  1  snapshot A    schema fingerprint (columns, constraints incl. convalidated, triggers, functions incl. body + ACL)
                   + row counts
  1b negative      the behaviour probes on the pre-0025 twin: the two v2-only refusals (LRM-split email in person.bio,
                   email in claim.claim_text) must be ALLOWED here, so the step-4b refusals prove 0025 did it
  2  apply 0025    the migration file verbatim
  3  re-apply      second paste is a clean no-op (fingerprint unchanged)
  4  verify        staging/0025_verify.sql steps 1-3: every behaviour row ok = t, every catalog row ok = t,
                   every existing-row count = 0
  4b behaviour     (rolled back) LRM email in person.bio refused by the trigger; email in claim.claim_text refused by
                   claim_text_no_pii; a clean claim_text update passes
  4c validate      the nine VALIDATE CONSTRAINT statements succeed on the twin's rows (inside a rolled-back txn)
  5  rollback      staging/0025_rollback.sql verbatim
  6  snapshot C    must EQUAL snapshot A: ROLLBACK PROVEN only if so
  7  negative      the 1b probes are allowed again
  (--leave-applied re-applies 0025 + verify at the end.)

Usage:
  python3 supabase/scripts/rehearse_0025.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0025.py --preflight-only
  python3 supabase/scripts/rehearse_0025.py --execute         # full gate, ends rolled back
  python3 supabase/scripts/rehearse_0025.py --execute --reset-first
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

MIGRATION = os.path.join(SUPA, "migrations", "0025_pii_backstop_normalized.sql")
VERIFY = os.path.join(SUPA, "staging", "0025_verify.sql")
ROLLBACK = os.path.join(SUPA, "staging", "0025_rollback.sql")

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

PREFLIGHT_SQL = """
select 'prereq', (to_regclass('public.claim_verification') is not null and to_regclass('public.claim_label') is not null
       and to_regclass('public.entity_alias') is not null and to_regclass('public.sweep_query') is not null
       and to_regprocedure('public.no_contact_pii_v1(text)') is not null)::text;
select 'v2_present', (to_regprocedure('public.no_contact_pii_v2(text)') is not null)::text;
select 'claims', count(*)::text from public.claim;
select 'persons', count(*)::text from public.person;
"""

PERSON_PROBE = "insert into public.person (id, name, bio) values (gen_random_uuid(), 'rehearse 0025 probe', U&'dana@exa\\200Emple.c\\200Eom')"
CLAIM_PROBE = ("update public.claim set claim_text = 'reach dana@example.com' "
               "where id = (select id from public.claim order by id limit 1)")
CLEAN_PROBE = ("update public.claim set claim_text = claim_text || ' (rehearsal)' "
               "where id = (select id from public.claim order by id limit 1)")


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


def verify_statements() -> list[str]:
    """Steps 1-3 of the verify file: the uncommented statements, in order."""
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]


def verify() -> bool:
    stmts = verify_statements()
    if len(stmts) != 3:
        print(f"  FAIL verify file: expected 3 statements (steps 1-3), found {len(stmts)}")
        return False
    good = True
    for i, s in enumerate(stmts, 1):
        rows = [r.split("\t") for r in psql(["-tA", "-F", "\t"], stdin=s + ";").stdout.splitlines() if r]
        if i == 1:
            bad = [r for r in rows if r[-1] != "t"]
            print(f"  {'PASS' if not bad else 'FAIL'} step 1 behaviour: {len(rows) - len(bad)}/{len(rows)} rows ok")
            for r in bad:
                print(f"       row {rows.index(r) + 1}: expected_ok={r[1]} got={r[2]}")
        elif i == 2:
            bad = [r[0] for r in rows if r[-1] != "t"]
            print(f"  {'PASS' if not bad else 'FAIL'} step 2 catalog: {len(rows) - len(bad)}/{len(rows)} ok {bad or ''}")
        else:
            bad = [f"{r[0]}={r[1]}" for r in rows if r[1] != "0"]
            print(f"  {'PASS' if not bad else 'FAIL'} step 3 existing rows: {len(rows)} sites, violating {bad or 'none'}")
        good &= not bad
    return good


def validate_in_txn() -> bool:
    lines = [l.strip()[2:].strip() for l in open(VERIFY, encoding="utf-8")
             if re.match(r"\s*--\s*alter table .* validate constraint", l)]
    if len(lines) != 9:
        print(f"  FAIL found {len(lines)} VALIDATE statements, expected 9")
        return False
    p = psql([], stdin="begin;\n" + "\n".join(lines) + "\nrollback;\n", check=False)
    ok = p.returncode == 0
    print(f"  {'PASS' if ok else 'FAIL'} all 9 VALIDATE CONSTRAINT statements succeed (rolled back)")
    if not ok:
        sys.stderr.write(p.stderr[-800:])
    return ok


def snapshot() -> dict:
    return kv(SNAPSHOT_SQL)


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def print_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")


def negative(phase: str) -> bool:
    print(f"[{phase}] negative control: v2-only refusals are allowed without 0025")
    return (run_probe(PERSON_PROBE, "person LRM email", "allowed")
            & run_probe(CLAIM_PROBE, "claim_text email", "allowed"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--reset-first", action="store_true")
    ap.add_argument("--leave-applied", action="store_true")
    a = ap.parse_args()
    for f in (MIGRATION, VERIFY, ROLLBACK):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    refuse_non_twin()
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}")
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    print("  " + " ".join(f"{k}={v}" for k, v in pf.items()))
    if pf.get("prereq") != "true":
        print("  FAIL 0022/0023 not on the twin")
        return 1
    if pf.get("v2_present") == "true":
        if not a.reset_first:
            print("  FAIL v2 already on the twin: rerun with --reset-first")
            return 1
        if not run_file(ROLLBACK, "reset: rollback file"):
            return 1
    if int(pf.get("claims", "0")) == 0:
        print("  FAIL twin has no claims; the claim probes need one row")
        return 1
    if a.preflight_only:
        print("PREFLIGHT OK")
        return 0

    ok = True
    print("[1] snapshot A")
    A = snapshot()
    print("  " + " ".join(f"{k}={v[:12]}" for k, v in A.items() if not k.startswith("constraint_names")))
    ok &= negative("1b")
    if not ok:
        return 1

    print("[2] apply 0025")
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

    print("[4] verify (staging/0025_verify.sql steps 1-3)")
    ok &= verify()
    print("[4b] behaviour (rolled back)")
    ok &= run_probe(PERSON_PROBE, "person LRM email", "trigger")
    ok &= run_probe(CLAIM_PROBE, "claim_text email", "check:claim_text_no_pii")
    ok &= run_probe(CLEAN_PROBE, "clean claim_text update", "allowed")
    print("[4c] validate")
    ok &= validate_in_txn()

    print("[5] rollback")
    if not run_file(ROLLBACK, "staging/0025_rollback.sql"):
        return 1
    print("[6] snapshot C == snapshot A")
    d = diff(A, snapshot())
    print(f"  {'PASS ROLLBACK PROVEN' if not d else 'FAIL rollback did not restore snapshot A'}")
    print_diff(d)
    ok &= not d
    ok &= negative("7")

    if a.leave_applied and ok:
        print("[8] leave applied")
        ok &= run_file(MIGRATION, "apply") and verify()
    print(f"\nREHEARSAL 0025: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
