# Topic clustering gap: definition, diagnosis, plan

**Linear:** YED-304 · **Status:** proposal, for build by Claude Code + Obvious · **Owner of decisions:** Alex
**Evidence:** read-only SQL against The-Prod-Brain (`oicikjyzmxqfomrrqkvf`), 2026-11-03. Queries in the appendix.

---

## 1. The problem in one paragraph

The market-intelligence graph reports **trends per theme, not per topic**: 30 curated clusters ("themes"),
each holding many topics. A topic counts towards a trend only once it is assigned to a cluster. That
assignment was done **once**, as a bootstrap in July/August, and nothing has assigned a topic since.
New topics keep arriving from every post-event run, but they sit outside every theme, so the trend view
quietly under-counts the autumn. The health view already measures this and has been tripping, but nothing
alerts on it, so the nightly job stays green.

## 2. What we found (prod, 2026-11-03)

| Measure | Value | Do-nothing baseline |
|---|---|---|
| Live topics (`public.topic`) | 272 | — |
| Topics with no cluster | **102** (37%) | 0 on 8 Aug, after the bootstrap |
| …of topics added after 17 Jul | 94 of 119 unassigned | 145 of 153 assigned before |
| Unassigned topics tagged on **attended** events | 33 | these are the ones that change trends |
| Attended events since 6 Aug | 25 | — |
| …that add **nothing** to any trend | **9** (36%) | 0 if assignment ran |
| Attended-event topic tags dropped by the compute | 39 of 272 (14%) | 0 |
| Health tripwire `canonicalization_backlog` | 102 vs threshold 5 → `trip` | — |
| Health tripwire `granularity_insufficient` | 1.000 vs 0.400 → `trip` | see §4.4 |
| Nightly health check (`healthcheck_2b.py`) | green, 30 of 30 runs | — |

The 9 invisible events break into **two different failures**:

- **2 events have topic tags, but none are clustered** (Shortlist Aug 24, Elastic{ON} Oct 8). This is the clustering gap.
- **7 events have no topic tags at all** (RevGenius IRL Aug 12, Agentics Aug 19, Agentic AI in Production Aug 20,
  and four Sept 8–9 webinars: GLM-5.3, Attio, Clay RevOps, ElevenLabs). This is a **tagging** gap upstream of clustering.
  It is likely a separate cause (webinars or events never run through `/post-event-content` Step 3.8). It's in scope
  to diagnose, not to assume.

Partial events matter too: Daytona (Sept 9) has 10 tags, of which 4 count; Revolt! Day 1 has 4, of which 1 counts.

## 3. Why it happened (root cause)

1. **Clustering was built as a bootstrap, not a process.** YED-110 (gtm-os `scripts/topic_intelligence/bootstrap_clusters.py`)
   clustered the 170 existing topics on their Notion rich text into N=30 themes, with a calibration report, and wrote
   them once. The 2B migration carried those assignments forward (`build_2b_canonical_v2.py` step C, via
   `topic_crosswalk`), plus one LLM pass on 8 Aug for 25 more. No ongoing step was ever specified.
2. **The producer can't write the column.** New topics enter through `substrate.py ensure-entity` → `spine_client.py`.
   `spine_client.ALLOW["topic"]` is `{id, name, description} ∪ common`, with no `cluster_id`, `cluster_assignment_confidence`
   or `cluster_assigned_by`. Even a willing producer has no sanctioned path to assign a cluster.
3. **The compute silently drops unassigned topics.** `compute_topic_intelligence` (0012) filters `t.cluster_id is not null`.
   That's correct for the maths, but it means a gap shows up as *fewer events*, never as an error.
4. **The detector isn't wired to an alarm.** `topic_intelligence_health` (0013) computes `canonicalization_backlog`
   and has tripped for weeks. Only the Hub cockpit strip reads it. `healthcheck_2b.py` checks *internal consistency*
   (stored numbers = recompute), which stays true however many topics are missing.

**The systemic lesson:** a check that verifies the maths is right is not a check that the inputs are complete.
It's the same blind spot as YED-297 (columns that exist but nobody looks at). Every derived metric needs a
*coverage* assertion beside its *correctness* assertion.

