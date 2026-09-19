#!/usr/bin/env bash
# quorum-merge.sh — merge the two build-quality judge seats (Claude/Sonnet + Gemini) into one `quorum` record.
# Each seat writes its own schema-stable run-log line separately; THIS writes the additive quorum block
# (spec §6 + the judge-trigger/merge mechanic). No seat needs the other's result at its own write time.
# Spec: .claude/references/cross-provider-judge.md.
#
# Usage:
#   quorum-merge.sh --artifact <path> --mode interactive|autonomous \
#     --claude-verdict '<json>'  --gemini-log <path>|--gemini-verdict '<json>' \
#     [--claude-run-id <id>] [--gemini-run-id <id>] [--label <run>] [--print-only]
#
# Each verdict JSON must carry at least {"verdict":"pass|flag","weighted_score":0.0}; per-criterion scores
# (criterion_scores[] or a criteria{} map) are used when present to detect a flat ceiling.
# Resolution (2026-09-19, YED-206 — pass/flag agreement alone is NOT independence):
#   escalation reasons = verdict_mismatch · score_divergence (|claude-gemini| >= QUORUM_DIVERGENCE, default 0.15)
#                        · flat_ceiling:<seat> (all five criteria 1.0 = low-information) · gemini_no_evidence_parity
#   no reasons          -> auto (final = agreed verdict)
#   reasons + interactive -> escalated (final = agreed verdict if verdicts match, else flag; pending Alex's ack)
#   reasons + autonomous  -> failsafe_flag (final = flag, queued for later human review).
# Why: the Gemini seat returned a flat 1.0 on 20/23 real artifacts and "agreed" with every Sonnet pass; 14 of 16
# historical quorums were auto-accepted on that basis. Triage: .claude/notes/gemini-judge-triage-2026-09-19.md.
# Exit 0 on success; prints the quorum summary to stdout and (if written) the log path.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true

ARTIFACT=""; MODE="interactive"; CV=""; GV=""; GLOG=""; CRID=""; GRID=""; LABEL=""; PRINT_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --artifact) ARTIFACT="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --claude-verdict) CV="$2"; shift 2;;
    --gemini-verdict) GV="$2"; shift 2;;
    --gemini-log) GLOG="$2"; shift 2;;
    --claude-run-id) CRID="$2"; shift 2;;
    --gemini-run-id) GRID="$2"; shift 2;;
    --label) LABEL="$2"; shift 2;;
    --print-only) PRINT_ONLY=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -n "$ARTIFACT" ] || { echo "ERROR: --artifact required" >&2; exit 2; }
[ -n "$CV" ] || { echo "ERROR: --claude-verdict <json> required" >&2; exit 2; }
case "$MODE" in interactive|autonomous) ;; *) echo "ERROR: --mode must be interactive|autonomous" >&2; exit 2;; esac

# --- gemini verdict: inline JSON or read from its run-log line ---
if [ -z "$GV" ]; then
  [ -n "$GLOG" ] && [ -r "$GLOG" ] || { echo "ERROR: need --gemini-verdict or a readable --gemini-log" >&2; exit 2; }
  # a log file may hold several appended runs — the LAST line is the run being merged
  GV=$(tail -1 "$GLOG" | jq -c '{verdict, weighted_score, criterion_scores, flat_ceiling, evidence_parity}' 2>/dev/null) \
    || { echo "ERROR: could not parse gemini verdict from $GLOG" >&2; exit 2; }
  [ -z "$GRID" ] && GRID=$(tail -1 "$GLOG" | jq -r '.run_id // empty' 2>/dev/null)
fi

# --- parse verdicts (fail loudly on malformed input rather than silently mis-resolving) ---
CVD=$(printf '%s' "$CV" | jq -r '.verdict' 2>/dev/null); CWS=$(printf '%s' "$CV" | jq -r '.weighted_score' 2>/dev/null)
GVD=$(printf '%s' "$GV" | jq -r '.verdict' 2>/dev/null); GWS=$(printf '%s' "$GV" | jq -r '.weighted_score' 2>/dev/null)
for v in "$CVD" "$GVD"; do case "$v" in pass|flag) ;; *) echo "ERROR: a verdict is not pass|flag (got claude='$CVD' gemini='$GVD')" >&2; exit 2;; esac; done

