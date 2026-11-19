-- =============================================================================
-- 0022 · Knowledge-graph phase 1, shared schema (ADR-14 discovery loop + graph review B0/B5)
-- Linear: YED-384 · Design: discovery-loop-design.md §3 ("0021" table, renumbered 0022) and
-- graph-review-fable.md B0 / B5 / §2.4 item 4 ("0021 shared with ADR-14").
--
-- NOT APPLIED. Twin rehearsal (supabase/scripts/rehearse_0022.py) + Alex dashboard apply
-- required (CLAUDE.md invariant 2). ADDITIVE ONLY: no column, row or index is dropped or renamed.
--
-- ORDER: APPLY 0021 FIRST (then 0022). 0022 creates, reads and checks no object 0020 or 0021
-- creates or changes (no feed_items reference; the company_signals row is not touched), so it is
-- technically independent. The order rule exists because 0018's and 0021's VERIFY blocks assert
-- `count(*) = 6` on lane_registry and 0022 makes it 10. 0021's header names a "FOLLOW-UP 0022"
-- (flip company_signals active): that follow-up needs the next free number.
--
-- WRITERS FIRST: the name_norm unique indexes turn a near-duplicate company/topic create into a
-- 409. substrate.py resolves by the same normalisation (norm_company / norm_plain, parity-tested
-- against these SQL functions on the twin) and re-resolves + reuses on a 409, so ship that
-- substrate.py change before (or with) this paste.
--
-- WHAT (one transaction):
--   1. event.kind += 'researched' (B0): one occasion row per researched-not-attended event, so the
--      ~4,948 stranded research claims can carry an event_id. mi.lens_of() gains ONE line so a
--      researched occasion lenses to NULL at event level (it was 'research' through the
--      'substrate:research%' source rule) and never 'attended'. Claims keep their lens by lane:
--      lens_of('researched', 'substrate:research', 'research') is still 'research'. A claim with a
--      NULL lane under a researched event is unlensed (info row info_null_lane_claims_under_events).
--   2. claim.use_count / last_used_at maintained by a trigger on claim_usage (ADR-14 §3). It
--      RECOMPUTES from claim_usage for the affected claim(s) on insert, delete and claim_id/used_at
--      update, after locking those claim rows FOR UPDATE (two concurrent inserts for one claim would
--      otherwise each count from their own snapshot and the second would overwrite the first: a lost
--      update, reproduced on the twin by rehearse_0022.py step 4c). Then a one-time backfill from the
--      existing rows. No producer may set these columns (spine_client ALLOW leaves them out, ADR-10
--      D5); the DB is their only writer. Nothing ranks on them until >= 20 outcome rows exist.
--   3. Identity (S1b DDL half, ADR-10 D5 re-trigger met by the discovery loop as the second producer):
--        public.norm_name_v1(text)  companies: lowercase, strip ONE legal suffix ANCHORED TO THE END
--                                   (`Acme, Inc.` -> acme; `Co-Marketing` and `AG-UI` keep their
--                                   leading token), collapse non-alphanumerics to one space, trim.
--        public.norm_plain_v1(text) topics and persons: the same without any suffix strip.
--      Both are VERSIONED: never CREATE OR REPLACE them. A changed body would silently desync every
--      stored index entry and alias_norm value from what the function now returns. Ship
--      norm_*_v2 + new indexes instead. (This file creates them only when absent.)
--      Indexes: UNIQUE company (norm_name_v1(name)), UNIQUE topic (norm_plain_v1(name)), NON-unique
--      person (norm_plain_v1(name), company_id) (people share names, ADR-4). Expression indexes, not
--      generated columns: no table rewrite, no new column on person (the PII-guarded table), and
--      load_twin.py's select=* -> COPY keeps working. The old lower(name) unique indexes STAY.
--      public.entity_alias: alias_norm is generated with norm_name_v1 for companies and norm_plain_v1
--      otherwise; one spelling resolves to one entity per type.
--   4. public.sweep_query: the discovery loop's query ledger (one row per issued query per ISO week).
--   5. CHECK widenings: claim_usage.consumer += 'brief', 'published'; claim_relation.method += 'llm';
--      documents.source_type += 'email', 'meeting_note', 'notion_comment' (YED-390: the private originals
--      vault stores those bodies as documents rows; visibility stays 'private' by default, 0009).
--   6. lane_registry rows theme_sweep, claim_review, notion_prior, reconcile, all active = false.
--   7. Security: both new tables RLS on, no policies, every privilege revoked from public / anon /
--      authenticated (0020's pattern). service_role keeps its grants. The new functions lose EXECUTE
--      for public / anon / authenticated and are granted to service_role explicitly (the CHECKs and
--      index expressions run as the writing role).
--   8. DB-level PII backstop on the two new free-text columns: CHECK (public.no_contact_pii_v1(...))
--      on entity_alias.alias and sweep_query.template. The function carries spine_client.py's
--      EMAIL_RE / PHONE_RE verbatim (the same literals as public.assert_no_contact_pii(), 0017);
--      check_pii_regex_parity.py compares this file byte for byte. Versioned like the normalisers.
--
-- NOT HERE, deliberately: dropping doc_claims (not additive, own migration); entity_merge; the
-- feeds / company_signals "bridge routine" text (0021 owns company_signals); the other graph-review
-- lane rows (pre_event_research, post_event_claims, transcripts, posts).
--
-- RE-RUNNABLE and LOCK-LIGHT on re-paste: every DDL statement is catalog-guarded (0016 pattern), so
-- a second paste takes no ACCESS EXCLUSIVE lock on event / claim_usage / claim_relation and creates
-- no index. Only the backfill (0 rows on a re-paste) and the idempotent REVOKE/GRANTs run again.
--
-- APPLY (Alex, prod dashboard): runbook = supabase/scripts/0022_preflight_dashboard.sql, this file,
-- then supabase/scripts/0022_verify_dashboard.sql. Paste OUTSIDE 07:00-09:00 UTC. lock_timeout is
-- 5s: a busy table fails the paste instead of queueing; just re-paste.
-- IF A UNIQUE INDEX FAILS (or the PREFLIGHT lists a collision): a near-duplicate name exists. Do NOT
-- merge to make it pass. Rename the losing row so its normalised name differs: the tombstoned row if
-- one side is a tombstone (metadata.merged_into set), else the newer row, e.g.
--   name -> '<name> [dup <first 8 chars of its id>]'
-- through spine_client (PATCH /company?id=eq.<id>, invariant 1), then re-run PREFLIGHT, re-paste.
-- =============================================================================

begin;
set local lock_timeout = '5s';

-- -----------------------------------------------------------------------------
-- 1. event.kind += 'researched'; lens_of: a researched occasion is unlensed at event level.
-- -----------------------------------------------------------------------------
do $do$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.event'::regclass and conname = 'event_kind_enum'
                   and pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''attended''::text, ''market''::text, ''funding''::text, ''launch''::text, ''exec_move''::text, ''role_posted''::text, ''application''::text, ''interview''::text, ''reference''::text, ''published''::text, ''researched''::text])))') then
    alter table public.event drop constraint if exists event_kind_enum;
    alter table public.event add constraint event_kind_enum check (kind in (
      'attended', 'market', 'funding', 'launch', 'exec_move',
      'role_posted', 'application', 'interview',
      'reference',
      'published',
      'researched'     -- NEW (B0): researched, not (yet) attended; promoted in place to 'attended' on evidence
    ));
  end if;
