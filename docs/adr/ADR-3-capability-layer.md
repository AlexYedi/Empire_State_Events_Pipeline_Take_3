# ADR-3 — Capability layer: extract spine-agnostic shared infra

- **Status:** Accepted (2026-08-07). Detail deferred to the capability PRD (Track B).
- **Linear:** YED-130. **Depends on:** ADR-0. **Runs as:** isolated parallel track (Track B).
- **Decider:** Alex.

## Context

Both projects independently built the same "boring substrate" — a PII/egress safety contract, an adapter→gate→render read pattern, an honesty/no-fabricated-numbers taxonomy, a build-journal/"arc" format. gtm-os-hub already has concrete versions (`lib/public-safety.ts`: `assertPublicSafe()` + `Public*` allowlist + publish-gate + denylist scrubber + CI gate). Duplicating this per-project is undifferentiated waste; it is also spine-agnostic, so it can move before the data migration settles.

## Decision

**Extract the spine-agnostic shared infrastructure into the shared `alex` Claude Code plugin (already the working precedent for cross-repo sharing), as a separate track that neither blocks nor is blocked by the data migration.**

**Sharing test:** *does it encode a product's unique point of view?* → lens-specific, stays put. Undifferentiated plumbing → shared.

- **Shared (extract):** the PII/egress contract (default-deny, three layers), the adapter→gate→render pattern, the honesty taxonomy, the build-journal/arc format.
- **Lens-specific (stays):** Empire's live content/job lenses + relevance recompute; GTM's themes, `/signal` render, University, Orchid identity.
- **Explicitly OUT of this track (scope discipline, per CTO):** toolchain unification — bun vs pnpm, one-vs-two Vercel/PostHog footprints. Surface-tier concerns, kept per-repo, tracked separately. Folding them in endangers the data work.

## Constraints

- **Track isolation (CTO guardrail):** the extraction must not introduce a dependency that entangles the data cutover. Shared package versions are consumed by both hubs; the data migration must not need to wait on, or force, a capability release.
- **Coupling direction (Head-of-Product guardrail):** the shared core is a dependency both products *use*; it never gains authority to redefine a product's domain semantics.

## Options considered

- **A. Extract to the `alex` plugin (CHOSEN).** Uses the existing sharing mechanism; ships value early; de-risks the DoD gate by proving the shared substrate independently.
- **B. New shared package/repo.** More ceremony than warranted now; revisit if the plugin proves too coarse-grained.
- **C. Leave duplicated until after the data layer.** Rejected — that's the "false-dependency trap" the systems-analyst flagged; the substrate is spine-agnostic and gains nothing from waiting.

## Consequences

- **Positive:** early, low-risk value; a single reviewed egress/honesty contract instead of two drifting copies; DoD gate de-risked.
- **Costs:** a shared package introduces a version/ownership surface — own it centrally with the same PRD-first + DoD discipline.

## Reversibility

High. Extraction is additive to the plugin; a hub can pin or fork a shared component if a genuine divergence appears.
