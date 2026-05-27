---
description: "Workflow B-lite — take a manually-uploaded post-event transcript, condition it against the event roster, then run content-correspondent to produce LinkedIn drafts + outreach in Notion Content Drafts. Manual-upload anchored (Granola auto-fetch DISABLED 2026-05-27 — app nonoperational on Alex's device; do not fire the Granola API or MCP)."
argument-hint: "[event name as it appears in Notion / Google Calendar / Granola]"
---

# /post-event-content — manual-upload post-event flow

> ## ⚠️ GRANOLA IS OFF (status 2026-05-27)
> Granola is **nonoperational on Alex's device** — the mobile app is a waitlist-only placeholder, so there are no recordings to fetch. **Do NOT fire the Granola REST API or the Granola MCP** for post-event recordings, here or anywhere. **Post-event transcripts are MANUAL UPLOAD only** until Granola ships a working app. The Granola auto-fetch path is retained below but **DISABLED** — re-enable it (and remove this banner) only once Granola actually records on Alex's device.

Takes a transcript Alex uploads/pastes from his own recording of an attended event, resolves the event to its Notion row, **conditions the transcript against the event roster (Step 3.5 — `transcript-conditioning`)**, then invokes `content-correspondent` with the conditioned quote bank.

**Input:** event name (one argument) + the transcript (manual upload/paste).

**Output:**
- One Notion Content Drafts row per content piece (Tier 1 comment, Tier 2 post + visual brief, bucket-sorted outreach DMs)
- All drafts in `needs_review` status, Event Phase = `post_event`, linked to the Notion Event row

---

## Trigger

This command runs when:
- Alex types `/post-event-content [event name]`
- Alex says "post-event content for [event]" / "draft the post for last night's [event]" / "write up [event] from Granola"

If the user invokes `content-correspondent` directly with raw pasted material, defer to that skill's existing path — this command adds Notion event-resolution + roster-grounded conditioning around a manual transcript upload.

## Required inputs

1. **Event name** — fuzzy-match-friendly. The command resolves it against the Notion Events DB by title similarity, then anchors downstream lookups.
2. **Transcript (manual upload/paste)** — Alex's own recording transcript for the event (Otter/Zoom/phone export or pasted text). This is the post-event input now that Granola is off. **No `GRANOLA_API_KEY` needed** — the Granola path is disabled.

## Step 1 — Resolve the Notion Event row

Search Notion Events DB (`9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`) by event title using `mcp__notion__notion-search`. From the matching row, read:

- `Event Name` (title)
- `Event Date` (date) — anchors the Granola query window
- `Google Calendar Event ID` (text) — deterministic join key when populated
- The page URL (used later for the Content Draft `Event` relation)

**If no Notion match:** prompt Alex with the top 3 candidates from Notion by title similarity. If still no match, accept "create draft without Notion anchor" — content can still be generated from Granola alone; the Content Draft just won't have a Notion Event relation set.

**If multiple matches (same title, different dates):** present the candidates with dates and ask Alex to pick.

## Step 2 — Ingest the manual transcript

Granola auto-fetch is **disabled** (see banner) — get the transcript from Alex directly:

