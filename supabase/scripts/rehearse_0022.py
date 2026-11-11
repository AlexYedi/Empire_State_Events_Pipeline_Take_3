#!/usr/bin/env python3
"""
rehearse_0022.py — prove migration 0022 (knowledge-graph phase 1, shared schema: event kind
'researched' + lens_of, claim.use_count trigger + backfill, norm_name / name_norm indexes /
entity_alias, sweep_query, CHECK widenings, four lane_registry rows; YED-384) on the
Phantom-Test-Case twin before Alex pastes it into prod (CLAUDE.md invariant 2).
Shape: rehearse_0016.py (twin-only constants, scrubbed child env, VERIFY/ROLLBACK parsed from the
migration itself so the bytes Alex pastes are the bytes proven here) + rehearse_0019/0020's
negative control (the checks must FAIL on the un-migrated state, else they prove nothing).

Gates (all must pass, in order):
  0  preflight     twin reachable; prerequisites (0009 claim layer, 0016 lens_of + lane_registry,
                   topic_intelligence.topic_cluster, service_role/anon); no 0022 objects yet
                   (else --reset-first); no norm_name collisions in the twin's company/topic rows
  0b fixtures      commit 3 claim_usage rows on the twin (used_at in 2000-01-01, the cleanup key)
                   so the backfill has real work and use_count_matches_usage can discriminate
  1  snapshot A    schema fingerprint (public, mi, topic_intelligence: columns, constraints,
                   indexes, triggers, function ACL/config/BODY, relations + RLS + ACL, policies)
                   + row counts + sum(use_count) + count(last_used_at)
  1b negative      the VERIFY block on the un-migrated twin: every gated check that is not keep_*
                   must NOT return t; every keep_* must return t (fail-closed: an error is never a pass)
  2  apply 0022
  3  re-apply      second paste must be a clean no-op (fingerprint + counts identical)
  4  verify        every VERIFY row t (info_* printed only)
  4b behaviour     twin-only, each case in its own rolled-back transaction under the named role:
                   researched insert / observed refused; trigger insert/insert/update/delete keeps
                   use_count + last_used_at exact; consumer brief/published + method llm accepted,
                   junk refused; name_norm uniqueness bites as service_role; entity_alias norm,
                   dedup and empty-norm refusal; sweep_query vocab / dedup (nulls not distinct) /
                   counters; anon refused on both tables and on norm_name()
  5  planted       each fault alone; VERIFY must fail on the NAMED check; re-apply must restore
     faults        all-t:  5a drop the use_count trigger      -> use_count_trigger_present
                           5b grant anon SELECT on entity_alias -> entity_alias_no_api_grants
                           5c drift one claim's use_count       -> use_count_matches_usage
                           5d drop company_name_norm_uq         -> company_name_norm_unique
                           5e restore the pre-0022 kind CHECK   -> event_kind_researched
                           5f restore 0016's lens_of body       -> lens_of_researched_null
  6  rollback      the ROLLBACK block, verbatim
  7  snapshot C    must EQUAL snapshot A (fingerprint incl. lens_of body, every count, use_count
                   sum, last_used_at count): ROLLBACK PROVEN only if so
  8  cleanup       delete the 0b fixtures; twin claim_usage back to its preflight count
  9  (optional)    --leave-applied re-applies 0022 + verify

HARD REFUSAL: only ever connects to the twin's session pooler as the twin's tenant user with the
twin's password. Host and user are constants (no env overrides), checked before every connection.
Child processes get an environment scrubbed of every variable that names or holds prod material.
No override flag. The password is read from .env and never printed.

Default is a dry run: print the plan from the migration file and exit, with NO connection.

Usage:
  python supabase/scripts/rehearse_0022.py                      # dry run, no connection
  python supabase/scripts/rehearse_0022.py --preflight-only
  python supabase/scripts/rehearse_0022.py --execute            # full gate, ends rolled back
  python supabase/scripts/rehearse_0022.py --execute --leave-applied
  python supabase/scripts/rehearse_0022.py --execute --reset-first   # after an interrupted run
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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

MIGRATION = os.path.join(SUPA, "migrations", "0022_graph_phase1_shared.sql")
FIXTURE_TS = "2000-01-01"          # fixture claim_usage rows carry used_at on this date (cleanup key)
NEW_LANES = ("theme_sweep", "claim_review", "notion_prior", "reconcile")

SCHEMAS = "('public','mi','topic_intelligence')"
COUNT_TABLES = ["public.company", "public.topic", "public.person", "public.event", "public.claim",
                "public.claim_usage", "public.claim_relation", "public.documents",
                "public.lane_registry", "public.lane_run"]

# Everything 0022 could touch. Functions carry md5(prosrc): lens_of's BODY changes, so a rollback
# that restored the signature but not the body would otherwise look identical.
SNAPSHOT_SQL = f"""
select 'cols', md5(coalesce(string_agg(table_schema||'.'||table_name||'.'||column_name||':'||data_type||':'||
         is_nullable||':'||coalesce(column_default,'')||':'||is_generated, '|' order by table_schema, table_name, column_name), ''))
  from information_schema.columns where table_schema in {SCHEMAS};
