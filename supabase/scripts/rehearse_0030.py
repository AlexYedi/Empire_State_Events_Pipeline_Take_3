#!/usr/bin/env python3
"""
rehearse_0030.py — prove migration 0030 (existing public objects lose their anon/authenticated grants; TEMP on the
database stops going to PUBLIC; YED-483) on the Phantom-Test-Case twin before Alex pastes it into prod (invariant 2).
Twin-only constants and refusal logic are byte-identical to rehearse_0029.py (scrubbed child env, no override flag).

The twin lags prod: earlier rehearsals (0028, 0029) were left rolled back, and five spine tables plus two RPC
functions carry older grants there. So the harness first brings the twin's in-scope grants to prod parity, proves
parity against the prod step-0 evidence file, rehearses 0030, rolls 0030 back, then undoes the parity setup and proves
the twin is back to exactly what it found.

Gates (all must pass, in order):
  0  as found      twin reachable; snapshot Z (raw + canonical ACLs over public/mi/signal_read/topic_intelligence,
                   default ACLs, database ACL, policies, view options)
  P  parity        0028 and 0029 verbatim, then PARITY_SQL (company/event/event_entity/person/topic and the two RPC
                   functions get prod's exact ACLs). staging/0030_verify.sql step 0 on the twin must EQUAL
                   supabase/evidence/0030_prod_step0_before-20261122.tsv (read-only on prod via the MCP)
  1  snapshot A    raw + canonical fingerprint; anon/authenticated reads of the 2 signal_read views (SET ROLE, count + md5)
  1a negative ctl  before apply, anon CAN select the 14 tables (0 rows, RLS) and execute the 5 functions, and a
                   login-less clone of supabase_read_only_user's grants, and anon, CAN create a temp table
  1b guard probes  (rolled back) PART 1 passes clean; refuses a mixed state and an unexpected anon grant elsewhere;
                   PART 1 + PART 3 without PART 2 makes the postflight raise
  1c REST before   twin publishable key: both views return rows; GET person and POST rpc/match_doc_chunks succeed
                   (the dormant exposure, reproduced); full URL printed per probe
  2  apply 0030    the migration file verbatim
  3  re-apply      second paste is a NOTICE no-op (fingerprint unchanged)
  4  verify        step 1 every row ok = t; step 0 equals the prod baseline transformed by exactly the intended change
  4a anon after    views identical (SET ROLE and REST); 14 tables and 5 functions denied 42501; REST person and rpc denied
  4b writers       (rolled back) as service_role: insert + update person and update one row of each set_updated_at
                   table: updated_at is reset by the trigger; a person row carrying an email is refused by the PII trigger
  4c info          (rolled back) a trigger still fires for a role with NO EXECUTE on the trigger function
  4d TEMP after    supabase_read_only_user has no TEMP; the clone and anon get 42501 on create temp table;
                   service_role and pipeline_writer still can
  5  rollback      the ROLLBACK-BEGIN..ROLLBACK-END block from the migration header, verbatim
  6  snapshot C    raw ACLs byte-identical to snapshot A; PART 1 sees PRE; reads, REST and TEMP probes equal gate 1
  7  teardown      PARITY_UNDO, then 0029's and 0028's own rollback blocks: the twin equals snapshot Z (as found)

Usage:
  python3 supabase/scripts/rehearse_0030.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0030.py --preflight-only  # gate 0 only (read-only)
  TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0030.py --execute   # full gate, twin ends as found
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

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

TWIN_REST = f"https://{TWIN_REF}.supabase.co/rest/v1"
MIGRATION = os.path.join(SUPA, "migrations", "0030_revoke_existing_api_grants.sql")
M0028 = os.path.join(SUPA, "migrations", "0028_signal_views_owner_rights.sql")
M0029 = os.path.join(SUPA, "migrations", "0029_default_privileges_api_roles.sql")
VERIFY = os.path.join(SUPA, "staging", "0030_verify.sql")
PROD_STEP0 = os.path.join(SUPA, "evidence", "0030_prod_step0_before-20261122.tsv")
VIEWS = ["signal_read.v_topic_movement", "signal_read.v_topic_intersections"]
SCHEMAS = ["public", "signal_read", "topic_intelligence", "mi"]
TABLES = ["artifact_outcome", "claim", "claim_entity", "claim_relation", "claim_usage", "doc_chunks", "doc_claims",
          "document_entity", "documents", "company", "event", "event_entity", "person", "topic"]
UPDATED_AT_TABLES = ["artifact_outcome", "company", "event", "person", "topic"]
TEMP_KEEP = ["service_role", "pipeline_writer", "supabase_auth_admin", "supabase_storage_admin", "supabase_etl_admin",
             "supabase_realtime_admin", "supabase_replication_admin"]
TEMP_LOSE = ["anon", "authenticated", "authenticator", "pgbouncer", "supabase_privileged_role", "supabase_read_only_user"]

# Twin-only parity: the twin's 5 cv2 spine tables still carry anon/authenticated arwdDxtm and its two RPC functions
# PUBLIC EXECUTE; prod has the ACLs below (read-only on prod 2026-11-22). Raw item order matches prod exactly.
CV2 = "public.company, public.event, public.event_entity, public.person, public.topic"
RPC_FNS_SQL = ("select p.oid::regprocedure::text from pg_proc p where p.pronamespace = 'public'::regnamespace "
               "and p.proname in ('match_claims_hybrid', 'entity_neighborhood') order by 1")
PARITY_SQL = f"""
begin;
revoke all on {CV2} from anon, authenticated, service_role;
grant select, insert, update, delete on {CV2} to service_role;
grant select on {CV2} to anon, authenticated;
{{rpc_revoke}}
commit;
"""
PARITY_UNDO = f"""
begin;
revoke all on {CV2} from anon, authenticated, service_role;
grant all on {CV2} to anon;
grant all on {CV2} to authenticated;
grant all on {CV2} to service_role;
{{rpc_restore}}
commit;
"""

ACL = ("case when {0} is null then 'DEFAULT' else coalesce((select string_agg(e, ',' order by e) from "
       "(select a.grantor::regrole::text||'>'||case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end"
       "||':'||a.privilege_type||':'||a.is_grantable::text as e from aclexplode({0}) a) s), '') end")
NSP_LIST = ", ".join(f"'{s}'" for s in SCHEMAS)
CANON_SQL = f"""
select 'defacl.'||defaclrole::regrole::text||'.'||case defaclnamespace when 0 then '(global)'
         else defaclnamespace::regnamespace::text end||'.'||defaclobjtype::text, {ACL.format('defaclacl')}
  from pg_default_acl;
