#!/bin/zsh
# esep-mini scheduled-job runner (YED-347; fallback per decision YED-385 after bridge env ids proved unstable).
# Called by launchd: run-job.sh <job>. Runs in the REAL checkout (it holds the gitignored inputs), on main only.
# Never prints secrets: .env is read by spine_client.py itself, never by this script.
set -u
REAL="$HOME/Developer/Empire_State_Events_Pipeline_Take_3"
LOGDIR="$HOME/Library/Logs/esep-runner"
JOB="${1:-}"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export ENABLE_CLAUDEAI_MCP_SERVERS=false   # no claude.ai connectors in any job
mkdir -p "$LOGDIR"
LOG="$LOGDIR/${JOB:-unknown}-$(date -u +%Y%m%dT%H%M%SZ).log"
exec >>"$LOG" 2>&1
echo "== $JOB start $(date -u +%FT%TZ) host=$(hostname)"

cd "$REAL" || { echo "FAIL: no checkout at $REAL"; exit 2; }
BR="$(git branch --show-current)"
[[ "$BR" == "main" ]] || { echo "FAIL: checkout is on '$BR', not main; refusing to run"; exit 3; }
git pull --ff-only -q origin main || echo "WARN: git pull failed; running on $(git log -1 --format=%h)"
echo "commit $(git log -1 --format='%h %s')"
[[ -x .venv/bin/python ]] || uv venv -q --python 3.12 .venv || { echo "FAIL: venv bootstrap"; exit 4; }
PY=.venv/bin/python

case "$JOB" in
  reconcile)
    # Read-only (reconcile.py writes nothing to any database). Only output: the gitignored queue file + this log.
    Q=.claude/.state/reconcile-queue.json
    mkdir -p .claude/.state
    BASE=()
    [[ -f "$Q" ]] && cp "$Q" .claude/.state/reconcile-queue.prev.json && BASE=(--baseline .claude/.state/reconcile-queue.prev.json)
    $PY .claude/scripts/substrate.py reconcile --report --queue "$Q" "${BASE[@]}"
    RC=$?
    ;;
  smoke)
    # Proves the claude -p path headless under launchd: tools limited, no MCP, no prompts (dontAsk denies anything else).
    claude -p --model sonnet --permission-mode dontAsk --strict-mcp-config --no-session-persistence \
      --allowedTools "Bash(.venv/bin/python:*)" "Bash(hostname)" "WebSearch" -- \
      "READ-ONLY smoke test. Make no writes anywhere and never display .env or any secret. Run each command below as its own separate Bash call (no chaining), report raw output, and keep going if one fails.
(a) .venv/bin/python .claude/scripts/spine_client.py --selftest   -> PASS if the last line says all guard cases pass.
(b) .venv/bin/python -c \"import sys; sys.path.insert(0,'.claude/scripts'); import spine_client as s; print(s.req('GET','/lane_registry?select=lane,active'))\"   -> PASS if it starts with (200,
(c) one WebSearch for: PostgREST horizontal filtering documentation   -> PASS if at least one result.
(d) hostname   -> PASS only if exactly esep-mini.
End with one line per check (check | PASS/FAIL | evidence), then SMOKE: ALL PASS or SMOKE: FAIL (<which>)."
    RC=$?
    ;;
  *)
    echo "FAIL: unknown job '$JOB' (known: reconcile, smoke)"; RC=64 ;;
esac
echo "== $JOB end $(date -u +%FT%TZ) exit=$RC"
exit $RC
