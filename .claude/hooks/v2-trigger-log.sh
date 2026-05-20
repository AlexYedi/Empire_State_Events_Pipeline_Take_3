#!/usr/bin/env bash
# Stop hook — v2-trigger logging
# Issue: YED-27 Hook B
#
# Behavior:
#   If the session ran any of the 4 v2-relevant skills, append a structured entry
#   to .claude/artifacts/trigger-log.md (timestamp + skills + trigger choice "?"),
#   and prompt Alex the 4-option trigger question via additionalContext.
#   Alex updates the "?" later with his answer.
#
#   After 4 entries, prepend a summary line: "Trigger status: X-of-3 firing, last updated YYYY-MM-DD".
#
# Output contract: JSON on stdout with top-level `systemMessage` field
# (Stop hooks do NOT support hookSpecificOutput.additionalContext — that's
# valid only for UserPromptSubmit / PostToolUse / PostToolBatch. Discovered
# 2026-05-20 — the schema validator rejects additionalContext on Stop.)

set -uo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

STATE_DIR=".claude/.state"
SKILLS_FILE="$STATE_DIR/${SESSION_ID}.relevant_skills"
LOG_FILE=".claude/artifacts/trigger-log.md"

# Disable override
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("v2-trigger-log")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    rm -f "$SKILLS_FILE" 2>/dev/null
    exit 0
  fi
fi

[ ! -f "$SKILLS_FILE" ] && exit 0

# Dedup skills that fired this session
SKILLS=$(sort -u "$SKILLS_FILE" | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')
[ -z "$SKILLS" ] && { rm -f "$SKILLS_FILE"; exit 0; }

# Write a partial log entry (trigger choice = "?", Alex fills it in later)
mkdir -p "$(dirname "$LOG_FILE")"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
DATE_ONLY=$(date -u +%Y-%m-%d)

ENTRY="- $TIMESTAMP | session: \`${SESSION_ID:0:8}\` | skills: $SKILLS | trigger: **?**"

# Ensure log file has header
if [ ! -f "$LOG_FILE" ]; then
  cat > "$LOG_FILE" <<EOF
# v2-trigger log

YED-27 Hook B logs each session that invokes pre-event-content, pattern-synthesis, content-correspondent, or event-research. After each entry, Alex picks a trigger from the 4-option question and replaces the **?** with the chosen number (1, 2, 3, or 4).

Triggers:
1. Output didn't match its spec
2. Wished you had measurement
3. Needed new orchestration code vs. clicking pieces together
4. None of the above

## Entries

EOF
fi

echo "$ENTRY" >> "$LOG_FILE"

# After 4 entries, prepend/update summary line
ENTRY_COUNT=$(grep -cE '^- [0-9]{4}-' "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$ENTRY_COUNT" -ge 4 ]; then
  # Count answered (1-3) entries (firing) vs answered-4 (not firing). "?" still pending.
  FIRING=$(grep -cE '\*\*[123]\*\*$' "$LOG_FILE" 2>/dev/null || echo 0)
  NOT_FIRING=$(grep -cE '\*\*4\*\*$' "$LOG_FILE" 2>/dev/null || echo 0)
  ANSWERED=$((FIRING + NOT_FIRING))

  # Remove any existing summary line, then prepend a fresh one
  TMP_FILE=$(mktemp)
  grep -v '^_Trigger status:' "$LOG_FILE" > "$TMP_FILE"
  {
    head -n 1 "$TMP_FILE"
    echo ""
    echo "_Trigger status: $FIRING-of-3 firing (of $ANSWERED answered, $((ENTRY_COUNT - ANSWERED)) pending), last updated $DATE_ONLY_"
    tail -n +2 "$TMP_FILE"
  } > "$LOG_FILE"
  rm -f "$TMP_FILE"
fi

# Prompt Alex with the 4-option question
PROMPT=$(cat <<EOF
## 🟠 v2-trigger check (YED-27 Hook B)

This session ran: **$SKILLS**

Did any v2 trigger fire this session?
1. Output didn't match its spec
2. Wished you had measurement
3. Needed new orchestration code vs. clicking pieces together
4. None of the above

A partial entry was logged in \`$LOG_FILE\` with trigger **?**. Update it with the chosen number when convenient.

To disable this hook: add \`"hooks": {"disable": ["v2-trigger-log"]}\` to \`.claude/settings.local.json\`.
EOF
)

ESCAPED=$(printf '%s' "$PROMPT" | jq -Rsa .)
printf '{"systemMessage":%s}\n' "$ESCAPED"

# Cleanup session state
rm -f "$SKILLS_FILE" 2>/dev/null

exit 0
