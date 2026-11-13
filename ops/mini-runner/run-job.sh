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
LOG="${RUNJOB_LOG:-$LOGDIR/${JOB:-unknown}-$(date -u +%Y%m%dT%H%M%SZ).log}"   # a re-exec keeps the same log
exec >>"$LOG" 2>&1
echo "== $JOB start $(date -u +%FT%TZ) host=$(hostname)"

cd "$REAL" || { echo "FAIL: no checkout at $REAL"; exit 2; }
BR="$(git branch --show-current)"
[[ "$BR" == "main" ]] || { echo "FAIL: checkout is on '$BR', not main; refusing to run"; /usr/bin/python3 ops/mini-runner/alert.py job "$JOB" 3 "$LOG"; exit 3; }
SELF="$REAL/ops/mini-runner/run-job.sh"
SELF_SHA="$(shasum "$SELF" | awk '{print $1}')"
git pull --ff-only -q origin main || echo "WARN: git pull failed; running on $(git log -1 --format=%h)"
# zsh has already read this script into memory, so a pull that changes it would otherwise run the OLD version once
# (2026-11-13: the first `sweep` run failed "unknown job" right after pulling the commit that added it). Re-exec once.
if [[ -z "${RUNJOB_REEXEC:-}" && "$(shasum "$SELF" | awk '{print $1}')" != "$SELF_SHA" ]]; then
  echo "run-job.sh changed in this pull; re-running on the new version"
  RUNJOB_REEXEC=1 RUNJOB_LOG="$LOG" exec /bin/zsh "$SELF" "$JOB"
fi
echo "commit $(git log -1 --format='%h %s')"
[[ -x .venv/bin/python ]] || uv venv -q --python 3.12 .venv || { echo "FAIL: venv bootstrap"; /usr/bin/python3 ops/mini-runner/alert.py job "$JOB" 4 "$LOG"; exit 4; }
PY=.venv/bin/python

# YED-395: the laptop holds the local inventories reconcile reads (untracked Event Content, event-transcripts,
# .claude/.state/{research,briefs,post-event}). sync_inputs pulls a read-only mirror of them into INPUTS, outside
# every git work tree, over Tailscale with a dedicated key the laptop restricts to `rrsync -ro <checkout>`.
# --delete only ever touches INPUTS (a pure mirror). *.PRIVATE.* files are never copied (reconcile skips them anyway).
INPUTS="$HOME/Developer/esep-inputs"
LAPTOP="${ESEP_LAPTOP:-alexs-macbook-pro-2}"
sync_inputs() {
  mkdir -p "$INPUTS"
  # Media is excluded: reconcile classifies by file NAME and returns no evidence class for MEDIA_EXT
  # (reconcile.py), so copying recordings/slides would move gigabytes for zero signal. Keep this list in step with MEDIA_EXT.
  local media=(png jpg jpeg gif pdf html m4a mp3 mp4 mov wav docx pptx svg webp zip)
  local ex=(--exclude='*.PRIVATE.*' --exclude='.DS_Store')
  for e in $media; do ex+=(--exclude="*.$e" --exclude="*.${(U)e}"); done
  /opt/homebrew/bin/rsync -a --delete --delete-excluded --relative "${ex[@]}" \
    -e "ssh -i $HOME/.ssh/esep_sync -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes" \
    "$LAPTOP:Event Content/" ":event-transcripts/" \
    ":.claude/.state/research/" ":.claude/.state/briefs/" ":.claude/.state/post-event/" \
    "$INPUTS/"
  local rc=$?
  # 23/24 = partial transfer (e.g. one source dir doesn't exist on the laptop yet): keep what arrived, don't fail the job.
  [[ $rc -eq 23 || $rc -eq 24 ]] && { echo "WARN: partial sync rc=$rc (a source path is missing on the laptop)"; return 0; }
  return $rc
}

