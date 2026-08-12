# ADR-4 — Increment 2: link, recompute on the Empire prod DB, retire the spine (expand-contract)

- **Status:** Accepted (2026-08-07). **Linear:** YED-130 (+ YED-116 as Step 0). **Depends on:** ADR-1, `increment-2-premortem.md`.
- **Decider:** Alex — committed to the full 2a→2b.

## Context
Increment 1 shipped a *carried snapshot* of gtm-os's topic-intelligence onto Empire prod DB `oicikjyzmxqfomrrqkvf` (keyed to gtm UUIDs, beside `public`, both hubs render it live). Increment 2 makes it *truly canonical* — linked to Empire's own graph, computed on Empire's own data — and **retires the gtm spine** (the original "one source of truth" goal). The stress-test measured the feared-destructive parts as deterministic/low-risk and located the real work in the recompute substrate.

## Decisions
1. **Do the full 2a→2b**, split by risk:
   - **2a — Link (deterministic, low-risk, additive-shaped):** link the carried intelligence to `public` via the measured crosswalks (145 topics + 383 entities 1:1 by de-hyphenated `notion_page_id`); insert the 25 gtm-only topics; recover the 12 entity "false splits" by exact-normalized-name; backfill 2 Empire topic notion-ids; +1 net-new entity. Reviewed crosswalk tables, zero-orphan invariant. **No recompute, spine untouched.**
   - **2b — Recompute + decommission (substantial build):** re-ingest the IRL event graph (Notion → `public.event`/`event_entity`, role-vocab expansion), build the cluster dimension on `public.topic`, rewrite `compute_topic_intelligence` from `relations`→`event_entity`, recompute, validate, atomic-swap, retire the spine.
2. **EXPAND-CONTRACT, never in-place.** Build everything in a parallel schema `canonical_v2`; `public` is read-only during the build; cut over by **atomic swap** (rename / view-repoint that both hubs + the pipeline resolve). Rollback = swap back. **This removes the Supabase Pro/PITR requirement** — the swap-back is the rollback.
3. **Dedup = soft-merge + merge-map-first**, three-tier confidence gate (exact-id→auto, strong-name→auto+map, fuzzy→**human review, never auto**), tombstone not delete, hard-delete deferred past validation. Persons never fuzzy-merged (65% linkedin coverage).
4. **Validation = invariants + a fresh reference implementation** on the event_entity model. "Differs from the gtm snapshot, as expected" is NOT validation (the old oracle is invalid post-rewrite). Write the relations→event_entity co-occurrence/role **semantic mapping spec first**, reviewed.
5. **Safety rails:** pipeline **write-freeze** window + delta reconciliation during build+swap; **cold logical export of the spine** before any decommission; decommission is a separate dated approval gated on invariants-passing (not "N nights of diff"); RLS deny-all + **no PII in logs / staging tables**; re-clone the Phantom Test Case DB fresh before the real rehearsal.
6. **No statement runs on the Empire prod DB until the full sequence — including a PROVEN rollback — is green on a fresh Phantom Test Case DB** (the 7-item rehearsal gate in `increment-2-premortem.md`).

## Options rejected
- **In-place destructive on `public`** — no rollback without PITR; hybrid-state + live-hub risk. Hard NO-GO.
- **Fresh separate project** — worsens the live-pipeline delta + forces cross-project repointing under pressure. Rejected in favour of same-project parallel-schema.
- **Fuzzy entity/topic matching** — unnecessary (crosswalks are deterministic) and the person corruption path. Rejected.

## Consequences
- **Positive:** retires the cross-account spine (kills the duplicate) + makes the intelligence self-sufficient and fresh on Empire's data; rollback-safe without Pro; the deterministic 2a banks value with near-zero risk.
- **Costs:** 2b is a real build — an ingestion port (Notion IRL events → `public`) + a pervasive compute rewrite; the Empire prod DB will hold two `event` kinds (trend-radar + IRL). The silent-empty-recompute trap is the top risk → invariants + fresh reference impl + "re-ingest before recompute" ordering.
- **Reversibility:** high by construction (expand-contract swap-back), *provided* the Phantom Test Case DB rehearsal proves the swap-back before the Empire prod DB is touched.

## Sequence
YED-116 topic-set frozen (Step 0) → 2a link (build + verify) → 2b build `canonical_v2` (re-ingest → cluster dim → compute rewrite → recompute) → **full Phantom-Test-Case rehearsal + proven rollback** → atomic-swap canonical → N-night invariant validation → cold-export + decommission spine.