select 'rel.'||c.oid::regclass::text||'('||c.relkind::text||')', 'owner='||c.relowner::regrole::text||' acl='||
       {ACL.format('c.relacl')}||' opts='||coalesce(array_to_string(c.reloptions, ','), '')
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST}) and c.relkind in ('r', 'v', 'm', 'S', 'p', 'f');
select 'col.'||c.oid::regclass::text||'.'||a.attname, a.attacl::text
  from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST}) and a.attacl is not null;
select 'fn.'||p.oid::regprocedure::text, 'owner='||p.proowner::regrole::text||' secdef='||p.prosecdef::text||' acl='||
       {ACL.format('p.proacl')}
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in ({NSP_LIST});
select 'nsp.'||nspname, {ACL.format('nspacl')} from pg_namespace where nspname in ({NSP_LIST});
select 'db.'||datname, {ACL.format('datacl')} from pg_database where datname = current_database();
select 'pol.'||polrelid::regclass::text||'.'||polname, polcmd::text||' roles='||polroles::regrole[]::text||' qual='||
       coalesce(pg_get_expr(polqual, polrelid), '')
  from pg_policy p join pg_class c on c.oid = p.polrelid join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST});
"""
RAW_SQL = f"""
select 'raw.rel.'||c.oid::regclass::text, coalesce(c.relacl::text, 'NULL')
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST}) and c.relkind in ('r', 'v', 'm', 'S', 'p', 'f');
select 'raw.fn.'||p.oid::regprocedure::text, coalesce(p.proacl::text, 'NULL')
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in ({NSP_LIST});
select 'raw.nsp.'||nspname, coalesce(nspacl::text, 'NULL') from pg_namespace where nspname in ({NSP_LIST});
select 'raw.db.'||datname, coalesce(datacl::text, 'NULL') from pg_database where datname = current_database();
"""

FUNCS = ["public.set_updated_at()", "public.assert_no_contact_pii()", "public.assert_no_pii_columns()",
         "public.match_doc_chunks(vector,integer,uuid,text)",
         "public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)"]
# a call per function that reaches the permission check: trigger functions refuse a direct call with 0A000 AFTER the
# EXECUTE check passes, so 0A000 = executable, 42501 = denied
FUNC_CALLS = {
    "public.set_updated_at()": "select public.set_updated_at()",
    "public.assert_no_contact_pii()": "select public.assert_no_contact_pii()",
    "public.assert_no_pii_columns()": "select public.assert_no_pii_columns()",
    "public.match_doc_chunks(vector,integer,uuid,text)": "select count(*) from public.match_doc_chunks(null::vector, 1)",
    "public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)":
        "select count(*) from public.match_doc_chunks_hybrid(null::vector, 'probe', 1)",
}

WRITER_PROBE = """
begin;
set local role service_role;
do $w$
declare
  v_id uuid; v_u timestamptz; t text; n int; v_pii text := 'not raised';
