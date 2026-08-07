# APPLY — MI data-layer consolidation, Increment 1 (YED-130 / ADR-1)

**Carry-forward copy of gtm-os's topic-intelligence into the canonical Empire project.**
Additive only. Zero DML/DDL on Empire's `public` schema. Fully reversible (rollback = drop
two schemas + revert one config). Spec: `mi-consolidation/ADR-1-data-layer.md` +
`pre-mortem-data-layer.md`.

Artifacts in this bundle:

| File | What it does |
|---|---|
| `migrations/0001_topic_intelligence_schema.sql` | schema `topic_intelligence` + carried-forward tables (RLS deny-all) |
| `migrations/0002_signal_read_views.sql` | schema `signal_read` + anon-safe `security_invoker` views (k≥5) |
| `migrations/0003_roles_grants_definer.sql` | `pipeline_writer` role, grants, SECURITY DEFINER write path |
| `scripts/carry_forward_topic_intelligence.py` | idempotent PostgREST copy of the 4 tables |

---

## (a) The cross-account constraint — READ FIRST

The canonical project `oicikjyzmxqfomrrqkvf` is on the **A.Yedi** Supabase account.

- **The Supabase MCP is connected to a DIFFERENT account** (`Same Old Expressions` / GTM_OS)
  and **CANNOT be used** against the canonical project. Do not attempt `apply_migration` /
  `execute_sql` via MCP here — wrong account.
- **PostgREST (the REST Data API) cannot run DDL.** `CREATE SCHEMA/TABLE/ROLE/FUNCTION` and
  `GRANT` are not expressible over PostgREST.
- **Therefore DDL (0001–0003) must be applied by Alex**, either:
  1. **Supabase dashboard → SQL Editor** (paste each file whole; each is wrapped in
     `begin; … commit;` so it runs atomically), **or**
  2. **`psql` / a connection string** (`psql "$CANONICAL_DB_URL" -f migrations/0001_...sql`),
- **All of this happens on a Supabase BRANCH of `oicikjyzmxqfomrrqkvf`**, never directly on
  production. A branch gives an isolated copy of the database to validate against before merge.

The Python carry-forward (step 4) DOES use PostgREST (it only moves rows, no DDL).

---

## (b) Ordered steps

### 0. Freeze the gtm-os source spine (fidelity precondition for AC1a)
The AC1a test is an **exact-match against a FROZEN spine**. Before copying:
- Set the gtm-os spine (`abkvgihlbwfloentugtd`, `signal` schema) **read-only for these tables**
  (stop any writer) and **turn the nightly `compute_topic_intelligence` pg_cron job OFF**
  (`select cron.unschedule('topic-intel-nightly');`). Record the freeze time.
- Rationale: pre-mortem #1 + #9 — a moving source makes exact-match un-testable / falsely red.

### 1. Create a branch of the canonical project
- Supabase dashboard → project `oicikjyzmxqfomrrqkvf` → **Branches → Create branch**
  (name e.g. `mi-increment-1`). Wait for it to provision.
- Capture the branch's connection string + Data API URL/keys (they differ from production).

### 2. Apply the DDL, in order, on the branch
Run against the **branch** (SQL Editor or psql):
1. `migrations/0001_topic_intelligence_schema.sql`
2. `migrations/0002_signal_read_views.sql`
3. `migrations/0003_roles_grants_definer.sql`

Sanity checks after each:
```sql
-- after 0001: five tables exist, RLS on, zero rows
select table_name from information_schema.tables where table_schema='topic_intelligence';
select relname, relrowsecurity from pg_class
  where relnamespace = 'topic_intelligence'::regnamespace and relkind='r';
-- after 0002: both views are security_invoker = on
select c.relname, c.reloptions
  from pg_class c
  where c.relnamespace = 'signal_read'::regnamespace and c.relkind='v';
--   -> reloptions must contain 'security_invoker=on' (formatted 'security_invoker=true') for BOTH views
-- after 0003: role exists, has no direct DML on topic_intelligence
select rolname from pg_roles where rolname='pipeline_writer';
select has_table_privilege('pipeline_writer','topic_intelligence.topic_trend','INSERT'); -- expect false
select has_function_privilege('pipeline_writer',
  'topic_intelligence.upsert_topic_trend(text,uuid,text,date,int,int,int,numeric,text,boolean,text,uuid)',
  'EXECUTE'); -- expect true
```

### 3. Temporarily expose `topic_intelligence` for the PostgREST load
The loader writes with `Content-Profile: topic_intelligence`; PostgREST only honors a profile
whose schema is in the exposed list. On the **branch**, set Data API **Exposed schemas** to:
```
public, signal_read, topic_intelligence
```
(anon stays safe: no anon grant on `topic_intelligence.topics`, and the other three are RLS/grant-
limited to counts via views). *Alternative if you prefer never to expose it: skip this step and
load via `psql`/`\copy` instead of the Python script.*

### 4. Run the carry-forward
Env (loader reads at runtime, nothing hardcoded):
- from `gtm-os/.env`: `SUPABASE_SPINE_URL`, `SUPABASE_SPINE_SERVICE_KEY`
- from `Empire_State_Events_Pipeline_Take_3/.env`: `SUPABASE_API_KEY`
- **`SUPABASE_URL`** → set to the **branch** Data API URL for this run (the script defaults to the
  production URL `https://oicikjyzmxqfomrrqkvf.supabase.co` if unset — override it to hit the branch).

```bash
# dry run first — source counts only, no writes:
python supabase/scripts/carry_forward_topic_intelligence.py --dry-run
#   expect: topic_cluster 30 / topics 170 / topic_trend 96 / topic_pair_metric 286

# then the real copy (FK-safe order, idempotent upsert):
SUPABASE_URL="https://<branch-ref>.supabase.co" \
python supabase/scripts/carry_forward_topic_intelligence.py
```

