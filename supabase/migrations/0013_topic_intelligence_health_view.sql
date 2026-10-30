-- 0013_topic_intelligence_health_view.sql
-- Topic-intelligence health strip on the MI graph (YED-122). COCKPIT-ONLY READ VIEW.
-- =============================================================================
-- ADDITIVE ONLY. Creates ONE view (`topic_intelligence.topic_intelligence_health`)
-- and touches nothing else — no table, function, grant, or config change. Fully
-- reversible (rollback = drop the view). Linear: YED-122 (GTM cockpit health strip).
--
-- PROVENANCE: ported from the retired gtm-os spine
--   (gtm-os:scripts/topic_intelligence/topic_intelligence_health.sql, YED-120),
--   whose `signal.*` schema was deleted with the spine on 2026-08-20
--   (cold export: gtm-os/supabase/archive/spine-decommission-2026-08-20/).
--   The tripwire set, thresholds, and ok/watch/trip logic are UNCHANGED; only the
--   table names and the tagging surface are repointed, mechanically:
--
--     signal.topic_trend        -> topic_intelligence.topic_trend   (same columns; 0001/0007)
--     signal.topics             -> public.topic  (cluster_id + cluster_assignment_confidence
--                                  moved to the entity table at the 2b cutover — 0006; the
--                                  live compute (0012) reads membership from public.topic,
--                                  so the health strip must read the SAME live source, not
--                                  the frozen Increment-1 snapshot topic_intelligence.topics)
--     signal.relations          -> public.event_entity role='tagged_topic' (0012 pattern),
--                                  scoped to e.kind='attended' for parity with the compute
--     signal.topic_pair_metric  -> topic_intelligence.topic_pair_metric (same columns)
--     signal.conflict_log       -> NO MI-graph counterpart (see DEGRADED below)
--
-- DEGRADED FACET (flagged for review, not silent):
--   The spine's `canonicalization_backlog` tripwire counted
--   unassigned topics + signal.conflict_log rows at resolution='human_pending'.
--   The MI graph has no conflict_log (topic canonicalization is curated upstream;
--   no such table exists in 0001-0012). That facet is OMITTED: the tripwire now
--   tracks unassigned topics only. Threshold stays 5. If a conflict log lands on
--   the MI graph later, re-add the facet with CREATE OR REPLACE.
--
-- SECURITY (cockpit-only): the view lives in `topic_intelligence`, which is NOT in
--   the Data API exposed-schemas (0001/0003) — there is no PostgREST path to it.
--   security_invoker=on means the view runs with the CALLER's privileges, so an
--   anon/authenticated caller would need base grants on public.event / event_entity /
--   topic that it does not hold (defense-in-depth on top of the unexposed schema).
--   No grant of any kind is issued on the view. The cockpit reads it with the
--   service-role key, which bypasses RLS and requires NO schema-exposure toggle.
--   Every metric it computes is a count/ratio — zero PII, no person rows, no
--   bridge_entity_ids (ADR-9).
--
-- APPLY: Supabase dashboard SQL Editor (paste whole file) or
--   psql "<session-pooler DSN>" -v ON_ERROR_STOP=1 -f supabase/migrations/0013_topic_intelligence_health_view.sql
--   Project: oicikjyzmxqfomrrqkvf (canonical Empire). Runbook:
--   supabase/APPLY_YED122_HEALTH_VIEW.md (rehearse on a scratch/branch DB first).
-- =============================================================================

begin;

create or replace view topic_intelligence.topic_intelligence_health
  with (security_invoker = on) as
