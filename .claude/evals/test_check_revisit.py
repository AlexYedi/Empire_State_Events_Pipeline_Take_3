#!/usr/bin/env python3
"""test_check_revisit.py: calibration_stats.check() + the judge.py ack path (YED-231 §4.3/§4.5). Offline, free.

check() REPORTS: it names the moment Alex should revisit the voting seat and never edits seats.json.
ack is the only alex_ack writer: append-only `quorum_ack` rows, one per run, folded in by calibration_stats.load().
Run: python3 .claude/evals/test_check_revisit.py
"""
import argparse, hashlib, io, json, os, sys, tempfile, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibration_stats as cal
import judge

ok = n = 0


def ck(name, cond, detail=""):
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"   {detail}" if detail and not cond else ""))


SEATS = {"seats": [{"id": "claude", "seat_name": "claude:sonnet", "role": "voting", "since": "2026-07-17"},
                   {"id": "openai", "seat_name": "openai", "role": "shadow", "since": "2026-09-19"}],
         "revisit": {"since": "2026-09-28", "min_new_acks": 5, "kappa_floor": 0.40, "recall_floor": 0.50, "n_min": 15,
                     "candidate": {"seat": "openai", "model": "gpt-5.4-mini"}}}
# (seat verdict, Alex's truth). LOW: po .60, pe .52 -> kappa .17, recall .50 (the kappa arm fires).
LOW = [("pass", "pass")] * 8 + [("pass", "flag")] * 4 + [("flag", "pass")] * 4 + [("flag", "flag")] * 4
# GOOD: kappa .80, recall .89
GOOD = [("pass", "pass")] * 10 + [("pass", "flag")] + [("flag", "pass")] + [("flag", "flag")] * 8


def rows_for(pairs, n_new):
    """20 voter runs: the last `n_new` dated after revisit.since. Each carries its own ack (agree = truth == verdict)."""
    out = []
    for i, (v, t) in enumerate(pairs):
        new = i >= len(pairs) - n_new
        ts = f"2026-09-{29 if new else 20}T{i:02d}:00:00Z"
        out.append({"run_id": f"s{i}", "timestamp": ts, "artifact": f"a{i}.md",
                    "artifact_sha256": hashlib.sha256(f"a{i}".encode()).hexdigest(), "judge_model": "claude:sonnet",
                    "calibration_set": "prospective", "evidence_parity": True, "verdict": v,
                    "criterion_scores": [{"id": c, "score": 0.8} for c in "abcde"],
                    "alex_ack": "agree" if v == t else "disagree"})
    return out


with tempfile.TemporaryDirectory() as d:
    sf = os.path.join(d, "seats.json")
    json.dump(SEATS, open(sf, "w"))
    before = open(sf, "rb").read()
    c4 = cal.check(rows_for(LOW, 4), seats_file=sf)
    c5 = cal.check(rows_for(LOW, 5), seats_file=sf)
    g5 = cal.check(rows_for(GOOD, 5), seats_file=sf)
    ck("fixture: LOW measures kappa < 0.40 on n = 20", c5["kappa"] is not None and c5["kappa"] < 0.40 and c5["n"] == 20, str(c5["kappa"]))
    ck("4 new acks, low kappa -> not_due (the window needs 5 fresh labels)", c4["status"] == "not_due" and c4["new_acks"] == 4, str(c4))
    ck("5 new acks, low kappa -> revisit_due", c5["status"] == "revisit_due" and c5["new_acks"] == 5, str(c5))
    ck("…and the banner names the numbers and the candidate", "REVISIT" in cal.banner(c5) and "gpt-5.4-mini" in cal.banner(c5))
    ck("5 new acks, kappa 0.80 / recall 0.89 -> not_due", g5["status"] == "not_due" and g5["kappa"] >= 0.6 and g5["flag_recall"] >= 0.7, str(g5))
    ck("…and no banner", cal.banner(g5) == "")
    ck("recall arm alone fires: recall < 0.50 with fresh acks",
       cal.check(rows_for([("pass", "pass")] * 12 + [("pass", "flag")] * 5 + [("flag", "flag")] * 3, 5), seats_file=sf)["status"] == "revisit_due")
    ck("check() never writes seats.json", open(sf, "rb").read() == before)
    esc = rows_for(LOW, 5) + [{"record_type": "quorum", "resolution": "escalated",
                               "seats": [{"id": "claude", "role": "voting", "run_id": "s0"}, {"id": "claude", "run_id": "s1"}]}]
    ck("n_from_escalation counts scored runs whose quorum escalated", cal.check(esc, seats_file=sf)["n_from_escalation"] == 2)
    json.dump({**SEATS, "seats": [dict(SEATS["seats"][1])]}, open(sf, "w"))
    ck("no voting seat -> reported, not crashed", cal.check([], seats_file=sf)["status"] == "no_voting_seat")

# ---- judge.py ack: append-only, one per run, folded by load() --------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    judge.LOGS = d
    f = os.path.join(d, "2026-09-28-x-quorum-j1.jsonl")
    q = {"record_type": "quorum", "run_id": "quorum-j1", "artifact": "range:aaaaaaa..bbbbbbb", "artifact_sha256": "c" * 64,
         "final_verdict": "pass", "resolution": "auto", "alex_ack": None,
         "seats": [{"id": "claude", "role": "voting", "verdict": "pass"}, {"id": "openai", "role": "shadow", "verdict": "flag", "weighted_score": 0.6}]}
    open(f, "w").write(json.dumps(q) + "\n")
    before = open(f).read()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = judge.ack(argparse.Namespace(run=["quorum-j1"], verdict="agree", note="fine"))
    lines = open(f).read().splitlines()
    ck("ack: exit 0 and the quorum row is untouched (append-only)", rc == 0 and open(f).read().startswith(before) and len(lines) == 2)
    a = json.loads(lines[1])
    ck("ack: a quorum_ack row with a full UTC timestamp", a["record_type"] == "quorum_ack" and a["alex_ack"] == "agree"
       and len(a["alex_ack_at"]) == 20 and a["alex_ack_at"].endswith("Z"))
    ck("ack: the shadow verdict is revealed only after the ack", "openai flag (0.6)" in buf.getvalue())
    folded = [r for r in cal.load(d) if r.get("record_type") == "quorum"][0]
    ck("load() folds the ack into its quorum row", folded["alex_ack"] == "agree" and folded["alex_ack_note"] == "fine")
    with contextlib.redirect_stderr(io.StringIO()):
        rc2 = judge.ack(argparse.Namespace(run=["quorum-j1"], verdict="disagree", note=""))
    ck("ack: a second ack on the same run is refused", rc2 == 2 and len(open(f).read().splitlines()) == 2)
    with contextlib.redirect_stderr(io.StringIO()):
        rc3 = judge.ack(argparse.Namespace(run=["quorum-nope"], verdict="agree", note=""))
    ck("ack: an unknown run id is refused", rc3 == 2)
    ck("ack rows are not seat rows (no verdict, no seat)", cal.seat_of(a) is None)

print(f"{ok}/{n} revisit/ack cases pass")
sys.exit(0 if ok == n else 1)
