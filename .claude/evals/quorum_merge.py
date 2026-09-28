#!/usr/bin/env python3
"""quorum_merge.py: merge the judge seats into one verdict (YED-209; right-sized by YED-231).

Spec: .claude/references/judge-right-size-yed-231.md §2/§4. Roles come from seats.json, a static map only Alex edits:
  voting   its verdict IS the verdict
  shadow   runs on every build, hidden from Alex until he acks; it can only ADD an escalation, never decide
  off      not run and not consulted (the adapter is kept)

  voting seat           other signals                              -> resolution        final
  pass                  none                                       -> auto              pass
  flag                  no INTEGRITY reason                        -> auto              flag  (rework is already a conversation)
  pass                  a shadow reason (below)                    -> escalated*        pass pending Alex's ack
  any                   an INTEGRITY reason                        -> escalated*        flag
  * in --mode autonomous every `escalated` becomes `failsafe_flag` with final = flag (never auto-resolved).

  Shadow reasons (only from a shadow whose quotes verified):
    verdict_mismatch:<seat>     the shadow's verdict differs from the voter's
    score_divergence            |voter - shadow| >= QUORUM_DIVERGENCE (default 0.15)
    shadow_major_defect:<seat>  on a voter PASS, the shadow filed a `major` defect whose own quote verified
  INTEGRITY reasons mean we cannot trust that the seats scored the same thing, or that the voter's verdict is
  evidence, so the artifact is never recorded as passing: seat_missing · seat_invalid · evidence_mismatch ·
  no_bundle_hash · no_voting_seat. A seat whose defect quotes fail verification (>30%) is tagged
  evidence_unverified:<seat> and loses every signal for this run; for the voter that means its vote, so the run
  ends in no_voting_seat. Flat ceilings and missing evidence parity are recorded as notes, not escalations.

Usage:
  quorum_merge.py --artifact <path|range:..|files:..> --seat <id>=<run-log.jsonl> [--seat ...]
                  [--mode interactive|autonomous] [--label <run-id>] [--print-only] [--reveal-shadow]
Each --seat points at that seat's run-log file; the LAST row for this artifact is used. `judge.py run` calls this
for you. Exit 0 when a verdict was produced; 2 on a usage error such as an unknown seat id (nothing is merged).
A malformed seat row is NOT an exception: it becomes seat_invalid.
"""
from __future__ import annotations
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibration_stats as cal  # noqa: E402
import judge_lib as jl  # noqa: E402

INTEGRITY = {"seat_missing", "seat_invalid", "evidence_mismatch", "no_bundle_hash", "no_voting_seat"}


def last_row(path: str, artifact: str) -> tuple[dict | None, int]:
    """The LAST seat row for this artifact, plus the count of unparseable lines.

    Deliberately NOT "the last row that has a verdict": if the newest row is partial, that is a seat_invalid to
    surface, not something to paper over by reaching further back for an older, healthier-looking row.
    """
    rows, corrupt = [], 0
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            corrupt += 1
            continue
        if r.get("record_type") not in ("quorum", "quorum_ack") and r.get("artifact") == artifact:
            rows.append(r)
    return (rows[-1] if rows else None), corrupt


def valid_row(r: dict | None) -> bool:
    """A row we can actually score with. Validates EVERY field merge() later touches, so nothing downstream may
    raise on a row this accepts (a junk `criterion_scores` once crashed is_flat(); found by the Sonnet seat)."""
    if not isinstance(r, dict) or r.get("verdict") not in ("pass", "flag"):
        return False
    ws = r.get("weighted_score")
    if not isinstance(ws, (int, float)) or isinstance(ws, bool):
        return False
    cs = r.get("criterion_scores")
    if cs is not None and (not isinstance(cs, list) or not all(isinstance(c, dict) for c in cs)):
        return False
    qc = r.get("quote_check")
    if qc is not None and not isinstance(qc, dict):
        return False
    d = r.get("defects")
    return d is None or isinstance(d, list)


def is_flat(r: dict) -> bool:
    cs = r.get("criterion_scores") or []
    return r.get("flat_ceiling") is True or (len(cs) == 5 and all(c.get("score") == 1 for c in cs))


def verified_majors(r: dict) -> int:
    """`major` defects whose OWN quote verified (quote_check.matched_in is aligned with defects). A row without
    matched_in (pre-YED-231) counts 0: an unproven major must not escalate."""
    mi = (r.get("quote_check") or {}).get("matched_in")
    if not isinstance(mi, list):
        return 0
    return sum(1 for d, m in zip(r.get("defects") or [], mi) if isinstance(d, dict) and d.get("severity") == "major" and m)


