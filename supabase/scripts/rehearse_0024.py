#!/usr/bin/env python3
"""
rehearse_0024.py — prove migration 0024 (the three live claim readers — match_claims_hybrid,
entity_neighborhood, mi.fact — move onto public.claim_current; claim_current gains is_retired; EXECUTE
on both functions narrowed to service_role; YED-428, ADR-15 decisions 7/8/11) on the Phantom-Test-Case
twin before Alex pastes it into prod (CLAUDE.md invariant 2).
Shape: rehearse_0023.py (twin-only constants and refusal logic byte-identical, scrubbed child env,
PREFLIGHT/VERIFY/ROLLBACK parsed from the migration itself so the bytes Alex pastes are the bytes proven
here, negative control, planted faults, rollback must restore snapshot A exactly).

Gates (all must pass, in order):
  0  preflight     twin reachable; 0023 present (claim_current, claim.rank, claim_verification); 0024
                   absent (old 8-arg match_claims_hybrid only, no is_retired) else --reset-first; the
                   migration's own PREFLIGHT block reads true on its three gating rows and its baseline_*
                   counts equal the harness's; the committed dashboard files equal what this script
                   generates (else --emit-dashboard)
  1  snapshot A    schema fingerprint (public, mi, topic_intelligence) + reader fingerprint (the readers'
                   arguments, return type, ACL, proconfig, body; claim_current / mi.fact / fact_company /
                   fact_topic definition, reloptions, ACL, columns, comment) + counts + READER RESULTS
                   (match_claims_hybrid x6 call shapes and entity_neighborhood x5 seeds as service_role,
                   their old output columns only; mi.fact / fact_company / fact_topic row hashes as
                   postgres, the mi_slice definer)
  1b negative      VERIFY on the 0023-only twin: every gated non-keep_ row must NOT be t, every keep_ row
                   must be t (fail-closed: an error is never a pass)
  2  apply 0024
  3  re-apply      second paste is a clean no-op (fingerprint + reader results + function/view OIDs)
  4  verify        every VERIFY row t; dashboard UNION ALL form 'true' on every gated row; VERIFY info_*
                   rows equal the PREFLIGHT baseline_* rows
  4b behaviour     (i) reader results identical to snapshot A at apply (old call shapes incl. the 8
                   named-arg and 8 positional-arg calls); (ii) twin-only cases, each rolled back:
                   deprecated / contradicted / expired retire a claim from all five read surfaces, a later
                   'confirmed' restores it, disputed + overdue pass through flagged, filter_visibility,
                   rejected stays controlled by filter_statuses, anon / authenticated refused
  5  planted       each fault alone; VERIFY must fail on the NAMED row; re-apply restores all-t
     faults
  6  rollback      the ROLLBACK block, verbatim
  7  snapshot C    must EQUAL snapshot A (the 0023-applied state): ROLLBACK PROVEN only if so
  8  cleanup       no rehearsal rows left; twin back to its preflight counts and the 0023 reader shape
  9  (optional)    --leave-applied re-applies 0024 + verify

HARD REFUSAL: only ever connects to the twin's session pooler as the twin's tenant user with the
twin's password. Host and user are constants, checked before every connection. Child processes get
an environment scrubbed of every variable that names or holds prod material. No override flag.
The password is read from .env and never printed.

Usage:
  python supabase/scripts/rehearse_0024.py                      # dry run, no connection
  python supabase/scripts/rehearse_0024.py --emit-dashboard     # (re)write the two runbook SQL files
  python supabase/scripts/rehearse_0024.py --preflight-only
  python supabase/scripts/rehearse_0024.py --execute            # full gate, ends rolled back (0023 state)
  python supabase/scripts/rehearse_0024.py --execute --reset-first   # after an interrupted run
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

MIGRATION = os.path.join(SUPA, "migrations", "0024_readers_on_claim_current.sql")
DASH_PREFLIGHT = os.path.join(HERE, "0024_preflight_dashboard.sql")
DASH_VERIFY = os.path.join(HERE, "0024_verify_dashboard.sql")
REHEARSAL_SOURCE_KEY = "rehearse_0024"     # every claim a behaviour case inserts carries this (cleanup key)
TOKEN = "zqxrehearsetok"                   # keyword no real claim carries: the behaviour claims' match_claims_hybrid hook

MCH8 = "public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])"
MCH9 = "public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])"
EN = "public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)"
READER_VIEWS = ("public.claim_current", "mi.fact", "mi.fact_company", "mi.fact_topic")

SCHEMAS = "('public','mi','topic_intelligence')"
COUNT_TABLES = ["public.company", "public.topic", "public.person", "public.event", "public.claim",
                "public.claim_usage", "public.claim_relation", "public.claim_entity", "public.documents",
                "public.entity_alias", "public.sweep_query", "public.lane_registry",
                "public.claim_verification", "public.claim_label", "public.judge_audit"]

# Broad schema fingerprint: the rehearse_0023 shape (function ACL/config/BODY, view definitions, relation
# ACL + reloptions) plus comments on the reader objects.
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
         coalesce(c.relacl::text,'')||':'||coalesce(array_to_string(c.reloptions, ','),''), '|' order by n.nspname, c.relname), ''))
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
 where n.nspname in {SCHEMAS} and c.relkind in ('r','v','m','p','i');
select 'policies', md5(coalesce(string_agg(schemaname||'.'||tablename||'.'||policyname, '|' order by 1), ''))
  from pg_policies where schemaname in {SCHEMAS};
select 'views', md5(coalesce(string_agg(schemaname||'.'||viewname||':'||md5(definition), '|' order by schemaname, viewname), ''))
  from pg_views where schemaname in {SCHEMAS};
select 'data.claim_by_status', coalesce(string_agg(status||'='||n, ',' order by status), '')
  from (select status, count(*) n from public.claim group by status) s;
select 'data.claim_by_rank', coalesce(string_agg(rank||'='||n, ',' order by rank), '')
  from (select rank, count(*) n from public.claim group by rank) s;
select 'data.claim_rehearsal_rows', count(*)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';
""" + "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in COUNT_TABLES)

