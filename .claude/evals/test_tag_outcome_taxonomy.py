#!/usr/bin/env python3
"""test_tag_outcome_taxonomy.py — convention checks for the tag-outcome reply taxonomy (E-09 / Eric P3, YED-220).

The rules this encodes: connection/meeting replies grade into the 11-label taxonomy
(positives = positive_interested + positive_soft + positive_referral), and Outcome Value is
positives ÷ sent recorded ALONGSIDE its null baseline (YED-212) — never one without the other,
and the baseline itself is never invented (it lives in the private value-action registry).
Offline, free; run from the repo root: `python3 .claude/evals/test_tag_outcome_taxonomy.py`.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, ".claude", "skills", "tag-outcome", "SKILL.md")
FIXTURE = os.path.join(ROOT, ".claude", "skills", "tag-outcome", "fixtures", "reply-grading-fixture.md")
REGISTRY = ".claude/references/value-action-registry.md"  # private; checked as a path only

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
ck("ooo and bounce are excluded from the denominator",
   skill.count("excluded from the denominator") >= 2)
ck("first reply per person only (later messages are conversation, not signal)",
   "first reply per person" in skill)
ck("the baseline lives in the value-action registry, read by path",
   REGISTRY in skill and "never copy it into fixtures, tests or committed output" in skill)
ck("the skill forbids inventing a baseline (absent row → recorded gap, not a guess)",
   "Never invent a baseline" in skill)
ck("the registry edit is specified for Alex's session, not done by a PR",
   "Alex's session" in skill and "not in a PR" in skill)
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
m = re.search(r"\[LinkedIn/HubSpot\][^\n]*positives 3/8 sent = 37\.5% vs null baseline [0-9.]+% \(do-nothing\)", fixture)
ck("fixture's Outcome Value line records the rate AND the baseline together", bool(m))
ck("fixture labels its baseline as a placeholder, never a real registry value",
   "fictional fixture placeholder" in fixture)
ck("fixture shows the registry row it would produce (the registry edit stays in Alex's session)",
   "Registry row this fixture would produce" in fixture)

# --- Privacy gates (AGENTS.md rules 1/4; Blueprint privacy checks) ---
ck("fixture holds no contact data — no emails or phones, only fictional names", "@" not in fixture)
ck("no private-input filenames inside the fixture",
   "me-model" not in fixture and "target-companies" not in fixture)
ck("fixture declares itself fictional end to end", "Everything here is fictional" in fixture)
try:
    ignored = subprocess.run(["git", "check-ignore", "-q", REGISTRY], cwd=ROOT).returncode == 0
except OSError:
    ignored = REGISTRY in open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
ck("value-action registry path is gitignored (private reference can never be committed)", ignored)

print(f"{ok}/{n} tag-outcome taxonomy cases pass")
sys.exit(0 if ok == n else 1)
