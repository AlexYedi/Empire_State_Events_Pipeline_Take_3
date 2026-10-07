#!/usr/bin/env python3
"""comp_gate.py — role-radar's comp gate (rubric v2.3) as code, not prose (YED-255).

Why: the 2026-09-27 rulings (midpoint · emerging-seller low end · base-only top · "up to X" = X − $20K ·
two rules → the higher figure · exactly-at-floor clears) were ~500 words of arithmetic in SKILL.md that a
model re-derived on every scan. Arithmetic is code. The model still decides the two judgment inputs:
is this JD pitched at an emerging seller, and does the band read as OTE or base.

The floor NEVER lives in this repo: it is read at runtime from `.claude/references/me-model.md` §1.5
(gitignored), or passed with --floor. Self-test uses a synthetic floor.

Usage:
  comp_gate.py --text "$180K – $220K OTE" [--emerging] [--floor 200000]
  comp_gate.py --low 180000 --high 220000 --label base [--emerging]
  comp_gate.py --selftest
Output: one JSON object {verdict: PASS|REJECT|UNKNOWN, figure, rules, note}. Exit 0 always except bad args (2)
or an unreadable floor (3): a missing floor is a loud failure, never a silent pass.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ME_MODEL = os.path.join(os.path.dirname(__file__), "..", "references", "me-model.md")
ONE_SIDED_DISCOUNT = 20_000
FLOOR_RX = re.compile(r"floor\s*=\s*\$\s*([\d,]+(?:\.\d+)?)\s*([kK])?")
MONEY = r"(?<![A-Za-z])\$\s*([\d,]+(?:\.\d+)?)\s*([kKmM])?"   # USD only: CA$/MX$/A$ are skipped
RANGE_RX = re.compile(MONEY + r"\s*(?:-|–|—|to)\s*" + MONEY)
UPTO_RX = re.compile(r"(?:up to|as much as|max(?:imum)? of)\s*" + MONEY, re.I)
SINGLE_RX = re.compile(MONEY)
BASE_RX = re.compile(r"\b(?:base(?:\s+salary|\s+pay)?|salary|before variable|plus commission|offers commission)\b"
                     r"|\+\s*commission", re.I)
OTE_RX = re.compile(r"\b(OTE|on[- ]target earnings|total (?:target )?compensation)\b", re.I)


def _usd(num: str, suffix: str | None) -> int:
    v = float(num.replace(",", ""))
    if suffix and suffix.lower() == "k":
        v *= 1_000
    elif suffix and suffix.lower() == "m":
        v *= 1_000_000
    return int(round(v))


def _label(window: str) -> str:
    return "ote" if OTE_RX.search(window) else "base" if BASE_RX.search(window) else "unlabelled"


def _window(text: str, start: int, end: int) -> str:
    """The band's own clause: up to 60 chars back and 30 forward, cut at a clause break or another $ amount,
    so a neighbouring band's label ("…; OTE $250K") never leaks onto this one."""
    before = re.split(r"[;.\n]|\$\s*\d[\d,]*\s*[kKmM]?", text[max(0, start - 60):start])[-1]
    after = re.split(r"[;.\n$]", text[end:end + 30])[0]
    return before + text[start:end] + after


def parse_comp(text: str) -> dict:
    """Posted comp text -> {low, high, label: ote|base|unlabelled, one_sided, snippet}; {} when nothing posted.

    USD only: amounts are counted when $20K <= amount < $2M (drops "$5M seed"-style noise above salary scale);
    "US$" is read as USD, any other currency prefix (CA$, MX$, A$) is skipped -> UNKNOWN. Each range is labelled
    from its OWN neighbourhood (60 chars before, 30 after), so "Base $150K-$180K; OTE $250K-$300K" labels each
    band separately; when several bands are posted, an OTE-labelled band wins (it is the comparable figure)."""
    if not text:
        return {}
    text = text.replace("US$", "$")
    found = []
    for m in RANGE_RX.finditer(text):
        lo, hi = _usd(m.group(1), m.group(2) or m.group(4)), _usd(m.group(3), m.group(4))
        if 20_000 <= lo <= hi < 2_000_000:
            win = _window(text, m.start(), m.end())
            found.append({"low": lo, "high": hi, "label": _label(win), "one_sided": False, "snippet": m.group(0)})
    if found:
        return next((f for f in found if f["label"] == "ote"), found[0])
    m = UPTO_RX.search(text)
    if m:
        hi = _usd(m.group(1), m.group(2))
        if 20_000 <= hi < 2_000_000:
            return {"low": None, "high": hi, "label": _label(text), "one_sided": True, "snippet": m.group(0)}
    for m in SINGLE_RX.finditer(text):
        v = _usd(m.group(1), m.group(2))
        if 20_000 <= v < 2_000_000:
            win = _window(text, m.start(), m.end())
            return {"low": v, "high": v, "label": _label(win), "one_sided": False, "snippet": m.group(0)}
    return {}


