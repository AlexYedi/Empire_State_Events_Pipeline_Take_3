# Increment 2b — `relations` → `event_entity` semantic-mapping spec

**Status:** DRAFT for review (the "reviewed spec FIRST" gate — PRD AC2b.3, DoD #5, pre-mortem fix #4).
**Linear:** YED-130 · **Depends on:** 2a crosswalks (`0004_increment_2a_link.sql`, applied), `topic_cluster` + `topic.cluster_id` (2b, AC2b.2).
**Naming:** *Empire prod DB* = `oicikjyzmxqfomrrqkvf`; *Phantom Test Case DB* = `ytfzzsxcxxbejnowmkmk`. "canonical" = master record only.

> **Why this doc exists.** The gtm `compute_topic_intelligence` runs over gtm's polymorphic typed-edge table `signal.relations`. Empire has **no `relations` table** — its event graph is the hyperedge `public.event_entity(event_id, entity_type, entity_id, role)`. If we rewrite the compute by mechanical find-replace without pinning the semantics, the function will run clean and emit a **structurally-valid-but-empty** snapshot (the silent-failure trap). This spec pins, edge by edge, what each `relations` read *means* and how it is expressed in `event_entity`, so the rewrite is a faithful port and the invariant suite has a definition to check against.

---

## 1. What the compute actually reads (measured from the source)

`gtm-os/scripts/topic_intelligence/compute_topic_intelligence.sql` reads **exactly three edge shapes** from `signal.relations` plus two dimensions. Nothing else in `relations` touches the computation:

| # | gtm `relations` predicate | Meaning | Used for |
|---|---|---|---|
| E1 | `relation_type='tagged_topic' AND from_type='event' AND to_type='topic' AND is_active` | event **is tagged with** topic | cluster membership of an event (→ event_count, co-occurrence) |
| E2 | `relation_type IN ('speaker_at','host_of','panelist_at') AND from_type='entity' AND to_type='event' AND is_active` | person **spoke/hosted/paneled at** event | distinct_speaker_count + bridges |
| D1 | `events.event_date` | when the event happened | windowing (month/week/all_time) |
| D2 | `topics.cluster_id` | topic → theme rollup | subject grain (`subject_level='cluster'`) |

**Not read by the compute** (so not on the critical path for the recompute, though they still re-ingest as edges): `attended`, `works_at`, `co_event`, `related_topic`. Note especially: **`attended` is NOT a speaker edge** — an attendee never counts toward `distinct_speaker_count` or a bridge. Preserve that exclusion exactly.

---

## 2. The edge mapping (`relations` → `event_entity`)

`event_entity` is a hyperedge from an event to a participating entity, discriminated by `(entity_type, role)`. The `unique(event_id, entity_type, entity_id, role)` constraint is the dedup key. Re-ingest (AC2b.1) translates each gtm edge as follows, re-keying gtm UUIDs → Empire ids via the 2a crosswalks (`topic_crosswalk`, `entity_crosswalk`):

| gtm `relations` edge | gtm shape | → Empire `event_entity` row | Empire id source |
|---|---|---|---|
| `tagged_topic` | event → topic | `(event_id, entity_type='topic', entity_id=<empire topic id>, role='tagged_topic')` | `topic_crosswalk` (145) + 25 inserted gtm-only topics |
| `speaker_at` | person → event | `(event_id, entity_type='person', entity_id=<empire person id>, role='speaker')` | `entity_crosswalk` |
| `host_of` | person → event | `(event_id, entity_type='person', entity_id=<empire person id>, role='host')` | `entity_crosswalk` |
| `panelist_at` | person → event | `(event_id, entity_type='person', entity_id=<empire person id>, role='panelist')` | `entity_crosswalk` |
| `attended` | person → event | `(event_id, entity_type='person', entity_id=<empire person id>, role='attendee')` | `entity_crosswalk` |
| `works_at` | person → company | **NOT an `event_entity` row** → `public.person.company_id = <empire company id>` FK | `entity_crosswalk` (both sides) |
| `co_event` | event → event | dropped (derivable; not consumed by compute) | — |
| `related_topic` | topic → topic | dropped (topic-topic; not consumed by compute) | — |

**Role vocabulary (the reviewed "role-vocab expansion" AC2b.1 asks for):** the Empire `event_entity.role` values become the closed set `{'tagged_topic','speaker','host','panelist','attendee'}`. The **speaker set** for the compute is `role IN ('speaker','host','panelist')` — the exact image of gtm's `('speaker_at','host_of','panelist_at')`. `attendee` is deliberately excluded from that set.

---

## 3. The two semantic questions AC2b.3 requires answered

**Q1 — What is a "co-occurrence" in the `event_entity` model?**
Two clusters co-occur when a **single event is tagged with a topic in cluster A and a topic in cluster B**. In `event_entity`: self-join the `role='tagged_topic'` rows on `event_id`, roll each `entity_id` (topic) up to its `cluster_id` via `public.topic`, keep pairs with `cluster_a < cluster_b`, count **distinct events**. Identical semantics to gtm's `cluster_events ⋈ cluster_events ON event_id` — only the substrate changes.

**Q2 — Does `role` weight or filter edges?**
It **filters**, never weights (the gtm math is unweighted counts). Two gates:
- topic tagging = `entity_type='topic' AND role='tagged_topic'`
- speaker set = `entity_type='person' AND role IN ('speaker','host','panelist')`
No role multiplies a count. The only "weighting" in the math is the fixed `intersection_score = cooc + 2·bridge + 2·novelty_bonus`, which is unchanged and lives in the score formula, not the edge read.

**The bridge rule carries verbatim.** A bridge person must be in the speaker set at **two DISTINCT events** — one whose tags reach cluster A, another (different `event_id`) whose tags reach cluster B. A single dual-tagged event does **not** make its speakers bridge that pair (that is co-occurrence). This is gtm's 2026-08-07 bridge-inflation fix (`event_id <> event_id` join predicate); reproduce it exactly, and `bridge_person_count = cardinality(bridge_entity_ids)` via `array_agg(distinct …)`.

---

## 4. The math that must NOT change (port verbatim)

Carry these from `compute_topic_intelligence.sql` unchanged — only the FROM/JOIN substrate moves to `event_entity`:
- **Windows:** `month`=30d, `week`=7d, `all_time`=null. Prior window = the same-length window immediately preceding (NULL for all_time).
- **`event_date` handling:** Empire `event.event_date` is `timestamptz`; gtm's is `date`. **Cast to `date`** for every window boundary comparison (`e.event_date::date >= p_as_of - make_interval(days => w.days)`), so a same-day event is not excluded by a time component.
- **momentum** = `(ec - prior)/greatest(prior,1)`.
- **trend_label:** `ec<3 → insufficient_data`; `all_time → steady`; `prior=0 → new`; `momentum ≥ 0.5 → heating`; `≤ -0.5 → cooling`; else `steady`. *(This is the upstream vocab the hubs already map — heating→rising / cooling→falling / insufficient_data→steady in `UPSTREAM_TREND_MAP`. Keep the labels; the hub reconciliation stays valid.)*
- **is_low_confidence** = `ec<3 OR window='week'`.
- **novelty:** `first_cooccurred_on` = earliest shared-event date all-time; `is_new_pair` = first co-occ inside the window; `+2` score bonus when new.
- **content_hash:** same `md5(inputs)` recipe (idempotency/lineage). Inputs are the same scalars, now over Empire ids.
- **Write contract:** DELETE-by-`as_of_date` + INSERT in one txn, writer = owner/`service_role` (deny-all RLS eats the insert otherwise), reload not blind-upsert (stale-orphan-pair guard).

---

## 5. The one load-bearing decision — RESOLVED (grounded in the existing taxonomy; open to override)

**Scoping the recompute to the IRL event graph, not the trend-radar events.**

Empire `public.event` currently holds **17 `kind='market'` trend-radar signals** (a "market signal = an event" modeling choice from the base pipeline) with ~20 `event_entity` edges — a *different semantic* from the IRL speaker/host graph. After 2b re-ingest, `public.event` holds **both kinds** (market + IRL). If the recompute reads *all* `event_entity` topic tags, the 17 market signals' topic tags leak into cluster co-occurrence and inflate/distort the themes — conflating "this theme is heating at real events" with "a market-radar item mentioned this topic."

**Decision — GROUNDED in the existing taxonomy (not invented):** re-ingest the IRL events under the **existing `kind='attended'`** value and **scope every CTE of the recompute to `where e.kind='attended'`**. The base pipeline already documents this taxonomy (`.claude/references/market-intel-spine.md` §event): `attended` = *"Alex participates — meetups"* vs `market`/`funding`/`launch`/`exec_move` (happen *to* entities) vs `role_posted`/`application`/`interview` (job-lens). The re-ingested speaker/host/meetup graph **is** the `attended` semantic.

Why `attended`, not a new `community`/`irl` value:
- **Semantically exact** — `attended` is defined precisely as the meetup graph we're re-ingesting.
- **Inventing a kind would break live code** — `recompute_relevance.py:84` already queries `kind=eq.attended&event_date=gt.now` to reinforce relevance from upcoming meetups. A new value fragments meetups across two kinds and makes that query silently miss the re-ingested events. `attended` keeps the base pipeline whole and is the natural invariant boundary (`event_count` over `attended` events only).
- **Currently 0 rows** — `attended` is defined + queried but unpopulated (all 17 live events are `market`); the re-ingest is its first, intended populator.

**Alternatives considered:** (a) *no filter* — rejected, silently conflates trend-radar with meetup activity; (b) *a new `community`/`irl` kind* — rejected, ignores the existing taxonomy and breaks `recompute_relevance.py`; (c) *separate `irl_event` table* — rejected, re-introduces the schema fork 2b is collapsing and complicates the atomic swap. One shared `event` table + the existing `kind` discriminator is the best-of-both.

**Second, smaller decision — cluster identity:** carry gtm's `topic_cluster.cluster_id` **UUIDs verbatim** into Empire's new `topic_cluster` (the 30 themes are curated work product; their ids are stable identity). Then `public.topic.cluster_id` and `topic_trend.subject_id` reuse those UUIDs, so the Increment-1 carried `signal_read` grain stays resolvable across the swap. *(Recommendation: yes, carry verbatim — 90%, high.)*

---

## 6. Invariants this mapping licenses (feed AC2b.4)

Because the semantics are pinned, the invariant suite can assert:
1. **Conservation:** every cluster with ≥1 IRL event in a window appears in `topic_trend` for that window; every topic tagged on a counted event rolls to exactly one cluster.
2. **Monotonicity:** adding an IRL event never *decreases* any pair's `cooccurrence_event_count` (all_time).
3. **Symmetry / canonical order:** `subject_a_id < subject_b_id`; no self-pairs; `pair(A,B)` appears once.
4. **Bridge integrity:** `bridge_person_count = cardinality(bridge_entity_ids)`; every bridge person is in the speaker set (`role IN speaker/host/panelist`) at ≥2 distinct events spanning the two clusters.
5. **Kind isolation:** zero `event_entity` rows from `kind<>'attended'` events contribute to any `topic_trend`/`topic_pair_metric` row (guards the §5 decision).
6. **Zero-orphan:** every counted `event_entity.entity_id` resolves to a live, non-tombstoned Empire topic/person (via 2a merge-map).
7. **Golden cases:** 3 hand-built IRL events → hand-computed expected clusters/pairs match the SQL and the fresh reference impl.

---

## 7. Downstream build order (unchanged from ADR-4, gated on this spec being reviewed)
Review this spec → build `topic_cluster` + `topic.cluster_id` (AC2b.2) → re-ingest IRL events per §2 into `canonical_v2` (AC2b.1) → rewrite compute per §2–4 with the §5 kind-scope (AC2b.3) → invariants + fresh reference impl (§6, AC2b.4) → **full Phantom Test Case DB rehearsal + proven rollback** → atomic swap → decommission gate.
