#!/usr/bin/env bash
# run-canaries.sh — the scheduled half of the judge control set (YED-209 build step 8).
#
# controls.py can already run controls on demand. What was missing is the thing that makes the trust ladder
# self-enforcing: something that runs a SMALL fixed sample on a schedule, records the result where the quorum
# can see it, and lets a seat that fails be demoted automatically. Without it, "canaries fresh" in the spec's
# auto-pass rule was a condition nobody ever checked.
#
#   run-canaries.sh [--seat openai|gemini] [--size N] [--full] [--dry-run] [--reason "why"]
#
# Writes .claude/evals/controls/state.json: per seat, the last run's timestamp, the resolved model id, the
# per-item outcomes, and pass/fail. calibration_stats.py --gate reads it and demotes a seat one rung on two
# consecutive failures, or when the resolved model id changed and no canary has passed since.
#
# Cheap by design: the default 3-item sample on gpt-5.4-mini is ~$0.13. Run it before /rigor-review and after
# any seat config change. Exit: 0 all green · 1 a seat failed · 2 usage · 4 budget.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 2

SEAT=""; SIZE=3; FULL=0; DRY=""; REASON="scheduled"
while [ $# -gt 0 ]; do
  case "$1" in
    --seat)    SEAT="$2"; shift 2;;
    --size)    SIZE="$2"; shift 2;;
    --full)    FULL=1; shift;;
    --dry-run) DRY="--dry-run"; shift;;
    --reason)  REASON="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

STATE=".claude/evals/controls/state.json"
SEATS=".claude/evals/seats.json"
[ -r "$SEATS" ] || { echo "ERROR: $SEATS unreadable" >&2; exit 2; }

# adapter-backed seats only: the Claude seat runs as a subagent and cannot be driven from a shell hook
mapfile -t IDS < <(jq -r '.seats[] | select(.runner != "agent") | .id' "$SEATS")
[ -n "$SEAT" ] && IDS=("$SEAT")
[ "$FULL" = "1" ] && SIZE=0

RC=0
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TMP=$(mktemp); echo '{}' > "$TMP"
[ -r "$STATE" ] && cp "$STATE" "$TMP"

for id in "${IDS[@]}"; do
  echo "== canary: seat $id ($([ "$SIZE" = 0 ] && echo "full set" || echo "$SIZE items"))"
  ARGS=(--seat "$id" --label-suffix="-canary-${TS//[:-]/}")
  [ "$SIZE" != "0" ] && ARGS+=(--limit "$SIZE")
  [ -n "$DRY" ] && ARGS+=("$DRY")
  OUT=$(python3 .claude/evals/controls.py run "${ARGS[@]}" 2>&1); echo "$OUT" | sed 's/^/   /'
  [ -n "$DRY" ] && continue

  # parse the summary controls.py already prints; a seat is GREEN only if every item matched its label
  MISSES=$(printf '%s\n' "$OUT" | grep -c '^  ✗' || true)
  SCORED=$(printf '%s\n' "$OUT" | grep -cE '^  (✓|✗)' || true)
  MODEL=$(jq -r --arg i "$id" '.seats[]|select(.id==$i)|.model // "default"' "$SEATS")
  # the resolved model id is what actually answered — a silent snapshot swap must invalidate freshness
  RESOLVED=$(ls -t .claude/evals/logs/*canary-${TS//[:-]/}*.jsonl 2>/dev/null | head -1 \
             | xargs -I{} sh -c 'tail -1 {} | jq -r ".judge_model_resolved // .judge_model // \"?\""' 2>/dev/null || echo "?")
  if [ "$SCORED" -eq 0 ]; then
    STATUS="error"; RC=1
  elif [ "$MISSES" -eq 0 ]; then
    STATUS="pass"
  else
    STATUS="fail"; RC=1
  fi
  echo "   -> $STATUS ($((SCORED-MISSES))/$SCORED matched their label; model $RESOLVED)"

  jq --arg i "$id" --arg ts "$TS" --arg st "$STATUS" --arg m "$MODEL" --arg r "$RESOLVED" \
     --arg why "$REASON" --argjson scored "$SCORED" --argjson misses "$MISSES" \
     '.[$i] = {last_run:$ts, status:$st, model:$m, model_resolved:$r, scored:$scored, misses:$misses,
               reason:$why,
               consecutive_failures: (if $st=="pass" then 0 else ((.[$i].consecutive_failures // 0) + 1) end)}' \
     "$TMP" > "$TMP.new" && mv "$TMP.new" "$TMP"
done

if [ -z "$DRY" ]; then
  mkdir -p "$(dirname "$STATE")"
  jq -S . "$TMP" > "$STATE"
  echo "state -> $STATE"
fi
rm -f "$TMP"
exit $RC
