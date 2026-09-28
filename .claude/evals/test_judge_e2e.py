#!/usr/bin/env python3
"""test_judge_e2e.py: judge.py run -> --resume -> ack on real multi-file ranges, offline (YED-231 acceptance).

No model is called: a canned reviewer verdict stands in for the Sonnet subagent. Logs and state go to a temp dir.
Checks: a multi-file PR ends in pass/flag without escalating on bundle mechanics (a quote from file 2 verifies);
one command runs the whole judge; Alex is asked only on flag; a guarded path flags whatever the score; acks are
append-only and one per run. Run from the repo root: python3 .claude/evals/test_judge_e2e.py
"""
import json, os, subprocess, sys, tempfile
ok = n = 0


def ck(name, cond, detail=""):
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"   {detail}" if detail and not cond else ""))


tmp = tempfile.mkdtemp(prefix="judge-e2e-")
env = dict(os.environ, JUDGE_LOG_DIR=os.path.join(tmp, "logs"), JUDGE_STATE_DIR=os.path.join(tmp, "state"),
           CLAUDE_PROJECT_DIR=os.getcwd())
J = lambda *a: subprocess.run(["python3", ".claude/evals/judge.py", *a], capture_output=True, text=True, env=env)


def verdict(quote_from: str | None, score: float = 0.88) -> str:
    v = {"checks_performed": ["read every file"], "criterion_scores": [
        {"id": c, "score": score, "reasoning": "r"} for c in
        ("correctness", "completeness", "convention_adherence", "anti_pattern_avoidance", "diagnostics")],
        "defects": [], "cap_flags": {}}
    if quote_from:
        v["defects"] = [{"file": "x", "line": 1, "quote": quote_from, "criterion": "diagnostics", "severity": "minor",
                         "description": "nit"}]
    p = os.path.join(tmp, f"v{len(os.listdir(tmp))}.json")
    json.dump(v, open(p, "w"))
    return p


if subprocess.run(["git", "cat-file", "-e", "42602e4^{commit}"], capture_output=True).returncode:
    print("  ✗ fixture ranges not reachable — run `git fetch origin` first"); sys.exit(1)

# 1. a multi-file bundle with NO guarded path (two hooks, --files)
r = J("run", "--files", ".claude/hooks/check-refs.sh", ".claude/hooks/density-check.sh", "--artifact-type", "hook",
      "--label", "e2e-files")
ck("run --files: bundle built, reviewer brief written, one NEXT instruction", r.returncode == 0 and "NEXT" in r.stdout, r.stderr)
brief = os.path.join(tmp, "state", "e2e-files", "brief.txt")
ck("the brief carries the output contract", os.path.isfile(brief) and "===== OUTPUT (reviewer)" in open(brief).read())
second = next(l for l in open(".claude/hooks/density-check.sh").read().splitlines()[3:] if len(l.strip()) > 25)
r = J("run", "--resume", "e2e-files", "--verdict", verdict(second.strip()))
ck("resume: a quote from file 2 verifies and a clean multi-file run PASSES (no escalation on bundle mechanics)",
   r.returncode == 0 and "PASS" in r.stdout and "ASK ALEX" not in r.stdout, r.stdout + r.stderr)

# 2. a range that touches the spine write path: FLAG for human review even at a high score
r = J("run", "--range", "c607c08..42602e4", "--artifact-type", "hook", "--label", "e2e-range")
ck("run --range: PR #139 builds and warns about the guarded path up front", r.returncode == 0 and "guarded path" in r.stdout,
   r.stdout + r.stderr)
r = J("run", "--resume", "e2e-range", "--verdict", verdict(None, 0.95))
ck("resume: guarded path flags whatever the score, and Alex is asked", "FLAG" in r.stdout and "ASK ALEX" in r.stdout
   and "guarded_path:.claude/scripts/spine_client.py" in r.stdout, r.stdout + r.stderr)

# 3. ack: append-only, one per run
r = J("ack", "--run", "e2e-range", "agree", "guarded path reviewed")
ck("ack: written", r.returncode == 0 and "acked e2e-range" in r.stdout, r.stderr)
r = J("ack", "--run", "e2e-range", "disagree")
ck("ack: a second ack on the same run is refused", r.returncode == 2 and "already acked" in r.stderr)
rows = [json.loads(l) for f in os.listdir(os.path.join(tmp, "logs")) for l in open(os.path.join(tmp, "logs", f))]
ck("logs: one reviewer row per run + one ack row, nothing rewritten",
   sorted(r.get("record_type") or "run" for r in rows) == ["ack", "run", "run"])
ck("logs: the reviewer row carries final_verdict + flag_reasons and no seat status",
   all("final_verdict" in r and "seat_status" not in r for r in rows if not r.get("record_type")))

# 4. a malformed verdict is rejected and nothing is logged
J("run", "--files", ".claude/hooks/density-check.sh", "--artifact-type", "hook", "--label", "e2e-bad")
bad = os.path.join(tmp, "bad.json"); json.dump({"criterion_scores": []}, open(bad, "w"))
r = J("run", "--resume", "e2e-bad", "--verdict", bad)
ck("resume: a malformed verdict is rejected (rc 1), nothing logged", r.returncode == 1 and
   not any("e2e-bad" in f for f in os.listdir(os.path.join(tmp, "logs"))))

print(f"{ok}/{n} judge end-to-end cases pass")
sys.exit(0 if ok == n else 1)
