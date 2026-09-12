# Post-Performance Ingestion + Match-Back — Plan

## Context

Alex exported LinkedIn `SinglePostAnalytics` for every post into a Google Drive folder
("Post Performance") — his first move to **restore the acted-on-value feedback loop** (the
north-star the measurement layer has been running dark on, and the #1 "restore the loop"
recommendation from the roadmap re-eval). This is the raw material to finally answer *is the
content working, and for whom* — and to give every post the LinkedIn link the pipeline has
lacked.

This plan ingests those files into one clean dataset and attempts to match each post back to
its Notion Content Draft + Event, including three investigation dimensions Alex asked for:
content/event backlink, A/B variant discernment, and visual-creative/format signal.

**Confirmed by reading (read-only) 5 files across the full date range:**
- 55 files, uniform LinkedIn export schema (Identity → Discovery → Profile activity →
  Engagement → Viewer demographics). All fully readable.
- **~50 distinct posts** — 5 are duplicate exports (`7475523174328143873`, `7452415883068690432`,
  `7460046384646324224`, `7470545414950207488`, `7467998547888549888`). Duplicates are the same
  post exported at different times with slightly drifted metrics (e.g. 230 vs 226 impressions) →
  **dedupe rule: keep the latest export per post ID.**
- Actual span is **~1/8/2026 → 8/25/2026 (~7.5 months)**, wider than the "4 months" assumed.
- No post body text in the files — only the **URL slug** (slugified opening line, often naming the
  venue/event/thesis) + canonical post URL + date/time + format cue.

## Approach

1. **Download + parse (parent thread only** — claude.ai Drive/Notion MCP connectors do NOT work
   in subagents). `download_file_content` each of the 55 files → decode → parse with
   Python/`openpyxl` in the scratchpad → one row per file.
2. **Normalize + dedupe** into a single table (CSV + JSON) keyed on the URL `ugcPost` activity ID;
   keep latest export per post. Columns: post_id, post_url, date, time, format(inferred),
   opening_slug, impressions, members_reached, profile_viewers, followers_gained,
   social_engagements, reactions, comments, reposts, saves, sends. Demographics kept in a nested
   block per post (job title / seniority / industry / location / company size).
3. **Enrich from the slug/URL:** derive opening-line, venue/event hint, and **format**
   (carousel/document vs single-image vs text-only) from the URL pattern.
4. **Match-back (read-only Notion):** query Content Drafts DB by date (± publish time) and
   slug/topic → link to the Content Draft and its related Event. Assign a **match_confidence**
   (high / medium / low / needs-manual) per post.
   - **Actively shrink the ambiguous set** before declaring anything "needs verification":
     exhaust the cheap secondary keys first — exact date+time collision breaks, slug token
     overlap with draft text, event-date alignment, and (where still tied) a live-post pull via
     the post URL to read the real opening line. Only what survives *all* of those stays
     ambiguous.
   - Output the irreducible residue as a **short, discrete checklist** (post link + date + the 1–2
     candidate drafts + why it's ambiguous), so Alex verifies only the minimal portion by hand.
5. **Investigation columns:**
   - `matched_event`, `matched_draft` (backlink).
   - `variant_guess` (A/B/uncertain) — compare the posted opening slug against the matched
     draft's A vs B opening lines; mark uncertain when they don't discriminate.
   - `format` + `intended_visual` — format inferred from URL; the actual creative pulled from the
     matched draft's visual brief / exported PDF where present.
6. **Output (no Notion writes this pass — refine first):**
   - `post-performance-dataset.csv` + `.json` (deduped, enriched, matched).
   - A summary: per-post table + a match report flagging the manual-confirm tail and any posts
     with no confident draft/event.
   Proposed location: `.claude/artifacts/post-performance/` (durable, uncommitted) — confirm or
   redirect.

## Critical files / tools
- **Google Drive MCP** (`download_file_content`, parent thread) — the 55 source files, folder
  `12hDKEg0YYDd7FTji3mMellMUcuZnwgjU`.
- **Bash + Python/openpyxl** — parse xlsx → table (scratchpad workspace).
- **Notion MCP** (`notion-query-data-sources` / `notion-fetch`, read-only, parent thread) —
  Content Drafts `collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`, Events
  `collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`.

## Scope guard
Analysis/data pass, not a build — no skill/agent/command/schema change, so the heavy DoD gate
auto-waives. **No Notion writes, no CRM, no content changes** this pass. If it graduates into a
persisted measurement dataset/schema, DoD (PRD-first) re-applies.

## Verification
Spot-check known anchors: NeueHouse Madison event post (5/12), GTM single-vs-multi (6/3 →
YED-67 theme), The Shortlist Founder Showcase carousel (8/25). Confirm dedupe kept 50 distinct
posts. Confirm the match report's confident matches align with those known events, and that the
manual-confirm tail is small.
