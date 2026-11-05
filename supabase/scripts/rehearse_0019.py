#!/usr/bin/env python3
"""
rehearse_0019.py: prove migration 0019 (revoke API-role write privileges on
nine MI spine tables + the postgres default ACL in public, YED-311) on the
Phantom-Test-Case twin, before Alex pastes it into the prod dashboard
(CLAUDE.md invariant 2).

Gates (all must pass, in order):
  0  preflight   refuse prod; twin reachable; record whether the twin carries
                 the same anon/authenticated write grants as prod (if not, the
                 rehearsal still proves apply/idempotency/rollback, and says so)
  1  snapshot A  relacl of the 9 tables + the postgres default ACL in public
  1b negative    the step-3 checks run on the UN-migrated state and must FAIL
                 (a check that passes without the fix proves nothing); the INSERT
                 case rejects an RLS refusal (same SQLSTATE 42501) as proof
  2  apply       0019, verbatim
  3  verify      catalog: every anon/authenticated entry on the 9 tables is
                 exactly `r` (SELECT); the postgres default ACL grants them
                 nothing beyond `r`.
                 behaviour (inside a rolled-back transaction, SET ROLE anon):
                 SELECT works; INSERT, UPDATE, DELETE and TRUNCATE each fail
                 with insufficient_privilege
  4  re-apply    0019 again: idempotent; verify again
  5  rollback    the ROLLBACK block from the migration header, verbatim
  6  snapshot C  must EQUAL snapshot A: the rollback is PROVEN only if so
  7  leave       re-apply 0019 + verify (default; --no-leave stops at 6)

HARD REFUSAL: never touches prod (oicikjyzmxqfomrrqkvf). No override flag.
Env: PHANTOM_TEST_DB_PASSWORD (required, from .env); TWIN_DB_HOST /
TWIN_DB_PORT / TWIN_DB_USER (session pooler: aws-1-us-east-2.pooler.supabase.com,
user postgres.ytfzzsxcxxbejnowmkmk).
"""
from __future__ import annotations
import argparse, datetime as dt, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SUPA = os.path.dirname(HERE)
REPO = os.path.dirname(SUPA)
PSQL = os.environ.get("PSQL_BIN", "psql")
TWIN_REF = "ytfzzsxcxxbejnowmkmk"
PROD_REF = "oicikjyzmxqfomrrqkvf"
MIGRATION = os.path.join(SUPA, "migrations", "0019_revoke_api_role_writes.sql")
TABLES = ["artifact_outcome", "claim", "claim_entity", "claim_relation", "claim_usage",
          "doc_chunks", "doc_claims", "document_entity", "documents"]

TWIN_HOST = os.environ.get("TWIN_DB_HOST", f"db.{TWIN_REF}.supabase.co")
TWIN_PORT = os.environ.get("TWIN_DB_PORT", "5432")
TWIN_USER = os.environ.get("TWIN_DB_USER", "postgres")
TWIN_CONN = (f"host={TWIN_HOST} port={TWIN_PORT} user={TWIN_USER} "
             f"dbname=postgres sslmode=require connect_timeout=30")
TLIST = ",".join(f"'{t}'" for t in TABLES)
# Prod state recorded read-only 2026-11-05 (relacl / defaclacl text, grantor included).
PROD_TABLE_ACL = ("{postgres=arwdDxtm/postgres,anon=arwdDxtm/postgres,"
                  "authenticated=arwdDxtm/postgres,service_role=arwdDxtm/postgres}")
PROD_DEFAULT_ACL = PROD_TABLE_ACL

