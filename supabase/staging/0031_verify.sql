-- 0031_verify.sql: probes for supabase/migrations/0031_public_spine_stats_view.sql (GTM-34).
-- Read-only. Two statements; rehearse_0031.py runs step 0 at gates P, 1, 4 and 6 and step 1 at gate 4.
-- ACLs are compared as sorted grantee:PRIVILEGE sets (PUBLIC for grantee 0), never as raw aclitem[] text.
-- Step 0 holds no row counts (twin and prod differ); step 1 compares the view to direct aggregates in the same query.
--
-- 0. BEFORE and AFTER apply (prod via the dashboard or the read-only MCP, the twin via the harness).
--    Expected change: the 4 view rows go from <absent> to the built shape, and one exposure row appears:
--    public.v_public_spine_stats=anon:SELECT,authenticated:SELECT. Every table, rls, owner, exposure and schema row
--    is otherwise identical before and after (and identical again after the rollback).
with v(oid, relacl) as (
  select c.oid, c.relacl from pg_class c where c.oid = to_regclass('public.v_public_spine_stats')
), t(rel) as (
  select unnest(array['company', 'person', 'event', 'claim'])
), ex(obj, acl) as (
  select n.nspname || '.' || c.relname, c.relacl from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and c.relkind in ('r', 'p', 'v', 'm', 'S', 'f')
     and not exists (select 1 from pg_depend d where d.classid = 'pg_class'::regclass and d.objid = c.oid and d.deptype = 'e')
  union all
  select n.nspname || '.' || c.relname || '.' || a.attname, a.attacl
    from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and a.attacl is not null
  union all
  select p.oid::regprocedure::text, coalesce(p.proacl, acldefault('f', p.proowner))
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence')
     and not exists (select 1 from pg_depend d where d.classid = 'pg_proc'::regclass and d.objid = p.oid and d.deptype = 'e')
)
select section, obj, privileges from (
  select 'view' as section, 'public.v_public_spine_stats' as obj,
         coalesce((select 'kind=' || c.relkind::text || ' owner=' || c.relowner::regrole::text || ' opts='
                          || coalesce((select string_agg(o, ',' order by o collate "C") from unnest(c.reloptions) o), '')
                     from v join pg_class c on c.oid = v.oid), '<absent>') as privileges
  union all
  select 'view_acl', 'public.v_public_spine_stats',
         case when not exists (select 1 from v) then '<absent>'
              else coalesce((select string_agg(e, ',' order by e collate "C")
                               from v, lateral (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
                                                       || ':' || a.privilege_type
                                                       || case when a.is_grantable then '*' else '' end as e
                                                  from aclexplode(v.relacl) a) s), '') end
  union all
  select 'view_cols', 'public.v_public_spine_stats',
         coalesce((select string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' order by a.attnum)
                     from v join pg_attribute a on a.attrelid = v.oid and a.attnum > 0 and not a.attisdropped), '<absent>')
  union all
  select 'view_deps', 'public.v_public_spine_stats',
         coalesce((select string_agg(dep, ',' order by dep collate "C")
                     from (select distinct rn.nspname || '.' || rc.relname || coalesce('.' || ra.attname, '') as dep
                             from v join pg_rewrite rw on rw.ev_class = v.oid
                             join pg_depend d on d.classid = 'pg_rewrite'::regclass and d.objid = rw.oid
                                             and d.refclassid = 'pg_class'::regclass and d.refobjid <> v.oid
                             join pg_class rc on rc.oid = d.refobjid
                             join pg_namespace rn on rn.oid = rc.relnamespace
                             left join pg_attribute ra on ra.attrelid = d.refobjid and ra.attnum = d.refobjsubid
                                                      and d.refobjsubid > 0) s), '<absent>')
  union all
  select 'table', 'public.' || t.rel,
         (select string_agg(e, ',' order by e collate "C")
            from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end || ':' || a.privilege_type
                         || case when a.is_grantable then '*' else '' end as e
                    from pg_class c, aclexplode(c.relacl) a where c.oid = ('public.' || t.rel)::regclass) s)
    from t
  union all
  select 'rls', 'public.' || t.rel,
         'owner=' || c.relowner::regrole::text || ' rls=' || c.relrowsecurity::text || ' force=' || c.relforcerowsecurity::text
    from t join pg_class c on c.oid = ('public.' || t.rel)::regclass
  union all
  select 'owner', 'postgres', 'bypassrls=' || rolbypassrls::text || ' super=' || rolsuper::text
    from pg_roles where rolname = 'postgres'
  union all
  select 'exposure', y.obj, string_agg(y.e, ',' order by y.e collate "C")
    from (select ex.obj, case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end || ':' || a.privilege_type as e
            from ex, aclexplode(ex.acl) a
           where a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)) y
   group by y.obj
  union all
  select 'schema', r || '@public', 'usage=' || has_schema_privilege(r, 'public', 'USAGE')
                                   || ' create=' || has_schema_privilege(r, 'public', 'CREATE')
    from unnest(array['anon', 'authenticated']) r
) x
order by section collate "C", obj collate "C";

