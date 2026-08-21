# ADR-5 — The event research brief is ONE artifact: a scannable head + a deep prose body

- **Status:** Accepted (2026-08-21). **Linear:** YED-136. **PRD:** ChatPRD "Event Field Guide" (Empire State project) + Notion mirror. **Spec:** `.claude/proposals/event-field-guide.md`. **Validated by:** the Daytona render spike (`.claude/proposals/field-guide-spike-daytona.md`). **Adversarial pass:** `alex:cto-principal-architect` pre-mortem, folded in.
- **Decider:** Alex — "collapse brief and field guide into one research output," always-maximal depth.
- **Scope note:** Governs the **base event pipeline's Notion Content model** — distinct from ADR-0…4 (the Market-Intelligence Supabase graph). Extends the append-only ADR practice to the base pipeline because it sets a structural invariant.
- **Drafting note (honesty):** An earlier same-session draft of this ADR specced the Deep Read as a *separate, non-canonical companion* Content Draft. That was reversed **before any build** — Alex correctly identified that a second artifact overlapping the brief was ~60–70% redundant (mostly *form*, not new facts) and would split attention. This record supersedes that draft in place. The decision below is the merged design.

## Context

`/event-deep-research` writes a single `research_brief` that serves two needs at once: a **scannable in-room reference** (who to talk to, hooks, questions, signals — glanceable on a phone at the event) and, aspirationally, a **readable briefing**. The database-shaped bullet-lattice form optimized the first and strangled the second — the read felt "light, highlighty, machine-readable." Alex wants a ~45-minute, prose, novice-friendly **commute read** that makes him conversant in a space he's new to, and a richer substrate for pre/post-event content. The render spike proved the prose quality is achievable and clearly beats the lattice. The open question was *artifact shape*: a second document, or one document doing both jobs.

## Decisions

1. **One artifact, two layers — not two artifacts.** The research brief is a single Notion record (the existing `research_brief` Content Draft body + the Event page `## Research Brief` section), structured as:
   - **The Scan (head):** Quick Take · People at-a-glance (hooks + prioritization signals) · Questions to ask · Success Signals · Verification Flags. Terse, phone-glanceable in the room. This is roughly today's brief, minus the topic/company lattice.
   - **The Deep Read (body):** the prose "Field Guide" — The Frame · Primer/Landscape (topic lineage + inline jargon + mechanism + live debate) · Companies (narrative arcs) · People (career arcs) · Cross-Event Threads. Rendered by the `field-guide-renderer` (Opus, section-by-section). Carries the topic + company depth that the lattice used to hold, now as comprehension prose.
   - Topics and companies live in the Deep Read (not double-covered in the head); people appear in both at two resolutions (10-second hook in the head, full arc in the body) — that's overview-vs-detail, not redundancy.

2. **No separate Content Type, no companion, no dual source of truth.** The Deep Read is a section of the one brief. The content pipeline (`pre-event-content`, `post-event-content`, `pattern-synthesis`) reads this one, now-richer artifact. Canonicality is trivial: there is one artifact. (The bigger ingest input is a non-issue at current context sizes — Alex, 2026-08-21.)

3. **The Deep Read renders decoupled and additive.** The Scan head + the Step-4 entity writes commit **first and independently**. The Deep Read is rendered and **appended** after, in a phase that may fail without affecting the Scan head, the entity records, or the content pipeline. A Deep-Read render failure is a warning, never a pipeline failure. Idempotent: re-runs replace the `## Deep Read` section under a `deep_read_rendered` marker; the rest of the page stays append-only.

4. **The Deep Read does not duplicate outbound outputs.** It renders comprehension only — NOT prepared questions (those are the Scan head), NOT documentarian post-angles or connection-note copy (those are `pre-event-content`). It is the substrate those draw from. This is the edge-redundancy the merge exists to remove.

5. **Provenance + citations are part of the contract.** Every Deep-Read claim carries a source tier (`web-verified` / `notion-prior` / `email-signal`); a `notion-prior` claim may not appear unless web **re-grounds** it (Rule 12 extended to the memory layer — prevents self-memory laundering across recurring entities). Well-established technical background may define jargon without a citation; funding/metric/CVE/positioning claims must be cited. Citations are **endnotes** (body stays audio-clean for a later ElevenLabs/NotebookLM step).

## Options rejected

- **Separate companion Field Guide** (the earlier same-session draft) — ~60–70% redundant with the brief (mostly form), two artifacts to keep in sync, split attention (SEV-2.7). Rejected — this is the whole reason for the merge.
- **Deepen the brief but skip the long-form read** — leanest, but gives up the cram-for-the-final artifact Alex explicitly wants. Rejected.
- **Expand into one giant undifferentiated doc** (no scan/deep split) — would force a 45-minute scroll to find an in-room hook. Rejected in favour of the head/body split.
- **Coupled render** (Deep Read inside the same write transaction as the Scan head) — puts a ~13k-token generation on the working critical path. Rejected — see Decision 3.
- **Inline citations** — read terribly aloud; block the audio path. Rejected for endnotes.

## Consequences

- **Positive:** one source of truth (no sync/attention split); the real new value (historical spine + mechanism + prose) is preserved; the content pipeline gets a richer substrate for free; a leaner build than the two-artifact plan (no separate Content Type, no dual-compression gymnastics).
- **Costs:** the brief body gets long (accepted — negligible at current context sizes); the render is always-maximal on Opus (cost accepted, Alex's call); document discipline is required to keep the Scan head genuinely scannable and the Deep Read genuinely deep.
- **Reversibility:** high. The Deep Read is an appended, marker-guarded section; removing or restructuring it touches nothing the pipeline depends on structurally.

## Build note

No schema migration: the Deep Read is body content on the existing `research_brief` Content Draft + Event page. Confirm the render→append phase runs only after the Scan head has committed (Decision 3). The `field_guide` Content Type from the earlier draft is NOT created.
