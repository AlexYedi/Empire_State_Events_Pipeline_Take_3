-- =============================================================================
-- 0027 · retire schema pre2b (the parked pre-cutover originals) and drop its one external FK
-- Linear: YED-298 (retire pre2b) · YED-311 (anon base-table reads on topic_intelligence): HELD, see PART 3.
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   python3 supabase/scripts/rehearse_0027.py --execute
--
-- PREREQUISITE: cold export done. `pre2b` holds person rows (name, bio, linkedin_url), so the export is NOT in git.
--   It is a pg_dump of schema pre2b taken FROM THE TWIN (Phantom-Test-Case, a clone of prod). The twin's pre2b is
--   the same August cutover snapshot as prod's: nothing has written to pre2b since the 2b swap
--   (staging/2b_swap.sql), and prod's last read was 2026-11-04.
--   Default path: /private/tmp/claude-501/pre2b_export/pre2b_export.sql (mode 600), written by
--   `rehearse_0027.py --execute`. Copy it somewhere durable (R2 esep-library, private) before the prod apply.
--   Before pasting this into prod, run staging/0027_verify.sql step 0 on prod (read-only). Its exact row counts and
--   per-table md5 must equal the twin's, which rehearse_0027.py prints at gate 0. If they match, the twin export
--   restores prod byte-for-byte. If they differ, stop: take the export from prod instead.
--
-- WHY:
--   * YED-298: `pre2b` is the 2b swap's parking lot: 9 tables, about 1.2 MB, kept so 2b_rollback.sql could undo the
--     swap. The swap has been live since August and 2b's nightly healthcheck has passed since. Nothing reads pre2b:
--     no views, functions or cron jobs; anon and authenticated have no USAGE. It still carries 232 person rows
--     with bios outside every later PII control, which is the main reason to remove it rather than leave it.
--   * The one thing outside pre2b that points in: FK topic_intelligence.topics.topics_cluster_id_fkey ->
--     pre2b.topic_cluster. `topics` is a frozen August snapshot (170 rows, never updated, nothing reads it).
--     Decision: drop that constraint only and keep the table and its rows.
--
-- WHAT (one transaction; idempotent: a second paste raises nothing and changes nothing):
--   PART 1  preflight. Raises unless pre2b is exactly as expected, or already gone (then NOTICE and no-op):
--           a. pre2b contains exactly the 9 tables below, plus only indexes and sequences (no views, functions,
--              types or other relations);
--           b. walking pg_depend from the schema, every object a CASCADE would drop belongs to pre2b (its tables'
--              indexes, sequences, row types, constraints, triggers, defaults, policies, toast). The only outside
--              object allowed is topics_cluster_id_fkey (plus its RI triggers on topics), which PART 2 drops first;
--           c. no function outside pre2b names `pre2b.` in its body (pg_depend cannot see plpgsql bodies), and no
--              pg_cron job mentions pre2b.
--   PART 2  drop topics_cluster_id_fkey (guarded), re-check that nothing outside pre2b depends on it, then
--           `drop schema pre2b cascade`.
--   PART 3  YED-311 (drop tc/tt/tpm_anon_read on topic_intelligence; revoke anon/authenticated SELECT): NOT IN
--           THIS MIGRATION. gtm-os-hub's /signal page reads prod's signal_read.v_topic_movement and
--           v_topic_intersections with the anon key (gtm-os-hub lib/supabase/spine.ts:19-23,
--           lib/sources/topic-intelligence.ts:178-188). Those views are security_invoker = on (0002), so they
--           run as anon and NEED those policies and grants. Revoking them would blank /signal. That fork goes to
--           Alex. topic_intelligence is not in exposed-schemas, so there is no direct REST path to the base tables
--           today; the k>=5 bypass needs that toggle or a SQL session as anon.
--
-- LOCKS: ACCESS EXCLUSIVE on the 9 pre2b tables and on topic_intelligence.topics, taken at the top of PART 1 so no
--   session can add a dependent object between the check and the drop. Nothing reads these tables, so the locks
--   last milliseconds. Live tables (public.*, topic_intelligence.topic_cluster/trend/pair_metric) are not locked.
--
-- ROLLBACK (rehearsed by rehearse_0027.py gate 5):
--   1. psql -X -v ON_ERROR_STOP=1 -1 -f <export>       -- recreates schema pre2b: tables, rows, indexes,
--                                                         constraints, RLS, its 3 policies, grants
--   2. alter table topic_intelligence.topics
--        add constraint topics_cluster_id_fkey foreign key (cluster_id) references pre2b.topic_cluster(cluster_id);
--   Snapshot C must equal snapshot A (schema fingerprint + per-table row md5), 0025/0026 objects included.
-- =============================================================================

begin;

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  v_ns       oid := to_regnamespace('pre2b');
  v_expected text[] := array['company', 'event', 'event_entity', 'ingestion_run', 'person', 'topic',
                             'topic_cluster', 'topic_pair_metric', 'topic_trend'];
  v_tables   text[];
  v_kinds    text;
  v_fk       oid;
  v_outside  text;
  v_text     text;
  v_cron     int := 0;
  r          text;
