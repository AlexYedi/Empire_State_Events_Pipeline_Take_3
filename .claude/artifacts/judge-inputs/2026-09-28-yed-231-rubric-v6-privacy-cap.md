# build-quality@6 — privacy-layer defect cap (YED-231)

## Purpose
Encode Alex's ruling (2026-09-28, disagree ack on the YED-236 quorum): a confirmed correctness defect in ANY layer of a privacy/security/access-control mechanism must FLAG, regardless of any backstop. Implemented as a new rubric version (build-quality@6 = @5 + one composite cap: privacy_layer_defect -> composite <= 0.65), wired into every scorer (judge_lib.score, gemini-judge.sh jq, legacy quorum-merge.sh claude recompute) and both structured-output schemas (Gemini responseSchema, OpenAI json schema), with default rubric paths moved to v6, docs updated, and parity tests added.

## Diff (vs origin/main merge-base)
```diff
diff --git a/.claude/evals/rubrics/build-quality-v6.md b/.claude/evals/rubrics/build-quality-v6.md
new file mode 100644
index 0000000..46c0262
--- /dev/null
+++ b/.claude/evals/rubrics/build-quality-v6.md
@@ -0,0 +1,87 @@
+# Rubric: `build-quality@6`
+
+Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code —
+**plus** rendered **`deep_read`** content artifacts (the prose Deep Read of the event research brief, ADR-5 / YED-136).
+Owned by the eval convention (`rubric_version` = `build-quality@6`; never mutate — bump to `@7`).
+Pair with the judge system prompt **`prompts/judge-system-v2.md`**.
+
+**What changed from `@5` (2026-09-28, YED-231 — Alex's privacy-layer ruling on the YED-236 quorum):**
+One new composite cap; criteria, weights, anchors and pass band are **unchanged**, so `@6` composites are comparable to
+`@5` everywhere the new flag is false.
+- **NEW cap — privacy-layer defect → composite ≤ 0.65 (a FLAG).** Set `privacy_layer_defect` when you **confirm** a
+  correctness defect in **any layer** of a privacy, security or access-control mechanism — a filter, guard, redaction,
+  permission/role check, secret handling, allow/deny list, "never publish X" rule — **even when another layer (a
+  backstop, a second guard, a verifier) would catch the failure.** A backstop never excuses a broken layer: each
+  layer must be correct on its own, because a silently broken layer turns defence-in-depth into single-layer
+  protection without anyone noticing. File the defect in `defects[]` (criterion `correctness`) as the evidence.
+  Do NOT set it for a hardening suggestion, a missing extra layer, or a diagnostics/logging gap in a correct layer.
+  Motivating case (2026-09-27, YED-236): `build_graph.py`'s gitignore filter mishandled `./`-prefixed references, a
+  real defect in the first layer of a public-privacy control. The voting seat found it and still passed the change
+  (0.784) by crediting the hub's independent guard; Alex acked **disagree** ("a flaw in the first layer of a privacy
+  control should fail regardless of the backstop").
+
+**What changed from `@4` (2026-09-19, YED-206 — the Gemini rubber-stamp triage):**
+`@4` had one pass anchor and one fail anchor per criterion and defined 1.0 as "matches the pass anchor or better", so a
+judge that found no fail anchor could legally return 1.0 on everything. The Gemini seat did exactly that on 20 of 23
+real prospective artifacts (triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`). Three changes; criteria,
+weights and pass band are **unchanged**, so `@5` composites are comparable to `@4`:
+1. **The top of the scale must be earned** — 1.0 = "searched this criterion for defects and can name what was checked";
+   a **0.85 middle anchor** ("ships with reviewer nits") is added to every criterion.
+2. **Defects before scores** — every run returns a `defects[]` list (line/section, criterion, spec ref, severity) *before*
+   criterion scores. A run with **all five criteria at 1.0** is recorded `flat_ceiling: true` and treated as
+   **low-information** by the quorum (it escalates instead of auto-accepting) — earned 1.0s on a single criterion are fine.
+3. **NEW cap — spec drift:** when a spec/ADR/decision record is supplied and the artifact's behaviour **contradicts a
+   numbered decision** in it, **correctness ≤ 0.70**. Motivating case: `substrate.py` defaulted event `kind` to
+   `'attended'`, contradicting ADR-10 decision 9 ("attendance is never inferred"); one seat praised that line as good
+   practice.
+
+Score each criterion **independently 0–1**. Composite = weighted sum, **then apply the caps**. **The harness, not the
+judge, computes the composite and the verdict** from criterion scores + cap flags.
+**Verdict: pass if (capped) composite ≥ 0.70, else flag-for-rework.**
+
+| id | weight | what "good" means |
+|---|---|---|
+| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. **Behaviour checked against each numbered spec decision supplied — contradiction caps ≤ 0.70.** **For `deep_read`: every stated fact is web-verified or web-re-grounded; jargon defined correctly; mechanisms accurate.** |
+| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. **Cap ≤ 0.60 if a load-bearing referenced file/rubric/doc does not exist.** **For commands: cap ≤ 0.35 if the orchestration skeleton is absent (agents listed but never dispatched, or no named output destination).** **For `deep_read`: the required sections present at appropriate depth, endnotes consolidated, no `> Gap` left silently unresolved.** |
+| `convention_adherence` | 0.20 | House conventions: file placement + frontmatter, naming (**project** skills in `.claude/skills/` take NO `alex:` prefix), source-of-truth discipline, MCP/tool + Notion-plan constraints, SDK constraints (fan-out from parent thread; MCP writes parent-thread only). **For `deep_read`: prose-not-lattice; jargon defined inline; citations as ENDNOTES not inline; provenance discipline (Rule 12).** |
+| `anti_pattern_avoidance` | 0.20 | Avoids: over-engineering/ceremony, duplicating state, resurrecting a tombstoned decision (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS the sanctioned Market-Intelligence store), fabricated numbers/specificity, orphan metrics, hardcoded secrets, lossy summarization where fidelity matters, speculative surface with no named friction. **For `deep_read`: no generic-explainer padding, no bullet-lattice fallback, no duplicating the Scan head or outbound copy.** |
+| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming; a skeleton presented as finished, a docstring promising a property the code doesn't have, or an unverified claim stamped "verified", is dishonest framing). **For `deep_read`: `> Gap` notes present where evidence was thin; company-reported vs. audited distinguished.** |
+
+### Composite caps (applied AFTER the weighted sum, by the harness)
+1. **Confidence-honesty cap → composite ≤ 0.65** when an unverified/uncited claim is asserted as verified.
+2. **Density cap → composite ≤ 0.65** when `artifact_type = deep_read` AND a padding signal (per `density-check.sh`) is, on inspection, generic-explainer filler rather than legitimate on-ramp.
+3. **Privacy-layer defect cap → composite ≤ 0.65 (NEW in `@6`)** when a confirmed correctness defect sits in any layer of a privacy/security/access-control mechanism, whatever the backstop.
+4. Per-criterion caps: **spec drift → correctness ≤ 0.70 (`@5`)**; dangling-reference → completeness ≤ 0.60 (also composite ≤ 0.60, mechanized by `check-refs.sh`); command-skeleton-absent → completeness ≤ 0.35.
+
+### Per-criterion anchors (pass · mid · fail)
+- **correctness** — pass (1.0): checked every numbered spec decision and the main code paths; none contradicted. mid (0.85): works as specified; one minor edge-case or naming slip. fail: references a tool/DB that doesn't exist; **code contradicts a numbered spec decision** (cap ≤ 0.70); a Deep Read asserting a thesis claim with no source.
+- **completeness** — pass: methodology + failure-modes + references *that all exist*. mid: all AC items present; one secondary part thin or a non-load-bearing piece deferred and *said so*. fail: an AC item silently unaddressed; `TODO` left in; a Deep Read dropping a researched section.
+- **convention_adherence** — pass: correct placement/frontmatter/naming throughout. mid: conventions followed; one cosmetic slip. fail: hardcoded secret; bypasses the single guarded write path; a Deep Read regressed to a bullet lattice.
+- **anti_pattern_avoidance** — pass: contract-first lean foundation. mid: lean, with one piece of speculative surface or duplicated state. fail: builds the platform when "lean" was decided; resurrects a tombstoned decision.
+- **diagnostics** — pass: comments explain the contract; failures are loud and specific; docstrings match behaviour. mid: failures loud, but a reported count or docstring overstates what's proven. fail: opaque/silent failure mode; overclaims certainty; asserts unverified as verified (also triggers the confidence-honesty cap).
+
+### Machine-readable
+```json
+{
+  "rubric_version": "build-quality@6",
+  "judge_system": "judge-system-v2",
+  "pass_band": 0.70,
+  "criteria": [
+    {"id": "correctness", "weight": 0.30},
+    {"id": "completeness", "weight": 0.20},
+    {"id": "convention_adherence", "weight": 0.20},
+    {"id": "anti_pattern_avoidance", "weight": 0.20},
+    {"id": "diagnostics", "weight": 0.10}
+  ],
+  "required_output": ["defects[] before criterion_scores", "cap flags", "NO judge-computed composite/verdict"],
+  "low_information": "all five criteria == 1.0 -> flat_ceiling:true -> quorum escalates",
+  "composite_caps": [
+    {"when": "confidence-honesty violation (unverified claim asserted as verified)", "max": 0.65},
+    {"when": "privacy_layer_defect: confirmed correctness defect in any layer of a privacy/security/access-control mechanism, regardless of backstop", "max": 0.65},
+    {"when": "artifact_type=deep_read AND density padding signal is generic-explainer filler", "max": 0.65, "mechanized_by": ".claude/hooks/density-check.sh"},
+    {"when": "behaviour contradicts a numbered decision in a supplied spec/ADR", "max": 0.70, "criterion": "correctness"},
+    {"when": "references a load-bearing file/rubric/doc that does not exist", "max": 0.60, "criterion": "completeness", "mechanized_by": ".claude/hooks/check-refs.sh"},
+    {"when": "artifact_type=command AND orchestration skeleton absent", "max": 0.35, "criterion": "completeness"}
+  ]
+}
+```
diff --git a/.claude/commands/judge-build.md b/.claude/commands/judge-build.md
index ca03361..69a235e 100644
--- a/.claude/commands/judge-build.md
+++ b/.claude/commands/judge-build.md
@@ -1,5 +1,5 @@
 ---
