# Empire State — Roadmap & Plan of Record (v2 · adopted 2026-09-12)

**This file is the single, version-controlled plan of record.** Linear is the live "what's open"
(`linear-convention.md`); this file is the narrative spine and the *sequencing*. Two rules keep it a
plan and not a ledger: **the runway never carries Done items** (shipped work drops to §10), and
**every runway item names its dependency, appetite band, and why-now**. v1 (2026-08-07 → 2026-09-12)
is preserved in git history; its load-bearing decisions are carried in §9.

---

## 1. The arc — from a pipeline that records to an engine that learns

The system is already good at **recording** (research briefs, `post_event_brief`s, the Notion KG,
telemetry, the build journal) and newly good at **watching** (ADR-8's drift router, the trust strip,
relevance recompute). The next horizon is **learning**: every attended event, ingested book, inbox
signal, and build session becomes exhaust that (a) feeds **one graph**, (b) organized by an explicit
**reference architecture of applied-AI systems** — so the engine knows *what* to keep an ear to the
ground on — and (c) improves the pipeline's own skills through a **judged, human-approved loop**.
It is the software-factory thesis applied to our own system, and the most credible technical-buyer
story the work can tell: *a self-improving market-intelligence engine, with its exhaust on display.*

## 2. North stars (unchanged from v1)

- **Program:** build better, not faster; operational north-star = **acted-on value** (`value-action-registry.md`).
- **Career / product:** the **Market-Intelligence Engine** as the differentiator and the job-search asset.
- **Content:** audience-first documentarian authority (`audience-north-star.md`).
- **Shared mission (empire-state + gtm-os):** employment is a balanced, first-class outcome of the work — never an at-all-costs imperative that narrows the build.

## 3. Programs and lanes

| | What it is | State (2026-09-12) |
|---|---|---|
| **P1 · One Graph** — close the loops | Every producer writes to the MI spine; every consumer reads it | trend ✅ inbox ✅ doc-KB ½ (B1+B2 inert) · **post-event ✗** · roles ✗ |
| **P2 · The Map** — organize the graph | The **Applied-AI Reference Architecture** shipped as `signal-taxonomy` v2 (topics = system components/layers), a hub surface, and the **third MI lens = the architecture lens** (YED-126) | not started; taxonomy is a flat 14-row synonym list |
| **P3 · The Loop** — learn from exhaust | Rigor layer v2: correction-recurrence → *proposed* codified fix (a PR) → judge-gated → Alex merges. Built **on** ADR-8 + the registry's existing "system proposes a fix" row + `/rigor-review`, not beside them | watching ✅ (ADR-8, YED-158) · learning ✗ |
| **Career lane** (continuous) | The consumers: resume tailor (YED-151), interview-prep ICP (YED-152), Clay-backed warm outreach (YED-65, parked), headline test + the theme→prior-post index (YED-178), event deep-dives (= the content pipeline). Every anchor throws off a build-in-public artifact via the journal | in flight |
| **Hygiene lane** (standing tax) | Garbled-name verification, entity dedup (systemic fix = YED-47), denylist enforcement, OBS smoke test, YED-141, YED-137, Linear-to-git-truth | ongoing |

## 4. The dependency chain

`SEC contract (YED-81)` → `P1 producers` → `P2 map` → `P3 loop` → `unattended scheduling (Q1)`

Producers before organizers before learners: a graph can't be organized before it's filled, and
nothing learns from exhaust it doesn't emit. SEC sits first because the richest data (people named in
transcripts) and both scale steps (whole-inbox scan, anything unattended) are gated on it.

## 5. The quarter — Sep 15 → Dec 12 (2-week cycles as circuit breakers; appetite bands, never estimates)

### Phase 0 — Gates & cleanup (→ ~Sep 19)
| Item | Appetite | Why first |
|---|---|---|
| Linear reconciled to this plan (§7) — now the **backlog reconciliation** (`.claude/notes/open-items-inventory-2026-09-13.md`, container rule in `linear-convention.md`) | <1wk | The plan can't be true while zombie programs compete with it; YED-81 + YED-161 shipped (#73/#74/#75) and dropped to §10 |
| OBS live GUI pass + first real smoke test + ETL (**YED-177**) | <1d / 3–7d | YED-154 was "Done" on paper only |

