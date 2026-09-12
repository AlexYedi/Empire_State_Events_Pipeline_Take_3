# ADR-6 — The research brief is canonical as a Content Draft; the Event page carries the head, not a full mirror

- **Status:** Accepted 2026-09-11 (Alex).
- **Relationship to ADR-5:** **Refines, does not reverse.** ADR-5's core principle — *one artifact, two layers (scannable head + deep prose body)* — stands unchanged. This ADR settles only **where the deep body is stored**, and removes the duplication ADR-5 left in place.

## Context

ADR-5 Decision 1 defined the brief as "a single Notion record (the existing `research_brief` Content Draft body + the Event page `## Research Brief` section)." In practice that means the **full body is written twice** — once to the Content Draft (named canonical) and once mirrored into the Event page. The post-event path mirrors the same way (`## Post-Event Brief`, guarded by a `post_event_processed` idempotency marker).

The open ruling was framed as "research-brief artifact **discrete vs. event-body**." On inspection it was never either/or — the brief is already discrete *and* mirrored. The real question: **keep the mirror?**

Two copies of the same long-form body means drift risk, doubled write cost, and ambiguity about which is authoritative.

## Decisions

1. **Canonical stays the discrete `research_brief` Content Draft.** Unchanged from ADR-5.
2. **The Event page carries the scannable head only** — or a link plus a short summary — under `## Research Brief`. It does **not** mirror the Deep Read body.
3. **Post-event follows the same rule:** the `post_event_brief` Content Draft holds the full body; the Event page carries a pointer/summary under `## Post-Event Brief`.
4. **Idempotency + quality markers stay on the artifact** (`deep_read_rendered`, `post_event_processed`), not the entity.

## Rationale — why discrete stays canonical

- **Artifact ≠ entity.** An Event is a real-world occurrence (a graph node). A brief is an artifact *about* it, with its own lifecycle: version, `Content Status` (needs_review → approved), and a render marker. Events have no review status; briefs do.
- **Graph (decisive).** Content Drafts support **multi-Event relations** — the mechanism pattern-synthesis uses for two-thesis posts spanning 2+ events. A brief living only in an Event body **cannot relate to a second event**; the hyperedge is lost.
- **Measurement.** Content Drafts carry `Goal` / `Target` / `Outcome` / `Outcome Value` — the acted-on-value north-star hangs off those properties. Page-body text has **no properties**: not filterable, not goal-taggable, not outcome-trackable. Collapsing into the Event body would silently amputate every brief from the measurement layer.
- **RAG (YED-118 / YED-156).** Chunking and retrieval need documents with stable identity + metadata for provenance and clean supersede/versioning. Chunks harvested from an Event page body inherit the *Event's* identity, degrading "which artifact asserted this, and which version?" — exactly the citation quality the Doc-KB exists to provide.
- **Regeneration.** Re-running research refreshes the artifact without rewriting the entity page that carries the event's relation graph.

## Options rejected

- **Event-body-only (drop the Content Draft).** Loses multi-Event relations, all filterable/measurable properties, and clean RAG provenance. Rejected.
- **Status quo — full dual-write.** Two full copies of a long body drift, double the write cost, and blur which is canonical. Rejected; this ADR exists to remove it.

## Consequences

- The Event page becomes a **navigational surface** (head + pointer), not a second content store — "one place to look at the event" ergonomics survive without a second copy.
- Write paths change: `/event-deep-research` (Step 4) and `/post-event-content` append the head/pointer instead of the full body.
- **No backfill required.** Existing Event pages keep their mirrored bodies; the rule binds new runs. Trimming historical mirrors is optional cleanup, not a migration.
- `.claude/references/notion-schema.md` needs its brief-placement notes updated to match.

## Build note

Touches the Notion write path (parent-thread MCP writes) + the schema reference. Confirm the Event-page append still runs only after the Scan head has committed (ADR-5 Decision 3).
