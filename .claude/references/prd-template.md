# Canonical PRD template (build-elevating)

**Purpose.** The default spec for any non-trivial build (DoD gate item 1). Composed from Alex's own
corpus (`writing-prds`, `writing-north-star-metrics`, `ai-product-strategy`, `risk-playbooks`,
`head-of-product-engineering`, systems-thinking) + external canon (Amazon PR-FAQ, Shape Up, the
Linear Method, spec-kit, Anthropic's agent-engineering posts).

**The one idea that governs this template.** Because an *agent* writes these, human authoring cost is
~0 — so the classic failure inverts: the risk is **too much frictionless precision**, not too little
thinking. Optimize for **forcing decisions, not writing descriptions**, and make staleness cheap.
Two rules follow:
- **Comprehensive on reasoning, deferred on implementation.** Go deep on problem, alternatives,
  failure analysis, decision rationale, success + eval. Do NOT pre-commit implementation values reality
  will decide (chunk size, exact schema, field types) — flag them as build-time detail (§8).
- **Never rewrite — append to the Decision Log.** A dated decision entry is the anti-staleness engine.
  The PRD stays true because history accretes, not because sections get edited.

**Anti-creep (same discipline as the DoD gate).** Target ≤ ~1 page of prose + the decision log. If the
body creeps toward exhaustive, that's the rule-beating signal — shrink it. Length dilutes the
executable signal; padding is docked by `build-quality@4`'s density cap. A section with nothing
load-bearing to say is deleted, not filled.

---

## Template (copy this)

> **Title** · **Linear:** YED-NN · **Date:** YYYY-MM-DD · **Owner:** Alex · **Status:** draft/approved
> · **Appetite:** <3d | 3-7d | 1-2wk | 2wk+ · **Backfilled?** no (yes → one-line why + honest DoD waiver)

**1. Problem & why now** *(PR-FAQ head — the most important section).*
The problem, the evidence it's real, and *why now*. Lead with the problem, never the solution
(the #1 PRD mistake). One-line "press release": if this shipped, what changes for whom — and would
anyone care? If you can't write that line, stop.

**2. Goals / Non-goals.**
Goals as outcomes. **Non-goals are hard and explicit** — agents over-build on fuzzy edges. Resolve
optionality: "TBD" / "support both" reads to the executing agent as *build both*. Decide or exclude.

**3. Solution sketch + alternatives considered.**
The chosen approach in a few lines, then the **alternatives weighed and why rejected** (this is where
the real thinking lives — e.g. the R2-vs-GCS-vs-Supabase reasoning belongs *here*, not buried in chat).

**4. Leverage & systems check** *(our differentiator).*
- **Leverage point** this build targets (Meadows ladder — most builds only diddle parameters #12;
  the cheap high-leverage move is usually information flows #6). Name it + a **direction check**.
- **Archetype guarded against** — especially **Shifting the Burden** (our documented root cause: rigor
  living in optional docs) and **Seeking the Wrong Goal / Rule-Beating** (Goodhart). One line each.

**5. Rabbit holes + pre-mortem** *(satisfies DoD item 3 — the adversarial pass, inline).*
Named rabbit holes (where scope/risk actually hides). Then: *"It's N weeks later and this is a regret —
why?"* — top 2-3 failure modes + the fix folded into the plan.

**6. Success criteria + eval** *(measure value delivered, not captured).*
- **North-star metric**: leading not lagging, simple, precisely defined ("what counts as X?"), tied to
  the acted-on-value north-star, with a **counter-metric / guardrail** against gaming.
- **Value-action-registry row** (required — no orphan metrics): `{threshold → action → surface}`,
  surface ∈ {in-session DoD · Hub dashboard · weekly review}.
- **Acceptance criteria** — each requirement as a *checkable statement the build-quality judge can grade*.
  "Done" = these pass. This is the PRD→Linear→judge loop-closer.

**7. AI-native fields** *(for AI/agent builds — from `ai-product-strategy`).*
Human-AI boundary (what the agent decides vs. the human gates); failure/squishiness UX (the 1% wrong);
built-for-the-slope (swappable models); which eval/judge *is* the living acceptance layer.

**8. Build-time details — flagged, deferred (NOT committed).**
The implementation precision reality will decide: chunk size, index type, exact fields, library choice.
Listed so they're *conscious deferrals*, not omissions. Resolved during the build, recorded in §10.

**9. Constitution / invariants this build must honor.**
Pointer to the non-negotiables it touches: CLAUDE.md invariants, `notion-write-gotchas.md`,
`sdk-runtime-constraints.md`, `market-intel-spine.md`, the relevant ADR(s). (spec-kit's constitution
pattern — make the invariants machine-consumable, not prose the agent may skip.)

**10. Linear wiring + Decision log.**
- **Linear:** one issue per requirement/story; labels `project-<slug>` + `cycle-<n>`; `blockedBy` wired
  from any "Depends on" line; milestone set. (Full rules: `.claude/references/linear-convention.md`.)
- **Decision log (dated, append-only):**
  - `YYYY-MM-DD` — <decision> — <why> — <what it supersedes, if any>

---

## Section-to-gate map (why each section exists)

| Section | Satisfies |
|---|---|
| 1 Problem/why-now | `writing-prds` "problem first"; PR-FAQ |
| 3 Alternatives | decision rationale (the R2 lesson); Shape-Up pitch |
| 4 Leverage/systems | systems-thinking harness; guards the diagnosed root cause |
| 5 Pre-mortem | **DoD gate item 3** (adversarial pass) — inline, not separate |
| 6 Success + eval + registry row | `writing-north-star-metrics`; value-action-registry (no orphan metrics); "evals as PRDs" |
| 6 Acceptance criteria | **build-quality judge** grades against the spec, not vibes |
| 8 Deferred details | anti-staleness (the chunk-size-was-wrong-by-Phase-0 lesson) |
| 10 Linear + decision log | **DoD gate item 2**; anti-staleness engine |

## Worked example (condensed — YED-118 in this shape)
- **1 Problem/why-now:** Drive-MCP retrieval is filename-only; can't ask a whole book; corpus fights Gmail's 15GB. *Press release:* "Ask the reference library and get cited passages" — yes, it's the M3 differentiator.
- **3 Alternatives:** blob store R2 vs GCS vs Supabase-Storage → R2 (decoupled, 10GB, $0 egress, no pause); the Supabase-Pro detour died on a stranded credit. Embeddings local vs hosted → local (zero-metered).
- **4 Leverage:** information-flow (#6) — route a doc's claims to the decider. Archetype guarded: Shifting-the-Burden (build ahead of corpus volume justified strategically, eyes open).
- **5 Pre-mortem:** small-model recall; DDL/wrong-project; corpus-maturity → fixes: recall@k gate + bge-base fallback; front-loaded Phase 0; explicit maturity call.
- **6 Success:** recall@8 ≥ 80% on a Baseten eval set (→ shipped 88%); registry row {recall<80% → swap to bge-base → in-session}. Acceptance: ingest end-to-end + dedup no-op + cited answer.
- **8 Deferred:** chunk size, hnsw vs ivfflat, top-k, bge query prefix — all decided in build.
- **10 Decision log:** `2026-09-10 — kept R2 over Supabase-Storage — Pro credit stranded on GTM_OS org; decoupling+10GB+no-pause won.`

*This template is itself held to its own rules: it defers nothing load-bearing and forces the decisions above.*
