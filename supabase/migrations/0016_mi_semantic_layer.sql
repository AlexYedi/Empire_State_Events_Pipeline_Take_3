-- =====================================================================
-- 0016 — MI semantic layer (ADR-13): theme history, segment history, lane registry + ledger,
--        event.signal_type, schema `mi` (lens function + read-only views), one reader.
-- Linear: YED-307 · Spec: docs/proposals/2026-11-04-market-lens-and-slices.md §3–§4, §6 Phase A item 1
--         · precondition named in docs/proposals/2026-11-03-dynamic-topic-taxonomy.md §9
--         · consumer contract (slice.py #273, hub#58): docs/adr/ADR-13-market-lens-slice-layer.md
-- Numbered 0016, not 0015: 0015_scrub_pre2b_person_email.sql is applied to prod and lives on PR #261.
--
-- ADDITIVE ONLY. What this adds, and nothing else:
--   * public.topic_cluster_membership              SCD Type 2 theme membership, seeded from today's
--                                                   public.topic.cluster_id, kept in sync by triggers
--   * public.topic_membership_sync() + 2 triggers  on public.topic (insert / cluster or tombstone change)
--   * public.company_segment_history               SCD Type 2 company segment (empty; lane 5 fills it)
--   * public.lane_registry                         one row per ingestion lane (seeded: lanes 0–5)
--   * public.lane_run                              one row per lane run (the lane ledger)
--   * public.event.signal_type                      nullable column + CHECK over six values + partial index
--   * schema mi                                     lens_of(), theme_as_of(), eight read-only views
--   * public.mi_slice(text, jsonb)                  STABLE SECURITY DEFINER reader over five views
-- No existing column, constraint, function, grant or row is changed. Two triggers are ADDED to
-- public.topic (they write only to the new membership table). The only DML is seeding two tables
-- this file creates (membership, lane registry).
--
-- MARKET DEDUP WEEK BUCKET (contract item 6, option b): NO event_week column. A unique index
--   cannot span public.event and public.event_entity, where the company link lives, so a
--   (source, kind, signal_type, week, company) key is not expressible as an index. Instead:
--   weekly market producers (hiring_pulse first) set event_date to the SUNDAY that ends the ISO
--   week (00:00 UTC), and substrate.py ensure-event dedups on (source, kind, signal_type,
--   event_date, company edge) before insert. mi.fact buckets every fact by ISO (Monday) week,
--   and that Sunday falls in the same ISO week, so the two agree.
--
-- PROD FACTS this file is written against (read-only psql, 2026-11-04, PG 17.6):
--   * public.topic has cluster_id / cluster_assignment_confidence numeric(4,3) / cluster_assigned_by,
--     and NO cluster-assignment timestamp column (nor a metadata key for one) -> the seed uses the
--     spec's fallback valid_from = 2026-08-08. Last assigned topic was created 2026-08-08.
--   * 272 topics, 170 assigned (all cluster_assigned_by='llm'), 26 merge tombstones
--     (metadata ? 'merged_into'), 14 of which STILL carry a cluster_id -> seed = 156 rows.
--     No '<Theme> (general)' topics exist yet (general_facts is 0 until they do).
--   * public.event has no signal_type column; kinds = the 10-value event_kind_enum (0009).
--   * claim.lane is 'research' (3,543 rows) or 'A' (2,188); no claim has a null asserted_at.
--   * Default privileges in `public` grant ALL on new tables and EXECUTE on new functions to
--     anon + authenticated. Hence the explicit REVOKEs below.
--   * pipeline_writer exists (NOLOGIN) and holds no table grants in public.
--
-- SECURITY MODEL (0003 / 0012 / 0013 pattern):
--   * new tables: all in `public` (ADR-13: spine_client writes public only; 0003 keeps
--     topic_intelligence off the API). RLS on, no policies, public/anon/authenticated revoked;
--     the service-role REST path via spine_client is the only writer.
--   * schema mi: not in the Data API exposed schemas; USAGE revoked from public/anon/authenticated.
--     Views are security_invoker, so even a granted caller needs base-table rights.
--   * public.mi_slice: STABLE (PostgREST may call it by GET, read-only), SECURITY DEFINER owned by
--     the migration runner, search_path pinned, every reference schema-qualified, no dynamic SQL,
--     EXECUTE only service_role (least privilege, spec §4).
--
-- RE-RUNNABLE: every statement is guarded (if not exists / or replace / drop … if exists /
--   not-exists or on-conflict seeds). A second paste is a no-op. Rehearse with
--   supabase/scripts/rehearse_0016.py on the twin (ytfzzsxcxxbejnowmkmk) before Alex pastes
--   into prod (CLAUDE.md invariant 2). Verify and rollback blocks are at the bottom, between
--   machine-readable markers the harness parses (keep the markers and one check per statement).
-- =====================================================================
begin;

-- ---------------------------------------------------------------------
-- 1. Theme membership, SCD Type 2 (Kimball). One row per (topic, cluster, interval).
--    The open row (valid_to is null) is the current assignment; at most one per topic.
--    A topic with no open row is unassigned. Rows are closed, never deleted or edited.
-- ---------------------------------------------------------------------
create table if not exists public.topic_cluster_membership (
  membership_id  uuid primary key default gen_random_uuid(),
  topic_id       uuid not null references public.topic(id) on delete cascade,
  cluster_id     uuid not null references topic_intelligence.topic_cluster(cluster_id),
  valid_from     timestamptz not null,
  valid_to       timestamptz,
  assigned_by    text not null check (assigned_by in ('llm', 'session', 'human', 'merge')),
  confidence     numeric(4,3) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  change_kind    text not null default 'assign'
                   check (change_kind in ('seed', 'assign', 'reassign', 'merge', 'revert')),
  created_at     timestamptz not null default now(),
  check (valid_to is null or valid_to > valid_from)
);
create unique index if not exists topic_cluster_membership_one_open_uq
  on public.topic_cluster_membership (topic_id) where valid_to is null;
create index if not exists topic_cluster_membership_topic_from_idx
  on public.topic_cluster_membership (topic_id, valid_from);
create index if not exists topic_cluster_membership_cluster_idx
  on public.topic_cluster_membership (cluster_id);

comment on table public.topic_cluster_membership is
  'ADR-13: effective-dated topic -> theme (cluster) membership, SCD Type 2. Read through mi.theme_as_of(). '
  'Seeded 0016 from public.topic.cluster_id with valid_from 2026-08-08 (no assignment timestamp exists). '
  'Overlap between closed rows is checked by the verify block, not a constraint (btree_gist not installed).';

-- Seed: one open row per assigned, non-tombstoned topic. Re-runnable (not-exists guard).
-- coalesce(): metadata is nullable, and `null ? key` is null, which would silently drop the row.
insert into public.topic_cluster_membership
  (topic_id, cluster_id, valid_from, valid_to, assigned_by, confidence, change_kind)
select t.id, t.cluster_id, timestamptz '2026-08-08 00:00:00+00', null,
       coalesce(t.cluster_assigned_by, 'llm'), t.cluster_assignment_confidence, 'seed'
from public.topic t
where t.cluster_id is not null
  and not coalesce(t.metadata ? 'merged_into', false)
  and not exists (select 1 from public.topic_cluster_membership m where m.topic_id = t.id);

-- 1b. Keep membership in sync with public.topic in the database (one topic write -> both records).
--     Fires on INSERT with a cluster_id, and on UPDATE when cluster_id changes OR the topic's
--     tombstone state changes (merge tombstones keep their cluster_id — 14 do in prod — so a
--     cluster_id-only trigger would miss them). Rules:
--       tombstone, or cluster_id null -> close the open row (if any), open nothing
--       cluster unchanged             -> no-op (idempotent; the WHEN clause also skips it)
--       cluster changed               -> close the open row, open a new one: 'reassign'
--                                        ('assign' when there was no open row)
--     Timestamps use clock_timestamp(), not now(): now() is fixed per transaction, so an
--     insert-then-reassign in ONE transaction would close a row with valid_to = valid_from and
--     violate the interval check. valid_from is nudged 1µs past the closed row's start if equal.
--     assigned_by is carried from topic.cluster_assigned_by (null -> 'session'). A value outside
--     the CHECK vocabulary raises and aborts the topic write: loud vocabulary drift, by design.
create or replace function public.topic_membership_sync()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, pg_temp
as $fn$
declare
  v_tomb      boolean := coalesce(new.metadata ? 'merged_into', false);
  v_open_id   uuid;
  v_open_cl   uuid;
  v_open_from timestamptz;
  v_had_open  boolean;
  v_ts        timestamptz := clock_timestamp();
begin
  select m.membership_id, m.cluster_id, m.valid_from
    into v_open_id, v_open_cl, v_open_from
    from public.topic_cluster_membership m
   where m.topic_id = new.id and m.valid_to is null
   for update;
  v_had_open := v_open_id is not null;

  if v_had_open and v_ts <= v_open_from then
    v_ts := v_open_from + interval '1 microsecond';
  end if;

  if v_tomb or new.cluster_id is null then
    if v_had_open then
      update public.topic_cluster_membership set valid_to = v_ts where membership_id = v_open_id;
    end if;
    return null;
  end if;

  if v_had_open and v_open_cl = new.cluster_id then
    return null;
  end if;

  if v_had_open then
    update public.topic_cluster_membership set valid_to = v_ts where membership_id = v_open_id;
  end if;

  insert into public.topic_cluster_membership
    (topic_id, cluster_id, valid_from, valid_to, assigned_by, confidence, change_kind)
  values
    (new.id, new.cluster_id, v_ts, null, coalesce(new.cluster_assigned_by, 'session'),
     new.cluster_assignment_confidence, case when v_had_open then 'reassign' else 'assign' end);
  return null;
end;
$fn$;
revoke all on function public.topic_membership_sync() from public, anon, authenticated;

drop trigger if exists topic_membership_sync_ins on public.topic;
create trigger topic_membership_sync_ins
  after insert on public.topic
  for each row when (new.cluster_id is not null)
  execute function public.topic_membership_sync();

drop trigger if exists topic_membership_sync_upd on public.topic;
create trigger topic_membership_sync_upd
  after update of cluster_id, metadata on public.topic
  for each row when (old.cluster_id is distinct from new.cluster_id
                     or coalesce(old.metadata ? 'merged_into', false)
                        is distinct from coalesce(new.metadata ? 'merged_into', false))
  execute function public.topic_membership_sync();

-- ---------------------------------------------------------------------
-- 2. Company segment history, SCD Type 2. Empty at creation (lane 5 writes it).
--    No PII: every text column is a constrained token or short label; no contact fields.
-- ---------------------------------------------------------------------
create table if not exists public.company_segment_history (
  segment_id      uuid primary key default gen_random_uuid(),
  company_id      uuid not null references public.company(id) on delete cascade,
  stage           text check (stage is null or stage in
                    ('pre_seed', 'seed', 'series_a', 'series_b', 'series_c_plus',
                     'growth', 'public', 'acquired', 'bootstrapped', 'unknown')),
  industry        text check (industry is null or industry ~ '^[A-Za-z0-9][A-Za-z0-9 /&+.,-]{0,59}$'),
  headcount_band  text check (headcount_band is null or headcount_band in
                    ('1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5001+')),
  hq_metro        text check (hq_metro is null or hq_metro ~ '^[a-z][a-z0-9_]{1,39}$'),
  target_tier     text check (target_tier is null or target_tier in ('A', 'B', 'C')),
  valid_from      timestamptz not null,
  valid_to        timestamptz,
  source          text not null check (source ~ '^[a-z][a-z0-9_:.-]{1,39}$'),
  created_at      timestamptz not null default now(),
  check (valid_to is null or valid_to > valid_from)
);
create unique index if not exists company_segment_history_one_open_uq
  on public.company_segment_history (company_id) where valid_to is null;
create index if not exists company_segment_history_company_from_idx
  on public.company_segment_history (company_id, valid_from);

comment on table public.company_segment_history is
  'ADR-13: company segment (stage, industry, headcount band, HQ metro, target tier) as SCD Type 2. '
  'target_tier mirrors the PRIVATE target list: never render it on a public hub surface.';

-- ---------------------------------------------------------------------
-- 3. Lane registry + lane ledger (spec §2, L1–L3, L6). The registry lets a lane that has
--    NEVER run still FAIL freshness: freshness = days since the lane's latest finished
--    successful/partial run; FLAG at >= freshness_flag_days, FAIL at >= freshness_fail_days;
--    an ACTIVE lane with no such run is FAIL. Inactive lanes are not alarmed.
--    Seeded INACTIVE: each lane's producer PR flips active = true when it ships, so the
--    nightly does not go red on day one for lanes nobody has built yet.
-- ---------------------------------------------------------------------
create table if not exists public.lane_registry (
  lane                 text primary key check (lane ~ '^[a-z][a-z0-9_]{1,39}$'),
  schedule             text not null check (char_length(schedule)  <= 200),
  owner                text not null check (char_length(owner)     <= 60),
  consumer             text not null check (char_length(consumer)  <= 200),
  kill_rule            text not null check (char_length(kill_rule) <= 300),
  active               boolean not null default false,
  freshness_flag_days  integer not null default 7  check (freshness_flag_days > 0),
  freshness_fail_days  integer not null default 14,
  check (freshness_fail_days > freshness_flag_days)
);

insert into public.lane_registry
  (lane, schedule, owner, consumer, kill_rule, active, freshness_flag_days, freshness_fail_days)
values
  ('corpus_mine', 'one backfill (batches of 200), then per research brief at stage-research',
   'alex', 'Q1, Q3, Q8; the research-lens column of every slice',
   'below 90% entity-linked after the backfill -> fix the claim extractor upstream; 0 used items in 4 briefs -> stop, decision issue',
   false, 7, 14),
  ('hiring_pulse', 'weekly GitHub Action (Sunday)', 'alex', 'Q2, Q5; Monday Market Brief',
   'items_written = 0 for 3 runs -> FAIL; 0 used items in 4 briefs -> stop, decision issue',
   false, 7, 14),
  ('company_signals', 'weekly, Monday session (akta MCP); credit cap per run', 'alex', 'Q2-Q6; Monday Market Brief',
   'over the credit cap Alex set -> pause; <60% watchlist coverage at 90 days -> widen sources before widening the list',
   false, 7, 14),
  ('research_frontier', 'weekly, Monday session (Hugging Face trending)', 'alex', 'Q7; Deep Read; Monday Market Brief',
   'items_written = 0 for 3 runs -> FAIL; 0 used items in 4 briefs -> stop, decision issue',
   false, 7, 14),
  ('feeds', 'weekly GitHub Action fetch; Monday session classifies', 'alex', 'Q4, Q6; Monday Market Brief',
   'items_written = 0 for 3 runs -> FAIL; 0 used items in 4 briefs -> stop, decision issue',
   false, 7, 14),
  ('segment_enrichment', 'once per company on first sight, refresh quarterly', 'alex', 'the segment dimension of every slice',
   'Apollo thin and akta over cap -> pause; review at 90 days',
   false, 92, 120)
on conflict (lane) do nothing;

comment on table public.lane_registry is
  'ADR-13: one row per ingestion lane (schedule, owner, consumer, kill rule, freshness thresholds). '
  'Seeded lanes 0-5 of spec §2, inactive; lane 6 (theme_sweep, optional) is added when it is built.';

create table if not exists public.lane_run (
  run_id          uuid primary key default gen_random_uuid(),
  lane            text not null references public.lane_registry(lane),
  started_at      timestamptz not null default now(),
  finished_at     timestamptz,
  status          text not null default 'running'
                    check (status in ('running', 'success', 'partial', 'failed', 'skipped')),
  items_seen      integer not null default 0 check (items_seen >= 0),
  items_written   integer not null default 0 check (items_written >= 0),
  items_refused   integer not null default 0 check (items_refused >= 0),
  credits_spent   numeric not null default 0 check (credits_spent >= 0),
  -- length-capped so a run can't dump a scraped body here; spine_client scans every string too
  error           text check (error is null or char_length(error) <= 1000),
  check (finished_at is null or finished_at >= started_at)
);
create index if not exists lane_run_lane_started_idx
  on public.lane_run (lane, started_at desc);

comment on table public.lane_run is
  'ADR-13: ingestion-lane run ledger. items_written = 0 for 2 runs FLAG, 3 FAIL (spec §3.3).';

-- ---------------------------------------------------------------------
-- 4. event.signal_type — finer than kind, coarser than metadata (spec §3.1). Nullable;
--    no existing row is touched. Constraint is drop-then-add so a re-run is a no-op.
-- ---------------------------------------------------------------------
alter table public.event add column if not exists signal_type text;
alter table public.event drop constraint if exists event_signal_type_check;
alter table public.event add constraint event_signal_type_check check (signal_type is null or signal_type in
  ('hiring_pulse', 'paper', 'model_release', 'news', 'partnership', 'layoff'));
create index if not exists event_signal_type_idx on public.event (signal_type) where signal_type is not null;

-- ---------------------------------------------------------------------
-- 5. Security for the new tables: RLS on, no policies, grant-level path removed.
-- ---------------------------------------------------------------------
alter table public.topic_cluster_membership enable row level security;
alter table public.lane_registry            enable row level security;
alter table public.lane_run                 enable row level security;
alter table public.company_segment_history  enable row level security;

revoke all on public.topic_cluster_membership from public, anon, authenticated;
revoke all on public.lane_registry            from public, anon, authenticated;
revoke all on public.lane_run                 from public, anon, authenticated;
revoke all on public.company_segment_history  from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- 6. Schema mi — the semantic layer. Read-only views; nothing here stores data.
-- ---------------------------------------------------------------------
create schema if not exists mi;
revoke all on schema mi from public, anon, authenticated;
comment on schema mi is
  'ADR-13 semantic layer (conformed dimensions over event + claim). NOT API-exposed. Read through public.mi_slice().';

-- 6a. Lens is derived, never stored (spec §3.1). Order matters:
--     job first (YED-149 isolation wins over everything), then research lane/source (a research
--     claim occasioned by an attended event is still research), then attended, then market kinds.
--     Anything else (reference, published, an occasion-less non-research claim) is NULL = unlensed.
create or replace function mi.lens_of(p_kind text, p_source text, p_lane text)
returns text
language sql
immutable
set search_path = pg_catalog, pg_temp
as $fn$
  select case
    when p_kind in ('role_posted', 'application', 'interview')          then 'job'
    when p_lane = 'research' or p_source like 'substrate:research%'      then 'research'
    when p_kind = 'attended'                                             then 'attended'
    when p_kind in ('market', 'funding', 'launch', 'exec_move')          then 'market'
    else null
  end
$fn$;
revoke all on function mi.lens_of(text, text, text) from public;

-- 6b. Theme as of a timestamp (SCD2 read). 'asof' = a membership row covers p_ts.
--     'seed' = p_ts predates the topic's earliest membership, so the earliest membership is
--     projected back (spec §3.1 pre-history fallback). No row = unassigned at p_ts, or p_ts null.
create or replace function mi.theme_as_of(p_topic_id uuid, p_ts timestamptz)
returns table (cluster_id uuid, theme_resolved text)
language sql
stable
set search_path = pg_catalog, pg_temp
as $fn$
  select u.cluster_id, u.theme_resolved
  from (
    select m.cluster_id, 'asof'::text as theme_resolved, 1 as prio
      from public.topic_cluster_membership m
     where m.topic_id = p_topic_id
       and m.valid_from <= p_ts
       and (m.valid_to is null or p_ts < m.valid_to)
    union all
    select e.cluster_id, 'seed'::text, 2
      from (select m.cluster_id, m.valid_from
              from public.topic_cluster_membership m
             where m.topic_id = p_topic_id
             order by m.valid_from, m.membership_id
             limit 1) e
     where p_ts < e.valid_from
  ) u
  order by u.prio
  limit 1
$fn$;
revoke all on function mi.theme_as_of(uuid, timestamptz) from public;

-- 6c. mi.fact — one row per event or (non-rejected) claim, with the §3.1 dimensions.
--     Claims take kind from their occasion event (null if none). asserted_week is the Monday of
--     the ISO week in UTC, computed once here so every view buckets identically.
create or replace view mi.fact with (security_invoker = on) as
select 'event'::text                                            as fact_type,
       e.id                                                     as fact_id,
       e.id                                                     as occasion_event_id,
       mi.lens_of(e.kind, e.source, null)                       as lens,
       e.kind                                                   as kind,
       e.signal_type                                            as signal_type,
       null::text                                               as lane,
       nullif(split_part(coalesce(e.source, ''), ':', 1), '')   as source_system,
       coalesce(e.url, e.notion_page_id, e.id::text)            as source_ref,
       case when e.source like 'inbox_miner%'                   then 'email_signal'
            when e.kind = 'attended'                            then 'first_hand'
            when e.kind in ('market', 'funding', 'launch', 'exec_move',
                            'role_posted', 'application', 'interview') then 'web_verified'
            else 'reference' end                                as provenance_tier,
       e.event_date                                             as asserted_at,
       date_trunc('week', e.event_date at time zone 'UTC')::date as asserted_week,
       e.created_at                                             as observed_at
from public.event e
union all
select 'claim'::text,
       c.id,
       c.event_id,
       mi.lens_of(oe.kind, null, c.lane),
       oe.kind,
       null::text,
       c.lane,
       'substrate'::text,
       coalesce(c.document_id::text, c.source_key),
       c.provenance_tier,
       c.asserted_at,
       date_trunc('week', c.asserted_at at time zone 'UTC')::date,
       c.created_at
from public.claim c
left join public.event oe on oe.id = c.event_id
where c.status <> 'rejected';

-- 6d. fact × topic × theme-as-of-asserted_at. Direct topic edges only (event_entity any role,
--     claim_entity any role), de-duplicated per (fact, topic). theme_id null = unthemed.
create or replace view mi.fact_topic with (security_invoker = on) as
with edges as (
  select 'event'::text as fact_type, ee.event_id as fact_id, ee.entity_id as topic_id
    from public.event_entity ee where ee.entity_type = 'topic'
  union
  select 'claim'::text, ce.claim_id, ce.entity_id
    from public.claim_entity ce where ce.entity_type = 'topic'
)
select f.fact_type, f.fact_id, f.lens, f.kind, f.signal_type, f.source_ref, f.provenance_tier,
       f.asserted_at, f.asserted_week, f.observed_at,
       ed.topic_id, th.cluster_id as theme_id, th.theme_resolved
from mi.fact f
join edges ed on ed.fact_type = f.fact_type and ed.fact_id = f.fact_id
left join lateral mi.theme_as_of(ed.topic_id, f.asserted_at) th on true;

-- 6e. fact × company (direct company edges only). Helper with four callers below.
create or replace view mi.fact_company with (security_invoker = on) as
with edges as (
  select 'event'::text as fact_type, ee.event_id as fact_id, ee.entity_id as company_id
    from public.event_entity ee where ee.entity_type = 'company'
  union
  select 'claim'::text, ce.claim_id, ce.entity_id
    from public.claim_entity ce where ce.entity_type = 'company'
)
select f.fact_type, f.fact_id, f.lens, f.kind, f.signal_type, f.source_system, f.source_ref,
       f.provenance_tier, f.asserted_at, f.asserted_week, f.observed_at, ed.company_id
from mi.fact f
join edges ed on ed.fact_type = f.fact_type and ed.fact_id = f.fact_id;

-- 6f. mi.theme_week — CONSUMER CONTRACT (ADR-13). One row per theme × lens × ISO week.
--     Columns, in order: theme_id, theme, iso_week ('YYYY-Www'), lens, facts, distinct_companies,
--     distinct_sources, general_facts, floor_flag, theme_resolved. NO total column, by
--     construction (spec §3.3 rule 1). Job lens excluded (YED-149).
--     floor_flag: 'insufficient_data' when the theme × lens has < 3 facts in the trailing 8 ISO
--     weeks ending at this row's week (0012's floor), else 'ok'. When floor_flag is
--     'insufficient_data', `facts` is still returned but CONSUMERS MUST NOT RENDER IT.
--     theme_resolved: 'seed' if ANY fact in the cell took its theme from the pre-history
--     fallback, else 'asof' (conservative: the label a brief must print).
--     general_facts: facts tagged to the theme's '<Theme> (general)' topic.
--     iso_week sorts lexically = chronologically, so window filters compare strings.
create or replace view mi.theme_week with (security_invoker = on) as
with tagged as (
  select ft.*, coalesce(t.name ~ ' \(general\)$', false) as is_general
  from mi.fact_topic ft
  join public.topic t on t.id = ft.topic_id
  where ft.theme_id is not null and ft.asserted_week is not null
    and ft.lens in ('attended', 'research', 'market')
),
cell as (
  select g.theme_id, g.lens, g.asserted_week as week_start,
         count(distinct (g.fact_type, g.fact_id))                                as facts,
         count(distinct g.source_ref)                                            as distinct_sources,
         count(distinct (g.fact_type, g.fact_id)) filter (where g.is_general)    as general_facts,
         case when bool_or(g.theme_resolved = 'seed') then 'seed' else 'asof' end as theme_resolved
  from tagged g
  group by g.theme_id, g.lens, g.asserted_week
),
comp as (
  select g.theme_id, g.lens, g.asserted_week as week_start, count(distinct fc.company_id) as distinct_companies
  from tagged g
  join mi.fact_company fc on fc.fact_type = g.fact_type and fc.fact_id = g.fact_id
  group by g.theme_id, g.lens, g.asserted_week
)
select c.theme_id,
       tc.display_name                                   as theme,
       to_char(c.week_start, 'IYYY-"W"IW')               as iso_week,
       c.lens,
       c.facts,
       coalesce(k.distinct_companies, 0)::bigint         as distinct_companies,
       c.distinct_sources,
       c.general_facts,
       case when sum(c.facts) over w < 3 then 'insufficient_data' else 'ok' end as floor_flag,
       c.theme_resolved
