#!/usr/bin/env python3
"""YED-156 A.5 — eval-set integrity checker (zero metered calls, no DB).

Verifies, against the LOCAL extractions of the source document, that an eval set
is actually gradeable before anyone runs an arm against it:

  1. every `gold` phrase occurs verbatim in BOTH the epub and the PDF extraction
     (whitespace/case-normalized + ligature-repaired on both sides),
  2. every `gold` is unique enough to be a usable label — it reports how many
     epub sections and PDF pages contain it (>1 section is a warning, not a fail),
  3. the PRD Rule-Beating guards hold: >=3 `paraphrase` cases with ZERO
     content-word overlap against their own gold phrase, and >=3
     `ligature_target` cases whose gold contains a former-ligature word,
  4. chapter spread.

`--fix` backfills `locator.pdf_pages` (and asserts `locator.epub_section`) from
what was actually found, so the locator field is measured, not asserted.

Usage:
  ./.venv/bin/python .../validate_eval_set.py [--set eval_set_v2.json]
                                              [--doc "Inference Engineering"] [--fix]
Exit 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dockb_common as dk  # noqa: E402
from retrieval_metrics import normalize_text as norm  # noqa: E402  (single source of truth)

# Words the PDF ligature split used to break. A gold phrase containing one of
# these exercises the repair path end to end (extract -> index -> match).
LIGATURE_STEMS = ("prefill", "specific", "configuration", "efficient", "sufficient",
                  "classification", "fine", "offload", "profil", "verif", "identif")

STOP = set("""a an the and or but if then than that this these those of in on at to for from by with
into over under about as is are was were be been being it its it's do does did doing have has had
having i you he she they we me my your our their there here what which who whom when where why how
should would could can may might must will shall not no nor so such own same too very just also
does don't get got make made use used using one two three more most less least much many any some
each every other another between within across during per via if while after before over up down out
off again further once all both few own s t don now""".split())


def content_words(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", norm(s)) if w not in STOP and len(w) > 2}


def load_sources(doc: str):
    ep, _ = dk.extract_epub(dk.resolve_doc_path(f"{doc}.epub"))
    pd, _ = dk.extract_pdf(dk.resolve_doc_path(f"{doc}.pdf"))
    return ep, pd


def find(sections: list[dict], gold: str) -> list[str]:
    """Titles of every section whose text contains gold (normalized)."""
    g = norm(gold)
    return [s["title"] for s in sections if g in norm(s["text"])]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=os.path.join(HERE, "eval_set_v2.json"))
    ap.add_argument("--doc", default=None, help="basename in the library (default: set's `doc`)")
    ap.add_argument("--fix", action="store_true", help="backfill locator.pdf_pages in place")
    args = ap.parse_args()

    spec = json.load(open(args.set))
    cases = spec["cases"]
    doc = args.doc or spec["doc"]
    print(f"Validating {os.path.basename(args.set)}: {len(cases)} cases against '{doc}' "
          f"(epub + pdf)\n" + "=" * 78)

    epub, pdf = load_sources(doc)
    print(f"  epub: {len(epub)} sections   pdf: {len(pdf)} pages\n")

    failures, warnings = [], []
    for c in cases:
        e_hits, p_hits = find(epub, c["gold"]), find(pdf, c["gold"])
        ok = bool(e_hits) and bool(p_hits)
        mark = "ok  " if ok else "FAIL"
        print(f"[{mark}] {c['id']}  epub={len(e_hits)} pdf={len(p_hits)}  \"{c['gold'][:56]}\"")
        if not ok:
            failures.append(f"{c['id']}: gold missing from "
                            f"{'epub' if not e_hits else ''}{' + ' if not e_hits and not p_hits else ''}"
                            f"{'pdf' if not p_hits else ''} -> {c['gold']!r}")
            continue
        if len(e_hits) > 1:
            warnings.append(f"{c['id']}: gold occurs in {len(e_hits)} epub sections {e_hits}")
        # locator truth-check / backfill
        declared = (c.get("locator") or {}).get("epub_section")
        if declared and declared not in e_hits:
            warnings.append(f"{c['id']}: declared epub_section {declared!r} != found {e_hits}")
        if args.fix:
            c.setdefault("locator", {})
            c["locator"]["epub_section"] = e_hits[0]
            c["locator"]["pdf_pages"] = p_hits[0] if len(p_hits) == 1 else p_hits

    # ---- guard 1: paraphrase cases carry zero content-word overlap -----------
    print("\n" + "-" * 78 + "\nParaphrase guard (question vs its own gold phrase):")
    para = [c for c in cases if c.get("paraphrase")]
    for c in para:
        shared = content_words(c["q"]) & content_words(c["gold"])
        status = "ok  " if not shared else "FAIL"
        print(f"[{status}] {c['id']}  overlap={sorted(shared) or 'none'}")
        if shared:
            failures.append(f"{c['id']}: paraphrase case shares {sorted(shared)} with its gold")
    if len(para) < 3:
        failures.append(f"only {len(para)} paraphrase cases, PRD guard requires >= 3")
    print(f"  -> {len(para)} paraphrase cases (guard: >= 3)")

    # ---- guard 2: former-ligature words are actually exercised ---------------
    print("\nLigature guard (gold must contain a former-ligature word):")
    lig = [c for c in cases if c.get("ligature_target")]
    for c in lig:
        g = norm(c["gold"])
        hit = [s for s in LIGATURE_STEMS if s in g]
        status = "ok  " if hit else "FAIL"
        print(f"[{status}] {c['id']}  words={hit or 'NONE'}")
        if not hit:
            failures.append(f"{c['id']}: flagged ligature_target but gold has no ligature word")
    if len(lig) < 3:
        failures.append(f"only {len(lig)} ligature_target cases, PRD guard requires >= 3")
    print(f"  -> {len(lig)} ligature cases (guard: >= 3)")

    # ---- guard 3: chapter spread -------------------------------------------
    print("\nChapter spread:")
    spread: dict[str, int] = {}
    for c in cases:
        sec = (c.get("locator") or {}).get("epub_section") or "?"
        ch = sec.split(">")[0].strip()
        spread[ch] = spread.get(ch, 0) + 1
    for ch, n in sorted(spread.items()):
        print(f"  {n:>2}  {ch}")
    if len(spread) < 5:
        warnings.append(f"only {len(spread)} distinct chapters represented")

    print("\n" + "=" * 78)
    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")
    if args.fix and not failures:
        json.dump(spec, open(args.set, "w"), indent=2, ensure_ascii=False)
        open(args.set, "a").write("\n")
        print(f"\nlocators backfilled -> {args.set}")
    print(f"\n{len(cases)} cases | {len(failures)} failures | {len(warnings)} warnings")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
