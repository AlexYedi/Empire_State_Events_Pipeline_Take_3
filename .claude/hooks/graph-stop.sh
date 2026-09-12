#!/usr/bin/env bash
# Stop hook — rebuild the system graph after a session's edits land.
#
# Why both ends: the SessionStart rebuild is what gets READ, but rebuilding again at Stop means the
# drift a session just introduced is recorded while the work is still fresh, and the cache on disk
# always matches the commit it was built from (meta.git_sha). A consumer that finds meta.git_sha != HEAD
# knows the cache is stale and rebuilds rather than trusting it.
#
# Spec: docs/adr/ADR-8-system-graph-drift-router.md
#
# SILENT BY DESIGN. It surfaces nothing — a Stop hook that lectured at the end of every session is the
# noise ADR-8 D4 exists to prevent, and the findings are already shown at the next session's start.
# The one exception: a NEW actionable finding that this session introduced gets a one-line
# `systemMessage`, because that is the moment the author can still fix it cheaply.
#
# Disable via .claude/settings.local.json → {"hooks":{"disable":["graph-stop"]}}.
# Advisory ALWAYS — never blocks; exit 0 unconditionally.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ] && command -v jq >/dev/null 2>&1 \
   && jq -e '.hooks.disable | index("graph-stop")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
  exit 0
fi

BUILDER=".claude/scripts/build_graph.py"
STATE=".claude/.state/system-graph"
[ -f "$BUILDER" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

# What was actionable BEFORE this rebuild (i.e. as of session start)?
BEFORE=$(python3 - <<'PY' 2>/dev/null || true
import json, os
p = ".claude/.state/system-graph/edges.jsonl"
out = set()
if os.path.exists(p):
    for ln in open(p):
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if e.get("type") == "references" and not e.get("exists") and e.get("class") == "repo":
            out.add(e["dst"])
print("\n".join(sorted(out)))
PY
)

# One rebuild, which also prints the findings (`--check` always rebuilds first).
AFTER=$(python3 "$BUILDER" --check dangling-ref 2>/dev/null \
        | sed -n 's/^dangling-ref: \([^ ]*\) .*/\1/p' || true)

NEW=$(comm -13 <(printf '%s\n' "$BEFORE" | sort -u) <(printf '%s\n' "$AFTER" | sort -u) 2>/dev/null \
      | grep -v '^$' || true)

if [ -n "$NEW" ] && command -v jq >/dev/null 2>&1; then
  MSG="🔗 system-graph: this session introduced $(printf '%s\n' "$NEW" | wc -l | tr -d ' ') new dangling reference(s): $(printf '%s' "$NEW" | tr '\n' ' '). Cheapest to fix now; otherwise it surfaces at next session start."
  jq -cn --arg m "$MSG" '{systemMessage:$m}'
fi
exit 0
