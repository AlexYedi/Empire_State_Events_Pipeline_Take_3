-- =============================================================================
-- 0030 · existing public objects: anon/authenticated lose their dormant grants; TEMP on the database is no longer
--        granted to PUBLIC (closes the read-only MCP role's temp-table write path)
-- Linear: YED-483 (follow-up to 0029 / YED-482) + add-on: the TEMP gap of supabase_read_only_user.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0030.py --execute
-- Before AND after the paste, run staging/0030_verify.sql step 0 on prod (read-only) and keep both outputs.
-- After the paste, step 1 must show every row ok = t.
--
-- WHY:
--   0029 stopped NEW objects from auto-granting the API roles. EXISTING objects kept what the old defaults gave them.
--   Read-only on prod, 2026-11-22:
--     * 14 public tables grant SELECT to anon and authenticated. RLS is on with 0 policies, so anon reads 0 rows
--       today (REST GET /rest/v1/person with the publishable key: 200, Content-Range */0). RLS is the only gate:
--       one permissive policy added later opens the table. Same pattern as YED-311.
--     * 5 public functions (all postgres-owned, SECURITY INVOKER) grant EXECUTE to PUBLIC, anon and authenticated:
--       match_doc_chunks, match_doc_chunks_hybrid (RPC-callable by anon), and the trigger functions
--       set_updated_at, assert_no_contact_pii, assert_no_pii_columns.
--     * pg_database.datacl for postgres is {=Tc/postgres,...}: PUBLIC holds TEMPORARY. That is the ONLY way
--       supabase_read_only_user (the Supabase MCP connector's login; default_transaction_read_only=on, no CREATE on
--       any schema) gets TEMP, so `set transaction read write; create temp table ...` works for it. anon and
--       authenticated get TEMP the same way.
--
-- LIVE-USE CHECK (read-only, prod, last 24h of edge_logs, apikey prefix not sb_secret):
--   * node (gtm-os-hub /signal): GET signal_read.v_topic_movement, v_topic_intersections (200) and
--     public.v_public_spine_stats (404, missing: GTM-34). Nothing else.
--   * curl from the operator's IP: one-off probes during the 0028 build (claim and person returned */0, the
--     topic_intelligence base tables, /graphql/v1). Not a dependency.
--   * No /rest/v1/rpc call with a publishable key. All RPC traffic (entity_neighborhood, match_claims_hybrid,
--     mi_slice) used sb_secret (service_role). Every spine write used sb_secret.
--   So nothing live uses a grant revoked here, and the keep list below is what gtm-os-hub reads.
--
-- WHAT (one transaction; idempotent: a second paste raises a NOTICE and changes nothing):
--   PART 1  preflight. Raises unless the session can act as postgres and the in-scope state is EXACTLY one of:
--             PRE   the 14 tables, 5 functions and the database ACL as listed in the constants below, AND the only
--                   other anon/authenticated/PUBLIC grants on non-extension objects in public, mi, signal_read and
--                   topic_intelligence are SELECT on the two signal_read views;
--             POST  the same with the revokes and explicit grants of PART 2 in place: NOTICE, then no-op.
--           Anything else (a mixed state, a new anon-granted object, a missing role) raises: inspect by hand.
--   PART 2  only in PRE:
--             revoke all on the 14 tables from anon, authenticated
--             revoke all on the 5 functions from public, anon, authenticated
--             grant execute on the 3 trigger functions to pipeline_writer (it held EXECUTE only through PUBLIC)
--             revoke temporary on database from public
--             grant temporary on database to service_role, pipeline_writer, supabase_auth_admin,
--               supabase_storage_admin, supabase_etl_admin, supabase_realtime_admin, supabase_replication_admin
--   PART 3  postflight: raises (rolling back everything) unless the exact POST state holds, the keep list is intact,
--           service_role and postgres hold exactly what they held before, and has_database_privilege(..., 'TEMP') is
--           false for supabase_read_only_user, anon, authenticated and authenticator and true for every role in the
--           TEMP keep list.
--
-- KEEP (not touched; asserted by PART 1 and PART 3):
--   * SELECT for anon, authenticated on signal_read.v_topic_movement and v_topic_intersections (gtm-os-hub /signal).
--   * USAGE on schema public (PUBLIC, anon, authenticated) and on schema signal_read (anon, authenticated).
--   * CONNECT on the database for PUBLIC (every login still connects).
--   * service_role: its existing table rights (arwdDxtm on 9 tables, arwd on company/event/event_entity/person/topic)
--     and its explicit EXECUTE on all 5 functions. postgres: everything (owner).
--   * supabase_read_only_user keeps every read (pg_read_all_data); it loses only TEMP.
--
-- TRIGGERS AND WHO NEEDS EXECUTE:
--   set_updated_at fires on public artifact_outcome, company, event, person, topic (BEFORE UPDATE);
--   assert_no_contact_pii and assert_no_pii_columns fire on public.person (BEFORE INSERT OR UPDATE). Postgres checks
--   EXECUTE on a trigger function when the trigger is CREATED, not when it fires (the rehearsal shows a trigger still
--   firing for a role with no EXECUTE on it). Functions the trigger body CALLS are checked as the statement's role:
--   assert_no_contact_pii calls public.no_contact_pii_v2, which is postgres + service_role only (unchanged).
--   Writers: service_role (spine_client.py, gtm-os lib/spine.ts) holds EXECUTE explicitly already. pipeline_writer
--   writes no public table today (topic_intelligence only), but held EXECUTE only via PUBLIC, so it gets it
--   explicitly on the 3 trigger functions. No other role writes these tables.
--
-- SCOPE NOTES:
--   * Sequences and views: no public sequence and no view other than the two signal_read views grants anything to
--     anon/authenticated/PUBLIC on prod (PART 1 asserts it), so nothing to revoke there.
--   * Extension objects (pgvector's ~110 functions in public, owned by supabase_admin) keep PUBLIC/anon/authenticated
--     EXECUTE. They are extension members, postgres does not own them, and the vector operators need them.
--   * supabase_privileged_role, authenticator and pgbouncer lose TEMP with PUBLIC and do not get it back: none of
--     them creates temp tables (PostgREST runs requests after SET ROLE; pgbouncer only runs its auth query).
--     supabase_admin is a superuser; postgres and dashboard_user hold TEMP explicitly already.
--   * TEMP on the database is granted by postgres (the database owner, grantor of the PUBLIC item), so postgres can
--     revoke it. No Supabase-managed grantor is involved; nothing had to be skipped.
--
-- RULE FOR EVERY FUTURE MIGRATION (0029 + this): an object is reachable only by its owner and the roles its migration
--   GRANTs explicitly. Anon access is a deliberate `grant select on <view> to anon, authenticated` (e.g. GTM-34's
--   v_public_spine_stats). A role that needs temp tables needs `grant temporary on database postgres to <role>`.
--
-- LOCKS: GRANT/REVOKE update catalog rows only; no table rewrite. lock_timeout = 5s.
--
-- ROLLBACK (exact statements; rehearse_0030.py gate 5 runs this block verbatim from this header and proves the raw
--   ACLs come back byte-identical, item order included). The 9 tables re-grant service_role after anon/authenticated
--   and the functions are rebuilt from empty, because Postgres appends a re-granted item at the end of the ACL:
-- ROLLBACK-BEGIN
--   begin;
--   revoke all on public.artifact_outcome, public.claim, public.claim_entity, public.claim_relation,
--     public.claim_usage, public.doc_chunks, public.doc_claims, public.document_entity, public.documents
--     from service_role;
--   grant select on public.artifact_outcome, public.claim, public.claim_entity, public.claim_relation,
--     public.claim_usage, public.doc_chunks, public.doc_claims, public.document_entity, public.documents
--     to anon, authenticated;
--   grant all on public.artifact_outcome, public.claim, public.claim_entity, public.claim_relation,
--     public.claim_usage, public.doc_chunks, public.doc_claims, public.document_entity, public.documents
--     to service_role;
--   grant select on public.company, public.event, public.event_entity, public.person, public.topic
--     to anon, authenticated;
--   revoke all on function public.set_updated_at(), public.assert_no_contact_pii(), public.assert_no_pii_columns(),
--     public.match_doc_chunks(vector, integer, uuid, text),
--     public.match_doc_chunks_hybrid(vector, text, integer, integer, integer, uuid, text)
--     from public, postgres, anon, authenticated, service_role, pipeline_writer;
--   grant execute on function public.set_updated_at(), public.assert_no_contact_pii(), public.assert_no_pii_columns(),
--     public.match_doc_chunks(vector, integer, uuid, text),
--     public.match_doc_chunks_hybrid(vector, text, integer, integer, integer, uuid, text)
--     to public, postgres, anon, authenticated, service_role;
--   revoke temporary on database postgres from service_role, pipeline_writer, supabase_auth_admin,
--     supabase_storage_admin, supabase_etl_admin, supabase_realtime_admin, supabase_replication_admin;
--   grant temporary on database postgres to public;
--   commit;
-- ROLLBACK-END
-- =============================================================================

begin;

set local lock_timeout = '5s';

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  t9  constant text[] := array['artifact_outcome', 'claim', 'claim_entity', 'claim_relation', 'claim_usage',
                               'doc_chunks', 'doc_claims', 'document_entity', 'documents'];
  t5  constant text[] := array['company', 'event', 'event_entity', 'person', 'topic'];
  f3  constant text[] := array['public.set_updated_at()', 'public.assert_no_contact_pii()', 'public.assert_no_pii_columns()'];
  f2  constant text[] := array['public.match_doc_chunks(vector,integer,uuid,text)',
                               'public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)'];
  all8 constant text[] := array['DELETE', 'INSERT', 'MAINTAIN', 'REFERENCES', 'SELECT', 'TRIGGER', 'TRUNCATE', 'UPDATE'];
  temp_keep constant text[] := array['service_role', 'pipeline_writer', 'supabase_auth_admin', 'supabase_storage_admin',
                                     'supabase_etl_admin', 'supabase_realtime_admin', 'supabase_replication_admin'];
  keep_exposure constant text := 'signal_read.v_topic_intersections=anon:SELECT,authenticated:SELECT;'
                                 'signal_read.v_topic_movement=anon:SELECT,authenticated:SELECT';
  db_pre constant text[] := array['PUBLIC:CONNECT', 'PUBLIC:TEMPORARY', 'dashboard_user:CONNECT', 'dashboard_user:CREATE',
                                  'dashboard_user:TEMPORARY', 'postgres:CONNECT', 'postgres:CREATE', 'postgres:TEMPORARY',
                                  'supabase_etl_admin:CREATE', 'supabase_storage_admin:CREATE'];
  want_pre text; want_post text; got text; got_exposure text; v_missing text;
  pg8 text[]; sr8 text[]; sr4 text[];
begin
  if not pg_has_role(current_user, 'postgres', 'member') then
    raise exception '0030 preflight: % cannot act as postgres (not a member). Paste as postgres.', current_user;
  end if;
  select string_agg(r, ',') into v_missing
    from unnest(temp_keep || array['anon', 'authenticated', 'authenticator', 'supabase_read_only_user', 'dashboard_user']) r
   where not exists (select 1 from pg_roles where rolname = r);
  if v_missing is not null then
    raise exception '0030 preflight: expected roles missing: %. Inspect by hand.', v_missing;
  end if;

  pg8 := array(select 'postgres:' || p from unnest(all8) p);
  sr8 := array(select 'service_role:' || p from unnest(all8) p);
  sr4 := array['service_role:DELETE', 'service_role:INSERT', 'service_role:SELECT', 'service_role:UPDATE'];

  -- expected canonical state: "object=sorted grantee:PRIV list" items, sorted, ';'-joined
  with e(obj, pre, post) as (
    select 'public.' || t, array['anon:SELECT', 'authenticated:SELECT'] || pg8 || sr8, pg8 || sr8 from unnest(t9) t
    union all
    select 'public.' || t, array['anon:SELECT', 'authenticated:SELECT'] || pg8 || sr4, pg8 || sr4 from unnest(t5) t
    union all
    select f, array['PUBLIC:EXECUTE', 'anon:EXECUTE', 'authenticated:EXECUTE', 'postgres:EXECUTE', 'service_role:EXECUTE'],
              array['pipeline_writer:EXECUTE', 'postgres:EXECUTE', 'service_role:EXECUTE'] from unnest(f3) f
    union all
    select f, array['PUBLIC:EXECUTE', 'anon:EXECUTE', 'authenticated:EXECUTE', 'postgres:EXECUTE', 'service_role:EXECUTE'],
              array['postgres:EXECUTE', 'service_role:EXECUTE'] from unnest(f2) f
    union all
    select 'database', db_pre,
           array(select x from unnest(db_pre) x where x <> 'PUBLIC:TEMPORARY') || array(select r || ':TEMPORARY' from unnest(temp_keep) r)
  )
  select string_agg(obj || '=' || (select string_agg(x, ',' order by x collate "C") from unnest(pre) x), ';' order by obj collate "C"),
         string_agg(obj || '=' || (select string_agg(x, ',' order by x collate "C") from unnest(post) x), ';' order by obj collate "C")
    into want_pre, want_post from e;

  -- actual canonical state of the same objects
  with o(obj, acl) as (
    select 'public.' || c.relname, c.relacl from pg_class c
     where c.relnamespace = 'public'::regnamespace and c.relname = any (t9 || t5) and c.relkind = 'r'
    union all
    select f, coalesce(p.proacl, acldefault('f', p.proowner)) from unnest(f3 || f2) f join pg_proc p on p.oid = f::regprocedure
    union all
    select 'database', coalesce(d.datacl, acldefault('d', d.datdba)) from pg_database d where d.datname = current_database()
  )
  select string_agg(obj || '=' || coalesce((select string_agg(e, ',' order by e collate "C")
                                  from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
                                          || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
                                          from aclexplode(acl) a) s), ''), ';' order by obj collate "C")
    into got from o;

  -- every other anon/authenticated/PUBLIC grant on a non-extension object in the pipeline schemas
  with o(obj, acl) as (
    select n.nspname || '.' || c.relname, c.relacl from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and c.relkind in ('r', 'p', 'v', 'm', 'S', 'f')
       and not (n.nspname = 'public' and c.relname = any (t9 || t5))
       and not exists (select 1 from pg_depend d where d.classid = 'pg_class'::regclass and d.objid = c.oid and d.deptype = 'e')
    union all
    select n.nspname || '.' || c.relname || '.' || a.attname, a.attacl
      from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
     where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence') and a.attacl is not null
    union all
    select p.oid::regprocedure::text, coalesce(p.proacl, acldefault('f', p.proowner))
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
     where n.nspname in ('public', 'mi', 'signal_read', 'topic_intelligence')
       and p.oid <> all (array(select f::regprocedure::oid from unnest(f3 || f2) f))
       and not exists (select 1 from pg_depend d where d.classid = 'pg_proc'::regclass and d.objid = p.oid and d.deptype = 'e')
  ), x as (
    select obj, string_agg(e, ',' order by e collate "C") as privs
      from (select o.obj, case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end || ':' || a.privilege_type as e
              from o, aclexplode(o.acl) a
             where a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole)) y
     group by obj
  )
  select string_agg(obj || '=' || privs, ';' order by obj collate "C") into got_exposure from x;

  if got_exposure is distinct from keep_exposure then
    raise exception '0030 preflight: anon/authenticated/PUBLIC grants outside the in-scope list differ from the keep list. got [%], want [%]. Inspect by hand.',
      coalesce(got_exposure, '<none>'), keep_exposure;
  end if;

  if got = want_pre then
    perform set_config('mig0030.state', 'pre', true);
    raise notice '0030 preflight OK: PRE state (14 tables anon/authenticated SELECT, 5 functions PUBLIC/anon/authenticated EXECUTE, database TEMP to PUBLIC; keep list exact).';
  elsif got = want_post then
    perform set_config('mig0030.state', 'post', true);
    raise notice '0030: already applied (tables, functions and database TEMP in the POST state); nothing to do.';
  else
    raise exception E'0030 preflight: mixed or unexpected state. Inspect by hand.\n got      [%]\n want PRE [%]\n want POST[%]',
      got, want_pre, want_post;
  end if;
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $apply$
begin
  if current_setting('mig0030.state', true) is distinct from 'pre' then
    return;
  end if;

  revoke all on public.artifact_outcome, public.claim, public.claim_entity, public.claim_relation, public.claim_usage,
                public.doc_chunks, public.doc_claims, public.document_entity, public.documents,
                public.company, public.event, public.event_entity, public.person, public.topic
    from anon, authenticated;
  raise notice '0030: 14 public tables no longer granted to anon, authenticated';

  revoke all on function public.set_updated_at(), public.assert_no_contact_pii(), public.assert_no_pii_columns(),
                         public.match_doc_chunks(vector, integer, uuid, text),
                         public.match_doc_chunks_hybrid(vector, text, integer, integer, integer, uuid, text)
    from public, anon, authenticated;
  grant execute on function public.set_updated_at(), public.assert_no_contact_pii(), public.assert_no_pii_columns()
    to pipeline_writer;
  raise notice '0030: 5 public functions no longer executable by PUBLIC, anon, authenticated; pipeline_writer holds EXECUTE on the 3 trigger functions explicitly';

  execute format('revoke temporary on database %I from public', current_database());
  execute format('grant temporary on database %I to service_role, pipeline_writer, supabase_auth_admin, '
                 'supabase_storage_admin, supabase_etl_admin, supabase_realtime_admin, supabase_replication_admin',
                 current_database());
  raise notice '0030: TEMP on database % no longer granted to PUBLIC; granted explicitly to the 7 roles that may need temp tables',
               current_database();
