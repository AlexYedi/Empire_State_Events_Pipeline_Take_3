---
description: "Pull events from the 'Going to Events' Google Calendar (next 14 days), find new ones with a PIPELINE block in the description, and run /event-deep-research + pre-event-content on each — one event at a time with continue-or-quit control between events."
---

# /check-new-events

Lightweight orchestration on top of Workflow A. Detects new event invites that carry a PIPELINE block in the GCal description, dedups against Notion, then runs the full research + content chain on each — interactively, one event at a time. Alex controls the pace via a continue-or-quit prompt between events.

**Input:** none — pulls automatically from the "Going to Events" calendar.

**Output:**
- For each event processed: full Notion writes (Companies, Topics, People, Events, Content Drafts) + HubSpot writes + LinkedIn drafts in `needs_review` via pre-event-content
- Final summary: events seen / processed / skipped / errored

---

## Trigger

This command runs when:
- Alex types `/check-new-events`
- Alex says "check the calendar for new events", "any new events to research", "what's new on my calendar", "pull new invites"

## Required inputs

None. The calendar ID and time window are hardcoded; the PIPELINE block is the structured input.

## Step 1 — Query Google Calendar

Use `mcp__claude_ai_Google_Calendar__list_events` with these exact parameters:

- `calendarId`: `4c84184ac3e761c3f94be43193656a785ece4752ed6b553facfcb52e668a333b@group.calendar.google.com` (the "Going to Events" calendar)
- `startTime`: current ISO 8601 timestamp in `America/New_York`
- `endTime`: 14 days from now in `America/New_York`
- `pageSize`: 50
- `eventTypeFilter`: `["default"]` (skip OOO, focusTime, birthdays, etc.)
- `orderBy`: `startTime`

**Failure mode:** if the MCP call errors, report it cleanly and exit. Do NOT proceed with stale or partial data.

## Step 2 — Detect PIPELINE blocks

For each event in the response, check the `description` field for a PIPELINE block.

A valid PIPELINE block is:
- A line containing `---` (markdown horizontal rule, may have surrounding whitespace)
- Immediately followed by a line starting with `PIPELINE` (case-sensitive)
- Continues to end of description (no terminator needed)

The description may contain:
- HTML entities (`&amp;`, `&lt;`) — preserve as-is for now; LLM parser will handle
- `<br>` tags — treat as line breaks for block detection
- Other organizer content — only the PIPELINE block matters for parsing

If no PIPELINE block found in any event, report:
> "No new events with PIPELINE blocks in the next 14 days. Either you haven't added the block to any new invites, or all events with blocks are already in Notion."
Then exit.

## Step 3 — Parse PIPELINE fields (LLM, not regex)

For each event with a PIPELINE block, extract the structured fields using natural-language understanding (NOT strict regex):

- **Speakers** — list of `Name (Title, Company)` entries, but tolerate format variations: comma/dash/at-sign/semicolon separators, bulleted lists, missing titles, missing companies, just-names
- **Host** — organizing entity name (free text)
- **Topics** — comma-separated keywords (any separator OK)
- **URL** — first http(s) URL in the block (optional)
- **Intent** — one of `attend`, `documentary`, `both` (optional; default to `attend` if absent)

Required fields: Speakers, Host, Topics. If any of these are missing or empty, log the event as a parse warning and exclude it from processing — surface it at the end of the run.

## Step 4 — Dedup check against Notion

For each parsed event, query the Notion Events DB to check whether a row already exists:

- Use `mcp__notion__notion-search` with the event title as query, then filter results to the Events database (`9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`)
- Compare by event title + start date (both must match)
- If a match exists: classify as DUPE (skip — do not re-process)

**Failure mode:** if Notion search fails, fail open — proceed to Step 5 and let `/event-deep-research`'s own Step 1.5 dedup logic catch the duplicate (slightly more work, but no data risk).

## Step 5 — Present detection summary to Alex

Before running any research, surface the full plan in this format:

```
📅 Checked "Going to Events" — next 14 days

Found N events with PIPELINE blocks:
  ✨ NEW (will process):
    1. [Event title] — [date, time]
       Speakers: [parsed]
       Host: [parsed]
       Topics: [parsed]
       Intent: [parsed]
    2. ...
  ⏭️  DUPE (already in Notion — skipping):
    - [Event title] — [date]
  ⚠️  PARSE WARNING (incomplete PIPELINE block — needs your attention):
    - [Event title] — missing: [field]

About to run /event-deep-research + pre-event-content on N new events, one at a time.
Continue? [y / cancel]
```

Wait for Alex's confirmation before proceeding.

## Step 6 — Per-event chain (loop with continue-or-quit)

For each NEW event, in chronological order (soonest first):

### 6a. Run /event-deep-research