begin
  insert into public.person (name, updated_at) values ('Rehearsal Probe 0030', '2000-01-01') returning id into v_id;
  update public.person set title = 'probe' where id = v_id returning updated_at into v_u;
  raise notice 'W person insert+update as %: updated_at % (trigger fired: %)', current_user, v_u, v_u > '2001-01-01';
  foreach t in array array['artifact_outcome', 'company', 'event', 'topic'] loop
    execute format('with x as (select ctid from public.%I limit 1) update public.%I u set updated_at = ''2000-01-01'' '
                   'from x where u.ctid = x.ctid returning u.updated_at', t, t) into v_u;
    get diagnostics n = row_count;
    raise notice 'W % update as %: rows % updated_at % (trigger fired: %)', t, current_user, n, v_u,
      case when n = 0 then 'n/a (empty table)' else (v_u > '2001-01-01')::text end;
  end loop;
  begin
    insert into public.person (name, bio) values ('Rehearsal Probe 0030 b', 'reach me at probe.person@example.com');
  exception when others then
    v_pii := sqlstate || ' ' || left(sqlerrm, 90);
  end;
  raise notice 'W pii trigger as %: %', current_user, v_pii;
end
$w$;
rollback;
"""
NOEXEC_PROBE = """
begin;
revoke execute on function public.set_updated_at() from service_role, pipeline_writer, public, anon, authenticated;
set local role service_role;
do $n$
declare v_u timestamptz; n int;
begin
  raise notice 'N service_role EXECUTE on set_updated_at: %', has_function_privilege('public.set_updated_at()', 'execute');
  with x as (select ctid from public.topic limit 1)
  update public.topic u set updated_at = '2000-01-01' from x where u.ctid = x.ctid returning u.updated_at into v_u;
  get diagnostics n = row_count;
  raise notice 'N topic update with no EXECUTE: rows % updated_at % (trigger fired: %)', n, v_u, v_u > '2001-01-01';
