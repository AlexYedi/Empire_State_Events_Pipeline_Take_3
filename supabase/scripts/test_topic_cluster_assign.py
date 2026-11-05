#!/usr/bin/env python3
"""test_topic_cluster_assign.py — offline unit tests for the YED-304 W2 assigner.

Stdlib unittest; runnable without network and without the embedding model (the embedder is
mocked with synthetic fixtures). Covers the corrected fixed-taxonomy baseline method: the
kNN vote and confidence formula, leave-one-out evaluation, the (k, threshold) sweep with
Wilson 95% lower bounds, the do-nothing baselines (LOO form), the ship rule, the fixture
loader, and the twin-only connection guard.

Usage: python3 supabase/scripts/test_topic_cluster_assign.py   (or `python3 -m unittest`)
"""
import argparse
import json
import math
import os
import random
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import topic_cluster_assign as tca  # noqa: E402
import topic_intel_compute as tic  # noqa: E402  (the shared YED-312 read-only guard)


def topic(i, cluster_id=None, name=None, description=None):
    return tca.Topic(id=f"00000000-0000-0000-0000-{i:012d}", name=name or f"topic {i}",
                     description=description, cluster_id=cluster_id,
                     cluster_assigned_by="llm" if cluster_id else None,
                     cluster_assignment_confidence=0.9 if cluster_id else None)


def unit(x, y, z=0.0):
    n = (x * x + y * y + z * z) ** 0.5
    return [x / n, y / n, z / n]


def dims(*leading):
    """A real 384-dim vector (the pinned model's width) with the given leading components."""
    return list(leading) + [0.0] * (tca.EMBED_DIM - len(leading))


class MockEmbedder:
    """Deterministic fake: fixed vectors per text, fails loud on unknown text."""

    def __init__(self, table):
        self.table = table

    def embed(self, texts):
        return [list(self.table[t]) for t in texts]


class TestTopicText(unittest.TestCase):
    def test_name_only_is_the_corrected_basis(self):
        self.assertEqual(tca.topic_text("Agent tooling", None), "Agent tooling")
        self.assertEqual(tca.topic_text("Agent tooling", ""), "Agent tooling")

    def test_description_joins_with_newline_when_present(self):
        self.assertEqual(tca.topic_text("Agent tooling", "frameworks"),
                         "Agent tooling\nframeworks")


