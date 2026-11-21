-- =============================================================================
-- 0028 · signal_read views run with their owner's rights; anon/authenticated lose direct base-table reads
-- Linear: YED-311. Decision: Alex, 2026-11-21, YED-311 option A.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   python3 supabase/scripts/rehearse_0028.py --execute
-- Before the paste, run staging/0028_verify.sql step 0 on prod (read-only) and keep the output: the view row counts
-- and md5s there must match step 0 again after the paste (the /signal payload must not change).
--
-- ORDER WITH 0027 (PR #403, supabase/migrations/0027_retire_pre2b.sql, not yet applied to prod):
--   staging/0027_verify.sql step 1 asserts the opposite end state for these objects (tc/tt/tpm_anon_read KEPT, anon
--   SELECT on the 3 base tables KEPT, both views security_invoker = on). So the prod order is fixed:
--     1. paste 0027                      2. run staging/0027_verify.sql step 1 (every row ok = t)
--     3. paste 0028 (this file)          4. run staging/0028_verify.sql step 1 (every row ok = t)
--   Running 0027 verify step 1 AFTER 0028 shows 3 false rows (ti_anon_policies_kept, anon_select_kept,
--   views_security_invoker): expected, not a regression. 0028 does not depend on 0027 (it touches no pre2b object),
--   so pasting 0028 first would also apply cleanly, but it would turn 0027's step 1 red and make that verify useless
--   as 0027's gate. Do not reorder.
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
--           tpm_anon_read all exist) or POST (views owner-rights, no anon policies, no anon/authenticated SELECT
--           on the 3 tables and no USAGE on topic_intelligence: NOTICE, then every later step is a guarded no-op).
--           In both states it also raises if:
--             a. the view owner could not read every row with owner rights (not the table owner without FORCE RLS,
--                and not BYPASSRLS);
--             b. any OTHER view or materialized view that reads a topic_intelligence relation is selectable by
--                anon or authenticated (it would lose rows, or it is a second unsuppressed door);
--             c. any non-security-definer function whose body names topic_intelligence is executable by anon or
--                authenticated (it would break, since it runs as the caller);
--             d. anon or authenticated hold any privilege on any OTHER object in topic_intelligence (relation or
--                column ACL, or EXECUTE on a function, PUBLIC default included): the USAGE revoke would break it.
--   PART 2  alter both views set (security_invoker = off) (only if currently on); drop the 3 policies (if exists);
--           revoke SELECT on the 3 tables from anon and authenticated (only where the ACL holds it); revoke
--           USAGE on schema topic_intelligence from anon and authenticated (only where the ACL holds it).
--   PART 3  postflight: raises (rolling back everything) unless the end state holds: views owner-rights and still
--           granted to anon/authenticated; anon/authenticated keep USAGE on signal_read and have none on
--           topic_intelligence; no anon policies; anon/authenticated hold no table- or column-level SELECT on the
--           3 tables; service_role keeps SELECT and schema USAGE; RLS still enabled on the 3 tables.
--
-- SCHEMA USAGE (second layer, included): PART 2 also revokes USAGE on schema topic_intelligence from anon and
--   authenticated. Safe because, read-only on prod 2026-11-21, the only privileges anon/authenticated hold on any
--   object in topic_intelligence are the SELECT grants on the 3 base tables this migration revokes anyway:
--   no other table/view/sequence ACL or column ACL names them (topic_intelligence_health and topics: postgres +
--   service_role only); the schema's 2 functions (compute_topic_intelligence, upsert_topic_trend) are SECURITY
--   DEFINER with EXECUTE for postgres + pipeline_writer only; no default ACL in the schema; no function outside the
--   schema names topic_intelligence; the only views outside the schema that read it are the 2 signal_read views
--   (owner rights after PART 2: relation privileges are checked as the view owner, and schema USAGE only at name
--   lookup, which happened when the view was created) and mi.theme_week / mi.theme_lead_lag (anon and
--   authenticated cannot select them). The preflight re-asserts all of that at paste time (checks b, c, d) and
--   refuses otherwise. Effect: if a future grant or policy on a topic_intelligence table slips in, anon still cannot
--   resolve the schema, and PostgREST (topic_intelligence is in the exposed schemas: the 11-21 probe read it)
--   answers 401 instead of rows. gtm-os-hub TopicIntelHealthStrip (reads topic_intelligence_health as anon) fails
--   with 42501 today (no SELECT); after this it still fails with 42501 (now on the schema), so nothing that works
--   today breaks. Re-granting is one line in the rollback block.
--
-- NOT CHANGED: service_role and postgres keep their table and schema access. topic_intel_compute.py (nightly)
--   connects as postgres (MI_DB_DSN), does `set role pipeline_writer`, and calls the security-definer
--   topic_intelligence.compute_topic_intelligence() owned by postgres (0012); neither role is touched here, and
--   pipeline_writer keeps USAGE on the schema. RLS stays enabled on the 3 tables (deny-all for non-owners).
--
-- FORCE RLS: read-only on prod 2026-11-21, relforcerowsecurity = false on all 3 base tables (and on every
--   topic_intelligence table), and the view owner postgres owns them and has BYPASSRLS (rolsuper = false). Either
--   fact alone exempts the owner from RLS, so the owner-rights views see every row with no policy. Choice: add NO
--   owner policy and do NOT force RLS. Forcing would add nothing (BYPASSRLS still wins) and, if postgres ever lost
--   BYPASSRLS, would silently empty the views and break the nightly security-definer compute that writes these
--   tables. Preflight check (a) refuses the paste unless the owner can read every row (table owner without FORCE
--   RLS, or BYPASSRLS), and staging/0028_verify.sql re-checks it.
--
-- SUPABASE ADVISOR: after this, the advisor's `security_definer_view` lint (level ERROR) will flag 2 objects:
--   signal_read.v_topic_movement and signal_read.v_topic_intersections (baseline 11-21: 0 such findings). ACCEPTED, by design: the view is the suppression boundary, so it must run
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
--   grant usage on schema topic_intelligence to anon, authenticated;
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
  v_usage    int;
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
  select count(*) into v_usage from pg_namespace n, aclexplode(n.nspacl) a
   where n.nspname = 'topic_intelligence' and a.privilege_type = 'USAGE'
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

  -- b. no other anon/authenticated-readable view reads any topic_intelligence relation
  select string_agg(distinct c.oid::regclass::text, ', ') into v_bad
    from pg_depend d join pg_rewrite rw on rw.oid = d.objid join pg_class c on c.oid = rw.ev_class
         join pg_class t on t.oid = d.refobjid
   where d.classid = 'pg_rewrite'::regclass and d.refclassid = 'pg_class'::regclass
     and t.relnamespace = 'topic_intelligence'::regnamespace and c.oid <> all (v_views)
     and c.oid <> d.refobjid and c.relkind in ('v', 'm')
     and (has_table_privilege('anon', c.oid, 'select') or has_table_privilege('authenticated', c.oid, 'select'));
  if v_bad is not null then
    raise exception '0028 preflight: other views readable by anon/authenticated read the base tables: %', v_bad;
  end if;

  -- c. no caller-rights function executable by anon/authenticated names topic_intelligence (pg_depend cannot see bodies)
  select string_agg(p.oid::regprocedure::text, ', ') into v_bad
    from pg_proc p
   where not p.prosecdef
     and p.prosrc ~ 'topic_intelligence\.'
     and (has_function_privilege('anon', p.oid, 'execute') or has_function_privilege('authenticated', p.oid, 'execute'));
  if v_bad is not null then
    raise exception '0028 preflight: caller-rights functions executable by anon/authenticated read topic_intelligence: %', v_bad;
  end if;

  -- d. apart from the 3 base-table SELECT grants revoked below, anon/authenticated hold nothing in topic_intelligence
  --    (else the schema USAGE revoke would break it)
  select string_agg(x, ', ') into v_bad from (
    select c.oid::regclass::text || ' (' || a.privilege_type || ' to ' || a.grantee::regrole::text || ')' as x
      from pg_class c, aclexplode(c.relacl) a
     where c.relnamespace = 'topic_intelligence'::regnamespace
       and a.grantee in ('anon'::regrole::oid, 'authenticated'::regrole::oid, 0::oid)
       and not (c.oid = any (v_tables) and a.privilege_type = 'SELECT' and a.grantee <> 0::oid)
    union all
    select c.oid::regclass::text || '.' || att.attname || ' (column ' || a.privilege_type || ')'
      from pg_class c join pg_attribute att on att.attrelid = c.oid, aclexplode(att.attacl) a
     where c.relnamespace = 'topic_intelligence'::regnamespace
       and a.grantee in ('anon'::regrole::oid, 'authenticated'::regrole::oid, 0::oid)
    union all
    select p.oid::regprocedure::text || ' (EXECUTE)'
      from pg_proc p
     where p.pronamespace = 'topic_intelligence'::regnamespace
       and (has_function_privilege('anon', p.oid, 'execute') or has_function_privilege('authenticated', p.oid, 'execute'))
  ) s;
  if v_bad is not null then
    raise exception '0028 preflight: anon/authenticated hold other privileges in topic_intelligence (the USAGE revoke would break them): %', v_bad;
  end if;

  if v_on = 2 and v_policies = 3 then
    raise notice '0028 preflight OK: PRE state (views security_invoker = on, 3 anon policies, % anon/authenticated SELECT grants, % anon/authenticated USAGE grants on topic_intelligence).', v_grants, v_usage;
  elsif v_on = 0 and v_policies = 0 and v_grants = 0 and v_usage = 0 then
    raise notice '0028: already applied (views owner-rights, no anon policies, no anon/authenticated SELECT or schema USAGE); nothing to do.';
  else
    raise exception '0028 preflight: mixed state (security_invoker=on views %/2, anon policies %/3, anon/authenticated SELECT grants %, topic_intelligence USAGE grants %). Inspect by hand.',
      v_on, v_policies, v_grants, v_usage;
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

  for r in select a.grantee::regrole as g from pg_namespace n, aclexplode(n.nspacl) a
            where n.nspname = 'topic_intelligence' and a.privilege_type = 'USAGE'
              and a.grantee in ('anon'::regrole, 'authenticated'::regrole) loop
    execute format('revoke usage on schema topic_intelligence from %s', r.g);
    raise notice '0028: revoked USAGE on schema topic_intelligence from %', r.g;
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
  foreach g in array array['anon', 'authenticated'] loop
    if has_schema_privilege(g, 'topic_intelligence', 'usage') then
      v_fail := v_fail || format('%s still has USAGE on topic_intelligence', g);
    end if;
    if not has_schema_privilege(g, 'signal_read', 'usage') then
      v_fail := v_fail || format('%s lost USAGE on signal_read', g);
    end if;
  end loop;
  if not has_schema_privilege('service_role', 'topic_intelligence', 'usage') then
    v_fail := v_fail || 'service_role lost USAGE on topic_intelligence'::text;
  end if;
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
