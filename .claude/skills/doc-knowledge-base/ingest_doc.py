#!/usr/bin/env python3
"""YED-118 /ingest-doc — ingest one document into the knowledge base.

Flow: sha256 dedup -> upload raw blob to R2 -> extract text (epub|pdf) ->
chunk -> embed locally (bge-small, 384-d) -> insert documents + doc_chunks
into Supabase pgvector over REST.

Usage:
  python ingest_doc.py <path> [--title T] [--author A] [--source-type book|whitepaper|filing|pdf]
"""
import argparse, os, sys, uuid
import dockb_common as dk

BATCH = 100  # doc_chunks rows per REST insert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--title", default=None)
    ap.add_argument("--author", default=None)
    ap.add_argument("--source-type", default=None,
                    choices=["book", "whitepaper", "filing", "pdf", "other"])
    args = ap.parse_args()

    path = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isfile(path):
        sys.exit(f"ERROR: file not found: {path}")
    fname = os.path.basename(path)
    ext = os.path.splitext(fname)[1].lower()

    with open(path, "rb") as f:
        blob = f.read()
    sha = dk.sha256_bytes(blob)

    # 1. dedup
    status, rows = dk.supa("GET", f"/documents?sha256=eq.{sha}&select=id,title")
    if rows:
        print(f"SKIP (already ingested): {rows[0]['title']}  id={rows[0]['id']}")
        return

    # 2. extract
    print(f"Extracting {ext} ...")
    if ext == ".epub":
        sections, meta = dk.extract_epub(path)
        stype = args.source_type or "book"
    elif ext == ".pdf":
        sections, meta = dk.extract_pdf(path)
        stype = args.source_type or "pdf"
    else:
        sys.exit(f"ERROR: unsupported extension {ext} (epub|pdf only)")
    if not sections:
        sys.exit("ERROR: no extractable text found")

    title = args.title or meta.get("title") or fname
    author = args.author or meta.get("author")
    word_count = sum(len(s["text"].split()) for s in sections)

    # 3. chunk
    chunks = dk.chunk_sections(sections)
    print(f"  {len(sections)} sections -> {len(chunks)} chunks "
          f"(~{word_count:,} words)")

    # 4. embed
    print("Embedding (local bge-small) ...")
    vectors = dk.embed_passages([c["content"] for c in chunks])

    # 5. upload blob to R2 (id chosen client-side so it keys the blob)
    doc_id = str(uuid.uuid4())
    blob_key = f"{doc_id}/{fname}"
    print(f"Uploading blob -> r2://{dk.env()['R2_BUCKET']}/{blob_key}")
    dk.r2_put(blob_key, blob)

    # 6. insert documents row
    dk.supa("POST", "/documents", body=[{
        "id": doc_id, "title": title, "author": author, "source_type": stype,
        "blob_key": blob_key, "sha256": sha, "word_count": word_count,
        "embedding_model": dk.EMBED_MODEL,
    }])

    # 7. insert doc_chunks in batches
    rows = [{
        "document_id": doc_id, "chunk_index": i, "content": c["content"],
        "embedding": dk.vec_literal(v), "token_count": c["token_count"],
        "locator": c["locator"],
    } for i, (c, v) in enumerate(zip(chunks, vectors))]
    for b in range(0, len(rows), BATCH):
        dk.supa("POST", "/doc_chunks", body=rows[b:b + BATCH])
        print(f"  inserted chunks {b}..{min(b+BATCH, len(rows))-1}")

    print(f"\nDONE: '{title}'\n  doc_id={doc_id}\n  chunks={len(rows)}  "
          f"words={word_count:,}\n  blob={blob_key}")


if __name__ == "__main__":
    main()
