#!/usr/bin/env python3
"""test_variant_tags.py — offline convention check for the tagged 3-variant experiment fixture
(E-09 / YED-220, harvest note row 4). Synthetic numbers only; no private inputs, no network.

Verifies the fixture in `.claude/skills/content-patterns/fixtures/tagged-variants.md` applies the
goal-tagging variant convention: every differing variant carries a `variant_tag:` from the
enumerated set, verdicts match the baseline-relative thresholds (winner >= 2x, loser < 50%,
21-day wait), and a kill verdict logs its reason. Enforcement is tag-only (Blueprint judgment
J3): the checker NEVER rejects a variant for changing more than its tagged variable — it only
verifies a tag exists and the numbers/verdicts agree.

Usage: python3 .claude/scripts/test_variant_tags.py [--selftest | path/to/fixture.md]
"""
import datetime as dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "..", "skills", "content-patterns", "fixtures", "tagged-variants.md")

ALLOWED_TAGS = {"hook_type", "format", "opener"}
PRIVATE_INPUTS = ("me-model.md", "target-companies.md")  # CLAUDE.md invariant 4 — never in fixtures

_VERDICT_WORD = {"winner": "keep", "loser": "kill", "in_band": "iterate"}


def compute_verdict(rate_pct: float, baseline_pct: float):
    """Baseline-relative verdict per goal-tagging.md: >=2x winner, <50% loser, else in band."""
    if baseline_pct <= 0:
        raise ValueError("baseline must be positive (a null baseline of 0 cannot be scaled)")
    ratio = rate_pct / baseline_pct
    if ratio >= 2.0:
        return "winner", ratio
    if ratio < 0.5:
        return "loser", ratio
    return "in_band", ratio


def parse_experiment(text: str) -> dict:
    """Parse the fixture markdown into its experiment block and variant sections."""
    baseline_m = re.search(r"^- baseline:\s*([\d.]+)\s*%", text, re.M)
    launched_m = re.search(r"^- launched:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    judged_m = re.search(r"^- judged:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    sections = re.split(r"^## ", text, flags=re.M)[1:]
    variants = []
    for sec in sections:
        name = sec.splitlines()[0].strip()
        tag_m = re.search(r"^variant_tag:\s*(\S+)", sec, re.M)
        result_m = re.search(r"^result:\s*([\d.]+)\s*%", sec, re.M)
        verdict_m = re.search(r"^verdict:\s*(\w+)", sec, re.M)
        variants.append({
            "name": name,
            "tag": tag_m.group(1) if tag_m else None,
            "result": float(result_m.group(1)) if result_m else None,
            "verdict_word": verdict_m.group(1).lower() if verdict_m else None,
            "section": sec,
        })
    return {
        "baseline": float(baseline_m.group(1)) if baseline_m else None,
        "launched": launched_m.group(1) if launched_m else None,
        "judged": judged_m.group(1) if judged_m else None,
        "variants": [v for v in variants if v["tag"] or v["result"] is not None],
    }


def check_fixture(text: str) -> list:
    """Return a list of convention violations (empty = fixture passes). Tag-only: multi-change
    variants are never flagged for their content, only for a missing/unknown tag or bad numbers."""
    findings = []
    exp = parse_experiment(text)
    if exp["baseline"] is None:
        return ["no `baseline: N%` line in the experiment block"]
    if not (exp["launched"] and exp["judged"]):
        return ["missing `launched:` / `judged:` dates in the experiment block"]
    wait = (dt.date.fromisoformat(exp["judged"]) - dt.date.fromisoformat(exp["launched"])).days
    if wait < 21:
        findings.append(f"judged {wait} days after launch — the 21-day wait was not satisfied")
    if not exp["variants"]:
        findings.append("no tagged variant sections found")
    for v in exp["variants"]:
        name = v["name"] or "unnamed"
        if not v["tag"]:
            findings.append(f"{name}: differing variant carries no variant_tag")
            continue
        if v["tag"] not in ALLOWED_TAGS:
            findings.append(f"{name}: variant_tag '{v['tag']}' not in {sorted(ALLOWED_TAGS)}")
        if v["result"] is None:
            findings.append(f"{name}: no `result: N%` line")
            continue
        expected, ratio = compute_verdict(v["result"], exp["baseline"])
        got = v["verdict_word"]
        if got != _VERDICT_WORD[expected]:
            findings.append(f"{name}: result is {v['result']}% ({ratio:.2f}x baseline) → expected "
                            f"'{_VERDICT_WORD[expected]}', found '{got}'")
        if expected == "loser" and not re.search(r"reason logged", v["section"], re.I):
            findings.append(f"{name}: kill verdict without a logged reason")
    for private in PRIVATE_INPUTS:
        if private.lower() in text.lower():
            findings.append(f"private-input filename `{private}` appears in the fixture (invariant 4)")
    return findings


ok = n = 0


def ck(name, cond):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name)


