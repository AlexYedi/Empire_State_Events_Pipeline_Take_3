#!/usr/bin/env python3
"""test_judge_lib.py: the judge's deterministic parts (YED-209; single reviewer since YED-231).

Scores are pinned to fixed expected values (the numbers the jq parity test held until the Gemini adapter was
removed, so the arithmetic is unchanged). Also covers quote verification, the must-cite rule, finalize() (the
only place a final verdict is decided), guarded paths and the judge-layer rule.
Run: python3 .claude/evals/test_judge_lib.py
"""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_lib as jl


def V(scores, **flags):
    f = {"confidence_honesty_violation": False, "spec_drift": False, "command_skeleton_absent": False, "density_padding": False,
         "privacy_layer_defect": False}
    f.update(flags)
    return {"criterion_scores": [{"id": c, "score": s, "reasoning": "r"} for c, s in zip(jl.CRITERIA, scores)],
            "defects": [], "checks_performed": ["x"], "cap_flags": f}


FIX = [("flat ceiling", V([1, 1, 1, 1, 1]), "skill", False, 1.0), ("nits", V([.85, .9, .85, .95, .8]), "skill", False, 0.875),
       ("right on the pass line", V([.7, .7, .7, .7, .7]), "code", False, 0.7),
       ("just under", V([.69, .7, .7, .7, .7]), "code", False, 0.697),
       ("spec drift caps correctness", V([.95, .9, .9, .9, .9], spec_drift=True), "code", False, 0.84),
       ("honesty cap", V([.95, .95, .95, .95, .95], confidence_honesty_violation=True), "skill", False, 0.65),
       ("dangling caps both", V([.95, .95, .95, .95, .95]), "skill", True, 0.6),
       ("command skeleton", V([.9, .9, .9, .9, .9], command_skeleton_absent=True), "command", False, 0.79),
       ("skeleton flag ignored off-type", V([.9, .9, .9, .9, .9], command_skeleton_absent=True), "skill", False, 0.9),
       ("density only on deep_read", V([.9, .9, .9, .9, .9], density_padding=True), "deep_read", False, 0.65),
       ("density ignored off-type", V([.9, .9, .9, .9, .9], density_padding=True), "skill", False, 0.9),
       ("out of range clamps", V([1.4, -0.2, .9, .9, .9]), "skill", False, 0.75),
       # YED-231 item 7: the privacy cap moved out of the score (finalize() flags on it instead; tested below)
       ("privacy flag no longer caps the score", V([.95, .95, .95, .95, .95], privacy_layer_defect=True), "code", False, 0.95)]
ok = n = 0


def ck(name, cond):
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name)


for name, v, atype, dang, want in FIX:
    a = jl.score(v, atype, dang)
    ck(f"score: {name}  ({a['weighted_score']} {a['verdict']})",
       a["weighted_score"] == want and a["verdict"] == ("pass" if want >= jl.PASS_LINE else "flag"))

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

# finalize(): the only place a final verdict is decided (YED-231). Pass needs nothing to fire.
base = dict(jl.score(V([.9, .9, .9, .9, .9]), "code", False), artifact=".claude/scripts/x.py", quote_check={})
ck("finalize: a clean pass stays pass, no reasons", jl.finalize(base) == {"final_verdict": "pass", "flag_reasons": []})
low = dict(base, verdict="flag", weighted_score=0.61)
ck("finalize: a score under the line flags", jl.finalize(low)["final_verdict"] == "flag")
ck("finalize: the privacy flag flags a strong score (no score cap needed)",
   jl.finalize(dict(base, privacy_layer_defect=True))["final_verdict"] == "flag")
ck("finalize: flat 1.0 flags as low-information", jl.finalize(dict(base, flat_ceiling=True))["final_verdict"] == "flag")
ck("finalize: >30% fabricated quotes flags", jl.finalize(dict(base, quote_check={"evidence_unverified": True}))["final_verdict"] == "flag")
g = jl.finalize(base, {"files": [{"path": ".claude/skills/x/SKILL.md"}, {"path": ".claude/scripts/spine_client.py"}]})
ck("finalize: a bundle touching the spine write path needs human review",
   g["final_verdict"] == "flag" and any("guarded_path:.claude/scripts/spine_client.py" in r for r in g["flag_reasons"]))
ck("guarded: named guard/filter/allowlist files match by name",
   jl.guarded_paths(["a/inbox-allowlist.md", "b/privacy_filter.py", "c/deny-list.txt", "d/notes.md"])
   == ["a/inbox-allowlist.md", "b/privacy_filter.py", "c/deny-list.txt"])
ck("guarded: .gitignore is a privacy filter", jl.guarded_paths([".gitignore"]) == [".gitignore"])
ck("guarded: ordinary files do not match", jl.guarded_paths([".claude/skills/role-radar/SKILL.md", ".claude/hooks/density-check.sh"]) == [])
ck("judge layer: judge files are recognised", all(jl.is_judge_layer(p) for p in (
   ".claude/evals/judge_lib.py", ".claude/skills/judge-build/SKILL.md", ".claude/evals/rubrics/build-quality-v6.md",
   ".claude/hooks/seat-log.py")))
ck("judge layer: neighbours in .claude/evals are not", not jl.is_judge_layer(".claude/evals/test_event_claim.py")
   and not jl.is_judge_layer(".claude/evals/logs/x.jsonl"))
p = subprocess.run(["python3", ".claude/evals/judge.py", "run", "--artifact", ".claude/evals/judge_lib.py",
                    "--artifact-type", "code"], capture_output=True, text=True)
ck("judge.py: the judge layer is refused as a target (never self-judged)", p.returncode == 2 and "never judged" in p.stderr)

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