end
$do$;

-- 0016's body plus the one 'researched' line, after the job rule (job isolation still wins first)
-- and before the research rule. p_lane is null only for event-level facts (mi.fact passes null for
-- events), so research claims hung on a researched event keep their 'research' lens.
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
  -- Serialise writers per claim BEFORE counting. Its own statement, so the recount below takes a
  -- fresh READ COMMITTED snapshot after the lock is granted and sees the other writer's committed
  -- row. Ordered by id so two multi-claim writers can't deadlock.
  perform 1 from public.claim where id = any(ids) order by id for update;
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
comment on function public.claim_usage_sync_use_count() is
  '0022 (ADR-14 §3): keeps claim.use_count / last_used_at equal to count(*) / max(used_at) over '
  'claim_usage for the claim, under a FOR UPDATE lock on the claim row. The only writer of those columns.';

do $do$
begin
  if not exists (select 1 from pg_trigger t
                  where t.tgrelid = 'public.claim_usage'::regclass and t.tgname = 'claim_usage_sync_use_count'
                    and t.tgfoid = 'public.claim_usage_sync_use_count()'::regprocedure
                    and t.tgtype = 29 and t.tgenabled = 'O'
                    and (select array_agg(a.attname::text order by a.attname) from pg_attribute a
                          where a.attrelid = t.tgrelid and a.attnum = any(t.tgattr::int2[])) = array['claim_id', 'used_at']) then
    create or replace trigger claim_usage_sync_use_count
      after insert or delete or update of claim_id, used_at on public.claim_usage
      for each row execute function public.claim_usage_sync_use_count();
  end if;
