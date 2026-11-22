-- =============================================================================
-- 0029 · new objects created by postgres stop auto-granting anon/authenticated (default privileges)
-- Linear: YED-482 (supersedes the public half of YED-329). Scope approved by Alex 2026-11-21.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   python3 supabase/scripts/rehearse_0029.py --execute
-- Before AND after the paste, run staging/0029_verify.sql step 0 on prod (read-only) and keep both outputs.
-- After the paste, step 1 must show every row ok = t.
--
-- WHY:
--   pg_default_acl for role postgres in schema public (read-only on prod 2026-11-21) gives every NEW object to the
--   API roles automatically:
--     tables     anon=r, authenticated=r                 (0019 trimmed this from ALL to SELECT but kept it)
--     sequences  anon=rwU, authenticated=rwU             (SELECT, UPDATE = setval, USAGE = nextval)
--     functions  anon=X, authenticated=X                 (EXECUTE)
--   and postgres has NO global (namespace 0) function entry, so Postgres's built-in default also applies:
--   EXECUTE to PUBLIC on every new function, in every schema. anon and authenticated are members of PUBLIC.
--   Effect: a new public table is anon-readable the moment it is created unless RLS is enabled in the same
--   migration, and a new SECURITY DEFINER function anywhere in an exposed schema is anon-callable via
--   /rest/v1/rpc unless its migration revokes EXECUTE by hand (0016 and 0012 did; the next one may not). Same
--   pattern as YED-311. No live exposure today: that is what this migration keeps true for future objects.
--
--   Rehearsal finding that set the scope of PART 2: revoking anon/authenticated from the public schema entry ALONE
--   does not stop anon executing new functions. The twin probe created a function after that revoke and got
--   proacl {=X/postgres,postgres=X/postgres,service_role=X/postgres}, anon EXECUTE = true, via PUBLIC. So the
--   global PUBLIC revoke below is required, not optional.
--
-- WHAT (one transaction; idempotent: a second paste raises a NOTICE and changes nothing):
--   PART 1  preflight. Asserts the session can act FOR ROLE postgres, then raises unless postgres's default ACLs
--           are in exactly one of two states (compared as sorted grantee:privilege sets):
--             PRE   public tables/sequences/functions exactly as listed above (with postgres and service_role
--                   entries), no global function entry;
--             POST  the same with every anon/authenticated item gone, and a global function entry
--                   {postgres=X/postgres} (no PUBLIC). NOTICE, then every later step is a guarded no-op.
--           In both states it also raises if postgres has a default ACL in any schema other than public and
--           storage, or any global entry other than functions (unexpected: inspect by hand).
--   PART 2  only where the item is present: for role postgres in schema public, revoke all on tables, sequences
--           and functions from anon and authenticated; for role postgres globally, revoke execute on functions
--           from public.
--   PART 3  postflight: raises (rolling back everything) unless the exact POST state holds, service_role's and
--           postgres's own entries are unchanged, and storage's entries are unchanged. Then a behavioural check in
--           a subtransaction that is always undone: as postgres, create a table, a sequence, a SECURITY DEFINER
--           function in public and a function in mi; anon and authenticated must hold no privilege on any of them,
--           and service_role must hold full table rights, sequence rwU and function EXECUTE on the public ones.
--
-- SCOPE (read-only on prod 2026-11-21):
--   * Other pipeline schemas: postgres has NO default ACL in mi, signal_read or topic_intelligence. New tables,
--     views and sequences there get only the owner. Their only API-role exposure was the PUBLIC function default,
--     which the global revoke closes. (0003's "alter default privileges in schema topic_intelligence revoke execute
--     on functions from public" never had an effect: a schema entry can only add to the global default.)
--   * service_role defaults stay UNCHANGED: arwdDxtm on new public tables, rwU on sequences, X on functions. Spine
--     writes go through REST with the secret key (service_role; spine_client.py, gtm-os lib/spine.ts). The
--     postflight asserts service_role's entries byte-for-byte.
--   * Who writes, and why none of them depends on these defaults: roles on prod are postgres (login, BYPASSRLS),
--     service_role (BYPASSRLS), pipeline_writer (nologin; postgres is its member; topic_intel_compute.py does
--     `set role pipeline_writer` and calls topic_intelligence.compute_topic_intelligence(), granted to it by name
--     in 0012), anon and authenticated. pipeline_writer has no default ACL at all. The last-24h prod edge log has
--     /rest/v1/rpc calls only to entity_neighborhood, match_claims_hybrid and mi_slice, all EXECUTE =
--     postgres + service_role only, so those callers already use the secret key.
--   * Anon readers: gtm-os-hub reads prod as anon only via signal_read.v_topic_movement and v_topic_intersections
--     (lib/sources/topic-intelligence.ts) and public.v_public_spine_stats (lib/sources/spine.ts; missing on prod,
--     GTM-34). Those views exist already, and existing objects are untouched. TopicIntelHealthStrip reads with
--     MI_SUPABASE_SERVICE_ROLE_KEY. gtm-os has no anon-key read of prod. No RPC is called with the anon key.
--   * EXISTING objects are NOT changed. anon/authenticated still hold SELECT on 14 public tables (RLS on, no
--     policies, so 0 rows) and EXECUTE on 5 public functions; that inventory and a proposed "revoke existing
--     grants" follow-up are in the PR, not here.
--   * storage: postgres's storage defaults grant anon/authenticated ALL on tables, rwU on sequences and X on
--     functions, but postgres owns no object in storage (every relation is supabase_storage_admin's). Out of scope;
--     the postflight asserts it unchanged. (Note: the global function revoke also applies to any function postgres
--     ever creates in storage; the storage schema entry still grants anon/authenticated X there.)
--
-- SUPABASE_ADMIN LIMITATION (out of scope, documented, not failed on): pg_default_acl also holds entries for role
--   supabase_admin in public (anon=arwdDxtm on tables, rwU on sequences, X on functions) and in graphql /
--   graphql_public. ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin needs membership in supabase_admin;
--   pg_has_role('postgres', 'supabase_admin', 'member') = false on prod, and the twin rehearsal proves the
--   attempt fails with 42501. Those entries apply only to objects supabase_admin creates (platform and extension
--   objects, e.g. pgvector functions). Every non-extension object in public is postgres-owned. Supabase owns that
--   role; this migration leaves it alone.
--
-- RULE FOR EVERY FUTURE MIGRATION (after this is applied): a new object is reachable only by its owner (postgres)
--   and, in public, service_role. Whatever else needs access must be GRANTed explicitly in the same migration:
--     grant select on <new public view>                to anon, authenticated;   -- only a deliberate anon window
--     grant execute on function <schema>.<fn>(<args>)   to service_role;          -- in mi / topic_intelligence /
--                                                                                 -- signal_read: no default at all
--     grant execute on function <fn>(<args>)            to pipeline_writer;       -- as 0012 already does
--   A function used inside an anon-readable view also needs EXECUTE for the caller (functions in views are checked
--   as the querying role, not the view owner).
--
-- LOCKS: none on user tables. ALTER DEFAULT PRIVILEGES touches only pg_default_acl. lock_timeout = 5s anyway.
--
-- ROLLBACK (exact statements; rehearse_0029.py gate 5 runs this block verbatim from this header). Granting EXECUTE
--   back to PUBLIC returns the global entry to the built-in default, so Postgres deletes the row:
-- ROLLBACK-BEGIN
--   begin;
--   alter default privileges for role postgres grant execute on functions to public;
--   alter default privileges for role postgres in schema public grant select on tables to anon, authenticated;
--   alter default privileges for role postgres in schema public grant select, update, usage on sequences to anon, authenticated;
--   alter default privileges for role postgres in schema public grant execute on functions to anon, authenticated;
--   commit;
-- ROLLBACK-END
-- =============================================================================

begin;

set local lock_timeout = '5s';

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  -- canonical form: sorted "grantee:PRIVILEGE" items (PUBLIC for grantee 0, '*' when grantable)
  c_pg_r  constant text := 'postgres:DELETE,postgres:INSERT,postgres:MAINTAIN,postgres:REFERENCES,postgres:SELECT,'
                           'postgres:TRIGGER,postgres:TRUNCATE,postgres:UPDATE';
  c_sr_r  constant text := 'service_role:DELETE,service_role:INSERT,service_role:MAINTAIN,service_role:REFERENCES,'
                           'service_role:SELECT,service_role:TRIGGER,service_role:TRUNCATE,service_role:UPDATE';
  pre_r   text;
  pre_s   constant text := 'anon:SELECT,anon:UPDATE,anon:USAGE,authenticated:SELECT,authenticated:UPDATE,'
                           'authenticated:USAGE,postgres:SELECT,postgres:UPDATE,postgres:USAGE,'
                           'service_role:SELECT,service_role:UPDATE,service_role:USAGE';
  pre_f   constant text := 'anon:EXECUTE,authenticated:EXECUTE,postgres:EXECUTE,service_role:EXECUTE';
  post_r  text;
  post_s  constant text := 'postgres:SELECT,postgres:UPDATE,postgres:USAGE,service_role:SELECT,service_role:UPDATE,'
                           'service_role:USAGE';
  post_f  constant text := 'postgres:EXECUTE,service_role:EXECUTE';
  post_gf constant text := 'postgres:EXECUTE';
  v_r text; v_s text; v_f text; v_gf text; v_bad text;
begin
  pre_r  := 'anon:SELECT,authenticated:SELECT,' || c_pg_r || ',' || c_sr_r;
  post_r := c_pg_r || ',' || c_sr_r;

  if not pg_has_role(current_user, 'postgres', 'member') then
    raise exception '0029 preflight: % cannot act FOR ROLE postgres (not a member). Paste as postgres.', current_user;
  end if;

  select (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
            || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
            from aclexplode(d.defaclacl) a) s) into v_r
    from pg_default_acl d where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 'public'::regnamespace and d.defaclobjtype = 'r';
  select (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
            || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
            from aclexplode(d.defaclacl) a) s) into v_s
    from pg_default_acl d where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 'public'::regnamespace and d.defaclobjtype = 'S';
  select (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
            || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
            from aclexplode(d.defaclacl) a) s) into v_f
    from pg_default_acl d where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 'public'::regnamespace and d.defaclobjtype = 'f';
  select (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
            || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
            from aclexplode(d.defaclacl) a) s) into v_gf
    from pg_default_acl d where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 0 and d.defaclobjtype = 'f';

  -- unexpected postgres entries: any schema other than public/storage, any global entry other than functions
  select string_agg(case d.defaclnamespace when 0 then '(global)' else d.defaclnamespace::regnamespace::text end
                    || ':' || d.defaclobjtype::text || '=' || d.defaclacl::text, '; ') into v_bad
    from pg_default_acl d
   where d.defaclrole = 'postgres'::regrole
     and ((d.defaclnamespace = 0 and d.defaclobjtype <> 'f')
          or (d.defaclnamespace <> 0 and d.defaclnamespace not in ('public'::regnamespace, 'storage'::regnamespace)));
  if v_bad is not null then
    raise exception '0029 preflight: unexpected postgres default ACLs (inspect by hand): %', v_bad;
  end if;

  if v_r is not distinct from pre_r and v_s is not distinct from pre_s and v_f is not distinct from pre_f and v_gf is null then
    raise notice '0029 preflight OK: PRE state (public tables anon/authenticated SELECT, sequences rwU, functions X; no global function entry, so new functions get PUBLIC EXECUTE).';
  elsif v_r is not distinct from post_r and v_s is not distinct from post_s and v_f is not distinct from post_f
        and v_gf is not distinct from post_gf then
    raise notice '0029: already applied (no anon/authenticated in postgres''s public defaults; global functions = postgres only); nothing to do.';
  else
    raise exception '0029 preflight: mixed or unexpected state. public tables=[%] sequences=[%] functions=[%] global functions=[%]. Inspect by hand.',
      v_r, v_s, v_f, coalesce(v_gf, '<none: built-in PUBLIC EXECUTE>');
  end if;
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $apply$
declare
  r record;
