#!/usr/bin/env bash
# gemini-judge.sh — the independent (cross-provider) build-quality judge.
# Runs an artifact through Gemini Pro against the current build-quality rubric (--rubric; version derived from the file), emits the same eval run-log line
# as /judge-build (schema-stable), tagged judge_model=gemini + calibration_set. Spec:
# .claude/references/cross-provider-judge.md. Claude seat runs separately via the Agent tool.
#
# Usage:
#   gemini-judge.sh --artifact <path> [--artifact-type <t>] [--calibration-set backfill|prospective]
#                   [--context "<per-artifact spec/context>"] [--model gemini-pro-latest]
#                   [--rubric <path>] [--system <path>] [--label <run-id>] [--print-only]
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true

ARTIFACT=""; ATYPE="skill"; CALSET="prospective"; CONTEXT=""; SPEC_FILES=""
MODEL="gemini-pro-latest"
RUBRIC=".claude/evals/rubrics/build-quality-v5.md"
SYSTEM=".claude/evals/prompts/judge-system-v2.md"
LABEL=""; PRINT_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --artifact) ARTIFACT="$2"; shift 2;;
    --artifact-type) ATYPE="$2"; shift 2;;
    --calibration-set) CALSET="$2"; shift 2;;
    --context) CONTEXT="$2"; shift 2;;
    --spec-file) SPEC_FILES="$SPEC_FILES $2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    --rubric) RUBRIC="$2"; shift 2;;
    --system) SYSTEM="$2"; shift 2;;
    --label) LABEL="$2"; shift 2;;
    --print-only) PRINT_ONLY=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -n "$ARTIFACT" ] && [ -r "$ARTIFACT" ] || { echo "ERROR: --artifact missing/unreadable: $ARTIFACT" >&2; exit 2; }
[ -r "$RUBRIC" ] || { echo "ERROR: rubric unreadable: $RUBRIC" >&2; exit 2; }
[ -r "$SYSTEM" ] || { echo "ERROR: system prompt unreadable: $SYSTEM" >&2; exit 2; }
# --- evidence parity (added 2026-09-11) --------------------------------------------------
# cross-provider-judge.md ALREADY requires apples-to-apples ("Gemini gets the SAME ... spec/context
# the Claude judge gets"). The implementation had drifted to artifact-only runs, which silently
# demotes the independent BIAS-control seat into a weak second variance sample: cross-file defects
# (spec-vs-code drift, registry/citation errors) are structurally invisible without the spec.
# Found 2026-09-11 when Sonnet caught 3 defects on inbox-miner and Gemini returned a flat 1.0 —
# a negative control proved Gemini discriminates fine (0.35/flag on a seeded-bad artifact), so the
# fault was the harness, not the model. Parity is now recorded so asymmetric runs can be EXCLUDED
# from the calibration rate that gates dropping "provisional".
for sf in $SPEC_FILES; do
  if [ -r "$sf" ]; then
    CONTEXT="${CONTEXT}

===== SPEC FILE: ${sf} =====
$(cat "$sf")"
  else
    echo "WARNING: --spec-file unreadable, skipped: $sf" >&2
  fi
done
CTX_LEN=$(printf '%s' "$CONTEXT" | wc -c | tr -d ' ')
if [ "$CTX_LEN" -lt 400 ]; then
  PARITY="false"
  echo "  ⚠️  EVIDENCE-PARITY WARNING: context is ${CTX_LEN} chars; no substantive spec supplied." >&2
  echo "      The Claude seat is briefed with the spec + supporting files; this seat is not." >&2
  echo "      Cross-file defects are invisible to it, so an 'agree' here is WEAK corroboration." >&2
  echo "      Pass --spec-file <path> (repeatable). Logging evidence_parity:false — exclude from calibration." >&2
else
  PARITY="true"
fi

# derive the rubric version from the rubric file (never hardcode — it drifts when the default bumps)
RUBRIC_VER=$(grep -oE 'build-quality@[0-9]+' "$RUBRIC" | head -1)
[ -n "$RUBRIC_VER" ] || RUBRIC_VER="build-quality@unknown"

# --- key (never printed) ---
set -a; . ./.env 2>/dev/null; set +a
[ -n "${GEMINI_API_KEY:-}" ] || { echo "ERROR: GEMINI_API_KEY not set in .env" >&2; exit 1; }