def merge(artifact: str, seat_rows: dict[str, dict | None], cfg: list[dict], mode: str = "interactive",
          threshold: float = 0.15) -> dict:
    # Normalise at the boundary: anything that is not a dict becomes a sentinel, so nothing below defends itself.
    seat_rows = {k: (v if isinstance(v, dict) else (None if v is None else {"_malformed": repr(v)[:80]}))
                 for k, v in seat_rows.items()}
    role = {s["id"]: s.get("role", "shadow") for s in cfg}
    reasons: list[str] = []
    notes: list[str] = []
    voters: dict[str, dict] = {}
    shadows: dict[str, dict] = {}
    for s in cfg:
        sid, rl, row = s["id"], role[s["id"]], seat_rows.get(s["id"])
        if rl == "off":
            continue
        voting = rl == "voting"
        if row is None:
            (reasons if voting else notes).append(f"{'seat' if voting else 'shadow'}_missing:{sid}")
        elif not valid_row(row):
            (reasons if voting else notes).append(f"{'seat' if voting else 'shadow'}_invalid:{sid}")
        else:
            (voters if voting else shadows)[sid] = row
    live = {**voters, **shadows}
    unverified = {sid for sid, r in live.items() if (r.get("quote_check") or {}).get("evidence_unverified")}
    notes += [f"evidence_unverified:{sid}" for sid in sorted(unverified)]

    hashes = {sid: r.get("bundle_sha256") for sid, r in live.items()}
    reasons += [f"no_bundle_hash:{sid}" for sid, h in hashes.items() if not h]
    if len({h for h in hashes.values() if h}) > 1:
        reasons.append("evidence_mismatch")
    for sid, r in live.items():
        if is_flat(r):
            notes.append(f"flat_ceiling:{sid}")
        if r.get("evidence_parity") is False:
            notes.append(f"no_evidence_parity:{sid}")

    # a voter whose quotes are fabricated loses its vote: if it invented a defect's evidence, its pass is not evidence
    counted = {sid: r for sid, r in voters.items() if sid not in unverified}
    verdicts = {r["verdict"] for r in counted.values()}
    if not counted:
        reasons.append("no_voting_seat")
        agreed = None
    elif len(verdicts) > 1:
        reasons.append("verdict_mismatch")           # two voters disagree: never majority-resolved
        agreed = None
    else:
        agreed = next(iter(verdicts))
    div = 0.0
    if agreed is not None:
        for sid, r in shadows.items():
            if sid in unverified:
                continue                             # an unverified shadow cannot escalate by any route
            if r["verdict"] != agreed:
                reasons.append(f"verdict_mismatch:{sid}")
            div = max([div] + [abs(r["weighted_score"] - v["weighted_score"]) for v in counted.values()])
            if agreed == "pass" and verified_majors(r):
                reasons.append(f"shadow_major_defect:{sid}")
        if div >= threshold:
            reasons.append("score_divergence")

    reasons = sorted(set(reasons))
    integrity = sorted(x for x in reasons if x.split(":")[0] in INTEGRITY)
    esc = "failsafe_flag" if mode == "autonomous" else "escalated"
    if integrity or agreed is None:
        resolution, final = esc, "flag"
    elif agreed == "flag":
        resolution, final = "auto", "flag"
    elif not reasons:
        resolution, final = "auto", "pass"
    else:
        resolution, final = esc, ("flag" if mode == "autonomous" else "pass")

    def block(sid: str) -> dict:
        r = seat_rows.get(sid)
        if r is None:
            return {"verdict": None}
        if not valid_row(r):
            return {"verdict": None, "weighted_score": None, "run_id": r.get("run_id"), "valid": False}
        return {"verdict": r["verdict"], "weighted_score": r["weighted_score"], "run_id": r.get("run_id"), "valid": True,
                "flat_ceiling": is_flat(r), "bundle_sha256": r.get("bundle_sha256")}

    seats = [{"id": s["id"], "role": role[s["id"]], **block(s["id"])} for s in cfg if role[s["id"]] != "off"]
    return {"record_type": "quorum", "artifact": artifact, "mode": mode,
            "artifact_sha256": next((r.get("artifact_sha256") for r in live.values() if r.get("artifact_sha256")), None),
            "agree": agreed is not None and not any(x.startswith("verdict_mismatch") for x in reasons),
            "resolution": resolution, "final_verdict": final, "divergence": round(div, 3),
            "escalation_reasons": reasons, "integrity_reasons": integrity, "notes": notes,
            "voting_seats": sorted(voters), "seats": seats,
            # the LOG keeps every seat's real verdict, shadow included (calibration needs it). Hiding-until-ack is a
            # PRESENTATION rule: any consumer must re-apply it (seats[].role == "shadow" and alex_ack == null).
            "contains_unacked_shadow_verdicts": any(x["role"] == "shadow" and x.get("verdict") for x in seats),
            "alex_ack": None}


