-- =============================================================================
-- 0023 · Intelligence graph v2: L1 evidence, judge record, rank/flag, freshness, human labels
-- Linear: YED-384 · Design: docs/adr/ADR-15-intelligence-graph-v2.md decisions 4, 5, 7, 8, 11, 14.
--
-- APPLIED to prod 2026-11-14 (Alex; evidence supabase/evidence/yed384_0023_prod_verify-20261114.md). Twin rehearsal (supabase/scripts/rehearse_0023.py) + Alex dashboard apply required
-- (CLAUDE.md invariant 2). ADDITIVE ONLY: no column, row, constraint or index is dropped or renamed.
--
-- ORDER: APPLY 0022 FIRST. 0023 reuses public.no_contact_pii_v1(text) (0022 §8) for its PII CHECKs
-- and refuses to run without it (guard below).
--
-- READERS FIRST (ADR-15 decision 7): 0023 only ADDS rank / review_flag with neutral defaults
-- (rank 'normal', flag null), so match_claims_hybrid (0010), entity_neighborhood (0011) and mi.fact (0016) are unaffected.
-- Before ANY row gets a non-default rank or flag, the follow-up migration 0024 moves those three
-- readers onto public.claim_current. Until then spine_client's claim ALLOW list must leave rank and
-- review_flag out (a guard-file change: Alex reviews it, CLAUDE.md invariant 1).
--
-- WHAT (one transaction):
--   1. public.claim_evidence_ok_v1(jsonb): the evidence-shape predicate. NULL is fine (v1 rows);
--      otherwise a JSON array of 1-8 objects with exactly {para_idx: int >= 0, quote: non-empty
--      string of <= 25 words}. 25 words = the 0009 licensing guard on claim.quote, per span.
--      VERSIONED like 0022's functions: created only when absent, never CREATE OR REPLACE.
--   2. claim columns (all nullable or constant-default: no table rewrite):
--        evidence                                       multi-span support (decision 2, 14)
--        judge_verdict, judge_model, judge_prompt_hash, judged_at   the judge record (decision 4)
--        rank ('preferred'|'normal'|'deprecated', default 'normal'), review_flag (null|
--        'needs_review'|'disputed')                     instead of widening status (decision 7)
--        valid_from, valid_to                           validity window (decision 7)
--        freshness_class, freshness_conf, freshness_reason, next_check_at   (decision 8)
--        visibility ('private'|'public_ok', default 'private'; the documents vocabulary, 0009)
--      CHECKs: vocabularies, judge record all-or-nothing, valid_to >= valid_from, freshness_conf in
--      [0,1], evidence shape, and the PII backstop on evidence and freshness_reason.
--   3. public.claim_verification: append-only re-check log (decision 8; absorbs YED-410). An UPDATE
--      is refused by trigger. DELETE is not trigger-guarded: the API roles hold no privilege
--      (RLS + revokes) and service_role writes only through spine_client, which has no delete verb
--      for this table; rows otherwise leave by cascade when their claim is deleted.
--   4. public.claim_label: one row per human label (decision 4b / 5). inclusion_prob is the
--      sampling probability of the claim in its sample run: oversampling means every estimate
--      weights a label by 1 / inclusion_prob (Horvitz-Thompson). One label per claim per run.
--   5. public.judge_audit: one row per audit run, part 'a' (planted errors) or 'b' (human labels).
--      Totals only; the per-claim truth lives in claim_label.
--   6. public.claim_current: security_invoker view over claim + its latest verification, with
--      is_current and is_overdue. The read surface for 0024's readers and for retrieval's
--      overdue flag (decision 8: retrieval flags, the parent re-checks).
--   7. Security: RLS on the three new tables, no policies, every privilege revoked from public /
--      anon / authenticated (0020/0022 pattern); the view and the new function likewise; the
--      function is granted to service_role explicitly (CHECKs run as the writing role).
--
-- NOT HERE, deliberately (ADR-15 decision 14): entity_merge, claim_derivation,
-- independent_source_group, source reliability, insight, insight_claim (each ships with its first
-- writer); `layer`, `recorded_at`, `invalidated_by` (dropped in rev 2); the reader rewrite (0024).
--
-- RE-RUNNABLE and LOCK-LIGHT on re-paste: every DDL statement is catalog-guarded, so a second paste
-- takes no ACCESS EXCLUSIVE lock on claim. The first paste takes it briefly per ALTER (column adds
-- are catalog-only; each CHECK scans claim once, ~6k rows).
--
-- APPLY (Alex, prod dashboard): supabase/scripts/0023_preflight_dashboard.sql, this file, then
-- supabase/scripts/0023_verify_dashboard.sql. Paste OUTSIDE 07:00-09:00 UTC. lock_timeout is 5s:
-- a busy table fails the paste instead of queueing; just re-paste.
-- =============================================================================

