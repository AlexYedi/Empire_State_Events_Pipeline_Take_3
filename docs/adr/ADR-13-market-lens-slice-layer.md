# ADR-13 — Market lens + slice layer: conformed dimensions, Type 2 history, one reader

**Status:** **Proposed 2026-11-04** (draft for review; YED-307). Alex approved the design's five decisions on 2026-11-04 (`docs/proposals/2026-11-04-market-lens-and-slices.md` §9). This becomes Accepted once migration 0016 passes `supabase/scripts/rehearse_0016.py` on the twin and Alex has pasted it into prod.
**Governs:** how facts in the MI graph are sliced by lens, theme, company segment and time; the schema `mi`; the lane registry and ledger; and the one read path out of the semantic layer, `public.mi_slice`.

## Context

The graph holds two views of the world and reports one. The attended lens has 84 events and 1,384 first-hand claims. The research lens has 3,543 research-lane claims taken from about 35 briefs. Today nothing counts the research lens, slices it or links it to a theme. Three market lanes have died (inbox miner, `trend_radar`, `morning_refresh`), and all for the same reason: they had no schedule, no weekly reader and no ledger (proposal §0.5, L1–L3).

Two things block any honest comparison across lenses:
1. **Theme membership has no history.** `public.topic.cluster_id` holds only the current value. As soon as a surface stores week-over-week numbers, a topic merge or a re-cluster silently rewrites every past delta (dynamic-taxonomy proposal §9: the hard ordering constraint).
2. **No conformed dimensions.** Each consumer would otherwise derive lens, week and theme in its own way, so the hub number and the session number would drift apart. Two consumer PRs (slice.py #273 and hub#58) have already coded against incompatible guesses.

## Decision

| # | Decision | Why |
|---|---|---|
| 1 | **Lens is derived, never stored:** `mi.lens_of(kind, source, lane)`, one immutable function. Rules are checked in order: job kinds → `job`; `lane='research'` or source `substrate:research*` → `research`; `attended` → `attended`; `market`, `funding`, `launch` or `exec_move` → `market`; anything else → NULL (unlensed). | One place, so nothing can drift. Job comes first so YED-149 isolation always wins. Research comes before attended because 705 research claims are attached to attended events and are still research. |
| 2 | **Theme membership is a Type 2 slowly changing dimension:** `public.topic_cluster_membership`, with at most one open row per topic (partial unique index). **It is kept in sync by the database:** `public.topic_membership_sync()` (SECURITY DEFINER, pinned `search_path`) runs AFTER INSERT and AFTER UPDATE OF `cluster_id, metadata` on `public.topic`. A changed cluster closes the open row and opens a new one (`reassign`, carrying `cluster_assigned_by` and `cluster_assignment_confidence`); a null cluster or a new tombstone closes it; an unchanged cluster is a no-op. The seed is today's `cluster_id` for non-tombstoned topics, with `valid_from = 2026-08-08`: no assignment timestamp exists in prod, and the last assigned topic was created that day. Read it through `mi.theme_as_of(topic, ts)`. That function returns `theme_resolved = 'asof'` when a row covers `ts`. It returns `'seed'` when `ts` is earlier than the topic's first row, in which case the earliest membership is projected back. | Kimball SCD2. This is the §9 precondition. The trigger means one topic write keeps both records true, so no producer (session assignment, `substrate.py merge`) can forget the close/open pair (proposal §8 FMEA row). It also watches `metadata`, because merge tombstones keep their `cluster_id`. The `seed` flag keeps 14 years of research claims inside theme slices without pretending they were classified at the time. |
| 3 | **Company segment is Type 2 as well:** `public.company_segment_history`. Every text column is a constrained token or a short label, and there are no contact fields. | A Series B in October must still read as an earlier stage for September facts. |
| 4 | **Lanes are registered, then ledgered:** `public.lane_registry` holds one row per lane (schedule, owner, consumer, kill rule, `active`, freshness thresholds) and is seeded with lanes 0–5, all inactive. `public.lane_run` holds one row per run, with a foreign key to the registry. | A lane that has never run can still FAIL: an active lane with no finished run is FAIL. Seeding them inactive keeps the nightly from going red on day one; each lane's producer PR flips it to active. |
| 5 | **`event.signal_type`** is a nullable column with a CHECK over (`hiring_pulse`, `paper`, `model_release`, `news`, `partnership`, `layoff`). No `event_week` column is added. Weekly market producers set `event_date` to the Sunday that ends the ISO week, at 00:00 UTC. `substrate.py ensure-event` dedups on (source, kind, signal_type, event_date, company edge). | The company link lives in `event_entity`, and a unique index can't span two tables, so the week-dedup key can't be expressed as an index (contract item 6, option b). |
| 6 | **Schema `mi` holds the semantic layer, as views only.** It has `fact`, `fact_topic`, `fact_company`, `theme_week`, `theme_lead_lag`, `company_timeline`, `company_cohort` and `hiring_around_theme`. All are `security_invoker`. The schema is not API-exposed, and USAGE is revoked from public, anon and authenticated. Job-lens facts never enter any view's counts. | Semantic layer (Codd's OLAP; LookML and dbt metrics in their modern form). At thousands of rows, Postgres views are the whole engine. |
| 7 | **One reader:** `public.mi_slice(view, filters)`. It is STABLE and SECURITY DEFINER, with a pinned `search_path`, static SQL per view and a server-side allowlist of five views. EXECUTE is granted only to `service_role` (least privilege, proposal §4). The six named business slices (`attended_vs_market_by_theme_8w` and the rest, proposal §4) are compositions over these views and live in `slices.md` / `slice.py`, not in the database. | One door, with no dynamic SQL and so no injection surface. Adding a view means a reviewed `create or replace`. |
| 8 | **Additive only.** The rollback drops only what 0016 adds. The rehearsal on the twin includes two planted faults and the full nightly chain (L7), and must finish with an identical schema fingerprint. | `migration-playbook.md`; ADR-4 decisions 2 and 6; ADR-10 decision 5. |