from cell c
join topic_intelligence.topic_cluster tc on tc.cluster_id = c.theme_id
left join comp k on k.theme_id = c.theme_id and k.lens = c.lens and k.week_start = c.week_start
window w as (partition by c.theme_id, c.lens order by c.week_start
             range between interval '49 days' preceding and current row);

-- 6g. mi.theme_lead_lag — CONSUMER CONTRACT (ADR-13). One row per theme.
--     Columns: theme_id, theme, market_first_seen, attended_first_seen, market_lead_weeks,
--     attended_count_8w, market_count_8w, lead_lag_shown.
--     market_lead_weeks = (attended_first_seen − market_first_seen) in weeks.
--     POSITIVE MEANS THE MARKET LED. Counts are the trailing 8 ISO weeks ending in the week of
--     current_date (anchored on today, so a stalled pipeline reads as stale).
--     lead_lag_shown = both lenses clear the floor (>= 3 facts in those 8 weeks). When false,
--     market_lead_weeks is still returned but consumers must not render it.
--     The permutation band (band_low / band_high, spec §7) is Phase B and is not here.
create or replace view mi.theme_lead_lag with (security_invoker = on) as
with bounds as (
  select date_trunc('week', current_date::timestamp)::date as to_monday
),
per_lens as (
  select ft.theme_id, ft.lens,
         min(ft.asserted_at) as first_seen,
         count(distinct (ft.fact_type, ft.fact_id))
           filter (where ft.asserted_week between b.to_monday - 49 and b.to_monday) as count_8w
  from mi.fact_topic ft cross join bounds b
  where ft.theme_id is not null and ft.asserted_at is not null
    and ft.lens in ('attended', 'market')
  group by ft.theme_id, ft.lens
)
select tc.cluster_id                       as theme_id,
       tc.display_name                     as theme,
       m.first_seen                        as market_first_seen,
       a.first_seen                        as attended_first_seen,
       round((extract(epoch from (a.first_seen - m.first_seen)) / 604800.0)::numeric, 1) as market_lead_weeks,
       coalesce(a.count_8w, 0)             as attended_count_8w,
       coalesce(m.count_8w, 0)             as market_count_8w,
       (coalesce(a.count_8w, 0) >= 3 and coalesce(m.count_8w, 0) >= 3) as lead_lag_shown