end
$apply$;

-- PART 3 ---------------------------------------------------------------------------------------------------------
do $post$
declare
  t14 constant text[] := array['artifact_outcome', 'claim', 'claim_entity', 'claim_relation', 'claim_usage', 'doc_chunks',
                               'doc_claims', 'document_entity', 'documents', 'company', 'event', 'event_entity', 'person', 'topic'];
  t9  constant text[] := array['artifact_outcome', 'claim', 'claim_entity', 'claim_relation', 'claim_usage',
                               'doc_chunks', 'doc_claims', 'document_entity', 'documents'];
  f5  constant text[] := array['public.set_updated_at()', 'public.assert_no_contact_pii()', 'public.assert_no_pii_columns()',
                               'public.match_doc_chunks(vector,integer,uuid,text)',
                               'public.match_doc_chunks_hybrid(vector,text,integer,integer,integer,uuid,text)'];
  f3  constant text[] := array['public.set_updated_at()', 'public.assert_no_contact_pii()', 'public.assert_no_pii_columns()'];
  temp_yes constant text[] := array['postgres', 'dashboard_user', 'supabase_admin', 'service_role', 'pipeline_writer',
                                    'supabase_auth_admin', 'supabase_storage_admin', 'supabase_etl_admin',
                                    'supabase_realtime_admin', 'supabase_replication_admin'];
  temp_no  constant text[] := array['supabase_read_only_user', 'anon', 'authenticated', 'authenticator'];
  v_fail text[] := '{}';
  r text; t text; f text; got text; want text;
