---
description: "Close a non-trivial build session against the Definition-of-Done gate — surface the ≤3+1 checklist, capture met/waived-with-reason per item, and record it to telemetry via .claude/.state/<session>.build_meta (folded into the build_session row by the Stop hook). Informs, never blocks."
argument-hint: "[optional: correction-rounds count, or notes]"
---

# /dod-close — Close a build against the DoD gate

Runs the **Definition of Done** ritual and writes the semantic telemetry fields that were missing —
this is the writer that closes the rigor loop. Methodology lives in CLAUDE.md `<definition_of_done>`.

## Trigger
At the end of a **non-trivial** build session (adds/changes a skill, agent, command, pipeline
component; alters a schema/data contract; came from an approved plan; or is hard to reverse). Alex
types `/dod-close`, or the agent runs it before closing such a session. Trivial builds (typo, one-line
fix, config tweak, doc edit, pure research) auto-waive the gate — skip it.

## Shape (single-thread, main conversation only)
1. **Surface the ≤3+1 checklist** from CLAUDE.md `<definition_of_done>`, per item **met** or
   **waived-with-one-line-reason** (waivers are data, not failures):
   1. Spec artifact before code (ChatPRD → Notion)
   2. Linear issue opened/updated
   3. One adversarial pass in writing (pre-mortem / `alex:cto-principal-architect` / `alex:risk-playbooks`)
   4. build-quality judge ran on this build, this session. A waiver must say *no gradable artifact* or
      name the Linear issue holding the make-up run; the writer rejects an item-4 waiver whose reason has neither (YED-201 Fix 1A)
2. **Ask for `correction_rounds`** — how many corrective back-and-forth rounds this build took (the
   friction signal; optional, integer).
3. **Call the writer once:**
   ```
   .claude/hooks/dod-close.sh --dod-met <true|false> --dod-waived <true|false> \
       --correction-rounds <N> [--reason "item: why" ...]
   ```
   It writes `.claude/.state/$CLAUDE_CODE_SESSION_ID.build_meta` (the Stop hook folds the three
   fields into the session's `build_session` row) and appends any waiver reason to
   `.claude/artifacts/dod-waivers.jsonl` (what `/rigor-review` reads for clustering).
4. **Capture the build-journal prose entry** — run the shared routine in
   **`.claude/references/journal-entry-prompt.md`**: draft today's ≤3-line what/why/value from the
   session's shipped facts, ask ≤3 sharpening forks, write `.claude/data/build-journal-prose.json`,
   regenerate the hub journal, and flag the (manual) hub deploy. This is what stops the prose sidecar
   lapsing silently: closing a non-trivial build *is* the moment its journal entry gets written, not a
   thing Alex has to remember later. Skip only if the build genuinely shipped nothing journal-worthy
   (say so). The standalone `/journal-entry` command runs the same routine for non-DoD break points.

## Guardrails
- **Informs, never blocks** (CLAUDE.md is explicit). Waive-with-reason is always the honest fast path.
- **Main conversation only** — the Stop hook fires for *this* session's id; a subagent has a
  different/child context. Do not run inside a subagent.
- **Content-gated** — booleans/ints + Alex's own short reason strings only; never artifact bodies.
- Contract is frozen: the writer emits exactly `{dod_met, dod_waived, correction_rounds}` —
  see `.claude/references/build-session-contract.md`.

## Ground truth
- Gate definition: CLAUDE.md `<definition_of_done>` · writer: `.claude/hooks/dod-close.sh`
- Telemetry contract: `.claude/references/build-session-contract.md` · emitter: `.claude/hooks/build-session-emit.sh`
- Downstream reader: `/rigor-review` + `.claude/references/value-action-registry.md`
