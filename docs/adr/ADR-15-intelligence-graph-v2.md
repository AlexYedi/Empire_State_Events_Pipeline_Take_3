# ADR-15 — Intelligence graph v2: layered derived knowledge, document-scoped support, an audited judge, and freshness by class

**Status:** **Proposed 2026-11-13** (revision 2, after the Fable adversarial review; YED-384). It becomes Accepted once migration 0023 passes its twin rehearsal and Alex has applied it to prod.
**Governs:** what a claim is and when it counts as supported; how claims are extracted, judged and kept fresh; how relations, trends and insights are derived from them; what migration 0023 adds and what later migrations add; how each layer is measured.
**Inputs:**
- the plan `docs/adr/proposals/2026-11-12-intelligence-graph-v2.md` (§7 and §7b record Alex's decisions of 11-12 and 11-13)
- the judge pilot (`.claude/.state/judge-pilot-20261112/`, gitignored)
- the knowledge-graph research check (`.claude/.state/kg-research-20261113/report.md`)
- YED-410 (use-time fact-check), which this ADR absorbs
- the Fable adversarial review of revision 1 (findings B1–B3 and the should-fix items, all addressed below)

**Builds on:** ADR-9 (the PII boundary, extended here from fields to claims), ADR-10 (the knowledge substrate: claims point at events; one producer path; one retrieval path) and ADR-13 (the lens and slice layer). It reverses none of them. Migration 0022 must be applied before 0023.

> **Numbering:** `theme-sweeper` refers to ADR-14 (§2.2), which is not on `main`. Before this ADR merges, confirm that 15 is still free on `main` (see the README numbering note).

## Context

v1 prose extraction reached 0.98 precision by copying. Every content word of a claim had to appear in its source paragraph. The claims were accurate and nearly useless ("X is CTO of Y"), because the gate measured only one thing. Most of the graph's value sits above single facts: paraphrased assertions, relations, trends and synthesis. Each of these can be checked for accuracy as long as it records what it was derived from.

The judge pilot (11-12 to 11-13) answered three questions the plan had left open.

1. **What "supported" means.** In the first labelling round, Alex marked 99 of 100 v2 claims supported. The judges flagged 12. A document-level rerun showed that 11 of those 12 were supported by other paragraphs of the same brief: the harness had shown the judges one paragraph, while the extractor read the whole document. After a re-label under the strict, document-scoped standard, Alex marked all 100 supported.
2. **Which judge.** No judge could be chosen from a set with one or zero negatives. Two balanced planted-error sets were built instead: one written by Sonnet, one by fixed rules.
3. **Whether a second, cross-family checker adds anything.** It does not (decision 4).

## Decision

| # | Decision | Why |
|---|---|---|
| 1 | **Layers.** <br>• L0 sources: immutable, graded A–F for reliability per source. <br>• L1 assertions: paraphrased, typed, standalone claims with evidence spans. <br>• L1 entity attributes: titles and roles, routed off the claim path. <br>• Entity resolution: one node per real thing. Every merge is human-approved, logged and reversible. <br>• L2 relations: backed by at least one supported L1 claim; strength counts independent sources. <br>• L3 analytics: volume-normalised, FDR-controlled, backtested. <br>• L4 insights: generated on demand, with every premise cited. <br>• L5 products. <br>Each layer has its own definition of correct and its own metric (plan §3). | Accuracy is a property of a statement measured against its evidence. It can be measured after paraphrase and inference, layer by layer. |
| 2 | **"Supported" is strict and document-scoped.** Every part of a claim must be stated somewhere in its source document (the same brief or transcript), or in the event's own title and date. Several paragraphs may contribute. A claim is unsupported if it contains any of: <br>• a detail stated nowhere in the document <br>• a relationship the document never states <br>• a dropped hedge <br>• a changed tense <br>Leaving something out is not a fault. | This matches how the extractor reads and how Alex labels. The paragraph-scoped version produced 11 false "unsupported" verdicts out of 12. |
| 3 | **The extractor cites every evidence span.** <br>• Evidence is a list of `{para_idx, quote}`: one entry per paragraph used, together covering every element of the claim. The first entry is the main paragraph. <br>• Each quote is at most **25 words**, the licensing guard from 0009 now applied per span. <br>• Stored in `claim.evidence jsonb`. <br>• `claim.quote` and `locator.para_idx` keep the first span, so existing readers and full-text search still work. <br>• `claim_key` stays `sha256(normalized claim_text)`, so staging stays idempotent. <br>• A quote not found verbatim in its paragraph fails the claim mechanically, before any judge. <br>• The judge sees the claim, every cited paragraph and the event line. | All 4 of Claude's wrong flags on the real set came from a post-hoc span locator that missed a supporting paragraph (P006, P022, P034, P084). Whoever writes the claim knows which paragraphs it used. |
| 4 | **One judge, Claude, audited in two parts.** MiniCheck (7B and T5) is dropped. Plan principle 7 is amended (see the plan). <br><br>**(a) Competence floor, using planted errors.** <br>• Each audit plants about 150 rule-based errors, with at least 40 dropped hedges and 40 tense changes. <br>• The judge passes if the catch rate's Wilson 95% lower bound is at least 0.90 (143/150). <br>• A trip is confirmed on a second, fresh batch before the judge is benched. <br>• A false-alarm rate is computed on human-labelled supported claims; κ is not used. <br>• This audit cannot measure self-preference: by construction, most rule-planted errors are absent from the source text, so a string check catches them. It proves the judge is awake. <br><br>**(b) Self-preference and correlated error, using human labels.** <br>• Each month Alex blind-labels about 40 claims the judge passed, drawn from production. <br>• The sample oversamples multi-span, partnership, thesis and hedge-bearing claims, the claims where the extractor and judge most likely share a blind spot. <br>• The judge keeps its seat while the pooled 3-month false-pass rate has a Wilson 95% upper bound of at most 0.08. That needs about 120 labels with 2 or fewer false passes. <br>• These labels are also the PPI labels for decision 5, so they add little cost. <br><br>**When either part trips:** the judge is benched, and its claims stage as `needs_review` until a fix passes both parts on fresh data. <br>**When to re-audit:** monthly, and whenever the judge's model ID or prompt hash changes. | MiniCheck-7B caught 0 of Claude's 2 misses and raised wrong flags on correct claims from 4 to 7. Neither the rule-planted set nor MiniCheck tests the risk that matters: errors that Claude-the-extractor makes and Claude-the-judge tolerates, such as bridging inferences, adjacent facts asserted as a relationship, or attribution shifts. Only human labels on natural errors measure that (Panickssery et al., 2024). The pilot's measurement of judge recall on natural errors rests on n = 0, because all 100 real claims were supported. |
| 5 | **Gate on human labels, not judge rates.** <br>• A batch is about 100 staged claims from one extractor version. <br>• It is accepted when the PPI-corrected faithfulness estimate's 95% lower bound is at least 0.90. <br>• That estimate combines the judge's labels on the batch with at least 40 human labels drawn from it (the decision 4b sample). <br>• Where every claim is human-labelled, the Wilson lower bound is used instead. <br>• A raw judge rate is never the gate. <br>• Coverage (claims per document and per 1,000 words) is reported beside every gate, with v1 on the same documents as the baseline. | A judge with 97% agreement still has a bias that PPI can correct; a raw judge rate cannot be audited. A precision-only gate rewards emitting fewer, safer claims, which is the v1 failure (Goodhart). |
| 6 | **Provenance on every derived row.** `claim_derivation` records the child, its parents, the method, the model, the prompt hash, the checker version and the run (W3C PROV-O style). When an L1 claim is retracted or deprecated, every L2–L4 descendant is flagged `needs_review`, together with the products that cited it. This ships with L2 (build step 5), when the first derived rows exist. | The retraction cascade and method attribution both need the parent links. Building the table before any writer exists is YAGNI. |
| 7 | **Leave `claim.status` alone. Add a rank and a review flag.** <br>• `status` keeps its CHECK: `candidate`, `approved`, `rejected`. <br>• 0023 adds `claim.rank` (`preferred`, `normal` or `deprecated`; default `normal`). <br>• 0023 adds `claim.review_flag` (null, `needs_review` or `disputed`). <br>• One view, `public.claim_current`, exposes status, rank, flag and the latest verification outcome. <br>• **Prerequisite:** before any non-default rank or flag is written, `match_claims` (0010/0011) and `mi.fact` (0016) are changed to read through `claim_current`. Then disputed claims are surfaced with their flag, deprecated claims leave the counts, and claims last checked as `contradicted` are dropped or flagged. <br>• Validity windows: `valid_from` and `valid_to` on claims. When a newer fact supersedes an older one, a `claim_relation` supersedes edge closes the older claim's `valid_to`. There is no separate `recorded_at` (it duplicates `created_at`) and no `invalidated_by` (it duplicates the supersedes edge). | Adding values to the status CHECK would break two live readers silently. Disputed claims would vanish from retrieval, and deprecated ones would still count in hub theme numbers. |
| 8 | **Freshness by class, re-checked at use, logged append-only.** <br>• A claim stays valid until shown otherwise. <br>• `freshness_class` and its re-check interval: historical, never; fast-moving, 14–30 days; slow-moving, 90 days; opinion or prediction, scored as a forecast and never re-verified. `none_fits` is allowed. <br>• Each claim also stores `freshness_conf`, `freshness_reason` and `next_check_at`. <br>• **Retrieval only flags overdue claims.** The parent session runs the re-checks, at most 5 per product, after retrieval. This keeps web reads and spine writes out of the retrieval path (CLAUDE.md invariant 5; ADR-10 decision 4). <br>• The pre-brief batch covers only the claims the Monday brief cites. <br>• An `unverifiable` result backs off (next check at twice the interval). After 3 attempts the claim gets `review_flag = needs_review`. <br>• Every check appends a `claim_verification` row: confirmed, updated, contradicted or unverifiable, plus source, method and run. A check never edits the claim. "Last confirmed" comes from the log. <br>• **Absorbs YED-410:** the log is the verdict write-back; `claim_current` surfaces it to retrieval; the pre-brief batch is the Market Brief's verify step. <br>• **Classifier baseline:** a lookup on `claim_type` plus the extractor's `time_sensitive` flag. The classifier ships only if it beats the lookup on a labelled sample of about 50 claims. | Approve on traceability, check truth at use (Alex, 11-12). Re-checking everything on a timer wastes calls on facts nobody uses. Without backoff, the same unverifiable claims would take every query's 5 slots. |
| 9 | **Observability before tuning.** The Monday brief's graph-health section reports: <br>• the share of borderline (confidence < 0.7) and `none_fits` freshness classes <br>• the edge-case log <br>• the backlog of overdue and `needs_review` claims <br>• the latest result of both judge audits <br>Classes, thresholds and audit floors change only when observed data shows the need. | Alex, 11-13: add or change only on observed, value-adding evidence. |
| 10 | **Only independent sources corroborate.** `independent_source_group` collapses syndicated copies, rewrites of one press release, and briefs quoting each other into one source. Edge strength counts groups, never mentions. Source reliability (A–F) and claim credibility (1–6) are graded separately (Admiralty). Ships with L2 (build step 5). | Ten copies of one press release are one source. |
| 11 | **Visibility travels with the claim.** <br>• 0023 adds `claim.visibility` with the vocabulary `documents.visibility` already uses (`private`, `public_ok`). A claim defaults to its document's value. <br>• Derived rows take the most restrictive parent's value. <br>• **Prerequisite:** the visibility filter goes into `match_claims` and the L5 renderers before any non-default value matters. <br>• New free-text columns (`freshness_reason`, `claim_verification` notes) get the `no_contact_pii_v1` CHECK, RLS and the revokes from 0022 items 7–8. <br>• The `spine_client` allowlist edits get human review (CLAUDE.md invariant 1). | Extends ADR-9 from fields to claims. A tag that no reader filters protects nothing. |
| 12 | **Insights are records with premises.** `insight` and `insight_claim` hold L4 output. `insight_claim` has a role (supports, counter or context) and a rank. Insights are generated on demand from L1–L3 (LazyGraphRAG). Every premise is cited, and contrary evidence is weighed (ACH). Dated predictions are scored by Brier skill against a base-rate forecaster once enough have resolved. These tables ship with the L4 agent (build step 7). | Claims stay atomic and decontextualized. The "so what" lives in its own record, so it can be retracted without touching the facts. |
| 13 | **Retrieval is a router over a hybrid index.** <br>• Default: vector plus keyword search. <br>• Multi-hop, comparison and temporal questions: one-hop entity expansion. <br>• Corpus-wide questions: map-reduce over the theme hierarchy. <br>• A labelled web lane keeps graph and web citations separate and shows disagreements without resolving them. Web facts enter the graph only through the normal pipeline. <br>• No precomputed community summaries. | From the research check: hybrid retrieval beats either method alone; graphs win on multi-hop and temporal questions and lose on lookups; community summaries give the weakest value for money. |
| 14 | **Migration 0023 carries only what L1 and freshness need.** Additive only, rehearsed on the twin, applied by Alex (ADR-10 decision 5; `migration-playbook.md`). <br><br>**Columns on `claim`:** `evidence` (jsonb), `judge_verdict`, `judge_model`, `judge_prompt_hash`, `judged_at`, `rank`, `review_flag`, `valid_from`, `valid_to`, `freshness_class`, `freshness_conf`, `freshness_reason`, `next_check_at`, `visibility`. <br>**Tables:** `claim_verification`, and `judge_audit` (run date, part a or b, n, caught or false-pass count, bound, passed, judge model, prompt hash). <br>**Also `claim_label`** (claim, sample run, stratum, inclusion probability, label, labelled at): one row per human label. PPI and the 4b false-pass rate need per-claim labels, and because 4b oversamples, every estimate weights each label by 1 / inclusion probability. `judge_audit` keeps only the run totals. <br>**Surfacing (decision 4b):** a monthly mini-runner job draws the stratified sample read-only, publishes a private blind-labelling page (claim and its cited spans only; no judge verdict shown), and opens a Linear issue for Alex with the link and a due date. The parent session reads the labels back and writes `claim_label` rows through spine_client. <br>**View:** `claim_current`. <br><br>**Deferred to the migrations that ship their first writer:** <br>• `entity_merge`: entity resolution (step 5) <br>• `claim_derivation`, `independent_source_group` and source reliability: L2 (step 5) <br>• `insight` and `insight_claim`: L4 (step 7) <br>`layer` is dropped: L1 is the only layer stored on `claim`, and insights have their own table. <br><br>**Already in place, not rebuilt:** `claim.asserted_at`, `claim_relation`, `entity_alias` (0022), provenance tiers, `documents.supersedes_id`. | Nothing in v2 needs a destructive change. v1 rows stay and are ranked, never deleted. A table with no writer is unrehearsable surface area. |

### Judge pilot results (decision 4)

Every judge got span-scoped input: the claim, all its cited paragraphs and the event line.

| | Claude Fable | MiniCheck-7B | MiniCheck-T5 |
|---|---|---|---|
| Real claims (100; Alex: all supported): correct claims wrongly flagged | 4 | 5 | 8 |
| Planted by Sonnet (80 items; 36 errors): κ, caught | +0.92, 35/36 | +0.87, 31/36 | +0.74, 29/36 |
| Planted by rules (76 items; 38 errors): κ, caught | +0.97, 37/38 | +0.71 | +0.71 |
| Dropped hedges caught (both planted sets) | 10/11 | 2/11 | 2/11 |
| Errors Claude missed that MiniCheck caught | — | 0 of 2 | — |

**Null baselines:**
- An always-yes judge scores κ 0 on both planted sets.
- A number-presence string check catches 10/10 of the rule-planted swapped numbers with 0/38 false alarms. On those error classes the rule-planted set measures little beyond what a regex already does.
- The judgment-bearing class is the dropped hedge. Claude caught 7/8 on the rule-planted set, Wilson lower bound ≈ 0.53.

**What this does and does not show:** Claude is the strongest of the three, and MiniCheck adds nothing Claude lacks. The pilot does **not** measure Claude's recall on errors that occur naturally in production. Decision 4b exists to measure it.

## Evaluation contract

| Measure | Layer | Gate or target | Null baseline |
|---|---|---|---|
| Faithfulness (PPI-corrected lower bound) | L1 | ≥ 0.90 per batch (decision 5) | always-yes judge; v1 extractive output |
| Coverage (claims per document and per 1,000 words; Claimify element coverage on a labelled subset) | L1 | reported beside every faithfulness gate | v1 on the same documents |
| Judge competence (planted catch-rate lower bound; false alarms on human-labelled positives) | judge | ≥ 0.90; confirmed on a second batch | the mechanical checks (span-verbatim and number-presence) |
| Judge false-pass rate on production claims (human-labelled) | judge | pooled 3-month upper bound ≤ 0.08 | — (this is the human measurement) |
| Span validity, numeric fidelity | L1 | 100% (mechanical) | — |
| Usefulness (1–3, blind) | L1 | paired v2-minus-v1 difference on the **same documents**, 95% interval above 0 | v1 (current unpaired read: 32% vs 20% useful-3, not yet met) |
| Merge precision **and** B-cubed recall | entity resolution | precision first; recall reported | no merging (perfect precision, zero recall) |
| Independent-source count | L2 | reported per edge | raw mention count |
| Trend validity | L3 | FDR-controlled, volume-normalised | "every rising theme keeps rising" |
| Citation precision and recall (ALCE) | L4 | reported | — |
| Brier skill score | L4 predictions | > 0 once enough have resolved | base-rate forecaster |
| Temporal backtest | retrieval | graph+vector beats vector on temporal questions, judged in both orders | plain vector retrieval (runs **first**) |
| Freshness classifier accuracy | ops | beats the lookup on about 50 labelled claims | the `claim_type` + `time_sensitive` lookup |

Kept out: raw accuracy where there are no true negatives, ROUGE/BLEU, plain F1, and any judge score not validated against labels.

## Consequences

- **Cost:**
  - One Claude judge call per staged claim.
  - A monthly planted audit of about 300 items (the error set plus its originals).
  - About 40 blind labels a month from Alex, roughly 15–20 minutes. These double as the PPI labels.
  - The Mac mini MiniCheck runner is retired. Its scripts stay in the pilot folder.
- **Accepted risk:** same-family self-preference is measured monthly, not excluded by structure. If an audit trips, try these in order:
  1. Fix the judge prompt.
  2. Use a different Claude model as the judge.
  3. Move the extractor to a model outside the Claude family. This needs a new pilot.
- **Extractor work:**
  - The v3 prompt caps each span at 25 words.
  - `pilot.py check-v3` validates multi-span evidence.
  - The producer (`substrate.py stage-claims`) writes `evidence`, the judge fields and the first-span `quote`.
- **Reader work, before any non-default value is written:** `match_claims` and `mi.fact` move to `claim_current`, and gain the visibility filter.
- **Retrieval work:**
  - The router and the labelled web lane are new.
  - The temporal backtest against plain vector retrieval runs before either ships.
- **Ops:** the Monday brief gets a graph-health section and a pre-brief freshness batch limited to the claims it cites.

## Rejected alternatives

| Option | Why not |
|---|---|
| Keep principle 7 as written: MiniCheck-7B as the main judge, plus a rule-based hedge check | 7B catches 2/11 dropped hedges, the error class Alex's hedge rule exists for. It also adds a second gate to build and maintain. |
| Claude as the main judge, with MiniCheck as a free second opinion | Zero rescues and more false flags: review theater. |
| Treat the rule-planted audit as the self-preference test | A string check already catches most rule-planted errors. Such an audit proves competence, not independence (Fable review B1). |
| Add `disputed` and `deprecated` to the `claim.status` CHECK | That breaks `match_claims` and `mi.fact` silently (Fable review B3). |
| Ship every v2 table in 0023 | Six tables would have no writer until build steps 5–7. |
| Paragraph-scoped support | Under it, 11 of the 12 disputed verdicts were harness artifacts. |
| Re-checking at query time, inside retrieval | It puts web reads and spine writes in the retrieval path. |
| Timed re-verification of every claim | It spends calls on facts nobody uses. |
| Precomputed GraphRAG community summaries | The weakest value for money in the research check. |

## Revisit triggers (provisional thresholds)

- Either judge audit trips, confirmed on a second batch.
- The borderline share of freshness classes stays above 25% for two weeks running, or `none_fits` exceeds 10%.
- The temporal backtest shows no gain for graph+vector over plain vector retrieval. If so, reconsider the layers above L1 before building more.
- v2 fails the paired usefulness test against v1. If so, v1's extractive claims stay primary and v2 becomes the L4 premise layer only.
- The overdue backlog grows for four weeks running. The re-check budget is then too small for the claims in use.
