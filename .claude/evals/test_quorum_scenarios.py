"""Offline scenario tests for quorum-merge.sh (YED-206). No network, no API cost; --print-only writes nothing.

Covers the 2026-09-19 rules: escalate on verdict_mismatch / score_divergence (>=0.15) / flat_ceiling:<seat> /
gemini_no_evidence_parity, and the harness recompute of the CLAUDE seat's composite (round 3).
Run: python3 .claude/evals/test_quorum_scenarios.py
"""
import json, os, pathlib, subprocess

W = os.environ.get("CLAUDE_PROJECT_DIR") or str(pathlib.Path(__file__).resolve().parents[2])
FLAT = [{"id": i, "score": 1} for i in ("correctness", "completeness", "convention_adherence", "anti_pattern_avoidance", "diagnostics")]
CASES = [
    ("1. today's PR81 case: Sonnet 0.87, Gemini flat 1.0", "interactive",
     {"verdict": "pass", "weighted_score": 0.87, "criteria": {"correctness": .85, "completeness": .85, "convention_adherence": .95, "anti_pattern_avoidance": .9, "diagnostics": .75}},
     {"verdict": "pass", "weighted_score": 1.0, "criterion_scores": FLAT, "evidence_parity": True}, "escalated"),
    ("2. genuine agreement 0.86 vs 0.82", "interactive",
     {"verdict": "pass", "weighted_score": 0.86}, {"verdict": "pass", "weighted_score": 0.82, "flat_ceiling": False, "evidence_parity": True}, "auto"),
    ("3. same verdict, gap 0.95 vs 0.72", "interactive",
     {"verdict": "pass", "weighted_score": 0.95}, {"verdict": "pass", "weighted_score": 0.72, "evidence_parity": True}, "escalated"),
    ("4. autonomous, Gemini without spec", "autonomous",
     {"verdict": "pass", "weighted_score": 0.8}, {"verdict": "pass", "weighted_score": 0.8, "evidence_parity": False}, "failsafe_flag"),
    # round 3: the harness recomputes the CLAUDE seat too. Self-reported 0.95 is wrong (real: .8*.3+.9*.2+.9*.2+.9*.2+.7*.1=0.85);
    # with spec_drift set, correctness caps to 0.70 -> 0.21+0.18+0.18+0.18+0.07 = 0.82.
    ("6. claude seat recomputed (self-reported 0.95, spec_drift cap)", "interactive",
     {"verdict": "pass", "weighted_score": 0.95,
      "criterion_scores": [{"id": "correctness", "score": 0.8}, {"id": "completeness", "score": 0.9},
                           {"id": "convention_adherence", "score": 0.9}, {"id": "anti_pattern_avoidance", "score": 0.9},
                           {"id": "diagnostics", "score": 0.7}],
      "cap_flags": {"spec_drift": True, "confidence_honesty_violation": False, "command_skeleton_absent": False, "density_padding": False}},
     {"verdict": "pass", "weighted_score": 0.80, "evidence_parity": True}, "auto"),
    ("5. verdict mismatch (old behaviour kept)", "interactive",
     {"verdict": "flag", "weighted_score": 0.65}, {"verdict": "pass", "weighted_score": 0.74, "evidence_parity": True}, "escalated"),
]
ok = 0
for name, mode, cv, gv, want in CASES:
    r = subprocess.run(["bash", ".claude/hooks/quorum-merge.sh", "--artifact", ".claude/scripts/substrate.py", "--mode", mode,
                        "--print-only", "--claude-verdict", json.dumps(cv), "--gemini-verdict", json.dumps(gv)],
                       cwd=W, capture_output=True, text=True)
    out = r.stdout + r.stderr
    got = next((w for w in ("failsafe_flag", "escalated", "auto") if f"->  {w}" in out), "?")
    ok += got == want
    print(f"{'PASS' if got == want else 'FAIL'}  {name}: want {want}, got {got}")
    for line in out.splitlines()[1:]:
        print("      " + line.strip())
print(f"{ok}/{len(CASES)} scenarios pass")
raise SystemExit(0 if ok == len(CASES) else 1)