## Consumer contract (source of truth for slice.py #273 and hub#58)

**Call.** `POST` or `GET /rest/v1/rpc/mi_slice` with `{"view": "<name>", "filters": {...}}`, using the service-role key. The function is STABLE, so PostgREST runs it in a read-only transaction, and GET works.

- `view` must be one of: `mi.theme_week`, `mi.theme_lead_lag`, `mi.company_timeline`, `mi.company_cohort`, `mi.hiring_around_theme`. Anything else raises.
- `filters` keys: `weeks` (1–104, default 8), `lens` (`attended`, `research` or `market`), `theme_id`, `company_id`, `limit` (1–5000, default 1000). Unknown keys raise.

**Returns** a single jsonb object:

```json
{"view": "mi.theme_week",
 "rows": [ ... ],
 "denominators": {
   "attended": {"events": 0},
   "research": {"briefs": 0},
   "market":   {"facts_by_source": {"<source_system>": 0}, "watchlist_covered": 0, "watchlist_size": 0},
   "job":      {"boards_scanned": 0}},
 "window": {"from_week": "YYYY-Www", "to_week": "YYYY-Www", "anchored_on": "YYYY-MM-DD"}}
```

- **Window.** The window is the `weeks` ISO weeks ending in the week of `current_date`. It is anchored on today, never on the latest row, so a stalled pipeline reads as stale. It filters the rows of `mi.theme_week` and `mi.company_timeline`. `mi.theme_lead_lag` and `mi.hiring_around_theme` carry their own fixed 8-week windows, also anchored on today. `mi.company_cohort` is all-time.
- **Denominators** are computed in SQL, for the window, per lens, and never summed. All four lenses are always present. They bucket on `asserted_week`, the same basis as the rows.
  - `attended.events`: attended events in the window.
  - `research.briefs`: distinct source documents of research-lens claims in the window.
  - `market.facts_by_source`: market facts in the window, keyed by `event.source` prefix.
  - `watchlist_size`: companies carrying a target tier.
  - `watchlist_covered`: watchlist companies with at least one market fact in the window.
  - `job.boards_scanned`: distinct companies with a job-lens posting in the window. This is an approximation; see the open questions.

**`mi.theme_week`** has one row per theme × lens × ISO week, and no total column. Columns, in order: `theme_id, theme, iso_week, lens, facts, distinct_companies, distinct_sources, general_facts, floor_flag, theme_resolved`.
- `iso_week` is `'YYYY-Www'` and sorts chronologically as a string.
- `floor_flag` is `'insufficient_data'` when the theme × lens has fewer than 3 facts in the 8 ISO weeks ending at that row's week; otherwise it is `'ok'`. **When the flag is `insufficient_data`, `facts` is still returned, and consumers must not render it.**
- `theme_resolved` is `'seed'` if any fact in the cell took its theme from the pre-history fallback, else `'asof'`. Print it.
- `general_facts` counts facts tagged to the theme's `'<Theme> (general)'` topic. It is 0 until those topics exist.

**`mi.theme_lead_lag`** has one row per theme. Columns: `theme_id, theme, market_first_seen, attended_first_seen, market_lead_weeks, attended_count_8w, market_count_8w, lead_lag_shown`.
- **`market_lead_weeks` = (`attended_first_seen` − `market_first_seen`) in weeks. A positive value means the market led.**
- `lead_lag_shown` is true only when both 8-week counts are at least 3. When it is false, `market_lead_weeks` is still returned, and consumers must not render it.
- There are no `band_low` or `band_high` columns; the permutation band is Phase B.

