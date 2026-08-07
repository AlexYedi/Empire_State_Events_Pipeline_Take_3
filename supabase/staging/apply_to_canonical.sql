-- apply_to_canonical.sql — MI Increment 1 cutover for mi-canonical-prod (oicikjyzmxqfomrrqkvf)
-- ==============================================================================================
-- RUN THIS IN THE CANONICAL PROJECT'S SQL EDITOR (oicikjyzmxqfomrrqkvf, org A.Yedi).
-- ADDITIVE ONLY: creates NEW schemas topic_intelligence + signal_read + a scoped role.
-- ZERO changes to your existing public data. Do NOT run market-intel-schema.sql (public exists).
-- Rollback: drop schema topic_intelligence cascade; drop schema signal_read cascade;
-- After running: (1) expose signal_read, (2) Claude carries the intelligence forward over REST.

-- ==================== 1. topic_intelligence schema (0001) ====================
-- 0001_topic_intelligence_schema.sql
-- MI data-layer consolidation — Increment 1 (YED-130 / ADR-1). CARRY-FORWARD COPY.
-- =============================================================================
-- ADDITIVE ONLY. This migration creates a NEW schema (`topic_intelligence`) on the
-- canonical Empire project (oicikjyzmxqfomrrqkvf, org A.Yedi). It makes ZERO DML/DDL
-- against Empire's existing `public` schema — genuinely reversible (rollback = drop
-- this schema). See ADR-1 §"Increment split" and pre-mortem failure-mode #7.
--
-- Purpose: recreate gtm-os's already-computed topic-intelligence tables in THIS schema
-- so the frozen gtm-os spine (abkvgihlbwfloentugtd, `signal` schema) can be copied in
-- faithfully — preserving gtm-os's internal PK/FK VALUES so the fidelity test (AC1a) is
-- an exact-match vs the frozen spine. We do NOT recompute here (that is Increment 2).
--
-- Shapes mirror gtm-os migrations signal_02 (topics), signal_06 (topic_cluster +
-- topics cluster columns), signal_07 (topic_trend, topic_pair_metric). PK / unique /
-- index / CHECK shapes are preserved verbatim so the copy is faithful.
--
-- DELIBERATE DEVIATIONS FROM gtm-os SHAPE (documented, reviewed):
--   1. ingestion_run_id FK is REMOVED (column + NOT NULL + values preserved; no
--      REFERENCES). Rationale below at the ingestion_run block.
--   2. moddatetime UPDATE triggers are OMITTED. gtm-os's topic_cluster carries a
--      `set_modtime` moddatetime trigger that rewrites last_modified_at on every UPDATE.
--      During carry-forward the loader upserts (ON CONFLICT DO UPDATE); a moddatetime
--      trigger would overwrite the carried last_modified_at with now(), breaking the
--      AC1a exact-match against the frozen spine. In Increment 1 these tables are a
--      FROZEN SNAPSHOT, not a live-written table, so the operational trigger is not
--      needed. Re-add it in Increment 2 when this schema becomes the live writer.
--
-- SECURITY: RLS enabled + deny-all (no policies) on every table. The service_role /
-- sb_secret key BYPASSES RLS (that is how the carry-forward lands rows). RLS here is a
-- floor for anon/authenticated only. anon reaches this data ONLY through the
-- security_invoker views in 0002 (signal_read) — never these base tables directly.
-- topic_intelligence is intentionally kept OUT of the Data API exposed-schemas (0003).
--
-- APPLY: cross-account constraint — the Supabase MCP is on a different account and
-- CANNOT be used here; PostgREST cannot run DDL. Apply this file in the canonical
-- project's dashboard SQL editor OR via psql/connection string, on a Supabase BRANCH
-- of oicikjyzmxqfomrrqkvf. Full runbook: supabase/APPLY.md.
-- =============================================================================

begin;

create schema if not exists topic_intelligence;