# --- deterministic dangling-reference pre-pass (mechanizes the @4 dangling-ref cap; models under-apply it — bf17) ---
DANGLING=""
if [ -x .claude/hooks/check-refs.sh ]; then
  DANGLING=$(.claude/hooks/check-refs.sh --artifact "$ARTIFACT" 2>/dev/null)
fi

# --- deterministic tombstone pre-pass (YED-201 Fix 2A): live references to removed tools/decisions ---
TOMBS=""
if [ -x .claude/hooks/check-tombstones.py ]; then
  TOMBS=$(python3 .claude/hooks/check-tombstones.py --artifact "$ARTIFACT" 2>/dev/null)
fi

# --- density pre-pass (deep_read only; supplies the number-side of the @4 density cap — NOT a deterministic cap:
#     padding vs. legitimate novice on-ramp is a judgment call, so the script flags and the judge decides) ---
DENSITY=""
if [ "$ATYPE" = "deep_read" ] && [ -x .claude/hooks/density-check.sh ]; then
  DENSITY=$(.claude/hooks/density-check.sh --artifact "$ARTIFACT" 2>/dev/null | grep -E '^density-check: (words|OK|PADDING-RISK|UNCITED-LONGFORM)' | head -1)
fi

# --- @5 instructions (2026-09-19, YED-206) -------------------------------------------------------
# The @4 block pre-filled "verdict":"pass", told the seat to judge house criteria "conservatively" (read as: don't
# penalise), and let the MODEL compute the composite. Triage (.claude/notes/gemini-judge-triage-2026-09-19.md): the
# seat returned a flat 1.0 on 20/23 real prospective artifacts. Now: the schema forces defects[] BEFORE scores
# (generationConfig.responseSchema below — a system-prompt-only version of this was tested and ignored), nothing is
# pre-filled, and THIS SCRIPT computes the composite + verdict from criterion scores and cap flags.
INSTR='You are scoring ONE build artifact against the rubric above, following the judge system rules.
Work in this order, and the output schema enforces it:
1. checks_performed: list the concrete things you checked (e.g. "each numbered ADR decision vs the code", "every write path", "error handling on network calls").
2. defects: every defect you found, major or minor, each with location (line number, function or section), criterion, severity, spec_ref (the numbered spec/ADR decision it contradicts, or ""), and description. Competent artifacts usually still have minor reviewer nits; list them.
3. criterion_scores: score each of the 5 criteria 0-1 INDEPENDENTLY using the rubric scale (1.0 = searched and found nothing of consequence; ~0.85 = passes with nits; 0.70 = pass line; below = send back). Reasoning must cite specific lines or sections.
4. cap_flags: set confidence_honesty_violation (an unverified/uncited claim asserted as verified), spec_drift (behaviour contradicts a numbered decision in the supplied spec), command_skeleton_absent (a command that lists agents without dispatch/output), density_padding (deep_read only: padding is generic filler, not legitimate novice on-ramp; an honestly short section is NOT padding).
Do NOT compute a composite score or a verdict; the harness does that.
House-context primer (for convention_adherence/anti_pattern_avoidance): project skills in .claude/skills/ take NO alex: prefix (that prefix is for alex-plugin skills only); subagents cannot spawn subagents (fan-out runs from the parent thread); MCP writes are parent-thread only; Supabase as the Market-Intelligence store is sanctioned (NOT an anti-pattern), Supabase as a measurement store is tombstoned. If you lack house context for a convention question, say so in the reasoning and score what you CAN verify; do not default to 1.0.'

