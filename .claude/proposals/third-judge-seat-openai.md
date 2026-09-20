<!-- Spec for YED-209. Infra = spec (YED-129): this in-repo reference is the spec artifact; no ChatPRD doc.
     Authored 2026-09-19 by the principal-architect agent on Fable 5.1, read-only, before any code.
     STATUS: PROPOSED, awaiting Alex's rulings on the three forks at the end. Build is blocked on PR #85 (YED-206). -->

# Third judge seat (OpenAI): design spec for approval

No files in the repo were edited and no paid API was called. I ran `git fetch`, a dry-run `git merge-tree` (it leaves one unreferenced object in `.git` and does not touch the working tree), and `calibration_stats.py` against log copies in the scratchpad. OpenAI prices and data rules were read from OpenAI's live docs today.

## Summary
1. **What it is.** A third judge seat, `openai:gpt-5.4`, runs on every `/judge-build` next to Sonnet and Gemini. All seats get one shared, hashed evidence bundle, and seats are defined by a config file, so a fourth seat is config and not code.
2. **The rule that makes it air tight.** A seat's PASS reduces scrutiny only after that seat has earned voting status against your labels, while any seat's doubt can add scrutiny. Promotion is a manual config commit by you. Demotion is automatic and computed from the run-logs on every run.
3. **How the new seat enters.** It starts in **shadow**: recorded, no power, and hidden from you until after you ack, so your label stays uncontaminated. It moves to advisory after a control-set bake-off and to voting only on prospective numbers, realistically December to January.
4. **Cost.** About $0.14 per run on gpt-5.4. The bake-off is a one-time ~$11, the remaining backfill ~$3, canaries ~$1.50 a month and production ~$2–4 a month, so $50 lasts roughly 7–9 months. Mechanical caps sit at $0.50 per run, $8 a month and $45 lifetime.
5. **What you do.** Approve the three forks at the end. Buy prepaid OpenAI credits with auto-recharge off, create a dedicated project key, confirm data sharing is off, and ack judge runs as you do today.
6. **A prerequisite I found.** Once #85 merges with main, the trusted Sonnet seat measures κ 0.50 / recall 0.60, below its own bars, because of a truth-matching bug. That bug has to be fixed before any auto-demotion rule ships (§0).

## 0. Finding that changes the plan: calibration "truth" is matched by file path, not file content
`calibration_stats.py` scores a run against the nearest-in-time ack for the same artifact path.

| Logs | Sonnet agreement | κ | Flag recall | n |
|---|---|---|---|---|
| #85 branch | 0.90 | 0.80 | 0.80 | 10 |
| main, and main ∪ branch | 0.73 | 0.50 | 0.60 | 15 |

- There are 4 "misses". Three of them are the 22:30 re-judges of `inbox-miner`, `pre-event-content` and `role-radar`, run after PR #87 fixed those files and scored against flags on the pre-fix content.
- Sonnet correctly passed fixed files and is being marked wrong for it.
- Four Sonnet rows have no `timestamp` at all, because the orchestrating model hand-writes that log line, and they fall out of the match window.

**Fix (build step 2):** every seat row and quorum row carries `artifact_sha256`. Truth matches on the hash first, and the time window is used only for legacy rows without a hash. Without this, auto-demotion would demote Sonnet the day it ships and every run would escalate.

Confidence in this diagnosis: 90%. I traced each miss row by row.

## 1. Seat role and trust ladder
There are three statuses, held in a new file `.claude/evals/seats.json`.

| Status | Power |
|---|---|
| `shadow` | Runs and is logged, with no effect on resolution. Its output is shown to you only after you ack. |
| `advisory` | Can add escalation reasons. It can never enable or cause an auto-accept. |
| `voting` | Its verdict counts toward the final verdict. |

Effective status is the lower of the configured status and the earned status. `quorum_merge.py` calls `calibration_stats.py --gate --json` on each run, which is local, free and fast.

