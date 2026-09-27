#!/usr/bin/env bash
# _run_in_progress.sh — shared helper for the Stop-hook gates (deep-read-gate.sh, substrate-gate.sh).
#
# WHY (2026-09-27, YED-205 acceptance run): Claude Code fires `Stop` at EVERY turn end, not once at
# session close. Both gates were written as if Stop meant "run close", so a run that legitimately
# had a `pending` ledger row for 30+ minutes (Deep Read rendering, a background graph write, a
# human approval) was blocked on every turn, re-invoked the model each time, and logged one FALSE
# failure row per turn (9 rows in one session). The gate's intent — a skipped step must not close
# green — is right; its trigger granularity was wrong.
#
# THE SIGNAL: the event claim (.claude/hooks/event-claim.py, YED-213). A run claims its event at
# Step 1.0 and releases it at Step 6 (or the claim expires after ttl_hours). While THIS session
# holds a live claim, pending rows mean "in progress", not "skipped". The first turn end after the
# claim is released or expires is the real gate.
#
# Contract: `run_in_progress "<session_id>"` → exit 0 (and sets RUN_IN_PROGRESS_CLAIM to the claim
# file) when a claim exists with session_id == <session_id>, released_at == null, and
# (heartbeat // claimed_at) + ttl_hours*3600 > now. Anything else — no id, `_pending`, missing
# dir, unparseable timestamp, corrupt file — returns 1, so the gate stays STRICT (fail-closed).
# EVENT_CLAIM_DIR overrides the machine-global default for tests only.

run_in_progress() {
  local sid="$1" dir="${EVENT_CLAIM_DIR:-$HOME/.claude/event-claims}" now f
  RUN_IN_PROGRESS_CLAIM=""
  [ -z "$sid" ] && return 1
  [ "$sid" = "_pending" ] && return 1
  [ -d "$dir" ] || return 1
  command -v jq >/dev/null 2>&1 || return 1
  now=$(date -u +%s)
  for f in "$dir"/*.json; do
    [ -f "$f" ] || continue
    if jq -e --arg s "$sid" --argjson now "$now" '
          (.session_id == $s)
          and (.released_at == null)
          and ((((.heartbeat // .claimed_at // "") | fromdate?) // 0) + (((.ttl_hours // 4) | tonumber? // 4) * 3600) > $now)
        ' "$f" >/dev/null 2>&1; then
      RUN_IN_PROGRESS_CLAIM="$f"
      return 0
    fi
  done
  return 1
}

# already_logged <fail_log> <event_name> <session_id> <events_json>
# → exit 0 when a failure row for the same session + same event set already exists (log-once guard).
already_logged() {
  local log="$1" ev_name="$2" sid="$3" events="$4"
  [ -f "$log" ] || return 1
  command -v jq >/dev/null 2>&1 || return 1
  [ -n "$(jq -c --arg n "$ev_name" --arg s "$sid" --argjson ev "$events" \
          'select(type=="object" and .event==$n and .session==$s and .events==$ev)' "$log" 2>/dev/null | head -1)" ]
}