from topic_intelligence.topic_cluster tc
left join per_lens a on a.theme_id = tc.cluster_id and a.lens = 'attended'
left join per_lens m on m.theme_id = tc.cluster_id and m.lens = 'market';

-- 6h. company × lens × ISO week (job lens excluded, as everywhere in mi).
create or replace view mi.company_timeline with (security_invoker = on) as
select fc.company_id, c.name as company_name, fc.lens,
       to_char(fc.asserted_week, 'IYYY-"W"IW')                             as iso_week,
       count(distinct (fc.fact_type, fc.fact_id))                         as facts,
       array_agg(distinct fc.kind)        filter (where fc.kind is not null)        as kinds,
       array_agg(distinct fc.signal_type) filter (where fc.signal_type is not null) as signal_types,
       count(distinct fc.source_ref)                                      as distinct_sources,
       min(fc.asserted_at) as first_asserted_at, max(fc.asserted_at) as last_asserted_at
from mi.fact_company fc
join public.company c on c.id = fc.company_id
where fc.lens in ('attended', 'research', 'market') and fc.asserted_week is not null
group by fc.company_id, c.name, fc.lens, fc.asserted_week;

-- 6i. company cohort: first-seen quarter per lens (UTC), CURRENT segment (open row), target flag.
--     Merge tombstones excluded.
create or replace view mi.company_cohort with (security_invoker = on) as
with firsts as (
  select fc.company_id,
         min(fc.asserted_at)                                        as first_seen_any,
         min(fc.asserted_at) filter (where fc.lens = 'attended')    as first_seen_attended,
         min(fc.asserted_at) filter (where fc.lens = 'research')    as first_seen_research,
         min(fc.asserted_at) filter (where fc.lens = 'market')      as first_seen_market
  from mi.fact_company fc
  where fc.lens in ('attended', 'research', 'market') and fc.asserted_at is not null
  group by fc.company_id
)
select c.id as company_id, c.name as company_name,
       f.first_seen_any,
       to_char(f.first_seen_any      at time zone 'UTC', 'YYYY-"Q"Q') as first_seen_quarter,
       to_char(f.first_seen_attended at time zone 'UTC', 'YYYY-"Q"Q') as first_seen_attended_quarter,
       to_char(f.first_seen_research at time zone 'UTC', 'YYYY-"Q"Q') as first_seen_research_quarter,
       to_char(f.first_seen_market   at time zone 'UTC', 'YYYY-"Q"Q') as first_seen_market_quarter,
       s.stage, s.industry, s.headcount_band, s.hq_metro,
       coalesce(s.target_tier, c.metadata->>'target_tier') as target_tier
