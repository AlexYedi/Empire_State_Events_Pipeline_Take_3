#!/usr/bin/env bash
# test_gate_in_progress.sh — pins the Stop-hook gates' per-turn vs run-close semantics (2026-09-27).
#
# Background: Claude Code fires Stop at every turn end. Before this change a `pending` ledger row
# blocked every turn and logged one FALSE failure row per turn (9 rows in session b7b796e0). Now a
# pending row is in-progress while the session holds a live event claim, and failure rows are
# written once per (session, event set). Offline, free: temp project dir, temp claim dir.
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
TMP=$(mktemp -d -t gatetest)
export CLAUDE_PROJECT_DIR="$TMP" EVENT_CLAIM_DIR="$TMP/claims" GATE_STALE_HOURS=4
mkdir -p "$TMP/.claude/.state" "$TMP/.claude/artifacts" "$EVENT_CLAIM_DIR"
G="$REPO/.claude/hooks/deep-read-gate.sh"; S="$REPO/.claude/hooks/substrate-gate.sh"
SW="$REPO/.claude/hooks/gate-sweep-sessionstart.sh"
DLOG="$TMP/.claude/artifacts/deep-read-gate-failures.jsonl"; SLOG="$TMP/.claude/artifacts/substrate-gate-failures.jsonl"
SID="test-session-1"
ok=0; n=0
ck() { n=$((n+1)); if eval "$2"; then ok=$((ok+1)); echo "  ✓ $1"; else echo "  ✗ $1"; fi; }
run() { printf '{"session_id":"%s","stop_hook_active":%s}' "$1" "$2" | bash "$3" 2>/dev/null; }
rows() { if [ -f "$1" ]; then grep -c "\"event\":\"$2\"" "$1"; else echo 0; fi; }   # grep -c prints 0 itself (exit 1 is not an error here)
NOWZ=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OLDZ=$(python3 -c "import datetime as d;print((d.datetime.now(d.timezone.utc)-d.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%SZ'))")

echo "{\"event\":\"E\",\"page_id\":\"p1\",\"marker\":\"pending\",\"ts\":\"$NOWZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
echo "{\"key\":\"research:p1\",\"event\":\"E\",\"marker\":\"pending\",\"phase\":\"pre_event\",\"ts\":\"$NOWZ\"}" > "$TMP/.claude/.state/$SID.substrate_gate.jsonl"
claim() { printf '{"event":"E","slug":"e","session_id":"%s","claimed_at":"%s","heartbeat":"%s","ttl_hours":%s,"released_at":%s}' "$1" "$2" "$2" "$3" "$4" > "$EVENT_CLAIM_DIR/e.json"; }

echo "in-progress (claim live for THIS session)"
claim "$SID" "$NOWZ" 4.0 null
out=$(run "$SID" false "$G"); ck "(a) deep-read: pending + live claim → silent, no block" '[ -z "$out" ]'
out=$(run "$SID" false "$S"); ck "(a) substrate: pending + live claim → silent, no block" '[ -z "$out" ]'
out=$(run "$SID" true "$G");  ck "(a) even with stop_hook_active → silent, nothing logged" '[ -z "$out" ] && [ "$(rows "$DLOG" deep_read_gate_failed)" = 0 ]'

echo "not in progress"
claim "other-session" "$NOWZ" 4.0 null
out=$(run "$SID" false "$G"); ck "(a2) another session's claim does not count → block" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
claim "$SID" "$NOWZ" 4.0 "\"$NOWZ\""
out=$(run "$SID" false "$G"); ck "(b) claim RELEASED → first stop blocks" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
ck "(b) ...and blocking logs nothing" '[ "$(rows "$DLOG" deep_read_gate_failed)" = 0 ]'
out=$(run "$SID" true "$G");  ck "(b) second stop (stop_hook_active) → systemMessage + exactly 1 row" 'printf "%s" "$out" | grep -q systemMessage && [ "$(rows "$DLOG" deep_read_gate_failed)" = 1 ]'
out=$(run "$SID" true "$G");  ck "(c) third stop → still exactly 1 row (log-once)" '[ "$(rows "$DLOG" deep_read_gate_failed)" = 1 ]'
out=$(run "$SID" false "$S"); ck "(b) substrate: released claim → block" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
out=$(run "$SID" true "$S"); out=$(run "$SID" true "$S"); ck "(c) substrate: two closing stops → 1 row" '[ "$(rows "$SLOG" substrate_gate_failed)" = 1 ]'
claim "$SID" "$OLDZ" 4.0 null
out=$(run "$SID" false "$G"); ck "(b2) EXPIRED claim (5h old, ttl 4h) → block" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
claim "$SID" "$NOWZ" 4.0 null
out=$(run "" false "$G");     ck "(d) empty session id → strict path (block), claim ignored" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
printf '{ broken json' > "$EVENT_CLAIM_DIR/e.json"
out=$(run "$SID" false "$G"); ck "(e) corrupt claim file → strict path (block)" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'
rm -f "$EVENT_CLAIM_DIR/e.json"
out=$(run "$SID" false "$G"); ck "(e2) no claim dir contents → block" 'printf "%s" "$out" | grep -q "\"decision\":\"block\""'

