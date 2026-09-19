-- =====================================================================
-- 0009 — Knowledge Substrate S1a (ADR-10) — ADDITIVE ONLY
--
-- Target: rehearse on Phantom-Test-Case (ytfzzsxcxxbejnowmkmk) FIRST, per
-- supabase/SUBSTRATE_S1A_REHEARSAL_RUNBOOK.md. Prod (oicikjyzmxqfomrrqkvf,
-- "The-Prod-Brain") only after the rehearsal — incl. a PROVEN rollback — is green,
-- and only by Alex in the SQL Editor (ADR-10 decision 4: no MCP DDL).
--
-- What "additive" means here, precisely:
--   * new tables:   claim, claim_entity, claim_relation, document_entity,
--                   artifact_outcome, claim_usage
--   * new columns:  documents.{event_id, external_ref, doc_date, version,
--                   supersedes_id, is_current, produced_by, visibility, metadata}
--   * two WIDENINGS (a CHECK that admits more values; a NOT NULL dropped):
--       event_kind_enum    += 'published'
--       documents.source_type += our artifact types; documents.blob_key nullable
--     A widening never rejects an existing row. The rollback deliberately does
--     NOT re-narrow them (re-narrowing fails once new-type rows exist) — they
--     stay widened, which is harmless. That is what keeps the rollback valid
--     forever instead of for ~4 hours (review finding 1b).
--   * NOT here (that is S1b, week 2, YED-47): name_norm columns, the unique-index
--     swap on company/topic, entity_alias, entity_merge, entity embeddings.
--   * doc_claims is NOT renamed. `claim` is a new table; doc_claims (0 rows)
--     stays in place, deprecated, until S1b drops it.
--
-- Re-runnable: every statement is guarded (if not exists / drop … if exists),
-- including the trigger (Postgres has no CREATE TRIGGER IF NOT EXISTS — review
-- finding 1c). A second paste is a no-op, not a silent full rollback.
--
-- After COMMIT, run supabase/staging/s1a_verify.sql — it asserts BEHAVIOUR
-- (inserts that must succeed, inserts that must fail) and raises on any miss.
-- =====================================================================
begin;

create extension if not exists vector;

-- ---------------------------------------------------------------------
-- 1. Event kinds: + 'published' only (ADR-10 decision 3: no 'observed';
--    'shipped' deferred). Widening — re-validates existing rows.
-- ---------------------------------------------------------------------
alter table public.event drop constraint if exists event_kind_enum;
alter table public.event add constraint event_kind_enum check (kind in (
  'attended', 'market', 'funding', 'launch', 'exec_move',
  'role_posted', 'application', 'interview',
  'reference',
  'published'      -- NEW: Alex published an artifact (content-lens memory + outcome anchor)
));

-- ---------------------------------------------------------------------
-- 2. Documents: generalize from "books in R2" to every artifact with a body
-- ---------------------------------------------------------------------
alter table public.documents alter column blob_key drop not null;   -- our own artifacts have no R2 blob

alter table public.documents drop constraint if exists documents_source_type_check;
alter table public.documents add constraint documents_source_type_check check (source_type in (
  'book', 'whitepaper', 'filing', 'pdf', 'other',
  'research_brief', 'deep_read', 'prior_context_pack', 'post_event_brief', 'transcript',
  'linkedin_post', 'carousel', 'connection_note', 'dossier', 'project_idea',
  'scan_digest', 'build_retro', 'note', 'glossary'
));

alter table public.documents
  add column if not exists event_id       uuid references public.event(id) on delete set null,
  add column if not exists external_ref   text,          -- Notion page id · repo path · PR url · message-id
  add column if not exists doc_date       timestamptz,   -- when the artifact is "about" (event date / publish date)
  add column if not exists version        integer not null default 1,
  add column if not exists supersedes_id  uuid references public.documents(id) on delete set null,
  add column if not exists is_current     boolean not null default true,
  add column if not exists produced_by    text,          -- command / skill that produced it
  add column if not exists visibility     text not null default 'private',
  add column if not exists metadata       jsonb not null default '{}';

