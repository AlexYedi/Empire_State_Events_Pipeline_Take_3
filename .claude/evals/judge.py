#!/usr/bin/env python3
"""judge.py: the build-quality judge in one command (YED-231; spec .claude/references/judge-right-size-yed-231.md).

  judge.py run (--artifact P | --files A B … | --range BASE..HEAD) --artifact-type T --spec-file S [--context C]
               [--mode interactive|autonomous] [--label L] [--dry-run]
      1. builds ONE bundle (judge_lib, privacy guard, pre-passes), 2. runs every `shadow` seat's adapter on it,
      3. writes the Sonnet brief and prints how to dispatch it. The Sonnet seat is a subagent, and only the PARENT
      thread can spawn one (SDK constraint), so the run pauses here. Then:
  judge.py run --resume <run-id> --sonnet-verdict <json>
      logs the Sonnet verdict through seat-log.py (the only writer), merges (quorum_merge), prints ONE line, and
      the revisit banner when calibration_stats.check() says it is due.
  judge.py ack --run <quorum-run-id> [--run …] agree|disagree ["note"]
      the ONLY alex_ack writer: appends a `quorum_ack` row (never rewrites a row), stamps alex_ack_at in UTC,
      refuses a second ack on the same run, then shows the shadow verdicts it was hiding.
  judge.py pending [--days 7]
      un-acked clean passes, for the weekly batch-ack in /rigor-review.

Exit: 0 ok · 2 usage · 3 privacy guard · 4 budget (from a shadow adapter's dry-run).
"""
from __future__ import annotations
import argparse, datetime, glob, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calibration_stats as cal  # noqa: E402
import judge_lib as jl  # noqa: E402
import quorum_merge as qm  # noqa: E402

LOGS = ".claude/evals/logs"
STATE = ".claude/.state/judge"
OUTPUT_CONTRACT = """

===== OUTPUT (Sonnet seat) =====
Return ONLY one JSON object, no prose around it:
{"checks_performed": [str], "defects": [{"file": str, "line": int, "quote": str, "location": str, "criterion": one of
the 5 criteria, "severity": "major"|"minor", "spec_ref": str, "description": str}], "criterion_scores": [{"id": str,
"score": number, "reasoning": str}] (all 5), "cap_flags": {"confidence_honesty_violation": bool, "spec_drift": bool,
"command_skeleton_absent": bool, "density_padding": bool, "privacy_layer_defect": bool}}
No composite, no verdict: the harness computes both. Every `quote` is checked verbatim against the bundle. Do not
read .claude/evals/logs/."""


def _logged_path(text: str) -> str | None:
    m = re.search(r"logged\s*(?:→|->)\s*(\S+\.jsonl)", text)
    return m.group(1) if m else None


