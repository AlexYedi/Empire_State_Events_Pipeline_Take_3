#!/usr/bin/env python3
"""YED-156 A.5 — 3-arm retrieval A/B harness. Zero metered calls.

Arms
  dense                     Phase A baseline: bge-small query embedding ->
                            match_doc_chunks RPC -> top-k. Works today.
  hybrid_rerank             match_doc_chunks_hybrid (dense + keyword, fused by
                            reciprocal rank) over-fetches `candidate_n`, then the
                            local cross-encoder in rerank.py reorders to top-k.
                            REQUIRES the A.5 migration.
  contextual_hybrid_rerank  same, restricted to documents ingested under the
                            'contextual_v1' profile, where each chunk carries a
                            1-2 sentence situating `context`.
                            REQUIRES the A.5 migration AND a contextual ingest.

GUARD: `.claude/references/doc-kb-migration-a5.sql` is NOT applied to the live
project as of 2026-09-11 — `match_doc_chunks_hybrid`, `doc_chunks.tsv` and
`documents.retrieval_profile` do not exist. The two hybrid arms detect that and
exit with the exact remediation instead of a PostgREST stack trace. The `dense`
arm is unaffected and runs today.

Ship rule (PRD §Success). Against the `dense` baseline on the same eval set:
  hybrid_rerank ships if
      (recall@8 gain >= +0.08  OR  precision@8 gain >= +0.10)
      AND the other metric regresses by no more than 0.02
      AND net question flips >= +2
  contextual_hybrid_rerank ships only if it adds >= +0.05 recall@8 over
      hybrid_rerank — contextual ingest costs metered tokens at ingest time, so
      it has to clear a bar of its own, not merely beat the dense baseline.

Usage
  ./.venv/bin/python .../ab_harness.py --arms dense
  ./.venv/bin/python .../ab_harness.py --arms dense,hybrid_rerank --k 8 --out run.json
"""
from __future__ import annotations
import argparse, json, os, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dockb_common as dk                      # noqa: E402
import retrieval_metrics as rm                 # noqa: E402

ARMS = ("dense", "hybrid_rerank", "contextual_hybrid_rerank")
SHIP = {"recall_gain": 0.08, "precision_gain": 0.10,
        "max_other_regression": 0.02, "min_net_flips": 2,
        "contextual_extra_recall": 0.05}


class MigrationMissing(RuntimeError):
    """Raised when an arm needs doc-kb-migration-a5.sql and it is not applied."""


# --------------------------------------------------------------------------
# migration probe
# --------------------------------------------------------------------------
def migration_applied() -> tuple[bool, str]:
    """Cheapest honest probe: ask PostgREST for the hybrid RPC and the profile column.

    PostgREST answers PGRST202 ('Could not find the function') for a missing RPC
    and PGRST204/42703 for a missing column, so a single failed call is enough —
    no DDL introspection and no write.
    """
    try:
        dk.supa("POST", "/rpc/match_doc_chunks_hybrid",
                body={"query_embedding": dk.vec_literal([0.0] * dk.EMBED_DIM),
                      "query_text": "probe", "match_count": 1, "candidate_n": 1})
    except RuntimeError as e:
        return False, f"match_doc_chunks_hybrid missing ({str(e)[:160]})"
    try:
        dk.supa("GET", "/documents?select=retrieval_profile&limit=1")
    except RuntimeError as e:
        return False, f"documents.retrieval_profile missing ({str(e)[:160]})"
    return True, "applied"


def _require_migration():
    ok, why = migration_applied()
    if not ok:
        raise MigrationMissing(
            f"A.5 migration not applied to Supabase project {dk.SUPABASE_REF}: {why}\n"
            "  FIX: open the `empire state ai` SQL Editor (REST/dashboard only — never "
            "the Supabase MCP, which points at a different account) and run\n"
            "       .claude/references/doc-kb-migration-a5.sql\n"
            "  Then re-run this arm. The `dense` arm needs nothing and runs today.")


