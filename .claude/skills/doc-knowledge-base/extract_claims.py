#!/usr/bin/env python3
"""YED-157 B2 — extract candidate claims from an ingested doc into doc_claims.

Writes ONLY to the `doc_claims` staging table (status='candidate'). Nothing
reaches the MI graph here — promotion to `event` happens at the /doc-digest
gate, after Alex approves line by line.

Backend: Gemini (GEMINI_API_KEY), matching the house adapter convention in
.claude/hooks/gemini-judge.sh. Zero Claude tokens. Implemented in Python rather
than the PRD's sketched bash because it reuses dockb_common's extraction and
Supabase REST helpers; the model stays a swappable adapter (`extractor` /
`extractor_model` columns), which was the PRD's actual requirement.

Idempotent: claim_key = sha256(normalized claim text); the table is unique on
(document_sha256, claim_key) and inserts use resolution=ignore-duplicates, so
re-running adds nothing.

Usage:
  python extract_claims.py "Inference Engineering" [--limit N] [--dry-run]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, time, urllib.request, urllib.error
import dockb_common as dk

MODEL_DEFAULT = "gemini-pro-latest"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
MIN_SECTION_CHARS = 600          # skip stubs/front matter
QUOTE_WORD_CAP = 25              # licensing guard (PRD §3f)

PROMPT = """You extract NOTABLE CLAIMS from one section of a reference book, for a \
market-intelligence graph owned by Alex — a senior enterprise B2B SaaS / GTM professional \
building AI-native products and job-searching at AI-native companies.

A claim is NOTABLE only if it changes something for ONE of these two lenses:
  - JOB-SEARCH: ammunition for an interview at an AI-infra/AI-native company (a number, a
    tradeoff, a practitioner opinion he could credibly reference).
  - CONTENT: a thesis, tension, or non-obvious fact he could write about.
Generic textbook definitions, restatements of common knowledge, and section summaries are
NOT notable. If the section contains nothing notable, return an empty array. Abstaining is
correct and expected — most sections yield 0-2 claims.