def run(a) -> int:
    if a.resume:
        return resume(a)
    seats = json.load(open(cal.SEATS_FILE, encoding="utf-8"))["seats"]
    try:
        b = jl.build_bundle(a.artifact, a.artifact_type, a.system, a.rubric, a.context, a.spec_file,
                            files=a.files, rng=a.rng)
    except jl.PrivacyViolation as e:
        print(f"PRIVACY GUARD (nothing built, nothing sent): {e}", file=sys.stderr); return 3
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2
    rid = a.label or f"{jl.slug_for(b['artifact'])}-{jl.now_utc().replace('-', '').replace(':', '')}"
    d = os.path.join(STATE, rid)
    os.makedirs(d, exist_ok=True)
    bpath, brief = os.path.join(d, "bundle.json"), os.path.join(d, "brief.txt")
    json.dump(b, open(bpath, "w", encoding="utf-8"))
    open(brief, "w", encoding="utf-8").write(b["text"] + OUTPUT_CONTRACT)
    print(f"judge {rid}: bundle {b['bundle_sha256'][:12]} · {b['artifact']} · {len(b['files'])} file(s), "
          f"{b['bundle_mode']} · {len(b['text'])} chars · evidence_parity={b['evidence_parity']}")
    if not b["evidence_parity"]:
        print("  ⚠️  EVIDENCE-PARITY: < 400 chars of spec. Rebuild with --spec-file (no seat flag can repair it).")
    shadow_logs, rc_worst = {}, 0
    for s in seats:
        if s.get("role") != "shadow" or not str(s.get("runner", "")).endswith((".sh", ".py")):
            continue
        cmd = ["bash", s["runner"]] if s["runner"].endswith(".sh") else ["python3", s["runner"]]
        p = subprocess.run(cmd + ["--bundle", bpath, "--label", f"{s['id']}-{rid}"] + (["--dry-run"] if a.dry_run else []),
                           capture_output=True, text=True)
        path = _logged_path(p.stdout + p.stderr)
        if a.dry_run:
            print(f"  {s['id']} (shadow) dry-run rc={p.returncode}: {(p.stdout + p.stderr).strip().splitlines()[-1:]}")
            rc_worst = max(rc_worst, p.returncode if p.returncode in (3, 4) else 0)
        elif p.returncode == 0 and path:
            shadow_logs[s["id"]] = path
            print(f"  {s['id']} (shadow) scored; verdict hidden until you ack")
        else:
            print(f"  {s['id']} (shadow) FAILED rc={p.returncode}: {(p.stdout + p.stderr).strip()[-200:]} "
                  "(recorded as shadow_missing; the voter still decides)")
    json.dump({"run_id": rid, "artifact": b["artifact"], "artifact_type": a.artifact_type, "mode": a.mode,
               "bundle": bpath, "shadow_logs": shadow_logs}, open(os.path.join(d, "state.json"), "w"))
    if a.dry_run:
        print("  dry-run: nothing sent, nothing logged."); return rc_worst
    print(f"  NEXT (parent thread): dispatch the Sonnet seat with the Agent tool, model: sonnet, prompt:\n"
          f"    \"Read {brief} and follow it exactly. Return only the JSON object.\"\n"
          f"  save its JSON to {d}/sonnet.json, then:\n"
          f"    python3 .claude/evals/judge.py run --resume {rid} --sonnet-verdict {d}/sonnet.json")
    return 0


def resume(a) -> int:
    try:
        st = json.load(open(os.path.join(STATE, a.resume, "state.json"), encoding="utf-8"))
    except (OSError, ValueError):
        print(f"ERROR: no judge run '{a.resume}' under {STATE}/", file=sys.stderr); return 2
    rows: dict[str, dict | None] = {}
    if a.sonnet_verdict:
        p = subprocess.run(["python3", ".claude/hooks/seat-log.py", "--artifact-type", st["artifact_type"],
                            "--verdict-file", a.sonnet_verdict, "--bundle", st["bundle"], "--label", f"sonnet-{a.resume}"],
                           capture_output=True, text=True)
        if p.returncode:
            print(f"Sonnet verdict rejected by seat-log.py (rc={p.returncode}): {p.stderr.strip()[:300]}\n"
                  "  recorded as seat_missing:claude, which ends in flag", file=sys.stderr)
        else:
            rows["claude"] = json.loads(p.stdout.strip().splitlines()[-1])
    for sid, path in st["shadow_logs"].items():
        rows[sid] = qm.last_row(path, st["artifact"])[0] if os.path.isfile(path) else None
    cfg = json.load(open(cal.SEATS_FILE, encoding="utf-8"))["seats"]
    rec = qm.finalize(qm.merge(st["artifact"], rows, cfg, a.mode or st["mode"],
                               float(os.environ.get("QUORUM_DIVERGENCE", "0.15"))), f"quorum-{a.resume}")
    out = qm.write(rec)
    voter = next((s for s in rec["seats"] if s["role"] == "voting"), {})
    ask = rec["resolution"] == "escalated"
    print(f"judge {a.resume}: {rec['final_verdict'].upper()} ({rec['resolution']}) · voter {voter.get('weighted_score')}"
          + (f" · {' '.join(rec['escalation_reasons'])}" if rec["escalation_reasons"] else "")
          + (f" · ACK: judge.py ack --run {rec['run_id']} agree|disagree \"why\"" if ask else "") + f" · {out}")
    bn = cal.banner(cal.check(cal.load(LOGS)))
    if bn:
        print(bn)
    return 0


def _role(s: dict) -> str | None:
    return s.get("role") or s.get("effective")          # pre-YED-231 quorum rows carried `effective`


