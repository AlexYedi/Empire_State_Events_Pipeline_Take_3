"""Behaviour tests for .claude/hooks/ab-reminder.sh — it must fire only while genuinely due.

A reminder that cannot turn itself off is worse than no reminder: it trains you to ignore the block.
These five cases pin that contract. Fixtures are temp eval-log files, removed at the end.
Run: python3 .claude/hooks/test_ab_reminder.py
"""
import os, pathlib, subprocess

W = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parents[2])
LOGS = W / ".claude/evals/logs"
E1 = LOGS / "2026-09-21-ab-yed172-show-and-tell.jsonl"   # temp fixtures, removed at the end
E2 = LOGS / "2026-09-23-ab-yed172-clay.jsonl"


def run(day):
    r = subprocess.run(["bash", ".claude/hooks/ab-reminder.sh"], cwd=W, capture_output=True, text=True,
                       env={**os.environ, "AB_TODAY": day})
    return r.stdout.strip()


CASES = []
for f in (E1, E2):
    f.unlink(missing_ok=True)
CASES.append(("before the window (9/19)", run("2026-09-19") == "", "silent"))
out = run("2026-09-20")
CASES.append(("in window, nothing scored", "both events pending" in out and "Show and Tell" in out and "Clay" in out, "both listed"))
E1.write_text('{"fixture":"event 1 scored"}\n')
out = run("2026-09-22")
CASES.append(("event 1 scored", "1 event pending" in out and "Show and Tell" not in out and "Clay" in out, "only event 2"))
E2.write_text('{"fixture":"event 2 scored"}\n')
CASES.append(("both scored", run("2026-09-23") == "", "silent, permanently"))
for f in (E1, E2):
    f.unlink(missing_ok=True)
CASES.append(("after hard stop (9/27), nothing scored", run("2026-09-27") == "", "silent (expires itself)"))

ok = 0
for name, passed, expect in CASES:
    ok += passed
    print(f"{'PASS' if passed else 'FAIL'}  {name} → {expect}")
print(f"{ok}/{len(CASES)} pass")
raise SystemExit(0 if ok == len(CASES) else 1)
