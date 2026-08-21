#!/usr/bin/env bash
# check-refs.sh — deterministic dangling-reference check for the build-quality judge.
# Extracts load-bearing repo-relative file references from a build artifact and reports which do NOT exist.
# Mechanizes the build-quality@4 dangling-reference cap (models under-apply it — bf17). CONSERVATIVE by design:
# only flags clearly path-shaped `.claude/…` (and `~/.claude/…`) tokens, and SKIPS any reference whose surrounding
# non-whitespace run contains a glob (`*`), an angle-bracket `<placeholder>`, an ellipsis (`...`/`…`), or a URL
# (`://`) — so a false "dangling" never wrongly caps a good artifact. It errs toward under-flagging (safe): if a
# run is ambiguous it is skipped, never guessed.
# Spec: .claude/references/cross-provider-judge.md.
#
# Usage: check-refs.sh --artifact <path>
#   stdout: one missing referenced path per line (empty = none missing)
#   stderr: a one-line summary ("N referenced path(s) missing of M checked")
#   exit:   0 always (advisory; the caller enforces the cap)
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || true

ARTIFACT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --artifact) ARTIFACT="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -n "$ARTIFACT" ] && [ -r "$ARTIFACT" ] || { echo "ERROR: --artifact missing/unreadable: $ARTIFACT" >&2; exit 2; }

# Pass 1: grab the WHOLE non-whitespace run around each `.claude/` (so the skip-filters can SEE special chars that
# a narrow path-charset would truncate away — the reachability fix). Drop any run that is a URL/glob/placeholder/
# ellipsis. From each surviving (clean) run, re-extract the concrete path(s) with the strict path charset — grep -oE
# emits ALL matches in the run, so `a,b` with no space still yields both. Strip trailing markup; dedupe.
CANDIDATES=$(grep -oE '[^[:space:]]*\.claude/[^[:space:]]*' "$ARTIFACT" 2>/dev/null \
  | while IFS= read -r run; do
      case "$run" in
        *'://'*|http*)              continue;;  # path embedded in a URL
        *'*'*|*'<'*|*'>'*)          continue;;  # glob or <placeholder>
        *'…'*|*'...'*)              continue;;  # ellipsis-elided illustrative path
      esac
      printf '%s' "$run" | grep -oE '(~/|\./)?\.claude/[A-Za-z0-9._@/-]+'
    done \
  | sed -E 's/[.,;:)`"'"'"']+$//' \
  | sort -u)

missing=0; checked=0
while IFS= read -r ref; do
  [ -n "$ref" ] || continue
  probe="$ref"; case "$probe" in "~/"*) probe="${HOME}/${probe#\~/}";; esac
  checked=$((checked+1))
  if [ ! -e "$probe" ]; then
    echo "$ref"
    missing=$((missing+1))
  fi
done <<< "$CANDIDATES"

echo "check-refs: ${missing} referenced path(s) missing of ${checked} checked in ${ARTIFACT}" >&2
exit 0
