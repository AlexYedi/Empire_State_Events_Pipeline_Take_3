# APPLY — Topic-intelligence health view (YED-122)

**Cockpit-only health strip for the MI graph.** One additive view
(`topic_intelligence.topic_intelligence_health`), ported from the retired gtm-os spine
(`gtm-os:scripts/topic_intelligence/topic_intelligence_health.sql`, YED-120). No table,
function, grant, or Data-API config changes. Fully reversible (rollback = drop the view).

**Linear:** YED-122 (GTM cockpit health strip) · **Migration:**
`supabase/migrations/0013_topic_intelligence_health_view.sql`

> **Hard boundary.** This runbook is for the HUMAN operator (Alex). No agent or script
> executes any statement in this file against any database. DDL is applied by Alex from
> the Supabase dashboard SQL editor after a twin rehearsal — same gate as every prior
> migration (ADR-1 / ADR-2 convention).

**What changed vs the spine view (summary — full mapping in the migration header):**
- `signal.topic_trend` / `signal.topic_pair_metric` → `topic_intelligence.*` (same columns).
- Membership and unassigned-topic counts read `public.topic` (the live post-2b source,
  matching the 0012 compute), not the frozen `topic_intelligence.topics` snapshot.
- The tagging denominator reads `public.event_entity` (`role='tagged_topic'`, attended
  events) — the same surface the live compute reads.
- **REVIEW FIX (runtime metric):** the spine's `runtime_snapshot_gap` took the max gap
  between consecutive snapshots over **all history**, so the 2026-08→10 recompute outage
  (49 days) tripped it forever. The ported tripwire now measures **freshness — days
  since the latest snapshot** (`current_date - max(as_of_date)`), threshold unchanged
  at 1: it clears as soon as the nightly recompute lands and trips only while the job
  has actually stalled. Tripwire key kept for cockpit continuity.
- **DEGRADED:** `signal.conflict_log` has no MI-graph counterpart, so
  `canonicalization_backlog` now counts unassigned topics only (its human_pending facet
  is omitted). Flagged in the migration header and PR body; re-add the facet if a
  conflict log ever lands on the MI graph.

---

## 1. Twin rehearsal (scratch project — do this FIRST)

Rehearse on a disposable copy before production. Either a **Supabase branch** of
`oicikjyzmxqfomrrqkvf` (dashboard → Branches → Create branch, e.g. `yed-122-rehearsal`)
or the **Phantom Test Case DB** (`ytfzzsxcxxbejnowmkmk`) restored fresh from prod.

1. Confirm the scratch DB is post-2b state (it must have `topic_intelligence.*` and
   `public.topic(cluster_id, cluster_assignment_confidence)`):
   ```sql
   select 'topic_trend' t, count(*) from topic_intelligence.topic_trend
   union all select 'topic_pair_metric', count(*) from topic_intelligence.topic_pair_metric
   union all select 'public.topic', count(*) from public.topic;
   -- Expect nonzero on all three; zero on topic_trend means the scratch predates the
   -- nightly recompute — restore a fresher copy before judging the view's output.
   ```
2. In the scratch project's **SQL Editor**, paste **all of**
   `supabase/migrations/0013_topic_intelligence_health_view.sql` and run it
   (wrapped in `begin; … commit;` — it runs atomically).
3. Run the verification query from §3 below. Expect 6 rows.
4. Spot-check one metric by hand, e.g. unassigned topics:
   ```sql
   select count(*) from public.topic where cluster_id is null;   -- must equal the
   -- 'canonicalization_backlog' metric value in the view
   ```
5. Run the security checks from §4 (security_invoker on, no anon/authenticated SELECT).
6. Rollback drill: `drop view if exists topic_intelligence.topic_intelligence_health;`
   then re-apply once — proves the whole file is idempotent (`create or replace`) and
   the rollback is clean.

**Gate:** all of §3/§4 green on the scratch DB before touching production.

---

