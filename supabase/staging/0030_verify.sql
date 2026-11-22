-- 0030_verify.sql: probes for supabase/migrations/0030_revoke_existing_api_grants.sql (YED-483).
-- Read-only. Two statements; rehearse_0030.py runs step 0 at gates P, 1 and 4 and step 1 at gate 4.
-- ACLs are compared as sorted grantee:PRIVILEGE sets (PUBLIC for grantee 0), never as raw aclitem[] text.
--
-- 0. BEFORE and AFTER apply (prod via the dashboard or the read-only MCP, the twin via the harness).
--    Expected change: table rows lose anon:SELECT and authenticated:SELECT; function rows lose PUBLIC/anon/
--    authenticated:EXECUTE (the 3 trigger functions gain pipeline_writer:EXECUTE); the database row loses
--    PUBLIC:TEMPORARY and gains <role>:TEMPORARY for the 7 keep roles; temp rows flip to f for anon, authenticated,
--    authenticator, pgbouncer, supabase_privileged_role and supabase_read_only_user. Every exposure, connect and schema
--    row is identical before and after.
with t(rel) as (
  select unnest(array['artifact_outcome', 'claim', 'claim_entity', 'claim_relation', 'claim_usage', 'doc_chunks',
                      'doc_claims', 'document_entity', 'documents', 'company', 'event', 'event_entity', 'person', 'topic'])
), f(fn) as (
  select unnest(array['public.set_updated_at()', 'public.assert_no_contact_pii()', 'public.assert_no_pii_columns()',
                      'public.match_doc_chunks(vector,integer,uuid,text)',
                      'public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)'])
), roles(r) as (
  select rolname::text from pg_roles
   where rolname in ('postgres', 'service_role', 'pipeline_writer', 'anon', 'authenticated', 'authenticator', 'pgbouncer',
                     'dashboard_user', 'supabase_admin', 'supabase_auth_admin', 'supabase_storage_admin', 'supabase_etl_admin',
                     'supabase_realtime_admin', 'supabase_replication_admin', 'supabase_privileged_role',
                     'supabase_read_only_user')
), o(section, obj, acl) as (
  select 'table', 'public.' || c.relname, c.relacl from t join pg_class c on c.oid = ('public.' || t.rel)::regclass
  union all
  select 'function', f.fn, coalesce(p.proacl, acldefault('f', p.proowner)) from f join pg_proc p on p.oid = f.fn::regprocedure
  union all
  select 'database', d.datname::text, coalesce(d.datacl, acldefault('d', d.datdba)) from pg_database d
   where d.datname = current_database()
), ex(obj, acl) as (
  select n.nspname || '.' || c.relname, c.relacl from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and c.relkind in ('r', 'p', 'v', 'm', 'S', 'f')
     and not (n.nspname = 'public' and c.relname in (select rel from t))
     and not exists (select 1 from pg_depend d where d.classid = 'pg_class'::regclass and d.objid = c.oid and d.deptype = 'e')
  union all
  select n.nspname || '.' || c.relname || '.' || a.attname, a.attacl
    from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and a.attacl is not null
  union all
  select p.oid::regprocedure::text, coalesce(p.proacl, acldefault('f', p.proowner))
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence')
     and p.oid not in (select fn::regprocedure::oid from f)
     and not exists (select 1 from pg_depend d where d.classid = 'pg_proc'::regclass and d.objid = p.oid and d.deptype = 'e')
)
select section, obj, privileges from (
  select o.section, o.obj,
         (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
            || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e from aclexplode(o.acl) a) s) as privileges
    from o
  union all
  select 'exposure', y.obj, string_agg(y.e, ',' order by y.e collate "C")
    from (select ex.obj, case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end || ':' || a.privilege_type as e
            from ex, aclexplode(ex.acl) a
           where a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)) y
   group by y.obj
  union all
  select 'temp', r, has_database_privilege(r, current_database(), 'TEMP')::text from roles
  union all
  select 'connect', r, has_database_privilege(r, current_database(), 'CONNECT')::text from roles
  union all
  select 'schema', r || '@' || s, 'usage=' || has_schema_privilege(r, s, 'USAGE') || ' create=' || has_schema_privilege(r, s, 'CREATE')
    from unnest(array['anon', 'authenticated', 'supabase_read_only_user']) r,
         unnest(array['public', 'mi', 'signal_read', 'topic_intelligence']) s
) x
order by section collate "C", obj collate "C";

