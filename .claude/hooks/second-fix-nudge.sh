#!/usr/bin/env bash
# second-fix-nudge.sh — PreToolUse nudge for the second-fix stop rule.
# Spec: .claude/references/second-fix-stop-rule.md. Never blocks; injects context only.
# Fires on: Linear issue CREATE (no `id`), and Agent dispatches labelled judge round >=3 / re-judge.
set -uo pipefail

input="$(cat)"
tool="$(jq -r '.tool_name // empty' <<<"$input" 2>/dev/null)" || exit 0

msg=""
case "$tool" in
  mcp__linear__save_issue)
    # Updates carry an id; only creates are the spiral signal.
    if [[ -z "$(jq -r '.tool_input.id // empty' <<<"$input")" ]]; then
      msg="Second-fix stop rule: is this new issue a fix/follow-up to something built in the last 7 days? If so, and it's the 2nd+ fix on that component, dispatch alex:cto-principal-architect first ('design problem? what should we remove?') and cite its answer in the issue. See .claude/references/second-fix-stop-rule.md."
    fi
    ;;
  Agent|Task)
    desc="$(jq -r '(.tool_input.description // "") + " " + (.tool_input.prompt // "" | .[0:300])' <<<"$input" | tr '[:upper:]' '[:lower:]')"
    if grep -Eq 'judge' <<<"$desc" && grep -Eq 're-?judge|round ([3-9]|[1-9][0-9])' <<<"$desc"; then
      msg="Second-fix stop rule: this is judge round 3+ / a re-judge on the same build. Before another fix-and-rejudge cycle, dispatch alex:cto-principal-architect: 'is this a design problem — what should we remove?'. See .claude/references/second-fix-stop-rule.md."
    fi
    ;;
esac

[[ -z "$msg" ]] && exit 0
jq -n --arg m "$msg" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$m}}'
exit 0