### 5. Validate (AC1a) — see (c). Then re-set exposed-schemas — see (e).

---

## (c) AC1a validation — carried tables EXACT-MATCH the frozen spine

AC1a = **port fidelity**: same input, exact-match vs the **frozen** gtm-os spine (this is a copy,
so exact-match is the correct test — pre-mortem #1). Because floats/timestamps/ordering can create
brittle "not-EXACT" noise (pre-mortem #9), define canonical determinism:
- **canonical ordering:** compare with a fixed `ORDER BY <primary key>`.
- **ε on floats:** `momentum`, `intersection_score`, `cluster_assignment_confidence` compared with
  `abs(a-b) <= 1e-9`; treat `NULL` == `NULL`.
- **timestamps / arrays:** copied verbatim (no moddatetime trigger on the target — 0001 header), so
  `last_modified_at`, `computed_at`, `bridge_entity_ids[]` must match byte-for-byte.

**Approach — three checks per table:**

1. **Row counts match** (fast tripwire). On source (`Accept-Profile: signal`) and target
   (`Accept-Profile: topic_intelligence`), `count=exact` per table → must be equal
   (30 / 170 / 96 / 286).

2. **Aggregate fingerprint match** (cheap full-table equality). Run the SAME query on both DBs and
   compare the single output row. Example for the fully-numeric tables:
   ```sql
   -- topic_trend fingerprint (run on spine as signal.*, on target as topic_intelligence.*)
   select count(*)                              as n,
          sum(event_count)                      as sum_ev,
          sum(distinct_speaker_count)           as sum_spk,
          round(sum(coalesce(momentum,0))::numeric, 9) as sum_mom,
          md5(string_agg(content_hash, '|' order by trend_id)) as hash_fp
   from signal.topic_trend;                      -- topic_intelligence.topic_trend on target
   ```
   ```sql
   -- topic_pair_metric fingerprint
   select count(*)                                   as n,
          sum(cooccurrence_event_count)              as sum_cooc,
          sum(bridge_person_count)                   as sum_bridge,
          sum(cardinality(bridge_entity_ids))        as sum_bridge_ids,
          md5(string_agg(content_hash, '|' order by pair_metric_id)) as hash_fp
   from signal.topic_pair_metric;
   ```
   `content_hash` is gtm-os's own computed lineage digest, so an equal `md5(string_agg(content_hash
   ORDER BY pk))` proves every carried row's identity matches the frozen source. Do the analogous
   fingerprint for `topic_cluster` (agg over `canonical_slug`, `curation_status`) and `topics`
   (agg over `canonical_slug`, `cluster_id`, `cluster_assignment_confidence`).

3. **Row-level diff on mismatch only.** If (1) or (2) disagree, pull both tables ordered by PK
   (the loader already reads `order=<pk>`) and diff client-side with the ε rule above to find the
   offending rows. A clean re-run of the idempotent loader should converge (upsert, no trigger).

**AC1a passes when:** counts equal AND fingerprints equal for all four tables. Record the result
against the freeze timestamp from step 0.

---

## (d) Security advisor check (on the branch)

Run **`get_advisors`** (security lint) **on the branch** — **from the account that OWNS the project
(A.Yedi)**, since the MCP on the other account cannot see this project. In the A.Yedi dashboard this
is **Advisors → Security**. Expect zero new criticals from this change; specifically confirm:
- no "security_definer view" finding on `signal_read.*` (both must be `security_invoker`);
- no "RLS disabled" finding on any `topic_intelligence.*` table;
- no unexpected anon-readable exposure of `topic_intelligence.topics` or `bridge_entity_ids`.
Gate go-live on a clean advisor pass (pre-mortem #4, #5).

---

## (e) Exposed-schemas change (go-live)

After AC1a + advisors pass, set the **final** Data API **Exposed schemas** (remove the transient
`topic_intelligence` from step 3):
```
public, signal_read
```
- `signal_read` = the only new public surface (anon-safe views).
- `topic_intelligence` **excluded** — no direct API path to base tables.
- exposed-schemas is **project-wide** (touches empire-state-hub's live `public` surface too —
  pre-mortem #5): apply in a **low-traffic window**, right after the advisor gate. This is also
  guided in the 0003 config note.

---

## (f) Hub-wiring follow-ups (separate steps, after go-live)

Both are downstream of a live `signal_read` and are tracked separately (not part of this DDL bundle):
1. **empire-state-hub panel** — add a "Topic movement / intersections" panel that reads
   `signal_read.v_topic_movement` + `v_topic_intersections` (anon key, public surface).
2. **gtm-os-hub `/signal`** — repoint its `/signal` view to the same two canonical views, so both
   hubs read ONE source (ADR-1: "wire both hubs to one view").

---

## (g) Rollback

Increment 1 is reversible by construction — `public` is untouched throughout.
1. Revert Data API exposed-schemas back to **`public`** (drop `signal_read`).
2. Drop the two schemas (cascades views, tables, the definer function):
   ```sql
   drop schema if exists signal_read cascade;
   drop schema if exists topic_intelligence cascade;
   ```
3. Revoke the `public` grants and drop the role if nothing depends on it:
   ```sql
   revoke all on public.company, public.person, public.topic, public.event,
     public.event_entity from pipeline_writer;
   drop role if exists pipeline_writer;
   ```
4. Delete the branch (if validation failed) — production never changed.
5. Re-enable the gtm-os nightly `compute_topic_intelligence` job if you unfroze the plan
   (undo step 0).

> The destructive dedup / topic-set reconciliation / spine decommission is **Increment 2** — a
> separately gated workstream (PITR restore drill + N-night validation + merge-map). Not here.
