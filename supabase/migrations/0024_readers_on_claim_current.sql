-- =============================================================================
-- 0024 · Move the three live claim readers onto public.claim_current (ADR-15 decision 7 prerequisite)
-- Linear: YED-428 (parent YED-384) · Design: docs/adr/ADR-15-intelligence-graph-v2.md decisions 7, 8, 11.
--
-- APPLIED to prod 2026-11-14 (Alex; evidence supabase/evidence/yed384_0024_prod_verify-20261114.md). Twin rehearsal (supabase/scripts/rehearse_0024.py) + Alex dashboard apply required
-- (CLAUDE.md invariant 2).
--
-- ORDER: APPLY 0023 FIRST (applied to prod 2026-11-14). 0024 refuses to run without claim_current.
--
-- WHY: 0023 added claim.rank / review_flag / visibility / validity window and the re-check log, all
-- at neutral values. These readers still read public.claim and filter on status only, so the moment a
-- writer sets rank = 'deprecated' or a re-check logs 'contradicted', retired claims would keep reaching
-- retrieval packs and hub theme counts, and disputed claims would arrive with no flag. 0024 must land
-- before spine_client allows rank / review_flag / visibility (YED-429 stage 2).
--
-- BEHAVIOUR AT APPLY: identical results. Every prod claim is rank 'normal', no validity window, no
-- verification row (0023 VERIFY 2026-11-14), so nothing is retired. VERIFY proves the counts match.
--
-- WHAT (one transaction):
--   1. claim_current gains ONE column at the end, is_retired = rank 'deprecated' OR validity window
--      closed OR latest re-check 'contradicted'. Status is deliberately NOT part of it, so each reader
--      keeps its own status rule (is_current = status <> 'rejected' AND NOT is_retired, unchanged).
--   2. match_claims_hybrid (0010; called by retrieve.py through spine_client as service_role):
--        * base reads claim_current, keeps `status = any(filter_statuses)`, adds `not is_retired`;
--        * NEW trailing argument filter_visibility text[] DEFAULT NULL (null = no filter). L5 renderers
--          that produce public copy pass array['public_ok'] (ADR-15 decision 11);
--        * NEW trailing output columns review_flag, last_check_outcome, is_overdue, visibility, so a
--          disputed or overdue claim arrives flagged (decision 8: retrieval flags, the parent re-checks).
--      The return type changes, so this is DROP + CREATE of the 8-argument function inside the same
--      transaction (no window where it is missing). Callers use named arguments, so the old call shape
--      still works. Any other overload is left untouched.
--   3. entity_neighborhood (0011): same signature and jsonb shape; its `cl` block reads claim_current,
--      adds `not is_retired`, and each claim object gains review_flag, last_check_outcome, is_overdue,
--      visibility.
--   4. mi.fact (0016): the claim branch reads claim_current with `status <> 'rejected' and not
--      is_retired`. Same columns, same order, so mi.fact_company / mi.fact_topic need no change.
--      Recreated WITH (security_invoker = on) explicitly so the option cannot be dropped.
--   5. EXECUTE on both functions: revoked from public / anon / authenticated, granted to service_role.
--      Today anon and authenticated can call them but RLS on claim (no policies) returns 0 rows; after
--      0024 the functions read claim_current, which those roles cannot select (0023), so a call would
--      raise. Revoking makes that explicit. No caller uses those roles (repo + hub checked 2026-11-14).
--
-- NOT HERE: spine_client ALLOW changes (YED-429, guard file, Alex review); any producer writing rank /
-- review_flag / visibility.
--
-- RE-RUNNABLE: the view and mi.fact use CREATE OR REPLACE; the function swap is guarded by the old argument
-- signature, so a second paste does not drop it again. lock_timeout 5s; re-paste on timeout.
--
-- APPLY (Alex, prod dashboard): supabase/scripts/0024_preflight_dashboard.sql, this file ("Run without
-- RLS"), then supabase/scripts/0024_verify_dashboard.sql. Outside 07:00-09:00 UTC.
-- =============================================================================

begin;
set local lock_timeout = '5s';

do $do$
begin
  if to_regclass('public.claim_current') is null
     or not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name = 'rank') then
    raise exception '0024 needs 0023 (public.claim_current / claim.rank missing). Apply 0023 first.';
  end if;