## 2. Apply on production (`oicikjyzmxqfomrrqkvf`)

1. Supabase dashboard → project **`oicikjyzmxqfomrrqkvf`** (org A.Yedi) → **SQL Editor**.
2. Paste **all of** `supabase/migrations/0013_topic_intelligence_health_view.sql`.
3. Run. Success = `CREATE VIEW` / `COMMENT` / two `REVOKE`s, transaction committed.
   (If a previous run already created the view, `create or replace` makes the file
   idempotent — safe to re-run.)
4. No psql needed; if you prefer it:
   `psql "<session-pooler DSN>" -v ON_ERROR_STOP=1 -f supabase/migrations/0013_topic_intelligence_health_view.sql`

> **No PostgREST schema-exposure toggle is needed.** The Data API exposed-schemas list
> stays exactly as it is (`public, signal_read`) — `topic_intelligence` remains
> unexposed, so the view has no REST route at all. The cockpit reads it with the
> **service-role key**, which bypasses RLS and connects over the direct Postgres path
> (or the service-role API), neither of which requires the schema to be exposed. Do NOT
> add `topic_intelligence` to exposed schemas for this.

---

## 3. Post-apply verification (read-only)

```sql
select * from topic_intelligence.topic_intelligence_health order by tripwire;
```

Expect exactly 6 rows — `granularity_occupancy`, `granularity_insufficient`,
`membership_confidence`, `canonicalization_backlog`, `runtime_snapshot_gap`,
`bridge_inflation` — each with `status` in (`ok`, `watch`, `trip`, `no_data`).

Plausible sample output (illustrative — nightly recompute ran today; one thin cluster
month; 96 topics not yet cluster-assigned):

| tripwire | metric | status |
|---|---|---|
| granularity_occupancy | 0.181 | watch |
| granularity_insufficient | 1.000 | trip |
| membership_confidence | 0.106 | ok |
| canonicalization_backlog | 96 | trip |
| runtime_snapshot_gap | 0 | ok |
| bridge_inflation | 3.00 | ok |

`runtime_snapshot_gap` is **freshness** (days since the latest `topic_trend`
snapshot), not the spine's all-history max gap: `0` means the nightly recompute
landed today; it climbs only while the job has actually stalled and re-clears on the
next successful run. A historical outage no longer trips it permanently.

`no_data` on a metric means its source had no rows (e.g. before the first recompute
lands a snapshot, or an empty `topic_trend` for the freshness measure); it is not an
error, but if every row is `no_data` a day after the nightly compute has run,
investigate.

Cross-checks (optional, one metric is enough to trust the port):
```sql
select count(*) from public.topic where cluster_id is null;  -- == canonicalization_backlog metric
```

---

## 4. Security verification (read-only)

```sql
-- view must be security_invoker (per the 0002 ADR-backed convention for views over
-- the intelligence schema — invoker rights, never definer):
select reloptions from pg_class
 where oid = 'topic_intelligence.topic_intelligence_health'::regclass;
--   -> must include security_invoker=on

-- no anon/authenticated path (belt and braces; the schema is also unexposed):
select has_table_privilege('anon',
  'topic_intelligence.topic_intelligence_health', 'SELECT');          -- f
select has_table_privilege('authenticated',
  'topic_intelligence.topic_intelligence_health', 'SELECT');          -- f
```

Then run **Advisors → Security** in the A.Yedi dashboard and confirm no new critical
(e.g. a "security definer view" finding would be a red flag — the view is invoker).

**Cockpit wiring (separate step, not this PR):** the GTM cockpit authenticates with the
MI graph's service-role key and reads
`topic_intelligence.topic_intelligence_health` over the service-role API. Provisioning
that key to the cockpit is a human follow-up (tracked on YED-122).

---

## 5. Rollback

```sql
drop view if exists topic_intelligence.topic_intelligence_health;
```

Nothing else was created or modified — no table, function, grant, or config change —
so this single statement is the complete rollback.
