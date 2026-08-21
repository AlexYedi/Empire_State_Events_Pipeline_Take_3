#!/usr/bin/env bash
# density-check.sh — deterministic anti-padding signal for the build-quality judge (deep_read artifacts).
# Computes the word-to-cited-fact ratio of a rendered Deep Read (or a single Deep-Read section) and flags
# padding risk. Mechanizes the build-quality@4 density cap (deep_read only) — the number-side of an
# inherently judgment-laden check, mirroring check-refs.sh: this script supplies the ground-truth counts,
# the judge seat decides whether high ratio = padding (generic-explainer filler) vs. legitimate novice
# on-ramp prose (which is uncited BY DESIGN and must NOT be penalised just for being uncited).
#
# The metric: prose_words / citation_count.  "Citations" = consolidated endnote entries (`[n] source — url`
# lines). Novice on-ramp prose is intentionally uncited, so a section with FEW words needs few citations —
# the flag is for LONG prose that is THIN on grounded facts (the padding smell the spike's anti-padding gate
# exists to catch). Reference band from the Daytona spike: ~150–200 words/citation reads as healthy,
# citation-dense prose. Default flag threshold is deliberately loose (300) so legitimate on-ramp never
# false-flags as long as the artifact carries enough real citations overall.
# Spec: .claude/evals/rubrics/build-quality-v4.md · .claude/proposals/event-field-guide.md (anti-padding).
#
# Usage: density-check.sh --artifact <path> [--max-ratio <N>]
#   stdout: a per-section word table + a summary verdict line
#   stderr: one-line summary
#   exit:   0 always (advisory; the judge enforces the cap)
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true

ARTIFACT=""
MAX_RATIO=300          # words-per-citation above which we flag PADDING-RISK
UNCITED_LONGFORM=400   # prose words with ZERO citations above which we flag UNCITED-LONGFORM
while [ $# -gt 0 ]; do
  case "$1" in
    --artifact)  ARTIFACT="$2"; shift 2;;
    --max-ratio) MAX_RATIO="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -n "$ARTIFACT" ] && [ -r "$ARTIFACT" ] || { echo "ERROR: --artifact missing/unreadable: $ARTIFACT" >&2; exit 2; }

# A line is an ENDNOTE ENTRY if it starts (after optional whitespace) with `[<digits>]` — the consolidated
# `[n] source — url` list a stitched Deep Read ends with. These are the cited facts. They are NOT prose, so
# they're excluded from the prose word count.
CITATIONS=$(grep -cE '^[[:space:]]*\[[0-9]+\]' "$ARTIFACT" 2>/dev/null || echo 0)

# Prose words = every word on a line that is NOT an endnote entry and NOT a bare markdown header marker.
# Headers themselves carry a few words; we keep them (cheap, negligible) but drop the leading `#` tokens.
PROSE_WORDS=$(grep -vE '^[[:space:]]*\[[0-9]+\]' "$ARTIFACT" 2>/dev/null \
  | sed -E 's/^[[:space:]]*#+[[:space:]]*//' \
  | wc -w | tr -d ' ')

# Per-section word counts (split on `##`/`###` headers) so the judge can see if one section is bloated.
echo "density-check — $ARTIFACT"
echo "----------------------------------------"
awk '
  /^#{2,3}[[:space:]]/ {
    if (sec != "") printf "  %-42s %5d words\n", substr(sec,1,42), w
    sec=$0; sub(/^#+[[:space:]]*/,"",sec); w=0; next
  }
  /^[[:space:]]*\[[0-9]+\]/ { next }   # endnote entries are not prose
  { n=split($0,a," "); w+=n }
  END { if (sec != "") printf "  %-42s %5d words\n", substr(sec,1,42), w }
' "$ARTIFACT"
echo "----------------------------------------"

# Ratio + verdict.
VERDICT="OK"
if [ "$CITATIONS" -eq 0 ]; then
  RATIO="n/a"
  if [ "$PROSE_WORDS" -gt "$UNCITED_LONGFORM" ]; then VERDICT="UNCITED-LONGFORM"; fi
else
  RATIO=$(( PROSE_WORDS / CITATIONS ))
  if [ "$RATIO" -gt "$MAX_RATIO" ]; then VERDICT="PADDING-RISK"; fi
fi

echo "density-check: words=${PROSE_WORDS} citations=${CITATIONS} words_per_citation=${RATIO} threshold=${MAX_RATIO} verdict=${VERDICT}"
case "$VERDICT" in
  PADDING-RISK)     echo "  → LONG prose thin on grounded facts. Judge: is this generic-explainer padding, or under-citation of real facts? Either caps density." ;;
  UNCITED-LONGFORM) echo "  → ${PROSE_WORDS} words with zero endnotes. Legitimate only if it is pure common-knowledge on-ramp; otherwise it asserts facts without sources." ;;
  OK)               echo "  → Within the healthy citation-density band. No padding signal." ;;
esac

echo "density-check: ${VERDICT} (words=${PROSE_WORDS} citations=${CITATIONS} ratio=${RATIO}) in ${ARTIFACT}" >&2
exit 0
