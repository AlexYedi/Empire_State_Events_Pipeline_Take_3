#!/usr/bin/env python3
"""test_tag_outcome_taxonomy.py — convention checks for the tag-outcome reply taxonomy (E-09 / Eric P3, YED-220).

The rules this encodes: connection/meeting replies grade into the 11-label taxonomy
(positives = positive_interested + positive_soft + positive_referral), and Outcome Value is
positives ÷ sent recorded ALONGSIDE its null baseline (YED-212) — never one without the other,
and the baseline itself is never invented. The baseline travels with the outcome as three
fields (null_baseline / baseline_method / baseline_date); the value-action registry was
deliberately retired (commit 5b1b1ed) and must not reappear here.
Offline, free; run from the repo root: `python3 .claude/scripts/test_tag_outcome_taxonomy.py`
(--selftest runs the same suite; everything in it is offline).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, ".claude", "skills", "tag-outcome", "SKILL.md")
FIXTURE = os.path.join(ROOT, ".claude", "skills", "tag-outcome", "fixtures", "reply-grading-fixture.md")

EXPECTED_LABELS = [
    "positive_interested", "positive_soft", "positive_referral",
    "neutral_question",
    "negative_notnow", "negative_notfit", "negative_hostile",
    "no_response", "ooo", "bounce", "other",
]
POSITIVE_LABELS = ["positive_interested", "positive_soft", "positive_referral"]

ok = n = 0
def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)

skill = open(SKILL, encoding="utf-8").read()
fixture = open(FIXTURE, encoding="utf-8").read() if os.path.exists(FIXTURE) else ""

# --- Skill: the 11-label taxonomy ---
rows = re.findall(r"^\| `([a-z_]+)` \|", skill, re.M)
ck("SKILL.md defines exactly 11 labels, in the source's order", rows == EXPECTED_LABELS)
ck("no duplicate or stray label rows", len(rows) == 11)
ck("the three positive labels are the positive set",
   all(f"`{l}`" in skill for l in POSITIVE_LABELS))
ck("`no_response` is a label (the dominant outcome for 1:1 outreach needs an explicit home)",
   "no_response" in rows)
ck("negative_hostile is tracked as a risk signal, not just a bucket",
   "risk signal" in skill)

# --- Skill: positives ÷ sent alongside the null baseline (YED-212) ---
ck("Outcome Value pairs positives ÷ sent WITH its null baseline (YED-212 named)",
   "positives ÷ sent" in skill and "YED-212" in skill)
ck("the baseline travels with the outcome as three fields",
   all(f in skill for f in ("`null_baseline`", "`baseline_method`", "`baseline_date`")))
ck("absent baseline → recorded `none` + surfaced gap, never invented",
   "null_baseline: none" in skill and re.search(r"never invent a baseline", skill, re.I) is not None)
ck("the retired value-action registry is not revived (no reference anywhere in the skill)",
   "value-action-registry" not in skill)
ck("ooo and bounce are excluded from the denominator",
   skill.count("excluded from the denominator") >= 2)
ck("first reply per person only (later messages are conversation, not signal)",
   "first reply per person" in skill)
ck("adaptation is cited (source skill + harvest note), not silent",
   "positive-reply-scoring" in skill and "eric-coldoutboundskills-harvest" in skill)

# --- Fixture: worked example, arithmetic recomputed from the fixture itself ---
labels = re.findall(r"\| \d+ \| [^|]+ \| [^|]+ \| [^|]+ \| `([a-z_]+)` \|", fixture)
ck("fixture grades a full sent set (10 rows) using only taxonomy labels",
   len(labels) == 10 and all(l in EXPECTED_LABELS for l in labels))
positives = sum(labels.count(l) for l in POSITIVE_LABELS)
excluded = labels.count("ooo") + labels.count("bounce")
denom = len(labels) - excluded
rate = f"{100 * positives / denom:.1f}%"
ck(f"fixture arithmetic matches the rule ({positives} positives ÷ {denom} = {rate})",
   positives == 3 and denom == 8 and rate == "37.5%" and "3/8" in fixture and "37.5%" in fixture)
m = re.search(r"positives 3/8 sent = 37\.5% vs null baseline [0-9.]+% \(do-nothing; method: [^;]+; [0-9]{4}-[0-9]{2}-[0-9]{2}[^)]*\)", fixture)
ck("fixture's Outcome Value line records the rate AND all three baseline fields", bool(m))
ck("fixture labels its baseline values as placeholders, never real measurements",
   "fictional fixture placeholder" in fixture)
ck("fixture demonstrates the three baseline fields explicitly",
   all(f in fixture for f in ("`null_baseline`", "`baseline_method`", "`baseline_date`")))

# --- Privacy gates (AGENTS.md rules 1/4; Blueprint privacy checks) ---
ck("fixture holds no contact data — no emails or phones, only fictional names", "@" not in fixture)
ck("no private-input filenames inside the fixture",
   "me-model" not in fixture and "target-companies" not in fixture)
ck("the retired registry is not referenced by the fixture either",
   "value-action-registry" not in fixture)
ck("fixture declares itself fictional end to end", "Everything here is fictional" in fixture)

print(f"\n{ok}/{n} tag-outcome taxonomy cases pass")
print(f"selftest: {ok}/{n} cases pass")
sys.exit(0 if ok == n else 1)