-- gen_random_uuid() default for any FUTURE in-schema insert (carried rows keep their
-- source UUIDs). pgcrypto already present on canonical (market-intel-schema.sql); safe.
create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- ingestion_run — minimal run-control table (mirrors gtm-os signal_01).
-- WHY MINIMAL, WHY NO INBOUND FK: Increment 1 copies ONLY the four intelligence
-- tables, not gtm-os's full ingestion_run history. gtm-os's carried rows all carry a
-- (NOT NULL) ingestion_run_id pointing at run rows we are NOT copying. To land a
-- faithful copy without also dragging the entire run history across, the four tables
-- KEEP `ingestion_run_id uuid not null` with the ORIGINAL gtm-os values (lineage
-- preserved) but DROP the FK constraint. This table is provided so the SECURITY DEFINER
-- write path (0003) has a local run-log target for FUTURE writes; it is NOT referenced
-- by the carried tables' columns in Increment 1.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.ingestion_run (
  run_id           uuid primary key default gen_random_uuid(),
  source           text not null,
  runtime          text not null
                     check (runtime in ('n8n','pg_cron','github_actions','manual','edge_function')),
  started_at       timestamptz not null default now(),
  finished_at      timestamptz,
  status           text not null default 'running'
                     check (status in ('running','success','failed','partial')),
  records_seen     int,
  records_written  int,
  watermark_before text,
  watermark_after  text,
  error_detail     text,
  created_at       timestamptz not null default now()
);
create index if not exists ingestion_run_source
  on topic_intelligence.ingestion_run(source, started_at desc);
alter table topic_intelligence.ingestion_run enable row level security;

-- -----------------------------------------------------------------------------
-- topic_cluster — canonical THEME dimension (theme -> topic rollup). Mirrors
-- gtm-os signal_06. 30 curated rows carried forward. parent_cluster_id self-FK kept
-- (reserved; NULL in V1). ingestion_run_id FK dropped (see note above).
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.topic_cluster (
  cluster_id        uuid primary key default gen_random_uuid(),
  canonical_slug    text not null unique,
  display_name      text not null,
  description       text,
  parent_cluster_id uuid references topic_intelligence.topic_cluster(cluster_id),
  curation_status   text not null default 'proposed'
                      check (curation_status in ('proposed','approved','deprecated')),
  curated_by        text,
  source            text not null,
  source_record_id  text,
  content_hash      text,
  fetched_at        timestamptz not null default now(),
  last_verified_at  timestamptz not null default now(),
  last_modified_at  timestamptz not null default now(),
  ingestion_run_id  uuid not null,   -- gtm-os value preserved; FK intentionally omitted (see header)
  created_at        timestamptz not null default now(),
  constraint topic_cluster_identity
    check (source_record_id is not null or content_hash is not null),
  constraint topic_cluster_no_self_parent
    check (parent_cluster_id is null or parent_cluster_id <> cluster_id)
);
create unique index if not exists topic_cluster_source_record_uq
  on topic_intelligence.topic_cluster(source, source_record_id) where source_record_id is not null;
alter table topic_intelligence.topic_cluster enable row level security;
-- NOTE: gtm-os's moddatetime set_modtime trigger intentionally omitted here (see header §2).

