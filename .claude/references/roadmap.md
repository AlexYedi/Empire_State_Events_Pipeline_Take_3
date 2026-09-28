# Empire State — Roadmap & Plan of Record (v3 · adopted 2026-09-28)

## 1. How to use this file

**Read this before proposing work.** It is the one list for product direction, as of 2026-09-28.
Linear holds the open items (label `carry-over` for anything dated); this file holds direction.
**Single writer:** one session edits it at a time. §9–§10 are append-only history. v2's arc, programs,
quarter plan, anchors, kill list and pre-mortem are superseded; they live in git history.

## 2. North star and outcomes

**North star: the body of work generates inbound** — dated organizer, hiring-manager/recruiter or
speaker inbound attributed to a post or the corpus, hand-logged in `audience-north-star.md` the day it
happens. **Baseline:** 1 in 9 months (one organizer invite) ≈ 0.1/month; 0 hiring-manager activations.
**Target by 2027-03-27:** ≥6, ≥2 hiring-manager-class. <3 = "no information", not failure (§7).

| Outcome | Signal | Do-nothing baseline | Target |
|---|---|---|---|
| **O1 · Publishing mix follows performance** | Post-event share of published posts; class median vs overall | 26% (13/50); recap median 354 vs overall 262; roundup 197–272 | ≥50% by 12/12; class median ≥1.5× overall |
| **O2 · Rooms is the destination** | Vercel Web Analytics page views on `/rooms/*` with a LinkedIn referrer, per linked recap; inbound links | 0 links/post, 0 referred views, 0 inbound links | ≥10 referred views/linked recap by 12/12; ≥2 inbound links by 3/27 |
| **O3 · The search runs through the pipeline** (an outcome, not a forcing function) | Interviews referencing the hub/Rooms/posts; hours per application | 0 recorded; hours per hand-tailored resume | ≥1/month from Nov; <30 min via `/tailor-resume` |

## 3. Horizons (≤3 builds in flight; content runs are not builds)

### Now — October

| Item | Why | Size | Kill / continue test | Linear |
|---|---|---|---|---|
| Rooms link in the next two recaps | O2; recaps dead-end | S, no build | 10/28 (§4) | YED-241 |
| Speaker deep-dives: Postgres 10/9, LeadDev 10/16 | O1; 14 transcripts unmined | S, no build | ≥1 speaker reshare or ≥1.25× recap median by 10/30 → default | YED-243 |
| Roundup at 1 variant, 10/4–11/1 | O1; weakest format costs most | S, no build | 11/1 (§4) | YED-242 |
| The Shortlist recap-partner pitch, 10/10 | North star | S | yes/no by 10/24 | YED-244 |
| X cross-post test, 10/5–11/2 | Only unacted audience signal | S | 11/2 (§4) | YED-239 |
| Field Report mini-edition, Oct 20–24 | O1 + north star | M, content | 11/7 (§4) | YED-126 |
| LinkedIn analytics export | Audience claims unmeasured since 8/25 | S, manual | by 11/15, or stop claiming segment reach | YED-247 |
| Confirm Vercel Web Analytics reads `/rooms/*` views + referrer (shipped with Rooms; no new tool) | 10/28 needs a denominator | S | reads by 10/14, else readout is links-only | — |
| `/tailor-resume`, on demand | O3 | S, ≤1 d | 2nd use <30 min | YED-151 |

### Next — Nov → Dec 12

| Item | Why | Size | Kill / continue test | Linear |
|---|---|---|---|---|
| Field Report #1 (one theme, corpus-wide, cited) | O1 + north star | M | ≥2× recap median saves+reshares or ≥1 speaker/HM DM by 12/5 → quarterly | YED-126 |
| Theme → prior-post index (flat Notion view) | Back-links compound | S, 1 h | used in ≥3 posts by 12/12 | YED-178 |
| C-5 "Who's hiring commercial AI roles in NYC, scored", one post | O3 as content | S | HM inbound or ≥1.25× median → monthly | — |
| Rooms v1.1: search, speaker tags | O2 | M | only after positive 10/28; ≥1.5× views over 3 recaps | — |
| Second organizer pitch | North star | S | one yes by 12/12 | — |
| Selective HubSpot pass (~10–15, create-once) | CRM for people met | S | one pass | YED-238 |
| Dec 12 prep: graph-consumer tally + review | Gate for Later | S | §4 | — |

### Later — Jan → Mar 2027 (all conditional on Dec 12)

