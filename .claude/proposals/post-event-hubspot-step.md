# Spec — Gated post-event HubSpot step (`/post-event-content` Step 5.5)

**Status:** approved (Alex, 2026-08-25) · **Linear:** YED-142 · **Written before code** (DoD item 1)

## Problem
`/post-event-content` persists the Notion knowledge-graph (People/Companies/Topics, Step 3.8) but has no formal HubSpot CRM step. The founder-showcase branch references "→ CRM" informally; pre-event HubSpot writes were parked in the 2026-08-25 restore loop. We need one deliberate, safe pattern for when CRM writes happen and for whom.

## Decision: post-event, selective, create-once (NOT create-all-then-update)
The rejected pattern is "batch-create a record for every researched speaker up front, then update them all at the end." It fails on two axes:
1. **Enrichment trap** — most researched speakers are never meaningfully engaged; batch-creating them makes CRM a scraped directory, violating the pipeline value philosophy (*relationships, not contact enrichment* — `feedback_pipeline_value_philosophy`).
2. **Fragile update path** — create-then-update forces the HubSpot field-merge path that the predecessor project (new-jack-city) repeatedly broke on. CLAUDE.md Rule 6: *prefer create over update.*

### The encoded pattern
- **Timing:** post-event only. Pre-event, the person record lives in **Notion People** (knowledge graph); HubSpot (relationship/pipeline CRM) gets a contact only once there's a real reason.
- **Selection bar** — a candidate qualifies only if one holds:
  - Alex actually spoke with them in the room, OR
  - they are an opt-in outreach target (named in Step 4), OR
  - they are a deliberate pipeline / job-search target (e.g. a hiring manager at a target company).
  Everyone else stays in Notion People. Default is exclusion, not inclusion.
- **Create-once:**
  - dedup-search HubSpot first by name + company (email is the primary dedup key when known) — Rule 11.
  - **NEW** → create Company (if new) → Contact → associate → one Note.
  - **EXISTS** → add a Note only. Additive; never field-merge existing properties (Rule 6).
- **Note = the event-association mechanism** (Static Lists are unavailable via MCP): `event · date · role · what was discussed · next step`. It only has real content post-event.
- **Human gate:** a dedup'd confirmation table (person · company · NEW/EXISTS · action · note preview) → Alex approves/edits/skips per row before any write. Tier-3 irreversible external write.
- **Idempotency:** before adding a Note, check the contact for an existing Note naming this event — no note-spam on re-run.
- **Default skip:** if nobody clears the bar, skip and say so.
- **Showcase reuse:** for founder-showcase events, Step 3.4's contact-extraction already produced the candidate set (founders + explicitly called-out teammates) + an Apollo CSV — reuse it, don't re-derive.

### The one pre-event exception (out of scope for this command)
A single hand-picked pre-event create is justified for a *known* high-priority target (a hiring manager at a company Alex is actively pursuing) so the touch can be tracked. That is a deliberate one-off done manually — never the batch default, and not part of `/post-event-content`.

## Topology / constraints
- **Parent-thread only.** The HubSpot MCP is unavailable inside subagents (`project_notion_writes_must_be_parent_thread` — same class of constraint). All HubSpot writes happen inline in the parent, which is also where the confirmation table must render.
- **Write order** (CLAUDE.md HubSpot Write Orchestration): Company → Contact + association → Note.
- **Tools:** `search_crm_objects` (dedup) · `manage_crm_objects` (create contact/company, associate, create Note engagement) · `search_properties` / `discover_hubspot_schema` when unsure of internal property names.
- **Schema:** `.claude/references/notion-schema.md` (HubSpot CRM fields + Notes convention).

## Pre-mortem (DoD item 3 — adversarial pass)
- **Duplicate contacts** → mandatory dedup-search-first; classify NEW vs EXISTS before any write; email is primary key.
- **Over-creation / enrichment creep** → the selection bar + default-exclusion + the human gate. If the candidate list looks like "the whole roster," that's the failure signal — cut it.
- **Note-spam on re-run** → idempotency check for an existing event-Note before adding.
- **Fragile field-merge** → EXISTS path never merges properties; it only appends a Note.
- **Silent subagent failure** → writes are parent-thread; if the MCP is unavailable, fail clean and surface the candidate table so Alex can act manually.
- **Wrong-person Note** → the confirmation table shows the note preview + resolved company before write; garbled names are already web-verified upstream (showcase guard).

## Non-goals
- No Static Lists (MCP-unavailable). No sequences/automation. No pre-event writes. No field-merge updates. No auto-write without the gate.
