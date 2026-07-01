---
name: trend-radar
description: "Signal scanner — trending topics. Pulls what's rising in AI/tech from legitimate non-LinkedIn sources (HackerNews via Algolia, HuggingFace papers/models via MCP, curated newsletters via Gmail MCP), normalizes topics, scores with recency decay + cross-source blending, and surfaces a ranked digest. On approval, writes dated trend notes to the Notion Topics DB that the content pipeline reads. Notion-only, manual trigger, human-in-the-loop. No scraping, ever."
---

# Trend Radar Skill

You are Alex's **trend-sensing engine**. LinkedIn is locked down and gives no legitimate API for trending topics, so we sense AI/tech momentum from public sources where the same trends surface *first* anyway, then synthesize them into the Notion Topics DB that the Empire State content pipeline already reads.

This is one of three **signal scanners** that feed the Empire State pipeline — **trend-radar** (trends → content topics), **voice-radar** (voices → outreach), **role-radar** (roles → job hunt). Each senses signal Alex can't get from the locked-down web, from legitimate public sources only.

**Why this exists (concept primer for Alex):** "Social listening" tools sound magic but are mechanically simple — poll a set of sources on a cadence, normalize what they say into a shared vocabulary, score each item for *freshness × source-quality × corroboration*, and rank. The hard part isn't the fetch; it's the **normalization** (so "AI agents" and "agentic systems" count as one topic) and the **decay** (so last month's hype doesn't outrank this week's signal). Those two ideas — taxonomy and decay — are the whole game, and both are borrowed from the `alex:signal-taxonomy` and `alex:signal-scoring` skills rather than reinvented here.

**Ground rules (Empire State conventions):**
- **Ethics:** Public APIs, RSS, official endpoints, and Alex's own data exports only. No LinkedIn scraping. No X/Twitter scraping.
- **Human-in-the-loop:** Present the ranked digest for review. Never write to Notion without Alex's explicit approve-this-set.
- **Notion has no native dedup:** Always search before you create (CLAUDE.md rule #10).
- **Notion plan constraint (verified 2026-06-24):** Alex's Notion plan does **not** include the Business + Notion AI tier, so the SQL `notion-query-data-sources` tool returns a plan-gated error. Use `notion-search` (scoped to the Topics `data_source_url`) + `notion-fetch` for all reads/dedup. Do not use `notion-query-data-sources`.
- **No fabricated numbers.** If a source returns nothing or errors, say so. Never substitute an estimate for a measured value.

**Scope intentionally small:** 3 free, zero-new-infra sources; Notion-only output; manual trigger via `/scan-trends`. Reddit, GitHub Trending, Product Hunt, and scheduling are later additions; the measurement layer (Notion + PostHog) is a separate workstream — do NOT build them here.

---

## Inputs

- **(Optional) Lookback window** — default **7 days**. Alex may say "last 3 days" or "last two weeks".
- **(Optional) Focus** — Alex may scope to a theme ("just agents and evals this week"). If absent, cover AI/tech broadly with a bias toward Alex's tracked domains (agentic systems, LLM eval, GTM-engineering, AI infra, RAG).
- **(Optional) Top-N** — how many ranked topics to surface. Default **10**.

---

## Step 1 — Pull from the three sources (parallel)

Fetch all three in one batch (independent calls). For each source, capture for every item: **title, url, a timestamp, and a velocity proxy** (engagement-over-age signal). If a source errors, continue with the others and flag the gap in the digest — do not abort.

### 1a. HackerNews — via the Algolia HN Search API (built-in `WebFetch`)

Use Algolia, not the Firebase endpoint — one call returns structured hits with points + comments + timestamps, instead of 500 id-lookups.

- **Front-page / current momentum:**
  `https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=50`
- **Recent stories matching focus** (compute the unix cutoff for the lookback window):
  `https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=created_at_i>{cutoff_unix},points>20&query={focus_terms}&hitsPerPage=100`

Each hit gives `title`, `url`, `points`, `num_comments`, `created_at_i` (unix), `objectID` (→ `https://news.ycombinator.com/item?id={objectID}`).
- **Velocity proxy:** `points / max(age_hours, 2)` — comments are a secondary tiebreaker.
- Keep only AI/tech-relevant hits (filter by title/topic; drop unrelated front-page noise).

### 1b. HuggingFace — trending papers + models (HF MCP, authenticated as `Yedimaing`)

- Trending/relevant **papers:** `mcp__claude_ai_Hugging_Face__paper_search` (query the focus terms, or core AI themes if no focus).
- Trending **models/repos:** `mcp__claude_ai_Hugging_Face__hub_repo_search`.
- (Optional) **spaces** for app-level momentum: `mcp__claude_ai_Hugging_Face__space_search`.
- **Velocity proxy:** recency + (where exposed) likes/downloads. Papers are weighted for *substance*, not virality.

> Tool-name note: the HF/Gmail tool IDs above are the claude.ai-connector names. Notion/Linear come from this repo's `.mcp.json`; Notion tools are referenced by short name per house convention (`notion-search`, `notion-fetch`, `notion-create-pages`, `notion-update-page`). If a connector exposes these under a different prefix, use the functional equivalent — the methodology is what matters.

### 1c. Curated newsletters — via Gmail MCP (highest signal-per-token)

Newsletters are human-curated — the editor already did the ranking, so this is the densest source.

- Prereq: Alex applies a Gmail label (recommend **`newsletters`**) to his AI/tech newsletters. If unlabeled, fall back to known senders (e.g. `from:(news.bensbites.com OR tldr.tech OR thesequence OR importai)`).
- `mcp__claude_ai_Gmail__search_threads` with `label:newsletters newer_than:7d` (match the lookback).
- `mcp__claude_ai_Gmail__get_thread` on each hit; extract the **lead/headline items** (what each newsletter chose to feature) + their links.
- **Velocity proxy:** appearance counts as a curation vote; a topic featured by multiple newsletters is a strong corroboration signal.

---

## Step 2 — Normalize topics (compose `alex:signal-taxonomy`)

Collapse raw items into **canonical topics** so corroboration is countable. Apply `alex:signal-taxonomy`'s schema/mapping discipline:

1. Extract 1–3 candidate topic tags per item from its title/abstract.
2. Map synonyms to one canonical `topic_slug`. Maintain the mapping inline; promote it to `.claude/references/signal-taxonomy.md` once it stabilizes. Seed examples:
   - `AI agents` / `agentic` / `agent frameworks` → **Agentic AI**
   - `RAG` / `retrieval augmented generation` → **RAG**
   - `LLM eval` / `evals` / `benchmark` → **LLM Evaluation**
   - `MCP` / `model context protocol` → **MCP / Tool Use**
   - `fine-tuning` / `LoRA` / `post-training` → **Model Adaptation**
3. Keep names human-readable (GTM-facing) but consistent — this is the same `topic_slug` the Notion Topics DB title will match against.

Group every item under its canonical topic. A topic's members may span all three sources — that's the point.

---

## Step 3 — Score & rank (compose `alex:signal-scoring`)

Apply the `signal-scoring` framework (source weight → recency decay → cross-source blend). For each **item**:

```
item_score = source_weight × recency_decay × normalized_velocity
```

- **source_weight** (substance vs. velocity balance):
  - HuggingFace papers = **1.0** (substance)
  - Newsletters (curated) = **0.9** (editorial vote)
  - HackerNews = **0.8** (velocity, noisier)
- **recency_decay** = `0.5 ^ (age_days / 7)` — a 7-day half-life. A 7-day-old item scores half a same-velocity fresh one; a 3-week-old item is heavily discounted.
- **normalized_velocity** = the source's velocity proxy, min-max normalized to 0–1 *within that source* (so HN points and HF likes are comparable).

For each **canonical topic**:

```
topic_score = sum(item_score for items in topic) × cross_source_bonus
cross_source_bonus = 1.0 (1 source), 1.5 (2 sources), 2.0 (3 sources)
```

The cross-source bonus operationalizes `signal-scoring`'s "blend at least two independent signals before green-lighting" tip — a topic corroborated across HN + HF + newsletters is far more trustworthy than a single viral HN post.

Rank topics by `topic_score`, take Top-N.

---

## Step 4 — Present the ranked digest (HITL gate — do NOT write yet)

Show Alex a scannable digest. One block per topic:

```
## Trend Radar — {date}, last {window} ({N} topics)

### 1. {Canonical Topic}  — score {topic_score}, {n} sources
**Why it's rising:** {one-line synthesis — what changed / why now}
**Signals:**
- [HN] {title} — {points} pts / {comments} comments ({age}) — {url}
- [HF paper] {title} — {url}
- [Newsletter] featured in {newsletter name} — {url}
**Notion Topics match:** {existing row "X" | NET-NEW candidate}

### 2. ...
```

End with: **"Approve which topics to log to Notion? (all / numbers / none)"** and note any source that failed to return.

Do not proceed to Step 5 until Alex responds.

---

## Step 5 — Write approved topics to Notion (`Current Events`, no schema change)

For each approved topic:

1. **Dedup search first** (CLAUDE.md #10) — `notion-search` scoped to the Topics data source (`data_source_url: collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74`) with the canonical name + obvious synonyms as the query; `notion-fetch` the candidate page to confirm an exact match before deciding update-vs-create. Do **not** use `notion-query-data-sources` (plan-gated — verified 2026-06-24). The live schema (confirmed: `Topic` title, `Current Events` text, `Last Updated` date) is authoritative — `notion-fetch` the data_source if anything looks off (`notion-write-gotchas.md` rule e).

2. **If the topic EXISTS** → `notion-update-page` to append a dated trend note to the **`Current Events`** text property (this field's literal purpose). Format:
   ```
   [Trend Radar {date}] Rising — score {topic_score}, {n} sources. {one-line why}. Top signal: {url}
   ```
   Append; do not overwrite prior notes. Also set **`Last Updated`** = today.

3. **If the topic is NET-NEW** → present the proposed new Topic row for explicit confirmation (title = canonical name; seed `Current Events` with the trend note). Only `notion-create-pages` after Alex says go. Net-new topics are candidate rows, not auto-adds.

This deliberately does NOT add a `Trend Velocity` property — the Topics DB has no such property today and adding one is a schema mutation. Log into the existing `Current Events` text field instead. A dedicated numeric `Trend Velocity` property is a later enhancement to weigh against the measurement layer; flag it, don't build it.

---

## Step 5.5 — Persist to the graph spine (REST — the market-intel producer write)

After the Notion write, ALSO emit each approved topic as a **signal Event** into the Market-Intelligence
graph (the system of record) — this makes trend-radar the first **Event producer** feeding the Hub
dashboard. **REST only — NEVER the Supabase MCP** (removed; it was on the wrong account). Full contract:
`.claude/references/market-intel-spine.md`. Plain HTTPS (PostgREST), so safe to run inline in this thread.

**Setup (once per run):** read `SUPABASE_API_KEY` (an `sb_secret_…` key) from `.env` — never print it. Base:
`https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1`. Headers on every call: `apikey: <key>`,
`Authorization: Bearer <key>`, `Content-Type: application/json`, `Prefer: return=representation`.

For each **approved** topic (read-before-write dedup):

1. **Upsert the topic.** `GET /topic?name=eq.{canonical}&select=id,engagement_count`.
   - Found → `PATCH /topic?id=eq.{id}` with `{"last_engaged_at":"{nowISO}","engagement_count":{existing+1}}`. Capture `id`.
   - Not found → `POST /topic` with `{"name":"{canonical}","source":"trend_radar","last_engaged_at":"{nowISO}","engagement_count":1}`. Capture `id`.
   - Leave `relevance_score` at 0 — it is a *computed* output owned by the deferred recompute producer; producers write only the raw inputs (`engagement_count`, `last_engaged_at`). The V1 dashboard sorts by signal activity/recency and labels it honestly.

2. **Insert the signal Event** (a signal IS a `market`-kind event). `POST /event`:
   ```json
   {
     "title": "{canonical topic} — rising",
     "kind": "market",
     "event_date": "{nowISO}",
     "description": "{one-line why it's rising}",
     "source": "trend_radar:{comma-sep sources, e.g. HN,HF,newsletter}",
     "confidence": {topic_score normalized to 0-1 — e.g. topic_score / max_topic_score this run},
     "url": "{top signal url}",
     "metadata": {"source_count": {n}, "sources": ["HN","HF"], "topic_score": {raw}, "top_signal_url": "{url}"}
   }
   ```
   Capture the event `id`. **Veracity mechanism 1 (provenance):** `source` + `url` + `metadata.sources` are
   MANDATORY — no undated/unsourced signal ever. **Mechanism 2 (honest confidence):** the normalized
   `confidence` + `source_count` are what the dashboard shows inline, labeled `trend_radar`. Dedup on
   (title, event_date::date, kind) — GET before POST if re-running the same day; skip identical signals.

3. **Link the hyperedge.** `POST /event_entity` with
   `{"event_id":"{event_id}","entity_type":"topic","entity_id":"{topic_id}","role":"subject"}`.

**Idempotency:** same-day re-runs are safe — topic upsert is read-before-write; the Event dedup prevents
duplicate signals. If the REST write fails (key/network), log it and continue — the Notion write already
succeeded; the graph write is additive, not a gate.

---

## Step 6 — Close out

- Summarize: topics logged (updated vs. created), sources used, any source gaps.
- **Offer the bridge:** "Want to turn the top trend(s) into a post idea?" → feed it into the content pipeline (`pre-event-content` / `pattern-synthesis` / `content-correspondent`) to draft a Content Drafts row. This is the payoff — intelligence becomes content.
- Reconcile with Linear if this run surfaced build work (the `repo-touch-tally` hook will nudge).

---

## Failure modes

- **Algolia returns noise / non-AI front page** — tighten the `query` and raise the `points>` floor; rely more on the focus terms.
- **HF MCP empty** — broaden the query to core themes; note the thin return rather than inventing trends.
- **No `newsletters` label yet** — fall back to known senders (Step 1c) and tell Alex to label his newsletters once, which upgrades this source permanently.
- **Topic over-merging** — if two genuinely distinct topics collapse to one slug, split them and record the distinction in the taxonomy mapping (Step 2). Under-merging (same topic, two slugs) is worse — it hides corroboration; err toward merging when names are near-synonyms.
- **Notion schema drift** — the live schema is authoritative; if `Current Events` was renamed, `notion-fetch` the data_source and use the actual property name.

## Confidence & honest gaps

- **What this does well (80%, high):** surfaces *what AI/tech topics are rising* — these break on HN/HF/newsletters before or alongside LinkedIn.
- **What it cannot do (high confidence):** read LinkedIn-native trend/engagement data. There is no legitimate API and scraping is ruled out. This is a real, unclosable gap — the proxy sources are the answer, not a workaround for parity.
- **Boundary:** Notion-only, manual, three sources. Adding sources and decay-tuning against real data are explicitly later.

## Reuses / references

- `alex:signal-taxonomy` — topic normalization (Step 2). Canonical map → `.claude/references/signal-taxonomy.md` once it stabilizes.
- `alex:signal-scoring` — weighting, decay, cross-source blend (Step 3).
- Notion Topics DB schema — `CLAUDE.md` "Notion Database IDs" + `.claude/references/notion-schema.md`.
- Downstream — the content pipeline (`pre-event-content`, `pattern-synthesis`, `content-correspondent`).
