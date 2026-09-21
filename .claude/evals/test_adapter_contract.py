#!/usr/bin/env python3
"""test_adapter_contract.py — every judge adapter speaks the same CLI (rigor-review 2026-09-21).

WHY THIS EXISTS. Four times in two days a metric said "the model is bad" and the harness was at fault. The
fourth: `controls.py` started passing `--artifact-blob`, only `openai_judge.py` knew it, and EVERY Gemini
control run died with "unknown arg" — which the canary then recorded as the Gemini SEAT failing. A seat was
one run away from being auto-demoted for a flag it had never been taught.

The shape is always the same: a change lands in one adapter, the others silently break or get blamed. This
test makes adapters prove they share a contract, offline and free: every invocation passes --dry-run, which both adapters now honour by stopping before the
network call. (The first version of this test used --print-only and cost $0.11 before I killed it — on the
Gemini adapter --print-only still calls the API and only skips the log write. Hence --dry-run is itself now
part of the contract.)

Run: python3 .claude/evals/test_adapter_contract.py
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile

# Flags every seat adapter must ACCEPT (parse without "unknown arg"). Add a flag here the moment any caller
# — controls.py, run-canaries.sh, the judge-build skill — starts passing it to more than one adapter.
REQUIRED = ["--artifact", "--artifact-type", "--calibration-set", "--context", "--spec-file",
            "--model", "--rubric", "--system", "--label", "--print-only", "--bundle", "--artifact-blob", "--dry-run"]
UNKNOWN_FLAG = "--definitely-not-a-real-flag"
ok = n = 0


def ck(name: str, cond: bool, detail: str = "") -> None:
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"   {detail}" if detail and not cond else ""))


def run(runner: str, args: list[str]) -> subprocess.CompletedProcess:
    cmd = (["bash", runner] if runner.endswith(".sh") else ["python3", runner]) + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def main() -> int:
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    seats = [s for s in json.load(open(".claude/evals/seats.json"))["seats"] if s.get("runner", "").endswith((".sh", ".py"))]
    ck("at least two adapter-backed seats exist to compare", len(seats) >= 2)
    art = ".claude/evals/judge_lib.py"          # tracked, in-repo, safe: the guards will pass on it

    for s in seats:
        r = s["runner"]
        ck(f"{s['id']}: runner exists and is executable", os.path.isfile(r) and os.access(r, os.X_OK), r)
        if not os.path.isfile(r):
            continue
        # 1. every required flag parses. --print-only stops before the log write; we only care that the
        #    adapter does not reject the FLAG. A guard/budget/API failure is fine and expected here.
        for flag in REQUIRED:
            val = {"--artifact": art, "--artifact-type": "code", "--calibration-set": "control",
                   "--context": "x", "--spec-file": art, "--model": "m", "--rubric": ".claude/evals/rubrics/build-quality-v5.md",
                   "--system": ".claude/evals/prompts/judge-system-v2.md", "--label": "contract-test",
                   "--bundle": "", "--artifact-blob": "0" * 40}.get(flag)
            args = ["--artifact", art, "--dry-run"] + ([flag] if val is None else [flag, val])
            p = run(r, args)
            blob = (p.stdout + p.stderr).lower()
            ck(f"{s['id']}: accepts {flag}", "unknown arg" not in blob and "unrecognized arguments" not in blob,
               (p.stdout + p.stderr).strip().splitlines()[0] if (p.stdout + p.stderr).strip() else "")
        # 2. an UNKNOWN flag must fail loudly, not be ignored — silence is how a caller's typo becomes a
        #    seat's "failure".
        p = run(r, ["--artifact", art, UNKNOWN_FLAG, "x", "--dry-run"])
        blob = (p.stdout + p.stderr).lower()
        ck(f"{s['id']}: rejects an unknown flag loudly", p.returncode != 0 or "unknown arg" in blob or "unrecognized" in blob,
           f"rc={p.returncode}")
        # 3. the provenance guard is enforced identically: a bogus blob claim must never be sent
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, dir=".claude/evals") as f:
            f.write("not a real control\n"); tmp = f.name
        try:
            p = run(r, ["--artifact", tmp, "--artifact-blob", "0" * 40, "--dry-run"])
            blob = (p.stdout + p.stderr).lower()
            ck(f"{s['id']}: refuses a forged --artifact-blob claim", "privacy guard" in blob or "does not match" in blob,
               (p.stdout + p.stderr).strip()[:90])
        finally:
            os.unlink(tmp)

    print(f"{ok}/{n} adapter-contract cases pass")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