-- 1. AFTER apply: every row ok = true.
with t(rel, sr) as (
  select unnest(array['artifact_outcome', 'claim', 'claim_entity', 'claim_relation', 'claim_usage', 'doc_chunks',
                      'doc_claims', 'document_entity', 'documents', 'company', 'event', 'event_entity', 'person', 'topic']),
         unnest(array['arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm', 'arwdDxtm',
                      'arwd', 'arwd', 'arwd', 'arwd', 'arwd'])
), f(fn, trig) as (
  select unnest(array['public.set_updated_at()', 'public.assert_no_contact_pii()', 'public.assert_no_pii_columns()',
                      'public.match_doc_chunks(vector,integer,uuid,text)',
                      'public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)']),
         unnest(array[true, true, true, false, false])
), sr_acl as (
  select t.rel, t.sr,
         (select string_agg(a.privilege_type, ',' order by a.privilege_type collate "C") from pg_class c, aclexplode(c.relacl) a
           where c.oid = ('public.' || t.rel)::regclass and a.grantee = 'service_role'::regrole) as got
    from t
)
select 'tables_no_anon_authenticated' as check_name,
  not exists (select 1 from t, unnest(array['anon', 'authenticated']) r
               where has_table_privilege(r, 'public.' || t.rel, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')) as ok
union all select 'tables_no_public_items',
  not exists (select 1 from t, pg_class c, aclexplode(c.relacl) a where c.oid = ('public.' || t.rel)::regclass
               and (a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)))
union all select 'tables_service_role_unchanged',
  bool_and(got = case sr when 'arwdDxtm' then 'DELETE,INSERT,MAINTAIN,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE'
                                          else 'DELETE,INSERT,SELECT,UPDATE' end) from sr_acl
union all select 'tables_postgres_unchanged',
  not exists (select 1 from t where (select string_agg(a.privilege_type, ',' order by a.privilege_type collate "C")
                                        from pg_class c, aclexplode(c.relacl) a
                                       where c.oid = ('public.' || t.rel)::regclass and a.grantee = 'postgres'::regrole)
                                     is distinct from 'DELETE,INSERT,MAINTAIN,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE')
union all select 'functions_no_public_anon_authenticated',
  not exists (select 1 from f, pg_proc p, aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
               where p.oid = f.fn::regprocedure and (a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)))
  and not exists (select 1 from f, unnest(array['anon', 'authenticated']) r where has_function_privilege(r, f.fn, 'execute'))
union all select 'functions_postgres_service_role_execute',
  not exists (select 1 from f, unnest(array['postgres', 'service_role']) r where not has_function_privilege(r, f.fn, 'execute'))
union all select 'trigger_functions_pipeline_writer_explicit',
  not exists (select 1 from f where f.trig and not exists (
    select 1 from pg_proc p, aclexplode(p.proacl) a where p.oid = f.fn::regprocedure and a.grantee = 'pipeline_writer'::regrole))
union all select 'read_only_user_cannot_create_temp',
  not has_database_privilege('supabase_read_only_user', current_database(), 'TEMP')
union all select 'api_roles_cannot_create_temp',
  not has_database_privilege('anon', current_database(), 'TEMP')
  and not has_database_privilege('authenticated', current_database(), 'TEMP')
  and not has_database_privilege('authenticator', current_database(), 'TEMP')
union all select 'database_no_public_temp',
  not exists (select 1 from pg_database d, aclexplode(coalesce(d.datacl, acldefault('d', d.datdba))) a
               where d.datname = current_database() and a.grantee = 0 and a.privilege_type = 'TEMPORARY')
union all select 'temp_keep_roles_hold_temp',
  not exists (select 1 from unnest(array['postgres', 'dashboard_user', 'supabase_admin', 'service_role', 'pipeline_writer',
                                         'supabase_auth_admin', 'supabase_storage_admin', 'supabase_etl_admin',
                                         'supabase_realtime_admin', 'supabase_replication_admin']) r
               where not has_database_privilege(r, current_database(), 'TEMP'))
union all select 'connect_kept',
  not exists (select 1 from unnest(array['anon', 'authenticated', 'authenticator', 'supabase_read_only_user', 'service_role']) r
               where not has_database_privilege(r, current_database(), 'CONNECT'))
union all select 'read_only_user_reads_kept',
  not exists (select 1 from t where not has_table_privilege('supabase_read_only_user', 'public.' || t.rel, 'SELECT'))
union all select 'keep_signal_read_views_anon',
  has_table_privilege('anon', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('anon', 'signal_read.v_topic_intersections', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_movement', 'select')
  and has_table_privilege('authenticated', 'signal_read.v_topic_intersections', 'select')
union all select 'keep_schema_usage',
  has_schema_privilege('anon', 'public', 'USAGE') and has_schema_privilege('authenticated', 'public', 'USAGE')
  and has_schema_privilege('anon', 'signal_read', 'USAGE') and has_schema_privilege('authenticated', 'signal_read', 'USAGE');
