-- 0012 — Live topic-intelligence compute (YED-230 / YED-131): port 0008 to the post-swap schemas
-- Linear: YED-230 (nightly health-check red since 09-19), YED-131 (wire the live nightly recompute)
--
-- WHY: the 2b cutover (2026-08-10) moved canonical_v2.{event,event_entity,topic} -> public and
--   canonical_v2.{topic_trend,topic_pair_metric,ingestion_run} -> topic_intelligence, but the only
--   compute function stayed behind as canonical_v2.compute_topic_intelligence, whose body still
--   names canonical_v2.* tables that no longer exist. Nothing has recomputed since, so the stored
--   snapshot froze at as_of 2026-08-10 while attended events kept arriving -> the nightly
--   health-check's independent recompute disagrees with the stale rows every night.
--
-- WHAT: the SAME function body as 0008, with ONLY the table names repointed (mechanical, checked
--   by supabase/scripts/topic_intel_compute.py --dry-run, which executes this file's SELECTs):
--     canonical_v2.event / event_entity / topic            -> public.event / event_entity / topic
--     canonical_v2.topic_trend / topic_pair_metric / ingestion_run -> topic_intelligence.*
--   THE MATH IS UNCHANGED: windows 30/7/all_time, momentum, trend_label, the 2026-08-07 bridge
--   fix (two DISTINCT events), content_hash recipe, intersection_score, novelty. Reads stay scoped
--   to kind='attended' + role='tagged_topic'. No person PII is written (ADR-9): the topic tables
--   hold cluster ids, counts and bridge person UUIDs only, exactly as before.
--
-- WRITE PATH (runbook 2B §6 + 0003): SECURITY DEFINER owned by the migration runner (postgres),
--   search_path pinned, EXECUTE granted ONLY to pipeline_writer. The nightly Action runs
--   `set role pipeline_writer; select topic_intelligence.compute_topic_intelligence(...)`, so the
--   session that triggers the write can do nothing else in topic_intelligence. Write contract is
--   0008's: DELETE-by-as_of_date + INSERT in one transaction (the function body); prior dates are
--   never touched.
--
-- ALSO: drops the stale canonical_v2.compute_topic_intelligence (it now references missing
--   tables; calling it can only error) — removes the footgun the issue flagged.
--
-- APPLY: Supabase dashboard SQL Editor (paste whole file) or
--   psql "<session-pooler DSN>" -v ON_ERROR_STOP=1 -f supabase/migrations/0012_topic_intelligence_live_compute.sql
-- Verify: see the checks at the bottom of this file.

begin;

create or replace function topic_intelligence.compute_topic_intelligence(
  p_as_of   date default current_date,
  p_runtime text default 'manual'
) returns uuid
language plpgsql
security definer
set search_path = pg_catalog, pg_temp
as $fn$
declare
  v_run_id uuid;
  w        record;
begin
  insert into topic_intelligence.ingestion_run (source, runtime, status, started_at)
  values ('computed', p_runtime, 'running', now())
  returning run_id into v_run_id;

  -- RELOAD: clear only this as_of_date (never prior dates)
  delete from topic_intelligence.topic_trend       where as_of_date = p_as_of;
  delete from topic_intelligence.topic_pair_metric where as_of_date = p_as_of;

  for w in
    select window_type, days
    from (values ('month', 30), ('week', 7), ('all_time', null::int)) as t(window_type, days)
  loop
    -----------------------------------------------------------------------
    -- TREND (cluster level)
    -----------------------------------------------------------------------
    insert into topic_intelligence.topic_trend (
      subject_level, subject_id, window_type, as_of_date,
      event_count, distinct_speaker_count, prior_event_count, momentum,
      trend_label, is_low_confidence, source, content_hash, ingestion_run_id)
    with tagged as (
      -- event -> topic tag (role='tagged_topic'), event scoped to kind='attended',
      -- topic rolled to its cluster
      select t.cluster_id, e.id as event_id, e.event_date
      from public.event_entity ee
      join public.event e on e.id = ee.event_id
      join public.topic t on t.id = ee.entity_id
      where ee.entity_type='topic' and ee.role='tagged_topic'
        and e.kind='attended'
        and t.cluster_id is not null
        and (w.days is null or e.event_date::date >= p_as_of - make_interval(days => w.days))
    ),
    this_w as (
      select cluster_id, count(distinct event_id) as ec from tagged group by cluster_id
    ),
    prior_w as (
      select t.cluster_id, count(distinct e.id) as pc
      from public.event_entity ee
      join public.event e on e.id = ee.event_id
      join public.topic t on t.id = ee.entity_id
      where w.days is not null
        and ee.entity_type='topic' and ee.role='tagged_topic'
        and e.kind='attended'
        and t.cluster_id is not null
        and e.event_date::date >= p_as_of - make_interval(days => 2*w.days)
        and e.event_date::date <  p_as_of - make_interval(days => w.days)
      group by t.cluster_id
    ),
    spk as (
      -- distinct speakers (speaker/host/panelist) at the cluster's tagged events
      select tg.cluster_id, count(distinct sp.entity_id) as sc
      from tagged tg
      join public.event_entity sp
        on sp.event_id = tg.event_id
       and sp.entity_type='person' and sp.role in ('speaker','host','panelist')
      group by tg.cluster_id
    )
    select
      'cluster', tw.cluster_id, w.window_type, p_as_of,
      tw.ec,
      coalesce(s.sc, 0),
      case when w.days is null then null else coalesce(pw.pc, 0) end,
      case when w.days is null then null
           else (tw.ec - coalesce(pw.pc,0))::numeric / greatest(coalesce(pw.pc,0), 1) end,
      case
        when tw.ec < 3           then 'insufficient_data'
        when w.days is null      then 'steady'
        when coalesce(pw.pc,0)=0 then 'new'
        when (tw.ec - coalesce(pw.pc,0))::numeric/greatest(coalesce(pw.pc,0),1) >=  0.5 then 'heating'
        when (tw.ec - coalesce(pw.pc,0))::numeric/greatest(coalesce(pw.pc,0),1) <= -0.5 then 'cooling'
        else 'steady'
      end,
      (tw.ec < 3) or (w.window_type = 'week'),
      'computed',
      md5(tw.cluster_id::text||'|'||w.window_type||'|'||p_as_of::text||'|'||tw.ec||'|'||coalesce(s.sc,0)||'|'||coalesce(pw.pc,0)),
      v_run_id
    from this_w tw
    left join prior_w pw on pw.cluster_id = tw.cluster_id
    left join spk     s  on s.cluster_id  = tw.cluster_id;

    -----------------------------------------------------------------------
    -- PAIRS: co-occurrence (shared events) + bridges (shared speakers)
    -----------------------------------------------------------------------
    insert into topic_intelligence.topic_pair_metric (
      subject_level, subject_a_id, subject_b_id, window_type, as_of_date,
      cooccurrence_event_count, bridge_person_count, bridge_entity_ids,
      first_cooccurred_on, is_new_pair, intersection_score,
      source, content_hash, ingestion_run_id)
    with cluster_events as (
      select distinct t.cluster_id, e.id as event_id, e.event_date
      from public.event_entity ee
      join public.event e on e.id = ee.event_id
      join public.topic t on t.id = ee.entity_id
      where ee.entity_type='topic' and ee.role='tagged_topic'
        and e.kind='attended'
        and t.cluster_id is not null
        and (w.days is null or e.event_date::date >= p_as_of - make_interval(days => w.days))
    ),
    cooc as (
      select ce1.cluster_id as a, ce2.cluster_id as b,
             count(distinct ce1.event_id) as cnt
      from cluster_events ce1
      join cluster_events ce2 on ce1.event_id = ce2.event_id and ce1.cluster_id < ce2.cluster_id
      group by ce1.cluster_id, ce2.cluster_id
    ),
    -- speaker -> (cluster, event): keep event_id so a bridge requires TWO DISTINCT events
    -- (the 2026-08-07 bridge-inflation fix — a single dual-tagged event is co-occurrence, not a bridge).
    speaker_cluster_event as (
      select distinct sp.entity_id, t.cluster_id, e.id as event_id
      from public.event_entity sp
      join public.event e on e.id = sp.event_id
      join public.event_entity tt
        on tt.event_id = e.id and tt.entity_type='topic' and tt.role='tagged_topic'
      join public.topic t on t.id = tt.entity_id
      where sp.entity_type='person' and sp.role in ('speaker','host','panelist')
        and e.kind='attended'
        and t.cluster_id is not null
        and (w.days is null or e.event_date::date >= p_as_of - make_interval(days => w.days))
    ),
    bridges as (
      select sc1.cluster_id as a, sc2.cluster_id as b,
             count(distinct sc1.entity_id)      as bcnt,
             array_agg(distinct sc1.entity_id)  as barr
      from speaker_cluster_event sc1
      join speaker_cluster_event sc2
        on sc1.entity_id = sc2.entity_id
       and sc1.cluster_id < sc2.cluster_id
       and sc1.event_id  <> sc2.event_id
      group by sc1.cluster_id, sc2.cluster_id
    ),
    all_time_first as (
      select e1.a, e1.b, min(e1.event_date) as first_ever
      from (
        select ce_a.cluster_id as a, ce_b.cluster_id as b, ce_a.event_date
        from (select distinct t.cluster_id, e.id as event_id, e.event_date
              from public.event_entity ee
              join public.event e on e.id = ee.event_id
              join public.topic t on t.id = ee.entity_id
              where ee.entity_type='topic' and ee.role='tagged_topic'
                and e.kind='attended' and t.cluster_id is not null) ce_a
        join (select distinct t.cluster_id, e.id as event_id
              from public.event_entity ee
              join public.event e on e.id = ee.event_id
              join public.topic t on t.id = ee.entity_id
              where ee.entity_type='topic' and ee.role='tagged_topic'
                and e.kind='attended' and t.cluster_id is not null) ce_b
          on ce_a.event_id = ce_b.event_id and ce_a.cluster_id < ce_b.cluster_id
      ) e1 group by e1.a, e1.b
    )
    select
      'cluster',
      coalesce(c.a, b.a),
      coalesce(c.b, b.b),
      w.window_type, p_as_of,
      coalesce(c.cnt, 0),
      coalesce(b.bcnt, 0),
      coalesce(b.barr, '{}'::uuid[]),
      atf.first_ever,
      (w.days is not null and atf.first_ever is not null
        and atf.first_ever >= p_as_of - make_interval(days => w.days)),
      coalesce(c.cnt,0) + 2*coalesce(b.bcnt,0)
        + case when (w.days is not null and atf.first_ever is not null
                     and atf.first_ever >= p_as_of - make_interval(days => w.days)) then 2 else 0 end,
      'computed',
      md5(coalesce(c.a,b.a)::text||'|'||coalesce(c.b,b.b)::text||'|'||w.window_type||'|'||p_as_of::text
          ||'|'||coalesce(c.cnt,0)||'|'||coalesce(b.bcnt,0)||'|'||coalesce(atf.first_ever::text,'')),
      v_run_id
    from cooc c
    full outer join bridges b on c.a = b.a and c.b = b.b
    left join all_time_first atf
      on atf.a = coalesce(c.a, b.a) and atf.b = coalesce(c.b, b.b);

  end loop;

  update topic_intelligence.ingestion_run set status='success', finished_at=now() where run_id = v_run_id;
  return v_run_id;
end;
$fn$;

revoke all on function topic_intelligence.compute_topic_intelligence(date, text) from public;
grant execute on function topic_intelligence.compute_topic_intelligence(date, text) to pipeline_writer;

-- pipeline_writer needs USAGE on the schema to resolve the function name (0003 revoked ALL on
-- the schema). USAGE grants no table access: the base tables stay revoked from pipeline_writer.
grant usage on schema topic_intelligence to pipeline_writer;

-- Let the Action's login (postgres, via MI_DB_DSN) assume pipeline_writer. On PG16+ the creator
-- of a role holds ADMIN but not SET on it, so `set role pipeline_writer` fails until this runs.
grant pipeline_writer to postgres with set true, inherit false;

-- Retire the pre-swap copy (its body names canonical_v2 tables that were moved at the swap).
drop function if exists canonical_v2.compute_topic_intelligence(date, text);

commit;

-- Verify (read-only):
--   select has_function_privilege('pipeline_writer',
--          'topic_intelligence.compute_topic_intelligence(date,text)', 'execute');      -- t
--   select has_table_privilege('pipeline_writer', 'topic_intelligence.topic_trend', 'insert'); -- f
--   select set_option from pg_auth_members am join pg_roles r on r.oid = am.roleid
--     join pg_roles m on m.oid = am.member
--    where r.rolname = 'pipeline_writer' and m.rolname = 'postgres';                   -- a t row
-- First write (or let the Action's workflow_dispatch do it):
--   set role pipeline_writer;
--   select topic_intelligence.compute_topic_intelligence(current_date, 'manual');
--   reset role;
--
-- Rollback:
--   drop function if exists topic_intelligence.compute_topic_intelligence(date, text);
--   revoke usage on schema topic_intelligence from pipeline_writer;
--   revoke pipeline_writer from postgres;   -- removes only the SET grant added here
--   -- (rows written by the function are ordinary snapshot rows: delete by as_of_date if needed)
