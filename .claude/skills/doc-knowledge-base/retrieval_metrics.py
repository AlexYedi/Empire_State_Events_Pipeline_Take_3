#!/usr/bin/env python3
"""YED-156 A.5 — vendored retrieval metrics. Deterministic, offline, zero metered calls.

WHY VENDORED INSTEAD OF RAGAS
-----------------------------
The PRD asks for the non-LLM retrieval metrics only. Ragas' headline
`context_recall` / `context_precision` are LLM-judged by default: they call a
model to decide whether each retrieved context supports the reference answer.
That is metered, non-deterministic, and makes the A/B's own measuring stick
drift between arms. Ragas does ship `NonLLMContextRecall` /
`NonLLMContextPrecisionWithReference`, but those compare retrieved contexts to
full *reference context strings* by fuzzy string distance over a threshold — a
noisier contract than "does this chunk contain the gold phrase", and it would
require pasting whole passages into the eval set. For that we would take
langchain-core + pydantic pinning + datasets, on a package whose API broke
across 0.1 -> 0.2 -> 0.3. The whole computation we need is below, in ~40 lines.

Recommendation: do NOT take the Ragas dependency for this. Confidence ~88%.
Revisit only if/when we want LLM-judged *answer* metrics (faithfulness, answer
relevancy) — a different job, with a metered budget attached, and by then the
Tier-2 judge in `.claude/evals/` is the house-native place for it anyway.

THE RELEVANCE PREDICATE (the load-bearing decision)
---------------------------------------------------
A retrieved chunk counts as relevant to a case if EITHER:
  (a) GOLD  — its text contains the case's `gold` phrase, after normalization; or
  (b) LOCATOR — its locator (page/section range) intersects the case's
      reference locator.

Why OR, and not gold alone: the continuous token-window packer splits on token
budget, not on sentence boundaries, so a gold phrase can straddle two adjacent
chunks. When it does, the chunk that IS the correct passage scores as a miss —
a defect in the measurement, not in retrieval. (Phase A already hit this and
wrote it off as "a metric artifact".) Locator overlap repairs exactly that case.

Why not locator alone: a ~400-token chunk spans one to three pages, and a page
holds several unrelated passages, so pure locator matching over-credits
neighbors and inflates precision.

Both metrics use the SAME predicate on purpose — mixing predicates makes
recall and precision non-comparable. `mode` lets you recompute under the strict
gold-only predicate, and the harness reports both so a loosened predicate can
never be mistaken for a retrieval win.

CEILING NOTE: most cases have exactly one authoring passage, so
context_precision@8 has a low natural ceiling (~1-3/8). It is a RELATIVE signal
across arms, never an absolute quality score.
"""
from __future__ import annotations
import re, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dockb_common as dk  # noqa: E402

# Rejoin a hyphen that splits a word, INCLUDING across a line break. The PDF
# breaks words at the margin ("com- pute-bound", "quan- tization"); the epub
# does not. Dropping the hyphen on BOTH sides makes the two extractions
# comparable without guessing which hyphens are real. Requires alphanumerics on
# both sides, so a standalone " - " dash survives.
_HYPHEN_JOIN = re.compile(r"(?<=[A-Za-z0-9])-\s*(?=[A-Za-z0-9])")
_PAGE = re.compile(r"p\.(\d+)")


def normalize_text(s: str) -> str:
    """Case/whitespace fold + ligature repair + de-hyphenation. Applied to BOTH sides.

    Repairing ligatures on the *retrieved* side is deliberate: it makes a gold
    match measure RETRIEVAL rather than the vintage of the extraction that built
    the index. (The live Phase-A index predates the ligature fix and still holds
    `prefi ll`; without this the ligature cases would fail for the wrong reason.)
    """
    return re.sub(r"\s+", " ", _HYPHEN_JOIN.sub("", dk.repair_ligatures(s))).lower().strip()


def _pages(loc) -> set[int]:
    """Page numbers named by a locator. Accepts 'p.12', 'p.12-p.14', a list, or a dict."""
    if loc is None:
        return set()
    if isinstance(loc, dict):
        loc = loc.get("pdf_pages") or loc.get("section") or ""
    if isinstance(loc, (list, tuple)):
        return set().union(*(_pages(x) for x in loc)) if loc else set()
    nums = [int(n) for n in _PAGE.findall(str(loc))]
    return set(range(min(nums), max(nums) + 1)) if nums else set()


def _sections(loc) -> set[str]:
    """Section titles named by a locator (epub side); empty for page-only locators."""
    if isinstance(loc, dict):
        loc = loc.get("epub_section") or loc.get("section") or ""
    if isinstance(loc, (list, tuple)):
        return set().union(*(_sections(x) for x in loc)) if loc else set()
    s = normalize_text(str(loc))
    return {s} if s and not _PAGE.search(str(loc)) else set()


def is_relevant(chunk: dict, case: dict, mode: str = "either") -> bool:
    """True if `chunk` is the passage `case` was authored from. See module docstring."""
    gold = normalize_text(case["gold"]) in normalize_text(chunk.get("content", ""))
    if mode == "gold":
        return gold
    ref, got = case.get("locator"), chunk.get("locator")
    loc = bool(_pages(ref) & _pages(got)) or bool(_sections(ref) & _sections(got))
    return loc if mode == "locator" else (gold or loc)


def context_recall(retrieved: list[dict], case: dict, k: int, mode: str = "either") -> float:
    """Fraction of the case's reference passages surfaced in the top-k.

    Each case is authored from exactly one passage, so this is 1.0 if any top-k
    chunk is relevant and 0.0 otherwise — a per-case hit. Average over cases for
    context_recall@k.
    """
    return 1.0 if any(is_relevant(c, case, mode) for c in retrieved[:k]) else 0.0


def context_precision(retrieved: list[dict], case: dict, k: int, mode: str = "either") -> float:
    """Share of the top-k that is relevant. Averaged over cases for context_precision@k."""
    top = retrieved[:k]
    return (sum(is_relevant(c, case, mode) for c in top) / len(top)) if top else 0.0


def first_hit_rank(retrieved: list[dict], case: dict, k: int, mode: str = "either") -> int | None:
    """1-based rank of the first relevant chunk in the top-k, or None."""
    return next((i + 1 for i, c in enumerate(retrieved[:k]) if is_relevant(c, case, mode)), None)


def score_set(results: dict[str, list[dict]], cases: list[dict], k: int,
              mode: str = "either") -> dict:
    """Aggregate {case_id -> retrieved chunks} into the arm's metric block."""
    by_id = {c["id"]: c for c in cases}
    rec = {cid: context_recall(r, by_id[cid], k, mode) for cid, r in results.items()}
    pre = {cid: context_precision(r, by_id[cid], k, mode) for cid, r in results.items()}
    n = max(len(rec), 1)
    return {
        "k": k, "mode": mode, "n_cases": len(rec),
        f"context_recall@{k}": sum(rec.values()) / n,
        f"context_precision@{k}": sum(pre.values()) / n,
        "per_case_recall": rec,
        "per_case_precision": pre,
        "ranks": {cid: first_hit_rank(r, by_id[cid], k, mode) for cid, r in results.items()},
    }
