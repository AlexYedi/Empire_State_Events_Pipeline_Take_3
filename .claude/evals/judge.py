#!/usr/bin/env python3
"""judge.py: the build-quality judge in one command (YED-231; design .claude/references/judge.md).

One reviewer (Claude Sonnet) raises flags. No seats, no quorum, no trust ladder: nothing here reads a calibration
number. When to run it at all is the artifact-class trigger list in .claude/skills/judge-build/SKILL.md.

  judge.py run (--artifact P | --files A B … | --range BASE..HEAD) --artifact-type T [--spec-file S …] [--context C]
               [--label L] [--calibration-set prospective|control] [--artifact-blob SHA]
      Builds ONE bundle (judge_lib: privacy guard + pre-passes), writes the reviewer brief, and prints how to
      dispatch it. The reviewer is a subagent and only the PARENT thread can spawn one (SDK constraint), so the
      run pauses here. The judge layer itself is refused as a target and dropped from a range (never self-judged).
  judge.py run --resume <run-id> --verdict <reviewer.json> [--judge-model claude:sonnet[:<model id>]]
      Logs the verdict through seat-log.py (the only writer; it computes score, final verdict and flag reasons)
      and prints ONE line. PASS needs nothing from Alex. FLAG prints the reasons and the ack command.
  judge.py ack --run <run-id> agree|disagree ["note"]
      Append-only ack row (never rewrites a row), UTC-stamped, one per run.

Exit: 0 ok · 1 verdict rejected · 2 usage · 3 privacy guard.
"""
from __future__ import annotations
import argparse, glob, json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_lib as jl  # noqa: E402

LOGS = os.environ.get("JUDGE_LOG_DIR") or ".claude/evals/logs"      # override only for offline tests
STATE = os.environ.get("JUDGE_STATE_DIR") or ".claude/.state/judge"
OUTPUT_CONTRACT = """

===== OUTPUT (reviewer) =====
Return ONLY one JSON object, no prose around it:
{"checks_performed": [str], "defects": [{"file": str, "line": int, "quote": str, "location": str, "criterion": one of
the 5 criteria, "severity": "major"|"minor", "spec_ref": str, "description": str}], "criterion_scores": [{"id": str,
"score": number, "reasoning": str}] (all 5), "cap_flags": {"confidence_honesty_violation": bool, "spec_drift": bool,
"command_skeleton_absent": bool, "density_padding": bool, "privacy_layer_defect": bool}}
No composite, no verdict: the harness computes both. Every `quote` is checked verbatim against the bundle. Do not
read .claude/evals/logs/."""


