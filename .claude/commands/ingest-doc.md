---
description: Ingest a long-form document (epub/PDF) into the knowledge base — R2 blob + Supabase pgvector, local embeddings. YED-118.
---

# /ingest-doc — add a document to the knowledge base

Ingests one document end-to-end: sha256 dedup → upload raw blob to Cloudflare R2 →
extract text → chunk → embed locally (bge-small, 384-d) → insert `documents` +
`doc_chunks` into Supabase pgvector over REST. Zero metered cost.

**Skill:** `.claude/skills/doc-knowledge-base/` (methodology, architecture, limits).

## Steps

1. **Intake.** Get the file path from Alex (epub preferred; PDF best-effort). Confirm it
   exists. Optional overrides: `--title`, `--author`, `--source-type book|whitepaper|filing|pdf`
   (title/author auto-read from file metadata if omitted).
2. **Preflight.** Ensure the repo venv exists (`.venv/bin/python`); if not, run the one-time
   setup from the skill's SKILL.md. Ensure `.env` is present (symlink in worktrees).
3. **Ingest.** Run from the repo root:
   ```
   ./.venv/bin/python ".claude/skills/doc-knowledge-base/ingest_doc.py" "<path>" [--source-type book]
   ```
   This makes authenticated network writes (R2 + Supabase) — **the network-write classifier will
   prompt; approve it.** A large book embeds in ~30–60s on CPU.
4. **Report** the result to Alex: title, `doc_id`, chunk count, word count, blob key. If the doc
   was already present, the script prints `SKIP` (sha256 dedup) — surface that, don't re-ingest.

## Failure modes
- **Unsupported extension** → only `.epub` / `.pdf`. Convert or supply another format.
- **Classifier blocks the write** → approve the Bash action / add a permission rule; the whole
  pipeline is REST writes.
- **`create extension`/table 404** → the DDL (`.claude/references/doc-kb-schema.sql`) wasn't applied
  to `oicikjyzmxqfomrrqkvf`. Apply it in the dashboard first.
- **Oversized/garbled chunks** → check the extraction preview; PDF ligature artifacts are a known
  limit (prefer epub).

## Verify
`/ask-library "<a question the doc answers>"` should return cited passages from it.