begin;
set local lock_timeout = '5s';

do $do$
begin
  if to_regprocedure('public.no_contact_pii_v1(text)') is null then
    raise exception '0023 needs 0022 (public.no_contact_pii_v1 is missing). Apply 0022 first.';
  end if;
end
$do$;

-- -----------------------------------------------------------------------------
-- 1. Versioned evidence predicate. Created only when ABSENT; NEVER CREATE OR REPLACE.
--    Python twin: .claude/.state/judge-pilot-20261112/pilot.py check_v3 (span shape) — the
--    extractor-side check stays the primary guard; this is the DB backstop.
-- -----------------------------------------------------------------------------
do $do$
begin
  if to_regprocedure('public.claim_evidence_ok_v1(jsonb)') is null then
    execute $ddl$
      create function public.claim_evidence_ok_v1(e jsonb)
      returns boolean
      language sql
      immutable
      parallel safe
      set search_path = pg_catalog, pg_temp
      as $fn$
        -- CASE, not AND/OR: SQL does not promise short-circuit order, and jsonb_array_length /
        -- jsonb_object_keys raise on the wrong type. A malformed value must return false, never error.
        select case
          when e is null then true
          when jsonb_typeof(e) <> 'array' then false
          when jsonb_array_length(e) not between 1 and 8 then false
          else not exists (
            select 1 from jsonb_array_elements(e) as s(span)
             where case
                     when jsonb_typeof(s.span) <> 'object' then true
                     when (select array_agg(k order by k) from jsonb_object_keys(s.span) as k)
                          is distinct from array['para_idx', 'quote'] then true
                     when jsonb_typeof(s.span -> 'para_idx') <> 'number' then true
                     when (s.span ->> 'para_idx') !~ '^[0-9]{1,6}$' then true
                     when jsonb_typeof(s.span -> 'quote') <> 'string' then true
                     when btrim(s.span ->> 'quote') = '' then true
                     else array_length(regexp_split_to_array(btrim(s.span ->> 'quote'), '\s+'), 1) > 25
                   end)
        end
      $fn$
    $ddl$;
  end if;
end
$do$;
revoke all on function public.claim_evidence_ok_v1(jsonb) from public, anon, authenticated;
grant execute on function public.claim_evidence_ok_v1(jsonb) to service_role;

-- -----------------------------------------------------------------------------
-- 2. claim columns + CHECKs (each constraint guarded by name, so a re-paste is a no-op).
-- -----------------------------------------------------------------------------
alter table public.claim
  add column if not exists evidence           jsonb,
  add column if not exists judge_verdict      text,
  add column if not exists judge_model        text,
  add column if not exists judge_prompt_hash  text,
  add column if not exists judged_at          timestamptz,
  add column if not exists rank               text not null default 'normal',
  add column if not exists review_flag        text,
  add column if not exists valid_from         timestamptz,
  add column if not exists valid_to           timestamptz,
  add column if not exists freshness_class    text,
  add column if not exists freshness_conf     numeric,
  add column if not exists freshness_reason   text,
  add column if not exists next_check_at      timestamptz,
  add column if not exists visibility         text not null default 'private';