# Targeted, readable fingerprint of the objects 0024 touches. Keyed by signature, so the 8-arg and 9-arg
# match_claims_hybrid are different keys (A vs C proves the 8-arg one is back and the 9-arg one gone).
_views = ",".join(f"'{v}'::regclass" for v in READER_VIEWS)
READER_FP_SQL = f"""
select 'fp.fn.'||p.oid::regprocedure::text,
       'acl='||coalesce(p.proacl::text,'NULL')||' secdef='||p.prosecdef::text||' vol='||p.provolatile::text||
       ' cfg='||coalesce(array_to_string(p.proconfig, ','),'')||' args='||md5(pg_get_function_arguments(p.oid))||
       ' result='||md5(pg_get_function_result(p.oid))||' body='||md5(p.prosrc)||
       ' comment='||md5(coalesce(obj_description(p.oid, 'pg_proc'), ''))
  from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname in ('match_claims_hybrid', 'entity_neighborhood');
select 'fp.fn_signatures', string_agg(p.oid::regprocedure::text, ' ; ' order by p.oid::regprocedure::text)
  from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname in ('match_claims_hybrid', 'entity_neighborhood');
select 'fp.view.'||c.oid::regclass::text,
       'opts='||coalesce(array_to_string(c.reloptions, ','),'')||' acl='||coalesce(c.relacl::text,'NULL')||
       ' def='||md5(pg_get_viewdef(c.oid))||
       ' cols='||md5((select string_agg(attname||':'||format_type(atttypid, atttypmod), ',' order by attnum)
                        from pg_attribute where attrelid = c.oid and attnum > 0 and not attisdropped))||
       ' comment='||md5(coalesce(obj_description(c.oid, 'pg_class'), ''))
  from pg_class c where c.oid in ({_views});
select 'fp.claim_current_tail_cols', (select string_agg(column_name, ',' order by ordinal_position)
  from information_schema.columns where table_schema = 'public' and table_name = 'claim_current'
   and ordinal_position > (select count(*) from information_schema.columns where table_schema = 'public' and table_name = 'claim'));
"""
# OIDs: only compared across the re-apply (step 3). A rollback recreates match_claims_hybrid and
# claim_current, so their OIDs legitimately differ between A and C.
OID_SQL = f"""
select 'oid.'||p.oid::regprocedure::text, p.oid::text
  from pg_proc p where p.pronamespace = 'public'::regnamespace and p.proname in ('match_claims_hybrid', 'entity_neighborhood');
select 'oid.'||c.oid::regclass::text, c.oid::text from pg_class c where c.oid in ({_views});
"""

# ---- reader results. Old output columns only, so the 0023 readers and the 0024 readers are comparable.
QE = "(select embedding from public.claim where embedding is not null order by id limit 1)"
SEED = "(select entity_id from public.claim_entity group by entity_id order by count(*) desc, entity_id offset {} limit 1)"
EV_SEED = "(select entity_id from public.event_entity group by entity_id order by count(*) desc, entity_id limit 1)"
TOP_TIER = "(select array[provenance_tier] from public.claim group by provenance_tier order by count(*) desc, provenance_tier limit 1)"
MCH_OLD_COLS = ("r.id, r.claim_text, r.claim_type, r.quote, r.locator, r.provenance_tier, r.confidence, r.status, "
                "r.metadata, r.document_id, r.event_id, r.asserted_at, r.dense_rank, r.keyword_rank, r.rrf_score")
