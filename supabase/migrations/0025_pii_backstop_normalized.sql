-- 0025_pii_backstop_normalized.sql
-- YED-392 + YED-324 (reworked 2026-11-20, approved plan): the DB PII backstop reads the CANONICAL form of text, and
-- every free-text site that had a v1 check, plus claim_text / quote and the person trigger, goes through it.
-- =============================================================================
-- NOT APPLIED. Twin rehearsal + Alex dashboard apply required (invariant 2). DDL is never applied by a session.
--
-- LAYER CONTRACTS (each layer is tested against its own contract, alone: fixtures/pii_probe_corpus.jsonl,
-- .claude/scripts/check_pii_corpus.py; --emit-sql prints a DDL-free SELECT of this function's expression):
--   L3 (this file) promises the canonical form ONLY: the raw text, and the text after
--       1. stripping every Unicode Default_Ignorable_Code_Point (ign_re: generated from the Unicode definition by
--          pii_normalize.IGNORABLE_CLASS; the parity check proves it covers the Python set),
--       1b. reading the JSON escapes \n \t \r as a space (esc_re; YED-318: jsonb::text writes a newline inside a
--          value as the two characters \n, which left `call\n555-123-0100` with no separator before the number),
--       2. normalize(.., NFKC)  (full-width ＠ and digits fold to ASCII; immutable on PG17),
--       3. folding the UTS-46 dots U+3002 U+FF0E U+FF61 to '.',
--       4. folding the CLOSED set of '@' spellings (at_re: &#64; &#064; &#x40; &#X0040; &commat; with or without
--          ';', %40, [at] (at) {at} [@], case-insensitive),
--     matched against spine_client EMAIL_RE / PHONE_RE, with EMAIL_ALLOWLIST_RE (noreply@ and friends) exempting
--     an email match exactly as the client does (allow_re).
--   OUT of L3's contract, on purpose (Python L1/L2 only, spine_client + pii_normalize): word forms (`x at y dot z`,
--     `x at y.tld`), [dot] / [.] / <at> / ⓐ, general HTML-entity and percent decoding, bare 10+ digit runs,
--     DECLARED_IDS shape checks, JSON-structure walking. A CHECK that guessed at prose would block real rows.
--
-- WHAT CHANGES
--   1. NEW public.no_contact_pii_v2(text) with the contract above. VERSIONED like v1: never CREATE OR REPLACE; a
--      change ships _v3. v1 (0022) is kept as is, and its existing CHECKs stay in place.
--   2. public.assert_no_contact_pii() (person trigger, 0017): CREATE OR REPLACE so every scanned column
--      (name, title, bio, role_context, metadata::text) goes through no_contact_pii_v2. Same columns, same
--      exception text; the regex literals now live in v2 only.
--   3. NEW CHECK (public.no_contact_pii_v2(col)) NOT VALID on every free-text site:
--        claim.claim_text, claim.quote (no DB check before), and every v1 site: claim.evidence::text,
--        claim.freshness_reason, claim_verification.note / source_url, claim_label.note, entity_alias.alias,
--        sweep_query.template.
--      LOCKS: ADD CONSTRAINT .. CHECK .. NOT VALID skips the table scan but still takes a brief ACCESS EXCLUSIVE
--      lock on each table (queued behind running transactions; apply at a quiet moment). VALIDATE CONSTRAINT later
--      takes SHARE UPDATE EXCLUSIVE and scans without blocking reads or writes.
--
-- WHY: YED-392 / YED-324 / YED-318 and the 11-19 safeguards review: invisible format characters outside a hand list of 7,
-- non-Latin scripts outside an enumerated range list, and v1 sites that stayed ASCII-only all passed. A flaw in
-- any privacy layer is a defect even when an upstream gate catches it.
--
-- PRE-APPLY REHEARSAL (supabase/staging/0025_verify.sql):
--   0. read-only on prod BEFORE apply: `python3 .claude/scripts/check_pii_corpus.py --emit-sql` and run the SELECT;
--      every row must report ok (out_of_contract rows report but never fail).
--   1. twin: apply this file, run 0025_verify.sql steps 1-3 (behaviour, catalog, per-site violating-row counts).
--   2. If every step-3 count is 0: VALIDATE the constraints (step 4). A non-zero count is triaged first.
--   3. The 0017 / s04_d1 person probes still pass (step 5).
--
-- ROLLBACK: drop the nine constraints by name (step 2 of the verify file lists them), re-run 0017's
--           assert_no_contact_pii(), then `drop function if exists public.no_contact_pii_v2(text);`.
--
-- IDEMPOTENT: v2 and every CHECK are catalog-guarded; the person function is CREATE OR REPLACE.
-- PREREQUISITES: 0022 (entity_alias, sweep_query, v1) and 0023 (claim.evidence, claim_verification, claim_label).
-- =============================================================================

do $do$
begin
  if to_regclass('public.claim_verification') is null or to_regclass('public.claim_label') is null
     or to_regclass('public.entity_alias') is null or to_regclass('public.sweep_query') is null then
    raise exception '0025 needs 0022 and 0023 applied first (claim_verification / claim_label / entity_alias / sweep_query missing).';
  end if;