end
$do$;

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
-- 3 + 8. Versioned functions: two normalisers and the PII predicate. Created only when ABSENT;
--        NEVER CREATE OR REPLACE (see header). Python twins: substrate.py norm_company / norm_plain.
-- -----------------------------------------------------------------------------
do $do$
begin
  if to_regprocedure('public.norm_name_v1(text)') is null then
    execute $ddl$
      create function public.norm_name_v1(t text)
      returns text
      language sql
      immutable
      parallel safe
      set search_path = pg_catalog, pg_temp
      as $fn$
        select nullif(trim(regexp_replace(
                 regexp_replace(lower(coalesce(t, '')),
                   '\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\M[^a-z0-9]*$', ''),
                 '[^a-z0-9]+', ' ', 'g')), '')
      $fn$
    $ddl$;
  end if;
  if to_regprocedure('public.norm_plain_v1(text)') is null then
    execute $ddl$
      create function public.norm_plain_v1(t text)
      returns text
      language sql
      immutable
      parallel safe
      set search_path = pg_catalog, pg_temp
      as $fn$
        select nullif(trim(regexp_replace(lower(coalesce(t, '')), '[^a-z0-9]+', ' ', 'g')), '')
      $fn$
    $ddl$;
  end if;
  if to_regprocedure('public.no_contact_pii_v1(text)') is null then
    execute $ddl$
      create function public.no_contact_pii_v1(t text)
      returns boolean
      language plpgsql
      immutable
      parallel safe
      set search_path = pg_catalog, pg_temp
      as $fn$
      declare
        -- Verbatim spine_client.py EMAIL_RE / PHONE_RE (= public.assert_no_contact_pii(), 0017).
        -- check_pii_regex_parity.py compares these two lines byte for byte.
        email_re text := $re$(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])$re$;
        phone_re text := $re$(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
      begin
        return t is null or not (t ~ email_re or t ~ phone_re);
      end
      $fn$
    $ddl$;
  end if;
end
$do$;
revoke all on function public.norm_name_v1(text)      from public, anon, authenticated;
revoke all on function public.norm_plain_v1(text)     from public, anon, authenticated;
revoke all on function public.no_contact_pii_v1(text) from public, anon, authenticated;
grant execute on function public.norm_name_v1(text)      to service_role;
grant execute on function public.norm_plain_v1(text)     to service_role;
grant execute on function public.no_contact_pii_v1(text) to service_role;
comment on function public.norm_name_v1(text) is
  '0022 (S1b): company name key (end-anchored legal-suffix strip). VERSIONED: never CREATE OR REPLACE; ship _v2.';
comment on function public.norm_plain_v1(text) is
  '0022 (S1b): topic / person name key (no suffix strip). VERSIONED: never CREATE OR REPLACE; ship _v2.';
comment on function public.no_contact_pii_v1(text) is
  '0022: true unless the text matches spine EMAIL_RE / PHONE_RE. Backs CHECKs. VERSIONED: never CREATE OR REPLACE.';

do $do$
begin
  if to_regclass('public.company_name_norm_uq') is null then
    create unique index company_name_norm_uq on public.company (public.norm_name_v1(name));
  end if;
  if to_regclass('public.topic_name_norm_uq') is null then
    create unique index topic_name_norm_uq on public.topic (public.norm_plain_v1(name));
  end if;
  if to_regclass('public.person_name_norm_company_idx') is null then
    create index person_name_norm_company_idx on public.person (public.norm_plain_v1(name), company_id);
  end if;
end
$do$;

create table if not exists public.entity_alias (
  id           uuid primary key default gen_random_uuid(),
  entity_type  text not null check (entity_type in ('company', 'person', 'topic')),
  entity_id    uuid not null,                     -- polymorphic, like claim_entity (no FK)
  alias        text not null check (char_length(alias) between 1 and 200),
  alias_norm   text generated always as (case when entity_type = 'company' then public.norm_name_v1(alias)
                                              else public.norm_plain_v1(alias) end) stored,
  source       text not null check (source ~ '^[a-z][a-z0-9_:.-]{1,59}$'),   -- notion | sweep | ats | merge | manual ...
  confidence   numeric not null default 1.0 check (confidence >= 0 and confidence <= 1),
  created_at   timestamptz not null default now(),
  constraint entity_alias_norm_present check (alias_norm is not null)
);
comment on table public.entity_alias is
  '0022 (S1b / ADR-14): other names an entity is known by. Resolution order: name key -> alias_norm '
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
comment on table public.sweep_query is
  '0022 (ADR-14 §3): one row per discovery-loop query per ISO week, with its yield. seed_event_id / '
  'seed_claim_id tie a query to what raised it, so seed yield is a join. Written only via spine_client.';

-- Indexes + the PII CHECKs, catalog-guarded so a re-paste restores a dropped one and touches nothing else.
do $do$
begin
  if to_regclass('public.entity_alias_type_norm_uq') is null then
    create unique index entity_alias_type_norm_uq on public.entity_alias (entity_type, alias_norm);
  end if;
  if to_regclass('public.entity_alias_entity_idx') is null then
    create index entity_alias_entity_idx on public.entity_alias (entity_type, entity_id);
  end if;
  if to_regclass('public.sweep_query_theme_week_idx') is null then
    create index sweep_query_theme_week_idx on public.sweep_query (theme_id, iso_week);
  end if;
  if to_regclass('public.sweep_query_seed_event_idx') is null then
    create index sweep_query_seed_event_idx on public.sweep_query (seed_event_id) where seed_event_id is not null;
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.entity_alias'::regclass
                   and conname = 'entity_alias_alias_no_pii') then
    alter table public.entity_alias add constraint entity_alias_alias_no_pii check (public.no_contact_pii_v1(alias));
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.sweep_query'::regclass
                   and conname = 'sweep_query_template_no_pii') then
    alter table public.sweep_query add constraint sweep_query_template_no_pii check (public.no_contact_pii_v1(template));
  end if;
