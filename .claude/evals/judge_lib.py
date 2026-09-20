#!/usr/bin/env python3
"""judge_lib.py: the parts of the build-quality judge that every seat must share (YED-209).

Why a library: with two seats the scoring math lived as jq inside gemini-judge.sh. With N seats, every seat has
to get the SAME evidence and be scored by the SAME arithmetic, or "agreement" between seats means nothing.
Spec: .claude/proposals/third-judge-seat-openai.md. This file owns:

  score()          the @5 composite + caps + verdict. Mirrors gemini-judge.sh's jq exactly (parity is tested).
  build_bundle()   ONE evidence bundle per run, identical for every seat, with a sha256 so a merge can prove it.
  verify_quotes()  a defect must quote the artifact verbatim; a fabricated quote is a format failure.
  privacy_guard()  nothing gitignored, outside the repo, or secret-looking is ever sent to a provider.
  ledger / caps    every paid API attempt is recorded; per-run, monthly and lifetime caps are enforced here.

Seats never compute their own composite or verdict. Seats never see each other's output: nothing here accepts one.
"""
from __future__ import annotations
import datetime, hashlib, json, os, re, subprocess

CRITERIA = ("correctness", "completeness", "convention_adherence", "anti_pattern_avoidance", "diagnostics")
WEIGHTS = {"correctness": 0.30, "completeness": 0.20, "convention_adherence": 0.20,
           "anti_pattern_avoidance": 0.20, "diagnostics": 0.10}
