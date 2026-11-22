#!/usr/bin/env python3
"""
rehearse_0029.py — prove migration 0029 (postgres's default privileges stop auto-granting anon/authenticated on new
public tables, sequences and functions, and stop the built-in PUBLIC EXECUTE on new functions; YED-482) on the
Phantom-Test-Case twin before Alex pastes it into prod (invariant 2).
Twin-only constants and refusal logic are byte-identical to rehearse_0028.py (scrubbed child env, no override flag).

Gates (all must pass, in order):
  0  preflight     twin reachable; PRE state per the migration's PART 1 (run alone, rolled back); prints
                   staging/0029_verify.sql step 0 (every default ACL, canonical) for comparison with prod
  1  snapshot A    default ACLs (canonical, every role) + EXISTING-object grants: aclexplode over every relation,
                   column ACL, function and the schema itself in public, signal_read, topic_intelligence and mi
                   + anon/authenticated reads of the 2 signal_read views (count + md5, `set local role`, rolled back)
  1a negative ctl  (rolled back) as postgres, create a table, a sequence and a SECURITY DEFINER function in public
                   and a function in mi: anon and authenticated DO get privileges on them before apply
  1b limitation    (rolled back) ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin is refused for postgres (42501):
                   the supabase_admin defaults are out of reach by design, documented in the header
  1c guard probes  (rolled back) PART 1 passes on the clean twin and refuses (i) a mixed state (only the tables
                   default revoked), (ii) an unexpected postgres default ACL in another schema; PART 1 + PART 3
                   without PART 2 (a wrong end state) makes the postflight raise
  1d REST before   as anon over PostgREST with the twin's publishable key: both signal_read views return rows;
                   full URL printed per probe
  2  apply 0029    the migration file verbatim
  3  re-apply      second paste is a NOTICE no-op (defaults + object snapshot unchanged)
  4  verify        staging/0029_verify.sql step 1: every row ok = t; step 0 diff vs gate 0 is exactly the
                   expected change (postgres/public r,S,f lose anon/authenticated; postgres/(global)/f appears)
  4a probe after   (rolled back) the same creates: anon/authenticated hold NO privilege on any new object;
                   service_role still holds full table rights, sequence rwU and EXECUTE on the new public function
  4b existing      object-grant snapshot byte-identical to snapshot A; view reads as anon/authenticated identical
  4c REST after    each view returns the same status, total and md5 as gate 1d
  5  rollback      the ROLLBACK-BEGIN..ROLLBACK-END block from the migration header, verbatim
  6  snapshot C    defaults + object grants + role reads must EQUAL snapshot A; PART 1 sees PRE again; the 1a
                   probe gives anon privileges again; REST equals 1d: ROLLBACK PROVEN only if all hold
  (--leave-applied re-applies 0029 + verify at the end.)

Usage:
  python3 supabase/scripts/rehearse_0029.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0029.py --preflight-only
  TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0029.py --execute   # full gate, ends rolled back

The twin's publishable key (public by design; from the Supabase MCP `get_publishable_keys` on the twin) comes from
TWIN_PUBLISHABLE_KEY or --publishable-key, never from the repo. The REST base is pinned to the twin ref.
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
MIGRATION = os.path.join(SUPA, "migrations", "0029_default_privileges_api_roles.sql")
VERIFY = os.path.join(SUPA, "staging", "0029_verify.sql")
VIEWS = ["signal_read.v_topic_movement", "signal_read.v_topic_intersections"]
SCHEMAS = ["public", "signal_read", "topic_intelligence", "mi"]

# Canonical ACL: sorted grantor>grantee:privilege:grantable items (PUBLIC for grantee 0); '' for NULL ACLs is kept
# distinct as 'DEFAULT' so a NULL -> explicit change shows up.
ACL = ("case when {0} is null then 'DEFAULT' else coalesce((select string_agg(e, ',' order by e) from "
       "(select a.grantor::regrole::text||'>'||case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end"
       "||':'||a.privilege_type||':'||a.is_grantable::text as e from aclexplode({0}) a) s), '') end")
NSP_LIST = ", ".join(f"'{s}'" for s in SCHEMAS)
DEFAULTS_SQL = f"""
select 'defacl.'||defaclrole::regrole::text||'.'||case defaclnamespace when 0 then '(global)'
         else defaclnamespace::regnamespace::text end||'.'||defaclobjtype::text, {ACL.format('defaclacl')}
  from pg_default_acl;
