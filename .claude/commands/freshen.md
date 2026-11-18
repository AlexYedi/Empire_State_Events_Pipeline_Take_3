---
description: "Bring this session up to date before work starts: on esep-mini, run the laptop→mini sync now (private inputs + Claude memory) and copy the fresh private files into this worktree; anywhere, fetch origin and report drift. Run it first in any mini session (YED-411)."
---

# /freshen

Run this before anything else in a session, especially a Remote Control session on esep-mini.

1. Run `zsh ops/mini-runner/freshen.sh` with Bash (from the repo root of this checkout or worktree).
2. Report its last line, the one starting `FRESHEN:`, verbatim.
3. If that line contains `LAPTOP ASLEEP`, `REFUSED`, `MISSING`, `sync exit` or `fetch failed`, say so plainly before any other work and ask Alex whether to continue on the older copy.
4. If the branch is behind `origin/main`, say how many commits, and pull (`git pull --ff-only`) only if this session's task needs current main.

It changes no tracked file: it syncs gitignored private inputs and Claude memory, and copies the private files into this worktree after checking each one is gitignored and untracked. Background: `.claude/references/mini-runner.md`, "Claude memory" and "/freshen".