echo "SessionStart sweep (abandoned runs)"
echo "{\"event\":\"E\",\"page_id\":\"p1\",\"marker\":\"pending\",\"ts\":\"$NOWZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
out=$(bash "$SW" 2>/dev/null); ck "(f) fresh pending row, no claim → not abandoned yet, no output" '[ -z "$out" ] && [ "$(rows "$DLOG" deep_read_gate_abandoned)" = 0 ]'
echo "{\"event\":\"E\",\"page_id\":\"p1\",\"marker\":\"pending\",\"ts\":\"$OLDZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
out=$(bash "$SW" 2>/dev/null); ck "(f) 5h-old pending row, no claim → reported + 1 abandoned row" 'printf "%s" "$out" | grep -q "Abandoned gate rows" && [ "$(rows "$DLOG" deep_read_gate_abandoned)" = 1 ]'
out=$(bash "$SW" 2>/dev/null); ck "(f) second sweep → still 1 row (log-once), still reported" 'printf "%s" "$out" | grep -q "Abandoned gate rows" && [ "$(rows "$DLOG" deep_read_gate_abandoned)" = 1 ]'
claim "$SID" "$NOWZ" 4.0 null
out=$(bash "$SW" 2>/dev/null); ck "(f) old row but session claim live → not abandoned" '[ -z "$out" ]'

echo "SessionEnd mode (YED-228 follow-up)"
rm -f "$DLOG" "$SLOG"
echo "{\"event\":\"E\",\"page_id\":\"p1\",\"marker\":\"pending\",\"ts\":\"$NOWZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
echo "{\"event\":\"F\",\"page_id\":\"p9\",\"marker\":\"pending\",\"ts\":\"$NOWZ\"}" > "$TMP/.claude/.state/other-session.deep_read_gate.jsonl"
se() { printf '{"session_id":"%s","reason":"%s","hook_event_name":"SessionEnd"}' "$1" "$2" | bash "$SW" --session-end >/dev/null 2>&1; }
se "$SID" resume;             ck "(g) reason=resume → nothing logged (same conversation continues)" '[ "$(rows "$DLOG" deep_read_gate_abandoned)" = 0 ]'
se "$SID" prompt_input_exit;  ck "(g) session exits with a FRESH pending row + live claim → logged abandoned (no age, claim ignored)" '[ "$(rows "$DLOG" deep_read_gate_abandoned)" = 1 ]'
ck "(g) ...only the ending session: the other session's row is untouched" '! grep -q "p9" "$DLOG"'
se "$SID" other;              ck "(g) second SessionEnd → still 1 row (log-once)" '[ "$(rows "$DLOG" deep_read_gate_abandoned)" = 1 ]'
rm -f "$EVENT_CLAIM_DIR/e.json"
echo "{\"event\":\"E\",\"page_id\":\"p1\",\"marker\":\"pending\",\"ts\":\"$OLDZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
bash "$SW" >/dev/null 2>&1;  ck "(g) the later SessionStart sweep does not double-log it" '[ "$(rows "$DLOG" deep_read_gate_abandoned)" = 1 ]'

echo "corrupt ts never crashes the sweep (PR #139, found by the Gemini seat)"
rm -f "$DLOG" "$EVENT_CLAIM_DIR/e.json"
printf '%s\n%s\n%s\n' \
  '{"event":"E1","page_id":"q1","marker":"pending","ts":""}' \
  '{"event":"E2","page_id":"q2","marker":"pending"}' \
  "{\"event\":\"E3\",\"page_id\":\"q3\",\"marker\":\"pending\",\"ts\":\"$OLDZ\"}" > "$TMP/.claude/.state/$SID.deep_read_gate.jsonl"
out=$(bash "$SW" 2>&1); rc=$?
ck "(i) empty ts + missing ts + a valid old row → sweep exits 0, no shell error" '[ "$rc" = 0 ] && ! printf "%s" "$out" | grep -qi "bad math\|syntax error"'
ck "(i) ...all three rows surfaced (corrupt ts reads as ancient; the row after them is still reached)" '[ "$(rows "$DLOG" deep_read_gate_abandoned)" = 3 ]'
ck "(i) ...and the corrupt ones are labelled as such" 'printf "%s" "$out" | grep -q "no ts — corrupt row"'

echo "gate that cannot run says so (YED-228 follow-up)"
NOJQ="$TMP/nojq"; mkdir -p "$NOJQ"; for b in bash cat dirname date grep printf; do ln -sf "$(command -v $b)" "$NOJQ/$b" 2>/dev/null; done
out=$(printf '{"session_id":"%s","stop_hook_active":false}' "$SID" | PATH="$NOJQ" "$NOJQ/bash" "$G" 2>/dev/null)
ck "(h) deep-read gate without jq → systemMessage naming the cause, not silence" 'printf "%s" "$out" | grep -q "gate could NOT run (jq not installed)"'
out=$(printf '{"session_id":"%s","stop_hook_active":false}' "$SID" | PATH="$NOJQ" "$NOJQ/bash" "$S" 2>/dev/null)
ck "(h) substrate gate without jq → systemMessage" 'printf "%s" "$out" | grep -q "substrate-gate: gate could NOT run"'
out=$(printf '{}' | CLAUDE_PROJECT_DIR="$TMP/does-not-exist" bash "$G" 2>/dev/null)
ck "(h) unreachable project dir → systemMessage" 'printf "%s" "$out" | grep -q "project dir unreachable"'

echo "selftest: $ok/$n gate cases pass"
rm -rf "$TMP"
[ "$ok" -eq "$n" ]