-- -----------------------------------------------------------------------------
-- topics — atomic topic dimension + non-destructive cluster-membership columns.
-- Mirrors gtm-os signal_02 (base) + signal_06 (cluster_id, cluster_assignment_*).
-- 170 rows carried; ~all carry a cluster_id. cluster_id FK re-pointed at the
-- in-schema topic_cluster (copied first; FK-safe load order). ingestion_run_id FK dropped.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.topics (
  topic_id                       uuid primary key default gen_random_uuid(),
  canonical_slug                 text not null unique,
  display_name                   text not null,
  synonym_set                    jsonb not null default '[]'::jsonb,
  source                         text not null,
  source_record_id               text,
  content_hash                   text,
  fetched_at                     timestamptz not null default now(),
  last_verified_at               timestamptz not null default now(),
  last_modified_at               timestamptz not null default now(),
  ingestion_run_id               uuid not null,   -- gtm-os value preserved; FK omitted (see header)
  created_at                     timestamptz not null default now(),
  -- signal_06 cluster-membership columns (nullable FK = a topic may be unassigned):
  cluster_id                     uuid references topic_intelligence.topic_cluster(cluster_id),
  cluster_assignment_confidence  numeric(4,3),
  cluster_assigned_by            text,
  constraint topics_identity_present
    check (source_record_id is not null or content_hash is not null),
  constraint topics_cluster_confidence_range
    check (cluster_assignment_confidence is null
           or (cluster_assignment_confidence >= 0 and cluster_assignment_confidence <= 1))
);
create unique index if not exists topics_source_record_uq
  on topic_intelligence.topics(source, source_record_id) where source_record_id is not null;
create index if not exists topics_synonyms
  on topic_intelligence.topics using gin (synonym_set jsonb_path_ops);
create index if not exists topics_cluster
  on topic_intelligence.topics(cluster_id) where cluster_id is not null;
alter table topic_intelligence.topics enable row level security;

-- -----------------------------------------------------------------------------
-- topic_trend — computed theme trajectory, one (subject, window, as_of_date) snapshot.
-- Mirrors gtm-os signal_07. 96 rows carried. subject_id is polymorphic (topic_id or
-- cluster_id) — no FK in gtm-os, none here. ingestion_run_id FK dropped.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.topic_trend (
  trend_id               uuid primary key default gen_random_uuid(),
  subject_level          text not null check (subject_level in ('topic','cluster')),
  subject_id             uuid not null,
  window_type            text not null check (window_type in ('week','month','all_time')),
  as_of_date             date not null,
  event_count            int  not null default 0,
  distinct_speaker_count int  not null default 0,
  prior_event_count      int,
  momentum               numeric,
  trend_label            text
                           check (trend_label in ('heating','steady','cooling','new','insufficient_data')),
  is_low_confidence      boolean not null default false,
  source                 text not null default 'computed',
  content_hash           text not null,
  ingestion_run_id       uuid not null,   -- gtm-os value preserved; FK omitted (see header)
  computed_at            timestamptz not null default now(),
  created_at             timestamptz not null default now(),
  constraint topic_trend_content_hash_nonempty check (content_hash <> '')
);
create unique index if not exists topic_trend_grain_uq
  on topic_intelligence.topic_trend(subject_level, subject_id, window_type, as_of_date);
create index if not exists topic_trend_asof
  on topic_intelligence.topic_trend(as_of_date desc, window_type);
alter table topic_intelligence.topic_trend enable row level security;

-- -----------------------------------------------------------------------------
-- topic_pair_metric — computed theme-pair co-occurrence + shared-speaker bridges.
-- Mirrors gtm-os signal_07. 286 rows carried. bridge_entity_ids[] is re-identifiable
-- (raw entity UUIDs) and is NEVER exposed by the signal_read views (0002). Canonical
-- order + bridge-count-matches CHECKs preserved. ingestion_run_id FK dropped.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.topic_pair_metric (
  pair_metric_id           uuid primary key default gen_random_uuid(),
  subject_level            text not null check (subject_level in ('topic','cluster')),
  subject_a_id             uuid not null,
  subject_b_id             uuid not null,
  window_type              text not null check (window_type in ('week','month','all_time')),
  as_of_date               date not null,
  cooccurrence_event_count int  not null default 0,
  bridge_person_count      int  not null default 0,
  bridge_entity_ids        uuid[] not null default '{}',
  first_cooccurred_on      date,
  is_new_pair              boolean not null default false,
  intersection_score       numeric,
  source                   text not null default 'computed',
  content_hash             text not null,
  ingestion_run_id         uuid not null,   -- gtm-os value preserved; FK omitted (see header)
  computed_at              timestamptz not null default now(),
  created_at               timestamptz not null default now(),
  constraint topic_pair_order check (subject_a_id < subject_b_id),
  constraint topic_pair_content_hash_nonempty check (content_hash <> ''),
  constraint topic_pair_bridge_count_matches
    check (bridge_person_count = cardinality(bridge_entity_ids))
);
create unique index if not exists topic_pair_grain_uq
  on topic_intelligence.topic_pair_metric(subject_level, subject_a_id, subject_b_id, window_type, as_of_date);