class TestCosine(unittest.TestCase):
    def test_identical_orthogonal_opposite(self):
        self.assertAlmostEqual(tca.cosine([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(tca.cosine([1, 0], [0, 1]), 0.0)
        self.assertAlmostEqual(tca.cosine([1, 0], [-1, 0]), -1.0)

    def test_scale_invariant(self):
        self.assertAlmostEqual(tca.cosine([2, 0], [8, 0]), 1.0)

    def test_zero_vector_is_safe(self):
        self.assertEqual(tca.cosine([0, 0], [1, 1]), 0.0)

    def test_dimension_mismatch_refused(self):
        with self.assertRaises(ValueError):
            tca.cosine([1, 0], [1, 0, 0])

    def test_l2_normalize(self):
        self.assertAlmostEqual(sum(x * x for x in tca.l2_normalize([3, 4])), 1.0)
        self.assertEqual(tca.l2_normalize([0, 0]), [0.0, 0.0])


class TestKnnVote(unittest.TestCase):
    def test_confidence_is_share_times_top1(self):
        # a (c1, sim 1.0) + c (c1, sim 0.6) vs b (c2, sim 0.8): c1 wins on mass 1.6/2.4.
        res = tca.knn_vote([1, 0], [("a", "c1", [1, 0]), ("b", "c2", [0.8, 0.6]),
                                    ("c", "c1", [0.6, 0.8])], k=3)
        self.assertAlmostEqual(res.confidence, (1.6 / 2.4) * 1.0)
        self.assertEqual(res.winning_cluster_id, "c1")
        self.assertAlmostEqual(res.top1_similarity, 1.0)

    def test_k_truncates_neighbours(self):
        # k=1 must ignore the second, weaker c1 neighbour: vote mass is c1's alone.
        res = tca.knn_vote([1, 0], [("a", "c1", [1, 0]), ("b", "c2", [0.8, 0.6])], k=1)
        self.assertEqual(res.winning_cluster_id, "c1")
        self.assertAlmostEqual(res.ranked[0].vote_share, 1.0)

    def test_ties_break_lexicographically(self):
        res = tca.knn_vote([1, 0], [("a", "c2", [1, 0]), ("b", "c1", [1, 0])], k=2)
        self.assertEqual(res.winning_cluster_id, "c1")

    def test_ranked_is_share_desc_top3_for_review_queue(self):
        res = tca.knn_vote([1, 0], [("a", "c1", [1, 0]), ("b", "c2", [0.8, 0.6]),
                                    ("c", "c3", [0.6, 0.8]), ("d", "c1", [0.9, 0.1])], k=4)
        self.assertEqual([cv.cluster_id for cv in res.ranked[:3]], ["c1", "c2", "c3"])
        self.assertTrue(all(a.vote_share >= b.vote_share
                            for a, b in zip(res.ranked, res.ranked[1:])))

    def test_zero_similarity_mass_falls_back_to_count_shares(self):
        res = tca.knn_vote([1, 0], [("a", "c1", [0, 1]), ("b", "c2", [0, 1])], k=2)
        self.assertAlmostEqual(res.confidence, 0.0)  # top-1 sim is 0 → confidence 0
        self.assertAlmostEqual(res.ranked[0].vote_share, 0.5)  # uniform, not NaN

    def test_empty_neighbours_refused(self):
        with self.assertRaises(ValueError):
            tca.knn_vote([1, 0], [], k=3)


class TestLeaveOneOut(unittest.TestCase):
    def test_separated_clusters_classify_perfectly(self):
        topics = [topic(i, f"c{i % 3}") for i in range(12)]
        vecs = {t.id: [float(t.cluster_id == "c0"), float(t.cluster_id == "c1"),
                       float(t.cluster_id == "c2")] for t in topics}
        rows = tca.leave_one_out(topics, vecs)
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(r.correct for r in rows))

    def test_excludes_self_from_its_own_neighbourhood(self):
        # A single-member cluster's topic can never be correctly LOO-classified by
        # similarity (its own cluster is not in the training pool).
        topics = [topic(1, "solo"), topic(2, "c1"), topic(3, "c1")]
        vecs = {t.id: unit(*((1, 0, 0) if t.cluster_id == "solo" else (0, 1, 0)))
                for t in topics}
        rows = tca.leave_one_out(topics, vecs)
        solo = next(r for r in rows if r.topic.cluster_id == "solo")
        self.assertFalse(solo.correct)
        self.assertEqual(solo.result.winning_cluster_id, "c1")

    def test_ties_break_deterministically(self):
        topics = [topic(1, "c-b"), topic(2, "c-a")]
        vecs = {topics[0].id: [1.0, 0.0], topics[1].id: [0.0, 1.0]}
        rows = tca.leave_one_out(topics, vecs)
        self.assertEqual(rows[0].result.winning_cluster_id, "c-a")

    def test_k_actually_changes_the_neighbourhood(self):
        """Regression: leave_one_out must pass k through to the vote, not evaluate every
        sweep point on one silently-fixed k."""
        # q's cluster-mate at cos 0.90; five c2 neighbours at cos 0.70 each. k=1: the mate
        # votes alone → c1 correct. k=7: c2 out-masses c1 (5×0.70 > 0.90) → wrong.
        at_cos = lambda c: [c, math.sqrt(1 - c * c)]
        topics = [topic(1, "c1"), topic(2, "c1")] + [topic(i, "c2") for i in range(3, 8)]
        vecs = {t.id: (at_cos(0.90) if t.id == topics[0].id else
                       at_cos(0.90) if t.cluster_id == "c1" else at_cos(0.70))
                for t in topics}
        at_k1 = tca.leave_one_out(topics, vecs, k=1)[0]
        at_k7 = tca.leave_one_out(topics, vecs, k=7)[0]
        self.assertTrue(at_k1.correct)
        self.assertFalse(at_k7.correct)
        self.assertNotEqual(at_k1.result.confidence, at_k7.result.confidence)


class TestWilson(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(tca.wilson_lower_bound(0, 10), 0.0)
        self.assertAlmostEqual(tca.wilson_lower_bound(9, 10), 0.5958, places=3)
        self.assertAlmostEqual(tca.wilson_lower_bound(17, 17), 0.8157, places=3)

    def test_empty_trial_set_is_zero(self):
        self.assertEqual(tca.wilson_lower_bound(0, 0), 0.0)

    def test_lower_bound_is_below_raw_precision(self):
        for s, n in ((9, 10), (30, 33), (150, 160)):
            self.assertLess(tca.wilson_lower_bound(s, n), s / n)


class TestEvalPointAndShipRule(unittest.TestCase):
    @staticmethod
    def rows(confidences, corrects):
        return [tca.Loorow(topic(i, f"c{i % 2}"),
                           tca.VoteResult(f"c{i % 2}", c, 0.95, ()), ok)
                for i, (c, ok) in enumerate(zip(confidences, corrects))]

    def test_eval_point_splits_auto_from_review(self):
        rows = self.rows([0.9, 0.9, 0.9, 0.5, 0.5], [True, True, False, True, False])
        p = tca.eval_point(7, 0.80, rows)
        self.assertEqual(p.n_auto, 3)
        self.assertEqual(p.correct_auto, 2)
        self.assertAlmostEqual(p.precision_auto, 2 / 3)
        self.assertAlmostEqual(p.coverage_auto, 0.6)
        self.assertLess(p.wilson_lo, 2 / 3)

    def test_no_auto_assignments(self):
        p = tca.eval_point(7, 0.99, self.rows([0.5], [True]))
        self.assertIsNone(p.precision_auto)
        self.assertEqual(p.wilson_lo, 0.0)

    def test_ship_rule_takes_lowest_qualifying_threshold(self):
        # Everything correct: qualifies from 0.50 up — the rule must pick the LOWEST bar.
        rows = self.rows([0.9] * 10, [True] * 10)
        points = [tca.eval_point(7, thr, rows) for thr in tca.SWEEP_THRESHOLDS]
        ship = tca.choose_ship_point(points, baseline_floor=0.30)
        self.assertIsNotNone(ship)
        self.assertEqual(ship.threshold, 0.50)
        self.assertAlmostEqual(ship.coverage_auto, 1.0)

    def test_ship_rule_fails_when_cannot_beat_baseline_floor(self):
        rows = self.rows([0.9] * 10, [True] * 9 + [False])
        points = [tca.eval_point(7, thr, rows) for thr in tca.SWEEP_THRESHOLDS]
        # precision 0.9 raw, but 9/10 Wilson lo ≈ 0.545 — an 0.60 floor must fail it
        self.assertIsNone(tca.choose_ship_point(points, baseline_floor=0.60))
        ship = tca.choose_ship_point(points, baseline_floor=0.54)
        self.assertIsNotNone(ship)

    def test_ship_rule_prefers_highest_coverage_across_k(self):
        rows_low = self.rows([0.9] * 10, [True] * 10)          # everything confident
        points = [tca.eval_point(1, 0.50, rows_low)]
        rows_sparse = self.rows([0.9] * 4 + [0.4] * 6, [True] * 10)
        points += [tca.eval_point(7, 0.50, rows_sparse)]
        ship = tca.choose_ship_point(points, baseline_floor=0.30)
        self.assertEqual(ship.k, 1)  # coverage 1.0 beats 0.4

    def test_baseline_floor_comes_from_the_worse_baseline(self):
        rows = self.rows([0.9] * 10, [True] * 10)
        points = [tca.eval_point(7, thr, rows) for thr in tca.SWEEP_THRESHOLDS]
        self.assertIsNone(tca.choose_ship_point(points, baseline_floor=0.999))


class TestBaselines(unittest.TestCase):
    def test_always_largest_loo_scores_against_the_mode(self):
        assigned = [topic(1, "c1"), topic(2, "c1"), topic(3, "c2")]
        # trial 1: train {c1, c2} → c1 ✓; trial 2: {c1, c2} → c1 ✓; trial 3: {c1, c1} → c1 ✗
        self.assertAlmostEqual(tca.baseline_always_largest_loo(assigned), 2 / 3)

    def test_always_largest_loo_tie_breaks_lexicographically(self):
        assigned = [topic(1, "c2"), topic(2, "c1")]
        self.assertAlmostEqual(tca.baseline_always_largest_loo(assigned), 0.0)

    def test_size_weighted_random_loo_is_deterministic_per_seed(self):
        assigned = [topic(i, f"c{i % 3}") for i in range(9)]
        r1 = tca.baseline_size_weighted_random_loo(assigned, random.Random(7))
        r2 = tca.baseline_size_weighted_random_loo(assigned, random.Random(7))
        self.assertEqual(r1, r2)

    def test_size_weighted_random_tracks_cluster_sizes(self):
        assigned = [topic(i, "big") for i in range(90)] + [topic(99, "small")]
        rng = random.Random(3)
        for _ in range(20):  # every rep must land between 0 and 1 and favour 'big'
            p = tca.baseline_size_weighted_random_loo(assigned, rng)
            self.assertGreater(p, 0.85)
            self.assertLess(p, 1.0)


class TestRunScoring(unittest.TestCase):
    def setUp(self):
        # Three clusters with distinct directions; the ambiguous query sits between c1 and c2.
        self.vecs = {}
        assigned = []
        for i in range(4):
            t = topic(i, "c1", name=f"infra {i}")
            self.vecs[t.id] = unit(1, 0.02 * i, 0)
            assigned.append(t)
        for i in range(4, 8):
            t = topic(i, "c2", name=f"content {i}")
            self.vecs[t.id] = unit(0, 1, 0.02 * (i - 4))
            assigned.append(t)
        for i in range(8, 12):
            t = topic(i, "c3", name=f"jobs {i}")
            self.vecs[t.id] = unit(0, 0, 1)
            assigned.append(t)
        self.assigned = assigned
        self.confident = topic(20, None, name="vector database startup")
        self.ambiguous = topic(21, None, name="halfway topic")
        self.vecs[self.confident.id] = unit(1, 0.01, 0)
        self.vecs[self.ambiguous.id] = unit(0.5, 0.5, 0)

    def test_confident_and_ambiguous_split(self):
        assignments, review = tca.run_scoring(
            [self.confident, self.ambiguous], self.assigned, self.vecs, k=7,
            attended_ids=set())
        self.assertEqual([a.topic.id for a in assignments], [self.confident.id])
        self.assertEqual([r.topic.id for r in review], [self.ambiguous.id])
        item = review[0]
        self.assertTrue(1 <= len(item.candidates()) <= 3)  # up to top-3 candidates
        self.assertGreaterEqual(item.candidates()[0].vote_share,
                                item.candidates()[-1].vote_share)

    def test_threshold_parameter_moves_the_bar(self):
        assignments, _ = tca.run_scoring([self.confident], self.assigned, self.vecs, k=7,
                                         attended_ids=set(), threshold=0.99999)
        self.assertEqual(assignments, [])  # impossibly high bar → everything to review

    def test_attended_linked_sort_first(self):
        confident2 = topic(22, None, name="another confident one")
        self.vecs[confident2.id] = unit(1, 0.02, 0)
        assignments, review = tca.run_scoring(
            [self.confident, confident2, self.ambiguous], self.assigned, self.vecs, k=7,
            attended_ids={confident2.id, self.ambiguous.id})
        # attended-linked auto-assignments precede non-attended ones of any confidence
        self.assertEqual([a.topic.id for a in assignments],
                         [confident2.id, self.confident.id])
        # and the ambiguous attended-linked topic leads the review queue, flagged
        self.assertEqual(review[0].topic.id, self.ambiguous.id)
        self.assertTrue(review[0].attended_linked)


class TestTwinConnectionGuard(unittest.TestCase):
    """The twin-only connection guard: read-only probes must never point at prod."""

    def test_connection_guard_refuses_prod_and_foreign_hosts(self):
        with self.assertRaises(SystemExit):
            tca._check_twin_conn("host=db.oicikjyzmxqfomrrqkvf.supabase.co port=5432")
        with self.assertRaises(SystemExit):
            tca._check_twin_conn("host=db.evilpostgres.example.com port=5432")
        self.assertEqual(tca._check_twin_conn(tca.TWIN_CONN), tca.TWIN_CONN)

    def test_connection_guard_pooler_rules(self):
        # Pooler conns are accepted only with the twin project ref in the username.
        ok = ("host=aws-1-us-east-2.pooler.supabase.com port=5432 "
              f"user=postgres.{tca.TWIN_REF} dbname=postgres sslmode=require")
        self.assertEqual(tca._check_twin_conn(ok), ok)
        with self.assertRaises(SystemExit):  # pooler but the PROD ref in the username
            tca._check_twin_conn("host=aws-1-us-east-2.pooler.supabase.com port=5432 "
                                 f"user=postgres.{tca.PROD_REF} dbname=postgres")
        with self.assertRaises(SystemExit):  # pooler but no twin ref anywhere
            tca._check_twin_conn("host=aws-1-us-east-2.pooler.supabase.com port=5432 "
                                 "user=postgres dbname=postgres")
        with self.assertRaises(SystemExit):  # PROD ref smuggled in any position
            tca._check_twin_conn(f"host=db.{tca.TWIN_REF}.supabase.co user={tca.PROD_REF}")


class TestFixtureLoader(unittest.TestCase):
    def make_fixture(self, path):
        with open(path, "w") as f:
            json.dump({"source": "test", "generated_at": "2026-11-03T00:00:00Z", "topics": [
                {"id": "00000000-0000-0000-0000-000000000001", "name": "Assigned A",
                 "cluster_id": "00000000-0000-0000-0000-0000000000cc",
                 "cluster_assigned_by": "llm", "attended_linked": True},
                {"id": "00000000-0000-0000-0000-000000000002", "name": "Backlog B",
                 "cluster_id": None, "cluster_assigned_by": None, "attended_linked": False}],
                "clusters": [{"cluster_id": "00000000-0000-0000-0000-0000000000cc",
                              "name": "Cluster CC", "slug": "cc"}]}, f)

    def test_loads_name_only_topics_attended_and_clusters(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "fx.json")
            self.make_fixture(p)
            fx = tca.load_fixture(p)
        self.assertEqual(len(fx.topics), 2)
        self.assertTrue(all(t.description is None for t in fx.topics))  # name-only by design
        self.assertEqual(fx.topics[0].cluster_assigned_by, "llm")
        self.assertEqual(fx.attended_ids, {"00000000-0000-0000-0000-000000000001"})
        self.assertEqual(fx.clusters["00000000-0000-0000-0000-0000000000cc"]["name"], "Cluster CC")

    def test_empty_fixture_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "fx.json")
            with open(p, "w") as f:
                json.dump({"topics": [], "clusters": []}, f)
            with self.assertRaises(RuntimeError):
                tca.load_fixture(p)

    def test_cluster_label_handles_both_name_shapes(self):
        self.assertEqual(tca.cluster_label("cc", {"cc": {"name": "Named"}}), "Named")
        self.assertEqual(tca.cluster_label("cc", {"cc": "Also named"}), "Also named")
        self.assertEqual(tca.cluster_label("cc", {}), "cluster cc")


class TestEmbedTopics(unittest.TestCase):
    def test_maps_vectors_to_topics(self):
        topics = [topic(1), topic(2)]
        vecs = tca.embed_topics(topics, MockEmbedder({
            "topic 1": dims(1, 0), "topic 2": dims(0, 1)}))
        self.assertEqual(set(vecs), {t.id for t in topics})

    def test_embeds_name_plus_description_when_present(self):
        topics = [tca.Topic("id-1", "Agentic AI", "autonomous systems", None, None, None)]
        vecs = tca.embed_topics(topics, MockEmbedder({"Agentic AI\nautonomous systems": dims(1.0)}))
        self.assertEqual(vecs["id-1"], dims(1.0))

    def test_unknown_text_fails_loud(self):
        with self.assertRaises(KeyError):
            tca.embed_topics([topic(1)], MockEmbedder({}))

    def test_wrong_dimension_refused(self):
        with self.assertRaises(RuntimeError):
            tca.embed_topics([topic(1)], MockEmbedder({"topic 1": [1.0]}))

    def test_wrong_count_refused(self):
        class TwoVectors(MockEmbedder):
            def embed(self, texts):
                return [[1.0], [2.0]]

        with self.assertRaises(RuntimeError):
            tca.embed_topics([topic(1)], TwoVectors({}))


class TestTombstoneFilter(unittest.TestCase):
    def test_fragment_matches_the_postgres_json_operator(self):
        self.assertIn("?", tca.TOMBSTONE_FILTER)
        self.assertIn("merged_into", tca.TOMBSTONE_FILTER)
        self.assertIn("not", tca.TOMBSTONE_FILTER)
        # NULL metadata must not drop a row: the 0016 coalesce idiom.
        self.assertIn("coalesce", tca.TOMBSTONE_FILTER)


TWIN_CSV_COLS = {"id", "name", "cluster_id", "cluster_assigned_by",
                 "cluster_assignment_confidence", "metadata"}


def fake_twin_psql(csv_text):
    """Replace tca.psql / tca.twin_topic_columns with a canned twin response. The fake records
    every SQL string it is asked to run — the fetch-repoint regression asserts on them."""
    orig = (tca.psql, tca.twin_topic_columns)

    def fake(sql, *a, **k):
        fake.calls.append(sql)
        return csv_text

    fake.calls = []
    tca.twin_topic_columns = lambda *a, **k: set(TWIN_CSV_COLS)
    tca.psql = fake
    return orig


class TestFetchTopicsTwin(unittest.TestCase):
    """Twin CSV parse: psql --csv renders NULL as the empty string, so the merge-tombstone
    exclusion must test falsiness, not `is None`. Regression for the 2026-11-05 dry-run,
    where the `is None` form silently kept 12 tombstones in the unassigned pool."""

    CSV = (
        "id,name,cluster_id,cluster_assigned_by,cluster_assignment_confidence,metadata\n"
        '"11111111-1111-1111-1111-111111111111","assigned topic",'
        '"c0000000-0000-0000-0000-000000000001","llm",0.900,"{}"\n'
        '"22222222-2222-2222-2222-222222222222","live unassigned",,,,\n'
        '"33333333-3333-3333-3333-333333333333","merged away",,,,'
        '"{""merged_into"": ""aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa""}"\n'
        '"44444444-4444-4444-4444-444444444444","merged but clustered",'
        '"c0000000-0000-0000-0000-000000000001","session",0.950,'
        '"{""merged_into"": ""aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa""}"\n'
    )

    def setUp(self):
        self._orig = fake_twin_psql(self.CSV)

    def tearDown(self):
        tca.psql, tca.twin_topic_columns = self._orig

    def load(self):
        return tca.fetch_topics_twin("not-a-real-password")

    def test_tombstone_is_excluded(self):
        topics, meta = self.load()
        # exactly three parse: assigned, live unassigned, merged-but-clustered
        self.assertEqual(len(topics), 3)
        self.assertEqual(meta["tombstones_excluded"], 1)
        self.assertNotIn("33333333-3333-3333-3333-333333333333", {t.id for t in topics})

    def test_fetch_queries_public_topic(self):
        # The repoint regression: the fetch must read public.topic (canonical_v2 is gone
        # post-swap) — a re-repoint to the legacy schema must fail here.
        self.load()
        self.assertEqual(len(tca.psql.calls), 1)
        self.assertIn(f"from {tca.TWIN_TOPIC_SCHEMA}.topic", tca.psql.calls[0])
        self.assertNotIn("canonical_v2", " ".join(tca.psql.calls))

    def test_null_cluster_parses_to_none_and_stays_in_pool(self):
        topics, _ = self.load()
        live = next(t for t in topics if t.id == "22222222-2222-2222-2222-222222222222")
        self.assertIsNone(live.cluster_id)
        self.assertIsNone(live.cluster_assigned_by)

    def test_merged_but_clustered_row_stays_assigned(self):
        # A tombstone marker on a row that still carries a cluster is an assigned row:
        # the exclusion is for the unassigned pool only.
        topics, meta = self.load()
        self.assertEqual(meta["tombstones_excluded"], 1)
        kept = next(t for t in topics if t.id == "44444444-4444-4444-4444-444444444444")
        self.assertEqual(kept.cluster_id, "c0000000-0000-0000-0000-000000000001")

    def test_empty_confidence_parses_to_none(self):
        topics, _ = self.load()
        live = next(t for t in topics if t.id == "22222222-2222-2222-2222-222222222222")
        self.assertIsNone(live.cluster_assignment_confidence)


class TestMergedIntoParsing(unittest.TestCase):
    """The tombstone test parses metadata JSON; substring and is-null forms drop live rows.
    Regression for review finding Major-2 on PR #306."""

    @staticmethod
    def run_with(metadata_json: str | None):
        # psql --csv renders NULL as the empty string — mirror that here.
        meta_col = "" if metadata_json is None else f'"{metadata_json.replace(chr(34), chr(34) * 2)}"'
        csv_text = (
            "id,name,cluster_id,cluster_assigned_by,cluster_assignment_confidence,metadata\n"
            f'"55555555-5555-5555-5555-555555555555","probe topic",,,,{meta_col}\n'
        )
        orig = fake_twin_psql(csv_text)
        try:
            return tca.fetch_topics_twin("not-a-real-password")
        finally:
            tca.psql, tca.twin_topic_columns = orig

    def test_reverted_merge_is_kept(self):
        # substrate.py merge --revert pops merged_into but appends merge_history: the topic
        # is live and unassigned, and a substring match on "merged_into" hid it.
        topics, meta = self.run_with('{"merge_history": [{"merged_into": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}]}')
        self.assertEqual(meta["tombstones_excluded"], 0)
        self.assertEqual(len(topics), 1)

    def test_null_merged_into_is_kept(self):
        topics, meta = self.run_with('{"merged_into": null}')
        self.assertEqual(meta["tombstones_excluded"], 0)
        self.assertEqual(len(topics), 1)

    def test_null_metadata_is_kept(self):
        topics, meta = self.run_with(None)
        self.assertEqual(meta["tombstones_excluded"], 0)
        self.assertEqual(len(topics), 1)

    def test_malformed_metadata_is_kept(self):
        # Not a tombstone we can prove: keep the row rather than silently shrinking the pool.
        topics, meta = self.run_with("not json at all")
        self.assertEqual(meta["tombstones_excluded"], 0)
        self.assertEqual(len(topics), 1)

    def test_live_tombstone_is_excluded(self):
        csv_text = (
            "id,name,cluster_id,cluster_assigned_by,cluster_assignment_confidence,metadata\n"
            '"22222222-2222-2222-2222-222222222222","live unassigned",,,,\n'
            '"55555555-5555-5555-5555-555555555555","tombstone",,,,'
            '"{""merged_into"": ""aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa""}"\n'
        )
        orig = fake_twin_psql(csv_text)
        try:
            topics, meta = tca.fetch_topics_twin("not-a-real-password")
        finally:
            tca.psql, tca.twin_topic_columns = orig
        self.assertEqual(meta["tombstones_excluded"], 1)
        self.assertEqual(len(topics), 1)


class TestReadOnlyGuard(unittest.TestCase):
    """psql() runs every twin query inside the shared YED-312 read-only transaction and
    discards output without an 'on' verdict. Regression for review finding Major-1."""

    def test_argv_reuses_the_shared_guard(self):
        argv = tca.guarded_psql_argv("psql", "conn", "select 1")
        self.assertEqual(argv[:2], ["psql", "conn"])
        self.assertEqual(argv[-2:], ["-c", "rollback;"])
        self.assertIn(tic.RO_ASSERT, argv)
        commands = [argv[i + 1] for i, a in enumerate(argv) if a == "-c"]
        self.assertEqual(commands[0], "begin read only;")
        self.assertEqual(commands[1], "show transaction_read_only;")
        self.assertEqual(commands[2], tic.RO_ASSERT)
        self.assertEqual(commands[3], "select 1")
        self.assertEqual(commands[-1], "rollback;")

    def test_guard_matches_topic_intel_compute_ro_argv_shape(self):
        argv = tca.guarded_psql_argv("psql", "conn", "select 1")
        ro = tic.ro_argv("psql", "conn", "select 1")
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "-c"],
                         [ro[i + 1] for i, a in enumerate(ro) if a == "-c"])

    @staticmethod
    def fake_run(stdout, rc=0):
        result = types.SimpleNamespace(returncode=rc, stdout=stdout, stderr="")

        def run(argv, **k):
            result.argv = argv
            return result

        return run

    def test_output_without_an_on_verdict_is_discarded(self):
        orig = tca.subprocess.run
        tca.subprocess.run = self.fake_run("transaction_read_only\noff\nid,name\nx,y\n")
        try:
            with self.assertRaises(RuntimeError):
                tca.psql("select 1", "pw")
        finally:
            tca.subprocess.run = orig

    def test_unexpected_show_shape_fails_closed(self):
        orig = tca.subprocess.run
        tca.subprocess.run = self.fake_run("BEGIN\non\nid,name\n")
        try:
            with self.assertRaises(RuntimeError):
                tca.psql("select 1", "pw")
        finally:
            tca.subprocess.run = orig

    def test_guarded_output_strips_the_verdict_lines(self):
        orig = tca.subprocess.run
        tca.subprocess.run = self.fake_run("transaction_read_only\non\nid,name\nx,y\n")
        try:
            self.assertEqual(tca.psql("select 1", "pw"), "id,name\nx,y\n")
        finally:
            tca.subprocess.run = orig


