# Execution-week frictions (append-only)

Window: 2026-05-15 → ~2026-06-05. Raw capture, no structure. End-of-window batch review against published count + 2026-05-14 falsification triggers.

---

- **2026-05-20** — Linear priorities (YED-29 SessionStart hook) not project-scoped — same Yedibalian-team-wide block renders in every repo, so it's not actionable at the project level. Spec for fix folded into YED-30 (per-repo `.claude/linear-project.json` + hook patch to filter by Linear Project ID). Defer until end-of-window. Also surfaced sub-issue: SessionStart `additionalContext` is invisible to user in terminal — only renders into Claude's context. If we eventually want it visible at terminal-start, hook needs to also `>&2` echo. Captured here, not actioned.

---

## 2026-05-20 — Calendar-invite-as-structured-intake (auto-trigger event research)

### The friction
Events get booked 1+ weeks out. Alex tells himself "I'll come back to it" for research/content. Reality: events accrue, return-to-it doesn't happen, and pre-event window becomes a batch review-edit-publish crunch. The "come back to it" step is the failure point.

Possible mapping to 2026-05-14 systems-analyst diagnostic: deferred review may be the gating loop on publishing rate. Test before assuming (see falsification protocol below).

### The proposed architecture (build-better, no API integration to build)

**Step 1 — Add a structured PIPELINE block to the event invite description at acceptance time:**

```
[organizer's description, pasted verbatim]

---
PIPELINE
Speakers: Name (Title, Company), Name (Title, Company)
Host: Organizing entity
Topics: keyword, keyword, keyword
URL: https://...
Intent: attend / documentary / both
```

Friction lands at the moment of acceptance (when intent is high) rather than at content time (when intent has faded). The invite itself becomes the durable record — GCal becomes the event history, no separate intake form needed.

**Step 2 — Text expander or clipboard snippet** for the template so it pastes in 1 keystroke. Tooling: Raycast snippets, macOS Text Replacements, or Wispr Flow snippet. ~5 min setup once template is locked.

**Step 3 — Scheduled `/schedule` routine:**
- Cadence: daily, ~7am
- Query Google Calendar MCP (`mcp__claude_ai_Google_Calendar__list_events`) for events in next 14 days
- Look for `PIPELINE` block in event description
- Cross-check Notion Events DB by title + date to skip already-ingested events
- For each new event with PIPELINE block:
  1. Parse fields (Speakers, Host, Topics, URL, Intent)
  2. Run `/event-deep-research` with the structured input (skip the parsing step the command currently does — fields are already structured)
  3. Write brief to Notion Events + Content Drafts in `needs_review` status
  4. Optionally chain `pre-event-content` to draft LinkedIn post + DMs in same routine pass
- Failure modes: malformed PIPELINE block → log to scratchpad, skip event. Missing GCal MCP env → graceful fallback like the Linear hook pattern.

**Step 4 — Review cadence:** Notion Content Drafts kanban becomes the daily morning ritual instead of pre-event crunch. Reviews happen over days, in small bites, with full week of runway to event.

