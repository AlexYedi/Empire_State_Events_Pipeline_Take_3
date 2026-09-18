-- =====================================================================
-- S1a ROLLBACK — undoes 0009_substrate_s1a_additive.sql
--
-- Valid indefinitely, not just "before data lands" (review finding 1b):
--   * it only DROPS what S1a added (tables, columns, indexes, one CHECK);
--   * it deliberately does NOT re-narrow the three widenings —
--       event_kind_enum still admits 'published'
--       documents_source_type_check still admits our artifact types
--       documents.blob_key stays nullable
--     Re-narrowing would fail the moment any new-type row exists. Leaving a
--     constraint wider than before rejects nothing, so it is safe to keep.
--   * rows in pre-existing tables are untouched (documents rows for our
--     artifacts survive as plain documents; 'published' events survive).
--
-- Proven on Phantom-Test-Case by supabase/scripts/rehearse_s1a.py: the
-- schema fingerprint after rollback equals the pre-S1a fingerprint (the three
-- widenings are excluded from the fingerprint by design) and all counts match.
-- =====================================================================
begin;

drop table if exists public.claim_usage;
drop table if exists public.artifact_outcome;
drop table if exists public.claim_relation;
drop table if exists public.claim_entity;
drop table if exists public.claim;
drop table if exists public.document_entity;

drop index if exists public.documents_external_ref_version_uq;
drop index if exists public.documents_external_ref_current_uq;
drop index if exists public.documents_event_idx;
drop index if exists public.documents_source_type_idx;

alter table public.documents drop constraint if exists documents_visibility_check;
alter table public.documents
  drop column if exists event_id,
  drop column if exists external_ref,
  drop column if exists doc_date,
  drop column if exists version,
  drop column if exists supersedes_id,
  drop column if exists is_current,
  drop column if exists produced_by,
  drop column if exists visibility,
  drop column if exists metadata;

comment on table public.doc_claims is null;

commit;