case "$JOB" in
  sync)
    sync_inputs
    RC=$?
    [[ $RC -eq 0 ]] && echo "sync OK: $(find "$INPUTS" -type f | wc -l | tr -d ' ') files in $INPUTS" \
                    || { [[ $RC -eq 255 ]] && echo "sync SKIP: laptop unreachable (asleep / off Tailscale); next hour retries" \
                                           || echo "sync FAIL rc=$RC: a real error, read this log"; }
    ;;
  reconcile)
    # Read-only (reconcile.py writes nothing to any database). Only output: the gitignored queue file + this log.
    # Inventories come from the laptop mirror when one exists (best-effort fresh pull first), else this checkout.
    sync_inputs && echo "pre-reconcile sync OK" || echo "WARN: pre-reconcile sync failed; using last mirror"
    ROOT="$REAL"; [[ -d "$INPUTS/Event Content" ]] && ROOT="$INPUTS"
    echo "inventory root: $ROOT"
    Q=.claude/.state/reconcile-queue.json
    mkdir -p .claude/.state
    BASE=()
    [[ -f "$Q" ]] && cp "$Q" .claude/.state/reconcile-queue.prev.json && BASE=(--baseline .claude/.state/reconcile-queue.prev.json)
    $PY .claude/scripts/substrate.py reconcile --report --root "$ROOT" --queue "$Q" "${BASE[@]}"
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
  sweep)
    # YED-384: daily theme sweep, the first scheduled job that runs a model. Read-only: the theme-sweeper agent holds
    # WebSearch + WebFetch only; theme-sweep.sh validates every manifest and writes only under .claude/.state/sweeps/.
    sync_inputs && echo "pre-sweep sync OK" || echo "WARN: pre-sweep sync failed; using last mirror"
    INPUTS_ROOT="$INPUTS" PY="$PY" zsh ops/mini-runner/theme-sweep.sh
    RC=$?
    ;;
  export)
    # YED-384 plan B3: incremental Notion export of brief bodies from the last run's cursor. Read-only against Notion
    # (notion_export.py only GETs); writes only the gitignored OUT folder and notion-export.watermark.json.
    # No model, no database writes. The first run on a machine has no watermark, so it backfills once.
    # OUT is one stable folder refreshed in place (one subfolder per event), NOT the script's default .state/briefs/:
    # reconcile reads that directory as post-event briefs, so ~170 exported bodies there would skew its report.
    WM=.claude/.state/notion-export.watermark.json
    OUT="${NOTION_EXPORT_OUT:-.claude/.state/notion-export-live}"
    echo "out: $OUT"
    if [[ -f "$WM" ]]; then
      MODE=incremental
      "$PY" -c 'import json,sys; w=json.load(open(sys.argv[1])); print("cursor: since=%s advanced=%s retry=%d" % (w.get("since"), w.get("advanced"), len(w.get("failed") or [])))' "$WM"
    else
      MODE=backfill; echo "no watermark yet: this run is a one-time backfill"
    fi
    # NOTION_TOKEN goes from this checkout's .env into the exporter's environment only; it is never echoed or exported
    # into this shell. Missing key = exit 7 (alerts), not a silent skip.
    "$PY" - "$MODE" "$OUT" <<'PYEOF'
import os, sys
key = None
try:
    for line in open(".env", encoding="utf-8"):
        k, _, v = line.strip().partition("=")
        if k == "NOTION_TOKEN":
            key = v.strip().strip('"').strip("'") or None
except OSError:
    pass
if not key:
    print("FAIL: no NOTION_TOKEN in the runner checkout's .env (add the Notion integration token there; launchd reads no shell profile)")
    sys.exit(7)
py = os.path.abspath(".venv/bin/python")
os.execve(py, [py, ".claude/scripts/notion_export.py", sys.argv[1], "--out", sys.argv[2]], dict(os.environ, NOTION_TOKEN=key))
PYEOF
    RC=$?
    # notion_export exits 0 even when single pages fail (it counts them and holds the cursor). Surface a held cursor
    # as a failure so the alert fires; the held pages are retried first on the next run.
    if [[ $RC -eq 0 && -f "$WM" ]] && ! "$PY" -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("advanced") else 1)' "$WM"; then
      echo "export: some pages failed; cursor held, they retry first next run"; RC=8
    fi
    ;;
  brief)
    # YED-384: Monday Market Brief for the current ISO week. Deterministic (market_brief.py is the whole render step
    # of /market-brief; no model). GET-only spine reads through spine_client; writes only the gitignored
    # .claude/.state/market-briefs/market-brief-<week>.md. No Notion publish, no spine writes.
    sync_inputs && echo "pre-brief sync OK" || echo "WARN: pre-brief sync failed; using last mirror"
    ROOT="$REAL"; [[ -d "$INPUTS/Event Content" ]] && ROOT="$INPUTS"
    WEEK="${BRIEF_WEEK:-$(date +%G-W%V)}"
    echo "week: $WEEK · inventory root: $ROOT"
    # market_brief reads a flat directory of RAW manifests and re-validates each strictly (the normalized *.valid.json
    # carries extra keys and is rejected). Sweeps live in .claude/.state/sweeps/<date>/: link the last 14 days' raw
    # ones; the script drops invalid ones and keeps those whose window overlaps the read week or the week before.
    SW="$(mktemp -d)"
    for f in .claude/.state/sweeps/*/*.raw.json(N.mw-2); do ln -s "$PWD/$f" "$SW/${${f:h}:t}-${f:t}"; done
    echo "sweep manifests linked: $(ls "$SW" | wc -l | tr -d ' ')"
    "$PY" .claude/scripts/market_brief.py --week "$WEEK" --root "$ROOT" --sweeps "$SW"
    RC=$?
    rm -rf "$SW"
    ;;
  *)
    echo "FAIL: unknown job '$JOB' (known: sync, reconcile, smoke, sweep, export, brief)"; RC=64 ;;
esac
echo "== $JOB end $(date -u +%FT%TZ) exit=$RC"
# Failure alert (Linear issue when LINEAR_API_KEY is in .env, plus a notification and ALERTS.txt; once per job per day),
# and a login check after every model job. alert.py never changes the exit code.
"$PY" ops/mini-runner/alert.py job "$JOB" "$RC" "$LOG"
# brief runs no model, but it is the one job sure to run every Monday: a weekly early warning before sweeps start failing.
[[ "$JOB" == (sweep|smoke|brief) ]] && "$PY" ops/mini-runner/alert.py login
exit $RC