class TestCheckTwin(unittest.TestCase):
    """--check-twin exit codes: a required schema without cluster_id fails; a legacy probe
    that cannot run is informational only. Regression for review finding Minor-4."""

    @staticmethod
    def run_check(cols_by_schema, legacy_raises=False):
        def cols(password, psql_bin, schema):
            if legacy_raises and schema != tca.TWIN_TOPIC_SCHEMA:
                raise RuntimeError("no such table")
            return cols_by_schema.get(schema, set())

        def fake_psql(sql, *a, **k):
            if " as n" in sql:
                return "n\n5\n"
            if " as assigned" in sql:
                return "assigned\n3\n"
            if " as tomb" in sql:
                return "tomb\n1\n"
            return "links\n7\n"

        orig = (tca.twin_topic_columns, tca.psql, tca.fetch_event_links)
        tca.twin_topic_columns = cols
        tca.psql = fake_psql
        tca.fetch_event_links = lambda *a, **k: {"topic_event_links": 7, "attended_topic_ids": set()}
        try:
            return tca.run_check_twin("not-a-real-password", argparse.Namespace(psql_bin="psql"))
        finally:
            tca.twin_topic_columns, tca.psql, tca.fetch_event_links = orig

    def test_required_schema_without_cluster_id_fails(self):
        rc = self.run_check({tca.TWIN_TOPIC_SCHEMA: {"id", "name", "metadata"}})
        self.assertEqual(rc, 1)

    def test_legacy_probe_failure_is_informational(self):
        full = {"id", "name", "cluster_id", "cluster_assigned_by", "cluster_assignment_confidence",
                "metadata", "description", "created_at"}
        rc = self.run_check({tca.TWIN_TOPIC_SCHEMA: full, "canonical_v2": set()}, legacy_raises=True)
        self.assertEqual(rc, 0)

    def test_healthy_twin_passes(self):
        full = {"id", "name", "cluster_id", "cluster_assigned_by", "cluster_assignment_confidence",
                "metadata", "description", "created_at"}
        rc = self.run_check({tca.TWIN_TOPIC_SCHEMA: full, "canonical_v2": set()})
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