def _quorums() -> list[tuple[str, dict]]:
    out = []
    for f in sorted(glob.glob(os.path.join(LOGS, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("record_type") == "quorum":
                out.append((f, r))
    return out


def ack(a) -> int:
    folded = {r.get("run_id"): r for r in cal.load(LOGS) if r.get("record_type") == "quorum"}
    qs = _quorums()
    rc = 0
    for run_id in a.run:
        hits = [(f, r) for f, r in qs if r.get("run_id") == run_id]
        if len(hits) != 1:
            print(f"REFUSED {run_id}: {len(hits)} quorum rows carry this run_id (need exactly 1)", file=sys.stderr)
            rc = 2; continue
        f, r = hits[0]
        if (folded.get(run_id) or {}).get("alex_ack") or r.get("alex_ack"):
            print(f"REFUSED {run_id}: already acked ({(folded.get(run_id) or r).get('alex_ack')}); acks are append-only "
                  "and one per run", file=sys.stderr)
            rc = 2; continue
        now = jl.now_utc()
        jl.append_log(f, {"record_type": "quorum_ack", "run_id": run_id, "artifact": r.get("artifact"),
                          "artifact_sha256": r.get("artifact_sha256"), "alex_ack": a.verdict, "alex_ack_at": now,
                          "note": a.note or None, "timestamp": now,
                          "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession")})
        shown = ", ".join(f"{s['id']} {s.get('verdict')} ({s.get('weighted_score')})" for s in r.get("seats", [])
                          if _role(s) == "shadow") or "no shadow seat"
        print(f"acked {run_id}: {a.verdict} · final was {r.get('final_verdict')} · shadow revealed: {shown}")
    return rc


def pending(a) -> int:
    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = cal.load(LOGS)
    todo = [r for r in rows if r.get("record_type") == "quorum" and r.get("resolution") == "auto"
            and r.get("final_verdict") == "pass" and not r.get("alex_ack") and str(r.get("timestamp") or "") >= cut]
    for q in todo:
        v = next((s for s in q.get("seats") or [] if _role(s) == "voting"), {})
        row = next((r for r in rows if r.get("run_id") == v.get("run_id") and r.get("record_type") is None
                    and r.get("artifact") == q.get("artifact")), {})
        ds = sorted(row.get("defects") or [], key=lambda d: d.get("severity") != "major")
        top = (f"[{ds[0].get('severity')}] " + str(ds[0].get("description") or ds[0].get("issue")
                                                    or ds[0].get("location") or "")[:90]) if ds else "(no defects)"
        print(f"  {q['run_id']:<48} {q.get('artifact')}  {v.get('weighted_score')}  {top}")
    if todo:
        print(f"{len(todo)} un-acked clean pass(es). One answer for all:\n  python3 .claude/evals/judge.py ack "
              + " ".join(f"--run {q['run_id']}" for q in todo) + " agree")
    else:
        print(f"no un-acked clean passes in the last {a.days}d")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="build-quality judge: run / ack / pending")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    src = r.add_mutually_exclusive_group()
    src.add_argument("--artifact"); src.add_argument("--files", nargs="+"); src.add_argument("--range", dest="rng")
    src.add_argument("--resume", metavar="RUN_ID")
    r.add_argument("--sonnet-verdict"); r.add_argument("--artifact-type", default="skill")
    r.add_argument("--spec-file", action="append", default=[]); r.add_argument("--context", default="")
    r.add_argument("--mode", choices=["interactive", "autonomous"]); r.add_argument("--label", default="")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v6.md")
    r.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
    k = sub.add_parser("ack")
    k.add_argument("--run", action="append", required=True); k.add_argument("verdict", choices=["agree", "disagree"])
    k.add_argument("note", nargs="?", default="")
    p = sub.add_parser("pending"); p.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if a.cmd == "run":
        if not (a.resume or a.artifact or a.files or a.rng):
            ap.error("run needs one of --artifact, --files, --range, --resume")
        if not a.resume:
            a.mode = a.mode or "interactive"
        return run(a)
    return ack(a) if a.cmd == "ack" else pending(a)


if __name__ == "__main__":
    sys.exit(main())