select 'constraints', md5(coalesce(string_agg(conrelid::regclass::text||'.'||conname||':'||pg_get_constraintdef(oid), '|'
         order by conrelid::regclass::text, conname), ''))
  from pg_constraint where connamespace in (select oid from pg_namespace where nspname in {SCHEMAS});
select 'indexes', md5(coalesce(string_agg(schemaname||'.'||indexname||':'||indexdef, '|' order by schemaname, indexname), ''))
  from pg_indexes where schemaname in {SCHEMAS};
select 'triggers', md5(coalesce(string_agg(tgrelid::regclass::text||'.'||tgname||':'||tgenabled::text||':'||tgtype::text, '|'
         order by tgrelid::regclass::text, tgname), ''))
  from pg_trigger where not tgisinternal
   and tgrelid in (select c.oid from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname in {SCHEMAS});
select 'functions', md5(coalesce(string_agg(p.oid::regprocedure::text||':'||coalesce(p.proacl::text,'')||':'||p.prosecdef::text||':'||
         p.provolatile::text||':'||coalesce(array_to_string(p.proconfig, ','),'')||':'||md5(p.prosrc), '|' order by p.oid::regprocedure::text), ''))
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace where n.nspname in {SCHEMAS};
select 'relations', md5(coalesce(string_agg(n.nspname||'.'||c.relname||':'||c.relkind::text||':'||c.relrowsecurity::text||':'||
         coalesce(c.relacl::text,''), '|' order by n.nspname, c.relname), ''))
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in {SCHEMAS} and c.relkind in ('r','v','m','p','i');
select 'policies', md5(coalesce(string_agg(schemaname||'.'||tablename||'.'||policyname, '|' order by 1), ''))
  from pg_policies where schemaname in {SCHEMAS};
select 'lens_of_src_md5', md5(prosrc) from pg_proc where oid = 'mi.lens_of(text,text,text)'::regprocedure;
select 'data.claim_use_count_sum', coalesce(sum(use_count), 0)::text from public.claim;
select 'data.claim_last_used_at_set', count(last_used_at)::text from public.claim;
select 'data.lane_registry_lanes', string_agg(lane, ',' order by lane) from public.lane_registry;
""" + "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in COUNT_TABLES)

PREFLIGHT_SQL = f"""
select 'has.claim_usage', (to_regclass('public.claim_usage') is not null)::text;
select 'has.claim_relation', (to_regclass('public.claim_relation') is not null)::text;
select 'has.lens_of', (to_regprocedure('mi.lens_of(text,text,text)') is not null)::text;
select 'has.lane_registry', (to_regclass('public.lane_registry') is not null)::text;
select 'has.lane_run', (to_regclass('public.lane_run') is not null)::text;
select 'has.topic_cluster', (to_regclass('topic_intelligence.topic_cluster') is not null)::text;
select 'has.roles', (count(*) = 3)::text from pg_roles where rolname in ('service_role','anon','authenticated');
select 'has.docs_with_claims', (count(*) >= 3)::text from public.claim where document_id is not null;
select 'clean.no_entity_alias', (to_regclass('public.entity_alias') is null)::text;
select 'clean.no_sweep_query', (to_regclass('public.sweep_query') is null)::text;
select 'clean.no_norm_name', (to_regprocedure('public.norm_name(text)') is null)::text;
select 'clean.no_trigger', (count(*) = 0)::text from pg_trigger where tgrelid = 'public.claim_usage'::regclass and tgname = 'claim_usage_sync_use_count';
select 'clean.no_researched', (count(*) = 0)::text from pg_constraint
 where conrelid = 'public.event'::regclass and conname = 'event_kind_enum' and pg_get_constraintdef(oid) like '%researched%';
