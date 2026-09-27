#!/usr/bin/env bash
# Deep Read marker gate — Stop hook — YED-139 (Layer 1 enforcer)
#
# Makes a silently-skipped Deep Read (Step 4.5) fail the run instead of closing green.
# Reads the per-session ledger written by deep-read-ledger.sh; if any Event page the run
# touched is still `pending` (Scan head committed, Deep Read NOT rendered) — or the ledger
# has an unparseable line (fail-closed) — it FAILS the run:
#   - First stop attempt (interactive)  → decision:block, forcing the agent to re-run
#     Step 4.5 or explicitly `waive` the page before it can close.
#   - Already blocked once (stop_hook_active) → the run IS closing with pending: persist a
#     durable FAILED record + surface a loud systemMessage, then allow the stop (the
#     autonomous / can't-resolve "report FAILED" path — never traps the session).
#
# Stop fires per turn; the gate treats pending as in-progress while the event claim is live; it fails at the
# first turn end after the claim is released or expires (2026-09-27, YED-228 — see _run_in_progress.sh).
#
# Fails CLOSED by design (adversarial-review hardened):
#   - a `pending` row (default at Scan-head commit, flipped only on successful Step 4.5),
#   - an unparseable ledger line (corruption never reads as "clean/empty"),
#   - an empty stdin session_id (scan ALL session ledgers rather than exit silently).
#
# Durability (review finding #2b): the Aug-2026 regression was invisible AFTER THE FACT.
# On a close-with-pending, this hook appends a row to .claude/artifacts/deep-read-gate-failures.jsonl
# so the failure survives the transcript (rigor-review / a human can see it). A perishable
# systemMessage alone would repeat the original invisibility.
#
# NOTE (hard constraint): the authoritative marker lives in Notion, unreadable from a shell
# hook (MCP-in-conversation only). This hook enforces the LOCAL LEDGER; the in-conversation
# terminal gate (check-new-events Step 8 / event-deep-research Step 6.5) re-fetches the real
# Notion marker and reconciles. The hook is the deterministic floor; the terminal gate is the
# authoritative reconciliation when present (it is skippable by the same LLM — the hook is not).
#
# Output contract: JSON on stdout. `decision:block`+`reason` blocks the stop (reason → model);
# `systemMessage` is surfaced, non-blocking. Always exit 0.

set -uo pipefail

# A gate that cannot run must say so (YED-228 follow-up): a missing jq or an unreachable project dir used to
# `exit 0` silently, turning the gate into a no-op nobody could see. Static JSON — jq may be the thing missing.
cant_run() { printf '{"systemMessage":"⚠️ %s: gate could NOT run (%s) — pending Deep Read / graph-write rows are UNCHECKED this turn."}\n' "$1" "$2"; exit 0; }

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || cant_run "deep-read-gate" "project dir unreachable"

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)

STATE_DIR=".claude/.state"
FAIL_LOG=".claude/artifacts/deep-read-gate-failures.jsonl"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Disable override (matches v2-trigger-log convention)
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("deep-read-gate")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    exit 0
  fi
fi

command -v jq >/dev/null 2>&1 || cant_run "deep-read-gate" "jq not installed"

# shellcheck source=_run_in_progress.sh
. "$(dirname "${BASH_SOURCE[0]}")/_run_in_progress.sh"

# Resolve which ledger file(s) to enforce.
LEDGERS=()
if [ -n "$SESSION_ID" ]; then
  F="$STATE_DIR/${SESSION_ID}.deep_read_gate.jsonl"
  # Same _pending fallback as the writer (Dock/--resume/subagent contexts).
  [ ! -f "$F" ] && [ -f "$STATE_DIR/_pending.deep_read_gate.jsonl" ] && F="$STATE_DIR/_pending.deep_read_gate.jsonl"
  [ -f "$F" ] && LEDGERS=("$F")
