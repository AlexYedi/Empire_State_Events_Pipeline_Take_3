-- 0028_verify.sql: probes for supabase/migrations/0028_signal_views_owner_rights.sql (YED-311).
-- Read-only. Three statements; rehearse_0028.py runs step 0 at gates 0 and 4, step 1 at gate 4, and step 2 as anon
-- and as authenticated (begin; set local role ...; step 2; rollback) at gates 1 and 4.
-- PROD ORDER (see the migration header): paste 0027 -> 0027_verify step 1 -> paste 0028 -> this file's step 1.
--
-- 0. BEFORE and AFTER apply (read-only; prod via the dashboard, the twin via the harness): row count and md5 of each
--    view's full output, ordered by every column. Run as postgres, this is what the views return to their owner;
--    after 0028 it is exactly what anon sees. The two runs must be equal: 0028 changes who the view runs as, not
--    what it returns. Also the current security state, so the prod paste can be checked against the PRE state.
select 'v_topic_movement' as probe, count(*)::text as n,
       md5(coalesce(string_agg(x::text, '|' order by x), '')) as h
  from signal_read.v_topic_movement x
union all select 'v_topic_intersections', count(*)::text,
       md5(coalesce(string_agg(x::text, '|' order by x), ''))
  from signal_read.v_topic_intersections x
union all select 'views_security_invoker_on', count(*)::text, ''
  from pg_class where relnamespace = 'signal_read'::regnamespace
   and relname in ('v_topic_movement', 'v_topic_intersections') and 'security_invoker=on' = any (coalesce(reloptions, '{}'))
union all select 'anon_policies', count(*)::text, ''
  from pg_policies where schemaname = 'topic_intelligence' and policyname in ('tc_anon_read', 'tt_anon_read', 'tpm_anon_read')
union all select 'anon_auth_ti_usage', count(*)::text, ''
  from pg_namespace n, aclexplode(n.nspacl) a where n.nspname = 'topic_intelligence' and a.privilege_type = 'USAGE'
   and a.grantee in ('anon'::regrole, 'authenticated'::regrole)
order by 1;

-- 1. AFTER apply: every row ok = true.
select 'views_owner_rights' as check_name,
  (select count(*) from pg_class where relnamespace = 'signal_read'::regnamespace
     and relname in ('v_topic_movement', 'v_topic_intersections')
     and not ('security_invoker=on' = any (coalesce(reloptions, '{}')))) = 2 as ok