MCH_CALLS = {
    "named8": f"public.match_claims_hybrid(query_embedding => {QE}, query_text => 'agents', match_count => 20, candidate_n => 40, "
              "rrf_k => 60, filter_entity_ids => null::uuid[], filter_statuses => array['approved','candidate'], filter_tiers => null::text[])",
    "positional8": f"public.match_claims_hybrid({QE}, 'agents', 20, 40, 60, null::uuid[], array['approved','candidate'], null::text[])",
    "retrieve_py": f"public.match_claims_hybrid(query_embedding => {QE}, query_text => 'AI agents sales', match_count => 30, "
                   "filter_entity_ids => null::uuid[])",
    "entity_filter": f"public.match_claims_hybrid(query_embedding => {QE}, query_text => 'pricing', match_count => 100, candidate_n => 200, "
                     f"filter_entity_ids => array[{SEED.format(0)}, {SEED.format(1)}, {SEED.format(2)}])",
    "approved_tier": f"public.match_claims_hybrid(query_embedding => {QE}, query_text => 'funding', match_count => 50, "
                     f"filter_statuses => array['approved'], filter_tiers => {TOP_TIER})",
    "wide": f"public.match_claims_hybrid(query_embedding => {QE}, query_text => 'company', match_count => 2000, candidate_n => 1000)",
}
EN_CALLS = {
    "seed0": f"public.entity_neighborhood(array[{SEED.format(0)}])",
    "seed1": f"public.entity_neighborhood(array[{SEED.format(1)}])",
    "seed2": f"public.entity_neighborhood(array[{SEED.format(2)}])",
    "seed0_all": f"public.entity_neighborhood(array[{SEED.format(0)}], max_events => 100000, max_claims => 100000, max_docs => 100000)",
    "event_seed": f"public.entity_neighborhood(array[{EV_SEED}])",
}
_EN_NEW_KEYS = "array['review_flag','last_check_outcome','is_overdue','visibility']"
# match_claims_hybrid's ORDER BY (rrf_score desc, asserted_at desc nulls last) leaves exact ties in an unspecified
# order, and a new plan may reorder them (seen on the twin: 'wide', 6 of 1156 rows, all exact ties). res.mch.*
# therefore hashes every row and every value in the order the contract defines, ties broken by id; ord.mch.* is
# the raw returned order, printed when it moves, never gating.
MCH_CANON = "r.rrf_score desc, r.asserted_at desc nulls last, r.id"
READER_SQL = ("begin;\nset local role service_role;\n"
              + "\n".join(f"select 'res.mch.{k}', count(*)::text||' rows:'||md5(coalesce(string_agg(row({MCH_OLD_COLS})::text, "
                          f"E'\\n' order by {MCH_CANON}), '')) from {call} with ordinality as r;\n"
                          f"select 'ord.mch.{k}', md5(coalesce(string_agg(r.id::text, ',' order by r.ordinality), '')) "
                          f"from {call} with ordinality as r;" for k, call in MCH_CALLS.items())
              + "\n"
              + "\n".join(f"select 'res.en.{k}', jsonb_array_length(j->'claims')::text||'c/'||jsonb_array_length(j->'events')::text||'e/'||"
                          f"jsonb_array_length(j->'documents')::text||'d:'||md5(jsonb_build_array(j->'events', j->'edges', j->'documents', "
                          f"j->'hiring', (select coalesce(jsonb_agg(c - {_EN_NEW_KEYS} order by o), '[]'::jsonb) "
                          f"from jsonb_array_elements(j->'claims') with ordinality t(c, o)))::text) from (select {call} j) s;"
                          for k, call in EN_CALLS.items())
              + "\nrollback;\n"
              # mi views: read as postgres, the owner and the definer of mi_slice (service_role has no USAGE on mi)
              + "begin;\n"
              "select 'res.mi.fact_by_type', string_agg(fact_type||'='||n, ',' order by fact_type) "
              "from (select fact_type, count(*) n from mi.fact group by 1) s;\n"
              + "\n".join(f"select 'res.{v}', count(*)::text||' rows:'||md5(coalesce(string_agg(f::text, E'\\n' order by f::text), '')) "
                          f"from {v} f;" for v in ("mi.fact", "mi.fact_company", "mi.fact_topic"))
              + "\nrollback;\n")

PREFLIGHT_SQL = f"""
select 'has.claim_current', (to_regclass('public.claim_current') is not null)::text;
select 'has.claim_rank', exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name = 'rank')::text;
select 'has.claim_verification', (to_regclass('public.claim_verification') is not null)::text;
select 'has.mi_views', (to_regclass('mi.fact') is not null and to_regclass('mi.fact_company') is not null and to_regclass('mi.fact_topic') is not null)::text;
select 'has.roles', (count(*) = 3)::text from pg_roles where rolname in ('service_role','anon','authenticated');
select 'has.claims', (count(*) >= 3)::text from public.claim;
select 'has.embeddings', (count(*) >= 1)::text from public.claim where embedding is not null;
select 'has.topic_and_company_links', (count(distinct entity_type) = 2)::text from public.claim_entity where entity_type in ('topic', 'company');
select 'clean.no_is_retired', (not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim_current' and column_name = 'is_retired'))::text;
select 'clean.old_mch_only', (to_regprocedure('{MCH8}') is not null and to_regprocedure('{MCH9}') is null)::text;
select 'clean.en_reads_claim', (select prosrc ~ 'from public\\.claim c' from pg_proc where oid = to_regprocedure('{EN}'))::text;
select 'clean.no_rehearsal_rows', (count(*) = 0)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';
select 'info.claim_rows', count(*)::text from public.claim;
select 'info.mi_fact_claim_rows', count(*)::text from mi.fact where fact_type = 'claim';
select 'info.mi_fact_rows', count(*)::text from mi.fact;
select 'info.live_claims', count(*)::text from public.claim where status in ('approved', 'candidate');
select 'info.embedded_claims', count(*)::text from public.claim where embedding is not null;
"""
REQUIRED = ["has.claim_current", "has.claim_rank", "has.claim_verification", "has.mi_views", "has.roles", "has.claims",
            "has.embeddings", "has.topic_and_company_links"]
CLEAN = ["clean.no_is_retired", "clean.old_mch_only", "clean.en_reads_claim", "clean.no_rehearsal_rows"]
PREFLIGHT_GATING = ("prereq_0023", "old_match_claims_shape", "nothing_retired_yet")
# (PREFLIGHT baseline row, harness preflight count, VERIFY info row that must equal it after the paste)
BASELINES = (("baseline_mi_fact_claim_rows", "info.mi_fact_claim_rows", "info_mi_fact_claim_rows"),
             ("baseline_mi_fact_rows", "info.mi_fact_rows", "info_mi_fact_rows"),
             ("baseline_live_claims", "info.live_claims", "info_live_claims"))

CLEANUP_SQL = f"delete from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';"


# ----------------------------------------------------------------------------- behaviour cases
def _expect_error(sqlstate_name: str, stmt: str, label: str) -> str:
    return f"""  begin
    {stmt};
    raise exception 'FAIL[{label}]: statement was allowed';
  exception when {sqlstate_name} then null;
  end;"""


