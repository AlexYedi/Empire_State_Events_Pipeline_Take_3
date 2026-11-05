-- 0017_pii_backstop_intl_phone.sql
-- YED-309: the PII DB backstop catches international phone numbers written
-- with separators (+44 20 7946 0958, +44 (0)20 7946 0958, +33 1 99 00 12 34).
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
-- ENGINE NOTE: the new alternative introduces constructs the live shape does
-- NOT use: a positive lookahead (?=…), and lookaround nested inside it (a
-- negative lookahead within the positive one). What was verified, not
-- assumed:
--   (a) Python re vs Tcl regexp (Spencer ARE, the engine Postgres vendors),
--       lookbehinds rewritten since Tcl lacks them: 0 divergences on 115,907
--       fuzzed strings (PR #277 review).
--   (b) Read-only on prod (Postgres 17, datctype en_US.UTF-8, 2026-11-04):
--       the full 3-alternative pattern compiles under `~` and matched Python
--       on 15 probes, NBSP separators included — probe 0 below.
--   Prod note: canonical_v2.person does NOT exist on prod (probe 1's cv2
--   leg is a no-op there; the twin may have it).
--
-- IDEMPOTENT: CREATE OR REPLACE FUNCTION; a re-run is a no-op.
--
-- PRE-PROMOTION REHEARSAL PROBES (all read-only):
--   0. COMPILE + BEHAVIOUR CHECK — run on the twin AND read-only on prod
--      BEFORE applying. Any row with ok = false (or a regex compile error)
--      means DO NOT APPLY. Why this is needed: plpgsql holds phone_re as a
--      text literal, so CREATE OR REPLACE succeeds even if the pattern is
--      invalid ARE; the error would surface only on the next person write,
--      as a failed trigger on every insert/update.
--        select s, expected, s ~ p as got, (s ~ p) = expected as ok
--        from (values
--          ('+44 20 7946 0958',                  true),
--          ('+44-20-7946-0958',                  true),
--          ('+49 (0)30 1234 5678',               true),
--          ('call +33 1 99 00 12 34 today',      true),
--          ('555-123-4567',                      true),
--          ('+15551234567',                      true),
--          ('+44' || chr(160) || '20 7946 0958', true),   -- NBSP separator
--          ('revenue +12 345 678 EUR',           true),   -- known false positive
--          ('+1 234 567 890 shares',             true),   -- known false positive
--          ('+44 20',                            false),
--          ('+1.2.3.4.5.6.7',                    false),
--          ('2026-11-04 12:30:45',               false),
--          ('v2.3.4',                            false),
--          ('+40.7128 -74.0060',                 false),
--          ('x',                                 false)
--        ) v(s, expected),
--        (select $re$(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$ as p) r
--        order by ok, s;
--      expect 15 rows, all ok = true.
--   1. Existing rows that the NEW alternative would now refuse on UPDATE,
--      on both person tables (cv2 leg catalog-guarded, like Part 3 of
--      pii-db-check.sql):
--        select id from public.person
--        where coalesce(name,'') || ' ' || coalesce(title,'') || ' ' ||
--              coalesce(bio,'') || ' ' || coalesce(role_context,'') || ' ' ||
--              coalesce(metadata::text,'{}')
--              ~ $re$(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
--        do $$
--        declare n bigint;
--        begin
--          if exists (select 1 from information_schema.tables
--                     where table_schema = 'canonical_v2' and table_name = 'person') then
--            select count(*) into n from canonical_v2.person
--            where coalesce(name,'') || ' ' || coalesce(title,'') || ' ' ||
--                  coalesce(bio,'') || ' ' || coalesce(role_context,'') || ' ' ||
--                  coalesce(metadata::text,'{}')
--                  ~ $re$(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
--            raise notice 'canonical_v2.person rows matching the new alternative: % (expect 0)', n;
--          else
--            raise notice 'canonical_v2.person not found — cv2 leg skipped (expected on prod).';
--          end if;
--        end;
--        $$;
--      expect 0 rows / 0 count. Any hit is either real contact PII to scrub
--      (through spine_write.py) or a false positive to report back on YED-309
--      before promotion — a hit blocks updates to that row once 0017 is live.
--      (Prod, 2026-11-04, read-only: alternative 3 alone had 0 hits on
--      public.person — 506 rows as to_jsonb — and on claim, documents,
--      company, event, topic.)
--   2. Refusal checks after apply: an UPDATE setting bio to each of
--      '+44 20 7946 0958', '+44 (0)20 7946 0958', '+33 6 39 98 12 34' raises
--      'ADR-9 tier-2 violation…'; '2026-11-04', '+12.50', '+3 4 5',
--      '192.168.1.10' pass. (staging/s04_d1_verify.sql does not yet carry
--      these rows; extend it or run them by hand on the twin.)
--   3. The existing s04_d1_verify.sql checks still PASS (US / E.164 / email
--      refused; clean + nulling writes pass).
--
-- ROLLBACK (the twin-rehearsal leg Alex runs first): re-run the pre-YED-309
-- function, which is what prod runs today. Get it verbatim with
--   git show 622a221:docs/adr/proposals/pii-db-check.sql
-- and paste ONLY its Part 1 — the `create or replace function
-- public.assert_no_contact_pii()` statement, from that line through its
-- closing `$$;`. Do not paste Parts 2–3 (they would re-run trigger DDL).
-- Its phone_re ends after the E.164 alternative:
--   ...|(?<![\w.])\+\d{10,15}(?![\w])
-- Then revert docs/adr/proposals/pii-db-check.sql + spine_client.py PHONE_RE
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
