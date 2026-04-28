# Signal Pipeline — Project Brief

**Purpose:** Single resume-from-cold doc for the Signal Pipeline project. Any future session (or Alex returning after a break) should be able to read this top-to-bottom and pick up exactly where we left off without rehashing prior conversation.

**Last updated:** 2026-04-21
**Status:** Phase 0 scaffolded (5 docs committed). Phase 0 execution blocked on MCP access from Claude Code CLI.
**Dev branch:** `claude/resume-strategy-planning-06kMr`

---

## What this project is

Two parallel workstreams that together move Alex from "NYC AI events content creator" to "Clay-tier full-stack GTM engineer candidate with a defensible portfolio":

- **Project A — Signal Pipeline** (this project). Long-running, iterative, internal. Builds an always-on signal layer that decouples content + outreach from IRL events, increases volume of high-quality specific material, and produces rung-1 (data foundation) + rung-2 (data modeling) portfolio assets along the way. The existing events pipeline is the *first completed module*, not something being rebuilt.
- **Project B — Hub** (sibling, lives at TBD path). Digital presence as canonical distribution surface. Framer v1 frontloaded sprint, 1–2 weeks of work, uses material that already exists. Parallel track; deliberately thin coupling with Project A.

This brief is scoped to Project A only. Project B will get its own brief when it kicks off.

---

## What's been decided (locked, don't relitigate without a flag)

| Decision | Value | Source |
|---|---|---|
| Project shape | Signal Pipeline (long-running) + Hub (parallel sprint) | Session 2026-04-20 |
| Events pipeline treatment | First completed module, NOT restarted | CLAUDE.md + cross-map |
| Enterprise-grade interpretation | Production-quality patterns applied proportionally — data contracts, schema rigor, idempotency, secrets hygiene, real logging, real evals on LLM parts. NOT Kubernetes-for-one-user | Session 2026-04-20 |
| 9-domain overlay mechanism | Hybrid: CLAUDE.md standing instruction + mandatory Roadmap Mapping sections in briefs + `roadmap-overlay.md` reference doc. Tiebreaker rule firm: build merits first, overlay is tiebreaker when alternatives equivalent or gap-flag when leaving a domain cold. Never primary driver. | Session 2026-04-20 |
| 9-domain overlay sequencing | Strategy+plan → details → overlay pass. NOT strategy built to pad domain coverage | Session 2026-04-20 |
| Phase 0 framing | Exploration, not build. Data inventory + signal discovery + hygiene spec | 2026-04-21 |
| Rung sequence | Foundation → Modeling → Activation. Don't skip to activation | Clay blog + session 2026-04-21 |
| Distribution V1 | LinkedIn only, human-in-the-loop approve-before-publish, 3–4 posts/week target | Session 2026-04-20 |
| Budget | <$100/mo additional spend. Revisit when we can name exactly what value is choked by lack of spend | Session 2026-04-20 |
| Data spine | Supabase free tier | Session 2026-04-21 |
| Workflow runtime | Vercel Workflow DevKit TABLED (bad docs / robustness issues from gtm-os experience). Decide later based on actual Phase 1 needs | Session 2026-04-21 |
| Hygiene workstream | First-class writeup with own living document and changelog | Session 2026-04-21 |
| Ethics rule | No LinkedIn scraping. No Twitter/X scraping. Public APIs, RSS, official endpoints, and Alex's own data exports only | Session 2026-04-21 |
| Watchlist approach | DO NOT construct a watchlist from external sources. Let existing data (what Alex has actually acted on) reveal the true watchlist | Session 2026-04-21 |

---

## What's been shipped in the repo

All in `Signal_Pipeline/Phase_0/`:

| File | Lines | What it is |
|---|---|---|
| `README.md` | 94 | Phase 0 overview, execution order, time-box, guardrails |
| `clay-play-patterns.md` | 151 | Modeling cheat sheet — Clay / Pocus / Common Room play anatomy translated to Alex's job-hunt funnel |
| `00_data_inventory_protocol.md` | 252 | How to audit the existing Notion + HubSpot + LinkedIn data |
| `01_signal_discovery_method.md` | 227 | Four-step method to derive signal seed list from Alex's acted-on history |
| `02_hygiene_tier_1_spec.md` | 315 | First-class living hygiene document (entity identity, provenance, contracts, dedup, suppression) |