"""
OBJECTS_SQL = f"""
select 'rel.'||c.oid::regclass::text||'('||c.relkind::text||')', 'owner='||c.relowner::regrole::text||' acl='||
       {ACL.format('c.relacl')}
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST}) and c.relkind in ('r', 'v', 'm', 'S', 'p', 'f');
select 'col.'||c.oid::regclass::text||'.'||a.attname, a.attacl::text
  from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in ({NSP_LIST}) and a.attacl is not null;
select 'fn.'||p.oid::regprocedure::text, 'owner='||p.proowner::regrole::text||' secdef='||p.prosecdef::text||' acl='||
       {ACL.format('p.proacl')}
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in ({NSP_LIST});
select 'nsp.'||nspname, {ACL.format('nspacl')} from pg_namespace where nspname in ({NSP_LIST});
"""

# 1a / 4a / 6: create one of each as postgres, report every API role's privileges, always roll back
PROBE_SQL = """
begin;
create table public.rehearse_0029_t (id int);
create sequence public.rehearse_0029_s;
create function public.rehearse_0029_f() returns int language sql security definer set search_path = '' as 'select 1';
create function mi.rehearse_0029_f() returns int language sql as 'select 1';
select r||'.table', (select string_agg(p, ',' order by p) from unnest(array['SELECT','INSERT','UPDATE','DELETE',
         'TRUNCATE','REFERENCES','TRIGGER']) p where has_table_privilege(r, 'public.rehearse_0029_t', p))
  from unnest(array['anon','authenticated','service_role']) r;
select r||'.sequence', (select string_agg(p, ',' order by p) from unnest(array['SELECT','UPDATE','USAGE']) p
         where has_sequence_privilege(r, 'public.rehearse_0029_s', p))
  from unnest(array['anon','authenticated','service_role']) r;
select r||'.function', has_function_privilege(r, 'public.rehearse_0029_f()', 'execute')::text
  from unnest(array['anon','authenticated','service_role']) r;
select r||'.mi_function', has_function_privilege(r, 'mi.rehearse_0029_f()', 'execute')::text
  from unnest(array['anon','authenticated','service_role']) r;