### What it gains
- Removes "I'll come back to it" by removing the come-back step entirely
- Distributes content review across days vs. batch crunch
- Invite is the structured intake (one source of truth, not three)
- Intent filter preserved (Alex still types the fields = still chooses what's worth content)
- No new infra — uses GCal MCP that already exists + `/schedule` harness feature

### What it costs
- Template iteration + lock (~1 hour — get the fields right so they don't churn)
- Text expander setup (~5 min once template locked)
- `/schedule` routine setup (~1-2 hours including failure-mode handling)
- One real upcoming-event end-to-end test
- **Total: ~half-day**

### Open design decisions
- **Auto-run `/event-deep-research` or stage in `intake` status for manual trigger?** Auto = less friction but loses the "approve to research" gate. Stage = preserves gate but reintroduces a manual step. Default recommendation: auto, since the PIPELINE block presence IS the approval signal.
- **Chain `pre-event-content` in the same routine or wait for separate trigger?** Chaining = content drafts ready Day 1 after acceptance. Separate = lets brief settle before content gets written against it. Default recommendation: chain — that's the whole point of the design.
- **PIPELINE block format — markdown, YAML, JSON?** Markdown headers feel most natural for a calendar invite description. YAML is more parser-friendly but uglier in GCal UI. Recommendation: markdown with regex extraction (defensible against minor formatting drift).
- **What happens when invite metadata changes after research has run?** (Speaker swapped, location moved, etc.) Detect via GCal `updated` timestamp; flag in Notion for re-research vs. silent diff vs. skip. Defer this decision until real-world test surfaces the edge case.

### Falsification protocol (BEFORE building)
Per execution-focus discipline (2026-05-15 memory): friction observation alone doesn't justify breaking the window. Confirmation requires recurrence.

**Per-event tally** — every time Alex accepts an event in the next 7-10 days, log here:
- Date of acceptance
- Event date
- Did the "come back to it" pattern fire? (y/n)
- If y: what blocked the immediate content-creation alternative

Tally log:
- (none yet — starting 2026-05-20)

**Decision rule:**
- 3+ events in next 7-10 days trigger the "come back to it" pattern → confirmed signal → re-engage early to build
- <3 events trigger it → wait until 2026-06-05 end-of-window, decide with full publishing-rate data
- 0 events trigger it (publishing rate jumps without this) → don't build; the friction wasn't the gate

### Re-engagement state (when window closes or trigger fires)
This spec is build-ready. Half-day estimate assumes:
- No new architecture decisions surface during build
- Template fields lock on first iteration (use the structure above as starting point)
- Existing `/schedule` harness works for the routine (verify before committing to estimate)
- Existing `/event-deep-research` command accepts structured input (may require a small modification to skip parsing and accept pre-parsed fields)

If any of those assumptions break, estimate could expand to 1-1.5 days.

### 2026-05-20 update — execution-focus break decision

Decision: build Option B (full chain) immediately, breaking the 21-day execution-focus window on Day 5.

**Reasoning (preserved for end-of-window review):**
- Behavioral argument advanced from "speculative friction" to "named pattern with clean architectural fit": user is *already* editing the GCal invite (moves to "going to events" calendar at registration), so PIPELINE block nests inside an existing action rather than inventing new discipline.
- Mobile context-switch cost (GCal → Notion → back) makes the Tier 0 "create Notion row at acceptance" workaround non-viable; the friction it adds is the very friction we were engineering around.
- All tooling exists inside Claude subscription: connected GCal + Notion MCPs. No third-party integration to build.

**Cost accepted:** 3-5 hours during execution-focus window. **Actual cost:** ~6-7 hours (mid-build pivot from `/schedule` remote routine → manual `/check-new-events` slash command after Phase 0 revealed CronCreate is session-bound + remote routines wouldn't have access to project-level slash commands/skills anyway).

### 2026-05-20 build outcome

**Shipped:**
- `/check-new-events` slash command (`.claude/commands/check-new-events.md`) — session-driven, triggered manually when Alex opens Claude Code
- PIPELINE block template + reference (`.claude/references/pipeline-block-template.md`) — 200-char-tolerant LLM-parsed structured block
- Text expander `;pipeline` set up in macOS Text Replacements (syncs to iOS via iCloud)
- DM spec patch: speaker/host outreach reframed from multi-sentence DMs to **2 variants × 200-char connection request notes** (A = talk-anchored, B = adjacent-work-anchored) — updates landed in `pre-event-content/SKILL.md`, `outreach-templates.md`, CLAUDE.md Phase 2

**Validated end-to-end on Ray Dev Day (2026-05-21):**
- `/check-new-events` detected 5 PIPELINE-block events, parsed all fields correctly, dedup against Notion clean
- `/event-deep-research` ran the full chain (entity confirm → triage approval → 4-agent parallel fan-out → synthesizer brief → 5 Notion DB writes)
- `pre-event-content` produced LinkedIn post + 4-slide visual carousel + 5 A/B connection notes (1 B-variant skipped per fallback rule for thin adjacent-work signal) + 11 prepared questions

**Deferred to fresh session:**
- HubSpot writes for Ray Dev Day (mechanical CRM creates, not validation-critical)
- Notion writes for 7 pre-event-content drafts pages (content generated in-conversation, batch-write via notion-writer pending)
- Full chain on AI Demo Night + 3 other 5/26-5/28 PIPELINE-block events Alex added today (Scaling Enterprise AI Agents, Evolution of Commerce, Building Agentic Marketing)

### Falsification protocol updates (track during remaining execution-focus window)

The 5 PIPELINE blocks Alex added today are themselves data — he tagged every content-worthy event on his calendar in one ~1-minute pass. That's a positive signal for the "PIPELINE-at-acceptance is sustainable" hypothesis. The harder test is the next 2 weeks: does he keep adding blocks at acceptance time for newly-booked events, or does the discipline atrophy when there's no fresh build excitement?

**Tally log — events Alex accepts in remaining window (track here):**
- (none yet — log future acceptances with: date accepted | event title | PIPELINE block added at acceptance? y/n | if n: why not)

**Decision rules going forward:**
- If PIPELINE-block-at-acceptance rate ≥ 80% over next 2 weeks → discipline is sustainable; ship the remaining Phase 7 mechanical writes + close build
- If rate drops below 50% → investigate WHY (expander friction? GCal mobile UX? cognitive load at acceptance?) before adding more tooling
- If `needs_review` queue overflows (briefs faster than Alex can process them) → that's a different failure mode requiring queue prioritization, not more ingestion automation

**End-of-window review should ALSO answer:**
- Did the PIPELINE block discipline sustain at acceptance time (not just retroactive backfill)?
- Did `/check-new-events` get used more than once a week, or did it become "I'll run it when I remember"?
- Did the distributed-review-across-days promise hold, or did briefs pile up?
- Net effect on publishing rate: up, down, or flat?
- New question raised by today's build: did the 200-char connection note spec produce notes Alex actually sent (vs. the previous multi-sentence DMs which may have been generated but never shipped)?

---

## 2026-05-21 — Granola → post-event content (transcript-paste friction kill)

### The friction (NAMED, not speculative)
Alex's own words: "I have had significant friction post-event and haven't been posting afterwards, I'm drained by the end of the day, and the trying to upload the full transcript plus audio file that doesn't play well was a pain." Publishing rate on post-event content has been near-zero across the execution-focus window — i.e., the failure mode the 2026-05-15 window was set up to address is firing specifically on the post-event leg.

Forcing function: 2 attended events tomorrow (2026-05-22), post-event content needed after. Manual fallback would replicate the same friction that's been blocking publishing.

### The decision — break the rule (second time in window, both times intentional)

Decision: build Granola-anchored `/post-event-content` flow tonight (2026-05-21). This is the second execution-focus break (first was `/check-new-events` on 2026-05-20).

**Systems-thinking framing (rule-out discipline):**

| Archetype considered | Verdict | Why |
|---|---|---|
| Shifting the Burden | **Rejected.** | The 2026-05-15 rule was written to guard against this — automating before the manual habit was established. But the manual habit HAS been attempted (full transcript paste + audio upload) and is the documented failure point. Removing it isn't burden-shifting; it's removing a confirmed friction. |
| Drift to Low Performance | **Rejected.** | Post-event publishing isn't gradually drifting — it's been flat-near-zero. Different shape. |
| Balancing Loop with Drain | **Match.** | The post-event content stock is being drained by exhaustion + upload friction at a rate that swamps the inflow (room observations). Granola pre-synthesis removes the largest single drain. |

The rule that was set 2026-05-15 was "resist architecture work that delays publishing." This is architecture work that **enables** publishing. Same intent, same direction — the rule bends here, doesn't break.

### What was built tonight

1. **New slash command** — `.claude/commands/post-event-content.md`
   - Resolves event name → Notion Event row (by title search)
   - Fetches Granola note via REST API (list + get with transcript)
   - Dual-path resolution: deterministic `Google Calendar Event ID` match (preferred), title+date fuzzy fallback
   - Passes structured Granola output (summary_markdown + diarized transcript + attendees) into `content-correspondent`
   - Drafts committed to Notion Content Drafts via `notion-writer` with Event Phase = post_event

2. **Notion Events DB property add** — `Google Calendar Event ID` (text, 9th property)
   - Added manually by Alex in Notion UI (Notion MCP wasn't surfaced in the build session, so this was a manual step — 30 seconds)
   - Populated going forward by `/check-new-events` → `/event-deep-research` → `notion-writer`
   - Empty for events created before 2026-05-21; dual-path resolution handles them via title+date fallback (no backfill required)

3. **Upstream chain updated** to write the new property at intake:
   - `.claude/commands/check-new-events.md` — captures `event.id` from GCal MCP response, passes to `/event-deep-research`
   - `.claude/commands/event-deep-research.md` — accepts `Google Calendar Event ID:` line in input, forwards to `notion-writer`
   - `.claude/agents/ops/notion-writer.md` — writes the property on Event row creation, plain text, raw `event.id` verbatim

4. **content-correspondent SKILL.md updated** — added Mode A (Granola-anchored structured input) and Mode B (manual paste, legacy) sections at the top. Skill now operationalizes the Granola integration the prose previously only mentioned.

5. **API key storage** — `~/.zshrc` export of `GRANOLA_API_KEY`. Same env-var pattern as `LINEAR_API_KEY` (see env handoff memory: terminal-launched Claude Code only, Dock-launched doesn't inherit).

### What was NOT built (deferred deliberately)

- **Granola MCP server install** — would be cleaner than REST/curl but adds settings.json edit + restart cycle. REST works tonight; MCP is v2 polish.
- **Backfill of GCal Event ID on existing Notion Event rows** — not required because of dual-path resolution. Tomorrow's 2 events will run on title+date fallback.
- **Auto-detection of Granola notes without an Alex trigger** — the command is manually invoked. No webhook (Granola doesn't expose them) and no polling daemon. Manual kickoff is the right scope.

### Cost accepted

- ~2-3 hours of build time tonight
- Alex's two manual steps:
  1. Add `Google Calendar Event ID` (text) property to Notion Events DB via UI
  2. Add `export GRANOLA_API_KEY="grn_..."` to `~/.zshrc` and `source` it (or restart terminal)

### Falsification criteria — track during remaining execution-focus window

**Primary metric:** number of post-event LinkedIn posts published in the remaining window (2026-05-21 → 2026-06-05). Baseline before this build: ~0.

**Decision rules:**
- **≥3 post-event posts published in remaining ~2 weeks** → friction WAS the gate; the build paid off; harden the path (move to Granola MCP, add the post-event-synthesis full chain).
- **1-2 posts published** → friction was a factor but not the only gate; investigate what else is blocking (energy management, post fatigue, content-correspondent draft quality, voice authenticity in Granola summaries).
- **0 posts published** → the gate was somewhere else entirely (mood, demand, the room not actually being post-worthy). Roll back enthusiasm for further automation; refocus on the actual gate.

**Per-event tally (track here):**
- (none yet — start with the 2 events on 2026-05-22)
- Per event, log: event date | Granola match path (A/B) used | minutes from `/post-event-content` invocation → draft in Notion | minutes from draft → published post | what gated each step

### Open questions for end-of-window review

- Did Granola's AI summary produce content Alex's voice survived (vs. summary-flattened mush)?
- Did the dual-path resolution actually catch a title-match edge case in practice, or was the GCal ID always present?
- Did `notion-writer` need any schema gotcha fixes for the new property? (Should be plain text — easiest possible property type.)
- Did Alex use `/post-event-content` more than once per event-attended, or was it run-once-and-move-on?
- Was 36h the right date window, or did we need to widen to 48h on real-world data?
- Did the structured input (summary + transcript) actually produce better drafts than Mode B (manual paste) would have? If summary alone or transcript alone is better, prune the unused half.

---

## 2026-05-27 — First live full-pipeline run (manual transcript → dual-angle content) + new gotchas

### Context
Ran the post-event pipeline end-to-end, live, as a deliberate full-system test on the **Scaling Enterprise AI Agents** transcript (5-speaker panel, manually pasted `.docx` — Granola didn't record). Produced TWO parallel content packages (Alex wanted optionality to review same-night): Path A *"Engineering now runs security,"* Path B *"Measurement is the gate."* Every stage fired: inline transcript conditioning → content-correspondent (Mode B) → 2 visual briefs → 2 live Gamma carousels → notion-writer (6 Content Drafts) → notion-update link-back. Zero property rejections on the Notion writes; People name→URL mapping resolved by the agent itself.

### Findings (the point of the test)

1. **Mode A is unusable for walk-up / pasted-transcript events.** `/post-event-content` is hard-wired to Granola; with a pasted transcript the only path was invoking content-correspondent directly in Mode B. **TODO:** thin `/post-event-content-manual` wrapper, or a `--paste` branch on the existing command, so Mode B has a front door instead of riding the skill bare.

2. **Transcript conditioning is real work that wasn't a formal stage.** Speaker resolution + entity normalization + a confidence-scored quote bank materially de-risked the quotes (raw ASR mangled Vercel→"Purcell", Salehi→"vahan", MCP→"FCP", agentic→"genetic"; diarized "Speaker N" labels smeared identity). Codified as a v1 skill stub: `.claude/skills/transcript-intelligence/transcript-conditioning/SKILL.md`. NOT yet wired as an automatic upstream step. Distinct from `transcript-analysis` (that's N≥10 sales-call mining; this is single-event content conditioning).

3. **New Notion gotcha (now logged as CLAUDE.md update-page gotcha "l").** `notion-update-page` `update_content` `old_str` must match the STORED markdown — Notion normalizes `_italics_` → `*italics*` on write, so a match against the authored underscore form failed with "No matches found." Fetch-then-match, or author the match with asterisks. (Hit live wiring the Gamma carousel URLs into the two post drafts.)

4. **Gamma:** `numCards` is silently ignored when `cardSplit: "inputTextBreaks"` — card count = number of `---` delimiters. Control count with delimiters, not `numCards`. Minor note worth adding to `visual-briefs.md`.

5. **Source-flag (Rule 12) carried correctly.** Speaker lines treated as primary (transcript); the "847 deployments / 76% failed / 94% named owner" stat on the carousels came from the brief's cited sources — flagged to Alex to spot-check that citation before either post goes public. No firm/person *thesis* claim asserted unsourced.

6. **Positive signal:** notion-writer generalized cleanly from its event-research design to standalone Content-Draft creation + relation resolution, despite its SKILL reference being event-research-centric. The agent set is more reusable than its docs imply.

### Decisions deferred to Alex
- Pick a post to ship (or stagger A and B across the week — they don't compete; A is contrarian, B is data-backed).
- Refine carousels in the Gamma editor (no MCP edit), export PDF for the LinkedIn document post.
- Wire-ups (TODO 1 + finding-2 upstream wiring + finding-4 visual-briefs note) batched here, not actioned, pending green-light. Note: skill/command/agent changes are session-frozen — any wire-up needs a FRESH conversation to validate.

---

## 2026-06-11 — WINDOW CLOSED. Brake lifted, replaced by a steering bias.

End-of-window close-out (6 days past the ~2026-06-05 target date). Inputs reviewed: this frictions log, the v2-trigger log (10 machine invocations across the window — pre-event 5x, content-correspondent 2x, check-new-events 2x, event-research 1x; steady generation), Notion Content Drafts schema, Alex's verbal read.

**Outcome:** The window worked, then inverted. Publishing increased (Alex's read). But at execution volume the rule turned counter-productive — executing the work surfaced real-time improvement ideas, and the "capture-and-defer, don't build" discipline left that friction sitting in the active publishing path. The deferral itself became the drag on publishing. Systems framing: the balancing loop that protected the publishing stock flipped into the constraint draining it. The brake outlived its purpose.

**Decision (Alex):** Retire the no-build rule. Build improvements in real time while executing.

**Replacement — steering bias, not a brake:** Build freely, but each build should remove a *named friction on the active publishing path*. Friction-remover → build inline, now. Speculative architecture with no named publishing friction behind it → still skip (the original R2 / Shifting-the-Burden trap; the only thing the bias rules out). Same friction-remover-vs-R2-trap test as the 2026-05-21 entry — now applied LIVE, not deferred to a batch.

**Note on the published-count metric:** never got a clean system number this close-out — Notion `Content Status = published` is a lagging proxy (drafts can be posted to LinkedIn without flipping status, and vice versa). The 12 trigger-log `?` marks were also never resolved to a trigger number, so YED-27's per-session signal didn't accrue. Neither blocks the decision (Alex's verbal read — "publishing increased, deferral now slowing it" — is sufficient and is the ground truth the status field only approximates), but if a future diagnostic needs a hard publish number, instrument LinkedIn reality, not the Notion status field.

**Doc changes made this session:** CLAUDE.md open-priorities block (rule retired + bias added, pipeline-v2 ungated), memory `execution-focus-2026-05-15` (flipped to CLOSED + close-out), MEMORY.md pointer.
