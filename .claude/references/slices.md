# Canonical slices (YED-304, market lens + slice layer)

Named slices from the market-lens design (`docs/proposals/2026-11-04-market-lens-and-slices.md` §4).
They are the reviewable, versioned registry `.claude/scripts/slice.py` loads: each JSON descriptor
below is a `public.mi_slice(view, filters)` call — the one door into the `mi` schema. The views'
SQL definitions land with **migration 0016 (`mi_semantic_layer`, ADR-13)**; until that migration is
applied, `slice.py` runs selftests against `supabase/fixtures/mi_slice_fixtures.json` only and
refuses prod (`--allow-prod` gate). When 0016 lands, append each view's SQL to this file.

Row contract every payload must satisfy (slice.py validates, fails closed — design §3.3):

1. **Never sum across lenses.** Every row carries `lens ∈ attended · research · market · job`;
   `lens='all'` is a contract error. Lenses render as adjacent columns, each with its own denominator.
2. **Denominators per lens.** `denominators` must name one for every lens present in rows:
   attended = events in window · research = briefs (documents) in window · market = facts per
   source in window + watchlist coverage · job = boards scanned.
3. **Floors before labels.** A theme × lens cell under 3 facts in 8 weeks carries
   `floor_flag: "insufficient_data"`; a lead/lag figure on a floored cell renders "no information".
4. **General-topic counts labelled.** Counts on a theme's `(general)` topic arrive as
   `general_facts` (labelled `N (M general)`) or as explicit `topic: "(general)"` rows — never
   merged into named-topic counts (PR #267 rule).
5. **Time.** Slices bucket on `asserted_at` (when it was true); `observed_at` (when we learned it)
   is carried and printed beside it. A 2024 funding round ingested today is not this week's news.
6. **Floors and the lead gate.** Every row carries `floor_flag` (`ok` or `insufficient_data`) —
   a row without one is a contract error (fail closed; raw counts are not a pass). Lead/lag
   figures render only when the payload carries `lead_lag_shown: true` (`mi.theme_lead_lag`
   computes it: true only when BOTH lenses clear the floor). A row-level `theme_resolved`
   marker (e.g. `"seed"`) renders as a `[seed]` label on the dimension, never a column.
7. **Pinned response shape.** The RPC returns `{view, rows, denominators, window}` — qualified
   view names (`mi.theme_week`, …) with the requested view and time window echoed back.
   `mi_slice(view, filters)` is STABLE and GET-callable; full columns land in ADR-13's
   consumer-contract section on the 0016 PR.

```json
[
  {"name": "attended_vs_market_by_theme_8w",
   "view": "mi.theme_week",
   "lenses": ["attended", "market"],
   "filters": {"lenses": ["attended", "market"], "window_weeks": 8},
   "question": "Q1 — is my room ahead of or behind the market on each theme? (lead/lag in weeks)",
   "denominators_expected": ["attended", "market"]},
  {"name": "funded_not_attended_90d",
   "view": "mi.theme_week",
   "lenses": ["attended", "market"],
   "filters": {"lenses": ["attended", "market"], "window_days": 90, "kinds": ["funding"]},
   "question": "Q3 — which themes does the market fund that my rooms ignore? Read the adjacent columns: market funding facts next to the attended tag count.",
   "denominators_expected": ["attended", "market"]},
  {"name": "target_companies_heating_qtd",
   "view": "mi.company_timeline",
   "lenses": ["market"],
   "filters": {"lenses": ["market"], "target_tier": ["A", "B"], "period": "qtd"},
   "question": "Q5 — which of my target companies are heating up (funding, hiring, launches) this quarter? Tier flags live in the DB and never render on a public hub page.",
   "denominators_expected": ["market"]},
  {"name": "new_nyc_companies_by_quarter",
   "view": "mi.company_cohort",
   "lenses": ["market", "attended"],
   "filters": {"cohort": "first_seen_quarter", "hq_metro": "nyc"},
   "question": "Q6 — which NYC companies first appeared this quarter, in which lens?",
   "denominators_expected": ["market", "attended"]},
  {"name": "research_without_room_corroboration",
   "view": "mi.theme_week",
   "lenses": ["research"],
   "filters": {"lenses": ["research"], "window_days": 90, "attended_corroboration": "none"},
   "question": "Q8 — what did the research briefs establish that no event has said out loud?",
   "denominators_expected": ["research"]},
  {"name": "frontier_vs_room",
   "view": "mi.theme_week",
   "lenses": ["market", "attended"],
   "filters": {"lenses": ["market", "attended"], "window_weeks": 8, "signal_types": ["paper", "model_release"]},
   "question": "Q7 — where does the research frontier (papers, model releases) sit relative to what speakers claim? Papers and model releases are market events (the market lens); `research` means claims from briefs.",
   "denominators_expected": ["market", "attended"]}
]
```

## Cohort predicates

Saved predicates, not a table — persisted only when a surface needs them (design §4). Not
executable here; they name the rows a slice's filters should select.

```json
[
  {"name": "first_seen_2026Q3_any_lens", "predicate": "company_cohort.first_seen_quarter == '2026-Q3'"},
  {"name": "market_leads_attended_4w", "predicate": "theme_lead_lag.market_first_seen <= attended_first_seen - 28 days, both lenses above the 3-fact floor"},
  {"name": "seed_to_a_agentic_infrastructure", "predicate": "company_segment_history transition seed → series_a in the last 90 days, industry == agentic infrastructure"},
  {"name": "target_tier_A_B", "predicate": "company.metadata.target_tier in ('A','B') — private, never rendered publicly"}
]
```

## Running

```bash
python3 .claude/scripts/slice.py list                                  # the six canonical slices
python3 .claude/scripts/slice.py run attended_vs_market_by_theme_8w --since 2026-09-08
python3 .claude/scripts/slice.py run frontier_vs_room --lens market  # one lens, others excluded, never merged
python3 .claude/scripts/slice.py adhoc --view mi.company_timeline --filters '{"target_tier":["A","B"]}'
python3 .claude/scripts/slice.py --selftest                            # offline, fixtures only
```

Live runs need `SLICE_API_KEY` (the twin `ytfzzsxcxxbejnowmkmk` service key — the repo `.env`
holds the prod key and slice.py deliberately never reads it) and migration 0016 applied to that
project. Until then the offline surface is `--selftest`.