union all select 'views_still_granted_to_anon_authenticated',
  has_table_privilege('anon', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('anon', 'signal_read.v_topic_intersections', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_intersections', 'select')
union all select 'views_owner_bypasses_rls',
  (select bool_and(r.rolbypassrls) from pg_class c join pg_roles r on r.oid = c.relowner
    where c.oid in ('signal_read.v_topic_movement'::regclass, 'signal_read.v_topic_intersections'::regclass))
union all select 'anon_policies_gone',
  not exists (select 1 from pg_policies where schemaname = 'topic_intelligence'
              and policyname in ('tc_anon_read', 'tt_anon_read', 'tpm_anon_read'))
union all select 'anon_authenticated_no_base_select',
  not exists (select 1 from unnest(array['topic_intelligence.topic_cluster', 'topic_intelligence.topic_trend',
                                         'topic_intelligence.topic_pair_metric']) t
              cross join unnest(array['anon', 'authenticated']) g
              where has_any_column_privilege(g, t, 'select'))
union all select 'service_role_base_select_kept',
  has_table_privilege('service_role', 'topic_intelligence.topic_cluster', 'select')
  and has_table_privilege('service_role', 'topic_intelligence.topic_trend', 'select')
  and has_table_privilege('service_role', 'topic_intelligence.topic_pair_metric', 'select')
union all select 'base_rls_still_enabled',
  (select bool_and(relrowsecurity) from pg_class where oid in ('topic_intelligence.topic_cluster'::regclass,
     'topic_intelligence.topic_trend'::regclass, 'topic_intelligence.topic_pair_metric'::regclass))
union all select 'no_other_anon_view_on_base',
  not exists (select 1 from pg_depend d join pg_rewrite rw on rw.oid = d.objid join pg_class c on c.oid = rw.ev_class
              where d.classid = 'pg_rewrite'::regclass and c.oid <> d.refobjid and c.relkind in ('v', 'm')
                and d.refobjid in ('topic_intelligence.topic_cluster'::regclass, 'topic_intelligence.topic_trend'::regclass,
                                   'topic_intelligence.topic_pair_metric'::regclass)
                and c.oid not in ('signal_read.v_topic_movement'::regclass, 'signal_read.v_topic_intersections'::regclass)
                and (has_table_privilege('anon', c.oid, 'select') or has_table_privilege('authenticated', c.oid, 'select')))
union all select 'v_topic_movement_columns_pinned',
  (select string_agg(attname, ',' order by attnum) from pg_attribute
    where attrelid = 'signal_read.v_topic_movement'::regclass and attnum > 0 and not attisdropped)
  = 'theme,window_type,as_of_date,event_count,distinct_speaker_count,momentum,trend_label,is_low_confidence'
union all select 'v_topic_intersections_columns_pinned',
  (select string_agg(attname, ',' order by attnum) from pg_attribute
    where attrelid = 'signal_read.v_topic_intersections'::regclass and attnum > 0 and not attisdropped)
  = 'theme_a,theme_b,window_type,as_of_date,cooccurrence_event_count,bridge_person_count,is_new_pair,intersection_score'
union all select 'anon_authenticated_no_ti_schema_usage',
  not has_schema_privilege('anon', 'topic_intelligence', 'usage')
  and not has_schema_privilege('authenticated', 'topic_intelligence', 'usage')
union all select 'anon_authenticated_signal_read_usage_kept',
  has_schema_privilege('anon', 'signal_read', 'usage') and has_schema_privilege('authenticated', 'signal_read', 'usage')
union all select 'service_role_ti_schema_usage_kept', has_schema_privilege('service_role', 'topic_intelligence', 'usage')
union all select 'v_topic_movement_rows', (select count(*) from signal_read.v_topic_movement) > 0
union all select 'v_topic_intersections_rows', (select count(*) from signal_read.v_topic_intersections) > 0
union all select 'k5_v_topic_movement',
  not exists (select 1 from signal_read.v_topic_movement where event_count < 5 or distinct_speaker_count < 5)
union all select 'k5_v_topic_intersections',
  not exists (select 1 from signal_read.v_topic_intersections where cooccurrence_event_count < 5 or bridge_person_count < 5);

-- 2. AS ANON (and authenticated), on the twin harness only: rehearse_0028.py wraps this in
--    `begin; set local role anon; ...; rollback;`. Do not run it on prod (as postgres in the dashboard it would only
--    repeat step 1). Every row ok = true: the views return rows to the caller, k>=5 holds in what the caller sees,
--    and the caller holds neither USAGE on topic_intelligence nor SELECT on the 3 base tables (resolved by oid from
--    pg_class, so the statement itself never needs the schema).
select 'as_' || current_user || '_v_topic_movement_rows' as check_name,
  (select count(*) from signal_read.v_topic_movement) > 0 as ok
union all select 'as_' || current_user || '_v_topic_intersections_rows',
  (select count(*) from signal_read.v_topic_intersections) > 0
union all select 'as_' || current_user || '_k5_v_topic_movement',
  not exists (select 1 from signal_read.v_topic_movement where event_count < 5 or distinct_speaker_count < 5)
union all select 'as_' || current_user || '_k5_v_topic_intersections',
  not exists (select 1 from signal_read.v_topic_intersections where cooccurrence_event_count < 5 or bridge_person_count < 5)
union all select 'as_' || current_user || '_no_ti_schema_usage', not has_schema_privilege('topic_intelligence', 'usage')
union all select 'as_' || current_user || '_no_base_select',
  not exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
              where n.nspname = 'topic_intelligence' and c.relname in ('topic_cluster', 'topic_trend', 'topic_pair_metric')
                and has_any_column_privilege(c.oid, 'select'));
