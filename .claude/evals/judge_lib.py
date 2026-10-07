#!/usr/bin/env python3
"""judge_lib.py: the build-quality judge's shared mechanics (YED-209; right-sized by YED-231, 2026-09-28).

One reviewer (Claude Sonnet, dispatched from the parent thread) scores a bundle; everything around the model's
judgement is deterministic and lives here. Entry point: judge.py. Design: .claude/references/judge.md.

  score()          the build-quality@6 composite + caps + score verdict. The model never computes these.
  finalize()       the run's final pass/flag and the reasons for a flag (score, guarded path, privacy flag,
                   flat ceiling, fabricated quotes). Alex is prompted only on a flag.
  guarded_paths()  the deterministic privacy rule: a bundle touching a guard/filter/allowlist file needs human
                   review, whatever the score (replaces the @6 privacy score cap, YED-231 item 7).
  build_bundle()   ONE evidence bundle per run: one file (--artifact), a file list (--files) or a git range
                   (--range), bundle_version 3.
  verify_quotes()  a defect must quote the bundle verbatim (any file, spec or context in it).
  privacy_guard()  nothing gitignored, outside the repo, or secret-looking is ever put in a bundle.
"""
from __future__ import annotations
import datetime, hashlib, json, os, re, subprocess

CRITERIA = ("correctness", "completeness", "convention_adherence", "anti_pattern_avoidance", "diagnostics")
WEIGHTS = {"correctness": 0.30, "completeness": 0.20, "convention_adherence": 0.20,
           "anti_pattern_avoidance": 0.20, "diagnostics": 0.10}
