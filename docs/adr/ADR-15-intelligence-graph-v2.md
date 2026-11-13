# ADR-15 — Intelligence graph v2: layered derived knowledge, document-scoped support, an audited judge, and freshness by class

**Status:** **Proposed 2026-11-13** (draft for the Fable adversarial review; YED-384). It becomes Accepted once migration 0023 passes its twin rehearsal and Alex has applied it to prod.
**Governs:** what a claim is and when it counts as supported; how claims are extracted, judged, kept fresh and derived into relations, trends and insights; the tables migration 0023 adds; and how each layer is measured.
**Inputs:** the plan `docs/adr/proposals/2026-11-12-intelligence-graph-v2.md` (§7 and §7b record Alex's decisions of 11-12 and 11-13), the judge pilot (`.claude/.state/judge-pilot-20261112/`, gitignored), the knowledge-graph research check (`.claude/.state/kg-research-20261113/report.md`) and YED-410 (use-time fact-check), which this ADR absorbs.
**Builds on:** ADR-9 (PII boundary; extended here from fields to claims), ADR-10 (knowledge substrate: claims point at events, one producer path, one retrieval path) and ADR-13 (lens and slice layer). It reverses none of them.

> **Numbering:** ADR-14 is referenced by `theme-sweeper` (ADR-14 §2.2) but is not on `main`. Before this merges, confirm 15 is still free on `main` (README numbering note).

## Context

The v1 prose extractor reached 0.98 precision by copying: every content word of a claim had to appear in its source paragraph. The claims were accurate and nearly useless ("X is CTO of Y"), because the gate measured only one thing. Most of the graph's value lies above single facts, in paraphrased assertions, relations, trends and synthesis, and each of those can be checked for accuracy as long as it records what it was derived from.

The judge pilot (11-12 to 11-13) answered three questions the plan left open:

1. **What "supported" means.** Alex first marked 99 of 100 v2 claims supported while the judges flagged 12. A document-level rerun showed that 11 of the 12 were supported by *other paragraphs of the same brief*: the harness showed judges one paragraph while the extractor read the whole document. The standard was fine; the harness was wrong.
2. **Which judge.** No judge could be chosen from a set with one negative (every κ ≈ 0, against 99% raw agreement for an always-yes judge). Two balanced planted-error sets settled it: one written by Sonnet, one by fixed rules that no model authored.
3. **Whether a second, cross-family checker adds anything.** It does not (decision 4).

## Decision

| # | Decision | Why |
|---|---|---|
| 1 | **Layers.** L0 sources (immutable, reliability A–F per source); L1 assertions (paraphrased, typed, standalone claims with evidence spans); L1 entity attributes (titles and roles routed off the claim path); entity resolution (one node per real thing, merges logged and reversible); L2 relations (backed by ≥1 supported L1 claim; strength = independent sources); L3 analytics (volume-normalised, FDR-controlled, backtested); L4 insights (generated on demand, every premise cited); L5 products. Each layer has its own definition of correct and its own metric (plan §3). | Accuracy is a property of a statement against its evidence, so it can be measured after paraphrase and inference, layer by layer. |
| 2 | **Supported = strict and document-scoped.** Every part of a claim must be stated somewhere in its source document (the same brief or transcript) or in the event's own title and date. Several paragraphs may contribute. A detail stated nowhere in the document, a relationship the document never states, a dropped hedge or a changed tense is unsupported. Omission is not a fault. | Matches how the extractor reads and how Alex labels. The paragraph-scoped version produced 11 false "unsupported" verdicts out of 12. |
| 3 | **The extractor cites every evidence span.** Evidence is a list of `{para_idx, quote}`, one per paragraph used, together covering every element of the claim (`extract-v3-prompt.md`). The judge sees the claim, its cited spans and the event line. A quote that is not found verbatim in its paragraph fails the claim mechanically, before any judge. | All 4 of Claude's wrong flags on the real set came from a post-hoc span locator that missed a supporting paragraph (P006, P022, P034, P084). The writer of the claim is the one who knows which paragraphs it used. |
| 4 | **One judge: Claude, audited against errors no model wrote.** Plan principle 7 is amended from "never judge your own output" to this. MiniCheck (7B and T5) is dropped. **Audit:** each month a fresh batch of rule-planted errors (swapped number, wrong entity, dropped hedge, added detail, tense change) plus their unaltered originals is judged and scored against the planted gold. The judge keeps its seat while the catch rate's Wilson 95% lower bound is ≥ 0.80 and κ ≥ 0.80 (provisional floors from the pilot). Below either, the judge is benched: claims stage as `needs_review` until a fix passes the audit. | Results below. A second checker earns its seat only by catching what the first misses; MiniCheck-7B caught 0 of Claude's 2 misses and raised false flags on correct claims from 4 to 7. The rule-planted set *is* the self-preference test, and Claude scored highest on it. A recurring audit measures the risk instead of buying a weaker instrument to cover it. |
| 5 | **Gate on human labels, not judge rates.** L1 batches of n ≈ 100 are accepted when the Wilson 95% lower bound on faithfulness is ≥ 0.90, computed on Alex's labels or on judge labels corrected by prediction-powered inference (PPI). Raw judge rates are never the gate. | A judge with 97% agreement still has a bias PPI can correct; a raw judge rate cannot be audited. |
| 6 | **Provenance on every derived row.** `claim_derivation` records child, parents, method, model, prompt hash, checker version and run (W3C PROV-O style). A retracted, invalidated or deprecated L1 claim flags every L2–L4 descendant `needs_review`, with the products that cited it. | The retraction cascade and method attribution both need the parent links; nothing else can rebuild them later. |
| 7 | **Bitemporal claims; history is never overwritten.** `valid_from`, `valid_to`, `recorded_at` and `invalidated_by` on claims. A newer fact closes the older one's window. Contradictions are ranked (preferred / normal / deprecated) or marked `disputed`, never silently resolved. | Zep/Graphiti pattern; temporal questions are where graphs beat plain vector retrieval (research check). |
| 8 | **Freshness by class, re-checked lazily, logged append-only.** A claim stays valid until shown otherwise. A classifier assigns `freshness_class` (historical: never re-check; fast-moving: 14–30 days; slow-moving: 90 days; opinion/prediction: scored as a forecast, not re-verified) with `freshness_conf` and `freshness_reason`; `none_fits` is allowed. Overdue claims are re-checked when next used (≤ 5 per query) and in one batch before the Monday brief. Every check appends a `claim_verification` row (confirmed / updated / contradicted / unverifiable, source, method, run); a check never edits the claim. "Last confirmed" is derived from the log. **This absorbs YED-410**: the log is the verdict write-back it asked for, retrieval surfaces the latest outcome, and the Monday brief's pre-publish batch is its missing verify step. | Approve on traceability, check truth at use (Alex, 11-12). Re-checking everything on a timer wastes calls on facts nobody uses. |
| 9 | **Observability before tuning.** The Monday brief's graph-health section reports the share of borderline (confidence < 0.7) and `none_fits` freshness classifications, the edge-case log, and the latest judge-audit result. Classes, thresholds and audit floors change only when observed data shows the need. | Alex, 11-13: add or change only on observed, value-adding evidence. |
| 10 | **Independent corroboration only.** `independent_source_group` collapses syndicated copies, rewrites of one press release and briefs quoting each other into one source. Edge strength counts groups, never mentions. Source reliability (A–F) and claim credibility (1–6) are graded separately (Admiralty). | Ten copies of one press release are one source. |
| 11 | **Visibility travels with the claim.** Each row is public, private or off-the-record; derived rows inherit the most restrictive parent; L5 products show only what their audience may see. | Extends ADR-9 from fields to claims. |
| 12 | **Insights are records with premises.** `insight` and `insight_claim` (role supports / counter / context, rank) hold L4 output, generated on demand from L1–L3 (LazyGraphRAG), with the derivation fields and a preferred / normal / deprecated rank. Every premise is cited; contrary evidence is weighed (ACH). Dated predictions are scored by Brier skill against a base-rate forecaster once enough resolve. | Claims stay atomic and decontextualized; the "so what" lives in its own record, so it can be retracted without touching the facts. |
| 13 | **Retrieval is a router over a hybrid index.** Vector plus keyword search by default; one-hop entity expansion for multi-hop, comparison and temporal questions; map-reduce over the theme hierarchy for corpus-wide questions. A labelled web lane keeps graph and web citations separate and shows disagreements without resolving them; web facts enter the graph only through the normal pipeline. No precomputed community summaries. | Research check: hybrid beats either alone; graphs win on multi-hop and temporal questions and lose on lookups; community summaries are the weakest value for money. |
| 14 | **Migration 0023 is additive only**, twin-rehearsed, applied by Alex (ADR-10 decision 5, `migration-playbook.md`). It adds: `layer` and visibility on claims; the bitemporal columns; `disputed`/`deprecated` claim ranks; `claim_derivation`; source reliability on documents/sources; `independent_source_group`; `freshness_class`/`freshness_conf`/`freshness_reason`; `claim_verification`; `entity_merge` (deferred from 0022); `insight` and `insight_claim`. Already in place and not rebuilt: `claim.asserted_at`, `claim_relation`, `entity_alias` (0022), provenance tiers, `documents.supersedes_id`. | Nothing in v2 needs a destructive change; v1 rows stay and are ranked, not deleted. |

### Judge pilot results (decision 4)

Span-scoped input for every judge: the claim, all its cited paragraphs and the event line.

| | Claude Fable | MiniCheck-7B | MiniCheck-T5 |
|---|---|---|---|
| Real claims (100; Alex: all supported): correct claims wrongly flagged | 4 | 5 | 8 |
| Planted by Sonnet (80; 36 errors): κ, caught | +0.92, 35/36 | +0.87, 31/36 | +0.74, 29/36 |
| Planted by rules (76; 38 errors): κ, caught | **+0.97, 37/38** | +0.71 | +0.71 |
| Dropped hedges caught (both planted sets) | 10/11 | 2/11 | 2/11 |
| Errors Claude missed that MiniCheck caught | — | 0 of 2 | — |

**Null baseline:** an always-yes judge scores κ 0 on both planted sets; on the real set it would flag nothing, and its "accuracy" there is 100% because the set has no negatives, which is why κ is not reported on it. **Caveat:** "MiniCheck never rescues Claude" rests on 2 chances. The monthly audit keeps that measurement running.

## Evaluation contract

| Measure | Layer | Gate or target | Null baseline |
|---|---|---|---|
| Faithfulness (Wilson LB, PPI-corrected) | L1 | ≥ 0.90 per n ≈ 100 batch | always-yes judge; v1 extractive output |
| Judge audit (catch-rate LB, κ) | judge | ≥ 0.80 / ≥ 0.80 monthly | always-yes judge (κ 0) |
| Span validity | L1 | 100% of quotes found verbatim | — (mechanical) |
| Numeric fidelity | L1 | 100% exact | — (mechanical) |
| Usefulness (0–3, blind) | L1 | v2 beats v1 with non-overlapping intervals | v1 on the same items (currently 32% vs 20% useful-3, intervals overlap: **not yet met**) |
| Merge precision, B-cubed | entity resolution | precision first | no merging |
| Independent-source count | L2 | reported per edge | raw mention count |
| Trend validity | L3 | FDR-controlled, volume-normalised | "every rising theme keeps rising" |
| Citation precision/recall (ALCE) | L4 | reported | — |
| Brier skill score | L4 predictions | > 0 once enough resolve | base-rate forecaster |
| Temporal backtest | retrieval | graph+vector beats vector on temporal questions, judged in both orders | plain vector retrieval (runs **first**) |
| Freshness classifier | ops | borderline and `none_fits` shares reported weekly | — |

Kept out: raw accuracy where no true negatives exist, ROUGE/BLEU, plain F1, and any judge score not validated against labels.

## Consequences

- **Cost:** one Claude judge call per staged claim, plus a monthly audit of about 80 items. The Mac mini MiniCheck runner is not needed; its scripts stay in the pilot folder.
- **Risk accepted:** same-family self-preference is measured monthly rather than structurally excluded. If the audit trips, the fallback order is (a) a judge prompt fix, (b) a different Claude model as judge, (c) a non-Claude extractor (re-pilot required).
- **Extractor work:** v3 prompt with multi-span evidence; `pilot.py check()` must validate a list of spans instead of one `para_idx`.
- **Retrieval work:** the router and the labelled web lane are new; the temporal backtest against plain vector retrieval runs before either ships.
- **Ops:** the Monday brief gains a graph-health section and a pre-publish freshness batch.

## Rejected alternatives

| Option | Why not |
|---|---|
| Keep principle 7 as written (MiniCheck-7B primary + a rule-based hedge check) | 7B catches 2/11 dropped hedges, the error class Alex's hedge rule exists for; the extra gate adds build and maintenance with lower quality. |
| Claude primary + MiniCheck as a free second opinion | Zero rescues, +3 false flags on the real set: review theater. |
| Move the extractor off Claude so Claude can judge without self-preference | Needs a new extractor pilot; the audit answers the same risk at a fraction of the cost. Kept as fallback (c). |
| Paragraph-scoped support | 11 of 12 disputed verdicts were harness artifacts under it. |
| Time-based re-verification of every claim | Spends calls on facts nobody uses; lazy re-check at use plus a pre-brief batch covers what ships. |
| Precomputed GraphRAG community summaries | Weakest value for money in the research check; on-demand synthesis instead. |

## Revisit triggers (provisional thresholds)

- The judge audit trips either floor in any month.
- The borderline share of freshness classifications exceeds 25% for two consecutive weeks, or `none_fits` exceeds 10%.
- The temporal backtest shows no gain for graph+vector over plain vector retrieval: the graph layers above L1 are then reconsidered before more is built.
- v2 fails to beat v1 on usefulness in the head-to-head: v1's extractive claims stay primary and v2 becomes the L4 premise layer only.