-- 1. AFTER apply: every row ok = true.
with v as (
  select c.oid, c.relkind, c.relowner, c.reloptions, c.relacl from pg_class c
   where c.oid = to_regclass('public.v_public_spine_stats')
), base(rel) as (
  select unnest(array['public.company', 'public.person', 'public.event', 'public.claim'])
), direct as (
  select (select count(*) from public.company) + (select count(*) from public.person) as entity_count,
         (select count(*) from public.event) as event_count,
         (select count(*) from public.claim where status = 'approved') as signal_count,
         (select max(created_at) from public.claim where status = 'approved') as last_signal_at
), deps as (
  select distinct rn.nspname || '.' || rc.relname || coalesce('.' || ra.attname, '') as dep
    from v join pg_rewrite rw on rw.ev_class = v.oid
    join pg_depend d on d.classid = 'pg_rewrite'::regclass and d.objid = rw.oid
                    and d.refclassid = 'pg_class'::regclass and d.refobjid <> v.oid
    join pg_class rc on rc.oid = d.refobjid
    join pg_namespace rn on rn.oid = rc.relnamespace
    left join pg_attribute ra on ra.attrelid = d.refobjid and ra.attnum = d.refobjsubid and d.refobjsubid > 0
)
select 'view_exists' as check_name, exists (select 1 from v where relkind = 'v') as ok
union all select 'view_owner_postgres', exists (select 1 from v where relowner = 'postgres'::regrole)
union all select 'view_owner_rights',
  exists (select 1 from v)
  and coalesce((select lower(option_value) from v, pg_options_to_table(v.reloptions) where option_name = 'security_invoker'),
               'false') in ('off', 'false', '0', 'no')
union all select 'view_security_barrier',
  coalesce((select lower(option_value) from v, pg_options_to_table(v.reloptions) where option_name = 'security_barrier'),
           'false') in ('on', 'true', '1', 'yes')
union all select 'view_owner_reads_every_base_row',
  not exists (select 1 from base, pg_class c, pg_roles r
               where c.oid = base.rel::regclass and r.rolname = 'postgres'
                 and not (has_table_privilege('postgres', c.oid, 'SELECT')
                          and (r.rolbypassrls or (c.relowner = r.oid and not c.relforcerowsecurity))))
union all select 'view_api_roles_select_only',
  exists (select 1 from v)
  and not exists (select 1 from unnest(array['anon', 'authenticated', 'service_role']) r
                   where not has_table_privilege(r, 'public.v_public_spine_stats', 'SELECT')
                      or has_table_privilege(r, 'public.v_public_spine_stats',
                                             'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'))
union all select 'view_acl_exact',
  (select string_agg(e, ',' order by e collate "C")
     from v, lateral (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end || ':' || a.privilege_type
                             || case when a.is_grantable then '*' else '' end as e from aclexplode(v.relacl) a) s)
  = 'anon:SELECT,authenticated:SELECT,postgres:DELETE,postgres:INSERT,postgres:MAINTAIN,postgres:REFERENCES,'
    'postgres:SELECT,postgres:TRIGGER,postgres:TRUNCATE,postgres:UPDATE,service_role:SELECT'
union all select 'view_no_public_items',
  exists (select 1 from v) and not exists (select 1 from v, aclexplode(v.relacl) a where a.grantee = 0)
union all select 'base_tables_no_anon_authenticated',
  not exists (select 1 from base, unnest(array['anon', 'authenticated']) r
               where has_table_privilege(r, base.rel, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
                  or has_any_column_privilege(r, base.rel, 'SELECT,INSERT,UPDATE,REFERENCES'))
union all select 'base_tables_no_public_items',
  not exists (select 1 from base, pg_class c, aclexplode(c.relacl) a
               where c.oid = base.rel::regclass and (a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)))
union all select 'base_tables_rls_on',
  not exists (select 1 from base, pg_class c where c.oid = base.rel::regclass and not c.relrowsecurity)
union all select 'view_returns_one_row', (select count(*) from public.v_public_spine_stats) = 1
union all select 'view_counts_match_direct_aggregates',
  coalesce((select s.entity_count = d.entity_count and s.event_count = d.event_count and s.signal_count = d.signal_count
                   and s.last_signal_at is not distinct from d.last_signal_at
              from public.v_public_spine_stats s, direct d), false)
union all select 'view_counts_nonzero',
  coalesce((select entity_count > 0 and event_count > 0 and signal_count > 0 and last_signal_at is not null
              from public.v_public_spine_stats), false)
union all select 'view_columns_exact',
  (select string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' order by a.attnum)
     from v join pg_attribute a on a.attrelid = v.oid and a.attnum > 0 and not a.attisdropped)
  = 'entity_count:bigint,event_count:bigint,signal_count:bigint,last_signal_at:timestamp with time zone'
union all select 'view_no_text_columns',
  exists (select 1 from v)
  and not exists (select 1 from v join pg_attribute a on a.attrelid = v.oid and a.attnum > 0 and not a.attisdropped
                   join pg_type ty on ty.oid = a.atttypid
                   where ty.typcategory in ('S', 'U', 'A') or ty.typname in ('json', 'jsonb', 'uuid'))
union all select 'view_reads_only_aggregate_inputs',
  (select string_agg(dep, ',' order by dep collate "C") from deps)
  = 'public.claim.created_at,public.claim.status,public.company,public.event,public.person';