end
$do$;

-- -----------------------------------------------------------------------------
-- 1. claim_current + is_retired (appended; existing columns unchanged, so CREATE OR REPLACE is legal).
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
       (c.next_check_at is not null and c.next_check_at <= now())           as is_overdue,
       (c.rank = 'deprecated'
        or (c.valid_to is not null and c.valid_to <= now())
        or v.outcome is not distinct from 'contradicted')                    as is_retired
  from public.claim c
  left join lateral (
    select cv.outcome, cv.checked_at
      from public.claim_verification cv
     where cv.claim_id = c.id
     order by cv.checked_at desc, cv.id desc
     limit 1) v on true;
comment on view public.claim_current is
  '0023/0024 (ADR-15 d7/d8): claim + latest verification. is_retired = deprecated, expired or last check '
  'contradicted (status-independent); is_current = not rejected and not retired; is_overdue = next_check_at '
  'passed. Read by match_claims_hybrid, entity_neighborhood and mi.fact (0024).';
revoke all on public.claim_current from public, anon, authenticated;

-- -----------------------------------------------------------------------------
-- 2. match_claims_hybrid: drop the 8-arg version only if it still has the 0010 return shape.
-- -----------------------------------------------------------------------------
do $do$
begin
  if to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is not null then
    drop function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[]);
  end if;
end
$do$;

create or replace function public.match_claims_hybrid(
  query_embedding    vector,
  query_text         text,
  match_count        integer DEFAULT 20,
  candidate_n        integer DEFAULT 40,
  rrf_k              integer DEFAULT 60,
  filter_entity_ids  uuid[]  DEFAULT NULL::uuid[],
  filter_statuses    text[]  DEFAULT ARRAY['approved'::text, 'candidate'::text],
  filter_tiers       text[]  DEFAULT NULL::text[],
  filter_visibility  text[]  DEFAULT NULL::text[])
returns table(id uuid, claim_text text, claim_type text, quote text, locator jsonb, provenance_tier text,
              confidence numeric, status text, metadata jsonb, document_id uuid, event_id uuid,
              asserted_at timestamp with time zone, dense_rank integer, keyword_rank integer,
              rrf_score double precision,
              review_flag text, last_check_outcome text, is_overdue boolean, visibility text)
language sql
stable
set search_path to 'public'
as $function$
  with base as (
    select c.*
    from public.claim_current c
    where c.status = any(filter_statuses)
      and not c.is_retired
      and (filter_visibility is null or c.visibility = any(filter_visibility))
      and (filter_tiers is null or c.provenance_tier = any(filter_tiers))
      and (filter_entity_ids is null
           or exists (select 1 from public.claim_entity ce
                      where ce.claim_id = c.id and ce.entity_id = any(filter_entity_ids))
           or exists (select 1 from public.event_entity ee
                      where ee.event_id = c.event_id and ee.entity_id = any(filter_entity_ids)))
  ),
  dense as (
    select id, row_number() over (order by embedding <=> query_embedding) as r
    from base where embedding is not null
    order by embedding <=> query_embedding limit candidate_n
  ),
  kw as (
    select id, row_number() over (order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc) as r
    from base where tsv @@ websearch_to_tsquery('english', query_text)
    order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc limit candidate_n
  ),
  fused as (
    select coalesce(d.id, k.id) as id, d.r as dr, k.r as kr,
           coalesce(1.0 / (rrf_k + d.r), 0) + coalesce(1.0 / (rrf_k + k.r), 0) as score
    from dense d full outer join kw k on d.id = k.id
  )
  select b.id, b.claim_text, b.claim_type, b.quote, b.locator, b.provenance_tier, b.confidence,
         b.status, b.metadata, b.document_id, b.event_id, b.asserted_at,
         f.dr::integer, f.kr::integer, f.score::float,
         b.review_flag, b.last_check_outcome, b.is_overdue, b.visibility
  from fused f join base b on b.id = f.id
  order by f.score desc, b.asserted_at desc nulls last
  limit match_count;
$function$;
revoke all on function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[], text[]) from public, anon, authenticated;
grant execute on function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[], text[]) to service_role;

