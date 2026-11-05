#!/usr/bin/env python3
"""topic_cluster_assign.py — YED-304 W2: kNN embedding assigner for topic clusters.

The FIXED-TAXONOMY BASELINE study for the YED-304 clustering gap. Production path is on
hold pending the dynamic-taxonomy design review (PR #264); this script delivers the
corrected validation that any new design must beat. Spec: docs/proposals/2026-11-03-topic-
clustering-gap.md §4 W2, as corrected by the PR #264 review (comments 6614919600 series)
and Alex's data corrections (170 assigned, k sweep, tombstone backlog 94).

Method
  Embed topic NAMES ONLY with the pinned local model BAAI/bge-small-en-v1.5 (384-d, the
  model .claude/scripts/dockb_common.py pins), cosine similarity, deterministic. Name-only
  is deliberate: the fixture is name-only by design and 94 of 102 backlog topics have no
  description — validating on name+description would overstate backlog performance.
  For a query topic: take its k nearest ASSIGNED topics, vote per cluster weighted by
  similarity.
      confidence = winning cluster's vote share × top-1 similarity
  confidence >= threshold → auto-assign (cluster_assigned_by = 'embedding_auto')
  confidence <  threshold → review queue: topic, top-3 candidate clusters with scores,
                            plus a none-fits / new-theme option.

Modes
  --validate   Leave-one-out study over ALL curated assignments in the fixture: each topic
               is assigned blind with kNN over the other 169, swept over k in {1,3,5,7} and
               thresholds 0.50–0.90, scored against the always-largest-cluster and
               size-weighted-random baselines with Wilson 95% intervals. Writes ONLY the
               evidence report. Exit 0 = ship point found, 3 = GATE FAILED.
  --dry-run    (default) Score every unassigned topic against all curated assignments; emit
               the auto-assign list (attended-event-linked topics flagged first) and the
               review queue to supabase/evidence/. No writes. --source fixture (default,
               offline) or --source twin (read-only; excludes merge tombstones).
  --check-twin Read-only schema + row-count probe of the twin (public.topic and
               legacy schemas, tombstone counts, event links).

  The nightly write path (--apply, reviewed on PR #266) is intentionally absent pending the
  dynamic-taxonomy design review; its code shape is retrievable from git history.

CAVEATS the report states explicitly (data corrections, 2026-11-03):
  - All 170 curated assignments are cluster_assigned_by='llm' (the original bootstrap), so
    validation measures AGREEMENT WITH THE LLM BOOTSTRAP TAXONOMY, not hand-labelled truth.
  - Clusters are small (2–10 topics; 8 of 30 have ≤3 members), so k=7 is biased toward
    large clusters — hence the k sweep.
  - `attended_linked` is a snapshot that changes after the W4 data fixes; the fixture is
    regenerated before any backfill dry-run. Do not treat it as stable.

Twin access (only for --source twin / --check-twin): psql, user postgres, password from env
PHANTOM_TEST_DB_PASSWORD (same pattern as supabase/scripts/validate_twin.py); PSQL_BIN and
TWIN_CONN override the connection. The fixture is committed name-only; the twin read path
targets public.topic, where the cluster columns live since the post-0016-era swap
(verified live 2026-11-05; canonical_v2 is gone).

Dependencies: stdlib only for everything except embeddings — see
supabase/scripts/requirements-topic-cluster.txt. Importing this module never loads
fastembed; tests run fully offline with a mocked embedder.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol, Sequence

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- twin-only safety ------------------------------------------------------------------------
TWIN_REF = "ytfzzsxcxxbejnowmkmk"
TWIN_HOST = f"db.{TWIN_REF}.supabase.co"
PROD_REF = "oicikjyzmxqfomrrqkvf"  # never a target of any kind; this script is read-only
# Direct host by default (validate_twin.py pattern). TWIN_CONN overrides it — e.g. the session
# pooler user=postgres.<ref> for sandboxes without an IPv6 route to the direct host.
TWIN_CONN = (os.environ.get("TWIN_CONN")
             or f"host={TWIN_HOST} port=5432 user=postgres "
                "dbname=postgres sslmode=require connect_timeout=30")
# The live cluster-state table on the twin. Post-swap (2026-11-05 live probe) the cluster
# columns live in public.topic and canonical_v2 is gone — legacy schemas are probed
# informationally, never read from.
TWIN_TOPIC_SCHEMA = "public"
TWIN_LEGACY_SCHEMAS = ("canonical_v2",)

# --- data ------------------------------------------------------------------------------------
FIXTURE_PATH = os.path.join(REPO_ROOT, "supabase", "fixtures", "yed304_topic_clusters.json")

# --- method constants (spec §4 W2 as corrected) ------------------------------------------------
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # the pin from .claude/scripts/dockb_common.py
EMBED_DIM = 384
K = 7
AUTO_THRESHOLD = 0.80  # the dry-run bar; --validate sweeps and calibrates it
SWEEP_KS = (1, 3, 5, 7)
SWEEP_THRESHOLDS = tuple(round(0.50 + 0.05 * i, 2) for i in range(9))  # 0.50 … 0.90
GATE_PRECISION = 0.90
BASELINE_REPS = 1000  # seeded repetitions for the empirical size-weighted-random baseline
SEED = 20261103
Z95 = 1.959963984540054  # two-sided 95% normal quantile


# ----------------------------------------------------------------------------------------------
# Data types
# ----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    description: str | None
    cluster_id: str | None
    cluster_assigned_by: str | None
    cluster_assignment_confidence: float | None
    created_at: str | None = None


@dataclass(frozen=True)
class ClusterVote:
    cluster_id: str
    vote_share: float          # this cluster's share of the k neighbours' similarity mass
    best_similarity: float     # best neighbour similarity within this cluster


@dataclass(frozen=True)
class VoteResult:
    winning_cluster_id: str
    confidence: float          # winning vote share × top-1 similarity (spec formula)
    top1_similarity: float     # similarity to the nearest assigned topic, any cluster
    ranked: tuple[ClusterVote, ...]  # vote share desc, ties by cluster_id — top-3 goes to review


@dataclass(frozen=True)
class FixtureData:
    topics: list[Topic]
    clusters: dict[str, dict]  # cluster_id -> {"name": ..., "slug": ...}
    attended_ids: set[str]
    generated_at: str | None
    source: str


# ----------------------------------------------------------------------------------------------
# Pure math — unit-tested offline (test_topic_cluster_assign.py), no network, no model
# ----------------------------------------------------------------------------------------------

def topic_text(name: str, description: str | None) -> str:
    """The string that gets embedded. Name-only is the corrected validation basis."""
    return f"{name}\n{description}" if description else name


def l2_normalize(vec: Sequence[float]) -> list[float]:
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0.0:
        return [0.0] * len(vec)
    return [x / norm for x in vec]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"cosine: dimension mismatch {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def knn_vote(query_vec: Sequence[float], neighbors: Sequence[tuple[str, str, Sequence[float]]],
             k: int = K) -> VoteResult:
    """Similarity-weighted vote over the k nearest ASSIGNED topics.

    neighbors: (topic_id, cluster_id, embedding). Votes are per cluster, weighted by
    similarity; confidence = winning share × top-1 similarity (spec §4 W2). Deterministic:
    neighbours tie-break by (similarity desc, topic_id, cluster_id); clusters tie-break by
    (vote_share desc, cluster_id).
    """
    scored = [(cid, tid, cosine(query_vec, vec)) for (tid, cid, vec) in neighbors]
    if not scored:
        raise ValueError("kNN vote needs at least one assigned neighbour")
    top = sorted(scored, key=lambda t: (-t[2], t[1], t[0]))[:k]
    top1 = top[0][2]
    total = sum(s for _, _, s in top)
    # If every neighbour is orthogonal (total == 0) the similarity mass is degenerate —
    # fall back to count shares so ranking stays well-defined; confidence is 0 anyway (top1 == 0).
    by_cluster: dict[str, list[float]] = {}
    for cid, _, s in top:
        by_cluster.setdefault(cid, []).append(s)
    ranked = sorted(
        (ClusterVote(cid, sum(sims) / total if total > 0.0 else len(sims) / len(top),
                     max(sims)) for cid, sims in by_cluster.items()),
        key=lambda cv: (-cv.vote_share, cv.cluster_id))
    win = ranked[0]
    return VoteResult(win.cluster_id, win.vote_share * top1, top1, tuple(ranked))


def baseline_always_largest_loo(assigned: list[Topic]) -> float:
    """Do-nothing baseline (a), leave-one-out form: for each topic, predict the mode cluster
    of the OTHER topics. Returns its precision over all trials."""
    correct = 0
    for t in assigned:
        counts = Counter(o.cluster_id for o in assigned if o.id != t.id and o.cluster_id)
        if not counts:
            raise ValueError("baseline_always_largest_loo: needs >= 2 assigned topics")
        pick = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        correct += pick == t.cluster_id
    return correct / len(assigned)


def baseline_size_weighted_random_loo(assigned: list[Topic], rng: random.Random) -> float:
    """Do-nothing baseline (b), leave-one-out form: predict a random other member's cluster
    (== size-weighted random). One pass; average several seeded passes for stability."""
    correct = 0
    for t in assigned:
        others = [o.cluster_id for o in assigned if o.id != t.id and o.cluster_id]
        if not others:
            raise ValueError("baseline_size_weighted_random_loo: needs >= 2 assigned topics")
        correct += rng.choice(others) == t.cluster_id
    return correct / len(assigned)


def wilson_lower_bound(successes: int, n: int, z: float = Z95) -> float:
    """Wilson score interval lower bound (default 95%). The ship rule compares THIS against
    the baselines, not the raw precision — small-n precision is otherwise overconfident."""
    if n <= 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return max(0.0, (centre - margin) / denom)


# ----------------------------------------------------------------------------------------------
# Evaluation: leave-one-out + the (k, threshold) sweep + the ship rule
# ----------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Loorow:
    topic: Topic
    result: VoteResult
    correct: bool


@dataclass(frozen=True)
class EvalPoint:
    k: int
    threshold: float
    n_auto: int
    correct_auto: int
    precision_auto: float | None  # None = no topic cleared this bar
    wilson_lo: float
    coverage_auto: float

    def qualifies(self, bar: float, baseline_floor: float) -> bool:
        return (self.precision_auto is not None and self.precision_auto >= bar
                and self.wilson_lo > baseline_floor)


def leave_one_out(assigned: list[Topic], vecs: dict[str, list[float]],
                  k: int = K) -> list[Loorow]:
    """Blind LOO: every topic predicted from all the others. Deterministic per topic."""
    rows = []
    for t in assigned:
        others = [(o.id, o.cluster_id, vecs[o.id]) for o in assigned if o.id != t.id]
        res = knn_vote(vecs[t.id], others, k=k)
        rows.append(Loorow(t, res, res.winning_cluster_id == t.cluster_id))
    return rows


def eval_point(k: int, threshold: float, rows: list[Loorow]) -> EvalPoint:
    auto = [r for r in rows if r.result.confidence >= threshold]
    n = len(auto)
    correct = sum(1 for r in auto if r.correct)
    return EvalPoint(k=k, threshold=threshold, n_auto=n, correct_auto=correct,
                     precision_auto=(correct / n) if n else None,
                     wilson_lo=wilson_lower_bound(correct, n),
                     coverage_auto=n / len(rows) if rows else 0.0)


def choose_ship_point(points: Sequence[EvalPoint], baseline_floor: float,
                      bar: float = GATE_PRECISION) -> EvalPoint | None:
    """The corrected ship rule (PR #264 review, point 4): the LOWEST threshold where
    precision >= bar AND the Wilson 95% lower bound beats both baselines. Across k values,
    highest coverage wins (ties: precision desc, then smaller k). None = gate failed."""
    qualifying = [p for p in points if p.qualifies(bar, baseline_floor)]
    if not qualifying:
        return None
    return max(qualifying, key=lambda p: (p.coverage_auto, p.precision_auto or 0.0, -p.k))


# ----------------------------------------------------------------------------------------------
# Fixture I/O — the committed name-only export; validation never needs a database
# ----------------------------------------------------------------------------------------------

def load_fixture(path: str = FIXTURE_PATH) -> FixtureData:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data["topics"]
    topics: list[Topic] = []
    for row in raw:
        conf = row.get("cluster_assignment_confidence")
        topics.append(Topic(
            id=row["id"], name=row["name"], description=None,  # fixture is name-only by design
            cluster_id=row.get("cluster_id"),
            cluster_assigned_by=row.get("cluster_assigned_by"),
            cluster_assignment_confidence=float(conf) if conf not in (None, "") else None,
        ))
    if not topics:
        raise RuntimeError(f"fixture {path} has no topics — aborting rather than validating on nothing")
    clusters = {c["cluster_id"]: c for c in data.get("clusters", [])}
    return FixtureData(topics=topics, clusters=clusters,
                       attended_ids={t["id"] for t in raw if t.get("attended_linked")},
                       generated_at=data.get("generated_at"), source=data.get("source", ""))


# ----------------------------------------------------------------------------------------------
# Twin I/O — read-only (--source twin / --check-twin); the script has no write path
# ----------------------------------------------------------------------------------------------

def _check_twin_conn(conn: str) -> str:
    """Refuse any connection string that is not exactly the twin (spec §7: twin only).

    Accepts either the direct twin host, or a Supabase session pooler host with the twin
    project ref in the username (IPv4 route for sandboxes without IPv6 to the direct host).
    """
    if PROD_REF in conn:
        raise SystemExit(f"refusing PROD connection (ref {PROD_REF})")
    if f"db.{TWIN_REF}.supabase.co" in conn:
        return conn
    if ".pooler.supabase.com" in conn and f"user=postgres.{TWIN_REF}" in conn:
        return conn
    raise SystemExit(f"refusing non-twin connection: host={conn.split(' ')[0]}")


def psql(sql: str, password: str, *, psql_bin: str = "psql", conn: str = TWIN_CONN) -> str:
    _check_twin_conn(conn)
    env = dict(os.environ, PGPASSWORD=password, PGCLIENTENCODING="UTF8")
    p = subprocess.run([psql_bin, conn, "--csv", "-v", "ON_ERROR_STOP=1", "-c", sql],
                       text=True, capture_output=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"psql failed (rc={p.returncode}): {p.stderr.strip()[:500]}")
    return p.stdout


TOMBSTONE_FILTER = "not (metadata ? 'merged_into')"  # merge tombstones are not backlog


def twin_topic_columns(password: str, psql_bin: str, schema: str) -> set[str]:
    """Columns of <schema>.topic on the twin; empty set when the table does not exist."""
    out = psql("select column_name from information_schema.columns "
               f"where table_schema='{schema}' and table_name='topic'",
               password, psql_bin=psql_bin)
    return {r["column_name"] for r in csv.DictReader(io.StringIO(out))}


def fetch_topics_twin(password: str, psql_bin: str = "psql") -> tuple[list[Topic], dict]:
    """Read the twin's clustering state from public.topic — the cluster columns
    live there since the post-swap twin state (verified live 2026-11-05: public.topic has the
    W1 columns, canonical_v2 is gone). Merge tombstones are excluded from the unassigned pool
    per the data corrections. Returns (topics, meta)."""
    cols = twin_topic_columns(password, psql_bin, TWIN_TOPIC_SCHEMA)
    missing = {c for c in ("id", "name", "cluster_id") if c not in cols}
    if missing:
        raise RuntimeError(f"{TWIN_TOPIC_SCHEMA}.topic lacks {sorted(missing)} — the W1-columned "
                           "table is not where the probe says; refusing to guess")
    wanted = ["id", "name", "cluster_id", "cluster_assigned_by"]
    if "cluster_assignment_confidence" in cols:
        wanted.append("cluster_assignment_confidence")
    if "metadata" in cols:
        wanted.append("metadata")
    sel = ", ".join(f"{c}::text as {c}" if c == "metadata" else c for c in wanted)
    out = psql(f"select {sel} from {TWIN_TOPIC_SCHEMA}.topic", password, psql_bin=psql_bin)
    topics, n_tomb = [], 0
    for row in csv.DictReader(io.StringIO(out)):
        conf = row.get("cluster_assignment_confidence")
        meta = row.get("metadata")
        # psql --csv renders NULL as the empty string (DictReader never yields None here),
        # so the tombstone test must be falsy, not `is None` — the None form silently kept
        # every merge tombstone in the unassigned pool (caught in the 2026-11-05 dry-run).
        cluster_id = row["cluster_id"] or None
        if cluster_id is None and meta and "merged_into" in meta:
            n_tomb += 1
            continue
        topics.append(Topic(
            id=row["id"], name=row["name"], description=None,  # twin copy: name-only is the basis
            cluster_id=cluster_id,
            cluster_assigned_by=row["cluster_assigned_by"] or None,
            cluster_assignment_confidence=float(conf) if conf not in ("", None) else None,
        ))
    if not topics:
        raise RuntimeError("twin query returned 0 topics — aborting rather than validating on nothing")
    return topics, {"tombstones_excluded": n_tomb}


def fetch_event_links(password: str, psql_bin: str = "psql") -> dict[str, int]:
    """Read-only event-link counts: topic-tagged links total, and attended-linked topics."""
    out = psql("select count(*)::int as links from public.event_entity where entity_type='topic'",
               password, psql_bin=psql_bin)
    links = int(next(iter(csv.DictReader(io.StringIO(out))))["links"])
    attended = len(fetch_attended_topic_ids(password, psql_bin))
    return {"topic_event_links": links, "attended_topic_ids": attended}


def fetch_attended_topic_ids(password: str, psql_bin: str = "psql") -> set[str]:
    out = psql("select distinct ee.entity_id from public.event_entity ee "
               "join public.event e on e.id = ee.event_id "
               "where ee.entity_type = 'topic' and e.kind = 'attended'",
               password, psql_bin=psql_bin)
    return {r["entity_id"] for r in csv.DictReader(io.StringIO(out)) if r.get("entity_id")}


# ----------------------------------------------------------------------------------------------
# Embedding — lazy fastembed so the module imports (and tests run) without it
# ----------------------------------------------------------------------------------------------

class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class BgeSmallEmbedder:
    """Local deterministic embeddings of the pinned model via fastembed (ONNX, CPU)."""

    def __init__(self, model_name: str = EMBED_MODEL):
        self._model_name = model_name
        self._model = None

    def _ensure(self):
        if self._model is None:
            from fastembed import TextEmbedding  # lazy: core stays stdlib-only
            self._model = TextEmbedding(model_name=self._model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [l2_normalize([float(x) for x in vec])
                for vec in self._ensure().embed(list(texts))]


def embed_topics(topics: list[Topic], embedder: Embedder) -> dict[str, list[float]]:
    texts = [topic_text(t.name, t.description) for t in topics]
    vecs = embedder.embed(texts)
    if len(vecs) != len(topics):
        raise RuntimeError(f"embedder returned {len(vecs)} vectors for {len(topics)} topics")
    bad = [t.id for t, v in zip(topics, vecs) if len(v) != EMBED_DIM]
    if bad:
        raise RuntimeError(f"embedder produced non-{EMBED_DIM}-dim vectors, e.g. {bad[0]}")
    return {t.id: v for t, v in zip(topics, vecs)}


# ----------------------------------------------------------------------------------------------
# Runs
# ----------------------------------------------------------------------------------------------

@dataclass
class Assignment:
    """A confident auto-assignment (--dry-run list item)."""
    topic: Topic
    result: VoteResult
    attended_linked: bool


@dataclass
class ReviewItem:
    """Below the confidence bar: everything Alex needs to pick a cluster himself."""
    topic: Topic
    result: VoteResult
    attended_linked: bool

    def candidates(self, n: int = 3) -> list[ClusterVote]:
        return list(self.result.ranked[:n])


def run_scoring(queries: list[Topic], assigned: list[Topic], vecs: dict[str, list[float]],
                k: int, attended_ids: set[str],
                threshold: float = AUTO_THRESHOLD,
                ) -> tuple[list[Assignment], list[ReviewItem]]:
    """Score every query against the assigned pool. Returns (auto-assign list, review queue).

    The auto-assign list is ordered attended-linked first, then confidence desc, then name —
    the spec's 'attended-linked topics go first'.
    """
    neighbor_index = [(t.id, t.cluster_id, vecs[t.id]) for t in assigned]
    assignments, review = [], []
    for t in queries:
        result = knn_vote(vecs[t.id], neighbor_index, k)
        flag = t.id in attended_ids
        if result.confidence >= threshold:
            assignments.append(Assignment(t, result, flag))
        else:
            review.append(ReviewItem(t, result, flag))
    assignments.sort(key=lambda a: (not a.attended_linked, -a.result.confidence, a.topic.name))
    review.sort(key=lambda r: (not r.attended_linked, -r.result.confidence, r.topic.name))
    return assignments, review


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def cluster_label(cluster_id: str, names: dict[str, dict] | dict[str, str]) -> str:
    name = names.get(cluster_id, {}).get("name") if isinstance(names.get(cluster_id), dict) \
        else names.get(cluster_id)
    return name or f"cluster {cluster_id[:8]}"


# --- --validate: the fixed-taxonomy baseline study --------------------------------------------

def run_validate(args: argparse.Namespace) -> int:
    fx = load_fixture(args.fixture)
    assigned = [t for t in fx.topics if t.cluster_id is not None]
    unassigned = [t for t in fx.topics if t.cluster_id is None]
    n_clusters = len({t.cluster_id for t in assigned})
    print(f"fixture: {len(fx.topics)} topics · {len(assigned)} assigned · {n_clusters} "
          f"clusters · {len(unassigned)} unassigned")
    if len(assigned) < 30:
        raise RuntimeError(f"only {len(assigned)} assigned topics — too few for the study")

    vecs = embed_topics(assigned, BgeSmallEmbedder())
    print(f"embedded {len(assigned)} topic names with {EMBED_MODEL} ({EMBED_DIM}-d); "
          f"running leave-one-out…")
    # LOO must be recomputed per k — neighbourhood composition (and therefore vote
    # share and confidence) changes with k; relabelling one set of rows would lie.
    rows_by_k = {k: leave_one_out(assigned, vecs, k=k) for k in SWEEP_KS}

    # Do-nothing baselines over the SAME trial set (LOO form), plus their mean over reps.
    largest_precision = baseline_always_largest_loo(assigned)
    rng = random.Random(args.seed + 1)
    weighted_precisions = [baseline_size_weighted_random_loo(assigned, rng)
                           for _ in range(BASELINE_REPS)]
    weighted_mean = sum(weighted_precisions) / len(weighted_precisions)
    baseline_floor = max(largest_precision, weighted_mean)

    points = [eval_point(k, thr, rows_by_k[k]) for k in SWEEP_KS for thr in SWEEP_THRESHOLDS]
    ship = choose_ship_point(points, baseline_floor)
    passed = ship is not None
    table_rows = rows_by_k[ship.k] if ship else rows_by_k[K]
    report = render_validation_report(fx, assigned, unassigned, table_rows, points, ship,
                                      largest_precision, weighted_mean, args)
    path = os.path.join(args.evidence_dir, f"yed-304-holdout-validation-{utc_date()}.md")
    os.makedirs(args.evidence_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"report: {path}")
    if passed:
        print(f"SHIP POINT: k={ship.k}, threshold={ship.threshold:.2f} — precision "
              f"{ship.precision_auto:.3f} (wilson95lo {ship.wilson_lo:.3f}), coverage "
              f"{ship.coverage_auto:.3f}, vs baseline floor {baseline_floor:.3f}")
        return 0
    print("GATE FAILED: no (k, threshold) combination reached precision >= "
          f"{GATE_PRECISION:.2f} with the Wilson 95% lower bound above the baseline floor "
          f"{baseline_floor:.3f}. STOP — do not build or run the backfill.")
    return 3


def render_validation_report(fx: FixtureData, assigned: list[Topic], unassigned: list[Topic],
                             rows: list[Loorow], points: list[EvalPoint],
                             ship: EvalPoint | None, largest_precision: float,
                             weighted_mean: float, args: argparse.Namespace) -> str:
    names = fx.clusters
    n_assigned, n_unassigned = len(assigned), len(unassigned)
    lines = [
        "# YED-304 W2 — fixed-taxonomy baseline validation (leave-one-out)",
        "",
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by "
        "`supabase/scripts/topic_cluster_assign.py --validate` (offline, fixture-backed; no "
        "database writes).",
        "",
        "## What this measures — read first",
        "",
        "- **This is the fixed-taxonomy BASELINE study.** Production clustering is on hold "
        "pending the dynamic-taxonomy design review (PR #264); any new design must beat "
        "these numbers.",
        "- **Agreement, not accuracy:** all 170 curated assignments are "
        "`cluster_assigned_by='llm'` (the original bootstrap). This study measures agreement "
        "with the LLM bootstrap taxonomy, **not** hand-labelled ground truth.",
        "- **Name-only embeddings:** the fixture is name-only by design (most backlog topics "
        "have no description); name+description results would overstate backlog performance.",
        "- **attended_linked is a snapshot** that changes after the W4 data fixes; the fixture "
        "is regenerated before any backfill dry-run. Not treated as stable here.",
        f"- **Backlog:** the fixture's {n_unassigned} unassigned rows include 8 merge "
        "tombstones (`metadata ? 'merged_into'`) that are not identifiable in the name-only "
        "fixture; the real backlog is **94**. Twin-backed runs exclude them explicitly.",
        "",
        "## Method",
        "",
        f"- Embeddings: `{EMBED_MODEL}` ({EMBED_DIM}-d, the pin from "
        "`.claude/scripts/dockb_common.py`), local ONNX inference via fastembed, cosine "
        "similarity, deterministic.",
        "- **Leave-one-out over all 170 curated assignments:** each topic is assigned blind "
        "with kNN over the other 169; vote per cluster weighted by similarity; confidence = "
        "winning cluster's vote share × top-1 similarity.",
        f"- k swept over {list(SWEEP_KS)} (clusters are small — 2–10 topics, 8 of 30 with ≤3 "
        "members — so k=7 alone would be biased toward large clusters) and the confidence "
        f"threshold over {list(SWEEP_THRESHOLDS)}.",
        "- Ship rule (PR #264 review): the lowest threshold where precision ≥ "
        f"{GATE_PRECISION:.2f} AND the Wilson 95% lower bound beats both baselines; across k, "
        "highest coverage wins.",
        f"- Baselines over the same trial set: (a) always-largest-cluster (LOO form); "
        f"(b) size-weighted-random, mean over {BASELINE_REPS} seeded repetitions.",
        "",
        "## Data",
        "",
        f"- Fixture: `supabase/fixtures/yed304_topic_clusters.json` "
        f"(generated {fx.generated_at or 'unknown'}; source: {fx.source})",
        f"- Topics: **{len(fx.topics)}** · assigned (LLM bootstrap): **{n_assigned}** · "
        f"clusters: **{len(names)}** · unassigned: **{n_unassigned}** (8 tombstones → real "
        "backlog 94)",
        "",
        "## Sweep results — precision / Wilson 95% lower bound / coverage",
        "",
        "| k | threshold | auto-n | precision | wilson95_lo | coverage | qualifies |",
        "|---|---|---|---|---|---|---|",
    ]
    baseline_floor = max(largest_precision, weighted_mean)
    for p in points:
        lines.append(
            f"| {p.k} | {p.threshold:.2f} | {p.n_auto} | "
            + (f"{p.precision_auto:.3f}" if p.precision_auto is not None else "n/a")
            + f" | {p.wilson_lo:.3f} | {p.coverage_auto:.3f} | "
            + ("✅" if p.qualifies(GATE_PRECISION, baseline_floor) else "") + " |")
    lines += [
        "",
        "## Baselines (same trial set, coverage 1.0)",
        "",
        f"- (a) Always-largest-cluster (LOO form): **{largest_precision:.3f}**",
        f"- (b) Size-weighted-random (LOO form): mean **{weighted_mean:.3f}** over "
        f"{BASELINE_REPS} seeded reps",
        f"- Baseline floor for the ship rule: **{baseline_floor:.3f}**",
        "",
    ]
    if ship is not None:
        lines += [
            "## Verdict",
            "",
            f"**PASS** — ship point: **k={ship.k}, threshold={ship.threshold:.2f}** · "
            f"precision {ship.precision_auto:.3f} ({ship.correct_auto}/{ship.n_auto}) · "
            f"Wilson 95% lower bound {ship.wilson_lo:.3f} > baseline floor {baseline_floor:.3f} "
            f"· coverage {ship.coverage_auto:.3f} ({ship.n_auto}/170 auto-assigned, "
            f"{170 - ship.n_auto} to review).",
            "",
            "The gate clears for the fixed taxonomy. This number is the bar any dynamic-"
            "taxonomy design must beat. The backfill dry-run remains a separate task and the "
            "nightly write stays behind the W1 allowlist + design review.",
            "",
        ]
        auto_threshold = ship.threshold
    else:
        lines += [
            "## Verdict",
            "",
            f"**FAIL** — no (k, threshold) combination reached precision ≥ {GATE_PRECISION:.2f} "
            f"with the Wilson 95% lower bound above the baseline floor {baseline_floor:.3f}. "
            "STOP — do not build or run the backfill.",
            "",
        ]
        auto_threshold = max(SWEEP_THRESHOLDS)
    lines += [
        "## Per-topic results (leave-one-out)",
        "",
        f"Auto column uses the ship-point threshold {auto_threshold:.2f}"
        if ship is not None else f"Auto column uses the highest swept threshold {auto_threshold:.2f}",
        "",
        "| topic | true cluster | predicted cluster | top-1 sim | confidence | auto | correct |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: (not r.correct, -r.result.confidence, r.topic.name)):
        t = r.topic
        lines.append(
            f"| {t.name} | {cluster_label(t.cluster_id, names)} | "
            f"{cluster_label(r.result.winning_cluster_id, names)} | "
            f"{r.result.top1_similarity:.3f} | {r.result.confidence:.3f} | "
            f"{'yes' if r.result.confidence >= auto_threshold else 'no'} | "
            f"{'✅' if r.correct else '❌'} |")
    lines.append("")
    return "\n".join(lines)


# --- --dry-run --------------------------------------------------------------------------------

def run_dry_run(args: argparse.Namespace) -> int:
    if args.source == "twin":
        password = require_twin_password()
        topics, meta = fetch_topics_twin(password, args.psql_bin)
        attended_ids = fetch_attended_topic_ids(password, args.psql_bin)
        names: dict = {}
        origin = (f"twin {TWIN_HOST} ({TWIN_TOPIC_SCHEMA}.topic; "
                  f"{meta['tombstones_excluded']} tombstones excluded)")
    else:
        fx = load_fixture(args.fixture)
        topics = fx.topics
        attended_ids = fx.attended_ids
        names = fx.clusters
        origin = f"fixture {os.path.relpath(args.fixture, REPO_ROOT)}"
    assigned = [t for t in topics if t.cluster_id is not None]
    unassigned = [t for t in topics if t.cluster_id is None]
    print(f"source: {origin}")
    print(f"topics: {len(topics)} · assigned {len(assigned)} · unassigned {len(unassigned)} · "
          f"{sum(1 for t in unassigned if t.id in attended_ids)} unattended-flagged backlog rows")
    vecs = embed_topics(topics, BgeSmallEmbedder())
    assignments, review = run_scoring(unassigned, assigned, vecs, args.k, attended_ids,
                                      threshold=args.threshold)

    auto_rows = [{"topic_id": a.topic.id, "name": a.topic.name,
                  "cluster_id": a.result.winning_cluster_id,
                  "cluster_name": cluster_label(a.result.winning_cluster_id, names),
                  "cluster_assignment_confidence": round(a.result.confidence, 4),
                  "top1_similarity": round(a.result.top1_similarity, 4),
                  "attended_linked": a.attended_linked} for a in assignments]
    review_rows = [{"topic_id": r.topic.id, "name": r.topic.name,
                    "confidence": round(r.result.confidence, 4),
                    "top1_similarity": round(r.result.top1_similarity, 4),
                    "attended_linked": r.attended_linked,
                    "candidates": [{"cluster_id": cv.cluster_id,
                                    "cluster_name": cluster_label(cv.cluster_id, names),
                                    "vote_share": round(cv.vote_share, 4),
                                    "best_similarity": round(cv.best_similarity, 4)}
                                   for cv in r.candidates()],
                    "option_none_fits": "none-fits / new theme (Alex decides; written as `human`)"}
                   for r in review]
    payload = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "mode": "dry-run", "source": origin, "model": EMBED_MODEL,
               "k": args.k, "auto_threshold": args.threshold,
               "caveats": ["name-only embeddings",
                           "attended_linked is a changing snapshot (W4)",
                           "validation measures agreement with the LLM bootstrap taxonomy"],
               "counts": {"topics": len(topics), "assigned": len(assigned),
                          "unassigned": len(unassigned),
                          "unassigned_attended_linked": sum(1 for t in unassigned
                                                            if t.id in attended_ids),
                          "auto_assign": len(auto_rows), "review_queue": len(review_rows)},
               "auto_assign": auto_rows, "review_queue": review_rows}
    os.makedirs(args.evidence_dir, exist_ok=True)
    json_path = os.path.join(args.evidence_dir, f"yed-304-w2-dry-run-{utc_date()}.json")
    md_path = os.path.join(args.evidence_dir, f"yed-304-w2-dry-run-{utc_date()}.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_dry_run_md(payload))
    print(f"dry-run outputs: {md_path} · {json_path}")
    print(f"auto-assign: {len(auto_rows)} · review queue: {len(review_rows)}")
    return 0


def render_dry_run_md(payload: dict) -> str:
    c = payload["counts"]
    lines = [
        "# YED-304 W2 — dry-run (no writes)",
        "",
        f"Generated {payload['generated_utc']} from `{payload['source']}` with `{EMBED_MODEL}` "
        f"({EMBED_DIM}-d), k={payload['k']}, confidence = winning vote share × top-1 similarity, "
        f"auto-assign at >= {payload['auto_threshold']:.2f}. Read-only: nothing was written.",
        "",
        "Caveats: name-only embeddings · `attended_linked` is a changing snapshot (W4) · "
        "validation measures agreement with the LLM bootstrap taxonomy, not ground truth.",
        "",
        f"- Topics: {c['topics']} · assigned: {c['assigned']} · unassigned: {c['unassigned']} "
        f"(of which {c['unassigned_attended_linked']} are attended-event-linked)",
        f"- **Auto-assign list: {c['auto_assign']}** · **Review queue: {c['review_queue']}**",
        "",
        "## Auto-assign list (attended-event-linked first)",
        "",
        "| topic | cluster | confidence | top-1 sim | attended-linked |",
        "|---|---|---|---|---|",
    ]
    for a in payload["auto_assign"]:
        lines.append(f"| {a['name']} | {a['cluster_name']} | {a['cluster_assignment_confidence']:.3f} "
                     f"| {a['top1_similarity']:.3f} | {'⚠️ yes' if a['attended_linked'] else 'no'} |")
    lines += [
        "",
        "## Review queue (below the confidence bar — Alex decides)",
        "",
        "Top-3 candidate clusters with scores; a none-fits / new-theme option is implicit for "
        "every row. Alex's picks are written as `human`.",
        "",
        "| topic | top-3 candidate clusters (share / best sim) | confidence | attended-linked |",
        "|---|---|---|---|",
    ]
    for r in payload["review_queue"]:
        cands = " · ".join(f"{c['cluster_name']} ({c['vote_share']:.2f}/{c['best_similarity']:.2f})"
                           for c in r["candidates"])
        lines.append(f"| {r['name']} | {cands} | {r['confidence']:.3f} "
                     f"| {'⚠️ yes' if r['attended_linked'] else 'no'} |")
    lines += [
        "",
        "---",
        "",
        "Machine-readable companion: `yed-304-w2-dry-run-" + utc_date() + ".json`.",
        "",
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------
# --check-twin: read-only schema + row-count probe
# ----------------------------------------------------------------------------------------------

def run_check_twin(password: str, args: argparse.Namespace) -> int:
    """Read-only probe of the twin's clustering state. Reports what exists and what is
    missing, never guesses."""
    _check_twin_conn(TWIN_CONN)
    ok = True
    # public.topic is required (the live cluster-state table); a legacy schema's absence
    # is expected post-swap, not a failure.
    for schema in (TWIN_TOPIC_SCHEMA,) + TWIN_LEGACY_SCHEMAS:
        required = schema == TWIN_TOPIC_SCHEMA
        try:
            cols = twin_topic_columns(password, args.psql_bin, schema)
            if not cols:
                print(f"  {schema}.topic: {'MISSING' if required else 'absent (legacy, expected)'}")
                ok = ok and not required
                continue
            wanted = sorted({"id", "name", "description", "cluster_id", "cluster_assigned_by",
                             "cluster_assignment_confidence", "metadata", "created_at"} & cols)
            out = psql(f"select count(*)::int as n from {schema}.topic",
                       password, psql_bin=args.psql_bin)
            n = int(next(iter(csv.DictReader(io.StringIO(out))))["n"])
            print(f"  {schema}.topic: {n} rows; columns: {', '.join(wanted)}")
            if "cluster_id" in cols:
                out = psql(f"select count(*)::int as assigned from {schema}.topic "
                           f"where cluster_id is not null"
                           + (" and not (metadata ? 'merged_into')" if "metadata" in cols else ""),
                           password, psql_bin=args.psql_bin)
                assigned = int(next(iter(csv.DictReader(io.StringIO(out))))["assigned"])
                print(f"    assigned rows: {assigned}")
            if "metadata" in cols:
                out = psql(f"select count(*)::int as tomb from {schema}.topic "
                           "where cluster_id is null and metadata ? 'merged_into'",
                           password, psql_bin=args.psql_bin)
                tomb = int(next(iter(csv.DictReader(io.StringIO(out))))["tomb"])
                print(f"    merge tombstones (null cluster + merged_into): {tomb}")
        except RuntimeError as e:
            print(f"  {schema}.topic probe FAILED: {e}")
            ok = False
    try:
        links = fetch_event_links(password, args.psql_bin)
        print(f"  event links: {links}")
    except RuntimeError as e:
        print(f"  event-link probe FAILED (informational): {e}")
    return 0 if ok else 1


def require_twin_password() -> str:
    password = os.environ.get("PHANTOM_TEST_DB_PASSWORD")
    if not password:
        raise SystemExit("PHANTOM_TEST_DB_PASSWORD not set — twin access unavailable. Export it "
                         "(pattern: supabase/scripts/validate_twin.py); this script never reads "
                         ".env itself and never touches prod with psql.")
    return password


# ----------------------------------------------------------------------------------------------
# --selftest — offline smoke checks in the repo's selftest convention
# ----------------------------------------------------------------------------------------------

def selftest() -> bool:
    checks: list[tuple[str, Callable[[], None]]] = []

    def check(name: str, fn: Callable[[], None]) -> None:
        checks.append((name, fn))

    def expect_raise(fn: Callable[[], None], exc: type[BaseException]) -> None:
        try:
            fn()
        except exc:
            return
        raise AssertionError("expected " + exc.__name__)

    def assert_true(cond: bool, msg: str = "condition false") -> None:
        if not cond:
            raise AssertionError(msg)

    check("cosine: identical=1 orthogonal=0 opposite=-1 zero-safe", lambda: (
        assert_true(cosine([1, 0], [1, 0]) == 1.0, "identical"),
        assert_true(cosine([1, 0], [0, 1]) == 0.0, "orthogonal"),
        assert_true(cosine([1, 0], [-1, 0]) == -1.0, "opposite"),
        assert_true(cosine([0, 0], [1, 1]) == 0.0, "zero-vector safe"),
        None))

    check("topic_text: name-only is the corrected basis", lambda: (
        assert_true(topic_text("A", None) == "A", "name-only"),
        assert_true(topic_text("A", "d") == "A\nd", "with description"),
        None))

    def _vote_math() -> None:
        # a (c1, sim 1.0) + c (c1, sim 0.6) vs b (c2, sim 0.8): c1 wins on mass 1.6/2.4,
        # confidence = share × top-1 = (1.6/2.4) × 1.0 exactly.
        q = [1.0, 0.0]
        res = knn_vote(q, [("a", "c1", [1.0, 0.0]), ("b", "c2", [0.8, 0.6]),
                           ("c", "c1", [0.6, 0.8])], k=3)
        share_c1 = (1.0 + 0.6) / (1.0 + 0.8 + 0.6)
        assert_true(abs(res.confidence - share_c1 * 1.0) < 1e-9, "confidence formula")
        assert_true(res.winning_cluster_id == "c1", "winner")
        assert_true(abs(res.top1_similarity - 1.0) < 1e-9, "top-1")

    check("knn_vote: confidence = share × top-1, weighted per cluster", _vote_math)

    def _vote_ties() -> None:
        # Two clusters with identical similarity: the lexicographically smaller cluster wins.
        res = knn_vote([1.0, 0.0], [("a", "c2", [1.0, 0.0]), ("b", "c1", [1.0, 0.0])], k=2)
        assert_true(res.winning_cluster_id == "c1", f"tie-break picked {res.winning_cluster_id}")

    check("knn_vote: deterministic tie-break by cluster id", _vote_ties)

    check("knn_vote: empty neighbours refused", lambda: expect_raise(
        lambda: knn_vote([1.0], [], k=3), ValueError))

    def _loo() -> None:
        # Three well-separated clusters: LOO must classify everything correctly.
        topics = [Topic(f"00000000-0000-0000-0000-{i:012d}", f"n{i}", None,
                        f"c{i % 3}", "llm", None) for i in range(12)]
        vecs = {t.id: [float(t.cluster_id == "c0"), float(t.cluster_id == "c1"),
                       float(t.cluster_id == "c2")] for t in topics}
        rows = leave_one_out(topics, vecs)
        assert_true(len(rows) == 12, f"expected 12 trials, got {len(rows)}")
        assert_true(all(r.correct for r in rows), "separated clusters must classify perfectly")
        # ties break lexicographically: equidistant single-member clusters → smaller cluster id wins
        lone = [Topic("id-a", "a", None, "c-b", None, None), Topic("id-b", "b", None, "c-a", None, None)]
        vv = {"id-a": [1.0, 0.0], "id-b": [0.0, 1.0]}
        rows2 = leave_one_out(lone, vv)
        assert_true(rows2[0].result.winning_cluster_id == "c-a", "tie-break")

    check("leave_one_out: perfect on separated clusters, deterministic ties", _loo)

    def _wilson() -> None:
        assert_true(wilson_lower_bound(0, 10) == 0.0, "0 successes → 0 lower bound")
        assert_true(abs(wilson_lower_bound(9, 10) - 0.5958) < 0.01, "9/10 wilson-lo ≈ 0.596")
        assert_true(wilson_lower_bound(5, 5) < 1.0, "5/5 lower bound still < 1")
        assert_true(wilson_lower_bound(0, 0) == 0.0, "empty trial set → 0")

    check("wilson_lower_bound: known values, empty-safe", _wilson)

    def _sweep() -> None:
        rows = [Loorow(Topic(f"id{i}", f"n{i}", None, "c1", None, None),
                       VoteResult("c1", 0.9 if i < 6 else 0.5, 0.9, ()), True) for i in range(10)]
        p = eval_point(7, 0.80, rows)
        assert_true(p.n_auto == 6 and p.correct_auto == 6 and p.precision_auto == 1.0,
                    f"auto split wrong: {p}")
        assert_true(abs(p.coverage_auto - 0.6) < 1e-9, "coverage")
        # ship rule: lowest qualifying threshold, must beat the baseline floor.
        # At 0.50 all ten rows are auto and correct → precision 1.0, wilson-lo(10,10)=0.722
        # > floor 0.55, so 0.50 qualifies; SWEEP_THRESHOLDS starts at 0.50.
        points = [eval_point(7, thr, rows) for thr in SWEEP_THRESHOLDS]
        ship = choose_ship_point(points, baseline_floor=0.55)
        assert_true(ship is not None and ship.threshold == 0.50, "lowest qualifying threshold")
        assert_true(choose_ship_point(points, baseline_floor=0.99) is None,
                    "impossible floor must fail the gate")

    check("eval_point + choose_ship_point: threshold/coverage/wilson rule", _sweep)

    check("baseline_always_largest_loo: mode of the others", lambda: assert_true(
        abs(baseline_always_largest_loo(
            [Topic("a", "a", None, "c1", None, None), Topic("b", "b", None, "c1", None, None),
             Topic("c", "c", None, "c2", None, None)]) - (2 / 3)) < 1e-9, "mode precision"))

    def _fixture_loader() -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "fx.json")
            with open(p, "w") as f:
                json.dump({"source": "test", "generated_at": "t", "topics": [
                    {"id": "00000000-0000-0000-0000-000000000001", "name": "A",
                     "cluster_id": "00000000-0000-0000-0000-0000000000cc",
                     "cluster_assigned_by": "llm", "attended_linked": True},
                    {"id": "00000000-0000-0000-0000-000000000002", "name": "B",
                     "cluster_id": None, "cluster_assigned_by": None, "attended_linked": False}],
                    "clusters": [{"cluster_id": "00000000-0000-0000-0000-0000000000cc",
                                  "name": "Cluster CC", "slug": "cc"}]}, f)
            fx = load_fixture(p)
            assert_true(len(fx.topics) == 2 and fx.topics[0].description is None,
                        "fixture is name-only")
            assert_true(fx.attended_ids == {"00000000-0000-0000-0000-000000000001"}, "attended")
            assert_true(fx.clusters["00000000-0000-0000-0000-0000000000cc"]["name"] == "Cluster CC",
                        "cluster names load")

    check("load_fixture: name-only topics, attended set, cluster names", _fixture_loader)

    check("twin-only guard: prod and foreign hosts refused", lambda: (
        expect_raise(lambda: _check_twin_conn(f"host=db.{PROD_REF}.supabase.co port=5432"),
                     SystemExit),
        assert_true(_check_twin_conn(TWIN_CONN) == TWIN_CONN, "twin conn accepted"),
        expect_raise(lambda: _check_twin_conn(
            f"host=aws-1-us-east-2.pooler.supabase.com user=postgres.{PROD_REF}"), SystemExit),
        None))

    failed = []
    for name, fn in checks:
        try:
            fn()
            print(f"  ✓ {name}")
        except Exception as e:  # noqa: BLE001 — a selftest reports every failure, never hides one
            failed.append(name)
            print(f"  ✗ {name}: {e}")
    print(f"selftest: {len(checks) - len(failed)}/{len(checks)} checks pass")
    return not failed


# ----------------------------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--validate", action="store_true",
                       help="leave-one-out baseline study (fixture, offline); writes only the "
                            "evidence report; exit 3 = gate failed")
    modes.add_argument("--dry-run", action="store_true",
                       help="score all unassigned topics; emit auto-assign list + review queue "
                            "to supabase/evidence/ (default mode; no writes)")
    modes.add_argument("--check-twin", action="store_true",
                       help="read-only twin probe: schema + row counts + tombstones")
    ap.add_argument("--source", choices=("fixture", "twin"), default="fixture",
                    help="data source for --dry-run (default: fixture, offline)")
    ap.add_argument("--fixture", default=FIXTURE_PATH, help="fixture path override")
    ap.add_argument("--k", type=int, default=K, help=f"neighbours for dry-run (spec: 7; "
                                                     f"--validate sweeps {list(SWEEP_KS)})")
    ap.add_argument("--threshold", type=float, default=AUTO_THRESHOLD,
                    help=f"auto-assign confidence bar for dry-run (spec: {AUTO_THRESHOLD}; "
                         "--validate sweeps 0.50–0.90 and calibrates)")
    ap.add_argument("--seed", type=int, default=SEED, help=f"baseline RNG seed (default {SEED})")
    ap.add_argument("--evidence-dir",
                    default=os.path.join(REPO_ROOT, "supabase", "evidence"))
    ap.add_argument("--psql-bin", default=os.environ.get("PSQL_BIN", "psql"))
    ap.add_argument("--selftest", action="store_true", help="offline smoke checks; no network")
    args = ap.parse_args(argv)
    if args.selftest:
        return 0 if selftest() else 1
    if args.k < 1:
        ap.error("--k must be >= 1")
    if args.validate:
        return run_validate(args)
    if args.check_twin:
        return run_check_twin(require_twin_password(), args)
    return run_dry_run(args)


if __name__ == "__main__":
    sys.exit(main())
