#!/usr/bin/env bash
# Stop hook — build-session telemetry emitter (YED-88 · PRD US-2)
#
# Contract-first, lean foundation (decided 2026-06-26: defer the OTEL collector + Langfuse platform):
#   1. ALWAYS append an authoritative `build_session` record to .claude/artifacts/build-sessions.jsonl
#      (source of truth; survives any backend change).
#   2. PROJECT to PostHog /capture/ ONLY if $POSTHOG_PROJECT_KEY is set (derived, swappable adapter).
#
# Content-gated by construction: emits metadata + counts ONLY — never prompt/tool-input/output bodies (YED-81).
# Contract: .claude/references/build-session-contract.md (v1).
# Stop hooks emit a top-level `systemMessage` if anything; this one stays silent on success.

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

# Load project .env (where POSTHOG_PROJECT_KEY lives) if the key isn't already in the environment.
# A .env is not auto-loaded into a hook's process, so source it here. All non-assignment lines in
# .env are `#` comments, so this is safe; guarded so it never aborts the hook.
if [ -z "${POSTHOG_PROJECT_KEY:-}" ] && [ -f ".env" ]; then
  set -a; . ./.env 2>/dev/null || true; set +a
fi

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -z "$SESSION_ID" ] && exit 0

# Disable override (mirrors the v2-trigger-log convention)
SETTINGS_LOCAL=".claude/settings.local.json"
if [ -f "$SETTINGS_LOCAL" ]; then
  if jq -e '.hooks.disable | index("build-session-emit")' "$SETTINGS_LOCAL" >/dev/null 2>&1; then
    exit 0
  fi
fi

CONTRACT_VERSION="1"
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
PROJECT=$(basename "${CWD:-${CLAUDE_PROJECT_DIR:-$(pwd)}}")
ENDED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RUN_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")

# --- transcript-derived metrics (best-effort; content-gated = counts only) ---
TOOL_USES=0; ASSISTANT_TURNS=0; TOKENS_IN=0; TOKENS_OUT=0; STARTED_AT=""; BUILD_TOUCHED=false; TOOLS_USED="[]"
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  TOOL_USES=$(jq -s '[.[]? | (.message.content // []) | .[]? | select(.type=="tool_use")] | length' "$TRANSCRIPT" 2>/dev/null || echo 0)
  TOOLS_USED=$(jq -cs '[.[]? | (.message.content // []) | .[]? | select(.type=="tool_use") | .name] | unique' "$TRANSCRIPT" 2>/dev/null || echo "[]")
  ASSISTANT_TURNS=$(jq -s '[.[]? | select(.type=="assistant")] | length' "$TRANSCRIPT" 2>/dev/null || echo 0)
  TOKENS_IN=$(jq -s '[.[]? | .message.usage.input_tokens // empty] | add // 0' "$TRANSCRIPT" 2>/dev/null || echo 0)
  TOKENS_OUT=$(jq -s '[.[]? | .message.usage.output_tokens // empty] | add // 0' "$TRANSCRIPT" 2>/dev/null || echo 0)
  STARTED_AT=$(jq -rs '[.[]? | .timestamp // empty] | first // ""' "$TRANSCRIPT" 2>/dev/null || echo "")
  if jq -es 'any(.[]?; (.message.content // []) | .[]? | select(.type=="tool_use" and (.name=="Edit" or .name=="Write")) | ((.input.file_path // "") | test("\\.claude/(skills|agents|commands|hooks)")))' "$TRANSCRIPT" >/dev/null 2>&1; then
    BUILD_TOUCHED=true
  fi
fi

# Defensive defaults (guard against empty → invalid JSON)
[ -z "${TOOL_USES//[0-9]/}" ] || TOOL_USES=0
[ -z "${ASSISTANT_TURNS//[0-9]/}" ] || ASSISTANT_TURNS=0
[ -z "${TOKENS_IN//[0-9]/}" ] || TOKENS_IN=0
[ -z "${TOKENS_OUT//[0-9]/}" ] || TOKENS_OUT=0
echo "$TOOLS_USED" | jq -e . >/dev/null 2>&1 || TOOLS_USED="[]"

# --- optional semantic fields (set during the session by DoD/judge wiring; nullable) ---
META_FILE=".claude/.state/${SESSION_ID}.build_meta"
DOD_MET=null; DOD_WAIVED=null; CORRECTION_ROUNDS=null
if [ -f "$META_FILE" ]; then
  DOD_MET=$(jq -c '.dod_met // null' "$META_FILE" 2>/dev/null || echo null)
  DOD_WAIVED=$(jq -c '.dod_waived // null' "$META_FILE" 2>/dev/null || echo null)
  CORRECTION_ROUNDS=$(jq -c '.correction_rounds // null' "$META_FILE" 2>/dev/null || echo null)
fi

# --- build the authoritative record (content-gated) ---
RECORD=$(jq -nc \
  --arg sid "$SESSION_ID" --arg cv "$CONTRACT_VERSION" --arg rv "$RUN_VERSION" \
  --arg proj "$PROJECT" --arg started "$STARTED_AT" --arg ended "$ENDED_AT" \
  --argjson tool_uses "$TOOL_USES" --argjson turns "$ASSISTANT_TURNS" \
  --argjson tin "$TOKENS_IN" --argjson tout "$TOKENS_OUT" \
  --argjson tools "$TOOLS_USED" --argjson touched "$BUILD_TOUCHED" \
  --argjson dod_met "$DOD_MET" --argjson dod_waived "$DOD_WAIVED" --argjson corr "$CORRECTION_ROUNDS" \
  '{event:"build_session", contract_version:$cv, session_id:$sid, run_version:$rv, project:$proj,
    started_at:$started, ended_at:$ended, tool_uses:$tool_uses, assistant_turns:$turns,
    tokens_in:$tin, tokens_out:$tout, tools_used:$tools, build_dir_touched:$touched,
    dod_met:$dod_met, dod_waived:$dod_waived, correction_rounds:$corr}' 2>/dev/null) || exit 0

[ -z "$RECORD" ] && exit 0

# --- 1. authoritative append-only record (always) ---
mkdir -p .claude/artifacts
printf '%s\n' "$RECORD" >> .claude/artifacts/build-sessions.jsonl

# --- 2. PostHog projection (derived; only if key present) ---
if [ -n "${POSTHOG_PROJECT_KEY:-}" ]; then
  PAYLOAD=$(echo "$RECORD" | jq -c \
    --arg k "$POSTHOG_PROJECT_KEY" --arg did "alex-${PROJECT}" --arg ts "$ENDED_AT" \
    '{api_key:$k, event:"build_session", distinct_id:$did, timestamp:$ts, properties:.}')
  curl -sf --max-time 5 -X POST "${POSTHOG_HOST:-https://us.i.posthog.com}/capture/" \
    -H "Content-Type: application/json" -d "$PAYLOAD" >/dev/null 2>&1 || true
fi

exit 0