def selftest():
    fixture_text = open(FIXTURE, encoding="utf-8").read()

    # Threshold math (boundary-inclusive: exactly 2.0x is a winner, exactly 0.5x is in band).
    ck("2.25x baseline → winner", compute_verdict(4.5, 2.0)[0] == "winner")
    ck("0.40x baseline → loser", compute_verdict(0.8, 2.0)[0] == "loser")
    ck("1.30x baseline → in band", compute_verdict(2.6, 2.0)[0] == "in_band")
    ck("exactly 2.0x → winner (boundary inclusive)", compute_verdict(4.0, 2.0)[0] == "winner")
    ck("exactly 0.5x → in band (loser is strictly <50%)", compute_verdict(1.0, 2.0)[0] == "in_band")

    # The committed fixture passes end to end.
    ck("committed fixture passes the convention check", check_fixture(fixture_text) == [])

    # Tag-only enforcement (J3): a variant that changed two things but carries a valid tag and
    # honest numbers must NOT be rejected — the checker never inspects prose for discipline.
    multi_change = fixture_text + (
        "\n## Variant D\n\nvariant_tag: opener\nresult: 3.0% engagement\n"
        "verdict: iterate — 1.50× baseline (in band). Also changed the hook — noted in the log.\n"
    )
    ck("multi-change variant is NOT rejected (tag-only, J3)", check_fixture(multi_change) == [])

    # Missing tag on a differing variant → finding.
    untagged = fixture_text.replace("variant_tag: opener\n", "")
    ck("untagged variant produces a finding", any("no variant_tag" in f for f in check_fixture(untagged)))

    # Unknown tag value → finding.
    bad_tag = fixture_text.replace("variant_tag: opener", "variant_tag: color")
    ck("unknown tag value produces a finding", any("not in" in f for f in check_fixture(bad_tag)))

    # Verdict that contradicts the thresholds → finding.
    wrong = fixture_text.replace("verdict: kill — 0.40×", "verdict: keep — 0.40×")
    ck("verdict contradicting the thresholds produces a finding", any("expected" in f for f in check_fixture(wrong)))

    # Kill without a logged reason → finding.
    no_reason = fixture_text.replace("Reason logged: the essay format", "The essay format")
    ck("kill verdict without a logged reason produces a finding",
       any("logged reason" in f for f in check_fixture(no_reason)))

    # Judging early → finding.
    early = fixture_text.replace("- judged: 2026-10-22", "- judged: 2026-10-08")
    ck("judging before 21 days produces a finding", any("21-day" in f for f in check_fixture(early)))

    # Private-input grep gate (invariant 4).
    leak = fixture_text.replace("linkedin_post_post", "linkedin_post_post (mirrors me-model.md §2)")
    ck("private-input filename in fixture produces a finding", check_fixture(leak) != [] and not check_fixture(fixture_text))

    print(f"selftest: {ok}/{n} cases passed")
    return ok == n


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    path = sys.argv[1] if len(sys.argv) > 1 else FIXTURE
    text = open(path, encoding="utf-8").read()
    findings = check_fixture(text)
    for f in findings:
        print(f"  ✗ {f}")
    print(f"{'FAIL' if findings else 'pass'}  {path}")
    sys.exit(1 if findings else 0)
