#!/usr/bin/env bash
# PostToolUse hook (matcher: Skill) — detect v2-relevant skill invocations
# Issue: YED-27 Hook B (v2-trigger logging — Layer B discipline)
#
# Behavior:
#   When the Skill tool is invoked with one of the 4 v2-relevant skills, append
#   the skill name to .claude/.state/<session_id>.relevant_skills.
#
# The v2-relevant skills/commands (per YED-27 spec — updated 2026-05-20):
#   pre-event-content, pattern-synthesis, content-correspondent
#   event-research (legacy skill name), event-deep-research (current slash command),
#   check-new-events (auto-ingest wrapper added 2026-05-20)
# All current and legacy names matched so detector survives skill/command renames.
#
# Emits no output (silent detector). The Stop hook reads and prompts.

set -uo pipefail

# Anchor CWD to project root so internal relative paths (.claude/.state/...) resolve
# regardless of how Claude Code launched the hook. Fixes "No such file or directory"
# under Dock-launched / --resume contexts. See settings.json $CLAUDE_PROJECT_DIR fix.
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

# Skill name may live in different fields depending on hook input shape.
# Try common ones; first hit wins.
SKILL_NAME=$(echo "$INPUT" | jq -r '
  .tool_input.skill // .tool_input.name // .tool_input.command //
  .tool_input.skill_name // empty
' 2>/dev/null)

[ -z "$SKILL_NAME" ] && exit 0

# Strip any plugin namespace prefix (e.g., alex:foo -> foo) for matching.
BARE_SKILL="${SKILL_NAME##*:}"

case "$BARE_SKILL" in
  pre-event-content|pattern-synthesis|content-correspondent|event-research|event-deep-research|check-new-events)
    STATE_DIR=".claude/.state"
    mkdir -p "$STATE_DIR" 2>/dev/null
    echo "$BARE_SKILL" >> "$STATE_DIR/${SESSION_ID}.relevant_skills"
    ;;
esac

exit 0
