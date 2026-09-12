# Architecture Decision Records — data layer

**Architecture Decision Records (ADRs)** capture *one decision each*: the context, the options considered, the choice, and its consequences. They exist to answer, for future-you or a collaborator, **"why is it shaped this way, and what were we deliberately choosing against?"** — so settled decisions aren't silently re-litigated and load-bearing constraints aren't violated by accident.

These records govern the **Market-Intelligence graph** (the consolidated single graph on the Empire prod DB, `oicikjyzmxqfomrrqkvf`). They were produced during the MI data-spine consolidation (Linear **YED-130**) and promoted here from a loose working folder so they live, versioned, next to the code they explain.

## The convention (read before changing anything they govern)
- **ADRs are append-only.** You never *edit* a past decision to reverse it — you write a **new** ADR that says "supersedes ADR-N," and mark the old one superseded. That keeps the decision history intact and makes reversing a decision a deliberate, recorded act (not a silent drift).
- If you're about to touch consolidation, the hubs' data access, the account boundary, or the event/intelligence model, **read the relevant ADR first.** If your change contradicts it, that's a new ADR, not a quiet override.

## The records
| ADR | Decision | The constraint it sets |
|---|---|---|
| [ADR-0](ADR-0-reconciliation.md) | Operating frame: three layers, decided separately | Don't re-bundle "which spine wins" — data / surface / capability are independent decisions |
| [ADR-1](ADR-1-data-layer.md) | Data → **Consolidation** (one graph), carry-forward hybrid | Migrate curated intelligence; recompute only deterministic math. Don't regenerate on thinner data |
| [ADR-2](ADR-2-surface-layer.md) | Surface → **Coexistence** (two hubs) | gtm-os-hub's identity is an **invariant** — never flatten it. Neither hub owns canonical state |
| [ADR-3](ADR-3-capability-layer.md) | Capability → **Extract** spine-agnostic substrate | Shared plumbing to the plugin; product POV stays lens-specific |
| [ADR-4](ADR-4-increment-2.md) | Increment 2: expand-contract recompute + retire the spine | Never in-place destructive; atomic swap with proven rollback |
| [ADR-5](ADR-5-event-field-guide.md) | Event research brief = **one** artifact: scannable head + deep prose body | One source of truth; the Deep Read renders **decoupled + additive** (a render failure never blocks the pipeline) and never duplicates the scan head or `pre-event-content`'s outbound outputs |
| [ADR-6](ADR-6-research-brief-placement.md) | Brief is **canonical as a Content Draft**; the Event page carries the **head/pointer, not a full mirror** | Refines ADR-5 (does not reverse it). Removes the dual-write of the deep body. Discrete wins on graph (multi-Event relations), measurement (Goal/Outcome properties), and RAG provenance |
| [ADR-7](ADR-7-inbox-signal-source.md) | Gmail inbox as a first-class MI signal source + Gmail write-scope expansion | Two-stage scan (metadata discovery → allowlist-only body extraction); dedup key is the **canonical, redirect-resolved URL**; capture broadly, tag relevance, never filter |
| [ADR-8](ADR-8-system-graph-drift-router.md) | A derived system graph over the repo's own build artifacts — a **router, not a detector** | Derived cache, never hand-edited; it reports *adjacent-to* and *absent*, never *contradicts*; advisory always; ≤5 findings per surface, and a check that drops below 50% precision **shrinks** |

> **Scope:** ADR-0…4 govern the Market-Intelligence Supabase graph. **ADR-5 / ADR-6** govern the **base event pipeline's Notion Content model**; **ADR-7** governs the **inbox as a signal producer** into the MI graph; **ADR-8** governs the repo's **own build-artifact graph — a rigor-layer cache, NOT the MI graph** (both get called "the graph"; they are unrelated). Same append-only discipline throughout, different subsystems.

> **Numbering note (2026-09-12):** two branches independently minted an **ADR-6**. The record above — brief placement — is the one that landed on `main` and keeps the number. A second draft, *"CRM boundary: Clarify is the live CRM"*, was written on the inbox-miner branch and is **not** part of this index: Clarify was rejected and its artifacts removed from `main` in `1240aae` (#58), so that draft never entered the record and there is nothing to reverse. **Mint ADR numbers from `main`, not from a branch** — the collision is only visible after a merge.

Supporting evidence (probe findings, pre-mortems — historical provenance, not live guardrails) is in [`evidence/`](evidence/).

## Related
- **The method, reusable:** [`../migration-playbook.md`](../migration-playbook.md) — the transferable "how to change a live system safely" pattern distilled from this work.
- **The narrative:** the seven-epic build story (shareable Artifact) — the human-readable *why*, start to finish.
- **The running log:** Linear YED-130 (milestones) · YED-131 (live-recompute follow-up).
- **The model reference:** [`../../.claude/references/market-intel-spine.md`](../../.claude/references/market-intel-spine.md) — how the graph works *now* (vs. these records, which explain *why* it's shaped that way).