PASS_LINE = 0.70
BUNDLE_VERSION = 3
# multi-file bundles (YED-231 §4.1): telemetry/log paths never belong in a judged range
RANGE_EXCLUDE_PREFIXES = (".claude/evals/logs/", ".claude/.state/")
FULL_TEXT_LIMIT = 60_000     # above this many chars of full-file text, big files are sent as changed hunks
HUNK_MIN_LINES = 400         # ...but only files longer than this; smaller files always go in whole
HUNK_CONTEXT = 40            # ±lines around each change in hunk mode
SECRET_RE = re.compile(r"sk-[A-Za-z0-9_-]{20,}|ph[cxs]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|"
                       r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


class JudgeError(Exception):
    """exit 1: API or format failure."""


class PrivacyViolation(Exception):
    """exit 3: something that must never leave the machine was about to be sent."""


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------- scoring (build-quality@6, frozen)
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
    out["privacy_layer_defect"] = bool(flags.get("privacy_layer_defect"))
    out["verdict"] = "pass" if out["weighted_score"] >= PASS_LINE else "flag"
    out["scoring"] = "harness-recomputed"
    return out


# ---------------------------------------------------------------- quote verification (anti-fabrication)
def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip().lower()


# Formatting a seat routinely drops or re-renders when it quotes PROSE: markdown `**`, backticks, a `*` at a word
# boundary, and a dash<->colon swap. (YED-223, 2026-09-27: a Sonnet seat quoted `**One exception — …:**` without
# the asterisks and another rendered an em-dash as a colon; the strict check called both fabricated, dropped the
# only voting seat, forced a false FLAG on a skill file.)
#
# PROSE ONLY. In code every one of those characters is syntax: stripping `_`/`__` turned `hay_loose`, `_private`
# and `__init__` into matchable fabrications, folding `--` let `--bundle` vouch for `: bundle`, and stripping `*`
# collapses `*args`. Judge rounds 1-2 reproduced each. So code-like artifacts are matched strictly (whitespace
# and case only) and `_` is never touched in any mode. Residual (recorded): in prose, a quote that differs only
# by the dash<->colon swap or dropped `**`/backticks/boundary `*` verifies.
PROSE_TYPES = frozenset({"skill", "command", "ref", "dossier", "deep_read"})
_MD_RE = re.compile(r"\*\*|`|(?<![A-Za-z0-9])\*|\*(?![A-Za-z0-9])")
_DASH_RE = re.compile(r"\s*(?:—|–|:)\s*|\s+-\s+")


def _norm_loose(t: str) -> str:
    return _norm(_DASH_RE.sub(" ~ ", _MD_RE.sub("", t)))


def _as_haystack(hay) -> list[tuple[str, str]]:
    """str -> one unnamed source; a list of (label, text) pairs or {label, text} dicts passes through."""
    if isinstance(hay, str):
        return [("artifact", hay)]
    out = []
    for h in hay or []:
        if isinstance(h, dict):
            out.append((str(h.get("label") or "?"), str(h.get("text") or "")))
        else:
            out.append((str(h[0]), str(h[1])))
    return out


def verify_quotes(defects: list, haystack, artifact_type: str | None = None) -> dict:
    """Each defect's `quote` must appear somewhere in the evidence the reviewer was given. Always modulo whitespace and
    case. For PROSE artifact types (PROSE_TYPES) also modulo dropped markdown `**` / backticks / boundary `*` and
    the em/en-dash / spaced-hyphen / colon swap; code-like types (and an unknown type) are matched strictly. See
    the comment above _MD_RE for why, and for the one recorded residual.

    `haystack` is the artifact text (a str, the single-file case) or a list of (label, text) sources: every file in
    the bundle, every spec file and the context (YED-231 §4.2). Quoting the spec decision you say is contradicted is
    REQUIRED by judge-system-v2 rule 4, so it has to verify; on 09-27 a one-file haystack stripped three correct
    quotes as "fabricated" and forced a false flag. `matched_in` is aligned with the INPUT `defects`
    list: the label of the first source that holds the quote, or None (unquoted or unmatched).

    `unverified` / `evidence_unverified` use the mode's match; `unverified_exact` keeps the strict count so drift
    in how the reviewer quotes stays visible. More than 30% unverified quotes = `evidence_unverified`, which
    finalize() turns into a flag: a review built on quotes that are not in the evidence cannot pass.
    """
    tolerant = artifact_type in PROSE_TYPES
    norm = _norm_loose if tolerant else _norm
    srcs = _as_haystack(haystack)
    hay = [(lbl, _norm(t), norm(t)) for lbl, t in srcs]
    matched_in, n, bad, bad_exact = [], 0, [], 0
    for d in defects or []:
        q = str(d.get("quote") or "") if isinstance(d, dict) else ""
        if not _norm(q):
            matched_in.append(None)
            continue
        n += 1
        qm, qe = norm(q), _norm(q)
        where = next((lbl for lbl, _, hm in hay if qm in hm), None)
        matched_in.append(where)
        if where is None:
            bad.append(q)
        if not any(qe in he for _, he, _ in hay):
            bad_exact += 1
    return {"quoted": n, "unverified": len(bad), "unverified_rate": round(len(bad) / n, 3) if n else 0.0,
            "evidence_unverified": bool(n) and len(bad) / n > 0.30,
            "unverified_quotes": [q[:120] for q in bad][:5], "matched_in": matched_in,
            "unverified_exact": bad_exact, "match": "prose-tolerant" if tolerant else "strict"}


def bundle_haystack(bundle: dict) -> list[tuple[str, str]]:
    """The quote haystack for a loaded bundle: its recorded `sources` (v3), else the artifact file (v2 bundles)."""
    if bundle.get("sources"):
        return _as_haystack(bundle["sources"])
    return [(bundle["artifact"], open(bundle["artifact"], encoding="utf-8").read())]


def must_cite_gaps(scored: dict) -> list[str]:
    """Any criterion under 0.85 needs a defect filed against it. Returns the criteria that break the rule."""
    have = {d.get("criterion") for d in scored.get("defects") or [] if isinstance(d, dict)}
    return [c["id"] for c in scored["criterion_scores"] if c["score"] < 0.85 and c["id"] not in have]


# ---------------------------------------------------------------- deterministic routing rules (YED-231)
# Guarded paths: the spine write path and the privacy filters. A bundle that touches one needs HUMAN review whatever
# the score (YED-231 item 7: the @6 privacy cap moved from a model flag to this path check). Match is on the repo
# path; the pattern catches future guard/filter/allowlist files by name. Widen it in a PR, never per run.
GUARDED_FILES = (".claude/scripts/spine_client.py", ".claude/scripts/inbox_boundary.py", ".gitignore")
GUARDED_NAME_RE = re.compile(r"guard|filter|allow-?list|deny-?list|boundary|privacy|redact|pii", re.I)
# The judge layer is never judged by itself (YED-231 item 5): judge.py refuses these as a target and drops them
# from a range. Telemetry is excluded separately (RANGE_EXCLUDE_PREFIXES).
JUDGE_LAYER = (".claude/evals/judge_lib.py", ".claude/evals/judge.py", ".claude/evals/calibration_stats.py",
               ".claude/evals/controls.py", ".claude/evals/controls/", ".claude/evals/rubrics/", ".claude/evals/prompts/",
               ".claude/evals/test_judge_lib.py", ".claude/evals/test_bundle_multifile.py",
               ".claude/evals/test_null_baseline.py", ".claude/evals/test_judge_e2e.py", ".claude/evals/README.md", ".claude/hooks/seat-log.py",
               ".claude/skills/judge-build/", ".claude/commands/judge-build.md", ".claude/references/judge.md")


def guarded_paths(paths: list[str]) -> list[str]:
    return sorted(p for p in paths if p in GUARDED_FILES or GUARDED_NAME_RE.search(os.path.basename(p)))


def is_judge_layer(path: str) -> bool:
    p = os.path.normpath(path).replace(os.sep, "/")
    return any(p == j or (j.endswith("/") and p.startswith(j)) for j in JUDGE_LAYER)


def finalize(row: dict, bundle: dict | None = None) -> dict:
    """The run's final verdict. Pass only if nothing below fires; every reason is shown to Alex with the flag.
    No calibration number enters here: this is score + deterministic rules, nothing learned."""
    reasons = []
    if row.get("verdict") != "pass":
        reasons.append(f"score {row.get('weighted_score')} < {PASS_LINE}")
    if row.get("privacy_layer_defect") or (row.get("cap_flags") or {}).get("privacy_layer_defect"):
        reasons.append("privacy_layer_defect (reviewer confirmed a defect in a privacy/security layer)")
    paths = [f["path"] for f in (bundle or {}).get("files") or [] if f.get("path")] or [row.get("artifact", "")]
    for g in guarded_paths(paths):
        reasons.append(f"guarded_path:{g} (human review required)")
    if row.get("flat_ceiling"):
        reasons.append("flat_ceiling (1.0 on all five criteria is low-information)")
    if (row.get("quote_check") or {}).get("evidence_unverified"):
        reasons.append("evidence_unverified (>30% of quoted defects are not in the bundle)")
    return {"final_verdict": "flag" if reasons else "pass", "flag_reasons": reasons}


# ---------------------------------------------------------------- privacy guard
def privacy_guard(paths: list[str], texts: list[str], verified_blobs: dict[str, str] | None = None) -> None:
    """Refuse to send anything gitignored, outside the repo, or secret-looking.

    `verified_blobs` maps a path to a git blob sha and is NOT an override: the file's bytes must be byte-identical
    to `git cat-file blob <sha>` in THIS repo. That is proof the content is already in the public history, which is
    exactly what the in-repo check is trying to establish, so a control materialised to a temp dir can be judged
    without punching a hole in the guard. If the bytes differ, the path is refused like any other. The secret scan
    always runs, on every text, verified or not.
    """
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if not root:
        raise PrivacyViolation("not inside a git repo: cannot prove the file is safe to send")
    verified_blobs = verified_blobs or {}
    for p in paths:
        want = verified_blobs.get(p)
        if want:
            blob = subprocess.run(["git", "cat-file", "blob", want], capture_output=True).stdout
            if blob and open(p, "rb").read() == blob:
                continue                      # provably this repo's own committed content
            raise PrivacyViolation(f"{p}: claimed git blob {want[:12]} does not match the file's bytes")
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
4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding), privacy_layer_defect (you CONFIRMED a correctness defect in ANY layer of a privacy/security/access-control mechanism - a filter, guard, redaction, permission check, secret handling, allow/deny list - even if another layer or backstop would catch it; a backstop never excuses a broken layer; NOT for hardening suggestions or logging gaps in a correct layer).
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