SNAPSHOT_SQL = f"""
select 'tbl.' || relname, coalesce(relacl::text, '-') from pg_class
 where relnamespace = 'public'::regnamespace and relname in ({TLIST})
union all
select 'defacl.postgres.public', coalesce((select defaclacl::text from pg_default_acl d
  where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 'public'::regnamespace
    and d.defaclobjtype = 'r'), '-');
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
        sys.exit(f"REFUSED: target must be the twin ({TWIN_REF}); this script never touches prod.")


def psql(args, stdin=None, check=True):
    pw = os.environ.get("PHANTOM_TEST_DB_PASSWORD") or ENV.get("PHANTOM_TEST_DB_PASSWORD")
    if not pw:
        sys.exit("PHANTOM_TEST_DB_PASSWORD not set: refusing to proceed.")
    p = subprocess.run([PSQL, TWIN_CONN, "-v", "ON_ERROR_STOP=1"] + args, input=stdin, text=True,
                       capture_output=True, env=dict(os.environ, PGPASSWORD=pw))
    if check and p.returncode != 0:
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-2000:])
        sys.exit(f"psql failed (rc={p.returncode})")
    return p


def kv(sql):
    out = psql(["-tA", "-F", "\t", "-c", sql]).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def api_entries(acl: str) -> dict:
    """{'anon': 'arwdDxtm', 'authenticated': '...'} from a relacl/defaclacl text."""
    out = {}
    for m in re.finditer(r"(anon|authenticated)=([a-zA-Z*]*)/", acl or ""):
        out[m.group(1)] = m.group(2)
    return out


def snapshot(label):
    s = kv(SNAPSHOT_SQL)
    writes = sum(1 for k, v in s.items() if k.startswith("tbl.")
                 for r, p in api_entries(v).items() if set(p) - {"r"})
    d = api_entries(s.get("defacl.postgres.public", ""))
    print(f"  {label}: tables={sum(1 for k in s if k.startswith('tbl.'))} "
          f"api-role entries with non-SELECT privileges={writes} default-acl api={d}")
    return s


def verify(label, expect_pass=True) -> bool:
    s = kv(SNAPSHOT_SQL)
    bad = [f"{k}:{r}={p}" for k, v in s.items() if k.startswith("tbl.")
           for r, p in api_entries(v).items() if p != "r"]
    missing = [k for k, v in s.items() if k.startswith("tbl.")
               and set(api_entries(v)) != {"anon", "authenticated"}]
    d = api_entries(s.get("defacl.postgres.public", ""))
    d_bad = [f"{r}={p}" for r, p in d.items() if set(p) - {"r"}]
    cat_ok = not bad and not missing and not d_bad
    if expect_pass:
        print(f"  catalog({label}): {'PASS' if cat_ok else 'FAIL'}"
              + ("" if cat_ok else f" :: non-r={bad} missing-select={missing} defacl={d_bad}"))
    # behaviour, as anon, in a rolled-back transaction
    cases = "\n".join(
        f"""  begin
    {stmt};
    raise exception 'FAIL: anon was ALLOWED: {name}';
  exception when insufficient_privilege then
    if sqlerrm ilike '%row-level security%' then
      raise exception 'FAIL: {name} refused by RLS, not by privilege (does not prove the revoke)';
    end if;
  end;""" for name, stmt in [
            ("insert", "insert into public.claim_usage (claim_id, document_id, consumer) values (gen_random_uuid(), gen_random_uuid(), 'rehearse_0019')"),
            ("update", "update public.documents set title = title where false"),
            ("delete", "delete from public.claim where false"),
            ("truncate", "truncate public.doc_claims"),
        ])
    sql = f"""begin;
set local role anon;
do $b$
declare n bigint;
begin
  select count(*) into n from public.claim;   -- SELECT must still work (RLS may return 0 rows)
{cases}
  raise notice '0019 BEHAVIOUR: PASS';
