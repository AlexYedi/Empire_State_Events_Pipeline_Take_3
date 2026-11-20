-- 0027_verify.sql: probes for supabase/migrations/0027_retire_pre2b_and_tighten_topic_reads.sql (YED-298).
-- Read-only. Two statements; rehearse_0027.py runs step 0 at gate 0 and step 1 at gate 4.
--
-- 0. BEFORE apply (read-only; prod via the dashboard, and the twin via the harness): exact row count and a row-level
--    md5 per pre2b table. Prod must equal the twin row for row. Only then does the twin export (taken by
--    rehearse_0027.py) restore prod's pre2b exactly. The hashes reveal nothing; the rows stay where they are.
select t.tbl, t.n, t.h from (
            select 'company' as tbl, count(*) as n, md5(coalesce(string_agg(x::text, '|' order by x::text), '')) as h from pre2b.company x
  union all select 'event', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.event x
  union all select 'event_entity', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.event_entity x
  union all select 'ingestion_run', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.ingestion_run x
  union all select 'person', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.person x
  union all select 'topic', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.topic x
  union all select 'topic_cluster', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.topic_cluster x
  union all select 'topic_pair_metric', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.topic_pair_metric x
  union all select 'topic_trend', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from pre2b.topic_trend x
  union all select 'ti.topics', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from topic_intelligence.topics x
) t order by t.tbl;

-- 1. AFTER apply: every row ok = true.
--    YED-311 is held (see the migration header), so the anon policies and grants on the three live
--    topic_intelligence tables must be UNCHANGED. The /signal page reads them through the security_invoker views.
select 'pre2b_gone' as check_name, to_regnamespace('pre2b') is null as ok
union all select 'fk_gone', not exists (select 1 from pg_constraint where conname = 'topics_cluster_id_fkey')
union all select 'no_constraint_mentions_pre2b',
  not exists (select 1 from pg_constraint where pg_get_constraintdef(oid) ~ '\mpre2b\.')
union all select 'topics_rows_170', (select count(*) from topic_intelligence.topics) = 170
union all select 'ti_anon_policies_kept',
  (select count(*) from pg_policies where schemaname = 'topic_intelligence'
     and policyname in ('tc_anon_read', 'tt_anon_read', 'tpm_anon_read')) = 3
union all select 'anon_select_kept',
  has_table_privilege('anon', 'topic_intelligence.topic_cluster', 'select')
  and has_table_privilege('anon', 'topic_intelligence.topic_trend', 'select')
  and has_table_privilege('anon', 'topic_intelligence.topic_pair_metric', 'select')
union all select 'service_role_select',
  has_table_privilege('service_role', 'topic_intelligence.topic_cluster', 'select')
  and has_table_privilege('service_role', 'topic_intelligence.topic_trend', 'select')
  and has_table_privilege('service_role', 'topic_intelligence.topic_pair_metric', 'select')
union all select 'views_security_invoker',
  (select count(*) from pg_class where relnamespace = 'signal_read'::regnamespace
     and relname in ('v_topic_movement', 'v_topic_intersections')
     and 'security_invoker=on' = any(reloptions)) = 2
union all select 'v_topic_movement_rows', (select count(*) from signal_read.v_topic_movement) > 0
union all select 'v_topic_intersections_rows', (select count(*) from signal_read.v_topic_intersections) > 0;