def _git(args: list[str], check: bool = True) -> bytes:
    r = subprocess.run(["git", *args], capture_output=True, timeout=60)
    if check and r.returncode:
        raise ValueError(f"git {' '.join(args)}: {r.stderr.decode(errors='replace').strip()[:200]}")
    return r.stdout


def _numbered(lines: list[tuple[int | None, str]]) -> str:
    return "\n".join(f"{i:>5}| {l}" if i is not None else "  ...| (unchanged lines omitted)" for i, l in lines)


def _hunk_lines(base: str, head: str, path: str) -> list[tuple[int | None, str]]:
    """The NEW side of each changed hunk (±HUNK_CONTEXT lines), with its real line numbers in the file at `head`."""
    out: list[tuple[int | None, str]] = []
    ln = 0
    for l in _git(["diff", f"-U{HUNK_CONTEXT}", "--no-color", "--no-renames", base, head, "--", path]
                  ).decode("utf-8", errors="replace").splitlines():
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", l)
        if m:
            if out:
                out.append((None, ""))
            ln = int(m.group(1))
            continue
        if not ln or l.startswith("\\"):
            continue                       # file header lines before the first hunk, or "\ No newline"
        if l.startswith("-"):
            continue                       # removed line: not in the file at head (it is in WHAT CHANGED)
        out.append((ln, l[1:]))
        ln += 1
    return out