end
$do$;

-- -----------------------------------------------------------------------------
-- 5. CHECK widenings (catalog-guarded: an already-widened CHECK is not re-taken).
-- -----------------------------------------------------------------------------
do $do$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.claim_usage'::regclass and conname = 'claim_usage_consumer_check'
                   and pg_get_constraintdef(oid) = 'CHECK ((consumer = ANY (ARRAY[''event''::text, ''content''::text, ''job''::text, ''ideation''::text, ''dev''::text, ''brief''::text, ''published''::text])))') then
    alter table public.claim_usage drop constraint if exists claim_usage_consumer_check;
    alter table public.claim_usage add constraint claim_usage_consumer_check
      check (consumer in ('event', 'content', 'job', 'ideation', 'dev', 'brief', 'published'));
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.claim_relation'::regclass and conname = 'claim_relation_method_check'
                   and pg_get_constraintdef(oid) = 'CHECK ((method = ANY (ARRAY[''human''::text, ''embedding''::text, ''rule''::text, ''llm''::text])))') then
    alter table public.claim_relation drop constraint if exists claim_relation_method_check;
    alter table public.claim_relation add constraint claim_relation_method_check
      check (method in ('human', 'embedding', 'rule', 'llm'));
  end if;
  -- YED-390: + email, meeting_note, notion_comment (the 0009 list otherwise unchanged, same order).
  if not exists (select 1 from pg_constraint where conrelid = 'public.documents'::regclass and conname = 'documents_source_type_check'
                   and pg_get_constraintdef(oid) = 'CHECK ((source_type = ANY (ARRAY[''book''::text, ''whitepaper''::text, ''filing''::text, ''pdf''::text, ''other''::text, ''research_brief''::text, ''deep_read''::text, ''prior_context_pack''::text, ''post_event_brief''::text, ''transcript''::text, ''linkedin_post''::text, ''carousel''::text, ''connection_note''::text, ''dossier''::text, ''project_idea''::text, ''scan_digest''::text, ''build_retro''::text, ''note''::text, ''glossary''::text, ''email''::text, ''meeting_note''::text, ''notion_comment''::text])))') then
    alter table public.documents drop constraint if exists documents_source_type_check;
    alter table public.documents add constraint documents_source_type_check check (source_type in (
      'book', 'whitepaper', 'filing', 'pdf', 'other',
      'research_brief', 'deep_read', 'prior_context_pack', 'post_event_brief', 'transcript',
      'linkedin_post', 'carousel', 'connection_note', 'dossier', 'project_idea',
      'scan_digest', 'build_retro', 'note', 'glossary',
      'email', 'meeting_note', 'notion_comment'
    ));
  end if;