end
$n$;
rollback;
"""


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
    out = psql(["-q", "-tA", "-F", "\t"], stdin=sql).stdout
    return dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)


def snapshot() -> dict:
    return {**kv(CANON_SQL), **kv(RAW_SQL)}


def canon_only(s: dict) -> dict:
    return {k: v for k, v in s.items() if not k.startswith("raw.")}


def notices(stderr: str, tag: str) -> list[str]:
    return [l.split("NOTICE:", 1)[1].strip() for l in stderr.splitlines() if "NOTICE:" in l and tag in l]


def run_sql(path_or_sql: str, label: str, is_file: bool = True, tag: str = "0030") -> tuple[bool, list[str]]:
    p = psql(["-f", path_or_sql] if is_file else [], stdin=None if is_file else path_or_sql, check=False)
    ok = p.returncode == 0
    n = notices(p.stderr, tag)
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    for line in n:
        print(f"      NOTICE {line[:220]}")
    if not ok:
        print("      " + "\n      ".join(p.stderr.strip().splitlines()[-6:]))
    return ok, n


def verify_statements() -> list[str]:
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]


def rows(sql: str) -> list[list[str]]:
    return [r.split("\t") for r in psql(["-tA", "-F", "\t"], stdin=sql + ";").stdout.splitlines() if r]


def step0() -> dict:
    return {f"{r[0]}\t{r[1]}": (r[2] if len(r) > 2 else "") for r in rows(verify_statements()[0])}


def prod_step0() -> dict:
    out = {}
    for line in open(PROD_STEP0, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        sec, obj, priv = line.rstrip("\n").split("\t")
        out[f"{sec}\t{obj}"] = priv
    return out


def expected_after(before: dict) -> dict:
    """The prod baseline transformed by exactly the change 0030 intends."""
    out = {}
    for k, v in before.items():
        sec, obj = k.split("\t")
        items = v.split(",") if sec in ("table", "function", "database") else None
        if sec == "table":
            items = [i for i in items if not i.startswith(("anon:", "authenticated:"))]
        elif sec == "function":
            items = [i for i in items if not i.startswith(("PUBLIC:", "anon:", "authenticated:"))]
            if obj in FUNCS[:3]:
                items.append("pipeline_writer:EXECUTE")
        elif sec == "database":
            items = [i for i in items if i != "PUBLIC:TEMPORARY"] + [f"{r}:TEMPORARY" for r in TEMP_KEEP]
        elif sec == "temp" and obj in TEMP_LOSE:
            v = "false"
        out[k] = ",".join(sorted(items, key=lambda s: s.encode())) if items is not None else v
    return out


def verify_step1() -> bool:
    out = rows(verify_statements()[1])
    for r in out:
        print(f"    {'ok ' if r[-1] == 't' else 'BAD'} {r[0]}")
    bad = [r[0] for r in out if r[-1] != "t"]
    print(f"  {'PASS' if out and not bad else 'FAIL'} step 1: {len(out) - len(bad)}/{len(out)} ok {bad or ''}")
    return bool(out) and not bad


def block(path: str, name: str, tag: str) -> str:
    text = open(path, encoding="utf-8").read()
    m = re.search(rf"-- {name} -+\n(do \${tag}\$.*?\${tag}\$;)", text, re.S)
    if not m:
        sys.exit(f"could not find the {name} block in {path}")
    return m.group(1)


def rollback_block(path: str) -> str:
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^-- ROLLBACK-BEGIN\n(.*?)^-- ROLLBACK-END$", text, re.S | re.M)
    if not m:
        sys.exit(f"could not find the ROLLBACK-BEGIN..ROLLBACK-END block in {path}")
    return "\n".join(re.sub(r"^--  ?", "", l, count=1) for l in m.group(1).splitlines()) + "\n"


def guard_probe(plant: str | None, body: str, label: str, want: str, want_ok: bool) -> bool:
    pre = (plant + ";\n") if plant else ""
    p = psql([], stdin=f"begin;\n{pre}{body}\nrollback;\n", check=False)
    ok = (p.returncode == 0 and want in p.stderr) if want_ok else (p.returncode != 0 and want in p.stderr)
    tail = (p.stderr.strip().splitlines() or [""])
    msg = next((l for l in tail if "ERROR" in l), None) or next((l for l in tail if "NOTICE" in l), tail[-1])
    print(f"  {'PASS' if ok else 'FAIL'} {label}: {msg.strip()[:230]}")
    return ok


def as_role(role: str, sql: str) -> str:
    """Run `sql` as `role` in a rolled-back txn; 'ok <last line>' or 'denied <SQLSTATE>'."""
    p = psql(["-q", "-tA"], stdin=f"\\set VERBOSITY verbose\nbegin;\nset local role {role};\n{sql};\nrollback;\n",
             check=False)
    if p.returncode == 0:
        got = [l for l in p.stdout.splitlines() if l.strip()]
        return "ok " + (got[-1].strip() if got else "")
    code = re.search(r"ERROR:\s+([0-9A-Z]{5}):", p.stderr)
    return f"err {code.group(1)}" if code else "ERR " + p.stderr.strip()[-120:]


def read_sql(rel: str) -> str:
    return f"select count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x), '')) from {rel} x"


def role_reads() -> dict:
    return {f"{role}:{v}": as_role(role, read_sql(v)) for role in ("anon", "authenticated") for v in VIEWS}


def anon_surface() -> dict:
    out = {f"anon:table:{t}": as_role("anon", f"select count(*) from public.{t}") for t in TABLES}
    out.update({f"anon:fn:{f}": as_role("anon", c) for f, c in FUNC_CALLS.items()})
    return out


def temp_probe(role: str, clone: bool = False) -> str:
    """Fresh connection; refuse to judge if the backend already owns a temp schema (pooler reuse would skip the check).
    clone=True: a login-less role with supabase_read_only_user's memberships, created and dropped in the same txn."""
    setup = ""
    if clone:
        setup = ("create role zz_rehearse_0030_ro nologin bypassrls;\n"
                 "grant pg_read_all_data, pg_monitor to zz_rehearse_0030_ro;\n"
                 "grant zz_rehearse_0030_ro to current_user;\n"
                 "alter role zz_rehearse_0030_ro set default_transaction_read_only = on;\n")
        role = "zz_rehearse_0030_ro"
    for _ in range(5):
        sql = (f"\\set VERBOSITY verbose\nselect 'tempns='||pg_my_temp_schema()::oid;\nbegin;\n{setup}"
               f"select 'has_temp='||has_database_privilege('{role}', current_database(), 'TEMP');\n"
               f"set local role {role};\nset transaction read write;\n"
               f"create temp table zz_rehearse_0030_tmp (i int);\nselect 'created';\nrollback;\n")
        p = psql(["-q", "-tA"], stdin=sql, check=False)
        if "tempns=0" not in p.stdout:
            continue
        has = re.search(r"has_temp=(\w+)", p.stdout)
        if p.returncode == 0 and "created" in p.stdout:
            return f"created (has_temp={has.group(1) if has else '?'})"
        code = re.search(r"ERROR:\s+([0-9A-Z]{5}):\s*(.*)", p.stderr)
        return (f"denied {code.group(1)} {code.group(2)[:70]} (has_temp={has.group(1) if has else '?'})" if code
                else "ERR " + p.stderr.strip()[-150:])
    return "ERR backend already had a temp schema 5 times (pooler reuse); cannot judge"


