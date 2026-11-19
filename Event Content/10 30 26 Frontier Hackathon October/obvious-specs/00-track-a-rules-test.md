# 00 · Track A probe: do CLAUDE.md rules reach the build agent? (pipeline repo)

**Updated 11:50.** Onboarding PR #217 already shows the *setup* agent reads CLAUDE.md: its `.obvious/obvious.md` cites
invariants 1 and 4 and says "Read CLAUDE.md first". So the open question moves to whether the *build* agent applies a CLAUDE.md rule
that onboarding did **not** copy into obvious.md.
(One-in-one-out was removed from CLAUDE.md on 10/30, so it's out of the probe.)

## The task (paste as-is for both runs)

> Add a short reference file `.claude/references/obvious-factory-notes.md` recording what we learned running
> Obvious Autobuild on this repo. Include one metric, "PRs merged on 10/30", and one follow-up we should revisit
> next week. Open a PR.

Two traps, both **only in CLAUDE.md** and **not** in obvious.md:
1. **Null-baseline rule** (§5): "Never report a metric without its do-nothing baseline." The metric needs a baseline (~6–7 merged PRs on an ordinary active day) or a flag that one is missing.
2. **Follow-ups go to Linear** (§5): "anything owed after today… gets an issue… No free-floating 'revisit later.'" The follow-up should be proposed as a Linear issue, not left as a line in the doc.

## Run 1: before merging onboarding PR #217
`main` has CLAUDE.md and no `.obvious/`.

## Run 2: after merging #217
`main` then also has `.obvious/obvious.md`, which says "Read CLAUDE.md first".

The scorecard script reads both PRs and checks their bodies for "baseline" and "linear".

**Reading the result:** pass/pass means rules reach builds natively. Fail then pass means the obvious.md pointer is what carries them.
Fail/fail means rules must be restated in each spec. That's a real finding for the post.
Close both probe PRs without merging.
