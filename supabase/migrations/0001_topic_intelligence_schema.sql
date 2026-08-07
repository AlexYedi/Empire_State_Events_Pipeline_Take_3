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