-description: "Cross-provider build-quality judge — score an artifact (skill/command/hook/ref/code, or a deep_read render) with a two-seat quorum (Claude/Sonnet + Gemini) against build-quality@5: mechanized dangling-ref cap + deep_read density pre-pass, per-criterion 0–1, weighted composite, merge to one quorum verdict, authoritative run-logs, capture your ack (calibration). Escalates on verdict mismatch, score divergence, a flat-1.0 seat, or missing evidence parity (fail-safe FLAG in autonomous). Gemini seat advisory. Never rewrites, never blocks."
+description: "Cross-provider build-quality judge — score an artifact (skill/command/hook/ref/code, or a deep_read render) with a two-seat quorum (Claude/Sonnet + Gemini) against build-quality@6: mechanized dangling-ref cap + deep_read density pre-pass, per-criterion 0–1, weighted composite, merge to one quorum verdict, authoritative run-logs, capture your ack (calibration). Escalates on verdict mismatch, score divergence, a flat-1.0 seat, or missing evidence parity (fail-safe FLAG in autonomous). Gemini seat advisory. Never rewrites, never blocks."
 argument-hint: "[artifact path or pasted content] [+ optional: the issue/AC it should satisfy]"
 ---
 
@@ -16,7 +16,7 @@ Runs when Alex types `/judge-build <artifact>` or says "judge this build", "scor
 1. **Intake** — resolve the artifact path + `artifact_type`; capture any spec/AC; determine **mode** (interactive = Alex in the loop, default; autonomous = batch/headless).
 2. **Pre-pass (mechanized)** — `bash .claude/hooks/check-refs.sh --artifact <path>` → the verified missing-references list (ground truth for both seats; enforces the `@5` dangling-ref cap deterministically). **If `artifact_type = deep_read`, also run** `bash .claude/hooks/density-check.sh --artifact <path>` → the words/citations density signal (flag only — the judge decides padding vs. legitimate on-ramp; NOT a hard cap).
 3. **Dispatch two seats** — (a) **Claude/Sonnet** seat via the `Agent` tool with `model: sonnet` (house-aware, independent of the Opus main thread); (b) **Gemini** seat via `bash .claude/hooks/gemini-judge.sh --artifact <path> --artifact-type <t> --calibration-set prospective`. Both score all 5 `build-quality@5` criteria (0–1 + reasoning, **defects listed first**) using `judge-system-v2.md` + `build-quality-v5.md`. The Gemini adapter enforces the order via `responseSchema` and **the harness computes the composite/verdict** — the model never does. **For a rendered Deep Read, pass `--artifact-type deep_read`** so Step 0's density pre-pass runs.
