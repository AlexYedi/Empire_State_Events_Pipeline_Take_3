# Factory merge tiers

How a pull request to `main` gets merged. The policy is `.github/factory-tiers.json`; the gate
is the `factory-gate` workflow, which runs the shared core from `AlexYedi/alex-factory`.

| Tier | What it covers | Who approves |
|---|---|---|
| T0 | Text in `docs/adr/*.md`, `docs/specs/*.md`, `docs/proposals/*.md`, `docs/bakeoff/**`, `docs/history.md` | Nobody: merges once checks pass |
| T1 | `.claude/scripts/**`, `.claude/skills/**`, `.claude/commands/**`, `.claude/references/*.md` | A model review, then the factory App |
| T2 | Everything else, and any guard, gate, PII, writer, spine, SQL or `.github` change | Alex |

Rules for agents opening PRs:

- Keep a PR to one tier when you can. A mixed PR takes the highest tier it touches.
- A new script or skill is T2 even inside a T1 folder. Land it first, then iterate at T1.
- A model BLOCK on a commit is sticky. Fix the code and push; don't ask for an override.
- If the gate says `blocklist_unconfigured`, `policy_invalid` or a token error, stop and report.
  These fail closed on purpose.
