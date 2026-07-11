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
#
# Content-gated: writes only booleans/ints + Alex's own short reason strings — never artifact bodies.
# MUST run in the MAIN conversation (where the Stop hook fires for this same session id), not a subagent.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

DOD_MET=null
DOD_WAIVED=false
CORRECTION_ROUNDS=null
REASONS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --dod-met)           DOD_MET="${2:-null}"; shift 2 ;;
    --dod-waived)        DOD_WAIVED="${2:-false}"; shift 2 ;;
    --correction-rounds) CORRECTION_ROUNDS="${2:-null}"; shift 2 ;;
    --reason)            REASONS+=("${2:-}"); shift 2 ;;
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
        '{ts:$ts, session_id:$sid, item:null, reason:$why}' >> "$WAIVER_LOG"
    else
      jq -nc --arg ts "$TS" --arg sid "$SID" --arg item "$ITEM" --arg why "$WHY" \
        '{ts:$ts, session_id:$sid, item:$item, reason:$why}' >> "$WAIVER_LOG"
    fi
  done
fi

echo "dod-close: wrote $META_FILE (dod_met=$DOD_MET dod_waived=$DOD_WAIVED correction_rounds=$CORRECTION_ROUNDS)"
exit 0
