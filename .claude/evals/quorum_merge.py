#!/usr/bin/env python3
"""quorum_merge.py: merge N judge seats into one verdict (YED-209). Generalises quorum-merge.sh (2 seats).

THE RULE THAT MAKES IT AIR TIGHT
  A seat's PASS reduces scrutiny only if that seat is VOTING (it earned that against Alex's labels).
  Any advisory or voting seat's DOUBT can add scrutiny. A shadow seat changes nothing, either way.
  A split is never auto-resolved: a majority built from possibly-correlated models is not independent evidence.

Status per seat = the LOWER of what Alex configured in seats.json and what the seat has earned
(calibration_stats.gate: auto-demotion, applied to every seat, the trusted one included).

  voting seats          other signals                          -> resolution        final
  all PASS              no reasons at all                      -> auto              pass
  all FLAG              no INTEGRITY reason                    -> auto              flag
  all PASS              quality reasons only                   -> escalated*        pass pending Alex's ack
  any                   an INTEGRITY reason                    -> escalated*        flag
  split                 anything                               -> escalated*        flag
  none effective        anything                               -> escalated*        flag   (no_voting_seat)
  * in --mode autonomous every `escalated` becomes `failsafe_flag` with final = flag (never auto-resolved).

  INTEGRITY reasons mean we cannot trust that the seats scored the same thing, so the artifact is never recorded
  as passing on their word: seat_missing · seat_invalid · evidence_mismatch · no_bundle_hash · no_voting_seat.
  QUALITY reasons are disagreement about the artifact itself and may stand as "pass pending ack": advisory_flag ·
  score_divergence · flat_ceiling · no_evidence_parity · same_group_only.
  A seat tagged evidence_unverified (>30% of its defect quotes are not in the artifact) loses BOTH its escalation
  power and its vote for that run: if its quotes are invented, its pass is not evidence either.
  NOT YET IMPLEMENTED (deferred to the canary step, spec §11 build step 8): spec §2 row 1 also requires "canaries
  fresh" for an auto-pass. There is no canary runner yet, so that condition is unchecked rather than forgotten.

Escalation reasons: verdict_mismatch · score_divergence (max pairwise |Δ| >= QUORUM_DIVERGENCE, default 0.15, among
non-shadow seats) · flat_ceiling:<seat> · no_evidence_parity:<seat> · advisory_flag:<seat> · seat_missing:<seat> ·
evidence_mismatch (seats scored different bundles) · no_bundle_hash:<seat> · no_voting_seat ·
same_group_only (all voting seats share one independence_group, so "unanimous" is one opinion).
A seat whose defect quotes fail verification (>30%) is tagged evidence_unverified:<seat>: recorded, and its own
flag / divergence no longer counts as a reason for THIS run (it cannot invent its way into an escalation).

Usage:
  quorum_merge.py --artifact <path> --seat <id>=<run-log.jsonl> [--seat ...] [--mode interactive|autonomous]
                  [--label <run-id>] [--print-only] [--reveal-shadow]
Each --seat points at that seat's run-log file; the LAST row for this artifact is used.
Exit 0 when a verdict was produced (advisory: the caller acts on `resolution`); 2 on a usage error such as an
unknown seat id, where nothing is merged. A malformed seat row is NOT an exception: it becomes seat_invalid.
"""
from __future__ import annotations
import argparse, itertools, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibration_stats as cal  # noqa: E402
import judge_lib as jl  # noqa: E402

ORDER = cal.ORDER
# reasons that mean the EVIDENCE is untrustworthy (vs. mere disagreement about the artifact)
INTEGRITY = {"seat_missing", "seat_invalid", "evidence_mismatch", "no_bundle_hash", "no_voting_seat"}


def last_row(path: str, artifact: str) -> dict | None:
    rows = []
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("record_type") != "quorum" and r.get("artifact") == artifact and r.get("verdict") in ("pass", "flag"):
            rows.append(r)
    return rows[-1] if rows else None


def valid_row(r: dict | None) -> bool:
    """A row we can actually score with. A seat that emitted a partial row is NOT silently treated as agreeing."""
    return bool(r) and r.get("verdict") in ("pass", "flag") and isinstance(r.get("weighted_score"), (int, float)) \
        and not isinstance(r.get("weighted_score"), bool)


def is_flat(r: dict) -> bool:
    cs = r.get("criterion_scores") or []
    return r.get("flat_ceiling") is True or (len(cs) == 5 and all(c.get("score") == 1 for c in cs))


