# ADR-6 — CRM boundary: Clarify is the live CRM, Notion stays the record, HubSpot goes dormant

- **Status:** Proposed (2026-09-08). Flips to **Accepted** once the §Gate free-tier verification is GREEN and Alex signs off. **Linear:** to open on the retarget workstream. **PRD:** pending (ChatPRD + Notion mirror — flagged; this ADR + the two proposals are the interim spec artifact). **Spec:** `.claude/proposals/clarify-crm-migration.md` (retarget + migration) + `.claude/proposals/clarify-integration.md` (capture lane + API reality). **Validated by:** live Clarify REST dry-create probe, 2026-09-08 (create shapes confirmed; note/merge/delete found MCP-only). **Adversarial pass:** the migration plan §7 risk table (`alex:cto-principal-architect`-authored) + this record's Options-rejected.
- **Decider:** Alex — "adopt Clarify as the capture + CRM layer; migrate the HubSpot book into it."
- **Scope note:** Governs the **base event pipeline's CRM write destination** (post-event `/post-event-content` Step 5.5) and the meeting-capture layer. Distinct from ADR-0…4 (the Market-Intelligence Supabase graph) and ADR-5 (the Notion content model). Extends the append-only ADR practice — reversing this = writing ADR-7, not editing ADR-6.
- **Drafting note (honesty — two mid-flight corrections, both caught before any build):**
  1. The companion plan first recommended **fresh-start, not migration**, on a "near-empty HubSpot" assumption. Falsified live (**245 contacts / 182 companies + event Notes** via the HubSpot MCP) → reversed to **MIGRATE** before code. Root cause: an assertion carried from prior context without the available one-call check.
  2. The write path was first specced **REST-via-`.env`** for all four functions. A live probe showed **notes/comments, merge, and delete are MCP-only** (no REST object type; all 404) → the write path is now **hybrid** (REST create + MCP note/merge/delete). Create shapes were confirmed 201 (JSON:API wrapper mandatory).

## Context

Granola (the prior capture tool) is nonoperational and captures no slides; webinars entered the schedule, which need slide capture. Clarify (`clarify.ai`) was adopted as the capture layer (its macOS local recorder captures non-host webinars incl. slides — `clarify-integration.md`). Clarify is also an AI-native CRM with a write API. Today the pipeline's post-event CRM writes go to **HubSpot** (Step 5.5 — gated, selective, create-once). A single deliberate CRM-write target is wanted; capture + CRM + AI-enrichment in one system is the draw. Known facts as of 2026-09-08: HubSpot holds **245 contacts / 182 companies + event Notes**; Clarify **auto-syncs Alex's Google Calendar + email** (already holds person + 50+ meeting objects, plus a native `__hubspot_id` field on records); Clarify REST create is confirmed, notes/merge/delete require its MCP.

## Decisions

1. **Three-system boundary.** **Notion = durable knowledge graph / system of record (UNCHANGED)** — People/Companies/Topics/Events/Content/Project Ideas. **Clarify = live CRM + capture + relationship/pipeline layer (NEW write target).** **HubSpot = dormant, one-edit-away fallback.** Clarify does **not** replace Notion; nothing critical lives only in Clarify.

2. **Post-event Step 5.5 writes to Clarify, discipline unchanged.** Same selective bar (spoke-with / opt-in / deliberately-pursued — default exclusion), dedup-search-before-create, create-once (add a Note for existing, never field-merge), human confirmation gate, parent-thread only. Only the destination changes.

3. **The write path is HYBRID (probe-confirmed 2026-09-08).** REST-via-`.env` (`PERSONAL_CLARIFY_KEY` + `WORKSPACE_SLUG`, JSON:API `{"data":{"type":…,"attributes":…}}`) handles **search + create `person`/`company`** (`name` object + flat `company_id` association). The **event-association Note (`add-comment`), dedup-merge (`merge-records`), and delete (`delete-records`) require the Clarify MCP.** Therefore the pipeline write path **depends on the Clarify MCP being connected** — REST alone is insufficient (it cannot attach the Note that is the point of Step 5.5).

4. **Migrate the HubSpot book — do not discard it.** A one-time, dedup-first programmatic backfill of the 245 contacts / 182 companies + their Notes into Clarify (the Notes carry the "met at [event] [date], discussed X" context, which re-capture cannot recover). Dedup against Clarify's auto-synced people/companies by name+email and the native `__hubspot_id`; EXISTS → add Note only; NEW → create then Note; batch-gated with a spot-check. Record-creates don't burn the AI-credit ceiling; well under the 20K-record cap. This backfill also clears the **outstanding deferred post-event backfill for last week's events** (NYC Voice AI Meetup 9/1 + Remy Masterclass 9/2 — verified never run: zero Sept HubSpot contacts).

5. **Gated on free-tier verification.** Before the retarget flips, verify in-app: (a) AI credit ceiling, (b) retention period, (c) data export. If any is disqualifying, the fallback holds with zero pipeline harm: **capture stays on Clarify, CRM writes stay on HubSpot** (Notion is the record either way).

## Options rejected

- **Stay on HubSpot for CRM** — rejected: Clarify unifies capture + CRM + enrichment and has a native write API; HubSpot has no data lock-in keeping us. (Note: the *trigger* to move is the capture gap, not CRM dissatisfaction — but once capturing in Clarify, splitting the CRM elsewhere is friction.)
- **Fresh-start / skip the migration** — rejected: the "near-empty" premise was false; 245 real contacts + event Notes are worth keeping live, and re-capture-on-next-touch loses the historical context that lives only in the Notes.
- **REST-only write adapter** — rejected as *impossible*: notes/merge/delete are MCP-only (probe-confirmed). The adapter must be hybrid; the MCP connection is a hard dependency of the write path.
- **Clarify replaces Notion too** — rejected hard: Clarify's free-tier retention/export are unverified and the product is ~15 months old; Notion's relational knowledge graph is the durable asset and stays the system of record.

## Consequences

- **Positive:** one system for capture + CRM + AI-enrichment; the 245-contact relationship history migrates instead of being abandoned; last week's deferred backfill gets cleared in the right system; the create path is de-risked (confirmed live); Notion-as-record keeps the whole move reversible.
- **Costs:** the write path now **hard-depends on the Clarify MCP** (a session-frozen connector — needs a fresh session), not just the REST key; the free-tier AI-credit ceiling is a standing watch item; product youth means the write-body shapes beyond create still need first-run confirmation; a one-time ~1–2 hr gated backfill.
- **Reversibility: high.** Because Notion is the record and HubSpot stays dormant, every failure mode has a **one-edit rollback** (repoint Step 5.5 back to HubSpot) with zero knowledge loss. This is what makes the cutover safe to do this week rather than after a long trial.

## Build note

DoD gate: this ADR is spec-item #1 (decision before code). Do NOT flip Step 5.5 until the §Gate verification is GREEN + Alex signs (Status → Accepted). The live probe confirmed `company`/`person` create shapes and left **2 labeled test records to delete** (`ZZ Adapter Test Co — DELETE ME`, `ZZ AdapterTest DELETE`). The Clarify MCP must be connected (fresh session) before the note/merge/delete half of the adapter — and therefore before any real Step 5.5 write, the migration backfill, or last week's clear-up — can run.