def _diff_old_side(diff: str) -> str:
    out, in_hunk = [], False
    for l in diff.splitlines():
        if l.startswith("diff --git"):
            in_hunk = False
        elif l.startswith("@@"):
            in_hunk = True
        elif in_hunk and l[:1] in (" ", "-"):
            out.append(l[1:])
    return "\n".join(out)


def _range_files(rng: str, skip_judge_layer: bool = False) -> tuple[str, str, list[str]]:
    """BASE..HEAD (or A...B = merge-base(A,B)..B) -> (base sha, head sha, changed paths minus telemetry)."""
    if "..." in rng:
        a_, b_ = rng.split("...", 1)
        base = _git(["merge-base", a_, b_]).decode().strip()
        head_ref = b_
    elif ".." in rng:
        base, head_ref = rng.split("..", 1)
    else:
        raise ValueError(f"--range must be BASE..HEAD, got {rng!r}")
    base = _git(["rev-parse", "--verify", f"{base}^{{commit}}"]).decode().strip()
    head = _git(["rev-parse", "--verify", f"{head_ref or 'HEAD'}^{{commit}}"]).decode().strip()
    names = _git(["diff", "--name-only", "--no-renames", base, head]).decode().splitlines()
    keep = [p for p in names if p and not p.startswith(RANGE_EXCLUDE_PREFIXES)
            and not (p.startswith(".claude/artifacts/") and p.endswith(".jsonl"))
            and not (skip_judge_layer and is_judge_layer(p))]
    return base, head, keep


def _range_guard(head: str, paths: list[str]) -> None:
    """Privacy for committed content: a symlink in the tree, or a path the ignore rules cover (force-added private
    file), is refused exactly like privacy_guard refuses it on disk. The secret scan runs later on every text."""
    for p in paths:
        mode = _git(["ls-tree", head, "--", p]).decode().split(" ", 1)[0]
        if mode == "120000":
            raise PrivacyViolation(f"{p}: a symlink in {head[:7]} (private refs are symlinked in worktrees)")
        if subprocess.run(["git", "check-ignore", "--no-index", "-q", p]).returncode == 0:
            raise PrivacyViolation(f"{p}: matches the ignore rules, so private by policy even though it was committed")


def guard_bundle(bundle: dict, artifact_blob: str | None = None) -> None:
    """Re-run the privacy guard on a LOADED bundle (a bundle is just a file on disk; an adapter re-checks it)."""
    files = [f for f in bundle.get("files") or [] if f.get("sha256")]
    if bundle.get("range"):
        _range_guard(bundle["range"]["head"], [f["path"] for f in files])
        privacy_guard([], [bundle["text"]])
    elif bundle.get("bundle_kind") == "files":
        privacy_guard([f["path"] for f in files], [bundle["text"]])
    else:
        blob = artifact_blob or bundle.get("artifact_blob")
        privacy_guard([bundle["artifact"]], [bundle["text"]], {bundle["artifact"]: blob} if blob else None)


def _prepasses(path: str, atype: str) -> tuple[list[str], list[str], str]:
    dangling = _run([".claude/hooks/check-refs.sh", "--artifact", path])
    tombs = _run(["python3", ".claude/hooks/check-tombstones.py", "--artifact", path])
    density = ""
    if atype == "deep_read":
        d = _run([".claude/hooks/density-check.sh", "--artifact", path])
        density = next((l for l in d.splitlines() if re.match(r"density-check: (words|OK|PADDING-RISK|UNCITED-LONGFORM)", l)), "")
    return [l for l in dangling.splitlines() if l], [l for l in tombs.splitlines() if l], density