end
$do$;

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
-- 7. Security for the new tables (0020 pattern; RLS guarded so a re-paste takes no lock).
-- -----------------------------------------------------------------------------
do $do$
begin
  if not (select relrowsecurity from pg_class where oid = 'public.entity_alias'::regclass) then
    alter table public.entity_alias enable row level security;
  end if;
  if not (select relrowsecurity from pg_class where oid = 'public.sweep_query'::regclass) then
    alter table public.sweep_query enable row level security;
  end if;
end
$do$;
revoke all on public.entity_alias from public, anon, authenticated;
revoke all on public.sweep_query  from public, anon, authenticated;

commit;

-- =============================================================================
-- PREFLIGHT (read-only; run on prod BEFORE the paste: supabase/scripts/0022_preflight_dashboard.sql
-- is this block). ONE statement. Expect NO collision_* rows and two baseline_* rows
-- (baseline_claim_usage_rows >= 1282, baseline_use_count_nonzero = 0). The key expressions are the
-- shipped function bodies with t -> name (rehearse_0022.py proves them equal to the functions).
-- A collision row lists `id:name` for every row sharing the key: rename the loser (header), re-run.
-- =============================================================================
-- PREFLIGHT:BEGIN
-- select 'collision_company' as check_name, k as norm_key, string_agg(id::text || ':' || name, ' | ' order by id) as detail
--   from (select id, name, nullif(trim(regexp_replace(regexp_replace(lower(coalesce(name, '')), '\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\M[^a-z0-9]*$', ''), '[^a-z0-9]+', ' ', 'g')), '') as k from public.company) s
--  where k is not null group by k having count(*) > 1
-- union all
-- select 'collision_topic', k, string_agg(id::text || ':' || name, ' | ' order by id)
--   from (select id, name, nullif(trim(regexp_replace(lower(coalesce(name, '')), '[^a-z0-9]+', ' ', 'g')), '') as k from public.topic) s
--  where k is not null group by k having count(*) > 1
-- union all
-- select 'baseline_claim_usage_rows', null, (select count(*) from public.claim_usage)::text
-- union all
-- select 'baseline_use_count_nonzero', null, (select count(*) from public.claim where use_count <> 0 or last_used_at is not null)::text;
-- PREFLIGHT:END

