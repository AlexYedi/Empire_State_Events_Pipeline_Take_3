-- =============================================================================
-- 0031 · public.v_public_spine_stats: one row of 4 aggregate numbers for the gtm-os-hub system map, readable by anon
-- Linear: GTM-34. Depends on 0030 (YED-483, PR #422): the base tables are closed to anon, so this view is the only door.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   TWIN_PUBLISHABLE_KEY=sb_publishable_... python3 supabase/scripts/rehearse_0031.py --execute
-- Before AND after the paste, run staging/0031_verify.sql step 0 on prod (read-only) and keep both outputs.
-- After the paste, step 1 must show every row ok = t.
--
-- WHY:
--   gtm-os-hub (lib/sources/spine.ts) reads, with the prod publishable (anon) key:
--     .from('v_public_spine_stats').select('entity_count, event_count, signal_count, last_signal_at').maybeSingle()
--   The view does not exist on prod, so PostgREST answers 404 and the system-map node shows "instrumenting"
--   (edge logs: node GET /rest/v1/v_public_spine_stats -> 404, the 0030 live-use check). The 4 column names are the
--   contract; the hub needs no change.
--
-- WHAT ANON SEES: exactly one row, 4 numbers, nothing else.
--   entity_count   bigint       count(public.company) + count(public.person)
--   event_count    bigint       count(public.event)
--   signal_count   bigint       count(public.claim) where status = 'approved'
--   last_signal_at timestamptz  max(public.claim.created_at) where status = 'approved'
--   No id, name, text or per-row value. Every claim is visibility = 'private'; aggregate counts and one timestamp are
--   the only thing that leaves claim (decision: Alex, GTM-34). The view reads only claim.status and claim.created_at;
--   staging/0031_verify.sql pins the column list and the column dependencies.
--
-- OWNER RIGHTS (security_invoker = off, owner postgres): 0030 revoked every anon/authenticated privilege on company,
--   person, event and claim, and RLS is on with no policy for them. An invoker view would run as anon and fail
--   (42501), and with a grant it would still count 0 rows under RLS: a false zero. Same call as 0028 for the two
--   signal_read views: the view runs as postgres, which owns the 4 tables (none has FORCE ROW LEVEL SECURITY) and has
--   BYPASSRLS, so it counts every row. PART 1 refuses the paste unless that holds. security_barrier = on: the view
--   has no WHERE that a caller could leak past, so it changes nothing today; it keeps a caller's quals from being
--   pushed below the view if a future edit adds one.
--
-- GRANTS: 0029 stopped default privileges from granting anything to anon/authenticated, and postgres' default ACL in
--   public gives service_role arwdDxtm on a new relation. PART 2 resets the view to exactly:
--   postgres (owner, all), anon SELECT, authenticated SELECT, service_role SELECT. PUBLIC gets nothing.
--
-- SUPABASE ADVISOR: the `security_definer_view` lint (ERROR) will flag public.v_public_spine_stats, as it flags the
--   two signal_read views after 0028. ACCEPTED by design: owner rights are what make the counts real while the base
--   tables stay closed. Dismiss it in the dashboard with that reason.
--
-- WHAT (one transaction; idempotent: a second paste raises a NOTICE and changes nothing):
--   PART 1  preflight. Raises unless the session can act as postgres; anon, authenticated, service_role exist;
--           company, person, event, claim exist and claim has status text and created_at timestamptz; the 0030 state
--           holds (anon/authenticated hold no table or column privilege on the 4 tables); RLS is on for the 4 tables
--           and postgres can read every row with owner rights; and the view is in exactly one of two states:
--             PRE   public.v_public_spine_stats does not exist (no relation of that name)
--             POST  it exists with exactly the shape PART 2 builds (owner, options, columns, ACL, dependencies):
--                   NOTICE, then no-op.
--           Anything else (a relation of that name with another shape) raises: inspect by hand.
--   PART 2  only in PRE: create the view; reset its grants; comment; ask PostgREST to reload its schema cache.
--   PART 3  postflight: raises (rolling back everything) unless the view has the exact POST shape, returns exactly
--           one row equal to the direct aggregates, and anon/authenticated still hold nothing on the 4 tables.
--
-- LOCKS: CREATE VIEW takes AccessShareLock on the 4 tables only (no rewrite, readers and writers unaffected).
--   lock_timeout = 5s.
--
-- ROLLBACK (exact statements; rehearse_0031.py gate 5 runs this block verbatim from this header and proves the twin
--   returns to its pre-apply snapshot):
-- ROLLBACK-BEGIN
--   begin;
--   drop view if exists public.v_public_spine_stats;
--   select pg_notify('pgrst', 'reload schema');
--   commit;
-- ROLLBACK-END
-- =============================================================================

begin;

set local lock_timeout = '5s';

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  base constant text[] := array['public.company', 'public.person', 'public.event', 'public.claim'];
  want_cols constant text := 'entity_count:bigint,event_count:bigint,signal_count:bigint,last_signal_at:timestamp with time zone';
  want_acl  constant text := 'anon:SELECT,authenticated:SELECT,postgres:DELETE,postgres:INSERT,postgres:MAINTAIN,'
                             'postgres:REFERENCES,postgres:SELECT,postgres:TRIGGER,postgres:TRUNCATE,postgres:UPDATE,'
                             'service_role:SELECT';
  want_deps constant text := 'public.claim.created_at,public.claim.status,public.company,public.event,public.person';
  v_missing text; v_bad text; v_oid oid; got text;
begin
  if not pg_has_role(current_user, 'postgres', 'member') then
    raise exception '0031 preflight: % cannot act as postgres (not a member). Paste as postgres.', current_user;
  end if;
  select string_agg(r, ',') into v_missing from unnest(array['anon', 'authenticated', 'service_role']) r
   where not exists (select 1 from pg_roles where rolname = r);
  if v_missing is not null then
    raise exception '0031 preflight: expected roles missing: %. Inspect by hand.', v_missing;
  end if;
  select string_agg(t, ',') into v_missing from unnest(base) t where to_regclass(t) is null;
  if v_missing is not null then
    raise exception '0031 preflight: base tables missing: %. Inspect by hand.', v_missing;
  end if;
  if (select string_agg(attname || ':' || format_type(atttypid, atttypmod), ',' order by attname)
        from pg_attribute where attrelid = 'public.claim'::regclass and attname in ('status', 'created_at')
         and not attisdropped) is distinct from 'created_at:timestamp with time zone,status:text' then
    raise exception '0031 preflight: public.claim has no status text / created_at timestamptz pair. Inspect by hand.';
  end if;

  -- the 0030 state: anon/authenticated hold nothing on the 4 tables (table or column level)
  select string_agg(r || ' on ' || t, '; ') into v_bad
    from unnest(base) t, unnest(array['anon', 'authenticated']) r
   where has_table_privilege(r, t, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
      or has_any_column_privilege(r, t, 'SELECT,INSERT,UPDATE,REFERENCES');
  if v_bad is not null then
    raise exception '0031 preflight: the 0030 state does not hold (anon/authenticated privilege: %). Apply 0030 first.', v_bad;
  end if;

  -- RLS on, and postgres reads every row with owner rights (0028 check a)
  select string_agg(c.oid::regclass::text, ',') into v_bad
    from pg_class c cross join pg_roles r
   where c.oid = any (array(select to_regclass(t)::oid from unnest(base) t)) and r.rolname = 'postgres'
     and (not c.relrowsecurity
          or not (has_table_privilege('postgres', c.oid, 'SELECT')
                  and (r.rolbypassrls or (c.relowner = r.oid and not c.relforcerowsecurity))));
  if v_bad is not null then
    raise exception '0031 preflight: RLS off, or postgres cannot read every row with owner rights, on: %. Inspect by hand.', v_bad;
  end if;

  v_oid := to_regclass('public.v_public_spine_stats');
  if v_oid is null then
    perform set_config('mig0031.state', 'pre', true);
    raise notice '0031 preflight OK: PRE state (view absent; 0030 state holds on company, person, event, claim; owner postgres reads every row).';
    return;
  end if;

  select concat_ws(' | ',
           'kind=' || c.relkind::text,
           'owner=' || c.relowner::regrole::text,
           'opts=' || coalesce((select string_agg(o, ',' order by o collate "C") from unnest(c.reloptions) o), ''),
           'cols=' || (select string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' order by a.attnum)
                         from pg_attribute a where a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped),
           'acl=' || coalesce((select string_agg(e, ',' order by e collate "C")
                                 from (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
                                              || ':' || a.privilege_type || case when a.is_grantable then '*' else '' end as e
                                         from aclexplode(c.relacl) a) s), ''),
           'deps=' || (select string_agg(dep, ',' order by dep collate "C")
                         from (select distinct rn.nspname || '.' || rc.relname
                                      || coalesce('.' || ra.attname, '') as dep
                                 from pg_rewrite rw
                                 join pg_depend d on d.classid = 'pg_rewrite'::regclass and d.objid = rw.oid
                                 join pg_class rc on rc.oid = d.refobjid
                                 join pg_namespace rn on rn.oid = rc.relnamespace
                                 left join pg_attribute ra on ra.attrelid = d.refobjid and ra.attnum = d.refobjsubid
                                                          and d.refobjsubid > 0
                                where rw.ev_class = c.oid and d.refclassid = 'pg_class'::regclass
                                  and d.refobjid <> c.oid) s))
    into got from pg_class c where c.oid = v_oid;

  if got = concat_ws(' | ', 'kind=v', 'owner=postgres', 'opts=security_barrier=true,security_invoker=off',
                     'cols=' || want_cols, 'acl=' || want_acl, 'deps=' || want_deps) then
    perform set_config('mig0031.state', 'post', true);
    raise notice '0031: already applied (public.v_public_spine_stats exists with the exact shape); nothing to do.';
  else
    raise exception E'0031 preflight: public.v_public_spine_stats exists with an unexpected shape. Inspect by hand.\n got [%]', got;
  end if;
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $apply$
begin
  if current_setting('mig0031.state', true) is distinct from 'pre' then
    return;
  end if;

  create view public.v_public_spine_stats with (security_invoker = off, security_barrier = true) as
  select ((select count(*) from public.company) + (select count(*) from public.person))::bigint as entity_count,
         (select count(*) from public.event)::bigint                                             as event_count,
         (select count(*) from public.claim c where c.status = 'approved')::bigint              as signal_count,
         (select max(c.created_at) from public.claim c where c.status = 'approved')             as last_signal_at;

  revoke all on public.v_public_spine_stats from public, anon, authenticated, service_role;
  grant select on public.v_public_spine_stats to anon, authenticated, service_role;

  comment on view public.v_public_spine_stats is
    'GTM-34 / 0031: one row of 4 aggregate numbers for the gtm-os-hub system map (anon-readable). Owner rights '
    '(security_invoker = off) by design: the base tables are closed to anon (0030). Aggregates only: never add an id, '
    'name, text or per-row column.';

  perform pg_notify('pgrst', 'reload schema');
  raise notice '0031: public.v_public_spine_stats created (owner rights, security_barrier); SELECT to anon, authenticated, service_role only';
end
$apply$;

-- PART 3 ---------------------------------------------------------------------------------------------------------
do $post$
declare
  base constant text[] := array['public.company', 'public.person', 'public.event', 'public.claim'];
  v_fail text[] := '{}';
  v_rows int; v_match boolean; r text; got text;
begin
  if to_regclass('public.v_public_spine_stats') is null then
    raise exception '0031 postflight FAILED (rolled back): public.v_public_spine_stats does not exist';
  end if;

  select c.relowner::regrole::text into got from pg_class c where c.oid = 'public.v_public_spine_stats'::regclass;
  if got is distinct from 'postgres' then
    v_fail := v_fail || format('owner is %s, want postgres', got);
  end if;
  if not exists (select 1 from pg_class c where c.oid = 'public.v_public_spine_stats'::regclass and c.relkind = 'v'
                    and 'security_invoker=off' = any (c.reloptions) and 'security_barrier=true' = any (c.reloptions)) then
    v_fail := v_fail || 'view is not relkind v with security_invoker=off, security_barrier=true'::text;
  end if;
  select string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' order by a.attnum) into got
    from pg_attribute a where a.attrelid = 'public.v_public_spine_stats'::regclass and a.attnum > 0 and not a.attisdropped;
  if got is distinct from 'entity_count:bigint,event_count:bigint,signal_count:bigint,last_signal_at:timestamp with time zone' then
    v_fail := v_fail || format('columns are [%s]', got);
  end if;

  foreach r in array array['anon', 'authenticated', 'service_role'] loop
    if not has_table_privilege(r, 'public.v_public_spine_stats', 'SELECT')
       or has_table_privilege(r, 'public.v_public_spine_stats', 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN') then
      v_fail := v_fail || format('%s does not hold exactly SELECT on the view', r);
    end if;
  end loop;
  if exists (select 1 from pg_class c, aclexplode(c.relacl) a
              where c.oid = 'public.v_public_spine_stats'::regclass and a.grantee = 0) then
    v_fail := v_fail || 'PUBLIC holds a privilege on the view'::text;
  end if;

  foreach r in array base loop
    if has_table_privilege('anon', r, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
       or has_table_privilege('authenticated', r, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN') then
      v_fail := v_fail || format('anon/authenticated hold a privilege on %s (0030 state broken)', r);
    end if;
  end loop;

  select count(*) into v_rows from public.v_public_spine_stats;
  select v.entity_count = (select count(*) from public.company) + (select count(*) from public.person)
     and v.event_count = (select count(*) from public.event)
     and v.signal_count = (select count(*) from public.claim where status = 'approved')
     and v.last_signal_at is not distinct from (select max(created_at) from public.claim where status = 'approved')
    into v_match from public.v_public_spine_stats v;
  if v_rows <> 1 or not coalesce(v_match, false) then
    v_fail := v_fail || format('view returns %s rows, aggregates match: %s', v_rows, coalesce(v_match::text, 'null'));
  end if;

  if cardinality(v_fail) > 0 then
    raise exception '0031 postflight FAILED (rolled back): %', array_to_string(v_fail, '; ');
  end if;
  raise notice '0031 postflight OK';
end
$post$;

commit;
