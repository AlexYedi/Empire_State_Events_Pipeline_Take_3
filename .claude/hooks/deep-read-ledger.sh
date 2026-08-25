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
# Corruption resilience (adversarial review finding #1): the upsert and the counters
# process the ledger LINE BY LINE. jq run over a whole file aborts the stream at the
# first invalid line, which would silently drop every other row (a false-green path);
# line-by-line means one bad line never wipes the others, and unparseable lines are
# PRESERVED and COUNTED AS PENDING (fail-closed) rather than skipped.
#
# Session id: prefers $CLAUDE_CODE_SESSION_ID (set in in-session Bash calls, same id the
# Stop hook receives as .session_id); falls back to `_pending` under Dock/--resume/subagent
# contexts where the env var is absent — the dod-close.sh / build-session-emit.sh convention.
#
# Usage (called by the command specs, NOT by a user):
#   deep-read-ledger.sh add      "<event title>" "<notion page_id>"   # Step 4g — default PENDING (idempotent per page_id)
#   deep-read-ledger.sh rendered "<notion page_id>"                    # Step 4.5d success — flip to RENDERED
#   deep-read-ledger.sh waive    "<notion page_id>" "<reason>"         # explicit acknowledged-pending (also logged durably)
#   deep-read-ledger.sh list                                          # print the ledger rows (for the terminal gate)
#   deep-read-ledger.sh pending-count                                 # PENDING + unparseable line count (fail-closed)
#
# Never blocks: on any internal error it exits 0 (a broken ledger must not break the pipeline;
# the Stop hook fails-closed on what it can read).

set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0

STATE_DIR=".claude/.state"
FAIL_LOG=".claude/artifacts/deep-read-gate-failures.jsonl"
SID="${CLAUDE_CODE_SESSION_ID:-_pending}"
LEDGER="$STATE_DIR/${SID}.deep_read_gate.jsonl"
mkdir -p "$STATE_DIR" 2>/dev/null

command -v jq >/dev/null 2>&1 || exit 0   # no jq → degrade silently; gate has nothing to read

CMD="${1:-}"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Rewrite the ledger, replacing the row whose page_id == $1 with the JSON object $2, or
# appending $2 if no such row exists. Line-by-line so a corrupt line can never wipe others;
# corrupt/other lines are kept verbatim. Atomic same-volume rename.
_upsert() {
  local pid="$1" newrow="$2" tmp linepid
  tmp=$(mktemp "$LEDGER.XXXXXX") || return 0
  if [ -f "$LEDGER" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      [ -z "$line" ] && continue
      linepid=$(printf '%s' "$line" | jq -r '.page_id // empty' 2>/dev/null)
      # Drop only a cleanly-parsed row that matches the target page_id; keep everything
      # else — including unparseable lines — so corruption is preserved, never dropped.
      [ "$linepid" = "$pid" ] && continue
      printf '%s\n' "$line" >> "$tmp"
    done < "$LEDGER"
  fi
  printf '%s\n' "$newrow" >> "$tmp"
  mv "$tmp" "$LEDGER" 2>/dev/null || rm -f "$tmp" 2>/dev/null
}

# Count PENDING rows, failing closed: a non-empty line that does not cleanly parse to a
# JSON object, or parses without a recognizable marker, counts as PENDING (needs attention).
_pending_count() {
  local f="$1" total=0 marker
  [ -f "$f" ] || { echo 0; return; }
  while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue
    marker=$(printf '%s' "$line" | jq -r 'if type=="object" then (.marker // "CORRUPT") else "CORRUPT" end' 2>/dev/null)
    [ -z "$marker" ] && marker="CORRUPT"
    case "$marker" in pending|CORRUPT) total=$((total+1));; esac
  done < "$f"
  echo "$total"
}

case "$CMD" in
  add)
    EVENT="${2:-}"; PID="${3:-}"
    [ -z "$PID" ] && { echo "deep-read-ledger: add needs <event> <page_id>" >&2; exit 0; }
    # Idempotent: if a row for this page_id already exists, leave it (don't clobber `rendered`).
    if [ -f "$LEDGER" ] && grep -Fq "\"page_id\":\"$PID\"" "$LEDGER" 2>/dev/null; then
      exit 0
    fi
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"pending", ts:$t}')
    _upsert "$PID" "$ROW"
    ;;
  rendered)
    PID="${2:-}"
    [ -z "$PID" ] && { echo "deep-read-ledger: rendered needs <page_id>" >&2; exit 0; }
    EVENT=""
    [ -f "$LEDGER" ] && EVENT=$(grep -F "\"page_id\":\"$PID\"" "$LEDGER" 2>/dev/null | tail -1 | jq -r '.event // empty' 2>/dev/null)
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"rendered", ts:$t}')
    _upsert "$PID" "$ROW"
    ;;
  waive)
    PID="${2:-}"; REASON="${3:-unspecified}"
    [ -z "$PID" ] && { echo "deep-read-ledger: waive needs <page_id> <reason>" >&2; exit 0; }
    EVENT=""
    [ -f "$LEDGER" ] && EVENT=$(grep -F "\"page_id\":\"$PID\"" "$LEDGER" 2>/dev/null | tail -1 | jq -r '.event // empty' 2>/dev/null)
    ROW=$(jq -cn --arg e "$EVENT" --arg p "$PID" --arg r "$REASON" --arg t "$NOW" \
      '{event:$e, page_id:$p, marker:"waived", reason:$r, ts:$t}')
    _upsert "$PID" "$ROW"
    # Durability (review finding #5): a waive is NOT a silent pass. Record it in the same
    # durable failure log the gate writes, so a self-waive still surfaces in rigor-review.
    mkdir -p "$(dirname "$FAIL_LOG")" 2>/dev/null
    jq -cn --arg s "$SID" --arg e "$EVENT" --arg p "$PID" --arg r "$REASON" --arg t "$NOW" \
      '{event:"deep_read_gate_waived", session:$s, page_event:$e, page_id:$p, reason:$r, ts:$t}' >> "$FAIL_LOG" 2>/dev/null
    ;;
  list)
    [ -f "$LEDGER" ] && cat "$LEDGER"
    ;;
  pending-count)
    _pending_count "$LEDGER"
    ;;
  *)
    echo "deep-read-ledger: unknown command '${CMD}' (use: add|rendered|waive|list|pending-count)" >&2
    ;;
esac

exit 0