SETUP = """  select embedding into qe from public.claim where embedding is not null order by id limit 1;
  select entity_id into tid from public.claim_entity where entity_type = 'topic' group by 1 order by count(*) desc, 1 limit 1;
  select entity_id into coid from public.claim_entity where entity_type = 'company' group by 1 order by count(*) desc, 1 limit 1;"""
DECL = ("declare cid uuid; c2 uuid; qe vector; tid uuid; coid uuid; v_m bool; v_e bool; v_f bool; v_t bool; v_c bool; "
        "s text; j jsonb;")


def _new_claim(var: str, key: str, status: str = "candidate") -> str:
    """A rehearsal claim linked to the twin's busiest topic and company, so it reaches all five surfaces."""
    return (f"  insert into public.claim (source_key, claim_key, claim_text, status, asserted_at) values "
            f"('{REHEARSAL_SOURCE_KEY}', 'rehearse_0024_{key}', 'rehearse_0024 {TOKEN} {key}', '{status}', now()) returning id into {var};\n"
            f"  insert into public.claim_entity (claim_id, entity_type, entity_id) values ({var}, 'topic', tid), ({var}, 'company', coid);")


def _mch(extra: str = "") -> str:
    return (f"public.match_claims_hybrid(query_embedding => qe, query_text => '{TOKEN}', match_count => 500, "
            f"candidate_n => 20{extra})")


EN_CALL = "public.entity_neighborhood(array[tid], max_events => 100000, max_claims => 100000, max_docs => 100000)"


def _seen(cid: str, label: str, m: bool, e: bool | None = None, f: bool | None = None, mch_extra: str = "") -> str:
    """Assert where claim `cid` is visible. m = match_claims_hybrid (as service_role), e = entity_neighborhood
    (as service_role), f = mi.fact and both dependents (as postgres, the mi_slice definer). Default: all equal m."""
    e = m if e is None else e
    f = m if f is None else f
    b = lambda x: "true" if x else "false"   # noqa: E731
    return f"""  select exists (select 1 from {_mch(mch_extra)} x where x.id = {cid}),
         exists (select 1 from jsonb_array_elements({EN_CALL} -> 'claims') x where (x->>'id')::uuid = {cid})
    into v_m, v_e;
  set local role postgres;
  select exists (select 1 from mi.fact where fact_type = 'claim' and fact_id = {cid}),
         exists (select 1 from mi.fact_topic where fact_type = 'claim' and fact_id = {cid}),
         exists (select 1 from mi.fact_company where fact_type = 'claim' and fact_id = {cid})
    into v_f, v_t, v_c;
  set local role service_role;
  if current_user <> 'service_role' then raise exception 'FAIL[{label}]: role switch back failed (%)', current_user; end if;
  if not (v_m = {b(m)} and v_e = {b(e)} and v_f = {b(f)} and v_t = {b(f)} and v_c = {b(f)}) then
    raise exception 'FAIL[{label}]: want mch={b(m)} en={b(e)} mi={b(f)}; got mch=% en=% fact=% fact_topic=% fact_company=%',
      v_m, v_e, v_f, v_t, v_c;
  end if;"""


def _col(cid: str, col: str, want: str, label: str, mch_extra: str = "") -> str:
    """The new output column `col` arrives with value `want` (SQL literal) from BOTH functions."""
    return f"""  select x.{col}::text into s from {_mch(mch_extra)} x where x.id = {cid};
  if s is distinct from ({want})::text then raise exception 'FAIL[{label}]: match_claims_hybrid.{col} = %', s; end if;
  select x->>'{col}' into s from jsonb_array_elements({EN_CALL} -> 'claims') x where (x->>'id')::uuid = {cid};
  if s is distinct from ({want})::text then raise exception 'FAIL[{label}]: entity_neighborhood claim.{col} = %', s; end if;"""


def behaviour_cases() -> list[tuple[str, str, str]]:
    """(name, role, DO-body). Each runs in its own transaction that is rolled back."""
    ok = "raise notice 'PASS';"
    return [
        ("old_call_shapes", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'shape')}
  perform count(*) from public.match_claims_hybrid(query_embedding => qe, query_text => 'x', match_count => 5, candidate_n => 10, rrf_k => 60,
          filter_entity_ids => null::uuid[], filter_statuses => array['approved','candidate'], filter_tiers => null::text[]);
  perform count(*) from public.match_claims_hybrid(qe, 'x', 5, 10, 60, null::uuid[], array['approved','candidate'], null::text[]);
  perform count(*) from public.match_claims_hybrid(qe, 'x', 5, 10, 60, null::uuid[], array['approved','candidate'], null::text[], null::text[]);
  perform count(*) from public.match_claims_hybrid(query_embedding => qe, query_text => 'x');
  perform public.entity_neighborhood(array[tid]);
  perform public.entity_neighborhood(array[tid], now() - interval '365 days', 10, 10, 10);
{_seen('cid', 'fresh-claim-visible', True)}
{_col('cid', 'review_flag', 'null', 'fresh-flag')}
{_col('cid', 'last_check_outcome', 'null', 'fresh-outcome')}
{_col('cid', 'is_overdue', "'false'", 'fresh-overdue')}
{_col('cid', 'visibility', "'private'", 'fresh-visibility')}
  {ok}
