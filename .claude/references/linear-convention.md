# Linear usage convention (solo AI-native cut)

**Purpose.** How this workspace uses Linear so it stays the single source of truth for "what's open"
without ceremony that a solo builder doesn't need. Distilled from the Linear Method
(linear.app/method), how Linear builds product, and Alex's existing conventions (YED-26 codification,
`head-of-product-engineering`, `prioritizing-roadmap`). Pairs with `.claude/references/prd-template.md`.

## The primitives — and how we use them

| Primitive | What it is | Our usage |
|---|---|---|
| **Issue** | Smallest reasonable unit of work, single owner, visible progress | **One issue per PRD requirement/story.** Title = the outcome. Don't split below "a reviewable change." |
| **Project** | A feature/outcome with a brief spec + one owner | **The PRD's home in Linear.** Project doc links to the ChatPRD/Notion PRD. Live projects: Market-Intelligence Engine · Build-Rigor & Measurement · Empire State Events · Full-Stack GTM Roadmap. |
| **Milestone** | A dated checkpoint inside a project | M1/M2/M3 on the MI Engine. Use for real gates, not decoration. |
| **Cycle** | 2-week rhythm; unfinished **rolls forward** | The circuit breaker (Shape-Up in Linear form) — an item that won't finish in a cycle gets **re-shaped, not extended**. Label `cycle-<n>`. |
| **Initiative** | Why multiple projects connect | **Defer until >~3 parallel projects genuinely connect.** Overkill for a solo builder before then. |

## Rules (the load-bearing few)

1. **Triage is the single source of truth for "what's open."** CLAUDE.md blocks are transitional
   duplicates, never new state. A SessionStart hook pulls live priorities (YED-26/29).
2. **Appetite, not estimates.** Use the bands `<3d · 3-7d · 1-2wk · 2wk+` (already the ideation
   timeline bands) — never story points. Fixed time, flexed scope.
3. **PRD ↔ issues, bidirectional.** The PRD lists "Depends on" lines → wire them as `blockedBy` so the
   dependency graph is queryable. Each issue references the PRD; the PRD's §10 lists the issues.
4. **Labels stay ≤3-5.** `project-<slug>`, `cycle-<n>`, and a type/priority tag. No sprawling taxonomy.
5. **Progress = shipped artifacts, not ticket theater.** A commit / PR / passing eval is progress; a
   status change alone is not. Link the PR/commit on the issue.
6. **Backlog discipline — don't hoard.** Cancel superseded issues; close-as-Done when work ships
   independently; re-issue only when explicit triggers fire (the 2026-05-13 triage pattern). "Important
   ones resurface; low-priority ones never get fixed."
7. **Comment the build's close on its issue** — decision record + PR link + gate result (as done on
   YED-118). The issue is the durable trace, mirroring the PRD's decision log.

## Adopt vs. skip (solo AI-native)

| Adopt | Skip / defer |
|---|---|
| Projects as PRD home; issues as build steps | Initiatives (until >3 projects connect) |
| 2-week cycles as circuit breakers (auto-roll-forward) | Estimates / story points (use appetite bands) |
| Triage = the open-work source of truth | Heavy label taxonomies |
| PRD↔issue links + `blockedBy` from "Depends on" | Multi-team *workflows*, SLAs, custom states — **two teams for two programs is fine** (Empire State + `GTM-OS`, ratified 2026-09-18; each repo sets `LINEAR_TEAM_ID` so the SessionStart pull is program-scoped) |
| Close-out comment with decision record + PR | Ticket theater / status-only progress |

## Container rule — one home per kind (ratified 2026-09-18)

Why this exists: the 2026-09-13 inventory found ~170 open/parked/undecided items across eleven
containers, and ten places where two artifacts disagreed about the same thing. Only "open work"
(Linear) and "sequencing" (`roadmap.md`) had a defined home; every other kind landed wherever it was
discovered. This table assigns the rest. Full record: `.claude/notes/open-items-inventory-2026-09-13.md`.

| Kind | Home | Shape |
|---|---|---|
| Open work | Linear issue in a project; milestone only if on the roadmap runway | `roadmap.md` references IDs only and never carries Done items |
| Parked idea **with** a revisit trigger | Linear Backlog, label `parked`, first body line `Revisit trigger: …` | trigger fires → move to Todo |
| Parked idea **without** a trigger | Notion Project Ideas DB (`collection://0956e6ed-8555-4d8f-8856-388966dedaab`) | not in Linear |
| Decision needed | Linear **Todo**, label `decision`, assigned to Alex, **due-dated**; body = options + recommendation | outcome → `roadmap.md` §9 (or an ADR if architectural); close Done |
| Environmental constraint (platform, SDK, MCP, env) | `.claude/references/platform-constraints.md` (extends `sdk-runtime-constraints.md`) | symptom · cause · workaround; memory files hold one-line pointers |
| Work dependency | Linear `blockedBy` relation | never a list in a doc |
| Debt | Linear Backlog issue if it will ever be paid; otherwise delete the text | no third "tombstone" state |
| Hub repo state (`build-arcs.json` futures, journal gaps) | Linear, project Empire State Hub | hub data files describe the present, never the future |

**The load-bearing rule:** a parked / deferred / decision thought is filed to its home **in the same turn**
it is written anywhere else, and the file carries the Linear ID or Notion link. The weekly
`/rigor-review` grep (`awaiting decision|revisit (after|when)|deferred|parked` outside lines carrying
`YED-`/`GTM-`/a Notion link) is the audit; this sentence is the fix.

**Labels under this rule:** `parked`, `decision` added; the unused Devin-playbook group and
`project-eval-harness` retired (a project is a project). Total stays ≤5 live labels + `cycle-<n>`.

## Sources
Linear Method (linear.app/method) · Linear conceptual model (linear.app/docs) · "How Linear builds
product" (Lenny) · CLAUDE.md YED-26 codification · `head-of-product-engineering` (one-issue-per-story +
`blockedBy`) · `prioritizing-roadmap` (conviction vs. hypothesis, seasons, kill low-usage).