def build_bundle(artifact: str | None, atype: str, system: str, rubric: str, context: str = "",
                 spec_files: list[str] | None = None, artifact_blob: str | None = None,
                 files: list[str] | None = None, rng: str | None = None, skip_judge_layer: bool = False) -> dict:
    """Everything the reviewer is allowed to see, in one fixed order, hashed so the run log can prove it.

    Exactly one of `artifact` (one file, the pre-v3 shape, byte-identical text), `files` (several files on disk) or
    `rng` (BASE..HEAD: the changed files at HEAD, telemetry excluded, plus the unified diff) names the evidence.
    """
    if sum(bool(x) for x in (artifact, files, rng)) != 1:
        raise ValueError("give exactly one of --artifact, --files, --range")
    if artifact:
        return _single_bundle(artifact, atype, system, rubric, context, spec_files or [], artifact_blob)
    spec_files = spec_files or []
    spec_texts = [(p, open(p, encoding="utf-8").read()) for p in spec_files]
    spec_blocks = [f"--- spec file: {p} ---\n{t}" for p, t in spec_texts]
    ctx = "\n\n".join(x for x in [context.strip(), *spec_blocks] if x)
    base = head = None
    entries: list[dict] = []            # {path, text (None if deleted), disk (path the pre-passes read)}
    if rng:
        base, head, paths = _range_files(rng, skip_judge_layer)
        if not paths:
            raise ValueError(f"range {rng} changes no judgeable file (telemetry{' and judge-layer' if skip_judge_layer else ''} "
                             "paths are excluded)")
        _range_guard(head, paths)
        privacy_guard(spec_files, [])
        for p in paths:
            present = subprocess.run(["git", "cat-file", "-e", f"{head}:{p}"], capture_output=True).returncode == 0
            entries.append({"path": p, "text": _git(["show", f"{head}:{p}"]).decode("utf-8", errors="replace")
                            if present else None})
    else:
        missing = [p for p in files if not os.path.isfile(p)]
        if missing:
            raise ValueError(f"--files: not a file: {', '.join(missing)}")
        privacy_guard([*files, *spec_files], [])
        entries = [{"path": p, "text": open(p, encoding="utf-8").read()} for p in files]
    privacy_guard([], [e["text"] for e in entries if e["text"]] + [ctx])      # secret scan, every text

    full_chars = sum(len(e["text"]) for e in entries if e["text"])
    mode = "hunks" if rng and full_chars > FULL_TEXT_LIMIT else "full"
    dangling, tombs, density = [], [], []
    blocks, sources, meta = [], [], []
    import tempfile
    with tempfile.TemporaryDirectory(prefix="judge-bundle-") as tmp:
        for e in entries:
            p, t = e["path"], e["text"]
            if t is None:
                blocks.append(f"===== FILE: {p} (DELETED in this range; see WHAT CHANGED) =====")
                meta.append({"path": p, "sha256": None, "lines": 0, "mode": "deleted"})
                continue
            disk = p
            if rng and not (os.path.isfile(p) and open(p, "rb").read() == t.encode("utf-8")):
                disk = os.path.join(tmp, p)             # the pre-passes read the content AT HEAD, not the worktree
                os.makedirs(os.path.dirname(disk), exist_ok=True)
                open(disk, "w", encoding="utf-8").write(t)
            dg, tb, dn = _prepasses(disk, atype)
            dangling += dg
            tombs += [x.replace(disk, p, 1) for x in tb]
            if dn:
                density.append(f"{p}: {dn}")
            lines = t.splitlines()
            sha = hashlib.sha256(t.encode("utf-8")).hexdigest()
            if mode == "hunks" and len(lines) > HUNK_MIN_LINES:
                hl = _hunk_lines(base, head, p)
                blocks.append(f"===== FILE: {p} ({len(lines)} lines; ONLY the changed hunks ±{HUNK_CONTEXT} lines are "
                              f"shown, bundle_mode: hunks — do not assume anything about the omitted lines) =====\n"
                              + _numbered(hl))
                sources.append({"label": p, "text": "\n".join(l for i, l in hl if i is not None)})
                meta.append({"path": p, "sha256": sha, "lines": len(lines), "mode": "hunks"})
            else:
                blocks.append(f"===== FILE: {p} ({len(lines)} lines) =====\n" + _numbered(list(enumerate(lines, 1))))
                sources.append({"label": p, "text": t})
                meta.append({"path": p, "sha256": sha, "lines": len(lines), "mode": "full"})
    diff = ""
    if rng:
        diff = _git(["diff", "--no-color", "--no-renames", base, head, "--", *[e["path"] for e in entries]]
                    ).decode("utf-8", errors="replace")
    sources += [{"label": p, "text": t} for p, t in spec_texts]
    if context.strip():
        sources.append({"label": "context", "text": context})
    if diff:
        sources.append({"label": "diff", "text": diff})
        # the diff's OLD side without the +/- margin: a reviewer quoting a line this range removed (it is on screen, in
        # WHAT CHANGED) must verify. The 09-27 deep-read-gate run lost its vote partly over exactly such a quote.
        sources.append({"label": "diff (removed side)", "text": _diff_old_side(diff)})
    dangling = sorted(set(dangling))
    art_sha = hashlib.sha256("\n".join(f"{m['path']}\t{m['sha256'] or 'deleted'}"
                                       for m in sorted(meta, key=lambda m: m["path"])).encode()).hexdigest()
    art_id = f"range:{base[:7]}..{head[:7]}" if rng else f"files:{len(meta)}@{art_sha[:12]}"
    text = (open(system, encoding="utf-8").read()
            + "\n\n===== RUBRIC (version is stated in the rubric text below) =====\n" + open(rubric, encoding="utf-8").read()
            + "\n\n===== ARTIFACT TYPE =====\n" + atype
            + "\n\n===== PER-ARTIFACT CONTEXT/SPEC =====\n" + (ctx or "(none supplied — score correctness/completeness against the artifact's own stated purpose; note reduced confidence)")
            + "\n\n===== VERIFIED-MISSING REFERENCES (deterministic file-existence check, run per file — treat as ground truth) =====\n"
            + ("\n".join(dangling) + "\n→ per the rubric, a load-bearing reference that does not exist caps completeness ≤0.60 (the harness enforces it)." if dangling else "(none — all checked .claude/ references exist)")
            + "\n\n===== LIVE REFERENCES TO REMOVED TOOLS/DECISIONS (deterministic tombstone check, run per file — each hit is ground truth; the list is a LOWER BOUND, so still read the files; YOU judge whether each hit is load-bearing) =====\n"
            + ("\n".join(tombs) + "\n→ a load-bearing step that relies on a removed tool is a correctness + anti_pattern_avoidance defect." if tombs else "(none)")
            + "\n\n===== DENSITY SIGNAL (deep_read only; a FLAG, not a verdict) =====\n" + ("\n".join(density) or "(not a deep_read artifact — density cap N/A)")
            + "\n\n===== ARTIFACT (multi-file bundle) =====\n" + f"{art_id} · {len(meta)} file(s) · bundle_mode: {mode}\n"
            + "\n".join(f"  {m['path']}  ({m['mode']}, {m['lines']} lines)" for m in meta)
            + ("\n\n===== WHAT CHANGED (unified diff " + f"{base[:7]}..{head[:7]}" + ") =====\n" + diff if diff else "")
            + "\n\n===== ARTIFACT FILES (line numbers in the margin are NOT part of the files) =====\n" + "\n\n".join(blocks)
            + "\n\n===== INSTRUCTIONS =====\n" + INSTRUCTIONS + MULTI_FILE_NOTE)
    return {"artifact_blob": None, "bundle_version": BUNDLE_VERSION, "bundle_kind": "range" if rng else "files",
            "bundle_mode": mode, "text": text, "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "artifact": art_id, "artifact_sha256": art_sha, "artifact_type": atype, "files": meta,
            "range": {"base": base, "head": head} if rng else None, "sources": sources,
            "has_dangling": bool(dangling), "dangling_refs": dangling,
            "evidence_parity": len(ctx) >= 400, "rubric_version": _rubric_version(rubric)}


