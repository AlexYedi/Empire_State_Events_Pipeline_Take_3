#!/usr/bin/env python3
"""test_variant_signal_gate.py — offline regression for variant_signal_gate.py (E-09 Eric P1, YED-220).

Pins the abstain-empty contract: a variant run with ZERO cited signal sources produces the
empty-field abstain — never prose, never a hedge — and every shipped variant traces to the
Evidence-Set source it cites. The citation anchor is the source URL from the research
brief's Evidence Set (re-pointed from row ids per Alex's PR #243 review: briefs are pages
with sections, not rows with ids); the gate verifies cited-URL membership in the Evidence
Set, so an invented citation fails exactly like a missing one. Dates, counts, and enums
are computed in code. Fixtures are fictional people and companies; no private inputs are
touched.

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


# Fictional structured source: the research brief's Evidence Set — URL-carrying rows
# organized by person/topic block (event-research Step 3 / ADR-5). No real URLs.
EVIDENCE = [
    {"url": "https://example.com/dana-agent-keynote",
     "source": "SignalFest keynote abstract",
     "block": "Dana Okafor — person block",
     "fact": "Keynote on evaluation-driven agent rollouts", "date": "2026-11-12"},
    {"url": "https://example.com/dana-pilots-post",
     "source": "LinkedIn post",
     "block": "Dana Okafor — person block",
     "fact": "Posted that 70% of agent pilots die before production", "date": "2026-10-20"},
]

# --- The headline fixture: a variant run with ZERO cited signal sources -----------------
zero_run = vsg.run_variants(
    [{"field": "variant_a", "text": "", "source_url": None},
     {"field": "variant_b", "text": "", "source_url": None}],
    EVIDENCE)
ck("zero-signal run: both fields abstain",
   all(r["verdict"] == "abstain" for r in zero_run),
   str(zero_run))
ck("zero-signal run: fields are the EMPTY string, not prose",
   all(r["verdict"] == "abstain" and r["source_url"] is None for r in zero_run))

# The same run with prose in a field — the exact failure the rule bans.
prose_run = vsg.gate_variant("Loved your thoughts on agent rollouts!", None, EVIDENCE)
ck("zero-signal run with prose → fail (nothing ships)",
   prose_run["verdict"] == "fail", str(prose_run))

# --- Abstain is the empty string, never a hedge ----------------------------------------
hedge_cases = ["N/A", "n/a.", "Unknown", "TBD", "to be determined", "Not applicable.",
               "no signal", "-", "—", "pending", "?"]
for h in hedge_cases:
    res = vsg.gate_variant(h, None, EVIDENCE)
    ck(f"hedge {h!r} is rejected as an abstain", res["verdict"] == "fail", str(res))
ck("the abstain constant is never a hedge",
   not vsg.is_hedge(vsg.EMPTY) and vsg.EMPTY == "")
ck("whitespace-only field with no citation abstains (empty in substance)",
   vsg.gate_variant("   ", None, EVIDENCE)["verdict"] == "abstain")

# --- Every shipped variant traces to a cited Evidence-Set URL ----------------------------
ship_a = vsg.gate_variant("Your SignalFest keynote on evaluation-driven agent rollouts — "
                          "does the evaluation bar survive production?",
                          "https://example.com/dana-agent-keynote", EVIDENCE)
ck("cited Evidence-Set URL + prose built from it → ship",
   ship_a["verdict"] == "ship", str(ship_a))
ck("URL NOT in the Evidence Set + prose → fail (invented citation)",
   vsg.gate_variant("prose", "https://example.com/not-in-brief", EVIDENCE)["verdict"] == "fail")
ck("cited URL + empty field → fail (citation without output)",
   vsg.gate_variant("", "https://example.com/dana-agent-keynote", EVIDENCE)["verdict"] == "fail")
ck("cited URL + hedge → fail (nothing ships even with a citation)",
   vsg.gate_variant("TBD", "https://example.com/dana-agent-keynote", EVIDENCE)["verdict"] == "fail")
ck("None URL is never treated as a citation",
   vsg.gate_variant("prose", None, EVIDENCE)["verdict"] == "fail")

# --- Fact-trace: numbers in prose must come from the cited source ------------------------
ck("sourced number (70, from the cited source) passes the fact-trace",
   vsg.unverified_numbers("You posted that 70% of agent pilots die before production",
                          EVIDENCE[1]) == [])
ck("unsourced number (99) is flagged by the fact-trace",
   vsg.unverified_numbers("70% of pilots die — you said 99%", EVIDENCE[1]) == ["99"])
ck("URL digits never back prose numbers (the anchor is not a fact)",
   vsg.unverified_numbers("See unit 4042", {"url": "https://example.com/row-4042",
                                            "fact": "no digits in this fact"}) == ["4042"])

# --- Dates, counts, enums are computed in code ------------------------------------------
ck("date rendered from the source's machine value",
   vsg.fmt_date(EVIDENCE[0]["date"]) == "November 12, 2026")
ck("absent date → empty-string abstain", vsg.fmt_date(None) == "")
ck("count computed from the machine integer",
   vsg.fmt_count(1, "keynote") == "1 keynote")
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
try:
    vsg.evidence_urls([{"no_url_here": True}])
    ck("an Evidence-Set row without a URL raises", False)
except ValueError:
    ck("an Evidence-Set row without a URL raises", True)

# --- Privacy: fixture content is fictional, no private-input references -----------------
fixture_blob = repr(EVIDENCE) + repr(zero_run)
for forbidden in ("me-model", "target-companies", "@", "github.com/AlexYedi"):
    ck(f"fixture contains no {forbidden!r} reference", forbidden not in fixture_blob)

print(f"\n{n}/{ok} passed" if ok == n else f"\nFAILED: {ok}/{n} passed")
sys.exit(0 if ok == n else 1)
