# OpenAI seat — model bake-off, PRE-REGISTERED (YED-209 build step 10)

Written **before any arm was run**, so the winner is chosen by a rule rather than by whichever number looked
best afterwards. Alex approved a pre-registered bake-off on 2026-09-19 (spec §4 / decision log fork 2).

## Arms
| arm | model | $/1M in | $/1M out |
|---|---|---|---|
| A | `gpt-5.4-mini` | 0.75 | 4.50 |
| B | `gpt-5.4` (the provisional default) | 2.50 | 15.00 |
| C | `gpt-5.5` | 5.00 | 30.00 |

Identical evidence per item (one bundle each), `reasoning.effort: medium`, harness-computed verdict.

## Test set
The clean control set (`manifest.json`): **6 negative** (real pre-fix states Alex labelled flag) and **10
positive** (states he acked pass). Seven blobs that came back labelled both ways were excluded before any arm
ran; the reason is recorded in the manifest, not hidden.

**Stage 1 (pilot, ~$2.70):** 3 negative + 3 positive, to prove the harness and show whether the arms separate
at all. **Stage 2:** the remaining 10 items, run only if stage 1 leaves two or more arms alive.

## The rule (fixed now)
1. **Disqualify** an arm with a false-flag rate > 1/6 on positives (an over-flagger causes escalation fatigue,
   which kills the gate more surely than a lenient seat).
2. **Disqualify** an arm with a flat-1.0 rate ≥ 0.20 on the items it passes (the Gemini failure mode).
3. Among survivors, **highest defect recall** on the negatives wins.
4. **Tie → the cheaper model wins.** A tie is a difference of fewer than 1 item.
5. If **no arm** clears 1 and 2, no seat is promoted out of shadow and the result is reported as a negative
   finding. "Add a third seat" is not a goal worth reaching by lowering the bar.

## Recorded regardless of outcome
Per arm: recall, false-flag rate, flat-1.0 rate, mean cost/run, mean defects/item, and the per-item verdicts.
Every call lands in `spend-ledger.jsonl`, every verdict in a run-log with `calibration_set: "control"`, so none
of this pollutes the prospective calibration that governs promotion.

## What this does NOT establish
Control performance is not the voting bar. It qualifies a model to be the OpenAI seat; the seat still enters at
**shadow** and still needs ≥25 prospective runs with ≥8 real flags, κ ≥ 0.60 and recall ≥ 0.70 against Alex's
own labels before it can vote. A model that aces a fixed 16-item set it may effectively see again is exactly the
kind of number this project has already been fooled by once.
