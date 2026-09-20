#!/usr/bin/env bash
# check-refs.sh — deterministic dangling-reference check for the build-quality judge.
# Extracts load-bearing repo-relative file references from a build artifact and reports which do NOT exist.
# Mechanizes the build-quality@4 dangling-reference cap (models under-apply it — bf17). CONSERVATIVE by design:
# only flags clearly path-shaped `.claude/…` (and `~/.claude/…`) tokens, and SKIPS any reference whose surrounding
# non-whitespace run contains a glob (`*`), an angle-bracket `<placeholder>`, an ellipsis (`...`/`…`), a URL
# (`://`), or a template/regex delimiter immediately after the path (`{slug}`, `\d+`, `.(json|md)`) — so a false
# "dangling" never wrongly caps a good artifact. It errs toward under-flagging (safe): if a run is ambiguous it is
# skipped, never guessed.
# Spec: .claude/references/cross-provider-judge.md.
# The extraction rules here are shared VERBATIM with .claude/scripts/build_graph.py (ADR-8 D2) — change both.
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
      # Template / regex / alternation: the path charset stops at `{`, `\`, `(`, `|`, `[`, `$`, `%`,
      # leaving a truncated prefix that can never exist on disk (`evolution-log-{slug}.md`,
      # `ADR-\d+`, `keyterms.(json|md)`). Shared verbatim with build_graph.py per ADR-8 D2.
      #
      # PER-MATCH, not per-run (fixed 2026-09-12, judge defect D4). The first cut dropped the WHOLE
      # whitespace-run on a template hit, silently swallowing real references that shared the run:
      # a path followed immediately by `(`, or a real path comma-joined to a template. Two
      # genuinely broken references went invisible per fixture.
      #
      # The discriminator is whether the charset stopped MID-TOKEN. A template leaves a dangling
      # separator before the delimiter (`keyterms.`+`(`, `evolution-log-`+`{`, `skills/`+`{`,
      # `ADR-`+`\`); a complete path does not (`real.md`+`(`). So: capture the optional delimiter,
      # drop only matches ending SEPARATOR+DELIMITER, then strip any surviving delimiter as
      # trailing markup. Under-flagging stays the bias, now scoped to the offending token rather
      # than its neighbours.
      printf '%s' "$run" | grep -oE '(~/|\./)?\.claude/[A-Za-z0-9._@/-]+[{(|[\$%]?' \
        | grep -vE '[._/-][{(|[\$%]$' \
        | sed -E 's/[{(|[\$%]$//'
    done \
  | sed -E 's/[.,;:)`"'"'"']+$//' \
  | sort -u)

missing=0; checked=0; ignored=0
while IFS= read -r ref; do
  [ -n "$ref" ] || continue
  probe="$ref"; case "$probe" in "~/"*) probe="${HOME}/${probe#\~/}";; esac
  # A GITIGNORED path that is absent is an ENVIRONMENT fact, not a defect: private refs (me-model,
  # inbox-allowlist) and local state (.state/, settings.local.json) are missing in every worktree by
  # design. Counting them capped positive controls at 0.60 during the 2026-09-20 bake-off and would
  # cap any judge run made in a worktree. The reference still has to exist in the repo's ignore rules
  # to qualify — an outright typo is not ignored, so it still flags.
  # try the bare path AND with a trailing slash: .gitignore lists runtime DIRS as ".claude/.state/", and
  # `git check-ignore .claude/.state` (no slash) does not match that rule.
  if [ ! -e "$probe" ] && { git check-ignore -q "$ref" 2>/dev/null || git check-ignore -q "${ref%/}/" 2>/dev/null; }; then
    ignored=$((ignored+1))
    continue
  fi
  checked=$((checked+1))
  if [ ! -e "$probe" ]; then
    echo "$ref"
    missing=$((missing+1))
  fi
done <<< "$CANDIDATES"

echo "check-refs: ${missing} referenced path(s) missing of ${checked} checked in ${ARTIFACT}$([ "$ignored" -gt 0 ] && echo " (${ignored} gitignored path(s) skipped: absent by design, not a defect)")" >&2
exit 0
