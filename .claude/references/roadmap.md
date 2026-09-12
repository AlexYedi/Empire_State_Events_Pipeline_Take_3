# Empire State — Roadmap & Plan of Record

**This file is the single, version-controlled plan of record.** It replaces two machine-local plans
that were cited everywhere but had vanished from disk (`~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`
= build-rigor program; `~/.claude/plans/where-do-we-stand-sunny-puzzle.md` = MI-Engine framing). Root
cause of their loss: plans-of-record lived only in un-versioned `~/.claude/plans/`. This one lives in the
repo so it can't silently disappear. **Linear is the live "what's open" source of truth; this file is the
narrative spine.** Last re-anchored: 2026-08-07 (YED-124); **facts reconciled 2026-09-12** (see "Shipped since" below).

---

## Next 3 moves (the runway)

1. **RAG / knowledge base (YED-118) — IN PROGRESS, well past kickoff (updated 2026-09-12).** Phase A shipped (`/ingest-doc`, `/ask-library`, doc-kb schema + RLS); **Phase A.5** hardening underway (contextual + hybrid + rerank, Ragas-gated — **YED-156**), plus **YED-157** (doc_claims staging + Gemini claim extractor) and **YED-155** (build-elevating PRD template + Linear convention). **Merged to `main` 2026-09-12 (PR #60)** — Phase A + A.5 (YED-156 Done) + YED-155 shipped; YED-157 shipped **B1+B2 only** (inert by design; B3–B6 remain, continuation branch `yed-157-phase-b`). The stray Clarify ADR-6 was dropped in the merge; no merge debt remains on this workstream.
2. **Graph consolidation (YED-130) — DONE (2026-08-10/13).** Resolved: consolidated onto ONE canonical graph — Empire's Supabase `oicikjyzmxqfomrrqkvf` hosts, the gtm-os `signal.*` model won; the redundant gtm spine was decommissioned (YED-135). No longer a runway item. Decision record: `docs/adr/`.
3. **Drop "provisional" on the build-quality judge — hold the bar as written (decided 2026-09-08).** At **4/15 acked prospective runs** (100% Gemini-vs-Alex so far); **~11 more** at ≥80% Gemini-vs-Alex needed. Accrues via interactive `/judge-build` acks (autonomous + backfill runs don't count). Watch: every prospective run so far has been a unanimous pass, so the disagreement/tiebreak path is still untested. + scope the second non-content lens (YED-126).

*Sequenced behind these, not dropped:* a second non-content MI lens (M3 pillar 3); audience-first content (YED-103); job-search Capstone 2 (YED-59).

### Shipped since the 2026-08-07 re-anchor (reconciled 2026-09-12)

Not previously reflected in this file — all merged to `main` unless noted:

- **Job-Search Engine v1** (YED-146 · 147 · 148 · 150 — all Done): me-model **Target-Role ICP §1.5**, `target-companies.md` registry (21 companies → ATS), **role-radar rubric v2 → v2.4**, Notion **Roles DB** (~172 roles scored), warm-path map. Rubric evolution: **v2.1** exemptions/intangibles · **v2.2** IC-vs-people-management gate · **v2.3** $200K OTE floor + Mid-Market level flexibility · **v2.4** A-tier threshold 78→85. *Still open in this project: YED-149 (graph producer, deferred v1.1), YED-151 (resume tailor), YED-152 (interview-prep ICP wiring).*
- **Inbox Intelligence Miner v1** (YED-153, Done; PR #61) — Gmail as a first-class MI producer; **ADR-7**. ⚠️ Gmail `modify` reauth still gates in-Gmail labeling + the morning cron.
- **OBS capture lane** (YED-154, Done; PR #63) — recording SOP + ingest ETL; the Granola/Clarify replacement. Live GUI pass + first real smoke test still outstanding.
- **ADR-8 system-graph drift router** (YED-158) — a derived graph over the repo's own build artifacts; a **router, not a detector**. Note: unrelated to the MI graph despite both being called "the graph."
- **Content-quality decision backlog cleared** (2026-09-11, 5 of 5): variants **3** · visual brief **mandatory** · **ADR-6** brief placement (discrete Content Draft canonical; Event page carries head/pointer, dual-write removed) · stance **advisory, not a gate** · A-tier **≥85**. Plus the **pre→post arc** (style guide **v1.0**): pre-event = table-set macro→micro→implications; post-event = the reality check, mining the `post_event_brief` **Pre→Post Gap**.
- **Judge hardening** — check-refs false-positive fix + cross-provider evidence parity.

**Process note (2026-09-12):** two branches independently minted an `ADR-6`. Rule now recorded in `docs/adr/README.md`: **mint ADR numbers from `main`, not from a branch** — a collision is only visible after a merge.

**Git topology (reconciled 2026-09-12):** single source of truth = `main`. Two worktrees (the `main` checkout + `ESP-jobsearch`), both to sit at `main` between sessions; continuation branches cut from `origin/main` per the CLAUDE.md git conventions and `.claude/references/reconciliation-terminal-charter.md`. Linear corrected to git truth the same day (YED-156 Done · YED-157 In Progress · four zombie In-Progress issues and four retired-program Urgents demoted · Build-Rigor project Completed · Job-Search Engine In Progress).

---

## Shared mission (empire-state + gtm-os) — the top frame

Build a cohesive, lens-agnostic **intelligence + GTM-engineering + content body of work** that
*demonstrates* full-stack-GTM capability. **Employment is a first-class, genuinely-pursued outcome of
that work — one balanced component carried in equal measure by both projects — never an "at all costs"
imperative that narrows or distorts the build.** The engine serves many lenses; job-search is one of
them, weighted like the others. (Recalibrated 2026-08-07: gtm-os had over-indexed on employment as its
telos; both repos now share it as a balanced component. gtm-os CLAUDE.md carries the same statement.)

## North stars (three nested under the shared mission)

- **Program:** "build better, not faster" as the default for every project; the measurement layer's operational north-star is **acted-on value** (outcome vs. each artifact's assigned goal, trended).
- **Career/product:** the **Market-Intelligence Engine** — a lens-agnostic research engine (Job-Search + Content cores today) that is the differentiator and the job-search asset.
- **Content:** audience-first documentarian authority (`.claude/references/audience-north-star.md`) feeding the job search.

---

## Program map (workstreams + state — 2026-08-07, reconciled 2026-09-12)

| Workstream | State | Home |
|---|---|---|
| **Market-Intelligence Engine** | M1 ✅ · M2 ✅ · **M3 scoped (next)** | Linear project "Market-Intelligence Engine"; Supabase `empire state ai` (`oicikjyzmxqfomrrqkvf`, REST) |
| **empire-state-hub** (canonical portfolio + cockpit) | live; Phase 3 content shipped; Phase 4 (session replay) backlog | repo `AlexYedi/empire-state-hub` |
| **Build-Rigor & Measurement Layer** | ✅ closed (DoD gate, telemetry→PostHog 524367, cross-provider judge); one open thread = drop-provisional | this repo `.claude/` + hub `/ops` |
| **Content & Voice Engine** | shipped (event research + pre/post content + living voice); **content-quality control system UNBLOCKED 2026-09-11** — all 4 rulings made, invariants contract now buildable | this repo `.claude/skills/` |
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
- **Topic-intelligence — cross-repo entanglement RESOLVED 2026-08-10 (YED-130).** It was built in the **gtm-os / gtm-os-hub** ecosystem (YED-110/120/122 Done); the consolidation settled it as **one graph, not two** — carried forward onto Empire's canonical Supabase `oicikjyzmxqfomrrqkvf` (gtm `signal.*` model won). The gtm spine is now redundant (decommission tracked YED-135). Canonical surface is empire-state-hub. Decision record: `docs/adr/`.

---

## Open threads / debt

- **MI graph reconciliation — RESOLVED 2026-08-10 (YED-130, Done).** Decided and shipped: consolidated onto ONE canonical graph — Empire's Supabase `oicikjyzmxqfomrrqkvf` **hosts**, the gtm-os `signal.*` **model won** (three-layer split: Data→consolidate, Surface→coexist, Capability→separate). The separate gtm spine (`abkvgihlbwfloentugtd`) is now redundant — a coherent static snapshot carried forward. Its **decommission is deferred, gated cleanup tracked as YED-135** (gated behind an N-night watch + the YED-131 crosswalk question — NOT blocked by YED-131). Decision record: `docs/adr/` (ADR-0→ADR-4); investigation brief: `~/Documents/GitHub/mi-consolidation-investigation-brief.md`.
- Drop-provisional on the judge (calibration continuation).
- Content-quality control system: **all 4 blocking rulings made 2026-09-11** (variants=3 · visual brief=mandatory · brief placement=ADR-6 discrete-canonical · stance=advisory-not-a-gate). **Unblocked** — the canonical invariants contract is now buildable; only the falsifiable rules bind as gates.
- CLAUDE.md `<project_architecture>` refreshed 2026-08-07; keep it current as M3 ships.

---

## Pointers

- **Live status:** Linear (team Yedibalian) — projects: Market-Intelligence Engine · Full-Stack GTM Roadmap · Empire State — Build-Rigor & Measurement · Empire State Events.
- **MI spine contract:** `.claude/references/market-intel-spine.md` · **schema:** `market-intel-schema.sql`.
- **Rigor:** `build-session-contract.md` · `value-action-registry.md` · `cross-provider-judge.md` · DoD in `CLAUDE.md`.
- **Content:** `audience-north-star.md` · `content-style-guide.md` · `content-anti-patterns.md`.
- **Workflows manual:** `.claude/WORKFLOWS.md`.