select 'acl.function', proacl::text from pg_proc where oid = 'public.rehearse_0029_f()'::regprocedure;
select 'acl.table', relacl::text from pg_class where oid = 'public.rehearse_0029_t'::regclass;
rollback;
"""

PLANT_MIXED = "alter default privileges for role postgres in schema public revoke all on tables from anon, authenticated"
PLANT_OTHER_SCHEMA = "alter default privileges for role postgres in schema mi grant select on tables to service_role"
SUPABASE_ADMIN_ATTEMPT = ("begin;\nalter default privileges for role supabase_admin in schema public "
                          "revoke all on tables from anon;\nrollback;\n")


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


def notices(stderr: str) -> list[str]:
    return [l.split("NOTICE:", 1)[1].strip() for l in stderr.splitlines() if "NOTICE:" in l and "0029" in l]


def run_sql(path_or_sql: str, label: str, is_file: bool = True) -> tuple[bool, list[str]]:
    p = psql(["-f", path_or_sql] if is_file else [], stdin=None if is_file else path_or_sql, check=False)
    ok = p.returncode == 0
    n = notices(p.stderr)
    print(f"  {'OK ' if ok else 'ERR'} {label}")
    for line in n:
        print(f"      NOTICE {line}")
    if not ok:
        sys.stderr.write(p.stderr[-1500:])
    return ok, n


def verify_statements() -> list[str]:
    text = "\n".join(l for l in open(VERIFY, encoding="utf-8").read().splitlines() if not l.lstrip().startswith("--"))
    return [s.strip() for s in re.split(r";\s*\n", text) if s.strip()]


def rows(sql: str) -> list[list[str]]:
    return [r.split("\t") for r in psql(["-tA", "-F", "\t"], stdin=sql + ";").stdout.splitlines() if r]


def verify_step0(show: bool = True) -> dict:
    out = {f"{r[0]}.{r[1]}.{r[2]}": r[3] if len(r) > 3 else "" for r in rows(verify_statements()[0])}
    if show:
        for k, v in out.items():
            print(f"    {k:<40} {v[:150]}")
    return out


def verify_step1() -> bool:
    out = rows(verify_statements()[1])
    for r in out:
        print(f"    {'ok ' if r[-1] == 't' else 'BAD'} {r[0]}")
    bad = [r[0] for r in out if r[-1] != "t"]
    print(f"  {'PASS' if out and not bad else 'FAIL'} step 1 catalog: {len(out) - len(bad)}/{len(out)} ok {bad or ''}")
    return bool(out) and not bad


def block(name: str, tag: str) -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(rf"-- {name} -+\n(do \${tag}\$.*?\${tag}\$;)", text, re.S)
    if not m:
        sys.exit(f"could not find the {name} block in the migration")
    return m.group(1)


def rollback_block() -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(r"^-- ROLLBACK-BEGIN\n(.*?)^-- ROLLBACK-END$", text, re.S | re.M)
    if not m:
        sys.exit("could not find the ROLLBACK-BEGIN..ROLLBACK-END block in the migration header")
    return "\n".join(re.sub(r"^--  ?", "", l, count=1) for l in m.group(1).splitlines()) + "\n"


def guard_probe(plant: str | None, body: str, label: str, want: str, want_ok: bool) -> bool:
    """Run `body` after planting `plant`, inside a rolled-back txn. want_ok: must succeed with `want` in a NOTICE;
    else must fail with `want` in the error."""
    pre = (plant + ";\n") if plant else ""
    p = psql([], stdin=f"begin;\n{pre}{body}\nrollback;\n", check=False)
    ok = (p.returncode == 0 and want in p.stderr) if want_ok else (p.returncode != 0 and want in p.stderr)
    tail = (p.stderr.strip().splitlines() or [""])
    msg = next((l for l in tail if "ERROR" in l), None) or next((l for l in tail if "NOTICE" in l), tail[-1])
    print(f"  {'PASS' if ok else 'FAIL'} {label}: {msg.strip()[:230]}")
    return ok


def probe() -> dict:
    out = kv(PROBE_SQL)
    for k, v in out.items():
        print(f"    {k:<28} {v}")
    return out


def read_as(role: str, rel: str) -> str:
    sel = f"select count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x), '')) from {rel} x"
    p = psql(["-q", "-tA"], stdin=f"\\set VERBOSITY verbose\nbegin;\nset local role {role};\n{sel};\nrollback;\n",
             check=False)
    if p.returncode == 0:
        got = [l for l in p.stdout.splitlines() if l.strip()]
        return got[-1].strip() if got else "ERR empty"
    code = re.search(r"ERROR:\s+([0-9A-Z]{5}):", p.stderr)
    return f"denied {code.group(1)}" if code else "ERR " + p.stderr.strip()[-120:]


def role_reads() -> dict:
    return {f"{role}:{v}": read_as(role, v) for role in ("anon", "authenticated") for v in VIEWS}


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


def print_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")


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


REST_TARGETS = [("signal_read", "v_topic_movement"), ("signal_read", "v_topic_intersections")]


def rest_probe(key: str, schema: str, rel: str) -> dict:
    url = f"{TWIN_REST}/{rel}?select=*"
    if TWIN_REF not in url or PROD_REF in url or not url.split("?")[0].endswith("/" + rel):
        sys.exit(f"REFUSED: bad REST probe URL {url}")
    req = urllib.request.Request(url, headers={"apikey": key, "Accept-Profile": schema, "Prefer": "count=exact",
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, body, cr = r.status, r.read(), r.headers.get("Content-Range", "")
    except urllib.error.HTTPError as e:
        status, body, cr = e.code, e.read(), e.headers.get("Content-Range", "")
    total = cr.rsplit("/", 1)[-1] if "/" in cr else "?"
    res = {"url": url, "status": status, "total": total, "md5": ""}
    try:
        data = json.loads(body or b"null")
    except ValueError:
        data = None
    if status in (200, 206) and isinstance(data, list):
        res["md5"] = hashlib.md5("|".join(sorted(json.dumps(x, sort_keys=True) for x in data)).encode()).hexdigest()
        res["returned"] = len(data)
    else:
        res["error"] = (data.get("code", "") + " " + data.get("message", ""))[:90] if isinstance(data, dict) else ""
    return res


def rest_probes(key: str) -> dict:
    out = {}
    for schema, rel in REST_TARGETS:
        r = rest_probe(key, schema, rel)
        out[f"{schema}.{rel}"] = r
        print(f"    GET {r['url']}  [Accept-Profile: {schema}] -> HTTP {r['status']} total={r['total']}"
              + (f" returned={r['returned']} md5={r['md5'][:12]}" if 'returned' in r else f" {r.get('error', '')}"))
    return out


def rest_sig(r: dict) -> tuple:
    return (r["status"], r["total"], r["md5"])


def api_has(p: dict, role: str) -> bool:
    """True if `role` holds anything on any of the probe's new objects."""
    return bool(p.get(f"{role}.table")) or bool(p.get(f"{role}.sequence")) \
        or p.get(f"{role}.function") == "true" or p.get(f"{role}.mi_function") == "true"


