"""Behaviour tests for .claude/hooks/ab-reminder.sh — it must fire only while genuinely due.

A reminder that cannot turn itself off is worse than no reminder: it trains you to ignore the block.
These five cases pin that contract. Fixtures are temp eval-log files, removed at the end.
Run: python3 .claude/hooks/test_ab_reminder.py
"""
import json, os, pathlib, shutil, subprocess, tempfile

REPO = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parents[2])

# The hook is driven ENTIRELY by what exists under .claude/, so the tests run against a scratch
# project dir rather than the repo. Fixed 2026-09-21: they previously ran in place and deleted only
# their own fixture logs, so the moment event 1 was genuinely scored and its log committed, the
# "nothing scored" case became unreachable and the suite failed — a behaviour test breaking because
# the behaviour finally happened. Isolation also means a run can never delete a real scorecard.
W = pathlib.Path(tempfile.mkdtemp(prefix="ab-reminder-test-"))
LOGS = W / ".claude/evals/logs"
LOGS.mkdir(parents=True)
(W / ".claude/hooks").mkdir(parents=True)
(W / ".claude/artifacts/ab-yed172").mkdir(parents=True)
shutil.copy(REPO / ".claude/hooks/ab-reminder.sh", W / ".claude/hooks/ab-reminder.sh")
for f in ("run-card-2026-09-21.md", "seed-2026-09-21.json", "seed-2026-09-23.json"):
    src = REPO / ".claude/artifacts/ab-yed172" / f
    if src.exists():
        shutil.copy(src, W / ".claude/artifacts/ab-yed172" / f)
# A SYNTHETIC active marker, not a copy of the live one (fixed 2026-09-24). Copying the real file coupled the
# suite to whether a freeze happened to be active that day: the moment YED-172's freeze was lifted, the
# "echo reads the marker" case failed despite the hook being correct. The fixture is what's under test here —
# that the hook quotes the file rather than restating the rule — so the fixture should be deterministic.
(W / ".claude/references").mkdir(parents=True, exist_ok=True)
(W / ".claude/references/graph-freeze.json").write_text(json.dumps({
    "active": True, "issue": "TEST-FIXTURE", "reason": "synthetic freeze for the reminder-hook contract test",
    "lifts_when": "never — this is a fixture",
}))

E1 = LOGS / "2026-09-24-ab-yed172-apollo-graphos.jsonl"
E2 = LOGS / "2026-09-24-ab-yed172-ai-builders.jsonl"


def run(day):
    r = subprocess.run(["bash", ".claude/hooks/ab-reminder.sh"], cwd=W, capture_output=True, text=True,
                       env={**os.environ, "AB_TODAY": day})
    return r.stdout.strip()


CASES = []
for f in (E1, E2):
    f.unlink(missing_ok=True)
CASES.append(("before the window (9/19)", run("2026-09-19") == "", "silent"))
# Assertions are STRUCTURAL, not name-based (fixed 2026-09-24). They previously asserted on the literal event
# titles ("Show and Tell", "Clay"); when the A/B's events were replaced mid-experiment the assertions failed
# even though the hook behaved correctly. Counting the rendered bullet lines tests the contract — how many
# events are still pending — without coupling the suite to which events those happen to be.
out = run("2026-09-20")
CASES.append(("in window, nothing scored",
              "both events pending" in out and out.count("\n- ") == 2, "both listed"))
E1.write_text('{"fixture":"event 1 scored"}\n')
out = run("2026-09-22")
CASES.append(("event 1 scored", "1 event pending" in out and out.count("\n- ") == 1, "only event 2"))
E2.write_text('{"fixture":"event 2 scored"}\n')
CASES.append(("both scored", run("2026-09-23") == "", "silent, permanently"))
for f in (E1, E2):
    f.unlink(missing_ok=True)
CASES.append(("after hard stop (9/27), nothing scored", run("2026-09-27") == "", "silent (expires itself)"))

# The freeze echo must come from graph-freeze.json, never from a restated copy in the hook (YED-213).
out = run("2026-09-22")
CASES.append(("freeze echo reads the committed marker",
              ("Graph-write freeze ACTIVE" in out and "graph-freeze.json" in out)
              if (W / ".claude/references/graph-freeze.json").exists() else True,
              "quotes the file, not a hardcoded sentence"))
(W / ".claude/references/graph-freeze.json").unlink(missing_ok=True)
CASES.append(("no marker → says writes are open", "No graph-write freeze active" in run("2026-09-22"),
              "absence of a freeze is stated, not silent"))

shutil.rmtree(W, ignore_errors=True)

ok = 0
for name, passed, expect in CASES:
    ok += passed
    print(f"{'PASS' if passed else 'FAIL'}  {name} → {expect}")
print(f"{ok}/{len(CASES)} pass")
raise SystemExit(0 if ok == len(CASES) else 1)