### Phase 1 — Close the loops · P1 (Cycles 1–2, ~Sep 22 → Oct 17) → **A1**
| Item | Appetite | Why now |
|---|---|---|
| **Post-event → MI producer** (YED-160): `/post-event-content` Step 3.9 emits attended-event claims as **staged** signals (candidate→approved, reusing the `doc_claims` pattern) with transcript provenance | 1–2wk | Highest-leverage build on the list: first-hand, Alex-only signal. Today the event *row* reaches the spine (YED-108); the *learnings* never do. Depends on YED-81. |
| **YED-157 B3–B5** — `/doc-digest` (4 lanes, HITL, 25-word check), consumer wiring (the two filter lines), extraction eval; YED-107 folded into lane D | 1–2wk | B1+B2 are inert until this exists; this is where doc-KB earns its keep |
| YED-149 roles → spine producer | 3–7d | Third producer; the job-search lens becomes graph-native |
| YED-131 nightly topic recompute (pg_cron, no LLM tokens) | <3d | Cheap; unblocks the P2 hub panels |

### Phase 2 — The map · P2 (Cycles 3–4, ~Oct 20 → Nov 14) → **A2**
| Item | Appetite | Why here |
|---|---|---|
| **YED-126 — the architecture lens:** Applied-AI Reference Architecture v1 (PRD-first, Fable-drafted) — layers/components of agentic + enterprise AI systems (model → environment → harness → factory, plus data/retrieval, evals, identity/governance, GTM). **Ships only as** `signal-taxonomy` v2 + topic remap + hub surface + the lens's query shape — never as prose alone | 1–2wk | Needs signal density to be grounded; before P1 it's a whitepaper (the R2 trap). Closes M3 pillar 3. |
| YED-114 hub topic-intelligence panels — home settled: **empire-state-hub** | 3–7d | The map needs a face |
| YED-104 T1 audience/conversation intelligence at draft time | 3–7d | Content becomes the graph's first *reader* at draft time (accumulating awareness) |
| **YED-47 hygiene tier-1 in code** — identity + provenance + dedup | 1–2wk | Duplicate entities are the symptom; the graph must be trustworthy before the loop learns from it |

### Phase 3 — The loop · P3 (Cycles 5–6, ~Nov 17 → Dec 12) → **A3**
| Item | Appetite | Why last |
|---|---|---|
| **YED-48** eval harness for event-research (10 golden + judge) | 1–2wk | You can't learn without a score |
| **Behavioral-exhaust loop v1 / Rigor v2** (YED-162): correction-recurrence ≥N → auto-proposed fix as a PR → judge-gated → Alex merges. Not net-new architecture | 1–2wk | Needs the judge trusted (de-provisional accrues passively) and an eval score |
| **ADR-8 Increment 2** (YED-163): extend the system graph to skills ↔ agents ↔ commands ↔ *outcomes* — the skills/agents graph | 3–7d | Watching → learning needs outcomes on the graph |
| Measurement → `alex` plugin promotion | <3d | Only after the loop has produced ≥1 merged fix — the proof it's load-bearing |
| YED-82 craft + honesty + launch (its security-audit half moves to Phase 0 with YED-81) | 3–7d | The hub as the interview artifact, polished after the quarter's proof exists |

**Deliberately deferred to Q1 2027 → one parked issue, YED-179** (unattended producer scheduling — also blocked on the metered-key decision YED-176; learned relevance weights; embedding-based dedup; X/Twitter ingestion). Hub session replay stays YED-113 (parked).

## 6. Anchors (Linear milestones M4–M6 on the MI Engine) — and what each proves

