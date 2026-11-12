# Proposal: AI intelligence graph v2 — layered, derived knowledge with layer-specific accuracy

*Status: draft plan (pre-ADR-15). 2026-11-12. Issue: YED-384. Inputs: Alex's direction 11-11/11-12, the v1 prose pilot, and a frontier check of 2025–26 work (sources in §8).*

## 1. Problem

v1 prose extraction reached 0.98 precision by copying: every content word of a claim had to appear in the source paragraph. The result is accurate fragments ("X is CTO of Y") that hold almost no analytical value. Nothing in the gate measured usefulness, so it optimised the one thing it measured.

Most of the graph's value lies **above** the facts: paraphrased assertions, relations, trends and synthesis. Accuracy is a property of a statement measured against its evidence. It can be checked after paraphrase and after inference, provided every derived item records what it was derived from.

## 2. Principles

1. **Every derived item knows its parents.** A derivation record (W3C PROV-O style) on every L2–L4 row stores the parents, the method, the model ID, the prompt hash, the checker version and the run ID.
2. **Each layer has its own definition of correct, and its own metric.** Faithfulness for assertions, support for relations, statistical validity for trends, cited premises and calibration for synthesis.
3. **Rate the source separately from the claim.** Source reliability (A–F) and information credibility (1–6) are graded independently (Admiralty/NATO practice). Faithfulness only says that a claim matches its source.
4. **Only independent sources corroborate.** Syndicated copies, rewrites of one press release, or one brief quoting another count as **one** source.
5. **Time is first-class.** Every assertion and relation is bitemporal: when it was true, and when we learned it (the Zep/Graphiti pattern). Superseded facts are invalidated, never overwritten.
6. **Visibility travels with the claim.** Each row is public, private or off-the-record. Derived rows inherit the most restrictive visibility among their parents, and L5 products only show what their audience may see. This extends the ADR-9 PII boundary from fields to claims.
7. **Never judge your own output.** The primary faithfulness checker comes from a different model family from the extractor. An LLM judge is a second opinion. Every judge is validated against Alex's labels.
8. **Every metric has a null baseline** (the house rule).

## 3. The layers

| Layer | Holds | Correct means | Checked by |
|---|---|---|---|
| **L0 Sources** | Originals: Drive vault, briefs, transcripts, web pages, email-derived docs | Immutable; reliability grade A–F per source | sha256; source-reliability rating per source/domain, reviewed quarterly |
| **L1 Assertions** | Paraphrased, typed, self-contained claims (launch, funding, metric, adoption, partnership, hire, thesis), each with its evidence span | **Claimify triplet**: entailment (the span supports the claim), element-level coverage, decontextualization (stands alone). Numbers, dates and names exactly match the source. Extraction is skipped when ambiguity can't be resolved. | Cross-family checker (candidate: Bespoke-MiniCheck-7B, local) plus an LLM second opinion; numeric-fidelity check; credibility grade 1–6 |
| **L1 entity attributes** | Titles, roles, descriptions, speaker slots | Matches source; bitemporal | Routed here from extraction instead of becoming claims |
| **Entity resolution** | One node per real company, person or topic | Merge precision first | An explicit LLM clustering step before L2 (KGGen pattern); B-cubed and pairwise precision/recall; every merge is human-approved and reversible |
| **L2 Relations** | Edges: competes, partners, uses, invests, hires-for, ships | Backed by ≥1 faithful L1 claim; strength = **independent** corroborations | Edge precision; independent-source count |
| **L3 Derived analytics** | Trends, velocity, anomalies, clusters | **Statistically valid and about the market, not the calendar** | Theme **share** of all claims, or a Poisson/negative-binomial model with a source-volume offset; block or circular-shift permutation (or Kleinberg burst detection); Benjamini–Hochberg FDR, or Benjamini–Yekutieli where themes are correlated; effect size; per-source-type reporting; backtest against the null "every rising theme keeps rising" |
| **L4 Synthesis** | Analyses, hypotheses, dated falsifiable predictions | Every premise cited; conclusion follows; contradicting evidence weighed (ACH); later, calibrated | Citation precision/recall (ALCE); counter-argument pass; **generated on demand** from L1–L3 rather than precomputed (LazyGraphRAG); Brier **skill score** against a base-rate forecaster, pooled by confidence bucket |
| **L5 Products** | Briefs, Monday Market Brief, posts | Inherits the checks above; respects visibility | Existing output-evaluator source check |

## 4. Lifecycle rules

- **Contradictions.** Conflicting L1 claims are never silently resolved. Each gets a rank (preferred, normal, deprecated) or a `disputed` status (Wikidata pattern). The adjudicator ranks them, and only unresolvable conflicts reach Alex. L4 applies Analysis of Competing Hypotheses wherever disputed claims are premises.
- **Retraction cascade.** When an L1 claim is invalidated, retracted or deprecated, every L2–L4 descendant found through the derivation table is flagged `needs_review`, with a reason. Products that cited it are listed.
- **Supersession.** A newer fact closes the older fact's validity window (`valid_to`, `invalidated_by`); history stays queryable.
- **Method versioning.** Each metric is reported per extractor, prompt and checker version, so a shift can be attributed to the method or to the data.

## 5. Evaluation contract

