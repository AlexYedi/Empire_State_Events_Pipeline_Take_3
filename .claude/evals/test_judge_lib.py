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
    f = {"confidence_honesty_violation": False, "spec_drift": False, "command_skeleton_absent": False, "density_padding": False,
         "privacy_layer_defect": False}
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
       ("out of range clamps", V([1.4, -0.2, .9, .9, .9]), "skill", False),
       # @6 (YED-231): a confirmed defect in any privacy layer flags, whatever the backstop
       ("privacy-layer cap flags a strong artifact", V([.95, .95, .95, .95, .95], privacy_layer_defect=True), "code", False),
       ("YED-236 regression: 0.784 pass -> flag", V([.75, .72, .85, .9, .65], privacy_layer_defect=True), "code", False),
       ("privacy flag off = @5 arithmetic", V([.75, .72, .85, .9, .65]), "code", False)]
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

# quorum-merge.sh keeps a THIRD copy of the composite arithmetic (its Claude-seat recompute). Bind it to judge_lib
# too (judge on the @6 build, 2026-09-28): extracted at test time, compared on every fixture it is defined for.
# It applies no dangling cap and applies density/skeleton regardless of artifact type, so those fixtures are skipped.
qsrc = open(".claude/hooks/quorum-merge.sh", encoding="utf-8").read()
qm = re.search(r"CV=\$\(printf '%s' \"\$CV\" \| jq -c '\n(.*?)'\)\n", qsrc, re.S)
ck("quorum-merge.sh recompute jq found", bool(qm))
if qm:
    for name, v, atype, dang in FIX:
        fl = v["cap_flags"]
        if dang or fl.get("density_padding") or fl.get("command_skeleton_absent"):
            continue
        r = subprocess.run(["jq", "-c", qm.group(1)], input=json.dumps(v), capture_output=True, text=True)
        q = json.loads(r.stdout) if r.returncode == 0 else {}
        a = jl.score(v, atype, dang)
        ck(f"score parity python==quorum-merge.sh: {name}  ({a['weighted_score']} {a['verdict']})",
           q.get("weighted_score") == a["weighted_score"] and q.get("verdict") == a["verdict"])

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
# YED-223: formatting a seat drops or re-renders in PROSE is not fabrication …
md = "**One exception — the emerging-seller signal:** when the JD pitches `x` at an early-career seller"
vq = lambda q, text, t: jl.verify_quotes([{"quote": q}], text, t)
ck("quotes: prose — stripped ** and backticks still verify",
   vq("One exception — the emerging-seller signal: when the JD pitches x", md, "skill")["unverified"] == 0)
ck("quotes: prose — em-dash rendered as a colon still verifies", vq("One exception: the emerging-seller signal", md, "skill")["unverified"] == 0)
ck("quotes: prose — spaced single hyphen swaps with an em-dash", vq("One exception - the emerging-seller signal", md, "ref")["unverified"] == 0)
ck("quotes: exact-mismatch count kept as a secondary field", vq("One exception: the emerging-seller signal", md, "skill")["unverified_exact"] == 1)
ck("quotes: prose — invented text still unverified", vq("the JD pitches it at a senior seller", md, "skill")["unverified"] == 1)
ck("quotes: an unknown artifact type is matched strictly", vq("One exception: the emerging-seller signal", md, None)["unverified"] == 1)
# … but in CODE every delimiter is syntax: judge rounds 1-2 fabrications, pinned as must-fail (strict mode)
code = ('x = hay_loose\ndef verify_quotes(defects, text):\n    print("ignored with --bundle")\n'
        'def __init__(self, _private, *args, **kwargs):\n')
for fake, why in (("hayloose", "intraword underscore"), ("def verifyquotes(defects, text):", "identifier underscore"),
                  ("ignored with: bundle", "`--` flag prefix"), ("def init(self", "dunder"),
                  ("self, private,", "leading underscore"), ("private, args, kwargs", "*args / **kwargs")):
    for t_ in ("code", "hook"):
        ck(f"quotes: {t_} — fabricated quote rejected ({why})", vq(fake, code, t_)["unverified"] == 1)
ck("quotes: code — a real snake_case quote still verifies", vq("x = hay_loose", code, "code")["unverified"] == 0)
# and prose mode never touches `_`, so a prose artifact quoting code is still safe on identifiers
ck("quotes: prose — underscores are never stripped", vq("hayloose", code, "skill")["unverified"] == 1)
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
    os.environ.pop("JUDGE_TOTAL_CAP_USD", None); os.environ.pop("JUDGE_MONTHLY_CAP_USD", None)
    with open(jl.LEDGER, "a") as f:                  # $44.90 spent in an EARLIER month: counts toward lifetime only
        f.write(json.dumps({"ts": "2020-01-15T00:00:00Z", "provider": "openai", "cost_usd": 44.9}) + "\n")
    ck("budget: no lifetime cap by default (lifted 2026-09-27) — old spend does not block",
       jl.check_budget("openai", "gpt-5.4", 20000, 16000) > 0)
    os.environ["JUDGE_TOTAL_CAP_USD"] = "45"
    try:
        jl.check_budget("openai", "gpt-5.4", 20000, 16000); ck("budget: opt-in lifetime cap still enforced", False)
    except jl.BudgetExceeded:
        ck("budget: opt-in lifetime cap still enforced", True)
    os.environ.pop("JUDGE_TOTAL_CAP_USD", None)
    jl.ledger_append(provider="openai", cost_usd=19.9)   # THIS month
    try:
        jl.check_budget("openai", "gpt-5.4", 20000, 16000); ck("budget: $20 monthly cap enforced", False)
    except jl.BudgetExceeded:
        ck("budget: $20 monthly cap enforced", True)
    jl.ledger_append(provider="google", cost_usd=999)
    ck("budget: another provider's spend is not counted", round(jl.spent("openai")[1], 2) == 64.8)

# YED-223: the build-time parity warning fires for a spec-less bundle and stays quiet for a specced one
import subprocess as _sp, tempfile as _tf, os as _os
for ctx, want in (("", True), ("x" * 500, False)):
    fd, out = _tf.mkstemp(suffix=".json"); _os.close(fd)
    p = _sp.run(["python3", ".claude/evals/judge_lib.py", "bundle", "--artifact", ".claude/evals/judge_lib.py",
                 "--artifact-type", "code", "--context", ctx, "--out", out], capture_output=True, text=True)
    _os.unlink(out)
    ck(f"bundle build: parity warning {'fires' if want else 'stays quiet'} ({len(ctx)}-char context)",
       ("EVIDENCE-PARITY WARNING" in p.stderr) == want and p.returncode == 0)

print(f"{ok}/{n} judge_lib cases pass")
sys.exit(0 if ok == n else 1)
