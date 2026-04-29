# Signal Pipeline — Phase 0: Exploration

**Owner:** Alex
**Started:** 2026-04-21
**Status:** V0 scaffolded; execution pending.
**Parent project:** Signal Pipeline (Project A in the parallel-projects plan — Signal Pipeline + Hub).

---

## Why Phase 0 exists

The prior strategy draft jumped straight to a watchlist + source stack (rung-3 activation territory) without auditing what we already have or validating what signals actually matter for Alex's goal. That's the exact failure mode Clay's blog flags as "fancy campaigns on incomplete data." Phase 0 is the correction: **inventory what exists → discover what signal matters empirically → formalize the hygiene layer** — before any always-on ingestion is designed.

Mapping to Clay's three-rung maturity model:

- **Rung 1 — Data foundation:** Phase 0 produces the hygiene spec (`02_hygiene_tier_1_spec.md`). Phase 1 implements it.
- **Rung 2 — Data modeling:** Phase 0 produces the signal seed list by letting the existing data speak (`01_signal_discovery_method.md`). Phase 2 builds scoring on those signals.
- **Rung 3 — Data activation:** Phase 0 does not touch this. Don't start here.

---

## What's in this folder

| File | What it is | When to use it |
|---|---|---|
| `README.md` | This overview | Start here |
| `clay-play-patterns.md` | Modeling cheat sheet — Clay / Pocus / Common Room vocabulary and play anatomy, translated to Alex's job-hunt funnel | Reference when writing the signal seed list or any play design |
| `00_data_inventory_protocol.md` | How to audit the existing Notion + HubSpot + LinkedIn data | Execute first |
| `01_signal_discovery_method.md` | How to derive the signal seed list from the inventory findings | Execute after `00` |
| `02_hygiene_tier_1_spec.md` | First-class, living hygiene document (entity identity, provenance, contracts, dedup, suppression) | Living reference; revised continuously |

Artifacts we'll produce during execution (not yet written):

- `inventory_findings.md` — output of `00`
- `signal_seed_list.md` — output of `01`
- `signal_seed_list_changelog.md` — ongoing

---

## Phase 0 execution order

1. **Read the cheat sheet.** `clay-play-patterns.md`. 15 minutes. Establishes vocabulary for everything that follows.
2. **Run the inventory.** `00_data_inventory_protocol.md`. Target 3–4 hours. Produces `inventory_findings.md`.
3. **Run the signal discovery method.** `01_signal_discovery_method.md`. Target 6–8 hours spread over 2–3 days. Produces `signal_seed_list.md`.
4. **Review the hygiene spec against findings.** `02_hygiene_tier_1_spec.md`. Not rewritten; amended with any gap-specific entries in its changelog. Target 1 hour.
5. **Lock Phase 1 scope.** The signal seed list becomes the exact input for Phase 1 ingestion design. Nothing else gets built.

**Total Phase 0 time-box:** 1.5–2 weeks of part-time work, assuming Alex continues other commitments in parallel.

---

## What success looks like at Phase 0 exit

Four concrete artifacts in this folder:

1. `inventory_findings.md` with real numbers, not guesses.
2. `signal_seed_list.md` with 5–10 named signals, each with the five-box anatomy, each with historical precision from Alex's own data.
3. `02_hygiene_tier_1_spec.md` amended with any gap-specific additions based on what the inventory revealed.
4. One writeup draft (half a page) framing all three as a rung-1 + rung-2 portfolio piece for the hub. This is the seed for the R1 "event intelligence as a GTM signal layer" asset named in the cross-map.

What Phase 0 does NOT produce:
- Any ingestion code.
- Any Supabase schema.
- Any decision on workflow runtime.
- Any watchlist.

Those come in Phase 1, scoped to exactly what the seed list requires.

---

## Guardrails (per the project contract)

- **Do not restart the events pipeline.** It's the first and best signal source, already running. Phase 0 treats it as such.
- **Build merits first.** 9-domain overlay happens after Phase 0 → Phase 1 plan is locked, not during.
- **No LinkedIn scraping.** Public APIs, RSS, official endpoints, and Alex's own data exports only.
- **Budget < $100/mo additional spend.** Phase 0 should cost $0 — it operates on existing MCP connections and existing data.
- **Hygiene is first-class, living.** The hygiene spec is expected to iterate continuously. Don't try to freeze it; don't try to finish it.

---

## Related

- Parent context: `CLAUDE.md`, `PROJECT_BRIEF.md`
- Cross-map: `Job Hunt System/02_cross_map_pipeline_to_roadmap.md` (R1 / R2 writeup framing)
- Roadmap: `Job Hunt System/00_full_stack_gtm_roadmap.md` (Domains 3 / 4 / 5 are the highest-leverage targets this work hits)
- Skills inventory: `Job Hunt System/01_gtm_agents_skills_map.md` (Parts 0 — data-signal-enrichment, analytics-pipeline-orchestration, business-intelligence — are the fluency targets)

---

## Branch / commit discipline

All Phase 0 documents commit to the dev branch the session is working on (flag: current branch is `claude/resume-strategy-planning-06kMr` per the checkout; Alex referenced `claude/summarize-chat-session-aWoX3` in session context — reconcile before merging).

Each findings / seed-list document gets committed separately with a dated commit message (`phase-0: inventory findings [YYYY-MM-DD]`). The hygiene doc's changelog is updated in the same commit as any spec change.
