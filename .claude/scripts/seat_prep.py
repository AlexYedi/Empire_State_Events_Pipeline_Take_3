#!/usr/bin/env python3
"""seat_prep: make the copy of a pipeline file that Gemini and Codex see (YED-517).

  seat_prep.py SRC.md --out OUT.md
  seat_prep.py --selftest

Alex, 27 Nov: "Nothing is private", "nothing is off the record". The seats see the whole file. This adds the
`visibility: public` line and runs second_opinion.gate, which refuses only an email address or a phone number
(ADR-9: contact data lives in HubSpot). Exit 0 = OUT.md may go to a seat; exit 2 = refused, OUT.md removed.
"""
from __future__ import annotations
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import second_opinion as so  # noqa: E402


def strip(text: str):
    body = "\n".join(l for l in text.splitlines() if l.strip() != "visibility: public")
    return "visibility: public\n" + body.strip() + "\n", []


def prep(src: str, out: str) -> int:
    if os.path.exists(out) and os.path.samefile(src, out):
        print("REFUSED: --out is the source file; write the seat copy somewhere else."); return 2
    raw = open(src, encoding="utf-8").read()
    if os.path.exists(out):
        os.remove(out)
    text, _ = strip(raw)
    try:
        so.gate(text)
    except so.Refused as e:
        print(f"REFUSED: {e}. Nothing written. Remove the address or number and rerun."); return 2
    open(out, "w", encoding="utf-8").write(text)
    print(f"OK {out}: {len(text.split())} words"); return 0


def selftest() -> int:
    ok = True
    text, _ = strip("# Brief\n## Success Signals\n- hiring manager at Acme\n## Off the record\n- after the mic\n")
    for cond, name in ((text.startswith("visibility: public\n"), "marker is line 1"),
                       ("hiring manager" in text and "after the mic" in text, "everything is kept")):
        print(("pass " if cond else "FAIL ") + name); ok &= cond
    try:
        so.gate(text + "ada@example.com\n"); print("FAIL gate refuses an email"); ok = False
    except so.Refused:
        print("pass gate refuses an email")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?"); ap.add_argument("--out"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.src or not a.out:
        ap.error("SRC and --out are required")
    sys.exit(prep(a.src, a.out))