begin
  foreach t in array t14 loop
    foreach r in array array['anon', 'authenticated'] loop
      if has_table_privilege(r, 'public.' || t, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN') then
        v_fail := v_fail || format('%s still holds a privilege on public.%s', r, t);
      end if;
    end loop;
    select string_agg(a.privilege_type, ',' order by a.privilege_type collate "C") into got
      from pg_class c, aclexplode(c.relacl) a
     where c.oid = ('public.' || t)::regclass and a.grantee = 'service_role'::regrole;
    want := case when t = any (t9) then 'DELETE,INSERT,MAINTAIN,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE'
                 else 'DELETE,INSERT,SELECT,UPDATE' end;
    if got is distinct from want then
      v_fail := v_fail || format('service_role on public.%s is [%s], want [%s]', t, got, want);
    end if;
    select string_agg(a.privilege_type, ',' order by a.privilege_type collate "C") into got
      from pg_class c, aclexplode(c.relacl) a
     where c.oid = ('public.' || t)::regclass and a.grantee = 'postgres'::regrole;
    if got is distinct from 'DELETE,INSERT,MAINTAIN,REFERENCES,SELECT,TRIGGER,TRUNCATE,UPDATE' then
      v_fail := v_fail || format('postgres on public.%s is [%s]', t, got);
    end if;
    if not has_table_privilege('supabase_read_only_user', 'public.' || t, 'SELECT') then
      v_fail := v_fail || format('supabase_read_only_user can no longer read public.%s', t);
    end if;
  end loop;

  foreach f in array f5 loop
    if exists (select 1 from pg_proc p, aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
                where p.oid = f::regprocedure and (a.grantee = 0 or a.grantee in ('anon'::regrole, 'authenticated'::regrole))) then
      v_fail := v_fail || format('%s still grants EXECUTE to PUBLIC/anon/authenticated', f);
    end if;
    foreach r in array array['anon', 'authenticated'] loop
      if has_function_privilege(r, f, 'execute') then
        v_fail := v_fail || format('%s can still execute %s', r, f);
      end if;
    end loop;
    foreach r in array array['postgres', 'service_role'] loop
      if not has_function_privilege(r, f, 'execute') then
        v_fail := v_fail || format('%s lost EXECUTE on %s', r, f);
      end if;
    end loop;
    if f = any (f3) and not has_function_privilege('pipeline_writer', f, 'execute') then
      v_fail := v_fail || format('pipeline_writer has no EXECUTE on trigger function %s', f);
    end if;
  end loop;

  foreach r in array temp_no loop
    if has_database_privilege(r, current_database(), 'TEMP') then
      v_fail := v_fail || format('%s can still create temp objects', r);
    end if;
  end loop;
  foreach r in array temp_yes loop
    if not has_database_privilege(r, current_database(), 'TEMP') then
      v_fail := v_fail || format('%s lost TEMP', r);
    end if;
  end loop;
  foreach r in array array['anon', 'authenticated', 'authenticator', 'supabase_read_only_user', 'service_role'] loop
    if not has_database_privilege(r, current_database(), 'CONNECT') then
      v_fail := v_fail || format('%s lost CONNECT', r);
    end if;
  end loop;

  -- keep list
  foreach r in array array['anon', 'authenticated'] loop
    if not (has_table_privilege(r, 'signal_read.v_topic_movement', 'SELECT')
            and has_table_privilege(r, 'signal_read.v_topic_intersections', 'SELECT')
            and has_schema_privilege(r, 'signal_read', 'USAGE') and has_schema_privilege(r, 'public', 'USAGE')) then
      v_fail := v_fail || format('%s lost a keep-list privilege (signal_read views or schema USAGE)', r);
    end if;
  end loop;

  if cardinality(v_fail) > 0 then
    raise exception '0030 postflight FAILED (rolled back): %', array_to_string(v_fail, '; ');
  end if;
  raise notice '0030 postflight OK';
end
$post$;

commit;