PASS_LINE = 0.70
BUNDLE_VERSION = 2
LEDGER = ".claude/evals/spend-ledger.jsonl"
PRICING = ".claude/evals/pricing.json"
SECRET_RE = re.compile(r"sk-[A-Za-z0-9_-]{20,}|ph[cxs]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|"
                       r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


class JudgeError(Exception):
    """exit 1: API or format failure."""


class PrivacyViolation(Exception):
    """exit 3: something that must never leave the machine was about to be sent."""


class BudgetExceeded(Exception):
    """exit 4: a spend cap was hit, or the model has no price on file."""


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- scoring (mirrors gemini-judge.sh, @5)
def score(verdict: dict, atype: str, has_dangling: bool) -> dict:
    """Per-criterion caps, weighted sum, composite caps, verdict. Caps only ever LOWER a score."""
    cs = verdict.get("criterion_scores")
    if not isinstance(cs, list) or sorted(c.get("id") for c in cs) != sorted(CRITERIA):
        raise JudgeError("verdict lacks exactly the 5 criteria")
    if not all(isinstance(c.get("score"), (int, float)) and not isinstance(c.get("score"), bool) for c in cs):
        raise JudgeError("a criterion score is missing or non-numeric")   # absent != worst-possible
    flags = verdict.get("cap_flags") or {}
    out = dict(verdict)
    out["flat_ceiling"] = all(c["score"] == 1 for c in cs)                 # on RAW scores, before any cap
    cs = [dict(c, score=min(1.0, max(0.0, float(c["score"])))) for c in cs]

    def cap(cid: str, mx: float, why: str) -> None:
        for c in cs:
            if c["id"] == cid and c["score"] > mx:
                c["score"] = mx
                c["reasoning"] = f'{c.get("reasoning", "")} [harness cap {mx}: {why}]'

    if flags.get("spec_drift"):
        cap("correctness", 0.70, "spec drift")
    if has_dangling:
        cap("completeness", 0.60, "check-refs: referenced file(s) missing")
    if atype == "command" and flags.get("command_skeleton_absent"):
        cap("completeness", 0.35, "command skeleton absent")
    s = {c["id"]: c["score"] for c in cs}
    raw = sum(s[k] * w for k, w in WEIGHTS.items())
    caps = [raw]
    if flags.get("confidence_honesty_violation"):
        caps.append(0.65)
    if atype == "deep_read" and flags.get("density_padding"):
        caps.append(0.65)
    if has_dangling:
        caps.append(0.60)
    out["criterion_scores"] = cs
    out["raw_score"] = round(raw * 1000) / 1000
    out["weighted_score"] = round(min(caps) * 1000) / 1000
    out["confidence_honesty_violation"] = bool(flags.get("confidence_honesty_violation"))
    out["verdict"] = "pass" if out["weighted_score"] >= PASS_LINE else "flag"
    out["scoring"] = "harness-recomputed"
    return out


# ---------------------------------------------------------------- quote verification (anti-fabrication)
def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip().lower()


def verify_quotes(defects: list, artifact_text: str) -> dict:
    """Each defect's `quote` must be a whitespace-normalized verbatim substring of the artifact.

    A seat that invents a flaw can't quote it. Returns counts; the caller tags the run `evidence_unverified`
    when more than 30% of quoted defects fail, which strips that seat's power to escalate for this run.
    """
    hay = _norm(artifact_text)
    quoted = [d for d in defects or [] if isinstance(d, dict) and _norm(str(d.get("quote") or ""))]
    bad = [d for d in quoted if _norm(str(d["quote"])) not in hay]
    n = len(quoted)
    return {"quoted": n, "unverified": len(bad), "unverified_rate": round(len(bad) / n, 3) if n else 0.0,
            "evidence_unverified": bool(n) and len(bad) / n > 0.30,
            "unverified_quotes": [str(d["quote"])[:120] for d in bad][:5]}


def must_cite_gaps(scored: dict) -> list[str]:
    """Any criterion under 0.85 needs a defect filed against it. Returns the criteria that break the rule."""
    have = {d.get("criterion") for d in scored.get("defects") or [] if isinstance(d, dict)}
    return [c["id"] for c in scored["criterion_scores"] if c["score"] < 0.85 and c["id"] not in have]


# ---------------------------------------------------------------- privacy guard
def privacy_guard(paths: list[str], texts: list[str]) -> None:
    """Refuse to send anything gitignored, outside the repo, or secret-looking. No override exists."""
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if not root:
        raise PrivacyViolation("not inside a git repo: cannot prove the file is safe to send")
    for p in paths:
        real = os.path.realpath(p)
        if os.path.islink(p) or not real.startswith(os.path.realpath(root) + os.sep):
            raise PrivacyViolation(f"{p}: a symlink, or outside this repo (private refs are symlinked in worktrees)")
        if subprocess.run(["git", "check-ignore", "-q", p]).returncode == 0:
            raise PrivacyViolation(f"{p}: gitignored, so private by policy (build-in-public.md)")
    for t in texts:
        m = SECRET_RE.search(t)
        if m:
            raise PrivacyViolation(f"secret-looking string in the evidence ({m.group(0)[:6]}…): nothing sent")


# ---------------------------------------------------------------- the evidence bundle
INSTRUCTIONS = """You are scoring ONE build artifact against the rubric above, following the judge system rules.
Work in this order, and the output schema enforces it:
1. checks_performed: list the concrete things you checked (e.g. "each numbered ADR decision vs the code", "every write path", "error handling on network calls").
2. defects: every defect you found, major or minor, each with location (the line number shown in the ARTIFACT CONTENT margin, plus function or section), criterion, severity, spec_ref (the numbered spec/ADR decision it contradicts, or ""), and description. Where the schema has a `quote` field, copy the offending text VERBATIM from that line (it is checked mechanically; a quote that is not in the artifact counts against you). Competent artifacts usually still have minor reviewer nits; list them.
3. criterion_scores: score each of the 5 criteria 0-1 INDEPENDENTLY using the rubric scale (1.0 = searched and found nothing of consequence; ~0.85 = passes with nits; 0.70 = pass line; below = send back). Reasoning must cite specific lines or sections. Any criterion you score below 0.85 must have at least one defect filed against it.
4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding).
Do NOT compute a composite score or a verdict; the harness does that.
House-context primer (for convention_adherence/anti_pattern_avoidance): project skills in .claude/skills/ take NO alex: prefix (that prefix is for alex-plugin skills only); subagents cannot spawn subagents (fan-out runs from the parent thread); MCP writes are parent-thread only; Supabase as the Market-Intelligence store is sanctioned (NOT an anti-pattern), Supabase as a measurement store is tombstoned. If you lack house context for a convention question, say so in the reasoning and score what you CAN verify; do not default to 1.0."""


def _rubric_version(rubric: str) -> str | None:
    m = re.search(r"build-quality@\d+", open(rubric, encoding="utf-8").read())
    return m.group(0) if m else None


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def build_bundle(artifact: str, atype: str, system: str, rubric: str, context: str = "",
                 spec_files: list[str] | None = None) -> dict:
    """Everything a seat is allowed to see, in one fixed order. Same bytes for every seat, or the merge refuses."""
    spec_files = spec_files or []
    art_text = open(artifact, encoding="utf-8").read()
    spec_blocks = [f"--- spec file: {p} ---\n{open(p, encoding='utf-8').read()}" for p in spec_files]
    ctx = "\n\n".join(x for x in [context.strip(), *spec_blocks] if x)
    privacy_guard([artifact, *spec_files], [art_text, ctx])
    dangling = _run([".claude/hooks/check-refs.sh", "--artifact", artifact])
    tombs = _run(["python3", ".claude/hooks/check-tombstones.py", "--artifact", artifact])
    density = ""
    if atype == "deep_read":
        d = _run([".claude/hooks/density-check.sh", "--artifact", artifact])
        density = next((l for l in d.splitlines() if re.match(r"density-check: (words|OK|PADDING-RISK|UNCITED-LONGFORM)", l)), "")
    numbered = "\n".join(f"{i:>5}| {l}" for i, l in enumerate(art_text.splitlines(), 1))
    text = (open(system, encoding="utf-8").read()
            + "\n\n===== RUBRIC (version is stated in the rubric text below) =====\n" + open(rubric, encoding="utf-8").read()
            + "\n\n===== ARTIFACT TYPE =====\n" + atype
            + "\n\n===== PER-ARTIFACT CONTEXT/SPEC =====\n" + (ctx or "(none supplied — score correctness/completeness against the artifact's own stated purpose; note reduced confidence)")
            + "\n\n===== VERIFIED-MISSING REFERENCES (deterministic file-existence check — treat as ground truth) =====\n"
            + (dangling + "\n→ per the rubric, a load-bearing reference that does not exist caps completeness ≤0.60 (the harness enforces it)." if dangling else "(none — all checked .claude/ references exist)")
            + "\n\n===== LIVE REFERENCES TO REMOVED TOOLS/DECISIONS (deterministic tombstone check — each hit is ground truth; the list is a LOWER BOUND, so still read the artifact; YOU judge whether each hit is load-bearing) =====\n"
            + (tombs + "\n→ a load-bearing step that relies on a removed tool is a correctness + anti_pattern_avoidance defect." if tombs else "(none)")
            + "\n\n===== DENSITY SIGNAL (deep_read only; a FLAG, not a verdict) =====\n" + (density or "(not a deep_read artifact — density cap N/A)")
            + "\n\n===== ARTIFACT PATH =====\n" + artifact
            + "\n\n===== ARTIFACT CONTENT (line numbers in the margin are NOT part of the file) =====\n" + numbered
            + "\n\n===== INSTRUCTIONS =====\n" + INSTRUCTIONS)
    return {"bundle_version": BUNDLE_VERSION, "text": text, "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "artifact": artifact, "artifact_sha256": sha256_file(artifact), "artifact_type": atype,
            "has_dangling": bool(dangling), "dangling_refs": dangling.splitlines(),
            "evidence_parity": len(ctx) >= 400,          # same bar gemini-judge.sh uses: a one-line context is not a spec
            "rubric_version": _rubric_version(rubric)}


# ---------------------------------------------------------------- spend ledger + caps
def _prices() -> dict:
    return json.load(open(PRICING, encoding="utf-8"))["models"]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = _prices().get(model)
    if not p:
        raise BudgetExceeded(f"{model} has no price in {PRICING}: refusing to spend blind")
    return round(input_tokens / 1e6 * p["input_per_mtok"] + output_tokens / 1e6 * p["output_per_mtok"], 6)


def spent(provider: str) -> tuple[float, float]:
    """(this calendar month UTC, lifetime) for one provider, from the ledger."""
    month, total, ym = 0.0, 0.0, now_utc()[:7]
    if os.path.exists(LEDGER):
        for line in open(LEDGER, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("provider") != provider:
                continue
            c = float(r.get("cost_usd") or 0)
            total += c
            if str(r.get("ts", ""))[:7] == ym:
                month += c
    return round(month, 6), round(total, 6)


def check_budget(provider: str, model: str, est_input_tokens: int, max_output_tokens: int) -> float:
    """Called BEFORE the request, with the worst case. Raises BudgetExceeded; returns the worst-case cost."""
    worst = cost_usd(model, est_input_tokens, max_output_tokens)
    per_run = float(os.environ.get("JUDGE_MAX_USD_PER_RUN", "0.50"))
    m_cap = float(os.environ.get("JUDGE_MONTHLY_CAP_USD", "8"))
    t_cap = float(os.environ.get("JUDGE_TOTAL_CAP_USD", "45"))
    month, total = spent(provider)
    if worst > per_run:
        raise BudgetExceeded(f"worst case ${worst:.3f} > per-run cap ${per_run:.2f} ({model})")
    if month + worst > m_cap:
        raise BudgetExceeded(f"month ${month:.2f} + ${worst:.3f} would pass the monthly cap ${m_cap:.2f}")
    if total + worst > t_cap:
        raise BudgetExceeded(f"lifetime ${total:.2f} + ${worst:.3f} would pass the lifetime cap ${t_cap:.2f}")
    return worst


def ledger_append(**row) -> None:
    """One row per paid API ATTEMPT, including failures (run-logs alone would miss those)."""
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_utc(), **row}) + "\n")


