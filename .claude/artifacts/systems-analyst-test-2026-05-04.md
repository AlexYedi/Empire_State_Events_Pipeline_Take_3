# Systems Analyst Agent — First Test Run

**Date:** 2026-05-04
**Scenario:** Empire State Events Pipeline — content publishing plateau hypothesis
**Agent:** `.claude/agents/ops/systems-analyst.md` (first invocation; via general-purpose proxy due to mid-conversation registration limitation per WORKFLOWS.md)
**Status:** Test passed; agent works as designed.
**Follow-up:** real-data validation run on the same day at [systems-analyst-real-data-2026-05-04.md](systems-analyst-real-data-2026-05-04.md) — the hypothetical findings here held up empirically against the actual Notion Content Drafts data, with confidence levels nudged upward.

---

## Headline finding

The prior hypothesis (Tragedy of the Commons) was **wrong**. Correct archetype match:
- **Shifting the Burden to the Intervenor (~80% confidence)** — the skills made research effortless, but Alex's *publishing decision-making muscle* is being atrophied by the volume of unshipped drafts. The intervention (skills) is replacing native capacity, not enhancing it.
- **Seeking the Wrong Goal (~75% confidence)** — the pipeline measures and rewards "briefs created" (visible, satisfying, easy to count). It does not equally reward "posts shipped." System optimizes the wrong target perfectly.

This matters because the **escapes are different**:
- Commons → privatize / regulate access to the shared resource
- Shifting the Burden → restore the system's native capacity *before* removing the intervention

Pursuing the Commons fix (e.g., "cap event intake") would only treat the symptom. The actual fix is to **redefine the success goal** (leverage point #3) and **surface the publish-rate gap weekly** (leverage point #6).

## Recommended intervention

**Highest leverage:** redefine the pipeline's success metric from "researched events" to "published posts per week" (with a quality counter-metric), and surface the publish-rate-vs-draft-rate gap weekly in Notion.

**What would tell us this analysis was wrong:**
- Publish rate stays flat after the goal change *and* drafts queue keeps growing → the bottleneck is somewhere else (e.g., LinkedIn motivation, audience response, day-job competition). Re-bound the system wider.
- Publish rate jumps but quality counter-metric crashes → Goodhart's Law strikes. Redesign the metric.
- Alex reports the goal change feels fine and the queue still grows → not Shifting-the-Burden; probably pure capacity mismatch (use leverage point #5: a hard rule like "every event ships exactly one post by Friday or the event is closed unpublished").

## Gaps in the canonical references the test surfaced

These are now applied in the next iteration of the references:

1. **Single-actor systems with multiple sub-roles** — `meadows-thinking-in-systems.md` doesn't address bounded rationality across roles within one person (Alex-as-researcher vs. Alex-as-reviewer). Worth a short addition.
2. **Perverse balancing loops** — the "decay-as-relief" loop (drafts that age out without being published act as an outflow that *looks* like delivery). Distinct enough from Drift to Low Performance to deserve its own callout.
3. **Diagnostic-questions Phase 4** — should explicitly prompt "what archetypes did you consider and reject, and why?" Adding this as a standing question makes the rule-out discipline less optional.
4. **H1/H2/H3 in agent output** — the agent definition references the horizon framework but the output template doesn't slot it. Either add horizons to the output schema or drop the framework reference.
5. **Tool budget** — agent has Bash/WebSearch/WebFetch/Grep/Glob; this analysis only used Read+Bash-for-ls. Consider tightening to Read-only for tighter role boundary.

## Agent-design verdict

**Worked as designed.** The eight-phase scaffold forced the analysis off the prior hypothesis (Commons) onto a better-fit archetype (Shifting the Burden + Wrong Goal) with cited evidence. The required `Considered and ruled out` field in §4 is what made the Commons rejection rigorous — without it, the agent would likely have politely affirmed the prior hypothesis. **Strong design choice.** The "Counterintuitive direction warning" slot earned its keep — surfaced the trap of "build a publishing automation skill" as deepening the Shifting-the-Burden pattern.

**Ship as-is. Treat the gaps above as the next iteration's reference-file additions.**
