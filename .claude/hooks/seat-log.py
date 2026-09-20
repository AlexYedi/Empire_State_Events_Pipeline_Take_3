#!/usr/bin/env python3
"""seat-log.py: the ONLY way the Claude (Sonnet) seat's verdict gets into the run-log (YED-209).

The Sonnet seat runs as a subagent, so its row used to be written by hand by the orchestrating model. On
2026-09-19 that produced four rows with made-up timestamps (00:00:00, 22:30:00 …) and no content hash, which
helped make the trusted seat read kappa 0.53. This writer takes ONLY the model's judgement (criterion scores,
defects, cap flags) and derives everything else itself: the real UTC time, the artifact's sha256, the session
id, and the composite + verdict (judge_lib.score, the same arithmetic every seat gets).

Usage:
  seat-log.py --artifact <path> --artifact-type <t> --verdict-file <json> [--bundle <bundle.json>]
              [--calibration-set prospective] [--label <run-id>] [--note "..."] [--judge-model claude:sonnet]
  The verdict JSON needs: criterion_scores[5]{id,score,reasoning}; optional defects[], checks_performed[], cap_flags{}.
Prints the scored verdict as JSON on stdout (pass it to quorum_merge.py) and the log path on stderr.
Exit: 0 ok · 1 malformed verdict · 2 usage.
"""
from __future__ import annotations
import argparse, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evals"))
import judge_lib as jl  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True); ap.add_argument("--artifact-type", default="skill")
    ap.add_argument("--verdict-file", required=True); ap.add_argument("--bundle", default="")
    ap.add_argument("--calibration-set", default="prospective"); ap.add_argument("--label", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--judge-model", default="claude:sonnet")
    ap.add_argument("--print-only", action="store_true")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if not os.path.isfile(a.artifact):
        print(f"ERROR: artifact not found: {a.artifact}", file=sys.stderr); return 2
    try:
        verdict = json.load(open(a.verdict_file, encoding="utf-8"))
        bundle = json.load(open(a.bundle, encoding="utf-8")) if a.bundle else {}
        dangling = bundle.get("has_dangling")
        if dangling is None:
            dangling = bool(jl._run([".claude/hooks/check-refs.sh", "--artifact", a.artifact]))
        reported = verdict.get("weighted_score")
        scored = jl.score(verdict, a.artifact_type, dangling)
    except (ValueError, OSError, jl.JudgeError) as e:
        print(f"ERROR: malformed verdict: {e}", file=sys.stderr); return 1
    qv = jl.verify_quotes(scored.get("defects") or [], open(a.artifact, encoding="utf-8").read())
    slug = jl.slug_for(a.artifact)
    rid = a.label or f"sonnet-{slug}"
    row = {"run_id": rid, "timestamp": jl.now_utc(), "artifact": a.artifact,
           "artifact_sha256": bundle.get("artifact_sha256") or jl.sha256_file(a.artifact),
           "artifact_type": a.artifact_type, "rubric": bundle.get("rubric_version") or "build-quality@5",
           "judge_model": a.judge_model, "judge_provider": "anthropic", "seat_status": "voting",
           "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession"),
           "criterion_scores": scored["criterion_scores"], "weighted_score": scored["weighted_score"],
           "raw_score": scored["raw_score"], "verdict": scored["verdict"], "alex_ack": None,
           "selfreported_weighted_score": reported if isinstance(reported, (int, float)) else None,
           "confidence_honesty_violation": scored["confidence_honesty_violation"],
           "defects": scored.get("defects") or [], "checks_performed": scored.get("checks_performed") or [],
           "cap_flags": scored.get("cap_flags") or {}, "flat_ceiling": scored["flat_ceiling"],
           "scoring": "harness-recomputed", "quote_check": qv, "must_cite_gaps": jl.must_cite_gaps(scored),
           "calibration_set": a.calibration_set, "evidence_parity": bundle.get("evidence_parity", True),
           "bundle_sha256": bundle.get("bundle_sha256"), "bundle_version": bundle.get("bundle_version")}
    if a.note:
        row["note"] = a.note
    if not a.print_only:
        out = f".claude/evals/logs/{row['timestamp'][:10]}-{slug}-{rid}.jsonl"
        jl.append_log(out, row)
        print(f"logged → {out}", file=sys.stderr)
    print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
