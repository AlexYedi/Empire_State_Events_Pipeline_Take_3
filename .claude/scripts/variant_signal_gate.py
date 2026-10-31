#!/usr/bin/env python3
"""variant_signal_gate.py — Eric P1 fact-before-prose + abstain-empty, as code (E-09, YED-220).

The model only turns facts a structured source has already proven into prose — it never
establishes a fact. Each A/B outreach variant must cite its signal: the **source URL from
the research brief's Evidence Set** (the URL-carrying evidence ledger, per event-research
Step 3 / ADR-5), plus the person/topic block it sits in. With no cited signal the variant
field is the EMPTY STRING and nothing ships. Abstain is "", never "N/A", never a hedge.
Dates, counts, and enums are computed in code from the source's machine values.

The cited anchor is verifiable: `gate_variant` checks that the cited URL appears in the
brief's Evidence Set — the same source-check discipline the output evaluator applies to
claims. An invented citation fails the gate exactly like a missing one.

Source: docs/archive/notes/eric-coldoutboundskills-harvest-2026-09-24.md §3 row 1
(coldoutboundskills `clay-playbooks/SKILL.md` rules 2–4). Citation scheme re-pointed from
row ids to Evidence-Set URLs per Alex's PR #243 second-look review (briefs are Notion
pages with sections, not rows with ids — a row-id scheme would force invented citations).

Offline proof: python3 .claude/scripts/test_variant_signal_gate.py
Selftest:      python3 .claude/scripts/variant_signal_gate.py --selftest
"""
import datetime
import re
import sys

# The abstain value — the ONLY sanctioned representation of an absent variant field.
EMPTY = ""

# Strings that look like an abstain but are not the abstain. Never ship these.
HEDGES = frozenset({
    "n/a", "na", "n.a", "n.a.", "unknown", "unk", "tbd", "tbc",
    "to be determined", "not applicable", "none available", "no signal",
    "-", "--", "—", "?", "todo", "pending",
})


def is_hedge(value):
    """True when value is one of the forbidden placeholder strings (case/period-insensitive)."""
    if not isinstance(value, str):
        return False
    v = value.strip().casefold().rstrip(".! ")
    return v in HEDGES


def evidence_urls(evidence_set):
    """The set of Evidence-Set URLs a variant may cite. Rows are the brief's URL-carrying
    evidence ledger (dicts with a "url" key; may also carry tier/source/date)."""
    try:
        return {r["url"] for r in evidence_set}
    except (TypeError, KeyError) as e:
        raise ValueError(f"evidence_set must be dicts with a 'url' key: {e}") from e


def gate_variant(text, source_url, evidence_set):
    """Verdict for one variant field against the brief's Evidence Set.

    source_url: the Evidence-Set URL the variant was built from (the citation anchor),
    evidence_set: iterable of Evidence-Set row dicts. Returns {"verdict", "reason"}:

    - "ship":    cites a URL present in the Evidence Set and carries prose built from it
    - "abstain": no cited URL and the field is the empty string — correct; ships empty
    - "fail":    no cited URL but the field carries prose or a hedge (nothing ships);
                 cites a URL while the field is empty (citation without output); or cites
                 a URL that is NOT in the Evidence Set — an invented citation is worse
                 than no citation
    """
    cited = source_url in evidence_urls(evidence_set)  # None is never an Evidence-Set URL
    if cited:
        if text is None or text.strip() == "":
            return {"verdict": "fail",
                    "reason": f"cites {source_url!r} but the field is empty — build the prose from the cited source, or drop the citation and abstain"}
        if is_hedge(text):
            return {"verdict": "fail",
                    "reason": f"hedge {text!r} with a citation is still nothing shipped — abstain is the empty string"}
        return {"verdict": "ship", "reason": f"prose built from cited Evidence-Set source {source_url!r}"}
    if text is None or text.strip() == "":
        return {"verdict": "abstain",
                "reason": "no cited Evidence-Set source and the field is the empty string — nothing ships (correct abstain)"}
    if is_hedge(text):
        return {"verdict": "fail",
                "reason": f"hedge {text!r} masquerading as an abstain — abstain is the empty string"}
    return {"verdict": "fail",
            "reason": "prose with no cited Evidence-Set source — the model never establishes a fact; nothing ships"}


def run_variants(variants, evidence_set):
    """Gate a batch of variants. Each is a dict {field, text, source_url}; returns
    [{field, source_url, verdict, reason}] in input order."""
    results = []
    for v in variants:
        res = gate_variant(v["text"], v["source_url"], evidence_set)
        results.append({"field": v["field"], "source_url": v["source_url"], **res})
    return results


def fmt_date(iso_date):
    """Compute the display date from a machine ISO value — never retype dates as prose.
    Absent input → the empty-string abstain."""
    if iso_date is None or iso_date == "":
        return EMPTY
    try:
        d = datetime.date.fromisoformat(str(iso_date))
    except ValueError as e:
        raise ValueError(f"fmt_date: {iso_date!r} is not an ISO date — dates arrive as machine values, never as prose") from e
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def fmt_count(n, singular, plural=None):
    """Compute the display count from a machine integer — never retype counts as prose.
    Absent input → the empty-string abstain."""
    if n is None or n == "":
        return EMPTY
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"fmt_count: {n!r} is not an int — counts arrive as machine values, never as prose")
    plural = plural if plural is not None else singular + "s"
    return f"{n:,} {singular if n == 1 else plural}"