def acked_versions(artifact: str) -> set:
    """Content hashes of this artifact that carry an ack (quorum_ack rows are folded in by cal.load)."""
    return {r.get("artifact_sha256") for r in cal.load(".claude/evals/logs")
            if r.get("record_type") == "quorum" and r.get("artifact") == artifact and r.get("alex_ack")}


def render(rec: dict, reveal: bool = False) -> list[str]:
    out = [f"== quorum ({rec['mode']}) — {rec['artifact']}"]
    for s in rec["seats"]:
        hidden = s["role"] == "shadow" and not reveal
        shown = "recorded (hidden until you ack, so it can't sway your label)" if hidden and s.get("verdict") else \
            ("— did not run" if s.get("verdict") is None else f"{s['verdict']} ({s['weighted_score']})")
        out.append(f"   {s['id']:<8} {s['role']:<7} {shown}")
    out.append(f"   divergence {rec['divergence']}  ->  {rec['resolution']}   final: {rec['final_verdict']}")
    if rec["escalation_reasons"]:
        out.append(f"   escalation reasons: {' '.join(rec['escalation_reasons'])}")
    if rec["notes"]:
        out.append(f"   notes: {' '.join(rec['notes'])}")
    return out


def finalize(rec: dict, label: str = "", corrupt: dict | None = None) -> dict:
    """Stamp id/time/content hash; a corrupt log line is never silently skipped."""
    for sid, nbad in sorted((corrupt or {}).items()):
        rec["notes"].append(f"corrupt_log_lines:{sid}={nbad}")
        print(f"   ⚠️  {nbad} unparseable line(s) in {sid}'s log — the row used may not be the newest.", file=sys.stderr)
    art = rec["artifact"]
    # the hash the seats scored wins; a plain file with no seat hash falls back to its bytes on disk
    sha = rec.get("artifact_sha256") or (jl.sha256_file(art) if os.path.isfile(art) else None)
    rec.update({"run_id": label or f"quorum-{jl.slug_for(art)}", "timestamp": jl.now_utc(), "artifact_sha256": sha,
                "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession")})
    return rec


def write(rec: dict) -> str:
    out = f".claude/evals/logs/{rec['timestamp'][:10]}-{jl.slug_for(rec['artifact'])}-{rec['run_id']}.jsonl"
    jl.append_log(out, rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--seat", action="append", default=[], metavar="ID=LOG")
    ap.add_argument("--mode", default="interactive", choices=["interactive", "autonomous"])
    ap.add_argument("--label", default=""); ap.add_argument("--print-only", action="store_true")
    ap.add_argument("--reveal-shadow", action="store_true",
                    help="show shadow seats' verdicts; REFUSED until this version of the artifact has an ack")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    cfg = json.load(open(cal.SEATS_FILE, encoding="utf-8"))["seats"]
    seat_rows: dict[str, dict | None] = {s["id"]: None for s in cfg}
    corrupt: dict[str, int] = {}
    for spec in a.seat:
        sid, _, path = spec.partition("=")
        if sid not in seat_rows:
            print(f"ERROR: unknown seat '{sid}' — not in {cal.SEATS_FILE}. Nothing merged (a typo must not "
                  f"silently drop a seat). Known ids: {', '.join(sorted(seat_rows))}", file=sys.stderr)
            return 2
        if os.path.isfile(path):
            seat_rows[sid], bad = last_row(path, a.artifact)
            if bad:
                corrupt[sid] = bad
    rec = finalize(merge(a.artifact, seat_rows, cfg, a.mode, float(os.environ.get("QUORUM_DIVERGENCE", "0.15"))),
                   a.label, corrupt)
    if a.reveal_shadow and rec["artifact_sha256"] not in acked_versions(a.artifact):
        print("REFUSED --reveal-shadow: no ack for THIS version of the artifact (content hash "
              f"{str(rec['artifact_sha256'])[:12]}). Ack first (judge.py ack), or the shadow seat's score anchors "
              "the label it is supposed to be measured against.", file=sys.stderr)
        return 2
    print("\n".join(render(rec, a.reveal_shadow)))
    if not a.print_only:
        print(f"   logged -> {write(rec)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