## 4. The fix

Four workstreams. W1 and W2 are the fix; W3 stops it happening silently again; W4 is the upstream tagging gap.

### W1. A sanctioned write path for cluster assignment (guarded change, human review)

- Add `cluster_id`, `cluster_assignment_confidence` and `cluster_assigned_by` to `spine_client.ALLOW["topic"]`.
  None of them is PII. This **is** a guard/allowlist diff, so per CLAUDE.md invariant 1 it gets human review
  even though it's harmless. Run `--selftest` and `--check-writers`.
- `cluster_assigned_by` values: `bootstrap` (existing), `llm` (existing), `embedding_auto`, `human`.

### W2. The assigner: backfill now, then run on every new topic

**Method (recommended): k-nearest-neighbour on embeddings against the 170 already-curated assignments.**

- Embed each topic's `name + description` with the local `bge-small` model `substrate.py` already uses (free,
  deterministic, runs in a GitHub Action, no metered API).
- For an unassigned topic, find its k=7 nearest *assigned* topics. Vote by similarity-weighted cluster.
  Confidence = winning cluster's share of the vote × top-1 similarity.
- **≥ 0.80 confidence → auto-assign** (`embedding_auto`). The health view's `membership_confidence` tripwire
  already treats 0.80 as the bar.
- **< 0.80 → review queue.** A table for Alex: topic, top-3 candidate clusters with scores, and a "none fits / new theme" option.
  Alex's picks are written as `human`.

**Why kNN over the curated set, not cluster centroids or an LLM:**
- The 145 curated assignments *are* the taxonomy's definition. kNN generalises from Alex's own curation
  instead of from a one-line cluster description.
- 94 of the 102 unassigned topics have no real description (name only). An LLM gains little on a bare name,
  costs per call, and isn't reproducible. kNN with a confidence gate is honest about the same uncertainty.
- Fallback if precision is poor (see W2 validation): an LLM pass on the review queue only, with Alex choosing the model and spend.

**Where it runs:**
1. **Backfill (once):** score all 102. Auto-assign the confident ones and hand Alex the queue. Attended-linked topics (33) go first.
2. **Ongoing (two hooks):**
   - Nightly, as a step in `mi-2b-nightly-healthcheck.yml` *before* `topic_intel_compute.py --apply`, so the same
     night's trends include the new topic.
   - Optionally at `/post-event-content` Step 3.8, to show the proposed theme in the run summary. This is a nice-to-have;
     the nightly step is enough.

**Validation before trusting it (the null baseline):** hold out 30 of the 145 curated topics, assign them blind,
and measure agreement with Alex's original choice. Compare against two do-nothing baselines: always-largest-cluster,
and random weighted by cluster size. Ship only if auto-assigned precision at ≥ 0.80 confidence is ≥ 90% and clearly beats both.

### W3. Turn the detector into an alarm

- In `healthcheck_2b.py`, add a coverage layer (layer 5) that reads `topic_intelligence_health`, plus a direct count:
  - **FAIL** (opens the nightly issue): any topic tagged on an attended event has been unassigned for more than 2 days
    (the nightly assigner should have caught it, so this means the assigner is broken).
  - **FLAG** (warning): the review queue has more than 10 topics, or any `trip` status in the view.
- Re-baseline the `canonicalization_backlog` threshold once the backfill lands.

### W4. Diagnose the 7 events with zero topic tags

- For each, check whether the Notion Event row has Topics relations and whether `/post-event-content` Step 3.8
  (`substrate.py ensure-entity`) ever ran. Expect two buckets: webinars never run post-event (a decision: should they
  count as `attended`?), and runs that skipped topic linking (a defect).
- Output: a short finding, plus either a backfill manifest or a Linear decision issue for Alex.

### 4.4 Open question: `granularity_insufficient` = 1.000

Every month-window theme is `insufficient_data`. Some of that may be this gap, since fewer counted events means
thinner windows. Some may be genuine sparsity: about 3 attended events a week spread over 30 themes. Re-measure after
the backfill before touching the threshold or the taxonomy.

## 5. What we considered and rejected