**`public.lane_run`** columns: `run_id, lane, started_at, finished_at, status, items_seen, items_written, items_refused, credits_spent, error`.

**Freshness rule** (for the health check, not yet wired): staleness = days since the lane's latest run with status `success` or `partial` and a `finished_at`. FLAG when staleness ≥ `freshness_flag_days` (default 7). FAIL when it is ≥ `freshness_fail_days` (default 14). An **active** lane with no such run is FAIL. Inactive lanes are not alarmed. `segment_enrichment` is seeded at 92 and 120 days because it refreshes quarterly.

## Write path: all four new tables live in `public` (decided 2026-11-04)

`topic_cluster_membership`, `lane_registry`, `lane_run` and `company_segment_history` are all in `public`. **Why:** `spine_client.py`, the one write path (ADR-9), writes through PostgREST to `public` only; it has no `Content-Profile` support. Migration 0003 deliberately keeps `topic_intelligence` off the API. Tables there could not be written by any sanctioned producer. The rejected alternatives were definer write functions plus RPC support in the guard (more guarded code), and exposing `topic_intelligence` (reverses 0003).

The protection is the same as every spine table: RLS on, no policies, and `revoke all` from public, anon and authenticated (default privileges in `public` would otherwise grant them ALL). The service-role key via `spine_client` is the only writer. `topic_cluster` stays in `topic_intelligence`; membership references it by foreign key.

## Platform constraints

- **The session pooler drops `PGOPTIONS`.** `-c default_transaction_read_only=on` is silently ignored; a prod "read-only" session came up with `default_transaction_read_only = off`. Prod read sessions must `set session characteristics as transaction read only` (and `set default_transaction_read_only = on`) inside the session, then assert `show transaction_read_only` = `on` before any query. Recorded in `.claude/references/platform-constraints.md`.
- `btree_gist` is not installed, so membership interval overlap is a verify check, not an exclusion constraint.

## Consequences

- Every slice prints a lens, a denominator and a resolution flag. The "never sum across lenses" rule holds by construction, because no view has a total column.
- Membership tracks `topic.cluster_id` automatically, so producers write only the topic. The cost: every topic insert or cluster/tombstone update does one extra indexed lookup and write. A `cluster_assigned_by` value outside (`llm`, `session`, `human`, `merge`) now **raises and aborts the topic write**. That is loud by design; widening the vocabulary is a migration.
- `load_twin.py` loads topics with COPY, which fires the insert trigger, so after a twin refresh the membership rows start at load time rather than 2026-08-08. Re-applying 0016 does not re-seed topics that already have rows.
- The prod VERIFY block is read-only. The trigger's behaviour is proved by a separate VERIFY_TWIN block that writes inside a rolled-back transaction. It runs on the twin only.
- `mi.fact` includes unlensed rows (NULL lens). Today that is the 796 occasion-less `notion_prior` claims. The views leave them out of every count, and the coverage stays visible.
- Rollback after any lane has written loses those rows and every `event.signal_type` value. It stays valid; it just isn't free.
- `load_twin.py` truncates with CASCADE, which empties the membership and segment tables.
- 14 merge tombstones in prod still carry a `cluster_id`. The seed excludes them, and verify reports the count as `info_tombstones_with_cluster_id` without failing.

## Open questions for review

Resolved 2026-11-04: the write-path schema (`public`); the sync trigger (in 0016); `mi_slice` EXECUTE (`service_role` only); the lens rule order (job → research → attended → market, else NULL).

1. **`notion_prior` claims stay unlensed (decided).** The 796 occasion-less `notion_prior` claims are Alex's prior context, not a witnessed room, a research brief or a market signal. They stay out of every lens count. Revisit only if a slice needs a "prior context" lens of its own.
2. `job.boards_scanned` approximates "boards scanned" with "companies with a posting". A true count needs role-radar to log its scans, for example as a lane.
3. The watchlist is defined only by target tier (empty today). The proposal's "top 100 by relevance among attended-linked companies" is not encoded.

## Relations

- Implements `docs/proposals/2026-11-04-market-lens-and-slices.md` §3–§4 and §6 Phase A item 1. Satisfies the §9 precondition in `docs/proposals/2026-11-03-dynamic-topic-taxonomy.md`.
- Bound by ADR-9: no PII columns; every write goes through `spine_client`. The `spine_client.ALLOW` rows ship in their own guarded PR.
- Extends ADR-10: claims stay first-class, and `mi.fact` reads them as they are. ADR-4 and ADR-10 decision 5 govern the additive-first and rehearsal discipline.
- Migration: `supabase/migrations/0016_mi_semantic_layer.sql`. Rehearsal: `supabase/scripts/rehearse_0016.py`.