from firsts f
join public.company c on c.id = f.company_id
left join public.company_segment_history s on s.company_id = c.id and s.valid_to is null
where not coalesce(c.metadata ? 'merged_into', false);

-- 6j. hiring around a theme (Q2): companies with market-lens facts on the theme in the last
--     8 weeks ⋈ their latest hiring_pulse (counts only) ⋈ attended presence (counts only;
--     no person names or ids leave this view). Empty until lane 1 writes hiring_pulse events.
create or replace view mi.hiring_around_theme with (security_invoker = on) as
with theme_co as (
  select ft.theme_id, fc.company_id,
         count(distinct (ft.fact_type, ft.fact_id)) as market_facts_8w,
         max(ft.asserted_at)                        as last_market_fact_at
  from mi.fact_topic ft
  join mi.fact_company fc on fc.fact_type = ft.fact_type and fc.fact_id = ft.fact_id
  where ft.lens = 'market' and ft.theme_id is not null
    and ft.asserted_at >= now() - interval '56 days'
  group by ft.theme_id, fc.company_id
),
pulse as (
  select distinct on (ee.entity_id)
         ee.entity_id as company_id, e.event_date as pulse_date,
         case when e.metadata->>'roles_open'   ~ '^\d+$'  then (e.metadata->>'roles_open')::int   end as roles_open,
         case when e.metadata->>'gtm_roles'    ~ '^\d+$'  then (e.metadata->>'gtm_roles')::int    end as gtm_roles,
         case when e.metadata->>'ai_gtm_roles' ~ '^\d+$'  then (e.metadata->>'ai_gtm_roles')::int end as ai_gtm_roles,
         case when e.metadata->>'delta_wow'    ~ '^-?\d+$' then (e.metadata->>'delta_wow')::int   end as delta_wow
  from public.event e
  join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
  where e.signal_type = 'hiring_pulse'
  order by ee.entity_id, e.event_date desc nulls last, e.created_at desc
),
presence as (
  select x.company_id, count(distinct x.event_id) as attended_events,
         count(distinct x.person_id) as attended_speakers
  from (
    select ee.entity_id as company_id, e.id as event_id, null::uuid as person_id
      from public.event e
      join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
     where e.kind = 'attended'
    union all
    select p.company_id, e.id, p.id
      from public.event e
      join public.event_entity sp on sp.event_id = e.id and sp.entity_type = 'person'
                                  and sp.role in ('speaker', 'host', 'panelist')
      join public.person p on p.id = sp.entity_id
     where e.kind = 'attended' and p.company_id is not null
  ) x
  group by x.company_id
)
select tco.theme_id, tc.display_name as theme, tco.company_id, c.name as company_name,
       tco.market_facts_8w, tco.last_market_fact_at,
       pu.pulse_date, pu.roles_open, pu.gtm_roles, pu.ai_gtm_roles, pu.delta_wow,
       coalesce(pr.attended_events, 0) as attended_events,
       coalesce(pr.attended_speakers, 0) as attended_speakers
