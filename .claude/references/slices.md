# Canonical slices (YED-304, market lens + slice layer)

Named slices from the market-lens design (`docs/proposals/2026-11-04-market-lens-and-slices.md` §4).
They are the reviewable, versioned registry `.claude/scripts/slice.py` loads: each JSON descriptor
below is a `public.mi_slice(view, filters)` call — the one door into the `mi` schema. The views' SQL
and the RPC both live in **migration 0016 (`mi_semantic_layer`, ADR-13), merged to main (`f9458b8`)
and applied to prod** — the shapes below mirror that migration, not the pre-merge proposal.
`slice.py` runs selftests against `supabase/fixtures/mi_slice_fixtures.json` offline and stays on
the twin unless `--allow-prod` is passed.

Row contract every payload must satisfy (slice.py validates, fails closed — design §3.3):

1. **Never sum across lenses.** Lensed rows carry `lens ∈ attended · research · market · job`;
   `lens='all'` is a contract error. Lenses render as adjacent columns, each with its own
   denominator. `mi.theme_lead_lag` and `mi.company_cohort` are lens-less views — no lens column
   is implied for them.
2. **Denominators, all four, always.** 0016 returns `denominators` for every lens whether or not
   rows exist: attended `{events}` · research `{briefs}` · market `{facts_by_source,
   watchlist_covered, watchlist_size}` · job `{boards_scanned}`. A missing canonical key is a
   contract error (§3.3 rule 2). The watchlist counts are the ONLY way the private target list
   appears anywhere — never a company-level tier column (ADR-13 F1).
3. **Floors before labels.** On `mi.theme_week`, a theme × lens cell under 3 facts in the window
   carries `floor_flag: "insufficient_data"` and renders as exactly that — the number is
   suppressed, not shown "for context". A row missing `floor_flag` is a contract error
   (fail closed; raw counts are not a pass).
