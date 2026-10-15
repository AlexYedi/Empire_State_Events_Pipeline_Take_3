#!/usr/bin/env python3
"""Deterministic pre-pass for the output-evaluator (YED-259): the checks a model shouldn't be trusted with.

  quotes   Every double-quoted span of 2+ words in a draft, matched against the transcript(s).
           Reports the best-matching transcript window, its score (0-1) and the speaker tag nearest it.
  sources  Every sentence carrying a figure (number, %, $, multiplier) or a funding/valuation verb,
           and whether the draft cites a URL anywhere. The evaluator judges each one; this only lists.

The output is JSON for the evaluator agent to read. It never edits the draft.

Usage:
  output_checks.py quotes  --draft DRAFT.md --transcript T1.md [--transcript T2.md ...] [--min 0.85]
  output_checks.py sources --draft DRAFT.md
"""
import argparse
import difflib
import json
import re
import sys

QMARK = re.compile(r'["“”]')


def quoted_spans(text):
    """Pair double quotes in order within each line, so a short quote ("world model") can't
    swallow the text up to the next real quote. Yields (start, quote_text)."""
    offset = 0
    for line in text.split("\n"):
        marks = [m.start() for m in QMARK.finditer(line)]
        for a, b in zip(marks[0::2], marks[1::2]):
            yield offset + a, line[a + 1:b]
        offset += len(line) + 1
SPEAKER = re.compile(r"\[(speaker_\d+)\]")
FIGURE = re.compile(r"(\$\s?\d|\d[\d,.]*\s?(%|percent|x\b|k\b|m\b|bn\b|million|billion|thousand|tokens)|\b\d{2,}[\d,]*\b)", re.I)
MONEY_VERB = re.compile(r"\b(raised|valuation|valued|series [a-e]|acquired|acquisition|revenue|arr|funding|ipo)\b", re.I)
URL = re.compile(r"https?://\S+")
FILLER = {"uh", "um", "uh,", "um,", "like,", "mm"}


def words(text):
    return [w for w in re.sub(r"[^\w\s']", " ", text.lower()).split() if w not in FILLER]


def best_window(q_words, t_words):
    n = len(q_words)
    if n == 0 or len(t_words) < n:
        return 0.0, 0
    best, at = 0.0, 0
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(q_words)
    # coarse pass on stride, then refine around the best hit
    stride = max(1, n // 4)
    for i in range(0, len(t_words) - n + 1, stride):
        sm.set_seq1(t_words[i:i + n])
        r = sm.ratio()
        if r > best:
            best, at = r, i
    for i in range(max(0, at - stride), min(len(t_words) - n, at + stride) + 1):
        for size in (n - 1, n, n + 1, n + 2):
            if size <= 0 or i + size > len(t_words):
                continue
            sm.set_seq1(t_words[i:i + size])
            r = sm.ratio()
            if r > best:
                best, at = r, i
    return round(best, 3), at


def cmd_quotes(args):
    draft = open(args.draft, errors="ignore").read()
    corpora = []
    for path in args.transcript:
        raw = open(path, errors="ignore").read()
        # keep a per-word speaker tag so a match can name its speaker
        # keep a per-word speaker tag and section heading, so a match can name who said it
        # (speaker ids restart per recording, so the section disambiguates them)
        toks, spk, cur, section = [], [], None, None
        for piece in re.split(r"(\[speaker_\d+\]|^## .*$)", raw, flags=re.M):
            stripped = piece.strip()
            if stripped.startswith("## "):
                section, cur = stripped[3:120], None
                continue
            m = SPEAKER.fullmatch(stripped) if stripped else None
            if m:
                cur = m.group(1)
                continue
            for w in words(piece):
                toks.append(w)
                spk.append((cur, section))
        corpora.append((path, toks, spk))
    results = []
    for start, q in quoted_spans(draft):
        q = q.strip()
        qw = words(q)
        if len(qw) < 2:  # 2-word phrases matter: "autonomous production" was a real misquote
            continue
        line_start = draft.rfind("\n", 0, start) + 1
        context = draft[line_start:start][-120:]
        best = {"score": 0.0}
        for path, toks, spk in corpora:
            score, at = best_window(qw, toks)
            if score > best["score"]:
                best = {"score": score, "transcript": path,
                        "speaker": spk[at][0] if spk else None, "section": spk[at][1] if spk else None,
                        "matched_text": " ".join(toks[at:at + len(qw) + 2])}
        results.append({"quote": q, "lead_in": context.strip(), **best,
                        "verdict": "match" if best["score"] >= args.min else "no-match"})
    out = {"check": "quotes", "draft": args.draft, "threshold": args.min, "quotes": results,
           "summary": {"total": len(results), "no_match": sum(r["verdict"] == "no-match" for r in results)}}
    print(json.dumps(out, indent=1))


def cmd_sources(args):
    draft = open(args.draft, errors="ignore").read()
    sentences = re.split(r"(?<=[.!?])\s+|\n+", draft)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) < 12 or s.startswith(("#", "http", "- **", "**Source")):
            continue
        if FIGURE.search(s) or MONEY_VERB.search(s):
            claims.append({"sentence": s[:300], "has_url_inline": bool(URL.search(s))})
    out = {"check": "sources", "draft": args.draft, "urls_in_draft": len(set(URL.findall(draft))),
           "claims": claims, "summary": {"claim_candidates": len(claims)}}
    print(json.dumps(out, indent=1))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quotes")
    q.add_argument("--draft", required=True)
    q.add_argument("--transcript", action="append", required=True)
    q.add_argument("--min", type=float, default=0.85)
    s = sub.add_parser("sources")
    s.add_argument("--draft", required=True)
    a = p.parse_args()
    {"quotes": cmd_quotes, "sources": cmd_sources}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
