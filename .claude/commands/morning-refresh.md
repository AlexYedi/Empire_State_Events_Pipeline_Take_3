---
description: "Daily progressive market-intelligence refresh. Delta-scans since the last run (newsletters, HN, web news, events that happened), matches against the existing graph, AUTO-LOGS new signals to the Supabase graph (no approval gate), and returns a review report: Farmed / Added / Changed / Cooled. The manual-trigger, human-in-the-loop, subscription-only first increment of the progressive trend engine (YED-115)."
argument-hint: "[optional: focus e.g. 'agents and evals' | window override e.g. 'last 3 days']"
---

# /morning-refresh — Daily Progressive MI Refresh

A lighter, **delta-aware** sibling of `/scan-trends`. Alex kicks this off each morning; it accumulates
new signals into the Market-Intelligence graph and hands back a short review of what changed. **Auto-logs —
it does NOT wait for approval to write** — but every write is reported so Alex reviews after the fact.

**Cost:** runs entirely in this Claude Code session (MCP pulls + REST writes) → subscription, **no API tokens.**
**Design of record:** YED-115. Methodology reused from `.claude/skills/trend-radar/SKILL.md`; graph-write
contract from `.claude/references/market-intel-spine.md`.

## Trigger
`/morning-refresh [focus|window]`, or Alex says "morning refresh", "what's new since yesterday", "daily scan".

## Core principle (append-only)
The graph is the **durable signal stock** — this command only ever **adds** (upsert topic, insert event,
insert edge). Nothing is deleted; "Cooled" in the report means *no new signal this window*, a ranking
observation, NOT a graph removal. Decay-weighting (deferred, YED-115) handles staleness later.

---

## Step 1 — Intake & derive the window (parent thread)
1. Read `SUPABASE_API_KEY` from `.env` (never print). Base `https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1`.
2. **Window start = the newest `trend_radar` signal already in the graph:**
   `GET /event?select=event_date&source=like.trend_radar*&order=event_date.desc&limit=1`.
   - Found → window = that timestamp → now.
   - None (first run) → default **last 24h**.
   - Honor an explicit override from args ("last 3 days").
3. Capture `WINDOW_START` (ISO) and `WINDOW_LABEL` for the report. State the window up front.

## Step 2 — Delta pull (fan out; only what's NEW in the window)
Pull each source scoped to the window; continue past any single-source failure and flag the gap.
Where a source returns large bodies (newsletter HTML), dispatch a **subagent** to distill featured items +
links so raw content stays out of context (see the `/scan-trends` 2026-08-06 pattern).
- **Newsletters** — Gmail `search_threads` with `label:Content/newsletters newer_than:{window}` (full nested
  path — leaf-only `label:newsletters` returns empty). `get_thread` the AI-substantive ones; extract
  featured items + real destination URLs.
- **HackerNews** — Algolia `search_by_date?tags=story&numericFilters=created_at_i>{WINDOW_START_unix},points>20`
  + `tags=front_page` for current momentum. Velocity proxy = points/age.
- **Web news** — `WebSearch` for headline AI/tech news in the window (funding, launches, exec moves, policy).
- **Events that happened** — `mcp__claude_ai_Google_Calendar__list_events` on the "Going to Events" calendar
  (`4c84184ac3e761c3f94be43193656a785ece4752ed6b553facfcb52e668a333b@group.calendar.google.com`) for events
  whose end fell inside the window, plus Notion Events with a date in-window. **Surface only** — do NOT write
  attended events to the graph here; that is `/post-event-content`'s job. Flag them for handoff.

## Step 3 — Normalize + match-before-create (Claude in the loop — this is what keeps the graph clean)
1. Collapse raw items into canonical topics (`alex:signal-taxonomy`), score with recency decay + cross-source
   blend (`alex:signal-scoring`).