-- -----------------------------------------------------------------------------
-- 3. entity_neighborhood: same signature; the cl block reads claim_current.
-- -----------------------------------------------------------------------------
create or replace function public.entity_neighborhood(seed_ids uuid[], since timestamp with time zone DEFAULT NULL::timestamp with time zone, max_events integer DEFAULT 60, max_claims integer DEFAULT 120, max_docs integer DEFAULT 40)
 returns jsonb
 language sql
 stable
 set search_path to 'public'
as $function$
  with ev as (
    select distinct e.id, e.title, e.kind, e.event_date, e.source, e.url, e.confidence
    from public.event e join public.event_entity ee on ee.event_id = e.id
    where ee.entity_id = any(seed_ids) and (since is null or e.event_date >= since)
      and e.kind <> all (array['role_posted', 'application', 'interview'])
    order by e.event_date desc nulls last limit max_events
  ),
  co as (
    select ee.event_id, ee.entity_type, ee.entity_id, ee.role,
           coalesce(c.name, p.name, t.name) as name
    from public.event_entity ee
    left join public.company c on c.id = ee.entity_id and ee.entity_type = 'company'
    left join public.person  p on p.id = ee.entity_id and ee.entity_type = 'person'
    left join public.topic   t on t.id = ee.entity_id and ee.entity_type = 'topic'
    where ee.event_id in (select id from ev)
  ),
  docs as (
    select distinct d.id, d.title, d.source_type, d.doc_date, d.external_ref, d.event_id
    from public.documents d
    left join public.document_entity de on de.document_id = d.id
    where d.is_current and (de.entity_id = any(seed_ids) or d.event_id in (select id from ev))
    order by d.doc_date desc nulls last limit max_docs
  ),
  cl as (
    select distinct c.id, c.claim_text, c.claim_type, c.provenance_tier, c.confidence, c.status,
           c.event_id, c.document_id, c.asserted_at, c.metadata,
           c.review_flag, c.last_check_outcome, c.is_overdue, c.visibility
    from public.claim_current c
    left join public.claim_entity ce on ce.claim_id = c.id
    where c.status in ('approved', 'candidate')
      and not c.is_retired
      and (ce.entity_id = any(seed_ids) or c.event_id in (select id from ev))
    order by c.asserted_at desc nulls last limit max_claims
  ),
  hiring as (
    select c.id as company_id, c.name, count(distinct e.id) as roles,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'A') as tier_a,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'B') as tier_b,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'C') as tier_c,
           max(e.event_date) as latest_posted
    from public.event e
    join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
    join public.company c on c.id = ee.entity_id
    where ee.entity_id = any(seed_ids) and e.kind = 'role_posted'
      and coalesce(e.metadata->>'status', '') <> 'archived'   -- archived in Notion = closed or not pursued
    group by c.id, c.name
  )
  select jsonb_build_object(
    'events',    (select coalesce(jsonb_agg(to_jsonb(ev)),     '[]'::jsonb) from ev),
    'edges',     (select coalesce(jsonb_agg(to_jsonb(co)),     '[]'::jsonb) from co),
    'documents', (select coalesce(jsonb_agg(to_jsonb(docs)),   '[]'::jsonb) from docs),
    'claims',    (select coalesce(jsonb_agg(to_jsonb(cl)),     '[]'::jsonb) from cl),
    'hiring',    (select coalesce(jsonb_agg(to_jsonb(hiring)), '[]'::jsonb) from hiring)
  );
$function$;
revoke all on function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) from public, anon, authenticated;
grant execute on function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) to service_role;

