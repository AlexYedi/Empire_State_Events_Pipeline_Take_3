# Execution-week frictions (append-only)

Window: 2026-05-15 → ~2026-06-05. Raw capture, no structure. End-of-window batch review against published count + 2026-05-14 falsification triggers.

---

- **2026-05-20** — Linear priorities (YED-29 SessionStart hook) not project-scoped — same Yedibalian-team-wide block renders in every repo, so it's not actionable at the project level. Spec for fix folded into YED-30 (per-repo `.claude/linear-project.json` + hook patch to filter by Linear Project ID). Defer until end-of-window. Also surfaced sub-issue: SessionStart `additionalContext` is invisible to user in terminal — only renders into Claude's context. If we eventually want it visible at terminal-start, hook needs to also `>&2` echo. Captured here, not actioned.