2. **Read the existing graph topics first:** `GET /topic?select=id,name,engagement_count&limit=300`.
3. For each candidate topic, **semantically match** against the existing set (not exact-name — e.g. map
   "LLM Evaluation" → existing "Agent Evaluation & Reliability in Production"). Only mint a NEW topic node
   when there is genuinely no home. (This human-in-the-loop match is why daily accumulation doesn't fragment
   the graph — the automated embedding version is the YED-115 upgrade, not needed here.)

## Step 4 — AUTO-WRITE to the graph (no approval gate; Step 5.5 REST pattern)
For each matched/new topic, write via REST (`.claude/references/market-intel-spine.md`):
1. **Upsert topic** — matched → `PATCH` (`engagement_count`+1, `last_engaged_at`=now); new → `POST`
   (`source:'trend_radar'`, `engagement_count:1`). Capture `topic_id`.
2. **Insert the signal event** — `POST /event` `kind='market'`, MANDATORY provenance
   (`source`, `url`, `metadata.sources`), normalized `confidence`. Dedup on (title, event_date::date, kind) —
   skip identical same-day signals. Capture `event_id`.
3. **Insert the hyperedge** — `POST /event_entity` (event→topic, role='subject').
Track counts as you go for the report. If a write fails, log it and continue (additive, not a gate).

## Step 5 — Compute the deltas (for the report)
- **Added** = topics newly created this run + signals newly inserted.
- **Changed/Reinforced** = existing topics that got a new signal (engagement bumped) — note new vs prior count.
- **Cooled** = topics that carried a `trend_radar` signal in the *previous* window but got none this run
  (query prior-window signals; diff against this run). Ranking observation only — nothing removed.
- **Sustained** = topics with signals in ≥2 consecutive runs (the "real trend, not a blip" tell).

## Step 6 — Output: the review report (NAMED OUTPUT)
Return a scannable report to the conversation (do NOT gate on it — writes already happened):
```
# Morning Refresh — {date} (window: {WINDOW_LABEL})

## Farmed
Newsletters: {n} new ({senders}) · HN: {n} · Web: {n} · Events in window: {n}
{any source gaps}

## Added ({n} new signals, {k} new topics)
- [NEW TOPIC] {topic} — {why} — {url}
- {topic} — {why} — {url}

## Changed / Reinforced ({n})
- {topic} (engagement {prev}→{new}) — {what's new} — {url}

## Cooled (no new signal this window)
- {topic} (last seen {when})

## Sustained (multi-run)
- {topic} — {n} runs running

## Events that happened → handoff
- {event} ({date}) — run /post-event-content?

## Worth posting today
- {1-2 lines: the strongest content angle from today's delta}
```
Everything above is **already written to the graph** — this is your after-the-fact review. The `/ops/market-intel`
dashboard reflects it immediately.

## Step 7 — Failure modes
- **Newsletter label empty** → confirm the full nested path `label:Content/newsletters`; then fall back to the
  curated senders (trend-radar Step 1c). Report the fallback.
- **A source errors** → skip it, note the gap in Farmed; never fabricate items.
- **Graph write fails (key/network/paused project)** → log the specific failure, keep going for the rest,
  and surface it under a `⚠️ Write failures` section so nothing is silently dropped.
- **First run (no prior signals)** → default 24h window; say so.
- **Nothing new in window** → say "no new signals since {last run}"; write nothing; still list Cooled/Sustained.

## What comes next
| Want to... | Do |
|---|---|
| Turn today's delta into a post | feed the top angle to `pre-event-content` / `pattern-synthesis` |
| A deeper weekly synthesis | run `/scan-trends` (full Top-N, richer newsletter read) |
| Recap an event that happened | `/post-event-content` |

## Ground truth / references
- Scan methodology: `.claude/skills/trend-radar/SKILL.md` (sources, taxonomy, scoring)
- Graph-write contract: `.claude/references/market-intel-spine.md` (REST, dedup, upsert)
- Design of record: **YED-115** (progressive engine: this is increment 1 — daily accumulate, manual trigger)
- Orchestration convention: `.claude/references/command-orchestration-convention.md`