| Anchor | Target | Proof |
|---|---|---|
| **A1 · One graph, three producers** (M4) | 2026-10-17 | Post-event, doc-digest, roles all writing to the spine; trust strip shows them; first digest approved |
| **A2 · The map** (M5) | 2026-11-14 | Reference architecture live as taxonomy v2 + hub panels; the architecture lens answers "what's moving in layer X" |
| **A3 · The loop closes** (M6) | 2026-12-12 | First judge-gated, exhaust-derived fix merged; event-research eval live; judge de-provisional |
| **Career** (continuous) | monthly | ≥1 hiring-manager activation traceable to a post or hub artifact (`audience-north-star.md` floor) |

## 7. Kill / re-home / defer (ratified by Alex 2026-09-12)

- **Canceled:** YED-67 + 68/69/70/71/72/73 (NY Tech Week single-vs-swarm harness — superseded by the cross-provider judge) · YED-41/42/46/57 (Full-Stack-GTM relics) · YED-55/56/59 (Capstone 2 — absorbed conceptually by the MI Engine; the CRM write already exists in YED-142; re-issue as an MI lens when a real outreach friction motivates it) · YED-107 (folded into YED-157 lane D).
- **Programs closed:** "Full-Stack GTM Roadmap (24-week half)" and "GTM-oS" — milestones at 0%, live ideas already inside the MI Engine + Job-Search Engine. Keeping two programs was the source-of-truth failure at the planning layer.
- **Re-homed:** YED-47, YED-128, YED-131 → MI Engine · YED-65 → Job-Search Engine · YED-114 → Empire State Hub · YED-129 → Build-Rigor · YED-141 → Empire State Events.
- **Parked:** this file no longer lists parked items. They live in Linear under label `parked` (with a revisit trigger) or in Notion Project Ideas (without one) — `linear-convention.md` §Container rule, 2026-09-18. Clarify stays dead (a ruling, not a park). *GTM University (GTM-3/GTM-10/GTM-11, formerly YED-98/100/101) un-parked 2026-09-13 → §9; all gtm-OS items moved to the `GTM-OS` Linear team 2026-09-18.*
- **Corrected to git truth:** YED-155 → Done (shipped in #60) · YED-66 → Done (the manual-upload path *is* `/post-event-content`) · YED-81 → High.

## 8. Pre-mortem (the adversarial pass)

- *The reference architecture becomes a whitepaper nobody reads* → it ships only as taxonomy v2 + panels + lens code.
- *Post-event floods the graph with low-confidence claims* → staged candidate→approved with a confidence cap, as doc-KB does.
- *Auto-fixes rot the skills* → proposals only, judge-gated, Alex merges; registry threshold governs.
- *Sessions collide once three programs run in parallel* → one worktree per program; `reconciliation-terminal-charter.md`.
- *Job search crowds out builds, or vice versa* → the career lane is *outputs of the programs*, plus one explicit weekly slot.

**Confidence:** ~75% on the ordering (producers → map → loop; SEC-first is non-negotiable). ~50% on dates — they are appetite, and cycles will re-shape items; that is the point.

## 9. Decision log (dated; append, never edit)

- **2026-09-18 — Backlog reconciliation.** Container rule ratified (`linear-convention.md`); ~170 inventory items triaged (`notes/backlog-triage-2026-09-18.md`) into 9 decisions (YED-128/129/34/173–176), ~20 new issues (YED-177–197), merges, and deletions; ADR-8 Amendment 3 (Increment 4); `GTM-OS` Linear team created and the 11 gtm-OS issues moved (GTM-1…11); labels `parked`/`decision` live. Prioritization (step 2) runs on the clean board.
- **2026-09-13 — GTM University un-parked (GTM-1, formerly YED-164; reverses the §7 park, Alex's call).** Re-aimed against Anthropic's *Staff AI Engineer, GTM Claudification* JD as a **north-star benchmark, not a pivot** — me-model §1.5 (commercial IC search) stays primary. v2 is add-only (v1 unit ids kept: +28 sub-tasks for oversight design, transcript-analysis evals, observability/ROI, Agent SDK + governed MCP, production engineering, inner-source, experimentation, explainable scoring) plus a sequenced 10-stage path; lives in gtm-os-hub. Overlap with P3 (YED-48 eval harness, YED-109 judge, YED-162 loop) is intentional — those builds count in both places.
- **2026-09-12 — v2 adopted.** §7 ratified; YED-81 re-raised to High and scoped as contract + write-path; the third MI lens = the architecture lens (YED-126). M3 closed honestly; M4–M6 opened as A1–A3. Build-Rigor project reopened to house P3.
- 2026-09-12 — Git conventions + `reconciliation-terminal-charter.md` (PR #67); ADR numbers are minted from `main`; per-workstream worktrees created on demand, never parked detached.
- 2026-09-12 — Do **not** archive the Linear project "Empire State Hub" — it is the canonical hub tracker (YED-76/81/82/113 live there). ADR-7 Accepted (#69).
- 2026-09-11 — Content-quality rulings: variants = 3 · visual brief mandatory · ADR-6 brief placement · stance advisory-not-a-gate · A-tier ≥ 85; style guide v1.0 (pre→post arc).
- 2026-09-08 — Judge stays provisional until ~15 independent-first-look acks ≥ 80%; hold the bar as written.
- 2026-08-10 — One MI graph (YED-130): Empire's Supabase `oicikjyzmxqfomrrqkvf` hosts; gtm `signal.*` model won; gtm spine decommissioned (YED-135). ADR-0…4.
- 2026-08-07 — Canonical hub = `empire-state-hub`; Supabase is the MI system of record (REST, never the MCP; the ban survives only for the measurement layer); `/morning-refresh` auto-logs as an accepted Tier-2 exception.
- 2026-06-28 — Audience-first content north-star adopted (YED-103).

## 10. Shipped log (condensed; full history in git + the hub `/journal`)

- **2026-09-13 → 09-18** — YED-81 SEC & PII guardrail contract + `spine_client.py` write path (ADR-9, #73) · YED-161 inbox boundary mechanism (#74) + denylist v1 accepted (#75) · YED-166 slide↔recording alignment (#77) · YED-167 Postgres glossary + health review (#78) · ADR-10 Knowledge Substrate stub minted.
- **2026-09-12** — Reconciliation to single-source `main` (#60–#70): doc-KB Phase A + A.5 (YED-118/156) + YED-157 B1+B2 · Inbox Miner v1 (YED-153, ADR-7) · OBS capture lane (YED-154) · ADR-8 drift router (YED-158) · per-session telemetry shards (YED-159) · charter + git conventions (#67).
- **2026-09-04 → 09-11** — Job-Search Engine v1 (YED-146/147/148/150): me-model ICP, `target-companies.md`, role-radar rubric v2.4, Notion Roles DB; content-quality decision backlog cleared.
- **2026-08** — MI consolidation (YED-130) · topic-intelligence layer (YED-110/120/122) · progressive engine (YED-115/117/121) · Deep Read brief v2 (YED-136) · build journal (YED-119).
- **2026-06 → 07** — Build-Rigor & Measurement layer (YED-87…94, project Completed 2026-09-12) · cross-provider judge (YED-109) · M1 interview-prep (YED-105) · M2 dashboard (YED-106) · Empire State Hub M1–M6.

## 11. Pointers

- **Live status:** Linear (team Yedibalian) — projects: Market-Intelligence Engine · Job-Search Engine · Empire State Hub · Empire State Events · Build-Rigor & Measurement.
- **MI spine:** `market-intel-spine.md` · schema `market-intel-schema.sql` · taxonomy `signal-taxonomy.md` (→ v2 in P2).
- **Rigor:** `value-action-registry.md` · `cross-provider-judge.md` · `build-session-contract.md` · DoD in `CLAUDE.md` · `prd-template.md` · `linear-convention.md`.
- **Content:** `audience-north-star.md` · `content-style-guide.md` · `content-anti-patterns.md`.
- **Decisions:** `docs/adr/` (ADR-0…8) · **Git:** `reconciliation-terminal-charter.md` + CLAUDE.md "Git conventions" · **Workflows:** `.claude/WORKFLOWS.md`.
