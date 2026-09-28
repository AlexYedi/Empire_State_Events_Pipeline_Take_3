#!/usr/bin/env python3
"""YED-156 A.5 — local cross-encoder reranker. Zero metered calls, CPU-only.

The hybrid arm over-fetches candidates from `match_doc_chunks_hybrid` (RRF over
dense + keyword) and then reorders them here. A bi-encoder embeds query and
passage independently, so it can only ever compare two frozen points in one
vector space; a cross-encoder reads (query, passage) jointly and scores the
pair, which is why it reliably fixes the top of the list. The cost is that it
cannot be precomputed — every pair is a forward pass — hence: over-fetch a few
dozen, rerank, keep the top n.

Model is PINNED by revision. Ingest-time embeddings are pinned separately in
dockb_common.EMBED_MODEL; the reranker is independent of them (it never touches
the vector index), so it can be swapped without re-embedding anything.

Measured on this machine (Apple Silicon, CPU, first run incl. download):
see `python rerank.py --bench` — it prints load time, latency for 20 pairs,
and on-disk model size so the numbers in the PRD stay honest.
"""
from __future__ import annotations
import argparse, os, time
from functools import lru_cache

# bge-reranker-base: 278M params, ~1.1 GB fp32 on disk, XLM-RoBERTa-base
# backbone. Chosen over bge-reranker-v2-m3 (568M, ~2.3 GB) because this runs on
# Alex's laptop CPU inside an eval loop, and over ms-marco-MiniLM-L-6-v2 (~90 MB)
# because the quality gap on technical prose is the whole point of the arm.
# Fallback if latency proves unacceptable: cross-encoder/ms-marco-MiniLM-L-6-v2.
RERANK_MODEL = "BAAI/bge-reranker-base"
RERANK_REVISION = "2cfc18c9415c912f9d8155881c133215df768a70"  # pinned; see --bench output
MAX_LENGTH = 512


@lru_cache(maxsize=1)
def _model():
    """Lazy singleton. First call downloads (~1.1 GB) into the HF cache."""
    from sentence_transformers import CrossEncoder
    return CrossEncoder(RERANK_MODEL, revision=RERANK_REVISION,
                        max_length=MAX_LENGTH, device="cpu")


def rerank(query: str, candidates: list[dict], top_n: int = 8,
           text_key: str = "content") -> list[dict]:
    """Reorder `candidates` by cross-encoder relevance to `query`; return the top_n.

    Each returned dict is the ORIGINAL candidate dict with `rerank_score` (raw
    logit, higher is better; not calibrated across queries) and `rerank_rank`
    added, so downstream metric code still sees `content` / `locator` / `id`.
    Candidates are not mutated in place — shallow copies are returned.
    Passing fewer than `top_n` candidates returns all of them, reordered.
    """
    if not candidates:
        return []
    texts = [c.get(text_key) or "" for c in candidates]
    if os.environ.get("DOCKB_RERANK_CONTEXT") and any(c.get("context") for c in candidates):
        # contextual arm: score the situated text the way it was indexed
        texts = [((c.get("context") or "") + " " + (c.get(text_key) or "")).strip()
                 for c in candidates]
    scores = _model().predict([(query, t) for t in texts],
                              show_progress_bar=False, batch_size=16)
    order = sorted(range(len(candidates)), key=lambda i: float(scores[i]), reverse=True)
    out = []
    for rank, i in enumerate(order[:top_n], 1):
        c = dict(candidates[i])
        c["rerank_score"] = float(scores[i])
        c["rerank_rank"] = rank
        out.append(c)
    return out


def _dir_size(path: str) -> int:
    """Bytes on disk. HF snapshots are symlinks into a shared blob store, so this
    follows links (os.stat, not lstat) and dedupes by inode to avoid double-counting."""
    seen, total = set(), 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                st = os.stat(os.path.join(root, f))       # follows symlinks
            except OSError:
                continue
            if st.st_ino in seen:
                continue
            seen.add(st.st_ino)
            total += st.st_size
    return total


def bench(n_pairs: int = 20) -> dict:
    """Measure load time, latency for n_pairs, and on-disk size. Printed, not asserted."""
    from huggingface_hub import snapshot_download
    t0 = time.perf_counter()
    m = _model()
    load_s = time.perf_counter() - t0

    q = "How much VRAM headroom over the model weights should I budget?"
    passage = ("The total amount of VRAM on a GPU limits the size of the model you can load "
               "onto it. The VRAM should hold the model weights, plus at least 50 percent "
               "headroom for KV cache (more for long context, high batch sizes, or video "
               "generation models). If there isn't enough VRAM available for the weights, "
               "loading the model will fail with an OOM (out of memory) error. ") * 3
    pairs = [(q, passage) for _ in range(n_pairs)]

    m.predict(pairs[:2], show_progress_bar=False)          # warm the graph
    t0 = time.perf_counter()
    m.predict(pairs, show_progress_bar=False, batch_size=16)
    pred_s = time.perf_counter() - t0

    cache = snapshot_download(RERANK_MODEL, revision=RERANK_REVISION)
    # The repo ships three copies of the same weights (safetensors + .bin + onnx);
    # only model.safetensors is loaded. Report both so "model size" is not misread.
    weights = os.path.join(cache, "model.safetensors")
    res = {"model": RERANK_MODEL, "revision": RERANK_REVISION,
           "load_seconds": round(load_s, 2), "n_pairs": n_pairs,
           "batch_seconds": round(pred_s, 3),
           "ms_per_pair": round(pred_s / n_pairs * 1000, 1),
           "weights_loaded_mb": round(os.stat(weights).st_size / 1e6, 1),
           "cache_total_mb": round(_dir_size(cache) / 1e6, 1),
           "cache_path": cache,
           "max_length": MAX_LENGTH, "device": "cpu"}
    for k, v in res.items():
        print(f"  {k:>16}: {v}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", action="store_true", help="report load time / latency / size")
    ap.add_argument("--pairs", type=int, default=20)
    a = ap.parse_args()
    if a.bench:
        bench(a.pairs)
    else:
        ap.print_help()