-4. **Collect** — the Gemini adapter wrote its own run-log line; append the Claude/Sonnet seat's line (`judge_provider:"anthropic"`, `rubric:"build-quality@5"`).
+4. **Collect** — the Gemini adapter wrote its own run-log line; append the Claude/Sonnet seat's line (`judge_provider:"anthropic"`, `rubric:"build-quality@6"`).
 5. **Merge → named output** — `bash .claude/hooks/quorum-merge.sh --artifact <path> --mode <mode> --claude-verdict '<json>' --gemini-log <path>` writes the authoritative **`quorum` record** with `agree` + `divergence` + `escalation_reasons[]` + `resolution` (`auto` / `escalated` / `failsafe_flag`) + `final_verdict`. **Matching verdicts no longer auto-accept:** it escalates on score divergence ≥0.15, a flat-1.0 seat, or a Gemini run without evidence parity (YED-206).
 6. **Present + ack (calibration)** — show both seats' per-criterion scores (scoped-quorum weighting noted); on **agree** ask "agree / disagree?" once; on **escalated** show the divergent criterion side-by-side and ask Alex to adjudicate; write the answer to the quorum record's `alex_ack`. Autonomous mode records `failsafe_flag` and does not block.
 7. **Failure modes** — no spec → score vs stated purpose, flag reduced confidence; artifact too large → judge load-bearing sections, no silent truncation; **Gemini seat errors → do NOT silently single-judge**: record the Claude seat, mark the quorum incomplete, flag for re-run.
