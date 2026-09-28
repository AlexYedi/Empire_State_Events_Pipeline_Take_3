-- =====================================================================
-- 0011 — YED-149: isolate the job lens from the event lens. ADDITIVE (one function, re-defined).
--
-- Apply AFTER 0010. Prod by Alex's SQL-Editor paste (DDL via MCP is declined). Re-runnable:
-- `create or replace`, identical signature, so callers (retrieve.py) need no change to keep working.
-- Spec: .claude/notes/yed-149-spec-2026-09-27.md decision 5.
--
-- Why: role-radar now writes `role_posted` events (hundreds, freshly dated). entity_neighborhood
-- ordered ALL kinds by event_date desc under `limit max_events`, so roles at a seed company would
-- crowd attended/market history out of every /event-deep-research Context Pack — and a future
-- `application`/`interview` row would surface in a brief. Two changes:
--   1. `ev` excludes the job-lens kinds (role_posted, application, interview) BEFORE the limit;
--   2. a new `hiring` key: one count row per SEED company (role_posted only — never applications
--      or interviews; archived roles excluded), with ICP-tier split and the latest posted date.
--      Counts, not titles.
-- Everything else is byte-for-byte 0010.
-- =====================================================================
begin;

create or replace function public.entity_neighborhood (
  seed_ids    uuid[],
  since       timestamptz default null,
  max_events  int default 60,
  max_claims  int default 120,
  max_docs    int default 40
)
returns jsonb language sql stable as $$
  with ev as (
    select distinct e.id, e.title, e.kind, e.event_date, e.source, e.url, e.confidence
    from public.event e join public.event_entity ee on ee.event_id = e.id
    where ee.entity_id = any(seed_ids) and (since is null or e.event_date >= since)
      and e.kind <> all (array['role_posted', 'application', 'interview'])
    order by e.event_date desc nulls last limit max_events
  ),
  co as (
    select ee.event_id, ee.entity_type, ee.entity_id, ee.role,
           coalesce(c.name, p.name, t.name) as name
    from public.event_entity ee
    left join public.company c on c.id = ee.entity_id and ee.entity_type = 'company'
    left join public.person  p on p.id = ee.entity_id and ee.entity_type = 'person'
    left join public.topic   t on t.id = ee.entity_id and ee.entity_type = 'topic'
    where ee.event_id in (select id from ev)
  ),
  docs as (
    select distinct d.id, d.title, d.source_type, d.doc_date, d.external_ref, d.event_id
    from public.documents d
    left join public.document_entity de on de.document_id = d.id
    where d.is_current and (de.entity_id = any(seed_ids) or d.event_id in (select id from ev))
    order by d.doc_date desc nulls last limit max_docs
  ),
  cl as (
    select distinct c.id, c.claim_text, c.claim_type, c.provenance_tier, c.confidence, c.status,
           c.event_id, c.document_id, c.asserted_at, c.metadata
    from public.claim c
    left join public.claim_entity ce on ce.claim_id = c.id
    where c.status in ('approved', 'candidate')
      and (ce.entity_id = any(seed_ids) or c.event_id in (select id from ev))
    order by c.asserted_at desc nulls last limit max_claims
  ),
  hiring as (
    select c.id as company_id, c.name, count(distinct e.id) as roles,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'A') as tier_a,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'B') as tier_b,
           count(distinct e.id) filter (where e.metadata->>'icp_tier' = 'C') as tier_c,
           max(e.event_date) as latest_posted
    from public.event e
    join public.event_entity ee on ee.event_id = e.id and ee.entity_type = 'company'
    join public.company c on c.id = ee.entity_id
    where ee.entity_id = any(seed_ids) and e.kind = 'role_posted'
      and coalesce(e.metadata->>'status', '') <> 'archived'   -- archived in Notion = closed or not pursued
    group by c.id, c.name
  )
  select jsonb_build_object(
    'events',    (select coalesce(jsonb_agg(to_jsonb(ev)),     '[]'::jsonb) from ev),
    'edges',     (select coalesce(jsonb_agg(to_jsonb(co)),     '[]'::jsonb) from co),
    'documents', (select coalesce(jsonb_agg(to_jsonb(docs)),   '[]'::jsonb) from docs),
    'claims',    (select coalesce(jsonb_agg(to_jsonb(cl)),     '[]'::jsonb) from cl),
    'hiring',    (select coalesce(jsonb_agg(to_jsonb(hiring)), '[]'::jsonb) from hiring)
  );
$$;
alter function public.entity_neighborhood(uuid[], timestamptz, int, int, int) set search_path = public;

commit;

-- ============================ VERIFY ============================
-- the new key is present (empty array until role_posted rows exist):
-- select public.entity_neighborhood(array[(select id from public.company limit 1)]) ? 'hiring';
-- no job-lens kind can reach `events` (expect 0):
-- select count(*) from jsonb_array_elements(
--   public.entity_neighborhood(array(select entity_id from public.event_entity ee join public.event e
--     on e.id = ee.event_id where e.kind = 'role_posted' and ee.entity_type = 'company'))->'events') x
--   where x->>'kind' in ('role_posted', 'application', 'interview');
