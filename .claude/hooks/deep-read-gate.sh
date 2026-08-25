#!/usr/bin/env bash
# Deep Read marker gate — Stop hook — YED-139 (Layer 1 enforcer)
#
# Makes a silently-skipped Deep Read (Step 4.5) impossible to close green. Reads the
# per-session ledger written by deep-read-ledger.sh; if any Event page the run touched
# is still `pending` (Scan head committed, Deep Read NOT rendered), it FAILS the run:
#   - First stop attempt (interactive)  → decision:block, forcing the agent to re-run
#     Step 4.5 or explicitly `waive` the page (idempotent) before it can close.
#   - Already blocked once (stop_hook_active) → loud persistent FAILED systemMessage,
#     then allow stop (the autonomous / can't-resolve "report FAILED" path — never traps).
#
# Fails CLOSED by design: the ledger row is written `pending` at the Scan-head commit
# (Step 4g) and only flips to `rendered` on a successful Step 4.5. A skipped render
# leaves it `pending` → this gate fails. See .claude/proposals/deep-read-marker-gate.md.
#
# NOTE (hard constraint): the authoritative marker lives in Notion, unreadable from a
# shell hook (Notion is MCP-in-conversation only). This hook enforces the *local ledger*;
# the in-conversation terminal gate (check-new-events Step 8 / event-deep-research close)
# re-fetches the real Notion marker and reconciles. Belt (hook) + suspenders (terminal).
#
# Output contract: JSON on stdout. Stop hooks support `decision:block`+`reason` (blocks the
# stop, reason goes to the model) and `systemMessage` (surfaced, non-blocking). Always exit 0.

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)

STATE_DIR=".claude/.state"
LEDGER="$STATE_DIR/${SESSION_ID}.deep_read_gate.jsonl"
# Same _pending fallback as the writer (Dock/--resume/subagent contexts where the env var
# was absent when rows were written).
[ ! -f "$LEDGER" ] && [ -f "$STATE_DIR/_pending.deep_read_gate.jsonl" ] && LEDGER="$STATE_DIR/_pending.deep_read_gate.jsonl"

# Disable override (matches v2-trigger-log convention)
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("deep-read-gate")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    exit 0
  fi
fi

command -v jq >/dev/null 2>&1 || exit 0
[ ! -f "$LEDGER" ] && exit 0   # no ledger → run touched no events → nothing to gate

PENDING=$(jq -s '[.[] | select(.marker == "pending")] | length' "$LEDGER" 2>/dev/null || echo 0)
[ "${PENDING:-0}" -eq 0 ] && exit 0   # all rendered or waived → gate passes, silent

# Build the pending list (one "- <event> (page <id-prefix>)" line per pending row).
PENDING_LIST=$(jq -rs '
  [.[] | select(.marker == "pending")]
  | map("  - " + (.event // "(untitled event)") + "  ·  page " + ((.page_id // "?")[0:8]))
  | join("\n")' "$LEDGER" 2>/dev/null)

WAIVED=$(jq -s '[.[] | select(.marker == "waived")] | length' "$LEDGER" 2>/dev/null || echo 0)
WAIVED_NOTE=""
[ "${WAIVED:-0}" -gt 0 ] && WAIVED_NOTE="

($WAIVED page(s) explicitly waived — acknowledged pending, not blocking.)"

FAILED_MSG="⚠️ DEEP READ GATE: FAILED — $PENDING event(s) closed with an UNRENDERED Deep Read (marker still \`deep_read_rendered: pending\`):

$PENDING_LIST

A Scan-head-only brief is a THIN brief — this is the exact Aug-2026 regression YED-139 exists to stop. To resolve:
  1. Re-run Step 4.5 of /event-deep-research (idempotent) for each event above, in a session where field-guide-renderer is registered — then the ledger flips to \`rendered\`; OR
  2. If you genuinely cannot render now (e.g. renderer unregistered this session), explicitly acknowledge each:
     .claude/hooks/deep-read-ledger.sh waive \"<page_id>\" \"<reason>\"
  Do NOT report these events as complete while they are pending.$WAIVED_NOTE"

if [ "$STOP_ACTIVE" != "true" ]; then
  # Interactive gate: block the close and hand the reason to the agent to act on.
  ESCAPED=$(printf '%s' "$FAILED_MSG" | jq -Rsa .)
  printf '{"decision":"block","reason":%s}\n' "$ESCAPED"
else
  # Already blocked once (autonomous / unresolvable) — surface a loud persistent FAILED
  # and allow the stop. Never trap the session.
  ESCAPED=$(printf '%s' "$FAILED_MSG" | jq -Rsa .)
  printf '{"systemMessage":%s}\n' "$ESCAPED"
fi

exit 0
