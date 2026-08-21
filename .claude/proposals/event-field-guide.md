# Event Field Guide — Spec (one-pager)

**Status:** DRAFT (pending adversarial pass + Alex sign-off) · **Owner:** Alex · **Date:** 2026-08-21
**Working name:** "Event Field Guide" (open to rename)
**Linear:** _(to open)_ · **ChatPRD/Notion mirror:** _(to file)_

---

## Problem

The `/event-deep-research` pipeline produces briefs that read as **light, highlighty, cryptic — more machine-readable than human-readable.** Alex commutes 2+ hours round-trip daily and would read a substantive briefing, but the current artifact is too short and too scaffold-shaped to be worth it. He's also entering spaces where he's a novice and wants "cram-for-a-final" grounding: historical context tied to current events and recent developments, with the confidence to engage.

**Root cause (from the actual files, not theory):** the output contract is a fixed nested-bullet lattice (every topic forced into Current Events / Opportunities / Challenges / Use Cases / Top Questions; every person into Bio / Recent activity / Talking Points / Signals). The *content* underneath is frequently dense — but the *form* reads like a spec sheet. An earlier (April 2026) era of briefs was flowing analytical prose and read far better. **The pipeline regressed from prose to bullet-lattice.** The fix is therefore partly a *restoration* (prose form) and partly an *expansion* (new depth layers), not a from-scratch invention.

Additional gaps in today's design: no historical/foundational layer (all sections are present/forward-looking); no novice on-ramp (jargon undefined, mechanisms unexplained); prior work is compressed for machine consumption, never surfaced richly to Alex as a reader.

## Goal

Off the **same research pass**, produce a second rendering — a long-form, prose, novice-friendly **Event Field Guide** built for the commute read and as the richer foundation for pre/post-event content. Do it **without changing the existing structured-brief contract** that the content pipeline depends on.

## Solution — one research pass, two renderings

1. **Structured Brief** — UNCHANGED contract. Scannable, in-room, keeps feeding `pre-event-content`, `post-event-content`, `pattern-synthesis` (they read the `research_brief` Content Draft). **Do not break this.**
2. **Event Field Guide** — NEW. Long-form prose, cited, novice-friendly. Lives as a **Notion page** (canonical), written as clean read-aloud prose so an ElevenLabs/NotebookLM **audio** step can be added later (not in v1).

### Field Guide spine (proportional budget for a rich event)

| Section | Budget | Purpose |
|---|---|---|
| The Frame | ~600w | Orientation: what this room is, state of the field, why it matters now, what you'll walk out able to discuss |
| Primer / Landscape | ~3,000w | The "cram for the final" core: per topic — lineage (how we got here), jargon defined inline w/ analogy, the *mechanism* behind claims, live debate, where it's heading |
| Companies | ~2,000w | Narrative arcs: founding thesis → funding arc → strategic evolution → today → headwinds → why they're here |
| People | ~2,000w | Career arcs (deep on 3–5 priority, lighter on rest): how their POV formed → recent activity → prior-correspondence/prior-event threads → what to engage on. Named + thanked. |
| Cross-Event Threads | ~600w | Continuity layer: recurring people, evolving debates, the narrowing arc across events Alex has attended |
| Questions, Angles & Sources | ~500w | Smart questions, documentarian angles, citations |

### Size / scale

- **~8,500-word CEILING for a rich event** (≈45 min dense read @ ~180–200 wpm technical). **Ceiling, NOT a quota.**
- Scales *down* for smaller events (a 2-speaker meetup may land at ~4,000w and be complete). **Never pad to hit a number** — write to the density the event actually supports.
- Expansion decomposition (honest promise): **~1/3 of the lift is form** (bullets → full-sentence prose, same facts, more readable ≈1.5–1.7x); **~2/3 is new substance** (historical spine, primer/mechanism, cross-event threads, more facts, citations). Roughly 5× a current ~1,700–1,900-word brief.

## Three new research layers (feed the specialists)

1. **Historical spine** — topic lineage; company founding-thesis → funding-arc → evolution; speaker career arc.
2. **Novice on-ramp** — jargon defined inline with analogy; the *mechanism* behind any fix-claim ("*how* does it solve X"). Extends the existing `define-jargon-inline` content discipline to research.
3. **3-source knowledge elevation (per entity):**
   - **(1) Notion — accumulated cross-event memory:** prior briefs, prior event overlaps, People/Companies/Topics records, banked quotes/observations. The continuity spine. (Cross-event recurrence is high — same NYC AI people/companies circulate.)
   - **(2) Email/newsletters — recency + personal radar:** correspondence, warm-thread state, newsletter coverage (last N days).
   - **(3) Web — grounding + depth:** takes the leads from (1)+(2) and verifies / updates / deepens / grounds them in current events + history.
   - Escalation is the point: **Notion + Email surface accumulated + live leads → Web elevates them into grounded, current, cited depth.**