1. Ask Alex to paste/upload the transcript from his own recording of the event (or confirm he already has one ready).
2. **Persist it immediately** to `event-transcripts/YYYY-MM-DD_<Event>.md` (date = the event's `Event Date`). Save FIRST, then proceed — a pasted-but-unsaved transcript is lost across sessions (see memory `feedback-comment-workflow-2026-05-26`).
3. Capture what you have: the **raw transcript** (verbatim quote source, after Step 3.5 conditioning), any **summary / notes** Alex adds (angle/thesis input), and the **attendee names** he recalls (cross-reference against Notion People DB for bucket sorting).

If Alex has no transcript (didn't record), still draft from his freeform recap + the pre-event brief — note the lower fidelity and skip verbatim quotes.

<details>
<summary>🚫 Granola auto-fetch — DISABLED (do not run; retained for re-enable when Granola is operational)</summary>

The Granola REST/MCP path is **not active** — the app is a waitlist placeholder on Alex's device, so there are no notes to fetch. Do NOT fire it. Re-enable only when Granola records for real, then restore the manual path as a fallback.

```bash
# DISABLED — do not run while Granola is nonoperational (2026-05-27)
# List:   GET https://public-api.granola.ai/v1/notes?created_after=<event_date>T00:00:00Z&created_before=<+36h>   (Bearer $GRANOLA_API_KEY)
# Detail: GET https://public-api.granola.ai/v1/notes/<note_id>?include=transcript
# Match:  Google Calendar Event ID (deterministic, preferred) → title+date fuzzy fallback
# Capture: summary_markdown · diarized transcript · attendees · web_url
```
</details>

## Step 3 — Confirm the event anchor (silent if unambiguous)

Only prompt if Step 1 had disambiguation (multiple or no Notion matches). Otherwise proceed silently to conditioning.

```
📝 Event: [Notion Event Name] — [date]
   Transcript: event-transcripts/[…].md  (~N turns / M words)
   Proceeding to condition + draft. [y / change / cancel]
```

## Step 3.5 — Condition the transcript (`transcript-conditioning`)

Before drafting, condition the transcript so speaker labels and proper nouns can be trusted in public copy. Diarization splits on pauses, not identity, and ASR mangles proper nouns (Vercel → "Purcell", Mahan → "vahan", MCP → "FCP") — quoting that raw misattributes lines and prints garbled names. Invoke the `transcript-conditioning` skill with:

- **Raw transcript** — the manually-uploaded transcript from Step 2 (persisted to `event-transcripts/`).
- **Roster + known entities (ground truth)** — pulled from this event's Notion record: related **People** (speaker/host roster), **Companies** (canonical org/product names), and the linked pre-event **research_brief** Content Draft. Conditioning anchors speaker resolution + entity normalization to these.

**When to run:**
- **Run by default** for multi-speaker panels, in-person / manual-paste transcripts, or any note where a named person will be quoted publicly.
- **Skip** only when Granola's diarization is clean AND the roster is ≤2 obvious speakers (per the skill's "When to use"). State the skip decision in one line.

**Output (passed to Step 4 in place of the raw transcript):**
1. Speaker resolution table (resolved person + tell + confidence)
2. Entity normalization glossary (+ ⚠️ excluded-garble list — never quoted)
3. Confidence-scored **quote bank** (HIGH = verbatim-safe; MED = paraphrase only)
4. Conditioning confidence score + down-weighted sections

**Discipline (Rule 12):** the transcript is a primary source for what a person *said in the room* — quote freely. It is NOT a source for external firm/person *thesis* claims; those still need independent citation before public use (CLAUDE.md Rule 12).

## Step 4 — Invoke content-correspondent with structured Granola input

Pass content-correspondent skill the following structured input (NOT raw transcript paste — leverage Granola's pre-synthesis):

```
Event: [Notion Event Name]
Date: [Event Date]
Notion Event URL: [Notion page URL]
Granola Note URL: [web_url from Granola]

=== Granola AI Summary (primary input — use for angle, takeaways, thesis) ===
[summary_markdown verbatim]

=== Conditioned Quote Bank + Glossary (from Step 3.5 — verbatim quote source) ===
[transcript-conditioning output: confidence-scored quote bank attributed to resolved speakers, the entity glossary (proper-noun spelling for public copy), the speaker-resolution table, and the conditioning confidence score. Quote HIGH-confidence lines verbatim; paraphrase MED; never print excluded-garble entities. If Step 3.5 was skipped, pass the raw diarized transcript here instead and note the skip.]

=== Attendees (cross-reference against Notion People DB) ===
[attendees + calendar_event.invitees, deduped]

=== Notion Pre-Event Brief (if available — for documentary thesis continuity) ===
[Pull from Notion: research_brief Content Draft linked to this Event]
```

content-correspondent then runs its standard logic per `.claude/skills/content-correspondent/SKILL.md`: bucket-sorts contacts, drafts Tier 1 comment + Tier 2 post + visual carousel brief + bucket A/B outreach DMs. The skill's existing "Granola → structured notes if the session was recorded; use for direct quotes from speakers" line is now operationalized — the structured input is exactly what it asked for.

## Step 5 — Write drafts to Notion via notion-writer

Once content-correspondent returns drafts, dispatch `notion-writer` to commit them:

```
subagent_type: notion-writer
prompt: [drafts list + Notion Event URL + People relations resolved + today's date]
```

Each draft becomes one Content Drafts row with:
- `Content Type` per draft (linkedin_post_post, linkedin_dm_speaker, linkedin_dm_host, etc.)
- `Event Phase` = `post_event`
- `Content Status` = `needs_review`
- `Platform` = `linkedin`
- `Event` relation = Notion Event URL
- `People` relation = matched People DB rows for each bucketed contact

## Step 6 — Summary

```
✅ /post-event-content complete: [Event Name]

Granola source: [note title] — [match path used]
Drafts created: N
  - Tier 1 comment: [Notion URL]
  - Tier 2 post + visual brief: [Notion URL]
  - Bucket A outreach: N drafts
  - Bucket B outreach: N drafts

All drafts in needs_review. Edit in Notion → mark approved when ready to ship.
```

---

## API key storage

Default storage: `~/.zshrc` export.

```bash
# Add to ~/.zshrc
export GRANOLA_API_KEY="grn_..."
```

Then either restart the terminal or run `source ~/.zshrc` before launching Claude Code.

**Caveat from project memory (`project_claude_code_env_handoff.md`):** Dock-launched Claude Code does NOT inherit `~/.zshrc`. Launch from terminal so `$GRANOLA_API_KEY` is visible. Same constraint as the Linear hook (`LINEAR_API_KEY`).

If the env var is missing at command time, the command should fail clean:

```
❌ GRANOLA_API_KEY not set. Add to ~/.zshrc:
   export GRANOLA_API_KEY="grn_..."
Then relaunch Claude Code from terminal.
```

NEVER hardcode the key in this file or in any committed file. NEVER log the key in command output.

---

## Failure modes

- **GRANOLA_API_KEY not set** — fail clean with setup instruction (above).
- **Granola API 401** — key invalid or expired. Tell Alex to regenerate in Granola Settings → API.
- **Granola API 429** — rate limit (5/sec sustained, 25 in 5sec burst). Sleep 2s and retry once.
- **Granola API returns empty list for the date window** — widen window to event_date ±48h once. If still empty, no recording exists (common for **in-person events** — Granola has no Android app). Offer the **manual-paste path**: Alex pastes his own recording's transcript, **persist it to `event-transcripts/YYYY-MM-DD_Event.md`** so it survives across sessions (see memory `feedback-comment-workflow-2026-05-26`), then run **Step 3.5 conditioning** on it (mandatory for manual paste) → Step 4. Or skip.
- **Multiple Granola notes match with comparable confidence** — present list with title + start_time + duration, ask Alex to pick.
- **Notion Event row not found** — present top 3 title-similarity candidates from Events DB. If none, allow "create draft without Notion anchor" path.
- **Notion People DB doesn't match Granola attendees** — pass attendee names through unmatched; content-correspondent will still draft outreach but Content Draft `People` relation will be sparse. Acceptable — Alex can backfill in Notion if needed.
- **notion-writer fails** — flag the error, return the in-memory drafts to Alex in chat so the work isn't lost. He can paste manually.

---

## Why this design

The friction kill is removing the transcript-paste step, not removing Alex from the loop. Granola already does diarization + AI synthesis; piping that structured output into content-correspondent (vs. raw transcript noise) gives the skill a higher-quality input and frees Alex from the post-event drain of "now I have to find the file and paste it in."

The dual-path resolution (GCal ID first, title fuzzy fallback) means:
- Future events captured via `/check-new-events` get the deterministic join automatically
- Existing events from before the GCal ID property was added still work via fallback
- No backfill required for the 2 events tomorrow — they'll match on title+date

The `summary_markdown` + diarized `transcript` together is intentional: summary drives angle/thesis decisions, transcript provides verbatim quotes for color. Summary alone is too tidy for Alex's documentarian voice; transcript alone is too noisy for fast angle-finding.

---

## Ground truth references

- **Granola API docs**: https://docs.granola.ai/introduction (auth, endpoints, rate limits)
- **Granola Get Note schema**: https://docs.granola.ai/api-reference/get-note.md (calendar_event, transcript, attendees fields)
- **Conditioning skill (Step 3.5)**: `.claude/skills/transcript-intelligence/transcript-conditioning/SKILL.md` — speaker resolution, entity glossary, confidence-scored quote bank
- **Downstream skill**: `.claude/skills/content-correspondent/SKILL.md` — content generation logic, bucket sorting, ladder
- **Downstream agent**: `.claude/agents/ops/notion-writer.md` — Content Drafts row creation, property mapping
- **Notion Events DB ID**: `9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`
- **Notion Content Drafts DB ID**: `6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`
- **Upstream chain**: `/check-new-events` → `/event-deep-research` writes `Google Calendar Event ID` to Events DB → this command uses it
- **Discipline-break decision record**: `.claude/notes/execution-week-frictions.md` (2026-05-20 entry for Granola integration)
