#!/usr/bin/env python3
"""test_quorum_nseat.py: the N-seat merge decision table (YED-209). No network, no spend.

2026-09-20: four expectations here were WRONG and encoded the bug both independent seats flagged on the first
three-seat run — a missing seat or a bundle-hash mismatch was recorded as "pass pending ack". The spec's §2 table
says integrity problems end in `flag`, because we cannot show the seats scored the same artifact. Fixed below.
Run: python3 .claude/evals/test_quorum_nseat.py   (the 2-seat suite, test_quorum_scenarios.py, still covers quorum-merge.sh)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quorum_merge as qm

CFG = [{"id": "claude", "status": "voting", "independence_group": "anthropic"},
       {"id": "gemini", "status": "advisory", "independence_group": "google"},
       {"id": "openai", "status": "shadow", "independence_group": "openai"}]
H = "b" * 64


def row(verdict="pass", ws=0.9, flat=False, h=H, parity=True, unverified=False):
    s = 1.0 if flat else ws
    return {"verdict": verdict, "weighted_score": 1.0 if flat else ws, "bundle_sha256": h, "evidence_parity": parity,
            "criterion_scores": [{"id": c, "score": s} for c in "abcde"], "run_id": "r",
            "quote_check": {"evidence_unverified": unverified}}


def eff(**over):
    e = {"claude": "voting", "gemini": "advisory", "openai": "shadow"}; e.update(over); return e


ok = n = 0


def ck(name, rec, resolution, final, has=(), lacks=()):
    global ok, n
    n += 1
    good = rec["resolution"] == resolution and rec["final_verdict"] == final and \
        all(any(r.startswith(x) for r in rec["escalation_reasons"]) for x in has) and \
        not any(any(r.startswith(x) for r in rec["escalation_reasons"]) for x in lacks)
    ok += good
    print(("  ✓ " if good else "  ✗ ") + f"{name}  -> {rec['resolution']}/{rec['final_verdict']} {rec['escalation_reasons']}")


M = lambda rows, e=None, mode="interactive", cfg=CFG: qm.merge("x.md", rows, cfg, e or eff(), mode)
ck("clean: voting pass + advisory pass, close scores -> auto pass", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}), "auto", "pass")
ck("shadow FLAG is ignored", M({"claude": row(), "gemini": row(ws=0.88), "openai": row("flag", 0.3)}), "auto", "pass", lacks=("advisory_flag", "score_divergence"))
ck("shadow seat missing is recorded only", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}), "auto", "pass", lacks=("seat_missing",))
ck("advisory FLAG vs voting pass -> escalates, pass pending ack", M({"claude": row(), "gemini": row("flag", 0.6), "openai": None}), "escalated", "pass", has=("advisory_flag:gemini",))
ck("two advisory passes cannot rescue a voting FLAG", M({"claude": row("flag", 0.5), "gemini": row(ws=0.95), "openai": row(ws=0.95)}, eff(openai="advisory")), "auto", "flag")
ck("advisory seat missing -> seat_missing", M({"claude": row(), "gemini": None, "openai": None}), "escalated", "flag", has=("seat_missing:gemini",))
ck("differing bundle hashes -> evidence_mismatch", M({"claude": row(), "gemini": row(ws=0.88, h="c" * 64), "openai": None}), "escalated", "flag", has=("evidence_mismatch",))
ck("a seat with no bundle hash -> no_bundle_hash", M({"claude": row(), "gemini": row(ws=0.88, h=None), "openai": None}), "escalated", "flag", has=("no_bundle_hash:gemini",))
ck("no effective voting seat -> flag (interactive)", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}, eff(claude="advisory")), "escalated", "flag", has=("no_voting_seat",))
ck("no effective voting seat -> failsafe (autonomous)", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}, eff(claude="advisory"), "autonomous"), "failsafe_flag", "flag", has=("no_voting_seat",))
ck("flat ceiling on an advisory seat escalates", M({"claude": row(), "gemini": row(flat=True), "openai": None}), "escalated", "pass", has=("flat_ceiling:gemini",))
ck("flat ceiling on the VOTING seat escalates too", M({"claude": row(flat=True), "gemini": row(ws=0.95), "openai": None}), "escalated", "pass", has=("flat_ceiling:claude",))
ck("score divergence >= 0.15 escalates", M({"claude": row(ws=0.95), "gemini": row(ws=0.75), "openai": None}), "escalated", "pass", has=("score_divergence",))
ck("advisory without evidence parity escalates", M({"claude": row(), "gemini": row(ws=0.88, parity=False), "openai": None}), "escalated", "pass", has=("no_evidence_parity:gemini",))
ck("2-1 voting split, autonomous -> failsafe flag", M({"claude": row(), "gemini": row(), "openai": row("flag", 0.5)}, eff(gemini="voting", openai="voting"), "autonomous"), "failsafe_flag", "flag", has=("verdict_mismatch",))
ck("2-1 voting split, interactive -> escalated FLAG (never majority-resolved)", M({"claude": row(), "gemini": row(), "openai": row("flag", 0.5)}, eff(gemini="voting", openai="voting")), "escalated", "flag", has=("verdict_mismatch",))
ck("three independent voting seats all pass -> auto pass", M({"claude": row(), "gemini": row(ws=0.88), "openai": row(ws=0.92)}, eff(gemini="voting", openai="voting")), "auto", "pass")
SAME = [{"id": "claude", "status": "voting", "independence_group": "anthropic"}, {"id": "gemini", "status": "voting", "independence_group": "anthropic"}]
ck("two voting seats from ONE group are one opinion -> escalates", qm.merge("x.md", {"claude": row(), "gemini": row(ws=0.88)}, SAME, {"claude": "voting", "gemini": "voting"}), "escalated", "pass", has=("same_group_only",))
ck("fabricated quotes strip a seat's power to escalate", M({"claude": row(), "gemini": row("flag", 0.4, unverified=True), "openai": None}), "auto", "pass", lacks=("advisory_flag", "score_divergence"))
ck("an auto-demoted voting seat no longer decides", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}, eff(claude="advisory")), "escalated", "flag", has=("no_voting_seat",))
ck("budget/cap exit leaves the seat missing; shadow -> no effect", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}), "auto", "pass")
ck("…but a missing ADVISORY openai seat escalates", M({"claude": row(), "gemini": row(ws=0.88), "openai": None}, eff(openai="advisory")), "escalated", "flag", has=("seat_missing:openai",))

# --- rules added 2026-09-20 after the first three-seat run found them missing -------------------------------
ck("integrity reason beats an agreed PASS: final is flag, never pass-pending-ack",
   M({"claude": row(), "gemini": None, "openai": None}), "escalated", "flag", has=("seat_missing:gemini",))
ck("a unanimous FLAG with an integrity reason does NOT auto-resolve",
   M({"claude": row("flag", 0.4), "gemini": None, "openai": None}), "escalated", "flag", has=("seat_missing:gemini",))
ck("a unanimous FLAG with no integrity reason still auto-resolves",
   M({"claude": row("flag", 0.4), "gemini": row("flag", 0.45), "openai": None}), "auto", "flag")
ck("a malformed seat row is seat_invalid, not a crash",
   M({"claude": row(), "gemini": {"verdict": "pass", "weighted_score": None, "bundle_sha256": H}, "openai": None}),
   "escalated", "flag", has=("seat_invalid:gemini",))
ck("a row missing weighted_score entirely is seat_invalid",
   M({"claude": row(), "gemini": {"verdict": "pass", "bundle_sha256": H}, "openai": None}),
   "escalated", "flag", has=("seat_invalid:gemini",))
ck("fabricated quotes cost the VOTING seat its vote, not just its escalation",
   M({"claude": row(unverified=True), "gemini": row(ws=0.9), "openai": None}), "escalated", "flag", has=("no_voting_seat",))
SAMEPROV = [{"id": "a", "status": "voting", "provider": "openai"}, {"id": "b", "status": "voting", "provider": "openai"}]
ck("two voting seats from one PROVIDER (no group set) are one opinion",
   qm.merge("x.md", {"a": row(), "b": row(ws=0.88)}, SAMEPROV, {"a": "voting", "b": "voting"}),
   "escalated", "pass", has=("same_group_only",))
print(f"{ok}/{n} n-seat scenarios pass")
sys.exit(0 if ok == n else 1)