select 'clean.no_new_lanes', (count(*) = 0)::text from public.lane_registry where lane in ({",".join(f"'{l}'" for l in NEW_LANES)});
select 'clean.no_fixtures', (count(*) = 0)::text from public.claim_usage where used_at < '{FIXTURE_TS}'::date + 1;
select 'info.claim_usage_rows', count(*)::text from public.claim_usage;
select 'info.use_count_nonzero', count(*)::text from public.claim where use_count <> 0 or last_used_at is not null;
"""
REQUIRED = ["has.claim_usage", "has.claim_relation", "has.lens_of", "has.lane_registry", "has.lane_run",
            "has.topic_cluster", "has.roles", "has.docs_with_claims"]
CLEAN = ["clean.no_entity_alias", "clean.no_sweep_query", "clean.no_norm_name", "clean.no_trigger",
         "clean.no_researched", "clean.no_new_lanes", "clean.no_fixtures"]

# The exact norm the migration ships, inlined so the collision probe runs BEFORE the function exists.
NORM_EXPR = ("nullif(trim(regexp_replace(regexp_replace(lower(coalesce(name, '')), "
             "'\\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\\M\\.?', '', 'g'), "
             "'[^a-z0-9]+', ' ', 'g')), '')")
COLLISION_SQL = (f"select 'collisions.company', count(*)::text from (select {NORM_EXPR} k from public.company) s "
                 f"where k is not null group by k having count(*) > 1;\n"
                 f"select 'collisions.topic', count(*)::text from (select {NORM_EXPR} k from public.topic) s "
                 f"where k is not null group by k having count(*) > 1;\n")

# Three fixture usage rows: claim A used by its own document, claim B used by two documents.
FIXTURE_SQL = f"""
begin;
with docs as (select id from public.documents order by id limit 2),
     cl as (select id, document_id from public.claim c
             where document_id is not null
               and not exists (select 1 from public.claim_usage u where u.claim_id = c.id)
             order by id limit 2),
     a as (select id, document_id from cl order by id limit 1),
     b as (select id from cl order by id offset 1 limit 1)
insert into public.claim_usage (claim_id, document_id, consumer, used_at)
select a.id, a.document_id, 'dev', '{FIXTURE_TS} 00:00:01+00' from a
union all
select b.id, d.id, 'dev', ('{FIXTURE_TS} 00:00:0' || (row_number() over (order by d.id) + 1)::text || '+00')::timestamptz
  from b cross join docs d;