EXPECTED_STEP0_CHANGE = {
    "postgres.public.r": ("anon:SELECT,authenticated:SELECT,", ""),
    "postgres.public.S": ("anon:SELECT,anon:UPDATE,anon:USAGE,authenticated:SELECT,authenticated:UPDATE,"
                          "authenticated:USAGE,", ""),
    "postgres.public.f": ("anon:EXECUTE,authenticated:EXECUTE,", ""),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--leave-applied", action="store_true")
    ap.add_argument("--publishable-key", default=None, help="twin publishable key (else TWIN_PUBLISHABLE_KEY)")
    a = ap.parse_args()
    for f in (MIGRATION, VERIFY):
        if not os.path.exists(f):
            sys.exit(f"missing {f}")
    refuse_non_twin()
    pre_block, post_block = block("PART 1", "pre"), block("PART 3", "post")
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1: {len(pre_block)} chars; PART 3: "
          f"{len(post_block)} chars; rollback block: {len(rollback_block().splitlines())} lines")
    if len(verify_statements()) != 2:
        sys.exit("verify file must hold exactly 2 statements (step 0, step 1)")
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] preflight")
    if not guard_probe(None, pre_block, "PART 1 sees the PRE state", "preflight OK: PRE state", True):
        print("  FAIL twin is not in the PRE state. Roll it back first.")
        return 1
    print("  staging/0029_verify.sql step 0 (run the same on prod before and after the paste):")
    step0 = verify_step0()
    if a.preflight_only:
        print("PREFLIGHT OK")
        return 0

    key = publishable_key(a.publishable_key)
    ok = True
    print("[1] snapshot A")
    DA, OA = kv(DEFAULTS_SQL), kv(OBJECTS_SQL)
    print(f"    default ACL rows: {len(DA)}; existing-object grant keys over {', '.join(SCHEMAS)}: {len(OA)}")
    print(f"    object snapshot md5: {hashlib.md5(json.dumps(OA, sort_keys=True).encode()).hexdigest()}")
    reads_a = role_reads()
    for k, v in reads_a.items():
        print(f"    {k:<55} {v}")
    if not all(":" in v and not v.startswith("0:") for v in reads_a.values()):
        print("  FAIL anon/authenticated do not read non-empty views before apply")
        return 1

    print("[1a] negative control: before apply, new objects ARE granted to anon/authenticated")
    pa = probe()
    nc = api_has(pa, "anon") and api_has(pa, "authenticated") and pa.get("anon.function") == "true"
    print(f"  {'PASS' if nc else 'FAIL'} anon and authenticated hold privileges on new objects before apply "
          f"(anon table={pa.get('anon.table')}, sequence={pa.get('anon.sequence')}, fn={pa.get('anon.function')}, "
          f"mi fn={pa.get('anon.mi_function')})")
    if not nc:
        return 1

    print("[1b] supabase_admin limitation (rolled back)")
    p = psql([], stdin=SUPABASE_ADMIN_ATTEMPT, check=False)
    refused = p.returncode != 0 and ("permission denied" in p.stderr or "42501" in p.stderr)
    err = next((l for l in p.stderr.splitlines() if "ERROR" in l), p.stderr.strip()[-160:])
    print(f"  {'PASS' if refused else 'FAIL'} postgres cannot alter supabase_admin's defaults: {err.strip()[:200]}")
    ok &= refused

    print("[1c] guard probes (rolled back)")
    ok &= guard_probe(PLANT_MIXED, pre_block, "mixed state (only the tables default revoked) refused",
                      "mixed or unexpected state", False)
    ok &= guard_probe(PLANT_OTHER_SCHEMA, pre_block, "unexpected postgres default ACL in schema mi refused",
                      "unexpected postgres default ACLs", False)
    ok &= guard_probe(None, pre_block + "\n" + post_block, "wrong end state (PART 2 skipped): postflight raises",
                      "postflight FAILED", False)
    if not ok:
        return 1

    print(f"[1d] REST as anon before apply ({TWIN_REST}, twin publishable key)")
    rest_a = rest_probes(key)
    views_open = all(r["status"] in (200, 206) and r["total"].isdigit() and int(r["total"]) > 0 for r in rest_a.values())
    print(f"  {'PASS' if views_open else 'FAIL'} both views return rows to anon over REST before apply")
    if not views_open:
        return 1

    print("[2] apply 0029")
    good, n = run_sql(MIGRATION, "apply")
    if not good or not any("postflight OK" in x for x in n):
        print("  FAIL apply (or no 'postflight OK' notice)")
        return 1
    DB, OB = kv(DEFAULTS_SQL), kv(OBJECTS_SQL)
    print("  default ACLs that changed (A -> B):")
    print_diff(diff(DA, DB))

    print("[3] re-apply (idempotent)")
    good, n = run_sql(MIGRATION, "re-apply")
    if not good:
        return 1
    d = diff({**DB, **OB}, {**kv(DEFAULTS_SQL), **kv(OBJECTS_SQL)})
    noop = not d and any("already applied" in x for x in n)
    print(f"  {'PASS' if noop else 'FAIL'} re-apply is a no-op (defaults + objects unchanged, 'already applied' notice)")
    print_diff(d)
    ok &= noop

    print("[4] verify (staging/0029_verify.sql)")
    ok &= verify_step1()
    step0_after = verify_step0(show=False)
    d0 = diff(step0, step0_after)
    want_keys = set(EXPECTED_STEP0_CHANGE) | {"postgres.(global).f"}
    exact = set(d0) == want_keys and d0["postgres.(global).f"] == (None, "postgres:EXECUTE")
    for k, (rm, _) in EXPECTED_STEP0_CHANGE.items():
        before, after = d0.get(k, (None, None))
        exact &= before is not None and after is not None and before.replace(rm, "", 1) == after and rm in before
    print(f"  {'PASS' if exact else 'FAIL'} step 0 changed exactly as expected (public r/S/f lose anon+authenticated; "
          f"global f = postgres:EXECUTE; every other row, service_role and storage included, identical)")
    print_diff(d0)
    ok &= exact

    print("[4a] probe after apply: new objects are NOT granted to anon/authenticated")
    pb = probe()
    closed = not api_has(pb, "anon") and not api_has(pb, "authenticated")
    print(f"  {'PASS' if closed else 'FAIL'} anon and authenticated hold no privilege on any new object")
    sr = (pb.get("service_role.table") == "DELETE,INSERT,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE"
          and pb.get("service_role.sequence") == "SELECT,UPDATE,USAGE" and pb.get("service_role.function") == "true")
    print(f"  {'PASS' if sr else 'FAIL'} service_role keeps full table rights, sequence rwU and EXECUTE on new public "
          f"objects (before: table={pa.get('service_role.table')} seq={pa.get('service_role.sequence')} "
          f"fn={pa.get('service_role.function')})")
    print(f"  INFO service_role on a new mi function: before={pa.get('service_role.mi_function')} after="
          f"{pb.get('service_role.mi_function')} (was via PUBLIC; mi has no schema default, so grant explicitly)")
    ok &= closed and sr

    print("[4b] existing objects untouched")
    d = diff(OA, OB)
    print(f"  {'PASS' if not d else 'FAIL'} existing-object grants byte-identical to snapshot A ({len(OA)} keys)")
    print_diff(d)
    ok &= not d
    reads_b = role_reads()
    d = diff(reads_a, reads_b)
    print(f"  {'PASS' if not d else 'FAIL'} signal_read views as anon/authenticated identical to snapshot A")
    print_diff(d)
    ok &= not d

    print("[4c] REST as anon after apply")
    rest_b = rest_probes(key)
    for t, r in rest_b.items():
        same = rest_sig(r) == rest_sig(rest_a[t])
        print(f"  {'PASS' if same else 'FAIL'} {t} same as before: HTTP {rest_a[t]['status']} -> {r['status']}, total "
              f"{rest_a[t]['total']} -> {r['total']}, md5 {rest_a[t]['md5'][:12]} -> {r['md5'][:12]}")
        ok &= same

    print("[5] rollback (header block, verbatim)")
    good, _ = run_sql(rollback_block(), "rollback", is_file=False)
    if not good:
        return 1
    print("[6] snapshot C == snapshot A")
    d = diff(DA, kv(DEFAULTS_SQL))
    print(f"  {'PASS' if not d else 'FAIL'} default ACLs equal snapshot A ({len(DA)} rows)")
    print_diff(d)
    ok &= not d
    d = diff(OA, kv(OBJECTS_SQL))
    print(f"  {'PASS' if not d else 'FAIL'} existing-object grants equal snapshot A ({len(OA)} keys)")
    print_diff(d)
    ok &= not d
    d = diff(reads_a, role_reads())
    print(f"  {'PASS' if not d else 'FAIL'} role reads equal snapshot A")
    ok &= not d
    back = guard_probe(None, pre_block, "PART 1 sees the PRE state again", "preflight OK: PRE state", True)
    ok &= back
    pc = probe()
    d = diff(pa, pc)
    print(f"  {'PASS' if not d else 'FAIL'} new-object probe equals gate 1a (anon privileges back)")
    print_diff(d)
    ok &= not d
    print("[6b] REST as anon after rollback == gate 1d")
    rest_c = rest_probes(key)
    d = {t: (rest_sig(rest_a[t]), rest_sig(rest_c[t])) for t in rest_a if rest_sig(rest_a[t]) != rest_sig(rest_c[t])}
    print(f"  {'PASS' if not d else 'FAIL'} REST probes equal gate 1d ({len(rest_a)} targets)")
    print_diff(d)
    ok &= not d
    print(f"  {'PASS ROLLBACK PROVEN' if ok else 'FAIL'}")

    if a.leave_applied and ok:
        print("[7] leave applied")
        good, _ = run_sql(MIGRATION, "apply")
        ok &= good and verify_step1()
    print(f"\nREHEARSAL 0029: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
