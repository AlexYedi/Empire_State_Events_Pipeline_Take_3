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
| Runner checkout | `~/Developer/Empire_State_Events_Pipeline_Take_3`, always on `main`, used only by launchd jobs. `run-job.sh` refuses to run on any other branch and fast-forwards `main` before each job, so launchd only runs merged code. It has its own `.venv` and its own copy of `.env` (Alex copies it) |
| Why not `~/Documents` | macOS privacy protection (TCC) blocks launchd-started programs from `~/Documents`: the first launchd smoke failed with `zsh: can't open input file` (exit 127). `~/Developer` is not protected, so no binary needs Full Disk Access. Interactive sessions and Remote Control keep using `~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3` |
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
| `smoke` | `com.esep.runner-smoke` | none (fire with `launchctl kickstart gui/$(id -u)/com.esep.runner-smoke`) | ALL PASS under launchd 2026-11-11 19:26Z (runner checkout, `a0d47ed`) |
| `reconcile` | `com.esep.nightly-reconcile` | 05:00 local (ET) daily | installed 2026-11-11 on Alex's yes; first run 2026-11-12 05:00 ET (check: YED-399) |
| `sync` | `com.esep.sync-inputs` | hourly, and once at load | YED-395; see "Laptop input sync" below |

`StartCalendarInterval` uses local time, so 05:00 ET holds across DST. If the mini was off at 05:00, launchd runs the job once
when it wakes (missed runs coalesce into one).

## Laptop input sync (YED-395)

The local inventories reconcile reads (untracked `Event Content/` files, `event-transcripts/`,
`.claude/.state/{research,briefs,post-event}`) are produced on the laptop. The mini **pulls** a read-only mirror of them
every hour into `~/Developer/esep-inputs/`, which sits outside every git work tree, and `reconcile` reads that mirror
(`--root`), after one best-effort fresh pull.

- Transport: `rsync` over Tailscale to `alexs-macbook-pro-2`, using a dedicated key `~/.ssh/esep_sync` (no passphrase, used for nothing else).
- Laptop side: that key is pinned in `~/.ssh/authorized_keys` to `restrict,command="/opt/homebrew/bin/rrsync -ro <checkout>"`, so it can
  only **read** the repo checkout, with no shell, no port forwarding and no writes.
- Why pull, not push: the laptop sleeps (a failed hour just retries), and a laptop-side launchd push would hit the same TCC block
  on `~/Documents` that moved the mini's runner to `~/Developer`.
- `--delete` only ever touches the mirror. `*.PRIVATE.*` files are never copied; reconcile skips them by name anyway.
- The mirror holds private inputs. It never enters git (invariant 4), and the mini has FileVault on.

Laptop setup, once (Alex, **on the laptop**):
1. System Settings → General → Sharing → **Remote Login** on, then (i) → **Allow full disk access for remote users** on
   (needed because the checkout is under `~/Documents`).
2. `brew install rsync` (provides `rrsync`). Homebrew's `rrsync` hard-codes `RSYNC = '/usr/bin/rsync'` (Apple's openrsync, which
   rejects `--confine-root`), so make a patched copy:
   `mkdir -p ~/.local/bin && sed 's#^RSYNC = .*#RSYNC = "/opt/homebrew/bin/rsync"#' /opt/homebrew/bin/rrsync > ~/.local/bin/rrsync-esep && chmod 755 ~/.local/bin/rrsync-esep`
   (re-run after a `brew upgrade rsync` if you want the newer rrsync; the old copy keeps working).
3. Append the mini's public key with the restriction:
   `echo "restrict,command=\"$HOME/.local/bin/rrsync-esep -ro $HOME/Documents/GitHub/Empire_State_Events_Pipeline_Take_3\" <contents of esep_sync.pub>" >> ~/.ssh/authorized_keys`
To revoke: delete that line on the laptop.

## Install (Alex runs these in Terminal.app; Claude may not install login items)

Merge the PR first: the plists point at `run-job.sh` in the runner checkout.

1. `cd ~/Developer/Empire_State_Events_Pipeline_Take_3 && git pull --ff-only` (one-time setup: `git clone` there, `uv venv --python 3.12 .venv`, copy `.env` in)
2. Smoke: `launchctl bootout gui/$(id -u)/com.esep.runner-smoke 2>/dev/null; cp ops/mini-runner/com.esep.runner-smoke.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.runner-smoke.plist && launchctl kickstart gui/$(id -u)/com.esep.runner-smoke`
   then `tail -5 "$(ls -t ~/Library/Logs/esep-runner/smoke-*.log | head -1)"` shows `SMOKE: ALL PASS`.
3. Nightly reconcile (only after approving a report): `cp ops/mini-runner/com.esep.nightly-reconcile.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.nightly-reconcile.plist`
4. Input sync (after the laptop setup above): `cp ops/mini-runner/com.esep.sync-inputs.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.sync-inputs.plist`
5. Remote access (already installed): `cp ops/mini-runner/com.esep.remote-control.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.esep.remote-control.plist`
6. Check any of them: `launchctl print gui/$(id -u)/<label> | grep -E 'state|last exit code'`. Remove: `launchctl bootout gui/$(id -u)/<label>`.

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
