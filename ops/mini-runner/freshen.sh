#!/bin/zsh
# /freshen (YED-411): bring THIS session up to date before work starts. Safe to run any time; changes no tracked file.
# On esep-mini: runs the sync job now (laptop -> mini private inputs + Claude memory, ~10 s), then copies the fresh
# private files into this worktree (Remote Control worktrees take a copy only when they are created). Anywhere: fetches
# origin and reports how far this checkout is from main. Ends with one summary line to paste back to Alex.
set -u
TOP="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "FRESHEN FAIL: not inside a git checkout"; exit 2; }
MAIN="$(git -C "$TOP" worktree list --porcelain | awk '/^worktree /{print $2; exit}')"
FILES=(.claude/references/me-model.md .claude/references/target-companies.md
       .claude/references/inbox-denylist.md .claude/references/inbox-allowlist.md)
note=()
if [[ "$(hostname -s)" == esep-mini ]]; then
  RUNNER="$HOME/Developer/Empire_State_Events_Pipeline_Take_3"
  RUNJOB_LOG="$HOME/Library/Logs/esep-runner/freshen-$(date -u +%Y%m%dT%H%M%SZ).log" zsh "$RUNNER/ops/mini-runner/run-job.sh" sync
  rc=$?
  log="$(ls -t $HOME/Library/Logs/esep-runner/freshen-*.log | head -1)"
  grep -E "^(sync|private sync|memory sync)|REFUSED|WARN|SKIP" "$log" | sed 's/^/  /'
  [[ $rc -eq 0 ]] || note+=("sync exit $rc: read $log")
  grep -q "laptop unreachable" "$log" && note+=("LAPTOP ASLEEP: using the copy from $(cat $HOME/Developer/esep-private/.synced-at 2>/dev/null)")
  synced="$(cat $HOME/Developer/esep-private/.synced-at 2>/dev/null || echo never)"
  mem="$(ls $HOME/.claude/projects/-Users-sameoldexpressions-Documents-GitHub-Empire-State-Events-Pipeline-Take-3/memory/*.md 2>/dev/null | wc -l | tr -d ' ')"
  inbox="$(find $HOME/Developer/esep-private/memory-inbox -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
else
  synced="n/a (not the mini)"; mem="$(ls $HOME/.claude/projects/*Empire-State-Events-Pipeline-Take-3/memory/*.md 2>/dev/null | wc -l | tr -d ' ')"
  # YED-447: the laptop owns the master memory, so it is where the mini's inbox gets promoted (/memory-inbox).
  inbox="$(ssh -o BatchMode=yes -o ConnectTimeout=5 esep-mini 'find ~/Developer/esep-private/memory-inbox -name "*.md" 2>/dev/null | wc -l' 2>/dev/null | tr -d ' ')"
  [[ -z "$inbox" ]] && inbox="unknown (mini unreachable)"
  [[ "$inbox" == <-> && "$inbox" -gt 0 ]] && note+=("MEMORY INBOX $inbox: run /memory-inbox")
fi
# Any host: a worktree has no private files of its own (git worktree add / Remote Control copy them once, or not at
# all). Copy the main checkout's current ones in, only where git ignores and does not track the path.
if [[ "$TOP" != "$MAIN" ]]; then
  for f in $FILES; do
    [[ -f "$MAIN/$f" ]] || continue
    if git -C "$TOP" check-ignore -q "$f" && ! git -C "$TOP" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
      mkdir -p "$TOP/${f:h}"; cp -p "$MAIN/$f" "$TOP/$f"
    else note+=("REFUSED $f (tracked or not ignored here)"); fi
  done
fi
git -C "$TOP" fetch -q origin 2>/dev/null || note+=("git fetch failed")
behind="$(git -C "$TOP" rev-list --count HEAD..origin/main 2>/dev/null || echo '?')"
mm="$(stat -f %Sm -t %m/%d "$TOP/.claude/references/me-model.md" 2>/dev/null || echo MISSING)"
[[ "$mm" == MISSING ]] && note+=("me-model MISSING in this checkout")
par="n/a"
if [[ -f "$HOME/Developer/esep-private/parity.json" ]]; then
  par="$(/usr/bin/python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); f=[x["check"] for x in r["results"] if x["status"]=="FAIL"]; print(("OK" if not f else "FAIL "+",".join(f))+" as of "+r["checked_at"][5:16].replace("T"," ")+"Z")' "$HOME/Developer/esep-private/parity.json" 2>/dev/null || echo unreadable)"
  [[ "$par" == FAIL* ]] && note+=("PARITY $par: run the parity job and read its log")
fi
echo "FRESHEN: host $(hostname -s) · synced $synced · me-model $mm · memory $mem notes · inbox $inbox · parity $par · $(git -C "$TOP" branch --show-current) is $behind behind origin/main${note:+ · ${(j: · :)note}}"
