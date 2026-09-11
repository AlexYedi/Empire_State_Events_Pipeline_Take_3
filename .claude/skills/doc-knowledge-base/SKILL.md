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
- `eval_retrieval.py` + `eval_set.json` — retrieval acceptance gate (recall@k).
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

## Known limitations (V1 — backlog, none block the gate)
- **PDF ligature artifacts** (`prefi ll`, `confi gure`) from pymupdf — cosmetic in
  citations + a minor retrieval drag. Prefer epub. Backlog: ligature-normalize at extract.
- **Front-matter noise** — TOC/index pages can appear in results. Backlog: skip front-matter at ingest.
- PDF is best-effort (page-based locators); epub gives cleaner structure.

## Phase B (not built — fast-follow)
Bridge doc claims into the MI graph: notable claims → `event` rows (`kind=market/reference`,
`source`=doc citation + chunk locator), linked via `event_entity` to the topics/companies
they discuss. Open design question: how claims are selected (manual flag vs LLM extraction pass).