Git status: all committed on `claude/resume-strategy-planning-06kMr` as of commit `e52e12a`, pushed to origin. No PR opened (per "don't create PRs unless asked" rule).

---

## Where we're blocked right now

**Blocker:** Notion + HubSpot MCP tools are not available in this Claude Code CLI session. They're listed in `STACK_README.md` as "Via Claude.ai" — meaning they're wired into the Claude.ai desktop app environment, not the CLI.

**Consequence:** Parts A (Notion inventory) and C (HubSpot inventory) of `00_data_inventory_protocol.md` cannot be executed from this session.

**Resolution path (confirmed with Alex, not yet executed):** Alex runs the inventory protocol in a Claude.ai desktop chat session where the MCPs are live. That session produces `inventory_findings.md` as markdown. Alex pastes it into this repo. Phase 0 then continues from there.

**What can happen in parallel in Claude Code CLI while waiting:**
- Skeleton of `inventory_findings.md` with tables pre-shaped, so the desktop session has a clean target to populate and we don't get format drift. (~20 min work. Awaiting Alex's go/no-go.)
- V0 draft of Step 1 of `01_signal_discovery_method.md` — the 30–50 candidate-signal enumeration — using docs + the 4 checked-in content artifacts as partial data. Explicitly marked as V0-pending-ground-truth. (Deferred; risk of generating work that gets revised once inventory arrives.)
- Small-sample audit of the 4 checked-in drafts and 1 brief — limited but real signal: named entities, content types, whether Success Signals were populated.

---

## Open questions / parked threads

Flagged explicitly so they get decisions rather than drift.

| # | Thread | Status |
|---|---|---|
| 1 | Relationship between `gtm-os` (active, PROJECT_BRIEF 2026-04-20) and Signal Pipeline — conceptual overlap, share infrastructure decisions | Flagged, not resolved. Decide before Phase 1 runtime choice |
| 2 | Relationship between `eval-harness` (active) and Signal Pipeline content evals — does eval-harness scope expand to cover Signal Pipeline? | Flagged, not resolved |
| 3 | Podcast / transcript ingestion | Deferred to Week 4–5 minimum. Brings vector store + RAG dependency |
| 4 | Full text of Clay blog + Pocus + Common Room pages | WebFetch 403's; if Alex wants full text fold-in, he can paste manually |
| 5 | Branch-name discrepancy | Resolved: stay on `claude/resume-strategy-planning-06kMr` |
| 6 | 9-domain overlay pass for the Phase 0 → Phase 1 plan | Sequenced for AFTER strategy + details are locked. Not due yet |
| 7 | Hub v1 build | Parallel track, not started. Framer brochure + 3 jobs-to-do + archive/history + projects body-of-work. Not blocked by Signal Pipeline |
| 8 | Is existing skill inventory fluency (gtm-agents catalog) being used? | Named as internalize-targets in cross-map. Not formalized as a learning plan. Revisit at domain-overlay pass |
| 9 | Entity-ID strategy across Notion ↔ Supabase spine | Decide at Phase 1 start |
| 10 | Conflict log location (Supabase table / Notion page / append-only file) | Decide at Phase 1 start |

---

## Outstanding to-dos, priority ordered

**P0 — blocks Phase 0 completion:**
1. **Run the data inventory** via Claude.ai desktop (Alex-led). Produces `Signal_Pipeline/Phase_0/inventory_findings.md`. Protocol spec is in `00_data_inventory_protocol.md`; it's self-contained.
2. **Part B — content performance audit.** Needs Alex's LinkedIn Creator Hub data and judgment on attributed DMs/outcomes. Not MCP-driven; manual work. Covered in §B of the inventory protocol.
3. **Part D — LinkedIn activity baseline.** Same constraint as Part B.

**P1 — runs after P0 completes:**
4. **Execute signal discovery method** (`01_signal_discovery_method.md` Steps 1–4). Produces `signal_seed_list.md`.
5. **Amend hygiene spec** with gap-specific entries surfaced by inventory. Add to `02_hygiene_tier_1_spec.md` changelog.
6. **Draft the R1 writeup** — "Event intelligence as a GTM signal layer" — the rung-1 + rung-2 portfolio asset named in the cross-map. Pulls directly from Phase 0 outputs.

