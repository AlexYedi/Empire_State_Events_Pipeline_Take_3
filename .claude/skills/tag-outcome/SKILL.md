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
Propose: **`hit`** (met/exceeded Target) · **`partial`** (real outcome, below Target) · **`miss`** (no meaningful outcome) · **`pending`** (not yet observable — leave it). Show the reasoning vs the Target; **Alex confirms or overrides** before writing. For `connection` / `meeting` goals, grade the underlying replies with the 11-label taxonomy below; the Outcome grade draws on it.

## Reply taxonomy — grading `connection` / `meeting` responses (E-09 / Eric P3, YED-220)

Each response to a sent connection note or DM is classified into exactly **one** of 11 labels (classify the **first reply per person** only — later messages are the conversation, not the signal):

| Label | Meaning | Positive? |
|---|---|---|
| `positive_interested` | "Yes, tell me more" / booked | ✅ |
| `positive_soft` | "Send more info" / "reach out in Q3" | ✅ |
| `positive_referral` | "Not me, but talk to X" | ✅ (referral is high-value) |
| `neutral_question` | A question, no commitment yet | ❌ |
| `negative_notnow` | "Not right now, maybe later" | ❌ |
| `negative_notfit` | "Not a fit" / "we don't need this" | ❌ |
| `negative_hostile` | Angry reply, complaint | ❌ — **track separately as a risk signal** |
| `no_response` | No reply within the observation window | ❌ |
| `ooo` | Out-of-office auto-reply | ❌ — **excluded from the denominator** |
| `bounce` | Delivery failure (email lane) | ❌ — **excluded from the denominator** |
| `other` | Can't tell (below classification confidence) | ❌ |

**Outcome Value = positives ÷ sent, recorded alongside its null baseline (YED-212).** `positives` = `positive_interested + positive_soft + positive_referral`; the denominator is `sent − ooo − bounce` (auto-replies and bounces are not real replies). Record **both** the rate **and** the do-nothing baseline it is judged against — a metric without its baseline is not a metric (CLAUDE.md §5). The baseline travels with the outcome itself, as three fields in the Outcome Value line:

- `null_baseline` — the do-nothing rate for this action type
- `baseline_method` — how it was established (the measured do-nothing reply rate for that action type, observed before/without the intervention)
- `baseline_date` — when it was measured

`"[LinkedIn/HubSpot] positives 3/8 sent = 37.5% vs null baseline 5% (do-nothing; method: measured do-nothing reply rate for connection_note; 2026-09-01→09-15)"`

If no baseline has been established for the action type yet, record `null_baseline: none` and surface the gap at close-out — **never invent a baseline**. (The value-action registry was deliberately retired — commit 5b1b1ed; baselines live in the outcome record, not in a resurrected private file.)

Worked fixture example (fictional end to end): `.claude/skills/tag-outcome/fixtures/reply-grading-fixture.md`.

**Provenance + adaptation note:** the taxonomy and the positives-÷-sent metric are adapted from Eric Nowoslawski's `positive-reply-scoring` skill (`coldoutboundskills`), harvested in `docs/archive/notes/eric-coldoutboundskills-harvest-2026-09-24.md` §3 row 3. One adaptation: the source's `unsubscribe` label (email opt-out at campaign scale) does not occur in 1:1 connection-note/DM outreach; `no_response` takes its slot — silence is the dominant outcome for a sent note, and the denominator needs an explicit home for it. The source's other rules are kept verbatim: hostile replies tracked as a risk signal, ooo/bounce excluded from the denominator, first-reply-only classification.

## Step 4 — Write back to the artifact
`notion-update-page` on the artifact row:
- `Outcome` = the confirmed grade.
- `Outcome Value` (text) = the realized signal + source, e.g. `"[LinkedIn] 620 impressions vs 500 target"`, `"[HubSpot] connected + coffee booked 6/24"`.
- `Outcome Date` (date) = today (expanded `date:Outcome Date:start` format per `notion-write-gotchas.md`).

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
