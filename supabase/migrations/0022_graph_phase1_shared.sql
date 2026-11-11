-- =============================================================================
-- 0022 · Knowledge-graph phase 1, shared schema (ADR-14 discovery loop + graph review B0/B5)
-- Linear: YED-384 · Design: discovery-loop-design.md §3 ("0021" table, renumbered 0022) and
-- graph-review-fable.md B0 / B5 / §2.4 item 4 ("0021 shared with ADR-14").
--
-- NOT APPLIED. Twin rehearsal (supabase/scripts/rehearse_0022.py) + Alex dashboard apply
-- required (CLAUDE.md invariant 2). ADDITIVE ONLY: no column, row or index is dropped or renamed.
--
-- ORDER. Written to apply cleanly after 0020 (feed_items, PR #305) and 0021 (company_signals
-- registry text, PR #314), and equally cleanly before them: 0022 creates, reads and checks NO
-- object either of them creates or changes (no feed_items reference; the company_signals row is
-- not touched). One coupling to know: 0018's and 0021's VERIFY blocks assert
-- `count(*) = 6` on lane_registry, so run THEIR verify before pasting 0022 (after it the count
-- is 10). 0021's header names a "FOLLOW-UP 0022" (flip company_signals active): that follow-up
-- now needs the next free number.
--
-- WHAT (seven parts, one transaction):
--   1. event.kind += 'researched' (B0): one occasion row per researched-not-attended event, so the
--      ~4,948 stranded research claims can carry an event_id. mi.lens_of() gains ONE line so a
--      researched occasion lenses to NULL at event level (it was 'research' through the
--      'substrate:research%' source rule) and never 'attended'. Claims keep their lens by lane:
--      lens_of('researched', 'substrate:research', 'research') is still 'research'.
--   2. claim.use_count / last_used_at maintained by a trigger on claim_usage (ADR-14 §3). It
--      RECOMPUTES from claim_usage for the affected claim(s) on insert, delete and claim_id/used_at
--      update (level-triggered, so a delete or an upsert can't drift the count), then a one-time
--      backfill from the 1,282 existing rows. No producer may set these columns (spine_client
--      ALLOW leaves them out, ADR-10 D5); the DB is now their only writer. Nothing ranks on them
--      until >= 20 outcome rows exist (ADR-10 D5, unchanged).
--   3. Identity (S1b DDL half, ADR-10 D5 re-trigger met by the discovery loop as the second
--      producer): public.norm_name(), name_norm UNIQUE expression indexes on company and topic,
--      a NON-unique (name_norm, company_id) index on person (people share names, ADR-4), and
--      public.entity_alias. Expression indexes, not generated columns: no table rewrite, no new
--      column on person (the PII-guarded table), and load_twin.py's select=* -> COPY keeps working.
--      Prod probe 2026-11-11 (GET-only, spine_client.req): 0 norm collisions in 426 companies and
--      317 topics, tombstones included -> the unique indexes ship unique. Person: 1 collision pair
--      (one side a merge tombstone) -> non-unique, as the plan already says.
--      The old lower(name) unique indexes STAY (additive; retiring them is a later, separate call).
--   4. public.sweep_query: the discovery loop's query ledger (one row per issued query per ISO
--      week; yield counters filled by the run).
--   5. CHECK widenings: claim_usage.consumer += 'brief', 'published'; claim_relation.method += 'llm'.
--   6. lane_registry rows theme_sweep, claim_review, notion_prior, reconcile, all active = false
--      (each producer PR flips its own, 0018's shape).
--   7. Security: both new tables RLS on, no policies, every privilege revoked from public / anon /
--      authenticated (0020's pattern; 0019 Part 2 still leaves new tables a default anon SELECT, so
--      the REVOKE is the read control). service_role (spine_client) keeps its grants. The two new
--      functions lose EXECUTE for public / anon / authenticated (the postgres default ACL grants it).
--
-- NOT HERE, deliberately: dropping doc_claims (graph review §2.5; not additive, own migration);
-- entity_merge (not needed while soft-merge lives in metadata); re-describing the feeds /
-- company_signals schedules as "bridge routine" (0021 owns company_signals' text); the other
-- graph-review lane rows (pre_event_research, post_event_claims, transcripts, posts).
--
-- RE-RUNNABLE: every statement is guarded (if not exists / or replace / drop-if-exists + add /
-- on conflict do nothing / idempotent backfill / no-op REVOKE). A second paste changes nothing.
--
-- APPLY (Alex, prod dashboard): paste OUTSIDE the 07:00-09:00 UTC nightly window.
-- lock_timeout is 5s: a busy table fails the paste instead of queueing; just re-paste.
-- If a CREATE UNIQUE INDEX fails, a name collision appeared since 2026-11-11: STOP, run the
-- PREFLIGHT query in the runbook, merge the pair (substrate.py merge), re-paste.
-- =============================================================================

begin;
set local lock_timeout = '5s';

-- -----------------------------------------------------------------------------
-- 1. event.kind += 'researched'; lens_of: a researched occasion is unlensed at event level.
-- -----------------------------------------------------------------------------
alter table public.event drop constraint if exists event_kind_enum;
alter table public.event add constraint event_kind_enum check (kind in (
  'attended', 'market', 'funding', 'launch', 'exec_move',
  'role_posted', 'application', 'interview',
  'reference',
  'published',
  'researched'     -- NEW (B0): researched, not (yet) attended; promoted in place to 'attended' on evidence
));

-- 0016's body plus the one 'researched' line, placed after the job rule (job isolation still wins
-- first) and before the research rule (which would otherwise lens the occasion row 'research' via
-- its 'substrate:research' source). p_lane is null only for event-level facts (mi.fact passes
-- null for events), so research claims hung on a researched event keep their 'research' lens.
create or replace function mi.lens_of(p_kind text, p_source text, p_lane text)
returns text
language sql
immutable
set search_path = pg_catalog, pg_temp
as $fn$
  select case
    when p_kind in ('role_posted', 'application', 'interview')          then 'job'
    when p_kind = 'researched' and p_lane is null                        then null
    when p_lane = 'research' or p_source like 'substrate:research%'      then 'research'
    when p_kind = 'attended'                                             then 'attended'
    when p_kind in ('market', 'funding', 'launch', 'exec_move')          then 'market'
    else null
  end
$fn$;
revoke all on function mi.lens_of(text, text, text) from public;

-- -----------------------------------------------------------------------------
-- 2. claim.use_count / last_used_at, DB-maintained from claim_usage.
-- -----------------------------------------------------------------------------
create or replace function public.claim_usage_sync_use_count()
returns trigger
language plpgsql
set search_path = pg_catalog, pg_temp
as $fn$
declare
  ids uuid[];
begin
  if tg_op = 'INSERT' then
    ids := array[new.claim_id];
  elsif tg_op = 'DELETE' then
    ids := array[old.claim_id];
  else
    ids := array[old.claim_id, new.claim_id];
  end if;
  -- Recompute, never increment: the count is whatever claim_usage says, so a delete, an upsert
  -- or a moved row can't leave it wrong. Indexed by claim_usage_claim_idx (0009).
  update public.claim c
     set use_count    = u.n,
         last_used_at = u.last_used
    from (select i.id,
                 (select count(*)::integer from public.claim_usage cu where cu.claim_id = i.id) as n,
                 (select max(cu.used_at)   from public.claim_usage cu where cu.claim_id = i.id) as last_used
            from unnest(ids) as i(id)) u
   where c.id = u.id
     and (c.use_count is distinct from u.n or c.last_used_at is distinct from u.last_used);
  return null;
end
$fn$;
revoke all on function public.claim_usage_sync_use_count() from public, anon, authenticated;

create or replace trigger claim_usage_sync_use_count
  after insert or delete or update of claim_id, used_at on public.claim_usage
  for each row execute function public.claim_usage_sync_use_count();

comment on function public.claim_usage_sync_use_count() is
  '0022 (ADR-14 §3): keeps claim.use_count / last_used_at equal to count(*) / max(used_at) over '
  'claim_usage for the claim. The only writer of those two columns (spine_client ALLOW excludes them).';

-- One-time backfill (idempotent: touches only rows that differ; a re-paste updates 0 rows).
update public.claim c
   set use_count    = coalesce(u.n, 0),
       last_used_at = u.last_used
  from public.claim c2
  left join (select claim_id, count(*)::integer as n, max(used_at) as last_used
               from public.claim_usage group by claim_id) u on u.claim_id = c2.id
 where c.id = c2.id
   and (c.use_count is distinct from coalesce(u.n, 0) or c.last_used_at is distinct from u.last_used);

-- -----------------------------------------------------------------------------
-- 3. Identity: norm_name(), name_norm indexes, entity_alias.
-- -----------------------------------------------------------------------------
-- Spec: knowledge-substrate-architecture-2026-09-18 §identity (S1b). Lowercase, drop legal
-- suffixes as whole words, collapse non-alphanumerics to one space, trim; empty -> NULL.
create or replace function public.norm_name(t text)
returns text
language sql
immutable
parallel safe
set search_path = pg_catalog, pg_temp
as $fn$
  select nullif(trim(regexp_replace(
           regexp_replace(lower(coalesce(t, '')),
             '\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\M\.?', '', 'g'),
           '[^a-z0-9]+', ' ', 'g')), '')
$fn$;
revoke all on function public.norm_name(text) from public, anon, authenticated;
comment on function public.norm_name(text) is
  '0022 (S1b): the canonical name normalizer behind the name_norm indexes and entity_alias.alias_norm.';

create unique index if not exists company_name_norm_uq on public.company (public.norm_name(name));
create unique index if not exists topic_name_norm_uq   on public.topic   (public.norm_name(name));
create index if not exists person_name_norm_company_idx on public.person (public.norm_name(name), company_id);

create table if not exists public.entity_alias (
  id           uuid primary key default gen_random_uuid(),
  entity_type  text not null check (entity_type in ('company', 'person', 'topic')),
  entity_id    uuid not null,                     -- polymorphic, like claim_entity (no FK)
  alias        text not null check (char_length(alias) between 1 and 200),
  alias_norm   text generated always as (public.norm_name(alias)) stored,
  source       text not null check (source ~ '^[a-z][a-z0-9_:.-]{1,59}$'),   -- notion | sweep | ats | merge | manual ...
  confidence   numeric not null default 1.0 check (confidence >= 0 and confidence <= 1),
  created_at   timestamptz not null default now(),
  constraint entity_alias_norm_present check (alias_norm is not null)
);
-- One alias spelling resolves to one entity per type (spec). An ambiguous spelling is the
-- writer's to surface, never a second row.
create unique index if not exists entity_alias_type_norm_uq on public.entity_alias (entity_type, alias_norm);
create index if not exists entity_alias_entity_idx on public.entity_alias (entity_type, entity_id);

comment on table public.entity_alias is
  '0022 (S1b / ADR-14): other names an entity is known by. Resolution order: name_norm -> alias_norm '
  '-> candidates shown to a human -> create. Written only via spine_client (ADR-9); never contact PII.';

-- -----------------------------------------------------------------------------
-- 4. sweep_query: the discovery-loop query ledger (ADR-14 §2, §3).
-- -----------------------------------------------------------------------------
create table if not exists public.sweep_query (
  query_id        uuid primary key default gen_random_uuid(),
  kind            text not null check (kind in ('velocity', 'gap', 'event', 'entity', 'room_topic',
                                                'room_entity', 'open_question', 'room_vs_market')),
  theme_id        uuid references topic_intelligence.topic_cluster(cluster_id) on delete set null,
  template        text not null check (char_length(template) between 1 and 500),   -- the query text the parent wrote; never page text
  seed_event_id   uuid references public.event(id) on delete set null,            -- the event that raised it (room_* / event kinds)
  seed_claim_id   uuid references public.claim(id) on delete set null,            -- the claim that raised it (open_question)
  iso_week        text not null check (iso_week ~ '^[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$'),
  lane_run_id     uuid references public.lane_run(run_id) on delete set null,
  status          text not null default 'open' check (status in ('open', 'ran', 'failed', 'closed')),
  items_returned  integer not null default 0 check (items_returned >= 0),
  items_written   integer not null default 0 check (items_written  >= 0),
  items_used      integer not null default 0 check (items_used     >= 0),
  searches        integer not null default 0 check (searches       >= 0),
  created_at      timestamptz not null default now(),                               -- design doc: issued_at
  last_run_at     timestamptz,
  -- Re-issuing the same query in the same week is an upsert, not a second row. NULLS NOT DISTINCT
  -- so theme-less (entity / event) queries dedup too (PG 15+; prod is 17.6).
  constraint sweep_query_issue_uq unique nulls not distinct (kind, theme_id, template, iso_week)
);
create index if not exists sweep_query_theme_week_idx on public.sweep_query (theme_id, iso_week);
create index if not exists sweep_query_seed_event_idx on public.sweep_query (seed_event_id) where seed_event_id is not null;

comment on table public.sweep_query is
  '0022 (ADR-14 §3): one row per discovery-loop query per ISO week, with its yield. seed_event_id / '
  'seed_claim_id tie a query to what raised it, so seed yield is a join. Written only via spine_client.';

-- -----------------------------------------------------------------------------
-- 5. CHECK widenings (re-validate existing rows; widening cannot fail on them).
-- -----------------------------------------------------------------------------
alter table public.claim_usage drop constraint if exists claim_usage_consumer_check;
alter table public.claim_usage add constraint claim_usage_consumer_check
  check (consumer in ('event', 'content', 'job', 'ideation', 'dev', 'brief', 'published'));

alter table public.claim_relation drop constraint if exists claim_relation_method_check;
alter table public.claim_relation add constraint claim_relation_method_check
  check (method in ('human', 'embedding', 'rule', 'llm'));

-- -----------------------------------------------------------------------------
-- 6. lane_registry: four new lanes, inactive (producers cannot write the registry; ADR-13).
-- -----------------------------------------------------------------------------
insert into public.lane_registry
  (lane, schedule, owner, consumer, kill_rule, active, freshness_flag_days, freshness_fail_days)
values
  ('theme_sweep',
   'daily 05:30 ET top-5 themes + weekly all themes Fri-Sun; bridge routine',
   'alex', 'Q1-Q3; Monday Market Brief; pre-event pack Market block',
   'items_written = 0 for 3 runs -> FAIL; precision < 0.6 on 2 consecutive checks -> pause; used fraction 0 for 4 briefs -> stop; > 600 searches/week -> top-3 themes, > 2 weeks shrunk -> decision issue',
   false, 2, 4),
  ('claim_review',
   'nightly sweep + on ingest after each stage-* verb; bridge routine',
   'alex', 'room-vs-web line of the Monday Market Brief; superseded filter in retrieve.py',
   'adjudicator precision < 0.6 -> embedding-only mode; contradicts > 20/week -> raise the confidence bar to 0.85 and report',
   false, 2, 4),
  ('notion_prior',
   'weekly Sunday routine (Notion connector), watermarked on last_edited_time + comment created_time',
   'alex', 'prior bank; human claim relations from review comments',
   'freshness FAIL at 21 days',
   false, 10, 21),
  ('reconcile',
   'nightly on the Mac mini: substrate.py reconcile --queue (--apply after two dry-run nights)',
   'alex', 'weekly Graph Health page; completeness ledger',
   'attended-with-claims share drops week over week -> FAIL; a gap class older than 7 days -> one Linear issue per class',
   false, 2, 4)
on conflict (lane) do nothing;

-- -----------------------------------------------------------------------------
-- 7. Security for the new tables (0020 pattern).
-- -----------------------------------------------------------------------------
alter table public.entity_alias enable row level security;
alter table public.sweep_query  enable row level security;
revoke all on public.entity_alias from public, anon, authenticated;
revoke all on public.sweep_query  from public, anon, authenticated;

commit;

-- =============================================================================
-- VERIFY (read-only). Run with psql in a READ-ONLY session per the twin-rehearsal runbook (the
-- dashboard SQL editor shows only the last result). Each statement returns <check> | <t/f>;
-- every row must be t. keep_* rows guard what 0022 must NOT break (they pass before and after);
-- info_* rows are printed, never gating.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'event_kind_researched', (select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''attended''::text, ''market''::text, ''funding''::text, ''launch''::text, ''exec_move''::text, ''role_posted''::text, ''application''::text, ''interview''::text, ''reference''::text, ''published''::text, ''researched''::text])))' from pg_constraint where conrelid = 'public.event'::regclass and conname = 'event_kind_enum');
-- select 'lens_of_researched_null', mi.lens_of('researched', null, null) is null and mi.lens_of('researched', 'substrate:research', null) is null and mi.lens_of('researched', 'substrate:research', 'research') = 'research' and coalesce(mi.lens_of('researched', null, 'A'), '') <> 'attended';
-- select 'keep_lens_of_0016_truth_table', mi.lens_of('attended', null, null) = 'attended' and mi.lens_of('attended', null, 'research') = 'research' and mi.lens_of('role_posted', 'substrate:research', 'research') = 'job' and mi.lens_of('funding', 'akta', null) = 'market' and mi.lens_of(null, 'substrate:research', null) = 'research' and mi.lens_of('published', null, null) is null and mi.lens_of(null, null, 'A') is null;
-- select 'keep_lens_of_immutable_no_api_exec', (select provolatile = 'i' from pg_proc where oid = 'mi.lens_of(text,text,text)'::regprocedure) and not has_function_privilege('anon', 'mi.lens_of(text,text,text)', 'execute');
-- select 'use_count_trigger_present', exists (select 1 from pg_trigger where tgrelid = 'public.claim_usage'::regclass and tgname = 'claim_usage_sync_use_count' and tgenabled = 'O' and tgfoid = 'public.claim_usage_sync_use_count()'::regprocedure and (tgtype & 1) = 1 and (tgtype & 4) = 4 and (tgtype & 8) = 8 and (tgtype & 16) = 16);
-- select 'use_count_fn_invoker_no_api_exec', (select not prosecdef and proconfig = array['search_path=pg_catalog, pg_temp'] from pg_proc where oid = 'public.claim_usage_sync_use_count()'::regprocedure) and not has_function_privilege('anon', 'public.claim_usage_sync_use_count()', 'execute') and not has_function_privilege('authenticated', 'public.claim_usage_sync_use_count()', 'execute');
-- select 'use_count_matches_usage', (select count(*) > 0 from public.claim_usage) and not exists (select 1 from public.claim c left join (select claim_id, count(*) as n, max(used_at) as l from public.claim_usage group by claim_id) u on u.claim_id = c.id where c.use_count <> coalesce(u.n, 0) or c.last_used_at is distinct from u.l);
-- select 'claim_usage_consumer_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((consumer = ANY (ARRAY[''event''::text, ''content''::text, ''job''::text, ''ideation''::text, ''dev''::text, ''brief''::text, ''published''::text])))' from pg_constraint where conrelid = 'public.claim_usage'::regclass and conname = 'claim_usage_consumer_check');
-- select 'claim_relation_method_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((method = ANY (ARRAY[''human''::text, ''embedding''::text, ''rule''::text, ''llm''::text])))' from pg_constraint where conrelid = 'public.claim_relation'::regclass and conname = 'claim_relation_method_check');
-- select 'norm_name_behaviour', (select provolatile = 'i' from pg_proc where oid = 'public.norm_name(text)'::regprocedure) and public.norm_name('Acme, Inc.') = 'acme' and public.norm_name('LangChain Inc') = 'langchain' and public.norm_name('  Zed (AI) ') = 'zed ai' and public.norm_name('Inc.') is null and not has_function_privilege('anon', 'public.norm_name(text)', 'execute') and not has_function_privilege('authenticated', 'public.norm_name(text)', 'execute');
-- select 'company_name_norm_unique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'company' and indexname = 'company_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX company_name_norm_uq ON public.company USING btree (norm_name(name))');
-- select 'topic_name_norm_unique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'topic' and indexname = 'topic_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX topic_name_norm_uq ON public.topic USING btree (norm_name(name))');
-- select 'person_name_norm_nonunique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'person' and indexname = 'person_name_norm_company_idx' and indexdef = 'CREATE INDEX person_name_norm_company_idx ON public.person USING btree (norm_name(name), company_id)');
-- select 'keep_lower_name_indexes', (select count(*) = 2 from pg_indexes where schemaname = 'public' and indexname in ('company_lower_idx', 'topic_lower_idx'));
-- select 'entity_alias_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'id,entity_type,entity_id,alias,alias_norm,source,confidence,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias');
-- select 'entity_alias_norm_generated', (select is_generated = 'ALWAYS' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias' and column_name = 'alias_norm');
-- select 'entity_alias_unique_norm', exists (select 1 from pg_indexes where schemaname = 'public' and indexname = 'entity_alias_type_norm_uq' and indexdef = 'CREATE UNIQUE INDEX entity_alias_type_norm_uq ON public.entity_alias USING btree (entity_type, alias_norm)');
-- select 'entity_alias_rls_on', (select relrowsecurity from pg_class where oid = 'public.entity_alias'::regclass);
-- select 'entity_alias_no_policies', to_regclass('public.entity_alias') is not null and not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'entity_alias');
-- select 'entity_alias_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.entity_alias', 'select') or has_table_privilege(r, 'public.entity_alias', 'insert') or has_table_privilege(r, 'public.entity_alias', 'update') or has_table_privilege(r, 'public.entity_alias', 'delete') or has_table_privilege(r, 'public.entity_alias', 'truncate') or has_table_privilege(r, 'public.entity_alias', 'references') or has_table_privilege(r, 'public.entity_alias', 'trigger') or has_table_privilege(r, 'public.entity_alias', 'maintain'));
-- select 'entity_alias_service_role_rw', has_table_privilege('service_role', 'public.entity_alias', 'select') and has_table_privilege('service_role', 'public.entity_alias', 'insert') and has_table_privilege('service_role', 'public.entity_alias', 'update') and has_table_privilege('service_role', 'public.entity_alias', 'delete');
-- select 'sweep_query_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'query_id,kind,theme_id,template,seed_event_id,seed_claim_id,iso_week,lane_run_id,status,items_returned,items_written,items_used,searches,created_at,last_run_at' from information_schema.columns where table_schema = 'public' and table_name = 'sweep_query');
-- select 'sweep_query_kind_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''velocity''::text, ''gap''::text, ''event''::text, ''entity''::text, ''room_topic''::text, ''room_entity''::text, ''open_question''::text, ''room_vs_market''::text])))' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_kind_check');
-- select 'sweep_query_issue_unique', (select pg_get_constraintdef(oid) = 'UNIQUE NULLS NOT DISTINCT (kind, theme_id, template, iso_week)' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_issue_uq');
-- select 'sweep_query_fks', (select count(*) = 4 from pg_constraint where conrelid = 'public.sweep_query'::regclass and contype = 'f' and confdeltype = 'n');
-- select 'sweep_query_rls_on', (select relrowsecurity from pg_class where oid = 'public.sweep_query'::regclass);
-- select 'sweep_query_no_policies', to_regclass('public.sweep_query') is not null and not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'sweep_query');
-- select 'sweep_query_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.sweep_query', 'select') or has_table_privilege(r, 'public.sweep_query', 'insert') or has_table_privilege(r, 'public.sweep_query', 'update') or has_table_privilege(r, 'public.sweep_query', 'delete') or has_table_privilege(r, 'public.sweep_query', 'truncate') or has_table_privilege(r, 'public.sweep_query', 'references') or has_table_privilege(r, 'public.sweep_query', 'trigger') or has_table_privilege(r, 'public.sweep_query', 'maintain'));
-- select 'sweep_query_service_role_rw', has_table_privilege('service_role', 'public.sweep_query', 'select') and has_table_privilege('service_role', 'public.sweep_query', 'insert') and has_table_privilege('service_role', 'public.sweep_query', 'update') and has_table_privilege('service_role', 'public.sweep_query', 'delete');
-- select 'new_tables_no_pii_columns', to_regclass('public.entity_alias') is not null and to_regclass('public.sweep_query') is not null and not exists (select 1 from information_schema.columns where table_schema = 'public' and table_name in ('entity_alias', 'sweep_query') and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)');
-- select 'lanes_0022_seeded_inactive', (select count(*) = 4 from public.lane_registry where not active and owner = 'alex' and ((lane = 'theme_sweep' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'daily 05:30 ET%') or (lane = 'claim_review' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'nightly sweep%') or (lane = 'notion_prior' and freshness_flag_days = 10 and freshness_fail_days = 21 and schedule like 'weekly Sunday%') or (lane = 'reconcile' and freshness_flag_days = 2 and freshness_fail_days = 4 and schedule like 'nightly on the Mac mini%')));
-- select 'keep_lanes_0016_present', (select count(*) = 6 from public.lane_registry where lane in ('corpus_mine', 'hiring_pulse', 'company_signals', 'research_frontier', 'feeds', 'segment_enrichment'));
-- select 'keep_registry_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.lane_registry', 'select') or has_table_privilege(r, 'public.lane_registry', 'insert') or has_table_privilege(r, 'public.lane_registry', 'update') or has_table_privilege(r, 'public.lane_registry', 'delete'));
-- select 'info_claim_usage_rows', (select count(*) from public.claim_usage)::text;
-- select 'info_claims_with_use_count', (select count(*) from public.claim where use_count > 0)::text;
-- select 'info_lane_registry_rows', (select count(*) from public.lane_registry)::text;
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (uncomment to run). Drops only what 0022 adds and restores the 0016 lens_of body and
-- the pre-0022 CHECKs byte for byte. It resets use_count / last_used_at to the pre-0022 state
-- (0 / null everywhere, recorded on prod 2026-11-11); claim_usage itself is untouched, so the
-- counts are re-derivable.
-- It FAILS LOUD, by design, if data already uses a new value: an event with kind 'researched', a
-- claim_usage row with consumer 'brief' / 'published', a claim_relation with method 'llm', or a
-- lane_run row on one of the four new lanes. Re-kind or remove those rows first; never weaken the
-- CHECKs to make the rollback pass.
--
-- ROLLBACK:BEGIN
-- begin;
-- set local lock_timeout = '5s';
-- drop trigger if exists claim_usage_sync_use_count on public.claim_usage;
-- drop function if exists public.claim_usage_sync_use_count();
-- update public.claim set use_count = 0, last_used_at = null where use_count <> 0 or last_used_at is not null;
-- drop table if exists public.sweep_query;
-- drop table if exists public.entity_alias;
-- drop index if exists public.company_name_norm_uq;
-- drop index if exists public.topic_name_norm_uq;
-- drop index if exists public.person_name_norm_company_idx;
-- drop function if exists public.norm_name(text);
-- delete from public.lane_registry where lane in ('theme_sweep', 'claim_review', 'notion_prior', 'reconcile');
-- alter table public.claim_relation drop constraint if exists claim_relation_method_check;
-- alter table public.claim_relation add constraint claim_relation_method_check check (method in ('human', 'embedding', 'rule'));
-- alter table public.claim_usage drop constraint if exists claim_usage_consumer_check;
-- alter table public.claim_usage add constraint claim_usage_consumer_check check (consumer in ('event', 'content', 'job', 'ideation', 'dev'));
-- alter table public.event drop constraint if exists event_kind_enum;
-- alter table public.event add constraint event_kind_enum check (kind in ('attended', 'market', 'funding', 'launch', 'exec_move', 'role_posted', 'application', 'interview', 'reference', 'published'));
-- create or replace function mi.lens_of(p_kind text, p_source text, p_lane text)
-- returns text
-- language sql
-- immutable
-- set search_path = pg_catalog, pg_temp
-- as $fn$
--   select case
--     when p_kind in ('role_posted', 'application', 'interview')          then 'job'
--     when p_lane = 'research' or p_source like 'substrate:research%'      then 'research'
--     when p_kind = 'attended'                                             then 'attended'
--     when p_kind in ('market', 'funding', 'launch', 'exec_move')          then 'market'
--     else null
--   end
-- $fn$;
-- revoke all on function mi.lens_of(text, text, text) from public;
-- commit;
-- ROLLBACK:END
-- =============================================================================
