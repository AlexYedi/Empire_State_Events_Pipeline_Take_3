# Rubric: `build-quality@2`

Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code.
Owned by the eval convention (`rubric_version` = `build-quality@2`; never mutate — bump to `@3`).

**What changed from `@1` (2026-07-15, first `/rigor-review`):** two anchors tightened in response to the
first calibration batch. `@1` is retained unchanged for the runs scored under it; new runs use `@2`.
1. **`completeness` — the dangling-reference cap.** A skill/command that references a repo file, rubric, or
   reference doc that **does not exist** (a load-bearing referenced-but-absent file) now **caps completeness
   below the pass band (≤ 0.60)**. Rationale: the one judge–human *disagree* in the `@1` batch — trend-radar
   passed at 0.76 while referencing a nonexistent `signal-taxonomy.md`, making a core step ad-hoc every run.
   Alex: the judge was too lenient. A promised-but-absent dependency is an incompleteness, not a deferral.
2. **`completeness` — the command-orchestration anchor.** For `artifact_type: command`, "complete" now
   requires the orchestration skeleton in `.claude/references/command-orchestration-convention.md`
   (intake+validate → dispatch → collect → synthesize → judge?(if graded) → **named output destination** →
   failure modes). A command that only *lists* agents under an "Invocations" heading — no dispatch order,
   no parallel/serial control flow, no output destination — **fails completeness (≤ 0.35)**. Rationale: the
   `thin-declarative-command` recurrence (count 5, the Jul-2 GTM suite).

Score each criterion **independently 0–1**. Composite = weighted sum. **Verdict: pass if composite ≥ 0.70,
else flag-for-rework.**

| id | weight | what "good" means |
|---|---|---|
| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. |
| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. **Cap ≤ 0.60 if a load-bearing referenced file/rubric/doc does not exist.** **For commands: cap ≤ 0.35 if the orchestration skeleton is absent (agents listed but never dispatched, or no named output destination).** |
| `convention_adherence` | 0.20 | Matches house conventions: file placement + frontmatter, naming, source-of-truth discipline, MCP/tool-name + Notion-plan constraints (e.g. `notion-search` not `notion-query-data-sources`), SDK constraints (fan-out from parent thread; MCP writes parent-thread only), `alex:`-prefix for plugin skills. |
| `anti_pattern_avoidance` | 0.20 | Avoids known traps: over-engineering/ceremony, duplicating state, **resurrecting a tombstoned/reversed decision** (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS sanctioned as the Market-Intelligence Engine system-of-record per the 2026-06-28 re-scope, so MI use is NOT an anti-pattern), fabricated numbers/specificity, **orphan metrics** (no `{threshold→action→surface}`), hardcoded secrets, lossy summarization where fidelity matters, **speculative surface with no named publishing friction** (CLAUDE.md steering bias). |
| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming — a command that presents as complete while non-functional is dishonest framing). |

### Per-criterion anchors (≥1 pass, ≥1 fail)
- **correctness** — pass: a hook tested to emit a valid record; a skill whose steps reference real Notion DB ids. fail: references a tool/DB that doesn't exist; claims an output the logic can't produce.
- **completeness** — pass: skill has methodology + failure-modes + references *that all exist*; command has the full orchestration skeleton; hook degrades gracefully. fail: an AC item silently unaddressed; `TODO` left in; **references a file that doesn't exist**; **command lists agents but never dispatches them**.
- **convention_adherence** — pass: `.claude/skills/<name>/SKILL.md` with correct frontmatter; uses the plan-compatible Notion reads; fan-out from parent thread. fail: wrong frontmatter; hardcodes a secret; a "lead agent orchestrates other agents" pattern (SDK-illegal).
- **anti_pattern_avoidance** — pass: contract-first lean foundation; tombstones reversed decisions; each build removes a named friction. fail: builds the platform when "lean" was decided; dual-writes state; adds a metric with no wired action; fabricated property mappings; speculative command with no friction behind it.
- **diagnostics** — pass: comments explain the contract; honest "best-effort" caveat. fail: opaque failure mode; overclaims certainty; presents a skeleton as a finished command.

### Machine-readable
```json
{
  "rubric_version": "build-quality@2",
  "pass_band": 0.70,
  "criteria": [
    {"id": "correctness", "weight": 0.30},
    {"id": "completeness", "weight": 0.20},
    {"id": "convention_adherence", "weight": 0.20},
    {"id": "anti_pattern_avoidance", "weight": 0.20},
    {"id": "diagnostics", "weight": 0.10}
  ],
  "completeness_caps": [
    {"when": "references a load-bearing file/rubric/doc that does not exist", "max": 0.60},
    {"when": "artifact_type=command AND orchestration skeleton absent", "max": 0.35}
  ]
}
```
