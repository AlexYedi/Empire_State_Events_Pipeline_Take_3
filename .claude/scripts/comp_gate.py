#!/usr/bin/env python3
"""comp_gate.py — role-radar's comp gate (rubric v2.3) as code, not prose (YED-255).

This file is the ONLY executable statement of the comp rules (ADR-12). me-model.md §1.5 holds the policy, the
floor and each ruling's date; role-radar SKILL.md points here and does not restate the arithmetic. A new ruling
lands as a code change + a --selftest case in the same commit, or it has not landed.

Ruling ledger (date · rule):
  2026-09-27  OTE or unlabelled band → midpoint · base band → top · emerging seller → low end ·
              "up to X" → X − $20K · two rules at once → the higher figure · exactly at the floor clears
  2026-10-07  commission offered, no split stated, band not labelled OTE → top ÷ 0.75
  2026-10-11  stated split ("70/30 Split"), band not labelled OTE → top ÷ base share · equity = a note, no dollars
  2026-10-11  a gross-up on a band that doesn't say "base"/"salary" is an assumption (band read as base): the figure stands, the rule
              and note say "assumed base", and the row is verified with the recruiter (ADR-12 V1; V2 = REVIEW)

Why: the 2026-09-27 rulings (midpoint · emerging-seller low end · base-only top · "up to X" = X − $20K ·
two rules → the higher figure · exactly-at-floor clears) were ~500 words of arithmetic in SKILL.md that a
model re-derived on every scan. Arithmetic is code. The model still decides the two judgment inputs:
is this JD pitched at an emerging seller, and does the band read as OTE or base.

The floor NEVER lives in this repo: it is read at runtime from `.claude/references/me-model.md` §1.5
(gitignored), or passed with --floor. Self-test uses a synthetic floor.

Usage:
  comp_gate.py --text "$180K – $220K OTE" [--emerging] [--floor 137000]
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
COMMISSION_RX = re.compile(r"commission|variable|\bbonus\b", re.I)
SPLIT_RX = re.compile(r"\b([5-9]\d)\s*/\s*([1-5]\d)\s*split\b", re.I)    # "70/30 Split" = base share / variable share
SAYS_BASE_RX = re.compile(r"\b(?:base|salary)\b", re.I)   # the band names itself base; "+ commission" alone does not
EQUITY_RX = re.compile(r"\bequity\b|\bRSUs?\b|stock options", re.I)
NO_SPLIT_BASE_SHARE = 0.75   # commission offered, split not stated: variable is at least 25% of OTE (ruled 2026-10-07)


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
            found.append({"low": lo, "high": hi, "label": _label(win), "one_sided": False, "snippet": m.group(0),
                          "says_base": bool(SAYS_BASE_RX.search(win))})
    if found:
        return _extras(next((f for f in found if f["label"] == "ote"), found[0]), text)
    m = UPTO_RX.search(text)
    if m:
        hi = _usd(m.group(1), m.group(2))
        if 20_000 <= hi < 2_000_000:
            return _extras({"low": None, "high": hi, "label": _label(text), "one_sided": True, "snippet": m.group(0),
                            "says_base": bool(SAYS_BASE_RX.search(text))}, text)
    for m in SINGLE_RX.finditer(text):
        v = _usd(m.group(1), m.group(2))
        if 20_000 <= v < 2_000_000:
            win = _window(text, m.start(), m.end())
            return _extras({"low": v, "high": v, "label": _label(win), "one_sided": False, "snippet": m.group(0),
                            "says_base": bool(SAYS_BASE_RX.search(win))}, text)
    return {}


def _extras(comp: dict, text: str) -> dict:
    """Posting-wide signals that sit outside the band's own clause (Ashby: "$X – $Y • Offers Equity • 70/30 Split")."""
    split = SPLIT_RX.search(text)
    if split and int(split.group(1)) + int(split.group(2)) == 100:
        comp["base_share"] = int(split.group(1)) / 100
    comp["commission"] = bool(COMMISSION_RX.search(text))
    comp["equity"] = bool(EQUITY_RX.search(text))
    return comp


def gate(comp: dict, floor: int, emerging: bool = False) -> dict:
    """Apply rubric v2.3. Returns {verdict, figure, rules, note}."""
    if not comp or comp.get("high") is None:
        return {"verdict": "UNKNOWN", "figure": None, "rules": ["not-posted"],
                "note": "Comp not posted: score on mechanism, never infer a reject."}
    lo, hi, label = comp.get("low"), comp["high"], comp.get("label", "unlabelled")
    cands: list[tuple[str, int]] = []
    # Variable gross-up (2026-10-11, Alex): a band not labelled OTE that carries a stated split ("70/30") is the base;
    # OTE = top ÷ base share. Commission with no split stated: ÷ 0.75 (2026-10-07). Joins the "higher figure" pool.
    # A band that doesn't call itself base/salary is READ as base by the gross-up: a guess (Ashby's "$X – $Y • Offers
    # Commission" never says which). Said aloud in the rule and the note. --label base from the CLI counts as stated.
    if label != "ote":
        tag = "" if comp.get("says_base", label == "base") else " (band assumed base)"
        if comp.get("base_share"):
            share = comp["base_share"]
            cands.append((f"stated {round(share * 100)}/{round(100 - share * 100)} split{tag}: top ÷ {share:.2f}",
                          int(hi / share)))
        elif comp.get("commission"):
            cands.append((f"commission, no split{tag}: top ÷ {NO_SPLIT_BASE_SHARE}", int(hi / NO_SPLIT_BASE_SHARE)))
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
    assumed = "band assumed base" in rule
    if assumed:
        note += " ASSUMED: the band is unlabelled and was read as base for the gross-up; verify with the recruiter."
    if comp.get("equity"):
        note += " Equity offered: upside not in the figure (value unposted); weigh it for pre-IPO / acquisition-track companies."
    return {"verdict": verdict, "figure": figure, "rules": [r for r, _ in cands], "note": note,
            "equity": bool(comp.get("equity")), "assumed": assumed}


