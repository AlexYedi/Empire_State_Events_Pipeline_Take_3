#!/usr/bin/env python3
"""YED-118 /ask-library — semantic retrieval over the knowledge base.

Embeds the question locally (bge-small, with the bge query instruction),
runs the match_doc_chunks pgvector RPC over REST, and prints the top-k
passages with citations. The grounded ANSWER is synthesized by the calling
command (Claude) from these passages — this script only retrieves.

Usage:
  python ask_library.py "question" [--k 8] [--doc <document_uuid>] [--json]
"""
import argparse, json
import dockb_common as dk


def retrieve(question: str, k: int = 8, doc_id: str | None = None) -> list[dict]:
    qvec = dk.embed_query(question)
    body = {"query_embedding": qvec, "match_count": k}
    if doc_id:
        body["filter_document_id"] = doc_id
    _, rows = dk.supa("POST", "/rpc/match_doc_chunks", body=body)
    rows = rows or []
    # map document_id -> title for citations
    ids = sorted({r["document_id"] for r in rows})
    titles = {}
    if ids:
        _, docs = dk.supa("GET", f"/documents?id=in.({','.join(ids)})&select=id,title,author")
        titles = {d["id"]: d for d in (docs or [])}
    for r in rows:
        d = titles.get(r["document_id"], {})
        r["doc_title"] = d.get("title", "?")
        r["doc_author"] = d.get("author")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--doc", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = retrieve(args.question, args.k, args.doc)
    if args.json:
        print(json.dumps(rows, indent=2))
        return

    if not rows:
        print("No passages found. (Is anything ingested yet?)")
        return
    print(f"Q: {args.question}\n{'='*70}")
    for i, r in enumerate(rows, 1):
        loc = r.get("locator") or {}
        sec = loc.get("section", "?")
        print(f"\n[{i}] {r['doc_title']} — {sec}   (similarity {r['similarity']:.3f})")
        content = r["content"]
        print(content if len(content) <= 900 else content[:900] + " …")
    print(f"\n{'='*70}\n{len(rows)} passages. Cite as: <doc_title> — <section>.")


if __name__ == "__main__":
    main()