# responseSchema forces the order checks -> defects -> scores -> cap flags (propertyOrdering) and required fields.
SCHEMA='{"type":"OBJECT","propertyOrdering":["checks_performed","defects","criterion_scores","cap_flags"],
 "required":["checks_performed","defects","criterion_scores","cap_flags"],
 "properties":{
  "checks_performed":{"type":"ARRAY","items":{"type":"STRING"}},
  "defects":{"type":"ARRAY","items":{"type":"OBJECT","propertyOrdering":["location","criterion","severity","spec_ref","description"],
    "required":["location","criterion","severity","spec_ref","description"],
    "properties":{"location":{"type":"STRING"},
      "criterion":{"type":"STRING","enum":["correctness","completeness","convention_adherence","anti_pattern_avoidance","diagnostics"]},
      "severity":{"type":"STRING","enum":["major","minor"]},"spec_ref":{"type":"STRING"},"description":{"type":"STRING"}}}},
  "criterion_scores":{"type":"ARRAY","items":{"type":"OBJECT","propertyOrdering":["id","score","reasoning"],"required":["id","score","reasoning"],
    "properties":{"id":{"type":"STRING","enum":["correctness","completeness","convention_adherence","anti_pattern_avoidance","diagnostics"]},
      "score":{"type":"NUMBER"},"reasoning":{"type":"STRING"}}}},
  "cap_flags":{"type":"OBJECT","required":["confidence_honesty_violation","spec_drift","command_skeleton_absent","density_padding"],
    "properties":{"confidence_honesty_violation":{"type":"BOOLEAN"},"spec_drift":{"type":"BOOLEAN"},
      "command_skeleton_absent":{"type":"BOOLEAN"},"density_padding":{"type":"BOOLEAN"}}}}}'

# --- build request body safely with jq (no manual escaping) ---
REQ=$(jq -n \
  --rawfile sys "$SYSTEM" --rawfile rubric "$RUBRIC" --rawfile art "$ARTIFACT" \
  --arg ctx "$CONTEXT" --arg atype "$ATYPE" --arg instr "$INSTR" --argjson schema "$SCHEMA" --arg path "$ARTIFACT" --arg dangling "$DANGLING" --arg density "$DENSITY" --arg tombs "$TOMBS" \
  '{contents:[{parts:[{text:(
      $sys + "\n\n===== RUBRIC (version is stated in the rubric text below) =====\n" + $rubric
      + "\n\n===== ARTIFACT TYPE =====\n" + $atype
      + "\n\n===== PER-ARTIFACT CONTEXT/SPEC =====\n" + (if $ctx=="" then "(none supplied — score correctness/completeness against the artifact'\''s own stated purpose; note reduced confidence)" else $ctx end)
      + "\n\n===== VERIFIED-MISSING REFERENCES (deterministic file-existence check — treat as ground truth) =====\n" + (if $dangling=="" then "(none — all checked .claude/ references exist)" else ($dangling + "\n→ per the rubric, a load-bearing reference that does not exist caps completeness ≤0.60 (the harness enforces it).") end)
      + "\n\n===== LIVE REFERENCES TO REMOVED TOOLS/DECISIONS (deterministic tombstone check vs platform-constraints.md — each hit is ground truth that the line names a removed thing with no removal marker within 40 chars; the list is a LOWER BOUND, so still read the artifact; YOU judge whether each hit is load-bearing) =====\n" + (if $tombs=="" then "(none)" else ($tombs + "\n→ a load-bearing step that relies on a removed tool is a correctness + anti_pattern_avoidance defect (resurrecting a superseded decision).") end)
      + "\n\n===== DENSITY SIGNAL (deep_read only; words÷citations — a FLAG, not a verdict; you decide padding vs. legitimate on-ramp) =====\n" + (if $density=="" then "(not a deep_read artifact, or density-check unavailable — density cap N/A)" else $density end)
      + "\n\n===== ARTIFACT PATH =====\n" + $path
      + "\n\n===== ARTIFACT CONTENT =====\n" + $art
      + "\n\n===== INSTRUCTIONS =====\n" + $instr
    )}]}],
   generationConfig:{temperature:0,maxOutputTokens:32768,responseMimeType:"application/json",responseSchema:$schema}}')

