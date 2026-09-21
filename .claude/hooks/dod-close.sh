#!/usr/bin/env bash
# DoD-close writer — the missing build_meta producer (closes the rigor loop).
#
# The telemetry Stop hook (build-session-emit.sh, lines 68-75) READS
#   .claude/.state/<SESSION_ID>.build_meta
# for the optional semantic fields {dod_met, dod_waived, correction_rounds} and folds them into
# the authoritative build_session row. Nothing in the repo WROTE that file — so those three fields
# were null in 100% of telemetry rows. This script is that writer.
#
# Contract: .claude/references/build-session-contract.md (v1) — write EXACTLY the three keys, no more.
#   The Stop hook freezes the shape; adding fields here does nothing but risk confusion.
#
# Session-id discovery (verified 2026-07-09): $CLAUDE_CODE_SESSION_ID in an in-session Bash call is
#   identical to the .session_id the Stop hook emits. So the session names its own build_meta file
#   deterministically — no SessionStart stamp, no schema change. If the var is ever absent (--resume,
#   Dock launch, or when run inside a subagent), we fall back to `_pending` and the Stop hook
#   reconciles it (see build-session-emit.sh). NOTE the var is CLAUDE_CODE_SESSION_ID, not
#   CLAUDE_SESSION_ID (that one is unset).
#
# Usage:
#   .claude/hooks/dod-close.sh --dod-met true|false [--dod-waived true|false] \
#       [--correction-rounds N] [--reason "one-liner" ...]
#
#   --dod-met            all applicable DoD items satisfied this build (bool)
#   --dod-waived         one or more items were waived-with-reason (bool; default false)
#   --correction-rounds  count of corrective rounds this session (int; optional -> null if omitted)
#   --reason             a waiver reason (repeatable; each appended to the waiver log). Required when
#                        --dod-waived true. Format "item: why" is encouraged but free-text is fine.
#                        A judge/item-4 waiver must contain "no gradable artifact" or a YED-/GTM- issue ID
#                        (YED-201 Fix 1A) or the whole call is rejected with exit 2.
#
# Content-gated: writes only booleans/ints + Alex's own short reason strings — never artifact bodies.
# MUST run in the MAIN conversation (where the Stop hook fires for this same session id), not a subagent.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

DOD_MET=null
DOD_WAIVED=false
CORRECTION_ROUNDS=null
REASONS=()
RECORDS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --dod-met)           DOD_MET="${2:-null}"; shift 2 ;;
    --dod-waived)        DOD_WAIVED="${2:-false}"; shift 2 ;;
    --correction-rounds) CORRECTION_ROUNDS="${2:-null}"; shift 2 ;;
    --reason)            REASONS+=("${2:-}"); shift 2 ;;
    --record)            RECORDS+=("${2:-}"); shift 2 ;;   # a note for the log that is NOT a waiver (e.g. a
                                                           # redemption). Counting these inflated the waiver
                                                           # rate by 2 of 12 in the 2026-09-21 review.
    *) echo "dod-close: unknown arg '$1'" >&2; shift ;;
  esac
done

# Validate booleans (anything not exactly true/false -> null for dod_met, false for dod_waived)
case "$DOD_MET" in true|false|null) ;; *) DOD_MET=null ;; esac
case "$DOD_WAIVED" in true|false) ;; *) DOD_WAIVED=false ;; esac
# correction_rounds: keep only if it's a non-negative integer, else null
case "$CORRECTION_ROUNDS" in ''|*[!0-9]*) CORRECTION_ROUNDS=null ;; esac

