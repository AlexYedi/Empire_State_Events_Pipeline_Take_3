-- 0017_pii_backstop_intl_phone.sql
-- YED-309: the PII DB backstop catches international phone numbers written
-- with separators (+44 20 7946 0958, +44 (0)20 7946 0958, +33 1 23 45 67 89).
-- =============================================================================
-- NOT APPLIED. Twin rehearsal + Alex dashboard apply required (invariant 2).
-- Migration number 0017 is PROVISIONAL: 0016 is the trends session's open
-- PR #274 (0016_mi_semantic_layer.sql). Renumber if that lands differently.
--
-- WHAT CHANGES: ONE function body, public.assert_no_contact_pii() — its
-- phone_re gains a third alternative. Nothing else: assert_no_pii_columns()
-- has no regex and is untouched; the four triggers (person_no_contact_pii,
-- cv2_person_no_contact_pii and the two *_no_pii_columns) reference the
-- function by name, so CREATE OR REPLACE swaps the body under them with no
-- trigger DDL. The function below is Part 1 of
-- docs/adr/proposals/pii-db-check.sql, verbatim; that file is what
-- .claude/scripts/check_pii_regex_parity.py compares against spine_client.py
-- PHONE_RE / EMAIL_RE byte-for-byte.
--
-- WHY: prod has carried this backstop since 2026-11-02 (pasted from
-- pii-db-check.sql). Its phone shape caught only US formats and compact
-- E.164, so a dashboard edit or guard-bypassing writer could still land a
-- formatted non-US number in person free-text. Bulk feed ingestion widens
-- that surface. The new alternative:
--   \+ CC(1-3 digits) [sep | optional (0) trunk] then 2-5 digit groups split
--   by space/dot/dash; a lookahead counts 7-15 digits across the whole run;
--   the tail guard refuses to stop before another sep+digit.
-- Separator-less 10-digit numbers stay OUT (decision A3, YED-183).
--
-- ENGINE NOTE: every construct here — (?<!…) lookbehind, (?=…)/(?!…)
-- lookahead, {m,n} bounds, [\s.-] classes — is ARE syntax Postgres accepts
-- (lookbehind since 9.6; the live shape already uses it). Pre-merge, the
-- pattern minus its lookbehinds was run through Tcl's regexp (Spencer ARE,
-- the engine Postgres vendors) and Python re on 33 TP/TN strings: 0
-- divergences. The twin rehearsal is the real-engine proof.
--
-- IDEMPOTENT: CREATE OR REPLACE FUNCTION; a re-run is a no-op.
--
-- PRE-PROMOTION REHEARSAL PROBES (twin first, then read-only on prod):
--   1. Existing rows that the NEW shape would now refuse on UPDATE:
--        select id from public.person
--        where coalesce(name,'') || ' ' || coalesce(title,'') || ' ' ||
--              coalesce(bio,'') || ' ' || coalesce(role_context,'') || ' ' ||
--              coalesce(metadata::text,'{}')
--              ~ $re$(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
--      expect 0 rows. Any hit is either real contact PII to scrub (through
--      spine_write.py) or a false positive to report back on YED-309 before
--      promotion — a hit blocks updates to that row once 0017 is live.
--   2. Refusal checks after apply: an UPDATE setting bio to each of
--      '+44 20 7946 0958', '+44 (0)20 7946 0958', '+33 6 39 98 12 34' raises
--      'ADR-9 tier-2 violation…'; '2026-11-04', '+12.50', '+3 4 5',
--      '192.168.1.10' pass. (staging/s04_d1_verify.sql does not yet carry
--      these rows; extend it or run them by hand on the twin.)
--   3. The existing s04_d1_verify.sql checks still PASS (US / E.164 / email
--      refused; clean + nulling writes pass).
--
-- ROLLBACK (the twin-rehearsal leg Alex runs first): re-run the pre-YED-309
-- body — identical to the function below except phone_re ends after the
-- E.164 alternative:
--   create or replace function public.assert_no_contact_pii()
--   returns trigger language plpgsql as $$
--   declare
--     email_re text := $re$(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])$re$;
--     phone_re text := $re$(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])$re$;
--   begin
--     (body unchanged — copy the begin…end block below)
--   end;
--   $$;
-- and revert docs/adr/proposals/pii-db-check.sql + spine_client.py PHONE_RE
-- together (parity must hold on whatever prod runs).
-- =============================================================================

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