def _rows() -> list[tuple[str, dict]]:
    out = []
    for f in sorted(glob.glob(os.path.join(LOGS, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                out.append((f, json.loads(line)))
            except ValueError:
                continue
    return out


def run(a) -> int:
    if a.resume:
        return resume(a)
    targets = ([a.artifact] if a.artifact else []) + (a.files or [])
    selfj = [p for p in targets if jl.is_judge_layer(p)]
    if selfj:
        print(f"REFUSED: {', '.join(selfj)} is the judge layer, which is never judged by itself (YED-231). "
              "Use the offline tests + deterministic checks instead.", file=sys.stderr)
        return 2
    try:
        b = jl.build_bundle(a.artifact, a.artifact_type, a.system, a.rubric, a.context, a.spec_file,
                            artifact_blob=a.artifact_blob, files=a.files, rng=a.rng, skip_judge_layer=True)
    except jl.PrivacyViolation as e:
        print(f"PRIVACY GUARD (nothing built): {e}", file=sys.stderr); return 3
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    rid = a.label or f"{jl.slug_for(b['artifact'])}-{jl.now_utc().replace('-', '').replace(':', '')}"
    d = os.path.join(STATE, rid)
    os.makedirs(d, exist_ok=True)
    bpath, brief = os.path.join(d, "bundle.json"), os.path.join(d, "brief.txt")
    json.dump(b, open(bpath, "w", encoding="utf-8"))
    open(brief, "w", encoding="utf-8").write(b["text"] + OUTPUT_CONTRACT)
    json.dump({"run_id": rid, "artifact_type": a.artifact_type, "bundle": bpath, "calibration_set": a.calibration_set},
              open(os.path.join(d, "state.json"), "w", encoding="utf-8"))
    guarded = jl.guarded_paths([f["path"] for f in b["files"]])
    print(f"judge {rid}: bundle {b['bundle_sha256'][:12]} · {b['artifact']} · {len(b['files'])} file(s), "
          f"{b['bundle_mode']} · {len(b['text'])} chars · evidence_parity={b['evidence_parity']}")
    if not b["evidence_parity"]:
        print("  ⚠️  EVIDENCE-PARITY: < 400 chars of spec. Rebuild with --spec-file if a spec exists.")
    if guarded:
        print(f"  guarded path(s) {', '.join(guarded)}: this run will FLAG for human review whatever the score.")
    print(f"  NEXT (parent thread): dispatch the reviewer with the Agent tool, model: sonnet, prompt:\n"
          f"    \"Read {brief} and follow it exactly. Return only the JSON object.\"\n"
          f"  save its JSON to {d}/verdict.json, then:\n"
          f"    python3 .claude/evals/judge.py run --resume {rid} --verdict {d}/verdict.json")
    return 0


def resume(a) -> int:
    try:
        st = json.load(open(os.path.join(STATE, a.resume, "state.json"), encoding="utf-8"))
    except (OSError, ValueError):
        print(f"ERROR: no judge run '{a.resume}' under {STATE}/", file=sys.stderr); return 2
    if not a.verdict:
        print("ERROR: --resume needs --verdict <reviewer.json>", file=sys.stderr); return 2
    prev = [r for _, r in _rows() if r.get("judge_provider") == "anthropic" and r.get("judge_model")]
    p = subprocess.run(["python3", ".claude/hooks/seat-log.py", "--artifact-type", st["artifact_type"],
                        "--verdict-file", a.verdict, "--bundle", st["bundle"], "--label", a.resume,
                        "--calibration-set", st.get("calibration_set") or "prospective", "--judge-model", a.judge_model],
                       capture_output=True, text=True)
    if p.returncode:
        print(f"verdict rejected by seat-log.py (rc={p.returncode}): {p.stderr.strip()[:300]}\n"
              "  nothing logged: re-dispatch the reviewer", file=sys.stderr)
        return 1
    row = json.loads(p.stdout.strip().splitlines()[-1])
    log = next((l.split("→", 1)[1].strip() for l in p.stderr.splitlines() if "logged →" in l), "")
    line = f"judge {a.resume}: {row['final_verdict'].upper()} · score {row['weighted_score']} · {row['artifact']}"
    if row["final_verdict"] == "flag":
        line += ("\n  reasons: " + "; ".join(row["flag_reasons"])
                 + f"\n  ASK ALEX, then: python3 .claude/evals/judge.py ack --run {a.resume} agree|disagree \"why\"")
    print(line + (f"\n  log: {log}" if log else ""))
    last = prev[-1]["judge_model"] if prev else None
    if last and last != a.judge_model:
        print(f"  model id changed ({last} → {a.judge_model}): run the control set once "
              "(python3 .claude/evals/controls.py plan). That is the ONLY trigger for a control run.")
    return 0


def ack(a) -> int:
    rows = _rows()
    hits = [(f, r) for f, r in rows if r.get("run_id") == a.run and r.get("record_type") is None
            and r.get("judge_provider") == "anthropic"]
    if len(hits) != 1:
        print(f"REFUSED {a.run}: {len(hits)} reviewer rows carry this run_id (need exactly 1)", file=sys.stderr)
        return 2
    if any(r.get("record_type") == "ack" and r.get("run_id") == a.run for _, r in rows):
        print(f"REFUSED {a.run}: already acked; acks are append-only and one per run", file=sys.stderr)
        return 2
    f, r = hits[0]
    now = jl.now_utc()
    jl.append_log(f, {"record_type": "ack", "run_id": a.run, "artifact": r.get("artifact"),
                      "artifact_sha256": r.get("artifact_sha256"), "artifact_type": r.get("artifact_type"),
                      "verdict": r.get("final_verdict") or r.get("verdict"), "alex_ack": a.verdict,
                      "alex_ack_at": now, "note": a.note or None, "timestamp": now,
                      "calibration_set": r.get("calibration_set"), "evidence_parity": r.get("evidence_parity"),
                      "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession")})
    print(f"acked {a.run}: {a.verdict} (final was {r.get('final_verdict') or r.get('verdict')})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="build-quality judge: run / ack")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    src = r.add_mutually_exclusive_group()
    src.add_argument("--artifact"); src.add_argument("--files", nargs="+"); src.add_argument("--range", dest="rng")
    src.add_argument("--resume", metavar="RUN_ID")
    r.add_argument("--verdict"); r.add_argument("--judge-model", default="claude:sonnet")
    r.add_argument("--artifact-type", default="skill")
    r.add_argument("--spec-file", action="append", default=[]); r.add_argument("--context", default="")
    r.add_argument("--label", default=""); r.add_argument("--artifact-blob")
    r.add_argument("--calibration-set", default="prospective")
    r.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v6.md")   # frozen at @6 (YED-231)
    r.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
    k = sub.add_parser("ack")
    k.add_argument("--run", required=True); k.add_argument("verdict", choices=["agree", "disagree"])
    k.add_argument("note", nargs="?", default="")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if a.cmd == "run":
        if not (a.resume or a.artifact or a.files or a.rng):
            ap.error("run needs one of --artifact, --files, --range, --resume")
        return run(a)
    return ack(a)


if __name__ == "__main__":
    sys.exit(main())