**Shadow → advisory.** All of the following, on the control and backfill sets:
- At least 20 scored runs.
- Control verdict accuracy of at least 10 of 12.
- Planted-defect recall of at least 0.70, meaning the seat's `defects[]` cites the planted line.
- False flags on positive controls of at most 1 in 6.
- Flat-1.0 rate below 0.30.
- Adapter or format failure rate below 5%.
- At least 5 clean prospective runs.

**Advisory → voting.** All of the following, measured only on rows that are prospective, evidence-parity true and hash-matched:
- n ≥ 25, including at least 8 artifacts whose truth is flag.
- κ ≥ 0.60.
- Flag recall ≥ 0.70.
- Flag precision ≥ 0.60.
- Flat-1.0 rate < 0.20.
- Agreement at least 0.10 above the always-pass baseline.
- Canaries green on the current resolved model id.
- Not redundant with Sonnet: inter-seat κ against Sonnet below 0.90, or at least one unique true catch.
- You change the config line yourself. Promotion is never automatic.

**How much n is enough.** At n = 25 the standard error on κ is still around 0.17. The 8-flag requirement is the constraint that actually binds. At the current ~10 first-look artifacts a month with ~30% flags, it takes about 3 months.

**Automatic demotion by one rung**, on a rolling window of the last 20 prospective runs:
- Flat-1.0 rate ≥ 0.30.
- Recall < 0.50 with at least 4 truth flags in the window.
- Precision < 0.40 with at least 5 seat flags (this is the over-flagging guard).
- κ < 0.40 with n ≥ 15.
- Two consecutive canary failures, or any flat 1.0 on a negative control.
- Resolved model id changed and no canary pass since.
- Adapter failure rate above 20% over the last 10 runs.

Demotion rules apply to Sonnet too (fork 3).

## 2. N-seat quorum rule
The voting seats decide the verdict, and advisory seats can only add caution. Seats with the same provider or the same `independence_group` count as one vote.

| Voting seats | Advisory seats | Result | Final verdict |
|---|---|---|---|
| All PASS, from ≥2 independence groups, max pairwise Δ < 0.15, none flat, bundle hashes match, canaries fresh | none flag | `auto` | pass |
| One voting seat only (today), PASS, not flat | all pass, none flat, Δ < 0.15, evidence parity true | `auto` — this is current behaviour, generalized | pass |
| All FLAG | any | `auto` — a flag goes to you anyway | flag |
| PASS | any advisory flags, is flat, lacks parity, or Δ ≥ 0.15 | `escalated`, or `failsafe_flag` in autonomous mode | pass pending your ack, or flag |
| Split (2–1 or 1–1) | any | `escalated`, or `failsafe_flag` | flag |
| No effective voting seat | any | `escalated`, or `failsafe_flag` with reason `no_voting_seat` | flag |
| Advisory or voting seat missing, or bundle hashes differ | any | `escalated`, or `failsafe_flag` with reason `seat_missing:<id>` or `evidence_mismatch` | flag |
| A shadow seat says anything or is missing | any | Recorded only | unchanged |

- **Why 2-of-3 majority is rejected.** A majority assembled from possibly correlated models is not independent evidence, and an escalation costs you about 15 seconds.
- **Evidence check.** A seat is tagged `evidence_unverified:<seat>` when more than 30% of its defect quotes fail verbatim verification (§6). That tag strips the seat's escalation power for that run and counts as a format failure.

## 3. What "rotation" should mean: all three seats, every run
- Cost is not the constraint. Roughly 10–30 runs a month at $0.14 is $1.50–4.
- Labeled n is the scarce resource, and every skipped run delays the seat's scorecard.
- **Rotating the second seat loses.** It halves each seat's n and removes the pairwise-correlation data.
- **A tiered setup loses.** Running the seat only on escalations means it is calibrated only on hard or disputed artifacts, which is a biased sample. It also never gets tested on the polished-looking passes where Gemini failed.

Confidence: 85%.

## 4. Model choice
- **Default: `gpt-5.4` with `reasoning.effort: "medium"`.**
- `gpt-5.4-pro`, at about $1.60 per run, is excluded.
- There is no automatic fallback. A different model is a different seat with its own scorecard.
- The "fallback" is the bake-off runner-up. It is switched in by a config edit and enters at advisory with the bake-off rows it already has.