commit;
"""
FIXTURE_CLEANUP_SQL = f"delete from public.claim_usage where used_at < '{FIXTURE_TS}'::date + 1;"

# Planted faults: (step, SQL, the VERIFY check that MUST go f).
FAULTS = [
    ("5a", "drop trigger claim_usage_sync_use_count on public.claim_usage;", "use_count_trigger_present"),
    ("5b", "grant select on public.entity_alias to anon;", "entity_alias_no_api_grants"),
    ("5c", f"update public.claim set use_count = use_count + 7 where id = (select claim_id from public.claim_usage "
           f"where used_at < '{FIXTURE_TS}'::date + 1 order by claim_id limit 1);", "use_count_matches_usage"),
    ("5d", "drop index public.company_name_norm_uq;", "company_name_norm_unique"),
    ("5e", "alter table public.event drop constraint event_kind_enum; alter table public.event add constraint "
           "event_kind_enum check (kind in ('attended', 'market', 'funding', 'launch', 'exec_move', 'role_posted', "
           "'application', 'interview', 'reference', 'published'));", "event_kind_researched"),
    ("5f", None, "lens_of_researched_null"),       # SQL = the 0016 lens_of body, taken from the ROLLBACK block
]


# ----------------------------------------------------------------------------- behaviour cases
def _expect_error(sqlstate_name: str, stmt: str, label: str) -> str:
    return f"""  begin
    {stmt};
    raise exception 'FAIL[{label}]: statement was allowed';
  exception when {sqlstate_name} then null;
  end;"""


def behaviour_cases() -> list[tuple[str, str, str]]:
    """(name, role, DO-body). Each runs in its own transaction that is rolled back."""
    ok_note = "raise notice 'PASS';"
    fix = f"used_at < '{FIXTURE_TS}'::date + 1"
    return [
        ("researched_kind", "service_role", f"""
  insert into public.event (title, kind, source) values ('rehearse_0022 researched', 'researched', 'substrate:research');
{_expect_error('check_violation', "insert into public.event (title, kind) values ('rehearse_0022 bad', 'observed')", 'observed')}
  {ok_note}"""),       # the lens of a researched occasion is VERIFY's lens_of_researched_null (mi is not API-exposed)
        ("use_count_trigger", "service_role", f"""
declare cid uuid; d1 uuid; d2 uuid; n int; l timestamptz;
begin
  select c.id into cid from public.claim c where not exists (select 1 from public.claim_usage u where u.claim_id = c.id) order by c.id limit 1;
  select id into d1 from public.documents order by id limit 1;
  select id into d2 from public.documents order by id offset 1 limit 1;
  insert into public.claim_usage (claim_id, document_id, consumer, used_at) values (cid, d1, 'brief', '2026-01-02T00:00:00Z');
  select use_count, last_used_at into n, l from public.claim where id = cid;
  if n <> 1 or l <> '2026-01-02T00:00:00Z' then raise exception 'FAIL[insert1]: % %', n, l; end if;
  insert into public.claim_usage (claim_id, document_id, consumer, used_at) values (cid, d2, 'published', '2026-01-05T00:00:00Z');
  select use_count, last_used_at into n, l from public.claim where id = cid;
  if n <> 2 or l <> '2026-01-05T00:00:00Z' then raise exception 'FAIL[insert2]: % %', n, l; end if;
  update public.claim_usage set used_at = '2026-01-01T00:00:00Z' where claim_id = cid and document_id = d2;
  select use_count, last_used_at into n, l from public.claim where id = cid;
  if n <> 2 or l <> '2026-01-02T00:00:00Z' then raise exception 'FAIL[update]: % %', n, l; end if;
  delete from public.claim_usage where claim_id = cid and document_id = d1;
  select use_count, last_used_at into n, l from public.claim where id = cid;
  if n <> 1 or l <> '2026-01-01T00:00:00Z' then raise exception 'FAIL[delete]: % %', n, l; end if;
  delete from public.claim_usage where claim_id = cid;
  select use_count, last_used_at into n, l from public.claim where id = cid;
  if n <> 0 or l is not null then raise exception 'FAIL[delete-all]: % %', n, l; end if;
  {ok_note}
end"""),
        ("check_widenings", "service_role", f"""
declare c1 uuid; c2 uuid; d1 uuid;
begin
  select id into c1 from public.claim order by id limit 1;
  select id into c2 from public.claim order by id offset 1 limit 1;
  select id into d1 from public.documents order by id offset 1 limit 1;
  insert into public.claim_relation (from_claim_id, to_claim_id, relation, method, confidence) values (c1, c2, 'corroborates', 'llm', 0.9);
{_expect_error('check_violation', "insert into public.claim_relation (from_claim_id, to_claim_id, relation, method) values (c2, c1, 'refines', 'magic')", 'method')}
{_expect_error('check_violation', "insert into public.claim_usage (claim_id, document_id, consumer) values (c2, d1, 'bogus')", 'consumer')}
  {ok_note}
