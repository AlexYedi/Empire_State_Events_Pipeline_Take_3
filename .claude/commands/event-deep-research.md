---
description: "Workflow A — full event research pipeline. Parses a pasted calendar invite, runs entity triage, fans out 4 parallel research subagents from this conversation, dispatches synthesizer for the brief, and writes to Notion + HubSpot. Replaces the monolithic event-research skill flow with a multi-agent architecture."
argument-hint: "[paste calendar invite text after the command]"
---

# /event-deep-research — Workflow A

Run the full event research pipeline using multi-agent fan-out **from the parent thread** (the slash command's main conversation). Subagents cannot dispatch sub-agents per Anthropic SDK design, so the parent owns the fan-out and a downstream synthesizer assembles the final brief.

**Input:** pasted calendar invite text (or invite + Alex's natural-language context like "Speaker: Jane Smith, CTO at Acme; Topics: agentic systems, enterprise AI").

**Output (ADR-5 — one artifact, two layers):**
- The **Scan head** of the research brief presented in conversation for Alex's review (in-room layer: Quick Take · People at-a-glance · Questions to ask · Success Signals · Verification Flags)
- Once approved → all 5 Notion DBs written (Companies, Topics, People, Events, Content Drafts) + HubSpot CRM (Companies, Contacts with associations, Notes)
- Then, **decoupled and additive**, the prose **Deep Read** (~45-min commute read) is rendered section-by-section by `field-guide-renderer` (Opus) and **appended** beneath the Scan head on the Event page + `research_brief` Content Draft. A render failure never blocks the pipeline.

---

## Trigger

This command runs when:
- Alex pastes a calendar invite and wants research
- Alex types `/event-deep-research` followed by invite text
- Alex says "research this event" / "deep research on [event]" / "run the event pipeline"

## Required inputs

1. **Event invite text** — pasted invite description, or natural-language description with speaker/host/topic cues
2. **(Optional) Google Calendar Event ID** — if the input includes a `Google Calendar Event ID:` line (as `/check-new-events` always passes), capture it and forward to `notion-writer` for the Events DB row. This is the deterministic join key to Granola for `/post-event-content`.
3. **(Optional) Stated focus** — if Alex says "I'm going to find a hiring manager" or "I want to test my POV on agentic systems", pass that downstream so Success Signals are tailored

## Step 1 — Parse and triage (this conversation, NOT a subagent)

Run **Steps 1, 1.5 of `.claude/skills/event-research/SKILL.md`** in this conversation:

1. Parse the invite into entities (Event, People, Companies, Topics)
2. Confirm entities with Alex
3. Run dedup search against Notion (5 DBs) per the canonicalization rules
4. Classify each entity: NEW / REFRESH-light / REFRESH-full / SKIP / APPEND-CURRENT-EVENTS-ONLY
5. Present triage plan to Alex for approval
6. Apply Alex's overrides (if any)

**Do NOT delegate this step.** Building the triage plan requires conversation with Alex.

**Preserve the raw description verbatim (added 2026-06-23 — fidelity fix).** Parsing into entities is LOSSY: it is a summary. Keep the full, unedited invite/`description` text as a `VERBATIM SOURCE` block and carry it forward to Step 2 unchanged. The entity list is an *index* into the source, NOT a replacement for it. Never let a downstream agent see only the summarized entities — talk abstracts, named themes (e.g. "partnerships", "go-to-market strategy"), attendee mix, and ordering nuance live in the raw text and are invisible once compressed. Root-cause of a 2026-06-23 defect where all outputs were built off a lossy summary.

## Step 1.7 — Prior-knowledge retrieval + conditioning (this conversation + a distiller subagent)

Before fan-out, load what the pipeline already knows about these entities so research **compounds** instead of restarting from web search every run. Run **Step 1.7 of `.claude/skills/event-research/SKILL.md`**:

1. **1.7a Retrieve (this thread — MCP reads must run in the parent):** for entities **with a prior record** (from the Step 1.5b dedup — pure-NEW entities are skipped here and researched from scratch in Step 2), pull prior Event brief bodies, People/Companies page bodies, Topics `Current Events` (newsletter/trend notes), Gmail correspondence + `label:Content/newsletters newer_than:14d`, and Supabase graph `market` signals over REST (`SUPABASE_API_KEY` from `.env`, **never** the MCP — see `.claude/references/market-intel-spine.md`). **Follow the enforced cost-guard procedure in SKILL Step 1.7a:** skip-no-prior → rank (event-series brief > returning people > companies with recent developments > topics) → hard-cap **N=8** → emit the mandatory audit line (`pulled · skipped-no-prior · capped/not-pulled · graph`) before dispatching the conditioner. **The graph read is best-effort:** `curl --max-time 8`; on non-2xx / timeout / empty, record `graph: no signals` and continue — never block or retry-loop.
2. **1.7b Condition (delegated):** dispatch `knowledge-conditioning` with the `VERBATIM SOURCE` block + triage plan + all raw pulls. It returns the **Prior-Context Pack** — relevance-filtered, provenance-tagged (`KNOWN` / `STALE` / `UNVERIFIED` + `[source · date]`), with a Continuity Ledger, per-entity cards, Graph Signals, and an Audit. Text-in / text-out; no I/O.
3. **1.7c Persist (this thread):** write the pack as a `prior_context_pack` Content Draft (`Platform: notion_only`, icon 🗃️) so "what prior knowledge fed this brief" is auditable. `notion-writer` relinks it + mirrors a `## Prior-Context Pack` section onto the Event page in Step 4.

**First-touch event (no prior record for any entity):** skip 1.7b/1.7c, note it, and run Step 2 from scratch. The graph read commonly returns empty until event-research write-back ships — expected, not a failure.

**Verify-first (the discipline):** the pack is prior context, never current fact. Downstream readers treat `KNOWN` as a foundation and `STALE` / `UNVERIFIED` as leads to refresh/verify; nothing stale or unsourced flows into the brief as fact (CLAUDE.md Rule 12).

## Step 2 — Multi-agent research fan-out (this conversation)

Once triage is approved, **dispatch all four specialists in parallel from this thread** via a single message containing four `Agent` tool calls. This must run in the parent thread because subagents cannot spawn other subagents (Anthropic SDK runtime constraint — see [code.claude.com/docs/en/sub-agents.md](https://code.claude.com/docs/en/sub-agents.md): *"Subagents cannot spawn other subagents. If your workflow requires nested delegation, use Skills or chain subagents from the main conversation."*).

The four parallel dispatches:

1. **company-researcher** — every Company entity that needs research (NEW or REFRESH). Pass the entity list scoped to this specialist + their triage paths + Alex's stated focus.
2. **person-researcher** — every Person entity that needs research (NEW or REFRESH). Skip the dispatch entirely if no people are named or all are SKIP.
3. **topic-landscape-analyst** — every Topic entity (NEW, REFRESH, or APPEND-CURRENT-EVENTS-ONLY). Topics never get full SKIP.
4. **competitive-signal-scanner** — runs across ALL companies (including SKIP) to surface market signals in last 60 days.

For each specialist, pass: **(1) the full `VERBATIM SOURCE` description block from Step 1, quoted unchanged and labeled as the source of truth** ("read every line; derive findings from THIS text — the framing below is supplementary, not a replacement"); (2) the entity list scoped to that specialist; (3) the triage path per entity; (4) the event name + date; (5) Alex's stated focus; **(6) that specialist's slice of the Step 1.7 Prior-Context Pack** — Companies cards → company-researcher; People cards → person-researcher; Topic cards → topic-landscape-analyst; Graph Signals + Continuity Ledger → competitive-signal-scanner — with the standing instruction: treat `KNOWN` as starting context, `STALE` / `UNVERIFIED` as leads to refresh/verify via web search, and never restate `UNVERIFIED` as fact. Omit (6) for a first-touch event or for specialists whose slice is empty.

**Mandatory (fidelity fix, 2026-06-23):** the verbatim description is item (1) for a reason — it goes in EVERY specialist dispatch, ahead of the entity list. Do NOT paraphrase it into the prompt and drop the original. If the parent only hands subagents the summarized entity list, the run repeats the defect where talk-abstract nuance and named-but-unsummarized themes never reach research. The Step 2.5 synthesizer also receives the raw invite — keep that.

**Return contract (added 2026-08-21 — YED-136):** each specialist now returns, alongside its prose blocks, (a) a **historical spine** (topic lineage / company founding→funding→evolution arc / person career arc — facts + dates), (b) **mechanism + jargon** material for the novice on-ramp, and (c) a per-entity **Evidence Ledger** — every specific/recent/contestable claim as a `tier · source · url · date` row. These feed the Deep Read render loop (Step 4.5); the URLs are mandatory for `web-verified` rows (the spike caught that missing URLs break endnotes). Preserve them when handing returns to the synthesizer.

Wait for all four to return before proceeding to Step 2.5. If a specialist returns thin output, re-invoke just that one with deeper scope — do not restart the whole fan-out.

## Step 2.5 — Synthesis (delegated to event-research-synthesizer)

Invoke the synthesizer subagent with all four specialist returns plus the triage plan and raw invite:

```
subagent_type: event-research-synthesizer
prompt: [event invite + triage plan + Alex's stated focus + all 4 specialist returns + the Step 1.7 Prior-Context Pack (Continuity Ledger + Graph Signals especially)]
```

The synthesizer:
1. Reconciles cross-references (signal-scanner findings vs. company-researcher findings)
2. Surfaces verification flags from specialists (mismatched domains, ambiguous identities)
3. Writes Quick Take, Success Signals, and assembles the **Scan head** (Quick Take · People at-a-glance · Questions to ask · Success Signals · Verification Flags) per event-research SKILL.md Step 3 — **NOT** the old topic/company lattice
4. Emits a `## Evidence Set` — URL-carrying, organized by Deep-Read render section — as internal fuel for Step 4.5 (do NOT display it to Alex as brief content)

The synthesizer returns **two blocks** (Scan head + Evidence Set) as text. **No Notion / HubSpot writes happen yet.** Hold the Evidence Set for Step 4.5 — preserve its URLs.

## Step 3 — Present brief for Alex review

Display **only the Scan head** from the synthesizer (the Evidence Set is internal — keep it for Step 4.5). Wait for Alex's approval.

Alex may request:
- Add or remove people / companies → restart from Step 1 with adjusted entity list
- Adjust research depth on specific entities → re-invoke that specific specialist (just that one) with deeper scope from this thread, then re-dispatch synthesizer with the updated returns
- Correct factual errors → patch the brief in conversation
- Add context that web search didn't surface → patch the brief in conversation

Iterate until Alex says "write it" / "proceed" / "looks good".

## Step 4 — Notion writes (delegated)

Invoke notion-writer subagent:

```
subagent_type: notion-writer
prompt: [approved brief + triage plan + raw invite text + today's date + Google Calendar Event ID (if captured in Step 1)]
```

notion-writer executes Steps 4a–4g of `.claude/skills/event-research/SKILL.md`:
- Companies (parallel-safe with Topics) → capture URLs
- Topics (parallel-safe with Companies) → capture URLs
- People (uses Company URLs) → capture URLs
- Event (uses People + Companies + Topics URLs) → capture URL
- Content Draft "[Event Name] — Research Brief" (uses Event URL)

Returns the confirmation block from Step 4g. The Event page + `research_brief` Content Draft now hold the **Scan head** plus an empty `## Deep Read` section carrying `<!-- deep_read_rendered: pending -->` — Step 4.5 fills it.

**Record the Deep Read ledger row (YED-139 — mandatory, do not skip).** The moment notion-writer returns the Event page URL/ID, register it in the per-session Deep Read gate ledger, defaulting to PENDING:

```
.claude/hooks/deep-read-ledger.sh add "<event title>" "<Event page id or URL>"
```

This is co-located with the Scan-head commit on purpose: the row is written **pending by default** and only flips to `rendered` on a successful Step 4.5 (below). The Stop-hook gate (`deep-read-gate.sh`) fails the run at close if any row is still pending — so a silently-skipped Deep Read cannot close green. Skipping this `add` is the one way to defeat the gate; it is as mandatory as the Notion write it sits beside.

## Step 4.5 — Render + append the Deep Read (this conversation — decoupled, additive)

**Only after Step 4 committed the Scan head (4g).** Run **Step 4.5 of `.claude/skills/event-research/SKILL.md`** in this conversation (the render dispatches and the Notion append both happen here — MCP writes are parent-thread only). This phase is **non-blocking**: a render failure is a warning, never a pipeline failure — the Scan head + entity records are already committed.

1. **Assemble slices (4.5a)** from the synthesizer's `## Evidence Set` (held from Step 2.5) — one URL-carrying evidence slice per Deep-Read section + event meta + Alex's focus + novice level.
2. **Render section-by-section (4.5b)** — dispatch `field-guide-renderer` (Opus) **once per section**, in order: The Frame → Primer/Landscape → Companies → People → Cross-Event Threads. Skip a section whose evidence slice is empty (no people → skip People; first-touch → skip Cross-Event Threads). **One section per call** — never ask for the whole Deep Read at once. Surface any `> Gap:` notes the renderer flags.
3. **Stitch (4.5c)** — dispatch `field-guide-renderer` in `stitch` mode with all rendered sections → the final Deep Read (opener + smoothed transitions + consolidated endnotes; no fact/citation added or removed).
4. **Append (4.5d)** — inline `notion-update-page` (real newlines, gotcha m): replace the `## Deep Read` section on **both** the Event page and the `research_brief` Content Draft with the stitched Deep Read; flip the marker to `<!-- deep_read_rendered: [today] -->`. Idempotent — a re-run replaces only that section. **On success, flip the ledger row too (YED-139):**
   ```
   .claude/hooks/deep-read-ledger.sh rendered "<Event page id or URL>"
   ```
   This clears the pending state the Stop-hook gate checks. Do it only after the Notion append actually succeeded.
5. **Confirm / warn (4.5e) — fail LOUD.** On total render failure, leave the marker `pending` and emit an explicit `⚠️ DEEP READ PENDING — [event]` line in this run's output (and, under `/check-new-events`, in the Step 7 batch summary's "Deep Read PENDING" block) so a thin, Scan-head-only brief is never mistaken for a finished one. **Leave the ledger row `pending`** (do NOT flip it) — the Stop-hook gate will FAIL the run at close, which is correct. Offer to re-run just Step 4.5 (idempotent). Only if Alex *explicitly accepts* shipping this event Scan-head-only for now, record the acknowledgement so the gate reports it as waived rather than failed:
   ```
   .claude/hooks/deep-read-ledger.sh waive "<Event page id or URL>" "<reason, e.g. renderer unregistered this session>"
   ```
   In batch/autonomous mode a `pending` marker is a **tracked incomplete that must appear in the final summary** — silent degradation to the Scan-head-only brief is the exact regression this step guards against (it is how the entire Aug-2026 Shortlist/AWS/Spark/GTM-Leaders batch shipped thin).

**Registry note:** `field-guide-renderer` is session-frozen like every subagent — if this run predates the agent's registration, the render loop won't dispatch it; run the pipeline in a fresh conversation.

## Step 5 — HubSpot writes (this conversation)

Run **Step 5 of `.claude/skills/event-research/SKILL.md`** in this conversation. The HubSpot MCP requires confirmation tables before each create — easier to handle inline with Alex than via subagent.

1. Recurrence check (5.0)
2. Create / refresh Companies (5a)
3. Create / refresh Contacts with company associations (5b)
4. Create Notes per contact with event name as body (5c)
5. Confirm writes (5d)

## Step 6 — Final summary

Present the Step 6 summary block from event-research SKILL.md (Notion + HubSpot results + next steps).

## Step 6.5 — Deep Read gate (run close — YED-139)

Before declaring the run complete, run the authoritative marker check (this is the in-conversation half of the gate — it reads the *real* Notion state, complementing the Stop-hook ledger check):

1. **Enumerate touched Event pages** — from the ledger (`.claude/hooks/deep-read-ledger.sh list`) plus this run's own record.
2. **Re-fetch each marker** — `notion-fetch` the Event page and read its `<!-- deep_read_rendered: [date|pending] -->` marker. This catches any drift between the ledger and Notion (the ledger is a local echo; Notion is the truth).
3. **Verdict:**
   - **All `rendered` (or explicitly waived)** → run passes; report Deep Read ✅.
   - **Any `pending`** → the run is **NOT complete**. Interactive: **block close** — present the pending event(s), offer the idempotent Step 4.5 re-run, and do not report the run as done. Autonomous/batch: report the run **FAILED** with the pending list (never a silent pass).
4. Reconcile the ledger with what you found (flip `rendered` / `waive` as appropriate) so the Stop-hook gate agrees with the authoritative Notion state.

This step and the Stop-hook `deep-read-gate.sh` are belt-and-suspenders: the hook fires even if this step is skipped; this step reads real Notion state and gives the interactive block.

---

## Workflow chain (what comes next)

After `/event-deep-research` completes successfully, common follow-ons:

| Want to... | Run |
|---|---|
| Generate pre-event content (LinkedIn posts, DMs, prepared questions) | `pre-event-content` skill — pulls research brief from Notion |
| Generate project ideas to build before the event | `project-ideation` skill — pulls topics + event from Notion |
| Capture retro after attending | Step 7 of `.claude/skills/event-research/SKILL.md` (handoff to `content-correspondent` for post-event content) |
| Synthesize multiple events from this week into one post | `pattern-synthesis` skill (needs ≥2 briefs) |

See `.claude/WORKFLOWS.md` for the full picture of how the four workflows interrelate.

---

## Failure modes (specific to multi-agent runs)

- **Specialist returns thin output** — re-invoke that one specialist from this thread with deeper scope or more specific direction. Re-dispatch synthesizer with updated returns. Don't restart the whole orchestration.
- **Parent times out during fan-out** — split: dispatch company-researcher + person-researcher in one batch, topic-landscape-analyst + competitive-signal-scanner in another, then dispatch synthesizer with all four returns merged.
- **Triage plan disagreement post-hoc** — if while reviewing the brief Alex realizes an entity should have been REFRESH instead of SKIP, re-invoke just the relevant specialist with the corrected path; don't restart the whole flow.
- **notion-writer hits a schema validation error** — the live Notion schema is authoritative. Use the API error text to fix the property value, retry. Per CLAUDE.md gotcha (e), verify with notion-fetch on the data_source URL if it persists.
- **notion-writer fails with "Prompt is too long"** — its `tools:` whitelist may have drifted to inherit too much. Verify `.claude/agents/ops/notion-writer.md` frontmatter still scopes `tools:` to Notion MCP + Read only.
- **Deep Read render fails (Step 4.5)** — this is **decoupled by design**: warn Alex, leave the `## Deep Read` marker `pending` (and the ledger row `pending` — do not flip it), and continue (or finish). The Scan head + entity records + content pipeline are unaffected. Re-run just Step 4.5 (idempotent). A single-section failure → render the rest and flag the gap; do not abandon the whole Deep Read for one thin section. The Step 6.5 gate + the Stop-hook `deep-read-gate.sh` will surface the pending marker at close — that's intended: decoupled-by-design means the render failure doesn't *block mid-run*, NOT that an unrendered Deep Read closes green.
- **A `field-guide-renderer` call returns a `> Gap:` note** (e.g. a `web-verified` fact missing its URL) — keep it in the output, surface it to Alex; it marks a citation to complete before public reuse. Trace it back to the specialist's Evidence Ledger / Step 1.7 URL capture.

## Why fan-out runs in the parent thread (architectural note)

Per Anthropic SDK design, subagents dispatched via `Agent` (formerly `Task`) cannot themselves dispatch further subagents — `Agent`/`Task` is not exposed to subagent contexts and cannot be granted via frontmatter. This is a deliberate constraint to prevent runaway nesting. The documented workaround pattern is "chain subagents from the main conversation": orchestrate from the slash command's parent thread, where `Agent` is available.

A previous version of this pipeline used an `event-research-orchestrator` subagent intended to fan out the four specialists from inside its own context. Empirical testing on 2026-05-07 (across 5 different subagents + the orchestrator) confirmed the SDK constraint and validated the pivot to parent-driven fan-out + synthesizer-only downstream agent. See WORKFLOWS.md "✅ Resolved 2026-05-07" section for the full diagnostic record.

## Ground truth references

The orchestration shape is defined here. The actual research / write methodology is in:
- `.claude/skills/event-research/SKILL.md` — full 7-step methodology (parse → triage → research → present → Notion writes → HubSpot writes → retro)
- `.claude/agents/research/event-research-synthesizer.md` — synthesizer contract (text-in, brief-out)
- `.claude/agents/research/{company-researcher, person-researcher, topic-landscape-analyst, competitive-signal-scanner}.md` — specialist contracts (now w/ historical spine + novice on-ramp + Evidence Ledger)
- `.claude/agents/content/field-guide-renderer.md` — Deep Read renderer contract (Opus, section-by-section + stitch, endnotes)
- `.claude/agents/ops/notion-writer.md` — Notion write contract
- `docs/adr/ADR-5-event-field-guide.md` + `.claude/proposals/event-field-guide.md` — the one-artifact / two-layer / decoupled-render invariants
- `CLAUDE.md` § Project Architecture — Notion/HubSpot schemas, write order, gotchas, SDK constraints
