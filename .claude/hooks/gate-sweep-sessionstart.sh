#!/usr/bin/env bash
# gate-sweep-sessionstart.sh — SessionStart hook (2026-09-27, sibling of the two Stop-hook gates).
#
# A dead session never fires Stop again, so a run that crashed with a `pending` ledger row would
# never be logged by deep-read-gate.sh / substrate-gate.sh once those gates stopped firing per turn
# (see _run_in_progress.sh). This sweep is the abandoned-run half of that change: at the start of
# ANY session it scans every per-session ledger for pending rows whose session holds no live event
# claim and whose row is older than STALE_HOURS, logs each once as `*_gate_abandoned`, and prints
# them so the new session sees what an earlier one left behind. It writes nothing else.
#
# SessionEnd mode (`--session-end`, YED-228 follow-up): Claude Code's SessionEnd event (verified 2026-09-27 in the
# hooks docs: fires when a session terminates, cannot block, stdout not shown) passes {session_id, reason}. In that
# mode the sweep looks ONLY at the ending session's ledgers, with no age threshold and without the live-claim
# exemption — the session is ending, so a claim it never released no longer means "in progress" — and logs its
# pending rows as abandoned at the moment of death instead of at the next SessionStart >4h later. `reason=resume`
# is skipped: the same conversation continues. Log-once keys make the later SessionStart sweep a no-op for them.
#
# Always exit 0. Plain-text stdout (same convention as graph-sessionstart.sh).

set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
command -v jq >/dev/null 2>&1 || exit 0
. "$(dirname "${BASH_SOURCE[0]}")/_run_in_progress.sh"

STATE_DIR=".claude/.state"
STALE_HOURS="${GATE_STALE_HOURS:-4}"
ONLY_SID=""; MIN_AGE=$(( STALE_HOURS * 3600 )); IGNORE_CLAIM=0
if [ "${1:-}" = "--session-end" ]; then
  IN=$(cat)
  ONLY_SID=$(printf '%s' "$IN" | jq -r '.session_id // empty' 2>/dev/null)
  REASON=$(printf '%s' "$IN" | jq -r '.reason // "other"' 2>/dev/null)
  { [ -z "$ONLY_SID" ] || [ "$REASON" = "resume" ]; } && exit 0
  MIN_AGE=0; IGNORE_CLAIM=1
fi
NOW_S=$(date -u +%s)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT=""

sweep() {   # sweep <ledger-glob-suffix> <log> <event-name> <id-field>
  local suffix="$1" log="$2" ev_name="$3" idf="$4" f sid line obj marker ts age id label events
  shopt -s nullglob
  for f in "$STATE_DIR"/*."$suffix"; do
    sid=$(basename "$f" ".$suffix")
    [ "$sid" = "_pending" ] && continue                  # no session to attribute; the gates handle it
    [ -n "$ONLY_SID" ] && [ "$sid" != "$ONLY_SID" ] && continue   # SessionEnd: only the ending session
    [ "$IGNORE_CLAIM" = 1 ] || { run_in_progress "$sid" && continue; }   # that session is live → not abandoned
    while IFS= read -r line || [ -n "$line" ]; do
      [ -z "$line" ] && continue
      obj=$(printf '%s' "$line" | jq -c 'if type=="object" then . else empty end' 2>/dev/null) || continue
      [ -z "$obj" ] && continue
      marker=$(printf '%s' "$obj" | jq -r '.marker // ""')
      [ "$marker" = "pending" ] || continue
      ts=$(printf '%s' "$obj" | jq -r '.ts // ""')
      age=$(( NOW_S - $( printf '%s' "$ts" | jq -Rr 'fromdate? // 0' 2>/dev/null || echo 0) ))
      [ "$age" -ge "$MIN_AGE" ] || continue
      id=$(printf '%s' "$obj" | jq -r ".$idf // \"?\"")
      label=$(printf '%s' "$obj" | jq -r '.event // "(untitled event)"')
      events=$(jq -cn --arg e "$label" --arg i "$id" --arg k "$idf" '[{event:$e} + {($k):$i}]')
      if ! already_logged "$log" "$ev_name" "$sid" "$events"; then
        mkdir -p "$(dirname "$log")" 2>/dev/null
        jq -cn --arg s "$sid" --arg t "$NOW" --argjson ev "$events" --arg src "$f" \
          '{event:$ev_name, session:$s, ts:$t, pending:1, corrupt:0, events:$ev, ledger:$src}' --arg ev_name "$ev_name" \
          >> "$log" 2>/dev/null
      fi
      OUT="${OUT}  - ${label}  ·  ${idf} ${id:0:17}  ·  session ${sid:0:8}  ·  pending since ${ts}
"
    done < "$f"
  done
  shopt -u nullglob
}

sweep "deep_read_gate.jsonl" ".claude/artifacts/deep-read-gate-failures.jsonl" "deep_read_gate_abandoned" "page_id"
sweep "substrate_gate.jsonl" ".claude/artifacts/substrate-gate-failures.jsonl" "substrate_gate_abandoned" "key"

if [ -n "$OUT" ]; then
  printf '## ⚠️ Abandoned gate rows (an earlier session closed with work pending)\n\n%s\nResolve each by re-running the step (Deep Read: Step 4.5 → `deep-read-ledger.sh rendered`; graph: `substrate.py stage-research|stage-claims`) or waive it with a logged reason. Logged once per row to the gate-failures artifacts.\n' "$OUT"
fi
exit 0
