-- 0008 — Increment 2b, part 4: the ported compute (AC2b.3)
-- Spec: supabase/specs/2b_relations_to_event_entity_mapping.md (§2–4) · Linear: YED-130
-- Source of the math: gtm-os/scripts/topic_intelligence/compute_topic_intelligence.sql
--
-- WHAT: a faithful port of gtm's compute_topic_intelligence. THE MATH IS UNCHANGED
--   (windows 30/7/all_time, momentum, trend_label per spec §3.2, the 2026-08-07 bridge-
--   inflation fix = two DISTINCT events, content_hash recipe, intersection_score, novelty).
--   ONLY the substrate moves: gtm signal.relations/events/topics  ->  canonical_v2.event_entity
--   /event/topic, per the spec §2 edge mapping. Reads are SCOPED to kind='attended' (spec §5),
--   and topic tags are read as role='tagged_topic' only (market's role='subject' can't leak).
--   Empire event_date is timestamptz -> cast ::date on every window boundary (spec §4).
--
-- WRITE CONTRACT (unchanged from gtm): DELETE-by-as_of_date + INSERT, atomic (the fn body is
--   one txn), writer = owner/service_role (deny-all RLS eats it otherwise). topic_pair_metric
--   is a DYNAMIC row set -> reload, never blind-upsert (stale-orphan-pair guard).
--
-- POST-SWAP: at cutover this becomes the nightly compute the pipeline calls; wire it to the
--   scoped writer role the same way 0003 does for topic_intelligence. During the rehearsal it
--   runs as owner. GATED: canonical_v2 only, Phantom Test Case DB first.

create or replace function canonical_v2.compute_topic_intelligence(
  p_as_of   date default current_date,
  p_runtime text default 'pg_cron'
) returns uuid
language plpgsql
as $fn$
declare
  v_run_id uuid;
  w        record;
begin
  insert into canonical_v2.ingestion_run (source, runtime, status, started_at)
  values ('computed', p_runtime, 'running', now())
  returning run_id into v_run_id;

  -- RELOAD: clear only this as_of_date (never prior dates)
  delete from canonical_v2.topic_trend       where as_of_date = p_as_of;
  delete from canonical_v2.topic_pair_metric where as_of_date = p_as_of;

  for w in
    select window_type, days
    from (values ('month', 30), ('week', 7), ('all_time', null::int)) as t(window_type, days)
  loop
    -----------------------------------------------------------------------
    -- TREND (cluster level)
    -----------------------------------------------------------------------
    insert into canonical_v2.topic_trend (
      subject_level, subject_id, window_type, as_of_date,
      event_count, distinct_speaker_count, prior_event_count, momentum,
      trend_label, is_low_confidence, source, content_hash, ingestion_run_id)
    with tagged as (
      -- event -> topic tag (role='tagged_topic'), event scoped to kind='attended',
      -- topic rolled to its cluster
      select t.cluster_id, e.id as event_id, e.event_date
      from canonical_v2.event_entity ee
      join canonical_v2.event e on e.id = ee.event_id
      join canonical_v2.topic t on t.id = ee.entity_id
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
      from canonical_v2.event_entity ee
      join canonical_v2.event e on e.id = ee.event_id
      join canonical_v2.topic t on t.id = ee.entity_id
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
      join canonical_v2.event_entity sp
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
    insert into canonical_v2.topic_pair_metric (
      subject_level, subject_a_id, subject_b_id, window_type, as_of_date,
      cooccurrence_event_count, bridge_person_count, bridge_entity_ids,
      first_cooccurred_on, is_new_pair, intersection_score,
      source, content_hash, ingestion_run_id)
    with cluster_events as (
      select distinct t.cluster_id, e.id as event_id, e.event_date
      from canonical_v2.event_entity ee
      join canonical_v2.event e on e.id = ee.event_id
      join canonical_v2.topic t on t.id = ee.entity_id
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
      from canonical_v2.event_entity sp
      join canonical_v2.event e on e.id = sp.event_id
      join canonical_v2.event_entity tt
        on tt.event_id = e.id and tt.entity_type='topic' and tt.role='tagged_topic'
      join canonical_v2.topic t on t.id = tt.entity_id
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
              from canonical_v2.event_entity ee
              join canonical_v2.event e on e.id = ee.event_id
              join canonical_v2.topic t on t.id = ee.entity_id
              where ee.entity_type='topic' and ee.role='tagged_topic'
                and e.kind='attended' and t.cluster_id is not null) ce_a
        join (select distinct t.cluster_id, e.id as event_id
              from canonical_v2.event_entity ee
              join canonical_v2.event e on e.id = ee.event_id
              join canonical_v2.topic t on t.id = ee.entity_id
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

  update canonical_v2.ingestion_run set status='success', finished_at=now() where run_id = v_run_id;
  return v_run_id;
end;
$fn$;

-- Manual run during the rehearsal (as owner/service_role):
--   select canonical_v2.compute_topic_intelligence(current_date, 'manual');
-- Then run the invariant suite (AC2b.4) + the fresh reference impl and require agreement
-- BEFORE trusting the snapshot. Do NOT schedule pg_cron until after the swap.
