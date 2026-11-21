#!/usr/bin/env python3
"""
rehearse_0028.py — prove migration 0028 (signal_read views run with owner rights; anon/authenticated lose direct
SELECT on topic_intelligence.topic_cluster/topic_trend/topic_pair_metric; YED-311 option A) on the Phantom-Test-Case
twin before Alex pastes it into prod (invariant 2).
Twin-only constants and refusal logic are byte-identical to rehearse_0027.py (scrubbed child env, no override flag).

Gates (all must pass, in order):
  0  preflight     twin reachable; PRE state (views security_invoker = on, 3 anon policies); 0025/0026 + pre2b
                   present; prints staging/0028_verify.sql step 0 (view count + md5) for comparison with prod
  1  snapshot A    fingerprint: view reloptions/owner/ACL/definition, base-table owner/RLS/ACL/column ACL, policies,
                   schema ACLs, default ACLs, dependents, base-table row md5; 0025/0026/pre2b context
                   + ROLE READS: anon, authenticated, service_role x (2 views: count + md5 of the full output ordered
                   by every column; 3 base tables: count), or the SQLSTATE when denied
  1a negative ctl  before apply, anon and authenticated CAN read all 3 base tables (else the revoke proves nothing)
  1b guard probes  (rolled back) the migration's PART 1 must REFUSE when (i) another anon-readable view reads a base
                   table, (ii) an anon-executable caller-rights function names one, (iii) the state is mixed
                   (one policy missing), (iv) anon holds another privilege in topic_intelligence (the schema USAGE
                   revoke would break it); and pass on the clean twin
  1c REST before   as anon over PostgREST with the twin's publishable key: the 3 base tables ARE readable (the live
                   exposure, reproduced) and both views return rows; full URL printed per probe
  2  apply 0028    the migration file verbatim
  3  re-apply      second paste is a NOTICE no-op (fingerprint unchanged)
  4  verify        staging/0028_verify.sql step 1: every row ok = t; step 0 view rows equal gate 0;
                   step 2 as anon and as authenticated (begin; set local role; rollback): every row ok = t
  4b roles         anon + authenticated: each view IDENTICAL to snapshot A (count + md5); base tables denied 42501.
                   service_role: base-table reads unchanged; view reads printed before/after (0002 never granted
                   them to service_role)
  4c REST after    base tables refused (401/403) or empty; each view returns the same count + md5 as gate 1c
  5  rollback      the ROLLBACK-BEGIN..ROLLBACK-END block from the migration header, verbatim
  6  snapshot C    must EQUAL snapshot A, role reads included: ROLLBACK PROVEN only if so; REST probes equal 1c
  (--leave-applied re-applies 0028 + verify at the end.)

Usage:
  python3 supabase/scripts/rehearse_0028.py                   # dry run, no connection
  python3 supabase/scripts/rehearse_0028.py --preflight-only
  TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0028.py --execute   # full gate, ends rolled back

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
MIGRATION = os.path.join(SUPA, "migrations", "0028_signal_views_owner_rights.sql")
VERIFY = os.path.join(SUPA, "staging", "0028_verify.sql")
VIEWS = ["signal_read.v_topic_movement", "signal_read.v_topic_intersections"]
BASE = ["topic_intelligence.topic_cluster", "topic_intelligence.topic_trend", "topic_intelligence.topic_pair_metric"]
ROLES = ["anon", "authenticated", "service_role"]

# ACLs are compared as sorted (grantor, grantee, privilege, grantable) sets: revoke + re-grant appends entries at the
# end of the aclitem array, so the raw array text changes order while the privileges are identical.
ACL = ("coalesce((select string_agg(e, ',' order by e) from (select a.grantor::regrole::text||'>'||"
       "case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end||':'||a.privilege_type||':'||"
       "a.is_grantable::text as e from aclexplode({}) a) s), '')")
SNAPSHOT_SQL = f"""
select 'view.'||c.relname, coalesce(c.reloptions::text,'')||' owner='||c.relowner::regrole::text||' acl='||
       {ACL.format('c.relacl')}||' def='||md5(pg_get_viewdef(c.oid))
  from pg_class c where c.relnamespace = 'signal_read'::regnamespace;
select 'tbl.'||c.relname, 'owner='||c.relowner::regrole::text||' rls='||c.relrowsecurity::text||' force='||
       c.relforcerowsecurity::text||' acl='||{ACL.format('c.relacl')}||' colacl='||
       coalesce((select string_agg(a.attname||'='||a.attacl::text, ',' order by a.attname) from pg_attribute a
                 where a.attrelid = c.oid and a.attacl is not null), '')
  from pg_class c where c.relnamespace = 'topic_intelligence'::regnamespace and c.relkind in ('r', 'v', 'm');
