-- 0006 — Increment 2b, part 2: canonical_v2 entity + theme dimension (AC2b.2)
-- Spec: supabase/specs/2b_relations_to_event_entity_mapping.md · Linear: YED-130
--
-- WHAT: completes the canonical_v2 graph structure — the entity tables (company, person,
--   topic) mirrored from public, plus the THEME dimension (topic_cluster + topic.cluster_id)
--   that the topic-intelligence compute rolls up to. Data is loaded by
--   build_2b_canonical_v2.py (copy public → canonical_v2; carry the 30 curated clusters +
--   assignments from the Increment-1 topic_intelligence snapshot).
--
-- WHY LIKE public.*: these tables are column-identical to public — copy the structure so it
--   can never drift, then add ONLY the new theme-membership columns. (LIKE copies
--   columns/defaults/checks/indexes but NOT foreign keys or triggers — re-added below.)
--
-- ⚠️ GATED: canonical_v2 only. Applied on a fresh Phantom Test Case DB during the rehearsal,
--   then on the Empire prod DB at cutover via the atomic swap. NEVER mutates live public.
-- SECURITY: RLS deny-all, no grants (fully private until the swap).

begin;

-- THEME dimension: the 30 curated clusters. Structure carried verbatim from the Increment-1
-- snapshot (topic_intelligence.topic_cluster), so cluster_id UUIDs stay stable identity.
create table if not exists canonical_v2.topic_cluster
  (like topic_intelligence.topic_cluster including all);
alter table canonical_v2.topic_cluster
  add constraint cv2_topic_cluster_parent_fk
  foreign key (parent_cluster_id) references canonical_v2.topic_cluster(cluster_id);
alter table canonical_v2.topic_cluster enable row level security;

-- ENTITY + atomic-topic tables: structurally identical to public → copy structure.
create table if not exists canonical_v2.company (like public.company including all);
create table if not exists canonical_v2.person  (like public.person  including all);
create table if not exists canonical_v2.topic   (like public.topic   including all);

-- Re-add the person → company FK (LIKE does not copy foreign keys).
alter table canonical_v2.person
  add constraint cv2_person_company_fk
  foreign key (company_id) references canonical_v2.company(id) on delete set null;

-- THEME membership on topic (public.topic has none; this is the 2b addition, AC2b.2).
-- Mirrors the signal_06 columns carried on topic_intelligence.topics.
alter table canonical_v2.topic add column if not exists cluster_id uuid
  references canonical_v2.topic_cluster(cluster_id) on delete no action;
alter table canonical_v2.topic add column if not exists cluster_assignment_confidence numeric(4,3);
alter table canonical_v2.topic add column if not exists cluster_assigned_by text;
alter table canonical_v2.topic
  add constraint cv2_topic_cluster_confidence_range
  check (cluster_assignment_confidence is null
         or (cluster_assignment_confidence >= 0 and cluster_assignment_confidence <= 1));
create index if not exists cv2_topic_cluster_idx
  on canonical_v2.topic(cluster_id) where cluster_id is not null;

-- updated_at triggers (LIKE does not copy triggers) — parity with public.
create trigger cv2_company_set_updated_at before update on canonical_v2.company
  for each row execute function public.set_updated_at();
create trigger cv2_person_set_updated_at before update on canonical_v2.person
  for each row execute function public.set_updated_at();
create trigger cv2_topic_set_updated_at before update on canonical_v2.topic
  for each row execute function public.set_updated_at();

alter table canonical_v2.company enable row level security;
alter table canonical_v2.person  enable row level security;
alter table canonical_v2.topic   enable row level security;

commit;

-- Rollback (pre-swap): drop schema canonical_v2 cascade;  (public untouched by construction)
