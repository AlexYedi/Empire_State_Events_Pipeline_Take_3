# ADR-0 — Consolidation reconciliation & operating frame

- **Status:** Accepted (2026-08-07)
- **Linear:** YED-130
- **Supersedes:** the same-day "lean onto empire-state" call; reconciles `mi-consolidation-investigation-brief.md` (Empire) and `mi-consolidation-gtm-os-handover.md` (GTM)
- **Deciders:** Alex (owner); reconciled from systems-analyst, cto-principal-architect, head-of-product
- **Scope of this ADR:** the *operating frame* only. The three layer-specific decisions are ADR-1/2/3 (data/surface/capability), gated on the Phase-1 probe.

## Context

Empire State (`Empire_State_Events_Pipeline_Take_3` + `empire-state-hub`) and GTM (`gtm-os` + `gtm-os-hub`) independently built Supabase "data spines" that converged on the same shape (entities + signals + lenses). The same enrichment work is now done twice and an insight captured in one project can't benefit the other — but the two products serve different missions, and gtm-os-hub carries a distinct identity a naive merge would flatten.

Two competing framings were authored the same day, from inside each project's own thread:
- **Empire brief:** "two spines, one winner" — pick a surviving spine, unify schema, re-key entities; treats `empire-state-hub` as *the* canonical surface.
- **GTM handover:** "three projects, two hubs, three layers" — the two-spine frame "misses two-thirds of the reality"; wants shared infrastructure with preserved distinct surfaces.

A neutral, parent-rooted investigation (this `GitHub/` folder) probed the ground truth and consulted three specialist agents. **The decision had been reversed three times in one day** — the systems-analyst diagnosed this as **Policy Resistance**: a single bundled question ("which spine wins") doing triple duty for three genuinely independent decisions, so each of Alex's builder-selves fights the whole bundle instead of the one layer it cares about.

### Ground truth (verified from the repos, read-only)

Three Supabase projects across **two different accounts** (a hard constraint — Empire's own rule: never cross accounts, never use the Supabase MCP across them):

| Ref | Account | What it is | Status |
|---|---|---|---|
| `oicikjyzmxqfomrrqkvf` | A.Yedi | Empire MI graph — `public`: `company`/`person`/`topic`/`event`/`event_entity`, relevance-scored | Real rows + 2 live consumers |
| `abkvgihlbwfloentugtd` | Same Old Expressions | gtm-os Signal spine — `signal`: polymorphic `entities`, identity resolution, provenance/lineage/suppression, topic-intelligence, `signal_read` views | More production-grade model |
| `nnywrmetdoixdbevvsvf` | Same Old Expressions | GTM_OS_HUB learning plane — `learning` + `public.v_public_*`; only project with real RLS policies | Orthogonal (University/time-tracking) |

The entity graph is modeled **twice, incompatibly** (Empire separate `company`/`person` tables vs gtm-os polymorphic `entities`). gtm-os has the better model; Empire has the data and the only live readers.

## Decision (the operating frame)

1. **Three-layer split.** Treat this as three independently-decided, separately-gated layers — **data / surface / capability** — not one "which spine wins" call. This is the structural fix for the Policy Resistance loop.
2. **Data → Consolidation; Surface → Coexistence** (MDM styles). One canonical source of truth at the data layer; the non-canonical spine survives as a *scoped schema*, not flattened. Two hubs remain separate apps at the surface layer.
3. **gtm-os-hub identity is a set of invariants:** {mission, style, GTM University, `/signal`, Orchid}. Any design that requires giving up one of these is rejected (enforced by the Uniqueness Preservation Check at the DoD gate).
4. **Data-layer leaning (to validate, not final): Empire *account* hosts canonical, GTM *model* wins.** "Which account" and "whose schema model" are separable; the Phase-1 probe tests this direction first and may overturn it.
5. **Cross-account = no permanent live link.** Foreign-data-wrapper / read-replica / live logical-replication are availability landmines across accounts. Honest end-states: physically consolidate into one account, or federate with one-directional *batch* sync — never a live link. FDW/logical-rep permitted only as migration mechanics inside cutover.
6. **This cycle stops at the Definition-of-Done gate** (reconcile → probe → ADRs → PRDs). Build/cutover/verify run afterward, branch-first, in the target repos.
7. **Sequencing:** the capability layer (spine-agnostic shared infra) proceeds first as an *isolated parallel track* that neither blocks nor is blocked by the data migration.

## Options considered

- **A. Two spines, one winner (Empire brief).** Rejected as the *frame* — it's the bundling that caused the reversals. Its correct kernel (one golden record at the data layer) is preserved as decision 2.
- **B. Three projects / three layers (GTM handover).** Adopted as the frame. Its correct kernel (preserve distinct surfaces) is decision 2/3.
- **C. Live cross-account federation (FDW/replica).** Rejected as a permanent architecture — different-accounts availability risk (decision 5).

## Consequences

- **Positive:** each builder-self's concern is named on its own layer, dropping defensiveness; the hardest decision (data) no longer blocks the shippable ones (capability first); gtm-os-hub's value is protected by an explicit gate, not hope.
- **Costs / new couplings:** physical consolidation introduces a project-wide `exposed-schemas` coupling between both hubs' `/signal` (must be config-as-code + alarmed); entity-ID re-keying across two graphs is the highest-risk step and gates everything downstream.
- **Follow-ups seeded:** ADR-1 (data), ADR-2 (surface), ADR-3 (capability); a standing cross-repo drift-review cadence + ADR log (the Shifting-the-Burden fix) so the next divergence doesn't need a fourth neutral thread; fix the stale `abkvgihlbwfloentugtd` provenance header in Empire's `market-intel-schema.sql`; explicit re-decision of YED-116 (shared taxonomy, previously cancelled) inside the data-layer PRD.

## Status of downstream gates

- **Phase 1 (probe)** — in progress. Gate: no high-impact unknown remains; time-boxed.
- **Phase 2 (ADR-1/2/3)** — blocked on probe.
- **Phase 3 (PRDs + DoD gate)** — blocked on ADRs; this cycle's stop line.