end"""),
        ("retire_deprecated", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'dep')}
{_seen('cid', 'before', True)}
  update public.claim set rank = 'deprecated' where id = cid;
{_seen('cid', 'deprecated', False)}
  update public.claim set rank = 'preferred' where id = cid;
{_seen('cid', 'preferred', True)}
  update public.claim set rank = 'normal' where id = cid;
{_seen('cid', 'normal', True)}
  {ok}
end"""),
        ("retire_contradicted", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'contra')}
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cid, 'contradicted', 'web', now() - interval '1 minute');
{_seen('cid', 'latest-contradicted', False)}
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cid, 'confirmed', 'human', now());
{_seen('cid', 'later-confirmed', True)}
{_col('cid', 'last_check_outcome', "'confirmed'", 'outcome-confirmed')}
  -- an OLDER contradicted row inserted after the confirmation does not retire it: newest checked_at wins
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cid, 'contradicted', 'web', now() - interval '1 day');
{_seen('cid', 'older-contradicted', True)}
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cid, 'unverifiable', 'llm', now() + interval '1 second');
{_seen('cid', 'latest-unverifiable', True)}
{_col('cid', 'last_check_outcome', "'unverifiable'", 'outcome-unverifiable')}
  {ok}
end"""),
        ("retire_expired", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'exp')}
  update public.claim set valid_to = now() - interval '1 second' where id = cid;
{_seen('cid', 'valid_to-past', False)}
  update public.claim set valid_to = now() + interval '1 day' where id = cid;
{_seen('cid', 'valid_to-future', True)}
  update public.claim set valid_from = now() - interval '30 days', valid_to = null where id = cid;
{_seen('cid', 'open-window', True)}
  {ok}
end"""),
        ("disputed_flagged", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'disp')}
  update public.claim set review_flag = 'disputed' where id = cid;
{_seen('cid', 'disputed-still-visible', True)}
{_col('cid', 'review_flag', "'disputed'", 'disputed-flag')}
  update public.claim set review_flag = 'needs_review' where id = cid;
{_seen('cid', 'needs_review-still-visible', True)}
{_col('cid', 'review_flag', "'needs_review'", 'needs_review-flag')}
  {ok}
end"""),
        ("overdue_passthrough", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'due')}
  update public.claim set next_check_at = now() - interval '1 hour' where id = cid;
{_seen('cid', 'overdue-still-visible', True)}
{_col('cid', 'is_overdue', "'true'", 'overdue-true')}
  update public.claim set next_check_at = now() + interval '1 hour' where id = cid;
{_col('cid', 'is_overdue', "'false'", 'overdue-false')}
  {ok}
end"""),
        ("filter_visibility", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'priv')}
{_new_claim('c2', 'pub')}
  update public.claim set visibility = 'public_ok' where id = c2;
{_seen('cid', 'public-filter-drops-private', False, e=True, f=True, mch_extra=", filter_visibility => array['public_ok']")}
{_seen('c2', 'public-filter-keeps-public', True, mch_extra=", filter_visibility => array['public_ok']")}
{_seen('cid', 'null-filter-private', True, mch_extra=", filter_visibility => null::text[]")}
{_seen('c2', 'null-filter-public', True, mch_extra=", filter_visibility => null::text[]")}
{_seen('cid', 'default-private', True)}
{_seen('c2', 'default-public', True)}
{_seen('cid', 'private-filter-keeps-private', True, mch_extra=", filter_visibility => array['private']")}
{_seen('c2', 'private-filter-drops-public', False, e=True, f=True, mch_extra=", filter_visibility => array['private']")}
{_col('c2', 'visibility', "'public_ok'", 'visibility-passthrough', mch_extra=", filter_visibility => array['public_ok']")}
  {ok}
end"""),
        ("rejected_by_filter_statuses", "service_role", f"""
{DECL}
begin
{SETUP}
{_new_claim('cid', 'rej', status='rejected')}
{_seen('cid', 'rejected-default', False)}
{_seen('cid', 'rejected-asked-for', True, e=False, f=False, mch_extra=", filter_statuses => array['rejected']")}
  update public.claim set rank = 'deprecated' where id = cid;
{_seen('cid', 'rejected-and-retired', False, mch_extra=", filter_statuses => array['rejected']")}
  update public.claim set rank = 'normal', status = 'approved' where id = cid;
{_seen('cid', 'approved', True)}
{_seen('cid', 'approved-only-filter', True, mch_extra=", filter_statuses => array['approved']")}
{_seen('cid', 'candidate-only-filter', False, e=True, f=True, mch_extra=", filter_statuses => array['candidate']")}
  {ok}
end"""),
    ] + [
        (f"{role}_refused", role, f"""
declare cn text;
begin
{_expect_error('insufficient_privilege', "perform 1 from public.match_claims_hybrid(query_embedding => null::vector, query_text => 'x')", 'exec-mch-named')}
{_expect_error('insufficient_privilege', "perform 1 from public.match_claims_hybrid(null::vector, 'x', 1, 1, 1, null::uuid[], array['approved'], null::text[], null::text[])", 'exec-mch-9')}
{_expect_error('insufficient_privilege', "perform public.entity_neighborhood(array[]::uuid[])", 'exec-en')}
{_expect_error('insufficient_privilege', "perform 1 from public.claim_current limit 1", 'select-claim_current')}
{_expect_error('insufficient_privilege', "perform 1 from mi.fact limit 1", 'select-mi.fact')}
  {ok}
