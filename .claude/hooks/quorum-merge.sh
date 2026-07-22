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
# Each verdict JSON must carry at least {"verdict":"pass|flag","weighted_score":0.0}.
# Resolution: agree -> auto (final = agreed verdict); disagree+interactive -> escalated (final = flag, pending Alex);
#             disagree+autonomous -> failsafe_flag (final = flag, queued for later human review).
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
  GV=$(jq -c '{verdict:.verdict, weighted_score:.weighted_score}' "$GLOG" 2>/dev/null) \
    || { echo "ERROR: could not parse gemini verdict from $GLOG" >&2; exit 2; }
  [ -z "$GRID" ] && GRID=$(jq -r '.run_id // empty' "$GLOG" 2>/dev/null)
fi

# --- parse verdicts (fail loudly on malformed input rather than silently mis-resolving) ---
CVD=$(printf '%s' "$CV" | jq -r '.verdict' 2>/dev/null); CWS=$(printf '%s' "$CV" | jq -r '.weighted_score' 2>/dev/null)
GVD=$(printf '%s' "$GV" | jq -r '.verdict' 2>/dev/null); GWS=$(printf '%s' "$GV" | jq -r '.weighted_score' 2>/dev/null)
for v in "$CVD" "$GVD"; do case "$v" in pass|flag) ;; *) echo "ERROR: a verdict is not pass|flag (got claude='$CVD' gemini='$GVD')" >&2; exit 2;; esac; done

# --- resolve ---
if [ "$CVD" = "$GVD" ]; then
  AGREE=true; RESOLUTION="auto"; FINAL="$CVD"
else
  AGREE=false; FINAL="flag"
  if [ "$MODE" = "autonomous" ]; then RESOLUTION="failsafe_flag"; else RESOLUTION="escalated"; fi
fi

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ); DAY=$(date -u +%Y-%m-%d)
B=$(basename "$ARTIFACT"); SLUG=$(basename "$(dirname "$ARTIFACT")" 2>/dev/null)
[ "$B" = "SKILL.md" ] || SLUG=$(echo "$B" | sed 's/\.[^.]*$//')
RID="${LABEL:-quorum-$(echo "$SLUG" | tr -c 'a-zA-Z0-9' '-')}"

echo "== quorum ($MODE) — $ARTIFACT"
echo "   claude/sonnet: $CVD ($CWS)   gemini: $GVD ($GWS)   agree: $AGREE   ->  $RESOLUTION   final: $FINAL"
[ "$RESOLUTION" = "escalated" ] && echo "   ACTION: surface both seats' per-criterion reasoning side-by-side; ask Alex agree/disagree -> quorum alex_ack."
[ "$RESOLUTION" = "failsafe_flag" ] && echo "   NOTE: autonomous split -> failed safe to FLAG; queued for later human review (non-destructive)."

if [ "$PRINT_ONLY" = "1" ]; then exit 0; fi

SID="${CLAUDE_CODE_SESSION_ID:-_nosession}"
OUT=".claude/evals/logs/${DAY}-${SLUG}-${RID}.jsonl"
jq -nc \
  --arg rid "$RID" --arg ts "$TS" --arg art "$ARTIFACT" --arg sid "$SID" --arg mode "$MODE" \
  --arg crid "$CRID" --arg grid "$GRID" --arg res "$RESOLUTION" --arg final "$FINAL" \
  --argjson agree "$AGREE" \
  --arg cvd "$CVD" --arg gvd "$GVD" --argjson cws "$CWS" --argjson gws "$GWS" \
  '{run_id:$rid, timestamp:$ts, artifact:$art, session_id:$sid, record_type:"quorum",
    claude:{verdict:$cvd, weighted_score:$cws, run_id:$crid},
    gemini:{verdict:$gvd, weighted_score:$gws, run_id:$grid},
    agree:$agree, resolution:$res, final_verdict:$final, mode:$mode, alex_ack:null}' > "$OUT"
echo "   logged -> $OUT"