**P2 — Phase 1 scoping (starts after Phase 0 exit):**
7. **Decide Phase 1 runtime** (n8n vs. Inngest vs. cron+scripts vs. Supabase edge functions). Vercel Workflow DevKit is tabled.
8. **Decide Notion ↔ Supabase relationship** (Notion stays as human workspace, Supabase is analytical spine — exact replication vs. write-both vs. one-way-sync). §3.3 of hygiene spec flags this.
9. **Write Phase 1 spec** — ingestion design for the 5–10 seed signals only, hygiene tier-1 implementation, R2 dashboard.
10. **Merge/coordinate with gtm-os + eval-harness** — the decisions above re: runtime and evals have to be made in light of what gtm-os / eval-harness are already doing.

**P3 — parallel (not blocked by Signal Pipeline):**
11. **Hub v1 (Project B)** — Framer brochure sprint. Separate brief when it kicks off.

**P4 — sequenced for later:**
12. **9-domain overlay pass** for the locked Phase 1 plan. After details are settled, not before.
13. **Phase 2 — first narrow activation play.** Comes after Phase 1 lands. Not scoped yet.

---

## Where we're going — the arc at 10,000 ft

```
Phase 0 — Exploration (NOW)
  └─ Inventory what exists
  └─ Discover signal from existing data
  └─ Formalize hygiene tier 1
  └─ Exit: signal_seed_list.md + inventory_findings.md + R1 draft

Phase 1 — Foundation + first modeling pass
  └─ Stand up Supabase spine
  └─ Implement hygiene tier 1
  └─ Ingest 2–3 signal types the seed list validated
  └─ R2 dashboard live (measurement layer BEFORE next content skill)
  └─ Exit: defensible rung-1 + rung-2 running in production

Phase 2 — First activation play
  └─ One narrow scored play
  └─ Defensible measurement plan
  └─ HITL approval step
  └─ Exit: first N1 capstone writeup, real data proving the play works or not

Phase 3+ — Iteration + new plays
  └─ Add signals as the data justifies them
  └─ Add activations one at a time
  └─ Eval harness over LLM-derived attributes (tier 3 hygiene)
  └─ Hub gets embedded live widgets here, not before
```

**Critical guardrails across all phases:**
- Do not ship a sixth content skill before R2 (measurement dashboard) exists. Clay red-flag #4.
- Do not conflate events pipeline with job-hunt funnel. Share Stages 1 and 4; different artifacts.
- Respect the active-project list in root `PROJECT_BRIEF.md` (gtm-os, eval-harness, scaffold-skill). Flag overlap explicitly when it appears.

---

## How to resume (concrete next action)

If you're Alex picking this up cold:

**Step 1 — Get unblocked.** Open Claude.ai desktop. Start a new chat. Give it this prompt:

> Read `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md` from my `Empire_State_Events_Pipeline_Take_3` repo (branch `claude/resume-strategy-planning-06kMr`). Then run Parts A (Notion inventory — all 4 sections) and Part C (HubSpot inventory — all 3 sections) against the live MCP connections. Produce `inventory_findings.md` in the format specified in Part E of that protocol. Report honestly — no fabricated numbers.

Paste the output into this CLI session, OR commit it directly to the repo and tell me the commit hash.

**Step 2 — Parts B and D.** Do these yourself, at your pace. Takes 30–60 minutes with LinkedIn Creator Hub open. The protocol describes what to capture. Low-precision is fine — flag it as low-precision in the writeup.

**Step 3 — Resume here.** Point me at the findings file. I'll execute signal discovery Steps 1–4, amend the hygiene spec with any gaps surfaced, and produce the R1 writeup draft.

If you're a future Claude session picking this up cold: read this whole doc, then `Signal_Pipeline/Phase_0/README.md`, then whichever Phase 0 file the next action targets. Don't reload everything; load on demand.

---

## Related docs

- `CLAUDE.md` — project-level standing instructions (root of repo)
- `PROJECT_BRIEF.md` — events pipeline + gtm-os/eval-harness/scaffold-skill active projects (root of repo)
- `Job Hunt System/02_cross_map_pipeline_to_roadmap.md` — the coverage matrix and R1–R5 + N1–N3 reframing that justifies this project
- `STACK_README.md` — tooling inventory (root of repo)
- `Signal_Pipeline/Phase_0/README.md` — entry point to the Phase 0 work
