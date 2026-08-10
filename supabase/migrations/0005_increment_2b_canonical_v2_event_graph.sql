-- 0005 — Increment 2b, part 1: canonical_v2 event-graph foundation + bounding-zone enums
-- Spec: supabase/specs/2b_relations_to_event_entity_mapping.md (§5, §8) · Linear: YED-130
--
-- WHAT: creates the parallel schema `canonical_v2` and its event-graph tables
--   (event, event_entity) with the "bounding-zone" CHECK enums (spec §8, check #2)
--   grounded in live-verified current values (2026-08-08: kind={market:17}, role={subject:20}).
-- WHY expand-contract: 2b builds the whole reconciled+recomputed graph in canonical_v2,
--   leaves `public` read-only, then ATOMIC-SWAPs. These constraints reach `public` only via
--   that swap — this migration NEVER mutates live `public`.
--
-- ⚠️ GATED: apply ONLY on a fresh Phantom Test Case DB (ytfzzsxcxxbejnowmkmk) during the
--   rehearsal, then on the Empire prod DB (oicikjyzmxqfomrrqkvf) at cutover. Never ad-hoc.
-- SECURITY: RLS deny-all (no policies) + no grants → fully private. The build applies as the
--   owner (psql); hub reads never touch canonical_v2 directly (they read signal_read, repointed
--   at swap). After the swap canonical_v2 *becomes* public and inherits public's existing grants.
--
-- Bounding zone (spec §8): a new tracked signal type = one deliberate enum edit here, not a
--   rogue string that could silently escape the compute's kind='attended' scope filter.

begin;

create schema if not exists canonical_v2;

-- event: temporal hyperedge, column-identical to public.event, + the kind bounding enum.
create table if not exists canonical_v2.event (
  id              uuid primary key default gen_random_uuid(),
  title           text not null,
  kind            text not null,
  event_date      timestamptz,
  description     text,
  url             text,
  source          text,
  confidence      numeric,
  notion_page_id  text,
  metadata        jsonb default '{}',
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  -- BOUNDING ZONE — full documented taxonomy (market-intel-spine.md), extended 2026-08-08:
  --   meetup lens: attended (the ONLY kind the topic-intelligence compute reads)
  --   trend-radar lens (happens-to-entities): market, funding, launch, exec_move,
  --     partnership (partnership announcements), adverse (adverse events)
  --   job lens: role_posted, application, interview
  constraint event_kind_enum check (kind in (
    'attended',
    'market', 'funding', 'launch', 'exec_move', 'partnership', 'adverse',
    'role_posted', 'application', 'interview'
  ))
);
create index if not exists cv2_event_kind_idx on canonical_v2.event (kind);
create index if not exists cv2_event_date_idx on canonical_v2.event (event_date);
create trigger cv2_event_set_updated_at before update on canonical_v2.event
  for each row execute function public.set_updated_at();

-- event_entity: the polymorphic hyperedge join, column-identical to public.event_entity,
-- + entity_type and role bounding enums.
create table if not exists canonical_v2.event_entity (
  id           uuid primary key default gen_random_uuid(),
  event_id     uuid not null references canonical_v2.event(id) on delete cascade,
  entity_type  text not null,
  entity_id    uuid not null,
  role         text,
  created_at   timestamptz default now(),
  unique (event_id, entity_type, entity_id, role),
  -- BOUNDING ZONE (spec §8):
  constraint event_entity_entity_type_enum check (entity_type in ('company', 'person', 'topic')),
  --   'subject'      — existing: how a market signal tags its one subject topic (live: 20 rows)
  --   'tagged_topic' — IRL meetup tags a covered topic (N per event); the compute reads THIS only
  --   speaker set    — speaker/host/panelist (image of gtm speaker_at/host_of/panelist_at)
  --   'attendee'     — participation; excluded from the speaker set
  constraint event_entity_role_enum check (role in (
    'subject', 'tagged_topic', 'speaker', 'host', 'panelist', 'attendee'
  ))
);
create index if not exists cv2_event_entity_event_idx  on canonical_v2.event_entity (event_id);
create index if not exists cv2_event_entity_entity_idx on canonical_v2.event_entity (entity_type, entity_id);

-- RLS deny-all: enable, add NO policies. anon/authenticated get nothing; owner (build) + BYPASSRLS
-- service_role still operate. No grants issued here (fully private until the swap).
alter table canonical_v2.event        enable row level security;
alter table canonical_v2.event_entity enable row level security;

commit;

-- Rollback (pre-swap): drop schema canonical_v2 cascade;  (public untouched by construction)