begin
  if v_ns is null then
    if exists (select 1 from pg_constraint where conname = 'topics_cluster_id_fkey'
               and conrelid = to_regclass('topic_intelligence.topics')) then
      raise exception '0027 preflight: pre2b is gone but topics_cluster_id_fkey still exists. Inspect by hand.';
    end if;
    raise notice '0027: pre2b already retired; nothing to do.';
    return;
  end if;

  -- lock first, so the dependency set cannot change before PART 2 drops it
  foreach r in array v_expected loop
    if to_regclass('pre2b.' || r) is not null then
      execute format('lock table pre2b.%I in access exclusive mode', r);
    end if;
  end loop;
  if to_regclass('topic_intelligence.topics') is not null then
    lock table topic_intelligence.topics in access exclusive mode;
  end if;

  -- a. exactly the 9 tables; only tables, indexes and sequences
  select array_agg(relname::text order by relname) into v_tables
    from pg_class where relnamespace = v_ns and relkind in ('r', 'p');
  if v_tables is distinct from v_expected then
    raise exception '0027 preflight: pre2b tables are %, expected %', v_tables, v_expected;
  end if;
  select string_agg(distinct relkind::text, ',') into v_kinds
    from pg_class where relnamespace = v_ns and relkind not in ('r', 'i', 'S');
  if v_kinds is not null then
    raise exception '0027 preflight: pre2b holds relations of kind % (views/matviews/foreign/etc.)', v_kinds;
  end if;
  if exists (select 1 from pg_proc where pronamespace = v_ns) then
    raise exception '0027 preflight: pre2b contains functions';
  end if;

  -- b. everything CASCADE would drop is inside pre2b, except the one known FK (and its RI triggers on topics)
  select oid into v_fk from pg_constraint
   where conname = 'topics_cluster_id_fkey' and conrelid = to_regclass('topic_intelligence.topics')
     and confrelid = to_regclass('pre2b.topic_cluster');
  if v_fk is null then
    raise exception '0027 preflight: FK topic_intelligence.topics.topics_cluster_id_fkey -> pre2b.topic_cluster not found';
  end if;

  with recursive dep(classid, objid) as (
    select d.classid, d.objid from pg_depend d
     where d.refclassid = 'pg_namespace'::regclass and d.refobjid = v_ns and d.deptype in ('n', 'a', 'i')
    union
    select d.classid, d.objid from pg_depend d
      join dep on d.refclassid = dep.classid and d.refobjid = dep.objid
     where d.deptype in ('n', 'a', 'i')
  ), owned as (
    select dep.classid, dep.objid,
      case dep.classid
        when 'pg_class'::regclass then (
          select case when c.relnamespace = 'pg_toast'::regnamespace
                      then (select o.relnamespace from pg_class o
                             where o.reltoastrelid = c.oid
                                or o.reltoastrelid = (select i.indrelid from pg_index i where i.indexrelid = c.oid))
                      else c.relnamespace end
            from pg_class c where c.oid = dep.objid)
        when 'pg_type'::regclass       then (select typnamespace from pg_type where oid = dep.objid)
        when 'pg_constraint'::regclass then (select connamespace from pg_constraint where oid = dep.objid)
        when 'pg_trigger'::regclass    then (select c.relnamespace from pg_trigger t join pg_class c on c.oid = t.tgrelid
                                              where t.oid = dep.objid)
        when 'pg_policy'::regclass     then (select c.relnamespace from pg_policy p join pg_class c on c.oid = p.polrelid
                                              where p.oid = dep.objid)
        when 'pg_attrdef'::regclass    then (select c.relnamespace from pg_attrdef a join pg_class c on c.oid = a.adrelid
                                              where a.oid = dep.objid)
        when 'pg_rewrite'::regclass    then (select c.relnamespace from pg_rewrite w join pg_class c on c.oid = w.ev_class
                                              where w.oid = dep.objid)
        when 'pg_proc'::regclass       then (select pronamespace from pg_proc where oid = dep.objid)
      end as ns
    from dep
  )
  select string_agg(pg_describe_object(classid, objid, 0), '; ') into v_outside
    from owned
   where ns is distinct from v_ns
     and not (classid = 'pg_constraint'::regclass and objid = v_fk)
     and not (classid = 'pg_trigger'::regclass
              and objid in (select oid from pg_trigger where tgconstraint = v_fk));
  if v_outside is not null then
    raise exception '0027 preflight: CASCADE would drop objects outside pre2b: %', v_outside;
  end if;

  -- c. text references pg_depend cannot see
  select string_agg(p.oid::regprocedure::text, ', ') into v_text
    from pg_proc p
   where p.pronamespace <> v_ns and p.prosrc ~* '\mpre2b\.'
     and p.pronamespace not in ('pg_catalog'::regnamespace, 'information_schema'::regnamespace);
  if v_text is not null then
    raise exception '0027 preflight: functions outside pre2b reference it by name: %', v_text;
  end if;
  if to_regclass('cron.job') is not null then
    execute $q$select count(*) from cron.job where command ~* 'pre2b'$q$ into v_cron;
    if v_cron > 0 then
      raise exception '0027 preflight: % pg_cron job(s) mention pre2b', v_cron;
    end if;
  end if;

  raise notice '0027 preflight OK: 9 tables, cascade set inside pre2b, one external FK (topic_intelligence.topics.topics_cluster_id_fkey).';
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $drop$
begin
  if to_regnamespace('pre2b') is null then
    return;
  end if;
  if exists (select 1 from pg_constraint where conname = 'topics_cluster_id_fkey'
             and conrelid = to_regclass('topic_intelligence.topics')) then
    alter table topic_intelligence.topics drop constraint topics_cluster_id_fkey;
  end if;
  -- belt and braces: after the FK drop, no constraint outside pre2b may reference a pre2b relation
  if exists (select 1 from pg_constraint
              where connamespace <> 'pre2b'::regnamespace
                and confrelid in (select oid from pg_class where relnamespace = 'pre2b'::regnamespace)) then
    raise exception '0027: a constraint outside pre2b still references it after the FK drop';
  end if;
  drop schema pre2b cascade;
  raise notice '0027: schema pre2b dropped; topics_cluster_id_fkey dropped; topic_intelligence.topics kept.';
end
$drop$;

-- PART 3 (YED-311): held. See header. Nothing here touches topic_intelligence policies or grants.

commit;
