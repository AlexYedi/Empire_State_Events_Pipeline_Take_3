# `.claude/evals/` — the shared eval home

The single home for LLM-as-judge quality evaluation in this pipeline. Established 2026-06-26 by the build-rigor layer (Linear YED-89 / PRD US-3); **coordinates with the `eval-harness` project** (Notion Project Ideas `348d3699…`), which owns the rubric/judge conventions and `rubric_version`. When eval-harness is built, its skill rubrics (pre-event-content, etc.) live here too. **One judge system, not two** (never-duplicate-state).

## Layout
- `rubrics/<name>.md` — rubric-as-code: criteria + weights + pass bands + ≥1 pass/fail example each, plus a machine-readable JSON block. Versioned as `<name>@N`; never mutate old versions (bump instead). **Current build rubric: `build-quality@5`** (`rubrics/build-quality-v5.md`, live 2026-09-19 — earned-1.0 scale + 0.85 mid anchor, `defects[]` required, NEW spec-drift cap correctness ≤0.70; YED-206). Previous: **`build-quality@4`** (`rubrics/build-quality-v4.md`, live 2026-08-21 — added the artifact-type-scoped **density cap** ≤0.65 for `deep_read` renders, mechanized by `hooks/density-check.sh`; YED-136). For every artifact type except `deep_read`, `@4` ≡ `@3`. `build-quality-v3.md` (`@3`, confidence-honesty cap), `build-quality-v2.md` (`@2`, dangling-ref + command-skeleton caps) and `build-quality.md` (`@1`) are retained for runs scored under them.
- `prompts/judge-system.md` — the shared judge system prompt, v1 (kept for runs scored under it).
- `prompts/judge-system-v2.md` — **current** (2026-09-19, YED-206): defects-before-scores, an earned 1.0, spec-before-impression, don't-trust-docstrings; the harness (not the judge) computes the composite.
- `calibration_stats.py` — per-seat agreement · always-pass baseline · Cohen's κ · flag recall · flat-1.0 rate.
- `logs/<YYYY-MM-DD>-<artifact>-<run-id>.jsonl` — **authoritative** append-only run-log (the source of truth). Notion is a *deferred projection*, not the store (same contract-first pattern as `build-session-contract.md`).

## Run-log record schema
```json
{ "run_id":"", "timestamp":"", "artifact":"", "artifact_type":"skill|command|hook|ref|code",
  "rubric":"build-quality@1", "judge_model":"", "session_id":"",
  "criterion_scores":[{"id":"","score":0.0,"reasoning":""}],
  "weighted_score":0.0, "verdict":"pass|flag", "alex_ack":null }
```
`alex_ack` is the **calibration field** — `null` until Alex reviews, then `"agree" | "disagree"` (+ optional note).

