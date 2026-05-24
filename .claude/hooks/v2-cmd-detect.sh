#!/usr/bin/env bash
# UserPromptExpansion hook — detect v2-relevant SLASH COMMAND invocations.
# Issue: YED-27 Hook B (gap fix, 2026-05-24)
#
# Why this exists (the bug it closes):
#   v2-trigger-detect.sh is bound to PostToolUse:Skill, which fires ONLY when a
#   skill is invoked through the Skill tool (the 3 natural-language skills:
#   pre-event-content, pattern-synthesis, content-correspondent).
#   SLASH COMMANDS (/check-new-events, /event-deep-research) are pre-loaded by the
#   harness via the command path and never emit a PostToolUse:Skill event, so the
#   detector was structurally blind to them — confirmed empirically 2026-05-24:
#   re-running /check-new-events left .claude/.state/ untouched (dir mtime unchanged),
#   so the Stop log hook's `[ ! -f "$SKILLS_FILE" ]` guard wrote nothing.
#   UserPromptExpansion fires precisely on slash-command expansion — the only seam
#   where a /command is unambiguously observable. Docs cite "log which commands
#   users invoke" as a canonical use case.
#
# Behavior:
#   On a v2-relevant slash command, append the bare command name to
#   .claude/.state/<session_id>.relevant_skills — the SAME file the Stop hook
#   (v2-trigger-log.sh) reads. Downstream logging pipeline is unchanged.
#
# v2-relevant slash commands: check-new-events, event-deep-research.
# (event-research is the legacy skill name, still matched by v2-trigger-detect.sh.)
#
# Emits no output (silent detector). The Stop hook reads and prompts.
#
# DEBUG (temporary, remove after first-run verification 2026-05-24): also dumps the
# raw stdin payload to .claude/.state/upe-debug.json so the exact field shape can be
# confirmed on the first real fire. Strip the DEBUG block once validated.

set -uo pipefail

# Anchor CWD to project root so internal relative paths (.claude/.state/...) resolve
# regardless of how Claude Code launched the hook. Matches v2-trigger-detect.sh.
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

INPUT=$(cat)

# --- DEBUG (temporary) -------------------------------------------------------
mkdir -p ".claude/.state" 2>/dev/null
printf '%s' "$INPUT" > ".claude/.state/upe-debug.json" 2>/dev/null
# -----------------------------------------------------------------------------

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

# Command-name field shape is not authoritatively documented — try candidates
# defensively (first hit wins), then fall back to parsing the raw prompt text.
CMD=$(echo "$INPUT" | jq -r '
  .command_name // .tool_input.command_name //
  .expansion.command_name // .command // empty
' 2>/dev/null)

if [ -z "$CMD" ]; then
  RAW=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
  # Strip leading slash and take the first command token (e.g. /check-new-events).
  CMD=$(printf '%s' "$RAW" | sed -n 's#^[[:space:]]*/\([a-zA-Z0-9_-]\{1,\}\).*#\1#p')
fi

[ -z "$CMD" ] && exit 0

# Strip any plugin namespace prefix (e.g. alex:foo -> foo) for matching.
BARE="${CMD##*:}"

case "$BARE" in
  check-new-events|event-deep-research)
    STATE_DIR=".claude/.state"
    mkdir -p "$STATE_DIR" 2>/dev/null
    echo "$BARE" >> "$STATE_DIR/${SESSION_ID}.relevant_skills"
    ;;
esac

exit 0
