-- =====================================================================
-- 0010 — Knowledge Substrate S2 (ADR-10): retrieval RPCs. ADDITIVE (functions only).
--
-- Apply AFTER 0009. Rehearse on Phantom-Test-Case first; prod by Alex's SQL-Editor
-- paste (ADR-10 decision 4). Re-runnable: `create or replace` throughout.
--
-- Adapted from the architecture doc §6.3 per the review and the S1a schema:
--   * no claim.speaker_person_id — speakers are claim_entity(role='asserted_by');
--   * recency is claim.asserted_at (assertion date), not created_at;
--   * statuses default to approved + candidate (candidates are first-hand claims from
--     Alex-reviewed briefs, labelled "unreviewed" by retrieve.py); rejected never returns;
--   * entity_neighborhood caps claims and documents (review "worth knowing" #2) and returns
--     only CURRENT documents;
--   * match_entities is deferred to S1b with the entity embeddings it needs.
-- =====================================================================
begin;

create or replace function public.match_claims_hybrid (
  query_embedding    vector(384),
  query_text         text,
  match_count        int    default 20,
  candidate_n        int    default 40,
  rrf_k              int    default 60,
  filter_entity_ids  uuid[] default null,           -- null = unscoped (the dev lens needs entity-less claims)
  filter_statuses    text[] default array['approved','candidate'],
  filter_tiers       text[] default null
)
returns table (id uuid, claim_text text, claim_type text, quote text, locator jsonb,
               provenance_tier text, confidence numeric, status text, metadata jsonb,
               document_id uuid, event_id uuid, asserted_at timestamptz,
               dense_rank integer, keyword_rank integer, rrf_score float)
language sql stable as $$
  with base as (
    select c.*
    from public.claim c
    where c.status = any(filter_statuses)
      and (filter_tiers is null or c.provenance_tier = any(filter_tiers))
      and (filter_entity_ids is null
           or exists (select 1 from public.claim_entity ce
                      where ce.claim_id = c.id and ce.entity_id = any(filter_entity_ids))
           or exists (select 1 from public.event_entity ee
                      where ee.event_id = c.event_id and ee.entity_id = any(filter_entity_ids)))
  ),
  dense as (
    select id, row_number() over (order by embedding <=> query_embedding) as r
    from base where embedding is not null
    order by embedding <=> query_embedding limit candidate_n
  ),
  kw as (
    select id, row_number() over (order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc) as r
    from base where tsv @@ websearch_to_tsquery('english', query_text)
    order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc limit candidate_n
  ),
  fused as (
    select coalesce(d.id, k.id) as id, d.r as dr, k.r as kr,
           coalesce(1.0 / (rrf_k + d.r), 0) + coalesce(1.0 / (rrf_k + k.r), 0) as score
    from dense d full outer join kw k on d.id = k.id
  )
  select b.id, b.claim_text, b.claim_type, b.quote, b.locator, b.provenance_tier, b.confidence,
         b.status, b.metadata, b.document_id, b.event_id, b.asserted_at,
         f.dr::integer, f.kr::integer, f.score::float
  from fused f join base b on b.id = f.id
  order by f.score desc, b.asserted_at desc nulls last
  limit match_count;
$$;
alter function public.match_claims_hybrid(vector, text, int, int, int, uuid[], text[], text[])
  set search_path = public;

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
  )
  select jsonb_build_object(
    'events',    (select coalesce(jsonb_agg(to_jsonb(ev)),   '[]'::jsonb) from ev),
    'edges',     (select coalesce(jsonb_agg(to_jsonb(co)),   '[]'::jsonb) from co),
    'documents', (select coalesce(jsonb_agg(to_jsonb(docs)), '[]'::jsonb) from docs),
    'claims',    (select coalesce(jsonb_agg(to_jsonb(cl)),   '[]'::jsonb) from cl)
  );
$$;
alter function public.entity_neighborhood(uuid[], timestamptz, int, int, int) set search_path = public;

commit;

-- ============================ VERIFY ============================
-- expect 2 rows
-- select proname from pg_proc where pronamespace = 'public'::regnamespace
--   and proname in ('match_claims_hybrid', 'entity_neighborhood') order by 1;
-- smoke — must not error (returns empty arrays until claims land):
-- select public.entity_neighborhood(array[(select id from public.company limit 1)]);