| Item | Size | Kill / continue test |
|---|---|---|
| Field Report #2 | M | same bar; two misses kill the format |
| C-8 pre-read audio, 3 episodes | S ×3 | completions + any "I listened" reply |
| `/interview-prep` reads Rooms + transcripts (replaces YED-207) | S | used in 2 dossiers |
| C-2 one chart: companies on NYC stages × open commercial AI roles | S | reposts by named companies |
| Taxonomy v2 + hub panels (YED-126, YED-114) | L | a named reader beyond Alex |
| Organizer partnership formalized | S | credit or stage slot by 3/27 |

## 4. Decision dates

- **10/24** Shortlist answer: yes → second pitch; no → park C-6 until a second organizer inbound.
- **10/28** Rooms readout: ≥10 referred views/recap → v1.1 in Nov, C-8 eligible Jan; else Rooms static.
- **10/30** Deep-dives → default Step 5.6 output, or opt-in.
- **11/1** Roundup: within ±0.10 of the 3-variant median → lean permanently; >25% worse → revert.
- **11/2** X: ≥5 builder follows/replies or 1 invite → keep; else drop.
- **11/7** Field Report mini → full #1, or the format is dead and YED-126 closes "shipped as content".
- **11/15** LinkedIn export → per-format demographics; else O1 measured on format only.
- **12/12 · MI graph go/no-go.** Go = ≥2 human-facing consumers read the graph (substrate pull, role-radar, interview prep) and ≥1 produced a published post or an application; baseline: substrate pull only. Go → scoped to the job lens; YED-179 and YED-126 infra eligible on a friction seen twice. No-go → freeze DDL and non-role producers; Supabase = read-only passive store.
- **12/12** Quarter review, O1–O3 vs baselines. **1/15** Field Report #2 go.
- **3/27** Six-month review: ≥6 growth · 3–5 hold · <3 format review (not instrumentation).

## 5. Idea portfolio (re-ranked 2026-09-28; replaces the 59-row census)

**Build next:** Field Report mini → #1 → #2 (C-1) · `/tailor-resume` (YED-151) · YED-178 index · Rooms v1.1 after 10/28 · `/interview-prep` on Rooms at the 2nd interview.

**Test cheaply first:** C-4 deep-dives · C-6 Shortlist · C-7 X · roundup lean · C-5 one post · C-2 one chart (if C-5 gets saves) · C-8 audio (Jan) · a "since last time" recap paragraph from the nightly recompute · deep-dive → speaker DM with the Rooms link (4 sends) · YED-238 · YED-220 items 1–2 as two paragraphs.

**Parked (trigger):**
- YED-208 content lens → manual index fails after ~10 posts · YED-207 → Dec 12 go + Rooms prep insufficient twice.
- YED-126 / YED-114 → #1 readers + Dec 12 go + a second viewer · YED-179 → Dec 12 go + friction twice · YED-249 → Dec 12 go.
- YED-233 backfill, YED-186 → a consumer · YED-65 Clay → first warm-outreach friction.
- YED-48 → brief regression twice · YED-191 → a public misspelling · YED-182 → a sandbox section in a report · YED-226 / YED-47 → dedup probe >0 pairs.
- YED-76 → a second viewer · Brief Pulse → a weekly question Notion can't answer · YED-235 → a book quoted in two posts · project ideation → one idea ships · GTM University → GTM-OS calendar.

**Killed:** P3 "The Loop" / Rigor v2 (YED-162) · ADR-8 Increment 2 (YED-163) · measurement → plugin promotion · the streaming cluster (Signal Desk, Signal Stream, GTM Situation Room, Ask-the-Stream, M2 dashboard, `/scan-trends` YED-180, `/morning-refresh`) · YED-104 · YED-234, 181, 145, 194, 192, 137, 113 · Phase 3 intake form · Stage 1 qualifier · `project-complete` · `/ops/ideas` + `/ops/backlog` · YED-219 as a gated magnet · the 8 portfolio demo builds · a newsletter.

## 6. Removal queue (tail of the 2026-09-28 prune)

1. Delete `.claude/hooks/second-fix-nudge.sh`.
2. `.claude/skills/doc-knowledge-base/` helpers → one `dockb_common.py` in `.claude/scripts/`.
3. Fix 10 stale references in `.claude/evals/`.
4. `.claude/scripts/spine_client.py` ~line 348 stale message (guarded: Alex reviews).
5. `pre-event-content`: renumber around "Step 5 retired".
6. Fold `.claude/skills/update-anti-patterns.md` into `update-voice-and-style`.
7. Archive the Linear Build-Rigor project · clear local `.state` scratch.
8. Hub `/ops/content-performance`: refresh or drop (waits on YED-247).
9. Rename Notion "Project Ideas" → "Specs & Ideas".

After this queue: **one-in-one-out.**

## 7. Guardrails and the biggest risk

