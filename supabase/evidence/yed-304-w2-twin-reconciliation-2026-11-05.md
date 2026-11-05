# YED-304 W2 — twin backfill dry-run reconciliation (2026-11-05)

Companion to `yed-304-w2-dry-run-2026-11-05.{md,json}` (twin source) and the PR #266
baseline (`yed-304-holdout-validation-2026-11-03.md`, fixture `yed304_topic_clusters.json`).
Read-only throughout: psql SELECTs on the twin (`ytfzzsxcxxbejnowmkmk`) via the session
pooler; nothing was written to the twin or to prod.

## Headline

**The backlog is already gone.** The twin's live unassigned pool is **1 topic**
("AI Personas & Digital Minds"), and the kNN dry-run at the PR #266 ship point
(k=3, threshold 0.85) auto-assigns **0** and queues **1** for review. Nothing to
auto-assign; one row for Alex.

## Reconciliation vs the PR #266 baseline and the fixture

| Check | Baseline (fixture, 2026-11-03) | Twin (2026-11-05) | Status |
|---|---|---|---|
| Ship point reproduced offline | k=3, thr=0.85 → auto 3 / review 99 | same run today, unchanged fixture → auto 3 / review 99 | ✅ exact reproduction |
| Curated pool integrity | 170 LLM bootstrap assignments | 156 live `cluster_assigned_by='llm'`, cluster agreement **156/156**, 0 moved | ✅ zero drift |
| Missing 14 of 170 | 8 tombstones identified in fixture work | 14 rows merged away since (tombstoned, cluster retained) | ✅ accounted for |
| Backlog | 102 unassigned (94 real after tombstones) | 89 assigned since (all `session`), 12 merged away, 1 live | ✅ fully traced |
| Attended-linked backlog | 33 flagged (changing snapshot, W4) | **0** | ✅ improved — every attended-linked topic now carries a theme |
| Cluster count | 30 | 33 (`topic_intelligence.topic_cluster`) | ℹ️ 3 themes added since the fixture |

The baseline's verdict stands unchanged: precision 0.900 at 5.9% coverage is
coverage-degenerate — and with the backlog cleared by the in-session assigner, the kNN
backfill has almost nothing left to do. The remaining question for Alex is exactly the
1-row review queue below.

## The one review-queue row (Alex decides; writes as `human`)

| topic | top-3 candidate clusters (share / best sim) | confidence |
|---|---|---|
| AI Personas & Digital Minds | AI Talent, Hiring & Leadership (0.67/0.80) · AI, Work & Society (0.33/0.80) | 0.531 |

Auto-assign bar is 0.85; this row sits at 0.531 with a split vote — a genuine
"none fits / new theme?" candidate.

## Script fixes this run required (same PR)

1. **Twin read path repointed `canonical_v2.topic` → `public.topic`.** The post-swap twin
   (verified live 2026-11-05) holds the cluster columns in `public.topic`; `canonical_v2`
   is gone. `--check-twin` now treats legacy schemas as informational, not a failure.
2. **Merge-tombstone exclusion fixed.** psql `--csv` renders NULL as `""`, so the old
   `row["cluster_id"] is None` test never fired: the first run of the day silently kept
   12 tombstones in the unassigned pool (it reported auto 3 / review 10). The corrected
   falsiness test excludes them (auto 0 / review 1). Regression-tested
   (`TestFetchTopicsTwin`, 4 cases; suite 48/48).

## Caveats (carried from the baseline)

- Name-only embeddings; confidence measures agreement with the LLM bootstrap taxonomy,
  not hand-labelled truth.
- `attended_linked` and the backlog are moving snapshots; counts above are as of
  2026-11-05T21:18Z.
