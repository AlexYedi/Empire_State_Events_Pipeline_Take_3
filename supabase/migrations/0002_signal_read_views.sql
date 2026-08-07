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