alter table public.documents drop constraint if exists documents_visibility_check;
alter table public.documents add constraint documents_visibility_check
  check (visibility in ('private', 'public_ok'));

-- Our-artifact identity (review "worth knowing" #1): one row per (ref, version),
-- and exactly one CURRENT row per ref. Books (external_ref null) are unaffected.
create unique index if not exists documents_external_ref_version_uq
  on public.documents (external_ref, version) where external_ref is not null;
create unique index if not exists documents_external_ref_current_uq
  on public.documents (external_ref) where external_ref is not null and is_current;
create index if not exists documents_event_idx       on public.documents (event_id);
create index if not exists documents_source_type_idx on public.documents (source_type);

create table if not exists public.document_entity (
  document_id  uuid not null references public.documents(id) on delete cascade,
  entity_type  text not null check (entity_type in ('company', 'person', 'topic')),
  entity_id    uuid not null,
  role         text not null default 'about' check (role in ('about', 'author', 'mentions')),
  created_at   timestamptz not null default now(),
  primary key (document_id, entity_type, entity_id, role)
);
create index if not exists document_entity_entity_idx on public.document_entity (entity_type, entity_id);

-- ---------------------------------------------------------------------
-- 3. Claims — the unified layer. One row per atomic assertion, any source.
--    Claims POINT AT events (event_id = the occasion); they are never
--    promoted into event rows (ADR-10 decision 1).
-- ---------------------------------------------------------------------
create table if not exists public.claim (
  id                 uuid primary key default gen_random_uuid(),
  source_key         text not null,   -- sha256 of the source document, or a synthetic
                                      -- occasion key: sha256('post_event:' || notion_event_id)
  claim_key          text not null,   -- sha256(normalized claim_text)
  claim_text         text not null,
  claim_type         text,            -- thesis | definition | statistic | practice | prediction |
                                      -- pitfall | hot_take | anecdote | recommendation | learning
  quote              text,            -- <= 25 words (licensing guard, enforced by the producer)
  locator            jsonb,           -- {section, speaker, timestamp, page, transcript_sha256}
  proposed_entities  jsonb not null default '[]',
  document_id        uuid references public.documents(id) on delete set null,
  event_id           uuid references public.event(id)     on delete set null,  -- the occasion
  provenance_tier    text not null default 'reference' check (provenance_tier in
                       ('first_hand', 'web_verified', 'email_signal', 'notion_prior',
                        'reference', 'model_inferred')),
  confidence         numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  asserted_at        timestamptz,     -- WHEN it was said (event/doc date), not when ingested —
                                      -- recency ranks on this (review finding 2)
  status             text not null default 'candidate'
                       check (status in ('candidate', 'approved', 'rejected')),
  extractor          text not null default 'claude',   -- claude | gemini | manual | parse
  extractor_model    text,
  lane               text,
  embedding          vector(384),     -- BAAI/bge-small-en-v1.5, same as doc_chunks
  embedding_model    text,
  tsv                tsvector generated always as
                       (to_tsvector('english', coalesce(claim_text, '') || ' ' || coalesce(quote, ''))) stored,
  utility_score      numeric not null default 0,   -- logged, NOT ranked on until >=20 outcomes (decision 5)
  use_count          integer not null default 0,
  last_used_at       timestamptz,
  metadata           jsonb not null default '{}',
  created_at         timestamptz not null default now(),
  reviewed_at        timestamptz,
  unique (source_key, claim_key)                    -- extraction is upsert-ignore => idempotent
);
create index if not exists claim_status_idx        on public.claim (status);
create index if not exists claim_source_idx        on public.claim (source_key);
create index if not exists claim_document_idx      on public.claim (document_id);
create index if not exists claim_event_idx         on public.claim (event_id);
create index if not exists claim_asserted_at_idx   on public.claim (asserted_at);
create index if not exists claim_tsv_gin           on public.claim using gin (tsv);
create index if not exists claim_embedding_hnsw    on public.claim using hnsw (embedding vector_cosine_ops);

-- Who a claim is about / who asserted it. `asserted_by` rows are the CANONICAL
-- speaker link (multi-speaker panels need N rows) — there is deliberately no
-- claim.speaker_person_id column to drift against it (review "worth knowing" #3).
create table if not exists public.claim_entity (
  claim_id     uuid not null references public.claim(id) on delete cascade,
  entity_type  text not null check (entity_type in ('company', 'person', 'topic')),
  entity_id    uuid not null,
  role         text not null default 'about' check (role in ('about', 'asserted_by', 'contrasts')),
  created_at   timestamptz not null default now(),
  primary key (claim_id, entity_type, entity_id, role)
);
create index if not exists claim_entity_entity_idx on public.claim_entity (entity_type, entity_id);

-- Claim <-> claim: contradiction, corroboration, supersession (review finding 3).
-- Consumers: pattern-synthesis (opposing theses), the content lens (stance
-- lineage), and rule-12 hygiene (a superseded stat never reaches a post).
create table if not exists public.claim_relation (
  id             uuid primary key default gen_random_uuid(),
  from_claim_id  uuid not null references public.claim(id) on delete cascade,
  to_claim_id    uuid not null references public.claim(id) on delete cascade,
  relation       text not null check (relation in ('contradicts', 'corroborates', 'supersedes', 'refines')),
  method         text not null default 'human' check (method in ('human', 'embedding', 'rule')),
  confidence     numeric check (confidence is null or (confidence >= 0 and confidence <= 1)),
  created_at     timestamptz not null default now(),
  check (from_claim_id <> to_claim_id),
  unique (from_claim_id, to_claim_id, relation)
);
create index if not exists claim_relation_to_idx on public.claim_relation (to_claim_id);

-- ---------------------------------------------------------------------
-- 4. Outcomes + usage — tables only, logged from day one. Nothing ranks on
--    them until >=20 outcome rows exist (ADR-10 decision 5).
-- ---------------------------------------------------------------------
create table if not exists public.artifact_outcome (
  document_id   uuid primary key references public.documents(id) on delete cascade,
  goal          text,   -- reach | engagement | connection | meeting | hybrid | internal | application | interview
  target        text,
  outcome       text check (outcome in ('hit', 'partial', 'miss', 'pending', 'na')),
  outcome_value text,
  outcome_date  timestamptz,
  source        text not null default 'tag_outcome',
  updated_at    timestamptz not null default now()
);
drop trigger if exists artifact_outcome_set_updated_at on public.artifact_outcome;
create trigger artifact_outcome_set_updated_at before update on public.artifact_outcome
  for each row execute function set_updated_at();

create table if not exists public.claim_usage (
  id           uuid primary key default gen_random_uuid(),
  claim_id     uuid not null references public.claim(id) on delete cascade,
  document_id  uuid not null references public.documents(id) on delete cascade,  -- the artifact that used it
  consumer     text not null check (consumer in ('event', 'content', 'job', 'ideation', 'dev')),
  used_at      timestamptz not null default now(),
  unique (claim_id, document_id)
);
create index if not exists claim_usage_claim_idx on public.claim_usage (claim_id);

-- ---------------------------------------------------------------------
-- 5. Security: RLS on, service-key only (matches every existing spine table).
-- ---------------------------------------------------------------------
alter table public.claim            enable row level security;
alter table public.claim_entity     enable row level security;
alter table public.claim_relation   enable row level security;
alter table public.document_entity  enable row level security;
alter table public.artifact_outcome enable row level security;
alter table public.claim_usage      enable row level security;

comment on table public.doc_claims is
  'DEPRECATED by ADR-10 (2026-09-18): superseded by public.claim. Kept (0 rows) until S1b drops it.';

commit;