RESP=$(curl -s -w $'\n%{http_code}' -H "x-goog-api-key: $GEMINI_API_KEY" -H "Content-Type: application/json" \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent" -d "$REQ" 2>/dev/null)
CODE=$(printf '%s\n' "$RESP" | tail -1)
BODY=$(printf '%s\n' "$RESP" | sed '$d')
if [ "$CODE" != "200" ]; then
  echo "ERROR: Gemini HTTP $CODE — $(printf '%s' "$BODY" | jq -r '.error.message // "(no message)"' 2>/dev/null)" >&2
  exit 1
fi

VERDICT_JSON=$(printf '%s' "$BODY" | jq -r '.candidates[0].content.parts[0].text // empty' 2>/dev/null)
RESOLVED=$(printf '%s' "$BODY" | jq -r '.modelVersion // "unknown"' 2>/dev/null)
USAGE=$(printf '%s' "$BODY" | jq -c '.usageMetadata // {}' 2>/dev/null)
[ -n "$VERDICT_JSON" ] || { echo "ERROR: empty verdict (thinking tokens may have starved output; raise maxOutputTokens)" >&2; exit 1; }
if ! echo "$VERDICT_JSON" | jq -e '.criterion_scores | length == 5' >/dev/null 2>&1; then
  # Loud AND inspectable: keep the full raw response + say WHY generation stopped (a MAX_TOKENS truncation and a
  # wrong-shape answer look identical in a 600-char head).
  DUMP="${TMPDIR:-/tmp}/gemini-judge-last-failure.json"; printf '%s' "$BODY" > "$DUMP"
  echo "ERROR: malformed verdict JSON — finishReason=$(printf '%s' "$BODY" | jq -r '.candidates[0].finishReason // "?"') ·" \
       "usage=$(printf '%s' "$BODY" | jq -c '.usageMetadata // {}') · valid_json=$(echo "$VERDICT_JSON" | jq -e . >/dev/null 2>&1 && echo yes || echo no) ·" \
       "criteria=$(echo "$VERDICT_JSON" | jq -r '.criterion_scores|length' 2>/dev/null || echo '?') · full response: $DUMP" >&2
  exit 1
fi

# --- @5: the HARNESS computes the composite + verdict (the model never does) -----------------------
# Per-criterion caps first (spec drift → correctness ≤0.70 · dangling ref → completeness ≤0.60 · command skeleton →
# completeness ≤0.35), then the weighted sum, then composite caps (confidence-honesty ≤0.65 · deep_read padding ≤0.65 ·
# dangling ≤0.60). Caps only ever LOWER a score. flat_ceiling = all five RAW scores == 1.0 (low-information; the
# quorum escalates instead of auto-accepting).
echo "$VERDICT_JSON" | jq -e '(.criterion_scores|map(.id)|sort) == ["anti_pattern_avoidance","completeness","convention_adherence","correctness","diagnostics"]' >/dev/null 2>&1 \
  || { echo "ERROR: verdict JSON lacks exactly the 5 criteria:" >&2; echo "$VERDICT_JSON" | head -c 600 >&2; exit 1; }
# every criterion score must be a real number: jq sorts null BELOW every number, so an absent score would be
# silently clamped to 0 by the range-clamp below ("model skipped a criterion" would become "worst possible defect").
echo "$VERDICT_JSON" | jq -e '[.criterion_scores[].score] | all(type == "number")' >/dev/null 2>&1 \
  || { echo "ERROR: a criterion score is missing or non-numeric:" >&2; echo "$VERDICT_JSON" | jq -c '.criterion_scores' >&2; exit 1; }
# a cap flag with no matching defect is evidence-free: cap anyway (fail-safe = lower), but say so.
echo "$VERDICT_JSON" | jq -r '[.cap_flags | to_entries[] | select(.value)] as $f | if ($f|length) > 0 and ((.defects|length) == 0)
  then "  ⚠️  cap flag(s) set with an EMPTY defects[] (" + ([$f[].key] | join(", ")) + ") — capping anyway; evidence missing." else empty end' >&2
HAS_DANGLING=$([ -n "$DANGLING" ] && echo true || echo false)
VERDICT_JSON=$(echo "$VERDICT_JSON" | jq -c --arg atype "$ATYPE" --argjson dangling "$HAS_DANGLING" '
  def cap(id; max; why): .criterion_scores |= map(if .id==id and .score>max then (.score=max | .reasoning=(.reasoning+" [harness cap "+(max|tostring)+": "+why+"]")) else . end);
  (.criterion_scores|map(.score)|all(. == 1)) as $flat
  | .flat_ceiling = $flat
  | .criterion_scores |= map(.score |= (if . > 1 then 1 elif . < 0 then 0 else . end))
  | (if .cap_flags.spec_drift then cap("correctness"; 0.70; "spec drift") else . end)
  | (if $dangling then cap("completeness"; 0.60; "check-refs: referenced file(s) missing") else . end)
  | (if $atype=="command" and .cap_flags.command_skeleton_absent then cap("completeness"; 0.35; "command skeleton absent") else . end)
  | (.criterion_scores|map({(.id): .score})|add) as $s
  | ($s.correctness*0.30 + $s.completeness*0.20 + $s.convention_adherence*0.20 + $s.anti_pattern_avoidance*0.20 + $s.diagnostics*0.10) as $raw
  | ([$raw]
     + (if .cap_flags.confidence_honesty_violation then [0.65] else [] end)
     + (if $atype=="deep_read" and .cap_flags.density_padding then [0.65] else [] end)
     + (if $dangling then [0.60] else [] end) | min) as $capped
  | .raw_score = (($raw*1000|round)/1000)
  | .weighted_score = (($capped*1000|round)/1000)
  | .confidence_honesty_violation = .cap_flags.confidence_honesty_violation
  | .verdict = (if .weighted_score >= 0.70 then "pass" else "flag" end)')
[ -n "$DANGLING" ] && echo "  check-refs: dangling reference(s) present → completeness/composite capped ≤0.60 deterministically" >&2
[ "$(echo "$VERDICT_JSON" | jq -r '.flat_ceiling')" = "true" ] && echo "  ⚠️  FLAT CEILING: all five criteria 1.0 — low-information; the quorum will escalate instead of auto-accepting." >&2

WS=$(echo "$VERDICT_JSON" | jq -r '.weighted_score'); VD=$(echo "$VERDICT_JSON" | jq -r '.verdict')
echo "== Gemini judge ($RESOLVED) — $ARTIFACT =>  $WS ($VD)  [set:$CALSET]"
echo "$VERDICT_JSON" | jq -r '.criterion_scores[] | "  \(.id) \(.score) — \(.reasoning)"'
echo "$VERDICT_JSON" | jq -r '"  defects: \(.defects|length) (\([.defects[]|select(.severity=="major")]|length) major) · checks: \(.checks_performed|length) · raw \(.raw_score) → capped \(.weighted_score)"'
echo "$VERDICT_JSON" | jq -r '.defects[] | "    - [\(.severity)/\(.criterion)] \(.location): \(.description)" + (if .spec_ref != "" then " (\(.spec_ref))" else "" end)'
echo "  usage: $USAGE"

if [ "$PRINT_ONLY" = "1" ]; then exit 0; fi

# --- write run-log line (schema-stable) ---
SID="${CLAUDE_CODE_SESSION_ID:-_nosession}"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ); DAY=$(date -u +%Y-%m-%d)
SLUG=$(basename "$(dirname "$ARTIFACT")" 2>/dev/null); B=$(basename "$ARTIFACT")
[ "$B" = "SKILL.md" ] || SLUG=$(echo "$B" | sed 's/\.[^.]*$//')
RID="${LABEL:-gemini-$(echo "$SLUG" | tr -c 'a-zA-Z0-9' '-')}"
OUT=".claude/evals/logs/${DAY}-${SLUG}-${RID}.jsonl"
jq -nc \
  --arg rid "$RID" --arg ts "$TS" --arg art "$ARTIFACT" --arg atype "$ATYPE" \
  --arg jm "gemini:$RESOLVED" --arg sid "$SID" --arg calset "$CALSET" --arg rver "$RUBRIC_VER" \
  --arg dangling "$DANGLING" --arg parity "$PARITY" --argjson v "$VERDICT_JSON" --argjson usage "$USAGE" \
  '{run_id:$rid, timestamp:$ts, artifact:$art, artifact_type:$atype, rubric:$rver,
    judge_model:$jm, session_id:$sid, criterion_scores:$v.criterion_scores,
    weighted_score:$v.weighted_score, verdict:$v.verdict, alex_ack:null,
    confidence_honesty_violation:($v.confidence_honesty_violation // false),
    defects:($v.defects // []), checks_performed:($v.checks_performed // []), cap_flags:($v.cap_flags // {}),
    raw_score:$v.raw_score, flat_ceiling:($v.flat_ceiling // false), scoring:"harness-recomputed",
    dangling_refs:($dangling | if .=="" then [] else split("\n") end),
    calibration_set:$calset, judge_provider:"google", evidence_parity:($parity=="true"), usage:$usage}' > "$OUT"
echo "  logged → $OUT"
