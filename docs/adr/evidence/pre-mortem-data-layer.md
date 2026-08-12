# Pre-mortem — Data-Layer build plan (2026-08-07)

Bounded adversarial pass before build: a read-only verification probe (derivation chain + phantom project) + a cto-principal-architect pre-mortem on the Data-Layer PRD. Satisfies the DoD "one adversarial pass in writing." **Verdict: GO-WITH-REVISIONS** (Increment 1 exactly as originally specced was NO-GO).

## The load-bearing finding
"gtm-os is a projection → regenerate, don't migrate" is **half true; the false half is load-bearing.** gtm-os's intelligence layer is **accreted, curated work product**, not a reproducible projection:
- 170→30 clustering = **LLM + full human review** (non-deterministic; frozen artifact maps gtm-os UUIDs, doesn't transfer to Empire's 160 topics).
- `compute_topic_intelligence` **hard-depends on `cluster_id`** (no clusters → 0 rows) and computes over gtm-os's `relations` graph; Empire's `event_entity` is a different shape → SQL must be **rewritten**, not ported.
- **Empire's event graph is thinner** (17 events / 20 edges vs 59 / 629) → regenerating on Empire yields near-empty output. → **Carry the intelligence forward (migrate), don't regenerate.**

## Verification facts (read-only probe)
- Derivation chain = 4 stages (raw topics → LLM+human canonicalize → SQL compute → emit). Regeneration needs schema + SQL-rewrite + LLM/human re-clustering — a 3-part build, not a function copy.
- Empire confirmed to have **no** `topic_cluster`/`topic_trend`/`topic_pair_metric` (404), no `relations`, no `entities` dim, no `ingestion_run`.
- **Phantom project confirmed:** `ytfzzsxcxxbejnowmkmk` appears in exactly one Empire doc, no code/env; empire-state-hub reads only `oicikjyzmxqfomrrqkvf`. → **three** projects, not four.

## Ranked failure modes (severity S1 = corruption/PII/irreversible)
1. **[S1] AC1 tests output-equality across divergent inputs** → deadlocks or gets faked green, then spine decommissioned + curated work lost. Fix: split into **AC1a** (port fidelity, same-input exact-match vs *frozen* spine) + **AC1b** (production correctness vs Python ref + structural invariants; divergence from gtm-os expected).
2. **[S1] Dedup is on the critical path** and is the highest-corruption op (false merge = PII incident, irreversible without a merge-map). Fix: pull it out of Increment 1; make it explicit, human-reviewed, with a persisted reversible merge-map.
3. **[S1] `service_role` bypass** makes write-scoping a fiction + voids RLS on read views. Fix: scoped `pipeline_writer` role + grants + `SECURITY DEFINER` functions; *RLS is not a control against `service_role`.*
4. **[S1] PII view leaks** — owner-privilege views leak `public.person` to anon; counts-only views re-identify at small cells on the merged data. Fix: `security_invoker=on`, `get_advisors` gate (branch + post-merge), small-cell suppression k≥5 tested on merged distribution.
5. **[S2] `exposed-schemas` is project-wide** → lighting up `/signal` touches empire-state-hub's live surface. Fix: expose only anon-safe `security_invoker` views; advisor gate before go-live; low-traffic window.
6. **[S2] The 6 non-joining entities** get silently dropped on decommission. Fix: reconciliation AC (classify test/orphan/legit) + sign-off, blocks decommission.
7. **[S2] "In-place rollback" is real only for the additive slice.** Destructive merge on `public` is not "repoint"-reversible. Fix: Increment 1 additive-only (reversible); destructive Increment 2 gated on PITR/dump restore drill + fresh in-place-vs-new-project decision.
8. **[S2] YED-116 (160 vs 170 topic set) is a prerequisite, not parallel** — everything keys on it. Fix: Step 0.
9. **[S2] "EXACT" is brittle** vs floats/seeds/tie-breaks. Fix: define canonical determinism (fixed seeds, ORDER BY tie-breaks, rounding, ε).
10. **[S3] Nightly compute now on the live prod project.** Fix: off-peak, scoped schema, runtime alert.

## Required PRD edits (4 non-negotiable pre-build: #1 re-scope, #2 split AC1, #3 grants+definer, #4 view-security)
Re-scope Increment 1 to additive-only (pull dedup + clustering into gated Increment 2); split AC1a/AC1b; grants + SECURITY DEFINER not RLS; security_invoker + get_advisors + small-cell k≥5; freeze spine during validation; decommission gate (AC1a×1 + AC1b×N + 6-entity reconciliation + merge-map); YED-116 as Step 0; canonical-determinism definition; PITR drill for destructive; off-peak compute + alert.
