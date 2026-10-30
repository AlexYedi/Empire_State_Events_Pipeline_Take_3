---
description: "Workflow A — full event research pipeline. Parses a pasted calendar invite, runs entity triage, fans out 4 parallel research subagents from this conversation, dispatches synthesizer for the brief, and writes to Notion + HubSpot. Replaces the monolithic event-research skill flow with a multi-agent architecture."
argument-hint: "[paste calendar invite text after the command]"
---

# /event-deep-research — Workflow A

Run the full event research pipeline using multi-agent fan-out **from the parent thread** (the slash command's main conversation). Per CLAUDE.md invariant 6 the parent owns the fan-out and a downstream synthesizer assembles the final brief.

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
2. **(Optional) Google Calendar Event ID** — if the input includes a `Google Calendar Event ID:` line (as `/check-new-events` always passes), capture it and write it to the Events DB row in Step 4 (wave 3 payload). This is the deterministic join key to Granola for `/post-event-content`.
3. **(Optional) Stated focus** — if Alex says "I'm going to find a hiring manager" or "I want to test my POV on agentic systems", pass that downstream so Success Signals are tailored


**Step 1.0 — CLAIM THE EVENT before anything else (YED-213, added 2026-09-24).** Git isolation does not isolate
Notion: on 2026-09-20 two sessions ran this pipeline for the same event and only avoided duplicate pages because
one happened to notice a Notion timestamp. Run this FIRST, before parsing:

```bash
python3 .claude/hooks/event-claim.py claim "<event name>" --note "<what you are running>"
```

* **exit 0** — you own this event's Notion namespace (Event, People, Companies, Topics, Content Drafts) for the run.
* **exit 3** — another session is already running it. **Go read-only for this event and report to Alex**, exactly as
  the reconciliation terminal does for git. Do not write. Takeover is deliberate and recorded:
  `--force "<why>"`. A crashed session's claim expires on its own after 4h.

**Release when the run closes** (or if you abandon it): `python3 .claude/hooks/event-claim.py release "<event name>"`.
`event-claim.py list` shows live claims across every session on this machine.

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

1. **1.7a Retrieve (this thread — MCP reads must run in the parent):** for entities **with a prior record** (from the Step 1.5b dedup — pure-NEW entities are skipped here and researched from scratch in Step 2), pull prior Event brief bodies, People/Companies page bodies, Topics `Current Events` (newsletter/trend notes), Gmail correspondence + `label:Content/newsletters newer_than:14d`, and Supabase graph context via the ONE retrieval path (S-01, YED-261): `.venv/bin/python .claude/scripts/retrieve.py --lens event --seed <scratch>/seed.json --out <scratch>/context-pack.md`, with the seed built from the Step 1.5b entities **with a prior record** (`{"type", "name", "notion_page_id"}` each, verbatim invite as `text`, `window_days: 365`) — the script reads `SUPABASE_API_KEY` from `.env` itself, **never** the MCP (see `.claude/references/market-intel-spine.md`). Its Context Pack (Continuity Ledger · entity cards · scored Claims, each tagged `c:<8>`) feeds the conditioner with the Notion/Gmail pulls, and its AUDIT line is the `graph:` entry of the mandatory audit below. **Follow the enforced cost-guard procedure in SKILL Step 1.7a:** skip-no-prior → rank (event-series brief > returning people > companies with recent developments > topics) → hard-cap **N=8** → emit the mandatory audit line (`pulled · skipped-no-prior · capped/not-pulled · graph`) before dispatching the conditioner. **The graph read is best-effort:** on script failure / timeout / empty pack, record `graph: no signals (<reason>)` and continue — never block or retry-loop. Exit 5 = RETRIEVAL FAILURE (the graph holds claims for these entities but the pack kept none): surface it loudly, never proceed as if there were no prior knowledge. (YED-262: usage attribution lands later — once Step 4.2 stages the `research_brief` document row, a re-attribution run may pass `--log-usage event --usage-document <documents.id>`; at 1.7a the audit line's `usage=not logged` is expected.)
2. **1.7b Condition (delegated):** dispatch `knowledge-conditioning` with the `VERBATIM SOURCE` block + triage plan + the 1.7a raw pulls. It returns the **Prior-Context Pack** — relevance-filtered, provenance-tagged (`KNOWN` / `STALE` / `UNVERIFIED` + `[source · date]`), with a Continuity Ledger, per-entity cards, Graph Signals, and an Audit. Text-in / text-out; no I/O.
3. **1.7c Persist (via `notion-writer`):** write the pack as a `prior_context_pack` Content Draft (`Platform: notion_only`, icon 🗃️) so "what prior knowledge fed this brief" is auditable. One-operation payload, same loop as Step 4: `key` = `draft:<event-slug>:prior_context_pack`, `dedup` = its title, manifest = the event's (`.claude/.state/notion-manifests/<event-slug>.json`); `notion_payload.py` → VALID → dispatch → show the table. Step 4 wave 4 relinks it and wave 3 mirrors a `## Prior-Context Pack` section onto the Event page.

**First-touch event (no prior record for any entity):** skip 1.7b/1.7c, note it, and run Step 2 from scratch. The graph read may come back empty (first-touch: the seed resolves nothing, mode `no seeds`) — expected, not a failure; Step 4.2 stages this run's research so the next run reads it.

**Verify-first (the discipline):** the pack is prior context, never current fact. Downstream readers treat `KNOWN` as a foundation and `STALE` / `UNVERIFIED` as leads to refresh/verify; nothing stale or unsourced flows into the brief as fact (the source-check rule, CLAUDE.md §6).

## Step 2 — Multi-agent research fan-out (this conversation)

Once triage is approved, **dispatch all four specialists in parallel from this thread** via a single message containing four `Agent` tool calls. This runs in the parent thread so one place owns concurrency and the chain (CLAUDE.md invariant 6).

The four parallel dispatches:

1. **company-researcher** — every Company entity that needs research (NEW, REFRESH, or FRAME-ONLY: a SKIP whose record has no Value Frame, YED-233). Pass the entity list scoped to this specialist + their triage paths + Alex's stated focus.
2. **person-researcher** — every Person entity that needs research (NEW or REFRESH). Skip the dispatch entirely if no people are named or all are SKIP.
3. **topic-landscape-analyst** — every Topic entity (NEW, REFRESH, or APPEND-CURRENT-EVENTS-ONLY). Topics never get full SKIP.
4. **competitive-signal-scanner** — runs across ALL companies (including SKIP) to surface market signals in last 60 days.

For each specialist, pass: **(1) the full `VERBATIM SOURCE` description block from Step 1, quoted unchanged and labeled as the source of truth** ("read every line; derive findings from THIS text — the framing below is supplementary, not a replacement"); (2) the entity list scoped to that specialist; (3) the triage path per entity; (4) the event name + date; (5) Alex's stated focus; **(6) that specialist's slice of the Step 1.7 Prior-Context Pack** — Companies cards → company-researcher; People cards → person-researcher; Topic cards → topic-landscape-analyst; Graph Signals + Continuity Ledger → competitive-signal-scanner — with the standing instruction: treat `KNOWN` as starting context, `STALE` / `UNVERIFIED` as leads to refresh/verify via web search, and never restate `UNVERIFIED` as fact. Omit (6) for a first-touch event or for specialists whose slice is empty.

**Mandatory (fidelity fix, 2026-06-23):** the verbatim description is item (1) for a reason — it goes in EVERY specialist dispatch, ahead of the entity list. Do NOT paraphrase it into the prompt and drop the original. If the parent only hands subagents the summarized entity list, the run repeats the defect where talk-abstract nuance and named-but-unsummarized themes never reach research. The Step 2.5 synthesizer also receives the raw invite — keep that.

**Return contract (added 2026-08-21 — YED-136):** each specialist now returns, alongside its prose blocks, (a) a **historical spine** (topic lineage / company founding→funding→evolution arc / person career arc — facts + dates), (b) **mechanism + jargon** material for the novice on-ramp, and (c) a per-entity **Evidence Ledger** under a heading exactly `##### Evidence Ledger — <Entity Name>`, one **bullet** per specific/recent/contestable claim in exactly this shape — `- claim: <≤15 words> | tier: web-verified | source: <site> | url: <full URL> | date: <YYYY-MM-DD>` — with tier ∈ `web-verified` / `email-signal` / `notion-prior` / `inference`. **Ask for this bullet form verbatim in every dispatch; do not ask for a table.** (Step 4.2's parser tolerates a `| claim | tier | source | url | date |` table as a fallback since 2026-09-27, after a run where every specialist emitted tables and the graph write found 0 admissible rows — but the bullet is the contract.) These feed the Deep Read render loop (Step 4.5); the URLs are mandatory for `web-verified` rows (the spike caught that missing URLs break endnotes). Preserve them when handing returns to the synthesizer.

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

## Step 4 — Notion writes (parent decides, `notion-writer` executes — CLAUDE.md invariant 5)

**Only after Alex approved the brief in Step 3.** The parent **decides every write** from Steps 4a–4f of `.claude/skills/event-research/SKILL.md` (triage path per entity, property values, page bodies) and hands them to the one Notion writer as payloads, the same shape as `/post-event-content` Step 5. The parent never calls `notion-create-pages` / `notion-update-page` itself on this step. Property mapping: `.claude/references/notion-schema.md`; formatting: `notion-write-gotchas.md`.
Inputs: approved brief + triage plan + raw invite text + today's date + Google Calendar Event ID (if captured in Step 1).

**Refresh merges are the parent's job, from a fresh fetch.** Union of `Industry / Space` / `Role Context`, Topic `Current Events` prepend + 6-block cap: the parent computes the final value and puts it in `properties`; the writer copies values, it never merges. **Every page a wave will `update` with a merged value is re-fetched while that wave's payload is built, every time.** Compare its `last_edited_time` with the one captured in Step 1.5b; if it is newer (Alex or another run edited it), re-merge from the fresh copy and note `re-merged` in the wave summary.

**Body markers (written at create time, so later edits are bounded).** Markers are `⟦name⟧` / `⟦/name⟧` with hyphenated names: Notion stores them byte-identical. **Never use HTML comments as markers:** Notion stores `<!-- x_y -->` as visible escaped text `\<!-- x\_y -->`, and an `update_content` on the raw form fails "No matches found" (sandbox 2026-10-24); the validator refuses a raw `<!--`. The live `notion-update-page` also has `insert_content` (position start|end), but the writer does not use it: anchors stay parent-owned. Every later body edit is a `content_updates` on a marker the create wrote:
- Company / Person / Topic page bodies end with `⟦/research-log⟧`; a refresh inserts its dated section before it.
- Event page and `research_brief` draft: `⟦research-brief⟧` … `⟦/research-brief⟧` around the Scan head; `⟦deep-read: pending⟧` + `⟦/deep-read⟧` under `## Deep Read`; the Event's `## Prior Snapshots` ends with `⟦/prior-snapshots⟧`.
- **Legacy pages** (created before the markers): `old_str` = the exact stored last block of the page (≥20 chars, copied from the fetch) and `new_str` = that block + the new section + the marker, which installs the marker for next time.
  - **Legacy Deep Read:** live pages carry the old marker in Notion's escaped form, exactly `\<!-- deep\_read\_rendered: pending -->` (or a date in place of `pending`); in payload JSON that is `"\\<!-- deep\\_read\\_rendered: pending -->"`. Copy it from the fetch. `old_str` runs from it through the next `## ` heading; `new_str` = `⟦deep-read: [today]⟧` + the Deep Read + `⟦/deep-read⟧` + the same heading. The validator checks all three.
  - **Legacy Research Brief:** `old_str` runs from `## Research Brief` through the next `## ` heading; `new_str` wraps the corrected section in `⟦research-brief⟧` … `⟦/research-brief⟧` and ends on the same heading.

**Four waves, because relations need URLs from the wave before.** Skip a wave with no operations. Each wave is one payload → validate → dispatch → read back:

| Wave | Operations (SKILL step) | Relations filled from the manifest |
|---|---|---|
| 1 | Companies (4b) + Topics (4c): NEW → `create`; REFRESH / FRAME-ONLY / APPEND-CURRENT-EVENTS-ONLY → `update` (+ `content_updates` before `⟦/research-log⟧` for the dated body section); SKIP → no operation | none |
| — | **Before wave 2, seed every SKIP entity** (all types) into the manifest as `"<type>:<slug>": {"page_id", "url", "op": "skip", "at"}` from the Step 1.5b hits (a local file write by the parent; no Notion call) | |
| 2 | People (4d), same mapping | `Company` ← wave 1 + seeded SKIP URLs |
| 3 | Event (4e): `create` with the markers above, body = Scan head + `## Deep Read` (pending) + `## Prior Snapshots` (the 4b audit-trail blocks) + `## Prior-Context Pack` mirror. Re-run of an existing Event → `update` with `content_updates` on the `research_brief` markers (4f re-run path) | `People` / `Companies` / `Topics` ← every created, refreshed **and** SKIP URL |
| 4 | `research_brief` Content Draft (4f) `create` (re-run → `update` with `content_updates`) + the Step 1.7c `prior_context_pack` relink (`update`, properties only) | `Event` ← wave 3 |

1. **Build the payload** at `<scratchpad>/notion-payload-<event-slug>-w<N>.json` (shape in `.claude/scripts/notion_payload.py`):
   - `run`: the event name · `manifest`: `.claude/.state/notion-manifests/<event-slug>.json` (gitignored; one per event, shared by Step 1.7c, all four waves and Step 4.5, so a rerun of any of them is safe)
   - `allowed_page_ids`: the bare UUIDs of the existing pages this wave updates (REFRESH targets from Step 1.5b, the existing Event on a re-run). The validator and the writer refuse an update to any page not in the manifest or this list, and a create into any database not among the 8 in CLAUDE.md §3.
   - `key`: `company:<slug>` · `topic:<slug>` · `person:<slug>` · `event:<event-slug>` · `draft:<event-slug>:research_brief` · `relink:<event-slug>:prior_context_pack`. Refresh updates add `:<YYYY-MM-DD>` so the next event's refresh of the same record is not skipped as done. **Re-runs (4f):** `event:<event-slug>:rerun:<YYYY-MM-DD>` and `draft:<event-slug>:research_brief:rerun:<YYYY-MM-DD>`, so corrections are never skipped as already in the manifest.
   - every `create` into a database carries `dedup` = the exact title. **Search-before-create stays explicit (invariant 8):** Step 1.5b already classified NEW vs existing, and the writer searches again before every create, so a record that appeared mid-run is skipped, not duplicated.
   - `update` takes the bare-UUID `page_id` (gotcha o); relations take the full page URLs from the manifest's `url` field (gotcha c).
   - Email / Phone / Phone Number never go in a payload built from research (gotcha n, ADR-9 tier 1); the validator refuses them on People unless the op carries `"alex_provided": true`.
2. **Validate:** `python3 .claude/scripts/notion_payload.py <payload>` must print `VALID`. Fix the payload, never the validator.
3. **Dispatch `notion-writer`** (`model: sonnet`) with the payload path. Show its created / updated / skipped / failed table inline.
4. **Read back before the next wave:** take the next wave's relation URLs from the manifest, not from memory. On `failed` rows, fix that operation and re-dispatch the same wave (done rows are skipped); before re-dispatching a failed **create**, let at least a minute pass (Notion search lags new pages, and the writer searches again before creating). Do not start a wave whose relations depend on a failed row. If the writer itself is unavailable, stop: do not write inline. Keep the payload, tell Alex which waves are unwritten, and re-dispatch when the writer is back (CLAUDE.md invariant 5). Report it in Step 6.

The four writer tables together are the Step 4g confirmation. The Event page + `research_brief` Content Draft now hold the **Scan head** plus a `## Deep Read` section carrying `⟦deep-read: pending⟧` and `⟦/deep-read⟧`. Step 4.5 fills it.

## Step 4.2 — Write the research to the knowledge graph (this conversation — YED-205, gated)

**Why:** the pre-event research is the richest thing this pipeline produces, and until YED-205 none of it reached the
graph that `/interview-prep`, retrieval and post-event runs read. Spec + decisions: `docs/archive/notes/yed-205-spec-2026-09-27.md`.
**What it writes:** the researched companies/people/topics, the `research_brief` document row, and one **claim** per
Evidence Ledger row, with `web_verified` for rows with a URL and `email_signal` for rows pointing at a public URL (a lead).
**What it never writes:** an event row. You have not attended yet (ADR-10 D9); `/post-event-content` 3.8b creates the
attended row and attaches these claims to it automatically. Private-correspondence rows (email-signal, no URL) and
`notion-prior` rows are skipped and counted, never written. All writes go through `spine_client` (ADR-9).

**4.2a Write two files (right after Step 4's Event page write)** under `.claude/.state/research/` (gitignored; `<slug>` = the event title, kebab-cased):
- `<slug>.manifest.json`: `{"event": {"notion_page_id": "<Event page id from 4g>", "title": "…", "event_date": "YYYY-MM-DD"},
  "entities": [...]}`. One entry per researched entity, from the triage plan + the 4g confirmation:
  company `{"type":"company","name","website","linkedin_url","notion_page_id"}` · person
  `{"type":"person","name","title","company","linkedin_url","notion_page_id"}` · topic `{"type":"topic","name","notion_page_id"}`.
  **Never** email, phone or bio (ADR-9). No `kind`, no `role`: there is no event row pre-event.
- `<slug>.evidence.md`: the synthesizer's **Evidence Set**, verbatim. If its `##### Evidence Ledger — <Name>` headings
  were lost, write the four specialist returns concatenated instead; their ledgers carry the same headings.

**4.2b Stage it:**
```
.venv/bin/python .claude/scripts/substrate.py stage-research --manifest .claude/.state/research/<slug>.manifest.json \
    --evidence .claude/.state/research/<slug>.evidence.md --brief-ref notion:<research brief Content Draft id from 4g>
```
Idempotent: a re-run reports `created=0`. Exit codes: **3** = zero admissible
ledger rows (loud; re-run with the raw specialist returns), **5** = the manifest lacks the Event page id. A network error: retry once; if it still fails, tell
Alex (list it in the Step 6 summary as an incomplete).

**4.2c Report** one line for Step 6: `Graph: <N> research claims (web <W> · email-lead <E>) · skipped <S> · unlinked headings <list or none>`.
If it genuinely cannot be written, say so in the Step 6 summary with the reason.

## Step 4.5 — Render + append the Deep Read (this conversation — decoupled, additive)

**Only after Step 4 committed the Scan head (4g).** Run **Step 4.5 of `.claude/skills/event-research/SKILL.md`** in this conversation: the parent dispatches the renders and builds the append payload; `notion-writer` executes it. This phase is **non-blocking**: a render failure is a warning, never a pipeline failure — the Scan head + entity records are already committed.

1. **Assemble slices (4.5a)** from the synthesizer's `## Evidence Set` (held from Step 2.5) — one URL-carrying evidence slice per Deep-Read section + event meta + Alex's focus + novice level.
2. **Render section-by-section (4.5b)** — dispatch `field-guide-renderer` (Opus) **once per section**, in order: The Frame → Primer/Landscape → Companies → People → Cross-Event Threads. Skip a section whose evidence slice is empty (no people → skip People; first-touch → skip Cross-Event Threads). **One section per call** — never ask for the whole Deep Read at once. Surface any `> Gap:` notes the renderer flags.
3. **Stitch (4.5c)** — dispatch `field-guide-renderer` in `stitch` mode with all rendered sections → the final Deep Read (opener + smoothed transitions + consolidated endnotes; no fact/citation added or removed).
4. **Append (4.5d) via `notion-writer`** — one payload, two `update` operations (Event page + `research_brief` Content Draft), each with `content_updates`: `old_str` = the whole marker-bounded section, from `⟦deep-read: …⟧` through `⟦/deep-read⟧`, copied from a fresh `notion-fetch` (on a first render that is just the two markers); `new_str` = `⟦deep-read: [today]⟧` + the stitched Deep Read + `⟦/deep-read⟧`, with real newlines (gotcha m; the validator refuses a literal `\n`, and a start marker without its end marker). Legacy pages without `⟦/deep-read⟧`: see the Step 4 legacy rule. `key` = `deepread:<event-slug>:<event|draft>:<YYYY-MM-DD>` (add `:r<n>` for a same-day re-render), manifest = the event's, both pages in the manifest already. `notion_payload.py` → VALID → dispatch → show the table. Idempotent: only that one section changes, and a retried key is skipped. `failed: anchor not found` means the stored text differs from the payload; re-fetch, copy it exactly, re-dispatch.
5. **Confirm / warn (4.5e) — fail LOUD.** On total render failure, leave the marker `pending` and emit an explicit `⚠️ DEEP READ PENDING — [event]` line in this run's output (and, under `/check-new-events`, in the Step 7 batch summary's "Deep Read PENDING" block) so a thin, Scan-head-only brief is never mistaken for a finished one. Step 6.5 will report the run incomplete, which is correct. Offer to re-run just Step 4.5 (idempotent). Only if Alex *explicitly accepts* shipping this event Scan-head-only for now, record it in the Step 6 summary as waived (with the reason) rather than pending.
   In batch/autonomous mode a `pending` marker is a **tracked incomplete that must appear in the final summary** — silent degradation to the Scan-head-only brief is the exact regression this step guards against (it is how the entire Aug-2026 Shortlist/AWS/Spark/GTM-Leaders batch shipped thin).

**Registry note:** if `field-guide-renderer` won't dispatch in this session, run the pipeline in a fresh conversation (CLAUDE.md invariant 7).

**Graph note (YED-205):** a Step 4.2 that did not stage is reported at Step 6.5; resolve it by re-running Step 4.2b.

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

Before declaring the run complete, run the authoritative marker check. This step is the **only** Deep Read / graph-write gate — do not skip it. It reads the *real* Notion state:

1. **Enumerate touched Event pages** — from this run's own record. Also report whether Step 4.2 staged (its 4.2c line, or the reason it did not).
2. **Re-fetch each marker** — `notion-fetch` the Event page and read its Deep Read marker in either form: `⟦deep-read: [date|pending]⟧` (pages from this version on) or the legacy escaped `\<!-- deep\_read\_rendered: [date|pending] -->` (older pages; Notion stores the old HTML comment as visible escaped text). No marker found at all counts as `pending`. Notion is the truth.
3. **Verdict:**
   - **All `rendered` (or explicitly waived)** → run passes; report Deep Read ✅.
   - **Any `pending`** → the run is **NOT complete**. Interactive: **block close** — present the pending event(s), offer the idempotent Step 4.5 re-run, and do not report the run as done. Autonomous/batch: report the run **FAILED** with the pending list (never a silent pass).

---

## Workflow chain (what comes next)

After `/event-deep-research` completes successfully, common follow-ons:

| Want to... | Run |
|---|---|
| Generate pre-event content (LinkedIn posts, DMs, prepared questions) | `pre-event-content` skill — pulls research brief from Notion |
| Capture retro after attending | Step 7 of `.claude/skills/event-research/SKILL.md` (handoff to `content-correspondent` for post-event content) |
| Synthesize multiple events from this week into one post | `pattern-synthesis` skill (needs ≥2 briefs) |

See `.claude/WORKFLOWS.md` for the full picture of how the four workflows interrelate.

---

## Failure modes (specific to multi-agent runs)

- **Specialist returns thin output** — re-invoke that one specialist from this thread with deeper scope or more specific direction. Re-dispatch synthesizer with updated returns. Don't restart the whole orchestration.
- **Parent times out during fan-out** — split: dispatch company-researcher + person-researcher in one batch, topic-landscape-analyst + competitive-signal-scanner in another, then dispatch synthesizer with all four returns merged.
- **Triage plan disagreement post-hoc** — if while reviewing the brief Alex realizes an entity should have been REFRESH instead of SKIP, re-invoke just the relevant specialist with the corrected path; don't restart the whole flow.
- **A Notion write hits a schema validation error** (a `failed` row in the writer's table) — the live Notion schema is authoritative. Use the API error text to fix that operation's property value in the payload, re-validate, re-dispatch the same wave. Per `notion-write-gotchas.md` (e), verify with notion-fetch on the data_source URL if it persists.
- **Deep Read render fails (Step 4.5)** — this is **decoupled by design**: warn Alex, leave the `## Deep Read` marker `pending`, and continue (or finish). The Scan head + entity records + content pipeline are unaffected. Re-run just Step 4.5 (idempotent). A single-section failure → render the rest and flag the gap; do not abandon the whole Deep Read for one thin section. The Step 6.5 check will surface the pending marker at close — that's intended: decoupled-by-design means the render failure doesn't *block mid-run*, NOT that an unrendered Deep Read closes green.
- **A `field-guide-renderer` call returns a `> Gap:` note** (e.g. a `web-verified` fact missing its URL) — keep it in the output, surface it to Alex; it marks a citation to complete before public reuse. Trace it back to the specialist's Evidence Ledger / Step 1.7 URL capture.

## Why fan-out runs in the parent thread (architectural note)

Parent fan-out is policy (CLAUDE.md invariant 6): one thread owns concurrency, ordering and the chain, which a predictable workflow needs (Anthropic, *Building Effective Agents*). History: until Claude Code v2.1.219 subagents could not dispatch subagents at all; the harness now allows nesting, and we choose not to use it here.

A previous version of this pipeline used an `event-research-orchestrator` subagent intended to fan out the four specialists from inside its own context. Empirical testing on 2026-05-07 (across 5 different subagents + the orchestrator) confirmed the then-current constraint and validated the pivot to parent-driven fan-out + synthesizer-only downstream agent. See WORKFLOWS.md "✅ Resolved 2026-05-07" section for the full diagnostic record.

## Ground truth references

The orchestration shape is defined here. The actual research / write methodology is in:
- `.claude/skills/event-research/SKILL.md` — full 7-step methodology (parse → triage → research → present → Notion writes → HubSpot writes → retro)
- `.claude/agents/research/event-research-synthesizer.md` — synthesizer contract (text-in, brief-out)
- `.claude/agents/research/{company-researcher, person-researcher, topic-landscape-analyst, competitive-signal-scanner}.md` — specialist contracts (now w/ historical spine + novice on-ramp + Evidence Ledger)
- `.claude/agents/content/field-guide-renderer.md` — Deep Read renderer contract (Opus, section-by-section + stitch, endnotes)
- `docs/adr/ADR-5-event-field-guide.md` + `docs/archive/proposals/event-field-guide.md` — the one-artifact / two-layer / decoupled-render invariants
- `.claude/references/notion-schema.md` (Notion/HubSpot schemas, write order) · `notion-write-gotchas.md` · CLAUDE.md §4 (invariants 5–7)
