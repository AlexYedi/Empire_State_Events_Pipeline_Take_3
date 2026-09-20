#!/usr/bin/env python3
"""openai_judge.py: the OpenAI seat of the build-quality judge (YED-209). Third seat, enters in SHADOW.

Same flags as gemini-judge.sh, plus --bundle (score a pre-built evidence bundle so every seat sees identical
bytes) and --dry-run (build + privacy guard + budget check, no network, free).

What makes this seat safe to add (spec: .claude/proposals/third-judge-seat-openai.md):
  * it never computes its own composite or verdict (judge_lib.score does, identically for every seat);
  * it never sees another seat's output (there is no input for one);
  * every defect must carry a verbatim quote, checked against the artifact (a made-up flaw can't be quoted);
  * a spend cap is checked BEFORE the request, and every attempt lands in the ledger, failures included;
  * the privacy guard refuses gitignored / out-of-repo / secret-looking evidence, with no override;
  * the key is read from .env and goes only into the HTTPS header: never argv, never a log, never stdout;
  * any failure exits non-zero. It never quietly degrades to "fewer seats".

Exit codes: 0 ok · 1 API/format failure · 2 usage · 3 privacy guard · 4 budget.
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evals"))
import judge_lib as jl  # noqa: E402

URL = "https://api.openai.com/v1/responses"
MAX_OUTPUT_TOKENS = 16000        # a ceiling, not a forecast: 10000 truncated 3 of 18 bake-off runs
BUDGET_OUTPUT_ESTIMATE = 9000    # what the PRE-CALL cap check assumes (observed use ~4-7k incl. reasoning).
# Using the 16000 ceiling here made gpt-5.5 look like a $0.52 run and blocked the arm entirely. The real
# protection is not this estimate: it is the monthly/lifetime caps, which are computed from ACTUAL ledger
# spend after each call, plus prepaid credit with auto-recharge off. This check only stops a wild overrun.
CRIT = list(jl.CRITERIA)
SCHEMA = {  # strict mode: every property required, no extras. Key order = the order the model must work in.
    "type": "object", "additionalProperties": False,
    "required": ["checks_performed", "defects", "criterion_scores", "cap_flags"],
    "properties": {
        "checks_performed": {"type": "array", "items": {"type": "string"}},
        "defects": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["line", "quote", "location", "criterion", "severity", "spec_ref", "description"],
            "properties": {"line": {"type": "integer"}, "quote": {"type": "string"}, "location": {"type": "string"},
                           "criterion": {"type": "string", "enum": CRIT},
                           "severity": {"type": "string", "enum": ["major", "minor"]},
                           "spec_ref": {"type": "string"}, "description": {"type": "string"}}}},
        "criterion_scores": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["id", "score", "reasoning"],
            "properties": {"id": {"type": "string", "enum": CRIT}, "score": {"type": "number"},
                           "reasoning": {"type": "string"}}}},
        "cap_flags": {"type": "object", "additionalProperties": False,
                      "required": ["confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding"],
                      "properties": {k: {"type": "boolean"} for k in
                                     ("confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding")}},
    },
}


def load_key() -> str:
    """OPENAI_API_KEY (standard) or OpenAI_KEY (as first saved), from the environment, else from .env."""
    for name in ("OPENAI_API_KEY", "OpenAI_KEY"):
        if os.environ.get(name):
            return os.environ[name].strip()
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            k, _, v = line.partition("=")
            if k.strip() in ("OPENAI_API_KEY", "OpenAI_KEY") and v.strip():
                return v.strip().strip("'\"")
    return ""


def call(key: str, body: dict) -> tuple[int, dict]:
    """POST with retries on 429/5xx/timeouts only. Never retries 400/401/403 (a retry can't fix those)."""
    data = json.dumps(body).encode()
    last: tuple[int, dict] = (0, {"error": {"message": "no attempt made"}})
    for attempt, wait in enumerate((0, 5, 20)):
        if wait:
            time.sleep(wait)
        req = urllib.request.Request(URL, data=data, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
            except ValueError:
                payload = {"error": {"message": f"HTTP {e.code} (non-JSON body)"}}
            last = (e.code, payload)
            if e.code not in (429, 500, 502, 503, 504):
                return last
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = (0, {"error": {"message": f"network: {type(e).__name__}"}})
    return last


def output_text(resp: dict) -> str:
    """The Responses API returns a list of output items; the JSON lives in the message's output_text part."""
    for item in resp.get("output") or []:
        if item.get("type") == "message":
            for part in item.get("content") or []:
                if part.get("type") == "refusal":
                    raise jl.JudgeError(f"model refused: {str(part.get('refusal'))[:200]}")
                if part.get("type") == "output_text":
                    return part.get("text") or ""
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="OpenAI seat of the build-quality judge")
    ap.add_argument("--artifact"); ap.add_argument("--artifact-type", default="skill")
    ap.add_argument("--calibration-set", default="prospective"); ap.add_argument("--context", default="")
    ap.add_argument("--spec-file", action="append", default=[])
    ap.add_argument("--model", default=None); ap.add_argument("--reasoning-effort", default=None)
    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v5.md")
    ap.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
    ap.add_argument("--label", default=""); ap.add_argument("--bundle", default="")
    ap.add_argument("--artifact-blob", default="", help="git blob sha proving this file is repo history (controls)")
    ap.add_argument("--seat-status", default=None, help="override for the log; default comes from seats.json")
    ap.add_argument("--print-only", action="store_true", help="make the call, print the verdict, write no run-log")
    ap.add_argument("--dry-run", action="store_true", help="build + guard + budget only; no network, no spend")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

    seat = next((s for s in json.load(open(".claude/evals/seats.json"))["seats"] if s["id"] == "openai"), {})
    model = a.model or seat.get("model") or "gpt-5.4"
    effort = a.reasoning_effort or seat.get("reasoning_effort") or "medium"
    status = a.seat_status or seat.get("status") or "shadow"

    try:
        if a.bundle:
            bundle = json.load(open(a.bundle, encoding="utf-8"))
            blob = a.artifact_blob or bundle.get("artifact_blob")
            jl.privacy_guard([bundle["artifact"]], [bundle["text"]],        # guard again: a bundle is just a file
                             {bundle["artifact"]: blob} if blob else None)
        else:
            if not a.artifact or not os.path.isfile(a.artifact):
                print(f"ERROR: --artifact missing/unreadable: {a.artifact}", file=sys.stderr); return 2
            bundle = jl.build_bundle(a.artifact, a.artifact_type, a.system, a.rubric, a.context, a.spec_file,
                                     artifact_blob=a.artifact_blob or None)
        est_in = len(bundle["text"]) // 3 + 600                              # deliberately high (chars/3, not /4)
        worst = jl.check_budget("openai", model, est_in, BUDGET_OUTPUT_ESTIMATE)
    except jl.PrivacyViolation as e:
        print(f"PRIVACY GUARD (nothing sent): {e}", file=sys.stderr); return 3
    except jl.BudgetExceeded as e:
        print(f"BUDGET (nothing sent): {e}", file=sys.stderr); return 4

    art, atype = bundle["artifact"], bundle["artifact_type"]
    if a.dry_run:
        m, t = jl.spent("openai")
        print(f"dry-run ok · {model}/{effort} · bundle {bundle['bundle_sha256'][:12]} · ~{est_in} input tok · "
              f"est ${worst:.3f} · spent ${m:.2f} this month, ${t:.2f} lifetime · nothing sent")
        return 0

    key = load_key()
    if not key:
        print("ERROR: no OPENAI_API_KEY (or OpenAI_KEY) in the environment or .env", file=sys.stderr); return 2

    body = {"model": model, "input": bundle["text"], "store": False, "max_output_tokens": MAX_OUTPUT_TOKENS,
            "reasoning": {"effort": effort},
            "text": {"format": {"type": "json_schema", "name": "judge_verdict", "strict": True, "schema": SCHEMA}}}
    code, resp = call(key, body)
    usage = resp.get("usage") or {}
    tin, tout = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
    cost = jl.cost_usd(model, tin, tout) if (tin or tout) else 0.0
    base = {"provider": "openai", "model": model, "artifact": art, "http": code, "input_tokens": tin,
            "output_tokens": tout, "cost_usd": cost, "calibration_set": a.calibration_set, "print_only": a.print_only}

    def fail(msg: str) -> int:
        jl.ledger_append(**base, ok=False, error=msg[:200])
        dump = os.path.join(os.environ.get("TMPDIR", "/tmp"), "openai-judge-last-failure.json")
        json.dump(resp, open(dump, "w"))                                     # the response body; never the request
        print(f"ERROR: {msg} · full response: {dump}", file=sys.stderr)
        return 1

    if code != 200:
        return fail(f"OpenAI HTTP {code}: {str((resp.get('error') or {}).get('message'))[:200]}")
    if resp.get("status") != "completed":
        return fail(f"status={resp.get('status')} reason={(resp.get('incomplete_details') or {}).get('reason')}")
    try:
        verdict = json.loads(output_text(resp) or "null")
        if not isinstance(verdict, dict):
            raise jl.JudgeError("no JSON verdict in the response")
        scored = jl.score(verdict, atype, bundle["has_dangling"])
    except (ValueError, jl.JudgeError) as e:
        return fail(f"malformed verdict: {e}")

    art_text = open(art, encoding="utf-8").read()
    qv = jl.verify_quotes(scored.get("defects") or [], art_text)
    gaps = jl.must_cite_gaps(scored)
    jl.ledger_append(**base, ok=True)

    resolved = resp.get("model") or model
    print(f"== OpenAI judge ({resolved}, effort {effort}, seat {status}) — {art} =>  {scored['weighted_score']} "
          f"({scored['verdict']})  [set:{a.calibration_set}]  ${cost:.4f}")
    nd = scored.get("defects") or []
    print(f"  defects: {len(nd)} ({sum(d.get('severity') == 'major' for d in nd)} major) · checks: "
          f"{len(scored.get('checks_performed') or [])} · raw {scored['raw_score']} → capped {scored['weighted_score']}")
    for d in nd:
        print(f"    - [{d.get('severity')}/{d.get('criterion')}] L{d.get('line')}: {str(d.get('description'))[:160]}")
    if scored["flat_ceiling"]:
        print("  ⚠️  FLAT CEILING: all five criteria 1.0 — low-information.", file=sys.stderr)
    if qv["evidence_unverified"]:
        print(f"  ⚠️  EVIDENCE UNVERIFIED: {qv['unverified']}/{qv['quoted']} quotes are not in the artifact.", file=sys.stderr)
    if gaps:
        print(f"  ⚠️  MUST-CITE: scored <0.85 with no defect filed against: {', '.join(gaps)}", file=sys.stderr)
    if a.print_only:
        return 0

    slug = jl.slug_for(art)
    rid = a.label or f"openai-{slug}"
    out = f".claude/evals/logs/{jl.now_utc()[:10]}-{slug}-{rid}.jsonl"
    jl.append_log(out, {
        "run_id": rid, "timestamp": jl.now_utc(), "artifact": art, "artifact_sha256": bundle["artifact_sha256"],
        "artifact_type": atype, "rubric": bundle.get("rubric_version"), "judge_model": f"openai:{model}",
        "judge_model_resolved": resolved, "judge_provider": "openai", "reasoning_effort": effort, "seat_status": status,
        "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession"),
        "criterion_scores": scored["criterion_scores"], "weighted_score": scored["weighted_score"],
        "raw_score": scored["raw_score"], "verdict": scored["verdict"], "alex_ack": None,
        "confidence_honesty_violation": scored["confidence_honesty_violation"], "defects": nd,
        "checks_performed": scored.get("checks_performed") or [], "cap_flags": scored.get("cap_flags") or {},
        "flat_ceiling": scored["flat_ceiling"], "scoring": "harness-recomputed", "quote_check": qv,
        "must_cite_gaps": gaps, "dangling_refs": bundle["dangling_refs"], "calibration_set": a.calibration_set,
        "evidence_parity": bundle["evidence_parity"], "bundle_sha256": bundle["bundle_sha256"],
        "bundle_version": bundle["bundle_version"], "artifact_blob": bundle.get("artifact_blob"),
        "usage": usage, "cost_usd": cost})
    print(f"  logged → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
