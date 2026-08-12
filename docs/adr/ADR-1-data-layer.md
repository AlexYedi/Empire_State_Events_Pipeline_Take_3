# ADR-1 — Data layer: single canonical graph (carry-forward hybrid)

- **Status:** Accepted (2026-08-07); **revised 2026-08-07 post pre-mortem** (see `pre-mortem-data-layer.md`). Detail in the Data-Layer PRD.
- **Linear:** YED-130. **Depends on:** ADR-0, `phase-1-probe-inventory.md`, `pre-mortem-data-layer.md`. **MDM style:** Consolidation (data) + Coexistence (surface).
- **Decider:** Alex.

## Context

The Phase-1 probe found gtm-os's **entities** are a deterministic projection of Empire (390/396 join). The original ADR-1 concluded from this "migration = regenerate, not re-key." **A stress-test/pre-mortem overturned the load-bearing half of that:**

- The **intelligence layer is accreted, curated work product, not a reproducible projection.** The 170→30 topic clustering is an **LLM pass + full human review** (non-deterministic; its frozen artifact maps gtm-os's UUIDs, so it does not transfer to Empire's different 160 topics). `compute_topic_intelligence` **hard-depends** on `cluster_id` (no clusters → zero rows) and runs over gtm-os's `relations` graph, which Empire lacks — Empire's `event_entity` is a different shape the SQL must be **rewritten** against.
- **Empire's event graph is *thinner*, not richer** (17 events / 20 edges vs gtm-os's 59 / 629). "Regenerate on Empire's data" would produce a near-empty, mostly `insufficient_data` result. The true upstream for both is the **Notion events pipeline**; gtm-os captured it more completely.
- The **entity crosswalk de-risks entity re-keying**, but the intelligence layer is the thing of value and it is **not cheaply regenerable**.

## Decision

**One canonical graph on the Empire account, built by *carrying the accreted intelligence forward* (migrate the curated inputs; recompute only the deterministic math on top) — not by regenerating from Empire's thinner data. Sequenced as an additive Increment 1, then a gated destructive Increment 2.**

**Carry-forward split:**
- **Migrate (embodies judgment or richer data, non-regenerable):** the 30 curated themes (`topic_cluster`), cluster assignments (`topics.cluster_id`), the dedup merge decisions (with a persisted, reversible merge-map), and the richer event/relation graph (or re-ingest events from Notion, the true source).
- **Recompute (pure math, deterministic):** `topic_trend`, `topic_pair_metric` — via the ported/rewritten compute, once inputs are in place.

**Model shape:** keep Empire's relational base + `person.company_id` FK (do **not** adopt gtm-os's `company_domain` flattening). Add the carried-forward intelligence as **new, scoped schemas** (`topic_intelligence`, `signal_read`).

**Canonical project:** evolve the existing Empire project (`oicikjyzmxqfomrrqkvf`) **for the additive Increment 1 only** (new schemas + views, zero `public` DML/DDL → genuinely reversible). The **destructive Increment 2** (dedup into `public`, topic-set reconciliation, decommission) re-opens the in-place-vs-fresh-project choice and is gated on a verified PITR/dump restore drill.

### Increment split (the core of the revision)
- **Increment 1 — additive, build-ready now:** on a branch, stand up `topic_intelligence` + `signal_read` schemas; **carry gtm-os's intelligence forward (copy) into `topic_intelligence`**; build anon-safe `signal_read` views; wire **both** hubs to one view. No `public` changes, no re-dedup, no re-clustering, no spine decommission. Because this is a **copy**, "exact-match vs the frozen spine" is the correct, buildable fidelity test.
- **Increment 2 — destructive, separately gated:** reconcile the 170-vs-160 topic set (YED-116), re-key/merge entities into `public`, re-ingest the richer event graph, **recompute** on the Empire prod DB, validate vs the Python reference (divergence from gtm-os is *expected*), then decommission the spine. Gated on: merge-map, N-night validation, PITR restore drill, small-cell + view-security re-audit on merged data.

## Security model correction (was wrong in v1)

Empire's pipeline authenticates as **`service_role` via the `sb_secret` key, which BYPASSES RLS entirely.** So "the write role can't touch the intelligence schema except via compute" is **not enforceable with RLS.** Enforce with **roles + grants + `SECURITY DEFINER`**: a scoped `pipeline_writer` role with grants only on the `public` tables it writes; `REVOKE ALL` on `topic_intelligence`/`signal_read`; intelligence writes only through definer functions (`EXECUTE`, never direct DML). Exposed views must be **`security_invoker = on`** (or owner-privilege views leak `public.person` PII to anon). *RLS is not a control against `service_role`.*

## Options considered (unchanged conclusion, corrected rationale)
- **A. Single graph, carry-forward hybrid (CHOSEN).** Preserves gtm-os's curated value; entity projection still lets Empire be the relational base.
- **B. Formalize the two-tier split.** Rejected — keeps two cross-account databases forever.
- **C. gtm-os polymorphic model wholesale.** Rejected — lossy FK flattening.
- **D. Regenerate on Empire (v1's implicit approach).** **Rejected by the pre-mortem** — Empire's inputs are thinner + the clustering isn't reproducible; would replace real value with a worse artifact.

## Consequences
- **Positive:** curated themes/clusters + richer event graph preserved; the risky ops (dedup, re-clustering, decommission) are isolated in a gated Increment 2; Increment 1 is a safe additive slice that still lights up `/signal` with real data.
- **Costs:** carry-forward is a migration with re-keying (map gtm-os topic/entity UUIDs onto canonical IDs; reconcile 170-vs-160 topics = YED-116) — more work than "re-run a function," but it preserves value and the entity crosswalk is deterministic. New project-wide `exposed-schemas` coupling of both hubs' reads (config-as-code + alarm + advisor gate).
- **Follow-ups → Data-Layer PRD:** the 11 pre-mortem edits (4 non-negotiable: additive re-scope, split AC1, grants+SECURITY DEFINER, view-security). Fix the phantom-project note in `market-intel-spine.md` (done). Backlog: Empire `company.linkedin_url` 0/182 + email gaps.

## Reversibility
- **Increment 1:** high — rollback = drop the new schemas + revert `exposed-schemas`; `public` untouched by construction.
- **Increment 2:** low — destructive `public` changes need a verified PITR/dump restore drill, not a "repoint"; a fresh canonical project on the A.Yedi account is reconsidered here as it makes the old project *be* the rollback.
