#!/usr/bin/env bash
# Deep Read ledger writer — YED-139 (Deep Read marker-enforcement gate, Layer 1 writer)
#
# The pipeline's parent thread calls this to record every Event page it touches and
# whether that page's Deep Read (Step 4.5) has been rendered. The companion Stop hook
# `deep-read-gate.sh` reads this ledger at session close and FAILS the run if any row
# is still `pending`. See .claude/proposals/deep-read-marker-gate.md.
#
# Ledger file: .claude/.state/<session>.deep_read_gate.jsonl  (one JSON object per line)
#   {"event":"<title>","page_id":"<notion-id>","marker":"pending|rendered|waived","reason":"<why, waive only>","ts":"<iso>"}
#
# Session id: prefers $CLAUDE_CODE_SESSION_ID (set in in-session Bash calls, same id the
# Stop hook receives as .session_id); falls back to `_pending` under Dock/--resume/subagent
# contexts where the env var is absent — exactly the dod-close.sh / build-session-emit.sh
# convention, so the Stop hook's `_pending` fallback reconciles it.
#
# Usage (called by the command specs, NOT by a user):
#   deep-read-ledger.sh add      "<event title>" "<notion page_id>"   # Step 4g — default PENDING (idempotent per page_id)
#   deep-read-ledger.sh rendered "<notion page_id>"                    # Step 4.5d success — flip to RENDERED
#   deep-read-ledger.sh waive    "<notion page_id>" "<reason>"         # explicit acknowledged-pending (e.g. renderer unregistered)
#   deep-read-ledger.sh list                                          # print the ledger rows (for the terminal gate)
#   deep-read-ledger.sh pending-count                                 # print the number of PENDING rows
#
# Never blocks: on any internal error it exits 0 (a broken ledger must not break the pipeline;
# the Stop hook fails-closed on what it can read).

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

STATE_DIR=".claude/.state"
SID="${CLAUDE_CODE_SESSION_ID:-_pending}"
LEDGER="$STATE_DIR/${SID}.deep_read_gate.jsonl"
mkdir -p "$STATE_DIR" 2>/dev/null

command -v jq >/dev/null 2>&1 || exit 0   # no jq → degrade silently; gate has nothing to read

CMD="${1:-}"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Rewrite the ledger, replacing the row whose page_id == $1 with $2 (a JSON object), or
# appending $2 if no such row exists. Atomic via temp file.
_upsert() {
  local pid="$1" newrow="$2" tmp
  tmp=$(mktemp) || return 0
  if [ -f "$LEDGER" ]; then
    jq -c --arg pid "$pid" 'select(.page_id != $pid)' "$LEDGER" > "$tmp" 2>/dev/null
  fi
  printf '%s\n' "$newrow" >> "$tmp"
  mv "$tmp" "$LEDGER" 2>/dev/null || rm -f "$tmp" 2>/dev/null
}

case "$CMD" in
  add)
    EVENT="${2:-}"; PID="${3:-}"
    [ -z "$PID" ] && { echo "deep-read-ledger: add needs <event> <page_id>" >&2; exit 0; }
    # Idempotent: if a row for this page_id already exists, leave it (don't clobber a `rendered`).
    if [ -f "$LEDGER" ] && jq -e --arg pid "$PID" 'select(.page_id == $pid)' "$LEDGER" >/dev/null 2>&1; then
      exit 0
    fi
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"pending", ts:$t}')
    _upsert "$PID" "$ROW"
    ;;
  rendered)
    PID="${2:-}"
    [ -z "$PID" ] && { echo "deep-read-ledger: rendered needs <page_id>" >&2; exit 0; }
    # Preserve the event title if a row already exists.
    EVENT=""
    if [ -f "$LEDGER" ]; then
      EVENT=$(jq -r --arg pid "$PID" 'select(.page_id == $pid) | .event' "$LEDGER" 2>/dev/null | head -1)
    fi
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"rendered", ts:$t}')
    _upsert "$PID" "$ROW"
    ;;
  waive)
    PID="${2:-}"; REASON="${3:-unspecified}"
    [ -z "$PID" ] && { echo "deep-read-ledger: waive needs <page_id> <reason>" >&2; exit 0; }
    EVENT=""
    if [ -f "$LEDGER" ]; then
      EVENT=$(jq -r --arg pid "$PID" 'select(.page_id == $pid) | .event' "$LEDGER" 2>/dev/null | head -1)
    fi
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg r "$REASON" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"waived", reason:$r, ts:$t}')
    _upsert "$PID" "$ROW"
    ;;
  list)
    [ -f "$LEDGER" ] && cat "$LEDGER"
    ;;
  pending-count)
    if [ -f "$LEDGER" ]; then
      jq -s '[.[] | select(.marker == "pending")] | length' "$LEDGER" 2>/dev/null || echo 0
    else
      echo 0
    fi
    ;;
  *)
    echo "deep-read-ledger: unknown command '${CMD}' (use: add|rendered|waive|list|pending-count)" >&2
    ;;
esac

exit 0
