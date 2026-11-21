-- =============================================================================
-- 0028 · signal_read views run with their owner's rights; anon/authenticated lose direct base-table reads
-- Linear: YED-311. Decision: Alex, 2026-11-21, YED-311 option A.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   python3 supabase/scripts/rehearse_0028.py --execute
-- Before the paste, run staging/0028_verify.sql step 0 on prod (read-only) and keep the output: the view row counts
-- and md5s there must match step 0 again after the paste (the /signal payload must not change).
--
-- WHY:
--   0002 made signal_read.v_topic_movement and v_topic_intersections security_invoker = on. An invoker view runs as
--   the CALLER, so for anon to read it at all, 0002 had to give anon and authenticated SELECT plus a using (true)
--   RLS policy on the three base tables (topic_cluster, topic_trend, topic_pair_metric). That means the k>=5
--   small-cell suppression lives only in the views, and anyone with a SQL session as anon (or a future
--   exposed-schemas toggle on topic_intelligence) can read the unsuppressed base rows and skip it.
--   Option A (Alex, 2026-11-21): the view IS the suppression boundary, so make it the only door. The views run with
--   their owner's rights (security_invoker = off), and the direct base-table path is closed. The anon grants on the
--   two views are unchanged, so gtm-os-hub /signal (lib/sources/topic-intelligence.ts:178-188, anon key via
--   lib/supabase/spine.ts:19-23) gets the same rows.
--
--   Why owner rights still return every row: the view owner is `postgres`, which owns the three tables, has
--   BYPASSRLS, and none of the tables has FORCE ROW LEVEL SECURITY. The preflight asserts all of that.
--
-- WHAT (one transaction; idempotent: a second paste raises a NOTICE and changes nothing):
--   PART 1  preflight. Locks the 2 views and 3 tables, then raises unless the database is in exactly one of two
--           states: PRE (both views exist and are security_invoker = on; tc_anon_read, tt_anon_read and
--           tpm_anon_read all exist) or POST (already applied: NOTICE, then every later step is a guarded no-op).
--           In both states it also raises if:
--             a. the view owner could not read every row with owner rights (not the table owner without FORCE RLS,
--                and not BYPASSRLS);
--             b. any OTHER view or materialized view that reads the 3 tables is selectable by anon or
--                authenticated (it would lose rows, or it is a second unsuppressed door);
--             c. any non-security-definer function whose body names the 3 tables is executable by anon or
--                authenticated (it would break, since it runs as the caller).
--   PART 2  alter both views set (security_invoker = off) (only if currently on); drop the 3 policies (if exists);
--           revoke SELECT on the 3 tables from anon and authenticated (only where the ACL holds it).
--   PART 3  postflight: raises (rolling back everything) unless the end state holds: views owner-rights and still
--           granted to anon/authenticated; no anon policies; anon/authenticated hold no table- or column-level
--           SELECT on the 3 tables; service_role keeps SELECT; RLS still enabled on the 3 tables.
--
-- NOT CHANGED: service_role and postgres keep their table access. topic_intel_compute.py (nightly) connects as
--   postgres (MI_DB_DSN), does `set role pipeline_writer`, and calls the security-definer
--   topic_intelligence.compute_topic_intelligence() owned by postgres (0012); neither role is touched here.
--   USAGE on schema topic_intelligence for anon/authenticated is left as 0002 set it; with no table grants it reads
--   nothing (noted in the PR as an optional follow-up). RLS stays enabled on the 3 tables (deny-all for non-owners).
--
-- SUPABASE ADVISOR: after this, the advisor's `security_definer_view` lint will flag signal_read.v_topic_movement and
--   signal_read.v_topic_intersections. ACCEPTED, by design: the view is the suppression boundary, so it must run
--   with its owner's rights, and flipping it back to security_invoker would reopen the base-table path this
--   migration closes. Dismiss it in the dashboard with that reason. Same call, same reasoning, as the hub learning
--   plane's public.v_public_* views: docs/adr/evidence/plans/investigate-the-supabase-warnings-hidden-umbrella.md
--   (row 2 and the "views are the deliberate anon window" notes: "Do NOT flip to security_invoker"). Residual risk
--   carried with it: a future edit that adds a column to these views has no RLS backstop, so staging/0028_verify.sql
--   pins each view's exact column list.
--
-- LOCKS: ACCESS EXCLUSIVE on the 2 views and the 3 base tables, taken at the top of PART 1 so the checked state
--   cannot change before PART 2 (ALTER VIEW SET and DROP POLICY need that level anyway). /signal reads and the
--   nightly compute wait for milliseconds. lock_timeout = 5s, so the paste fails fast instead of queueing behind a
--   long query and blocking every reader behind it.
--
-- ROLLBACK (exact statements; rehearse_0028.py gate 5 runs this block verbatim from this header):
-- ROLLBACK-BEGIN
--   begin;
--   grant select on topic_intelligence.topic_cluster     to anon, authenticated;
--   grant select on topic_intelligence.topic_trend       to anon, authenticated;
--   grant select on topic_intelligence.topic_pair_metric to anon, authenticated;
--   create policy tc_anon_read on topic_intelligence.topic_cluster
--     for select to anon, authenticated using (true);
--   create policy tt_anon_read on topic_intelligence.topic_trend
--     for select to anon, authenticated using (true);
--   create policy tpm_anon_read on topic_intelligence.topic_pair_metric
--     for select to anon, authenticated using (true);
--   alter view signal_read.v_topic_movement      set (security_invoker = on);
--   alter view signal_read.v_topic_intersections set (security_invoker = on);
--   commit;
-- ROLLBACK-END
-- =============================================================================

