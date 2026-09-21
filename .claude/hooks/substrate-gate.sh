#!/usr/bin/env bash
# Substrate gate — Stop hook — YED-160 (Knowledge Substrate W1; ADR-10)
# Spec: .claude/notes/knowledge-substrate-review-2026-09-18.md finding 6 ("make the skipped
# write a loud in-session failure — the same in-run enforcement shape as the Step-4.5 gate").
#
# Makes a silently-skipped graph write fail the run instead of closing green. The ledger is
# written by .claude/scripts/substrate.py:
#   /post-event-content 3.8b  `substrate.py ensure-event --expect-claims` -> row PENDING
#   /post-event-content 3.8c  `substrate.py stage-claims` success           -> row STAGED
#   explicit acknowledgement  `substrate.py waive --reason "..."`           -> row WAIVED (logged)
# If any row is PENDING (or a ledger line is unparseable — fail-closed), this hook:
#   - first stop attempt (interactive): decision:block, handing the agent the fix;
#   - already blocked once (stop_hook_active): persists a durable FAILED record to
#     .claude/artifacts/substrate-gate-failures.jsonl, surfaces it, and allows the stop.
#
# This is a deliberate sibling of deep-read-gate.sh (same contract, same fail-closed rules),
# kept separate so the judged Deep Read gate is not modified. Backfill runs do not use
# --expect-claims and never create rows here.
#
# Disable (emergency only): add "substrate-gate" to .hooks.disable in .claude/settings.local.json.
# Output contract: JSON on stdout. Always exit 0.

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)

STATE_DIR=".claude/.state"
FAIL_LOG=".claude/artifacts/substrate-gate-failures.jsonl"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ] && jq -e '.hooks.disable | index("substrate-gate")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
  exit 0
fi

command -v jq >/dev/null 2>&1 || exit 0

LEDGERS=()
if [ -n "$SESSION_ID" ]; then
  F="$STATE_DIR/${SESSION_ID}.substrate_gate.jsonl"
  [ ! -f "$F" ] && [ -f "$STATE_DIR/_pending.substrate_gate.jsonl" ] && F="$STATE_DIR/_pending.substrate_gate.jsonl"
  [ -f "$F" ] && LEDGERS=("$F")
else
  shopt -s nullglob
  LEDGERS=("$STATE_DIR"/*.substrate_gate.jsonl)   # empty session id: fail closed, scan all
  shopt -u nullglob
fi
[ "${#LEDGERS[@]}" -eq 0 ] && exit 0

PENDING=0
CORRUPT=0
PENDING_LIST=""
EVENTS_JSON="[]"
scan_line() {
  local line="$1" obj marker event key
  [ -z "$line" ] && return
  obj=$(printf '%s' "$line" | jq -c 'if type=="object" then . else empty end' 2>/dev/null)
  if [ -z "$obj" ]; then CORRUPT=$((CORRUPT+1)); PENDING=$((PENDING+1)); return; fi
  marker=$(printf '%s' "$obj" | jq -r '.marker // "CORRUPT"' 2>/dev/null)
  if [ "$marker" = "pending" ] || [ "$marker" = "CORRUPT" ]; then
    PENDING=$((PENDING+1))
    event=$(printf '%s' "$obj" | jq -r '.event // "(untitled event)"' 2>/dev/null)
    key=$(printf '%s' "$obj" | jq -r '.key // "?"' 2>/dev/null)
    PENDING_LIST="${PENDING_LIST}  - ${event}  ·  notion ${key:0:8}
"
    EVENTS_JSON=$(printf '%s' "$EVENTS_JSON" | jq -c --arg e "$event" --arg k "$key" '. + [{event:$e, key:$k}]' 2>/dev/null || printf '%s' "$EVENTS_JSON")
  fi
}
for L in "${LEDGERS[@]}"; do
  while IFS= read -r line || [ -n "$line" ]; do scan_line "$line"; done < "$L"
done

[ "${PENDING:-0}" -eq 0 ] && exit 0

CORRUPT_NOTE=""
[ "${CORRUPT:-0}" -gt 0 ] && CORRUPT_NOTE="
(Includes $CORRUPT unparseable ledger line(s), counted as pending — fail-closed.)"

# Freeze awareness (YED-213, 2026-09-21). The freeze and this gate watch different halves of a
# write — freeze: may it happen; gate: did it finish. substrate.py refuses frozen writes BEFORE a
# PENDING row exists, so under a freeze these rows can only predate it. Say so, and point at the
# escape valve, instead of instructing a stage-claims run the producer will refuse.
FREEZE_NOTE=""
FREEZE_FILE=".claude/references/graph-freeze.json"
if [ -f "$FREEZE_FILE" ] && jq -e '.active == true' "$FREEZE_FILE" >/dev/null 2>&1; then
  FZ_ISSUE=$(jq -r '.issue // "?"' "$FREEZE_FILE" 2>/dev/null)
  FZ_LIFTS=$(jq -r '.lifts_when // "see the file"' "$FREEZE_FILE" 2>/dev/null)
  FREEZE_NOTE="

⛔ A GRAPH-WRITE FREEZE IS ACTIVE ($FZ_ISSUE) — so option 1 will be REFUSED by substrate.py (exit 4).
These rows predate the freeze. Either waive them now with the freeze as the reason (option 2, the
normal move), or leave them pending and stage the claims once the freeze lifts: $FZ_LIFTS.
Freeze definition: $FREEZE_FILE"
fi

FAILED_MSG="⚠️ SUBSTRATE GATE: FAILED — $PENDING event(s) reached the graph (3.8b) but their learnings were never staged as claims (3.8c):

${PENDING_LIST}This is the 'decoupled quietly meant unobserved' failure the Deep Read gate exists for, on the knowledge graph. To resolve:
  1. Run /post-event-content Step 3.8c for each event above:
     .venv/bin/python .claude/scripts/substrate.py stage-claims --manifest <m.json> --brief <brief.md> --brief-ref notion:<brief id>
     (idempotent; the ledger flips to STAGED on success); OR
  2. If there is genuinely no brief to stage, acknowledge it (this is LOGGED, not a silent pass):
     .venv/bin/python .claude/scripts/substrate.py waive --manifest <m.json> --reason \"<why>\"
  Do NOT report these events as complete while they are pending.${CORRUPT_NOTE}${FREEZE_NOTE}"

if [ "$STOP_ACTIVE" != "true" ]; then
  printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$FAILED_MSG" | jq -Rsa .)"
else
  mkdir -p "$(dirname "$FAIL_LOG")" 2>/dev/null
  jq -cn --arg s "${SESSION_ID:-_empty}" --arg t "$NOW" \
        --argjson n "${PENDING:-0}" --argjson c "${CORRUPT:-0}" --argjson ev "$EVENTS_JSON" \
    '{event:"substrate_gate_failed", session:$s, ts:$t, pending:$n, corrupt:$c, events:$ev}' \
    >> "$FAIL_LOG" 2>/dev/null
  printf '{"systemMessage":%s}\n' "$(printf '%s' "$FAILED_MSG" | jq -Rsa .)"
fi

exit 0