def temp_probes() -> dict:
    out = {"clone_of_supabase_read_only_user": temp_probe("", clone=True)}
    for r in ("anon", "authenticated", "service_role", "pipeline_writer"):
        out[r] = temp_probe(r)
    return out


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def print_diff(d: dict, limit: int = 40) -> None:
    for k, (x, y) in list(d.items())[:limit]:
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")
    if len(d) > limit:
        print(f"  ... {len(d) - limit} more")


def publishable_key(arg: str | None) -> str:
    key = arg or os.environ.get("TWIN_PUBLISHABLE_KEY") or ""
    if not key:
        sys.exit("TWIN_PUBLISHABLE_KEY (or --publishable-key) not set: take it from the twin's get_publishable_keys.")
    prod_keys = {ENV.get(k) or os.environ.get(k) for k in ("SUPABASE_ANON_KEY", "MI_SUPABASE_ANON_KEY")} - {None, ""}
    if key in prod_keys or PROD_REF in key:
        sys.exit("REFUSED: that publishable key is prod's. The REST probes run against the twin only.")
    if key.startswith("sb_secret_") or '"service_role"' in key:
        sys.exit("REFUSED: a secret key; the REST probes must run as anon.")
    return key


# (schema, path, method, body)
REST_TARGETS = [("signal_read", "v_topic_movement", "GET", None),
                ("signal_read", "v_topic_intersections", "GET", None),
                ("public", "person", "GET", None),
                ("public", "rpc/match_doc_chunks", "POST", {"query_embedding": None, "match_count": 1})]


def rest_probe(key: str, schema: str, rel: str, method: str, body) -> dict:
    url = f"{TWIN_REST}/{rel}" + ("?select=*" if method == "GET" else "")
    if TWIN_REF not in url or PROD_REF in url or not url.split("?")[0].endswith("/" + rel):
        sys.exit(f"REFUSED: bad REST probe URL {url}")
    hdr = {"apikey": key, "Prefer": "count=exact", "Accept": "application/json"}
    hdr["Accept-Profile" if method == "GET" else "Content-Profile"] = schema
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, raw, cr = r.status, r.read(), r.headers.get("Content-Range", "")
    except urllib.error.HTTPError as e:
        status, raw, cr = e.code, e.read(), e.headers.get("Content-Range", "")
    total = cr.rsplit("/", 1)[-1] if "/" in cr else "?"
    res = {"url": url, "method": method, "status": status, "total": total, "md5": ""}
    try:
        payload = json.loads(raw or b"null")
    except ValueError:
        payload = None
    if status in (200, 206) and isinstance(payload, list):
        res["md5"] = hashlib.md5("|".join(sorted(json.dumps(x, sort_keys=True) for x in payload)).encode()).hexdigest()
        res["returned"] = len(payload)
    else:
        res["error"] = ((payload.get("code") or "") + " " + (payload.get("message") or ""))[:90] \
            if isinstance(payload, dict) else ""
    return res


def rest_probes(key: str) -> dict:
    out = {}
    for schema, rel, method, body in REST_TARGETS:
        r = rest_probe(key, schema, rel, method, body)
        out[f"{schema}.{rel}"] = r
        print(f"    {method} {r['url']}  [profile: {schema}] -> HTTP {r['status']} total={r['total']}"
              + (f" returned={r['returned']} md5={r['md5'][:12]}" if 'returned' in r else f" {r.get('error', '')}"))
    return out


def rest_sig(r: dict) -> tuple:
    return (r["status"], r["total"], r["md5"])