diff --git a/.claude/evals/judge_lib.py b/.claude/evals/judge_lib.py
index 030c235..4560597 100644
--- a/.claude/evals/judge_lib.py
+++ b/.claude/evals/judge_lib.py
@@ -48,7 +48,7 @@ def sha256_file(path: str) -> str:
     return hashlib.sha256(open(path, "rb").read()).hexdigest()
 
 
-# ---------------------------------------------------------------- scoring (mirrors gemini-judge.sh, @5)
+# ---------------------------------------------------------------- scoring (mirrors gemini-judge.sh, @6)
 def score(verdict: dict, atype: str, has_dangling: bool) -> dict:
     """Per-criterion caps, weighted sum, composite caps, verdict. Caps only ever LOWER a score."""
     cs = verdict.get("criterion_scores")
@@ -78,6 +78,8 @@ def score(verdict: dict, atype: str, has_dangling: bool) -> dict:
     caps = [raw]
     if flags.get("confidence_honesty_violation"):
         caps.append(0.65)
+    if flags.get("privacy_layer_defect"):            # @6 (YED-231): a broken privacy layer fails, backstop or not
+        caps.append(0.65)
     if atype == "deep_read" and flags.get("density_padding"):
         caps.append(0.65)
     if has_dangling:
@@ -86,6 +88,7 @@ def score(verdict: dict, atype: str, has_dangling: bool) -> dict:
     out["raw_score"] = round(raw * 1000) / 1000
     out["weighted_score"] = round(min(caps) * 1000) / 1000
     out["confidence_honesty_violation"] = bool(flags.get("confidence_honesty_violation"))
+    out["privacy_layer_defect"] = bool(flags.get("privacy_layer_defect"))
     out["verdict"] = "pass" if out["weighted_score"] >= PASS_LINE else "flag"
     out["scoring"] = "harness-recomputed"
     return out
@@ -182,7 +185,7 @@ Work in this order, and the output schema enforces it:
 1. checks_performed: list the concrete things you checked (e.g. "each numbered ADR decision vs the code", "every write path", "error handling on network calls").
 2. defects: every defect you found, major or minor, each with location (the line number shown in the ARTIFACT CONTENT margin, plus function or section), criterion, severity, spec_ref (the numbered spec/ADR decision it contradicts, or ""), and description. Where the schema has a `quote` field, copy the offending text VERBATIM from that line (it is checked mechanically; a quote that is not in the artifact counts against you). Competent artifacts usually still have minor reviewer nits; list them.
 3. criterion_scores: score each of the 5 criteria 0-1 INDEPENDENTLY using the rubric scale (1.0 = searched and found nothing of consequence; ~0.85 = passes with nits; 0.70 = pass line; below = send back). Reasoning must cite specific lines or sections. Any criterion you score below 0.85 must have at least one defect filed against it.
