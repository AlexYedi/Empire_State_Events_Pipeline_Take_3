#!/usr/bin/env python3
"""test_null_baseline.py — the null-model contract (YED-212). Offline, free.

The rule this encodes: a metric a do-nothing policy scores just as well on is not a standard. "83%
Gemini-vs-Alex agreement" was arithmetically the always-pass baseline, and the >=80% gate sat BELOW it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calibration_stats import null_check, NULL_MARGIN, NULL_MIN_N
ok = n = 0
def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)

ck("THE historical case: 0.83 agreement vs a 0.83 always-pass baseline is UNVALIDATED",
   null_check(0.833, 0.833, 18)["status"] == "unvalidated")
ck("...and the old gate's 0.80 threshold sat BELOW that baseline (why it could never fire)", 0.80 < 0.833)
ck("beating the baseline by exactly the margin validates", null_check(0.93, 0.83, 18)["status"] == "validated")
ck("beating it by less than the margin does not", null_check(0.92, 0.83, 18)["status"] == "unvalidated")
ck("a genuinely discriminating seat validates", null_check(0.90, 0.50, 20)["status"] == "validated")
ck(f"n < {NULL_MIN_N} is 'insufficient', never 'validated'", null_check(1.0, 0.0, 5)["status"] == "insufficient")
ck("zero variance is unvalidated however good the constant looks",
   null_check(0.95, 0.10, 20, values=["pass"] * 20)["status"] == "unvalidated")
ck("...and it says WHY (constant output)", null_check(0.95, 0.1, 20, values=["pass"] * 20)["reason"] == "zero_variance")
ck("variance present -> judged on the margin, not the variance arm",
   null_check(0.95, 0.10, 20, values=["pass"] * 18 + ["flag"] * 2)["status"] == "validated")
ck("missing observed/baseline is insufficient, never validated", null_check(None, 0.5, 20)["status"] == "insufficient")
ck("the margin is reported for the record", null_check(0.95, 0.80, 20)["margin"] == 0.15)
ck("a perfect seat on an all-pass corpus is still unvalidated (no flags to catch)",
   null_check(1.0, 1.0, 30, values=["pass"] * 30)["status"] == "unvalidated")
print(f"{ok}/{n} null-baseline cases pass")
sys.exit(0 if ok == n else 1)