begin
  for r in select d.defaclobjtype::text as t from pg_default_acl d
            where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 'public'::regnamespace
              and d.defaclobjtype in ('r', 'S', 'f')
              and exists (select 1 from aclexplode(d.defaclacl) a
                          where a.grantee in ('anon'::regrole, 'authenticated'::regrole))
            order by 1 loop
    execute format('alter default privileges for role postgres in schema public revoke all on %s from anon, authenticated',
                   case r.t when 'r' then 'tables' when 'S' then 'sequences' else 'functions' end);
    raise notice '0029: postgres/public % no longer auto-granted to anon, authenticated',
                 case r.t when 'r' then 'tables' when 'S' then 'sequences' else 'functions' end;
  end loop;

  if not exists (select 1 from pg_default_acl d
                  where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 0 and d.defaclobjtype = 'f')
     or exists (select 1 from pg_default_acl d, aclexplode(d.defaclacl) a
                 where d.defaclrole = 'postgres'::regrole and d.defaclnamespace = 0 and d.defaclobjtype = 'f'
                   and a.grantee = 0) then
    alter default privileges for role postgres revoke execute on functions from public;
    raise notice '0029: new postgres functions (every schema) no longer get EXECUTE for PUBLIC';
  end if;
end
$apply$;

-- PART 3 ---------------------------------------------------------------------------------------------------------
do $post$
declare
  v_fail text[] := '{}';
  k text; want text; got text;
  v_ok boolean;
  probe_done constant text := '0029-postflight-probe-undo';
