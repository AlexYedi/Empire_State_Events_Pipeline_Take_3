-- ============================================================================
-- PROPOSAL — PII Phase 2: Postgres CHECK/trigger backstop on `person`
-- ============================================================================
-- Status:   PROPOSAL ONLY — NOT APPLIED. (S-04, YED-183; docs lane.)
--           This file lives in docs/adr/proposals/, deliberately NOT in
--           supabase/migrations/. Per CLAUDE.md invariant 2, DDL is applied by
--           Alex from repo migrations only after a twin rehearsal on the twin
--           project. Nothing here runs until this file is (a) adopted and
--           (b) promoted to supabase/migrations/ by a human.
-- Repaired: 2026-11-01 per YED-279 (defects verified against the live
--           The-Prod-Brain project during the PR #235 review):
--             1. Part 2 refused every write to public.person because a
--                legacy, empty `email` column still exists there — it now
--                refuses only when a forbidden column is actually populated.
--             2. Part 3 aborted because canonical_v2.person does not exist —
--                the cv2 triggers are now guarded by a catalog check.
--             3. The shapes now carry spine EMAIL_RE/PHONE_RE verbatim (see
--                Part 1 note; the "Postgres has no lookaround" claim was
--                false).
--           Review follow-up (2026-11-01, PR #249 review): the phone shape is
--           pasted verbatim from spine's PHONE_RE in its PR #250 final form —
--           the A2 (?:1[\s.-])? leading-country-code prefix sits BEFORE the
--           +country group — and a CI parity check
--           (.claude/scripts/check_pii_regex_parity.py) extracts both
--           literals and fails on drift.
--           Finding the nulling-PATCH writer that keeps the legacy `email`
--           column alive and dropping the column remains the documented
--           PREREQUISITE for promotion — deliberately NOT handled here.
--           RESOLVED (2026-11-01, S-04 YED-183 D1): the writer was identified
--           — the one-time YED-81 email-null scrub
--           (`PATCH /person?email=not.is.null` -> {"email": null}, through the
--           guard; no standing code path) — see
--           docs/adr/proposals/person-email-nulling-writer-finding.md, and the
--           column drop is proposed as
--           supabase/migrations/0014_drop_legacy_person_email.sql (Alex-gated
--           promotion after twin rehearsal).
--           Twin-rehearsal instrument fix (2026-11-01, rehearse_s04_d1.py
--           bring-up): Part 1's refusal template read "…in person.%…" while
--           the argument is the qualified table (PL/pgSQL TG_ARGV is 0-based),
--           so refusals rendered "in person.public.person." — the Part-3
--           promise that the label names the table was broken. The template
--           now takes just the label: "…in public.person." / "…in
--           canonical_v2.person."
-- Builds on: ADR-9 ("Postgres CHECK/trigger on person as Phase-2 hardening"),
--            the regex shapes ratified in pii-regex-set.md, and the column
--            allowlist FORBIDDEN_COLUMNS in spine_client.py.
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
-- Mirrors EMAIL_RE / PHONE_RE from spine_client.py. Postgres ARE (the regex
-- dialect the `~` operator uses) supports lookahead/lookbehind and the other
-- constructs these shapes need, so the shapes are carried verbatim. The
-- earlier draft dropped the lookarounds on the false premise that Postgres
-- had no lookaround, and doubled its backslashes (`\\.`) — inside a
-- $$-quoted body under standard_conforming_strings the engine then saw a
-- literal backslash, not a dot. The literals below are dollar-quoted
-- ($re$…$re$) so they stay byte-identical to the Python source and no SQL
-- escape layer can drift them (YED-279 defect 3).
-- Parity is enforced, not assumed: .claude/scripts/check_pii_regex_parity.py
-- extracts both literals and fails CI on drift. The phone first alternative
-- carries A2's (?:1[\s.-])? leading-country-code prefix in its PR #250 final
-- form (before the +country group). One dialect nuance, immaterial for ASCII
-- contact PII: Python's \w/\d are Unicode-aware, ARE's follow the DB locale.
-- Known accepted trade-off carried over from pii-regex-set.md: separator-less
-- 10-digit numbers pass (A3).
-- YED-309 (2026-11-04): a third phone alternative now catches international
-- numbers written with separators (+44 20 7946 0958, +44 (0)20 7946 0958,
-- +33 1 99 00 12 34), closing pii-regex-set.md gap G1. It introduces
-- constructs the live shape does NOT use: a positive lookahead, and
-- lookaround nested inside it (a negative lookahead within the positive
-- one). What was verified, not assumed: (a) a Python-re vs Tcl-regexp
-- (Spencer ARE, the engine Postgres vendors) fuzz with lookbehinds
-- rewritten: 0 divergences on 115,907 strings (PR #277 review); (b) a
-- read-only probe on prod (Postgres 17, en_US.UTF-8): the full 3-alternative
-- pattern compiles under `~` and matched Python on 15 probes, NBSP
-- separators included. 0017's probe 0 re-runs (b) before apply, because
-- plpgsql holds the pattern as text and CREATE OR REPLACE never compiles
-- it. Prod still runs the pre-YED-309 shape until
-- supabase/migrations/0017_pii_backstop_intl_phone.sql is rehearsed and
-- applied; that migration carries this Part-1 function verbatim.

create or replace function public.assert_no_contact_pii()
returns trigger
language plpgsql
as $$
declare
  -- Verbatim spine_client.py EMAIL_RE.
  email_re text := $re$(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])$re$;
  -- Verbatim spine_client.py PHONE_RE (PR #250 final form: A2's
  -- leading-country-code prefix before the +country group; second
  -- alternative is the E.164 compact form; third is YED-309's
  -- international-with-separators form).
  phone_re text := $re$(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
begin
  -- Free-text columns on person (per the spine allowlist: professional-public
  -- identity only). name is scanned too — it is a string someone typed.
  if coalesce(new.name, '')          ~ email_re
  or coalesce(new.title, '')         ~ email_re
  or coalesce(new.bio, '')           ~ email_re
  or coalesce(new.role_context, '')  ~ email_re
  or coalesce(new.metadata::text, '{}') ~ email_re
  or coalesce(new.name, '')          ~ phone_re
  or coalesce(new.title, '')         ~ phone_re
  or coalesce(new.bio, '')           ~ phone_re
  or coalesce(new.role_context, '')  ~ phone_re
  or coalesce(new.metadata::text, '{}') ~ phone_re
  then
    raise exception 'ADR-9 tier-2 violation: contact PII (email/phone pattern) in %. Contact detail lives in HubSpot; see CLAUDE.md invariant 1.',
      tg_argv[0];  -- PL/pgSQL TG_ARGV is 0-based: the CREATE TRIGGER label arg.
  end if;
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Part 2 — trigger function: refuse writes that POPULATE forbidden columns
-- ---------------------------------------------------------------------------
-- The DB-side twin of spine_client.py's FORBIDDEN_COLUMNS. The first draft
-- refused every write the moment a forbidden column merely existed; on the
-- live project public.person still carries a legacy, empty `email` column
-- (YED-279 defect 1), so that variant blocked all writes. It now inspects the
-- row being written and raises only when a forbidden column carries a value —
-- the actual ADR-9 harm is contact PII landing in the graph, not column
-- existence. A future ALTER that re-adds email/phone onto person stays
-- covered: any write that populates it fails loudly with an ADR-9 message.
-- Dropping the legacy column (after finding the nulling-PATCH writer that
-- keeps it populated-null) is the documented promotion prerequisite,
-- tracked separately from this file.

create or replace function public.assert_no_pii_columns()
returns trigger
language plpgsql
as $$
declare
  bad text;
begin
  select string_agg(key, ', ' order by key)
    into bad
    from jsonb_each(to_jsonb(new))
    where lower(key) in
        ('email', 'e_mail', 'phone', 'phone_number', 'mobile', 'telephone')
      and value is not null
      and value <> 'null'::jsonb
      and value::text <> '""';
  if bad is not null then
    raise exception 'ADR-9 tier-2 violation: forbidden contact-PII column(s) % populated on %.%. Contact detail lives in HubSpot; see CLAUDE.md invariant 1.',
      bad, tg_table_schema, tg_table_name;
  end if;
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Part 3 — attach to both person tables (public + the canonical_v2 copy,
-- which is created via `like public.person` in migration 0006 and does not
-- inherit triggers). The label argument names the table in refusals.
-- The cv2 block is guarded: canonical_v2.person does not exist on every
-- environment yet, and an unguarded reference aborted the whole migration
-- (YED-279 defect 2). If cv2 is created after this runs, re-run the block —
-- or wire these triggers into migration 0006 at promotion time.
-- ---------------------------------------------------------------------------

drop trigger if exists person_no_contact_pii on public.person;
create trigger person_no_contact_pii
  before insert or update on public.person
  for each row execute function public.assert_no_contact_pii('public.person');

drop trigger if exists person_no_pii_columns on public.person;
create trigger person_no_pii_columns
  before insert or update on public.person
  for each row execute function public.assert_no_pii_columns();

do $$
begin
  if exists (
    select 1 from information_schema.tables
    where table_schema = 'canonical_v2'
      and table_name   = 'person'
  ) then
    drop trigger if exists cv2_person_no_contact_pii on canonical_v2.person;
    create trigger cv2_person_no_contact_pii
      before insert or update on canonical_v2.person
      for each row execute function public.assert_no_contact_pii('canonical_v2.person');

    drop trigger if exists cv2_person_no_pii_columns on canonical_v2.person;
    create trigger cv2_person_no_pii_columns
      before insert or update on canonical_v2.person
      for each row execute function public.assert_no_pii_columns();
  else
    raise notice 'canonical_v2.person not found — skipping cv2 triggers (re-run this block after migration 0006).';
  end if;
end;
$$;

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
--              ~ $re$(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])$re$;
--      Already verified against the live The-Prod-Brain during the PR #235
--      review of YED-279: 0 existing person rows match either the email or
--      the phone pattern — re-confirm on the twin at rehearsal time.
--   3. Confirm the nulling-update path still passes: a PATCH that sets
--      metadata/email fields to null contains no pattern and clears both the
--      scan and the populated-column check.
--   4. Promotion prerequisite (separate task): find the nulling-PATCH writer
--      that keeps the legacy public.person `email` column alive, then drop
--      the column. Part 2 tolerates its empty presence but the column has no
--      business on the spine allowlist.
-- ============================================================================