def merge(artifact: str, seat_rows: dict[str, dict | None], cfg: list[dict], effective: dict[str, str],
          mode: str = "interactive", threshold: float = 0.15) -> dict:
    reasons: list[str] = []
    notes: list[str] = []
    live = {}                                      # non-shadow seats that reported
    for seat in cfg:
        sid, eff = seat["id"], effective.get(seat["id"], seat.get("status", "shadow"))
        row = seat_rows.get(sid)
        if eff == "shadow":
            continue                               # recorded below, never consulted
        if row is None:
            reasons.append(f"seat_missing:{sid}")
            continue
        if not valid_row(row):
            reasons.append(f"seat_invalid:{sid}")     # partial/malformed row: loud, not a traceback
            continue
        live[sid] = row
    unverified = {sid for sid, r in live.items() if (r.get("quote_check") or {}).get("evidence_unverified")}
    for sid in sorted(unverified):
        notes.append(f"evidence_unverified:{sid}")

    # a seat whose quotes are fabricated loses its VOTE as well as its escalation power: if it invented the
    # evidence for a defect, its "pass" is not evidence either (the one direction the air-tight rule must cover).
    voting = {sid: r for sid, r in live.items() if effective[sid] == "voting" and sid not in unverified}
    advisory = {sid: r for sid, r in live.items() if effective[sid] == "advisory"}

    hashes = {sid: r.get("bundle_sha256") for sid, r in live.items()}
    for sid, h in hashes.items():
        if not h:
            reasons.append(f"no_bundle_hash:{sid}")
    if len({h for h in hashes.values() if h}) > 1:
        reasons.append("evidence_mismatch")

    for sid, r in live.items():
        if is_flat(r):
            reasons.append(f"flat_ceiling:{sid}")
        if r.get("evidence_parity") is False:
            reasons.append(f"no_evidence_parity:{sid}")
    for sid, r in advisory.items():
        if r["verdict"] == "flag" and sid not in unverified:
            reasons.append(f"advisory_flag:{sid}")

    counted = {sid: r for sid, r in live.items() if sid not in unverified}
    div = max((abs(a["weighted_score"] - b["weighted_score"]) for a, b in itertools.combinations(counted.values(), 2)),
              default=0.0)
    if div >= threshold:
        reasons.append("score_divergence")

    def group_of(sid: str) -> str:
        s_ = next(x for x in cfg if x["id"] == sid)
        return s_.get("independence_group") or s_.get("provider") or sid      # provider OR group: spec §2
    groups = {group_of(sid) for sid in voting}
    verdicts = {r["verdict"] for r in voting.values()}
    if not voting:
        reasons.append("no_voting_seat")
        agreed = None
    elif len(verdicts) > 1:
        reasons.append("verdict_mismatch")
        agreed = None
    else:
        agreed = verdicts.pop()
        if len(voting) > 1 and len(groups) == 1:
            reasons.append("same_group_only")

    reasons = sorted(set(reasons))
    integrity = sorted(r for r in reasons if r.split(":")[0] in INTEGRITY)
    if agreed == "flag" and not integrity:
        resolution, final = "auto", "flag"         # a flag goes to Alex anyway; nothing to protect against
    elif agreed == "pass" and not reasons:
        resolution, final = "auto", "pass"
    else:
        resolution = "failsafe_flag" if mode == "autonomous" else "escalated"
        # integrity reasons mean the seats may not have scored the same artifact: never record that as a pass.
        final = "pass" if (agreed == "pass" and mode != "autonomous" and not integrity) else "flag"

    def block(sid: str) -> dict | None:
        r = seat_rows.get(sid)
        if r is None:
            return None                                   # .get() throughout: a partial row must never traceback
        return {"verdict": r.get("verdict"), "weighted_score": r.get("weighted_score"), "run_id": r.get("run_id"),
                "valid": valid_row(r)}

    rec = {"record_type": "quorum", "artifact": artifact, "mode": mode,
           "agree": agreed is not None, "resolution": resolution, "final_verdict": final,
           "divergence": round(div, 3), "escalation_reasons": reasons, "integrity_reasons": integrity, "notes": notes,
           "seats": [{"id": s["id"], "configured": s.get("status"), "effective": effective.get(s["id"]),
                      "independence_group": s.get("independence_group"), **(block(s["id"]) or {"verdict": None}),
                      "flat_ceiling": bool(seat_rows.get(s["id"]) and is_flat(seat_rows[s["id"]])),
                      "bundle_sha256": (seat_rows.get(s["id"]) or {}).get("bundle_sha256")} for s in cfg],
           "quorum_rules": "n-seat v1 (YED-209): voting decides, advisory adds caution, shadow is recorded only",
           # the LOG deliberately keeps every seat's real verdict, shadow included — calibration_stats needs it to
           # ever promote that seat. Hiding-until-ack is a PRESENTATION rule; any other consumer of this file
           # (dashboard, export) must re-apply it by checking seats[].effective == "shadow" and alex_ack == null.
           "contains_unacked_shadow_verdicts": any(x["effective"] == "shadow" and x.get("verdict") for x in
                                                   [{"effective": effective.get(s["id"]), **(block(s["id"]) or {})} for s in cfg]),
           "alex_ack": None}
    for legacy in ("claude", "gemini"):            # back-compat blocks the 2-seat readers expect
        if block(legacy):
            rec[legacy] = block(legacy)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--seat", action="append", default=[], metavar="ID=LOG")
    ap.add_argument("--mode", default="interactive", choices=["interactive", "autonomous"])
    ap.add_argument("--label", default=""); ap.add_argument("--print-only", action="store_true")
    ap.add_argument("--reveal-shadow", action="store_true",
                    help="show shadow seats' verdicts; REFUSED until this artifact has an acked quorum row")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    cfg = json.load(open(cal.SEATS_FILE, encoding="utf-8"))["seats"]
    seat_rows: dict[str, dict | None] = {s["id"]: None for s in cfg}
    for spec in a.seat:
        sid, _, path = spec.partition("=")
        if sid not in seat_rows:
            print(f"ERROR: unknown seat '{sid}' — not in {cal.SEATS_FILE}. Nothing merged (a typo must not "
                  f"silently drop a seat). Known ids: {', '.join(sorted(seat_rows))}", file=sys.stderr)
            return 2
        seat_rows[sid] = last_row(path, a.artifact) if os.path.isfile(path) else None
    g = cal.gate(cal.load(".claude/evals/logs"), 3.0)
    effective = {s["id"]: g.get(s["id"], {}).get("effective", s.get("status", "shadow")) for s in cfg}
    if a.reveal_shadow and not any(
            r.get("record_type") == "quorum" and r.get("artifact") == a.artifact and r.get("alex_ack")
            for r in cal.load(".claude/evals/logs")):
        print("REFUSED --reveal-shadow: no acked quorum row for this artifact yet. Ack the verdict first, or the "
              "shadow seat's score anchors the label it is supposed to be measured against.", file=sys.stderr)
        return 2
    rec = merge(a.artifact, seat_rows, cfg, effective, a.mode, float(os.environ.get("QUORUM_DIVERGENCE", "0.15")))
    rec.update({"run_id": a.label or f"quorum-{jl.slug_for(a.artifact)}", "timestamp": jl.now_utc(),
                "artifact_sha256": jl.sha256_file(a.artifact) if os.path.isfile(a.artifact) else None,
                "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession"),
                "demotions": {k: v["demoted_because"] for k, v in g.items() if v["demoted_because"]}})

    print(f"== quorum ({a.mode}) — {a.artifact}")
    for s in rec["seats"]:
        hidden = s["effective"] == "shadow" and not a.reveal_shadow
        shown = "recorded (hidden until you ack, so it can't sway your label)" if hidden and s["verdict"] else \
            ("— did not run" if s["verdict"] is None else f"{s['verdict']} ({s['weighted_score']})")
        demo = "  ⬇ auto-demoted" if s["configured"] != s["effective"] else ""
        print(f"   {s['id']:<8} {s['effective']:<9} {shown}{demo}")
    print(f"   divergence {rec['divergence']}  ->  {rec['resolution']}   final: {rec['final_verdict']}")
    if rec["escalation_reasons"]:
        print(f"   escalation reasons: {' '.join(rec['escalation_reasons'])}")
    if rec["notes"]:
        print(f"   notes: {' '.join(rec['notes'])}")
    for k, why in rec["demotions"].items():
        print(f"   ⬇ {k} demoted: {'; '.join(why)}")
    if rec["resolution"] == "escalated":
        print("   ACTION: show each non-shadow seat's per-criterion reasoning side by side; ask Alex agree/disagree -> alex_ack.")
    if rec["resolution"] == "failsafe_flag":
        print("   NOTE: autonomous mode -> failed safe to FLAG; queued for human review. Nothing was auto-resolved.")
    if not a.print_only:
        out = f".claude/evals/logs/{rec['timestamp'][:10]}-{jl.slug_for(a.artifact)}-{rec['run_id']}.jsonl"
        jl.append_log(out, rec)
        print(f"   logged -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
