---
description: Ask a question over the document knowledge base — semantic retrieval + a grounded, cited answer. YED-118.
---

# /ask-library — semantic Q&A over the knowledge base

Embeds the question locally (bge-small, with the bge query instruction), runs the
`match_doc_chunks` pgvector RPC over REST, and returns the top-k passages with
citations. **Claude then synthesizes the grounded answer from those passages** —
the script retrieves; the answer is composed here, cited, and never beyond the
retrieved text.

**Skill:** `.claude/skills/doc-knowledge-base/`.

## Steps

1. **Intake.** Take the question from Alex. Optional: `--k <n>` (default 8),
   `--doc <document_uuid>` to scope to one document.
2. **Retrieve.** Run from the repo root:
   ```
   ./.venv/bin/python ".claude/skills/doc-knowledge-base/ask_library.py" "<question>" --k 8
   ```
   (Add `--json` when you want structured passages to work with programmatically.)
   This is a read (RPC + a documents lookup); approve the network prompt if shown.
3. **Synthesize.** Read the returned passages and write a grounded answer that:
   - uses **only** what the passages support (say so if they don't answer it);
   - **cites** each claim as `<doc_title> — <section/page>` (locators are page ranges for PDFs);
   - notes similarity/uncertainty when the top passages are weak (< ~0.5) or off-topic.
4. **Output.** Present the answer first, then a short "Sources" list of the cited passages.

## Failure modes
- **"No passages found"** → nothing ingested yet, or the `--doc` filter is wrong. Run `/ingest-doc` first.
- **Weak/irrelevant top passages** → say the library doesn't cover it rather than forcing an answer;
  suggest ingesting a doc that does.
- **Classifier blocks the read** → approve the Bash action.

## Note
Retrieval quality gate: recall@8 = 88% on *Inference Engineering* (see the skill's `eval_retrieval.py`).
Front-matter (TOC) pages can occasionally rank in — discount them when synthesizing.
