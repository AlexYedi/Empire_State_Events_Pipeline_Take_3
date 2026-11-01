-- 0014_drop_legacy_person_email.sql
-- S-04 (YED-183) D1: drop the legacy, empty public.person.email column — the
-- documented promotion prerequisite for the PII Phase-2 DB backstop
-- (docs/adr/proposals/pii-db-check.sql, prerequisite item 4).
-- =============================================================================
-- NOT APPLIED YET. Per CLAUDE.md invariant 2, DDL is applied by Alex from repo
-- migrations only after a twin rehearsal on the twin project. This file only
-- proposes the change; execution happens at the Alex-gated promotion step.
--
-- WHY (the writer finding, 2026-11-01 — full hunt record in
-- docs/adr/proposals/person-email-nulling-writer-finding.md):
--   The nulling-PATCH writer is the one-time YED-81 email-null migration:
--   a manual `PATCH /person?email=not.is.null` -> {"email": null} run when
--   ADR-9 was accepted (docs/archive/proposals/yed-81-sec-pii-guardrails.md,
--   Sketch item 4; decision log 2026-09-13: "the migration runs through the
--   guard"). It scrubbed every value but nobody ever dropped the column, so
--   public.person still carries a legacy, empty `email` column. That column's
--   mere existence is why Part 2 of pii-db-check.sql as first drafted refused
--   every write to public.person (YED-279 defect 1). No standing script in the
--   repo reads or writes person.email — the last writer of values
--   (backfill_people.py) was pruned in 8b79a12, and the nulling PATCH was a
--   one-time operational action. With the writer retired and the values gone,
--   the column has no business on the spine (ADR-9 tier 2: professional-public
--   identity only; contact detail lives in HubSpot) and nothing reads it.
--
-- SCOPE — both person tables, not just public:
--   canonical_v2.person was created as `like public.person including all`
--   (migration 0006) and therefore inherited the same legacy `email` column.
--   The Phase-2 backstop guards both tables (pii-db-check.sql Part 3), so the
--   drop covers both. The canonical_v2 leg is catalog-guarded: on any
--   environment where that table does not exist the block is skipped (same
--   guard pattern as pii-db-check.sql Part 3, per YED-279 defect 2).
--
-- SAFETY:
--   - `if exists` guards make this idempotent (a re-run after a partial
--     rehearsal apply is a no-op, not an error).
--   - No data migration needed: the YED-81 nulling PATCH left the column
--     empty on every row (verified 0 populated rows during the PR #235
--     review of YED-279; re-confirm on the twin at rehearsal time — probe
--     below). Nothing in the repo reads the column (grep across .claude/,
--     supabase/, docs/specs/ on 2026-11-01: only guard selftests and the
--     YED-81 history).
--   - Dropping a column is reversible only by re-adding it (data lost) — the
--     rehearsal probe below MUST show 0 populated rows before promotion.
--
-- PRE-PROMOTION REHEARSAL PROBE (run on the twin first):
--   select count(*) from public.person where email is not null;
--   -- expect 0. If it is not 0, STOP: re-run the YED-81 export + nulling
--   -- PATCH (through spine_write.py, which goes through the ADR-9 guard)
--   -- before promoting this migration.
--
-- ROLLBACK (the twin-rehearsal leg Alex runs first):
--   alter table public.person         add column email text;
--   alter table canonical_v2.person   add column email text;  -- if that table exists
--   (Values are NOT restored — the column was already empty; the YED-81 export
--    to the gitignored file is the only record of pre-scrub values.)

alter table public.person drop column if exists email;

do $$
begin
  if exists (
    select 1 from information_schema.tables
    where table_schema = 'canonical_v2'
      and table_name   = 'person'
  ) then
    alter table canonical_v2.person drop column if exists email;
  else
    raise notice 'canonical_v2.person not found — skipping its email drop (column would only exist there if the table predates this migration).';
  end if;
end;
$$;

-- Post-condition (assert at rehearsal): information_schema.columns has no
-- `email` row for either person table, and a plain person UPDATE still passes
-- the Phase-2 triggers (pii-db-check.sql rehearsal check 3).
