# YED-30 Step 5 — Empire State CLAUDE.md backport

**Status:** Ready to execute — pick up in fresh session
**Authored:** 2026-05-20 (end of YED-30 Steps 1-4 shipping session)
**Decision needed:** approve refactor plan, then execute
**Reviewer:** Alex
**Linear:** [YED-30](https://linear.app/yedibalian/issue/YED-30/layer-c-canonical-claudemd-fragment-new-project-starter-kit-build) (In Progress)

---

## Why this proposal exists

YED-30 (Layer C — Workspace Inheritance) is 4 of 5 steps complete as of 2026-05-20. The remaining Step 5 is the highest-stakes change in the whole three-layer arc: refactoring Empire State's 35KB CLAUDE.md to import the canonical fragment instead of duplicating its content.

It's deferred to a fresh session because:
1. **Context hygiene.** The shipping session accumulated 5+ Linear issues of context (YED-31, YED-36, YED-30 Steps 1-4). Step 5 only needs the canonical fragment + this CLAUDE.md — a fresh session reasons cleanly.
2. **Live inheritance test.** A fresh session in Empire State should *already* show Layer A (alex plugin) and Layer B (universal hooks) firing without any changes to this repo. Proving that before refactoring confirms the system works end-to-end.
3. **Highest-stakes touch.** Empire State's CLAUDE.md is the standing instruction the live events pipeline depends on. Easier to reason carefully when the only thing in context is the work.

## Prerequisites (already shipped)

- ✅ Canonical fragment at `~/Documents/GitHub/alex-agents-skills/Me/canonical-claude-md.md` (256 plugin skills, all 6 invariant blocks)
- ✅ Starter kit applied + validated in `gtm-os` (4-point health check all green, 2026-05-20)
- ✅ Starter kit applied + validated in `job-hunt-system` (4-point health check all green, 2026-05-20)
- ✅ Linear workspace toggle "Auto-close issues with merged linked PR" → OFF (no more partial-progress auto-closes)

## Opening prompt for the fresh session

Open Claude Code CLI in `~/Documents/GitHub/Empire_State_Events_Pipeline_Take_3` (fresh session, not a continuation), then paste:

```
YED-30 Step 5: backport the canonical CLAUDE.md fragment into Empire State.

Read .claude/proposals/yed-30-step-5-empire-state-backport.md first. Then
execute the diagnostic plan below (Stages 1 and 2 only — no edits yet) and
report back with the refactor plan for my approval.
```

## Execution plan

### Stage 1 — Diagnostic (no edits)

1. **Layer A+B health check.** Confirm in this fresh session:
   - "🟠 Linear priorities" block appears at session start (Layer B universal hook)
   - `alex:` namespaced skills loadable (Layer A plugin)
   - Cite one ticket + 3 skill names as evidence
2. **Read this repo's CLAUDE.md end-to-end** (currently ~35KB at root)
3. **Categorize every block in CLAUDE.md** into one of:
   - **REPLACE** — duplicated by canonical fragment (communication_rules, behavioral_rules, source-of-truth language, build-better-not-faster rules)
   - **KEEP as `<project_architecture>`** — Empire-State-specific (Notion DB IDs, schemas, write orchestration, gotchas, SDK runtime constraints, systems-thinking harness, pipeline phases, etc.)
   - **KEEP as `<standing_context_overlay>`** — Empire-State-specific context that adds to canonical (open priorities pointer, project status)
   - **DELETE** — stale or transitional content that doesn't belong anywhere (e.g., the "transitional duplicate until YED-26 ships" block — YED-26 has shipped)

### Stage 2 — Refactor plan (no edits)

Produce a markdown plan listing:
- The blocks-to-be-replaced (with line numbers from current CLAUDE.md)
- The blocks-to-be-kept (with their target overlay tag)
- The blocks-to-be-deleted (with reason)
- A risk note for any block where the call is ambiguous
- Estimated size of refactored CLAUDE.md (canonical fragment is ~6KB; overlays should be ~15-20KB; total ~25KB vs current 35KB)

### Stage 3 — Execute (only after plan approval)

1. Create branch `alex/yed-30-step-5-empire-state-backport`
2. Refactor CLAUDE.md per the approved plan
3. Verify the `@`-import resolves: spot-check that canonical content appears in the refactored file's session context
4. Commit + push + open PR
5. Validate in a fresh session (4-point health check identical to gtm-os/job-hunt-system, plus a 5th check on Empire-State-specific content recall — e.g., "name the 6 Notion DBs and 3 of their property gotchas")

## Risks

| Risk | Mitigation |
|---|---|
| Refactor breaks an in-flight pipeline behavior because Claude no longer reads a critical rule | Stage 1 audit categorizes every block. Anything ambiguous defaults to KEEP. Stage 3 validates in a fresh session before merge. |
| `@`-import path resolves on dev machine but not in some other context | Absolute path `~/Documents/GitHub/alex-agents-skills/Me/canonical-claude-md.md` is stable; gtm-os and job-hunt-system both validated with the same path. |
| Project-architecture block grows unwieldy | Keep it. It's *supposed* to be project-specific. The Notion DB schemas, gotchas, and SDK constraints are exactly the kind of content the canonical fragment doesn't try to absorb. |
| Linear auto-closes YED-30 on merge (the recurring tax) | Workspace toggle is now OFF. Confirmed before this proposal was written. |

## PR title + body (when ready to open)

With the Linear auto-close toggle off, naming is free of constraints:

- **Title**: `YED-30 Step 5: backport canonical fragment into Empire State CLAUDE.md`
- **Body**: include "Closes YED-30" — workspace toggle being off means this no longer auto-closes; manually flip YED-30 to Done after merge + validation

## Estimated effort

- Stage 1 diagnostic: 15-20 min
- Stage 2 plan: 10-15 min (parallelizable with Stage 1 if structured well)
- Stage 3 execute: 30-45 min including validation
- **Total: ~1 hour fresh-headed**

## What "done" looks like

- CLAUDE.md is ~25KB (down from ~35KB), with the canonical fragment imported via `@`
- Communication_rules, behavioral_rules, and other universal content are no longer duplicated — they live in the canonical, edited once
- Project_architecture block contains all Empire-State-specific content (Notion schemas, gotchas, SDK constraints, systems-thinking harness, phased roadmap) intact
- Fresh-session validation shows no behavior regression: live priorities pull works, alex plugin loads, canonical content + overlay both in context, Empire-State-specific recall (Notion DBs, gotchas, phase status) still accurate
- YED-30 manually flipped to Done after PR merge + validation