def gate(comp: dict, floor: int, emerging: bool = False) -> dict:
    """Apply rubric v2.3. Returns {verdict, figure, rules, note}."""
    if not comp or comp.get("high") is None:
        return {"verdict": "UNKNOWN", "figure": None, "rules": ["not-posted"],
                "note": "Comp not posted: score on mechanism, never infer a reject."}
    lo, hi, label = comp.get("low"), comp["high"], comp.get("label", "unlabelled")
    cands: list[tuple[str, int]] = []
    if comp.get("one_sided"):
        cands.append(("one-sided: X − $20K", hi - ONE_SIDED_DISCOUNT))
        if label == "base":
            cands.append(("base-only: top of range", hi))
    else:
        if label == "base":
            cands.append(("base-only: top of range", hi))
        if emerging:
            cands.append(("emerging seller: low end", lo))
        if not cands:   # OTE or unlabelled, not emerging
            rule = "OTE: midpoint" if label == "ote" else "unlabelled read as OTE: midpoint"
            cands.append((rule, (lo + hi) // 2))
    rule, figure = max(cands, key=lambda c: c[1])        # two rules at once -> the higher figure
    verdict = "PASS" if figure >= floor else "REJECT"   # exactly at the floor clears
    posted = f"${lo:,}–${hi:,}" if lo is not None and lo != hi else f"${hi:,}" + (" (up to)" if comp.get("one_sided") else "")
    both = "; ".join(f"{r} ${f:,}" for r, f in cands)
    note = f"Comp {posted} {label} → {both} → used ${figure:,} ({rule}) → {verdict} vs floor."
    return {"verdict": verdict, "figure": figure, "rules": [r for r, _ in cands], "note": note}


def read_floor(path: str = ME_MODEL) -> int:
    with open(path, encoding="utf-8") as fh:
        m = FLOOR_RX.search(fh.read())
    if not m:
        raise ValueError(f"no 'floor = $N' line in {path}")
    return _usd(m.group(1), m.group(2))


def selftest() -> int:
    F = 200_000   # synthetic floor — the real one never enters the repo
    cases = [
        # (text, emerging, expected verdict, expected figure)
        ("$180K – $220K OTE", False, "PASS", 200_000),            # midpoint exactly at floor clears
        ("$170,000 - $220,000 OTE", False, "REJECT", 195_000),    # midpoint below
        ("$180K–$221K OTE", True, "REJECT", 180_000),             # emerging seller: low end
        ("Base salary range $150K – $200K", False, "PASS", 200_000),   # base-only: top
        ("Base salary $150K-$210K", True, "PASS", 210_000),       # base + emerging -> higher figure (top)
        ("up to $215K", False, "REJECT", 195_000),                # one-sided: X − 20K
        ("up to $220K OTE", False, "PASS", 200_000),
        ("$180K - $230K", False, "PASS", 205_000),                # unlabelled -> midpoint
        ("$205K OTE", False, "PASS", 205_000),                    # single number
        ("Competitive salary + equity", False, "UNKNOWN", None),  # nothing posted
        ("OTE CA$180,000 - CA$230,000", False, "UNKNOWN", None),  # non-USD is not compared to a USD floor
        ("Salary: $150K - $200K", False, "PASS", 200_000),        # bare "Salary" = base band -> top (judge r1)
        ("Base salary $150K-$180K; OTE $250K-$300K", False, "PASS", 275_000),  # per-band labels; OTE band wins
        ("US$180,000 - US$230,000 OTE", False, "PASS", 205_000),  # explicit US$ is USD
        ("We raised a $5M seed. Pay $190K–$230K + commission", False, "PASS", 230_000),  # $5M ignored; commission = base
    ]
    ok = 0
    for text, em, want_v, want_f in cases:
        r = gate(parse_comp(text), F, em)
        good = r["verdict"] == want_v and r["figure"] == want_f
        ok += good
        print(f"  {'✓' if good else '✗'} {text!r} emerging={em} → {r['verdict']} {r['figure']} ({'; '.join(r['rules'])})")
    print(f"selftest: {ok}/{len(cases)} comp-gate cases pass")
    return 0 if ok == len(cases) else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--text"); ap.add_argument("--low", type=int); ap.add_argument("--high", type=int)
    ap.add_argument("--label", choices=["ote", "base", "unlabelled"], default="unlabelled")
    ap.add_argument("--one-sided", action="store_true"); ap.add_argument("--emerging", action="store_true")
    ap.add_argument("--floor", type=int); ap.add_argument("--me-model"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        floor = a.floor or (read_floor(a.me_model) if a.me_model else read_floor())
    except (OSError, ValueError) as e:
        print(f"comp_gate: cannot read the OTE floor ({e}); pass --floor", file=sys.stderr)
        return 3
    if a.text is not None:
        comp = parse_comp(a.text)
    elif a.high is not None:
        comp = {"low": a.low if a.low is not None else a.high, "high": a.high, "label": a.label, "one_sided": a.one_sided}
    else:
        ap.print_usage(sys.stderr); return 2
    print(json.dumps({**gate(comp, floor, a.emerging), "parsed": comp}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