else
  # Empty stdin session_id (review finding #4a): FAIL CLOSED — scan every session ledger
  # rather than exit silently. A writer that used a real $CLAUDE_CODE_SESSION_ID is only
  # reachable this way when the hook's stdin carries no id.
  shopt -s nullglob
  LEDGERS=("$STATE_DIR"/*.deep_read_gate.jsonl)
  shopt -u nullglob
fi

[ "${#LEDGERS[@]}" -eq 0 ] && exit 0   # no ledger → run touched no events → nothing to gate

# Resilient scan over the ledger set: count PENDING + unparseable (fail-closed), collect the
# pending event labels, and count corrupt lines separately for the message.
PENDING=0
CORRUPT=0
PENDING_LIST=""
EVENTS_JSON="[]"
scan_line() {
  local line="$1" obj marker event pid
  [ -z "$line" ] && return
  obj=$(printf '%s' "$line" | jq -c 'if type=="object" then . else empty end' 2>/dev/null)
  if [ -z "$obj" ]; then
    CORRUPT=$((CORRUPT+1)); PENDING=$((PENDING+1)); return
  fi
  marker=$(printf '%s' "$obj" | jq -r '.marker // "CORRUPT"' 2>/dev/null)
  if [ "$marker" = "pending" ] || [ "$marker" = "CORRUPT" ]; then
    PENDING=$((PENDING+1))
    event=$(printf '%s' "$obj" | jq -r '.event // "(untitled event)"' 2>/dev/null)
    pid=$(printf '%s' "$obj" | jq -r '.page_id // "?"' 2>/dev/null)
    PENDING_LIST="${PENDING_LIST}  - ${event}  ·  page ${pid:0:8}
"
    EVENTS_JSON=$(printf '%s' "$EVENTS_JSON" | jq -c --arg e "$event" --arg p "$pid" '. + [{event:$e, page_id:$p}]' 2>/dev/null || printf '%s' "$EVENTS_JSON")
  fi
}
for L in "${LEDGERS[@]}"; do
  while IFS= read -r line || [ -n "$line" ]; do scan_line "$line"; done < "$L"
done

[ "${PENDING:-0}" -eq 0 ] && exit 0   # all rendered or waived, no corruption → gate passes, silent

# In progress: this session still holds its event claim → pending is expected, not a skip. Silent.
run_in_progress "$SESSION_ID" && exit 0

CORRUPT_NOTE=""
[ "${CORRUPT:-0}" -gt 0 ] && CORRUPT_NOTE="
(Includes $CORRUPT unparseable ledger line(s), counted as pending — fail-closed.)"

FAILED_MSG="⚠️ DEEP READ GATE: FAILED — $PENDING event(s) closed with an UNRENDERED Deep Read (marker still \`deep_read_rendered: pending\`):

${PENDING_LIST}A Scan-head-only brief is a THIN brief — this is the exact Aug-2026 regression YED-139 exists to stop. To resolve:
  1. Re-run Step 4.5 of /event-deep-research (idempotent) for each event above, in a session where field-guide-renderer is registered — the ledger then flips to \`rendered\`; OR
  2. If you genuinely cannot render now (e.g. renderer unregistered this session), explicitly acknowledge each (this is LOGGED, not a silent pass):
     .claude/hooks/deep-read-ledger.sh waive \"<page_id>\" \"<reason>\"
  Do NOT report these events as complete while they are pending.${CORRUPT_NOTE}"

if [ "$STOP_ACTIVE" != "true" ]; then
  # Interactive gate: block the close and hand the reason to the agent to act on.
  # Not persisted yet — a block that gets resolved should leave no FAILED record.
  ESCAPED=$(printf '%s' "$FAILED_MSG" | jq -Rsa .)
  printf '{"decision":"block","reason":%s}\n' "$ESCAPED"
else
  # Already blocked once — the run IS closing with pending. Persist a DURABLE record so the
  # failure survives the transcript (review finding #2b), then surface it and allow the stop.
  mkdir -p "$(dirname "$FAIL_LOG")" 2>/dev/null
  if ! already_logged "$FAIL_LOG" "deep_read_gate_failed" "${SESSION_ID:-_empty}" "$EVENTS_JSON"; then
    jq -cn --arg s "${SESSION_ID:-_empty}" --arg t "$NOW" \
          --argjson n "${PENDING:-0}" --argjson c "${CORRUPT:-0}" --argjson ev "$EVENTS_JSON" \
      '{event:"deep_read_gate_failed", session:$s, ts:$t, pending:$n, corrupt:$c, events:$ev}' \
      >> "$FAIL_LOG" 2>/dev/null
  fi
  ESCAPED=$(printf '%s' "$FAILED_MSG" | jq -Rsa .)
  printf '{"systemMessage":%s}\n' "$ESCAPED"
fi

exit 0
