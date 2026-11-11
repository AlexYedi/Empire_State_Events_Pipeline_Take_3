# esep-mini: the always-on scheduled runner

Decision YED-385 · build YED-347 / YED-334 · first consumer YED-384 (graph phase 1).
Read on demand when a scheduled job misbehaves, the mini restarts, or a new nightly job is added.

## Design (and why not routines)

Scheduled jobs run from **launchd on the mini**, through `ops/mini-runner/run-job.sh <job>`, in the **real checkout**.
Claude Code routines on a bridge environment were tried first and rejected on 2026-11-11: a bridge environment's id is
minted per `claude remote-control` process, so every restart (reboot, crash, KeepAlive respawn, auto-update) gives a new id,
and every routine is pinned to an id. Measured: two consecutive LaunchAgent starts gave `env_017oHa…` then `env_0144mE…`, and
stopping a Terminal instance deleted `env_01LkCP…`. The earlier "laptop" environment `Mac:…:fc0e` was in fact this mini (a tmux
loop started 2026-11-06, before the rename), and its id survived only because that process never restarted.

| Piece | Value |
|---|---|
| Machine | Mac mini (Mac18,5), hostname `esep-mini`, macOS 27, FileVault **on** |
| Real checkout | `~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3`, always on `main`. `run-job.sh` refuses to run on any other branch and fast-forwards `main` before each job, so launchd only runs merged code |
| Job runner | `ops/mini-runner/run-job.sh` (jobs: `reconcile`, `smoke`); one log per run in `~/Library/Logs/esep-runner/<job>-<UTC>.log` |
| Remote access | LaunchAgent `com.esep.remote-control` keeps one `claude remote-control --spawn worktree` up, for phone/web access only. Not part of the scheduler; its environment id changes on restart, so never pin a routine to it |
| Power | `pmset`: `sleep 0`, `disksleep 0`, `autorestart 1` (boots itself after a power cut, then waits at the FileVault screen) |
| Python | uv-managed CPython 3.12 (`.venv`, no packages: the runner's scripts are stdlib-only). System python is 3.9: never use it |

Jobs:
- **Deterministic jobs run as plain Python, with no LLM** (the reconcile is one fixed command; wrapping it in `claude -p` buys nothing and costs tokens).
- **Judgment jobs** (theme sweeps, Monday brief) use `claude -p` with `--permission-mode dontAsk` (anything not allow-listed is denied, never prompted),
  a narrow `--allowedTools` list, `--strict-mcp-config` and `ENABLE_CLAUDEAI_MCP_SERVERS=false` (no MCP / connectors), and `--no-session-persistence`.
  The `smoke` job is the template.

Database reads go through `spine_client.py` only (invariant 1). REST paths need a leading slash: `req('GET', '/lane_registry?...')`.

## Jobs

| Job | LaunchAgent | Schedule | State |
|---|---|---|---|
| `smoke` | `com.esep.runner-smoke` | none (fire with `launchctl kickstart gui/$(id -u)/com.esep.runner-smoke`) | ALL PASS run directly 2026-11-11 18:03Z; launchd proof pending install |
| `reconcile` | `com.esep.nightly-reconcile` | 05:00 local (ET) daily | not installed until Alex approves the report |

`StartCalendarInterval` uses local time, so 05:00 ET holds across DST. If the mini was off at 05:00, launchd runs the job once
when it wakes (missed runs coalesce into one).

Known data-locality gap (YED-395): the mini has no `.claude/.state/{research,briefs,post-event}` and no `event-transcripts/`
(they live on the laptop), so its reconcile report over-counts `attended_no_local_source` and under-counts `*_not_staged`.

## Install (Alex runs these in Terminal.app; Claude may not install login items)

Merge the PR first: the plists point at `run-job.sh` in the real checkout.

1. `cd ~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3 && git pull --ff-only`
2. Smoke: `cp ops/mini-runner/com.esep.runner-smoke.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.runner-smoke.plist && launchctl kickstart gui/$(id -u)/com.esep.runner-smoke`
   then `tail -5 "$(ls -t ~/Library/Logs/esep-runner/smoke-*.log | head -1)"` shows `SMOKE: ALL PASS`.
3. Nightly reconcile (only after approving a report): `cp ops/mini-runner/com.esep.nightly-reconcile.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.nightly-reconcile.plist`
4. Remote access (already installed): `cp ops/mini-runner/com.esep.remote-control.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.remote-control.plist`
5. Check any of them: `launchctl print gui/$(id -u)/<label> | grep -E 'state|last exit code'`. Remove: `launchctl bootout gui/$(id -u)/<label>`.

LaunchAgents start only once the user is logged in. That is why the restart procedure below matters.

## Restart procedure (FileVault)

**Planned restart (updates, maintenance): always**
```
sudo fdesetup authrestart
```
in a real Terminal (the `!` prefix has no TTY for sudo). It unlocks FileVault for the next boot only, so the mini comes back
logged in and every LaunchAgent starts. `fdesetup supportsauthrestart` returns `true` on this machine. **Never** use a plain
Restart from the Apple menu or `sudo shutdown -r`: the mini will sit at the FileVault unlock screen and every job silently
stops until someone types the password.

**Unplanned (power cut, crash):** `autorestart 1` boots the mini, but it stops at the FileVault pre-boot screen. Nothing runs
until it is unlocked.
- Remote unlock: Remote Login (SSH) is on. Recent macOS (26+) can accept an SSH login at the FileVault pre-boot screen and
  unlock the disk from it. **Unverified on this mini**: test it once with a planned plain restart while on the same LAN
  (`ssh sameoldexpressions@esep-mini.local`, enter the login password, then wait for the full boot). Tailscale and other
  user-space VPNs are not up before unlock, so this works from the LAN only, not over the `100.x` address.
- If that does not work: unlock in person (keyboard or a monitor at the mini), or via Screen Sharing only once the OS has booted past FileVault.
- After any restart: `launchctl print gui/$(id -u)/com.esep.nightly-reconcile | grep -E 'state|last exit code'` and the newest log in `~/Library/Logs/esep-runner/`.

## Adding a job

Add a `case` to `run-job.sh` and a plist modelled on `com.esep.nightly-reconcile.plist`, in a PR. Prove it with a direct
`run-job.sh <job>` run, then a launchd kickstart, show Alex the output, and install the schedule only on his yes. No job
writes to the spine until its lane passes `spine_client.py --check-writers` and Alex approves the write path.