-4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding).
+4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding), privacy_layer_defect (you CONFIRMED a correctness defect in ANY layer of a privacy/security/access-control mechanism - a filter, guard, redaction, permission check, secret handling, allow/deny list - even if another layer or backstop would catch it; a backstop never excuses a broken layer; NOT for hardening suggestions or logging gaps in a correct layer).
 Do NOT compute a composite score or a verdict; the harness does that.
 House-context primer (for convention_adherence/anti_pattern_avoidance): project skills in .claude/skills/ take NO alex: prefix (that prefix is for alex-plugin skills only); subagents cannot spawn subagents (fan-out runs from the parent thread); MCP writes are parent-thread only; Supabase as the Market-Intelligence store is sanctioned (NOT an anti-pattern), Supabase as a measurement store is tombstoned. If you lack house context for a convention question, say so in the reasoning and score what you CAN verify; do not default to 1.0."""
 
@@ -308,7 +311,7 @@ def _cli() -> int:
     ap.add_argument("cmd", choices=["bundle"])
     ap.add_argument("--artifact", required=True); ap.add_argument("--artifact-type", default="skill")
     ap.add_argument("--context", default=""); ap.add_argument("--spec-file", action="append", default=[])
-    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v5.md")
+    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v6.md")
     ap.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
     ap.add_argument("--out", required=True)
     a = ap.parse_args()
diff --git a/.claude/evals/test_judge_lib.py b/.claude/evals/test_judge_lib.py
index 181a251..8eb3f5d 100644
--- a/.claude/evals/test_judge_lib.py
+++ b/.claude/evals/test_judge_lib.py
@@ -23,7 +23,8 @@ def jq_score(v, atype, dangling):
 
 
 def V(scores, **flags):
-    f = {"confidence_honesty_violation": False, "spec_drift": False, "command_skeleton_absent": False, "density_padding": False}
+    f = {"confidence_honesty_violation": False, "spec_drift": False, "command_skeleton_absent": False, "density_padding": False,
+         "privacy_layer_defect": False}
     f.update(flags)
     return {"criterion_scores": [{"id": c, "score": s, "reasoning": "r"} for c, s in zip(jl.CRITERIA, scores)],
             "defects": [], "checks_performed": ["x"], "cap_flags": f}
@@ -38,7 +39,11 @@ FIX = [("flat ceiling", V([1, 1, 1, 1, 1]), "skill", False), ("nits", V([.85, .9
        ("skeleton flag ignored off-type", V([.9, .9, .9, .9, .9], command_skeleton_absent=True), "skill", False),
        ("density only on deep_read", V([.9, .9, .9, .9, .9], density_padding=True), "deep_read", False),
        ("density ignored off-type", V([.9, .9, .9, .9, .9], density_padding=True), "skill", False),
-       ("out of range clamps", V([1.4, -0.2, .9, .9, .9]), "skill", False)]
+       ("out of range clamps", V([1.4, -0.2, .9, .9, .9]), "skill", False),
+       # @6 (YED-231): a confirmed defect in any privacy layer flags, whatever the backstop
+       ("privacy-layer cap flags a strong artifact", V([.95, .95, .95, .95, .95], privacy_layer_defect=True), "code", False),
+       ("YED-236 regression: 0.784 pass -> flag", V([.75, .72, .85, .9, .65], privacy_layer_defect=True), "code", False),
+       ("privacy flag off = @5 arithmetic", V([.75, .72, .85, .9, .65]), "code", False)]
 ok = n = 0
 
 
diff --git a/.claude/hooks/gemini-judge.sh b/.claude/hooks/gemini-judge.sh
index bd6f63b..502f229 100755
--- a/.claude/hooks/gemini-judge.sh
+++ b/.claude/hooks/gemini-judge.sh
@@ -13,7 +13,7 @@ cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true
 
 ARTIFACT=""; ATYPE="skill"; CALSET="prospective"; CONTEXT=""; SPEC_FILES=""
 MODEL="gemini-pro-latest"
-RUBRIC=".claude/evals/rubrics/build-quality-v5.md"
+RUBRIC=".claude/evals/rubrics/build-quality-v6.md"
 SYSTEM=".claude/evals/prompts/judge-system-v2.md"
 LABEL=""; PRINT_ONLY=0; BUNDLE=""; ABLOB=""; DRY_RUN=0
 while [ $# -gt 0 ]; do
@@ -129,7 +129,7 @@ Work in this order, and the output schema enforces it:
 1. checks_performed: list the concrete things you checked (e.g. "each numbered ADR decision vs the code", "every write path", "error handling on network calls").
 2. defects: every defect you found, major or minor, each with location (line number, function or section), criterion, severity, spec_ref (the numbered spec/ADR decision it contradicts, or ""), and description. Competent artifacts usually still have minor reviewer nits; list them.
 3. criterion_scores: score each of the 5 criteria 0-1 INDEPENDENTLY using the rubric scale (1.0 = searched and found nothing of consequence; ~0.85 = passes with nits; 0.70 = pass line; below = send back). Reasoning must cite specific lines or sections.
-4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding).
+4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding), privacy_layer_defect (you CONFIRMED a correctness defect in ANY layer of a privacy/security/access-control mechanism - a filter, guard, redaction, permission check, secret handling, allow/deny list - even if another layer or backstop would catch it; a backstop never excuses a broken layer; NOT for hardening suggestions or logging gaps in a correct layer).
 Do NOT compute a composite score or a verdict; the harness does that.
 House-context primer (for convention_adherence/anti_pattern_avoidance): project skills in .claude/skills/ take NO alex: prefix (that prefix is for alex-plugin skills only); subagents cannot spawn subagents (fan-out runs from the parent thread); MCP writes are parent-thread only; Supabase as the Market-Intelligence store is sanctioned (NOT an anti-pattern), Supabase as a measurement store is tombstoned. If you lack house context for a convention question, say so in the reasoning and score what you CAN verify; do not default to 1.0.'
 
@@ -146,9 +146,9 @@ SCHEMA='{"type":"OBJECT","propertyOrdering":["checks_performed","defects","crite
   "criterion_scores":{"type":"ARRAY","items":{"type":"OBJECT","propertyOrdering":["id","score","reasoning"],"required":["id","score","reasoning"],
     "properties":{"id":{"type":"STRING","enum":["correctness","completeness","convention_adherence","anti_pattern_avoidance","diagnostics"]},
       "score":{"type":"NUMBER"},"reasoning":{"type":"STRING"}}}},
-  "cap_flags":{"type":"OBJECT","required":["confidence_honesty_violation","spec_drift","command_skeleton_absent","density_padding"],
+  "cap_flags":{"type":"OBJECT","required":["confidence_honesty_violation","spec_drift","command_skeleton_absent","density_padding","privacy_layer_defect"],
     "properties":{"confidence_honesty_violation":{"type":"BOOLEAN"},"spec_drift":{"type":"BOOLEAN"},
-      "command_skeleton_absent":{"type":"BOOLEAN"},"density_padding":{"type":"BOOLEAN"}}}}}'
+      "command_skeleton_absent":{"type":"BOOLEAN"},"density_padding":{"type":"BOOLEAN"},"privacy_layer_defect":{"type":"BOOLEAN"}}}}}'
 
 # --- build request body safely with jq (no manual escaping) ---
 [ -n "$BUNDLE" ] && DANGLING=$(jq -r '.dangling_refs | join("\n")' "$BUNDLE")   # the cap must use the bundle's pre-pass
@@ -226,11 +226,13 @@ VERDICT_JSON=$(echo "$VERDICT_JSON" | jq -c --arg atype "$ATYPE" --argjson dangl
   | ($s.correctness*0.30 + $s.completeness*0.20 + $s.convention_adherence*0.20 + $s.anti_pattern_avoidance*0.20 + $s.diagnostics*0.10) as $raw
   | ([$raw]
      + (if .cap_flags.confidence_honesty_violation then [0.65] else [] end)
+     + (if .cap_flags.privacy_layer_defect then [0.65] else [] end)
      + (if $atype=="deep_read" and .cap_flags.density_padding then [0.65] else [] end)
      + (if $dangling then [0.60] else [] end) | min) as $capped
   | .raw_score = (($raw*1000|round)/1000)
   | .weighted_score = (($capped*1000|round)/1000)
   | .confidence_honesty_violation = .cap_flags.confidence_honesty_violation
+  | .privacy_layer_defect = (.cap_flags.privacy_layer_defect // false)
   | .verdict = (if .weighted_score >= 0.70 then "pass" else "flag" end)')
 [ -n "$DANGLING" ] && echo "  check-refs: dangling reference(s) present → completeness/composite capped ≤0.60 deterministically" >&2
 [ "$(echo "$VERDICT_JSON" | jq -r '.flat_ceiling')" = "true" ] && echo "  ⚠️  FLAT CEILING: all five criteria 1.0 — low-information; the quorum will escalate instead of auto-accepting." >&2
diff --git a/.claude/hooks/openai_judge.py b/.claude/hooks/openai_judge.py
index 185d25d..ec07f46 100755
--- a/.claude/hooks/openai_judge.py
+++ b/.claude/hooks/openai_judge.py
@@ -45,9 +45,11 @@ SCHEMA = {  # strict mode: every property required, no extras. Key order = the o
             "properties": {"id": {"type": "string", "enum": CRIT}, "score": {"type": "number"},
                            "reasoning": {"type": "string"}}}},
         "cap_flags": {"type": "object", "additionalProperties": False,
-                      "required": ["confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding"],
+                      "required": ["confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding",
+                                   "privacy_layer_defect"],
                       "properties": {k: {"type": "boolean"} for k in
-                                     ("confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding")}},
+                                     ("confidence_honesty_violation", "spec_drift", "command_skeleton_absent", "density_padding",
+                                      "privacy_layer_defect")}},
     },
 }
 
@@ -108,7 +110,7 @@ def main() -> int:
     ap.add_argument("--calibration-set", default="prospective"); ap.add_argument("--context", default="")
     ap.add_argument("--spec-file", action="append", default=[])
     ap.add_argument("--model", default=None); ap.add_argument("--reasoning-effort", default=None)
-    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v5.md")
+    ap.add_argument("--rubric", default=".claude/evals/rubrics/build-quality-v6.md")
     ap.add_argument("--system", default=".claude/evals/prompts/judge-system-v2.md")
     ap.add_argument("--label", default=""); ap.add_argument("--bundle", default="")
     ap.add_argument("--artifact-blob", default="", help="git blob sha proving this file is repo history (controls)")
diff --git a/.claude/hooks/quorum-merge.sh b/.claude/hooks/quorum-merge.sh
index 8b5193a..e22ec0a 100755
--- a/.claude/hooks/quorum-merge.sh
+++ b/.claude/hooks/quorum-merge.sh
@@ -68,7 +68,7 @@ if printf '%s' "$CV" | jq -e '(.criterion_scores|type)=="array" and (.criterion_
     | (if $f.command_skeleton_absent then cap("completeness"; 0.35) else . end)
     | (.criterion_scores|map({(.id): .score})|add) as $s
     | ($s.correctness*0.30 + $s.completeness*0.20 + $s.convention_adherence*0.20 + $s.anti_pattern_avoidance*0.20 + $s.diagnostics*0.10) as $raw
-    | ([$raw] + (if $f.confidence_honesty_violation then [0.65] else [] end) + (if $f.density_padding then [0.65] else [] end) | min) as $capped
+    | ([$raw] + (if $f.confidence_honesty_violation then [0.65] else [] end) + (if $f.density_padding then [0.65] else [] end) + (if $f.privacy_layer_defect then [0.65] else [] end) | min) as $capped
     | .weighted_score = (($capped*1000|round)/1000)
     | .verdict = (if .weighted_score >= 0.70 then "pass" else "flag" end)')
   CV_WS=$(printf '%s' "$CV" | jq -r '.weighted_score')
diff --git a/.claude/hooks/seat-log.py b/.claude/hooks/seat-log.py
index fa2183a..9d5b807 100755
--- a/.claude/hooks/seat-log.py
+++ b/.claude/hooks/seat-log.py
@@ -47,7 +47,7 @@ def main() -> int:
     rid = a.label or f"sonnet-{slug}"
     row = {"run_id": rid, "timestamp": jl.now_utc(), "artifact": a.artifact,
            "artifact_sha256": bundle.get("artifact_sha256") or jl.sha256_file(a.artifact),
-           "artifact_type": a.artifact_type, "rubric": bundle.get("rubric_version") or "build-quality@5",
+           "artifact_type": a.artifact_type, "rubric": bundle.get("rubric_version") or "build-quality@6",
            "judge_model": a.judge_model, "judge_provider": "anthropic", "seat_status": "voting",
            "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession"),
            "criterion_scores": scored["criterion_scores"], "weighted_score": scored["weighted_score"],
diff --git a/.claude/references/cross-provider-judge.md b/.claude/references/cross-provider-judge.md
index 62900b1..c589c76 100644
--- a/.claude/references/cross-provider-judge.md
+++ b/.claude/references/cross-provider-judge.md
@@ -17,11 +17,11 @@ the concrete path to dropping "provisional." This spec is the design; build foll
 - Why Gemini Pro not Flash-Lite: free tier on this key = Flash-Lite only (too weak → noisy disagreements). Billing enabled 2026-07-17; Pro is the quality independent seat. Cost is negligible at judge volume.
 
 ## Scoped quorum (not naïve 50/50)
-Both judges score all 5 `build-quality@5` criteria, BUT their votes are **weighted by domain competence**:
+Both judges score all 5 `build-quality@6` criteria (`@6` = `@5` + the privacy-layer defect cap, 2026-09-28), BUT their votes are **weighted by domain competence**:
 - **Provider-neutral criteria** (`correctness`, `completeness`) — Gemini's independent read carries full weight; this is where cross-provider catches Claude's blind spots.
 - **House-specific criteria** (`convention_adherence`, `anti_pattern_avoidance`) — Claude (Sonnet) retains primary judgment; Gemini lacks native Empire-State context (notion-search vs notion-query-data-sources, SDK subagent constraint, tombstoned decisions) unless heavily briefed. Gemini's vote here is advisory only.
 - `diagnostics` — shared.
-Gemini gets the SAME `judge-system-v2.md` + `build-quality@5` + per-artifact spec/context the Claude judge gets (apples-to-apples), plus a house-context primer for the convention criteria. For `deep_read` artifacts it also runs `density-check.sh` and gets the density signal (a flag, not a hard cap — the model judges padding vs. legitimate on-ramp).
+Gemini gets the SAME `judge-system-v2.md` + `build-quality@6` + per-artifact spec/context the Claude judge gets (apples-to-apples), plus a house-context primer for the convention criteria. For `deep_read` artifacts it also runs `density-check.sh` and gets the density signal (a flag, not a hard cap — the model judges padding vs. legitimate on-ramp).
 
 ## Quorum resolution (no model tiebreak — it would be circular)
 A disputant cannot adjudicate its own disagreement, and we have no genuinely-independent *third* provider. So:
diff --git a/.claude/skills/judge-build/SKILL.md b/.claude/skills/judge-build/SKILL.md
index d500fea..ec15eec 100644
--- a/.claude/skills/judge-build/SKILL.md
+++ b/.claude/skills/judge-build/SKILL.md
@@ -9,7 +9,8 @@ You orchestrate the **build-quality judge** so quality is a measurable, cross-pr
 
 **Load first (every run):**
 - `.claude/evals/prompts/judge-system-v2.md` — the **current** judge instructions (defects-before-scores, earned 1.0, don't-trust-docstrings). Follow verbatim. (`judge-system.md` = v1, retained for runs scored under it.)
-- `.claude/evals/rubrics/build-quality-v5.md` — the **current** rubric (`build-quality@5`, live 2026-09-19, YED-206): 1.0 must be EARNED ("searched and can name what was checked") + a 0.85 mid anchor, `defects[]` required before scores, and a **NEW spec-drift cap (correctness ≤0.70)** when behaviour contradicts a numbered spec/ADR decision. Pair with `prompts/judge-system-v2.md`. Record `rubric: "build-quality@5"` in every run-log. Inherited from `@4`: 5 criteria + weights, pass band 0.70, and the caps — composite **confidence-honesty cap ≤0.65** (unverified-asserted-as-verified → flag) + completeness caps (dangling-reference ≤0.60; command-skeleton-absent ≤0.35) + the **density cap ≤0.65 (`deep_read` artifacts only)** — padding (high word-to-cited-fact ratio that is generic-explainer filler, NOT legitimate novice on-ramp) → flag. (`build-quality-v4.md`/`-v3.md`/`-v2.md`/`.md` = retained `@3`/`@2`/`@1`; never mutate old versions. For every artifact type EXCEPT `deep_read`, `@4` ≡ `@3`.)
+- `.claude/evals/rubrics/build-quality-v6.md` — the **current** rubric (`build-quality@6`, live 2026-09-28, YED-231): `@5` plus ONE new composite cap — **`privacy_layer_defect` → composite ≤ 0.65 (FLAG)** when a confirmed correctness defect sits in ANY layer of a privacy/security/access-control mechanism, **whatever the backstop** (Alex's ruling on the YED-236 quorum: "a flaw in the first layer of a privacy control should fail regardless of the backstop"). Everything below about `@5` still holds. Record `rubric: "build-quality@6"`.
+- `.claude/evals/rubrics/build-quality-v5.md` — the **previous** rubric (`build-quality@5`, live 2026-09-19, YED-206): 1.0 must be EARNED ("searched and can name what was checked") + a 0.85 mid anchor, `defects[]` required before scores, and a **NEW spec-drift cap (correctness ≤0.70)** when behaviour contradicts a numbered spec/ADR decision. Pair with `prompts/judge-system-v2.md`. Record `rubric: "build-quality@5"` in every run-log. Inherited from `@4`: 5 criteria + weights, pass band 0.70, and the caps — composite **confidence-honesty cap ≤0.65** (unverified-asserted-as-verified → flag) + completeness caps (dangling-reference ≤0.60; command-skeleton-absent ≤0.35) + the **density cap ≤0.65 (`deep_read` artifacts only)** — padding (high word-to-cited-fact ratio that is generic-explainer filler, NOT legitimate novice on-ramp) → flag. (`build-quality-v4.md`/`-v3.md`/`-v2.md`/`.md` = retained `@3`/`@2`/`@1`; never mutate old versions. For every artifact type EXCEPT `deep_read`, `@4` ≡ `@3`.)
 
 **Ground rules:**
 - **Per-seat standing (revised 2026-09-19, YED-206).** Trust is per seat, on four numbers from `.claude/evals/calibration_stats.py` (agreement above the seat's always-pass baseline · κ ≥ 0.60 · flag recall ≥ 0.60 · flat-1.0 rate < 0.30): **Sonnet = trusted seat** (κ 0.80, recall 0.80); **Gemini = ADVISORY** (κ 0.27, recall 0.20, flat-1.0 0.82 — it rubber-stamped 20 of 23 real artifacts; triage: `.claude/notes/gemini-judge-triage-2026-09-19.md`). An advisory seat runs and is recorded but **cannot auto-accept a quorum**. Still do NOT hard-block on the score.
```

## Test evidence (author-run 2026-09-28)
- test_judge_lib: 50/50 incl. python==jq parity on 3 new fixtures (strong artifact + flag -> 0.65 flag; real YED-236 scores 0.75/0.72/0.85/0.9/0.65 + flag -> 0.65 flag; same scores, flag off -> 0.784 pass).
- test_quorum_scenarios 6/6, test_quorum_nseat 40/40, test_adapter_contract 39/39, test_null_baseline 12/12, test_canary_gate 9/9.
- Positive control: YED-236 re-judged under @6 — Sonnet voting seat set privacy_layer_defect; quorum final FLAG 0.65 (was PASS 0.784 under @5). Caveat: that seat read later git history that names the bug.
