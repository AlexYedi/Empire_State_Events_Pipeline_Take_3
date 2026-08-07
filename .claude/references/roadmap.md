# Empire State — Roadmap & Plan of Record

**This file is the single, version-controlled plan of record.** It replaces two machine-local plans
that were cited everywhere but had vanished from disk (`~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`
= build-rigor program; `~/.claude/plans/where-do-we-stand-sunny-puzzle.md` = MI-Engine framing). Root
cause of their loss: plans-of-record lived only in un-versioned `~/.claude/plans/`. This one lives in the
repo so it can't silently disappear. **Linear is the live "what's open" source of truth; this file is the
narrative spine.** Last re-anchored: 2026-08-07 (YED-124).

---

## Next 3 moves (the runway)

1. **MI Engine M3 — "the engine as differentiator" — kickoff: surface + reconcile topic-intelligence.** The topic-intelligence layer is already BUILT (YED-110 & YED-120 Done) — but it landed in the **gtm-os** ecosystem, not empire-state. So the next move is **not** "build it," it's: (a) resolve whether gtm-os's topic-intelligence runs on the *same* Supabase graph as the empire-state MI engine (`oicikjyzmxqfomrrqkvf`) or a separate spine — **an open structural decision** (see Open threads); then (b) surface it on the canonical **empire-state-hub** (YED-122 §B signal_read views + render; YED-114 spine node).
2. **Knowledge/RAG layer (YED-118)** — a document knowledge base as a new MI producer/source. Write its one-pager (ChatPRD → Notion) *before* building.
3. **Drop "provisional" on the build-quality judge** — ~13 more held-out Approach-B runs holding ≥80% Gemini-vs-Alex, so the engine's outputs are trusted, not just shipped.

*Sequenced behind these, not dropped:* a second non-content MI lens (M3 pillar 3); the content-quality control system; audience-first content (YED-103); job-search Capstone 2 (YED-59).

---

## North stars (three nested, honest)

- **Program:** "build better, not faster" as the default for every project; the measurement layer's operational north-star is **acted-on value** (outcome vs. each artifact's assigned goal, trended).
- **Career/product:** the **Market-Intelligence Engine** — a lens-agnostic research engine (Job-Search + Content cores today) that is the differentiator and the job-search asset.
- **Content:** audience-first documentarian authority (`.claude/references/audience-north-star.md`) feeding the job search.

---

## Program map (workstreams + state, 2026-08-07)