Prices per 1M tokens, input / output, from OpenAI's pricing page today. The per-run estimate assumes about 18K input tokens and 6K output tokens, where output includes reasoning tokens.

| Model | Input | Output | ~Cost per run | Runs for $50 |
|---|---|---|---|---|
| gpt-5.4-mini | $0.75 | $4.50 | $0.04 | ~1,250 |
| gpt-5 / gpt-5.1 | $1.25 | $10 | $0.08 | ~600 |
| gpt-5.2 | $1.75 | $14 | $0.12 | ~430 |
| **gpt-5.4** | $2.50 | $15 | $0.135 | ~370 |
| gpt-5.5 | $5 | $30 | $0.27 | ~185 |

**Bake-off: yes, pre-registered, the same way YED-172 was.**
- Three arms (5.4-mini, 5.4, 5.5) on a 24-item core set: 12 real pre-fix flag states, 6 known-good artifacts and 6 planted-defect controls.
- Cost: 24 × $0.445 ≈ $10.70.
- The winner is the arm with the highest recall on real (non-synthetic) flags, subject to at most 1 of 6 false flags on positive controls and a flat rate of at most 0.20.
- A tie within one item goes to the cheaper model.
- The winner runs the rest of the backfill for about $3.
- Gemini Pro was also a frontier model when it rubber-stamped, so model size alone does not protect against this.

## 5. Independence
**Mechanical independence.**
- A new `judge-bundle.sh` builds one evidence bundle, all in the same order: system prompt, rubric, artifact type, context, dangling references, tombstones, density signal, and the line-numbered artifact.
- It records `bundle_sha256` and `bundle_version: 2`.
- Every adapter takes `--bundle`, and the Sonnet subagent receives the rendered bundle text.
- Adapters accept no verdict inputs, so one seat cannot see another's verdict by construction.
- The merge raises `evidence_mismatch` if the bundle hashes differ.

**Correlation detection.** `calibration_stats.py --pairwise` reports:
- Inter-seat κ.
- Joint-miss counts on truth-flag items, compared with the product of each seat's miss rate.
- Spearman correlation on composites.
- A per-seat correlation between artifact length and score, as a verbosity-bias check.

**Collapsing correlated seats.** Two seats with κ ≥ 0.85 and shared misses collapse into one independence group.

**Bias checks that apply less here.**
- Position bias does not apply, because scoring is pointwise.
- OpenAI self-preference is a low risk, because the artifacts are Claude-produced. The check is a canary comparing a GPT-written artifact against a Claude-written equivalent, and it is low priority.

## 6. Anti-rubber-stamp and anti-over-flag mechanics
- **Output order.** Strict JSON schema enforces the order `checks_performed[{criterion, what}]` → `defects[{line, quote, criterion, severity, spec_ref, description}]` → `criterion_scores` → `cap_flags`. The harness computes the composite and the verdict.
- **Must-cite rule.**
  - Any criterion scored below 0.85 needs at least one defect on that criterion.
  - Any criterion scored 1.0 needs at least one `checks_performed` entry for it.
  - The harness verifies each `quote` as a whitespace-normalized verbatim substring near the cited `line`. This is what catches fabricated defects, the over-flag failure mode.
- **Flat-ceiling detection** is unchanged.
- **Canaries** live in `.claude/evals/controls/manifest.json`.
  - Negative controls reference pre-fix git blobs as `sha:path`, with no copies kept in the repo.
  - Planted-defect controls are patch files applied in a temp directory.
  - Positive controls are known-good artifacts.
  - Controls are tagged `calibration_set: "control"`, reported separately and never pooled into κ.
  - Schedule: a 3-item mini-set before each `/rigor-review` (~$0.40), and the full set whenever the resolved model id changes.
- **Synthetic controls are necessary and not sufficient.** Gemini's failure was precisely that it detects blatant faults and stamps polished work. The real pre-fix states, such as the ADR-10 decision 9 line, are the subtle tier.

