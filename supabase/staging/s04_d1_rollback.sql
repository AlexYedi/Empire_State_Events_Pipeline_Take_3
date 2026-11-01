-- =====================================================================
-- S-04 D1 ROLLBACK — undoes pii-db-check.sql + 0014_drop_legacy_person_email.sql
--
-- Valid indefinitely:
--   * it only DROPS what the backstop added (4 triggers, 2 functions);
--   * it re-adds the dropped legacy email column as an EMPTY text column —
--     the values were scrubbed by the one-time YED-81 nulling PATCH, so an
--     empty column is exactly the pre-rehearsal state (nothing to restore);
--   * rows in pre-existing tables are untouched.
--
-- Rehearsal proof obligation (rehearse_s04_d1.py gate 7): the schema
-- fingerprint after this rollback equals the pre-rehearsal fingerprint and
-- every person count matches — the rollback is PROVEN only if that holds.
-- (Column re-add lands at the end of the column order; the fingerprint is
-- order-insensitive by design, so pre/post fingerprints still match.)
--
-- Run on the twin only. On prod, rollback is Alex's dashboard paste
-- (CLAUDE.md invariant 2).
-- =====================================================================
begin;

-- The backstop (pii-db-check.sql), in its own documented rollback shape:
drop trigger if exists person_no_contact_pii    on public.person;
drop trigger if exists person_no_pii_columns    on public.person;
drop trigger if exists cv2_person_no_contact_pii on canonical_v2.person;
drop trigger if exists cv2_person_no_pii_columns on canonical_v2.person;
drop function if exists public.assert_no_contact_pii();
drop function if exists public.assert_no_pii_columns();

-- The column drop (0014), reversed as an empty column on both person tables.
-- Catalog-guarded on canonical_v2 — same pattern as 0014 itself.
alter table public.person add column if not exists email text;

do $rollback$
begin
  if exists (
    select 1 from information_schema.tables
    where table_schema = 'canonical_v2'
      and table_name   = 'person'
  ) then
    alter table canonical_v2.person add column if not exists email text;
  else
    raise notice 'canonical_v2.person not found — skipping its email re-add (nothing was dropped there).';
  end if;
end;
$rollback$;

commit;