For each claim return:
  claim_text  : one self-contained sentence stating the claim (your words, not the book's)
  claim_type  : one of thesis | statistic | practice | tradeoff | prediction | definition
  why_notable : <= 20 words naming WHAT IT CHANGES, and for which lens (job-search|content)
  quote       : the book's own supporting words, VERBATIM, MAXIMUM 25 WORDS (hard limit)
  entities    : [{"type":"topic"|"company","name":"..."}] that the claim is about (propose
                only; do not invent entities that are not clearly named or implied)
  confidence  : 0.0-1.0, your own confidence this is both accurate and notable

Return ONLY JSON: {"claims":[ ... ]}
"""


def gemini(prompt: str, model: str) -> dict:
    key = dk.env().get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("ERROR: GEMINI_API_KEY not set — use the manual-flag path "
                 "(/ask-library --flag) or add the key to .env")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8000,
                             "responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(GEMINI_URL.format(m=model), data=body, method="POST",
                                 headers={"x-goog-api-key": key,
                                          "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                payload = json.loads(r.read().decode())
            text = (payload.get("candidates", [{}])[0].get("content", {})
                    .get("parts", [{}])[0].get("text", ""))
            if not text:
                return {"claims": []}          # model abstained / empty part
            return json.loads(text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:200]
            if e.code in (429, 500, 503) and attempt < 2:
                time.sleep(4 * (attempt + 1)); continue
            sys.exit(f"ERROR: Gemini HTTP {e.code} — {detail}")
        except (json.JSONDecodeError, KeyError, IndexError):
            if attempt < 2:
                time.sleep(2); continue
            return {"claims": []}
    return {"claims": []}


def window_sections(sections: list[dict], target_words: int = 2500) -> list[dict]:
    """Merge consecutive page-sections into ~target_words windows.

    PDF extraction yields one section per PAGE, which is the wrong unit for claim
    extraction: too small to hold an argument, and a claim spanning a page break
    gets severed. epub sections are already semantic (chapter > heading) and pass
    through untouched.
    """
    out, buf, words, first = [], [], 0, None
    for sec in sections:
        n = len(sec["text"].split())
        if buf and words + n > target_words:
            out.append({"title": (first if first == buf[-1][0] else f"{first}-{buf[-1][0]}"),
                        "index": len(out), "text": "\n\n".join(t for _, t in buf)})
            buf, words, first = [], 0, None
        if first is None:
            first = sec["title"]
        buf.append((sec["title"], sec["text"])); words += n
    if buf:
        out.append({"title": (first if first == buf[-1][0] else f"{first}-{buf[-1][0]}"),
                    "index": len(out), "text": "\n\n".join(t for _, t in buf)})
    return out


def claim_key(text: str) -> str:
    norm = re.sub(r"[^a-z0-9 ]", "", text.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    return hashlib.sha256(norm.encode()).hexdigest()[:32]


def trim_quote(q: str) -> str:
    words = (q or "").split()
    return " ".join(words[:QUOTE_WORD_CAP])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc", help="document title (or sha256 prefix)")
    ap.add_argument("--limit", type=int, default=0, help="only first N sections (testing)")
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="extract, print, write nothing")
    args = ap.parse_args()

    # 1. resolve the document row
    # filter client-side: the library is small, and this sidesteps URL-encoding
    # of titles containing spaces (PostgREST or= filters are fussy about them).
    _, all_docs = dk.supa("GET", "/documents?select=id,title,author,sha256,blob_key,retrieval_profile")
    needle = args.doc.lower()
    rows = [d for d in (all_docs or [])
            if needle in d["title"].lower() or d["sha256"].startswith(args.doc)]
    if not rows:
        have = ", ".join(d["title"] for d in (all_docs or [])) or "(none ingested)"
        sys.exit(f"ERROR: no ingested document matching {args.doc!r}. Have: {have}")
    doc = rows[0]
    print(f"Document: {doc['title']} ({doc['retrieval_profile']})  sha={doc['sha256'][:12]}…")

    # 2. re-extract sections from the local library copy (larger, coherent units;
    #    chunks are retrieval-sized and would fragment claims)
    fname = os.path.basename(doc["blob_key"])
    path = dk.resolve_doc_path(fname)
    # Prefer an epub sibling: its sections are semantic ("Chapter 5 > 5.3 Caching"),
    # which are both better claim units and better citations than "p.140".
    if path.lower().endswith(".pdf"):
        try:
            sib = dk.resolve_doc_path(os.path.splitext(fname)[0] + ".epub")
            print(f"  using epub sibling for claim units: {os.path.basename(sib)}")
            path = sib
        except SystemExit:
            pass
    is_epub = path.lower().endswith(".epub")
    sections, _ = (dk.extract_epub if is_epub else dk.extract_pdf)(path)
    sections = [s for s in sections if len(s["text"]) >= MIN_SECTION_CHARS]
    if not is_epub:
        before = len(sections)
        sections = window_sections(sections)
        print(f"  windowed {before} page-sections -> {len(sections)} claim units")
    if args.limit:
        sections = sections[:args.limit]
    print(f"Sections to scan: {len(sections)}  (model {args.model})\n")

    rows_out, abstained = [], 0
    for i, sec in enumerate(sections, 1):
        prompt = (PROMPT + f"\n===== SECTION: {sec['title']} =====\n{sec['text'][:24000]}")
        claims = gemini(prompt, args.model).get("claims", []) or []
        if not claims:
            abstained += 1
        for c in claims:
            text = (c.get("claim_text") or "").strip()
            if not text:
                continue
            rows_out.append({
                "document_sha256": doc["sha256"],
                "claim_key": claim_key(text),
                "claim_text": text,
                "claim_type": c.get("claim_type"),
                "locator": {"section": sec["title"]},
                "quote": trim_quote(c.get("quote")),
                "proposed_entities": c.get("entities", []),
                "confidence": c.get("confidence"),
                "extractor": "gemini",
                "extractor_model": args.model,
                "lane": None,
                "status": "candidate",
            })
        print(f"  [{i:3d}/{len(sections)}] {sec['title'][:56]:56s} -> {len(claims)} claim(s)")

    print(f"\nExtracted {len(rows_out)} candidate claims "
          f"({abstained}/{len(sections)} sections abstained)")
    if args.dry_run:
        for r in rows_out[:8]:
            print(f"\n  • [{r['claim_type']}] {r['claim_text']}")
            print(f"    quote: \"{r['quote']}\"  @ {r['locator']['section'][:44]}"
                  f"  conf={r['confidence']}")
        print("\n(dry run — nothing written)")
        return
    if not rows_out:
        return
    # 3. upsert-ignore -> idempotent re-runs
    written = 0
    for b in range(0, len(rows_out), 100):
        dk.supa("POST", "/doc_claims?on_conflict=document_sha256,claim_key",
                body=rows_out[b:b + 100],
                headers={"Prefer": "resolution=ignore-duplicates,return=minimal"})
        written += len(rows_out[b:b + 100])
    _, after = dk.supa("GET", f"/doc_claims?document_sha256=eq.{doc['sha256']}&select=id")
    print(f"Sent {written}; doc_claims now holds {len(after)} row(s) for this document.")
    print("Next: /doc-digest to review and promote (nothing is in the graph yet).")


if __name__ == "__main__":
    main()