if [ "$DOD_WAIVED" = "true" ] && [ ${#REASONS[@]} -eq 0 ]; then
  echo "dod-close: --dod-waived true requires at least one --reason \"<one-liner>\"" >&2
  exit 2
fi

# --- judge-waiver rule (YED-201 Fix 1A, ruled 2026-09-19) ---
# "Advisory" means the judge's verdict doesn't GATE, not that running it is optional. 8 judge waivers
# accumulated 07-15 -> 09-18 under "advisory / next session" and the promised runs never happened.
# A waiver of DoD item 4 must name EITHER that there is no gradable artifact, OR the Linear issue that
# holds the make-up run (the container rule, applied to waivers). Rejected before anything is written.
# Limit (by design): this checks the FORMAT, not that the named issue is the real make-up run; /rigor-review
# recounts the class weekly. Judge-reviewed twice 2026-09-19 (Sonnet reproduced 7 bypasses; all closed).
for r in "${REASONS[@]}"; do
  # Split "label: reason" on the first colon OUTSIDE parentheses, so a colon inside the label
  # ("judge (context: YED-999 …): out of time") can't smuggle an ID into the reason.
  r=$(printf '%s' "$r" | sed 's/：/:/g; s/﹕/:/g')   # full-width / small colons count as the separator
  cut_at=$(printf '%s' "$r" | awk '{d=0; for(i=1;i<=length($0);i++){c=substr($0,i,1); if(c ~ /[([{]/)d++; else if(c ~ /[])}]/&&d>0)d--; else if(c==":"&&d==0){print i; exit}}}')
  if [ -n "$cut_at" ]; then
    item_part="${r:0:$((cut_at-1))}"; why_part="${r:$cut_at}"
  else
    item_part="$r"; why_part=""            # no label: an item-4 waiver MUST use "judge: <reason>" (below)
  fi
  # Trigger on any label that means DoD item 4: "judge", "item 4", "item4", or a bare "4".
  if printf '%s' "$item_part" | grep -qiE 'judge|item ?(4|four)|^[[:space:]]*(4|four)[[:space:]]*$'; then
    # The make-up pointer must be in the REASON (after the label), not anywhere in the string.
    if ! printf '%s' "$why_part" | grep -qiE 'no gradable artifact|(YED|GTM)-[0-9]+'; then
      echo "dod-close: judge waiver rejected: \"$r\"" >&2
      echo "  A DoD item-4 (judge) waiver must be written 'judge: <reason>', and the reason must say" >&2
      echo "  'no gradable artifact' OR name the Linear" >&2
      echo "  issue that holds the make-up run (e.g. 'judge: run in fresh session, YED-123'). YED-201 Fix 1A." >&2
      exit 2
    fi
  fi
done

WAIVER_LOG_DEFAULT=".claude/artifacts/dod-waivers.jsonl"
SID="${CLAUDE_CODE_SESSION_ID:-_pending}"
STATE_DIR=".claude/.state"
META_FILE="$STATE_DIR/${SID}.build_meta"
mkdir -p "$STATE_DIR"

# --- write the build_meta (exactly the 3 contract keys; last-write-wins = DoD state at close) ---
jq -nc \
  --argjson dod_met "$DOD_MET" \
  --argjson dod_waived "$DOD_WAIVED" \
  --argjson corr "$CORRECTION_ROUNDS" \
  '{dod_met:$dod_met, dod_waived:$dod_waived, correction_rounds:$corr}' \
  > "$META_FILE" 2>/dev/null || { echo "dod-close: failed to write $META_FILE" >&2; exit 1; }

# --- append waiver reasons (the reason log rigor-review reads for clustering; build_meta carries only the bool) ---
if [ "$DOD_WAIVED" = "true" ]; then
  WAIVER_LOG=".claude/artifacts/dod-waivers.jsonl"
  mkdir -p "$(dirname "$WAIVER_LOG")"
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  for r in "${REASONS[@]}"; do
    [ -z "$r" ] && continue
    # split "item: reason" if present, else item=null
    if printf '%s' "$r" | grep -q ':'; then
      ITEM=$(printf '%s' "$r" | sed 's/:.*//' | sed 's/^ *//;s/ *$//')
      WHY=$(printf '%s' "$r" | sed 's/^[^:]*://' | sed 's/^ *//;s/ *$//')
    else
      ITEM=null; WHY="$r"
    fi
    if [ "$ITEM" = "null" ]; then
      jq -nc --arg ts "$TS" --arg sid "$SID" --arg why "$WHY" \
        '{ts:$ts, session_id:$sid, item:null, reason:$why, type:"waiver"}' >> "$WAIVER_LOG"
    else
      jq -nc --arg ts "$TS" --arg sid "$SID" --arg item "$ITEM" --arg why "$WHY" \
        '{ts:$ts, session_id:$sid, item:$item, reason:$why, type:"waiver"}' >> "$WAIVER_LOG"
    fi
  done
fi

for r in "${RECORDS[@]:-}"; do
  [ -z "$r" ] && continue
  mkdir -p "$(dirname "$WAIVER_LOG_DEFAULT")" 2>/dev/null
  jq -nc --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg sid "$SID" --arg why "$r" \
    '{ts:$ts, session_id:$sid, item:"record", reason:$why, type:"record"}' >> ".claude/artifacts/dod-waivers.jsonl"
done

echo "dod-close: wrote $META_FILE (dod_met=$DOD_MET dod_waived=$DOD_WAIVED correction_rounds=$CORRECTION_ROUNDS)"
exit 0
