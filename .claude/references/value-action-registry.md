# Value-Action Registry (the strict value-action contract)

Every metric in the build-rigor + measurement layer, with its `{threshold → action → surface}`. **No orphan metrics:** if a metric can't name the action it triggers, it isn't collected (PRD US-8 / Linear YED-94).

**No un-baselined metrics (contract amended 2026-09-21, YED-212 — Alex ruled).** The contract is now
`{null-baseline → threshold-above-baseline → action → surface}`. Every gating metric must state **what a
do-nothing policy scores on it**, and its threshold must sit at least **+0.10 above** that baseline.

> *Why this exists.* "83% Gemini-vs-Alex agreement" was **arithmetically the always-pass baseline**: on a corpus
> where 83% of artifacts pass, a seat that says "pass" to everything scores 83% while carrying zero information.
> The gate's ≥80% threshold sat **below** the null model, so it could never fire. It wasn't a weak standard; it
> wasn't a standard. The behaviour was recorded on day one (2026-07-17: "compresses good artifacts to 1.0…
> fine for a pass/flag gate") and only caught 63 days later, by Alex's gut on PR #81 — not by any metric.
>
> **The detector.** Any metric within +0.10 of its do-nothing baseline over n≥10, **or with zero variance** over
> n≥10, is demoted to **unvalidated**; anything gating on it **loses the right to auto-accept**, and a fix issue
> opens. Implemented in `calibration_stats.null_check()`; it runs in `/rigor-review` Step 2.
>
> **Corollary — a metric that cannot go down is not a measurement.** Before adding one, ask what value it takes
> when the system does nothing, and whether it can ever cross its own threshold. This is the governance capstone — review it whenever a metric is added or changed. Owner of every action at crawl = Alex (HITL).

| Metric | Source | Threshold | Action | Surface |
|---|---|---|---|---|
| build-quality judge score | `/judge-build`: one Sonnet reviewer, `build-quality@6` (since YED-231, 2026-09-28) | < 0.70, or any flag | the run flags and Alex decides; it never gates (`judge.md`) | in-session (judge verdict) |
| judge–human agreement | calibration (`alex_ack`, `calibration_stats.py`) | **baseline = the always-pass rate on the same rows** (was 83%) · must beat it by ≥ +0.10, and κ ≥ 0.60 | report only; raw agreement never makes the judge a gate | weekly review |
| DoD waiver-rate on builds | US-1 waiver log | climbing wk/wk | revisit the scope test / enforcement | weekly review |
| `dod_met` (self-reported) | US-1 `/dod-close` | **baseline ~100%: 34 of 35 non-null values are `true`, waived sessions included.** "Met" currently means "the ritual ran" | **unvalidated as a quality signal** — read the waiver reasons, not the boolean. Fix = derive it, or retire it | weekly review |
| DoD coverage | US-1 + US-2 | **denominator matters: 35 of 1,048 `build_session` rows carry a triplet.** "14 of 16 closed sessions" counts only sessions that already ran `dod-close` | quote coverage against ALL build sessions, never against the self-selected subset | weekly review |
| corrective-rounds ÷ acted-on value | US-2 `user_prompts` + US-5 | up 2+ consecutive wks | find where the agent keeps missing; tighten the skill/rubric | weekly review |
| correction-recurrence (same class) | US-7 recurrence log | ≥ 3 across builds (N set 2026-09-18) | system **proposes** a codified fix (rubric/DoD/skill/few-shot) → Alex approves | weekly review |
| acted-on outcome vs goal | US-4 + US-5 | trending down | kill / retune the build or the distribution play | Hub dashboard + weekly |
| owned-asset engagement | US-5 / US-6 | below goal target | revise the asset / distribution strategy | Hub dashboard + weekly |
| telemetry ingestion health | US-2 hook | 0 `build_session` events / 48h on active days | investigate hook/exporter (observability-of-observability) | weekly / PostHog alert (US-6) |
| signal-source freshness (stalest producer) | M2 trust strip | > 7d since a producer's last successful run | flag "source may be stale/broken"; investigate that producer | Hub dashboard (trust strip) |
| signal provenance coverage | M2 trust strip | **baseline 0%** (was ~100% by construction) · < 80% of recent signals carry a source **URL** | tighten producer sourcing — a producer is emitting uncited signals | Hub dashboard (trust strip) |
| producer liveness | M2 trust strip | any producer silent > 14d | producer health check — is the source/API broken? | Hub dashboard (trust strip) |
| relevance ranking (evolving viewpoint) | M2 relevance recompute (YED-121) | a topic's relevance > ~1.5 (rising & fresh) | draft content on the strongest **uncovered** topic — feed `pre-event-content` / `pattern-synthesis` | Hub dashboard (evolving viewpoint) |
| viewpoint freshness | M2 relevance recompute (YED-121) | top relevance decaying / no topic re-engaged in > 7d | run a producer (`/scan-roles`, `/scan-inbox`) to farm new signal — the viewpoint is going stale | Hub dashboard (evolving viewpoint) |
| identity ambiguity (30d) | `identity_probe.py` over `.claude/artifacts/identity-ambiguity.jsonl` (YED-47, added 2026-09-27) | **baseline 0 — by construction when no producer session ran**, so read it beside the probe's session count; ≥ **10 distinct** (table, name) entries in 30 days | the DDL re-trigger: move the parked `name_norm` / `entity_alias` / `entity_merge` issue (YED-47's DDL half) to Todo. Below it, the ledger is the merge-proposal queue | weekly review |
| identity duplicates | `identity_probe.py` live graph (exact dupes · qualifier twins · website-host / LinkedIn collisions · tombstones-with-edges) | **baseline 2026-09-27: 1 person dupe · 3 company twins · 3 topic twins · 2 host collisions · 0 tombstones** — the floor to beat; any pair > 0 | propose each pair with `substrate.py merge … --dry-run`; **Alex approves every merge** (human-only, reversible, deletes nothing). A tombstone-with-edges is a merge-kept collision (fine) unless a producer wrote to it (bug → fix the resolver) | weekly review |

