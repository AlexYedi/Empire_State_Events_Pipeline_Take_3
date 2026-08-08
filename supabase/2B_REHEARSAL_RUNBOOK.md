# Increment 2b — Phantom Test Case rehearsal runbook

**Linear:** YED-130 · **Spec:** `specs/2b_relations_to_event_entity_mapping.md` · **PRD §5** (the 7-item gate) · **Decisions:** ADR-4, `increment-2-premortem.md`.

**Naming:** *Empire prod DB* = `oicikjyzmxqfomrrqkvf` (prod). *Phantom Test Case DB* = `ytfzzsxcxxbejnowmkmk` (disposable clone). "canonical" = master record only.

> **Hard gate.** No statement runs against the Empire prod DB until this entire sequence — **including a PROVEN rollback (step 7)** — is green on a fresh Phantom Test Case DB. The build scripts refuse a prod host unless `MI_ALLOW_CANONICAL=1`, which is set ONLY after step 7 passes.

## What's already built (branch `alex/yed-130-increment-2b`)
| Piece | Artifact |
|---|---|
| Event graph + bounding-zone enums | `migrations/0005_increment_2b_canonical_v2_event_graph.sql` |
| Theme dimension (topic_cluster + cluster_id) | `migrations/0006_increment_2b_canonical_v2_entities_clusters.sql` |
| Compute output tables | `migrations/0007_increment_2b_canonical_v2_compute_tables.sql` |
| Compute rewrite (relations→event_entity) | `migrations/0008_increment_2b_canonical_v2_compute.sql` |
| Carry clusters + IRL re-ingest | `scripts/build_2b_canonical_v2.py` |
| Validation oracle (ref impl + invariants) | `scripts/reference_impl_2b.py` |

## Prereqs
- Env: `PHANTOM_TEST_DB_PASSWORD`, `SUPABASE_SPINE_URL`, `SUPABASE_SPINE_SERVICE_KEY`, `PSQL_BIN`. Target defaults to the Phantom Test Case DB — do **not** set `MI_ALLOW_CANONICAL` yet.
- `libpq` psql at `/opt/homebrew/opt/libpq/bin/psql`.

---

## Step 0 — Re-clone a FRESH Phantom Test Case DB from the post-2a Empire prod DB
The twin must mirror the *current* (post-2a) prod state, not the pre-2a baseline. Clone/restore, then verify the post-2a counts before proceeding:
```
select 'topic' t, count(*) from public.topic
union all select 'company', count(*) from public.company
union all select 'person',  count(*) from public.person
union all select 'topic_crosswalk',  count(*) from topic_intelligence.topic_crosswalk
union all select 'entity_crosswalk', count(*) from topic_intelligence.entity_crosswalk;
-- expect ~ topic 185, company 183, person 232, topic_crosswalk 170, entity_crosswalk 396
```

## Step 1 — Apply the canonical_v2 structure + compute (0005→0008)
```
for f in 0005 0006 0007 0008; do
  "$PSQL_BIN" "$CONN" -v ON_ERROR_STOP=1 -f supabase/migrations/${f}_*.sql
done
```
Expect: schema `canonical_v2` with event/event_entity (enums), company/person/topic (+cluster_id), topic_cluster, ingestion_run, topic_trend, topic_pair_metric — all RLS deny-all — and the `compute_topic_intelligence` function.

## Step 2 — Build the graph (dry-run, then for real)
```
python supabase/scripts/build_2b_canonical_v2.py --dry-run    # sanity: ~59 events, ~629 relations
python supabase/scripts/build_2b_canonical_v2.py              # copy + carry clusters + re-ingest
```
Gate: the **zero-orphan** assertion passes; `UNRESOLVED` is 0 (or every unresolved edge is explained — a gtm entity/topic not in the crosswalk). Investigate any nonzero before continuing.

## Step 3 — Recompute
```
"$PSQL_BIN" "$CONN" -c "select canonical_v2.compute_topic_intelligence(current_date,'manual');"
```

## Step 4 — Validate (the oracle) — MUST pass
```
python supabase/scripts/reference_impl_2b.py            # add --verbose to see any mismatch
```
Gate: `✅ PASS` — the independent Python reference impl agrees row-for-row with the SQL, and every structural invariant holds. Any `FAIL` stops the rehearsal.

## Step 5 — Negative control (the gate must CATCH a fault)
Inject one deliberate fault on the twin and confirm it is caught, then undo it:
- a false-merge (point an `entity_crosswalk` row at the wrong Empire id) → re-run step 2 → a **zero-orphan or invariant** violation surfaces; **or**
- a mis-scoped tag (flip one re-ingested event to `kind='market'`) → re-run steps 3–4 → the `kind isolation` / `conservation` invariant fails.
A gate that never fails on a planted fault isn't a gate. Undo the injection before step 6.

## Step 6 — Atomic swap (author here, then prove) — AC2b.5
**Design (author the SQL as `staging/2b_swap.sql` + `staging/2b_rollback.sql`, run each inside ONE transaction; prove both on the twin before prod):**
- **Entity graph → `public`:** for each of `event, event_entity, company, person, topic` — `alter table public.<t> rename to <t>_pre2b;` then `alter table canonical_v2.<t> set schema public;`. FKs bind by OID and survive the schema move. `public.*` stays RLS deny-all (anon blocked; server secret-key reads only).
- **Intelligence stays in `topic_intelligence` (NON-exposed — do NOT move to public, or the k≥5 view suppression is bypassed via direct REST):** rename `topic_intelligence.{topic_cluster,topic_trend,topic_pair_metric}` → `*_pre2b`, `alter table canonical_v2.<t> set schema topic_intelligence;`, then re-apply the 0002 anon `grant select` + permissive RLS `*_anon_read` policies to the new tables.
- **Repoint `signal_read` views:** `create or replace` `v_topic_movement` + `v_topic_intersections` (defs are OID-bound, so recreate) over the new `topic_intelligence.*`. Column contract + k≥5 suppression unchanged.
- **Write path:** the nightly job now calls `canonical_v2.compute_topic_intelligence` (now `topic_intelligence`-resident after the move) → wire to the scoped writer role per `0003_roles_grants_definer.sql`.
- **Verify within 60s:** both hub endpoints (`/signal`, `/ops/market-intel`) return non-empty; a poller confirms `signal_read` never served a partial across the swap.

## Step 7 — PROVE the rollback — *the gate the whole plan hinges on*
Run `staging/2b_rollback.sql`: swap `*_pre2b` back into place, move the canonical_v2 tables back, restore the original views. Then assert **exact original row counts, zero loss** (compare to the step-0 snapshot). **If the rollback cannot be demonstrated on the twin, the Empire prod DB is never touched.**

## Step 8 — Time the swap window
Record the swap transaction duration → sizes the prod pipeline **write-freeze** (spec §4). 

## Step 9 — Decommission gate (SEPARATE, dated — never bundled)
Only after prod cutover + N nights of invariants-passing + both hubs healthy + zero outstanding human-review merges: **cold, encrypted logical export of the gtm spine** first, then retire it. Decommission is its own dated approval.

---
### Prod cutover (after step 7 is green)
Repeat steps 1–8 against the Empire prod DB with `MI_ALLOW_CANONICAL=1`, inside the pipeline write-freeze window, with the proven `staging/2b_swap.sql` / `2b_rollback.sql`. Keep `*_pre2b` tables until the N-night validation clears, then drop as a separate step.