end"""),
        ("name_norm_unique", "service_role", f"""
  insert into public.company (name) values ('Rehearse0022 Widgets');
{_expect_error('unique_violation', "insert into public.company (name) values ('Rehearse0022 Widgets, Inc.')", 'company')}
  insert into public.topic (name) values ('Rehearse0022 topic-x');
{_expect_error('unique_violation', "insert into public.topic (name) values ('rehearse0022 TOPIC x')", 'topic')}
  insert into public.person (name) values ('Rehearse0022 Same Name');
  insert into public.person (name) values ('Rehearse0022 Same-Name');
  {ok_note}"""),
        ("entity_alias", "service_role", f"""
declare cid uuid; nrm text;
begin
  select id into cid from public.company order by id limit 1;
  insert into public.entity_alias (entity_type, entity_id, alias, source) values ('company', cid, 'Rehearse0022 Corp.', 'manual');
  select alias_norm into nrm from public.entity_alias where entity_id = cid and source = 'manual';
  if nrm <> 'rehearse0022' then raise exception 'FAIL[norm]: %', nrm; end if;
{_expect_error('unique_violation', "insert into public.entity_alias (entity_type, entity_id, alias, source) values ('company', gen_random_uuid(), 'REHEARSE0022', 'sweep')", 'dedup')}
  insert into public.entity_alias (entity_type, entity_id, alias, source) values ('topic', gen_random_uuid(), 'rehearse0022', 'sweep');
{_expect_error('check_violation', "insert into public.entity_alias (entity_type, entity_id, alias, source) values ('company', cid, '!!!', 'manual')", 'empty-norm')}
{_expect_error('check_violation', "insert into public.entity_alias (entity_type, entity_id, alias, source) values ('event', cid, 'x', 'manual')", 'type')}
{_expect_error('generated_always', "insert into public.entity_alias (entity_type, entity_id, alias, alias_norm, source) values ('company', cid, 'y', 'y', 'manual')", 'generated')}
  {ok_note}
end"""),
        ("sweep_query", "service_role", f"""
declare th uuid;
begin
  select cluster_id into th from topic_intelligence.topic_cluster order by cluster_id limit 1;
  insert into public.sweep_query (kind, theme_id, template, iso_week) values ('velocity', th, 'agent evals 28d', '2026-W46');
  insert into public.sweep_query (kind, template, iso_week) values ('entity', 'Rehearse0022 Widgets news', '2026-W46');
{_expect_error('unique_violation', "insert into public.sweep_query (kind, template, iso_week) values ('entity', 'Rehearse0022 Widgets news', '2026-W46')", 'dedup-null-theme')}
{_expect_error('check_violation', "insert into public.sweep_query (kind, template, iso_week) values ('trending', 'x', '2026-W46')", 'kind')}
{_expect_error('check_violation', "insert into public.sweep_query (kind, template, iso_week) values ('gap', 'x', '2026-46')", 'iso_week')}
{_expect_error('check_violation', "insert into public.sweep_query (kind, template, iso_week, items_written) values ('gap', 'y', '2026-W46', -1)", 'counter')}
  {ok_note}