## Judge status (versioned — never change silently)
- **2026-09-28 — YED-231: the trust ladder, the Gemini/OpenAI seats, the quorum, the spend cap and DoD item 4 were removed.** The judge is one advisory Sonnet reviewer that flags (`judge.md`); nothing gates on calibration. The entries below are history.

- **2026-07-17 — build-quality judge → PROVISIONAL-TRUSTED.** Crossed the calibration gate (22 acked runs @ 86.4% agreement ≥ the ≥20-@-≥80% bar). Scope of trust: it **gates** the DoD "done" on *genuinely new, independent builds* (a `< 0.70` verdict flags before shipping). It stays **advisory** on self-produced / re-judged work — ~7 of the 22 acked runs are re-judges of same-session fixes (correlated), so the sample isn't fully independent. **Drop "provisional"** once independent-first-look agreement holds ≥80% across ~15+ runs (revisit each `/rigor-review`). The 3 disagrees (trend-radar leniency · gcc judge-variance · multi-agent unverified-as-verified) are logged calibration signals, not noise. Judge runs on the cheap model (Haiku); `build-quality@2` is the live rubric.

- **2026-09-18 — first `/rigor-review` since 07-17 (YED-189). Status: PROVISIONAL-TRUSTED, unchanged.** Correction to the line above: the live rubric is `build-quality@4` (08-21) and the seats are Sonnet + Gemini (not Haiku) since 07-17. Acked quorums 07-18→09-19: 12 of 18, **12/12 agree** at the quorum level (incl. the three YED-190 escalations Alex broke on 09-19, all toward flag). Independent first-look acks ≈12, still short of the ~15 bar, so "provisional" stays. **New caveat:** the Gemini seat returned 1.0 on 17 of 18 prospective non-control runs (the 18th: 0.98) and missed both real flags this window (`spine_client`, `inbox_boundary` — Sonnet caught them). Its concurrence is near-ceiling, so a quorum "agree" is mostly the Sonnet seat's signal. Nuance from 09-19: Gemini *did* catch one real defect Sonnet missed (inbox-miner L99), so the seats are complementary on some defects, not redundant. The problem is calibration (it scores almost everything 1.0), not zero signal. Watch-listed in `correction-recurrence.md`; not re-tuned yet.
- **Thresholds re-affirmed 2026-09-18:** `< 0.70` gate · `< 80%` agreement · waiver-rate "climbing wk/wk" · corrective-rounds "up 2+ wks" · outcome "trending down" · 48h ingestion · 7d/14d/80% trust-strip values. None moved: each either never fired or fired once and was correct. **One seed filled:** correction-recurrence `N = 3` (the only two acted-on classes fired at 5 and 1; 3 is the smallest count that separates a pattern from a one-off). **Set 2026-09-19 (YED-201 Fix 1A, Alex ruled):** DoD item 4's N = the build's own session; a judge waiver must say *no gradable artifact* or name the Linear issue holding the make-up run, enforced by `dod-close.sh`.

## Rules
- **Adding a metric?** It does not ship without a row here (threshold + action + surface). Can't fill the row ⇒ don't collect the metric.
- **Surfaces are capped at three** — *in-session DoD boundary · Hub dashboard · weekly review*. Don't add a 4th; route new metrics to one of these (extra surfaces = noise nobody acts on).
- **Actions stay HITL at crawl.** Automating any action is a deliberate, separate decision (not a default).
- **Thresholds are starting values.** `N` / "2+ wks" / "< 0.70" are seeds — tune them in the weekly review as real data accrues, and record the change here (this doc is versioned in git; never silently re-tune).