do $do$
declare
  c record;
begin
  for c in
    select * from (values
      ('claim_evidence_shape',         'check (public.claim_evidence_ok_v1(evidence))'),
      ('claim_evidence_no_pii',        'check (public.no_contact_pii_v1(evidence::text))'),
      ('claim_judge_verdict_vocab',    'check (judge_verdict is null or judge_verdict in (''supported'', ''unsupported'', ''abstain''))'),
      ('claim_judge_record_complete',  'check ((judge_verdict is null) = (judge_model is null) and (judge_verdict is null) = (judge_prompt_hash is null) and (judge_verdict is null) = (judged_at is null))'),
      ('claim_judge_prompt_hash_hex',  'check (judge_prompt_hash is null or judge_prompt_hash ~ ''^[0-9a-f]{64}$'')'),
      ('claim_rank_vocab',             'check (rank in (''preferred'', ''normal'', ''deprecated''))'),
      ('claim_review_flag_vocab',      'check (review_flag is null or review_flag in (''needs_review'', ''disputed''))'),
      ('claim_valid_window',           'check (valid_to is null or valid_from is null or valid_to >= valid_from)'),
      ('claim_freshness_class_vocab',  'check (freshness_class is null or freshness_class in (''historical'', ''fast_moving'', ''slow_moving'', ''opinion'', ''none_fits''))'),
      ('claim_freshness_conf_range',   'check (freshness_conf is null or (freshness_conf >= 0 and freshness_conf <= 1))'),
      ('claim_freshness_reason_no_pii','check (public.no_contact_pii_v1(freshness_reason))'),
      ('claim_visibility_vocab',       'check (visibility in (''private'', ''public_ok''))')
    ) as t(name, def)
  loop
    if not exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass and conname = c.name) then
      execute format('alter table public.claim add constraint %I %s', c.name, c.def);
    end if;
  end loop;
end
$do$;

create index if not exists claim_next_check_idx   on public.claim (next_check_at) where next_check_at is not null;
create index if not exists claim_review_flag_idx  on public.claim (review_flag)   where review_flag is not null;

comment on column public.claim.evidence is
  '0023 (ADR-15 d2/d14): [{para_idx, quote}] spans the extractor cites; 1-8 spans, each <= 25 words. NULL on v1 rows.';
comment on column public.claim.rank is
  '0023 (ADR-15 d7): preferred | normal | deprecated. Do not write a non-default value before 0024 moves the readers to claim_current.';
comment on column public.claim.review_flag is
  '0023 (ADR-15 d7/d8): null | needs_review | disputed. Same 0024 prerequisite as rank.';

-- -----------------------------------------------------------------------------
-- 3. claim_verification: append-only re-check log.
-- -----------------------------------------------------------------------------
create table if not exists public.claim_verification (
  id                  uuid primary key default gen_random_uuid(),
  claim_id            uuid not null references public.claim(id) on delete cascade,
  outcome             text not null check (outcome in ('confirmed', 'updated', 'contradicted', 'unverifiable')),
  method              text not null check (method in ('web', 'graph', 'human', 'llm')),
  source_url          text,
  source_document_id  uuid references public.documents(id) on delete set null,
  checker_model       text,
  run_id              text,
  note                text,
  checked_at          timestamptz not null default now(),
  constraint claim_verification_note_no_pii       check (public.no_contact_pii_v1(note)),
  constraint claim_verification_source_url_no_pii check (public.no_contact_pii_v1(source_url))
);
create index if not exists claim_verification_claim_idx on public.claim_verification (claim_id, checked_at desc);

create or replace function public.claim_verification_append_only()
returns trigger
language plpgsql
set search_path = pg_catalog, pg_temp
as $fn$
begin
  raise exception 'claim_verification is append-only (ADR-15 decision 8): insert a new row instead of updating %', old.id;
end
$fn$;
revoke all on function public.claim_verification_append_only() from public, anon, authenticated;