begin;

set local lock_timeout = '5s';

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  v_tables   oid[];
  v_views    oid[];
  v_on       int;
  v_policies int;
  v_grants   int;
  v_bad      text;
begin
  if to_regclass('signal_read.v_topic_movement') is null or to_regclass('signal_read.v_topic_intersections') is null
     or to_regclass('topic_intelligence.topic_cluster') is null or to_regclass('topic_intelligence.topic_trend') is null
     or to_regclass('topic_intelligence.topic_pair_metric') is null then
    raise exception '0028 preflight: a signal_read view or a topic_intelligence base table is missing. Inspect by hand.';
  end if;
  v_views  := array['signal_read.v_topic_movement'::regclass::oid, 'signal_read.v_topic_intersections'::regclass::oid];
  v_tables := array['topic_intelligence.topic_cluster'::regclass::oid, 'topic_intelligence.topic_trend'::regclass::oid,
                    'topic_intelligence.topic_pair_metric'::regclass::oid];

  lock table signal_read.v_topic_movement, signal_read.v_topic_intersections,
             topic_intelligence.topic_cluster, topic_intelligence.topic_trend, topic_intelligence.topic_pair_metric
    in access exclusive mode;

  select count(*) into v_on from pg_class
   where oid = any (v_views) and 'security_invoker=on' = any (coalesce(reloptions, '{}'));
  select count(*) into v_policies from pg_policies
   where schemaname = 'topic_intelligence' and (tablename, policyname) in
         (('topic_cluster', 'tc_anon_read'), ('topic_trend', 'tt_anon_read'), ('topic_pair_metric', 'tpm_anon_read'));
  select count(*) into v_grants from pg_class c, aclexplode(c.relacl) a
   where c.oid = any (v_tables) and a.privilege_type = 'SELECT'
     and a.grantee in ('anon'::regrole, 'authenticated'::regrole);

  -- a. the view owner must see every row with its own rights
  select string_agg(v.oid::regclass::text || ' -> ' || t.oid::regclass::text, ', ') into v_bad
    from pg_class v join pg_roles r on r.oid = v.relowner cross join pg_class t
   where v.oid = any (v_views) and t.oid = any (v_tables)
     and not (has_table_privilege(v.relowner, t.oid, 'select')
              and (r.rolbypassrls or (t.relowner = v.relowner and not t.relforcerowsecurity)));
  if v_bad is not null then
    raise exception '0028 preflight: the view owner cannot read every base row with owner rights: %', v_bad;
  end if;

  -- b. no other anon/authenticated-readable view reads the 3 tables
  select string_agg(distinct c.oid::regclass::text, ', ') into v_bad
    from pg_depend d join pg_rewrite rw on rw.oid = d.objid join pg_class c on c.oid = rw.ev_class
   where d.classid = 'pg_rewrite'::regclass and d.refobjid = any (v_tables) and c.oid <> all (v_views)
     and c.oid <> d.refobjid and c.relkind in ('v', 'm')
     and (has_table_privilege('anon', c.oid, 'select') or has_table_privilege('authenticated', c.oid, 'select'));
  if v_bad is not null then
    raise exception '0028 preflight: other views readable by anon/authenticated read the base tables: %', v_bad;
  end if;

  -- c. no caller-rights function readable by anon/authenticated names the 3 tables (pg_depend cannot see bodies)
  select string_agg(p.oid::regprocedure::text, ', ') into v_bad
    from pg_proc p
   where not p.prosecdef
     and p.prosrc ~ 'topic_intelligence\.(topic_cluster|topic_trend|topic_pair_metric)\M'
     and (has_function_privilege('anon', p.oid, 'execute') or has_function_privilege('authenticated', p.oid, 'execute'));
  if v_bad is not null then
    raise exception '0028 preflight: caller-rights functions executable by anon/authenticated read the base tables: %', v_bad;
  end if;

  if v_on = 2 and v_policies = 3 then
    raise notice '0028 preflight OK: PRE state (views security_invoker = on, 3 anon policies, % anon/authenticated SELECT grants).', v_grants;
  elsif v_on = 0 and v_policies = 0 and v_grants = 0 then
    raise notice '0028: already applied (views owner-rights, no anon policies, no anon/authenticated SELECT); nothing to do.';
  else
    raise exception '0028 preflight: mixed state (security_invoker=on views %/2, anon policies %/3, anon/authenticated SELECT grants %). Inspect by hand.',
      v_on, v_policies, v_grants;
  end if;
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $apply$
declare
  r record;
