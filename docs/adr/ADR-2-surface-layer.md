# ADR-2 — Surface layer: two hubs, coexistence

- **Status:** Accepted (2026-08-07). Detail deferred to PRD (Phase 3).
- **Linear:** YED-130. **Depends on:** ADR-0, ADR-1. **MDM style:** Coexistence.
- **Decider:** Alex.

## Context

Empire's brief treated `empire-state-hub` as *the* canonical surface — the erosion vector that would silently supersede gtm-os-hub. Alex's binding constraint: gtm-os-hub's {mission, style, GTM University, `/signal`, Orchid} stay unique ("enterprise, not siloed"). The probe confirmed the learning plane (`nnywrmetdoixdbevvsvf`) is orthogonal, and that `signal_read` — the read-model gtm-os-hub's `/signal` was meant to consume — **does not exist yet** (so `/signal` is nothing-to-strand-yet, a build-it-right opportunity, not a live surface at risk).

## Decision

**Two hubs, both first-class, each reading the ONE canonical graph (ADR-1) through its own scoped, anon-safe read-model. Neither hub supersedes the other. No hub owns canonical state — projection, not duplication.**

- **empire-state-hub** continues reading the Empire prod DB (`oicikjyzmxqfomrrqkvf`, now the best-of-both graph) via its existing REST read path; gains new read surfaces (topic-intelligence) as they land.
- **gtm-os-hub** keeps University (`/university`), `/signal`, `/cockpit`, its mission/style, and the Orchid identity. Its `/signal` is wired to the canonical `signal_read` read-model (built as an ADR-1 deliverable) — the first time it lights up, and it lights up against the shared graph.
- **The learning plane (`nnywrmetdoixdbevvsvf`) stays an independent GTM-owned project** — not merged, not shared-ified. (Its `learning` schema is correctly PII-isolated; only `v_public_*` exposed.)
- **Read discipline:** anon key + `signal_read` views for public reads; service-role only server-side (cockpit/ops), never on a public path; suppression-gated views stay gated.

## Uniqueness Preservation Check (surface layer)

The design passes iff it requires gtm-os-hub to give up **none** of {mission, style, University, `/signal`, Orchid}. This ADR gives up none: gtm-os-hub keeps all five and *gains* a live `/signal`. Recorded here as a testable acceptance criterion, re-checked at the DoD gate and in verification.

## Options considered

- **A. Two hubs, coexistence (CHOSEN).** Shared data, distinct surfaces.
- **B. One hub (empire-state-hub canonical).** Rejected — violates the binding constraint; deletes non-duplicated value (University, `/signal`, Orchid).
- **C. Two hubs + shared component library.** Not competing — that's the capability layer (ADR-3); adopted there.

## Consequences

- **Positive:** the constraint is satisfied structurally; both surfaces benefit from one enriched graph; `/signal` gets built right against the shared read-model rather than a soon-to-be-migrated spine.
- **Costs:** the Empire prod DB's project-wide `exposed-schemas` now couples both hubs' read-models (config-as-code + PostHog alarm; from ADR-0/1).
- **Open item → confirm before build:** the probe found a small events mirror (`events` 4, `event_briefs` 6) in the learning-plane `public` schema that **no gtm-os-hub code references** — untracked. Confirm whether it's an intended projection or leftover before finalizing the surface read contracts; do not build against it until sourced.

## Reversibility

High. Surfaces are separate apps coupled only by read contracts (views); a hub can change or roll back its read path independently without touching canonical state.
