#!/usr/bin/env python3
"""test_variant_signal_gate.py — offline regression for variant_signal_gate.py (E-09 Eric P1, YED-220).

Pins the abstain-empty contract: a variant run with ZERO cited signal rows produces the
empty-field abstain — never prose, never a hedge — and every shipped variant traces to the
signal row it cites. Dates, counts, and enums are computed in code. Fixtures are fictional
people and companies; no private inputs are touched.

Usage: python3 .claude/scripts/test_variant_signal_gate.py [path/to/variant_signal_gate.py]
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "vsg", sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "variant_signal_gate.py"))
vsg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vsg)

ok = n = 0


def ck(name, cond, detail=""):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name + (f" — {detail}" if (detail and not cond) else ""))


# Fictional structured source: the research-brief signal rows a variant may be built from.
ROWS = [
    {"id": "sig-001", "kind": "talk_abstract", "person": "Dana Okafor",
     "company": "Northbeam Analytics", "event": "SignalFest",
     "fact": "Keynote on evaluation-driven agent rollouts", "date": "2026-11-12", "talks": 1},
    {"id": "sig-002", "kind": "recent_post", "person": "Dana Okafor",
     "fact": "Posted that 70% of agent pilots die before production", "date": "2026-10-20"},
]

# --- The headline fixture: a variant run with ZERO cited signal rows -------------------
zero_run = vsg.run_variants(
    [{"field": "variant_a", "text": "", "signal_row": None},
     {"field": "variant_b", "text": "", "signal_row": None}],
    ROWS)
ck("zero-signal run: both fields abstain",
   all(r["verdict"] == "abstain" for r in zero_run),
   str(zero_run))
ck("zero-signal run: fields are the EMPTY string, not prose",
   all(r["verdict"] == "abstain" and r["signal_row"] is None for r in zero_run))

# The same run with prose in a field — the exact failure the rule bans.
prose_run = vsg.gate_variant("Loved your thoughts on agent rollouts!", None, ROWS)
ck("zero-signal run with prose → fail (nothing ships)",
   prose_run["verdict"] == "fail", str(prose_run))

# --- Abstain is the empty string, never a hedge ----------------------------------------
hedge_cases = ["N/A", "n/a.", "Unknown", "TBD", "to be determined", "Not applicable.",
               "no signal", "-", "—", "pending", "?"]
for h in hedge_cases:
    res = vsg.gate_variant(h, None, ROWS)
    ck(f"hedge {h!r} is rejected as an abstain", res["verdict"] == "fail", str(res))
ck("the abstain constant is never a hedge",
   not vsg.is_hedge(vsg.EMPTY) and vsg.EMPTY == "")
ck("whitespace-only field with no citation abstains (empty in substance)",
   vsg.gate_variant("   ", None, ROWS)["verdict"] == "abstain")

# --- Every shipped variant traces to its cited row --------------------------------------
ship_a = vsg.gate_variant("Your SignalFest keynote on evaluation-driven agent rollouts — "
                          "does the evaluation bar survive production?", "sig-001", ROWS)
ck("valid citation + prose built from the row → ship",
   ship_a["verdict"] == "ship", str(ship_a))
ck("unknown row id + prose → fail",
   vsg.gate_variant("prose", "sig-999", ROWS)["verdict"] == "fail")
ck("cited row + empty field → fail (citation without output)",
   vsg.gate_variant("", "sig-001", ROWS)["verdict"] == "fail")
ck("None row id is never treated as a citation",
   vsg.gate_variant("prose", None, ROWS)["verdict"] == "fail")

# --- Fact-trace: numbers in prose must come from the cited row --------------------------
ck("sourced number (70, from the row) passes the fact-trace",
   vsg.unverified_numbers("You posted that 70% of agent pilots die before production",
                          ROWS[1]) == [])
ck("unsourced number (99) is flagged by the fact-trace",
   vsg.unverified_numbers("70% of pilots die — you said 99%", ROWS[1]) == ["99"])

# --- Dates, counts, enums are computed in code ------------------------------------------
ck("date rendered from the row's machine value",
   vsg.fmt_date(ROWS[0]["date"]) == "November 12, 2026")
ck("absent date → empty-string abstain", vsg.fmt_date(None) == "")
ck("count computed from the machine integer",
   vsg.fmt_count(ROWS[0]["talks"], "keynote") == "1 keynote")
ck("absent count → empty-string abstain", vsg.fmt_count(None, "keynote") == "")
ck("enum validated against its allowed set",
   vsg.fmt_enum("plg", {"plg", "sales_led", "partner"}, "gtm_motion") == "plg")
ck("absent enum → empty-string abstain",
   vsg.fmt_enum(None, {"plg", "sales_led", "partner"}, "gtm_motion") == "")
try:
    vsg.fmt_enum("waterfall", {"plg", "sales_led", "partner"}, "gtm_motion")
    ck("out-of-set enum raises", False)
except ValueError:
    ck("out-of-set enum raises", True)
try:
    vsg.fmt_count("three", "keynote")
    ck("prose count raises (counts arrive as machine values)", False)
except ValueError:
    ck("prose count raises (counts arrive as machine values)", True)
try:
    vsg.fmt_date("November 12, 2026")
    ck("prose date raises (dates arrive as machine values)", False)
except ValueError:
    ck("prose date raises (dates arrive as machine values)", True)

# --- Privacy: fixture content is fictional, no private-input references -----------------
fixture_blob = repr(ROWS) + repr(zero_run)
for forbidden in ("me-model", "target-companies", "@", ".com"):
    ck(f"fixture contains no {forbidden!r} reference", forbidden not in fixture_blob)

print(f"\n{n}/{ok} passed" if ok == n else f"\nFAILED: {ok}/{n} passed")
sys.exit(0 if ok == n else 1)
