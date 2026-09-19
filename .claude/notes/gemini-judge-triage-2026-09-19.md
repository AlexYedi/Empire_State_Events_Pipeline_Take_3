# The Gemini seat was rubber-stamping — triage + fixes (2026-09-19, YED-206)

**Trigger.** On PR #81 (`substrate.py`) the Gemini seat returned **1.0 on all five criteria, twice** — once without the
spec (it printed its own evidence-parity warning), once with ADR-10 + the review + `spine_client.py`. The Sonnet seat
scored **0.87** and named five verifiable defects. Alex: *"something is seriously wrong with that judge."* Triage run by
a Fable agent (read-only on the repo, 4 Gemini calls, `--print-only` so no calibration rows were written); the base-rate
and smoking-gun findings were re-verified independently in-session before acting.

## What was wrong

**The seat detects blatant faults but rubber-stamps competent-looking work**, and the quorum hid it.

| Cause | Role | Confidence |
|---|---|---|
| **(C) Model behaviour** — halo/anchoring on how polished the artifact looks | primary | ~75% |
| **(E) Quorum compares only `pass`/`flag`** — 1.0 and 0.87 counted as "agree"; a seat that always passes always agrees | why nobody noticed (14 of 16 historical quorums auto-accepted on a Gemini 1.0) | ~95% (structural) |
| **(D) Rubric scale** — `@4` defined 1.0 as "matches the pass anchor", one pass + one fail anchor, no mid band | made a flat 1.0 *rubric-legal* | ~70% |
| **(B) Prompt** — template pre-filled `"verdict":"pass"`; "judge conservatively" on house criteria; no defect-enumeration step | contributor; a **system-prompt-only fix was tested and ignored by the model** | ~55% |
| **(A) Plumbing** — parse/coercion/truncation | **ruled out**: full rubric + spec reach the model (32k prompt tokens), parse failure exits 1, the only score mutation is the downward dangling cap | ~95% ruled out |

**The smoking gun.** On the *same* artifact, prompt and spec, Gemini praised `ensure_event`'s `kind='attended'` default
as "avoiding an anti-pattern". In the planted-defect run — primed by obvious faults — it cited that identical line as
violating **ADR-10 decision 9** ("attendance is never inferred"). Same model, same line, opposite reading.

**The base rate** (re-counted in-session, 41 Gemini rows, model unchanged since 07-17): **20 of 23 real prospective
runs scored a flat 1.0**, including four artifacts Alex later confirmed defective. Prospective defect recall: **1 of 5**.

**The calibration claim collapses.** The "83% Gemini-vs-Alex" that supported *provisional-trusted* equals the
**always-pass baseline** on that set (Alex flagged 3 of 18 → 15/18 = 83.3%). Measured properly: **κ = 0.27, flag
recall = 0.20, flat-1.0 rate = 0.82** (`.claude/evals/calibration_stats.py`).

## Fixes shipped (all four)

1. **Quorum escalates on more than verdict mismatch** (`.claude/hooks/quorum-merge.sh`). Escalation reasons:
   `verdict_mismatch` · `score_divergence` (|Δ| ≥ `QUORUM_DIVERGENCE`, default 0.15) · `flat_ceiling:<seat>` (all five
   criteria 1.0 = low-information) · `gemini_no_evidence_parity`. Interactive → escalate to Alex; autonomous → fail-safe
   FLAG. 5/5 offline scenario tests pass; **today's PR #81 case now escalates** (flat ceiling) instead of auto-accepting.
2. **Defects before scores, enforced by the response schema** (`.claude/hooks/gemini-judge.sh`). `responseSchema` +
   `propertyOrdering` require `checks_performed` → `defects[]` (location · criterion · severity · spec_ref ·
   description) → `criterion_scores` → `cap_flags`. The `"verdict":"pass"` prefill is gone, and **the harness — not the
   model — computes the composite and verdict** from criterion scores + caps. Failure diagnostics now print
   `finishReason` + usage and dump the full response (this immediately caught a `MAX_TOKENS` truncation: defect-first
   reasoning costs ~15k thinking tokens, so `maxOutputTokens` went 16k → 32k).
3. **`build-quality@5` + `judge-system-v2`**: 1.0 must be *earned* ("searched and can name what was checked"), a **0.85
   mid anchor** per criterion, **NEW spec-drift cap (correctness ≤ 0.70)** when behaviour contradicts a numbered spec
   decision, and don't-trust-the-docstring.
4. **Calibration restated** (`.claude/evals/calibration_stats.py` + `.claude/evals/README.md`): per-seat agreement vs
   its own always-pass baseline, Cohen's κ, flag recall, flat-1.0 rate. New standing: **Sonnet = trusted seat**
   (κ 0.80, recall 0.80); **Haiku borderline**; **Gemini ADVISORY** — kept in the quorum (it costs ~3¢ and catches
   defect types Sonnet misses) but it cannot auto-accept anything.

## Proof the fix works (same artifact, same spec, `--print-only`)

| Run | Artifact | Before | After |
|---|---|---|---|
| C | the exact judged `substrate.py` (`f82b02b^`) | 1.0 pass, 0 defects | **0.88 pass** — found the ADR-10 d9 contradiction (spec-drift cap → correctness 0.70) + a missing `asserted_at` fallback; 7 checks named |
| A | same + 3 planted defects (raw `urlopen` bypassing `spine_client`; email/phone on a person row; bare `except: pass`) | 0.25 flag | **0.64 flag** — all 3 found, plus d9 and a docstring overclaim |

**Bonus real defect, from the fixed seat:** `substrate.py`'s header claimed "Never `bio` … The guard backstops this",
but `spine_client.ALLOW` permits `bio` (it refuses only email/phone, including *inside* bio). The producer never sends
`bio` — the *docstring* overclaimed. Fixed in this branch.

## Follow-up finding, same day: the fixes CONTAIN the behaviour, they do not cure it

Judging the fixed `gemini-judge.sh` itself (spec = this note + `@5`), the Gemini seat returned **1.0 on all five
criteria with zero defects again** — under the defects-first schema, the earned-1.0 scale and harness-side scoring.
So the ordering is now clear and worth stating plainly: **(C) model behaviour is the cause, and (E) the quorum
containment is the fix.** `@5` + the schema moved it on one artifact (`substrate.py`: 1.0 → 0.88 with the d9
contradiction found) and not on another. What held in both cases is the harness: the run printed
`⚠️ FLAT CEILING … the quorum will escalate instead of auto-accepting` and the quorum escalated to Alex.

Caveat on this particular run: the artifact is the seat's *own* harness, so self-preference may be in play on top of
the halo effect. Either way the operating rule stands — **Gemini is advisory; a flat 1.0 never auto-accepts.**

## Still open
- `claim_relation` has no producer (in S1a scope, empty table) and `claim.quote` is never populated — tracked on YED-169.
- Haiku sits just under the κ/recall bars; it is not currently a quorum seat, so no action beyond the record.
- Model-side probes (`thinkingLevel: high`, a two-call adversary→scorer pattern) remain untried: Run D showed extra
  thinking alone did not move the score, so they are low expected value.
