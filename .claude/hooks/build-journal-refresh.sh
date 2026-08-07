#!/usr/bin/env bash
# Stop hook — auto-refresh the self-instrumenting build journal (YED-119 V2).
#
# Regenerates the Hub's build-journal.json from git + telemetry every session, but ONLY adopts the
# result (and nudges) when the *entries* actually changed — timestamp-only churn is ignored, so the
# Hub working tree stays clean on no-op sessions. It NEVER commits: build-journal.json is data the
# Hub reads, and committing stays human (branch-first + the GitHub Desktop flow). The reminder tells
# Alex to add today's ≤3-line prose and commit.
#
# Deterministic + zero-token by design (the generator is pure git/file assembly — no LLM). The richer
# LLM-synthesized narrative in the original YED-119 vision would additionally need a CLAUDE.md
# convention; this structured-auto V2 does not.
#
# Output: a top-level `systemMessage` (Stop hooks cannot use additionalContext — hook-schema-reference).
# Disable via .claude/settings.local.json → {"hooks":{"disable":["build-journal-refresh"]}}.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

# disable override (mirrors build-session-emit / v2-trigger-log)
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ] && jq -e '.hooks.disable | index("build-journal-refresh")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
  exit 0
fi

GEN=".claude/scripts/build_journal.py"
HUB="../empire-state-hub"
JOURNAL="$HUB/src/data/build-journal.json"
[ -f "$GEN" ] || exit 0
[ -d "$HUB/src/data" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# regenerate to a temp; compare ENTRIES only (ignore generated_at churn) before adopting
TMP=$(mktemp 2>/dev/null) || exit 0
trap 'rm -f "$TMP"' EXIT
python3 "$GEN" --out "$TMP" >/dev/null 2>&1 || exit 0

AFTER=$(jq -cS '.entries' "$TMP" 2>/dev/null || echo "null")
BEFORE=$(jq -cS '.entries' "$JOURNAL" 2>/dev/null || echo "missing")
[ "$AFTER" = "null" ] && exit 0                 # generator produced nothing usable → bail quietly
[ "$AFTER" = "$BEFORE" ] && exit 0              # no meaningful change → silent, leave Hub file untouched

# entries changed → adopt the regenerated journal
mv "$TMP" "$JOURNAL" 2>/dev/null || exit 0
trap - EXIT

TODAY=$(date -u +%Y-%m-%d)
UNCURATED=$(jq -r '[.entries[]? | select(.curated==false)] | length' "$JOURNAL" 2>/dev/null || echo 0)
TOP=$(jq -r '.entries[0].date // ""' "$JOURNAL" 2>/dev/null || echo "")
MSG="📓 Build journal regenerated — new shipped activity detected (latest entry: ${TOP:-today})."
MSG="$MSG If today ($TODAY) was a notable build, add a ≤3-line what/why/value summary to"
MSG="$MSG .claude/data/build-journal-prose.json, then commit build-journal.json in empire-state-hub."
[ "${UNCURATED:-0}" -gt 0 ] 2>/dev/null && MSG="$MSG ($UNCURATED day(s) currently render facts-only — no prose yet.)"

jq -nc --arg m "$MSG" '{systemMessage:$m}'
exit 0
