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

ARTIFACT=""; ATYPE="skill"; CALSET="prospective"; CONTEXT=""
MODEL="gemini-pro-latest"
RUBRIC=".claude/evals/rubrics/build-quality-v3.md"
SYSTEM=".claude/evals/prompts/judge-system.md"
LABEL=""; PRINT_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --artifact) ARTIFACT="$2"; shift 2;;
    --artifact-type) ATYPE="$2"; shift 2;;
    --calibration-set) CALSET="$2"; shift 2;;
    --context) CONTEXT="$2"; shift 2;;
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
# derive the rubric version from the rubric file (never hardcode — it drifts when the default bumps)
RUBRIC_VER=$(grep -oE 'build-quality@[0-9]+' "$RUBRIC" | head -1)
[ -n "$RUBRIC_VER" ] || RUBRIC_VER="build-quality@unknown"

# --- key (never printed) ---
set -a; . ./.env 2>/dev/null; set +a
[ -n "${GEMINI_API_KEY:-}" ] || { echo "ERROR: GEMINI_API_KEY not set in .env" >&2; exit 1; }

INSTR='You are scoring ONE build artifact. Follow the judge system rules and the rubric above.
Score each of the 5 criteria INDEPENDENTLY 0-1 with 1-3 sentences of reasoning citing the specific thing.
Scoped-quorum note: you are the INDEPENDENT cross-provider judge. Weight your judgment most on correctness and
completeness (provider-neutral). For convention_adherence and anti_pattern_avoidance you may lack this repo'\''s
house context, so judge them conservatively and say so if unsure. House-context primer (for convention_adherence/anti_pattern_avoidance): project skills in .claude/skills/ take NO alex: prefix (that prefix is for alex-plugin skills only); use notion-search NOT notion-query-data-sources; subagents cannot spawn subagents (fan-out runs from the parent thread); MCP writes are parent-thread only; Supabase as the Market-Intelligence store is sanctioned (NOT an anti-pattern), Supabase as a measurement store is tombstoned.
Return ONLY a JSON object with EXACTLY:
{"criterion_scores":[{"id":"correctness","score":0.0,"reasoning":""},{"id":"completeness","score":0.0,"reasoning":""},{"id":"convention_adherence","score":0.0,"reasoning":""},{"id":"anti_pattern_avoidance","score":0.0,"reasoning":""},{"id":"diagnostics","score":0.0,"reasoning":""}],"confidence_honesty_violation":false,"weighted_score":0.0,"verdict":"pass"}
Compute raw = correctness*0.30 + completeness*0.20 + convention_adherence*0.20 + anti_pattern_avoidance*0.20 + diagnostics*0.10 (round 3 dp). THEN apply build-quality@3 caps to get the final weighted_score: if the artifact asserts an unverified/uncited claim as verified, set confidence_honesty_violation=true and cap weighted_score<=0.65; if it references a load-bearing file that does not exist, cap<=0.60; if a command only lists agents without dispatch/output, cap<=0.35. verdict="pass" if final weighted_score>=0.70 else "flag".'

# --- build request body safely with jq (no manual escaping) ---
REQ=$(jq -n \
  --rawfile sys "$SYSTEM" --rawfile rubric "$RUBRIC" --rawfile art "$ARTIFACT" \
  --arg ctx "$CONTEXT" --arg atype "$ATYPE" --arg instr "$INSTR" --arg path "$ARTIFACT" \
  '{contents:[{parts:[{text:(
      $sys + "\n\n===== RUBRIC (version is stated in the rubric text below) =====\n" + $rubric
      + "\n\n===== ARTIFACT TYPE =====\n" + $atype
      + "\n\n===== PER-ARTIFACT CONTEXT/SPEC =====\n" + (if $ctx=="" then "(none supplied — score correctness/completeness against the artifact'\''s own stated purpose; note reduced confidence)" else $ctx end)
      + "\n\n===== ARTIFACT PATH =====\n" + $path
      + "\n\n===== ARTIFACT CONTENT =====\n" + $art
      + "\n\n===== INSTRUCTIONS =====\n" + $instr
    )}]}],
   generationConfig:{temperature:0,maxOutputTokens:16000,responseMimeType:"application/json"}}')

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
echo "$VERDICT_JSON" | jq -e '.criterion_scores | length == 5' >/dev/null 2>&1 || { echo "ERROR: malformed verdict JSON:" >&2; echo "$VERDICT_JSON" | head -c 600 >&2; exit 1; }

WS=$(echo "$VERDICT_JSON" | jq -r '.weighted_score'); VD=$(echo "$VERDICT_JSON" | jq -r '.verdict')
echo "== Gemini judge ($RESOLVED) — $ARTIFACT =>  $WS ($VD)  [set:$CALSET]"
echo "$VERDICT_JSON" | jq -r '.criterion_scores[] | "  \(.id) \(.score) — \(.reasoning)"'
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
  --argjson v "$VERDICT_JSON" --argjson usage "$USAGE" \
  '{run_id:$rid, timestamp:$ts, artifact:$art, artifact_type:$atype, rubric:$rver,
    judge_model:$jm, session_id:$sid, criterion_scores:$v.criterion_scores,
    weighted_score:$v.weighted_score, verdict:$v.verdict, alex_ack:null,
    confidence_honesty_violation:($v.confidence_honesty_violation // false),
    calibration_set:$calset, judge_provider:"google", usage:$usage}' > "$OUT"
echo "  logged → $OUT"