from theme_co tco
join topic_intelligence.topic_cluster tc on tc.cluster_id = tco.theme_id
join public.company c on c.id = tco.company_id
left join pulse pu on pu.company_id = tco.company_id
left join presence pr on pr.company_id = tco.company_id;

-- ---------------------------------------------------------------------
-- 7. public.mi_slice(view, filters) — the one door. CONSUMER CONTRACT (ADR-13).
--    view    : one of mi.theme_week, mi.theme_lead_lag, mi.company_timeline, mi.company_cohort,
--              mi.hiring_around_theme. Anything else raises.
--    filters : weeks (1..104, default 8) · lens (attended|research|market) · theme_id (uuid) ·
--              company_id (uuid) · limit (1..5000, default 1000). Unknown keys raise.
--    returns : {"view", "rows": [...], "denominators": {attended:{events}, research:{briefs},
--               market:{facts_by_source, watchlist_covered, watchlist_size}, job:{boards_scanned}},
--               "window": {"from_week", "to_week", "anchored_on"}}
--    The window is the `weeks` ISO weeks ending in the week of current_date (anchored on today,
--    never on the latest row). It filters rows of the week-grained views (theme_week,
--    company_timeline) and scopes every denominator. theme_lead_lag and hiring_around_theme
--    carry their own fixed 8-week windows; company_cohort is all-time.
--    Denominators are computed here, in SQL, never client-side. They bucket on asserted_week,
--    the same basis as the rows.
-- ---------------------------------------------------------------------
create or replace function public.mi_slice(view text, filters jsonb default '{}'::jsonb)
returns jsonb
language plpgsql
stable
security definer
set search_path = pg_catalog, pg_temp
as $fn$
declare
  v_view       text  := mi_slice.view;
  f            jsonb := coalesce(mi_slice.filters, '{}'::jsonb);
  p_weeks      int;
  p_lens       text;
  p_theme      uuid;
  p_co         uuid;
  p_limit      int;
  v_anchor     date := current_date;
  v_to_mon     date;
  v_from_mon   date;
  v_from_week  text;
  v_to_week    text;
  v_rows       jsonb;
  v_den        jsonb;