4. **General-topic counts labelled.** Counts on a theme's `(general)` catch-all topic are
   labelled (`N (M general)`, rows marked `[general]`) — never merged into named-topic counts
   (PR #267 rule).
5. **Time, anchored.** The window is `weeks` ISO weeks ending in the week of `current_date` —
   anchored on today, never on the latest row. `mi.company_timeline` carries both
   `first_asserted_at` (when it was true) and `last_asserted_at` (when we learned it).
6. **The lead gate.** Lead/lag lives in its own view, `mi.theme_lead_lag`. `market_lead_weeks`
   renders only when `lead_lag_shown` is true (both lenses clear the 3-fact floor). When false —
   the correct null state (e.g. a market lens with 0 facts in the last 8 weeks) — the lead renders
   `insufficient_data` with the 8-week counts beside it: rendered, not hidden, not special-cased.
7. **Markers, not columns.** `theme_resolved` (e.g. `"seed"`) renders as a `[seed]` label on the
   dimension; id columns (`theme_id`, `company_id`) are join keys, carried but not displayed.

Filters the RPC accepts (unknown keys raise server-side; slice.py pre-flights the same
allowlist and fails closed before the call): `weeks` (1..104, default 8) · `lens`
(attended|research|market) · `theme_id` (uuid) · `company_id` (uuid) · `limit` (1..5000).

```json
[
  {"name": "attended_vs_market_by_theme_8w",
   "view": "mi.theme_week",
   "lenses": ["attended", "market"],
   "filters": {"weeks": 8},
   "question": "Q1 — is my room ahead of or behind the market on each theme? (lead/lag in weeks)"},
  {"name": "theme_lead_lag_8w",
   "view": "mi.theme_lead_lag",
   "lenses": [],
   "filters": {},
   "question": "Q1b — per theme, did the market lead the room? market_lead_weeks renders only on lead_lag_shown; otherwise insufficient_data with both 8-week counts beside it."},
  {"name": "companies_heating_8w",
   "view": "mi.company_timeline",
   "lenses": ["market"],
   "filters": {"weeks": 8},
   "question": "Q5a — which companies are accumulating market facts week over week (funding, hiring, launches)? Scope one with company_id at runtime."},
  {"name": "funded_not_attended_90d",
   "view": "mi.theme_week",
   "lenses": ["attended", "market"],
   "filters": {},
   "blocked_filters": {"kinds": ["funding"], "window_days": 90},
   "status": "blocked_on_rpc",
   "question": "Q3 — which themes does the market fund that my rooms ignore? Read the adjacent columns: market funding facts next to the attended tag count."},
  {"name": "target_companies_heating_qtd",
   "view": "mi.company_timeline",
   "lenses": ["market"],
   "filters": {},
   "blocked_filters": {"target_tier": ["A", "B"], "period": "qtd"},
   "status": "blocked_on_rpc",
   "question": "Q5 — which of my target companies are heating up (funding, hiring, launches) this quarter? Tier flags live in the DB and never render on a public hub page. NOTE: a target_tier filter needs an ADR-13 privacy review, not just a migration."},
  {"name": "new_nyc_companies_by_quarter",
   "view": "mi.company_cohort",
   "lenses": ["market", "attended"],
   "filters": {},
   "blocked_filters": {"cohort": "first_seen_quarter", "hq_metro": "nyc"},
   "status": "blocked_on_rpc",
   "question": "Q6 — which NYC companies first appeared this quarter, in which lens?"},
  {"name": "research_without_room_corroboration",
   "view": "mi.theme_week",
   "lenses": ["research"],
   "filters": {},
   "blocked_filters": {"attended_corroboration": "none", "window_days": 90},
   "status": "blocked_on_rpc",
   "question": "Q8 — what did the research briefs establish that no event has said out loud?"},
  {"name": "frontier_vs_room",
   "view": "mi.theme_week",
   "lenses": ["market", "attended"],
   "filters": {},
   "blocked_filters": {"signal_types": ["paper", "model_release"], "window_weeks": 8},
   "status": "blocked_on_rpc",
   "question": "Q7 — where does the research frontier (papers, model releases) sit relative to what speakers claim? Papers and model releases are market events (the market lens); `research` means claims from briefs."}
]
```

Descriptors marked `blocked_on_rpc` keep their original question and the exact filters they need
(`blocked_filters`) — the current `mi_slice(view, filters)` signature cannot express them
(`kinds`, `signal_types`, `target_tier`, `period`, `attended_corroboration`, `hq_metro`), so
`list` shows them and `run` refuses with "needs an RPC extension" instead of silently rewording
what the slice answers. A `target_tier` filter additionally needs an ADR-13 privacy review before
any migration. Live-verified 2026-11-04: 0 market facts in the last 8 weeks — the market column
legitimately renders "no information (0 facts in window)".

## Cohort predicates

Saved predicates, not a table — persisted only when a surface needs them (design §4). Not
executable here; they name the rows a slice's filters should select.

```json
[
  {"name": "first_seen_2026Q3_any_lens", "predicate": "company_cohort.first_seen_quarter == '2026-Q3'"},
  {"name": "market_leads_attended_4w", "predicate": "theme_lead_lag.market_first_seen <= attended_first_seen - 28 days, lead_lag_shown true (both lenses above the 3-fact floor)"},
  {"name": "seed_to_a_agentic_infrastructure", "predicate": "company_segment_history transition seed → series_a in the last 90 days, industry == agentic infrastructure (read via company_cohort's current-segment columns)"},
  {"name": "watchlist_coverage", "predicate": "aggregate only — the private target list never leaves the DB except as mi_slice's market denominators (watchlist_covered / watchlist_size), never as company-level tier rows"}
]
```

## Running

```bash
python3 .claude/scripts/slice.py list                                  # the canonical slices
python3 .claude/scripts/slice.py run attended_vs_market_by_theme_8w
python3 .claude/scripts/slice.py run frontier_vs_room --lens market    # one lens, others excluded, never merged
python3 .claude/scripts/slice.py adhoc --view mi.company_timeline --filters '{"weeks": 12}'
python3 .claude/scripts/slice.py --selftest                            # offline, fixtures only
```

Live runs need `SLICE_API_KEY` (the twin `ytfzzsxcxxbejnowmkmk` service key — the repo `.env`
holds the prod key and slice.py deliberately never reads it). Read-only prod verification uses a
`SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY` session with `transaction_read_only = on`
asserted before any SELECT — the Supabase pooler ignores PGOPTIONS, so the SET statement is the
reliable path (same finding as `supabase/scripts/topic_intel_compute.py`).
