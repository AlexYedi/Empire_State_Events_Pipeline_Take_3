#!/usr/bin/env bash
# Stop hook — repo-touch reconcile-with-Linear reminder
# Issue: YED-27 Hook A
#
# Behavior:
#   If the session's tally file shows N>0 edits under .claude/{skills,agents,
#   commands,proposals}/, emit a reminder asking Alex to reconcile with Linear.
#   Cleans up state files for this session afterwards.
#
# Output contract: JSON on stdout with hookSpecificOutput.additionalContext.

set -uo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

STATE_DIR=".claude/.state"
TALLY_FILE="$STATE_DIR/${SESSION_ID}.touch_count"
FILES_FILE="$STATE_DIR/${SESSION_ID}.touch_files"

# Disable override: respect settings.local.json hooks.disable list
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("repo-touch-nudge")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    rm -f "$TALLY_FILE" "$FILES_FILE" 2>/dev/null
    exit 0
  fi
fi

[ ! -f "$TALLY_FILE" ] && exit 0
COUNT=$(cat "$TALLY_FILE" 2>/dev/null || echo 0)

if [ "$COUNT" -gt 0 ]; then
  # Build a deduped list of touched files for the reminder
  FILES=""
  if [ -f "$FILES_FILE" ]; then
    FILES=$(sort -u "$FILES_FILE" | sed 's|^|  - |' | head -10)
  fi

  REPO_NAME=$(basename "$(pwd)")
  NOUN="files"; [ "$COUNT" = "1" ] && NOUN="file"

  FILES_BLOCK=""
  [ -n "$FILES" ] && FILES_BLOCK=$(printf 'Files touched:\n%s' "$FILES")

  REMINDER=$(cat <<EOF
## 🟠 Repo-touch nudge (YED-27 Hook A)

This session touched **$COUNT $NOUN** under \`.claude/\` in **$REPO_NAME**.

$FILES_BLOCK

Reconcile with Linear:
- **Open an issue** for new work not yet tracked
- **Comment on an existing issue** for in-progress work
- **OR** explicitly acknowledge this is doc-only maintenance and no Linear update is needed

To disable this hook: add \`"hooks": {"disable": ["repo-touch-nudge"]}\` to \`.claude/settings.local.json\`.
EOF
)

  # JSON-escape and emit
  ESCAPED=$(printf '%s' "$REMINDER" | jq -Rsa .)
  printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":%s}}\n' "$ESCAPED"
fi

# Cleanup state for this session
rm -f "$TALLY_FILE" "$FILES_FILE" 2>/dev/null

exit 0