select 'ti.policies', coalesce(string_agg(tablename||'.'||policyname||':'||permissive||':'||roles::text||':'||
         cmd||':'||coalesce(qual,'')||':'||coalesce(with_check,''), '|' order by tablename, policyname), '')
  from pg_policies where schemaname = 'topic_intelligence';
select 'nsp.'||nspname, {ACL.format('nspacl')} from pg_namespace
 where nspname in ('signal_read', 'topic_intelligence', 'mi', 'public');
select 'default_acl', md5(coalesce(string_agg(e, '|' order by e), '')) from (select defaclrole::regrole::text||':'||
         defaclnamespace::text||':'||defaclobjtype::text||':'||defaclacl::text as e from pg_default_acl) s;
select 'deps', coalesce(string_agg(distinct d.refobjid::regclass::text||'<-'||c.oid::regclass::text, ', '), '')
  from pg_depend d join pg_rewrite rw on rw.oid = d.objid join pg_class c on c.oid = rw.ev_class
 where d.classid = 'pg_rewrite'::regclass and c.oid <> d.refobjid
   and d.refobjid in ('topic_intelligence.topic_cluster'::regclass, 'topic_intelligence.topic_trend'::regclass,
                      'topic_intelligence.topic_pair_metric'::regclass);
select 'rows.topic_cluster', count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x::text), ''))
  from topic_intelligence.topic_cluster x;
select 'rows.topic_trend', count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x::text), ''))
  from topic_intelligence.topic_trend x;
select 'rows.topic_pair_metric', count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x::text), ''))
  from topic_intelligence.topic_pair_metric x;