def append_log(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:                        # append: never clobber a same-day re-run
        f.write(json.dumps(row) + "\n")


def slug_for(artifact: str) -> str:
    b = os.path.basename(artifact)
    return os.path.basename(os.path.dirname(artifact)) if b == "SKILL.md" else os.path.splitext(b)[0]


def _cli() -> int:
    """judge_lib.py bundle --artifact P --artifact-type T [--context S] [--spec-file F ...] --out bundle.json"""
    import argparse, sys
    ap = argparse.ArgumentParser(description="build ONE evidence bundle for every judge seat")
    ap.add_argument("cmd", choices=["bundle"])
    ap.add_argument("--artifact", required=True); ap.add_argument("--artifact-type", default="skill")
    ap.add_argument("--context", default=""); ap.add_argument("--spec-file", action="append", default=[])
    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v5.md")
    ap.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        b = build_bundle(a.artifact, a.artifact_type, a.system, a.rubric, a.context, a.spec_file)
    except PrivacyViolation as e:
        print(f"PRIVACY GUARD (no bundle written): {e}", file=sys.stderr); return 3
    json.dump(b, open(a.out, "w", encoding="utf-8"))
    print(f"bundle {b['bundle_sha256'][:12]} · artifact {b['artifact_sha256'][:12]} · {len(b['text'])} chars · "
          f"evidence_parity={b['evidence_parity']} · dangling={len(b['dangling_refs'])} → {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
