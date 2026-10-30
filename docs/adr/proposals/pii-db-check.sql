-- ============================================================================
-- PROPOSAL — PII Phase 2: Postgres CHECK/trigger backstop on `person`
-- ============================================================================
-- Status:   PROPOSAL ONLY — NOT APPLIED. (S-04, YED-183; docs lane.)
--           This file lives in docs/adr/proposals/, deliberately NOT in
--           supabase/migrations/. Per CLAUDE.md invariant 2, DDL is applied by
--           Alex from repo migrations only after a twin rehearsal on the twin
--           project. Nothing here runs until this file is (a) adopted and
--           (b) promoted to supabase/migrations/ by a human.
-- Builds on: ADR-9 ("Postgres CHECK/trigger on person as Phase-2 hardening"),
--            the regex shapes ratified-or-proposed in pii-regex-set.md, and
--            the column allowlist FORBIDDEN_COLUMNS in spine_client.py.
-- Scope:    public.person and canonical_v2.person only. claim free-text
--           scanning stays Python-side (proposal doc pii-regex-set.md covers
--           why these same shapes, not a second dialect).
--
-- WHY A DB BACKSTOP AT ALL
--   The Python guard (spine_client.guard) is the single write chokepoint, but
--   it protects only writers that use it. A second enforcement layer inside
--   Postgres means a leaked service key, a dashboard edit, or a future writer
--   that bypasses the guard still cannot commit contact PII into person rows.
--   Defense in depth, not a replacement: the Python guard stays the primary
--   control (its refusal names the fix; the DB backstop just fails the write).

-- ---------------------------------------------------------------------------
-- Part 1 — trigger function: scan person free-text columns, refuse contact PII
-- ---------------------------------------------------------------------------
-- Mirrors EMAIL_RE / PHONE_RE from spine_client.py. Postgres has no lookahead/
-- lookbehind, so the boundary guards are dropped; the "separators or +"
-- phone requirement is kept so bare 10-digit integers (timestamps, ids) still
-- never trip it. Known accepted trade-off carried over from pii-regex-set.md:
-- separator-less 10-digit numbers and non-US formatted internationals pass.

create or replace function public.assert_no_contact_pii()
returns trigger
language plpgsql
as $$
begin
  -- Free-text columns on person (per the spine allowlist: professional-public
  -- identity only). name is scanned too — it is a string someone typed.
  if coalesce(new.name, '')          ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
  or coalesce(new.title, '')         ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
  or coalesce(new.bio, '')           ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
  or coalesce(new.role_context, '')  ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
  or coalesce(new.metadata::text, '{}') ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
  or coalesce(new.name, '')          ~ '(\+[0-9]{1,3}[[:space:].-]?)?(\([0-9]{3}\)|[0-9]{3})[[:space:].-][0-9]{3}[[:space:].-][0-9]{4}'
  or coalesce(new.title, '')         ~ '(\+[0-9]{1,3}[[:space:].-]?)?(\([0-9]{3}\)|[0-9]{3})[[:space:].-][0-9]{3}[[:space:].-][0-9]{4}'
  or coalesce(new.bio, '')           ~ '(\+[0-9]{1,3}[[:space:].-]?)?(\([0-9]{3}\)|[0-9]{3})[[:space:].-][0-9]{3}[[:space:].-][0-9]{4}'
  or coalesce(new.role_context, '')  ~ '(\+[0-9]{1,3}[[:space:].-]?)?(\([0-9]{3}\)|[0-9]{3})[[:space:].-][0-9]{3}[[:space:].-][0-9]{4}'
  or coalesce(new.metadata::text, '{}') ~ '(\+[0-9]{1,3}[[:space:].-]?)?(\([0-9]{3}\)|[0-9]{3})[[:space:].-][0-9]{3}[[:space:].-][0-9]{4}'
  then
    raise exception 'ADR-9 tier-2 violation: contact PII (email/phone pattern) in person.%. Contact detail lives in HubSpot; see CLAUDE.md invariant 1.',
      tg_argv[0];
  end if;
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Part 2 — trigger function: DDL watch on forbidden columns
-- ---------------------------------------------------------------------------
-- The DB-side twin of spine_client.py's FORBIDDEN_COLUMNS. Checked at write
-- time rather than DDL time because a CHECK cannot introspect column names;
-- if someone later ALTERs an email/phone column onto person, every subsequent
-- write fails loudly instead of the data flowing silently.

