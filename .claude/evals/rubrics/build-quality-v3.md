# Rubric: `build-quality@3`

Scope: **build artifacts** in the Empire State pipeline — skills, commands, hooks, reference docs, and code.
Owned by the eval convention (`rubric_version` = `build-quality@3`; never mutate — bump to `@4`).

**What changed from `@2` (2026-07-17, cross-provider backfill finding):** one **composite-level cap** added. `@2`'s
per-criterion completeness caps are retained. `@2` stays valid for runs scored under it; new runs use `@3`.

- **NEW — the confidence-honesty composite cap.** If the artifact commits a **confidence-honesty violation** —
  asserting an **unverified/uncited claim as verified** (stamping an API/fact/version as "verified" without a
  citation; presenting speculation or general-knowledge as established fact; claiming a check was done that
  wasn't) — the **composite is capped at 0.65 (→ flag)**, no matter how high the weighted sum. Rationale: the
  `bf18` finding — a localized honesty defect (multi-agent asserting `create_supervisor` as "verified 2026"
  without a source) was **detected by two independent providers** (Gemini docked diagnostics to 0.0, Haiku docked
  correctness/anti-pattern), yet the criterion-weighting **diluted it to a pass** (0.9 / 0.72). A dishonest
  "verified" claim must not survive the composite math just because it lands in one low-weight criterion.
  Which criterion catches it doesn't matter; the **cap is triggered by the violation existing at all.**

Score each criterion **independently 0–1**. Composite = weighted sum, **then apply the caps**.
**Verdict: pass if (capped) composite ≥ 0.70, else flag-for-rework.**

| id | weight | what "good" means |
|---|---|---|
| `correctness` | 0.30 | Does what its spec/PRD/issue/AC says. Logic sound; references real tools/DB-ids/files; if code, it parses/runs. |
| `completeness` | 0.20 | All required parts present; covers the AC; no TODO stubs; handles obvious edge/failure cases. **Cap ≤ 0.60 if a load-bearing referenced file/rubric/doc does not exist.** **For commands: cap ≤ 0.35 if the orchestration skeleton is absent (agents listed but never dispatched, or no named output destination).** |
| `convention_adherence` | 0.20 | House conventions: file placement + frontmatter, naming (note: **project** skills in `.claude/skills/` take NO `alex:` prefix — that prefix is for `alex`-*plugin* skills only), source-of-truth discipline, MCP/tool-name + Notion-plan constraints (`notion-search` not `notion-query-data-sources`), SDK constraints (fan-out from parent thread; MCP writes parent-thread only). |
| `anti_pattern_avoidance` | 0.20 | Avoids: over-engineering/ceremony, duplicating state, resurrecting a tombstoned decision (gtm-os/Langfuse; Supabase-as-*measurement*-store — but Supabase IS the sanctioned Market-Intelligence-Engine store, so MI use is NOT an anti-pattern), fabricated numbers/specificity, orphan metrics (no `{threshold→action→surface}`), hardcoded secrets, lossy summarization where fidelity matters, speculative surface with no named publishing friction. |
| `diagnostics` | 0.10 | Legible + maintainable; clear comments/errors; failures explicable; **honest about gaps/confidence** (no overclaiming; a skeleton presented as finished, or an unverified claim stamped "verified", is dishonest framing). |

### Composite caps (applied AFTER the weighted sum)
1. **Confidence-honesty cap → composite ≤ 0.65** when an unverified/uncited claim is asserted as verified (any criterion may detect it; the cap fires regardless).
2. (Inherited per-criterion completeness caps above: dangling-reference ≤ 0.60; command-skeleton-absent ≤ 0.35.)

### Per-criterion anchors (≥1 pass, ≥1 fail)
- **correctness** — pass: a hook tested to emit a valid record; a skill whose steps reference real Notion DB ids. fail: references a tool/DB that doesn't exist; claims an output the logic can't produce.
- **completeness** — pass: methodology + failure-modes + references *that all exist*; command has the full orchestration skeleton. fail: an AC item silently unaddressed; `TODO` left in; references a nonexistent file; command lists agents but never dispatches them.
- **convention_adherence** — pass: correct placement/frontmatter; plan-compatible Notion reads; fan-out from parent thread; no `alex:` prefix on a project skill. fail: wrong frontmatter; hardcoded secret; "lead agent orchestrates other agents" (SDK-illegal); `alex:` prefix wrongly demanded/applied on a project skill.
- **anti_pattern_avoidance** — pass: contract-first lean foundation; tombstones reversed decisions. fail: builds the platform when "lean" was decided; dual-writes state; metric with no wired action; fabricated property mappings.
- **diagnostics** — pass: comments explain the contract; honest "best-effort" caveat. fail: opaque failure mode; overclaims certainty; **asserts unverified as verified** (also triggers the composite cap).

### Machine-readable
```json
{
  "rubric_version": "build-quality@3",
  "pass_band": 0.70,
  "criteria": [
    {"id": "correctness", "weight": 0.30},
    {"id": "completeness", "weight": 0.20},
    {"id": "convention_adherence", "weight": 0.20},
    {"id": "anti_pattern_avoidance", "weight": 0.20},
    {"id": "diagnostics", "weight": 0.10}
  ],
  "composite_caps": [
    {"when": "confidence-honesty violation (unverified claim asserted as verified)", "max": 0.65},
    {"when": "references a load-bearing file/rubric/doc that does not exist", "max": 0.60, "criterion": "completeness"},
    {"when": "artifact_type=command AND orchestration skeleton absent", "max": 0.35, "criterion": "completeness"}
  ]
}
```
