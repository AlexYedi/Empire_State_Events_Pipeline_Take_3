-- 2b_swap.sql — Increment 2b atomic cutover (AC2b.5). ONE transaction.
-- Spec/runbook: supabase/2B_REHEARSAL_RUNBOOK.md §6 · Linear: YED-130
--
-- Makes canonical_v2 the live graph:
--   * entity graph  -> public              (hubs + pipeline read public.* by name; RLS deny-all)
--   * intelligence   -> topic_intelligence  (kept NON-exposed; only signal_read views reach it)
-- Originals are PARKED in schema `pre2b` (not renamed in place — that collides on constraint
-- names like company_pkey; a separate schema keeps names unique). Kept for rollback + N-night
-- validation, dropped as a separate step. Rollback = staging/2b_rollback.sql.
--
-- ⚠️ GATED: prove swap→rollback on the Phantom Test Case DB before the Empire prod DB.

begin;

create schema if not exists pre2b;

-- 1) ENTITY GRAPH: old public.* -> pre2b ; canonical_v2.* -> public. FKs follow by OID.
alter table public.company      set schema pre2b;
alter table public.person       set schema pre2b;
alter table public.topic        set schema pre2b;
alter table public.event        set schema pre2b;
alter table public.event_entity set schema pre2b;

alter table canonical_v2.company      set schema public;
alter table canonical_v2.person       set schema public;
alter table canonical_v2.topic        set schema public;
alter table canonical_v2.event        set schema public;
alter table canonical_v2.event_entity set schema public;

-- 2) INTELLIGENCE: drop views first (they depend on the old tables), then old ti.* -> pre2b, v2 -> ti.
drop view if exists signal_read.v_topic_movement;
drop view if exists signal_read.v_topic_intersections;

alter table topic_intelligence.topic_cluster     set schema pre2b;
alter table topic_intelligence.topic_trend        set schema pre2b;
alter table topic_intelligence.topic_pair_metric  set schema pre2b;
alter table topic_intelligence.ingestion_run      set schema pre2b;

alter table canonical_v2.topic_cluster     set schema topic_intelligence;
alter table canonical_v2.topic_trend        set schema topic_intelligence;
alter table canonical_v2.topic_pair_metric  set schema topic_intelligence;
alter table canonical_v2.ingestion_run      set schema topic_intelligence;

-- 3) GRANTS + RLS so hubs/pipeline keep working on the new tables.
grant select, insert, update, delete
  on public.company, public.person, public.topic, public.event, public.event_entity
  to service_role;
grant select
  on public.company, public.person, public.topic, public.event, public.event_entity
  to anon, authenticated;

grant usage on schema topic_intelligence to anon, authenticated;
grant select on topic_intelligence.topic_cluster, topic_intelligence.topic_trend, topic_intelligence.topic_pair_metric
  to anon, authenticated, service_role;
drop policy if exists tc_anon_read on topic_intelligence.topic_cluster;
create policy tc_anon_read on topic_intelligence.topic_cluster for select to anon, authenticated using (true);
drop policy if exists tt_anon_read on topic_intelligence.topic_trend;
create policy tt_anon_read on topic_intelligence.topic_trend for select to anon, authenticated using (true);
drop policy if exists tpm_anon_read on topic_intelligence.topic_pair_metric;
create policy tpm_anon_read on topic_intelligence.topic_pair_metric for select to anon, authenticated using (true);

-- 4) Recreate the signal_read views over the NEW topic_intelligence tables (identical to 0002; k>=5 suppression).
create view signal_read.v_topic_movement with (security_invoker = on) as
select distinct on (tt.subject_id, tt.window_type)
  tc.display_name as theme, tt.window_type, tt.as_of_date, tt.event_count,
  case when tt.distinct_speaker_count >= 5 then tt.distinct_speaker_count else null end as distinct_speaker_count,
  tt.momentum, tt.trend_label, tt.is_low_confidence
from topic_intelligence.topic_trend tt
join topic_intelligence.topic_cluster tc on tc.cluster_id = tt.subject_id
where tt.subject_level = 'cluster' and tt.event_count >= 5
order by tt.subject_id, tt.window_type, tt.as_of_date desc;

create view signal_read.v_topic_intersections with (security_invoker = on) as
select distinct on (tpm.subject_a_id, tpm.subject_b_id, tpm.window_type)
  ca.display_name as theme_a, cb.display_name as theme_b, tpm.window_type, tpm.as_of_date,
  case when tpm.cooccurrence_event_count >= 5 then tpm.cooccurrence_event_count else null end as cooccurrence_event_count,
  case when tpm.bridge_person_count >= 5 then tpm.bridge_person_count else null end as bridge_person_count,
  tpm.is_new_pair, tpm.intersection_score
from topic_intelligence.topic_pair_metric tpm
join topic_intelligence.topic_cluster ca on ca.cluster_id = tpm.subject_a_id
join topic_intelligence.topic_cluster cb on cb.cluster_id = tpm.subject_b_id
where tpm.subject_level = 'cluster' and (tpm.cooccurrence_event_count >= 5 or tpm.bridge_person_count >= 5)
order by tpm.subject_a_id, tpm.subject_b_id, tpm.window_type, tpm.as_of_date desc;

grant usage on schema signal_read to anon, authenticated;
grant select on signal_read.v_topic_movement, signal_read.v_topic_intersections to anon, authenticated;

commit;