select 'ctx.public.functions', md5(coalesce(string_agg(p.oid::regprocedure::text||':'||coalesce(p.proacl::text,'')||
         ':'||md5(p.prosrc), '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p where p.pronamespace = 'public'::regnamespace;
select 'ctx.claim_source_quote', (select count(*) from information_schema.columns where table_schema = 'public'
         and table_name = 'claim' and column_name in ('source_quote', 'source_quote_fetched_at'))::text;
select 'ctx.pre2b_rels', (select count(*) from pg_class where relnamespace = to_regnamespace('pre2b'))::text;
"""

PREFLIGHT_SQL = """
select 'pre2b_present', (to_regnamespace('pre2b') is not null)::text;
select 'v2_present', (to_regprocedure('public.no_contact_pii_v2(text)') is not null)::text;
select 'source_quote_present', exists (select 1 from information_schema.columns where table_schema = 'public'
       and table_name = 'claim' and column_name = 'source_quote')::text;
select 'views_invoker_on', (select count(*) from pg_class where oid in ('signal_read.v_topic_movement'::regclass,
       'signal_read.v_topic_intersections'::regclass) and 'security_invoker=on' = any (coalesce(reloptions, '{}')))::text;
select 'anon_policies', (select count(*) from pg_policies where schemaname = 'topic_intelligence'
       and policyname in ('tc_anon_read', 'tt_anon_read', 'tpm_anon_read'))::text;
select 'anon_ti_usage', has_schema_privilege('anon', 'topic_intelligence', 'usage')::text;
"""

# guard probes: each plants one condition, runs PART 1, and must see it refused; always rolled back
PROBE_VIEW = ("create view public.rehearse_0028_probe with (security_invoker = on) as "
              "select cluster_id from topic_intelligence.topic_cluster; "
              "grant select on public.rehearse_0028_probe to anon")
PROBE_FN = ("create function public.rehearse_0028_probe() returns bigint language plpgsql as "
            "$f$ begin return (select count(*) from topic_intelligence.topic_trend); end $f$; "
            "grant execute on function public.rehearse_0028_probe() to anon")
PROBE_MIXED = "drop policy tt_anon_read on topic_intelligence.topic_trend"
PROBE_OTHER_PRIV = "grant select on topic_intelligence.topics to anon"


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


def notices(stderr: str) -> list[str]:
    return [l.split("NOTICE:", 1)[1].strip() for l in stderr.splitlines() if "NOTICE:" in l and "0028" in l]


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


def verify_step0() -> list[list[str]]:
    out = rows(verify_statements()[0])
    for r in out:
        print(f"    {r[0]:<28} n={r[1]:<4} {('md5=' + r[2]) if r[2] else ''}")
    return out


def verify_step1() -> bool:
    out = rows(verify_statements()[1])
    for r in out:
        print(f"    {'ok ' if r[-1] == 't' else 'BAD'} {r[0]}")
    bad = [r[0] for r in out if r[-1] != "t"]
    print(f"  {'PASS' if not bad else 'FAIL'} step 1 catalog: {len(out) - len(bad)}/{len(out)} ok {bad or ''}")
    return not bad


def part1_block() -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(r"-- PART 1 -+\n(do \$pre\$.*?\$pre\$;)", text, re.S)
    if not m:
        sys.exit("could not find the PART 1 preflight block in the migration")
    return m.group(1)


def rollback_block() -> str:
    text = open(MIGRATION, encoding="utf-8").read()
    m = re.search(r"^-- ROLLBACK-BEGIN\n(.*?)^-- ROLLBACK-END$", text, re.S | re.M)
    if not m:
        sys.exit("could not find the ROLLBACK-BEGIN..ROLLBACK-END block in the migration header")
    return "\n".join(re.sub(r"^--  ?", "", l, count=1) for l in m.group(1).splitlines()) + "\n"


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


def read_as(role: str, rel: str) -> str:
    """What `role` gets from `rel`: views -> 'n:md5' of the full output ordered by every column (order by the row
    value compares column by column); base tables -> 'n'. Denied -> 'denied <SQLSTATE>'."""
    if rel in VIEWS:
        sel = f"select count(*)||':'||md5(coalesce(string_agg(x::text, '|' order by x), '')) from {rel} x"
    else:
        sel = f"select count(*)::text from {rel}"
    p = psql(["-q", "-tA"], stdin=f"\\set VERBOSITY verbose\nbegin;\nset local role {role};\n{sel};\nrollback;\n",
             check=False)
    if p.returncode == 0:
        got = [l for l in p.stdout.splitlines() if l.strip()]
        return got[-1].strip() if got else "ERR empty"
    code = re.search(r"ERROR:\s+([0-9A-Z]{5}):", p.stderr)
    return f"denied {code.group(1)}" if code else "ERR " + p.stderr.strip()[-120:]


def role_reads() -> dict:
    return {f"{role}:{rel}": read_as(role, rel) for role in ROLES for rel in VIEWS + BASE}


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


def verify_step2(role: str, info: bool = False) -> bool:
    """staging/0028_verify.sql step 2 run AS `role` inside a rolled-back transaction."""
    p = psql(["-q", "-tA", "-F", "\t"],
             stdin=f"begin;\nset local role {role};\n{verify_statements()[2]};\nrollback;\n", check=False)
    if p.returncode != 0:
        print(f"  FAIL step 2 as {role}: {p.stderr.strip()[-200:]}")
        return False
    out = [r.split("\t") for r in p.stdout.splitlines() if "\t" in r]
    for r in out:
        print(f"    {'ok ' if r[-1] == 't' else 'BAD'} {r[0]}")
    bad = [r[0] for r in out if r[-1] != "t"]
    verdict = "INFO" if info else ("PASS" if out and not bad else "FAIL")
    print(f"  {verdict} step 2 as {role}: {len(out) - len(bad)}/{len(out)} ok")
    return bool(out) and not bad


REST_TARGETS = [("signal_read", "v_topic_movement"), ("signal_read", "v_topic_intersections"),
                ("topic_intelligence", "topic_cluster"), ("topic_intelligence", "topic_trend"),
                ("topic_intelligence", "topic_pair_metric")]


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


def rest_probe(key: str, schema: str, rel: str) -> dict:
    """GET <twin>/rest/v1/<rel>?select=* as anon (publishable key). Returns status, exact total from
    Content-Range, and an md5 of the body rows (sorted canonical JSON) for the views."""
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
    res = {"url": url, "profile": schema, "status": status, "total": total, "md5": ""}
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


def rest_readable(r: dict) -> bool:
    return r["status"] in (200, 206) and r["total"].isdigit() and int(r["total"]) > 0


def rest_sig(r: dict) -> tuple:
    return (r["status"], r["total"], r["md5"])


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
    print(f"twin {TWIN_HOST} as {TWIN_USER}; migration {os.path.relpath(MIGRATION, REPO)}; "
          f"verify statements: {len(verify_statements())}; PART 1 block: {len(part1_block())} chars; "
          f"rollback block: {len(rollback_block().splitlines())} lines")
    if len(verify_statements()) != 3:
        sys.exit("verify file must hold exactly 3 statements (step 0, step 1, step 2)")
    if not (a.execute or a.preflight_only):
        print("dry run: no connection. Use --preflight-only or --execute.")
        return 0

    print("[0] preflight")
    pf = kv(PREFLIGHT_SQL)
    print("  " + " ".join(f"{k}={v}" for k, v in pf.items()))
    if pf.get("views_invoker_on") != "2" or pf.get("anon_policies") != "3" or pf.get("anon_ti_usage") != "true":
        print("  FAIL twin is not in the PRE state (2 security_invoker views, 3 anon policies). Roll it back first.")
        return 1
    print("  staging/0028_verify.sql step 0 (run the same on prod before and after the paste):")
    step0 = verify_step0()
    if a.preflight_only:
        print("PREFLIGHT OK")
        return 0

    key = publishable_key(a.publishable_key)
    ok = True
    print("[1] snapshot A")
    A = snapshot()
    for k, v in A.items():
        print(f"    {k:<28} {v[:150]}")
    print("  role reads (snapshot A):")
    reads_a = role_reads()
    print_reads(reads_a)

    print("[1a] negative control: before apply, anon and authenticated CAN read the base tables")
    nc = [f"{r}:{t}" for r in ("anon", "authenticated") for t in BASE]
    nc_ok = all(reads_a[k].isdigit() and int(reads_a[k]) > 0 for k in nc)
    print(f"  {'PASS' if nc_ok else 'FAIL'} " + ", ".join(f"{k}={reads_a[k]}" for k in nc))
    view_ok = all(":" in reads_a[f"{r}:{v}"] and not reads_a[f"{r}:{v}"].startswith("0:")
                  for r in ("anon", "authenticated") for v in VIEWS)
    print(f"  {'PASS' if view_ok else 'FAIL'} anon/authenticated read non-empty views before apply")
    if not (nc_ok and view_ok):
        return 1
    print("  step 2 as anon before apply (INFO: the no-access rows are expected BAD here):")
    verify_step2("anon", info=True)

    print("[1b] guard probes (rolled back)")
    ok &= guard_probe(None, "clean twin passes", None)
    ok &= guard_probe(PROBE_VIEW, "other anon-readable view on a base table refused", "other views readable")
    ok &= guard_probe(PROBE_FN, "anon-executable caller-rights function refused", "caller-rights functions")
    ok &= guard_probe(PROBE_MIXED, "mixed state (one policy missing) refused", "mixed state")
    ok &= guard_probe(PROBE_OTHER_PRIV, "other anon privilege in topic_intelligence refused", "hold other privileges")
    if not ok:
        return 1

    print(f"[1c] REST as anon before apply ({TWIN_REST}, twin publishable key)")
    rest_a = rest_probes(key)
    base = [t for t in rest_a if t.startswith("topic_intelligence.")]
    base_open = all(rest_readable(rest_a[t]) for t in base)
    # Prod exposes topic_intelligence in its PostgREST "exposed schemas"; the twin may not (a dashboard setting, not
    # DDL; this harness does not change it). Then PostgREST answers 406 PGRST106 before it ever reaches Postgres, the
    # REST base-table negative control cannot be reproduced here, and the DB-layer proof (gates 1a + 4b: `set role
    # anon`, which is what PostgREST does per request) carries it. Reported as N/A, never as PASS.
    base_not_exposed = all(rest_a[t]["status"] == 406 and "PGRST106" in rest_a[t].get("error", "") for t in base)
    views_open = all(rest_readable(rest_a[t]) for t in rest_a if t.startswith("signal_read."))
    if base_open:
        print("  PASS base tables readable by anon over REST before apply (exposure reproduced)")
    elif base_not_exposed:
        print("  N/A  base tables over REST: the twin does not expose schema topic_intelligence to PostgREST "
              "(406 PGRST106), unlike prod; the base-table negative control rests on gate 1a (DB layer)")
    else:
        print("  FAIL base tables neither readable nor 'schema not exposed' over REST before apply")
    print(f"  {'PASS' if views_open else 'FAIL'} views return rows to anon over REST before apply")
    if not ((base_open or base_not_exposed) and views_open):
        print("  STOP: the REST negative control does not hold on the twin, so the after-probe would prove nothing.")
        return 1

    print("[2] apply 0028")
    good, _ = run_sql(MIGRATION, "apply")
    if not good:
        return 1
    B = snapshot()
    print("  what changed (A -> B):")
    print_diff(diff(A, B))
    print("[3] re-apply (idempotent)")
    good, n = run_sql(MIGRATION, "re-apply")
    if not good:
        return 1
    d = diff(B, snapshot())
    noop = not d and any("already applied" in x for x in n)
    print(f"  {'PASS' if noop else 'FAIL'} re-apply is a no-op (fingerprint unchanged, 'already applied' notice)")
    print_diff(d)
    ok &= noop

    print("[4] verify (staging/0028_verify.sql)")
    ok &= verify_step1()
    print("  step 0 after apply:")
    step0_after = verify_step0()
    same_views = [r for r in step0_after if r[0].startswith("v_")] == [r for r in step0 if r[0].startswith("v_")]
    print(f"  {'PASS' if same_views else 'FAIL'} step 0 view rows (count + md5, as owner) equal gate 0")
    ok &= same_views

    for role in ("anon", "authenticated"):
        ok &= verify_step2(role)
    print("[4b] role reads after apply")
    reads_b = role_reads()
    print_reads(reads_b)
    for role in ("anon", "authenticated"):
        for v in VIEWS:
            k = f"{role}:{v}"
            same = reads_b[k] == reads_a[k]
            print(f"  {'PASS' if same else 'FAIL'} {k} identical to snapshot A ({reads_a[k]})")
            ok &= same
        for t in BASE:
            k = f"{role}:{t}"
            denied = reads_b[k] == "denied 42501"
            print(f"  {'PASS' if denied else 'FAIL'} {k} now {reads_b[k]} (was {reads_a[k]}; expect denied 42501)")
            ok &= denied
    for t in BASE:
        k = f"service_role:{t}"
        same = reads_b[k] == reads_a[k]
        print(f"  {'PASS' if same else 'FAIL'} {k} unchanged ({reads_a[k]} -> {reads_b[k]})")
        ok &= same
    for v in VIEWS:
        k = f"service_role:{v}"
        print(f"  INFO {k}: before={reads_a[k]} after={reads_b[k]}"
              f" ({'unchanged' if reads_a[k] == reads_b[k] else 'CHANGED'})")

    print("[4c] REST as anon after apply")
    rest_b = rest_probes(key)
    for t, r in rest_b.items():
        if t.startswith("topic_intelligence.") and base_not_exposed:
            same = r["status"] == 406
            print(f"  {'N/A ' if same else 'FAIL'} {t} HTTP {r['status']} (schema still not exposed on the twin; "
                  "the DB-layer refusal is gate 4b)")
            ok &= same
        elif t.startswith("topic_intelligence."):
            shut = r["status"] in (401, 403) or (r["status"] in (200, 206) and r["total"] == "0")
            print(f"  {'PASS' if shut else 'FAIL'} {t} refused or empty (HTTP {r['status']} total={r['total']}; "
                  f"was HTTP {rest_a[t]['status']} total={rest_a[t]['total']})")
            ok &= shut
        else:
            same = rest_sig(r) == rest_sig(rest_a[t])
            print(f"  {'PASS' if same else 'FAIL'} {t} same as before: total {rest_a[t]['total']} -> {r['total']}, "
                  f"md5 {rest_a[t]['md5'][:12]} -> {r['md5'][:12]}")
            ok &= same

    print("[5] rollback (header block, verbatim)")
    good, _ = run_sql(rollback_block(), "rollback", is_file=False)
    if not good:
        return 1
    print("[6] snapshot C == snapshot A")
    d = diff(A, snapshot())
    print(f"  {'PASS' if not d else 'FAIL'} catalog + row fingerprint equals snapshot A ({len(A)} keys)")
    print_diff(d)
    ok &= not d
    d = diff(reads_a, role_reads())
    print(f"  {'PASS' if not d else 'FAIL'} role reads equal snapshot A ({len(reads_a)} probes)")
    print_diff(d)
    ok &= not d
    pf = kv(PREFLIGHT_SQL)
    back = pf.get("views_invoker_on") == "2" and pf.get("anon_policies") == "3" and pf.get("anon_ti_usage") == "true"
    print(f"  {'PASS ROLLBACK PROVEN' if ok and back else 'FAIL'}: twin back in PRE state "
          + " ".join(f"{k}={v}" for k, v in pf.items()))
    ok &= back
    print("[6b] REST as anon after rollback == gate 1c")
    rest_c = rest_probes(key)
    d = {t: (rest_sig(rest_a[t]), rest_sig(rest_c[t])) for t in rest_a if rest_sig(rest_a[t]) != rest_sig(rest_c[t])}
    print(f"  {'PASS' if not d else 'FAIL'} REST probes equal gate 1c ({len(rest_a)} targets)")
    print_diff(d)
    ok &= not d

    if a.leave_applied and ok:
        print("[7] leave applied")
        good, _ = run_sql(MIGRATION, "apply")
        ok &= good and verify_step1()
    print(f"\nREHEARSAL 0028: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