do $do$
begin
  if not exists (select 1 from pg_trigger where tgrelid = 'public.claim_verification'::regclass
                   and tgname = 'claim_verification_append_only') then
    create trigger claim_verification_append_only
      before update on public.claim_verification
      for each row execute function public.claim_verification_append_only();
  elsif exists (select 1 from pg_trigger where tgrelid = 'public.claim_verification'::regclass
                  and tgname = 'claim_verification_append_only' and tgenabled <> 'O') then
    -- a re-paste repairs a disabled guard (lock taken only in that case)
    alter table public.claim_verification enable trigger claim_verification_append_only;
  end if;
end
$do$;

-- -----------------------------------------------------------------------------
-- 4. claim_label: one human label per claim per sample run.
-- -----------------------------------------------------------------------------
create table if not exists public.claim_label (
  id              uuid primary key default gen_random_uuid(),
  claim_id        uuid not null references public.claim(id) on delete cascade,
  sample_run      text not null,                 -- e.g. '2026-12-4b'
  stratum         text not null,                 -- e.g. 'multi_span', 'partnership', 'thesis', 'hedge', 'rest'
  inclusion_prob  numeric not null check (inclusion_prob > 0 and inclusion_prob <= 1),
  label           text not null check (label in ('supported', 'unsupported')),
  useful          smallint check (useful is null or useful between 0 and 2),
  labeler         text not null default 'alex',
  note            text,
  labelled_at     timestamptz not null default now(),
  constraint claim_label_note_no_pii check (public.no_contact_pii_v1(note)),
  unique (claim_id, sample_run)
);
create index if not exists claim_label_run_idx on public.claim_label (sample_run);

-- -----------------------------------------------------------------------------
-- 5. judge_audit: one row per audit run (totals).
-- -----------------------------------------------------------------------------
create table if not exists public.judge_audit (
  id                 uuid primary key default gen_random_uuid(),
  run_date           date not null,
  part               text not null check (part in ('a', 'b')),
  n                  integer not null check (n > 0),
  hits               integer not null,          -- part a: errors caught; part b: false passes
  bound              numeric not null check (bound >= 0 and bound <= 1),   -- a: Wilson LB; b: Wilson UB (pooled)
  threshold          numeric not null check (threshold >= 0 and threshold <= 1),
  passed             boolean not null,
  judge_model        text not null,
  judge_prompt_hash  text not null check (judge_prompt_hash ~ '^[0-9a-f]{64}$'),
  batch              text,
  confirms_audit_id  uuid references public.judge_audit(id) on delete set null,   -- a trip's confirming re-run
  created_at         timestamptz not null default now(),
  check (hits >= 0 and hits <= n),
  check ((part = 'a' and passed = (bound >= threshold)) or (part = 'b' and passed = (bound <= threshold)))
);
create index if not exists judge_audit_run_idx on public.judge_audit (part, run_date desc);

