---
name: doc-knowledge-base
description: Cloud document knowledge base + semantic RAG (YED-118). Ingest long-form reference docs (books, whitepapers, filings, PDFs) into R2 blob storage + Supabase pgvector, then answer questions with cited passages. Use for /ingest-doc and /ask-library, or when Alex asks "what does <book/doc> say about X" over the reference library.
---

# Document Knowledge Base (YED-118)

Semantic "ask my library" over long-form reference documents, and (Phase B) a
producer of Market-Intelligence signals. **PRD:** ChatPRD `c5add9ef…` / Notion
Project Ideas `3d6d3699…`. **Milestone:** MI-Engine M3, pillar 2.

## Architecture — two decoupled stores
- **Blob store — Cloudflare R2** (S3-compatible). Raw epub/PDF originals, touched
  only at ingest. Keys `R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY /
  R2_BUCKET=esep-library` in `.env`. Object key = `{doc_id}/{filename}`.
- **Vector index — Supabase pgvector** in `empire state ai` (`oicikjyzmxqfomrrqkvf`),
  REST + `SUPABASE_API_KEY` (never the MCP). Tables `documents` + `doc_chunks`,
  RPC `match_doc_chunks`. DDL: `.claude/references/doc-kb-schema.sql` (applied once
  in the dashboard; RLS enabled, service-key-only).
- **Embeddings — local `BAAI/bge-small-en-v1.5` (384-d)** via sentence-transformers.
  Zero metered cost. **Hard invariant: ingest and query use the identical model+version**
  (pinned as `EMBED_MODEL` in `dockb_common.py`). Fallback if a future doc under-recalls:
  `BAAI/bge-base-en-v1.5` (768-d) — requires a full re-embed + `vector(768)` schema change.

## Files
- `dockb_common.py` — shared lib: env, embeddings, R2, Supabase REST, extraction, chunking.
- `ingest_doc.py` — `/ingest-doc`. sha256 dedup → R2 upload → extract → chunk → embed → REST insert.
- `ask_library.py` — `/ask-library`. embed query → `match_doc_chunks` RPC → top-k passages + citations.
- `eval_retrieval.py` + `eval_set.json` — Phase-A retrieval acceptance gate (recall@k).
- **Phase A.5 (YED-156) — RAG upgrade, DB-independent half:**
  - `eval_set_v2.json` — 25 practitioner Q/A cases authored from the book, each with
    `reference_answer` / `gold` / measured `locator` / `tags`. 5 `paraphrase` cases carry
    **zero** content-word overlap with their gold (dense has to earn those); 4
    `ligature_target` cases sit on former-ligature words (prefill/specific/configuration)
    that v1 deliberately dodged. `reviewed_by_alex: false` — **it gates nothing until Alex approves it.**
  - `validate_eval_set.py` — proves every `gold` occurs in BOTH the epub and PDF
    extractions, enforces the two guards, and backfills measured locators (`--fix`).
  - `retrieval_metrics.py` — vendored `context_recall@k` / `context_precision@k`.
    Relevance = gold-phrase containment **OR** locator overlap; both metrics share the
    predicate. Also owns `normalize_text` (ligature repair + de-hyphenation, applied to
    both sides). **Ragas deliberately not taken** — rationale in the module docstring.
  - `rerank.py` — local cross-encoder `BAAI/bge-reranker-base`, revision-pinned, CPU.
    `--bench` reports load time / latency / size. Measured: 2.6 s warm load, **39 ms per
    pair** (20 pairs in 0.78 s), 1.11 GB weights. Zero metered calls.
  - `ab_harness.py` — 3 arms (`dense` | `hybrid_rerank` | `contextual_hybrid_rerank`) with
    per-arm recall/precision, question flips vs. baseline, p95 latency, and the PRD ship rule.
    The two hybrid arms **detect the un-applied A.5 migration and exit with the fix**.
- `requirements.txt` — deps.

## One-time setup (per checkout — `.venv` is gitignored/worktree-local)
```
python3 -m venv .venv
./.venv/bin/pip install -r .claude/skills/doc-knowledge-base/requirements.txt
```
**Local library:** large docs live in `~/Documents/Knowledge Library/{books,whitepapers,filings,other}/` (outside every repo; NOT iCloud-synced; R2 is the archive of record — pull back from R2 if lost). `/ingest-doc` resolves bare filenames against it; override with `DOC_LIBRARY_DIR` in `.env`.
(Worktrees also need `.env` symlinked to the main checkout — see [[project_worktree_env_missing_2026-09-08]].)

## Chunking
Continuous token-window packer over line-units tagged with page/section label:
uniform ~400-token chunks (hard cap 512, bge's max), ~60-token overlap **across page
boundaries**, page-range locators (`p.21–p.22`). Preserves original text. Fixes the
naive "one-chunk-per-page" + oversized-chunk failure.

## Retrieval quality (acceptance gate)
`eval_retrieval.py` scores recall@k (hit = any top-k chunk contains the gold phrase).
**Inference Engineering: recall@8 = 88% (7/8), bar 80% → PASS** with bge-small.
Run: `./.venv/bin/python .claude/skills/doc-knowledge-base/eval_retrieval.py --k 8`.
(The one strict-metric miss — "quantization" → a terse summary bullet — retrieves the
real quantization content fine; it's a metric artifact, not a capability gap.)

## Phase A.5 baseline (2026-09-11, `eval_set_v2.json`, k=8)
`dense` arm against the live index: **context_recall@8 = 0.840 (21/25)**,
context_precision@8 = 0.175, latency p50 298 ms / p95 554 ms.
Misses: `ie-003`, `ie-015`, `ie-019`, `ie-027` — **3 of the 4 are paraphrase cases**, i.e.
exactly the class dense retrieval is supposed to earn and currently does not. Two of them
also return a table-of-contents page (`p.6`) inside the top-8.
Run log: `.claude/evals/logs/2026-09-11-doc-kb-a5-ab-baseline.json`.
```
./.venv/bin/python .claude/skills/doc-knowledge-base/ab_harness.py --arms dense --k 8
```

> ⚠️ **The live index is STALE relative to the extractor.** It was ingested from the PDF on
> 2026-09-10, *before* the format hardening (`ba006f9`), so it still contains 19 `prefi ll`,
> 8 `confi guration`, 24 `specifi c` and 191 dot-leader TOC lines. The baseline above is a
> floor, not the extractor's true ceiling. **Re-ingest before treating these numbers as the
> comparison baseline for the hybrid arms** — otherwise the A/B measures an extractor
> upgrade and a retrieval upgrade at the same time and attributes both to retrieval.

## Known limitations (V1 — backlog, none block the gate)
- **PDF ligature artifacts** (`prefi ll`, `confi gure`) from pymupdf — cosmetic in
  citations + a minor retrieval drag. Prefer epub. Backlog: ligature-normalize at extract.
- **Front-matter noise** — TOC/index pages can appear in results. Backlog: skip front-matter at ingest.
- PDF is best-effort (page-based locators); epub gives cleaner structure.

## Phase B (not built — fast-follow)
Bridge doc claims into the MI graph: notable claims → `event` rows (`kind=market/reference`,
`source`=doc citation + chunk locator), linked via `event_entity` to the topics/companies
they discuss. Open design question: how claims are selected (manual flag vs LLM extraction pass).