begin
  if jsonb_typeof(f) <> 'object' then
    raise exception 'mi_slice: filters must be a json object';
  end if;
  if exists (select 1 from jsonb_object_keys(f) k
              where k not in ('weeks', 'lens', 'theme_id', 'company_id', 'limit')) then
    raise exception 'mi_slice: unknown filter key(s); allowed: weeks, lens, theme_id, company_id, limit';
  end if;
  p_weeks := least(greatest(coalesce((f->>'weeks')::int, 8), 1), 104);
  p_lens  := f->>'lens';
  p_theme := (f->>'theme_id')::uuid;
  p_co    := (f->>'company_id')::uuid;
  p_limit := least(greatest(coalesce((f->>'limit')::int, 1000), 1), 5000);
  if p_lens is not null and p_lens not in ('attended', 'research', 'market') then
    raise exception 'mi_slice: lens must be attended, research or market';
  end if;

  v_to_mon    := date_trunc('week', v_anchor::timestamp)::date;
  v_from_mon  := v_to_mon - 7 * (p_weeks - 1);
  v_from_week := to_char(v_from_mon, 'IYYY-"W"IW');
  v_to_week   := to_char(v_to_mon,   'IYYY-"W"IW');

  case v_view
  when 'mi.theme_week' then
    select coalesce(jsonb_agg(to_jsonb(x) order by x.iso_week desc, x.theme, x.lens), '[]'::jsonb) into v_rows
    from (select t.* from mi.theme_week t
           where t.iso_week between v_from_week and v_to_week
             and (p_theme is null or t.theme_id = p_theme)
             and (p_lens  is null or t.lens = p_lens)
           order by t.iso_week desc, t.theme, t.lens limit p_limit) x;

  when 'mi.theme_lead_lag' then
    select coalesce(jsonb_agg(to_jsonb(x) order by x.theme), '[]'::jsonb) into v_rows
    from (select t.* from mi.theme_lead_lag t
           where (p_theme is null or t.theme_id = p_theme)
           order by t.theme limit p_limit) x;

  when 'mi.company_timeline' then
    select coalesce(jsonb_agg(to_jsonb(x) order by x.iso_week desc, x.company_name, x.lens), '[]'::jsonb) into v_rows
    from (select t.* from mi.company_timeline t
           where t.iso_week between v_from_week and v_to_week
             and (p_co   is null or t.company_id = p_co)
             and (p_lens is null or t.lens = p_lens)
           order by t.iso_week desc, t.company_name, t.lens limit p_limit) x;

  when 'mi.company_cohort' then
    select coalesce(jsonb_agg(to_jsonb(x) order by x.first_seen_any desc, x.company_name), '[]'::jsonb) into v_rows
    from (select t.* from mi.company_cohort t
           where (p_co is null or t.company_id = p_co)
           order by t.first_seen_any desc, t.company_name limit p_limit) x;

  when 'mi.hiring_around_theme' then
    select coalesce(jsonb_agg(to_jsonb(x) order by x.theme, x.market_facts_8w desc), '[]'::jsonb) into v_rows
    from (select t.* from mi.hiring_around_theme t
           where (p_theme is null or t.theme_id = p_theme)
             and (p_co    is null or t.company_id = p_co)
           order by t.theme, t.market_facts_8w desc limit p_limit) x;

  else
    raise exception 'mi_slice: view % is not in the allowlist (ADR-13)', quote_literal(v_view);
  end case;

  -- Denominators per lens for the window (spec §3.3 rule 2). Never summed across lenses.
  -- watchlist = non-tombstoned companies carrying a target tier (open segment row, else
  -- company.metadata.target_tier); 0 until lane 5 / the target flag lands.
  -- boards_scanned = distinct companies with a job-lens posting observed in the window (the
  -- job lens has no scan ledger; see ADR-13 open questions).
  with win as (
    select * from mi.fact where asserted_week between v_from_mon and v_to_mon
  ),
  watch as (
    select c.id
      from public.company c
      left join public.company_segment_history s on s.company_id = c.id and s.valid_to is null
     where coalesce(s.target_tier, c.metadata->>'target_tier') is not null
       and not coalesce(c.metadata ? 'merged_into', false)
  )
  select jsonb_build_object(
    'attended', jsonb_build_object(
       'events', (select count(*) from win where fact_type = 'event' and lens = 'attended')),
    'research', jsonb_build_object(
       'briefs', (select count(distinct source_ref) from win where fact_type = 'claim' and lens = 'research')),
    'market', jsonb_build_object(
       'facts_by_source', coalesce((select jsonb_object_agg(s.src, s.n)
                                      from (select coalesce(source_system, 'unknown') as src, count(*) as n
                                              from win where lens = 'market' group by 1) s), '{}'::jsonb),
       'watchlist_covered', (select count(distinct fc.company_id)
                               from mi.fact_company fc join watch w on w.id = fc.company_id
                              where fc.lens = 'market' and fc.asserted_week between v_from_mon and v_to_mon),
       'watchlist_size', (select count(*) from watch)),
    'job', jsonb_build_object(
       'boards_scanned', (select count(distinct fc.company_id) from mi.fact_company fc
                           where fc.lens = 'job' and fc.asserted_week between v_from_mon and v_to_mon))
  ) into v_den;

  return jsonb_build_object(
    'view', v_view,
    'rows', v_rows,
    'denominators', v_den,
    'window', jsonb_build_object('from_week', v_from_week, 'to_week', v_to_week, 'anchored_on', v_anchor));
end;
$fn$;

revoke all on function public.mi_slice(text, jsonb) from public, anon, authenticated;
grant execute on function public.mi_slice(text, jsonb) to service_role;

comment on function public.mi_slice(text, jsonb) is
  'ADR-13: the one reader over schema mi. Five allowlisted views; returns {view, rows, denominators, window}. service_role only.';

commit;

