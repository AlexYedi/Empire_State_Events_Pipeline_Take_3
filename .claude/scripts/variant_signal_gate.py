#!/usr/bin/env python3
"""variant_signal_gate.py — Eric P1 fact-before-prose + abstain-empty, as code (E-09, YED-220).

The model only turns facts a structured source (a research-brief signal row) has already
proven into prose — it never establishes a fact. Each A/B outreach variant must cite the
signal row it was built from; with no cited signal the variant field is the EMPTY STRING
and nothing ships. Abstain is "", never "N/A", never a hedge. Dates, counts, and enums
are computed in code from the row's machine values.

Source: docs/archive/notes/eric-coldoutboundskills-harvest-2026-09-24.md §3 row 1
(coldoutboundskills `clay-playbooks/SKILL.md` rules 2–4).

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


def gate_variant(text, signal_row_id, signal_rows):
    """Verdict for one variant field against the structured source rows.

    signal_rows: iterable of dicts, each with an "id" key (the structured source the
    model may turn into prose). Returns {"verdict", "reason"}:

    - "ship":    cites a known row and carries prose built from it
    - "abstain": no cited row and the field is the empty string — correct; ships empty
    - "fail":    no cited row but the field carries prose or a hedge (nothing ships);
                 or cites a row while the field is empty (citation without output)
    """
    try:
        rows = {r["id"] for r in signal_rows}
    except (TypeError, KeyError) as e:
        raise ValueError(f"signal_rows must be dicts with an 'id' key: {e}") from e
    cited = signal_row_id in rows  # None is never a row id
    if cited:
        if text is None or text.strip() == "":
            return {"verdict": "fail",
                    "reason": f"cites row {signal_row_id!r} but the field is empty — build the prose from the row, or drop the citation and abstain"}
        return {"verdict": "ship", "reason": f"prose built from cited row {signal_row_id!r}"}
    if text is None or text.strip() == "":
        return {"verdict": "abstain",
                "reason": "no cited signal row and the field is the empty string — nothing ships (correct abstain)"}
    if is_hedge(text):
        return {"verdict": "fail",
                "reason": f"hedge {text!r} masquerading as an abstain — abstain is the empty string"}
    return {"verdict": "fail",
            "reason": "prose with no cited signal row — the model never establishes a fact; nothing ships"}


def run_variants(variants, signal_rows):
    """Gate a batch of variants. Each is a dict {field, text, signal_row}; returns
    [{field, signal_row, verdict, reason}] in input order."""
    results = []
    for v in variants:
        res = gate_variant(v["text"], v["signal_row"], signal_rows)
        results.append({"field": v["field"], "signal_row": v["signal_row"], **res})
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


def unverified_numbers(text, row):
    """Numbers stated in prose that the cited row does not back.

    The executable half of fact-before-prose: every number in a variant's prose must
    trace to a machine value in its cited row (as a number, or as a substring of one of
    the row's string values — "70" traces to "70% of pilots die"). Returns the list of
    untraced number tokens; empty list = every number is sourced. Generators run this
    before shipping; the presentation channel's own constants (e.g. the 200-char cap)
    are the caller's business and never pass through here.
    """
    backed = set()
    for v in (row.values() if isinstance(row, dict) else [row]):
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
    rows = [{"id": "sig-001", "fact": "Keynote at SignalFest on agent evaluation"},
            {"id": "sig-002", "fact": "Posted that 70% of agent pilots die before production"}]
    cases = [
        ("zero cited rows + prose → fail", "fail",
         gate_variant("Great keynote!", None, rows)["verdict"]),
        ("zero cited rows + empty → abstain", "abstain",
         gate_variant(EMPTY, None, rows)["verdict"]),
        ("zero cited rows + hedge → fail", "fail",
         gate_variant("N/A", None, rows)["verdict"]),
        ("hedge dash rejected", "fail",
         gate_variant("—", None, rows)["verdict"]),
        ("valid citation + prose → ship", "ship",
         gate_variant("Your SignalFest keynote on agent evaluation — does it survive contact with production?", "sig-001", rows)["verdict"]),
        ("unknown row id + prose → fail", "fail",
         gate_variant("prose", "sig-999", rows)["verdict"]),
        ("citation + empty field → fail", "fail",
         gate_variant(EMPTY, "sig-001", rows)["verdict"]),
        ("fmt_date computes from machine value", "November 12, 2026",
         fmt_date("2026-11-12")),
        ("fmt_date absent → empty abstain", EMPTY, fmt_date(None)),
        ("fmt_count computes from machine value", "1 talk", fmt_count(1, "talk")),
        ("fmt_count absent → empty abstain", EMPTY, fmt_count(None, "talk")),
        ("fmt_enum passes an allowed value", "sales_led",
         fmt_enum("sales_led", {"sales_led", "plg", "partner"}, "gtm_motion")),
        ("unverified_numbers flags an unsourced number", ["99"],
         unverified_numbers("70% of pilots die — you said 99%", rows[1])),
        ("unverified_numbers passes a sourced number", [],
         unverified_numbers("You posted that 70% of agent pilots die", rows[1])),
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
