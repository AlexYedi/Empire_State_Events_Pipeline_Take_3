#!/usr/bin/env python3
"""
rehearse_0023.py — prove migration 0023 (intelligence graph v2, L1: claim evidence spans, judge record,
rank / review_flag, validity window, freshness, visibility; claim_verification append-only log;
claim_label; judge_audit; claim_current view; YED-384, ADR-15) on the Phantom-Test-Case twin before
Alex pastes it into prod (CLAUDE.md invariant 2).
Shape: rehearse_0022.py (twin-only constants, scrubbed child env, PREFLIGHT/VERIFY/ROLLBACK parsed from
the migration itself so the bytes Alex pastes are the bytes proven here, negative control, planted
faults, rollback must restore snapshot A exactly).

Gates (all must pass, in order):
  0  preflight     twin reachable; 0022 present (no_contact_pii_v1, entity_alias, sweep_query); no 0023
                   objects (else --reset-first); the migration's own PREFLIGHT block reads true on its
                   three gating rows; the committed dashboard runbook files equal what this script
                   generates from the migration (else --emit-dashboard)
  1  snapshot A    schema fingerprint (public, mi, topic_intelligence; function ACL/config/BODY
                   included) + row counts
  1b negative      VERIFY on the un-migrated twin: every gated non-keep_ check must NOT be t, every
                   keep_ check must be t (fail-closed: an error is never a pass)
  2  apply 0023
  3  re-apply      second paste is a clean no-op (fingerprint + counts identical)
  4  verify        every VERIFY row t; the dashboard UNION ALL form reads 'true' on every gated row
  4b behaviour     twin-only cases, each rolled back, under the named role. A rejected write must be
                   rejected by the NAMED constraint (get stacked diagnostics), never by another error
  5  planted       each fault alone; VERIFY must fail on the NAMED check; re-apply restores all-t
     faults
  6  rollback      the ROLLBACK block, verbatim
  7  snapshot C    must EQUAL snapshot A: ROLLBACK PROVEN only if so
  8  cleanup       no rehearsal rows left; twin back to its preflight counts
  9  (optional)    --leave-applied re-applies 0023 + verify

HARD REFUSAL: only ever connects to the twin's session pooler as the twin's tenant user with the
twin's password. Host and user are constants, checked before every connection. Child processes get
an environment scrubbed of every variable that names or holds prod material. No override flag.
The password is read from .env and never printed.

Usage:
  python supabase/scripts/rehearse_0023.py                      # dry run, no connection
  python supabase/scripts/rehearse_0023.py --emit-dashboard     # (re)write the two runbook SQL files
  python supabase/scripts/rehearse_0023.py --preflight-only
  python supabase/scripts/rehearse_0023.py --execute            # full gate, ends rolled back
  python supabase/scripts/rehearse_0023.py --execute --reset-first   # after an interrupted run
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

MIGRATION = os.path.join(SUPA, "migrations", "0023_graph_v2_l1_freshness.sql")
DASH_PREFLIGHT = os.path.join(HERE, "0023_preflight_dashboard.sql")
DASH_VERIFY = os.path.join(HERE, "0023_verify_dashboard.sql")
REHEARSAL_SOURCE_KEY = "rehearse_0023"     # every claim a behaviour case inserts carries this (cleanup key)

NEW_COLUMNS = ("evidence", "judge_verdict", "judge_model", "judge_prompt_hash", "judged_at", "rank",
               "review_flag", "valid_from", "valid_to", "freshness_class", "freshness_conf",
               "freshness_reason", "next_check_at", "visibility")
NEW_CHECKS = ("claim_evidence_shape", "claim_evidence_no_pii", "claim_judge_verdict_vocab",
              "claim_judge_record_complete", "claim_judge_prompt_hash_hex", "claim_rank_vocab",
              "claim_review_flag_vocab", "claim_valid_window", "claim_freshness_class_vocab",
              "claim_freshness_conf_range", "claim_freshness_reason_no_pii", "claim_visibility_vocab")
NEW_RELATIONS = ("public.claim_verification", "public.claim_label", "public.judge_audit", "public.claim_current")

SCHEMAS = "('public','mi','topic_intelligence')"
COUNT_TABLES = ["public.company", "public.topic", "public.person", "public.event", "public.claim",
                "public.claim_usage", "public.claim_relation", "public.claim_entity", "public.documents",
                "public.entity_alias", "public.sweep_query", "public.lane_registry"]

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
select 'data.claim_rehearsal_rows', count(*)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';
""" + "\n".join(f"select 'count.{t}', count(*)::text from {t};" for t in COUNT_TABLES)
NEW_COUNTS = ("select 'count.claim_verification', count(*)::text from public.claim_verification;\n"
              "select 'count.claim_label', count(*)::text from public.claim_label;\n"
              "select 'count.judge_audit', count(*)::text from public.judge_audit;")

