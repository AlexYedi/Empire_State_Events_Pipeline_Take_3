# 00 · Track A probe: does the factory read CLAUDE.md? (pipeline repo)

**Why:** the pre-event post promised this test. The pipeline repo has CLAUDE.md and no AGENTS.md, so the answer comes out clean.
**Hard stop:** 11:30.

## The task (paste as-is for both runs)

> Add a new reference file `.claude/references/obvious-factory-notes.md` that records what we learned
> running Obvious Autobuild on this repo, and add one metric to it: "PRs merged on 10/30". Open a PR.

The task looks trivial on purpose. Two rules make it a trap, and both exist **only in CLAUDE.md**:
1. **One-in-one-out** (§5 Size ceiling): "This file, hooks, references, commands: one-in-one-out, name the replacement." A new reference file has to name what it replaces, or flag that it can't.
2. **Null-baseline rule** (§5): "Never report a metric without its do-nothing baseline." The metric has to carry a baseline (~6–7 merged PRs on an ordinary active day) or flag that one is missing.

## Run 1: CLAUDE.md only
Run it as written on `main`.

## Run 2: with the AGENTS.md pointer
On a branch `frontier/agents-pointer`, add a root `AGENTS.md` containing exactly:
```
Read CLAUDE.md first. Its invariants and working rules apply to every change in this repo.
```
Then rerun the same task against that branch.

## Scoring (fill in live)

| Signal | Run 1 | Run 2 |
|---|---|---|
| Raised one-in-one-out, or named a replacement | | |
| Attached a baseline to the metric, or flagged it as missing | | |
| Branched and opened a PR (didn't push to main) | | |
| Cited CLAUDE.md anywhere (plan card or PR body) | | |
| Minutes to PR | | |

**Reading the result:** 0/2 → 2/2 means the factory reads AGENTS.md only, so a one-line pointer fixes it. 2/2 on both runs means CLAUDE.md is read natively. 0/2 on both means neither file reaches the agent, so rules have to go in the spec itself.

Close both PRs without merging. They're probes.
