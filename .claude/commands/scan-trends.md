---
description: "Signal scanner — scan what's rising in AI/tech from legitimate non-LinkedIn sources (HackerNews, HuggingFace, curated newsletters), rank by recency-decayed cross-source score, and log approved topics to the Notion Topics DB. Notion-only, human-in-the-loop. No scraping."
argument-hint: "[optional: lookback window + focus, e.g. 'last 3 days, agents and evals']"
---

# /scan-trends — Trend Radar

Run the **trend-radar** methodology to sense what's rising in AI/tech and log the winners to Notion. Methodology lives in `.claude/skills/trend-radar/SKILL.md`.

**Input (all optional):** lookback window and/or focus, e.g. `/scan-trends last 3 days, agents and evals`. With no args: 7-day window, broad AI/tech, Top-10.

## Trigger
Runs when Alex types `/scan-trends [args]` or says "what's trending", "run trend radar", "scan AI trends this week".

## Orchestration shape
Single-thread skill run. Execute `.claude/skills/trend-radar/SKILL.md` end-to-end:
1. **Parse args** → window (default 7d), focus (default broad), Top-N (default 10).
2. **Step 1 — Pull (parallel):** Algolia HN Search (`WebFetch`), HuggingFace papers + models (HF MCP), labeled newsletters (Gmail MCP `search_threads` → `get_thread`). Continue past any single source failure; flag gaps.
3. **Step 2 — Normalize** topics to canonical slugs (`alex:signal-taxonomy`).
4. **Step 3 — Score & rank**: `source_weight × recency_decay (7-day half-life) × normalized_velocity`, then `× cross_source_bonus`. (`alex:signal-scoring`.)
5. **Step 4 — Present ranked digest. STOP for approval.** No Notion writes before Alex picks (all / numbers / none).
6. **Step 5 — Write approved topics**: dedup via `notion-search` scoped to Topics (`collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74`) + `notion-fetch` — NOT `notion-query-data-sources` (plan-gated); existing → append dated note to `Current Events` + set `Last Updated`; net-new → confirm, then create.
7. **Step 6 — Close out** + offer to feed a top trend into the content pipeline.

## Guardrails
- Public sources only — no LinkedIn/X scraping.
- Human-in-the-loop before any write. Search before create (no native dedup). Honest source gaps; no fabricated metrics.

## What comes next
| Want to... | Do |
|---|---|
| Turn a top trend into a post | feed it to `pre-event-content` / `pattern-synthesis` |
| Who's trending / social listening | `/scan-voices` |
| Track relevant roles | `/scan-roles` |

## Ground truth
- Methodology: `.claude/skills/trend-radar/SKILL.md`
- Scoring / taxonomy: `alex:signal-scoring`, `alex:signal-taxonomy`
- Notion schema: `.claude/references/notion-schema.md`