1. **No new stores:** no Supabase DDL before a Dec 12 go; no new Notion DBs; no mailing list.
2. **No meta regrowth:** ≤3 hooks; no dashboards, judge seats, eval harness or telemetry surfaces; analytics = Vercel Web Analytics only.
3. **No hub build without a readout;** no new `/ops` pages.
4. **No backfills without a consumer.** Role-radar rubric frozen to ~10/27.
5. **Don't reopen** Clarify, Gamma, OBS, judge quorum, the no-build window, the roundup's brief-only source, the substrate A/B.
6. **Contracts hold:** 3 variants, Notion first, source-check claims, scheduled posts frozen, HubSpot selective/create-once, recorded speech never public.
7. **Employment is measured (O3), never forced.**

**Risk:** the north star is lagging and rare (0.1/month), inviting premature kills or a regrown
measurement layer. **Mitigation:** every §4 decision reads a 2–4-week leading proxy; inbound is
hand-logged. If publishing falls below 2 posts/week for 3 weeks: maintenance mode, and Dec 12 defaults
to no-go. Confidence in the sequence: 65% (n=7–9 per cell; three of four Now tests are firsts).

## 9. Decision log (dated; append, never edit)

- **2026-09-28 — Roadmap v3 adopted (this file).** P3 loop killed; A1 met in reduced form: live producers are post-event claims (YED-160), research-brief claims and roles (role-radar Step 5.5, YED-149, the largest); the inbox (ADR-11) and trend producers are retired; Dec 12 go/no-go criteria in §4; analytics = Vercel Web Analytics (PostHog removed).
- **2026-09-28 — Carry-overs** live in Linear (label `carry-over`, due date, Who/What/When/Why/Context), rendered on the hub `/ops/todos`.
- **2026-09-28 — Recorded speech never public;** affected history purged.
- **2026-09-28 — Rooms shipped** on the hub, with Vercel Web Analytics.
- **2026-09-28 — Inbox lane retired (ADR-11).** Judge = one on-demand Sonnet reviewer by artifact class (YED-231).
- **2026-09-28 — Complexity reset:** the pipeline is the product; meta layer cut; `CLAUDE.md` ≤1,800 words, ≤3 hooks, one-in-one-out.
- **2026-09-18 — Oct-9 decisions ruled (Alex).** YED-128 **folded** into YED-168 (migrations become the spine's source of truth by construction; acceptance lines carried). YED-175 systems diagnostic **dropped** — the reconciliation is the intervention; reopen only if the container-rule audit trends up. YED-34 **re-scoped from delete to audit-and-place** after inspection (108 agent + 102 command files of real role content; promote the dispatch-worthy 10–20 to plugin root, fold the rest into umbrella skills as personas/references; delete nothing).
- **2026-09-18 — Four Oct-2 decisions ruled (Alex, on recommendation).** YED-129: **product = PRD, infra = spec** — ADRs/in-repo references are the spec artifact for infra; the three pending PRD mirrors (judge, ADR-8, inbox-miner) are closed as "ADR is the spec". YED-173: Content Pipeline v2 Stage 2 **killed as a unit** (parts absorbed: schemas → YED-168, eval gates → YED-48/judge, status automation behind the YED-23 flip). YED-174: YED-30 Step 5 CLAUDE.md canonical backport **approved** — execute in a fresh session after PR #79. YED-176: **Gemini fallback stays the default**; no Anthropic key until a scripted Claude call is on the runway.
- **2026-09-18 — Backlog reconciliation.** Container rule ratified (`linear-convention.md`); ~170 inventory items triaged (`docs/archive/notes/backlog-triage-2026-09-18.md`) into 9 decisions (YED-128/129/34/173–176), ~20 new issues (YED-177–197), merges, and deletions; ADR-8 Amendment 3 (Increment 4); `GTM-OS` Linear team created and the 11 gtm-OS issues moved (GTM-1…11); labels `parked`/`decision` live. Prioritization (step 2) runs on the clean board.
- **2026-09-13 — GTM University un-parked (GTM-1, formerly YED-164; reverses the §7 park, Alex's call).** Re-aimed against a *Staff AI Engineer, GTM* JD as a **north-star benchmark, not a pivot** — me-model §1.5 (commercial IC search) stays primary. v2 is add-only (v1 unit ids kept: +28 sub-tasks for oversight design, transcript-analysis evals, observability/ROI, Agent SDK + governed MCP, production engineering, inner-source, experimentation, explainable scoring) plus a sequenced 10-stage path; lives in gtm-os-hub. Overlap with P3 (YED-48 eval harness, YED-109 judge, YED-162 loop) is intentional — those builds count in both places.
- **2026-09-12 — v2 adopted.** §7 ratified; YED-81 re-raised to High and scoped as contract + write-path; the third MI lens = the architecture lens (YED-126). M3 closed honestly; M4–M6 opened as A1–A3. Build-Rigor project reopened to house P3.
- 2026-09-12 — Git conventions + `reconciliation-terminal-charter.md` (PR #67); ADR numbers are minted from `main`; per-workstream worktrees created on demand, never parked detached.
- 2026-09-12 — Do **not** archive the Linear project "Empire State Hub" — it is the canonical hub tracker (YED-76/81/82/113 live there). ADR-7 Accepted (#69).
- 2026-09-11 — Content-quality rulings: variants = 3 · visual brief mandatory · ADR-6 brief placement · stance advisory-not-a-gate · A-tier ≥ 85; style guide v1.0 (pre→post arc).
- 2026-09-08 — Judge stays provisional until ~15 independent-first-look acks ≥ 80%; hold the bar as written.
- 2026-08-10 — One MI graph (YED-130): Empire's Supabase `oicikjyzmxqfomrrqkvf` hosts; gtm `signal.*` model won; gtm spine decommissioned (YED-135). ADR-0…4.
- 2026-08-07 — Canonical hub = `empire-state-hub`; Supabase is the MI system of record (REST, never the MCP; the ban survives only for the measurement layer); `/morning-refresh` auto-logs as an accepted Tier-2 exception.
- 2026-06-28 — Audience-first content north-star adopted (YED-103).

## 10. Shipped log (condensed; full history in git + the hub `/journal`)

- **2026-09-28** — Complexity reset: dead surface pruned, lean `CLAUDE.md`, one-reviewer judge (YED-231), ADR-11, Supercut replaces OBS, Rooms live, nightly topic recompute, carry-overs, roadmap v3.
- **2026-09-19 → 09-27** — Knowledge Substrate: S1a/S2 migrations live on prod, **ADR-10 Accepted 2026-09-27 with Amendment 1** after the A/B (YED-172) split verdict (material: substrate; packaging: legacy) · post-event → MI producer (YED-160) + backfill through the producer (YED-171) · event-namespace single-writer + graph-write freeze enforced at the one write path (YED-213/214) · conditioner aims claims at named speakers + question claims first-class (YED-217/218) · third judge seat + null-baseline registry contract (YED-209/212) · role-radar: no-technical-roles scope (YED-221), comp-gate rules for every posting shape (YED-210), Roles DB hygiene (YED-224) · backlog reconciliation closed (YED-199).
- **2026-09-13 → 09-18** — YED-81 SEC & PII guardrail contract + `spine_client.py` write path (ADR-9, #73) · YED-161 inbox boundary mechanism (#74) + denylist v1 accepted (#75) · YED-166 slide↔recording alignment (#77) · YED-167 Postgres glossary + health review (#78) · ADR-10 Knowledge Substrate stub minted.
- **2026-09-12** — Reconciliation to single-source `main` (#60–#70): doc-KB Phase A + A.5 (YED-118/156) + YED-157 B1+B2 · Inbox Miner v1 (YED-153, ADR-7) · the since-retired OBS capture lane (YED-154, replaced by Supercut 2026-09-28) · ADR-8 drift router (YED-158) · per-session telemetry shards (YED-159) · charter + git conventions (#67).
- **2026-09-04 → 09-11** — Job-Search Engine v1 (YED-146/147/148/150): me-model ICP, `target-companies.md`, role-radar rubric v2.4, Notion Roles DB; content-quality decision backlog cleared.
- **2026-08** — MI consolidation (YED-130) · topic-intelligence layer (YED-110/120/122) · progressive engine (YED-115/117/121) · Deep Read brief v2 (YED-136) · build journal (YED-119).
- **2026-06 → 07** — Build-Rigor & Measurement layer (YED-87…94, project Completed 2026-09-12) · cross-provider judge (YED-109) · M1 interview-prep (YED-105) · M2 dashboard (YED-106) · Empire State Hub M1–M6.

## 11. Pointers

- **Open items:** Linear (team Yedibalian; `carry-over`, `parked`) · hub `/ops/todos`.
- **Content:** `audience-north-star.md` · `content-style-guide.md` · `content-anti-patterns.md` · `outreach-templates.md`.
- **Discipline:** `.github/pull_request_template.md` · `judge.md` · `second-fix-stop-rule.md` · `linear-convention.md` · `build-in-public.md`.
- **MI graph:** `market-intel-spine.md` · **Decisions:** `docs/adr/` · archive: `docs/archive/` · **Workflows:** `.claude/WORKFLOWS.md`.