## 7. Adapter contract: `.claude/hooks/openai-judge.sh`
- **Flags** are identical to `gemini-judge.sh`: `--artifact`, `--artifact-type`, `--calibration-set`, `--context`, `--spec-file`, `--model`, `--rubric`, `--system`, `--label`, `--print-only`. It adds `--bundle`.
- **Request.** `POST /v1/responses` with:
  - `text.format: {type: "json_schema", strict: true, …}`. Strict mode emits keys in schema order, which I put at about 85% confidence. Verify it on the first `--print-only` run.
  - `reasoning: {effort: "medium"}`, `store: false`, `max_output_tokens: 16000`.
- **Determinism, stated honestly.** I believe GPT-5-class reasoning models accept neither `temperature` nor a reliable `seed`. I am relying on memory here, not on a page I read, so check the current API reference before building. If it holds, determinism is measured and not set: duplicate canary runs give a per-seat `score_sd`.
- **Key handling.**
  - Reads `${OPENAI_API_KEY:-${OpenAI_KEY:-}}`.
  - The key is sent through `curl --config -` on stdin and never in argv. This is stricter than the Gemini adapter, whose key is visible in `ps`.
  - No `set -x`.
  - Failure dumps go to `$TMPDIR`.
- **Retries and timeouts.**
  - `--connect-timeout 10 --max-time 300`.
  - Two retries, at 5 seconds and 20 seconds, on 429, 5xx and timeouts only.
  - No retry on 400, 401 or 403.
- **Every response is validated.**
  - `status == "completed"`; an `incomplete` status prints `incomplete_details.reason`.
  - No refusal item in the output.
  - Exactly 5 criteria, all with numeric scores.
- **Exit codes.** 1 = API or format failure, 2 = usage error, 3 = privacy guard, 4 = budget. It never degrades silently.
- **Run-log, additive fields only.**
  - `judge_model: "openai:gpt-5.4"` and `judge_model_resolved` (taken from `.model`).
  - `judge_provider: "openai"`, `reasoning_effort`, `usage`, `cost_usd`.
  - `artifact_sha256`, `bundle_sha256`, `seat_status`.
- **Log writes** append with `>>`.

## 8. Cost guard
- **Ledger.** `.claude/evals/spend-ledger.jsonl` gets one row per API attempt, including `--print-only` runs and failures. Run-logs alone would miss those.
- **Price table.** Prices live in `.claude/evals/pricing.json` with an as-of date and the source URL. A model missing from the table causes exit 4.
- **Caps.**
  - `JUDGE_MAX_USD_PER_RUN=0.50`, checked before the call using the worst-case estimate.
  - `JUDGE_MONTHLY_CAP_USD=8`.
  - `JUDGE_TOTAL_CAP_USD=45`.
- **At a cap.** The adapter exits 4 and the merge records `seat_missing:openai`.
- **The true hard cap** is prepaid credits with auto-recharge off.

Proposed value-action registry rows:

| Metric | Threshold | Action | Surface |
|---|---|---|---|
| Judge API spend (ledger) | ≥ 75% of the monthly cap, or lifetime spend ≥ $35 | Review volume and model; you decide whether to top up or downgrade | weekly review |
| Seat canary | Any failure | The seat auto-demotes; investigate before trusting it again | in-session |
| Quorum escalation rate | > 40% over the last 20 quorums | Retune thresholds, or drop a noisy advisory seat to shadow | weekly review |

## 9. Privacy on a public repo
**What is sent to OpenAI.** The judge prompt, the rubric, the artifact, any spec files that were passed, and the pre-pass lists. The contents of files the artifact merely references are never sent.

**Bundle guard, exit 3, no override.**
- Any artifact or spec path that matches `git check-ignore`.
- Any path outside a git repo.
- A secret-pattern hit: `sk-`, `phc_`, `phx_`, `AIza`, a JWT, or a PEM header.