# --- low-information + divergence signals ---
THRESH="${QUORUM_DIVERGENCE:-0.15}"
flat() {  # all five criteria == 1.0 (from criterion_scores[] or a criteria{} map, or an explicit flat_ceiling flag)
  printf '%s' "$1" | jq -r '
    if .flat_ceiling == true then "true"
    elif (.criterion_scores|type)=="array" and (.criterion_scores|length)==5 then ([.criterion_scores[].score]|all(. == 1)|tostring)
    elif (.criteria|type)=="object" and (.criteria|length)==5 then ([.criteria[]|(if type=="object" then .score else . end)]|all(. == 1)|tostring)
    else "false" end' 2>/dev/null
}
CFLAT=$(flat "$CV"); GFLAT=$(flat "$GV")
GPARITY=$(printf '%s' "$GV" | jq -r 'if .evidence_parity == false then "false" else "true" end' 2>/dev/null)
DIV=$(jq -n --argjson c "$CWS" --argjson g "$GWS" '(($c-$g)|fabs*1000|round)/1000')
REASONS=()
[ "$CVD" != "$GVD" ] && REASONS+=("verdict_mismatch")
[ "$(jq -n --argjson d "$DIV" --argjson t "$THRESH" '$d >= $t')" = "true" ] && REASONS+=("score_divergence")
[ "$CFLAT" = "true" ] && REASONS+=("flat_ceiling:claude")
[ "$GFLAT" = "true" ] && REASONS+=("flat_ceiling:gemini")
[ "$GPARITY" = "false" ] && REASONS+=("gemini_no_evidence_parity")

# --- resolve ---
if [ "$CVD" = "$GVD" ]; then AGREE=true; else AGREE=false; fi
if [ ${#REASONS[@]} -eq 0 ]; then
  RESOLUTION="auto"; FINAL="$CVD"
elif [ "$MODE" = "autonomous" ]; then
  RESOLUTION="failsafe_flag"; FINAL="flag"
else
  RESOLUTION="escalated"; if [ "$AGREE" = true ]; then FINAL="$CVD"; else FINAL="flag"; fi
fi
REASONS_JSON=$(printf '%s\n' "${REASONS[@]:-}" | jq -R . | jq -sc 'map(select(. != ""))')

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ); DAY=$(date -u +%Y-%m-%d)
B=$(basename "$ARTIFACT"); SLUG=$(basename "$(dirname "$ARTIFACT")" 2>/dev/null)
[ "$B" = "SKILL.md" ] || SLUG=$(echo "$B" | sed 's/\.[^.]*$//')
RID="${LABEL:-quorum-$(echo "$SLUG" | tr -c 'a-zA-Z0-9' '-')}"

echo "== quorum ($MODE) — $ARTIFACT"
echo "   claude/sonnet: $CVD ($CWS)   gemini: $GVD ($GWS)   agree: $AGREE   divergence: $DIV   ->  $RESOLUTION   final: $FINAL"
[ ${#REASONS[@]} -gt 0 ] && echo "   escalation reasons: ${REASONS[*]}"
[ "$RESOLUTION" = "escalated" ] && echo "   ACTION: surface both seats' per-criterion reasoning side-by-side; ask Alex agree/disagree -> quorum alex_ack."
[ "$RESOLUTION" = "failsafe_flag" ] && echo "   NOTE: autonomous split -> failed safe to FLAG; queued for later human review (non-destructive)."

if [ "$PRINT_ONLY" = "1" ]; then exit 0; fi

SID="${CLAUDE_CODE_SESSION_ID:-_nosession}"
OUT=".claude/evals/logs/${DAY}-${SLUG}-${RID}.jsonl"
jq -nc \
  --arg rid "$RID" --arg ts "$TS" --arg art "$ARTIFACT" --arg sid "$SID" --arg mode "$MODE" \
  --arg crid "$CRID" --arg grid "$GRID" --arg res "$RESOLUTION" --arg final "$FINAL" \
  --argjson agree "$AGREE" --argjson div "$DIV" --argjson reasons "$REASONS_JSON" \
  --arg cflat "$CFLAT" --arg gflat "$GFLAT" --arg gparity "$GPARITY" \
  --arg cvd "$CVD" --arg gvd "$GVD" --argjson cws "$CWS" --argjson gws "$GWS" \
  '{run_id:$rid, timestamp:$ts, artifact:$art, session_id:$sid, record_type:"quorum",
    claude:{verdict:$cvd, weighted_score:$cws, run_id:$crid},
    gemini:{verdict:$gvd, weighted_score:$gws, run_id:$grid},
    agree:$agree, resolution:$res, final_verdict:$final, mode:$mode,
    divergence:$div, escalation_reasons:$reasons, flat_ceiling:{claude:($cflat=="true"), gemini:($gflat=="true")},
    gemini_evidence_parity:($gparity=="true"), weak_corroboration:($gflat=="true" or $gparity=="false"),
    quorum_rules:"2026-09-19 divergence+flat-ceiling (YED-206)", alex_ack:null}' > "$OUT"
echo "   logged -> $OUT"