-- =====================================================================
-- VERIFY (read-only). Each statement returns one row: <check name> | <t/f>. Every row must be t.
-- rehearse_0016.py parses the block between the markers; keep one check per statement, one line each.
-- =====================================================================
-- VERIFY:BEGIN
-- select 'mi_schema_exists', to_regnamespace('mi') is not null;
-- select 'mi_no_api_usage', not has_schema_privilege('anon', 'mi', 'usage') and not has_schema_privilege('authenticated', 'mi', 'usage');
-- select 'membership_one_open_index', exists (select 1 from pg_indexes where schemaname = 'public' and indexname = 'topic_cluster_membership_one_open_uq');
-- select 'membership_one_open_rows', not exists (select 1 from public.topic_cluster_membership where valid_to is null group by topic_id having count(*) > 1);
-- select 'membership_no_overlap', not exists (select 1 from public.topic_cluster_membership a join public.topic_cluster_membership b on a.topic_id = b.topic_id and a.membership_id <> b.membership_id and a.valid_from < coalesce(b.valid_to, 'infinity') and b.valid_from < coalesce(a.valid_to, 'infinity'));
-- select 'membership_no_tombstones', not exists (select 1 from public.topic_cluster_membership m join public.topic t on t.id = m.topic_id where m.valid_to is null and coalesce(t.metadata ? 'merged_into', false));
-- select 'membership_seed_parity', (select count(*) from public.topic t where t.cluster_id is not null and not coalesce(t.metadata ? 'merged_into', false)) = (select count(*) from public.topic_cluster_membership m join public.topic t on t.id = m.topic_id where m.valid_to is null and m.cluster_id = t.cluster_id);
-- select 'membership_seed_nonempty', exists (select 1 from public.topic_cluster_membership where change_kind = 'seed');
-- select 'theme_as_of_seed', coalesce((select th.theme_resolved = 'seed' and th.cluster_id = m.cluster_id from (select topic_id, cluster_id from public.topic_cluster_membership where valid_to is null order by topic_id limit 1) m cross join lateral mi.theme_as_of(m.topic_id, timestamptz '2012-07-10 00:00:00+00') th), false);
-- select 'theme_as_of_asof', coalesce((select th.theme_resolved = 'asof' and th.cluster_id = m.cluster_id from (select topic_id, cluster_id from public.topic_cluster_membership where valid_to is null order by topic_id limit 1) m cross join lateral mi.theme_as_of(m.topic_id, now()) th), false);
-- select 'theme_as_of_null_ts', not exists (select 1 from (select topic_id from public.topic_cluster_membership order by topic_id limit 1) m cross join lateral mi.theme_as_of(m.topic_id, null) th);
-- select 'lens_of_truth_table', mi.lens_of('attended', null, null) = 'attended' and mi.lens_of('attended', null, 'research') = 'research' and mi.lens_of('role_posted', 'substrate:research', 'research') = 'job' and mi.lens_of('funding', 'akta', null) = 'market' and mi.lens_of(null, 'substrate:research', null) = 'research' and mi.lens_of('published', null, null) is null and mi.lens_of(null, null, 'A') is null;
-- select 'lens_of_immutable', (select provolatile = 'i' from pg_proc where oid = 'mi.lens_of(text,text,text)'::regprocedure);
-- select 'lane_registry_seeded', (select count(*) = 6 and bool_and(not active) from public.lane_registry where lane in ('corpus_mine', 'hiring_pulse', 'company_signals', 'research_frontier', 'feeds', 'segment_enrichment'));
-- select 'lane_run_contract_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'run_id,lane,started_at,finished_at,status,items_seen,items_written,items_refused,credits_spent,error' from information_schema.columns where table_schema = 'public' and table_name = 'lane_run');
-- select 'lane_run_fk_registry', exists (select 1 from pg_constraint where conrelid = 'public.lane_run'::regclass and contype = 'f' and confrelid = 'public.lane_registry'::regclass);
-- select 'new_tables_rls_on', (select bool_and(relrowsecurity) from pg_class where oid in ('public.topic_cluster_membership'::regclass, 'public.lane_registry'::regclass, 'public.lane_run'::regclass, 'public.company_segment_history'::regclass));
-- select 'new_tables_no_policies', not exists (select 1 from pg_policies where (schemaname, tablename) in (('public', 'topic_cluster_membership'), ('public', 'lane_registry'), ('public', 'lane_run'), ('public', 'company_segment_history')));
-- select 'new_tables_no_api_grants', not exists (select 1 from unnest(array['public.topic_cluster_membership', 'public.lane_registry', 'public.lane_run', 'public.company_segment_history']) t cross join unnest(array['anon', 'authenticated']) r where has_table_privilege(r, t, 'select') or has_table_privilege(r, t, 'insert') or has_table_privilege(r, t, 'update') or has_table_privilege(r, t, 'delete'));
-- select 'no_pii_columns', not exists (select 1 from information_schema.columns where ((table_schema = 'public' and table_name in ('topic_cluster_membership', 'lane_registry', 'lane_run', 'company_segment_history')) or table_schema = 'mi') and column_name ~* '(e_?mail|phone|mobile|telephone|contact|address|linkedin)');
-- select 'event_signal_type_check', (select pg_get_constraintdef(oid) ~ 'hiring_pulse' and pg_get_constraintdef(oid) ~ 'paper' and pg_get_constraintdef(oid) ~ 'model_release' and pg_get_constraintdef(oid) ~ 'news' and pg_get_constraintdef(oid) ~ 'partnership' and pg_get_constraintdef(oid) ~ 'layoff' from pg_constraint where conrelid = 'public.event'::regclass and conname = 'event_signal_type_check');
-- select 'event_signal_type_nullable', (select is_nullable = 'YES' from information_schema.columns where table_schema = 'public' and table_name = 'event' and column_name = 'signal_type');
-- select 'fact_row_parity', (select count(*) from mi.fact) = (select count(*) from public.event) + (select count(*) from public.claim where status <> 'rejected');
-- select 'theme_week_contract_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'theme_id,theme,iso_week,lens,facts,distinct_companies,distinct_sources,general_facts,floor_flag,theme_resolved' from information_schema.columns where table_schema = 'mi' and table_name = 'theme_week');
-- select 'theme_week_no_job_lens', not exists (select 1 from mi.theme_week where lens not in ('attended', 'research', 'market'));
-- select 'theme_week_flag_values', not exists (select 1 from mi.theme_week where floor_flag not in ('ok', 'insufficient_data') or theme_resolved not in ('asof', 'seed'));
-- select 'theme_lead_lag_contract_columns', (select string_agg(column_name, ',' order by ordinal_position) = 'theme_id,theme,market_first_seen,attended_first_seen,market_lead_weeks,attended_count_8w,market_count_8w,lead_lag_shown' from information_schema.columns where table_schema = 'mi' and table_name = 'theme_lead_lag');
-- select 'mi_slice_stable_definer_pinned', (select provolatile = 's' and prosecdef and array_to_string(proconfig, ',') ~ '^search_path=' from pg_proc where oid = 'public.mi_slice(text,jsonb)'::regprocedure);
-- select 'mi_slice_arg_names', (select proargnames = array['view', 'filters'] from pg_proc where oid = 'public.mi_slice(text,jsonb)'::regprocedure);
-- select 'mi_slice_no_public_exec', (select proacl is not null and not exists (select 1 from aclexplode(proacl) a where a.grantee = 0 and a.privilege_type = 'EXECUTE') from pg_proc where oid = 'public.mi_slice(text,jsonb)'::regprocedure);
-- select 'mi_slice_exec_denied', not has_function_privilege('anon', 'public.mi_slice(text,jsonb)', 'execute') and not has_function_privilege('authenticated', 'public.mi_slice(text,jsonb)', 'execute');
-- select 'mi_slice_exec_service_role_only', has_function_privilege('service_role', 'public.mi_slice(text,jsonb)', 'execute') and not has_function_privilege('pipeline_writer', 'public.mi_slice(text,jsonb)', 'execute');
-- select 'mi_slice_envelope', (select bool_and(jsonb_typeof(r->'rows') = 'array' and r->>'view' = n and r->'denominators' ?& array['attended', 'research', 'market', 'job'] and r->'denominators'->'market' ?& array['facts_by_source', 'watchlist_covered', 'watchlist_size'] and r->'window' ?& array['from_week', 'to_week', 'anchored_on'] and r->'window'->>'to_week' = to_char(current_date, 'IYYY-"W"IW')) from unnest(array['mi.theme_week', 'mi.theme_lead_lag', 'mi.company_timeline', 'mi.company_cohort', 'mi.hiring_around_theme']) n cross join lateral (select public.mi_slice(n, '{"limit": 3}'::jsonb) as r) s);
-- select 'topic_sync_triggers_present', (select count(*) = 2 from pg_trigger where tgrelid = 'public.topic'::regclass and not tgisinternal and tgname in ('topic_membership_sync_ins', 'topic_membership_sync_upd') and tgenabled <> 'D');
-- select 'topic_sync_definer_pinned', (select prosecdef and array_to_string(proconfig, ',') ~ '^search_path=' from pg_proc where oid = 'public.topic_membership_sync()'::regprocedure);
-- select 'topic_sync_no_api_exec', not has_function_privilege('anon', 'public.topic_membership_sync()', 'execute') and not has_function_privilege('authenticated', 'public.topic_membership_sync()', 'execute');
-- select 'info_tombstones_with_cluster_id', (select count(*)::text from public.topic where cluster_id is not null and coalesce(metadata ? 'merged_into', false));
-- VERIFY:END
--
-- info_* rows are INFORMATIONAL: they print a value and never fail the gate. On prod the
-- tombstone count is 14 (2026-11-04); the seed excludes them, which is correct.
--
-- =====================================================================
-- VERIFY_TWIN (behavioural; TWIN ONLY — every write is inside a transaction that is ROLLED BACK).
-- Not part of the prod verify: the prod VERIFY block above stays read-only. rehearse_0016.py runs
-- this after VERIFY. It reassigns one seeded topic, re-sets the same cluster, nulls it, reopens it,
-- tombstones it, inserts a new clustered topic, and checks open-row parity after each step.
-- =====================================================================
-- VERIFY_TWIN:BEGIN
-- begin;
-- create temp table _v0016 on commit drop as select m.topic_id, m.cluster_id as old_cluster, (select c.cluster_id from topic_intelligence.topic_cluster c where c.cluster_id <> m.cluster_id order by c.cluster_id limit 1) as new_cluster from public.topic_cluster_membership m where m.valid_to is null order by m.topic_id limit 1;
-- select 'trig_fixture_ready', (select count(*) = 1 and bool_and(new_cluster is not null) from _v0016);
-- update public.topic t set cluster_id = v.new_cluster, cluster_assigned_by = 'session', cluster_assignment_confidence = 0.900 from _v0016 v where t.id = v.topic_id;
-- select 'trig_reassign_parity', (select count(*) = 1 and bool_and(m.cluster_id = v.new_cluster and m.change_kind = 'reassign' and m.assigned_by = 'session' and m.confidence = 0.900) from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id where m.valid_to is null) and (select count(*) = 1 from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id where m.valid_to is not null and m.cluster_id = v.old_cluster);
-- update public.topic t set cluster_id = v.new_cluster from _v0016 v where t.id = v.topic_id;
-- select 'trig_unchanged_is_noop', (select count(*) = 2 from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id);
-- update public.topic t set cluster_id = null from _v0016 v where t.id = v.topic_id;
-- select 'trig_null_closes', (select count(*) = 0 from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id where m.valid_to is null) and (select count(*) = 2 from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id);
-- update public.topic t set cluster_id = v.old_cluster, cluster_assigned_by = 'human' from _v0016 v where t.id = v.topic_id;
-- select 'trig_reopen_assign', (select count(*) = 1 and bool_and(m.cluster_id = v.old_cluster and m.change_kind = 'assign' and m.assigned_by = 'human') from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id where m.valid_to is null);
-- update public.topic t set metadata = coalesce(t.metadata, '{}'::jsonb) || '{"merged_into": "00000000-0000-0000-0000-000000000000"}'::jsonb from _v0016 v where t.id = v.topic_id;
-- select 'trig_tombstone_closes', (select count(*) = 0 from public.topic_cluster_membership m join _v0016 v on v.topic_id = m.topic_id where m.valid_to is null);
-- insert into public.topic (name, cluster_id, cluster_assigned_by) select '__verify_0016_topic__', v.old_cluster, 'session' from _v0016 v;
-- select 'trig_insert_opens', (select count(*) = 1 and bool_and(m.change_kind = 'assign' and m.valid_to is null) from public.topic_cluster_membership m join public.topic t on t.id = m.topic_id where t.name = '__verify_0016_topic__');
-- select 'trig_global_parity', (select count(*) from public.topic t where t.cluster_id is not null and not coalesce(t.metadata ? 'merged_into', false)) = (select count(*) from public.topic_cluster_membership m join public.topic t on t.id = m.topic_id where m.valid_to is null and m.cluster_id = t.cluster_id) and not exists (select 1 from public.topic_cluster_membership m join public.topic t on t.id = m.topic_id where m.valid_to is null and (t.cluster_id is null or t.cluster_id <> m.cluster_id or coalesce(t.metadata ? 'merged_into', false)));
-- select 'trig_intervals_valid', not exists (select 1 from public.topic_cluster_membership where valid_to is not null and valid_to <= valid_from);
-- rollback;
-- VERIFY_TWIN:END
--
-- Behavioural checks to run by hand on the twin (they raise, so they are not in the block):
--   select public.mi_slice('mi.fact', '{}');                     -- ERROR: not in the allowlist
--   select public.mi_slice('mi.theme_week', '{"sql": "x"}');     -- ERROR: unknown filter key(s)
--   begin;
--   insert into public.topic_cluster_membership (topic_id, cluster_id, valid_from, assigned_by)
--     select topic_id, cluster_id, now(), 'human' from public.topic_cluster_membership
--      where valid_to is null limit 1;                            -- ERROR: one_open_uq
--   rollback;
--   insert into public.lane_run (lane) values ('not_a_lane');   -- ERROR: FK to lane_registry