def read_floor(path: str = ME_MODEL) -> int:
    with open(path, encoding="utf-8") as fh:
        m = FLOOR_RX.search(fh.read())
    if not m:
        raise ValueError(f"no 'floor = $N' line in {path}")
    return _usd(m.group(1), m.group(2))


def selftest() -> int:
    F = 137_000   # synthetic floor, deliberately unrelated to any real figure; the real one never enters the repo
    cases = [
        # (text, emerging, expected verdict, expected figure)
        ("$120K – $154K OTE", False, "PASS", 137_000),            # midpoint exactly at floor clears
        ("$110,000 - $160,000 OTE", False, "REJECT", 135_000),    # midpoint below
        ("$125K–$170K OTE", True, "REJECT", 125_000),             # emerging seller: low end
        ("Base salary range $100K – $137K", False, "PASS", 137_000),   # base-only: top
        ("Base salary $100K-$150K", True, "PASS", 150_000),       # base + emerging -> higher figure (top)
        ("up to $150K", False, "REJECT", 130_000),                # one-sided: X − 20K
        ("up to $157K OTE", False, "PASS", 137_000),
        ("$120K - $160K", False, "PASS", 140_000),                # unlabelled -> midpoint
        ("$140K OTE", False, "PASS", 140_000),                    # single number
        ("Competitive salary + equity", False, "UNKNOWN", None),  # nothing posted
        ("OTE CA$120,000 - CA$160,000", False, "UNKNOWN", None),  # non-USD is not compared to a USD floor
        ("Salary: $100K - $140K", False, "PASS", 140_000),        # bare "Salary" = base band -> top (judge r1)
        ("Base salary $100K-$120K; OTE $170K-$210K", False, "PASS", 190_000),  # per-band labels; OTE band wins
        ("US$120,000 - US$160,000 OTE", False, "PASS", 140_000),  # explicit US$ is USD
        ("We raised a $5M seed. Pay $120K–$150K + commission", False, "PASS", 200_000),  # $5M ignored; commission, no split -> top ÷ 0.75
        ("$70K – $98K • Offers Equity • Offers Commission • 70/30 Split", False, "PASS", 140_000),  # stated split: top ÷ 0.70
        ("$70K – $95.8K • Offers Equity • Offers Commission • 70/30 Split", False, "REJECT", 136_857),  # just under
        ("Base salary $100K – $120K, equity", False, "REJECT", 120_000),  # no variable mentioned: no gross-up; equity is a note only
        ("$120K – $154K OTE • 70/30 Split", False, "PASS", 137_000),   # labelled OTE: split does not gross up again
        # Real postings (Ramp Ashby board, pulled 2026-10-11): the regression set for the Activation ruling (ADR-12 #3).
        ("$182K – $278K • Offers Equity • Multiple Ranges", False, "PASS", 230_000),              # CAM Enterprise
        ("$142K – $216K • Offers Equity • Offers Commission", False, "PASS", 288_000),            # CAM Mid-Market
        ("$93.6K – $143K • Offers Equity • Offers Commission • Multiple Ranges", False, "PASS", 190_666),   # CAM Scaled
        ("$190K – $290K • Offers Equity • Multiple Ranges", False, "PASS", 240_000),              # CAM Strategic Ent
        ("$108K – $165K • Offers Equity • Offers Commission • Multiple Ranges", False, "PASS", 220_000),    # Sr CAM Scaled
        ("$115K – $212.5K • Offers Equity • Offers Commission • 70/30 Split", False, "PASS", 303_571),     # Ent CAM Bill Pay
        ("$138K – $210K • Offers Equity • Offers Commission • Multiple Ranges", False, "PASS", 280_000),    # Sr CAM Partnerships
        ("$97.1K – $148.4K • Offers Equity • Offers Commission • Multiple Ranges", False, "PASS", 197_866), # CAM Commercial
        ("$138K – $210K • Offers Equity • Multiple Ranges", False, "PASS", 174_000),              # Procurement Product AM
    ]
    ok = 0
    for text, em, want_v, want_f in cases:
        r = gate(parse_comp(text), F, em)
        good = r["verdict"] == want_v and r["figure"] == want_f
        ok += good
        print(f"  {'✓' if good else '✗'} {text!r} emerging={em} → {r['verdict']} {r['figure']} ({'; '.join(r['rules'])})")
    # The "assumed base" flag: on an unlabelled gross-up, off when the band says base or OTE, off with no gross-up.
    flags = [("$70K – $98K • Offers Commission • 70/30 Split", True), ("Base salary $100K-$150K + commission", False),
             ("$120K – $154K OTE • Offers Commission", False), ("$182K – $278K • Offers Equity", False)]
    for text, want in flags:
        r = gate(parse_comp(text), F)
        good = r["assumed"] == want and (("ASSUMED" in r["note"]) == want)
        ok += good
        print(f"  {'✓' if good else '✗'} {text!r} → assumed={r['assumed']} (want {want})")
    n = len(cases) + len(flags)
    print(f"selftest: {ok}/{n} comp-gate cases pass")
    return 0 if ok == n else 1


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
