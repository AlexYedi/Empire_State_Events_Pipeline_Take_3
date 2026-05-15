#!/usr/bin/env bash
# PostToolUse hook — tally edits under .claude/{skills,agents,commands,proposals}/
# Issue: YED-27 Hook A (repo-touch nudge — Layer B discipline)
#
# Behavior:
#   Reads hook JSON on stdin. If the tool_input.file_path matches
#   .claude/(skills|agents|commands|proposals)/**, increment a per-session
#   tally file at .claude/.state/<session_id>.touch_count
#
# Emits no output (silent counter). Stop hook reads the tally and reminds.

set -uo pipefail

# Read entire hook input from stdin
INPUT=$(cat)

# Extract session_id and file_path defensively
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

# Bail silently if we couldn't parse what we need
[ -z "$SESSION_ID" ] && exit 0
[ -z "$FILE_PATH" ] && exit 0

# Match .claude/(skills|agents|commands|proposals)/...
if echo "$FILE_PATH" | grep -qE '\.claude/(skills|agents|commands|proposals)/'; then
  STATE_DIR=".claude/.state"
  mkdir -p "$STATE_DIR" 2>/dev/null
  TALLY_FILE="$STATE_DIR/${SESSION_ID}.touch_count"

  # Increment tally
  COUNT=0
  [ -f "$TALLY_FILE" ] && COUNT=$(cat "$TALLY_FILE" 2>/dev/null || echo 0)
  echo $((COUNT + 1)) > "$TALLY_FILE"

  # Also track the touched file paths for the reminder (newline-delimited, dedup at read time)
  echo "$FILE_PATH" >> "$STATE_DIR/${SESSION_ID}.touch_files"
fi

exit 0