| Option | Why not |
|---|---|
| Compute trends per topic and drop clusters | Removal was considered first. Topic-level counts are too sparse: most topics appear at 1–2 events, so every trend would be `insufficient_data`. Clusters exist to pool signal. |
| Re-run the full bootstrap clustering (re-cluster all 272) | It would churn the 145 curated assignments, break trend history continuity, and need a new calibration. Reserve it for a deliberate taxonomy revision (v2) if W2's review queue shows themes don't fit. |
| LLM assigns every new topic | Paid, non-deterministic, and little to work on for name-only topics. Kept as the fallback for the review queue only. |
| Assign inside `substrate.py` at create time only | Misses topics created outside post-event (research briefs, the market lane, or untagged: about 69 of the 102). The nightly step catches every source. |

## 6. Taxonomy drift: when to add a theme

If the review queue keeps getting "none fits" for related topics, that's a signal for a new theme, not a defect.
Rule: three or more "none fits" topics that Alex judges coherent → a proposed new `topic_cluster` row
(`curation_status = proposed`), which Alex approves. The taxonomy stays curated, so the system proposes and Alex decides.

## 7. Division of labour: Claude Code + Obvious

| Step | Builder | Reviewer | Gate |
|---|---|---|---|
| W1 allowlist diff + selftest | Obvious | Claude (code) | **Alex reviews** (guard file) |
| W2 assigner script + holdout validation report | Obvious | Claude re-runs the validation independently | Precision bar in W2 |
| W2 backfill dry-run on twin, then prod dry-run (read-only) | Obvious (twin), Claude (prod read-only) | — | Alex approves the auto-assign list and works the review queue |
| W2 prod write | **Alex** (REST through `spine_client`, never MCP DML) | Claude verifies after | — |
| W3 health-check coverage layer | Claude (builds on the YED-297 PR #262 shape) | Obvious | Twin fixtures FAIL/FLAG as designed |
| W4 zero-tag diagnosis | Claude (read-only, Notion + SQL) | — | Findings to Alex |
| Nightly wiring (`mi-2b-nightly-healthcheck.yml`) | Obvious | Claude | Twin run green |

**Rules of engagement for Obvious** (from S-04):
- Twin only: `ytfzzsxcxxbejnowmkmk`. No prod credentials, no prod DDL or DML.
- One PR per workstream. PR titles reference YED-304.
- Don't self-merge. Claude reviews, Alex merges.
- Commit trailer `Co-authored-by: Obvious <obvious@obvious.ai>` only, with no personal-email "Human author" lines.

## 8. Definition of done

- `public.topic` has 0 unassigned topics tagged on attended events. Total unassigned ≤ the review queue, and Alex has seen the queue.
- All attended events since 6 Aug that carry topic tags contribute to at least one trend (target: 18 of 18 tagged events, up from 16).
- The W4 finding has been delivered, and the 7 zero-tag events have been resolved or turned into a decision.
- The nightly job fails if an attended-linked topic stays unassigned for more than 2 days. A twin fixture proves it.
- The holdout validation report is committed under `supabase/evidence/`.

## Appendix: queries (read-only)

```sql
-- unassigned by creation era
select (created_at >= '2026-07-18') after_jul17, count(*), count(cluster_id) from public.topic group by 1;
-- unassigned by the event kind they're tagged on
select e.kind, count(distinct t.id) from public.topic t
left join public.event_entity ee on ee.entity_id=t.id and ee.entity_type='topic'
left join public.event e on e.id=ee.event_id where t.cluster_id is null group by 1;
-- per attended event since 6 Aug: tags vs clustered tags
select e.event_date::date, e.title,
  count(ee.*) filter (where ee.role='tagged_topic') tags,
  count(ee.*) filter (where ee.role='tagged_topic' and t.cluster_id is not null) clustered
from public.event e left join public.event_entity ee on ee.event_id=e.id and ee.entity_type='topic'
left join public.topic t on t.id=ee.entity_id
where e.kind='attended' and e.event_date>='2026-08-06' group by 1,2 order by 1;
-- the tripwire that was already firing
select * from topic_intelligence.topic_intelligence_health;
```
