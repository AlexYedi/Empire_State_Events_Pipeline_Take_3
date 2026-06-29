# Rubric: `build-quality@1`

Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code. Owned by the eval convention (`rubric_version` = `build-quality@1`; never mutate — bump to `@2`). Encodes the hard-won principles of this project so the judge enforces them.

Score each criterion **independently 0–1**. Composite = weighted sum. **Verdict: pass if composite ≥ 0.70, else flag-for-rework** (matches the PRD's "judge score < 0.7 → flag before done").

| id | weight | what "good" means |
|---|---|---|
| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. |
| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. |
| `convention_adherence` | 0.20 | Matches house conventions: file placement + frontmatter, naming, source-of-truth discipline, MCP/tool-name + Notion-plan constraints (e.g. `notion-search` not `notion-query-data-sources`). |
| `anti_pattern_avoidance` | 0.20 | Avoids known traps: over-engineering/ceremony, duplicating state, **resurrecting a tombstoned/reversed decision** (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS sanctioned as the Market-Intelligence Engine system-of-record per the 2026-06-28 re-scope, so MI use is NOT an anti-pattern), fabricated numbers, **orphan metrics** (no `{threshold→action→surface}`), hardcoded secrets, lossy summarization where fidelity matters. |
| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming). |

### Per-criterion anchors (≥1 pass, ≥1 fail)
- **correctness** — pass: a hook tested to emit a valid record; a skill whose steps reference real Notion DB ids. fail: references a tool/DB that doesn't exist; claims an output the logic can't produce.
- **completeness** — pass: skill has methodology + failure-modes + references; hook degrades gracefully. fail: an AC item silently unaddressed; `TODO` left in.
- **convention_adherence** — pass: `.claude/skills/<name>/SKILL.md` with correct frontmatter; uses the plan-compatible Notion reads. fail: wrong frontmatter; hardcodes a secret in a committed file.
- **anti_pattern_avoidance** — pass: contract-first lean foundation; tombstones reversed decisions. fail: builds the platform when "lean" was decided; dual-writes state; adds a metric with no wired action.
- **diagnostics** — pass: comments explain the contract; honest "best-effort" caveat. fail: opaque failure mode; overclaims certainty.

### Machine-readable (for a future automated judge)
```json
{
  "rubric_version": "build-quality@1",
  "pass_band": 0.70,
  "criteria": [
    {"id": "correctness", "weight": 0.30},
    {"id": "completeness", "weight": 0.20},
    {"id": "convention_adherence", "weight": 0.20},
    {"id": "anti_pattern_avoidance", "weight": 0.20},
    {"id": "diagnostics", "weight": 0.10}
  ]
}
```
