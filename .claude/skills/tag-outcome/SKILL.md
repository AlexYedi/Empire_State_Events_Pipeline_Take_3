---
name: tag-outcome
description: "Manual outcome-tagging ritual (<5 min) that closes the acted-on-value loop. Finds published Content Drafts that have an assigned Goal but no recorded Outcome, pulls the realized signal by goal type (HubSpot for connection/meeting; LinkedIn-native numbers for reach/engagement; owned-asset web analytics later), grades Outcome vs the Goal/Target, and writes Outcome + Outcome Value + Outcome Date back to the artifact. HITL, Notion-only, legitimate-only, no entity-spine."
---

# Tag Outcome Skill

You close the **acted-on-value loop**: US-4 stamped each artifact's *assigned Goal + Target* at creation; this skill records the *realized Outcome* against it. That comparison (outcome vs goal, trended) is the north-star the whole measurement layer exists for. Part of the build-rigor layer (PRD US-5 / Linear YED-91).

**Ground rules:**
- **Manual + HITL at crawl** (no entity-spine, no automation). The skill *assists* (pulls signals, proposes a grade); Alex confirms. The systems-analyst flagged manual rituals get skipped under pressure → keep this **fast (<5 min)** and make it easier over time, never heavier.
- **Legitimate-only:** HubSpot (your CRM), LinkedIn's *native* analytics read manually, owned-asset web analytics. No scraping.
- **No fabricated numbers:** if an outcome isn't observable yet, leave it `pending`. Never invent a metric.
- **Notion plan constraint:** use `notion-search` (scoped to Content Drafts) + `notion-fetch`, not `notion-query-data-sources`.

## Inputs
- **(Optional) Scope** — default: the tagging backlog (published drafts with a Goal but Outcome empty/`pending`). May narrow ("last week's posts", a specific artifact/event).
- **(Optional) Window** — how far back to consider (default 30 days; outcomes lag).

## Step 1 — Find the tagging backlog
`notion-search` the Content Drafts data source (`collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`) for recent published items; `notion-fetch` candidates and keep those with **`Content Status = published`**, a **`Goal`** that isn't `internal`, and **`Outcome` empty or `pending`**. Skip `internal`-goal artifacts (set `Outcome = na`). Present the backlog list.

## Step 2 — Pull the realized signal, by Goal type
For each artifact:
- **`connection` / `meeting`** → the outreach target is a person (the draft's `People` relation). Search HubSpot for that contact (`mcp__claude_ai_HubSpot__search_crm_objects`) and check recent notes/meetings/associations: did they connect? was a meeting/coffee booked? Present what's found.
- **`reach` / `engagement`** → ask Alex for the LinkedIn **native** number (impressions for reach; reactions+comments+reshares for engagement) for that post, vs its `Target`. (Manual log — legitimate; owned-asset web analytics via PostHog/Hub is a later source.)
- **`hybrid`** → pull both.

## Step 3 — Grade Outcome vs Target (HITL)
Propose: **`hit`** (met/exceeded Target) · **`partial`** (real outcome, below Target) · **`miss`** (no meaningful outcome) · **`pending`** (not yet observable — leave it). Show the reasoning vs the Target; **Alex confirms or overrides** before writing.

## Step 4 — Write back to the artifact
`notion-update-page` on the artifact row:
- `Outcome` = the confirmed grade.
- `Outcome Value` (text) = the realized signal + source, e.g. `"[LinkedIn] 620 impressions vs 500 target"`, `"[HubSpot] connected + coffee booked 6/24"`.
- `Outcome Date` (date) = today (expanded `date:Outcome Date:start` format per `notion-write-gotchas.md`).

## Step 4.5 — Publish-sync to the knowledge graph (YED-208; runs every time, not only for the backlog)
The graph's `published` events are what the `content` lens uses to back-link your prior posts, so every post marked
`published` in Notion must reach the graph. This step is idempotent. Spec: `.claude/notes/yed-208-spec-2026-09-27.md`.
1. **What's already there:** `.venv/bin/python .claude/scripts/substrate.py published-refs` prints the Notion page
   ids (undashed) already in the graph.
2. **What should be there:** query Content Drafts for `Content Status = published` (all of them, not just this
   ritual's backlog), with their `Published URL`, `Goal`, `Target`, `Outcome`, `Outcome Value`, `Outcome Date`,
   `Title`, `Content Type`, and `Event` / `Topics` / `People` relations.
3. **Build `.claude/.state/publish-sync.json`:** `{"posts": [...]}`, one entry per published post with a URL.
   - **New posts** (not in `published-refs`): `notion-fetch` the page and pass its body as `body_md`.
   - **Posts already in the graph:** omit `body_md`; the verb then only refreshes the outcome you just graded.
   - `event_notion_ids` = every page id in the post's `Event` relation (a roundup covers several). Pass the
     `Outcome Value` too: when it carries `Posted YYYY-MM-DD` (the LinkedIn export line), that becomes the publish
     date. Otherwise the earliest covered event's date stands in, since Notion has no published-date property.
   - `topics` / `people`: `[{"notion_page_id"}]` from the relations; a name is optional. ID-only entries resolve by
     page id and are never created nameless. **Never** email, phone or bio (ADR-9).
4. **Run:** `.venv/bin/python .claude/scripts/substrate.py publish --manifest .claude/.state/publish-sync.json`.
   Report its line: `publish: N/M posts in the graph · skipped K`. Posts without a URL are skipped by design. A post
   refused by the ADR-9 guard is named in the output: fix the text in Notion, then re-run.

## Step 5 — Close out
Summarize: hit / partial / miss / still-pending counts, and any trend vs prior runs ("reach goals 3/4 hit this cycle"). This feeds the north-star (US-6 Hub dashboard) and is a natural sub-step of the weekly review (US-7).

## Failure modes
- **Outcome not observable yet** (artifact too fresh) → leave `pending`; re-tag next ritual. Don't force a grade.
- **Person not in HubSpot / no draft `People` relation** → ask Alex directly; don't fabricate.
- **No LinkedIn number to hand** → leave `pending`; never estimate.
- **Goal was `internal`** → set `Outcome = na`, no grading.

## Reuses / references
- Assigned-goal side: `.claude/skills/content-patterns/goal-tagging.md`. Schema: `.claude/references/notion-schema.md` (Content Drafts).
- Tools: `notion-search`/`notion-fetch`/`notion-update-page`, `mcp__claude_ai_HubSpot__search_crm_objects` (+ `get_crm_objects`).
- Downstream: the north-star renders in the Empire State Hub dashboard (US-6); this ritual nests in the weekly review (US-7).