**What you toggle in OpenAI.**
- Create a dedicated project with a project-scoped key.
- Under Settings → Organization → Data controls, confirm input/output sharing is **off**.
- Do not join the free-daily-tokens data-sharing program. The small budget makes it tempting, and it opts you into training.

**Data retention.**
- API data is not used for training by default.
- `store: false` stops response persistence.
- The 30-day abuse-monitoring log remains. Zero Data Retention needs sales approval and is not worth pursuing for public content.

**Other changes.** Add `OPENAI_API_KEY=` to `.env.example`, and add a `platform-constraints.md` row for the key name.

## 10. Calibration plan
- **Approach A, backfill.** Run about 35 acked artifact states, reconstructed by hash or by git sha for pre-fix content, with `calibration_set: "backfill"`.
- **The labeled set.** It holds 16 flag acks over 13 artifacts, and I listed them from the logs.
- **The labels carry an anchoring bias.** Every seat's flag precision is 1.00, which means you have never rejected a flag. The labels are shaped by what the judges showed you.
- **Finding more flag-worthy examples.**
  - Mine git history for the pre-fix states of those 13 artifacts, plus files fixed after review in PRs #84, #85 and #87.
  - Add 6 planted-defect patches covering: spec drift, a live tombstoned tool, bare `except`, a bypass of `spine_client`, an absent command skeleton, and an unverified claim presented as verified.
- **Approach B, prospective.** The §1 bar for voting, including at least 8 real flags, applies. Backfill and control results never count toward voting.
- **Blind-first acks.** On 1 in 5 runs you give your verdict before seeing any scores, recorded as `ack_mode: "blind"`.

## 11. Build plan, in dependency order
1. **Reconcile #85 first.** One session does this, merge-only. Merge `origin/main` into the #85 branch and resolve the three conflicted files. I confirmed these by dry run.
   - `gemini-judge.sh`: keep #85's body and re-add #84's tombstone pre-pass, its `--arg tombs` and its prompt section.
   - `quorum-merge.sh`: keep #85's quorum record and use `>>`. Also fix the adapter's own `>` clobber, and the comment that describes the old behaviour.
   - `judge-build/SKILL.md`: keep #85's text, insert the tombstone step as Step 0.2, renumber density to 0.3, take the union of the reference lists, and change #84's "rubric unchanged at @4" to `@5`.
   - Run the quorum scenario tests (6 of 6), merge, and put a note in the README that the Sonnet standing will read low until step 2 lands.
   - Do not stack the third seat on #85.
2. **New worktree from main.** Add `artifact_sha256` and hash-first truth matching in `calibration_stats.py`. Add `.claude/hooks/seat-log.py`, a validated writer for the Sonnet seat's log line, which ends the missing-timestamp rows.
3. `judge-bundle.sh`, and the Gemini adapter refactored to use it.
4. `seats.json`, `pricing.json` and `controls/manifest.json` with its patches.
5. `openai-judge.sh` with the ledger.
6. `quorum_merge.py`, the N-seat merge. `quorum-merge.sh` stays as a back-compat wrapper so the existing 6 scenarios pass unchanged.
7. `calibration_stats.py` gains `--gate`, `--pairwise`, the `openai:` seat mapping and separate reporting for controls.
8. `run-canaries.sh`.
9. Docs:
   - `cross-provider-judge.md` v2.
   - `evals/README.md`.
   - `judge-build/SKILL.md` and `commands/judge-build.md`.
   - Registry rows in `value-action-registry.md`.
   - Rows in `platform-constraints.md`.
10. Bake-off → backfill → `/judge-build` on the new files themselves → `/dod-close`.

**New test scenarios.**
- Shadow flag is ignored.
- Advisory flag against a voting pass escalates.
- Two advisory passes cannot rescue a voting flag.
- Missing advisory seat → `seat_missing`.
- Missing shadow seat → recorded only.
- Differing bundle hashes → `evidence_mismatch`.
- No effective voting seat → fail-safe flag.
- Two voting seats from the same provider do not count as unanimity.
- 2–1 voting split, autonomous mode → `failsafe_flag`.
- Configured-voting seat auto-demoted by the gate.
- `evidence_unverified` strips a seat's escalation power.
- Budget exit 4 → `seat_missing`.