_cols = ",".join(f"'{c}'" for c in NEW_COLUMNS)
_checks = ",".join(f"'{c}'" for c in NEW_CHECKS)
PREFLIGHT_SQL = f"""
select 'has.no_contact_pii_v1', (to_regprocedure('public.no_contact_pii_v1(text)') is not null)::text;
select 'has.entity_alias', (to_regclass('public.entity_alias') is not null)::text;
select 'has.sweep_query', (to_regclass('public.sweep_query') is not null)::text;
select 'has.documents', (to_regclass('public.documents') is not null)::text;
select 'has.roles', (count(*) = 3)::text from pg_roles where rolname in ('service_role','anon','authenticated');
select 'has.claims', (count(*) >= 3)::text from public.claim;
select 'clean.no_new_columns', (count(*) = 0)::text from information_schema.columns
 where table_schema = 'public' and table_name = 'claim' and column_name in ({_cols});
select 'clean.no_new_checks', (count(*) = 0)::text from pg_constraint
 where conrelid = 'public.claim'::regclass and conname in ({_checks});
select 'clean.no_new_relations', ({" and ".join(f"to_regclass('{r}') is null" for r in NEW_RELATIONS)})::text;
select 'clean.no_new_funcs', (count(*) = 0)::text from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public' and p.proname in ('claim_evidence_ok_v1', 'claim_verification_append_only');
select 'clean.no_new_indexes', (count(*) = 0)::text from pg_indexes
 where schemaname = 'public' and indexname in ('claim_next_check_idx', 'claim_review_flag_idx');
select 'clean.no_rehearsal_rows', (count(*) = 0)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';
select 'info.claim_rows', count(*)::text from public.claim;
select 'info.claim_policies', count(*)::text from pg_policies where schemaname = 'public' and tablename = 'claim';
"""
REQUIRED = ["has.no_contact_pii_v1", "has.entity_alias", "has.sweep_query", "has.documents", "has.roles", "has.claims"]
CLEAN = ["clean.no_new_columns", "clean.no_new_checks", "clean.no_new_relations", "clean.no_new_funcs",
         "clean.no_new_indexes", "clean.no_rehearsal_rows"]
PREFLIGHT_GATING = ("prereq_0022", "no_0023_columns", "no_0023_tables")

CLEANUP_SQL = f"delete from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';"
GOOD_HASH = "ab" * 32


# ----------------------------------------------------------------------------- behaviour cases
def _expect_error(sqlstate_name: str, stmt: str, label: str) -> str:
    return f"""  begin
    {stmt};
    raise exception 'FAIL[{label}]: statement was allowed';
  exception when {sqlstate_name} then null;
  end;"""


def _expect_check(stmt: str, constraint: str | tuple[str, ...], label: str) -> str:
    """Rejected as a CHECK violation BY THE NAMED CONSTRAINT (a tuple only where one bad value breaks two
    constraints and Postgres picks which to report). Any other error propagates (FAIL); a check_violation
    from a different constraint is a FAIL too. Needs `cn text` declared."""
    names = (constraint,) if isinstance(constraint, str) else constraint
    allowed = ", ".join(f"'{n}'" for n in names)
    return f"""  begin
    {stmt};
    raise exception 'FAIL[{label}]: statement was allowed';
  exception when check_violation then
    get stacked diagnostics cn = constraint_name;
    if cn is null or cn not in ({allowed}) then
      raise exception 'FAIL[{label}]: rejected by % instead of {"/".join(names)}', cn;
    end if;
  end;"""


def _new_claim(var: str, key: str) -> str:
    return (f"  insert into public.claim (source_key, claim_key, claim_text) values "
            f"('{REHEARSAL_SOURCE_KEY}', 'rehearse_0023_{key}', 'rehearse_0023 {key}') returning id into {var};")


