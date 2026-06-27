#!/usr/bin/env bash
# Project judge runs (.claude/evals/logs/*.jsonl) -> PostHog as `judge_run` events.
# Mirrors build-session-emit.sh: the JSONL is the AUTHORITATIVE record; PostHog is the derived,
# swappable projection. Idempotent via $insert_id = run_id (re-runs dedup, no double-count).
# Content-gated: scores / verdict / per-criterion scores / ack only — NO reasoning text, no prompts.
#
# Usage: run after a judge run (or wire into /judge-build). Reads POSTHOG_PROJECT_KEY from .env.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" || exit 0
if [ -z "${POSTHOG_PROJECT_KEY:-}" ] && [ -f ".env" ]; then
  set -a; . ./.env 2>/dev/null || true; set +a
fi
[ -z "${POSTHOG_PROJECT_KEY:-}" ] && { echo "no POSTHOG_PROJECT_KEY — JSONL remains the record; skipping projection"; exit 0; }
HOST="${POSTHOG_HOST:-https://us.i.posthog.com}"

n=0
for f in .claude/evals/logs/*.jsonl; do
  [ -f "$f" ] || continue
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    payload=$(printf '%s' "$line" | jq -c --arg k "$POSTHOG_PROJECT_KEY" '
      {api_key:$k, event:"judge_run",
       distinct_id:("judge-" + (.artifact_type // "artifact")),
       timestamp:.timestamp,
       properties:{
         "$insert_id": .run_id, run_id: .run_id, rubric: .rubric,
         artifact: .artifact, artifact_type: .artifact_type,
         weighted_score: .weighted_score, verdict: .verdict,
         acked: ((.alex_ack // null) != null),
         ack_agree: (((.alex_ack // "") | ascii_downcase | startswith("agree"))),
         criteria: ([.criterion_scores[]? | {(.id): .score}] | add)
       }}' 2>/dev/null) || continue
    [ -z "$payload" ] && continue
    code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 8 -X POST "$HOST/capture/" \
      -H "Content-Type: application/json" -d "$payload" 2>/dev/null || echo "ERR")
    echo "  $(basename "$f"): HTTP $code"
    n=$((n+1))
  done < "$f"
done
echo "projected $n judge run(s) to PostHog"