| Workstream | State | Home |
|---|---|---|
| **Market-Intelligence Engine** | M1 ✅ · M2 ✅ · **M3 scoped (next)** | Linear project "Market-Intelligence Engine"; Supabase `empire state ai` (`oicikjyzmxqfomrrqkvf`, REST) |
| **empire-state-hub** (canonical portfolio + cockpit) | live; Phase 3 content shipped; Phase 4 (session replay) backlog | repo `AlexYedi/empire-state-hub` |
| **Build-Rigor & Measurement Layer** | ✅ closed (DoD gate, telemetry→PostHog 524367, cross-provider judge); one open thread = drop-provisional | this repo `.claude/` + hub `/ops` |
| **Content & Voice Engine** | shipped (event research + pre/post content + living voice); **content-quality control system = new workstream, paused on Alex's rulings** | this repo `.claude/skills/` |
| **Three-layer distribution (`alex` plugin)** | Layer A/B shipped; Layer C partial; measurement layer **deliberately NOT promoted** (pending proof it's load-bearing) | `AlexYedi/alex-agents-skills` |

---

## Market-Intelligence Engine — milestones

- **M1 — Interview-Prep Dossier (Job-Search lens) ✅** (YED-105). `/interview-prep`; proves the graph + specialists serve a non-content lens.
- **M2 — Content-lens dashboard + veracity V1 ✅** (YED-106). `/ops/market-intel` on the hub: signal feed, trust strip, **evolving-viewpoint relevance panel** (YED-121). Fed by the progressive engine (YED-115: `/morning-refresh` YED-117 + relevance recompute YED-121) and the topic-intelligence substrate (YED-120).
- **M3 — "The engine as differentiator" (scoped, next).** Deepen the product. Target ~2026-09-15 (re-dated honestly; the old ~Aug-17 anchor was hollow). Pillars:
  1. **Topic-intelligence layer** — already built (YED-110 & YED-120 **Done**, in the gtm-os ecosystem). M3 work = reconcile the graph (gtm-os vs empire-state — see Open threads) + surface on empire-state-hub (YED-122 §B, YED-114). Not a from-scratch build.
  2. **Knowledge/RAG layer** — YED-118 document knowledge base as an MI producer (PRD-first).
  3. **A second non-content lens** — beyond job-search + content (new issue to scope; e.g. company/deal or market-landscape intelligence).
  4. **Quality gate:** drop-provisional on the judge.
- **Future:** unattended scheduling of producers (the one piece that spends metered API tokens — deliberately last); learned relevance weights; embedding-based dedup.

---

## Structural decisions (recorded 2026-08-07)

- **Canonical Hub = `empire-state-hub`.** The recent work (build-arcs, journal, `/ops/market-intel`) lives here. The `gtm-os-hub` plans (`expressive-dreaming-spark.md`, `PHASE_1_BUILD_SPEC.md`) and the legacy Linear "Empire State Hub" project are superseded; fold any still-live issue (e.g. security YED-81) into the canonical hub.
- **Supabase is the MI Engine system-of-record** (REST, `SUPABASE_API_KEY`, never the Supabase MCP — different account). The old "no Supabase" architecture-philosophy line is **superseded** for the MI engine; "no n8n / no middleware" still holds. The Supabase *ban* survives only for the measurement/eval layer.
- **`/morning-refresh` auto-logs signals with no approval gate** — this is an accepted Tier-2 design exception (append-only, every write reported after the fact), NOT a silent divergence from the HITL default. Documented in `.claude/commands/morning-refresh.md`.
- **Topic-intelligence — cross-repo entanglement is LIVE, not resolved.** Reality (found 2026-08-07): it's built in the **gtm-os / gtm-os-hub** ecosystem (YED-110/120 Done, YED-122 in progress), while the MI Engine's canonical spine is empire-state's Supabase `oicikjyzmxqfomrrqkvf`. YED-116 (the shared-taxonomy decision) was cancelled, so whether these are one graph or two is **undecided** — the first thing M3 must settle (see Open threads). Canonical surface is empire-state-hub regardless.

---

## Open threads / debt

- **⚠️ MI graph reconciliation (M3 kickoff decision, needs Alex):** is gtm-os's topic-intelligence on the *same* Supabase graph as the empire-state MI engine (`oicikjyzmxqfomrrqkvf`), or a separate gtm-os spine? Decide one-graph-or-two before building more MI on top. This is the highest-priority structural unknown surfaced by the re-anchoring pass.
- Drop-provisional on the judge (calibration continuation).
- Content-quality control system: awaiting Alex's rulings (variants 2 vs 3; visual brief mandatory vs optional; research-brief artifact discrete vs event-body; pre-event stance) before building the canonical invariants contract — see `buzzing-scribbling-sky.md` (Step 1 diagnosis).
- CLAUDE.md `<project_architecture>` refreshed 2026-08-07; keep it current as M3 ships.

---

## Pointers

- **Live status:** Linear (team Yedibalian) — projects: Market-Intelligence Engine · Full-Stack GTM Roadmap · Empire State — Build-Rigor & Measurement · Empire State Events.
- **MI spine contract:** `.claude/references/market-intel-spine.md` · **schema:** `market-intel-schema.sql`.
- **Rigor:** `build-session-contract.md` · `value-action-registry.md` · `cross-provider-judge.md` · DoD in `CLAUDE.md`.
- **Content:** `audience-north-star.md` · `content-style-guide.md` · `content-anti-patterns.md`.
- **Workflows manual:** `.claude/WORKFLOWS.md`.
