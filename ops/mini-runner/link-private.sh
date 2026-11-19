#!/bin/zsh
# YED-411 step 2, run ONCE per interactive checkout (over `ssh esep-mini` is fine; launchd cannot write ~/Documents).
# Points the checkout's private paths at ~/Developer/esep-private, which the hourly `sync` job keeps current.
# FILES are HARD links: Claude Code copies regular files into new worktrees (.worktreeinclude) but skips symlinks, so a
# symlinked me-model reached no session (found 11/18). The hourly sync writes --inplace, so the shared inode stays live.
# DIRECTORIES (reviews) stay symlinks: they can't be hard-linked, and worktrees never copied them anyway.
# Refuses any path git tracks or does not ignore. Anything a link replaces is moved to ~/private-backups/<ts>/,
# outside every repo, never deleted. Re-running is safe: existing correct links are left alone.
set -u
REPO="${1:-$HOME/Documents/GitHub/Empire_State_Events_Pipeline_Take_3}"
PRIVATE="${ESEP_PRIVATE:-$HOME/Developer/esep-private}"
BACKUP="$HOME/private-backups/$(date +%Y%m%dT%H%M%S)"
PATHS=(.claude/references/me-model.md .claude/references/target-companies.md
       .claude/references/inbox-denylist.md .claude/references/inbox-allowlist.md .claude/.state/reviews)
[[ -d "$PRIVATE" ]] || { echo "FAIL: $PRIVATE missing; run the sync job first"; exit 2; }
rc=0
for p in $PATHS; do
  if ! git -C "$REPO" check-ignore -q "$p" || git -C "$REPO" ls-files --error-unmatch "$p" >/dev/null 2>&1; then
    echo "REFUSED: $p (tracked or not gitignored)"; rc=9; continue
  fi
  [[ -e "$PRIVATE/$p" ]] || { echo "SKIP: $p not in $PRIVATE yet"; continue; }
  dst="$REPO/$p"; src="$PRIVATE/$p"
  if [[ -d "$src" ]]; then
    if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then echo "ok (dir symlink): $p"; continue; fi
  else
    if [[ -f "$dst" && ! -L "$dst" && "$(stat -f %i "$dst")" == "$(stat -f %i "$src")" ]]; then echo "ok (hard link): $p"; continue; fi
  fi
  if [[ -e "$dst" || -L "$dst" ]]; then
    mkdir -p "$BACKUP/${p:h}"
    if [[ -L "$dst" ]]; then rm "$dst"; echo "removed old symlink: $p"; else mv "$dst" "$BACKUP/$p"; echo "moved old copy to $BACKUP/$p"; fi
  fi
  mkdir -p "${dst:h}"
  if [[ -d "$src" ]]; then ln -s "$src" "$dst"; echo "linked (dir symlink): $p"; else ln "$src" "$dst"; echo "linked (hard link): $p"; fi
done
[[ -n "$(git -C "$REPO" status --porcelain -- .claude/references .claude/.state 2>/dev/null)" ]] && { echo "FAIL: git now sees changes under .claude/references or .claude/.state"; rc=9; }
exit $rc