-- -----------------------------------------------------------------------------
-- 4. mi.fact: claim branch reads claim_current. Column list and order are unchanged.
-- -----------------------------------------------------------------------------
create or replace view mi.fact
with (security_invoker = on) as
 SELECT 'event'::text AS fact_type,
    e.id AS fact_id,
    e.id AS occasion_event_id,
    mi.lens_of(e.kind, e.source, NULL::text) AS lens,
    e.kind,
    e.signal_type,
    NULL::text AS lane,
    NULLIF(split_part(COALESCE(e.source, ''::text), ':'::text, 1), ''::text) AS source_system,
    COALESCE(e.url, e.notion_page_id, e.id::text) AS source_ref,
        CASE
            WHEN e.source ~~ 'inbox_miner%'::text THEN 'email_signal'::text
            WHEN e.kind = 'attended'::text THEN 'first_hand'::text
            WHEN e.kind = ANY (ARRAY['market'::text, 'funding'::text, 'launch'::text, 'exec_move'::text, 'role_posted'::text, 'application'::text, 'interview'::text]) THEN 'web_verified'::text
            ELSE 'reference'::text
        END AS provenance_tier,
    e.event_date AS asserted_at,
    date_trunc('week'::text, (e.event_date AT TIME ZONE 'UTC'::text))::date AS asserted_week,
    e.created_at AS observed_at
   FROM public.event e
UNION ALL
 SELECT 'claim'::text AS fact_type,
    c.id AS fact_id,
    c.event_id AS occasion_event_id,
    mi.lens_of(oe.kind, oe.source, c.lane) AS lens,
    oe.kind,
    NULL::text AS signal_type,
    c.lane,
    'substrate'::text AS source_system,
    COALESCE(c.document_id::text, c.source_key) AS source_ref,
    c.provenance_tier,
    c.asserted_at,
    date_trunc('week'::text, (c.asserted_at AT TIME ZONE 'UTC'::text))::date AS asserted_week,
    c.created_at AS observed_at
   FROM public.claim_current c
     LEFT JOIN public.event oe ON oe.id = c.event_id
  WHERE c.status <> 'rejected'::text
    AND NOT c.is_retired;

commit;

-- =============================================================================
-- PREFLIGHT (read-only; supabase/scripts/0024_preflight_dashboard.sql is this block). Expect
-- prereq_0023 = true, old_match_claims_shape = true, and note the three baseline_* counts: VERIFY's
-- info rows must equal them after the paste.
-- =============================================================================
-- PREFLIGHT:BEGIN
-- select 'prereq_0023' as check_name, (to_regclass('public.claim_current') is not null and exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'claim' and column_name = 'rank'))::text as detail
-- union all
-- select 'old_match_claims_shape', (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is not null and to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])') is null)::text
-- union all
-- select 'nothing_retired_yet', (not exists (select 1 from public.claim c where c.rank = 'deprecated' or (c.valid_to is not null and c.valid_to <= now())) and not exists (select 1 from public.claim_verification where outcome = 'contradicted'))::text
-- union all
-- select 'baseline_mi_fact_claim_rows', (select count(*) from mi.fact where fact_type = 'claim')::text
-- union all
-- select 'baseline_mi_fact_rows', (select count(*) from mi.fact)::text
-- union all
-- select 'baseline_live_claims', (select count(*) from public.claim where status in ('approved', 'candidate'))::text;
-- PREFLIGHT:END