-- -----------------------------------------------------------------------------
-- 6. claim_current: the read surface (security_invoker, so the caller's RLS applies).
-- -----------------------------------------------------------------------------
create or replace view public.claim_current
with (security_invoker = on) as
select c.*,
       v.outcome     as last_check_outcome,
       v.checked_at  as last_checked_at,
       (c.status <> 'rejected'
        and c.rank <> 'deprecated'
        and (c.valid_to is null or c.valid_to > now())
        and v.outcome is distinct from 'contradicted')                       as is_current,
       (c.next_check_at is not null and c.next_check_at <= now())           as is_overdue
  from public.claim c
  left join lateral (
    select cv.outcome, cv.checked_at
      from public.claim_verification cv
     where cv.claim_id = c.id
     order by cv.checked_at desc, cv.id desc
     limit 1) v on true;
comment on view public.claim_current is
  '0023 (ADR-15 d7/d8): claim + latest verification; is_current drops rejected, deprecated, expired and '
  'last-contradicted claims; is_overdue = next_check_at passed. 0024 moves match_claims_hybrid, entity_neighborhood and mi.fact onto it.';

-- -----------------------------------------------------------------------------
-- 7. Security (RLS guarded so a re-paste takes no lock).
-- -----------------------------------------------------------------------------
do $do$
declare
  t text;
begin
  foreach t in array array['claim_verification', 'claim_label', 'judge_audit'] loop
    if not (select relrowsecurity from pg_class where oid = format('public.%I', t)::regclass) then
      execute format('alter table public.%I enable row level security', t);
    end if;
  end loop;
end
$do$;
revoke all on public.claim_verification from public, anon, authenticated;
revoke all on public.claim_label        from public, anon, authenticated;
revoke all on public.judge_audit        from public, anon, authenticated;
revoke all on public.claim_current      from public, anon, authenticated;

commit;

-- =============================================================================
-- PREFLIGHT (read-only; run on prod BEFORE the paste: supabase/scripts/0023_preflight_dashboard.sql
-- is this block). Expect prereq_0022 = true, no_0023_columns = true, and the baseline counts.
-- =============================================================================
-- PREFLIGHT:BEGIN
-- select 'prereq_0022' as check_name, (to_regprocedure('public.no_contact_pii_v1(text)') is not null and to_regclass('public.entity_alias') is not null)::text as detail
-- union all
-- select 'no_0023_columns', (not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('evidence', 'judge_verdict', 'judge_model', 'judge_prompt_hash', 'judged_at', 'rank', 'review_flag', 'valid_from', 'valid_to', 'freshness_class', 'freshness_conf', 'freshness_reason', 'next_check_at', 'visibility')))::text
-- union all
-- select 'no_0023_tables', (to_regclass('public.claim_verification') is null and to_regclass('public.claim_label') is null and to_regclass('public.judge_audit') is null and to_regclass('public.claim_current') is null)::text
-- union all
-- select 'baseline_claim_rows', (select count(*) from public.claim)::text
-- union all
-- select 'baseline_claim_by_status', (select string_agg(status || '=' || n, ',' order by status) from (select status, count(*) n from public.claim group by status) s);
-- PREFLIGHT:END

