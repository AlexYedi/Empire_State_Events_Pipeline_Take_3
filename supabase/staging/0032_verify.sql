-- 0032_verify.sql: probes for supabase/migrations/0032_mi_fact_excludes_email_signal.sql (YED-509).
-- Read-only. Two statements; rehearse_0032.py runs step 0 at gates 1, 4 and 6 and step 1 at gates 1 (negative
-- control: the gated rows must NOT be t before apply) and 4 (every row t).
-- ACLs are compared as sorted grantee:PRIVILEGE sets (PUBLIC for grantee 0), never as raw aclitem[] text.
--
-- 0. BEFORE and AFTER apply (prod via the dashboard or the read-only MCP, the twin via the harness).
--    Expected change, and nothing else:
--      def / claim_branch_excludes_email_signal   false -> true
--      count / claim:email_signal                 <n>   -> <absent>   (n = 22 on prod, 2026-11-24)
--    Every other row (owner, options, ACL, columns, dependents, the event rows including event:email_signal, and
--    every other claim tier) is identical before and after, and identical again after the rollback.
with f as (
  select c.oid, c.relkind, c.relowner, c.reloptions, c.relacl,
         regexp_replace(pg_get_viewdef(c.oid, true), '\s+', ' ', 'g') as def
    from pg_class c where c.oid = to_regclass('mi.fact')
)
select section, obj, val from (
  select 'view' as section, 'mi.fact' as obj,
         coalesce((select 'kind=' || relkind::text || ' owner=' || relowner::regrole::text || ' opts='
                          || coalesce(array_to_string(reloptions, ','), '') from f), '<absent>') as val
  union all
  select 'view_acl', 'mi.fact',
         coalesce((select coalesce(string_agg(e, ',' order by e collate "C"), 'NULL (owner only)')
                     from f left join lateral (select case a.grantee when 0 then 'PUBLIC' else a.grantee::regrole::text end
                                                      || ':' || a.privilege_type
                                                      || case when a.is_grantable then '*' else '' end as e
                                                 from aclexplode(f.relacl) a) s on true), '<absent>')
  union all
  select 'view_cols', 'mi.fact',
         coalesce((select string_agg(a.attname || ':' || format_type(a.atttypid, a.atttypmod), ',' order by a.attnum)
                     from f join pg_attribute a on a.attrelid = f.oid and a.attnum > 0 and not a.attisdropped), '<absent>')
  union all
  select 'def', 'reads_claim_current', coalesce((select (def ~ 'FROM (public\.)?claim_current c ')::text from f), '<absent>')
  union all
  select 'def', 'claim_branch_not_retired', coalesce((select (def ~ 'AND NOT c\.is_retired')::text from f), '<absent>')
  union all
  select 'def', 'claim_branch_excludes_email_signal',
         coalesce((select (def ~ 'AND NOT c\.is_retired AND c\.provenance_tier <> ''email_signal''::text;$')::text from f),
                  '<absent>')
  union all
  select 'def', 'event_branch_tags_inbox_miner',
         coalesce((select (def ~ 'WHEN e\.source ~~ ''inbox_miner%''::text THEN ''email_signal''::text')::text from f),
                  '<absent>')
  union all
  select 'dependent', d, case when to_regclass(d) is null then '<absent>' else 'present' end
    from unnest(array['mi.fact_topic', 'mi.fact_company', 'mi.theme_week', 'mi.theme_lead_lag',
                      'mi.company_timeline', 'mi.company_cohort']) d
  union all
  select 'dependent', 'public.mi_slice(text,jsonb)',
         case when to_regprocedure('public.mi_slice(text,jsonb)') is null then '<absent>' else 'present' end
  union all
  select 'api', r || '@mi', 'usage=' || has_schema_privilege(r, 'mi', 'USAGE')
                            || ' fact_select=' || has_table_privilege(r, 'mi.fact', 'SELECT')
    from unnest(array['anon', 'authenticated']) r
  union all
  select 'count', fact_type || ':' || coalesce(provenance_tier, '<null>'), count(*)::text
    from mi.fact group by fact_type, provenance_tier
) x
order by section collate "C", obj collate "C";

-- 1. AFTER apply: every row ok = true. (Before apply, the negative control: mi_fact_claim_rows,
--    no_email_signal_claims_in_mi_fact and mi_fact_claim_branch_excludes_email_signal read false while the twin or
--    prod holds any email_signal claim; every keep_ row and mi_fact_reads_claim_current read true.)
with f as (
  select c.oid, c.relowner, c.reloptions, regexp_replace(pg_get_viewdef(c.oid, true), '\s+', ' ', 'g') as def
    from pg_class c where c.oid = to_regclass('mi.fact')
)
select 'mi_fact_claim_rows' as check_name,
  (select count(*) from mi.fact where fact_type = 'claim')
  = (select count(*) from public.claim_current c
      where c.status <> 'rejected' and not c.is_retired and c.provenance_tier <> 'email_signal') as ok
union all select 'no_email_signal_claims_in_mi_fact',
  not exists (select 1 from mi.fact where fact_type = 'claim' and provenance_tier = 'email_signal')
union all select 'mi_fact_claim_branch_excludes_email_signal',
  coalesce((select def ~ 'AND NOT c\.is_retired AND c\.provenance_tier <> ''email_signal''::text;$' from f), false)
union all select 'mi_fact_reads_claim_current',
  coalesce((select def ~ 'FROM (public\.)?claim_current c ' and def ~ 'NOT c\.is_retired' from f), false)
union all select 'keep_mi_fact_event_rows',
  (select count(*) from mi.fact where fact_type = 'event') = (select count(*) from public.event)
union all select 'keep_mi_fact_columns',
  (select string_agg(attname, ',' order by attnum) from pg_attribute
    where attrelid = to_regclass('mi.fact') and attnum > 0 and not attisdropped)
  = 'fact_type,fact_id,occasion_event_id,lens,kind,signal_type,lane,source_system,source_ref,provenance_tier,asserted_at,asserted_week,observed_at'
union all select 'keep_mi_fact_invoker',
  coalesce((select 'security_invoker=on' = any (reloptions) and cardinality(reloptions) = 1 from f), false)
union all select 'keep_mi_fact_owner_postgres',
  coalesce((select relowner = 'postgres'::regrole from f), false)
union all select 'keep_mi_no_api_roles',
  not has_schema_privilege('anon', 'mi', 'USAGE') and not has_schema_privilege('authenticated', 'mi', 'USAGE')
  and not has_table_privilege('anon', 'mi.fact', 'SELECT') and not has_table_privilege('authenticated', 'mi.fact', 'SELECT')
union all select 'keep_mi_dependents',
  to_regclass('mi.fact_topic') is not null and to_regclass('mi.fact_company') is not null
  and to_regclass('mi.theme_week') is not null and to_regclass('mi.theme_lead_lag') is not null
  and to_regclass('mi.company_timeline') is not null and to_regclass('mi.company_cohort') is not null
  and to_regprocedure('public.mi_slice(text,jsonb)') is not null;
