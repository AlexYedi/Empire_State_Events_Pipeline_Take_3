-- 0029_verify.sql: probes for supabase/migrations/0029_default_privileges_api_roles.sql (YED-482).
-- Read-only. Two statements; rehearse_0029.py runs step 0 at gates 0 and 4 and step 1 at gate 4.
-- Default ACLs are compared as sorted grantee:PRIVILEGE sets (PUBLIC for grantee 0), never as raw aclitem[] text:
-- a revoke + re-grant appends entries, so the raw array order changes while the privileges are identical.
--
-- 0. BEFORE and AFTER apply (prod via the dashboard, the twin via the harness): every pg_default_acl row, canonical.
--    Expected change: postgres/public r, S, f lose their anon:* and authenticated:* items, and a new row
--    postgres/(global)/f = postgres:EXECUTE appears. Every other row (service_role items included, storage, and all
--    supabase_admin / supabase_auth_admin rows) is identical before and after.
select defaclrole::regrole::text as role,
       case defaclnamespace when 0 then '(global)' else defaclnamespace::regnamespace::text end as nsp,
       defaclobjtype::text as objtype,
       (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
          || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
          from aclexplode(d.defaclacl) a) s) as privileges
  from pg_default_acl d
 order by 1, 2, 3;

-- 1. AFTER apply: every row ok = true.
with d as (
  select case defaclnamespace when 0 then '(global)' else defaclnamespace::regnamespace::text end as nsp,
         defaclobjtype::text as t, defaclacl
    from pg_default_acl where defaclrole = 'postgres'::regrole
), x as (
  select d.nsp, d.t, case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end as g, a.privilege_type as p
    from d, aclexplode(d.defaclacl) a
)
select 'postgres_public_tables_no_anon_authenticated' as check_name,
  exists (select 1 from d where nsp = 'public' and t = 'r')
  and not exists (select 1 from x where nsp = 'public' and t = 'r' and g in ('anon', 'authenticated', 'PUBLIC')) as ok
union all select 'postgres_public_sequences_no_anon_authenticated',
  exists (select 1 from d where nsp = 'public' and t = 'S')
  and not exists (select 1 from x where nsp = 'public' and t = 'S' and g in ('anon', 'authenticated', 'PUBLIC'))
union all select 'postgres_public_functions_no_anon_authenticated',
  exists (select 1 from d where nsp = 'public' and t = 'f')
  and not exists (select 1 from x where nsp = 'public' and t = 'f' and g in ('anon', 'authenticated', 'PUBLIC'))
union all select 'postgres_global_functions_no_public_execute',
  (select string_agg(g || ':' || p, ',' order by g collate "C", p collate "C") from x where nsp = '(global)' and t = 'f') = 'postgres:EXECUTE'
union all select 'postgres_no_other_global_entries',
  not exists (select 1 from d where nsp = '(global)' and t <> 'f')
union all select 'postgres_pipeline_schemas_no_api_role_defaults',
  not exists (select 1 from x where nsp in ('mi', 'signal_read', 'topic_intelligence')
              and g in ('anon', 'authenticated', 'PUBLIC'))
union all select 'service_role_public_tables_unchanged',
  (select string_agg(p, ',' order by p collate "C") from x where nsp = 'public' and t = 'r' and g = 'service_role')
  = 'DELETE,INSERT,MAINTAIN,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE'
union all select 'service_role_public_sequences_unchanged',
  (select string_agg(p, ',' order by p collate "C") from x where nsp = 'public' and t = 'S' and g = 'service_role') = 'SELECT,UPDATE,USAGE'
union all select 'service_role_public_functions_unchanged',
  (select string_agg(p, ',' order by p collate "C") from x where nsp = 'public' and t = 'f' and g = 'service_role') = 'EXECUTE'
union all select 'postgres_own_public_entries_unchanged',
  (select string_agg(t || '=' || p, ',' order by t collate "C", p collate "C") from x where nsp = 'public' and g = 'postgres')
  = 'S=SELECT,S=UPDATE,S=USAGE,f=EXECUTE,r=DELETE,r=INSERT,r=MAINTAIN,r=REFERENCES,r=SELECT,r=TRIGGER,r=TRUNCATE,r=UPDATE'
union all select 'storage_defaults_untouched_out_of_scope',
  (select count(*) from x where nsp = 'storage') = 48
  and (select count(*) from x where nsp = 'storage' and g in ('anon', 'authenticated')) = 24
union all select 'existing_signal_read_views_still_granted',
  has_table_privilege('anon', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('anon', 'signal_read.v_topic_intersections', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_intersections', 'select');