with
latest as (select max(as_of_date) as d from topic_intelligence.topic_trend),
tagged_events as (   -- total distinct attended events carrying any theme (occupancy denominator);
                     -- MI-graph equivalent of the spine's signal.relations count, with the same
                     -- event_kind/cluster scoping the live compute uses (0012)
  select count(distinct e.id) as n
  from public.event_entity ee
  join public.event e on e.id = ee.event_id
  join public.topic t on t.id = ee.entity_id
  where ee.entity_type='topic' and ee.role='tagged_topic'
    and e.kind='attended' and t.cluster_id is not null
),
-- (1) granularity: largest theme's share of all-time events (catch-all guard)
occupancy as (
  select max(tt.event_count)::numeric / greatest((select n from tagged_events),1) as v
  from topic_intelligence.topic_trend tt, latest
  where tt.window_type='all_time' and tt.subject_level='cluster' and tt.as_of_date=latest.d
),
-- (2) granularity: share of month-window themes stuck at insufficient_data (thin-data / stale-corpus)
insuff as (
  select avg((tt.trend_label='insufficient_data')::int)::numeric as v
  from topic_intelligence.topic_trend tt, latest
  where tt.window_type='month' and tt.subject_level='cluster' and tt.as_of_date=latest.d
),
-- (3) single-membership pressure: topics assigned with low confidence (likely bi-thematic).
--     Membership is read from public.topic — the LIVE source the 2b cutover and the 0012
--     compute use. Assigned rows with NULL confidence drop out of avg() by SQL NULL
--     semantics (they count in neither numerator nor denominator).
membership as (
  select avg((cluster_assignment_confidence < 0.80)::int)::numeric as v
  from public.topic where cluster_id is not null
),
-- (4) canonicalization: unassigned topics. DEGRADED vs the spine (see header): the
--     conflict_log human_pending facet has no MI-graph counterpart and is omitted.
canon as (
  select (select count(*) from public.topic where cluster_id is null) as v
),
-- (5) runtime: largest gap (days) between consecutive trend snapshots (heartbeat / pg_cron health)
gaps as (
  select coalesce(max(gap),0) as v from (
    select as_of_date - lag(as_of_date) over (order by as_of_date) as gap
    from (select distinct as_of_date from topic_intelligence.topic_trend) s
  ) g
),
-- (6) bridge inflation: worst bridge:co-occurrence ratio among all-time pairs that share an event
bridge as (
  select coalesce(max(bridge_person_count::numeric / cooccurrence_event_count),0) as v
  from topic_intelligence.topic_pair_metric tpm, latest
  where tpm.window_type='all_time' and tpm.as_of_date=latest.d and tpm.cooccurrence_event_count > 0
)
select * from (
  values
  ('granularity_occupancy',  'D2', (select round(v,3) from occupancy),  0.200,
     'largest theme share of attended, theme-tagged events'),
  ('granularity_insufficient','D2',(select round(v,3) from insuff),      0.400,
     'month-window themes at insufficient_data'),
  ('membership_confidence',   'D1', (select round(v,3) from membership), 0.150,
     'topics assigned below 0.80 confidence'),
  ('canonicalization_backlog','MT-7',(select v::numeric from canon),      5.000,
     'unassigned topics (DEGRADED: spine conflict_log human_pending facet has no MI-graph counterpart and is omitted)'),
  ('runtime_snapshot_gap',    'D4', (select v::numeric from gaps),        1.000,
     'max days between trend snapshots'),
  ('bridge_inflation',        'B',  (select round(v,2) from bridge),     10.000,
     'worst bridge:co-occurrence ratio')
) as h(tripwire, decision, metric, threshold, description)
cross join lateral (
  select case
    when h.metric is null then 'no_data'
    when h.metric >  h.threshold then 'trip'
    when h.metric >= h.threshold * 0.75 then 'watch'
    else 'ok'
  end as status
) s;

comment on view topic_intelligence.topic_intelligence_health is
  'V1-assumptions tripwire strip (YED-120 spec §8, ported YED-122): one row per simplification, status ok/watch/trip vs threshold. Cockpit-only (service-role); conflict_log facet degraded to unassigned-topics-only.';

-- COCKPIT-ONLY, belt and braces: no grant is issued on the view; explicitly strip any
-- inherited anon/authenticated path. topic_intelligence is not PostgREST-exposed
-- (0001/0003), so even without this there is no REST route — this only narrows the
-- direct-SQL surface.
revoke select on topic_intelligence.topic_intelligence_health from anon;
revoke select on topic_intelligence.topic_intelligence_health from authenticated;

commit;

-- Verify (read-only, service-role or postgres):
--   select * from topic_intelligence.topic_intelligence_health order by tripwire;
--   -- expect 6 rows, one per tripwire, status in (ok, watch, trip, no_data)
--   select reloptions from pg_class
--    where oid = 'topic_intelligence.topic_intelligence_health'::regclass;
--   -- reloptions must include security_invoker=on
--   select has_table_privilege('anon','topic_intelligence.topic_intelligence_health','SELECT');  -- f
--   select has_table_privilege('authenticated','topic_intelligence.topic_intelligence_health','SELECT'); -- f
--
-- Rollback:
--   drop view if exists topic_intelligence.topic_intelligence_health;
--   -- nothing else was created or modified by this migration.
