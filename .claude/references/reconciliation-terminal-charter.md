<!-- Committed 2026-09-12 from the durable memory copy (reference_reconciliation_terminal_charter_2026-09-12). This file is canonical from here on; the memory entry is the pointer. -->

# Reconciliation Terminal — Charter

**Purpose:** one session owns converging all branches/worktrees to a single source of truth (`main`). Everything below exists because *concurrent sessions on shared checkouts* caused every failure on 2026-09-12 (branches moving mid-operation, another session grabbing the main checkout, a `git stash` swallowing a live session's WIP).

## Rule 0 — The precondition (without this, the charter does nothing)
All other Claude Code / terminal sessions on this repo and its worktrees must be QUIESCED before the reconciliation terminal acts. Quiesced = each other session has committed + pushed its branch and is idle. A single reconciliation terminal running alongside live writers hits the same moving-target problem. If another session is live, the reconciliation terminal goes read-only and reports only. Verify:
`git worktree list` · `git -C <wt> status --short` (only build-sessions.jsonl churn = at rest) · `git rev-parse --abbrev-ref HEAD` (main checkout must be on `main`, not a feature branch) · re-check a branch tip twice — if it moved, a session is live.

## Rule 1 — This terminal MERGES and SYNCS; it does not BUILD
Allowed: `gh pr merge` (server-side), `fetch`, `pull --ff-only`, ref-only `git branch -f <non-checked-out> origin/main` (FF only), `worktree remove`/`branch -d` of merged branches, `gh pr create` for a branch at a stop point.
Forbidden: editing build-surface (skills/agents/commands/schemas), `rebase`/`merge`/`stash` inside a worktree another session may own, `--force`/`reset --hard`/history rewrite, `git add -A` (targeted adds only).

## Rule 2 — Inspect actual state before every action
`git fetch origin --prune` → `git rev-parse --short main origin/main <branch>` → `git merge-base <branch> origin/main` → `gh pr view <n> --json ...`. `mergeable: UNKNOWN` = wait, don't act.

## Rule 3 — Back up before anything irreversible
All branch work on origin before a merge (`rev-list --left-right --count origin/<b>...<b>` right side 0). Backup ref before a bury: `git branch -f backup/<name>-preOp <tip>`.

## Rule 4 — The convergence pattern that works (per branch)
1. Confirm a real stop point (complete, or remaining work inert-by-design — e.g. staging-only writes with no consumer). Mid-feature + not inert → hold.
2. Bury dead work: Clarify is REJECTED — no `clarify-*.md` and no `ADR-6-crm-boundary-clarify.md` reach main ([[project_crm_capture_decision_2026-09-09]]). Merging current main in usually buries it automatically; verify `git ls-files 'clarify*' '**/clarify*'` empty on tip.
3. `gh pr create` (if none) → wait `MERGEABLE/CLEAN` → `gh pr merge <n> --merge --delete-branch`.
4. Sync main: discard telemetry churn, `git pull --ff-only origin main`.
5. Remove converged worktree (`worktree remove --force`) + delete local branch (`--force` safe when only build-sessions.jsonl / .venv dirt).
6. Continuation branches cut from true `origin/main`, never stale local main.

## Rule 5 — Environment gotchas
git network is blocked by the default Bash sandbox (`curl` works, `git fetch/push` times out ~75s) → run network git with the sandbox disabled; `timeout` absent on macOS (bound probes with `curl --max-time`). `build-sessions.jsonl` churn is auto (Stop hook) — `git checkout --` it, never chase it. Worktrees lack `.env` ([[project_worktree_env_missing_2026-09-08]]). Media stays out of git (audio→R2 esep-library, images/transcripts→Drive; only final PDFs/markdown tracked).

## Rule 6 — Attribution
End commit messages + PR descriptions with the session's required Co-Authored-By / generated-with lines.
