-- 0025_rollback.sql: reverses supabase/migrations/0025_pii_backstop_normalized.sql (YED-392/324).
-- Proven on the twin by supabase/scripts/rehearse_0025.py (snapshot C must equal snapshot A).
-- 1. drop the nine v2 CHECKs; 2. restore 0017's assert_no_contact_pii() verbatim; 3. drop v2.
begin;
alter table public.claim drop constraint if exists claim_text_no_pii;
alter table public.claim drop constraint if exists claim_quote_no_pii;
alter table public.claim drop constraint if exists claim_evidence_no_pii_v2;
alter table public.claim drop constraint if exists claim_freshness_reason_no_pii_v2;
alter table public.claim_verification drop constraint if exists claim_verification_note_no_pii_v2;
alter table public.claim_verification drop constraint if exists claim_verification_source_url_no_pii_v2;
alter table public.claim_label drop constraint if exists claim_label_note_no_pii_v2;
alter table public.entity_alias drop constraint if exists entity_alias_alias_no_pii_v2;
alter table public.sweep_query drop constraint if exists sweep_query_template_no_pii_v2;

-- verbatim from supabase/migrations/0017_pii_backstop_intl_phone.sql (Part 1)
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

drop function if exists public.no_contact_pii_v2(text);
commit;
