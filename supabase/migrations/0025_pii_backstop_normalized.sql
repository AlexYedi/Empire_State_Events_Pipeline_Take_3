-- 0025_pii_backstop_normalized.sql
-- YED-392 + YED-324: the DB PII backstop reads contacts the way a human would decode them, and email
-- matching is Unicode-aware. The client guard (spine_client.py) gained the same two layers in the same PR.
-- =============================================================================
-- NOT APPLIED. Twin rehearsal + Alex dashboard apply required (invariant 2). Written by Claude in the
-- 11/18 unattended run; DDL is never applied by a session.
--
-- WHAT CHANGES
--   1. NEW public.no_contact_pii_v2(text): true unless the text, raw OR normalised, matches spine
--      EMAIL_RE / PHONE_RE, or the normalised copy holds a bare 10+ digit run outside URLs and ids.
--      Normalisation = pii_normalize.normalize() as far as SQL allows:
--        - @ / . entity and percent forms (&#64; &#x40; &commat; %40; &#46; &period; %2E)
--        - NFKC via normalize(t, NFKC)  (full-width ＠ and digits fold to ASCII; immutable on PG17)
--        - zero-width characters dropped; Unicode dashes -> '-'
--        - [at] (at) {at} / [dot] (dot) {dot}; 'x at y dot z'; spaced 'a @ b . c'
--      NOT covered in SQL (client layer only): general HTML entities and general percent-decoding.
--      VERSIONED like v1: never CREATE OR REPLACE; a change ships _v3.
--   2. public.assert_no_contact_pii() (person trigger, 0017): CREATE OR REPLACE with the Unicode-aware
--      EMAIL_RE. Body otherwise byte-identical to 0017 and to Part 1 of docs/adr/proposals/pii-db-check.sql.
--   3. NEW CHECKs on public.claim: claim_text_no_pii and claim_quote_no_pii, both
--      CHECK (public.no_contact_pii_v2(col)), added NOT VALID (new and updated rows only; no table scan,
--      SHARE ROW EXCLUSIVE lock held briefly). claim_text and quote had no DB-level PII check before.
--   v1 and its CHECKs (entity_alias.alias, sweep_query.template, claim.evidence, claim.freshness_reason)
--   are left alone; moving them to v2 is a follow-up once v2 has run clean.
--
-- WHY: YED-392 showed `dana [at] example [dot] com`, U+2011 hyphens, a bare 5551234567 and a full-width
-- ＠ all passing both the client guard and the DB functions; YED-324 showed a Cyrillic-script email passing
-- the ASCII-only EMAIL_RE. A flaw in any privacy layer is a defect even when an upstream gate catches it.
--
-- EVIDENCE (read-only, prod, PG 17.6, 2026-11-18):
--   - the new EMAIL_RE literal compiles under `~` and matched Python on 8 probes (Cyrillic, IDN, umlaut,
--     prose negatives); normalize(.., NFKC) folds 'ｊane＠example.com' to ASCII; normalize is immutable.
--   - shadow scan of every live claim / event / person / company / topic / documents row through the new
--     client guard: 0 new refusals (after exempting id / key / url / hash fields from the bare-digit rule,
--     which column-level CHECKs on claim_text / quote do not need).
--
-- PRE-APPLY REHEARSAL (run on the twin, then read-only on prod):
--   0. supabase/staging/0025_verify.sql step 1 must return ok = true on every row (its inline twin, run
--      read-only on prod with no DDL, returned 22/22 on 2026-11-18).
--   1. After apply: select count(*) from public.claim where not public.no_contact_pii_v2(claim_text)
--      or not public.no_contact_pii_v2(quote);  -- expect 0
--   2. If 0: alter table public.claim validate constraint claim_text_no_pii;
--            alter table public.claim validate constraint claim_quote_no_pii;
--   3. The 0017 / s04_d1 person probes still pass.
--
-- ROLLBACK: alter table public.claim drop constraint if exists claim_text_no_pii;
--           alter table public.claim drop constraint if exists claim_quote_no_pii;
--           drop function if exists public.no_contact_pii_v2(text);
--           then re-run 0017's assert_no_contact_pii() (ASCII EMAIL_RE) and revert spine_client.py EMAIL_RE
--           and docs/adr/proposals/pii-db-check.sql together (parity must hold on whatever prod runs).
--
-- IDEMPOTENT: v2 and the CHECKs are catalog-guarded; the person function is CREATE OR REPLACE.
-- =============================================================================

do $do$
begin
  if to_regprocedure('public.no_contact_pii_v2(text)') is null then
    execute $ddl$
      create function public.no_contact_pii_v2(t text)
      returns boolean
      language plpgsql
      immutable
      parallel safe
      set search_path = pg_catalog, pg_temp
      as $fn$
      declare
        -- Verbatim spine_client.py EMAIL_RE / PHONE_RE (check_pii_regex_parity.py compares every email_re /
        -- phone_re line in this file byte for byte).
        email_re text := $re$(?<![\w/])[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF._%+-]+@[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF-]+(?:\.[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF-]+)*\.[A-Za-z\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]{2,}(?![\w])$re$;
        phone_re text := $re$(?<![\w.+-])(?:1[\s.-])?(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])|(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)$re$;
        n text;
        d text;
      begin
        if t is null then
          return true;
        end if;
        n := coalesce(t, '');
        n := replace(replace(replace(replace(n, '&#64;', '@'), '&#x40;', '@'), '&commat;', '@'), '%40', '@');
        n := replace(replace(replace(replace(n, '&#46;', '.'), '&period;', '.'), '%2E', '.'), '%2e', '.');
        n := normalize(n, NFKC);
        n := regexp_replace(n, $re$[\u200B\u200C\u200D\u2060\uFEFF\u00AD\u180E]$re$, '', 'g');
        n := regexp_replace(n, $re$[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]$re$, '-', 'g');
        n := regexp_replace(n, $re$\s*[\[\(\{]\s*at\s*[\]\)\}]\s*$re$, '@', 'gi');
        n := regexp_replace(n, $re$\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*$re$, '.', 'gi');
        n := regexp_replace(n, $re$\y([a-z0-9._%+-]+)\s+at\s+([a-z0-9-]+)\s+dot\s+([a-z]{2,})\y$re$, '\1@\2.\3', 'gi');
        n := regexp_replace(n, $re$\s*@\s*$re$, '@', 'g');
        n := regexp_replace(n, $re$(?<=\w)\s+\.\s*(?=\w)$re$, '.', 'g');
        -- Bare 10+ digit runs count outside URLs and ids only (pii_normalize.PROTECTED).
        d := regexp_replace(n, $re$https?://[^\s<>\]\)]+|\y[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\y|\y[0-9a-fA-F]{32}\y$re$, ' ', 'g');
        return not (t ~ email_re or t ~ phone_re or n ~ email_re or n ~ phone_re or d ~ $re$(?<!\d)\d{10,}(?!\d)$re$);
      end
      $fn$
    $ddl$;
  end if;
end
$do$;
revoke all on function public.no_contact_pii_v2(text) from public, anon, authenticated;
grant execute on function public.no_contact_pii_v2(text) to service_role;
comment on function public.no_contact_pii_v2(text) is
  '0025 (YED-392/324): true unless the text, raw or normalised, matches spine EMAIL_RE / PHONE_RE or holds a bare 10+ digit run outside URLs/ids. Backs CHECKs. VERSIONED: never CREATE OR REPLACE.';

create or replace function public.assert_no_contact_pii()
returns trigger
language plpgsql
as $$
declare
  -- Verbatim spine_client.py EMAIL_RE.
  email_re text := $re$(?<![\w/])[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF._%+-]+@[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF-]+(?:\.[A-Za-z0-9\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF-]+)*\.[A-Za-z\u00C0-\u024F\u0370-\u03FF\u0400-\u052F\u0590-\u06FF\u0900-\u0DFF\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]{2,}(?![\w])$re$;
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

do $do$
begin
  if not exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass
                   and conname = 'claim_text_no_pii') then
    alter table public.claim add constraint claim_text_no_pii check (public.no_contact_pii_v2(claim_text)) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass
                   and conname = 'claim_quote_no_pii') then
    alter table public.claim add constraint claim_quote_no_pii check (public.no_contact_pii_v2(quote)) not valid;
  end if;
end
$do$;
