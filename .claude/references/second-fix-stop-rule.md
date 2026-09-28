# Second-fix stop rule (added 2026-09-27)

**Problem it answers.** Builds were spiralling: a build ships → the judge or a live run finds a defect →
a patch → a new finding → another patch and another Linear issue. Evidence (last 40 sessions): YED-227
went to judge round 5; YED-236 went build → judge fixes → privacy guard → quorum disagree → rubric cap.
Each round was locally reasonable; the stack of them is the bloat. Meadows archetype: **Fixes that Fail**
(each fix's side-effect is the next problem). Rejected: *Shifting the Burden* — the fixes weren't
substituting for a known fundamental solution; nobody had asked whether one existed.

A second cause: design work was dispatched to `general-purpose` agents (123 unique dispatches across the last 40 sessions — the most-used type,
incl. "Fable: design ADR-8", "Fable: Postgres health review") — which execute the framing they're handed.
`alex:cto-principal-architect` exists to challenge the framing and was used 5 times.

## The rule

**Trigger — any one of:**
1. You're about to make the **second fix to the same component** (file, script, skill, hook, or the
   same Linear issue family) within one workstream. The first fix is normal iteration; the second is a signal.
2. You're about to dispatch **judge round 3+** on the same build.
3. You're about to **open a new Linear issue whose purpose is to fix or follow up something built in
   the last 7 days**.

**Action — before writing the next patch:**
1. Stop patching.
2. Dispatch `alex:cto-principal-architect` (model override `fable` is fine) with the component, the
   fix history (one line each), and exactly one question:
   > *Is this a design problem rather than a bug — and what should we **remove** instead of add?*
3. Act on the answer. "Remove X" and "revert to Y" are first-class outcomes; "patch #3" is allowed only if
   the architect says the design is sound and names why.
4. **No new Linear issue** for the fix until the answer is in. If one is opened, it cites the answer.

**Exempt:** typos, one-line config, and fixes to *content* (posts, briefs) — this rule is for system parts.

## Agent routing default (the second half)

| Work | Dispatch |
|---|---|
| Design, architecture, "should this exist", fix-on-fix review | `alex:cto-principal-architect` |
| Systems diagnosis ("why does this keep happening") | `alex:systems-analyst` |
| Parallel fan-out of a skill, mechanical writes, judge seats | `general-purpose` (fine — a container, not a thinker) |

Using `general-purpose` for design work is the smell, not `general-purpose` itself.

## Enforcement (honest about its strength)

- **Prose only.** The optional nudge hook was removed 2026-09-28; restore from git history if YED-237's trigger fires.
- **Recount (by hand, when asked):** look for any component fixed ≥3 times in a week with no architect
  review in between (`git log` per path). That's the evidence of whether this rule works. If it doesn't change behaviour within
  ~3 weeks, that is YED-237's trigger — don't add more prose.