end
$do$;

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
        -- Verbatim spine_client.py EMAIL_RE / PHONE_RE / EMAIL_ALLOWLIST_RE and pii_normalize.py AT_SPELLING_RE;
        -- ign_re is pii_normalize.IGNORABLE_CLASS (check_pii_regex_parity.py compares every literal below).
        email_re text := $re$(?<![^\s@<>()\[\]{}\x22\x27,;:/\\])[^\s@<>()\[\]{}\x22\x27,;:/\\]+@[^\s@<>()\[\]{}\x22\x27,;:/\\]+\.(?:[A-Za-z]{2,}|[^\x01-\x7f]{2,})$re$;
        phone_re text := $re$(?<![\w.+-])(?:1[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/])?(?:\+\d{1,3}[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?)?(?:\(\d{3}\)[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?|\d{3}[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/])\d{3}[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?\d{4}(?![\w])|(?<![\w.])\+\d{10,15}(?![\w])|(?<![\w.+-])\+(?=\d(?:(?:[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?\(0\))?[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?\d){6,14}(?![\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?\d))\d{1,3}(?:[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?\(0\)[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]?|[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/])\d{1,8}(?:[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d{1,8}){1,4}(?![\w]|[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d)|(?<![\w.+-])07\d{3}[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d{6}(?![\w]|[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d)|(?<![\w.+-])0[1-9](?:[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d{2}){4}(?![\w]|[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/]\d)|[Ww][Aa]\.[Mm][Ee]/\+?\d{7,15}(?!\d)|(?<![\w])[Tt][Ee][Ll]:\+?[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/()]{0,2}\d(?:[\s.\-\u2010-\u2015\u2212\u00B7\u30FB/()]{0,2}\d){6,14}$re$;
        allow_re text := $re$^(?:noreply|no-reply|donotreply)@|@users\.noreply\.github\.com$$re$;
        at_re text := $re$\s{0,3}[\[\(\{]\s{0,3}(?:at|@)\s{0,3}[\]\)\}]\s{0,3}|&(?:#0*64|#x0*40|commat);?|%40$re$;
        ign_re text := $re$[\u00AD\u034F\u0600-\u0605\u061C\u06DD\u070F\u0890-\u0891\u08E2\u115F-\u1160\u17B4-\u17B5\u180B-\u180F\u200B-\u200F\u202A-\u202E\u2060-\u206F\u3164\uFE00-\uFE0F\uFEFF\uFFA0\uFFF0-\uFFFB\U000110BD\U000110CD\U00013430-\U0001343F\U0001BCA0-\U0001BCA3\U0001D173-\U0001D17A\U000E0000-\U000E0FFF]$re$;
        esc_re text := $re$\\[ntr]$re$;
      begin
        return
          -- <v2-expr> (check_pii_corpus.py --emit-sql lifts this expression verbatim; keep it one expression)
          t is null or not exists (
            select 1
            from unnest(array[
                   t,
                   regexp_replace(
                     translate(normalize(regexp_replace(regexp_replace(t, ign_re, '', 'g'), esc_re, ' ', 'g'), NFKC), E'\u3002\uFF0E\uFF61', '...'),
                     at_re, '@', 'gi')
                 ]) as f(x)
            where x ~ phone_re
               or exists (select 1 from regexp_matches(x, '(' || email_re || ')', 'g') as m where m[1] !~* allow_re)
          )
          -- </v2-expr>
        ;
      end
      $fn$
    $ddl$;
  end if;
end
$do$;
revoke all on function public.no_contact_pii_v2(text) from public, anon, authenticated;
grant execute on function public.no_contact_pii_v2(text) to service_role;
comment on function public.no_contact_pii_v2(text) is
  '0025 (YED-392/324): true unless the raw or canonical text (default-ignorables stripped, NFKC, UTS-46 dots, closed @ spellings) matches spine EMAIL_RE (minus EMAIL_ALLOWLIST_RE) or PHONE_RE. Word forms and bare digits are out of contract (client only). VERSIONED: never CREATE OR REPLACE.';

create or replace function public.assert_no_contact_pii()
returns trigger
language plpgsql
as $$
begin
  -- Free-text columns on person (per the spine allowlist: professional-public identity only). name is scanned
  -- too: it is a string someone typed. 0025: every column through no_contact_pii_v2 (the canonical-form contract),
  -- so the literals live in one function.
  if not (public.no_contact_pii_v2(new.name)
          and public.no_contact_pii_v2(new.title)
          and public.no_contact_pii_v2(new.bio)
          and public.no_contact_pii_v2(new.role_context)
          and public.no_contact_pii_v2(new.metadata::text))
  then
    raise exception 'ADR-9 tier-2 violation: contact PII (email/phone pattern) in %. Contact detail lives in HubSpot; see CLAUDE.md invariant 1.',
      tg_argv[0];  -- PL/pgSQL TG_ARGV is 0-based: the CREATE TRIGGER label arg.
  end if;
  return new;
end;
$$;

do $do$
declare
  r record;
begin
  for r in
    select * from (values
      ('public.claim',              'claim_text_no_pii',                        'claim_text'),
      ('public.claim',              'claim_quote_no_pii',                       'quote'),
      ('public.claim',              'claim_evidence_no_pii_v2',                 'evidence::text'),
      ('public.claim',              'claim_freshness_reason_no_pii_v2',         'freshness_reason'),
      ('public.claim_verification', 'claim_verification_note_no_pii_v2',        'note'),
      ('public.claim_verification', 'claim_verification_source_url_no_pii_v2',  'source_url'),
      ('public.claim_label',        'claim_label_note_no_pii_v2',               'note'),
      ('public.entity_alias',       'entity_alias_alias_no_pii_v2',             'alias'),
      ('public.sweep_query',        'sweep_query_template_no_pii_v2',           'template')
    ) v(tbl, con, expr)
  loop
    if not exists (select 1 from pg_constraint where conrelid = r.tbl::regclass and conname = r.con) then
      execute format('alter table %s add constraint %I check (public.no_contact_pii_v2(%s)) not valid',
                     r.tbl, r.con, r.expr);
    end if;
  end loop;
end
$do$;