**Two compression levels off one retrieval:** the *structured brief* keeps the COMPRESSED Prior-Context Pack (N=8, verify-first — correct for feeding specialists). The *Field Guide* surfaces the RICH version generously (cross-event continuity is a novice-grounding tool + documentarian edge). Both derive from the same Step 1.7 retrieval — no second fetch.

## Resolved design decisions (post-adversarial pass, 2026-08-21)

**Topology (SEV-1.1 — MCP constraint):** All Notion-memory + email-recency retrieval happens in the **parent thread** (MCP is unavailable in subagents). Parent builds a per-entity, provenance-tagged **evidence pack** and injects it as text into the web specialists, which do web grounding/verification only. This is the existing Step 1.7 pattern, made explicit for the elevation layers.

**Single evidence set, two views (SEV-2.6):** one retrieval → one **provenance-tagged, ranked evidence set**. The compressed Prior-Context Pack (specialists) is a strict **top-N subset** of the rich set (Field Guide) — never an independent re-summarization. Consistency is structural, not hoped-for.

**Renderer (SEV-1.2):** a NEW `field-guide-renderer` subagent (text-in/text-out), distinct from `event-research-synthesizer`. Renders **section-by-section** (each section against only its evidence slice) + a light stitch/transition pass. **Model: Opus** (prose quality is the goal; single-shot Sonnet is what produced the lattice). Registry is session-frozen → build/test in a fresh conversation.

**Critical-path decoupling (SEV-3.8):** structured brief + Notion writes commit **first, independently**. The Field Guide is a **strictly-additive Phase 2** that can fail without touching the pipeline.

**Canonicality (SEV-2.7):** structured brief stays the **sole pipeline input**. Field Guide is stamped **"reading companion — not source of truth."** Corrections destined for content go on the brief. (Revisit if the split-attention friction bites.)

**Anti-padding enforcement (SEV-3.9 — makes "ceiling not quota" real):** NO positive per-section word targets. Replace with an **evidence-count gate** ("< N grounded facts for this entity → 2–3 sentences and stop") + a **density criterion on `/judge-build`** (flag high word-to-cited-fact ratio). Section budgets below are **hard maxes only**, paired with a coverage checklist; brevity is rewarded.

**Provenance discipline (SEV-2.4 / SEV-2.5 / SEV-3.10 — memory-laundering guard):** every claim carries a source tier (`web-verified` / `notion-prior` / `email-signal`). A `notion-prior` claim may **not** appear in the Field Guide unless web **re-grounds** it (Rule 12 extended to the memory layer). Newsletters are **lead-generators only**, never corroboration — require independent origin. "Mechanism behind the claim" + inline-jargon prose are the highest fabrication-risk zones → bind to the same source-tier discipline; density judge also flags uncited mechanism assertions. Gmail name-collision is a known precision risk — verify identity before importing a thread as context.

**Citations (SEV-3.11):** **endnotes**, collected at each section end — body stays audio-clean. (Prevents a full rewrite when audio is added.)

**Field Guide idempotency (SEV-3.12):** define an **upsert** — match on the Event relation, refresh in place; no duplicate pages on re-run. Home = a `field_guide` Content Draft linked to the Event row (enables Cross-Event Threads). Linking to the Event row is a schema touch → **write the ADR** before wiring. Keep the `research_brief` Content Draft as-is.

**Specialists** (`company-researcher`, `person-researcher`, `topic-landscape-analyst`): add historical-spine + novice-on-ramp instructions + accept the injected evidence pack + richer return schema. (Fresh conversation to test — registry freeze.)

## Sequencing (OPEN — needs Alex)

The pre-mortem flagged goal-conflation: the diagnosed disease is a **form regression** (prose → lattice), whose cheapest cure is **loosening the structured brief's lattice** to allow in-section prose (~70–80% of the April feel, ~5% of the cost, one session, reversible). The Field Guide is the larger commute/novice/audio bet. Two paths:
- **Phase 1 (lattice-loosen the structured brief) → Phase 2 (Field Guide).** Cheap readability win first; also improves the brief Alex + the pipeline read; de-risks Phase 2.
- **Straight to the Field Guide.** The commute read is the headline deliverable; skip the interim.

Either way the Field Guide gets built — this is only about what ships first.

## Non-goals (v1)

- No change to the structured-brief contract or the content pipeline's inputs.
- No audio build (prose is written audio-*ready* with endnote citations; wiring is later).
- No depth "toggle" — Alex chose **always-maximal** depth (cost/runtime increase accepted, his call).
- Field Guide is not yet canonical for the content pipeline (companion only, v1).

## Success criteria

- A rich event produces a Field Guide that reads as flowing prose (April-era quality), is historically grounded + current + cited, defines its own jargon, and surfaces cross-event continuity — at ≤45 min read, never padded.
- The structured brief and the entire downstream content pipeline are byte-for-byte unaffected in contract.
- Alex reports he'd actually read it on the commute and walks in grounded.

## DoD

- [ ] Spec in ChatPRD → mirrored to Notion (this doc)
- [ ] Linear issue opened
- [ ] One adversarial pass (in progress — `alex:cto-principal-architect` pre-mortem)
- [ ] Build-quality judge run within N hours of build
