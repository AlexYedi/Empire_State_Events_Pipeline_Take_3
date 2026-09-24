#!/usr/bin/env bash
# ab-reminder.sh — SessionStart callout for the YED-172 A/B while it is live.
#
# Why a hook and not a note: the A/B is time-boxed (two events, due 2026-09-26) and any session opened in
# this repo — either checkout, any worktree — is a session that could run or forget it. A note only works
# if someone opens the note.
#
# It is LOUD while due, SILENT once done, and expires by itself:
#   * prints nothing outside [WINDOW_START, HARD_STOP]
#   * prints nothing for an event whose scorecard log already exists (.claude/evals/logs/*ab-yed172*<slug>*)
#   * prints nothing at all once both events are scored — no "disable me" step to remember
# Test any date without waiting:  AB_TODAY=2026-09-23 bash .claude/hooks/ab-reminder.sh
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0

WINDOW_START="2026-09-20"     # the evening event 1 is meant to run
HARD_STOP="2026-09-26"        # YED-172 due date; after this the hook is silent whatever the state
RUN_CARD=".claude/artifacts/ab-yed172/run-card-2026-09-21.md"
TODAY="${AB_TODAY:-$(date +%F)}"

# events: slug | seed | what it is | run-by
# Repointed 2026-09-24 to the events that ACTUALLY ran. The original two (show-and-tell, clay) were both
# replaced mid-experiment: AI Show and Tell was run then dropped (Alex didn't attend, so he couldn't score
# criterion 1), and the Clay livestream was abandoned when Notion MCP dropped and left the legacy arm without
# its data source. Because the silencing check matches on slug, leaving the old slugs here meant the hook
# could never see the real scorecards and would have kept firing to the 09-26 hard stop with the A/B closed.
EVENTS=(
  "apollo-graphos|.claude/artifacts/ab-yed172/seed-2026-09-24-apollo.json|Thu 9/24 · Is My Graph Healthy? (Apollo GraphQL, 11am webinar)|SCORED 2026-09-24"
  "ai-builders|.claude/artifacts/ab-yed172/seed-2026-09-24-aibuilders.json|Thu 9/24 · AI Builders Session (3percentclub, Brooklyn, 6pm)|SCORED 2026-09-24"
)

[ -r "$RUN_CARD" ] || exit 0                                   # the A/B was removed/finished — nothing to say
[[ "$TODAY" < "$WINDOW_START" || "$TODAY" > "$HARD_STOP" ]] && exit 0

pending=()
for e in "${EVENTS[@]}"; do
  IFS='|' read -r slug seed what when <<< "$e"
  # scored? any eval log naming this A/B and this event
  if compgen -G ".claude/evals/logs/*ab-yed172*${slug}*" >/dev/null 2>&1; then continue; fi
  pending+=("$what — $when")
done
[ ${#pending[@]} -eq 0 ] && exit 0                             # both scored: silent, permanently

echo "## ⏱ A/B IS LIVE (YED-172) — $( [ ${#pending[@]} -eq 2 ] && echo "both events pending" || echo "1 event pending" ), due 2026-09-26"
echo
for p in "${pending[@]}"; do echo "- $p"; done
echo
echo "**This decides whether the substrate replaces the legacy Step 1.7a pull, and whether ADR-10 goes to Accepted.**"
echo "Everything is pre-staged — Alex's only job is ~10 minutes of BLIND scoring."
echo
echo "Run card (roster, seeds, pre-registered scoring sheet, decision rule): \`$RUN_CARD\`"
echo "Method: conditioner runs TWICE (legacy-only → Pack A, substrate-only → Pack B) · coin-flip X/Y · strip arm tells ·"
echo "score with Alex + a Sonnet seat (NOT the Gemini seat, advisory per YED-206) · reveal key · log both scorecards to"
echo "\`.claude/evals/logs/<date>-ab-yed172-<slug>.jsonl\` — that log is what silences this reminder."
echo
# The freeze is declared ONCE, in graph-freeze.json, and ENFORCED by substrate.py (exit 4).
# This block only echoes it — never restate the rule here, or the copy drifts from the enforcement.
FREEZE_FILE=".claude/references/graph-freeze.json"
if command -v jq >/dev/null 2>&1 && [ -f "$FREEZE_FILE" ] && jq -e '.active == true' "$FREEZE_FILE" >/dev/null 2>&1; then
  echo "⛔ Graph-write freeze ACTIVE ($(jq -r '.issue // "?"' "$FREEZE_FILE")) — enforced, not advisory: substrate.py"
  echo "   refuses ensure-*/stage-claims/backfill/approve-claims with exit 4. Reads and --dry-run are unaffected."
  echo "   Lifts when: $(jq -r '.lifts_when // "see the file"' "$FREEZE_FILE")"
  echo "   Definition + override procedure: \`$FREEZE_FILE\`"
else
  echo "✅ No graph-write freeze active — substrate writes are open (YED-205 / YED-47 unblocked)."
fi
echo "Score each event before looking at the other."
