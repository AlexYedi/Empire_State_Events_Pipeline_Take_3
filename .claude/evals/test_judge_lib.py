#!/usr/bin/env python3
"""test_judge_lib.py: judge_lib.score() must equal the jq scorer inside gemini-judge.sh, on every fixture (YED-209).

Two seats scored by two different arithmetics would make "divergence" meaningless. The jq program is EXTRACTED
from gemini-judge.sh at test time, so if either side drifts this test fails. Also covers quote verification,
the must-cite rule, and the budget guard. Run: python3 .claude/evals/test_judge_lib.py
"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_lib as jl

src = open(".claude/hooks/gemini-judge.sh", encoding="utf-8").read()
m = re.search(r"jq -c --arg atype \"\$ATYPE\" --argjson dangling \"\$HAS_DANGLING\" '\n(.*?)'\)\n", src, re.S)
assert m, "could not find the jq scorer in gemini-judge.sh (did it move? update this test)"
JQ = m.group(1)


def jq_score(v, atype, dangling):
    r = subprocess.run(["jq", "-c", "--arg", "atype", atype, "--argjson", "dangling", json.dumps(dangling), JQ],
                       input=json.dumps(v), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def V(scores, **flags):
    f = {"confidence_honesty_violation": False, "spec_drift": False, "command_skeleton_absent": False, "density_padding": False}
    f.update(flags)
    return {"criterion_scores": [{"id": c, "score": s, "reasoning": "r"} for c, s in zip(jl.CRITERIA, scores)],
            "defects": [], "checks_performed": ["x"], "cap_flags": f}


FIX = [("flat ceiling", V([1, 1, 1, 1, 1]), "skill", False), ("nits", V([.85, .9, .85, .95, .8]), "skill", False),
       ("right on the pass line", V([.7, .7, .7, .7, .7]), "code", False), ("just under", V([.69, .7, .7, .7, .7]), "code", False),
       ("spec drift caps correctness", V([.95, .9, .9, .9, .9], spec_drift=True), "code", False),
       ("honesty cap", V([.95, .95, .95, .95, .95], confidence_honesty_violation=True), "skill", False),
       ("dangling caps both", V([.95, .95, .95, .95, .95]), "skill", True),
       ("command skeleton", V([.9, .9, .9, .9, .9], command_skeleton_absent=True), "command", False),
       ("skeleton flag ignored off-type", V([.9, .9, .9, .9, .9], command_skeleton_absent=True), "skill", False),
       ("density only on deep_read", V([.9, .9, .9, .9, .9], density_padding=True), "deep_read", False),
       ("density ignored off-type", V([.9, .9, .9, .9, .9], density_padding=True), "skill", False),
       ("out of range clamps", V([1.4, -0.2, .9, .9, .9]), "skill", False)]
ok = n = 0


def ck(name, cond):
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name)


for name, v, atype, dang in FIX:
    a, b = jl.score(v, atype, dang), jq_score(v, atype, dang)
    same = all(a[k] == b[k] for k in ("weighted_score", "raw_score", "verdict", "flat_ceiling")) and \
        [c["score"] for c in a["criterion_scores"]] == [c["score"] for c in b["criterion_scores"]]
    ck(f"score parity python==jq: {name}  ({a['weighted_score']} {a['verdict']})", same)

for bad in ({"criterion_scores": []}, V([1, 1, 1, 1, None])):
    try:
        jl.score(bad, "skill", False); ck("malformed verdict rejected", False)
    except jl.JudgeError:
        ck("malformed verdict rejected", True)

art = "def f():\n    return  1   # the answer\n"
q = jl.verify_quotes([{"quote": "return 1 # the answer"}, {"quote": "this text is not there"}, {"quote": ""}], art)
ck("quotes: whitespace-normalised match passes, a fabricated one fails, empty ignored", q["quoted"] == 2 and q["unverified"] == 1)
ck("quotes: >30% unverified => evidence_unverified", q["evidence_unverified"] is True)
ck("quotes: all real => verified", jl.verify_quotes([{"quote": "def f():"}], art)["evidence_unverified"] is False)
s = jl.score(V([.8, .9, .9, .9, .9]), "skill", False)
ck("must-cite: <0.85 with no defect is reported", jl.must_cite_gaps(s) == ["correctness"])
s["defects"] = [{"criterion": "correctness"}]
ck("must-cite: satisfied by a defect on that criterion", jl.must_cite_gaps(s) == [])

with tempfile.TemporaryDirectory() as d:
    jl.LEDGER = os.path.join(d, "ledger.jsonl")
    ck("budget: a priced model under the caps is allowed", jl.check_budget("openai", "gpt-5.4", 20000, 16000) > 0)
    try:
        jl.check_budget("openai", "not-a-model", 1, 1); ck("budget: unpriced model refused", False)
    except jl.BudgetExceeded:
        ck("budget: unpriced model refused", True)
    jl.ledger_append(provider="openai", cost_usd=44.9)
    try:
        jl.check_budget("openai", "gpt-5.4", 20000, 16000); ck("budget: lifetime cap enforced", False)
    except jl.BudgetExceeded:
        ck("budget: lifetime cap enforced", True)
    jl.ledger_append(provider="google", cost_usd=999)
    ck("budget: another provider's spend is not counted", jl.spent("openai")[1] == 44.9)

print(f"{ok}/{n} judge_lib cases pass")
sys.exit(0 if ok == n else 1)