# --------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------
def arm_dense(question: str, k: int, **_) -> list[dict]:
    body = {"query_embedding": dk.embed_query(question), "match_count": k}
    try:
        _, rows = dk.supa("POST", "/rpc/match_doc_chunks", body=body)
    except RuntimeError:
        # post-migration the RPC gained filter_profile; PostgREST can report the
        # overload as ambiguous if both shapes linger. Pin the baseline profile.
        body["filter_profile"] = "dense_v1"
        _, rows = dk.supa("POST", "/rpc/match_doc_chunks", body=body)
    return rows or []


def _hybrid(question: str, k: int, candidate_n: int, rrf_k: int, profile: str | None):
    _require_migration()
    import rerank
    body = {"query_embedding": dk.embed_query(question), "query_text": question,
            "match_count": candidate_n, "candidate_n": candidate_n, "rrf_k": rrf_k}
    if profile:
        body["filter_profile"] = profile
    _, rows = dk.supa("POST", "/rpc/match_doc_chunks_hybrid", body=body)
    return rerank.rerank(question, rows or [], top_n=k)


def arm_hybrid_rerank(question: str, k: int, candidate_n: int = 20,
                      rrf_k: int = 60, **_) -> list[dict]:
    return _hybrid(question, k, candidate_n, rrf_k, profile="dense_v1")


def arm_contextual_hybrid_rerank(question: str, k: int, candidate_n: int = 20,
                                 rrf_k: int = 60, **_) -> list[dict]:
    os.environ["DOCKB_RERANK_CONTEXT"] = "1"   # score context+content, as indexed
    try:
        rows = _hybrid(question, k, candidate_n, rrf_k, profile="contextual_v1")
    finally:
        os.environ.pop("DOCKB_RERANK_CONTEXT", None)
    if not rows:
        raise MigrationMissing(
            "no chunks under retrieval_profile='contextual_v1'. The A.5 migration "
            "creates the column but does NOT backfill context — re-ingest the doc "
            "with the contextual profile before running this arm.")
    return rows


ARM_FN = {"dense": arm_dense, "hybrid_rerank": arm_hybrid_rerank,
          "contextual_hybrid_rerank": arm_contextual_hybrid_rerank}


# --------------------------------------------------------------------------
# run + score
# --------------------------------------------------------------------------
def run_arm(name: str, cases: list[dict], k: int, mode: str, **kw) -> dict:
    fn, results, lat = ARM_FN[name], {}, []
    for c in cases:
        t0 = time.perf_counter()
        results[c["id"]] = fn(c["q"], k, **kw)
        lat.append((time.perf_counter() - t0) * 1000)
    block = rm.score_set(results, cases, k, mode)
    block["arm"] = name
    block["latency_ms"] = {
        "p50": round(statistics.median(lat), 1),
        "p95": round(sorted(lat)[max(0, int(round(0.95 * len(lat))) - 1)], 1),
        "mean": round(statistics.fmean(lat), 1), "max": round(max(lat), 1)}
    # strict gold-only view alongside the headline, so a loosened relevance
    # predicate can never be mistaken for a retrieval win
    block["strict_gold"] = {
        f"context_recall@{k}": rm.score_set(results, cases, k, "gold")[f"context_recall@{k}"]}
    block["_raw"] = results
    return block


def flips(base: dict, arm: dict, k: int) -> dict:
    b, a = base["per_case_recall"], arm["per_case_recall"]
    gained = sorted(i for i in a if a[i] > b.get(i, 0))
    lost = sorted(i for i in a if a[i] < b.get(i, 0))
    return {"gained": gained, "lost": lost, "net": len(gained) - len(lost)}


