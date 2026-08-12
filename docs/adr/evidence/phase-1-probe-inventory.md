# Phase 1 — Live probe inventory & crosswalk feasibility

- **Status:** Complete (2026-08-07). **Method:** read-only `curl` GET against each project's PostgREST REST API; exact counts from `Content-Range` (`Prefer: count=exact` + `Range: 0-0`); non-public schemas via `Accept-Profile`. No writes, no RPC, no Supabase MCP. Every number below is from a live HTTP response.
- **Linear:** YED-130. **Feeds:** ADR-1 (data layer).

## Headline finding — gtm-os is a downstream projection of Empire

Not two peer graphs. **gtm-os ⊂ Empire.** 100% of gtm-os's 396 entities and 409 `entity_external_ids` carry `source='events_pipeline'` and an Empire Notion page ID. Deterministic join `Empire.notion_page_id` (de-dashed) ↔ `signal.entity_external_ids.external_id` = **390/396 matched**; the 6 unmatched are newer than gtm-os's last ingestion (external_ids timestamped 2026-07-15). **The highest-risk item (entity-ID re-keying / false-merge) is de-risked — a clean deterministic key already exists.**

## A. Per-project inventory (live exact counts)

**Empire MI graph** — `oicikjyzmxqfomrrqkvf` (A.Yedi), schema `public`, REST exposed:
`company` 182 · `person` 232 (FK `company_id→company.id`) · `topic` 160 · `event` 17 · `event_entity` 20. Notion-linked 100%.

**gtm-os Signal spine** — `abkvgihlbwfloentugtd` (Same Old Expressions), schema `signal` (via `Accept-Profile: signal`), REST exposed, **alive**:
`entities` 396 (person 221 / company 175) · `entity_external_ids` 409 (100% events_pipeline) · `events` 59 · `topics` 170 · `signals` 452 · `relations` 629 · `provenance` 624 · `conflict_log` 0 · `suppression` 0 · `ingestion_run` 17 · `source_state` 1 · `topic_cluster` 30 · `topic_trend` 96 · `topic_pair_metric` 286 · `topic_intelligence_health` (view) 6. RPC `compute_topic_intelligence` present (not called).

**GTM_OS_HUB learning plane** — `nnywrmetdoixdbevvsvf` (Same Old Expressions), only `public` exposed:
`v_public_curriculum` 117 · `v_public_progress` 117 · `v_public_submissions` 1. `learning.*` base tables NOT REST-reachable (406 PGRST106 — by design). Unexpected small events mirror in `public`: `events` 4, `event_briefs` 6, `contacts` 0, `content_drafts` 0.

## B. Not retrievable via REST (needs SQL / dashboard / Management API)
RLS policy definitions, role GRANTs, `cron.job` rows, and the exposed-schemas (db-schemas) setting were not directly read. **Exposed schemas inferred from PGRST106 hints:** Empire `public`(+graphql_public); Spine `public, graphql_public, signal` — **`signal_read` NOT exposed/404**; Hub `public, graphql_public` — `learning` not exposed. RPCs not called (read-only guardrail).

## C. Entity-ID crosswalk feasibility (measured)
- **Deterministic key:** Notion page ID — Empire 414/414 (100%), gtm-os 409 external_ids → **390 join today**. Safe, no fuzzy matching. False-merge risk near zero.
- **Secondary keys (for any future independent source):** company domain ~93% both sides; person LinkedIn ~66% both sides; **company LinkedIn 0%**; **email absent both** (Empire 1/232, gtm-os 0/396).
- **Schema-shape mismatch to bridge:** Empire two tables + real FK (`person.company_id → company.id`) vs gtm-os one polymorphic `entities` dim with a denormalized `company_domain` **string** (no FK). Adopting gtm-os's model wholesale **flattens the FK to a string — lossy on graph structure.** The separable rigor worth keeping: provenance, identity-resolution dedup keys, topic-intelligence compute.

## D. Anomalies / flags
1. **Spine alive** — CLAUDE.md "NXDOMAIN/paused-deleted" note is stale; update it.
2. **`signal_read` unbuilt** — the hub read-model layer doesn't exist yet. gtm-os-hub `/signal` is *nothing-to-strand-yet*, not live-empty → build-it-right-once, not a stranding risk.
3. **Single source** — gtm-os `source_state`=1, 100% events_pipeline. The "multi-source signal layer" is currently single-source (Empire).
4. **Dedup machinery never exercised** — `conflict_log`=0, `suppression`=0 despite ~13 implied merges (409 external_ids → 396 entities).
5. **Data gaps** — Empire `company.linkedin_url` 0/182; email absent both graphs.
6. **Hub `public` events mirror** — small (`events` 4, `event_briefs` 6) sitting beside the learning views; confirm intended vs leftover.
7. **Prior claims verified:** gtm-os entities 396 ✓, topic_cluster 30 ✓, Empire topic 160 ✓. gtm-os `topics`=170 ≠ Empire 160 (spine topic set is not a 1:1 copy).

## Consequence for ADR-1
The framing shifts from "merge two peers" to **"collapse a redundant downstream projection + choose the canonical model."** Migration risk is low (deterministic crosswalk). Open decision: single canonical graph (best-of-both model: Empire relational FK + gtm-os rigor) vs formalize the existing source→projection two-tier split. Where topic-intelligence physically lives (schema in Empire project vs separate derived project) and account hosting still to confirm.