**Must not change.**
- Run-log and quorum fields change by addition only.
- Keep the `claude{}` and `gemini{}` blocks, `agree`, `resolution`, `final_verdict` and `alex_ack`.
- Rubric `@5` and `judge-system-v2` stay immutable.
- The build-session contract is untouched.
- The judge never rewrites an artifact and never hard-blocks.

**DoD.** This is infrastructure, so the artifact is a spec, per YED-129. A Linear issue is still owed. I did not file one because this task was read-only, and the container rule says to file it the same turn the spec is written.

## 12. Pre-mortem
Most likely causes of failure three months out, ranked, each with its mitigation in the design:
1. **The OpenAI seat rubber-stamps.** Prevented by shadow entry, flat-ceiling detection, canaries, the real subtle-defect tier, and the fact that an advisory seat's PASS can never reduce scrutiny.
2. **Escalation fatigue, where you stop reading and just ack.** Prevented by the advisory precision guard, the escalation-rate registry row, and quote verification.
3. **The seat never gets promoted because n and flags are too scarce, leaving permanent "theater".** Handled by an explicit timeline, all-runs rotation, and a removal rule: if it has not reached voting and has zero unique true catches after 6 months, drop it.
4. **A silent model-snapshot change shifts the seat's behaviour.** Prevented by logging the resolved model id and auto-demoting the seat until canaries pass on the new snapshot.
5. **Measurement bugs flatter or punish a seat.** Examples are the κ = 1.0 on a zero-variance sample and the path-based truth matching. Prevented by hash matching, the validated log writer, and the zero-variance guard that already exists.
6. **A cost or key incident.** Prevented by the ledger and caps, prepaid credits with no auto-recharge, the key passed on stdin, and the privacy guard.

**Risks this design does not solve.**
- Ground truth is anchored on the judges' own output, as the 1.00 flag precision shows. Blind-first acks only sample against it.
- Defects that all three LLMs miss never reach the truth set, so recall is an upper bound. Even at the promotion bar, the κ confidence intervals stay wide.

## Decisions for Alex
1. **Rotation.** Run all three seats every run, or tier the OpenAI seat to escalations only. Recommendation: all three every run.
2. **Bake-off.** A three-arm bake-off that includes gpt-5.5 for about $11, or commit to gpt-5.4 untested. Recommendation: run the bake-off. It is a one-time cost and the selection rule is pre-registered.
3. **Sonnet and auto-demotion.** Make Sonnet subject to the same auto-demotion as every other seat, or exempt it as the anchor. Recommendation: subject it, after the hash fix lands. Expect occasional stretches where every run escalates. That is the system being honest, and exempting the anchor seat would recreate the Gemini blind spot one level up.

**Confidence levels.**
- Quorum rule and trust ladder: 85%. The shape is proven by the containment work on #85.
- OpenAI API details (strict-schema key ordering, no temperature or seed control): 80%. Verify on the first `--print-only` call.
- Cost estimates: 75%. Reasoning-token volume at medium effort is the unknown.
- Reaching voting status by January: 50%. Flag scarcity is the bottleneck.

**Files relevant to this design.**
- On `origin/alex/yed-206-gemini-judge-fixes`, under `/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/.claude/`:
  - `hooks/gemini-judge.sh`
  - `hooks/quorum-merge.sh`
  - `evals/calibration_stats.py`
  - `evals/test_quorum_scenarios.py`
  - `evals/README.md`
  - `evals/prompts/judge-system-v2.md`
  - `evals/rubrics/build-quality-v5.md`
  - `references/cross-provider-judge.md`
  - `skills/judge-build/SKILL.md`
  - `commands/judge-build.md`
  - `notes/gemini-judge-triage-2026-09-19.md`
- On `origin/main`, under the same `.claude/` root:
  - `hooks/check-tombstones.py`
  - `hooks/check-refs.sh`
  - `references/platform-constraints.md`
  - `references/build-in-public.md`
  - `references/value-action-registry.md`