MULTI_FILE_NOTE = """
Multi-file bundle: every defect's `location`/`line` refers to one file; set the defect's `file` field (where the schema has one, else name it in `location`) to the path in that file's ===== FILE header. Quotes are checked against every file, spec file and the context in this bundle."""


def _single_bundle(artifact: str, atype: str, system: str, rubric: str, context: str,
                   spec_files: list[str], artifact_blob: str | None) -> dict:
    """The one-file bundle. Its TEXT is byte-identical to bundle_version 2; only the quote haystack grew (§4.2)."""
    art_text = open(artifact, encoding="utf-8").read()
    spec_texts = [(p, open(p, encoding="utf-8").read()) for p in spec_files]
    spec_blocks = [f"--- spec file: {p} ---\n{t}" for p, t in spec_texts]
    ctx = "\n\n".join(x for x in [context.strip(), *spec_blocks] if x)
    privacy_guard([artifact, *spec_files], [art_text, ctx],
                  {artifact: artifact_blob} if artifact_blob else None)
    dangling_l, tombs_l, density = _prepasses(artifact, atype)
    dangling, tombs = "\n".join(dangling_l), "\n".join(tombs_l)
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
    sources = [{"label": artifact, "text": art_text}, *({"label": p, "text": t} for p, t in spec_texts)]
    if context.strip():
        sources.append({"label": "context", "text": context})
    sha = sha256_file(artifact)
    return {"artifact_blob": artifact_blob, "bundle_version": BUNDLE_VERSION, "bundle_kind": "artifact",
            "bundle_mode": "full", "text": text, "bundle_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "artifact": artifact, "artifact_sha256": sha, "artifact_type": atype,
            "files": [{"path": artifact, "sha256": sha, "lines": len(art_text.splitlines()), "mode": "full"}],
            "range": None, "sources": sources,
            "has_dangling": bool(dangling), "dangling_refs": dangling_l,
            "evidence_parity": len(ctx) >= 400,          # a one-line context is not a spec
            "rubric_version": _rubric_version(rubric)}


