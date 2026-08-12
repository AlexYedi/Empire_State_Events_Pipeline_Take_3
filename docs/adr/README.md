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

Supporting evidence (probe findings, pre-mortems — historical provenance, not live guardrails) is in [`evidence/`](evidence/).

## Related
- **The method, reusable:** [`../migration-playbook.md`](../migration-playbook.md) — the transferable "how to change a live system safely" pattern distilled from this work.
- **The narrative:** the seven-epic build story (shareable Artifact) — the human-readable *why*, start to finish.
- **The running log:** Linear YED-130 (milestones) · YED-131 (live-recompute follow-up).
- **The model reference:** [`../../.claude/references/market-intel-spine.md`](../../.claude/references/market-intel-spine.md) — how the graph works *now* (vs. these records, which explain *why* it's shaped that way).