def rpc_parity_sql() -> tuple[str, str, list[str]]:
    fns = [r[0] for r in rows(RPC_FNS_SQL)]
    revoke = "\n".join(f"revoke all on function public.{f} from public, anon, authenticated;" for f in fns)
    restore = "\n".join(
        f"revoke all on function public.{f} from public, postgres, anon, authenticated, service_role;\n"
        f"grant execute on function public.{f} to public;\ngrant execute on function public.{f} to postgres;\n"
        f"grant execute on function public.{f} to anon;\ngrant execute on function public.{f} to authenticated;\n"
        f"grant execute on function public.{f} to service_role;" for f in fns)
    return revoke, restore, fns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--teardown-only", action="store_true",
                    help="recovery: undo the parity setup (parity undo, 0029 and 0028 rollback blocks) after a failed run")
    ap.add_argument("--publishable-key", default=None, help="twin publishable key (else TWIN_PUBLISHABLE_KEY)")
    a = ap.parse_args()
    for f in (MIGRATION, M0028, M0029, VERIFY, PROD_STEP0):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    refuse_non_twin()
    pre_block, post_block = block(MIGRATION, "PART 1", "pre"), block(MIGRATION, "PART 3", "post")
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1: {len(pre_block)} chars; PART 3: "
          f"{len(post_block)} chars; rollback block: {len(rollback_block(MIGRATION).splitlines())} lines; "
          f"prod baseline rows: {len(prod_step0())}")
    if len(verify_statements()) != 2:
        sys.exit("verify file must hold exactly 2 statements (step 0, step 1)")
    if a.teardown_only:
        _, rpc_restore, _ = rpc_parity_sql()
        for sql, label in ((PARITY_UNDO.format(rpc_restore=rpc_restore), "parity undo"),
                           (rollback_block(M0029), "0029 rollback block"), (rollback_block(M0028), "0028 rollback block")):
            if not run_sql(sql, label, is_file=False)[0]:
                return 1
        T = snapshot()
        print(f"    keys: {len(T)}; md5 {hashlib.md5(json.dumps(T, sort_keys=True).encode()).hexdigest()}")
        return 0
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] as found: snapshot Z")
    Z = snapshot()
    print(f"    keys: {len(Z)}; md5 {hashlib.md5(json.dumps(Z, sort_keys=True).encode()).hexdigest()}")
    s0 = step0()
    d = diff(prod_step0(), s0)
    print(f"  INFO twin step 0 vs prod baseline before parity: {len(d)} rows differ (expected: the twin lags prod)")
    if a.preflight_only:
        print_diff(d)
        print("PREFLIGHT OK (read-only)")
        return 0

    key = publishable_key(a.publishable_key)
    ok = True
    rpc_revoke, rpc_restore, rpc_fns = rpc_parity_sql()
    print(f"[P] parity setup (twin-only): 0028, 0029 verbatim; cv2 tables + {rpc_fns} to prod ACLs")
    good, n = run_sql(M0028, "apply 0028 verbatim", tag="0028")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL 0028 did not apply cleanly on the twin")
        return 1
    good, n = run_sql(M0029, "apply 0029 verbatim", tag="0029")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL 0029 did not apply cleanly on the twin (0028 stays applied: run teardown by hand)")
        return 1
    good, _ = run_sql(PARITY_SQL.format(rpc_revoke=rpc_revoke), "parity grants", is_file=False)
    if not good:
        return 1
    d = diff(prod_step0(), step0())
    print(f"  {'PASS' if not d else 'FAIL'} twin step 0 EQUALS the prod baseline "
          f"({os.path.relpath(PROD_STEP0, REPO)}, {len(prod_step0())} rows)")
    print_diff(d)
    if d:
        return 1

    print("[1] snapshot A")
    A = snapshot()
    print(f"    keys: {len(A)}; md5 {hashlib.md5(json.dumps(A, sort_keys=True).encode()).hexdigest()}")
    reads_a = role_reads()
    for k, v in reads_a.items():
        print(f"    {k:<55} {v}")
    if not all(v.startswith("ok ") and not v.startswith("ok 0:") for v in reads_a.values()):
        print("  FAIL anon/authenticated do not read non-empty views before apply")
        return 1

    print("[1a] negative control: before apply the dormant grants work")
    surf_a = anon_surface()
    for k, v in surf_a.items():
        print(f"    {k:<75} {v}")
    nc = all(v.startswith("ok ") for k, v in surf_a.items() if ":table:" in k) and \
        all(v.startswith("ok ") or v == "err 0A000" for k, v in surf_a.items() if ":fn:" in k)
    print(f"  {'PASS' if nc else 'FAIL'} anon selects all 14 tables (RLS: 0 rows) and passes the EXECUTE check on all 5 "
          f"functions (0A000 = trigger function refused a direct call AFTER the EXECUTE check)")
    temp_a = temp_probes()
    for k, v in temp_a.items():
        print(f"    temp {k:<40} {v}")
    tc = all(v.startswith("created") for v in temp_a.values())
    print(f"  {'PASS' if tc else 'FAIL'} the read-only clone, anon, authenticated, service_role and pipeline_writer "
          f"can all create a temp table before apply (TEMP via PUBLIC)")
    if not (nc and tc):
        return 1

    print("[1b] guard probes (rolled back)")
    ok &= guard_probe(None, pre_block, "PART 1 passes on the parity twin", "preflight OK: PRE state", True)
    ok &= guard_probe("revoke select on public.person from anon", pre_block, "mixed state refused",
                      "mixed or unexpected state", False)
    ok &= guard_probe("grant select on public.claim_current to anon", pre_block,
                      "unexpected anon grant outside the scope refused", "differ from the keep list", False)
    ok &= guard_probe(None, pre_block + "\n" + post_block, "wrong end state (PART 2 skipped): postflight raises",
                      "postflight FAILED", False)
    if not ok:
        return 1

    print(f"[1c] REST as anon before apply ({TWIN_REST}, twin publishable key)")
    rest_a = rest_probes(key)
    rb = all(rest_a[f"signal_read.{v}"]["status"] in (200, 206) and rest_a[f"signal_read.{v}"]["total"] not in ("0", "?")
             for v in ("v_topic_movement", "v_topic_intersections"))
    rb &= rest_a["public.person"]["status"] in (200, 206) and rest_a["public.rpc/match_doc_chunks"]["status"] == 200
    print(f"  {'PASS' if rb else 'FAIL'} views return rows; person (0 rows, RLS) and rpc/match_doc_chunks are reachable "
          f"as anon before apply")
    if not rb:
        return 1

    print("[2] apply 0030")
    good, n = run_sql(MIGRATION, "apply")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL apply (or no 'postflight OK' notice)")
        return 1
    B = snapshot()
    print("  ACLs that changed (A -> B), canonical:")
    print_diff(diff(canon_only(A), canon_only(B)))

    print("[3] re-apply (idempotent)")
    good, n = run_sql(MIGRATION, "re-apply")
    if not good:
        return 1
    d = diff(B, snapshot())
    noop = not d and any("already applied" in x for x in n)
    print(f"  {'PASS' if noop else 'FAIL'} re-apply is a no-op (raw + canonical unchanged, 'already applied' notice)")
    print_diff(d)
    ok &= noop

    print("[4] verify (staging/0030_verify.sql)")
    ok &= verify_step1()
    d = diff(expected_after(prod_step0()), step0())
    print(f"  {'PASS' if not d else 'FAIL'} step 0 equals the prod baseline transformed by exactly the intended change "
          f"(tables -anon/authenticated; functions -PUBLIC/anon/authenticated, +pipeline_writer on 3 trigger fns; "
          f"database -PUBLIC:TEMPORARY +7 roles; temp false for {', '.join(TEMP_LOSE)}; all else identical)")
    print_diff(d)
    ok &= not d

    print("[4a] anon after apply")
    reads_b = role_reads()
    d = diff(reads_a, reads_b)
    print(f"  {'PASS' if not d else 'FAIL'} signal_read views as anon/authenticated (SET ROLE) identical to snapshot A")
    print_diff(d)
    ok &= not d
    surf_b = anon_surface()
    for k, v in surf_b.items():
        print(f"    {k:<75} {v}")
    denied = all(v == "err 42501" for v in surf_b.values())
    print(f"  {'PASS' if denied else 'FAIL'} anon is denied (42501) on all 14 tables and all 5 functions")
    ok &= denied
    rest_b = rest_probes(key)
    for v in ("v_topic_movement", "v_topic_intersections"):
        t = f"signal_read.{v}"
        same = rest_sig(rest_b[t]) == rest_sig(rest_a[t])
        print(f"  {'PASS' if same else 'FAIL'} REST {t} same as before: HTTP {rest_a[t]['status']} -> "
              f"{rest_b[t]['status']}, total {rest_a[t]['total']} -> {rest_b[t]['total']}, md5 "
              f"{rest_a[t]['md5'][:12]} -> {rest_b[t]['md5'][:12]}")
        ok &= same
    shut = all(rest_b[t]["status"] not in (200, 206) for t in ("public.person", "public.rpc/match_doc_chunks"))
    print(f"  {'PASS' if shut else 'FAIL'} REST person -> HTTP {rest_b['public.person']['status']} "
          f"{rest_b['public.person'].get('error', '')}; rpc/match_doc_chunks -> HTTP "
          f"{rest_b['public.rpc/match_doc_chunks']['status']} {rest_b['public.rpc/match_doc_chunks'].get('error', '')}")
    ok &= shut

    print("[4b] writers after apply (rolled back): service_role fires the triggers")
    p = psql([], stdin=WRITER_PROBE, check=False)
    w = notices(p.stderr, "W ")
    for line in w:
        print(f"    {line}")
    wr = (p.returncode == 0 and any(l.startswith("W person insert+update") and "trigger fired: t" in l for l in w)
          and all("trigger fired: f" not in l for l in w)
          and any(l.startswith("W pii trigger") and "ADR-9" in l for l in w))
    print(f"  {'PASS' if wr else 'FAIL'} service_role inserts/updates spine rows, set_updated_at resets updated_at, "
          f"the PII trigger refuses an email (all rolled back)")
    if p.returncode != 0:
        print("      " + "\n      ".join(p.stderr.strip().splitlines()[-4:]))
    ok &= wr

    print("[4c] info (rolled back): trigger EXECUTE is checked at CREATE TRIGGER, not when it fires")
    p = psql([], stdin=NOEXEC_PROBE, check=False)
    for line in notices(p.stderr, "N "):
        print(f"    INFO {line}")
    if p.returncode != 0:
        print("    INFO probe errored: " + (p.stderr.strip().splitlines() or [""])[-1][:200])

    print("[4d] TEMP after apply")
    real = rows("select has_database_privilege('supabase_read_only_user', current_database(), 'TEMP')::text, "
                "exists (select 1 from pg_roles where rolname = 'supabase_read_only_user')::text, "
                "pg_has_role(current_user, 'supabase_read_only_user', 'member')::text")[0]
    print(f"    supabase_read_only_user exists={real[1]}; TEMP={real[0]}; postgres can SET ROLE to it={real[2]} "
          f"(false: tested through a login-less clone with its memberships, created and dropped in one rolled-back txn)")
    temp_b = temp_probes()
    for k, v in temp_b.items():
        print(f"    temp {k:<40} {v}")
    tb = (real[0] == "false"
          and all(temp_b[r].startswith("denied 42501") for r in ("clone_of_supabase_read_only_user", "anon", "authenticated"))
          and all(temp_b[r].startswith("created") for r in ("service_role", "pipeline_writer")))
    print(f"  {'PASS' if tb else 'FAIL'} read-only user has no TEMP; clone, anon, authenticated get 42501 on "
          f"`set transaction read write; create temp table`; service_role and pipeline_writer still can")
    left = rows("select count(*)::text from pg_roles where rolname like 'zz_rehearse_0030%'")[0][0]
    print(f"  {'PASS' if left == '0' else 'FAIL'} no clone role left behind ({left})")
    ok &= tb and left == "0"

    print("[5] rollback (header block, verbatim)")
    good, _ = run_sql(rollback_block(MIGRATION), "rollback", is_file=False)
    if not good:
        return 1
    print("[6] snapshot C == snapshot A")
    C = snapshot()
    d = diff(A, C)
    print(f"  {'PASS' if not d else 'FAIL'} raw + canonical ACLs byte-identical to snapshot A ({len(A)} keys, "
          f"raw aclitem order included)")
    print_diff(d)
    ok &= not d
    ok &= guard_probe(None, pre_block, "PART 1 sees the PRE state again", "preflight OK: PRE state", True)
    d = diff(reads_a, role_reads())
    print(f"  {'PASS' if not d else 'FAIL'} role reads equal snapshot A")
    ok &= not d
    d = diff(surf_a, anon_surface())
    print(f"  {'PASS' if not d else 'FAIL'} anon table/function surface equals gate 1a")
    print_diff(d)
    ok &= not d
    d = diff(prod_step0(), step0())
    print(f"  {'PASS' if not d else 'FAIL'} step 0 equals the prod baseline again")
    ok &= not d
    rest_c = rest_probes(key)
    d = {t: (rest_sig(rest_a[t]), rest_sig(rest_c[t])) for t in rest_a if rest_sig(rest_a[t]) != rest_sig(rest_c[t])}
    print(f"  {'PASS' if not d else 'FAIL'} REST probes equal gate 1c ({len(rest_a)} targets)")
    print_diff(d)
    ok &= not d
    temp_c = temp_probes()
    d = diff({k: v.split(" ")[0] for k, v in temp_a.items()}, {k: v.split(" ")[0] for k, v in temp_c.items()})
    print(f"  {'PASS' if not d else 'FAIL'} TEMP probes equal gate 1a")
    print_diff(d)
    ok &= not d
    print(f"  {'PASS ROLLBACK PROVEN' if ok else 'FAIL'}")

    print("[7] teardown: parity undo, 0029 rollback, 0028 rollback -> twin as found")
    good1, _ = run_sql(PARITY_UNDO.format(rpc_restore=rpc_restore), "parity undo", is_file=False)
    good2, _ = run_sql(rollback_block(M0029), "0029 rollback block (verbatim from its header)", is_file=False)
    good3, _ = run_sql(rollback_block(M0028), "0028 rollback block (verbatim from its header)", is_file=False)
    if not (good1 and good2 and good3):
        print("  FAIL teardown step errored: twin NOT as found, fix by hand")
        return 1
    Zc = snapshot()
    d = diff(canon_only(Z), canon_only(Zc))
    print(f"  {'PASS' if not d else 'FAIL'} canonical ACLs, defaults, policies and view options equal snapshot Z "
          f"({len(canon_only(Z))} keys)")
    print_diff(d)
    ok &= not d
    draw = diff({k: v for k, v in Z.items() if k.startswith("raw.")}, {k: v for k, v in Zc.items() if k.startswith("raw.")})
    print(f"  {'PASS' if not draw else 'INFO'} raw ACL text equals snapshot Z "
          f"({'byte-identical' if not draw else str(len(draw)) + ' differ in item order only (canonical equal above)'})")
    print_diff(draw, 10)

    print(f"\nREHEARSAL 0030: {'PASS' if ok else 'FAIL'} (twin left as found)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
