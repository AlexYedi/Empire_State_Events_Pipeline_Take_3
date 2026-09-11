-- =====================================================================
-- YED-156 — Doc-KB Phase A.5 migration (ADDITIVE ONLY — no dims change)
-- Project: Supabase `empire state ai` — ref oicikjyzmxqfomrrqkvf  (NOT any other project)
-- Apply ONCE via the empire state ai SQL Editor, AFTER doc-kb-schema.sql.
-- Adds: retrieval profiles (for the 3-arm A/B), per-chunk context (Contextual
-- Retrieval), a generated tsvector + GIN (keyword arm), and the hybrid RRF RPC.
-- Existing Phase-A rows are untouched: they become profile 'dense_v1'.
-- =====================================================================

-- 1. documents: profile + context provenance -------------------------
alter table public.documents
  add column if not exists retrieval_profile text not null default 'dense_v1'
    check (retrieval_profile in ('dense_v1','contextual_v1')),
  add column if not exists context_model    text,            -- e.g. 'claude-haiku-4-5' (null for dense_v1)
  add column if not exists context_cost_usd numeric(10,4);   -- one-time ingest spend, logged (PRD AC-5)

-- allow the SAME file to be ingested under a second profile (A/B side-by-side)
alter table public.documents drop constraint if exists documents_sha256_key;
create unique index if not exists documents_sha256_profile_uq
  on public.documents (sha256, retrieval_profile);

-- 2. doc_chunks: situating context + keyword index --------------------
alter table public.doc_chunks
  add column if not exists context text;      -- 1-2 sentence situating context (null for dense_v1)

-- generated tsvector over (context + content): auto-maintained, no app-side writes.
-- 'english' config (stemming) chosen as the build-time default; 'simple' is the
-- alternative for technical tokens — swap here + reindex if the A/B says so.
alter table public.doc_chunks
  add column if not exists tsv tsvector
    generated always as (to_tsvector('english', coalesce(context, '') || ' ' || content)) stored;
create index if not exists doc_chunks_tsv_gin on public.doc_chunks using gin (tsv);

-- 3. dense RPC: add a profile filter (so the baseline arm never mixes profiles)
--    Signature changes -> drop + recreate (avoids a PostgREST overload ambiguity).
drop function if exists public.match_doc_chunks(vector, int, uuid);
create or replace function public.match_doc_chunks (
  query_embedding    vector(384),
  match_count        int  default 8,
  filter_document_id uuid default null,
  filter_profile     text default null
)
returns table (id uuid, document_id uuid, chunk_index integer, content text,
               locator jsonb, similarity float)
language sql stable
as $$
  select c.id, c.document_id, c.chunk_index, c.content, c.locator,
         1 - (c.embedding <=> query_embedding) as similarity
  from public.doc_chunks c
  join public.documents d on d.id = c.document_id
  where (filter_document_id is null or c.document_id = filter_document_id)
    and (filter_profile is null or d.retrieval_profile = filter_profile)
  order by c.embedding <=> query_embedding
  limit match_count;
$$;
alter function public.match_doc_chunks(vector, int, uuid, text) set search_path = public;

-- 4. hybrid RPC: dense top-N ∪ keyword top-N -> reciprocal-rank fusion ----
--    Reranking happens client-side (local cross-encoder) on these candidates.
--    rrf_k / candidate_n are the deferred build-time params (PRD §8) — passed
--    per call so the harness can sweep them without a DDL change.
create or replace function public.match_doc_chunks_hybrid (
  query_embedding    vector(384),
  query_text         text,
  match_count        int  default 20,
  candidate_n        int  default 20,
  rrf_k              int  default 60,
  filter_document_id uuid default null,
  filter_profile     text default null
)
returns table (id uuid, document_id uuid, chunk_index integer, content text,
               context text, locator jsonb, dense_rank integer, keyword_rank integer,
               rrf_score float)
language sql stable
as $$
  with base as (
    select c.id, c.document_id, c.chunk_index, c.content, c.context, c.locator,
           c.embedding, c.tsv
    from public.doc_chunks c
    join public.documents d on d.id = c.document_id
    where (filter_document_id is null or c.document_id = filter_document_id)
      and (filter_profile is null or d.retrieval_profile = filter_profile)
  ),
  dense as (
    select id, row_number() over (order by embedding <=> query_embedding) as r
    from base
    order by embedding <=> query_embedding
    limit candidate_n
  ),
  kw as (
    select id,
           row_number() over (
             order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc) as r
    from base
    where tsv @@ websearch_to_tsquery('english', query_text)
    order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc
    limit candidate_n
  ),
  fused as (
    select coalesce(dense.id, kw.id) as id,
           dense.r as dr, kw.r as kr,
           coalesce(1.0 / (rrf_k + dense.r), 0) + coalesce(1.0 / (rrf_k + kw.r), 0) as score
    from dense full outer join kw on dense.id = kw.id
  )
  select b.id, b.document_id, b.chunk_index, b.content, b.context, b.locator,
         f.dr::integer, f.kr::integer, f.score::float
  from fused f
  join base b on b.id = f.id
  order by f.score desc, b.chunk_index
  limit match_count;
$$;
alter function public.match_doc_chunks_hybrid(vector, text, int, int, int, uuid, text)
  set search_path = public;

-- 5. Verify (optional) -------------------------------------------------
-- select retrieval_profile, count(*) from public.documents group by 1;          -- expect dense_v1 | 1
-- select count(*) from public.doc_chunks where tsv is not null;                 -- expect 250
-- select proname from pg_proc where proname like 'match_doc_chunks%';          -- expect both