Execute the full `/event-deep-research` workflow as documented in `.claude/commands/event-deep-research.md`. Pass the structured PIPELINE fields as the input in this natural-language format:

```
Event: [event title]
Date: [event date]
Location: [event location from GCal]

[Original description from organizer — text BEFORE the PIPELINE block in the GCal description]

Speaker: [Speakers parsed from PIPELINE block]
Host: [Host parsed from PIPELINE block]
Topics: [Topics parsed from PIPELINE block]
URL: [URL parsed from PIPELINE block]
```

This is the format `/event-deep-research` already accepts (per its required-inputs spec: "natural-language description with cues like 'Speaker: Jane Smith, CTO at Acme; Topics: agentic systems, enterprise AI'").

Follow Steps 1 through 6 of `/event-deep-research` exactly — including the three human-in-the-loop checkpoints (entity confirm, triage approval, brief approval). Do NOT bypass any approval gate.

When Step 1 (entity confirm) runs, the entities will largely already be in the input — confirm should be a fast y/n.

### 6b. Run pre-event-content

After `/event-deep-research` completes (Notion + HubSpot writes done), invoke the `pre-event-content` skill for the same event. It pulls the research brief from Notion automatically.

Output: LinkedIn post drafts + speaker/host DMs in Notion Content Drafts (`needs_review` status).

### 6c. Continue-or-quit prompt

After both 6a and 6b complete for one event, present:

```
✅ [Event title] complete.
   - Research brief: [Notion URL]
   - Content drafts: N items in needs_review

[X] more events pending: [list]

Continue with next event ([next event title])? [y / quit]
```

If Alex says yes / y / continue: move to next event.
If Alex says no / quit / stop / done: exit and run Step 7.

## Step 7 — Final summary

When the loop exits (either all events processed or Alex quit), report:

```
📊 /check-new-events session summary

Processed: N events
  - [Event 1 title]: brief + N drafts
  - [Event 2 title]: brief + N drafts
  ...

Skipped (already in Notion): M events
  - [list]

Parse warnings (needs your attention):
  - [Event title] — missing [field]
  - Action: fix the PIPELINE block in the invite and re-run /check-new-events

Pending (not processed this session): K events
  - [list]
  - Action: re-run /check-new-events later to continue
```

---

## Failure modes

- **GCal MCP error** — report cleanly and exit. Don't fake data.
- **No events found in time window** — report "No upcoming events on 'Going to Events' calendar in next 14 days" and exit.
- **No events with PIPELINE blocks** — report the message from Step 2 and exit.
- **All events are dupes** — report "Found N events but all are already in Notion" and exit.
- **Parse warning on an event** — exclude from this run, surface at end with the missing field, don't fail the whole session.
- **`/event-deep-research` fails mid-event** — report which event failed, mark it as "errored" in the summary, and prompt whether to continue with the next event or quit.
- **Notion search fails (Step 4)** — fail open: proceed without pre-dedup, let `/event-deep-research` Step 1.5 dedup catch it.

---

## Ground truth references

- **GCal MCP**: `mcp__claude_ai_Google_Calendar__list_events` — see schema in tool docs
- **Calendar ID** (Going to Events): `4c84184ac3e761c3f94be43193656a785ece4752ed6b553facfcb52e668a333b@group.calendar.google.com`
- **Notion Events DB ID**: `9dcbc999-b4ed-4a51-b48a-10aaf171f1ba` (see CLAUDE.md § Notion Database IDs)
- **Downstream command**: `.claude/commands/event-deep-research.md` (Workflow A — full research pipeline)
- **Downstream skill**: `pre-event-content` (canonical content skill — pulls brief from Notion)
- **PIPELINE template**: `.claude/references/pipeline-block-template.md` (added in Phase 7)

---

## Why this design (not a scheduled remote routine)

`CronCreate` (the only scheduling primitive available in this environment) is session-bound — jobs fire only while the Claude Code REPL is running on Alex's Mac. A scheduled remote routine on Anthropic's infrastructure also wouldn't work because project-level slash commands (`/event-deep-research`) and skills (`pre-event-content`) are scoped to Claude Code running in this repo, not to Claude.ai routines.

Additionally, `/event-deep-research` has three human-in-the-loop approval gates by design (entity confirm, triage approval, brief approval) — quality controls that catch hallucinated entities, prevent duplicate writes, and let Alex correct the brief before commit. "Silent automation" of the full chain would either bypass those gates (losing quality) or require Alex's presence anyway (so the scheduling buys nothing).

The session-driven design captures the original "PIPELINE block in the invite = structured intake" insight without those constraints. Alex types `/check-new-events` when he opens Claude Code; drafts populate as he watches; review distributes across days because Alex picks one event at a time via the continue-or-quit prompt.

See `.claude/notes/execution-week-frictions.md` for the full discipline-break decision record (2026-05-20).