def verdict(base: dict, arm: dict, k: int, ctx_base: dict | None = None) -> dict:
    rk, pk = f"context_recall@{k}", f"context_precision@{k}"
    dr, dp = arm[rk] - base[rk], arm[pk] - base[pk]
    f = flips(base, arm, k)
    if ctx_base is not None:      # contextual arm: measured against hybrid_rerank
        gain = arm[rk] - ctx_base[rk]
        return {"rule": f"contextual must add >= +{SHIP['contextual_extra_recall']:.2f} "
                        f"recall@{k} over hybrid_rerank",
                "recall_gain_over_hybrid": round(gain, 4),
                "ship": gain >= SHIP["contextual_extra_recall"], "flips": f}
    primary = dr >= SHIP["recall_gain"] or dp >= SHIP["precision_gain"]
    other_ok = (dp >= -SHIP["max_other_regression"] if dr >= SHIP["recall_gain"]
                else dr >= -SHIP["max_other_regression"])
    return {"rule": f"(d_recall >= +{SHIP['recall_gain']:.2f} OR d_precision >= "
                    f"+{SHIP['precision_gain']:.2f}) AND other >= "
                    f"-{SHIP['max_other_regression']:.2f} AND net flips >= "
                    f"+{SHIP['min_net_flips']}",
            "d_recall": round(dr, 4), "d_precision": round(dp, 4), "flips": f,
            "ship": bool(primary and other_ok and f["net"] >= SHIP["min_net_flips"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="dense", help="comma-separated subset of " + ",".join(ARMS))
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--candidate-n", type=int, default=20)
    ap.add_argument("--rrf-k", type=int, default=60)
    ap.add_argument("--mode", default="either", choices=["either", "gold", "locator"],
                    help="relevance predicate; see retrieval_metrics.py")
    ap.add_argument("--set", default=os.path.join(HERE, "eval_set_v2.json"))
    ap.add_argument("--out", default=None, help="write the full run log (JSON) here")
    a = ap.parse_args()

    spec = json.load(open(a.set))
    cases = spec["cases"]
    want = [x.strip() for x in a.arms.split(",") if x.strip()]
    bad = [x for x in want if x not in ARMS]
    if bad:
        print(f"unknown arm(s): {bad}; valid: {list(ARMS)}")
        return 2
    if not spec.get("reviewed_by_alex"):
        print("NOTE: eval_set reviewed_by_alex=false — these numbers are indicative, "
              "they do not gate anything yet.\n")

    rk, pk = f"context_recall@{a.k}", f"context_precision@{a.k}"
    print(f"3-arm retrieval A/B | doc={spec['doc']} | {len(cases)} cases | k={a.k} | "
          f"predicate={a.mode}\n" + "=" * 78)
    blocks, errors = {}, {}
    for name in want:
        print(f"\n--- {name} ---")
        try:
            b = run_arm(name, cases, a.k, a.mode,
                        candidate_n=a.candidate_n, rrf_k=a.rrf_k)
        except MigrationMissing as e:
            print(f"SKIPPED — {e}")
            errors[name] = str(e)
            continue
        blocks[name] = b
        print(f"  {rk:<24} {b[rk]:.3f}")
        print(f"  {pk:<24} {b[pk]:.3f}")
        print(f"  {'strict gold-only recall':<24} {b['strict_gold'][rk]:.3f}")
        print(f"  {'latency ms (p50/p95/max)':<24} "
              f"{b['latency_ms']['p50']}/{b['latency_ms']['p95']}/{b['latency_ms']['max']}")
        misses = sorted(i for i, v in b["per_case_recall"].items() if not v)
        print(f"  {'misses':<24} {misses or 'none'}")

    if "dense" in blocks:
        for name in ("hybrid_rerank", "contextual_hybrid_rerank"):
            if name not in blocks:
                continue
            ctx = blocks.get("hybrid_rerank") if name == "contextual_hybrid_rerank" else None
            v = verdict(blocks["dense"], blocks[name], a.k, ctx)
            print(f"\n--- ship rule: {name} ---\n  {v['rule']}")
            print(f"  {json.dumps({x: y for x, y in v.items() if x != 'rule'})}")
            print(f"  -> {'SHIP' if v['ship'] else 'DO NOT SHIP'}")
            blocks[name]["verdict"] = v

    if a.out:
        payload = {"eval_set": os.path.basename(a.set), "k": a.k, "mode": a.mode,
                   "reviewed_by_alex": spec.get("reviewed_by_alex", False),
                   "candidate_n": a.candidate_n, "rrf_k": a.rrf_k,
                   "arms": {n: {x: y for x, y in b.items() if x != "_raw"}
                            for n, b in blocks.items()},
                   "skipped": errors}
        json.dump(payload, open(a.out, "w"), indent=2)
        print(f"\nrun log -> {a.out}")
    return 0 if blocks else 1


if __name__ == "__main__":
    sys.exit(main())