## The calibration gate — per seat, and raw agreement is NOT enough (revised 2026-09-19, YED-206)
LLM-as-judge has **self-preference bias** — here it's judging work produced by a similar model (the "judge circularity" risk eval-harness flagged as R1). The original gate was "≥20 runs at ≥80% judge–human agreement". **That number is gameable by a seat that passes everything**: when Alex flags ~1 in 5 artifacts, a constant "pass" scores ~80% on its own. The Gemini seat's celebrated "83%" was exactly its always-pass baseline (triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`).

**The gate is now four numbers per seat**, produced by `python3 .claude/evals/calibration_stats.py`:

| metric | bar | why |
|---|---|---|
| agreement vs Alex | ≥ 0.80 **and above that seat's always-pass baseline** | the old number, kept but no longer alone |
| Cohen's κ | ≥ 0.60 | agreement corrected for chance; κ≈0 = adds nothing over always-passing |
| flag recall | ≥ 0.60 | of the artifacts Alex would send back, how many the seat caught — what a gate actually needs |
| flat-1.0 rate | < 0.30 | a seat scoring 1.0 on every criterion is low-information whatever its verdict |

**Standing as of 2026-09-19, recomputed after YED-201 restored the round-1 records a log-overwrite bug had been
destroying** (53 acked runs over 34 artifacts — a bigger, flag-heavier sample than the first cut of this table):

| seat | scored vs Alex | agree | baseline | κ | flag recall | flat 1.0 | standing |
|---|---|---|---|---|---|---|---|
| `claude:haiku` | 27 | 0.82 | 0.67 | 0.55 | 0.56 | 0.00 | advisory (κ + recall under) |
| `claude:sonnet` | 15 | **0.73** | 0.33 | **0.50** | 0.60 | 0.00 | advisory (agreement + κ under) |
| `gemini` | 26 | 0.65 | 0.62 | **0.12** | **0.10** | **0.81** | **advisory — fails 3 of 4** |
| `claude:opus` | 6 | 1.00 | 1.00 | — | — | 0.00 | not a seat; κ undefined (zero-variance sample) |

**No seat currently clears all four bars, including the one this file called "trusted" earlier the same day.** That
earlier read came from 10 scored runs on a pass-heavy sample; the restored records added flag-heavy ones and Sonnet's
absolute agreement fell to 0.73. Read honestly: Sonnet is still the most *informative* seat by a wide margin — 0.73
against a 0.33 always-pass baseline is a real signal, where Gemini's 0.65 against a 0.62 baseline is nearly none — but
**the bar is not moved to make a seat pass.** Consequence: the quorum escalates more often, which is the fail-safe
direction. Re-check as acks accrue; if the 0.80 absolute bar proves wrong for flag-heavy samples, change it in a dated
decision, never silently.

- *(Superseded 2026-09-28, YED-231: the advisory tier is gone. Roles are `voting` / `shadow` / `off` in `seats.json`, set by Alex; see the section below.)*
- Re-check on a rolling basis; failing a bar ⇒ fix the seat or the rubric, don't trust the score.
- The judge **scores + flags; it never auto-rewrites and never hard-blocks.**

## One voter, one shadow, one command (YED-231, 2026-09-28; replaced the YED-209 trust ladder)

Spec: `.claude/references/judge-right-size-yed-231.md`. How to run it: the `judge-build` skill (`python3 .claude/evals/judge.py run …`).

| File | Job |
|---|---|
| `seats.json` | Alex's static role map: `claude` **voting** · `openai` **shadow** · `gemini` **off** (adapter kept). Plus `revisit` floors and the named replacement candidate. No code writes it. A 4th seat is a row here, not new code |
| `judge.py` | `run` (bundle → shadow adapters → Sonnet brief → `--resume` merges, one line out) · `ack` (the ONLY `alex_ack` writer: append-only `quorum_ack` rows) · `pending` (un-acked clean passes, for the weekly batch-ack in `/rigor-review`) |
| `judge_lib.py` | what every seat shares: the scorer (parity-tested against the jq in `gemini-judge.sh`), the evidence bundle (`bundle_version 3`: `--artifact`, `--files` or `--range BASE..HEAD`, hunk mode over 60k chars) + its sha256, quote verification against the **whole bundle**, the privacy guard, the spend ledger + caps |
| `quorum_merge.py` | the merge: the voter's verdict is the verdict; a quote-verified shadow can only add `verdict_mismatch` / `score_divergence` / `shadow_major_defect`; integrity reasons force `flag`; shadow verdicts stay hidden until the ack |
| `calibration_stats.py --check` | the voter's κ / recall / null-check vs the `revisit` floors → a REVISIT banner (at every `judge.py run` and in `/rigor-review`). It **reports; it never changes a role** |
| `pricing.json` · `spend-ledger.jsonl` | prices with an as-of date; one ledger row per paid API attempt, failures included. Caps: `JUDGE_MAX_USD_PER_RUN` 0.50 · `JUDGE_MONTHLY_CAP_USD` 20 · `JUDGE_TOTAL_CAP_USD` unset = no lifetime cap (was 8 and 45; changed by Alex 2026-09-27) |
| `controls.py` · `controls/manifest.json` | the on-demand regression set: real labelled artifact states by git blob. `run` judges them and scores against the label (no longer scheduled; canaries retired 2026-09-28) |
| `test_judge_lib.py` · `test_bundle_multifile.py` · `test_quorum_nseat.py` · `test_check_revisit.py` · `test_adapter_contract.py` · `test_null_baseline.py` | offline, free; run them all (each is a script: `python3 <file>`) before changing any of the above |

**Truth is matched on content, not file name.** Every new row carries `artifact_sha256`; a run is scored only against
acks on the same hash. A legacy row without a hash is left *unscored* if git shows the file changed between the ack
and the run. (Before this, a file that was flagged, fixed and re-judged the same day had its correct "pass" scored
against the old flag, and the trusted seat read κ 0.53.)

**Revisit, not demotion (YED-231).** The ladder's canary and demotion rules produced 0 promotions in 70 days and its
one live output (demote the voter) was always suppressed by its own guard, so they were retired. `check()` fires when
the voter has ≥ 5 new acks since `revisit.since` and (κ < 0.40 on n ≥ 15, or flag recall < 0.50); the banner prints
the numbers, how much of the truth set came from escalations, and the candidate. Alex's `role` edit is the decision.
Rows with `calibration_set` in {control, bakeoff, negative-control, triage-experiment} never count.

## The null-model contract + the calibration-data ruling (YED-212, 2026-09-21)

**A metric a do-nothing policy scores just as well on is not a standard.** Every gating metric declares its
null baseline; a metric within +0.10 of it (n≥10), or with zero variance (n≥10), is **unvalidated** and cannot
auto-accept. `calibration_stats.null_check()` · surfaced in `--check` and in `/rigor-review` Step 2.

**Parity: absent ≠ paired.** 32 Gemini and 47 Claude rows predate the `evidence_parity` field and were being
counted as if the seat had been given the spec. Seat scoring is now **strict** (parity-true only) and reports
`parity_unknown` separately; `compute(..., strict_parity=False)` gives the historical view. Alex's **acks still
seed truth regardless of parity** — his verdict is about the artifact, not about what one seat was shown.
(Requiring parity there collapsed the truth pool from 35 artifacts to 1; caught in test.)

### Calibration-data ruling (Alex, 2026-09-21)
The Gemini seat's 2026-07-17 "provisional-trusted" promotion is **VOID as a trust claim**: it rested on 83%
agreement that was arithmetically the always-pass baseline. The rows are **kept as labelled data, partitioned**:

| partition | rows | standing |
|---|---|---|
| backfill (`calibration_set: backfill`) | 17 | baseline//history only — never evidence for promotion |
| prospective, `evidence_parity` absent | ~12 | **excluded** from seat scoring (counted as if paired until 2026-09-21) |
| prospective, `evidence_parity: true` | ~15 | valid — and these are the evidence *for* demoting Gemini to advisory |

## Deferred (non-destructive, do NOT build now) — now YED-188 (parked slate) + `platform-constraints.md` (2026-09-18)
A separate-model / cross-judge quorum (independence) and a Notion/PostHog projection of scores — per the lean-foundation decision (2026-06-26). The run-log contract above stays stable when added.