-- =============================================================================
-- VERIFY (read-only). Run with psql in a READ-ONLY session, or paste
-- supabase/scripts/0022_verify_dashboard.sql (this block as one UNION ALL; every non-info row must
-- read true). keep_* rows guard what 0022 must NOT break (they pass before and after); info_* rows
-- are printed, never gating.
-- =============================================================================
-- VERIFY:BEGIN
-- select 'event_kind_researched', (select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''attended''::text, ''market''::text, ''funding''::text, ''launch''::text, ''exec_move''::text, ''role_posted''::text, ''application''::text, ''interview''::text, ''reference''::text, ''published''::text, ''researched''::text])))' from pg_constraint where conrelid = 'public.event'::regclass and conname = 'event_kind_enum');
-- select 'lens_of_researched_null', mi.lens_of('researched', null, null) is null and mi.lens_of('researched', 'substrate:research', null) is null and mi.lens_of('researched', 'substrate:research', 'research') = 'research' and coalesce(mi.lens_of('researched', null, 'A'), '') <> 'attended';
-- select 'keep_lens_of_0016_truth_table', mi.lens_of('attended', null, null) = 'attended' and mi.lens_of('attended', null, 'research') = 'research' and mi.lens_of('role_posted', 'substrate:research', 'research') = 'job' and mi.lens_of('funding', 'akta', null) = 'market' and mi.lens_of(null, 'substrate:research', null) = 'research' and mi.lens_of('published', null, null) is null and mi.lens_of(null, null, 'A') is null;
-- select 'keep_lens_of_immutable_no_api_exec', (select provolatile = 'i' from pg_proc where oid = 'mi.lens_of(text,text,text)'::regprocedure) and not has_function_privilege('anon', 'mi.lens_of(text,text,text)', 'execute');
-- select 'use_count_trigger_present', exists (select 1 from pg_trigger t where t.tgrelid = 'public.claim_usage'::regclass and t.tgname = 'claim_usage_sync_use_count' and t.tgenabled = 'O' and t.tgfoid = 'public.claim_usage_sync_use_count()'::regprocedure and (t.tgtype & 1) = 1 and (t.tgtype & 2) = 0 and (t.tgtype & 4) = 4 and (t.tgtype & 8) = 8 and (t.tgtype & 16) = 16 and (select array_agg(a.attname::text order by a.attname) from pg_attribute a where a.attrelid = t.tgrelid and a.attnum = any(t.tgattr::int2[])) = array['claim_id', 'used_at']);
-- select 'use_count_fn_invoker_no_api_exec', (select not prosecdef and proconfig = array['search_path=pg_catalog, pg_temp'] from pg_proc where oid = 'public.claim_usage_sync_use_count()'::regprocedure) and not has_function_privilege('anon', 'public.claim_usage_sync_use_count()', 'execute') and not has_function_privilege('authenticated', 'public.claim_usage_sync_use_count()', 'execute');
-- select 'use_count_fn_locks_rows', (select prosrc ~ 'perform 1 from public\.claim where id = any\(ids\) order by id for update;' from pg_proc where oid = 'public.claim_usage_sync_use_count()'::regprocedure);
-- select 'use_count_matches_usage', (select count(*) > 0 from public.claim_usage) and not exists (select 1 from public.claim c left join (select claim_id, count(*) as n, max(used_at) as l from public.claim_usage group by claim_id) u on u.claim_id = c.id where c.use_count <> coalesce(u.n, 0) or c.last_used_at is distinct from u.l);
-- select 'claim_usage_consumer_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((consumer = ANY (ARRAY[''event''::text, ''content''::text, ''job''::text, ''ideation''::text, ''dev''::text, ''brief''::text, ''published''::text])))' from pg_constraint where conrelid = 'public.claim_usage'::regclass and conname = 'claim_usage_consumer_check');
-- select 'documents_source_type_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((source_type = ANY (ARRAY[''book''::text, ''whitepaper''::text, ''filing''::text, ''pdf''::text, ''other''::text, ''research_brief''::text, ''deep_read''::text, ''prior_context_pack''::text, ''post_event_brief''::text, ''transcript''::text, ''linkedin_post''::text, ''carousel''::text, ''connection_note''::text, ''dossier''::text, ''project_idea''::text, ''scan_digest''::text, ''build_retro''::text, ''note''::text, ''glossary''::text, ''email''::text, ''meeting_note''::text, ''notion_comment''::text])))' from pg_constraint where conrelid = 'public.documents'::regclass and conname = 'documents_source_type_check');
-- select 'claim_relation_method_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((method = ANY (ARRAY[''human''::text, ''embedding''::text, ''rule''::text, ''llm''::text])))' from pg_constraint where conrelid = 'public.claim_relation'::regclass and conname = 'claim_relation_method_check');
-- select 'norm_fns_behaviour', (select bool_and(provolatile = 'i') from pg_proc where oid in ('public.norm_name_v1(text)'::regprocedure, 'public.norm_plain_v1(text)'::regprocedure)) and public.norm_name_v1('Acme, Inc.') = 'acme' and public.norm_name_v1('LangChain Inc') = 'langchain' and public.norm_name_v1('Co-Marketing Labs') = 'co marketing labs' and public.norm_name_v1('AG-UI') = 'ag ui' and public.norm_name_v1('  Zed (AI) ') = 'zed ai' and public.norm_name_v1('Inc.') is null and public.norm_plain_v1('Agents Inc') = 'agents inc' and public.norm_plain_v1('AI-Agents') = 'ai agents' and public.norm_plain_v1('!!!') is null;
-- select 'norm_fns_exec_service_role_only', has_function_privilege('service_role', 'public.norm_name_v1(text)', 'execute') and has_function_privilege('service_role', 'public.norm_plain_v1(text)', 'execute') and not has_function_privilege('anon', 'public.norm_name_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.norm_name_v1(text)', 'execute') and not has_function_privilege('anon', 'public.norm_plain_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.norm_plain_v1(text)', 'execute');
-- select 'no_contact_pii_behaviour', (select provolatile = 'i' from pg_proc where oid = 'public.no_contact_pii_v1(text)'::regprocedure) and not public.no_contact_pii_v1('jane.doe@example.com') and not public.no_contact_pii_v1('call +44 20 7946 0958') and not public.no_contact_pii_v1('555-123-4567') and public.no_contact_pii_v1('Acme') and public.no_contact_pii_v1('https://x.com/@handle') and public.no_contact_pii_v1('2026-11-04 12:30:45') and public.no_contact_pii_v1(null) and has_function_privilege('service_role', 'public.no_contact_pii_v1(text)', 'execute') and not has_function_privilege('anon', 'public.no_contact_pii_v1(text)', 'execute') and not has_function_privilege('authenticated', 'public.no_contact_pii_v1(text)', 'execute');
-- select 'company_name_norm_unique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'company' and indexname = 'company_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX company_name_norm_uq ON public.company USING btree (norm_name_v1(name))');
-- select 'topic_name_norm_unique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'topic' and indexname = 'topic_name_norm_uq' and indexdef = 'CREATE UNIQUE INDEX topic_name_norm_uq ON public.topic USING btree (norm_plain_v1(name))');
-- select 'person_name_norm_nonunique', exists (select 1 from pg_indexes where schemaname = 'public' and tablename = 'person' and indexname = 'person_name_norm_company_idx' and indexdef = 'CREATE INDEX person_name_norm_company_idx ON public.person USING btree (norm_plain_v1(name), company_id)');
-- select 'keep_lower_name_indexes', (select count(*) = 2 from pg_indexes where schemaname = 'public' and indexname in ('company_lower_idx', 'topic_lower_idx'));
-- select 'entity_alias_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'id,entity_type,entity_id,alias,alias_norm,source,confidence,created_at' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias');
-- select 'entity_alias_norm_generated', (select is_generated = 'ALWAYS' and generation_expression ~ 'norm_name_v1\(alias\)' and generation_expression ~ 'norm_plain_v1\(alias\)' from information_schema.columns where table_schema = 'public' and table_name = 'entity_alias' and column_name = 'alias_norm');
-- select 'entity_alias_unique_norm', exists (select 1 from pg_indexes where schemaname = 'public' and indexname = 'entity_alias_type_norm_uq' and indexdef = 'CREATE UNIQUE INDEX entity_alias_type_norm_uq ON public.entity_alias USING btree (entity_type, alias_norm)');
-- select 'entity_alias_pii_check', (select pg_get_constraintdef(oid) = 'CHECK (no_contact_pii_v1(alias))' from pg_constraint where conrelid = 'public.entity_alias'::regclass and conname = 'entity_alias_alias_no_pii');
-- select 'entity_alias_rls_on', (select relrowsecurity from pg_class where oid = 'public.entity_alias'::regclass);
-- select 'entity_alias_no_policies', to_regclass('public.entity_alias') is not null and not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'entity_alias');
-- select 'entity_alias_no_api_grants', not exists (select 1 from unnest(array['anon', 'authenticated']) r where has_table_privilege(r, 'public.entity_alias', 'select') or has_table_privilege(r, 'public.entity_alias', 'insert') or has_table_privilege(r, 'public.entity_alias', 'update') or has_table_privilege(r, 'public.entity_alias', 'delete') or has_table_privilege(r, 'public.entity_alias', 'truncate') or has_table_privilege(r, 'public.entity_alias', 'references') or has_table_privilege(r, 'public.entity_alias', 'trigger') or has_table_privilege(r, 'public.entity_alias', 'maintain'));
-- select 'entity_alias_service_role_rw', has_table_privilege('service_role', 'public.entity_alias', 'select') and has_table_privilege('service_role', 'public.entity_alias', 'insert') and has_table_privilege('service_role', 'public.entity_alias', 'update') and has_table_privilege('service_role', 'public.entity_alias', 'delete');
-- select 'sweep_query_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'query_id,kind,theme_id,template,seed_event_id,seed_claim_id,iso_week,lane_run_id,status,items_returned,items_written,items_used,searches,created_at,last_run_at' from information_schema.columns where table_schema = 'public' and table_name = 'sweep_query');
-- select 'sweep_query_kind_vocab', (select pg_get_constraintdef(oid) = 'CHECK ((kind = ANY (ARRAY[''velocity''::text, ''gap''::text, ''event''::text, ''entity''::text, ''room_topic''::text, ''room_entity''::text, ''open_question''::text, ''room_vs_market''::text])))' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_kind_check');
-- select 'sweep_query_issue_unique', (select pg_get_constraintdef(oid) = 'UNIQUE NULLS NOT DISTINCT (kind, theme_id, template, iso_week)' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_issue_uq');
-- select 'sweep_query_pii_check', (select pg_get_constraintdef(oid) = 'CHECK (no_contact_pii_v1(template))' from pg_constraint where conrelid = 'public.sweep_query'::regclass and conname = 'sweep_query_template_no_pii');
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
-- select 'info_null_lane_claims_under_events', (select count(*) from public.claim where lane is null and event_id is not null)::text;
-- VERIFY:END

-- =============================================================================
-- ROLLBACK (uncomment to run). Drops only what 0022 adds and restores the 0016 lens_of body and
-- the pre-0022 CHECKs byte for byte. It resets use_count / last_used_at to the pre-0022 state
-- (0 / null everywhere, recorded on prod 2026-11-11); claim_usage itself is untouched, so the
-- counts are re-derivable.
-- EXPORT FIRST: the two DROP TABLEs destroy entity_alias and sweep_query rows. Before rolling back
-- a prod that has run for any time, export both (dashboard Table editor -> Export to CSV, or
-- `\copy public.entity_alias to 'entity_alias.csv' csv header` and the same for sweep_query) and
-- keep the files out of git.
-- It FAILS LOUD, by design, if data already uses a new value: an event with kind 'researched', a
-- claim_usage row with consumer 'brief' / 'published', a claim_relation with method 'llm', a documents
-- row with source_type 'email' / 'meeting_note' / 'notion_comment' (the YED-390 vault), or a
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
-- drop function if exists public.norm_name_v1(text);
-- drop function if exists public.norm_plain_v1(text);
-- drop function if exists public.no_contact_pii_v1(text);
-- delete from public.lane_registry where lane in ('theme_sweep', 'claim_review', 'notion_prior', 'reconcile');
-- alter table public.claim_relation drop constraint if exists claim_relation_method_check;
-- alter table public.claim_relation add constraint claim_relation_method_check check (method in ('human', 'embedding', 'rule'));
-- alter table public.claim_usage drop constraint if exists claim_usage_consumer_check;
-- alter table public.claim_usage add constraint claim_usage_consumer_check check (consumer in ('event', 'content', 'job', 'ideation', 'dev'));
-- alter table public.documents drop constraint if exists documents_source_type_check;
-- alter table public.documents add constraint documents_source_type_check check (source_type in ('book', 'whitepaper', 'filing', 'pdf', 'other', 'research_brief', 'deep_read', 'prior_context_pack', 'post_event_brief', 'transcript', 'linkedin_post', 'carousel', 'connection_note', 'dossier', 'project_idea', 'scan_digest', 'build_retro', 'note', 'glossary'));
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
