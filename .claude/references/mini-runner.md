# esep-mini: the always-on scheduled runner

Decision YED-385 · build YED-347 / YED-334 · first consumer YED-384 (graph phase 1).
Read on demand when a scheduled routine misbehaves, the mini restarts, or a new nightly job is added.

## What runs where

| Piece | Value |
|---|---|
| Machine | Mac mini (Mac18,5), hostname `esep-mini`, macOS 27, FileVault **on** |
| Real checkout | `~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3`, always on `main` (Remote Control serves from it; never switch its branch) |
| Bridge environment | `env_01LkCPq468uT6wRAt5EE1B5q` (registered by `claude remote-control --spawn worktree` from the checkout) |
| Keep-alive | LaunchAgent `com.esep.remote-control` (`ops/mini-runner/com.esep.remote-control.plist`), logs in `~/Library/Logs/esep-runner/` |
| Power | `pmset`: `sleep 0`, `disksleep 0`, `autorestart 1` (boots itself after a power cut, then waits at the FileVault screen) |
| Python | uv-managed CPython 3.12 (`.venv`, no packages: the runner's scripts are stdlib-only). System python is 3.9: never use it |

A routine fires into a **fresh git worktree** at `<checkout>/.claude/worktrees/bridge-<session>` cut from `origin/main`.
`.env` is present there; `.venv` and every untracked or gitignored input (`.claude/.state/`, `event-transcripts/`) are **not**.
So every routine prompt must (1) bootstrap `uv venv --python 3.12 .venv` itself and (2) point any `--root` / output path at
the real checkout, never at the worktree, which is discarded.

The Remote Control process must be running when a routine fires. If it is down, the fire leaves no run in `list_runs`:
check the routine with `RemoteTrigger get` and the LaunchAgent state, not just the run list.

## Routines on this environment

| Routine | Id | Schedule | State |
|---|---|---|---|
| Smoke (read-only, one-time) | `trig_0196DksQ6YNptsFLR3BUyhMt` | ran 2026-11-11 17:24Z | ALL PASS (selftest 129/129, REST GET 200, WebSearch, hostname `esep-mini`) |
| Nightly reconcile `--report` | `trig_012BJeWGvSa8pfCHr6SnVVz3` | `0 10 * * *` (05:00 ET) | created **disabled**; enable only on Alex's yes |

All routines here: `clear_mcp_connections: true`, minimal `allowed_tools`, read-only prompts. Database reads go through
`spine_client.py` only (invariant 1). REST paths need a leading slash: `req('GET', '/lane_registry?...')`.

Known data-locality gap: the mini has no `.claude/.state/{research,briefs,post-event}` and no `event-transcripts/`
(they live on the laptop), so its reconcile report over-counts `attended_no_local_source` and under-counts `*_not_staged`
relative to the laptop.

## Install / reinstall the keep-alive (Alex runs this; it needs a real Terminal)

1. Stop any Remote Control running in a Terminal window (Ctrl-C), so only one server serves the checkout.
2. `mkdir -p ~/Library/Logs/esep-runner && cp ~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/ops/mini-runner/com.esep.remote-control.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.remote-control.plist`
3. Verify: `launchctl print gui/$(id -u)/com.esep.remote-control | grep -E 'state|pid'` shows `state = running`, and
   `tail ~/Library/Logs/esep-runner/remote-control.*.log` shows it connected.
4. Remove: `launchctl bootout gui/$(id -u)/com.esep.remote-control`.

A LaunchAgent starts only once the user is logged in. That is why the restart procedure below matters.

## Restart procedure (FileVault)

**Planned restart (updates, maintenance): always**
```
sudo fdesetup authrestart
```
in a real Terminal (the `!` prefix has no TTY for sudo). It unlocks FileVault for the next boot only, so the mini comes back
logged in, the LaunchAgent starts Remote Control, and routines keep firing. `fdesetup supportsauthrestart` returns `true` on this
machine. **Never** use a plain Restart from the Apple menu or `sudo shutdown -r`: the mini will sit at the FileVault unlock
screen and every routine silently stops firing until someone types the password.

**Unplanned (power cut, crash):** `autorestart 1` boots the mini, but it stops at the FileVault pre-boot screen. Nothing runs
until it is unlocked.
- Remote unlock: Remote Login (SSH) is on. Recent macOS (26+) can accept an SSH login at the FileVault pre-boot screen and
  unlock the disk from it. **Unverified on this mini**: test it once with a planned plain restart while on the same LAN
  (`ssh sameoldexpressions@esep-mini.local`, enter the login password, then wait for the full boot). Tailscale and other
  user-space VPNs are not up before unlock, so this works from the LAN only, not over the `100.x` address.
- If that does not work: unlock in person (keyboard or a monitor at the mini), or log in via Screen Sharing only once the
  OS has booted past FileVault.
- After any restart, check: `launchctl print gui/$(id -u)/com.esep.remote-control | grep state` and that routine runs
  resume (`RemoteTrigger list_runs` on the nightly routine).

## Adding a nightly job

Copy the reconcile routine's shape: one-time smoke first, then cron, created `enabled: false`, run once manually, show
Alex the output, enable on his yes. No writes from a routine until its lane passes the writer checks
(`spine_client.py --check-writers`) and Alex approves the write path.
