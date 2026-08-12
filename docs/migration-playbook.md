# Migration Playbook — changing a live system safely

Distilled from the MI data-spine consolidation (Linear YED-130, 2026-08). Use it for any **hard-to-reverse change to a live schema or dataset with active readers** — a schema change, a data backfill, an ingestion re-wire, a cutover. It is *not* ceremony for a trivial change; it's the discipline for the ones that can fail **silently** (the query returns a number, and the number is wrong).

Project-scoped on purpose. Promote to the canonical/user-scope layer only after a *second* migration proves the pattern recurs (the YED-29/30 "project-first, then promote" gate) — not before.

## The seven moves

1. **Measure before you cut.** Run a read-only probe of ground truth *first*, and let it overturn the plan. In YED-130 the probe flipped the whole strategy (see move 3). Assumptions about a live system are hypotheses until measured.

2. **Split the decision.** Don't let one question do triple duty — that's how the same debate reverses three times in a day. One decision → one ADR, decided on its own merits. (`docs/adr/`.)

3. **Carry judgment, regenerate math.** Sort what you're migrating into *non-reproducible work product* (curated/LLM/human output → **migrate** it) vs. *deterministic derivations* (→ **recompute** them on the new substrate). Getting this split wrong in either direction is the expensive mistake.

4. **Link, don't duplicate.** Merge two datasets with a **deterministic crosswalk** on a shared key (an id both sides already store), not fuzzy matching. Soft-merge only: write a **reversible merge-map first**, tombstone rather than delete, and **never fuzzy-match people** (a wrong identity merge is silent and irreversible). Every link should be an auditable row with a method + confidence, not a probability.

5. **Build beside, don't mutate — expand-contract.** Assemble the new graph in a **parallel schema** while the live one stays read-only; cut over with an **atomic swap** (a rename in one transaction); **park the originals, don't drop them**. Then rollback is the same move in reverse — which removes the need for paid point-in-time restore. Constraint names are per-schema, so park originals in a *separate schema* to avoid collisions (e.g. `company_pkey`).

6. **Prove the rollback before you touch prod.** Rehearse the full sequence on a **fresh clone**, including a rollback proven to exact row counts — that's the gate the plan hinges on. On prod, go **additive-first**: build the new schema beside the live one and validate it there (invisible to readers) *before* the swap — that's what surfaces bugs while they're still harmless. (In YED-130, additive-first on prod caught a dropped-events bug with zero impact.)

7. **Validate against invariants + an independent oracle, not the old data.** After a rewrite the old output is an *invalid* oracle. Instead: an **independent reference implementation** that recomputes a different way and must agree row-for-row, plus **structural invariants** (laws the data must always obey — no orphans, no double-counts, no cross-contamination). Then a **nightly, alert-on-fail watch** runs those until the safety net (the parked originals) is dropped.

## Standing guardrails (apply throughout)
- **No PII in logs or staging tables.** A `RAISE NOTICE` of a person row is a leak; a dump on disk is a leak.
- **RLS deny-all on every new schema**; grant the narrowest access the readers actually need; keep suppressed/counts-only projections behind non-exposed schemas.
- **Keep the rollback net until it's earned away.** Parked originals + the nightly watch stay until N clean nights; decommissioning the net is a *separate, dated* decision, cold-export first.
- **Time the swap window** so you can size any required write-freeze from evidence, not a guess.

## The one-line version
> Measure before you cut · carry judgment, regenerate math · build beside, don't mutate · **prove the rollback before you touch prod** · additive-first surfaces bugs while they're harmless.

See the ADRs (`docs/adr/`) for the specific decisions and the rehearsal runbook (`supabase/2B_REHEARSAL_RUNBOOK.md`) for a worked, timed example.
