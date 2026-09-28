#!/usr/bin/env python3
"""test_quorum_nseat.py: the merge decision table (YED-209; right-sized by YED-231). No network, no spend.

Roles (seats.json): claude voting · openai shadow · gemini off. The voter's verdict is the verdict; a shadow can only
ADD an escalation (verdict mismatch, score divergence, a quote-verified `major` on a pass) and only if its own quotes
verified; integrity problems end in `flag`. The advisory tier, independence blocs and canaries were retired (§3).
Run: python3 .claude/evals/test_quorum_nseat.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quorum_merge as qm

CFG = [{"id": "claude", "role": "voting"}, {"id": "openai", "role": "shadow"}, {"id": "gemini", "role": "off"}]
H = "b" * 64


def row(verdict="pass", ws=0.9, flat=False, h=H, parity=True, unverified=False, majors=0, major_verified=True):
    s = 1.0 if flat else ws
    defects = [{"severity": "major", "quote": "q"} for _ in range(majors)] + [{"severity": "minor", "quote": "q"}]
    return {"verdict": verdict, "weighted_score": 1.0 if flat else ws, "bundle_sha256": h, "evidence_parity": parity,
            "criterion_scores": [{"id": c, "score": s} for c in "abcde"], "run_id": "r", "defects": defects,
            "quote_check": {"evidence_unverified": unverified,
                            "matched_in": [("f.py" if major_verified else None)] * majors + ["f.py"]}}


ok = n = 0


def ck(name, rec, resolution, final, has=(), lacks=()):
    global ok, n
    n += 1
    good = rec["resolution"] == resolution and rec["final_verdict"] == final and \
        all(any(r.startswith(x) for r in rec["escalation_reasons"]) for x in has) and \
        not any(any(r.startswith(x) for r in rec["escalation_reasons"]) for x in lacks)
    ok += good
    print(("  ✓ " if good else "  ✗ ") + f"{name}  -> {rec['resolution']}/{rec['final_verdict']} {rec['escalation_reasons']}")


M = lambda rows, mode="interactive", cfg=CFG: qm.merge("x.md", rows, cfg, mode)
V, S = "claude", "openai"
# --- the core table ---------------------------------------------------------------------------------------------
ck("clean: voter pass + shadow pass, close scores -> auto pass", M({V: row(), S: row(ws=0.88)}), "auto", "pass")
ck("voter pass, shadow missing -> auto pass (a shadow is never integrity)", M({V: row(), S: None}), "auto", "pass", lacks=("seat_missing",))
ck("voter FLAG -> auto flag, no prompt", M({V: row("flag", 0.5), S: row(ws=0.9)}), "auto", "flag")
ck("voter FLAG, autonomous -> auto flag too", M({V: row("flag", 0.5), S: row(ws=0.9)}, "autonomous"), "auto", "flag")
ck("shadow verdict mismatch on a voter pass -> escalated/pass", M({V: row(), S: row("flag", 0.85)}), "escalated", "pass", has=("verdict_mismatch:openai",))
ck("…autonomous -> failsafe flag", M({V: row(), S: row("flag", 0.85)}, "autonomous"), "failsafe_flag", "flag", has=("verdict_mismatch:openai",))
ck("score divergence >= 0.15 vs a verified shadow -> escalated/pass", M({V: row(ws=0.95), S: row(ws=0.78)}), "escalated", "pass", has=("score_divergence",))
ck("…autonomous -> failsafe flag", M({V: row(ws=0.95), S: row(ws=0.78)}, "autonomous"), "failsafe_flag", "flag", has=("score_divergence",))
ck("divergence just under 0.15 -> auto pass", M({V: row(ws=0.90), S: row(ws=0.76)}), "auto", "pass", lacks=("score_divergence",))
# --- shadow_major_defect ----------------------------------------------------------------------------------------
ck("shadow `major` with a verified quote on a voter pass -> escalated/pass", M({V: row(), S: row(ws=0.88, majors=1)}), "escalated", "pass", has=("shadow_major_defect:openai",))
ck("…autonomous -> failsafe flag", M({V: row(), S: row(ws=0.88, majors=1)}, "autonomous"), "failsafe_flag", "flag", has=("shadow_major_defect:openai",))
ck("same, but the shadow is evidence_unverified -> auto/pass", M({V: row(), S: row(ws=0.88, majors=1, unverified=True)}), "auto", "pass", lacks=("shadow_major_defect", "verdict_mismatch", "score_divergence"))
ck("a major whose OWN quote failed does not escalate", M({V: row(), S: row(ws=0.88, majors=1, major_verified=False)}), "auto", "pass", lacks=("shadow_major_defect",))
legacy = row(ws=0.88, majors=1); legacy["quote_check"].pop("matched_in")
ck("a pre-YED-231 row (no matched_in) cannot raise shadow_major_defect", M({V: row(), S: legacy}), "auto", "pass", lacks=("shadow_major_defect",))
ck("shadow major on a voter FLAG -> still auto flag", M({V: row("flag", 0.5), S: row(ws=0.55, majors=1)}), "auto", "flag")
ck("an unverified shadow cannot escalate by mismatch or divergence either", M({V: row(), S: row("flag", 0.3, unverified=True)}), "auto", "pass", lacks=("verdict_mismatch", "score_divergence"))
# --- integrity: always flag -------------------------------------------------------------------------------------
ck("voter unverified -> escalated/flag (no_voting_seat)", M({V: row(unverified=True), S: row(ws=0.9)}), "escalated", "flag", has=("no_voting_seat",))
ck("voter unverified, autonomous -> failsafe flag", M({V: row(unverified=True), S: row(ws=0.9)}, "autonomous"), "failsafe_flag", "flag", has=("no_voting_seat",))
ck("voter missing -> seat_missing + no_voting_seat -> flag", M({V: None, S: row()}), "escalated", "flag", has=("seat_missing:claude", "no_voting_seat"))
ck("voter missing, autonomous -> failsafe flag", M({V: None, S: row()}, "autonomous"), "failsafe_flag", "flag", has=("seat_missing:claude",))
ck("a unanimous-looking FLAG with an integrity reason does NOT auto-resolve", M({V: row("flag", 0.4), S: row("flag", 0.4, h="c" * 64)}), "escalated", "flag", has=("evidence_mismatch",))
ck("differing bundle hashes -> evidence_mismatch -> flag", M({V: row(), S: row(ws=0.88, h="c" * 64)}), "escalated", "flag", has=("evidence_mismatch",))
ck("a seat with no bundle hash -> no_bundle_hash -> flag", M({V: row(h=None), S: row(ws=0.88)}), "escalated", "flag", has=("no_bundle_hash:claude",))
ck("a malformed voter row is seat_invalid, not a crash", M({V: {"verdict": "pass", "weighted_score": None, "bundle_sha256": H}, S: row()}), "escalated", "flag", has=("seat_invalid:claude",))
ck("a voter row missing weighted_score entirely is seat_invalid", M({V: {"verdict": "pass", "bundle_sha256": H}, S: None}), "escalated", "flag", has=("seat_invalid:claude",))
JUNK = {"verdict": "pass", "weighted_score": 0.9, "bundle_sha256": H, "criterion_scores": ["not", "a", "dict", "x", "y"]}
ck("junk criterion_scores is seat_invalid, not an AttributeError", M({V: JUNK, S: None}), "escalated", "flag", has=("seat_invalid:claude",))
ck("junk quote_check is seat_invalid too", M({V: {"verdict": "pass", "weighted_score": 0.9, "bundle_sha256": H, "quote_check": "nope"}, S: None}), "escalated", "flag", has=("seat_invalid:claude",))
ck("a non-dict voter row is seat_invalid", M({V: "totally wrong", S: None}), "escalated", "flag", has=("seat_invalid:claude",))
r = M({V: row(), S: "garbage"})
ck("a malformed SHADOW row is a note, never integrity", r, "auto", "pass", lacks=("seat_invalid",)) if "shadow_invalid:openai" in r["notes"] \
    else ck("a malformed SHADOW row is a note", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
# --- notes, not escalations (spec §2: prompt only on the listed reasons) ----------------------------------------
r = M({V: row(flat=True), S: row(ws=0.95)})
ck("a flat 1.0 voter is recorded as a note, not an escalation", r, "auto", "pass", lacks=("flat_ceiling",)) if "flat_ceiling:claude" in r["notes"] \
    else ck("flat ceiling noted", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
r = M({V: row(parity=False), S: row(ws=0.9)})
ck("missing evidence parity is a note", r, "auto", "pass") if "no_evidence_parity:claude" in r["notes"] \
    else ck("parity noted", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
# --- roles ------------------------------------------------------------------------------------------------------
r = M({V: row(), S: row(), "gemini": row("flag", 0.1)})
ck("an `off` seat is never consulted, even if a row is handed in", r, "auto", "pass") if all(s["id"] != "gemini" for s in r["seats"]) \
    else ck("off seat excluded from the record", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
TWO = [{"id": "a", "role": "voting"}, {"id": "b", "role": "voting"}]
ck("two voters that split -> escalated FLAG, never majority-resolved", qm.merge("x.md", {"a": row(), "b": row("flag", 0.5)}, TWO), "escalated", "flag", has=("verdict_mismatch",))
r = M({V: row(), S: row("flag", 0.4)})
ck("the record hides nothing from the LOG but flags unacked shadow verdicts", r, "escalated", "pass") if r["contains_unacked_shadow_verdicts"] \
    else ck("unacked shadow flag", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
ck("the record carries no retired fields", r, "escalated", "pass") if not any(k in r for k in ("canary_freshness", "independent_blocs", "claude", "gemini", "quorum_rules")) \
    else ck("retired fields gone", {"resolution": "?", "final_verdict": "?", "escalation_reasons": []}, "auto", "pass")
print(f"{ok}/{n} n-seat scenarios pass")
sys.exit(0 if ok == n else 1)
