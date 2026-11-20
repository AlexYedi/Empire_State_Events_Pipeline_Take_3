-- =============================================================================
-- 0026 · claim.source_quote + claim.source_quote_fetched_at: a verbatim span from the cited page, per ledger row
-- Linear: YED-451 (parent YED-384) · Evidence: the 11/19 claim judge (g1119-t1) and its root-cause comment on PR #363.
--
-- PROPOSED. NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2).
-- Numbered 0026 because PR #383 holds 0025 (pii_backstop_normalized). Renumber if that changes.
--
-- WHY (root cause):
--   * The 11/19 judge found 23.0% of decisive verdicts on approved claims unsupported (1,175 of 5,113).
--   * In the seeded drift split, 63% of determinable failures were EXTRACTION errors. These are ledger rows the
--     research specialists wrote with figures, names, stages or dates that are not on the cited page.
--   * parse_ledger copies those rows with zero inference, so nothing downstream can check them. A ledger row
--     carries a URL but no text from the page.
--   * The fix (proposal (b) in the #363 comment): every web_verified ledger row carries a verbatim quote of at
--     most 25 words, taken from the page as fetched. The judge and v2's number and span checks then have source
--     text to test against.
--   * The fetch timestamp beside the quote lets a later re-check tell PAGE DRIFT (the page changed after
--     fetched_at; 23% of the split) apart from EXTRACTION error (the quote never supported the claim).
--
-- WHY NOT REUSE claim.quote:
--   * claim.quote (0009) is the speaker's own words on first-hand claims, and retrieval indexes it in tsv.
--   * A page excerpt is different evidence with a different licensing posture, and it needs a fetch time.
--   * Mixing the two would make quote mean two things. claim.quote is NULL on every ledger web_verified row today.
--
-- WHAT (one transaction, idempotent: add column if not exists; constraints guarded by name):
--   1. claim.source_quote text: at most 25 words (the 0009 licensing guard, now enforced in the DB), never blank,
--      and passing public.no_contact_pii_v1 (0022), the same PII CHECK 0023 put on evidence and freshness_reason.
--   2. claim.source_quote_fetched_at timestamptz, set if and only if source_quote is set.
--   3. NOT included: a CHECK requiring source_quote on new web_verified parse rows. That waits until the
--      ledger contract and parse_ledger emit the quote. Otherwise stage-research would fail on every brief.
--      It is sketched as PHASE 2 below and added NOT VALID, so it would bind new rows only.
--
-- AFTER APPLY (separate PRs, in order):
--   1. spine_client ALLOW["claim"] += source_quote, source_quote_fetched_at. GUARD-ADJACENT: Alex reviews.
--      source_quote is free text, so the client-side PII scan covers it too (two layers).
--   2. Ledger contract + specialists + parse_ledger: emit `quote` (<= 25 words, verbatim) and `fetched` per
--      web_verified row. Meta-commentary rows ("not found", "unverified") are never web_verified (proposal (c)).
--   3. stage-research judge at stage time (YED-451 (a)) compares source_quote to the claim before approval.
--   4. PHASE 2 CHECK below, once a full week of briefs stages cleanly with quotes.
--
-- BEHAVIOUR AT APPLY: nothing changes. Both columns are NULL on every row, all CHECKs hold trivially, and no
-- reader selects them.
-- =============================================================================

begin;

alter table public.claim
  add column if not exists source_quote             text,
  add column if not exists source_quote_fetched_at  timestamptz;

do $do$
declare
  c record;
begin
  if to_regprocedure('public.no_contact_pii_v1(text)') is null then
    raise exception '0026: public.no_contact_pii_v1(text) missing; apply 0022 first';
  end if;
  for c in
    select * from (values
      ('claim_source_quote_words',  'check (source_quote is null or (btrim(source_quote) <> '''' and array_length(regexp_split_to_array(btrim(source_quote), ''\s+''), 1) <= 25))'),
      ('claim_source_quote_no_pii', 'check (public.no_contact_pii_v1(source_quote))'),
      ('claim_source_quote_paired', 'check ((source_quote is null) = (source_quote_fetched_at is null))')
    ) as t(name, def)
  loop
    if not exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass and conname = c.name) then
      execute format('alter table public.claim add constraint %I %s', c.name, c.def);
    end if;
  end loop;
end
$do$;

comment on column public.claim.source_quote is
  '0026 (YED-451): verbatim span (<= 25 words) from the page at locator url, as fetched by the researcher. Evidence for the source-page judge. Not the speaker quote (that is claim.quote).';
comment on column public.claim.source_quote_fetched_at is
  '0026 (YED-451): when the page holding source_quote was fetched. Separates page drift (changed after this) from extraction error.';

commit;

-- -----------------------------------------------------------------------------
-- PHASE 2 (do NOT run with this file). Once parse_ledger emits source_quote, new web_verified ledger rows must
-- carry one. NOT VALID: binds inserts and updates from then on, never the ~6k historical rows.
-- -----------------------------------------------------------------------------
-- alter table public.claim add constraint claim_web_verified_needs_source_quote
--   check (provenance_tier <> 'web_verified' or extractor <> 'parse' or source_quote is not null) not valid;

-- -----------------------------------------------------------------------------
-- VERIFY (read-only). Every row must read true.
-- -----------------------------------------------------------------------------
-- VERIFY:BEGIN
-- select 'cols_present', (select count(*) = 2 from information_schema.columns where table_schema = 'public'
--   and table_name = 'claim' and column_name in ('source_quote', 'source_quote_fetched_at'))::text
-- union all select 'checks_present', (select count(*) = 3 from pg_constraint where conrelid = 'public.claim'::regclass
--   and conname in ('claim_source_quote_words', 'claim_source_quote_no_pii', 'claim_source_quote_paired'))::text
-- union all select 'all_null_at_apply', (select count(*) = 0 from public.claim
--   where source_quote is not null or source_quote_fetched_at is not null)::text
-- union all select 'phase2_not_added', (not exists (select 1 from pg_constraint where conrelid = 'public.claim'::regclass
--   and conname = 'claim_web_verified_needs_source_quote'))::text;
-- VERIFY:END

-- -----------------------------------------------------------------------------
-- TWIN REHEARSAL negatives (run on the twin only, each must FAIL with the named constraint, then roll back):
--   update claim set source_quote = repeat('w ', 26), source_quote_fetched_at = now() where id = <any>;  -- _words
--   update claim set source_quote = 'mail a@b.example.com', source_quote_fetched_at = now() where id = <any>; -- _no_pii
--   update claim set source_quote = 'ok' where id = <any>;                                                 -- _paired
--   update claim set source_quote = '   ', source_quote_fetched_at = now() where id = <any>;               -- _words
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- ROLLBACK (uncomment to run). Drops only what 0026 adds; nothing writes these columns until step 1-2 above.
-- -----------------------------------------------------------------------------
-- ROLLBACK:BEGIN
-- begin;
-- alter table public.claim drop constraint if exists claim_web_verified_needs_source_quote;
-- alter table public.claim drop constraint if exists claim_source_quote_paired;
-- alter table public.claim drop constraint if exists claim_source_quote_no_pii;
-- alter table public.claim drop constraint if exists claim_source_quote_words;
-- alter table public.claim drop column if exists source_quote_fetched_at;
-- alter table public.claim drop column if exists source_quote;
-- commit;
-- ROLLBACK:END