end""") for role in ("anon", "authenticated")
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


def stmt_between(text: str, start: str, end: str, label: str) -> str:
    """The statement in `text` that begins with `start` and ends at the first `end` after it."""
    i = text.find(start)
    k = text.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or k < 0:
        sys.exit(f"cannot locate {label} in the migration (planted faults are built from its own text)")
    return text[i:k + len(end)]


def dashboard_texts(src: str) -> tuple[str, str]:
    pre = commented_block(src, "PREFLIGHT").strip() + "\n"
    head_pre = ("-- 0024 PREFLIGHT for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).\n"
                "-- GENERATED from supabase/migrations/0024_readers_on_claim_current.sql by rehearse_0024.py --emit-dashboard;\n"
                "-- the rehearsal fails if this file drifts. READ-ONLY. APPLY 0023 FIRST, then run this, then 0024.\n"
                "-- Expect: prereq_0023 = true, old_match_claims_shape = true, nothing_retired_yet = true. Note the\n"
                "-- three baseline_* rows: after the paste VERIFY's info_mi_fact_claim_rows, info_mi_fact_rows and\n"
                "-- info_live_claims must equal baseline_mi_fact_claim_rows, baseline_mi_fact_rows, baseline_live_claims.\n"
                "-- Any false: STOP. prereq_0023 false = 0023 is not applied; old_match_claims_shape false = 0024 (or\n"
                "-- part of it) is already there (run 0024_verify_dashboard.sql); nothing_retired_yet false = a writer\n"
                "-- already retired a claim, so the *_at_apply rows will not hold: ask before pasting.\n")
    parts = []
    for line in commented_block(src, "VERIFY").splitlines():
        m = re.match(r"^select '([a-z0-9_]+)', (.*);$", line.strip())
        if m:
            parts.append(f"select '{m.group(1)}' as check_name, ({m.group(2)})::text as ok")
    head_ver = ("-- 0024 VERIFY for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).\n"
                "-- GENERATED from the migration's VERIFY block by rehearse_0024.py --emit-dashboard (drift fails the\n"
                "-- rehearsal). READ-ONLY. Run AFTER the 0024 paste. Expect %d rows; every row NOT starting with info_\n"
                "-- must read true. info_* rows = the preflight baseline_* rows. A false row: re-paste 0024 once (it is\n"
                "-- re-runnable), re-run this; still false = stop and run the ROLLBACK block.\n" % len(parts))
    return head_pre + pre, head_ver + "\nunion all\n".join(parts) + ";\n"


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
    """Every VERIFY statement WITHOUT stopping on error: an erroring statement has no row, and a missing
    row is a failure (fail-closed). Read-only SESSION, not one transaction: inside a single transaction
    the first error would abort every later check."""
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
    print(f"  {len(new)} 0024 checks on the 0023-only twin: {len(new) - len(passing_new)} fail (must be all)"
          + (f" :: PASSING WITHOUT THE FIX {passing_new}" if passing_new else ""))
    print(f"  {len(keep)} keep_ checks: {len(keep) - len(failing_keep)} pass (must be all)"
          + (f" :: failing {failing_keep}" if failing_keep else ""))
    return not passing_new and not failing_keep


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


def gated_diff(a: dict, b: dict) -> dict:
    """diff() minus the info-only ord.* keys, which are printed when they move."""
    d = diff(a, b)
    for k in [k for k in d if k.startswith("ord.")]:
        print(f"  info  {k}: tie order moved (row set and values gated by res.{k[4:]})")
        del d[k]
    return d


def snapshot() -> dict:
    return {**kv(SNAPSHOT_SQL), **kv(READER_FP_SQL), **kv(READER_SQL)}


def print_diff(d: dict) -> None:
    for k, (x, y) in d.items():
        print(f"  DIFF {k}:\n       before={x}\n       after ={y}")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Rehearse migration 0024 on the twin.")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only (default)")
    ap.add_argument("--execute", action="store_true", help="run the full gate against the twin")
    ap.add_argument("--preflight-only", action="store_true", help="connect, run preflight, stop")
    ap.add_argument("--emit-dashboard", action="store_true", help="write the two runbook SQL files and exit")
    ap.add_argument("--leave-applied", action="store_true", help="end in the 0024 state (with --execute)")
    ap.add_argument("--reset-first", action="store_true",
                    help="run the ROLLBACK block and delete rehearsal rows before preflight (after an interrupted run)")
    a = ap.parse_args()

    src = read_migration()
    verify_sql = commented_block(src, "VERIFY")
    rollback_sql = commented_block(src, "ROLLBACK")
    preflight_block = commented_block(src, "PREFLIGHT")
    expected = verify_names(verify_sql)
    dash_pre, dash_ver = dashboard_texts(src)
    if a.emit_dashboard:
        for path, text in ((DASH_PREFLIGHT, dash_pre), (DASH_VERIFY, dash_ver)):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"wrote {os.path.relpath(path, REPO)}")
        return 0

    # Planted faults, built from the migration's own text (the pre-0024 bodies are its ROLLBACK block).
    old_mch = stmt_between(rollback_sql, "create or replace function public.match_claims_hybrid", "$function$;", "old match_claims_hybrid")
    old_en = stmt_between(rollback_sql, "create or replace function public.entity_neighborhood", "$function$;", "old entity_neighborhood")
    old_fact = stmt_between(rollback_sql, "create or replace view mi.fact", "WHERE c.status <> 'rejected'::text;", "old mi.fact")
    new_fact = stmt_between(src, "create or replace view mi.fact", "AND NOT c.is_retired;", "new mi.fact")
    faults = [
        ("5a", "grant execute on function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[], text[]) to anon;",
         "functions_exec_service_role_only"),
        ("5b", old_fact, "mi_fact_reads_claim_current"),
        ("5c", "alter view mi.fact reset (security_invoker);", "keep_mi_fact_invoker"),
        ("5d", old_mch, "match_claims_new_shape_only"),
        ("5e", old_en, "entity_neighborhood_reads_claim_current"),
        ("5f", "grant select on public.claim_current to authenticated;", "keep_claim_current_invoker_no_api"),
        ("5g", "alter function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) security definer;",
         "functions_invoker_search_path"),
        ("5h", "grant execute on function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) to public;",
         "functions_exec_service_role_only"),
        ("5i", new_fact.replace("AND NOT c.is_retired;", "AND NOT c.is_retired AND c.status = 'approved'::text;"),
         "keep_mi_fact_claims_unchanged_at_apply"),
        ("5j", "alter function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[], text[]) reset search_path;",
         "functions_invoker_search_path"),
    ]
    missing = [n for _, _, n in faults if n not in expected]
    if missing:
        sys.exit(f"planted faults name checks that VERIFY lacks: {missing}")

    if not (a.execute or a.preflight_only) or a.dry_run:
        print("rehearse_0024 — DRY RUN (no connection made)\n")
        print(f"  target           twin {TWIN_REF} via {TWIN_HOST} as {TWIN_USER} (hard-coded; prod refused)")
        print(f"  migration        {os.path.relpath(MIGRATION, REPO)}  sha256:{hashlib.sha256(src.encode()).hexdigest()[:16]}…")
        print(f"  verify checks    {len(expected)}: {', '.join(expected)}")
        print(f"  reader results   match_claims_hybrid {', '.join(MCH_CALLS)}; entity_neighborhood {', '.join(EN_CALLS)}; mi.fact/fact_company/fact_topic")
        print(f"  behaviour cases  {', '.join(n for n, _, _ in behaviour_cases())}")
        print("  planted faults   " + "; ".join(f"{s} -> {n}" for s, _, n in faults))
        print("\n  run with --execute to perform it (twin only).")
        return 0

    refuse_non_twin()
    print(f"TARGET twin: {TWIN_HOST} as {TWIN_USER}  at {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"migration sha256: {hashlib.sha256(src.encode()).hexdigest()}")
    if a.reset_first:
        print("\n[-] reset: ROLLBACK block + rehearsal-row cleanup")
        run_sql(rollback_sql, "rollback (reset)")
        run_sql(CLEANUP_SQL, "rehearsal-row cleanup")

    print("\n[0] preflight")
    print(f"  twin server_version={psql(['-tA', '-c', 'show server_version']).stdout.strip()} (prod 17.6)")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:30s} {v}")
    if [k for k in REQUIRED if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin lacks prerequisites: {[k for k in REQUIRED if pf.get(k) != 'true']} "
                 "(0023 missing? run rehearse_0023.py --execute --leave-applied)")
    if [k for k in CLEAN if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin already has 0024 objects {[k for k in CLEAN if pf.get(k) != 'true']}; "
                 "re-run with --reset-first")
    out = psql(["-tA", "-F", "\t"], stdin="set default_transaction_read_only = on;\n" + preflight_block).stdout
    rows = dict(l.split("\t", 1) for l in out.splitlines() if "\t" in l)
    print(f"  migration PREFLIGHT block: {rows}")
    bad = [k for k in PREFLIGHT_GATING if rows.get(k) != "true"]
    if bad or not all(b in rows for b, _, _ in BASELINES):
        sys.exit(f"PREFLIGHT FAIL — the migration's own PREFLIGHT block is not green on the twin: {bad or rows}")
    off = [(b, rows[b], pf.get(h)) for b, h, _ in BASELINES if rows[b] != pf.get(h)]
    if off:
        sys.exit(f"PREFLIGHT FAIL — PREFLIGHT baselines disagree with the harness counts: {off}")
    for path, text in ((DASH_PREFLIGHT, dash_pre), (DASH_VERIFY, dash_ver)):
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if cur != text:
            sys.exit(f"PREFLIGHT FAIL — {os.path.relpath(path, REPO)} drifted from the migration; run --emit-dashboard")
    print("  dashboard runbook files in sync with the migration")
    base_claims = pf.get("info.claim_rows")
    if a.preflight_only:
        return 0

    print("\n[1] snapshot A (before; the 0023-applied state)")
    snap_a = snapshot()
    for k in sorted(snap_a):
        if k.startswith(("fp.", "res.", "ord.")):
            print(f"  {k:62s} {snap_a[k]}")
    empty = [k for k in snap_a if k.startswith("res.") and re.match(r"^0 rows|^0c/0e/0d", snap_a[k])]
    if empty:
        sys.exit(f"GATE FAIL at step 1 — reader probes return nothing, so 'identical at apply' would carry no information: {empty}")
    print(f"  {len([k for k in snap_a if not k.startswith(('count.', 'data.', 'res.', 'ord.', 'fp.'))])} schema parts, "
          f"{len([k for k in snap_a if k.startswith('fp.')])} reader fingerprints, "
          f"{len([k for k in snap_a if k.startswith('res.')])} reader results, "
          f"{len([k for k in snap_a if k.startswith(('count.', 'data.'))])} data values")

    print("\n[1b] negative control — 0024's checks must FAIL before the fix; keep_* must pass")
    if not negative_control(verify_sql, expected):
        sys.exit("GATE FAIL at 1b — a check passes without the fix (or a keep_ check is already red)")

    print("\n[2] apply 0024")
    if not apply("0024_readers_on_claim_current.sql"):
        sys.exit("GATE FAIL at step 2")

    print("\n[3] re-apply 0024 (must be a clean no-op, including function and view OIDs)")
    snap_b1 = snapshot()
    oids_b1 = kv(OID_SQL)
    if not apply("0024 second paste"):
        sys.exit("GATE FAIL at step 3 — 0024 is not re-runnable")
    d = gated_diff({**snap_b1, **oids_b1}, {**snapshot(), **kv(OID_SQL)})
    if d:
        print_diff(d)
        sys.exit("GATE FAIL at step 3 — second paste changed state")
    print(f"  OK  state identical after second paste ({len(oids_b1)} OIDs unchanged: the function swap did not re-fire)")

    print("\n[4] verify")
    if not verify(verify_sql, expected)[0]:
        sys.exit("GATE FAIL at step 4")
    got = run_verify(verify_sql)
    off = [(b, rows[b], i, got.get(i)) for b, _, i in BASELINES if got.get(i) != rows[b]]
    if off:
        sys.exit(f"GATE FAIL at step 4 — VERIFY info rows differ from the PREFLIGHT baselines: {off}")
    print("  info_* rows equal the PREFLIGHT baseline_* rows: " + ", ".join(f"{i}={got[i]}" for _, _, i in BASELINES))
    dash = psql(["-tA", "-F", "\t"], stdin="set default_transaction_read_only = on;\n" + dash_ver, check=False).stdout
    drows = [l.split("\t") for l in dash.splitlines() if "\t" in l]
    dbad = [n for n, v in drows if not n.startswith("info_") and v != "true"]
    print(f"  dashboard VERIFY: {len(drows)} rows, non-info rows not 'true': {dbad or 'none'}")
    if dbad or len(drows) != len(expected):
        sys.exit("GATE FAIL at step 4 — the dashboard VERIFY form disagrees")

    print("\n[4b] behaviour (twin only; every case rolled back)")
    res_d = gated_diff({k: v for k, v in snap_a.items() if k.startswith(("res.", "ord."))},
                       {k: v for k, v in snap_b1.items() if k.startswith(("res.", "ord."))})
    if res_d:
        print_diff(res_d)
        sys.exit("GATE FAIL at step 4b — reader results changed at apply")
    print(f"  PASS reader results identical to snapshot A at apply "
          f"({len([k for k in snap_a if k.startswith('res.')])} probes; old 8 named-arg and 8 positional-arg calls included)")
    if not behaviour():
        sys.exit("GATE FAIL at step 4b")
    d = gated_diff(snap_b1, snapshot())
    if d:
        print_diff(d)
        sys.exit("GATE FAIL at step 4b — a behaviour case leaked state")
    print("  OK  no state leaked from the behaviour cases")

    print("\n[5] planted faults — verify must catch each, re-apply must restore")
    for step, fault_sql, must_fail in faults:
        print(f"  [{step}] plant -> expect {must_fail}")
        psql([], stdin=fault_sql)
        ok, failed = verify(verify_sql, expected, quiet=True)
        if ok or must_fail not in failed:
            sys.exit(f"GATE FAIL at step {step} — verify did not flag {must_fail}; the gate is not a gate")
        print(f"  OK  fault caught by {must_fail}")
        if not apply(f"0024 restore after {step}") or not verify(verify_sql, expected, quiet=True)[0]:
            sys.exit(f"GATE FAIL at step {step} — re-apply did not restore a passing state")
    d = gated_diff(snap_b1, snapshot())
    if d:
        print_diff(d)
        sys.exit("GATE FAIL at step 5 — the restored state differs from the first apply")
    print("  OK  restored state identical to the first apply")

    print("\n[6] rollback")
    if not run_sql(rollback_sql, "ROLLBACK block"):
        sys.exit("GATE FAIL at step 6")

    print("\n[7] snapshot C must equal snapshot A (the 0023-applied state)")
    d = gated_diff(snap_a, snapshot())
    if d:
        print_diff(d)
        sys.exit("GATE FAIL at step 7 — rollback is NOT proven")
    print(f"  OK  schema fingerprint ({len([k for k in snap_a if not k.startswith(('count.', 'data.', 'res.', 'ord.', 'fp.'))])} parts) + "
          f"{len([k for k in snap_a if k.startswith('fp.')])} reader fingerprints (claim_current definition, ACL, reloptions, "
          f"comment included) + {len([k for k in snap_a if k.startswith('res.')])} reader results + "
          f"{len([k for k in snap_a if k.startswith(('count.', 'data.'))])} data values identical — ROLLBACK PROVEN")

    print("\n[8] cleanup")
    if not run_sql(CLEANUP_SQL, "rehearsal-row delete (expect 0)"):
        sys.exit("GATE FAIL at step 8")
    after = kv(f"select 'n', count(*)::text from public.claim;\n"
               f"select 'r', count(*)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';\n"
               f"select 'shape', (to_regprocedure('{MCH8}') is not null and to_regprocedure('{MCH9}') is null)::text;\n"
               "select 'no_is_retired', (not exists (select 1 from information_schema.columns where table_schema = 'public' "
               "and table_name = 'claim_current' and column_name = 'is_retired'))::text;")
    if after.get("n") != base_claims or after.get("r") != "0" or after.get("shape") != "true" or after.get("no_is_retired") != "true":
        sys.exit(f"GATE FAIL at step 8 — twin not back to preflight: {after}")
    print(f"  OK  claim rows {after['n']} (preflight {base_claims}); rehearsal rows 0; 8-arg match_claims_hybrid only; "
          "claim_current without is_retired")

    if a.leave_applied:
        print("\n[9] re-apply for development (--leave-applied)")
        if not apply("0024") or not verify(verify_sql, expected)[0]:
            sys.exit("re-apply verify failed")

    print("\n0024 REHEARSAL: GREEN — safe for Alex to run supabase/scripts/0024_preflight_dashboard.sql, paste 0024 "
          "into prod (The-Prod-Brain) after 0023, then run supabase/scripts/0024_verify_dashboard.sql there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