begin
  for k, want in select v.k, v.want from (values
      ('public:r', 'postgres:DELETE,postgres:INSERT,postgres:MAINTAIN,postgres:REFERENCES,postgres:SELECT,postgres:TRIGGER,'
                   'postgres:TRUNCATE,postgres:UPDATE,service_role:DELETE,service_role:INSERT,service_role:MAINTAIN,'
                   'service_role:REFERENCES,service_role:SELECT,service_role:TRIGGER,service_role:TRUNCATE,service_role:UPDATE'),
      ('public:S', 'postgres:SELECT,postgres:UPDATE,postgres:USAGE,service_role:SELECT,service_role:UPDATE,service_role:USAGE'),
      ('public:f', 'postgres:EXECUTE,service_role:EXECUTE'),
      ('(global):f', 'postgres:EXECUTE'),
      ('storage:r', 'anon:DELETE,anon:INSERT,anon:MAINTAIN,anon:REFERENCES,anon:SELECT,anon:TRIGGER,anon:TRUNCATE,anon:UPDATE,'
                    'authenticated:DELETE,authenticated:INSERT,authenticated:MAINTAIN,authenticated:REFERENCES,authenticated:SELECT,'
                    'authenticated:TRIGGER,authenticated:TRUNCATE,authenticated:UPDATE,postgres:DELETE,postgres:INSERT,'
                    'postgres:MAINTAIN,postgres:REFERENCES,postgres:SELECT,postgres:TRIGGER,postgres:TRUNCATE,postgres:UPDATE,'
                    'service_role:DELETE,service_role:INSERT,service_role:MAINTAIN,service_role:REFERENCES,service_role:SELECT,'
                    'service_role:TRIGGER,service_role:TRUNCATE,service_role:UPDATE'),
      ('storage:S', 'anon:SELECT,anon:UPDATE,anon:USAGE,authenticated:SELECT,authenticated:UPDATE,authenticated:USAGE,'
                    'postgres:SELECT,postgres:UPDATE,postgres:USAGE,service_role:SELECT,service_role:UPDATE,service_role:USAGE'),
      ('storage:f', 'anon:EXECUTE,authenticated:EXECUTE,postgres:EXECUTE,service_role:EXECUTE')
      ) v(k, want)
  loop
    select (select string_agg(e, ',' order by e collate "C") from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
              || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
              from aclexplode(d.defaclacl) a) s) into got
      from pg_default_acl d
     where d.defaclrole = 'postgres'::regrole
       and (case d.defaclnamespace when 0 then '(global)' else d.defaclnamespace::regnamespace::text end)
           || ':' || d.defaclobjtype::text = k;
    if got is distinct from want then
      v_fail := v_fail || format('%s is [%s], want [%s]', k, coalesce(got, '<no entry>'), want);
    end if;
  end loop;

  -- behaviour: create one of each as postgres, check, and always undo (the subtransaction is rolled back)
  begin
    create table public.zz_0029_probe_t (id int);
    create sequence public.zz_0029_probe_s;
    create function public.zz_0029_probe_f() returns int language sql security definer set search_path = '' as 'select 1';
    create function mi.zz_0029_probe_f() returns int language sql as 'select 1';
    foreach k in array array['anon', 'authenticated'] loop
      if has_table_privilege(k, 'public.zz_0029_probe_t', 'select,insert,update,delete,truncate,references,trigger') then
        v_fail := v_fail || format('%s holds a privilege on a new public table', k);
      end if;
      if has_sequence_privilege(k, 'public.zz_0029_probe_s', 'select,update,usage') then
        v_fail := v_fail || format('%s holds a privilege on a new public sequence', k);
      end if;
      if has_function_privilege(k, 'public.zz_0029_probe_f()', 'execute') then
        v_fail := v_fail || format('%s can execute a new public function', k);
      end if;
      if has_function_privilege(k, 'mi.zz_0029_probe_f()', 'execute') then
        v_fail := v_fail || format('%s can execute a new mi function', k);
      end if;
    end loop;
    v_ok := has_table_privilege('service_role', 'public.zz_0029_probe_t', 'select')
        and has_table_privilege('service_role', 'public.zz_0029_probe_t', 'insert')
        and has_table_privilege('service_role', 'public.zz_0029_probe_t', 'update')
        and has_table_privilege('service_role', 'public.zz_0029_probe_t', 'delete')
        and has_sequence_privilege('service_role', 'public.zz_0029_probe_s', 'usage')
        and has_sequence_privilege('service_role', 'public.zz_0029_probe_s', 'update')
        and has_function_privilege('service_role', 'public.zz_0029_probe_f()', 'execute');
    if not v_ok then
      v_fail := v_fail || 'service_role lost a default privilege on new public objects'::text;
    end if;
    raise exception using message = probe_done;
  exception when others then
    if sqlerrm <> probe_done then
      v_fail := v_fail || format('behaviour probe errored: %s', sqlerrm);
    end if;
  end;

  if cardinality(v_fail) > 0 then
    raise exception '0029 postflight FAILED (rolled back): %', array_to_string(v_fail, '; ');
  end if;
  raise notice '0029 postflight OK';
end
$post$;

commit;
