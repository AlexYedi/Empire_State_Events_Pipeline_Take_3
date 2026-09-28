#!/usr/bin/env python3
"""seat-log.py: the ONLY way the Sonnet reviewer's verdict gets into the run-log (YED-209; YED-231).

The reviewer runs as a subagent, so its row used to be written by hand by the orchestrating model. On
2026-09-19 that produced four rows with made-up timestamps (00:00:00, 22:30:00 …) and no content hash, which
corrupted the calibration report. This writer takes ONLY the model's judgement (criterion scores,
defects, cap flags) and derives everything else itself: the real UTC time, the artifact's sha256, the session
id, the composite + score verdict (judge_lib.score) and the final pass/flag with its reasons (judge_lib.finalize:
score, guarded paths, privacy flag, flat ceiling, fabricated quotes). judge.py --resume calls this for you.

Usage:
  seat-log.py [--artifact <path>] --artifact-type <t> --verdict-file <json> [--bundle <bundle.json>]
  (--artifact is required without --bundle; with one it must match, and a multi-file bundle supplies it)
              [--calibration-set prospective] [--label <run-id>] [--note "..."] [--judge-model claude:sonnet]
  The verdict JSON needs: criterion_scores[5]{id,score,reasoning}; optional defects[], checks_performed[], cap_flags{}.
Prints the logged row as JSON on stdout and the log path on stderr.
Exit: 0 ok · 1 malformed verdict · 2 usage.
"""
from __future__ import annotations
import argparse, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evals"))
import judge_lib as jl  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", default="", help="the file judged; optional with --bundle (a multi-file bundle "
                    "names itself, e.g. range:abc1234..def5678)")
    ap.add_argument("--artifact-type", default="skill")
    ap.add_argument("--verdict-file", required=True); ap.add_argument("--bundle", default="")
    ap.add_argument("--calibration-set", default="prospective"); ap.add_argument("--label", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--judge-model", default="claude:sonnet")
    ap.add_argument("--print-only", action="store_true")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        bundle = json.load(open(a.bundle, encoding="utf-8")) if a.bundle else {}
    except (ValueError, OSError) as e:
        print(f"ERROR: unreadable bundle: {e}", file=sys.stderr); return 2
    if bundle and a.artifact and a.artifact != bundle.get("artifact"):
        print(f"ERROR: --artifact {a.artifact} is not the bundle's artifact ({bundle.get('artifact')})", file=sys.stderr)
        return 2
    a.artifact = a.artifact or bundle.get("artifact", "")
    multi = bundle.get("bundle_kind") in ("range", "files")
    if not multi and not os.path.isfile(a.artifact):
        print(f"ERROR: artifact not found: {a.artifact}", file=sys.stderr); return 2
    try:
        verdict = json.load(open(a.verdict_file, encoding="utf-8"))
        dangling = bundle.get("has_dangling")
        if dangling is None:
            dangling = bool(jl._run([".claude/hooks/check-refs.sh", "--artifact", a.artifact]))
        reported = verdict.get("weighted_score")
        scored = jl.score(verdict, a.artifact_type, dangling)
    except (ValueError, OSError, jl.JudgeError) as e:
        print(f"ERROR: malformed verdict: {e}", file=sys.stderr); return 1
    # the haystack is everything the reviewer was shown: every file, spec file and the context (YED-231 §4.2)
    hay = jl.bundle_haystack(bundle) if bundle else open(a.artifact, encoding="utf-8").read()
    qv = jl.verify_quotes(scored.get("defects") or [], hay, a.artifact_type)
    slug = jl.slug_for(a.artifact)
    rid = a.label or f"sonnet-{slug}"
    row = {"run_id": rid, "timestamp": jl.now_utc(), "artifact": a.artifact,
           "artifact_sha256": bundle.get("artifact_sha256") or jl.sha256_file(a.artifact),
           "artifact_type": a.artifact_type, "rubric": bundle.get("rubric_version") or "build-quality@6",
           "judge_model": a.judge_model, "judge_provider": "anthropic",
           "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession"),
           "criterion_scores": scored["criterion_scores"], "weighted_score": scored["weighted_score"],
           "raw_score": scored["raw_score"], "verdict": scored["verdict"], "alex_ack": None,
           "selfreported_weighted_score": reported if isinstance(reported, (int, float)) else None,
           "confidence_honesty_violation": scored["confidence_honesty_violation"],
           "privacy_layer_defect": scored.get("privacy_layer_defect", False),   # a flag reason in finalize(); no score cap since YED-231
           "defects": scored.get("defects") or [], "checks_performed": scored.get("checks_performed") or [],
           "cap_flags": scored.get("cap_flags") or {}, "flat_ceiling": scored["flat_ceiling"],
           "scoring": "harness-recomputed", "quote_check": qv, "must_cite_gaps": jl.must_cite_gaps(scored),
           "calibration_set": a.calibration_set, "evidence_parity": bundle.get("evidence_parity", True),
           "bundle_sha256": bundle.get("bundle_sha256"), "bundle_version": bundle.get("bundle_version"),
           "bundle_mode": bundle.get("bundle_mode")}      # "hunks" = the reviewer never saw the whole of every file
    row.update(jl.finalize(row, bundle))                  # final_verdict + flag_reasons (Alex is asked only on flag)
    if a.note:
        row["note"] = a.note
    if not a.print_only:
        logs = os.environ.get("JUDGE_LOG_DIR") or ".claude/evals/logs"   # override only for offline tests
        out = f"{logs}/{row['timestamp'][:10]}-{slug}-{rid}.jsonl"
        jl.append_log(out, row)
        print(f"logged → {out}", file=sys.stderr)
    print(json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
