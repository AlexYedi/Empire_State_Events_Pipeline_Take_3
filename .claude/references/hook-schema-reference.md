# Claude Code Hook Schema Reference

> Read this BEFORE writing a new hook. The output schema is event-specific and not obvious from copying one event type's example to another. This card exists because we've now hit two distinct schema gotchas in this repo.
>
> Authoritative source: Claude Code's hook validator. The error messages it returns are accurate — trust them over docs that may have drifted.
> Last updated: 2026-05-20

---

## Event types + supported output

Hooks fire on one of these events. Each event has a different supported output schema. **You cannot mix-and-match across events.**

| Event | Supports `hookSpecificOutput.additionalContext`? | Where the output goes | Typical use |
|---|---|---|---|
| `SessionStart` | ✅ YES | Injected into Claude's context as a system reminder | Pre-load priorities, project state, env warnings |
| `UserPromptSubmit` | ✅ YES | Injected into Claude's context for that turn | Auto-suggest skills, inject relevant docs, log prompts |
| `PostToolUse` | ✅ YES (optional) | Injected into Claude's context after the tool call | Append context after specific tools fire |
| `PostToolBatch` | ✅ YES (optional) | Injected into Claude's context after a batch | Same as PostToolUse but for batched calls |
| `PreToolUse` | ❌ NO — uses `permissionDecision` instead | Gates the tool call (allow/deny/ask/defer) | Guard rails on specific tools |
| `Stop` | ❌ NO — use top-level `systemMessage` | Displayed to the user in their terminal at session end | End-of-session prompts, reminders, summaries |

---

## Top-level output fields (work on ANY event)

These fields appear at the JSON root, NOT nested under `hookSpecificOutput`:

| Field | Type | Used by | Effect |
|---|---|---|---|
| `continue` | boolean | any | Lets Claude continue normally if false-ish blocks |
| `suppressOutput` | boolean | any | Hides the hook's stdout from the user |
| `stopReason` | string | Stop | Reason text shown when Claude stops |
| `decision` | `"approve"` \| `"block"` | PreToolUse / Stop | Approves or blocks the action |
| `reason` | string | accompanies `decision` | Why the decision was made |
| `systemMessage` | string | **Stop hooks** + any event that wants a user-visible message | Displayed to the user in their terminal |
| `terminalSequence` | string | any | Raw terminal escape sequence to emit |
| `permissionDecision` | `"allow"` \| `"deny"` \| `"ask"` | PreToolUse | Permission gate for the tool |

---

## Gotchas encountered in this repo

### Gotcha 1 — Stop hooks cannot use `additionalContext`
**Date hit:** 2026-05-20 in `.claude/hooks/v2-trigger-log.sh`

The hook was emitting:
```json
{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "..."}}
```

This fails schema validation. Stop hooks support only the top-level fields (`systemMessage`, `stopReason`, etc.) — there's no `hookSpecificOutput` schema entry for Stop at all.

**Fix:** emit `{"systemMessage": "..."}` at the top level. The text displays in the user's terminal at session end, which is what the hook wanted anyway.

The misleading pattern: `linear-priorities.sh` (a SessionStart hook) uses `hookSpecificOutput.additionalContext` correctly. Copy-pasting that pattern to a Stop hook silently broke until the schema validator caught it.

### Gotcha 2 — `additionalContext` is invisible to the user in the terminal
**Date hit:** 2026-05-19 with `linear-priorities.sh` rendering

`additionalContext` (on SessionStart / UserPromptSubmit / PostToolUse / PostToolBatch) injects into Claude's context window — not the user's terminal. Claude sees it; the user doesn't (unless Claude reads it back).

If you want the user to see something in their terminal:
- For Stop events → use `systemMessage`
- For SessionStart events → there's no clean "show in terminal" path; either echo to stderr from the hook script (visible to the terminal as the hook runs) or have Claude reference the context proactively

For session-start in particular, the trick that works:
```bash
# Print to stderr (visible in terminal before Claude responds)
echo "## 🟠 Linear priorities" >&2
cat priorities.txt >&2

# Also emit JSON for Claude's context
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":%s}}\n' "$ESCAPED"
```

---

## Disable pattern

Every hook should respect a disable flag in `.claude/settings.local.json`. Standard shape:

```json
{
  "hooks": {
    "disable": ["hook-name-1", "hook-name-2"]
  }
}
```

Hook script preamble:
```bash
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("hook-name")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    exit 0
  fi
fi
```

For user-scoped hooks, also check `$HOME/.claude/settings.local.json` for the same flag.

---

## Debugging a hook

When a hook misbehaves:

1. **Read the schema validation error verbatim.** It lists the expected schema and shows your actual output. The diff is usually obvious once you compare.
2. **Run the hook script manually** with sample input piped in:
   ```bash
   echo '{"session_id":"test","prompt":"test"}' | bash ~/.claude/hooks/your-hook.sh
   ```
   Check stdout (the JSON output) and stderr (any errors).
3. **Validate the JSON** with `jq`:
   ```bash
   bash ~/.claude/hooks/your-hook.sh | jq .
   ```
   If `jq` errors, your JSON is malformed.
4. **Check for `set -e` traps.** If the script has `set -e` or `set -euo pipefail`, a partial failure mid-script can exit before emitting JSON, leaving the harness with empty stdout (which is also a schema error).

---

## Working examples to copy from

| Hook | File | Pattern |
|---|---|---|
| SessionStart with `additionalContext` | `~/.claude/hooks/linear-priorities.sh` | Live MCP query → JSON injection into Claude context |
| Stop with `systemMessage` | `.claude/hooks/v2-trigger-log.sh` | Session-end prompt to user terminal |
| PostToolUse counter | `~/.claude/hooks/repo-touch-tally.sh` (if applicable) | Tally per-tool invocations |

When writing a new hook, start by copying the one whose **event type matches yours** — not whose use case looks similar. Event type determines the schema; use case is secondary.

---

## Quick decision tree

> "I want to..."

- **...show text in the user's terminal at session start** → SessionStart hook + `echo >&2` (the `additionalContext` is for Claude, not the user)
- **...inject context into Claude's view at session start** → SessionStart hook + `hookSpecificOutput.additionalContext`
- **...show a prompt/reminder to the user when they finish a session** → Stop hook + `systemMessage`
- **...let Claude see something after a specific tool call fires** → PostToolUse hook + `hookSpecificOutput.additionalContext`
- **...gate or block a tool call** → PreToolUse hook + `permissionDecision`
- **...add per-turn context to Claude based on what the user typed** → UserPromptSubmit hook + `hookSpecificOutput.additionalContext`