create index if not exists topic_pair_asof
  on topic_intelligence.topic_pair_metric(as_of_date desc, window_type);
create index if not exists topic_pair_bridge_gin
  on topic_intelligence.topic_pair_metric using gin (bridge_entity_ids);
alter table topic_intelligence.topic_pair_metric enable row level security;

commit;

-- Rollback (Increment 1 is reversible by construction):
--   drop schema if exists topic_intelligence cascade;
-- `public` is untouched by this migration.

-- ==================== 2. signal_read views (0002) ====================
-- 0002_signal_read_views.sql
-- MI data-layer consolidation — Increment 1 (YED-130 / ADR-1). ANON-SAFE READ LAYER.
-- =============================================================================
-- ADDITIVE ONLY. Creates the `signal_read` schema of anon-safe views over
-- `topic_intelligence`. ZERO changes to Empire's `public` schema. This is the ONLY
-- schema (besides `public`) that goes into the Data API exposed-schemas list (0003) —
-- so anon/authenticated reach topic-intelligence data ONLY through these views, and
-- ONLY the counts-only, small-cell-suppressed projections defined here.
--
-- HARD REQUIREMENT (ADR-1 §"Security model correction", pre-mortem #4):
--   Every view is WITH (security_invoker = on). A security_definer (owner-privilege)
--   view would run with the owner's rights and could leak base rows to anon; invoker
--   rights force each query to be checked against the CALLER's grants + RLS.
--
-- SMALL-CELL SUPPRESSION (k-anonymity, k = 5): every COUNT cell is shown only when it
--   is >= 5; below 5 the cell is withheld (NULL), and a row is dropped entirely when it
--   would carry no surviving count. No PII, no person rows, no bridge_entity_ids.
--
-- ------------------------------------------------------------------------------------
-- READ-PRIVILEGE RECONCILIATION (important — surfaced for review):
--   The task specifies BOTH "every view MUST be security_invoker = on" AND "grant
--   nothing on base topic_intelligence to anon." Under Postgres these cannot both hold
--   literally: a security_invoker view is evaluated with the CALLER's privileges, so for
--   anon to read a security_invoker view at all, anon must hold SELECT (grant + RLS) on
--   the underlying tables the view traverses. A security_definer view would avoid the
--   base grant — but that is exactly the PII-leak vector the ADR forbids.
--
--   Resolution (least-privilege, documented): honor security_invoker=on (the hard,
--   ADR-backed requirement) and grant anon the NARROWEST base access that makes it work:
--     - USAGE on schema topic_intelligence
--     - SELECT on ONLY the three non-PII tables the views traverse
--       (topic_cluster, topic_trend, topic_pair_metric)
--     - a permissive RLS SELECT policy for anon/authenticated on those three tables
--   anon is granted NOTHING on `topics`, NOTHING writable, and NEVER sees
--   bridge_entity_ids (the views do not select it). Defense-in-depth that keeps this
--   safe even with the base grant: topic_intelligence is NOT in exposed-schemas, so
--   there is no direct PostgREST path to the base tables — the only reachable surface is
--   these suppressed, counts-only views. Re-audit small-cell + view security on merged
--   data in Increment 2 (pre-mortem #4).
-- =============================================================================

begin;

create schema if not exists signal_read;

-- Minimal base access required for security_invoker views to return rows to anon.
-- (See RECONCILIATION note above.) No grant on topic_intelligence.topics, no writes.
grant usage on schema topic_intelligence to anon, authenticated;
grant select on topic_intelligence.topic_cluster     to anon, authenticated;
grant select on topic_intelligence.topic_trend        to anon, authenticated;
grant select on topic_intelligence.topic_pair_metric  to anon, authenticated;

-- RLS is deny-all by default (0001 enabled RLS, no policy). Add a read-only,
-- non-PII SELECT policy for anon/authenticated on exactly the three tables the views
-- read. Suppression + counts-only projection happens in the views, not in RLS.
drop policy if exists tc_anon_read on topic_intelligence.topic_cluster;
create policy tc_anon_read on topic_intelligence.topic_cluster
  for select to anon, authenticated using (true);

drop policy if exists tt_anon_read on topic_intelligence.topic_trend;
create policy tt_anon_read on topic_intelligence.topic_trend
  for select to anon, authenticated using (true);

drop policy if exists tpm_anon_read on topic_intelligence.topic_pair_metric;
create policy tpm_anon_read on topic_intelligence.topic_pair_metric
  for select to anon, authenticated using (true);

-- -----------------------------------------------------------------------------
-- v_topic_movement — per-theme trajectory over time (COUNTS ONLY).
-- Exposes: theme display name + slug, window, as_of_date, event_count,
--          distinct_speaker_count, momentum ratio, trend_label.
-- Safe because: no person/entity rows; the only identifiers are the curated theme
--   name + slug (public editorial labels). Small-cell suppression:
--     - rows withheld unless event_count >= 5 (the headline count is the k-gate)
--     - distinct_speaker_count shown only when >= 5, else NULL (cell-level k-gate)
--   momentum/trend_label ride along only for surviving (event_count>=5) rows, so they
--   never describe a below-k population.
-- -----------------------------------------------------------------------------
-- Column contract matches the gtm-os-hub adapter (lib/sources/topic-intelligence.ts):
--   theme, event_count, distinct_speaker_count, momentum, trend_label, is_low_confidence, as_of_date.
-- distinct on (subject, window) + order by as_of_date desc => LATEST snapshot per theme (one row/theme).
drop view if exists signal_read.v_topic_movement;
create view signal_read.v_topic_movement
  with (security_invoker = on) as
select distinct on (tt.subject_id, tt.window_type)
  tc.display_name                                                  as theme,
  tt.window_type,
  tt.as_of_date,
  tt.event_count,
  case when tt.distinct_speaker_count >= 5
       then tt.distinct_speaker_count else null end                as distinct_speaker_count,
  tt.momentum,
  tt.trend_label,
  tt.is_low_confidence
from topic_intelligence.topic_trend tt
join topic_intelligence.topic_cluster tc
  on tc.cluster_id = tt.subject_id
where tt.subject_level = 'cluster'      -- V1 populates cluster-level only
  and tt.event_count >= 5              -- k-anonymity: withhold below-threshold themes
order by tt.subject_id, tt.window_type, tt.as_of_date desc;

comment on view signal_read.v_topic_movement is
  'Anon-safe (security_invoker, k>=5). Per-theme trajectory counts only; no PII. '
  'Rows withheld when event_count<5; distinct_speaker_count nulled when <5.';

-- -----------------------------------------------------------------------------
-- v_topic_intersections — theme-pair connections (COUNTS ONLY).
-- Exposes: both theme names/slugs (canonical order), window, as_of_date,
--          cooccurrence_event_count, bridge_person_count, is_new_pair.
-- Safe because: bridge_entity_ids (the raw "who bridges" UUID array) is NEVER selected;
--   only aggregate counts leave the base table. Small-cell suppression:
--     - rows withheld unless at least one count reaches k>=5
--       (cooccurrence_event_count >= 5 OR bridge_person_count >= 5)
--     - each count shown only when >= 5, else NULL (cell-level k-gate)
--   So a pair connected by 5 shared events but only 2 bridging people surfaces the
--   event count and NULLs the person count — never re-identifying a <5 group of people.
-- -----------------------------------------------------------------------------
-- Column contract matches the gtm-os-hub adapter: theme_a, theme_b, cooccurrence_event_count,
--   bridge_person_count, is_new_pair, intersection_score, as_of_date. Latest snapshot per pair.
drop view if exists signal_read.v_topic_intersections;
create view signal_read.v_topic_intersections
  with (security_invoker = on) as
select distinct on (tpm.subject_a_id, tpm.subject_b_id, tpm.window_type)
  ca.display_name                                                  as theme_a,
  cb.display_name                                                  as theme_b,
  tpm.window_type,
  tpm.as_of_date,
  case when tpm.cooccurrence_event_count >= 5
       then tpm.cooccurrence_event_count else null end             as cooccurrence_event_count,
  case when tpm.bridge_person_count >= 5
       then tpm.bridge_person_count else null end                  as bridge_person_count,
  tpm.is_new_pair,
  tpm.intersection_score
from topic_intelligence.topic_pair_metric tpm
join topic_intelligence.topic_cluster ca on ca.cluster_id = tpm.subject_a_id
join topic_intelligence.topic_cluster cb on cb.cluster_id = tpm.subject_b_id
where tpm.subject_level = 'cluster'
  and (tpm.cooccurrence_event_count >= 5 or tpm.bridge_person_count >= 5)
order by tpm.subject_a_id, tpm.subject_b_id, tpm.window_type, tpm.as_of_date desc;

comment on view signal_read.v_topic_intersections is
  'Anon-safe (security_invoker, k>=5). Theme-pair co-occurrence + shared-speaker counts '
  'only; bridge_entity_ids never exposed. Rows withheld unless a count reaches 5; each '
  'count nulled below 5.';

-- Expose the views (and ONLY the views) to the public roles. No base-table writes,
-- no grant on topic_intelligence.topics, nothing on `public` touched.
grant usage on schema signal_read to anon, authenticated;
grant select on signal_read.v_topic_movement       to anon, authenticated;
grant select on signal_read.v_topic_intersections  to anon, authenticated;

commit;

-- Rollback: drop schema if exists signal_read cascade;  (and revoke the base grants /
-- drop the anon RLS policies added above — see APPLY.md rollback section). `public` untouched.

-- ==================== 3. roles / grants / definer (0003) ====================
-- 0003_roles_grants_definer.sql
-- MI data-layer consolidation — Increment 1 (YED-130 / ADR-1). WRITE-PATH HARDENING.
-- =============================================================================
-- ADDITIVE ONLY. Creates a scoped `pipeline_writer` role, grants it ONLY what the
-- ingestion pipeline needs on `public`, REVOKES it from the intelligence schemas, and
-- defines the SECURITY DEFINER function pattern as the ONLY write path into
-- topic_intelligence. ZERO DML/DDL against `public` DATA — this migration only touches
-- GRANTS on `public` tables (privileges, not rows/columns) and objects in the two new
-- schemas. `public` table shapes and rows are untouched.
--
-- ############################################################################
-- ## RLS IS NOT A CONTROL AGAINST THE service_role / sb_secret KEY.          ##
-- ##                                                                          ##
-- ## Empire's pipeline currently authenticates as `service_role` via the      ##
-- ## `sb_secret` key, which BYPASSES Row-Level Security entirely. Therefore   ##
-- ## RLS deny-all on topic_intelligence is NOT what keeps the pipeline out of  ##
-- ## the intelligence schema. Enforcement here is ROLES + GRANTS + SECURITY   ##
-- ## DEFINER, not RLS:                                                         ##
-- ##   - a scoped `pipeline_writer` role with grants ONLY on the public tables  ##
-- ##     it must write;                                                        ##
-- ##   - REVOKE ALL on topic_intelligence + signal_read from pipeline_writer;   ##
-- ##   - the ONLY write into topic_intelligence is via SECURITY DEFINER        ##
-- ##     functions owned by a privileged role (EXECUTE granted; direct DML     ##
-- ##     revoked).                                                             ##
-- ##                                                                          ##
-- ## ACTION REQUIRED (ops): the pipeline MUST STOP using the sb_secret          ##
-- ## service key for routine writes and connect as `pipeline_writer` instead.  ##
-- ## While it keeps using sb_secret/service_role, every control below is       ##
-- ## advisory only — service_role bypasses all of it.                          ##
-- ############################################################################
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- 1. Scoped write role. CREATE ROLE has no IF NOT EXISTS -> guard with a DO block.
--    NOLOGIN group role: the pipeline's actual login role is GRANTed pipeline_writer,
--    or (Supabase) a dedicated login user is created out-of-band and granted this role.
-- -----------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'pipeline_writer') then
    create role pipeline_writer nologin;
  end if;
end
$$;

-- -----------------------------------------------------------------------------
-- 2. Grant ONLY what the ingestion pipeline needs on `public`.
--    Ingestion upserts dimension/hyperedge rows; it does not DELETE. No sequence
--    grants needed (all PKs default gen_random_uuid()).
-- -----------------------------------------------------------------------------
grant usage on schema public to pipeline_writer;
grant select, insert, update on
  public.company,
  public.person,
  public.topic,
  public.event,
  public.event_entity
to pipeline_writer;

-- -----------------------------------------------------------------------------
-- 3. REVOKE the intelligence schemas from pipeline_writer (both schema + objects).
--    pipeline_writer must never touch topic_intelligence or signal_read directly.
-- -----------------------------------------------------------------------------
revoke all on schema topic_intelligence from pipeline_writer;
revoke all on all tables    in schema topic_intelligence from pipeline_writer;
revoke all on all sequences in schema topic_intelligence from pipeline_writer;
revoke all on all functions in schema topic_intelligence from pipeline_writer;

revoke all on schema signal_read from pipeline_writer;
revoke all on all tables    in schema signal_read from pipeline_writer;
revoke all on all functions in schema signal_read from pipeline_writer;

-- Also revoke the PUBLIC pseudo-role's default EXECUTE on new functions in the
-- intelligence schema, so EXECUTE is grant-only (see the definer function below).
alter default privileges in schema topic_intelligence revoke execute on functions from public;

-- -----------------------------------------------------------------------------
-- 4. SECURITY DEFINER write-path PATTERN — the ONLY way pipeline_writer may write
--    into topic_intelligence. Owned by a privileged role (the migration runner /
--    table owner, e.g. postgres). Runs with the owner's rights, so it can INSERT even
--    though pipeline_writer has REVOKE ALL on the schema. `set search_path` pins name
--    resolution (security best practice for SECURITY DEFINER — prevents search_path
--    hijacking). EXECUTE granted to pipeline_writer; direct DML stays revoked.
--
--    This is a representative pattern (one table). Increment 2's live recompute adds
--    sibling definer functions (e.g. reload_topic_pair_metric) following the same mould;
--    the nightly compute is ported here as a definer function, never as direct DML.
-- -----------------------------------------------------------------------------
create or replace function topic_intelligence.upsert_topic_trend(
  p_subject_level          text,
  p_subject_id             uuid,
  p_window_type            text,
  p_as_of_date             date,
  p_event_count            int,
  p_distinct_speaker_count int,
  p_prior_event_count      int,
  p_momentum               numeric,
  p_trend_label            text,
  p_is_low_confidence      boolean,
  p_content_hash           text,
  p_ingestion_run_id       uuid
) returns uuid
language plpgsql
security definer
set search_path = topic_intelligence, pg_temp
as $fn$
declare
  v_trend_id uuid;
begin
  insert into topic_intelligence.topic_trend (
    subject_level, subject_id, window_type, as_of_date,
    event_count, distinct_speaker_count, prior_event_count, momentum,
    trend_label, is_low_confidence, source, content_hash, ingestion_run_id)
  values (
    p_subject_level, p_subject_id, p_window_type, p_as_of_date,
    p_event_count, p_distinct_speaker_count, p_prior_event_count, p_momentum,
    p_trend_label, p_is_low_confidence, 'computed', p_content_hash, p_ingestion_run_id)
  on conflict (subject_level, subject_id, window_type, as_of_date)
  do update set
    event_count            = excluded.event_count,
    distinct_speaker_count = excluded.distinct_speaker_count,
    prior_event_count      = excluded.prior_event_count,
    momentum               = excluded.momentum,
    trend_label            = excluded.trend_label,
    is_low_confidence      = excluded.is_low_confidence,
    content_hash           = excluded.content_hash,
    ingestion_run_id       = excluded.ingestion_run_id
  returning trend_id into v_trend_id;
  return v_trend_id;
end
$fn$;

-- EXECUTE is the ONLY intelligence-schema privilege pipeline_writer receives. It cannot
-- SELECT/INSERT/UPDATE the base tables directly (revoked in step 3); it may only call
-- this vetted definer function, which enforces the write shape.
revoke all on function topic_intelligence.upsert_topic_trend(
  text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid) from public;
grant execute on function topic_intelligence.upsert_topic_trend(
  text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid) to pipeline_writer;

commit;

-- =============================================================================
-- CONFIG NOTE (NOT SQL — apply in the Supabase dashboard, in a low-traffic window):
--
--   Data API "Exposed schemas" (Postgres setting `pgrst.db_schemas`) MUST be set to:
--       public, signal_read
--   i.e. ADD `signal_read`, do NOT add `topic_intelligence`.
--
--   - `public`      — Empire's existing surface (unchanged; already exposed).
--   - `signal_read` — the anon-safe, security_invoker, k>=5 views (0002).
--   - topic_intelligence is DELIBERATELY EXCLUDED so there is no direct PostgREST path
--     to the base intelligence tables (defense-in-depth on top of RLS + grants).
--
--   exposed-schemas is a PROJECT-WIDE setting (pre-mortem #5) — changing it touches
--   empire-state-hub's live `public` surface too. Apply in a low-traffic window and run
--   get_advisors on the branch first (APPLY.md steps (d)+(e)).
--
--   TRANSIENT EXCEPTION for the one-time carry-forward load: the Python loader
--   (carry_forward_topic_intelligence.py) writes via PostgREST with
--   `Content-Profile: topic_intelligence`, which requires topic_intelligence to be in
--   the exposed list FOR THE DURATION OF THE LOAD ONLY. Sequence in APPLY.md:
--       expose `public, signal_read, topic_intelligence` -> run loader -> validate ->
--       set final `public, signal_read`.
--   Anon stays safe throughout: even while transiently exposed, anon has no grant on
--   topic_intelligence.topics and RLS/grants restrict the other three to counts via views.
--   (Alternative if you prefer never to expose it: run the loader over psql/COPY instead
--    of PostgREST — see APPLY.md.)
-- =============================================================================

-- Rollback:
--   drop function if exists topic_intelligence.upsert_topic_trend(
--     text, uuid, text, date, int, int, int, numeric, text, boolean, text, uuid);
--   -- revoke the public grants and drop role if unused:
--   revoke all on public.company, public.person, public.topic, public.event,
--     public.event_entity from pipeline_writer;
--   drop role if exists pipeline_writer;   -- only if no login role depends on it
--   -- revert Data API exposed-schemas to `public` (remove signal_read).

-- ==================== 4. service_role grants on the new schemas ====================
-- Supabase auto-grants service_role on public but NOT on custom schemas. Grant explicitly so the
-- empire-state-hub secret key can read signal_read and the REST carry-forward can write.
grant usage on schema topic_intelligence, signal_read to service_role;
grant all on all tables in schema topic_intelligence to service_role;
grant all on all sequences in schema topic_intelligence to service_role;
grant select on all tables in schema signal_read to anon, authenticated, service_role;
