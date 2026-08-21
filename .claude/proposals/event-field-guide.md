# Event Research Brief v2 — one artifact: scannable head + deep prose body

**Status:** Approved to build (merged design) · **Owner:** Alex · **Date:** 2026-08-21
**Linear:** YED-136 · **PRD:** ChatPRD (Empire State) + Notion mirror · **ADR:** `docs/adr/ADR-5-event-field-guide.md`
**Validated by:** the Daytona render spike — `.claude/proposals/field-guide-spike-daytona.md`

---

## Problem

`/event-deep-research` briefs read as **light, highlighty, cryptic — machine-readable, not human-readable.** Root cause (from the actual files): the output contract is a fixed nested-bullet lattice; an April-2026 prose era read far better — **the pipeline regressed from prose to lattice.** Alex commutes 2+ hours/day and would read a substantive briefing; he also enters spaces where he's a novice and wants **"cram-for-a-final"** grounding — historical context tied to current events, with the confidence to engage in the room. Gaps in today's design: no historical/foundational layer, no novice on-ramp (jargon undefined, mechanisms unexplained), and accumulated prior work compressed for machines, never surfaced richly to Alex as a reader.

## Goal

Turn the research output into **one artifact with two layers** — a scannable in-room head and a deep, prose, novice-friendly commute-read body — that also serves as a richer substrate for pre/post-event content. **No second artifact** (an earlier draft proposed a separate companion Field Guide; rejected as ~60–70% redundant with the brief — see ADR-5).

## Solution — one artifact, two layers

The research brief (the existing `research_brief` Content Draft body + the Event page `## Research Brief`) becomes a single record with two layers:

### The Scan (head) — in-room, phone-glanceable
- **Quick Take** (2–3 sentences: the room / why it matters for Alex / best angle)
- **People at-a-glance** (per person: 1-line + personal & professional hook + prioritize / de-prioritize / open-on-site)
- **Questions to ask** (prepared + open questions)
- **Success Signals** (incl. ≥1 anti-signal)
- **Verification Flags**

Roughly today's brief, **minus** the topic/company bullet lattice (that depth moves to the Deep Read).

### The Deep Read (body) — the commute read (rendered by `field-guide-renderer`, Opus)

| Section | Hard max | Purpose |
|---|---|---|
| The Frame | ~600w | Orientation: the room, state of the field, why now, what he'll walk out able to discuss |
| Primer / Landscape | ~3,000w | The "cram-for-the-final" core: per topic — lineage, jargon defined inline w/ analogy, the *mechanism* behind claims, live debate, trajectory |
| Companies | ~2,000w | Narrative arcs: founding thesis → funding arc → evolution → today → headwinds → why here |
| People | ~2,000w | Career arcs (deep on 3–5, lighter on rest): how POV formed → recent activity → prior threads → what to engage on. Named + thanked. |
| Cross-Event Threads | ~600w | Continuity: recurring people, evolving debates, the arc across events attended |

**Not in the Deep Read:** prepared questions (Scan head), documentarian post-angles / connection copy (`pre-event-content`). The Deep Read is comprehension substrate, not a second copy of outbound outputs.

### Size / scale

- **~8,500-word CEILING** for the Deep Read at a rich event (≈45 min dense read). **Ceiling, NOT a quota** — scales down for small events, **never padded.** Section budgets are **hard maxes**, enforced by an evidence-count gate + a `/judge-build` density criterion (not positive word targets — those *are* the padding incentive).
- Expansion decomposition (honest): **~1/3 form** (prose) + **~2/3 new substance** (historical spine, mechanism, cross-event threads, more facts, citations).

## Three new research layers

1. **Historical spine** — topic lineage; company founding-thesis → funding-arc → evolution; speaker career arc.
2. **Novice on-ramp** — jargon defined inline w/ analogy; the *mechanism* behind fix-claims. (Common technical background defines terms without a citation; funding/metric/CVE/positioning claims must be cited — validated on the spike.)
3. **3-source knowledge elevation (per entity):** (1) **Notion** accumulated cross-event memory + (2) **Email/newsletters** recency radar → (3) **Web** grounds / verifies / deepens the leads. Notion+Email surface accumulated + live leads → Web elevates into grounded, current, cited depth.

## Resolved design decisions (post pre-mortem + spike)

- **One artifact (ADR-5).** No separate Content Type, no companion, one source of truth. The bigger ingest input is a non-issue at current context sizes.
- **Topology (MCP constraint):** all Notion + email retrieval runs in the **parent thread** (MCP unavailable in subagents); the parent builds a provenance-tagged evidence pack **carrying source URLs** and injects it into the web specialists, which do web grounding only.
- **Single evidence set:** one retrieval → one ranked, provenance-tagged evidence set (URLs preserved end-to-end — the spike caught their absence). The Scan-head specialists and the Deep-Read renderer draw from the same set.
- **Renderer:** `field-guide-renderer` subagent, **section-by-section on Opus** + a stitch pass. Validated on the Daytona spike (decisive pass).
- **Decoupled + additive render (SEV-3.8):** the Scan head + entity writes commit first, independently; the Deep Read is rendered and **appended** after, guarded by a `deep_read_rendered` marker (idempotent re-runs replace only that section). A render failure is a warning, never a pipeline failure.
- **Anti-padding:** evidence-count gate ("< ~3 grounded facts → 2–3 sentences and stop") + `/judge-build` density criterion (word-to-cited-fact ratio). Budgets are hard maxes; brevity rewarded.
- **Provenance discipline:** source-tier every claim (`web-verified` / `notion-prior` / `email-signal`); a `notion-prior` claim may not appear unless web **re-grounds** it (Rule 12 extended); newsletters = lead-generators only; verify Gmail identity (name-collision). **Citations = endnotes** (audio-clean body).
- **Specialists** (`company-`/`person-`/`topic-` researchers): add historical-spine + novice-on-ramp instructions + accept the injected evidence pack + a richer return schema. (Registry is session-frozen → author now, test in a fresh conversation.)

## Non-goals (v1)

- No second artifact / companion Field Guide (merged into the one brief).
- No audio build (prose is written audio-ready with endnote citations; wiring later).
- No depth toggle — always-maximal depth (cost/runtime accepted, Alex's call).
- The Deep Read never duplicates prepared questions or `pre-event-content`'s outbound outputs.

## Build tasks (remaining)

1. Step 1.7 → one provenance-tagged evidence set **carrying URLs** (rich, ranked) — SKILL + command + `knowledge-conditioning`.
2. Specialist edits — historical spine + novice on-ramp + accept the injected evidence pack.
3. `/event-deep-research` + SKILL — restructure the brief into Scan head + Deep Read; the parent orchestrates the section-wise render loop + stitch, then **appends** the Deep Read after the head commits (decoupled).
4. `/judge-build` density criterion (word-to-cited-fact ratio).
5. End-to-end test in a **fresh conversation** (registry freeze) → run `/judge-build`.

## Success criteria

- A rich event's Deep Read reads as flowing prose (spike-level quality), is historically grounded + current + cited, defines its own jargon, and surfaces cross-event continuity — at ≤45 min, never padded.
- The Scan head stays genuinely scannable in the room; the content pipeline keeps working off the one (richer) brief.
- Alex reports he'd actually read it on the commute and walks in grounded.

## DoD

- [x] Spec (this doc) · PRD in ChatPRD → Notion mirror · Linear YED-136 · adversarial pass (folded in) · **render spike (validated)**
- [ ] Build-quality judge (`/judge-build`) run within N hours of the build
