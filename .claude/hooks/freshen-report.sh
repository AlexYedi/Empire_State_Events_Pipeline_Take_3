#!/bin/zsh
# SessionStart hook (YED-448, approved 2026-11-25): on esep-mini only, print one FRESHEN-AUTO line so a session that
# skips /freshen still knows how stale it is. REPORT-ONLY: it copies no private file, runs no sync, and changes no
# tracked file. Its only side effect is `git fetch` (remote-tracking refs). It never blocks: every step is capped,
# every failure is swallowed, and it always exits 0 (CLAUDE.md §5: no wired hook may block a turn).
# For the full refresh (sync now + copy private files into a worktree) run /freshen.
setopt nullglob
[[ "$(hostname -s)" == esep-mini ]] || exit 0
# Runner jobs (ops/mini-runner/run-job.sh) pull main themselves and export this; skip them.
[[ "${ENABLE_CLAUDEAI_MCP_SERVERS:-}" == false ]] && exit 0
src="$(cat 2>/dev/null | /usr/bin/python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("source",""))
except Exception: print("")' 2>/dev/null)"
[[ "$src" == startup || "$src" == resume || -z "$src" ]] || exit 0

TOP="$(git -C "${CLAUDE_PROJECT_DIR:-$PWD}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
note=()
# 8-second cap on the fetch; perl's alarm stands in for `timeout`, which macOS lacks.
GIT_TERMINAL_PROMPT=0 /usr/bin/perl -e 'alarm shift; exec @ARGV' 8 git -C "$TOP" fetch -q origin 2>/dev/null \
  || note+=("fetch failed or timed out")
behind="$(git -C "$TOP" rev-list --count HEAD..origin/main 2>/dev/null || echo '?')"
synced="$(cat $HOME/Developer/esep-private/.synced-at 2>/dev/null || echo never)"
mm="present"; [[ -f "$TOP/.claude/references/me-model.md" ]] || { mm="MISSING"; note+=("me-model missing here: run /freshen"); }
par="n/a"
if [[ -f "$HOME/Developer/esep-private/parity.json" ]]; then
  par="$(/usr/bin/python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); f=[x["check"] for x in r["results"] if x["status"]=="FAIL"]; print(("OK" if not f else "FAIL "+",".join(f))+" as of "+r["checked_at"][5:16].replace("T"," ")+"Z")' "$HOME/Developer/esep-private/parity.json" 2>/dev/null || echo unreadable)"
fi
[[ "$behind" == <-> && "$behind" -gt 0 ]] && note+=("pull --ff-only if the task needs current main")
echo "FRESHEN-AUTO (report only): $(git -C "$TOP" branch --show-current) is $behind behind origin/main · private inputs synced $synced · me-model $mm · parity $par${note:+ · ${(j: · :)note}}. Run /freshen for a sync now."
exit 0