-- =====================================================================
-- ROLLBACK (drops only what 0016 adds, in dependency order). Rows in the four new tables and
-- any event.signal_type values are lost; before any lane has written, that is the seeds only.
-- rehearse_0016.py parses the block between the markers.
-- =====================================================================
-- ROLLBACK:BEGIN
-- begin;
-- drop trigger if exists topic_membership_sync_upd on public.topic;
-- drop trigger if exists topic_membership_sync_ins on public.topic;
-- drop function if exists public.topic_membership_sync();
-- drop function if exists public.mi_slice(text, jsonb);
-- drop view if exists mi.hiring_around_theme;
-- drop view if exists mi.company_cohort;
-- drop view if exists mi.company_timeline;
-- drop view if exists mi.theme_lead_lag;
-- drop view if exists mi.theme_week;
-- drop view if exists mi.fact_company;
-- drop view if exists mi.fact_topic;
-- drop view if exists mi.fact;
-- drop function if exists mi.theme_as_of(uuid, timestamptz);
-- drop function if exists mi.lens_of(text, text, text);
-- drop schema if exists mi;
-- drop index if exists public.event_signal_type_idx;
-- alter table public.event drop constraint if exists event_signal_type_check;
-- alter table public.event drop column if exists signal_type;
-- drop table if exists public.lane_run;
-- drop table if exists public.lane_registry;
-- drop table if exists public.company_segment_history;
-- drop table if exists public.topic_cluster_membership;
-- commit;
-- ROLLBACK:END