-- =============================================================================
-- VERIFY (read-only). Every non-info row must read true. *_at_apply rows hold only while nothing is
-- retired (right after the paste); info_* rows are printed, never gating.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'claim_current_is_retired_col', (select string_agg(column_name, ',' order by ordinal_position) from information_schema.columns where table_schema = 'public' and table_name = 'claim_current' and ordinal_position > (select count(*) from information_schema.columns where table_schema = 'public' and table_name = 'claim')) = 'last_check_outcome,last_checked_at,is_current,is_overdue,is_retired';
-- select 'keep_claim_current_invoker_no_api', (select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'public.claim_current'::regclass) and not has_table_privilege('anon', 'public.claim_current', 'select') and not has_table_privilege('authenticated', 'public.claim_current', 'select') and has_table_privilege('service_role', 'public.claim_current', 'select');
-- select 'match_claims_new_shape_only', to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])') is not null and to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[])') is null;
-- select 'match_claims_reads_claim_current', (select prosrc ~ 'from public\.claim_current c' and prosrc ~ 'not c\.is_retired' and prosrc ~ 'filter_visibility is null or c\.visibility = any\(filter_visibility\)' and prosrc !~ 'from public\.claim c' from pg_proc where oid = to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])'));
-- select 'match_claims_out_columns', (select array_to_string(proargnames[array_length(proargnames, 1) - 3:array_length(proargnames, 1)], ',') = 'review_flag,last_check_outcome,is_overdue,visibility' from pg_proc where oid = to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])'));
-- select 'entity_neighborhood_reads_claim_current', (select prosrc ~ 'from public\.claim_current c' and prosrc ~ 'not c\.is_retired' and prosrc ~ 'c\.review_flag, c\.last_check_outcome, c\.is_overdue, c\.visibility' and prosrc !~ 'from public\.claim c' from pg_proc where oid = to_regprocedure('public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)'));
-- select 'functions_exec_service_role_only', (select bool_and(has_function_privilege('service_role', f, 'execute') and not has_function_privilege('anon', f, 'execute') and not has_function_privilege('authenticated', f, 'execute')) from unnest(array['public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])', 'public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)']) f);
-- select 'functions_invoker_search_path', (select count(*) = 2 and bool_and(not prosecdef and proconfig is not distinct from array['search_path=public']) from pg_proc where oid in (to_regprocedure('public.match_claims_hybrid(vector,text,integer,integer,integer,uuid[],text[],text[],text[])'), to_regprocedure('public.entity_neighborhood(uuid[],timestamp with time zone,integer,integer,integer)')));
-- select 'mi_fact_reads_claim_current', (select pg_get_viewdef('mi.fact'::regclass, true) ~ 'FROM claim_current c' and pg_get_viewdef('mi.fact'::regclass, true) ~ 'NOT c\.is_retired');
-- select 'keep_mi_fact_invoker', (select coalesce('security_invoker=on' = any(reloptions), false) from pg_class where oid = 'mi.fact'::regclass);
-- select 'keep_mi_fact_columns', (select string_agg(attname, ',' order by attnum) = 'fact_type,fact_id,occasion_event_id,lens,kind,signal_type,lane,source_system,source_ref,provenance_tier,asserted_at,asserted_week,observed_at' from pg_attribute where attrelid = 'mi.fact'::regclass and attnum > 0 and not attisdropped);
-- select 'keep_mi_dependents', to_regclass('mi.fact_company') is not null and to_regclass('mi.fact_topic') is not null;
-- select 'keep_mi_fact_claims_unchanged_at_apply', (select count(*) from mi.fact where fact_type = 'claim') = (select count(*) from public.claim where status <> 'rejected');
-- select 'nothing_retired_at_apply', not exists (select 1 from public.claim_current where is_retired);
-- select 'info_mi_fact_claim_rows', (select count(*) from mi.fact where fact_type = 'claim')::text;
-- select 'info_mi_fact_rows', (select count(*) from mi.fact)::text;
-- select 'info_live_claims', (select count(*) from public.claim_current where status in ('approved', 'candidate') and not is_retired)::text;
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (uncomment to run). Restores the 0010 / 0011 / 0016 / 0023 bodies, return shapes and the
-- pre-0024 EXECUTE grants (public, anon, authenticated, service_role) byte for byte (revoke-all then
-- grant in the original order: a re-granted aclitem is appended, so grant alone reorders the ACL). It cannot
-- restore claim_current to the 0023 column list with CREATE OR REPLACE (a column cannot be removed
-- that way), so it drops and recreates the view; it FAILS LOUD if anything else has come to depend on
-- claim_current. Before rolling back with retired claims present, note that the old readers will
-- count them again.
--
-- ROLLBACK:BEGIN
-- begin;
-- set local lock_timeout = '5s';
-- drop function if exists public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[], text[]);
-- create or replace function public.match_claims_hybrid(query_embedding vector, query_text text, match_count integer DEFAULT 20, candidate_n integer DEFAULT 40, rrf_k integer DEFAULT 60, filter_entity_ids uuid[] DEFAULT NULL::uuid[], filter_statuses text[] DEFAULT ARRAY['approved'::text, 'candidate'::text], filter_tiers text[] DEFAULT NULL::text[])
--  returns table(id uuid, claim_text text, claim_type text, quote text, locator jsonb, provenance_tier text, confidence numeric, status text, metadata jsonb, document_id uuid, event_id uuid, asserted_at timestamp with time zone, dense_rank integer, keyword_rank integer, rrf_score double precision)
--  language sql
--  stable
--  set search_path to 'public'
-- as $function$
--   with base as (
--     select c.*
--     from public.claim c
--     where c.status = any(filter_statuses)
--       and (filter_tiers is null or c.provenance_tier = any(filter_tiers))
--       and (filter_entity_ids is null
--            or exists (select 1 from public.claim_entity ce
--                       where ce.claim_id = c.id and ce.entity_id = any(filter_entity_ids))
--            or exists (select 1 from public.event_entity ee
--                       where ee.event_id = c.event_id and ee.entity_id = any(filter_entity_ids)))
--   ),
--   dense as (
--     select id, row_number() over (order by embedding <=> query_embedding) as r
--     from base where embedding is not null
--     order by embedding <=> query_embedding limit candidate_n
--   ),
--   kw as (
--     select id, row_number() over (order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc) as r
--     from base where tsv @@ websearch_to_tsquery('english', query_text)
--     order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc limit candidate_n
--   ),
--   fused as (
--     select coalesce(d.id, k.id) as id, d.r as dr, k.r as kr,
--            coalesce(1.0 / (rrf_k + d.r), 0) + coalesce(1.0 / (rrf_k + k.r), 0) as score
--     from dense d full outer join kw k on d.id = k.id
--   )
--   select b.id, b.claim_text, b.claim_type, b.quote, b.locator, b.provenance_tier, b.confidence,
--          b.status, b.metadata, b.document_id, b.event_id, b.asserted_at,
--          f.dr::integer, f.kr::integer, f.score::float
--   from fused f join base b on b.id = f.id
--   order by f.score desc, b.asserted_at desc nulls last
--   limit match_count;
-- $function$;
-- revoke all on function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[]) from public, postgres, anon, authenticated, service_role;
-- grant execute on function public.match_claims_hybrid(vector, text, integer, integer, integer, uuid[], text[], text[]) to public, postgres, anon, authenticated, service_role;
-- create or replace function public.entity_neighborhood(seed_ids uuid[], since timestamp with time zone DEFAULT NULL::timestamp with time zone, max_events integer DEFAULT 60, max_claims integer DEFAULT 120, max_docs integer DEFAULT 40)
--  returns jsonb
--  language sql
--  stable
--  set search_path to 'public'
-- as $function$
--   with ev as (
--     select distinct e.id, e.title, e.kind, e.event_date, e.source, e.url, e.confidence
--     from public.event e join public.event_entity ee on ee.event_id = e.id
--     where ee.entity_id = any(seed_ids) and (since is null or e.event_date >= since)
--       and e.kind <> all (array['role_posted', 'application', 'interview'])
--     order by e.event_date desc nulls last limit max_events
--   ),
--   co as (
--     select ee.event_id, ee.entity_type, ee.entity_id, ee.role,
--            coalesce(c.name, p.name, t.name) as name
--     from public.event_entity ee
--     left join public.company c on c.id = ee.entity_id and ee.entity_type = 'company'
--     left join public.person  p on p.id = ee.entity_id and ee.entity_type = 'person'
--     left join public.topic   t on t.id = ee.entity_id and ee.entity_type = 'topic'
--     where ee.event_id in (select id from ev)
--   ),
--   docs as (
--     select distinct d.id, d.title, d.source_type, d.doc_date, d.external_ref, d.event_id
--     from public.documents d
--     left join public.document_entity de on de.document_id = d.id
--     where d.is_current and (de.entity_id = any(seed_ids) or d.event_id in (select id from ev))
--     order by d.doc_date desc nulls last limit max_docs
--   ),
--   cl as (
--     select distinct c.id, c.claim_text, c.claim_type, c.provenance_tier, c.confidence, c.status,
--            c.event_id, c.document_id, c.asserted_at, c.metadata
--     from public.claim c
--     left join public.claim_entity ce on ce.claim_id = c.id
--     where c.status in ('approved', 'candidate')
--       and (ce.entity_id = any(seed_ids) or c.event_id in (select id from ev))
--     order by c.asserted_at desc nulls last limit max_claims
--   ),
--   hiring as (
--     select c.id as company_id, c.name, count(distinct e.id) as roles,
--            count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'A') as tier_a,
--            count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'B') as tier_b,
--            count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'C') as tier_c,
--            max(e.event_date) as latest_posted
--     from public.event e
--     join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
--     join public.company c on c.id = ee.entity_id
--     where ee.entity_id = any(seed_ids) and e.kind = 'role_posted'
--       and coalesce(e.metadata->>'status', '') <> 'archived'   -- archived in Notion = closed or not pursued
--     group by c.id, c.name
--   )
--   select jsonb_build_object(
--     'events',    (select coalesce(jsonb_agg(to_jsonb(ev)),     '[]'::jsonb) from ev),
--     'edges',     (select coalesce(jsonb_agg(to_jsonb(co)),     '[]'::jsonb) from co),
--     'documents', (select coalesce(jsonb_agg(to_jsonb(docs)),   '[]'::jsonb) from docs),
--     'claims',    (select coalesce(jsonb_agg(to_jsonb(cl)),     '[]'::jsonb) from cl),
--     'hiring',    (select coalesce(jsonb_agg(to_jsonb(hiring)), '[]'::jsonb) from hiring)
--   );
-- $function$;
-- revoke all on function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) from public, postgres, anon, authenticated, service_role;
-- grant execute on function public.entity_neighborhood(uuid[], timestamp with time zone, integer, integer, integer) to public, postgres, anon, authenticated, service_role;
-- create or replace view mi.fact with (security_invoker = on) as
--  SELECT 'event'::text AS fact_type, e.id AS fact_id, e.id AS occasion_event_id, mi.lens_of(e.kind, e.source, NULL::text) AS lens, e.kind, e.signal_type, NULL::text AS lane, NULLIF(split_part(COALESCE(e.source, ''::text), ':'::text, 1), ''::text) AS source_system, COALESCE(e.url, e.notion_page_id, e.id::text) AS source_ref,
--         CASE WHEN e.source ~~ 'inbox_miner%'::text THEN 'email_signal'::text WHEN e.kind = 'attended'::text THEN 'first_hand'::text WHEN e.kind = ANY (ARRAY['market'::text, 'funding'::text, 'launch'::text, 'exec_move'::text, 'role_posted'::text, 'application'::text, 'interview'::text]) THEN 'web_verified'::text ELSE 'reference'::text END AS provenance_tier,
--     e.event_date AS asserted_at, date_trunc('week'::text, (e.event_date AT TIME ZONE 'UTC'::text))::date AS asserted_week, e.created_at AS observed_at
--    FROM public.event e
-- UNION ALL
--  SELECT 'claim'::text AS fact_type, c.id AS fact_id, c.event_id AS occasion_event_id, mi.lens_of(oe.kind, oe.source, c.lane) AS lens, oe.kind, NULL::text AS signal_type, c.lane, 'substrate'::text AS source_system, COALESCE(c.document_id::text, c.source_key) AS source_ref, c.provenance_tier, c.asserted_at, date_trunc('week'::text, (c.asserted_at AT TIME ZONE 'UTC'::text))::date AS asserted_week, c.created_at AS observed_at
--    FROM public.claim c LEFT JOIN public.event oe ON oe.id = c.event_id
--   WHERE c.status <> 'rejected'::text;
-- drop view public.claim_current;
-- create view public.claim_current with (security_invoker = on) as
-- select c.*,
--        v.outcome     as last_check_outcome,
--        v.checked_at  as last_checked_at,
--        (c.status <> 'rejected'
--         and c.rank <> 'deprecated'
--         and (c.valid_to is null or c.valid_to > now())
--         and v.outcome is distinct from 'contradicted')                       as is_current,
--        (c.next_check_at is not null and c.next_check_at <= now())           as is_overdue
--   from public.claim c
--   left join lateral (
--     select cv.outcome, cv.checked_at
--       from public.claim_verification cv
--      where cv.claim_id = c.id
--      order by cv.checked_at desc, cv.id desc
--      limit 1) v on true;
-- comment on view public.claim_current is
--   '0023 (ADR-15 d7/d8): claim + latest verification; is_current drops rejected, deprecated, expired and '
--   'last-contradicted claims; is_overdue = next_check_at passed. 0024 moves match_claims_hybrid, entity_neighborhood and mi.fact onto it.';
-- revoke all on public.claim_current from public, anon, authenticated;
-- commit;
-- ROLLBACK:END
-- =============================================================================
