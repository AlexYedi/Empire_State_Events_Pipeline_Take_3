-- 2b_rollback.sql — reverse staging/2b_swap.sql. ONE transaction. Sub-second, zero loss.
-- Spec/runbook: supabase/2B_REHEARSAL_RUNBOOK.md §7 (the gate the whole plan hinges on).
-- Moves the v2 tables back to canonical_v2, restores the originals from schema `pre2b`,
-- restores the original signal_read views, and drops the (now-empty) pre2b schema.
--
-- ⚠️ GATED: prove this returns exact pre-swap row counts on the Phantom Test Case DB.

begin;

-- 1) Drop the v2 views (they depend on the v2 topic_intelligence tables).
drop view if exists signal_read.v_topic_movement;
drop view if exists signal_read.v_topic_intersections;

-- 2) INTELLIGENCE back: v2 (in topic_intelligence) -> canonical_v2 ; originals (in pre2b) -> topic_intelligence.
alter table topic_intelligence.topic_cluster     set schema canonical_v2;
alter table topic_intelligence.topic_trend        set schema canonical_v2;
alter table topic_intelligence.topic_pair_metric  set schema canonical_v2;
alter table topic_intelligence.ingestion_run      set schema canonical_v2;

alter table pre2b.topic_cluster     set schema topic_intelligence;
alter table pre2b.topic_trend        set schema topic_intelligence;
alter table pre2b.topic_pair_metric  set schema topic_intelligence;
alter table pre2b.ingestion_run      set schema topic_intelligence;

-- 3) ENTITY GRAPH back: v2 (in public) -> canonical_v2 ; originals (in pre2b) -> public.
alter table public.company      set schema canonical_v2;
alter table public.person       set schema canonical_v2;
alter table public.topic        set schema canonical_v2;
alter table public.event        set schema canonical_v2;
alter table public.event_entity set schema canonical_v2;

alter table pre2b.company      set schema public;
alter table pre2b.person       set schema public;
alter table pre2b.topic        set schema public;
alter table pre2b.event        set schema public;
alter table pre2b.event_entity set schema public;

-- 4) Recreate the ORIGINAL signal_read views (identical to 0002, over the restored topic_intelligence tables).
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

-- 5) pre2b is now empty — drop it.
drop schema if exists pre2b;

commit;
