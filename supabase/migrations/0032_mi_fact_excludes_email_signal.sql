-- =============================================================================
-- 0032 · mi.fact: the claim branch excludes provenance_tier = 'email_signal' (ADR-16, Monday Market Brief "Themes moving")
-- Linear: YED-509. Decision: Alex, option A, 2026-11-24. Depends on 0024 (mi.fact reads claim_current, is_retired).
--
-- NOT APPLIED. DDL is applied by Alex from the dashboard after a twin rehearsal (CLAUDE.md invariant 2):
--   python3 supabase/scripts/rehearse_0032.py --execute
-- Before AND after the paste, run staging/0032_verify.sql step 0 on prod (read-only) and keep both outputs.
-- After the paste, step 1 must show every row ok = t.
--
-- WHY:
--   ADR-16: email_signal claims (mined from Alex's inbox) never reach public output. PR #435 (YED-459) enforced that in
--   code on every reader except one: mi.fact. Its claim branch passes every non-rejected, non-retired claim through,
--   so the 22 email_signal claims on prod (read 2026-11-24) flow into mi.fact_topic / mi.fact_company and from there
--   into mi.theme_week, mi.theme_lead_lag, mi.company_timeline and mi.company_cohort, all served by public.mi_slice.
--   The Monday Market Brief's "Themes moving" section, slice.py and sweep_seed.py read those views. Filtering at the
--   base view closes the gap once for every consumer; each consumer inherits it with no change.
--
-- THE RULE (Alex, 2026-11-24): content-bearing output excludes the email_signal tier; pure size/health counts do not.
--   So public.v_public_spine_stats (0031: entity, event and approved-claim counts plus one timestamp, no content)
--   stays UNCHANGED and keeps counting every tier. mi.fact and everything built on it is content-bearing (themes,
--   companies, weeks, kinds, source refs), so it excludes the tier.
--
-- SCOPE: the CLAIM branch only, as approved. The EVENT branch is untouched: it still tags source like 'inbox_miner%'
--   as email_signal (13 rows on prod, 2026-11-24) and still passes them through. Whether to filter those too is a
--   separate decision (fork in the PR for YED-509).
--
-- WHAT CHANGES: one predicate. The claim branch WHERE goes from
--     c.status <> 'rejected' AND NOT c.is_retired
--   to
--     c.status <> 'rejected' AND NOT c.is_retired AND c.provenance_tier <> 'email_signal'
--   claim.provenance_tier is NOT NULL (with a CHECK listing the tiers), so `<>` drops exactly the email_signal rows and
--   no null-tier row; PART 1 refuses the paste if that ever stops holding.
--   Same columns, same order, same security_invoker = on: CREATE OR REPLACE keeps the OID, the owner, the ACL and
--   every dependent view (fact_topic, fact_company, theme_week, theme_lead_lag, company_timeline, company_cohort) and
--   public.mi_slice. No grant, revoke or ownership statement: the ACLs stay exactly as 0028/0030 left them, and PART 3
--   proves owner and ACL are byte-identical before and after.
--
-- EXPECTED EFFECT ON PROD: mi.fact claim rows drop by exactly the email_signal claim count (22 on 2026-11-24); event
--   rows unchanged; theme_week cells lose exactly the email_signal claims tagged to them (cells that only held those
--   claims disappear); mi_slice denominators research.briefs may drop by the email_signal source refs.
--
-- WHAT (one transaction; idempotent: a second paste raises a NOTICE and changes nothing):
--   PART 1  preflight. Raises unless the session can act as postgres; mi.fact, claim_current (with is_retired) and the
--           six dependents plus mi_slice exist; claim.provenance_tier is NOT NULL; mi.fact has exactly the 13 columns,
--           owner postgres and reloptions {security_invoker=on}; and mi.fact is in exactly one of two states:
--             PRE   the 0024 shape: reads claim_current, claim branch ends `... AND NOT c.is_retired;`
--             POST  the 0032 shape: claim branch ends `... AND NOT c.is_retired AND c.provenance_tier <> 'email_signal'`
--                   NOTICE, then no-op.
--           Anything else raises: inspect by hand. Records the definition, owner and ACL for PART 3.
--   PART 2  only in PRE: CREATE OR REPLACE VIEW mi.fact with the one added predicate.
--   PART 3  postflight: raises (rolling back everything) unless the definition equals the PART 1 definition with
--           exactly the one predicate added (or is unchanged, in POST); owner, ACL, options and columns are unchanged;
--           the dependents exist; mi.fact holds no email_signal claim; its claim rows equal claim_current non-rejected
--           non-retired minus email_signal; its event rows equal public.event; anon/authenticated still hold nothing.
--
-- VERIFY (staging/0032_verify.sql step 1; every row ok = t after the paste): mi_fact_claim_rows,
--   no_email_signal_claims_in_mi_fact, mi_fact_claim_branch_excludes_email_signal, mi_fact_reads_claim_current,
--   keep_mi_fact_event_rows, keep_mi_fact_columns, keep_mi_fact_invoker, keep_mi_fact_owner_postgres,
--   keep_mi_no_api_roles, keep_mi_dependents.
--
-- LOCKS: CREATE OR REPLACE VIEW takes AccessExclusiveLock on mi.fact only (a catalog swap, no data rewrite).
--   lock_timeout = 5s; re-paste on timeout.
--
-- ROLLBACK (exact statements: the 0024 §4 definition, verbatim; rehearse_0032.py gate 5 runs this block verbatim from
--   this header and proves the twin returns to its pre-apply snapshot):
-- ROLLBACK-BEGIN
--   begin;
--   set local lock_timeout = '5s';
--   create or replace view mi.fact
--   with (security_invoker = on) as
--    SELECT 'event'::text AS fact_type,
--       e.id AS fact_id,
--       e.id AS occasion_event_id,
--       mi.lens_of(e.kind, e.source, NULL::text) AS lens,
--       e.kind,
--       e.signal_type,
--       NULL::text AS lane,
--       NULLIF(split_part(COALESCE(e.source, ''::text), ':'::text, 1), ''::text) AS source_system,
--       COALESCE(e.url, e.notion_page_id, e.id::text) AS source_ref,
--           CASE
--               WHEN e.source ~~ 'inbox_miner%'::text THEN 'email_signal'::text
--               WHEN e.kind = 'attended'::text THEN 'first_hand'::text
--               WHEN e.kind = ANY (ARRAY['market'::text, 'funding'::text, 'launch'::text, 'exec_move'::text, 'role_posted'::text, 'application'::text, 'interview'::text]) THEN 'web_verified'::text
--               ELSE 'reference'::text
--           END AS provenance_tier,
--       e.event_date AS asserted_at,
--       date_trunc('week'::text, (e.event_date AT TIME ZONE 'UTC'::text))::date AS asserted_week,
--       e.created_at AS observed_at
--      FROM public.event e
--   UNION ALL
--    SELECT 'claim'::text AS fact_type,
--       c.id AS fact_id,
--       c.event_id AS occasion_event_id,
--       mi.lens_of(oe.kind, oe.source, c.lane) AS lens,
--       oe.kind,
--       NULL::text AS signal_type,
--       c.lane,
--       'substrate'::text AS source_system,
--       COALESCE(c.document_id::text, c.source_key) AS source_ref,
--       c.provenance_tier,
--       c.asserted_at,
--       date_trunc('week'::text, (c.asserted_at AT TIME ZONE 'UTC'::text))::date AS asserted_week,
--       c.created_at AS observed_at
--      FROM public.claim_current c
--        LEFT JOIN public.event oe ON oe.id = c.event_id
--     WHERE c.status <> 'rejected'::text
--       AND NOT c.is_retired;
--   commit;
-- ROLLBACK-END
-- =============================================================================

begin;

set local lock_timeout = '5s';

-- PART 1 ---------------------------------------------------------------------------------------------------------
do $pre$
declare
  want_cols constant text := 'fact_type,fact_id,occasion_event_id,lens,kind,signal_type,lane,source_system,source_ref,'
                             'provenance_tier,asserted_at,asserted_week,observed_at';
  deps constant text[] := array['mi.fact_topic', 'mi.fact_company', 'mi.theme_week', 'mi.theme_lead_lag',
                                'mi.company_timeline', 'mi.company_cohort'];
  pre_tail  constant text := 'FROM (public\.)?claim_current c LEFT JOIN (public\.)?event oe ON oe\.id = c\.event_id '
                             'WHERE c\.status <> ''rejected''::text AND NOT c\.is_retired;$';
  post_tail constant text := 'FROM (public\.)?claim_current c LEFT JOIN (public\.)?event oe ON oe\.id = c\.event_id '
                             'WHERE c\.status <> ''rejected''::text AND NOT c\.is_retired '
                             'AND c\.provenance_tier <> ''email_signal''::text;$';
  v_missing text; v_def text; got text;
begin
  if not pg_has_role(current_user, 'postgres', 'member') then
    raise exception '0032 preflight: % cannot act as postgres (not a member). Paste as postgres.', current_user;
  end if;
  if to_regclass('mi.fact') is null or to_regclass('public.claim_current') is null then
    raise exception '0032 preflight: mi.fact or public.claim_current missing. Inspect by hand.';
  end if;
  if not exists (select 1 from pg_attribute where attrelid = 'public.claim_current'::regclass
                    and attname = 'is_retired' and not attisdropped) then
    raise exception '0032 preflight: public.claim_current has no is_retired. Apply 0024 first.';
  end if;
  select string_agg(d, ',') into v_missing from unnest(deps) d where to_regclass(d) is null;
  if v_missing is not null or to_regprocedure('public.mi_slice(text,jsonb)') is null then
    raise exception '0032 preflight: mi dependents missing: % (or public.mi_slice). Inspect by hand.',
      coalesce(v_missing, 'public.mi_slice(text,jsonb)');
  end if;
  if not coalesce((select attnotnull from pg_attribute where attrelid = 'public.claim'::regclass
                     and attname = 'provenance_tier' and not attisdropped), false) then
    raise exception '0032 preflight: public.claim.provenance_tier is nullable (or missing); `<> ''email_signal''` '
                    'would also drop null-tier claims. Inspect by hand.';
  end if;

  select concat_ws(' | ', 'kind=' || c.relkind::text, 'owner=' || c.relowner::regrole::text,
                   'opts=' || coalesce(array_to_string(c.reloptions, ','), ''),
                   'cols=' || (select string_agg(a.attname, ',' order by a.attnum) from pg_attribute a
                                where a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped))
    into got from pg_class c where c.oid = 'mi.fact'::regclass;
  if got is distinct from concat_ws(' | ', 'kind=v', 'owner=postgres', 'opts=security_invoker=on', 'cols=' || want_cols) then
    raise exception E'0032 preflight: mi.fact has an unexpected owner, options or column list. Inspect by hand.\n got [%]', got;
  end if;

  v_def := regexp_replace(pg_get_viewdef('mi.fact'::regclass, true), '\s+', ' ', 'g');
  perform set_config('mig0032.def_before', v_def, true);
  perform set_config('mig0032.acl_before',
                     coalesce((select relacl::text from pg_class where oid = 'mi.fact'::regclass), 'NULL'), true);

  if v_def ~ post_tail then
    perform set_config('mig0032.state', 'post', true);
    raise notice '0032: already applied (mi.fact claim branch already excludes email_signal); nothing to do.';
  elsif v_def ~ pre_tail then
    perform set_config('mig0032.state', 'pre', true);
    raise notice '0032 preflight OK: PRE state (mi.fact at the 0024 shape; provenance_tier NOT NULL; 6 dependents + mi_slice present).';
  else
    raise exception E'0032 preflight: mi.fact is not at the 0024 or the 0032 shape. Inspect by hand.\n tail [%]', right(v_def, 260);
  end if;
end
$pre$;

-- PART 2 ---------------------------------------------------------------------------------------------------------
do $apply$
begin
  if current_setting('mig0032.state', true) is distinct from 'pre' then
    return;
  end if;

  create or replace view mi.fact
  with (security_invoker = on) as
   SELECT 'event'::text AS fact_type,
      e.id AS fact_id,
      e.id AS occasion_event_id,
      mi.lens_of(e.kind, e.source, NULL::text) AS lens,
      e.kind,
      e.signal_type,
      NULL::text AS lane,
      NULLIF(split_part(COALESCE(e.source, ''::text), ':'::text, 1), ''::text) AS source_system,
      COALESCE(e.url, e.notion_page_id, e.id::text) AS source_ref,
          CASE
              WHEN e.source ~~ 'inbox_miner%'::text THEN 'email_signal'::text
              WHEN e.kind = 'attended'::text THEN 'first_hand'::text
              WHEN e.kind = ANY (ARRAY['market'::text, 'funding'::text, 'launch'::text, 'exec_move'::text, 'role_posted'::text, 'application'::text, 'interview'::text]) THEN 'web_verified'::text
              ELSE 'reference'::text
          END AS provenance_tier,
      e.event_date AS asserted_at,
      date_trunc('week'::text, (e.event_date AT TIME ZONE 'UTC'::text))::date AS asserted_week,
      e.created_at AS observed_at
     FROM public.event e
  UNION ALL
   SELECT 'claim'::text AS fact_type,
      c.id AS fact_id,
      c.event_id AS occasion_event_id,
      mi.lens_of(oe.kind, oe.source, c.lane) AS lens,
      oe.kind,
      NULL::text AS signal_type,
      c.lane,
      'substrate'::text AS source_system,
      COALESCE(c.document_id::text, c.source_key) AS source_ref,
      c.provenance_tier,
      c.asserted_at,
      date_trunc('week'::text, (c.asserted_at AT TIME ZONE 'UTC'::text))::date AS asserted_week,
      c.created_at AS observed_at
     FROM public.claim_current c
       LEFT JOIN public.event oe ON oe.id = c.event_id
    WHERE c.status <> 'rejected'::text
      AND NOT c.is_retired
      AND c.provenance_tier <> 'email_signal'::text;   -- ADR-16 / YED-509: email_signal claims never reach mi

  raise notice '0032: mi.fact claim branch now excludes provenance_tier = email_signal (event branch unchanged)';
end
$apply$;

-- PART 3 ---------------------------------------------------------------------------------------------------------
do $post$
declare
  want_cols constant text := 'fact_type,fact_id,occasion_event_id,lens,kind,signal_type,lane,source_system,source_ref,'
                             'provenance_tier,asserted_at,asserted_week,observed_at';
  deps constant text[] := array['mi.fact_topic', 'mi.fact_company', 'mi.theme_week', 'mi.theme_lead_lag',
                                'mi.company_timeline', 'mi.company_cohort'];
  v_fail text[] := '{}';
  v_before text := current_setting('mig0032.def_before', true);
  v_state text := current_setting('mig0032.state', true);
  v_def text; v_want text; got text; n_es bigint; n_claim bigint; n_want bigint; n_ev bigint; n_ev_want bigint;
begin
  if v_before is null or v_state is null then
    raise exception '0032 postflight FAILED (rolled back): PART 1 did not run in this transaction';
  end if;
  v_def := regexp_replace(pg_get_viewdef('mi.fact'::regclass, true), '\s+', ' ', 'g');
  v_want := case v_state
              when 'post' then v_before
              else regexp_replace(v_before, ' AND NOT c\.is_retired;$',
                                  ' AND NOT c.is_retired AND c.provenance_tier <> ''email_signal''::text;')
            end;
  if v_def is distinct from v_want then
    v_fail := v_fail || 'mi.fact definition is not the PART 1 definition plus exactly the email_signal predicate'::text;
  end if;

  select concat_ws(' | ', 'kind=' || c.relkind::text, 'owner=' || c.relowner::regrole::text,
                   'opts=' || coalesce(array_to_string(c.reloptions, ','), ''),
                   'cols=' || (select string_agg(a.attname, ',' order by a.attnum) from pg_attribute a
                                where a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped))
    into got from pg_class c where c.oid = 'mi.fact'::regclass;
  if got is distinct from concat_ws(' | ', 'kind=v', 'owner=postgres', 'opts=security_invoker=on', 'cols=' || want_cols) then
    v_fail := v_fail || format('mi.fact owner/options/columns changed: [%s]', got);
  end if;
  if coalesce((select relacl::text from pg_class where oid = 'mi.fact'::regclass), 'NULL')
     is distinct from current_setting('mig0032.acl_before', true) then
    v_fail := v_fail || 'mi.fact ACL changed'::text;
  end if;
  if exists (select 1 from unnest(deps) d where to_regclass(d) is null)
     or to_regprocedure('public.mi_slice(text,jsonb)') is null then
    v_fail := v_fail || 'an mi dependent or public.mi_slice is missing'::text;
  end if;
  if has_schema_privilege('anon', 'mi', 'USAGE') or has_schema_privilege('authenticated', 'mi', 'USAGE')
     or has_table_privilege('anon', 'mi.fact', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
     or has_table_privilege('authenticated', 'mi.fact', 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') then
    v_fail := v_fail || 'anon/authenticated hold a privilege on schema mi or mi.fact'::text;
  end if;

  select count(*) filter (where provenance_tier = 'email_signal'), count(*) into n_es, n_claim
    from mi.fact where fact_type = 'claim';
  select count(*) into n_want from public.claim_current c
   where c.status <> 'rejected' and not c.is_retired and c.provenance_tier <> 'email_signal';
  select count(*) into n_ev from mi.fact where fact_type = 'event';
  select count(*) into n_ev_want from public.event;
  if n_es <> 0 then
    v_fail := v_fail || format('mi.fact still holds %s email_signal claim rows', n_es);
  end if;
  if n_claim <> n_want then
    v_fail := v_fail || format('mi.fact claim rows %s <> claim_current non-rejected non-retired non-email_signal %s',
                               n_claim, n_want);
  end if;
  if n_ev <> n_ev_want then
    v_fail := v_fail || format('mi.fact event rows %s <> public.event %s (event branch must be unchanged)', n_ev, n_ev_want);
  end if;

  if cardinality(v_fail) > 0 then
    raise exception '0032 postflight FAILED (rolled back): %', array_to_string(v_fail, '; ');
  end if;
  raise notice '0032 postflight OK (claim rows %, email_signal claims 0, event rows %)', n_claim, n_ev;
end
$post$;

commit;