end"""),
        ("anon_refused", "anon", f"""
{_expect_error('insufficient_privilege', "perform 1 from public.entity_alias limit 1", 'select-alias')}
{_expect_error('insufficient_privilege', "insert into public.entity_alias (entity_type, entity_id, alias, source) values ('company', gen_random_uuid(), 'x', 'manual')", 'insert-alias')}
{_expect_error('insufficient_privilege', "perform 1 from public.sweep_query limit 1", 'select-sweep')}
{_expect_error('insufficient_privilege', "insert into public.sweep_query (kind, template, iso_week) values ('gap', 'x', '2026-W46')", 'insert-sweep')}
{_expect_error('insufficient_privilege', "perform public.norm_name('x')", 'exec-norm')}
  {ok_note}"""),
    ]


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


def lens_of_0016(rollback_sql: str) -> str:
    m = re.search(r"(create or replace function mi\.lens_of.*?\$fn\$;\nrevoke all on function mi\.lens_of\(text, text, text\) from public;)",
                  rollback_sql, re.S)
    if not m:
        sys.exit("ROLLBACK block has no lens_of restore")
    return m.group(1)


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
    env = {k: v for k, v in os.environ.items() if k not in PROD_SECRET_KEYS and PROD_REF not in v}
    env.pop("PGOPTIONS", None)
    env.update(PGPASSWORD=twin_password())
    return env


def psql(args: list[str], stdin: str | None = None, check: bool = True,
         stop_on_error: bool = True) -> subprocess.CompletedProcess:
    refuse_non_twin()
    flags = ["-X"] + (["-v", "ON_ERROR_STOP=1"] if stop_on_error else [])
    p = subprocess.run([PSQL, TWIN_CONN] + flags + args, input=stdin, text=True,
                       capture_output=True, env=child_env())
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


def run_verify(verify_sql: str) -> dict:
    """Run every VERIFY statement WITHOUT stopping on error: a statement that errors simply has no
    row, and a missing row is a failure (fail-closed). Read-only SESSION, not one transaction: inside
    a single transaction the first error would abort every later check."""
    p = psql(["-tA", "-F", "\t"], stdin="set default_transaction_read_only = on;\n" + verify_sql + "\n",
             check=False, stop_on_error=False)
    return dict(line.split("\t", 1) for line in p.stdout.splitlines() if "\t" in line)


def verify(verify_sql: str, expected: list[str], quiet: bool = False) -> tuple[bool, list[str]]:
    got = run_verify(verify_sql)
    if not quiet:
        for n in expected:
            if n.startswith("info_"):
                print(f"  info  {n} = {got.get(n, '<missing>')}")
    gated = [n for n in expected if not n.startswith("info_")]
    failed = [n for n in gated if got.get(n) != "t"]
    print(f"  verify -> {'PASS' if not failed else 'FAIL'} ({len(gated) - len(failed)}/{len(gated)})"
          + (f" :: failed {failed}" if failed else ""))
    return not failed, failed


def negative_control(verify_sql: str, expected: list[str]) -> bool:
    got = run_verify(verify_sql)
    gated = [n for n in expected if not n.startswith("info_")]
    keep = [n for n in gated if n.startswith("keep_")]
    new = [n for n in gated if not n.startswith("keep_")]
    passing_new = [n for n in new if got.get(n) == "t"]
    failing_keep = [n for n in keep if got.get(n) != "t"]
    ok = not passing_new and not failing_keep
    print(f"  {len(new)} 0022 checks on the un-migrated twin: {len(new) - len(passing_new)} fail (must be all)"
          + (f" :: PASSING WITHOUT THE FIX {passing_new}" if passing_new else ""))
    print(f"  {len(keep)} keep_ checks: {len(keep) - len(failing_keep)} pass (must be all)"
          + (f" :: failing {failing_keep}" if failing_keep else ""))
    return ok


def behaviour() -> bool:
    all_ok = True
    for name, role, body in behaviour_cases():
        do = body if body.lstrip().startswith("declare") else f"begin\n{body}\nend"
        sql = f"begin;\nset local role {role};\ndo $b$\n{do}\n$b$;\nrollback;\n"
        p = psql([], stdin=sql, check=False)
        ok = p.returncode == 0 and "PASS" in p.stderr
        all_ok &= ok
        msg = "" if ok else " :: " + next((l for l in p.stderr.splitlines() if "ERROR" in l), p.stderr.strip()[-200:])
        print(f"  {'PASS' if ok else 'FAIL'} {name} (as {role}){msg}")
    return all_ok


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


# ----------------------------------------------------------------------------- plan
def plan(src: str, verify_sql: str, rollback_sql: str) -> None:
    sha = hashlib.sha256(src.encode()).hexdigest()[:16]
    names = verify_names(verify_sql)
    print("rehearse_0022 — DRY RUN (no connection made)\n")
    print(f"  target           twin {TWIN_REF} via {TWIN_HOST} as {TWIN_USER} (hard-coded; prod refused)")
    print(f"  migration        {os.path.relpath(MIGRATION, REPO)}  sha256:{sha}…  {len(src.splitlines())} lines")
    print(f"  verify checks    {len(names)}: {', '.join(names)}")
    print(f"  rollback stmts   {len([l for l in rollback_sql.splitlines() if l.strip()])} lines")
    print(f"  behaviour cases  {', '.join(n for n, _, _ in behaviour_cases())}")
    print("  planted faults   " + "; ".join(f"{s} -> must fail {n}" for s, _, n in FAULTS))
    print("\n  steps: 0 preflight · 0b fixtures · 1 snapshot A · 1b negative control · 2 apply · 3 re-apply no-op · "
          "4 verify · 4b behaviour · 5 planted faults + restore · 6 rollback · 7 snapshot C == A · 8 cleanup")
    print("\n  run with --execute to perform it (twin only).")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Rehearse migration 0022 on the twin.")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only (default)")
    ap.add_argument("--execute", action="store_true", help="run the full gate against the twin")
    ap.add_argument("--preflight-only", action="store_true", help="connect, run preflight, stop")
    ap.add_argument("--leave-applied", action="store_true", help="end in the 0022 state (with --execute)")
    ap.add_argument("--reset-first", action="store_true",
                    help="run the ROLLBACK block and delete fixtures before preflight (after an interrupted run)")
    a = ap.parse_args()

    src = read_migration()
    verify_sql = commented_block(src, "VERIFY")
    rollback_sql = commented_block(src, "ROLLBACK")
    expected = verify_names(verify_sql)
    if not expected:
        sys.exit("VERIFY block parsed to zero checks")
    faults = [(s, sql if sql else lens_of_0016(rollback_sql), n) for s, sql, n in FAULTS]
    missing = [n for _, _, n in faults if n not in expected]
    if missing:
        sys.exit(f"planted faults name checks that VERIFY lacks: {missing}")

    if not (a.execute or a.preflight_only) or a.dry_run:
        plan(src, verify_sql, rollback_sql)
        return 0

    refuse_non_twin()
    print(f"TARGET twin: {TWIN_HOST} as {TWIN_USER}  at "
          f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"migration sha256: {hashlib.sha256(src.encode()).hexdigest()}")
    if a.reset_first:
        print("\n[-] reset: ROLLBACK block + fixture cleanup")
        run_sql(rollback_sql, "rollback (reset; errors tolerated if 0022 was not applied)")
        run_sql(FIXTURE_CLEANUP_SQL, "fixture cleanup")

    print("\n[0] preflight")
    print(f"  twin server_version={psql(['-tA', '-c', 'show server_version']).stdout.strip()} (prod 17.6)")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:28s} {v}")
    if [k for k in REQUIRED if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin lacks prerequisites: {[k for k in REQUIRED if pf.get(k) != 'true']}")
    if [k for k in CLEAN if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin already has 0022 objects {[k for k in CLEAN if pf.get(k) != 'true']}; "
                 "re-run with --reset-first")
    if pf.get("info.use_count_nonzero") != "0":
        sys.exit("PREFLIGHT FAIL — twin has non-zero use_count/last_used_at before 0022 (prod: 0 everywhere)")
    coll = kv(COLLISION_SQL)
    print(f"  norm_name collisions on the twin: company={coll.get('collisions.company', '0')} "
          f"topic={coll.get('collisions.topic', '0')} (prod probe 2026-11-11: 0 / 0)")
    if coll:
        sys.exit("PREFLIGHT FAIL — the unique name_norm indexes would fail on the twin's data")
    base_usage = pf.get("info.claim_usage_rows")
    if a.preflight_only:
        return 0

    print("\n[0b] fixtures: 3 claim_usage rows (2 claims; one used by 2 documents)")
    if not run_sql(FIXTURE_SQL, "fixture insert"):
        sys.exit("GATE FAIL at 0b")
    n_now = kv("select 'n', count(*)::text from public.claim_usage;")["n"]
    print(f"  claim_usage rows now {n_now} (was {base_usage})")

    print("\n[1] snapshot A (before)")
    snap_a = kv(SNAPSHOT_SQL)
    print(f"  lanes: {snap_a.get('data.lane_registry_lanes')}; use_count sum={snap_a.get('data.claim_use_count_sum')}")

    print("\n[1b] negative control — 0022's checks must FAIL before the fix; keep_* must pass")
    if not negative_control(verify_sql, expected):
        sys.exit("GATE FAIL at 1b — a check passes without the fix (or a keep_ check is already red)")

    print("\n[2] apply 0022")
    if not apply("0022_graph_phase1_shared.sql"):
        sys.exit("GATE FAIL at step 2")

    print("\n[3] re-apply 0022 (must be a clean no-op)")
    new_counts = ("select 'count.entity_alias', count(*)::text from public.entity_alias;\n"
                  "select 'count.sweep_query', count(*)::text from public.sweep_query;")
    snap_b1 = {**kv(SNAPSHOT_SQL), **kv(new_counts)}
    if not apply("0022 second paste"):
        sys.exit("GATE FAIL at step 3 — 0022 is not re-runnable")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(new_counts)})
    if d:
        sys.exit(f"GATE FAIL at step 3 — second paste changed state: {d}")
    print("  OK  state identical after second paste")

    print("\n[4] verify")
    if not verify(verify_sql, expected)[0]:
        sys.exit("GATE FAIL at step 4")

    print("\n[4b] behaviour (twin only; every case rolled back)")
    if not behaviour():
        sys.exit("GATE FAIL at step 4b")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(new_counts)})
    if d:
        sys.exit(f"GATE FAIL at step 4b — a behaviour case leaked state: {d}")
    print("  OK  no state leaked from the behaviour cases")

    print("\n[5] planted faults — verify must catch each, re-apply must restore")
    for step, fault_sql, must_fail in faults:
        print(f"  [{step}] plant -> expect {must_fail}")
        psql([], stdin=fault_sql)
        ok, failed = verify(verify_sql, expected, quiet=True)
        if ok or must_fail not in failed:
            sys.exit(f"GATE FAIL at step {step} — verify did not flag {must_fail}; the gate is not a gate")
        print(f"  OK  fault caught by {must_fail}")
        if not apply(f"0022 restore after {step}") or not verify(verify_sql, expected, quiet=True)[0]:
            sys.exit(f"GATE FAIL at step {step} — re-apply did not restore a passing state")

    print("\n[6] rollback")
    if not run_sql(rollback_sql, "ROLLBACK block"):
        sys.exit("GATE FAIL at step 6")

    print("\n[7] snapshot C must equal snapshot A")
    d = diff(snap_a, kv(SNAPSHOT_SQL))
    if d:
        for k, (x, y) in d.items():
            print(f"  DIFF {k}: before={x} after={y}")
        sys.exit("GATE FAIL at step 7 — rollback is NOT proven")
    print(f"  OK  schema fingerprint ({len([k for k in snap_a if not k.startswith(('count.', 'data.'))])} parts, "
          f"lens_of body included) + {len([k for k in snap_a if k.startswith(('count.', 'data.'))])} data values identical"
          " — ROLLBACK PROVEN")

    print("\n[8] cleanup fixtures")
    if not run_sql(FIXTURE_CLEANUP_SQL, "fixture delete"):
        sys.exit("GATE FAIL at step 8")
    after = kv("select 'n', count(*)::text from public.claim_usage;\n"
               "select 'nz', count(*)::text from public.claim where use_count <> 0 or last_used_at is not null;")
    if after.get("n") != base_usage or after.get("nz") != "0":
        sys.exit(f"GATE FAIL at step 8 — twin not back to preflight: {after}")
    print(f"  OK  claim_usage rows {after['n']} (preflight {base_usage}); use_count non-zero rows 0")

    if a.leave_applied:
        print("\n[9] re-apply for development (--leave-applied)")
        if not apply("0022") or not verify(verify_sql, expected)[0]:
            sys.exit("re-apply verify failed")

    print("\n0022 REHEARSAL: GREEN — safe for Alex to paste 0022 into prod (The-Prod-Brain), then run the "
          "VERIFY block there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