| Measure | Use | Gate / target |
|---|---|---|
| L1 faithfulness (precision) | Primary quality gate | Batches of **n≈100**; accept if the Wilson 95% lower bound is ≥0.90. Computed on human labels, or on judge labels corrected with prediction-powered inference (PPI); **never raw judge rates**. At n=50 one error fails (49/50 → lower bound 0.895). |
| L1 coverage + decontextualization | Recall-side quality | Claimify definitions; reported, target set after the pilot |
| F-beta (β=0.5) | One-number summary | Weights precision over recall |
| Usefulness (0–2) | Value | Blind labels; **baseline = v1 extractive output on the same items**; v2 must clearly beat it |
| Numeric fidelity | Statistics, dates, names | 100%, exact match |
| Judge validity | Every automated judge | Cohen's κ against Alex's labels; re-labelled periodically (criteria drift, Shankar et al.) |
| Entity resolution | Graph integrity | Merge precision first; B-cubed |
| Edge strength | L2 | Independent-source count, never raw mentions |
| Trend validity | L3 | FDR-controlled, volume-normalised, backtested against the null |
| Citation precision/recall | L4 | ALCE definitions |
| Calibration | L4 predictions | Brier skill score against a base-rate forecaster; reported only once enough predictions have resolved |
| Use | Whole system | `claim_usage`: which layers and types get pulled into products |

**Kept out:** accuracy (no meaningful true negatives), ROUGE/BLEU (they penalise good paraphrase), plain F1, and any judge score not validated against human labels.

## 6. Build sequence

1. **Judge pilot (decides principle 7 empirically).** Run the v2 extraction prompt on about 100 claims from the pilot briefs. The Claude judge and MiniCheck label them; Alex labels them blind (45–60 min). Report κ per judge and the Wilson lower bound. This also seeds the gold set.
2. **ADR-15** from this plan plus the pilot results; **Fable adversarial review**.
3. **Migration 0023** (twin-rehearsed):
   - `layer` and visibility on claims
   - bitemporal columns (`valid_from`, `valid_to`, `recorded_at`, `invalidated_by`)
   - claim `status` gains `disputed`/`deprecated` ranks
   - `claim_derivation` (child, parents, method, model, prompt hash, checker version, run)
   - source reliability on documents/sources
   - an `independent_source_group` key for corroboration
4. **Extractor v2 (L1)** in the Claimify style, with entity-attribute routing, the cross-family checker, the numeric-fidelity check and visibility inheritance. Head-to-head against v1 on usefulness and faithfulness, then stage the winner.
5. **Entity-resolution clustering step**, then **L2 relations** with independent corroboration.
6. **L3 trend engine** (normalised, time-respecting permutation, FDR, backtest), feeding the Monday Market Brief.
7. **L4 synthesis agent** (on demand, cited, ACH, dated predictions), plus the retraction cascade and calibration reporting.
8. **Evaluation per batch**, with the numbers published on the hub's In Flight page.

## 7. Decisions (Alex, 2026-11-12)

- **Pilot first, then the ADR.** Approved. The ADR-15 draft waits for the pilot's κ and Wilson numbers.
- **MiniCheck runs locally on the Mac mini** as one of the pilot's judges (open model, no API cost). Taken as approved with the pilot; it stays in only if its κ earns the seat.
- **The v1 prose batch stays approved.** Alex approved the 932 v1 prose claims that passed both gates (95.5% faithful on a 200-row pooled sample). Claims are approved on traceability, not truth; truth is checked at use (YED-410). The v2 head-to-head still runs, and if v2 wins, its claims are staged alongside v1 and v1 rows it supersedes are marked `deprecated`, not deleted.
- **The fact-check design (YED-410) merges into ADR-15.** Both drafts claimed migration 0023 and ADR-15; there is one of each.

## 8. Sources

Frontier check 2026-11-12 (research-analyst):
- Bitemporal agent-memory graphs: Zep/Graphiti, arXiv 2501.13956 (2025)
- Self-preference bias: Panickssery et al., NeurIPS 2024; arXiv 2508.06709; arXiv 2502.01534
- Claim checkers: MiniCheck (Tang et al., EMNLP 2024), LLM-AggreFact, FactCG (NAACL 2025)
- Small-n evaluation: Bowyer et al., ICML 2025; arXiv 2511.21140; prediction-powered inference (Angelopoulos et al., *Science* 2023)
- Claim extraction: Claimify (Metropolitansky & Larson, ACL 2025)
- Entity resolution: KGGen (NeurIPS 2025)
- On-demand synthesis and retrieval: LazyGraphRAG (MSR); HippoRAG 2 (ICML 2025)
- Forecasting: ForecastBench (FRI, 2025)
- Trend detection: BERTrend; Kleinberg burst detection
- Foundations:
  - provenance and claim models: W3C PROV-O (2013); Nanopublications (Groth et al., 2010); Wikidata ranks
  - knowledge-base construction: Knowledge Vault (Dong et al., KDD 2014); DeepDive (Zhang, Ré et al., CACM 2017); GraphRAG (Edge et al., 2024)
  - factual consistency and verification: SummaC; TRUE; AlignScore; FEVER; FActScore; RAGAS (EACL 2024); ALCE (EMNLP 2023)
  - LLM-judge evaluation: Zheng et al. (2023); Shankar et al. (UIST 2024)
  - intelligence tradecraft: ICD 203 (2015); Heuer (1999); Kent (1964); Admiralty/NATO source grading
  - statistics and forecasting: Brier (1950); Tetlock; Benjamini–Hochberg (1995); Benjamini–Yekutieli; B-cubed (Bagga & Baldwin, 1998)