def behaviour_cases() -> list[tuple[str, str, str]]:
    """(name, role, DO-body). Each runs in its own transaction that is rolled back."""
    ok = "raise notice 'PASS';"
    upd = "update public.claim set {} where id = cid"
    span = lambda q: "jsonb_build_array(jsonb_build_object('para_idx', 2, 'quote', " + q + "))"   # noqa: E731
    words = lambda n: f"array_to_string(array_fill('w'::text, array[{n}]), ' ')"               # noqa: E731
    return [
        ("claim_vocab_checks", "service_role", f"""
declare cid uuid; cn text; r record;
begin
  select id into cid from public.claim order by id limit 1;
  select rank, visibility, review_flag into r from public.claim where id = cid;
  if r.rank <> 'normal' or r.visibility <> 'private' or r.review_flag is not null then
    raise exception 'FAIL[defaults]: % % %', r.rank, r.visibility, r.review_flag; end if;
{_expect_check(upd.format("rank = 'top'"), 'claim_rank_vocab', 'rank')}
{_expect_error('not_null_violation', upd.format("rank = null"), 'rank-null')}
{_expect_check(upd.format("review_flag = 'maybe'"), 'claim_review_flag_vocab', 'review_flag')}
{_expect_check(upd.format("visibility = 'public'"), 'claim_visibility_vocab', 'visibility')}
{_expect_error('not_null_violation', upd.format("visibility = null"), 'visibility-null')}
{_expect_check(upd.format("freshness_class = 'stale'"), 'claim_freshness_class_vocab', 'freshness_class')}
{_expect_check(upd.format("freshness_conf = 1.01"), 'claim_freshness_conf_range', 'conf-high')}
{_expect_check(upd.format("freshness_conf = -0.01"), 'claim_freshness_conf_range', 'conf-low')}
{_expect_check(upd.format(f"judge_verdict = 'yes', judge_model = 'm', judge_prompt_hash = '{GOOD_HASH}', judged_at = now()"), 'claim_judge_verdict_vocab', 'judge_verdict')}
  update public.claim set rank = 'preferred', review_flag = 'disputed', visibility = 'public_ok',
         freshness_class = 'fast_moving', freshness_conf = 0, next_check_at = now() + interval '30 days',
         freshness_reason = 'funding rounds go stale within a quarter' where id = cid;
  update public.claim set rank = 'deprecated', review_flag = 'needs_review', freshness_class = 'none_fits', freshness_conf = 1 where id = cid;
  {ok}
end"""),
        ("judge_record", "service_role", f"""
declare cid uuid; cn text;
begin
  select id into cid from public.claim order by id limit 1;
{_expect_check(upd.format("judge_verdict = 'supported'"), 'claim_judge_record_complete', 'verdict-only')}
{_expect_check(upd.format(f"judge_verdict = 'supported', judge_model = 'm', judge_prompt_hash = '{GOOD_HASH}'"), 'claim_judge_record_complete', 'no-judged_at')}
{_expect_check(upd.format("judged_at = now()"), 'claim_judge_record_complete', 'judged_at-only')}
{_expect_check(upd.format(f"judge_verdict = 'supported', judge_model = 'm', judge_prompt_hash = '{GOOD_HASH.upper()}', judged_at = now()"), 'claim_judge_prompt_hash_hex', 'hash-upper')}
{_expect_check(upd.format(f"judge_verdict = 'supported', judge_model = 'm', judge_prompt_hash = '{GOOD_HASH[:63]}', judged_at = now()"), 'claim_judge_prompt_hash_hex', 'hash-63')}
{_expect_check(upd.format("judge_verdict = 'supported', judge_model = 'm', judge_prompt_hash = 'sha256:abc', judged_at = now()"), 'claim_judge_prompt_hash_hex', 'hash-junk')}
  update public.claim set judge_verdict = 'abstain', judge_model = 'claude-sonnet', judge_prompt_hash = '{GOOD_HASH}', judged_at = now() where id = cid;
  update public.claim set judge_verdict = null, judge_model = null, judge_prompt_hash = null, judged_at = null where id = cid;
  {ok}
end"""),
        ("valid_window", "service_role", f"""
declare cid uuid; cn text;
begin
  select id into cid from public.claim order by id limit 1;
{_expect_check(upd.format("valid_from = '2026-06-01', valid_to = '2026-05-31'"), 'claim_valid_window', 'to<from')}
  update public.claim set valid_from = '2026-06-01', valid_to = '2026-06-01' where id = cid;
  update public.claim set valid_from = null, valid_to = '2020-01-01' where id = cid;
  {ok}
end"""),
        ("evidence_shape", "service_role", f"""
declare cid uuid; cn text; got jsonb;
begin
  select id into cid from public.claim order by id limit 1;
  update public.claim set evidence = $j$[{{"para_idx": 3, "quote": "Acme raised a Series B"}}]$j$ where id = cid;
  select evidence into got from public.claim where id = cid;
  if got <> $j$[{{"para_idx": 3, "quote": "Acme raised a Series B"}}]$j$::jsonb then raise exception 'FAIL[1-span readback]: %', got; end if;
  update public.claim set evidence = $j$[{{"para_idx": 0, "quote": "a"}}, {{"para_idx": 12, "quote": "led by Index"}}]$j$ where id = cid;
  update public.claim set evidence = {span(words(25))} where id = cid;
  update public.claim set evidence = $j$[{{"para_idx": 4, "quote": "ARR grew 40% to $12.5M in 2025, from 3 to 118 customers (Q3 2025: 1.2x)"}}]$j$ where id = cid;
  update public.claim set evidence = (select jsonb_agg(jsonb_build_object('para_idx', i, 'quote', 'w')) from generate_series(1, 8) i) where id = cid;
  update public.claim set evidence = null where id = cid;
{_expect_check(upd.format("evidence = " + span(words(26))), 'claim_evidence_shape', '26-words')}
{_expect_check(upd.format("evidence = (select jsonb_agg(jsonb_build_object('para_idx', i, 'quote', 'w')) from generate_series(1, 9) i)"), 'claim_evidence_shape', '9-spans')}
{_expect_check(upd.format("evidence = $j$[{\"para_idx\": 1, \"quote\": \"x\", \"page\": 2}]$j$"), 'claim_evidence_shape', 'extra-key')}
{_expect_check(upd.format("evidence = $j$[\"Acme raised a Series B\"]$j$"), 'claim_evidence_shape', 'non-object-element')}
{_expect_check(upd.format("evidence = $j$[{\"para_idx\": 1, \"quote\": \"x\"}, 7]$j$"), 'claim_evidence_shape', 'mixed-non-object')}
{_expect_check(upd.format("evidence = $j${\"para_idx\": 1, \"quote\": \"x\"}$j$"), 'claim_evidence_shape', 'top-level-object')}
{_expect_check(upd.format("evidence = '[]'"), 'claim_evidence_shape', 'empty-array')}
{_expect_check(upd.format("evidence = $j$[{\"para_idx\": -1, \"quote\": \"x\"}]$j$"), 'claim_evidence_shape', 'negative-idx')}
{_expect_check(upd.format("evidence = $j$[{\"para_idx\": 1, \"quote\": \"   \"}]$j$"), 'claim_evidence_shape', 'blank-quote')}
  {ok}
end"""),
        ("claim_pii", "service_role", f"""
declare cid uuid; cn text;
begin
  select id into cid from public.claim order by id limit 1;
{_expect_check(upd.format("evidence = " + span("'write to jane.doe@example.com for the deck'")), 'claim_evidence_no_pii', 'evidence-email')}
{_expect_check(upd.format("evidence = " + span("'call +44 20 7946 0958 after six'")), 'claim_evidence_no_pii', 'evidence-phone-intl')}
{_expect_check(upd.format("evidence = " + span("'her cell is 555-123-4567'")), 'claim_evidence_no_pii', 'evidence-phone-us')}
{_expect_check(upd.format("freshness_reason = 'confirm with founder@veris.example.com'"), 'claim_freshness_reason_no_pii', 'reason-email')}
{_expect_check(upd.format("freshness_reason = 'ring (212) 555-0199 ext 4'"), 'claim_freshness_reason_no_pii', 'reason-phone')}
  update public.claim set freshness_reason = 'headcount moves monthly; see https://x.com/@acme' where id = cid;
  {ok}
end"""),
        ("claim_verification", "service_role", f"""
declare cnew uuid; cn text; vid uuid; n int;
begin
{_new_claim('cnew', 'cv')}
  insert into public.claim_verification (claim_id, outcome, method, source_url, note, checked_at)
       values (cnew, 'confirmed', 'web', 'https://example.com/press', 'still on the pricing page', now()) returning id into vid;
  insert into public.claim_verification (claim_id, outcome, method) values (cnew, 'unverifiable', 'llm');
  begin
    update public.claim_verification set note = 'edited' where id = vid;
    raise exception 'FAIL[update]: statement was allowed';
  exception when raise_exception then
    if sqlerrm not like 'claim_verification is append-only%' then raise exception 'FAIL[update]: wrong error %', sqlerrm; end if;
  end;
{_expect_check("insert into public.claim_verification (claim_id, outcome, method) values (cnew, 'stale', 'web')", 'claim_verification_outcome_check', 'outcome')}
{_expect_check("insert into public.claim_verification (claim_id, outcome, method) values (cnew, 'confirmed', 'vibes')", 'claim_verification_method_check', 'method')}
{_expect_check("insert into public.claim_verification (claim_id, outcome, method, note) values (cnew, 'confirmed', 'human', 'per jane.doe@example.com')", 'claim_verification_note_no_pii', 'note-email')}
{_expect_check("insert into public.claim_verification (claim_id, outcome, method, note) values (cnew, 'confirmed', 'human', 'called 555-123-4567')", 'claim_verification_note_no_pii', 'note-phone')}
{_expect_check("insert into public.claim_verification (claim_id, outcome, method, source_url) values (cnew, 'confirmed', 'web', 'mailto:jane.doe@example.com')", 'claim_verification_source_url_no_pii', 'url-email')}
{_expect_check("insert into public.claim_verification (claim_id, outcome, method, source_url) values (cnew, 'confirmed', 'web', 'tel:+1 212 555 0199')", 'claim_verification_source_url_no_pii', 'url-phone')}
{_expect_error('foreign_key_violation', "insert into public.claim_verification (claim_id, outcome, method) values (gen_random_uuid(), 'confirmed', 'web')", 'fk')}
  delete from public.claim where id = cnew;
  select count(*) into n from public.claim_verification where claim_id = cnew;
  if n <> 0 then raise exception 'FAIL[cascade]: % rows left', n; end if;
  {ok}
end"""),
        ("claim_label", "service_role", f"""
declare cnew uuid; cn text; n int;
begin
{_new_claim('cnew', 'cl')}
  insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label, useful, note)
       values (cnew, '2026-12-4b', 'multi_span', 0.25, 'supported', 2, 'span 2 carries it');
  insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label) values (cnew, '2027-01-4b', 'rest', 1, 'unsupported');
{_expect_error('unique_violation', "insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label) values (cnew, '2026-12-4b', 'rest', 0.5, 'unsupported')", 'dup-run')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label) values (cnew, 'r0', 'rest', 0, 'supported')", 'claim_label_inclusion_prob_check', 'prob-0')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label) values (cnew, 'r1', 'rest', 1.5, 'supported')", 'claim_label_inclusion_prob_check', 'prob>1')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label) values (cnew, 'r2', 'rest', 0.5, 'maybe')", 'claim_label_label_check', 'label')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label, useful) values (cnew, 'r3', 'rest', 0.5, 'supported', 3)", 'claim_label_useful_check', 'useful')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label, note) values (cnew, 'r4', 'rest', 0.5, 'supported', 'ask jane.doe@example.com')", 'claim_label_note_no_pii', 'note-email')}
{_expect_check("insert into public.claim_label (claim_id, sample_run, stratum, inclusion_prob, label, note) values (cnew, 'r5', 'rest', 0.5, 'supported', 'call +44 20 7946 0958')", 'claim_label_note_no_pii', 'note-phone')}
  delete from public.claim where id = cnew;
  select count(*) into n from public.claim_label where claim_id = cnew;
  if n <> 0 then raise exception 'FAIL[cascade]: % rows left', n; end if;
  {ok}
end"""),
        ("judge_audit", "service_role", f"""
declare cn text; aid uuid;
begin
  insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash)
       values ('2026-12-01', 'a', 40, 37, 0.82, 0.80, true, 'claude-sonnet', '{GOOD_HASH}') returning id into aid;
  insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash, confirms_audit_id)
       values ('2026-12-01', 'a', 40, 30, 0.61, 0.80, false, 'claude-sonnet', '{GOOD_HASH}', aid);
  insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash)
       values ('2026-12-01', 'b', 60, 2, 0.11, 0.15, true, 'claude-sonnet', '{GOOD_HASH}');
  insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash)
       values ('2026-12-01', 'b', 60, 9, 0.24, 0.15, false, 'claude-sonnet', '{GOOD_HASH}');
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 40, 30, 0.61, 0.80, true, 'm', '{GOOD_HASH}')", 'judge_audit_check1', 'a-passed-below')}
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 40, 37, 0.82, 0.80, false, 'm', '{GOOD_HASH}')", 'judge_audit_check1', 'a-failed-above')}
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'b', 60, 9, 0.24, 0.15, true, 'm', '{GOOD_HASH}')", 'judge_audit_check1', 'b-passed-above')}
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 40, 41, 0.9, 0.8, true, 'm', '{GOOD_HASH}')", 'judge_audit_check', 'hits>n')}
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'c', 40, 1, 0.9, 0.8, true, 'm', '{GOOD_HASH}')", ('judge_audit_part_check', 'judge_audit_check1'), 'part')}
{_expect_check(f"insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 0, 0, 0.9, 0.8, true, 'm', '{GOOD_HASH}')", 'judge_audit_n_check', 'n=0')}
{_expect_check("insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 40, 37, 0.82, 0.80, true, 'm', 'nothex')", 'judge_audit_judge_prompt_hash_check', 'hash')}
  {ok}
end"""),
        ("claim_current", "service_role", f"""
declare cnew uuid; r record;
begin
{_new_claim('cnew', 'cc')}
  select * into r from public.claim_current where id = cnew;
  if r.last_check_outcome is not null or not r.is_current or r.is_overdue then raise exception 'FAIL[fresh]: % % %', r.last_check_outcome, r.is_current, r.is_overdue; end if;
  -- inserted out of time order: the NEWEST checked_at wins, not the last insert
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cnew, 'contradicted', 'web', now() - interval '1 day');
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cnew, 'confirmed', 'web', now() - interval '2 days');
  select * into r from public.claim_current where id = cnew;
  if r.last_check_outcome <> 'contradicted' or r.is_current or r.last_checked_at <> now() - interval '1 day' then
    raise exception 'FAIL[contradicted-newest]: % % %', r.last_check_outcome, r.is_current, r.last_checked_at; end if;
  insert into public.claim_verification (claim_id, outcome, method, checked_at) values (cnew, 'confirmed', 'human', now());
  select * into r from public.claim_current where id = cnew;
  if r.last_check_outcome <> 'confirmed' or not r.is_current then raise exception 'FAIL[reconfirmed]: % %', r.last_check_outcome, r.is_current; end if;
  if (select count(*) from public.claim_current where id = cnew) <> 1 then raise exception 'FAIL[one-row-per-claim]'; end if;
  update public.claim set next_check_at = now() - interval '1 hour' where id = cnew;
  if not (select is_overdue from public.claim_current where id = cnew) then raise exception 'FAIL[overdue-past]'; end if;
  update public.claim set next_check_at = now() + interval '1 hour' where id = cnew;
  if (select is_overdue from public.claim_current where id = cnew) then raise exception 'FAIL[overdue-future]'; end if;
  update public.claim set rank = 'deprecated' where id = cnew;
  if (select is_current from public.claim_current where id = cnew) then raise exception 'FAIL[deprecated]'; end if;
  update public.claim set rank = 'normal', valid_to = now() - interval '1 second' where id = cnew;
  if (select is_current from public.claim_current where id = cnew) then raise exception 'FAIL[expired]'; end if;
  update public.claim set valid_to = now() + interval '1 day', status = 'rejected' where id = cnew;
  if (select is_current from public.claim_current where id = cnew) then raise exception 'FAIL[rejected]'; end if;
  update public.claim set status = 'approved' where id = cnew;
  if not (select is_current from public.claim_current where id = cnew) then raise exception 'FAIL[approved]'; end if;
  raise notice 'PASS';
end"""),
        ("direct_delete_probe", "service_role", f"""
declare cnew uuid; n int;
begin
{_new_claim('cnew', 'dd')}
  insert into public.claim_verification (claim_id, outcome, method) values (cnew, 'confirmed', 'web');
  delete from public.claim_verification where claim_id = cnew;
  get diagnostics n = row_count;
  raise notice 'INFO direct DELETE on claim_verification removed % row(s) (the trigger guards UPDATE only)', n;
  {ok}
end"""),
    ] + [
        (f"{role}_refused", role, f"""
declare cn text;
begin
{_expect_error('insufficient_privilege', "perform 1 from public.claim_current limit 1", 'select-view')}
{_expect_error('insufficient_privilege', "perform 1 from public.claim_verification limit 1", 'select-verification')}
{_expect_error('insufficient_privilege', "perform 1 from public.claim_label limit 1", 'select-label')}
{_expect_error('insufficient_privilege', "perform 1 from public.judge_audit limit 1", 'select-audit')}
{_expect_error('insufficient_privilege', "insert into public.claim_verification (claim_id, outcome, method) values (gen_random_uuid(), 'confirmed', 'web')", 'insert-verification')}
{_expect_error('insufficient_privilege', "insert into public.judge_audit (run_date, part, n, hits, bound, threshold, passed, judge_model, judge_prompt_hash) values ('2026-12-01', 'a', 1, 1, 1, 1, true, 'm', '" + GOOD_HASH + "')", 'insert-audit')}
{_expect_error('insufficient_privilege', "perform public.claim_evidence_ok_v1(null)", 'exec-evidence-fn')}
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


def dashboard_texts(src: str) -> tuple[str, str]:
    pre = commented_block(src, "PREFLIGHT").strip() + "\n"
    head_pre = ("-- 0023 PREFLIGHT for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).\n"
                "-- GENERATED from supabase/migrations/0023_graph_v2_l1_freshness.sql by rehearse_0023.py --emit-dashboard;\n"
                "-- the rehearsal fails if this file drifts. READ-ONLY. APPLY 0022 FIRST, then run this, then 0023.\n"
                "-- Expect: prereq_0022 = true, no_0023_columns = true, no_0023_tables = true. Note the two\n"
                "-- baseline_* rows: VERIFY's info_claim_rows must equal baseline_claim_rows after the paste.\n"
                "-- Any false: STOP. prereq_0022 false = 0022 is not applied; a no_0023_* false = a partial or\n"
                "-- earlier 0023 is already there (run 0023_verify_dashboard.sql to see which part).\n")
    parts = []
    for line in commented_block(src, "VERIFY").splitlines():
        m = re.match(r"^select '([a-z0-9_]+)', (.*);$", line.strip())
        if m:
            parts.append(f"select '{m.group(1)}' as check_name, ({m.group(2)})::text as ok")
    head_ver = ("-- 0023 VERIFY for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).\n"
                "-- GENERATED from the migration's VERIFY block by rehearse_0023.py --emit-dashboard (drift fails the\n"
                "-- rehearsal). READ-ONLY. Run AFTER the 0023 paste. Expect %d rows; every row NOT starting with info_\n"
                "-- must read true. info_claim_rows = the preflight baseline_claim_rows. A false row: re-paste 0023\n"
                "-- once (it is re-runnable), re-run this; still false = stop and run the ROLLBACK block.\n" % len(parts))
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
    print(f"  {len(new)} 0023 checks on the un-migrated twin: {len(new) - len(passing_new)} fail (must be all)"
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
        for line in p.stderr.splitlines():
            if "INFO " in line:
                print(f"        {line.split('INFO ', 1)[1]}")
    return all_ok


def diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Rehearse migration 0023 on the twin.")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only (default)")
    ap.add_argument("--execute", action="store_true", help="run the full gate against the twin")
    ap.add_argument("--preflight-only", action="store_true", help="connect, run preflight, stop")
    ap.add_argument("--emit-dashboard", action="store_true", help="write the two runbook SQL files and exit")
    ap.add_argument("--leave-applied", action="store_true", help="end in the 0023 state (with --execute)")
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
    faults = [
        ("5a", "alter table public.claim drop constraint claim_rank_vocab;", "claim_new_checks"),
        ("5b", "grant select on public.claim_current to anon;", "new_relations_no_api_grants"),
        ("5c", "alter table public.claim_verification disable trigger claim_verification_append_only;",
         "claim_verification_append_only_trigger"),
        ("5d", "alter table public.judge_audit disable row level security;", "new_tables_rls_on_no_policies"),
        ("5e", "grant execute on function public.claim_evidence_ok_v1(jsonb) to anon;", "evidence_fn_exec_service_role_only"),
        ("5f", "alter view public.claim_current set (security_invoker = off);", "claim_current_invoker"),
        ("5g", "alter table public.claim drop constraint claim_evidence_no_pii;", "pii_checks_on_new_text"),
        ("5h", "grant insert on public.claim_label to authenticated;", "new_relations_no_api_grants"),
    ]
    missing = [n for _, _, n in faults if n not in expected]
    if missing:
        sys.exit(f"planted faults name checks that VERIFY lacks: {missing}")

    if not (a.execute or a.preflight_only) or a.dry_run:
        print("rehearse_0023 — DRY RUN (no connection made)\n")
        print(f"  target           twin {TWIN_REF} via {TWIN_HOST} as {TWIN_USER} (hard-coded; prod refused)")
        print(f"  migration        {os.path.relpath(MIGRATION, REPO)}  sha256:{hashlib.sha256(src.encode()).hexdigest()[:16]}…")
        print(f"  verify checks    {len(expected)}: {', '.join(expected)}")
        print(f"  behaviour cases  {', '.join(n for n, _, _ in behaviour_cases())}")
        print("  planted faults   " + "; ".join(f"{s} -> {n}" for s, _, n in faults))
        print("\n  run with --execute to perform it (twin only).")
        return 0

    refuse_non_twin()
    print(f"TARGET twin: {TWIN_HOST} as {TWIN_USER}  at {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"migration sha256: {hashlib.sha256(src.encode()).hexdigest()}")
    if a.reset_first:
        print("\n[-] reset: ROLLBACK block + rehearsal-row cleanup")
        run_sql(rollback_sql, "rollback (reset; errors tolerated if 0023 was not applied)")
        run_sql(CLEANUP_SQL, "rehearsal-row cleanup")

    print("\n[0] preflight")
    print(f"  twin server_version={psql(['-tA', '-c', 'show server_version']).stdout.strip()} (prod 17.6)")
    pf = kv(PREFLIGHT_SQL)
    for k, v in pf.items():
        print(f"  {k:28s} {v}")
    if [k for k in REQUIRED if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin lacks prerequisites: {[k for k in REQUIRED if pf.get(k) != 'true']} "
                 "(0022 missing? run rehearse_0022.py --execute --leave-applied)")
    if [k for k in CLEAN if pf.get(k) != "true"]:
        sys.exit(f"PREFLIGHT FAIL — twin already has 0023 objects {[k for k in CLEAN if pf.get(k) != 'true']}; "
                 "re-run with --reset-first")
    out = psql(["-tA", "-F", "\t"], stdin="set default_transaction_read_only = on;\n" + preflight_block).stdout
    rows = dict(l.split("\t", 1) for l in out.splitlines() if "\t" in l)
    print(f"  migration PREFLIGHT block: {rows}")
    bad = [k for k in PREFLIGHT_GATING if rows.get(k) != "true"]
    if bad or not all(k in rows for k in ("baseline_claim_rows", "baseline_claim_by_status")):
        sys.exit(f"PREFLIGHT FAIL — the migration's own PREFLIGHT block is not green on the twin: {bad or rows}")
    if rows["baseline_claim_rows"] != pf.get("info.claim_rows"):
        sys.exit("PREFLIGHT FAIL — PREFLIGHT baseline_claim_rows disagrees with the harness count")
    for path, text in ((DASH_PREFLIGHT, dash_pre), (DASH_VERIFY, dash_ver)):
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if cur != text:
            sys.exit(f"PREFLIGHT FAIL — {os.path.relpath(path, REPO)} drifted from the migration; run --emit-dashboard")
    print("  dashboard runbook files in sync with the migration")
    base_claims = pf.get("info.claim_rows")
    if a.preflight_only:
        return 0

    print("\n[1] snapshot A (before)")
    snap_a = kv(SNAPSHOT_SQL)
    print(f"  claims by status: {snap_a.get('data.claim_by_status')}; "
          f"{len([k for k in snap_a if not k.startswith(('count.', 'data.'))])} schema parts, "
          f"{len([k for k in snap_a if k.startswith(('count.', 'data.'))])} data values")

    print("\n[1b] negative control — 0023's checks must FAIL before the fix; keep_* must pass")
    if not negative_control(verify_sql, expected):
        sys.exit("GATE FAIL at 1b — a check passes without the fix (or a keep_ check is already red)")

    print("\n[2] apply 0023")
    if not apply("0023_graph_v2_l1_freshness.sql"):
        sys.exit("GATE FAIL at step 2")

    print("\n[3] re-apply 0023 (must be a clean no-op)")
    snap_b1 = {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS)}
    if not apply("0023 second paste"):
        sys.exit("GATE FAIL at step 3 — 0023 is not re-runnable")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS)})
    if d:
        sys.exit(f"GATE FAIL at step 3 — second paste changed state: {d}")
    print("  OK  state identical after second paste")

    print("\n[4] verify")
    if not verify(verify_sql, expected)[0]:
        sys.exit("GATE FAIL at step 4")
    dash = psql(["-tA", "-F", "\t"], stdin="set default_transaction_read_only = on;\n" + dash_ver, check=False).stdout
    drows = [l.split("\t") for l in dash.splitlines() if "\t" in l]
    dbad = [n for n, v in drows if not n.startswith("info_") and v != "true"]
    print(f"  dashboard VERIFY: {len(drows)} rows, non-info rows not 'true': {dbad or 'none'}")
    if dbad or len(drows) != len(expected):
        sys.exit("GATE FAIL at step 4 — the dashboard VERIFY form disagrees")

    print("\n[4b] behaviour (twin only; every case rolled back)")
    if not behaviour():
        sys.exit("GATE FAIL at step 4b")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS)})
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
        if not apply(f"0023 restore after {step}") or not verify(verify_sql, expected, quiet=True)[0]:
            sys.exit(f"GATE FAIL at step {step} — re-apply did not restore a passing state")
    d = diff(snap_b1, {**kv(SNAPSHOT_SQL), **kv(NEW_COUNTS)})
    if d:
        sys.exit(f"GATE FAIL at step 5 — the restored state differs from the first apply: {d}")
    print("  OK  restored state identical to the first apply")

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
          f"function bodies + ACLs + view definitions included) + "
          f"{len([k for k in snap_a if k.startswith(('count.', 'data.'))])} data values identical — ROLLBACK PROVEN")

    print("\n[8] cleanup")
    if not run_sql(CLEANUP_SQL, "rehearsal-row delete (expect 0)"):
        sys.exit("GATE FAIL at step 8")
    after = kv(f"select 'n', count(*)::text from public.claim;\n"
               f"select 'r', count(*)::text from public.claim where source_key = '{REHEARSAL_SOURCE_KEY}';\n"
               + "\n".join(f"select 'rel.{r}', (to_regclass('{r}') is null)::text;" for r in NEW_RELATIONS))
    if after.get("n") != base_claims or after.get("r") != "0" or any(v != "true" for k, v in after.items() if k.startswith("rel.")):
        sys.exit(f"GATE FAIL at step 8 — twin not back to preflight: {after}")
    print(f"  OK  claim rows {after['n']} (preflight {base_claims}); rehearsal rows 0; no 0023 relations")

    if a.leave_applied:
        print("\n[9] re-apply for development (--leave-applied)")
        if not apply("0023") or not verify(verify_sql, expected)[0]:
            sys.exit("re-apply verify failed")

    print("\n0023 REHEARSAL: GREEN — safe for Alex to run supabase/scripts/0023_preflight_dashboard.sql, paste 0023 "
          "into prod (The-Prod-Brain) after 0022, then run supabase/scripts/0023_verify_dashboard.sql there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