begin
  for r in select c.oid::regclass as v from pg_class c
            where c.oid in ('signal_read.v_topic_movement'::regclass, 'signal_read.v_topic_intersections'::regclass)
              and 'security_invoker=on' = any (coalesce(c.reloptions, '{}')) loop
    execute format('alter view %s set (security_invoker = off)', r.v);
    raise notice '0028: % now runs with its owner''s rights', r.v;
  end loop;

  for r in select c.oid::regclass as t, a.grantee::regrole as g
             from pg_class c, aclexplode(c.relacl) a
            where c.oid in ('topic_intelligence.topic_cluster'::regclass, 'topic_intelligence.topic_trend'::regclass,
                            'topic_intelligence.topic_pair_metric'::regclass)
              and a.privilege_type = 'SELECT' and a.grantee in ('anon'::regrole, 'authenticated'::regrole) loop
    execute format('revoke select on %s from %s', r.t, r.g);
    raise notice '0028: revoked SELECT on % from %', r.t, r.g;
  end loop;
end
$apply$;

drop policy if exists tc_anon_read  on topic_intelligence.topic_cluster;
drop policy if exists tt_anon_read  on topic_intelligence.topic_trend;
drop policy if exists tpm_anon_read on topic_intelligence.topic_pair_metric;

-- PART 3 ---------------------------------------------------------------------------------------------------------
do $post$
declare
  v_fail text[] := '{}';
  t text;
  g text;
begin
  if exists (select 1 from pg_class where oid in ('signal_read.v_topic_movement'::regclass,
             'signal_read.v_topic_intersections'::regclass) and 'security_invoker=on' = any (coalesce(reloptions, '{}'))) then
    v_fail := v_fail || 'a view is still security_invoker = on'::text;
  end if;
  foreach t in array array['signal_read.v_topic_movement', 'signal_read.v_topic_intersections'] loop
    foreach g in array array['anon', 'authenticated'] loop
      if not has_table_privilege(g, t, 'select') then
        v_fail := v_fail || format('%s lost SELECT on %s', g, t);
      end if;
    end loop;
  end loop;
  if exists (select 1 from pg_policies where schemaname = 'topic_intelligence'
             and policyname in ('tc_anon_read', 'tt_anon_read', 'tpm_anon_read')) then
    v_fail := v_fail || 'an anon policy is still present'::text;
  end if;
  foreach t in array array['topic_intelligence.topic_cluster', 'topic_intelligence.topic_trend',
                           'topic_intelligence.topic_pair_metric'] loop
    foreach g in array array['anon', 'authenticated'] loop
      if has_any_column_privilege(g, t, 'select') then
        v_fail := v_fail || format('%s can still SELECT %s', g, t);
      end if;
    end loop;
    if not has_table_privilege('service_role', t, 'select') then
      v_fail := v_fail || format('service_role lost SELECT on %s', t);
    end if;
    if not (select relrowsecurity from pg_class where oid = t::regclass) then
      v_fail := v_fail || format('RLS is off on %s', t);
    end if;
  end loop;
  if cardinality(v_fail) > 0 then
    raise exception '0028 postflight FAILED (rolled back): %', array_to_string(v_fail, '; ');
  end if;
  raise notice '0028 postflight OK';
end
$post$;

commit;