-- =============================================================================
-- VERIFY (read-only). Every non-info row must read true. keep_* rows guard what 0023 must NOT
-- break (true before and after); *_at_apply rows hold only right after the paste (before any writer
-- uses the new columns); info_* rows are printed, never gating.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'claim_new_columns', (select count(*) = 14 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('evidence', 'judge_verdict', 'judge_model', 'judge_prompt_hash', 'judged_at', 'rank', 'review_flag', 'valid_from', 'valid_to', 'freshness_class', 'freshness_conf', 'freshness_reason', 'next_check_at', 'visibility'));
-- select 'claim_rank_visibility_defaults', (select bool_and(case column_name when 'rank' then column_default = '''normal''::text' and is_nullable = 'NO' when 'visibility' then column_default = '''private''::text' and is_nullable = 'NO' end) from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name in ('rank', 'visibility'));
-- select 'claim_new_checks', (select count(*) = 12 from pg_constraint where conrelid = 'public.claim'::regclass and contype = 'c' and convalidated and conname in ('claim_evidence_shape', 'claim_evidence_no_pii', 'claim_judge_verdict_vocab', 'claim_judge_record_complete', 'claim_judge_prompt_hash_hex', 'claim_rank_vocab', 'claim_review_flag_vocab', 'claim_valid_window', 'claim_freshness_class_vocab', 'claim_freshness_conf_range', 'claim_freshness_reason_no_pii', 'claim_visibility_vocab'));
-- select 'claim_all_rows_neutral_at_apply', not exists (select 1 from public.claim where rank <> 'normal' or review_flag is not null or visibility <> 'private' or evidence is not null or judge_verdict is not null);
-- select 'keep_claim_status_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((status = ANY (ARRAY[''candidate''::text, ''approved''::text, ''rejected''::text])))' from pg_constraint where conrelid = 'public.claim'::regclass and conname = 'claim_status_check');
-- select 'evidence_fn_behaviour', (select provolatile = 'i' from pg_proc where oid = 'public.claim_evidence_ok_v1(jsonb)'::regprocedure) and public.claim_evidence_ok_v1(null) and public.claim_evidence_ok_v1('[{"para_idx": 3, "quote": "Acme raised a Series B"}]') and public.claim_evidence_ok_v1('[{"para_idx": 0, "quote": "a"}, {"para_idx": 12, "quote": "b c"}]') and not public.claim_evidence_ok_v1('[]') and not public.claim_evidence_ok_v1('{"para_idx": 1, "quote": "x"}') and not public.claim_evidence_ok_v1('[{"para_idx": -1, "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1.5, "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": "1", "quote": "x"}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "  "}]') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "x", "extra": 1}]') and not public.claim_evidence_ok_v1('[{"quote": "x"}]') and not public.claim_evidence_ok_v1('["x"]') and not public.claim_evidence_ok_v1('"x"') and not public.claim_evidence_ok_v1('[{"para_idx": 1, "quote": "x"}, 7]') and public.claim_evidence_ok_v1(jsonb_build_array(jsonb_build_object('para_idx', 1, 'quote', array_to_string(array_fill('w'::text, array[25]), ' ')))) and not public.claim_evidence_ok_v1(jsonb_build_array(jsonb_build_object('para_idx', 1, 'quote', array_to_string(array_fill('w'::text, array[26]), ' '))));
-- select 'evidence_fn_exec_service_role_only', has_function_privilege('service_role', 'public.claim_evidence_ok_v1(jsonb)', 'execute') and not has_function_privilege('anon', 'public.claim_evidence_ok_v1(jsonb)', 'execute') and not has_function_privilege('authenticated', 'public.claim_evidence_ok_v1(jsonb)', 'execute');
-- select 'claim_verification_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'id,claim_id,outcome,method,source_url,source_document_id,checker_model,run_id,note,checked_at' from information_schema.columns where table_schema = 'public' and table_name = 'claim_verification');
-- select 'claim_verification_append_only_trigger', exists (select 1 from pg_trigger t where t.tgrelid = 'public.claim_verification'::regclass and t.tgname = 'claim_verification_append_only' and t.tgenabled = 'O' and t.tgfoid = 'public.claim_verification_append_only()'::regprocedure and (t.tgtype & 2) = 2 and (t.tgtype & 16) = 16 and (t.tgtype & 4) = 0 and (t.tgtype & 8) = 0);
-- select 'claim_label_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'id,claim_id,sample_run,stratum,inclusion_prob,label,useful,labeler,note,labelled_at' from information_schema.columns where table_schema = 'public' and table_name = 'claim_label');
-- select 'claim_label_one_per_run', exists (select 1 from pg_constraint where conrelid = 'public.claim_label'::regclass and contype = 'u' and pg_get_constraintdef(oid) = 'UNIQUE (claim_id, sample_run)');
-- select 'judge_audit_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'id,run_date,part,n,hits,bound,threshold,passed,judge_model,judge_prompt_hash,batch,confirms_audit_id,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'judge_audit');
-- select 'pii_checks_on_new_text', (select count(*) = 5 from pg_constraint where contype = 'c' and pg_get_constraintdef(oid) ~ 'no_contact_pii_v1' and conrelid in ('public.claim'::regclass, 'public.claim_verification'::regclass, 'public.claim_label'::regclass) and conname in ('claim_evidence_no_pii', 'claim_freshness_reason_no_pii', 'claim_verification_note_no_pii', 'claim_verification_source_url_no_pii', 'claim_label_note_no_pii'));
-- select 'new_tables_rls_on_no_policies', (select bool_and(relrowsecurity) from pg_class where oid in ('public.claim_verification'::regclass, 'public.claim_label'::regclass, 'public.judge_audit'::regclass)) and not exists (select 1 from pg_policies where schemaname = 'public' and tablename in ('claim_verification', 'claim_label', 'judge_audit'));
-- select 'new_relations_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r, unnest(array['public.claim_verification', 'public.claim_label', 'public.judge_audit', 'public.claim_current']) rel, unnest(array['select', 'insert', 'update', 'delete', 'truncate', 'references', 'trigger']) p where has_table_privilege(r, rel, p));
-- select 'new_tables_service_role_rw', (select bool_and(has_table_privilege('service_role', rel, 'select') and has_table_privilege('service_role', rel, 'insert') and has_table_privilege('service_role', rel, 'update') and has_table_privilege('service_role', rel, 'delete')) from unnest(array['public.claim_verification', 'public.claim_label', 'public.judge_audit']) rel) and has_table_privilege('service_role', 'public.claim_current', 'select');
-- select 'new_tables_no_pii_columns', (select count(*) = 3 from pg_class where oid in (to_regclass('public.claim_verification'), to_regclass('public.claim_label'), to_regclass('public.judge_audit'))) and not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name in ('claim_verification', 'claim_label', 'judge_audit') and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)');
-- select 'claim_current_invoker', (select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'public.claim_current'::regclass);
-- select 'claim_current_matches_claim_at_apply', (select count(*) from public.claim_current) = (select count(*) from public.claim) and (select count(*) filter (where is_current) from public.claim_current) = (select count(*) from public.claim where status <> 'rejected');
-- select 'keep_match_claims_present', to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is not null;
-- select 'keep_mi_fact_present', to_regclass('mi.fact') is not null or exists (select 1 from pg_proc where proname = 'fact' and pronamespace = 'mi'::regnamespace);
-- select 'info_claim_rows', (select count(*) from public.claim)::text;
-- select 'info_claim_current_is_current', (select count(*) filter (where is_current) from public.claim_current)::text;
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (uncomment to run). Drops only what 0023 adds. EXPORT FIRST on a prod that has run for
-- any time: the DROP TABLEs destroy claim_verification, claim_label and judge_audit rows, and the
-- DROP COLUMNs destroy evidence, judge records and freshness on claim (dashboard Table editor ->
-- Export to CSV; keep the files out of git). It FAILS LOUD if 0024 has already moved a reader onto
-- claim_current (the view drop would cascade into it): roll 0024 back first; never add CASCADE.
--
-- ROLLBACK:BEGIN
-- begin;
-- set local lock_timeout = '5s';
-- drop view if exists public.claim_current;
-- drop table if exists public.judge_audit;
-- drop table if exists public.claim_label;
-- drop table if exists public.claim_verification;
-- drop function if exists public.claim_verification_append_only();
-- drop index if exists public.claim_next_check_idx;
-- drop index if exists public.claim_review_flag_idx;
-- alter table public.claim
--   drop constraint if exists claim_evidence_shape,
--   drop constraint if exists claim_evidence_no_pii,
--   drop constraint if exists claim_judge_verdict_vocab,
--   drop constraint if exists claim_judge_record_complete,
--   drop constraint if exists claim_judge_prompt_hash_hex,
--   drop constraint if exists claim_rank_vocab,
--   drop constraint if exists claim_review_flag_vocab,
--   drop constraint if exists claim_valid_window,
--   drop constraint if exists claim_freshness_class_vocab,
--   drop constraint if exists claim_freshness_conf_range,
--   drop constraint if exists claim_freshness_reason_no_pii,
--   drop constraint if exists claim_visibility_vocab;
-- alter table public.claim
--   drop column if exists evidence,
--   drop column if exists judge_verdict,
--   drop column if exists judge_model,
--   drop column if exists judge_prompt_hash,
--   drop column if exists judged_at,
--   drop column if exists rank,
--   drop column if exists review_flag,
--   drop column if exists valid_from,
--   drop column if exists valid_to,
--   drop column if exists freshness_class,
--   drop column if exists freshness_conf,
--   drop column if exists freshness_reason,
--   drop column if exists next_check_at,
--   drop column if exists visibility;
-- drop function if exists public.claim_evidence_ok_v1(jsonb);
-- commit;
-- ROLLBACK:END
-- =============================================================================