end $b$;
rollback;
"""
    p = psql([], stdin=sql, check=False)
    beh_ok = p.returncode == 0 and "0019 BEHAVIOUR: PASS" in (p.stdout + p.stderr)
    if not expect_pass:
        ok = (not cat_ok) and (not beh_ok)
        why = (p.stdout + p.stderr).strip().splitlines()
        print(f"  negative control({label}): catalog-check {'fails' if not cat_ok else 'PASSES'}, "
              f"behaviour-check {'fails' if not beh_ok else 'PASSES'} on the un-migrated state -> "
              f"{'PASS (the checks discriminate)' if ok else 'FAIL (a check passes without the fix)'}"
              + (f" :: first refusal: {next((l for l in why if 'FAIL' in l), '')[-160:]}" if ok else ""))
        return ok
    print(f"  behaviour({label}) as anon: {'PASS' if beh_ok else 'FAIL'}"
          + ("" if beh_ok else f" :: {(p.stdout + p.stderr).strip()[-300:]}"))
    return cat_ok and beh_ok


def apply_file(path, label):
    p = psql(["-q", "-f", path], check=False)
    ok = p.returncode == 0
    print(f"  {'OK ' if ok else 'ERR'} {label}" + ("" if ok else f" :: {(p.stdout + p.stderr)[-400:]}"))
    return ok


def rollback_sql() -> str:
    src = open(MIGRATION).read()
    block = src.split("-- ROLLBACK", 1)[1].split("-- =====", 1)[0]
    lines = [l[2:].lstrip() if l.startswith("--") else l for l in block.splitlines()[1:]]
    return "\n".join(l for l in lines if l.strip()) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--no-leave", action="store_true")
    ap.add_argument("--reset-first", action="store_true",
                    help="apply the ROLLBACK block before preflight (twin left with 0019 applied by a prior run)")
    a = ap.parse_args()
    refuse_prod()
    print(f"TARGET twin: {TWIN_HOST}:{TWIN_PORT} as {TWIN_USER} (ref {TWIN_REF})  "
          f"at {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")

    if a.reset_first:
        print("[reset] applying the ROLLBACK block first (prior run left 0019 applied)")
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write(rollback_sql()); rb0 = f.name
        if not apply_file(rb0, "0019 rollback block (reset)"):
            sys.exit("STOP: reset failed")
        os.unlink(rb0)
        print()
    print("[0] preflight")
    ver = psql(["-tA", "-c", "show server_version"]).stdout.strip()
    print(f"  twin server_version={ver} (prod 17.6)")
    pre = kv(SNAPSHOT_SQL)
    diffs = [k for k, v in pre.items() if k.startswith("tbl.") and v != PROD_TABLE_ACL]
    dpre = pre.get("defacl.postgres.public", "")
    print(f"  full relacl text equal to prod's on {9 - len(diffs)}/9 tables"
          + (f" (differs: {diffs})" if diffs else "")
          + f"; default ACL equal to prod's: {dpre == PROD_DEFAULT_ACL}")
    n_tbl = sum(1 for k in pre if k.startswith("tbl."))
    with_writes = sum(1 for k, v in pre.items() if k.startswith("tbl.")
                      and any(set(p) - {"r"} for p in api_entries(v).values()))
    print(f"  tables present={n_tbl}/9; tables where api roles hold writes={with_writes} "
          f"(prod: 9/9) -> {'matches prod' if with_writes == 9 else 'DIFFERS from prod (noted; gates still run)'}")
    if n_tbl != 9:
        sys.exit("STOP: not all 9 tables exist on the twin")

    print("\n[1] snapshot A (before)")
    A = snapshot("A")
    print("\n[1b] negative control: the verify checks must FAIL before the fix")
    g = [verify("pre-apply", expect_pass=False)]
    print("\n[2] apply 0019")
    g.append(apply_file(MIGRATION, "0019_revoke_api_role_writes.sql"))
    print("\n[3] verify")
    g.append(verify("post-apply"))
    print("\n[4] re-apply 0019 (idempotency)")
    g.append(apply_file(MIGRATION, "0019 (re-apply)"))
    g.append(verify("post-reapply"))
    print("\n[5] rollback (the migration's ROLLBACK block)")
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
        f.write(rollback_sql())
        rb = f.name
    g.append(apply_file(rb, "0019 rollback block"))
    os.unlink(rb)
    print("\n[6] snapshot C (after rollback): must EQUAL snapshot A")
    C = snapshot("C")
    same = A == C
    print(f"  snapshot C == snapshot A: {'rollback PROVEN' if same else 'MISMATCH'}")
    if not same:
        for k in sorted(set(A) | set(C)):
            if A.get(k) != C.get(k):
                print(f"    {k}: A={A.get(k)} C={C.get(k)}")
    g.append(same)
    if not a.no_leave:
        print("\n[7] leave applied: re-apply 0019 + verify (twin ends in prod's post-promotion state)")
        g.append(apply_file(MIGRATION, "0019 (leave applied)"))
        g.append(verify("leave-applied"))
    print("\n0019 REHEARSAL: " + ("ALL GATES GREEN" if all(g) else "FAILED"))
    sys.exit(0 if all(g) else 1)


if __name__ == "__main__":
    main()
