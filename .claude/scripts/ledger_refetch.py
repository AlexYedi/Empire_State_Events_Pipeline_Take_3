#!/usr/bin/env python3
"""ledger_refetch — re-derive web-verified Evidence Ledger rows from page text that CODE fetched (YED-495).

Why: specialists wrote each row's verbatim quote themselves, from WebFetch, which returns a summary, not the page. A
self-reported quote is not proof, and four rounds of prompt rules moved the staging quote-check pass rate only from
27% to 61% (Madison Avenue, 2026-11-22, 40/66). In YED-493, page text fetched by code and given to an agent with no
tools gave 60/62 passes. This moves the proof into code:

  1 prepare   code parses the ledger rows (substrate.parse_ledger), fetches each cited URL once
              (substrate.fetch_page) and writes the extractor's input: per URL, the page text plus the specialist
              claims that cite it
  2 extract   the `ledger-extract` workflow (.claude/workflows/ledger-extract.js): one no-tools agent per batch of
              pages writes, for each claim, a quote copied from the fetched text and a claim written from that quote,
              or "none"
  3 swap      code rewrites the Evidence Set: each extracted row gets the new claim + quote + the fetch stamp; a row
              with no extraction keeps its claim, source, url and date but loses its quote (an unapproved candidate)

The specialists' claim/url/source/date still say WHAT to fetch; quote_check at staging stays the deterministic gate.
Runs in the parent between the Scan-head approval and Step 4.2a. Network: GET only (fetch_page). No graph, Notion or
HubSpot writes.

  .venv/bin/python .claude/scripts/ledger_refetch.py prepare --evidence <slug>.evidence.md --out <scratch>/<slug>.refetch.json
  (run the ledger-extract workflow with args = the "workflow_args" key of that file; save its result as JSON)
  .venv/bin/python .claude/scripts/ledger_refetch.py swap --evidence <slug>.evidence.md --prepared <scratch>/<slug>.refetch.json \
      --extracted <scratch>/<slug>.extracted.json --out <slug>.evidence.md
  .venv/bin/python .claude/scripts/ledger_refetch.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BATCH_CHARS = 90_000      # page text per extractor agent (Sonnet context, with room for the rules and claims)
PAGE_CAP = 40_000         # chars of one page passed to the extractor; quote_check reads the full page at staging
LEDGER_HEAD = re.compile(r"^##### Evidence Ledger — (.+?)\s*$")


def _fields(line: str) -> dict:
    f = {}
    for part in line[2:].split(" | "):
        k, _, v = part.partition(":")
        f[k.strip()] = v.strip()
    return f


def web_rows(md: str) -> list[dict]:
    """Every '- claim: … | tier: web-verified | … url: http…' bullet under an Evidence Ledger heading, with its line
    number, so swap can rewrite exactly that line."""
    out, entity = [], None
    for i, line in enumerate(md.splitlines()):
        m = LEDGER_HEAD.match(line)
        if m:
            entity = m.group(1)
            continue
        if not line.startswith("- claim:") or not entity:
            continue
        f = _fields(line)
        if f.get("tier") != "web-verified" or not f.get("url", "").startswith(("http://", "https://")):
            continue
        out.append({"rid": f"r{len(out)}", "line": i, "entity": entity, "claim": f.get("claim", ""),
                    "source": f.get("source", ""), "url": f["url"], "date": f.get("date", ""),
                    "quote": f.get("quote", ""), "fetched": f.get("fetched", "")})
    return out


def batches(pages: list[dict]) -> list[list[dict]]:
    out, cur, size = [], [], 0
    for p in pages:
        n = len(p["text"])
        if cur and size + n > BATCH_CHARS:
            out.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += n
    if cur:
        out.append(cur)
    return out


def prepare(md: str, fetch) -> dict:
    rows = web_rows(md)
    by_url: dict[str, list[dict]] = {}
    for r in rows:
        by_url.setdefault(r["url"], []).append(r)
    pages, failed = [], []
    for url, rs in by_url.items():
        text = fetch(url)
        stamp = __import__("substrate")._utc_stamp()
        if not text:
            failed.append(url)
            continue
        text = " ".join(text.split())[:PAGE_CAP]
        pages.append({"url": url, "fetched": stamp, "text": text,
                      "claims": [{"rid": r["rid"], "entity": r["entity"], "claim": r["claim"]} for r in rs]})
    return {"rows": rows, "fetch_failed": failed,
            "workflow_args": {"batches": batches(pages)},
            "stamps": {p["url"]: p["fetched"] for p in pages}}


def swap(md: str, prepared: dict, extracted: dict) -> tuple[str, dict]:
    """extracted = {"rows": [{"rid", "claim", "quote"} | {"rid", "none": true}, ...]} (the workflow's result)."""
    got = {e["rid"]: e for e in extracted.get("rows", []) if e.get("rid")}
    lines = md.splitlines()
    stats = {"rows": 0, "extracted": 0, "none": 0, "fetch_failed": 0}
    for r in prepared["rows"]:
        stats["rows"] += 1
        e = got.get(r["rid"])
        stamp = prepared["stamps"].get(r["url"])
        if e and not e.get("none") and e.get("quote") and e.get("claim") and stamp:
            stats["extracted"] += 1
            claim, quote, fetched = e["claim"].strip(), e["quote"].strip(), stamp
            lines[r["line"]] = (f"- claim: {claim} | tier: web-verified | source: {r['source']} | url: {r['url']} | "
                                f"date: {r['date']} | quote: {quote} | fetched: {fetched}")
        else:
            stats["fetch_failed" if not stamp else "none"] += 1
            lines[r["line"]] = (f"- claim: {r['claim']} | tier: web-verified | source: {r['source']} | url: {r['url']} | "
                                f"date: {r['date']}")
    return "\n".join(lines) + ("\n" if md.endswith("\n") else ""), stats


def selftest() -> bool:
    md = ("### Companies\n##### Evidence Ledger — Acme\n"
          "- claim: Acme raised $4M | tier: web-verified | source: TC | url: https://a.example/x | date: 2026-10-01 | quote: q | fetched: 2026-11-01T00:00:00Z\n"
          "- claim: Acme hires | tier: web-verified | source: Blog | url: https://b.example/y | date: 2026-10-02\n"
          "- claim: a lead | tier: email-signal | source: Gmail | url: n/a | date: 2026-10-03\n"
          "- claim: gone page | tier: web-verified | source: X | url: https://c.example/z | date: 2026-10-04 | quote: q2 | fetched: 2026-11-01T00:00:00Z\n")
    pages = {"https://a.example/x": "Acme   raised $4 million in seed funding.", "https://b.example/y": "Acme is hiring.",
             "https://c.example/z": None}
    p = prepare(md, lambda u: pages[u])
    ex = {"rows": [{"rid": "r0", "claim": "Acme raised $4 million in seed funding", "quote": "Acme raised $4 million in seed funding."},
                   {"rid": "r1", "none": True}]}
    out, st = swap(md, p, ex)
    L = out.splitlines()
    checks = [
        ("web rows only (email-signal skipped)", [r["rid"] for r in p["rows"]] == ["r0", "r1", "r2"]),
        ("one fetch per URL; a failed fetch is listed", p["fetch_failed"] == ["https://c.example/z"]
         and sum(len(b) for b in p["workflow_args"]["batches"]) == 2),
        ("page text whitespace-normalised for the extractor", p["workflow_args"]["batches"][0][0]["text"].startswith("Acme raised $4")),
        ("extracted row: new claim + quote + CODE's fetch stamp", "quote: Acme raised $4 million in seed funding." in L[2]
         and "fetched: 2026-11-01" not in L[2] and "source: TC | url: https://a.example/x | date: 2026-10-01" in L[2]),
        ("'none' row keeps claim/source/url/date and loses any quote", L[3].endswith("date: 2026-10-02") and "quote:" not in L[3]),
        ("failed-fetch row drops the self-reported quote", "quote:" not in L[5] and "gone page" in L[5]),
        ("non-web rows untouched", L[4] == md.splitlines()[4]),
        ("stats", st == {"rows": 3, "extracted": 1, "none": 1, "fetch_failed": 1}),
    ]
    for name, ok in checks:
        print(("  ✓ " if ok else "  ✗ ") + name)
    print(f"selftest: {sum(v for _, v in checks)}/{len(checks)} pass")
    return all(v for _, v in checks)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["prepare", "swap"])
    ap.add_argument("--evidence")
    ap.add_argument("--out")
    ap.add_argument("--prepared")
    ap.add_argument("--extracted")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if not (a.cmd and a.evidence and a.out):
        ap.error("prepare|swap with --evidence and --out (or --selftest)")
    md = open(a.evidence, encoding="utf-8").read()
    if a.cmd == "prepare":
        import substrate
        p = prepare(md, substrate.fetch_page)
        json.dump(p, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
        n = sum(len(pg["claims"]) for b in p["workflow_args"]["batches"] for pg in b)
        print(f"prepare: {len(p['rows'])} web rows · {sum(len(b) for b in p['workflow_args']['batches'])} pages fetched · "
              f"{len(p['fetch_failed'])} fetch failed · {n} claims to extract · {len(p['workflow_args']['batches'])} batches")
        return 0
    if not (a.prepared and a.extracted):
        ap.error("swap needs --prepared and --extracted")
    out, st = swap(md, json.load(open(a.prepared, encoding="utf-8")), json.load(open(a.extracted, encoding="utf-8")))
    open(a.out, "w", encoding="utf-8").write(out)
    print("swap: " + " · ".join(f"{k} {v}" for k, v in st.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