def append_log(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:                        # append: never clobber a same-day re-run
        f.write(json.dumps(row) + "\n")


def slug_for(artifact: str) -> str:
    if artifact.startswith(("range:", "files:")):       # multi-file bundle ids are not paths: make them filename-safe
        return re.sub(r"[^A-Za-z0-9]+", "-", artifact).strip("-")
    b = os.path.basename(artifact)
    return os.path.basename(os.path.dirname(artifact)) if b == "SKILL.md" else os.path.splitext(b)[0]


def _cli() -> int:
    """judge_lib.py bundle (--artifact P | --files A B ... | --range BASE..HEAD) --artifact-type T
                          [--context S] [--spec-file F ...] --out bundle.json"""
    import argparse, sys
    ap = argparse.ArgumentParser(description="build ONE evidence bundle for the judge (judge.py run does this for you)")
    ap.add_argument("cmd", choices=["bundle"])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--artifact"); src.add_argument("--files", nargs="+")
    src.add_argument("--range", dest="rng", metavar="BASE..HEAD")
    ap.add_argument("--artifact-type", default="skill")
    ap.add_argument("--context", default=""); ap.add_argument("--spec-file", action="append", default=[])
    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v6.md")
    ap.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        b = build_bundle(a.artifact, a.artifact_type, a.system, a.rubric, a.context, a.spec_file,
                         files=a.files, rng=a.rng)
    except PrivacyViolation as e:
        print(f"PRIVACY GUARD (no bundle written): {e}", file=sys.stderr); return 3
    except (ValueError, OSError) as e:
        print(f"ERROR (no bundle written): {e}", file=sys.stderr); return 2
    json.dump(b, open(a.out, "w", encoding="utf-8"))
    print(f"bundle {b['bundle_sha256'][:12]} · {b['artifact']} · {len(b['files'])} file(s), {b['bundle_mode']} · "
          f"artifact {b['artifact_sha256'][:12]} · {len(b['text'])} chars · "
          f"evidence_parity={b['evidence_parity']} · dangling={len(b['dangling_refs'])} → {a.out}")
    if not b["evidence_parity"]:
        # YED-223: parity is fixed HERE, at build time; the reviewer scores the bundle's bytes verbatim.
        print("\n  ⚠️  EVIDENCE-PARITY WARNING: this bundle carries < 400 chars of spec/context.\n"
              "      The run will log evidence_parity:false and be excluded from calibration_stats,\n"
              "      and cross-file defects (spec drift) are invisible to the reviewer.\n"
              "      Fix: REBUILD the bundle with --spec-file <in-repo spec> (repeatable) and/or --context.\n"
              "      A spec cannot be added after the bundle is built.\n",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
