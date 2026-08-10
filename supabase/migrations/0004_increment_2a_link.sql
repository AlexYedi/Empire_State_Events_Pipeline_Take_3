-- 0004_increment_2a_link.sql
-- MI data-layer consolidation — Increment 2a (YED-130 / ADR-4). LINK layer. ADDITIVE.
-- =============================================================================
-- ADDITIVE ONLY, LOW-RISK. Increment 1 (0001) carried gtm-os's topic-intelligence
-- onto canonical keyed to gtm's OWN UUIDs, standing BESIDE Empire's `public` graph.
-- 2a LINKS the two via deterministic crosswalks (measured by the YED-116 probe) —
-- NO recompute, NO destructive change, NO row merge/delete of existing data.
--
-- This migration creates THREE mapping/crosswalk tables in the existing
-- `topic_intelligence` schema. It makes ZERO DDL against `public`. The only writes
-- to `public` in 2a are a handful of net-new INSERTS performed by the companion
-- script (scripts/build_2a_link.py): 25 gtm-only topics + 1 net-new company. No
-- UPDATE/DELETE of any pre-existing `public` row. Rollback of THIS file =
--   drop table topic_intelligence.{topic_crosswalk,entity_crosswalk,merge_map};
-- (the crosswalks are reviewed data, not a schema change to the graph).
--
-- WHAT THE CROSSWALKS RECORD (from the probe — see ADR-4 + increment-2-premortem.md):
--   * TOPICS   : 170 gtm topics -> 145 linked 1:1 to public.topic by de-hyphenated
--                notion_page_id + 25 gtm-only inserted-then-linked. 13 Empire-only
--                topics stay unlinked; 2 Empire topics have NULL notion_page_id
--                (flagged for backfill, cannot join). topic_crosswalk holds all 170.
--   * ENTITIES : 396 gtm entities -> 383 linked 1:1 by notion_page_id + 12 recovered
--                by exact normalized name (false splits — same real entity, different
--                Notion page) + 1 genuinely new (inserted). NEVER fuzzy-matched
--                (persons only 65% linkedin coverage → fuzzy would false-merge PII).
--   * merge_map: one row per name-recovered link (the 12) — the reversibility
--                contract (soft-merge / merge-map-first, ADR-4 §3).
--
-- SECURITY: these three tables hold PII LINKAGE (which gtm entity == which Empire
-- person/company). RLS is ENABLED + DENY-ALL (no policies) on all three. The
-- service_role / sb_secret key BYPASSES RLS (that is how the build script lands
-- rows); RLS here is a floor so anon/authenticated can never read the linkage.
-- topic_intelligence stays OUT of the Data API exposed-schemas (0003). No PII is
-- written to logs or to these tables beyond the linkage ids + a de-identified
-- notion_page_id / evidence note.
--
-- IDEMPOTENT: create table/index if not exists. Safe to re-apply.
--
-- APPLY: psql against the target (staging twin ytfzzsxcxxbejnowmkmk for the
-- rehearsal; the canonical project only after the full rehearsal gate is green).
-- The Supabase MCP is on a different account and MUST NOT be used here.
-- =============================================================================

begin;

-- gen_random_uuid() default for merge_map.id (pgcrypto already present from 0001).
create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- topic_crosswalk — every gtm topic -> its Empire topic (or the Empire id of the
-- gtm-only topic once inserted). 170 rows total after the build:
--   method='notion_id'  (145) linked to a pre-existing public.topic by de-hyph id
--   method='inserted'   (25)  gtm-only topic inserted into public.topic, then linked
-- empire_topic_id is nullable ONLY as a transient state; after build_2a_link.py all
-- 170 rows carry a non-null empire_topic_id. `note` carries per-row rationale.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.topic_crosswalk (
  gtm_topic_id    uuid        not null,
  empire_topic_id uuid,                          -- public.topic.id (null only transiently)
  method          text        not null,          -- 'notion_id' | 'inserted'
  confidence      numeric,
  note            text,
  created_at      timestamptz not null default now(),
  primary key (gtm_topic_id),
  constraint topic_crosswalk_confidence_range
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);
create index if not exists topic_crosswalk_empire
  on topic_intelligence.topic_crosswalk(empire_topic_id) where empire_topic_id is not null;
alter table topic_intelligence.topic_crosswalk enable row level security;
-- RLS deny-all: no policies declared (service_role bypasses; anon/authenticated denied).

-- -----------------------------------------------------------------------------
-- entity_crosswalk — every gtm entity -> its Empire person/company. 396 rows:
--   method='notion_id'   (383) linked 1:1 by de-hyphenated notion_page_id
--   method='exact_name'  (12)  recovered by exact normalized name (false split)
--   method='inserted'    (1)   genuinely new -> inserted into public.company/person
-- empire_kind disambiguates which public table empire_id points at.
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.entity_crosswalk (
  gtm_entity_id uuid        primary key,
  empire_id     uuid        not null,            -- public.company.id | public.person.id
  empire_kind   text        not null check (empire_kind in ('company','person')),
  method        text        not null check (method in ('notion_id','exact_name','inserted')),
  confidence    numeric,
  created_at    timestamptz not null default now(),
  constraint entity_crosswalk_confidence_range
    check (confidence is null or (confidence >= 0 and confidence <= 1))
);
create index if not exists entity_crosswalk_empire
  on topic_intelligence.entity_crosswalk(empire_kind, empire_id);
alter table topic_intelligence.entity_crosswalk enable row level security;
-- RLS deny-all.

-- -----------------------------------------------------------------------------
-- merge_map — the reversibility contract. One row per name-recovered link (the 12).
-- Records that gtm entity `merged_gtm_id` is the same real entity as the surviving
-- Empire row `surviving_id` (soft-merge / merge-map-first, ADR-4 §3). Reversible:
-- delete the entity_crosswalk row for merged_gtm_id + this merge_map row. NO existing
-- Empire row is mutated by a recovery (the gtm entity simply points at the survivor).
-- `evidence` (jsonb) holds de-identified match evidence (kind, normalized-name match,
-- gtm source_record_id, and whether it collides with a notion-matched sibling).
-- -----------------------------------------------------------------------------
create table if not exists topic_intelligence.merge_map (
  id             uuid        primary key default gen_random_uuid(),
  surviving_id   uuid        not null,           -- the Empire row kept (public.*.id)
  merged_gtm_id  uuid        not null,           -- the gtm entity recovered onto it
  empire_kind    text        not null,           -- 'company' | 'person'
  notion_page_id text,                            -- gtm entity's own (unmatched) notion id
  method         text        not null,           -- 'exact_name'
  confidence     numeric,
  evidence       jsonb,
  created_at     timestamptz not null default now()
);
-- one merge record per recovered gtm entity (idempotency + semantic uniqueness).
create unique index if not exists merge_map_merged_gtm_uq
  on topic_intelligence.merge_map(merged_gtm_id);
alter table topic_intelligence.merge_map enable row level security;
-- RLS deny-all.

commit;

-- Rollback (2a is reversible by construction — these are additive mapping tables):
--   drop table if exists topic_intelligence.merge_map;
--   drop table if exists topic_intelligence.entity_crosswalk;
--   drop table if exists topic_intelligence.topic_crosswalk;
-- (To also undo the additive public inserts, delete public.topic/public.company rows
--  whose source = 'increment_2a_gtm' — see scripts/build_2a_link.py.)
-- `public` schema DDL is untouched by this migration.
