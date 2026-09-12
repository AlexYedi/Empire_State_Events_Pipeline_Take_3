#!/usr/bin/env bash
# SessionStart hook — rebuild the system graph and inject its actionable findings into context.
#
# This is the whole point of ADR-8: the rigor layer was good at RECORDING and bad at WATCHING, because
# every control was INVOKED (a command Alex types) rather than TRIGGERED. This hook is the trigger. No
# one runs it; it runs because a session started. If it finds nothing, it says nothing.
#
# Spec: docs/adr/ADR-8-system-graph-drift-router.md
#
# ROUTER, NOT DETECTOR (ADR-8 D3): it reports that a reference points at a file that does not exist —
# a mechanical fact — and never that two artifacts "contradict". Judgement stays with the reader.
#
# Precision budget (ADR-8 D4): at most 5 findings per surface. If this surface's 2-week precision falls
# below 50%, the check SHRINKS rather than growing more checks — noise here retrains Alex to ignore it,
# which is worse than silence.
#
# Zero-token, stdlib-only, no env, no network — so it also fires in Dock-launched sessions that never
# see .env (project_claude_code_env_handoff) and in fresh worktrees.
#
# Output: `hookSpecificOutput.additionalContext` (SessionStart's injection channel).
# Disable via .claude/settings.local.json → {"hooks":{"disable":["graph-sessionstart"]}}.
# Advisory ALWAYS — exit 0 unconditionally; it must never be able to block a session from starting.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ] && command -v jq >/dev/null 2>&1 \
   && jq -e '.hooks.disable | index("graph-sessionstart")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
  exit 0
fi

BUILDER=".claude/scripts/build_graph.py"
[ -f "$BUILDER" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# Rebuild from scratch (the cache is derived; the repo is the system of record) and collect findings.
FINDINGS=$(python3 "$BUILDER" --check dangling-ref 2>/dev/null | grep '^dangling-ref:' || true)
[ -n "$FINDINGS" ] || exit 0

COUNT=$(printf '%s\n' "$FINDINGS" | grep -c '^dangling-ref: ' || true)

CONTEXT="## 🔗 System-graph findings (ADR-8 — rebuilt at session start, nobody invoked it)

${COUNT} load-bearing reference(s) point at files that do not exist on disk. This is mechanical fact,
not judgement: the path was cited, the path is absent. Classes that are NOT actionable (runtime-
generated, \`~/\`-external, named in a plan, already tracked in Linear) are excluded.

${FINDINGS}

Each is one of: **fix** the reference (or create the file), **track** it (open/link a Linear issue),
**accept** it (say why), or **false-positive** it (the extractor over-flagged — that is a bug in
\`.claude/scripts/build_graph.py\`, fix it there, not by adding a placeholder file). Acting on these is
optional and they are capped at 5 — if they are consistently noise, say so and the check shrinks."

if command -v jq >/dev/null 2>&1; then
  jq -cn --arg c "$CONTEXT" \
    '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
fi
exit 0
