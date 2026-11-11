-- 0022 PREFLIGHT for the Supabase SQL editor (project oicikjyzmxqfomrrqkvf, The-Prod-Brain).
-- GENERATED from supabase/migrations/0022_graph_phase1_shared.sql by rehearse_0022.py --emit-dashboard;
-- the rehearsal fails if this file drifts. READ-ONLY. APPLY 0021 FIRST, then run this, then 0022.
-- Expect: NO collision_* rows; baseline_claim_usage_rows >= 1282; baseline_use_count_nonzero = 0.
-- A collision row lists id:name of every row sharing the key: rename the loser (the tombstoned
-- row, else the newer one) to '<name> [dup <first 8 of id>]' via spine_client, re-run. Never merge to pass.
select 'collision_company' as check_name, k as norm_key, string_agg(id::text || ':' || name, ' | ' order by id) as detail
  from (select id, name, nullif(trim(regexp_replace(regexp_replace(lower(coalesce(name, '')), '\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\M[^a-z0-9]*$', ''), '[^a-z0-9]+', ' ', 'g')), '') as k from public.company) s
 where k is not null group by k having count(*) > 1
union all
select 'collision_topic', k, string_agg(id::text || ':' || name, ' | ' order by id)
  from (select id, name, nullif(trim(regexp_replace(lower(coalesce(name, '')), '[^a-z0-9]+', ' ', 'g')), '') as k from public.topic) s
 where k is not null group by k having count(*) > 1
union all
select 'baseline_claim_usage_rows', null, (select count(*) from public.claim_usage)::text
union all
select 'baseline_use_count_nonzero', null, (select count(*) from public.claim where use_count <> 0 or last_used_at is not null)::text;
