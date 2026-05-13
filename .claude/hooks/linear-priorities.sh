#!/usr/bin/env bash
# SessionStart hook — Linear priorities pull
# Issue: YED-26 (Layer B foundation: single source of truth)
#
# Behavior:
#   - If LINEAR_API_KEY is set in env: queries Linear GraphQL for open issues
#     filtered by state ∈ {Backlog, Todo, In Progress} AND priority ≤ 3 (Medium+),
#     sorted by priority asc then updatedAt desc, capped at 5, formatted as
#     markdown bullets and emitted as additionalContext at session start.
#   - If LINEAR_API_KEY is NOT set: emits a one-line graceful-degradation message
#     telling Alex how to activate the hook. No errors, no failures.
#
# Output contract: emit JSON on stdout matching the SessionStart hook schema:
#   {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
# Errors go to stderr but never block session start.
#
# Team: Yedibalian (id: 816e0384-53f0-4159-a844-c8ee5d4b3067)
# When YED-29 promotes this to user-scope, the team-id becomes configurable.

set -uo pipefail

TEAM_ID="816e0384-53f0-4159-a844-c8ee5d4b3067"
MAX_ISSUES=5

emit_context() {
  local context="$1"
  # JSON-escape the context (newlines, quotes, backslashes)
  local escaped
  escaped=$(printf '%s' "$context" | jq -Rsa .)
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$escaped"
}

if [ -z "${LINEAR_API_KEY:-}" ]; then
  emit_context "## 🟠 Linear priorities (offline)

\`LINEAR_API_KEY\` not set — SessionStart hook running in graceful-fallback mode. To activate live priorities pull:

1. Create personal API key at https://linear.app/yedibalian/settings/api
2. Add to shell rc: \`export LINEAR_API_KEY=lin_api_...\`
3. Restart Claude Code session

Tracked under YED-26."
  exit 0
fi

# Build GraphQL query inline. Filter: team + state.type ∈ {backlog, unstarted, started} + priority ∈ {1,2,3} (Urgent/High/Medium).
# Using inline values rather than GraphQL variables — Linear's variable interpolation produced empty results in this
# server-side path (proven via bogus-key + diagnostic-curl comparison 2026-05-13). Team ID and max are constants
# anyway. Sorting happens client-side in jq below, so no orderBy needed.
QUERY="query { issues(filter: {team: {id: {eq: \"$TEAM_ID\"}}, state: {type: {in: [\"backlog\", \"unstarted\", \"started\"]}}, priority: {in: [1, 2, 3]}}, first: $MAX_ISSUES) { nodes { identifier title priority state { name } updatedAt } } }"

PAYLOAD=$(jq -nc --arg q "$QUERY" '{query: $q}')

RESPONSE=$(curl -sS -m 5 \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "https://api.linear.app/graphql" 2>/dev/null) || {
  emit_context "## 🟠 Linear priorities (network error)

Linear API call failed (timeout or network). Tracked under YED-26."
  exit 0
}

# Check for API errors
if echo "$RESPONSE" | jq -e '.errors' >/dev/null 2>&1; then
  ERR=$(echo "$RESPONSE" | jq -r '.errors[0].message' 2>/dev/null || echo "unknown error")
  emit_context "## 🟠 Linear priorities (API error)

Linear returned error: $ERR. Tracked under YED-26."
  exit 0
fi

# Parse issues — sort client-side by priority asc (1=Urgent, 2=High, 3=Medium), then by updatedAt desc.
# Sort technique: jq's sort_by is stable, so chaining sort_by(.updatedAt) | reverse | sort_by(.priority) gives
# priority asc with newest-first within each priority. Lexicographic sort on ISO 8601 strings is correct (no need
# for fromdateiso8601, which previously choked on Linear's millisecond-precision timestamps like "...19:38:41.888Z").
ISSUES=$(echo "$RESPONSE" | jq -r '
  .data.issues.nodes
  | sort_by(.updatedAt) | reverse | sort_by(.priority)
  | .[]
  | "- **[\(.identifier) — \(if .priority==1 then "Urgent" elif .priority==2 then "High" elif .priority==3 then "Medium" else "?" end), \(.state.name)]** \(.title)"
' 2>/dev/null)

if [ -z "$ISSUES" ]; then
  emit_context "## 🟠 Linear priorities

No open Medium+ priority issues in Yedibalian team. Clean slate."
  exit 0
fi

emit_context "## 🟠 Linear priorities (live pull, ≤$MAX_ISSUES items, Medium+ priority)

$ISSUES

_Source: Linear MCP via SessionStart hook (\`.claude/hooks/linear-priorities.sh\`). Replaces the static priorities block in CLAUDE.md — see YED-26._"