create or replace function public.assert_no_pii_columns()
returns trigger
language plpgsql
as $$
declare
  bad text;
begin
  select string_agg(column_name, ', ')
    into bad
    from information_schema.columns
    where table_schema = tg_table_schema
      and table_name   = tg_table_name
      and lower(column_name) in
        ('email', 'e_mail', 'phone', 'phone_number', 'mobile', 'telephone');
  if bad is not null then
    raise exception 'ADR-9 tier-2 violation: forbidden contact-PII column(s) % exist on %.%. Writes refuse until they are dropped.',
      bad, tg_table_schema, tg_table_name;
  end if;
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Part 3 — attach to both person tables (public + the canonical_v2 copy,
-- which is created via `like public.person` in migration 0006 and does not
-- inherit triggers). The label argument names the table in refusals.
-- ---------------------------------------------------------------------------

drop trigger if exists person_no_contact_pii on public.person;
create trigger person_no_contact_pii
  before insert or update on public.person
  for each row execute function public.assert_no_contact_pii('public.person');

drop trigger if exists person_no_pii_columns on public.person;
create trigger person_no_pii_columns
  before insert or update on public.person
  for each row execute function public.assert_no_pii_columns();

drop trigger if exists cv2_person_no_contact_pii on canonical_v2.person;
create trigger cv2_person_no_contact_pii
  before insert or update on canonical_v2.person
  for each row execute function public.assert_no_contact_pii('canonical_v2.person');

drop trigger if exists cv2_person_no_pii_columns on canonical_v2.person;
create trigger cv2_person_no_pii_columns
  before insert or update on canonical_v2.person
  for each row execute function public.assert_no_pii_columns();

-- A plain CHECK constraint (e.g. `check (bio !~ …)`) was considered and
-- rejected for the scan: it cannot cover the `metadata` jsonb, cannot be
-- silenced on the nulling-update path the Python guard explicitly allows
-- (`email: null` PATCH passes today), and a failed CHECK aborts with a
-- number instead of an ADR-9 explanation. Triggers give named, fixable errors.

-- ---------------------------------------------------------------------------
-- Rollback (the twin-rehearsal leg Alex runs first):
--   drop trigger if exists person_no_contact_pii  on public.person;
--   drop trigger if exists person_no_pii_columns  on public.person;
--   drop trigger if exists cv2_person_no_contact_pii on canonical_v2.person;
--   drop trigger if exists cv2_person_no_pii_columns on canonical_v2.person;
--   drop function if exists public.assert_no_contact_pii();
--   drop function if exists public.assert_no_pii_columns();
--
-- Pre-application rehearsal checks (run on the twin before promoting to
-- supabase/migrations/):
--   1. Confirm actual column names on public.person match the allowlist
--      assumed here (name, title, company_id, linkedin_url, bio,
--      role_context, metadata, …). The DDL for public.person predates the
--      migration history — verify live, do not assume.
--   2. Confirm existing rows would not fail on UPDATE (triggers fire on
--      update too; a legacy dirty row blocks only its own updates).
--      Suggested probe on the twin:
--        select id from public.person
--        where coalesce(bio,'') || coalesce(role_context,'')
--              ~ '[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}';
--   3. Confirm the nulling-update path still passes: a PATCH that sets
--      metadata/email fields to null contains no pattern and clears the scan.
-- ============================================================================