def fmt_enum(value, allowed, label="enum"):
    """Validate an enum field against its allowed set — enums arrive as machine values.
    Absent input → the empty-string abstain; out-of-set value raises."""
    if value is None or value == "":
        return EMPTY
    if value not in allowed:
        raise ValueError(f"fmt_{label}: {value!r} is not one of {sorted(allowed)}")
    return value


_NUM_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def unverified_numbers(text, source_row):
    """Numbers stated in prose that the cited source does not back.

    The executable half of fact-before-prose: every number in a variant's prose must
    trace to a machine value in its cited Evidence-Set row (as a number, or as a
    substring of one of the row's string values — "70" traces to "70% of pilots die").
    The row's citation keys ("url", "id") never back numbers: a URL is the anchor, not a
    fact — its digits cannot legitimize prose. Returns the list of untraced number
    tokens; empty list = every number is sourced. Generators run this before shipping;
    the presentation channel's own constants (e.g. the 200-char cap) are the caller's
    business and never pass through here.
    """
    backed = set()
    for k, v in (source_row.items() if isinstance(source_row, dict) else [(None, source_row)]):
        if k in ("url", "id"):
            continue
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            backed.add(str(v))
        for tok in _NUM_RE.findall(str(v)):
            backed.add(tok.replace(",", ""))
            backed.add(str(int(float(tok))) if _is_decimal(tok) else tok)
    unverified = []
    for tok in _NUM_RE.findall(text):
        clean = tok.replace(",", "")
        if clean not in backed:
            unverified.append(tok)
    return unverified


def _is_decimal(tok):
    return "." in tok


# --- selftest -------------------------------------------------------------

def _selftest():
    evidence = [
        {"url": "https://example.com/dana-agent-keynote",
         "source": "SignalFest keynote abstract",
         "block": "Dana Okafor — person block",
         "fact": "Keynote on evaluation-driven agent rollouts", "date": "2026-11-12"},
        {"url": "https://example.com/dana-pilots-post",
         "source": "LinkedIn post",
         "block": "Dana Okafor — person block",
         "fact": "70% of agent pilots die before production", "date": "2026-10-20"},
    ]
    cases = [
        ("no cited source + prose → fail", "fail",
         gate_variant("Great keynote!", None, evidence)["verdict"]),
        ("no cited source + empty → abstain", "abstain",
         gate_variant(EMPTY, None, evidence)["verdict"]),
        ("no cited source + hedge → fail", "fail",
         gate_variant("N/A", None, evidence)["verdict"]),
        ("hedge dash rejected", "fail",
         gate_variant("—", None, evidence)["verdict"]),
        ("cited Evidence-Set URL + prose → ship", "ship",
         gate_variant("Your SignalFest keynote on agent evaluation — does it survive contact with production?",
                      "https://example.com/dana-agent-keynote", evidence)["verdict"]),
        ("URL not in the Evidence Set → fail", "fail",
         gate_variant("prose", "https://example.com/not-in-brief", evidence)["verdict"]),
        ("cited URL + empty field → fail", "fail",
         gate_variant(EMPTY, "https://example.com/dana-agent-keynote", evidence)["verdict"]),
        ("cited URL + hedge → fail", "fail",
         gate_variant("TBD", "https://example.com/dana-agent-keynote", evidence)["verdict"]),
        ("fmt_date computes from machine value", "November 12, 2026",
         fmt_date("2026-11-12")),
        ("fmt_date absent → empty abstain", EMPTY, fmt_date(None)),
        ("fmt_count computes from machine value", "1 talk", fmt_count(1, "talk")),
        ("fmt_count absent → empty abstain", EMPTY, fmt_count(None, "talk")),
        ("fmt_enum passes an allowed value", "sales_led",
         fmt_enum("sales_led", {"sales_led", "plg", "partner"}, "gtm_motion")),
        ("unverified_numbers flags an unsourced number", ["99"],
         unverified_numbers("70% of pilots die — you said 99%", evidence[1])),
        ("unverified_numbers passes a sourced number", [],
         unverified_numbers("You posted that 70% of agent pilots die", evidence[1])),
        ("URL digits never back prose numbers", ["4042"],
         unverified_numbers("See unit 4042", {"url": "https://example.com/row-4042",
                                              "fact": "no digits in this fact"})),
        ("is_hedge catches TBD", True, is_hedge("TBD")),
    ]
    ok = 0
    for name, want, got in cases:
        passed = want == got
        ok += passed
        print(("  ✓ " if passed else "  ✗ ") + name + ("" if passed else f" — want {want!r}, got {got!r}"))
    print(f"selftest: {ok}/{len(cases)} passed")
    return ok == len(cases)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    print(__doc__)
    sys.exit(2)
