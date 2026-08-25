---
description: "Workflow B-lite — take a manually-uploaded post-event transcript, condition it against the event roster, then run content-correspondent to produce LinkedIn drafts + outreach in Notion Content Drafts. Manual-upload anchored (Granola auto-fetch DISABLED 2026-05-27 — app nonoperational on Alex's device; do not fire the Granola API or MCP)."
argument-hint: "[event name as it appears in Notion / Google Calendar / Granola]"
---

# /post-event-content — manual-upload post-event flow

> ## ⚠️ GRANOLA IS OFF (status 2026-05-27)
> Granola is **nonoperational on Alex's device** — the mobile app is a waitlist-only placeholder, so there are no recordings to fetch. **Do NOT fire the Granola REST API or the Granola MCP** for post-event recordings, here or anywhere. **Post-event transcripts are MANUAL UPLOAD only** until Granola ships a working app. The Granola auto-fetch path is retained below but **DISABLED** — re-enable it (and remove this banner) only once Granola actually records on Alex's device.

Takes a transcript Alex uploads/pastes from his own recording of an attended event, resolves the event to its Notion row, **conditions the transcript against the event roster (Step 3.5 — `transcript-conditioning`)**, then invokes `content-correspondent` with the conditioned quote bank.

**Input:** event name (one argument) + the transcript (manual upload/paste).

**Output (v2 — YED-96):**
- **`post_event_brief`** (the data store) — the full enhanced brief (18 sections incl. the **learnings tier**: pro-tips · best-practices · pitfalls · hot-takes · anecdotes · enriched concept glossary, + whole-quote Quote Bank + content-derived Speaker Map). Written **both** as the canonical Content Draft **and** appended to the **Event page** (`## Post-Event Brief`, pre + post side-by-side). Synthesized Step 3.7 from the conditioned transcript + roster + pre-event brief + Step 3.6 enrichment; every downstream draft references it.
- **Knowledge-graph write-back** (Step 3.8) — People / Companies / Topics rows created/enriched (dedup-mandatory) and relinked to the Event.
- **LinkedIn post(s) + visual carousel brief → Gamma** (Step 4). **Outreach is opt-in** — only for people Alex names; otherwise skipped.
- **HubSpot CRM write (Step 5.5 — GATED, opt-in, post-event only).** Selective (only people Alex actually engaged or is deliberately pursuing — not the whole roster), dedup-first, **create-once** (Notes for existing contacts, never field-merge), behind a confirmation gate. Default: skip. See `.claude/proposals/post-event-hubspot-step.md`.
- All drafts in `needs_review`, Event Phase = `post_event`, linked to the Notion Event row.

---

## Trigger

This command runs when:
- Alex types `/post-event-content [event name]`
- Alex says "post-event content for [event]" / "draft the post for last night's [event]" / "write up [event] from Granola"

If the user invokes `content-correspondent` directly with raw pasted material, defer to that skill's existing path — this command adds Notion event-resolution + roster-grounded conditioning around a manual transcript upload.

## Required inputs

1. **Event name** — fuzzy-match-friendly. The command resolves it against the Notion Events DB by title similarity, then anchors downstream lookups.
2. **Transcript (manual upload/paste)** — Alex's own recording transcript for the event (Otter/Zoom/phone export or pasted text). This is the post-event input now that Granola is off. **No `GRANOLA_API_KEY` needed** — the Granola path is disabled.

## Step 1 — Resolve the Notion Event row

Search Notion Events DB (`9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`) by event title using `mcp__notion__notion-search`. From the matching row, read:

- `Event Name` (title)
- `Event Date` (date) — anchors the Granola query window
- `Google Calendar Event ID` (text) — deterministic join key when populated
- The page URL (used later for the Content Draft `Event` relation)

**If no Notion match:** prompt Alex with the top 3 candidates from Notion by title similarity. If still no match, accept "create draft without Notion anchor" — content can still be generated from Granola alone; the Content Draft just won't have a Notion Event relation set.

**If multiple matches (same title, different dates):** present the candidates with dates and ask Alex to pick.

## Step 2 — Get the transcript (recording → ElevenLabs preferred; manual paste fallback)

Granola auto-fetch is **disabled** (see banner). Two paths, in order of preference:

### 2A — Recording → `/ingest-recording` (PREFERRED — proven on n=4 events; YED-95)
If Alex has the audio recording (`.m4a`/`.mp3`/`.wav`):
1. **Auto-seed keyterms from the Step-1 Notion roster** — pull this event's related **People** (speakers/hosts) + **Companies** (orgs/products) names into a temp keyterms file, one per line. (The `--expand-names` flag below then also seeds first/last tokens — the *Arielle / Donohue / Curran* lesson: speakers are often referred to by first-or-last name only.)
2. **Run the locked recipe** (`.claude/scripts/ingest_recording.py` — scribe_v2 + keyterms + word timestamps; see `/ingest-recording`):
   ```bash
   set -a; source ./.env; set +a
   uv run --with elevenlabs python .claude/scripts/ingest_recording.py \
     --audio "<recording>" --keyterms-file "<roster keyterms>" --expand-names [--num-speakers N]
   ```
3. Outputs (next to the audio): `… — Transcript (ElevenLabs).md` (the transcript) · `… .json` (word-level timestamps + confidence) · `… — REVIEW (low-confidence spots).md` (the quote-safety list → **carried into Step 3.5**).
4. **Persist** the EL transcript to `event-transcripts/YYYY-MM-DD_<Event>.md`. This is now the verbatim quote source.

### 2B — Manual paste (FALLBACK — recorder-app / other transcript)
1. Ask Alex to paste the transcript he has. **Persist immediately** to `event-transcripts/YYYY-MM-DD_<Event>.md` (save FIRST — unsaved = lost across sessions; memory `feedback-comment-workflow-2026-05-26`).
2. Recorder-app ASR under-renders proper nouns (**~55% vs ~87%** for the EL recipe across n=4) — prefer 2A whenever the audio exists.

Either path: also capture any **summary / notes** Alex adds (angle/thesis input) and the **attendee names** he recalls (cross-reference Notion People for bucket sorting). If there's neither transcript nor recording, draft from his freeform recap + the pre-event brief — note lower fidelity, skip verbatim quotes.

<details>
<summary>🚫 Granola auto-fetch — DISABLED (do not run; retained for re-enable when Granola is operational)</summary>

The Granola REST/MCP path is **not active** — the app is a waitlist placeholder on Alex's device, so there are no notes to fetch. Do NOT fire it. Re-enable only when Granola records for real, then restore the manual path as a fallback.

```bash
# DISABLED — do not run while Granola is nonoperational (2026-05-27)
# List:   GET https://public-api.granola.ai/v1/notes?created_after=<event_date>T00:00:00Z&created_before=<+36h>   (Bearer $GRANOLA_API_KEY)
# Detail: GET https://public-api.granola.ai/v1/notes/<note_id>?include=transcript
# Match:  Google Calendar Event ID (deterministic, preferred) → title+date fuzzy fallback
# Capture: summary_markdown · diarized transcript · attendees · web_url
```
</details>

## Step 3 — Confirm the event anchor (silent if unambiguous)

Only prompt if Step 1 had disambiguation (multiple or no Notion matches). Otherwise proceed silently to conditioning.

```
📝 Event: [Notion Event Name] — [date]
   Transcript: event-transcripts/[…].md  (~N turns / M words)
   Proceeding to condition + draft. [y / change / cancel]
```

### Step 3.4 — Detect event format (showcase branch)

Before conditioning, classify the event format from the transcript + event name:

- **Founder / Startup Showcase** — multiple founders pitch back-to-back, a QR/opt-in
  intro mechanic (named series: **The Shortlist**). If detected, apply the
  **`.claude/skills/content-patterns/founder-showcase.md`** style throughout:
  **establish the showcase FOCUS first** (hiring / product-launch / funding / mixed —
  ask Alex to clarify the purpose if ambiguous; it drives everything downstream);
  Step 3.7's brief becomes the **per-company 6-dimension breakdown**; Step 4's content-correspondent
  produces the **showcase recap** (**every company referenced — none dropped**) **+ one-slide-per-company
  carousel** (not a single-thesis room report) **+ a focus-driven first comment** (one verified
  reference link per company — careers pages if hiring, launch/blog/feature pages if product, etc.);
  the contact-extraction pass captures **founders + explicitly called-out teammates in the crowd**
  → CRM + an **Apollo enrichment CSV**. Enforce the showcase sensitivities: **confidential "stays in
  the room" funding is never published**, and **garbled transcript names are web-verified before any
  public/CRM use** (fan out one `company-researcher` per company).
- **Standard** (talk / panel / roundtable / demo) — proceed with the normal flow below.

## Step 3.5 — Condition the transcript (`transcript-conditioning`)

Before drafting, condition the transcript so speaker labels and proper nouns can be trusted in public copy. Diarization splits on pauses, not identity, and ASR mangles proper nouns (Vercel → "Purcell", Mahan → "vahan", MCP → "FCP") — quoting that raw misattributes lines and prints garbled names. Invoke the `transcript-conditioning` skill with:

- **Raw transcript** — the manually-uploaded transcript from Step 2 (persisted to `event-transcripts/`).
- **Roster + known entities (ground truth)** — pulled from this event's Notion record: related **People** (speaker/host roster), **Companies** (canonical org/product names), and the linked pre-event **research_brief** Content Draft. Conditioning anchors speaker resolution + entity normalization to these.
- **Quote-safety input (when Step 2A / ElevenLabs was used)** — the `… — REVIEW (low-confidence spots).md` list + the word-level `.json` confidence. Map EL per-word confidence directly onto the quote tiers below: low-confidence words must NOT be quoted verbatim (→ paraphrase or exclude), high-confidence spans are verbatim-safe. This is the **R1 quote-safety contract** — a clean-looking transcript must *raise* quote safety, not silently lower it (YED-95).

**When to run:**
- **Run by default** for multi-speaker panels, in-person / manual-paste transcripts, or any note where a named person will be quoted publicly.
- **Skip** only when Granola's diarization is clean AND the roster is ≤2 obvious speakers (per the skill's "When to use"). State the skip decision in one line.

**Output (passed to Step 4 in place of the raw transcript):**
1. Speaker resolution table (resolved person + tell + confidence)
2. Entity normalization glossary (+ ⚠️ excluded-garble list — never quoted)
3. Confidence-scored **quote bank** (HIGH = verbatim-safe; MED = paraphrase only)
4. Conditioning confidence score + down-weighted sections

**Discipline (Rule 12):** the transcript is a primary source for what a person *said in the room* — quote freely. It is NOT a source for external firm/person *thesis* claims; those still need independent citation before public use (CLAUDE.md Rule 12).

## Step 3.6 — Post-event enrichment (bounded · gated-on-use · cached)

Research the **net-new** entities the room surfaced that the pre-event brief didn't cover, so the brief stands alone and proper nouns / concepts are correct (the folder-only ABB run missed web-enrichable facts — YED-96). **Topology (hard rule):** subagents do the research and return structured text; the **parent owns the fan-out list and does all writes** (subagents can't spawn subagents — SDK constraint).

**What to enrich:**
- **Net-new speakers** flagged in the Step 3.7 Speaker Map (no pre-research) — full name · title · company · 1-line relevance · source URL · confidence.
- **Net-new companies / funds** named on stage.
- **Concepts / papers / frameworks** named (for the enriched Concept Glossary) — what it is, why it matters, a source link.

**Bounds (cost guards — YED-96 R5):**
- **Gated on use:** only enrich an entity that will appear in a public post OR is an opt-in outreach target. Don't crawl the long tail.
- **Cap N per event** (default ≤ 8 entities); enrich the highest-signal first, list the rest as "un-enriched — pull on demand."
- **Cache by entity:** check Notion People/Companies/Topics first (Step 3.8 dedup) — a recurring speaker/company already in the graph is NOT re-enriched; reuse the existing row.
- **Quality gate:** if you can't confirm an entity to a confidence bar, mark it **UNRESOLVED** rather than guess — a hallucinated bio feeds both the graph and public posts.

Feed results into the Step 3.7 brief (Concept Glossary · Speaker Map · Enrichment Resolutions) and the Step 3.8 write-back.

## Step 3.7 — Synthesize the `post_event_brief` (the data store / short-term memory)

Before content-correspondent drafts a single post, synthesize the **`post_event_brief`** as a Notion Content Draft. This is the post-event mirror of the pre-event `research_brief` — one comprehensive, browsable page that captures *everything the event produced* so it can be referenced by every downstream draft AND mined later as part of the knowledge graph.

**Inputs:**
- Conditioned quote bank + speaker resolution table + entity glossary (from Step 3.5)
- The pre-event `research_brief` linked to this Event (for pre→post comparison)
- Notion roster (People + Companies + Topics relations from the Event row)
- Slides/photos uploaded by Alex (catalog them, don't re-OCR)
- Alex's own freeform recap / observations if provided

**Completeness over curation (the v2 principle, YED-96):** the brief is the *exhaustive, enriched record of the room* — capture every quote (whole, not snippets), every learning, every named concept. Content (post/visual) is **selected** from the brief downstream; the brief itself discards nothing. Validated across n=4 formats — see `.claude/evals/post-event-brief-template-evidence.md` (the learnings tier fills even at demo nights; Pre→Post Gap is conditional on a pre-event brief; Stat Bank is format-variable).

**Required sections (the full enhanced brief — mirror this scaffold; expand each as the material warrants):**
1. **Page-index callout** at top + `/toc` hint (per CLAUDE.md gotcha `i`)
2. **Quick Take** — three sentences: what the room actually was, the headline, the event-type tag for content routing (single-presenter talk / multi-presenter showcase / shared-conversation panel)
3. **The Thesis** — the single sharpest takeaway from the room, as a quotable line if possible
4. **Pre → Post Gap** — table contrasting what the pre-event brief predicted vs. what actually happened (highest-value beat). *Conditional:* if no pre-event brief is linked, pull it from the Event page; if none exists, mark "n/a — no pre-event research."
5. **Speaker Map** — **content-derived** mapping of each raw diarization `speaker_id` → person · role · company, each with HIGH/MED/LOW confidence + the tell. ⚠️ Raw diarization IDs are **NEVER 1:1 with people** — attribute by content, not by ID. Flag net-new speakers (no pre-research) for the Step 3.6 enrichment pass.
6. **Full Quote Bank** — EVERY quotable line, captured **whole (not snippets)**, attributed to the mapped speaker, each tagged HIGH (verbatim-safe) / MED (paraphrase only). Completeness is the point; selection happens downstream.
7. **Pro-Tips** — actionable "if X, do Y" practices stated/implied in the room (attributed, confidence-tagged)
8. **Best Practices / Patterns** — patterns recurring across speakers/companies
9. **Pitfalls / Anti-Patterns** — what NOT to do; failures named in the room
10. **Hot Takes** — contrarian / surprising claims (attributed, confidence-tagged; captured raw here — the publish gate in Step 4 decides what ships)
11. **Substantive Insights** — ranked by durability / content value
12. **Anecdotes** — memorable stories / moments as narrative (separate from the quote bank), for hooks
13. **Concept Glossary (enriched)** — every concept / paper / framework / tool / method named; one line on what it is from context + the Step 3.6 web-enrichment (what it is, why it matters, a source link) inline, so the brief stands alone
14. **Tools / Companies Mentioned** — table: name · what it is · context in the room
15. **Stat Bank** — numbers + value + confidence/caveat (never invent precision the speaker didn't claim). *Format-variable* — rich at case-study/masterclass, thin at roundtable/demo.
16. **Documentarian Angles** — the cuts available for future content (primary + alternates + synthesis candidates)
17. **Open Loops & Verification Flags** — follow-ups to close (touch-1 sends, comment/synthesis windows) + what cannot be asserted publicly without independent source (Rule 12 items)
18. **Enrichment Resolutions** — what the Step 3.6 pass resolved/corrected (net-new speakers identified, concepts confirmed, errors fixed — e.g. the ABB "Kilian = Meta not Amazon" catch), each with a source

**Operational sub-sections (pipeline plumbing — keep these alongside the 18):** **Slides Catalog** (one line per slide) · **People & Outreach State** (person · role · bucket A/B/C/D · spoke? · next action) · **Content Assets Produced** (links to comment/posts/visual — fill after Step 5) · **Conditioning Notes** (speaker resolution + entity glossary + ⚠️ excluded-garble + conditioning confidence score).

**Notion properties:**
- `Title`: `Post-Event Brief — [Event Name] ([Event Date short])`
- `Content Type`: `post_event_brief`
- `Event Phase`: `post_event`
- `Content Status`: `needs_review`
- `Platform`: `notion_only` (it's an internal data store, not a publishable artifact)
- `Event`: relation to the resolved Notion Event row
- `People`: relations to every named person on the roster
- `Topics`: relations to every linked Topic
- `icon`: 🗃️ (data store)

**Also write the brief to the Event page + set the idempotency marker (v2 — YED-96):**
- **Event page:** append a `## Post-Event Brief` section to the resolved Event row's page body (mirroring how the pre-event research brief sits on the Event page), so pre + post sit **side-by-side** for in-context comparison. The canonical Content Draft above stays the downstream source-of-truth; the Event-page copy is the readable surface. (For long briefs, the Event-page section may be a rich summary + a link to the canonical Content Draft — never truncate the canonical copy.)
- **Idempotency marker:** before the first write, check the Event page for a `post_event_processed: YYYY-MM-DD` marker (a callout at the top of the `## Post-Event Brief` section). If present, do NOT re-create the brief/Content Draft — update in place. Prevents double-writes on a re-run (there is no state store).
- **Rollback / safety:** the Event-page write is **append-only** under its own `## Post-Event Brief` heading — never `replace_content` the page (protects the pre-event brief already on the page).

**Why this step exists:** without the brief, the post-event content is one-shot — written once, then orphaned. With it, the data store survives the publishing of any single draft and feeds future synthesis posts, weekly recaps, knowledge-base mining, and re-engagement DMs. The pre-event flow has this (research_brief); the post-event flow now mirrors it.

After writing the brief, capture its URL and pass it to Step 4 (content-correspondent uses it as `=== Post-Event Brief ===` input alongside the conditioned quote bank).

## Step 3.8 — Knowledge-graph write-back (dedup-mandatory)

Persist what the event added to the **People / Companies / Topics** graph so it compounds across events. **Search-before-create dedup is mandatory** (pipeline rules #10/#11) — duplicate "Hebbia" / "Hermes Frangoudis" nodes rot the graph (YED-96 R4).

1. **Build the delta:** from the Step 3.6 enrichment + the Speaker Map, list every People/Companies/Topics entity the event touched.
2. **Dedup:** for each, `notion-search` the relevant DB first → classify **MATCH (existing row)** vs **NEW** ("net-new" is defined relative to the live DB index, not a guess).
3. **Write (parent / main-thread only — the Notion MCP does NOT work from a subagent):**
   - **NEW** → create the row (People: Name · Current Title · Role Context · Known POV/Bio · LinkedIn · `Events` relation · Last Researched; Companies: Company Name · Description · Industry/Space · Website · `Events` relation; Topics per schema).
   - **MATCH** → enrich the existing row (append POV/bio, bump Last Researched) + add the `Events` relation to this event — do NOT create a second node.
4. **Relink** all touched rows to the Event (bidirectional — the Event's People/Companies/Topics auto-populate).

Schema + property formats: `.claude/references/notion-schema.md`. If Alex prefers a review gate over auto-write, surface the NEW-vs-MATCH delta for confirmation first.

## Step 4 — Invoke content-correspondent with structured Granola input

Pass content-correspondent skill the following structured input (NOT raw transcript paste — leverage Granola's pre-synthesis):

```
Event: [Notion Event Name]
Date: [Event Date]
Notion Event URL: [Notion page URL]
Granola Note URL: [web_url from Granola]

=== Granola AI Summary (primary input — use for angle, takeaways, thesis) ===
[summary_markdown verbatim]

=== Conditioned Quote Bank + Glossary (from Step 3.5 — verbatim quote source) ===
[transcript-conditioning output: confidence-scored quote bank attributed to resolved speakers, the entity glossary (proper-noun spelling for public copy), the speaker-resolution table, and the conditioning confidence score. Quote HIGH-confidence lines verbatim; paraphrase MED; never print excluded-garble entities. If Step 3.5 was skipped, pass the raw diarized transcript here instead and note the skip.]

=== Attendees (cross-reference against Notion People DB) ===
[attendees + calendar_event.invitees, deduped]

=== Notion Pre-Event Brief (if available — for documentary thesis continuity) ===
[Pull from Notion: research_brief Content Draft linked to this Event]
```

content-correspondent then runs its standard logic per `.claude/skills/content-correspondent/SKILL.md`: bucket-sorts contacts, drafts Tier 1 comment + Tier 2 post + visual carousel brief + bucket A/B outreach DMs. The skill's existing "Granola → structured notes if the session was recorded; use for direct quotes from speakers" line is now operationalized — the structured input is exactly what it asked for.

**v2 output set + gates (YED-96):**
- **Canonical outputs = the brief (Steps 3.7–3.8) + LinkedIn post(s) + the visual carousel brief → Gamma.** These always run.
- **Outreach is OPT-IN, not default.** Do NOT auto-draft bucket A/B DMs. Generate outreach **only for people Alex explicitly names** for this event (captured via the `steering-interview` "person you want to land well with" answer). Free-LinkedIn connection-message limits make blanket outreach low-yield. Default: skip and note "outreach skipped — none flagged."
- **Attribution → public-content HARD GATE (the one irreversible failure — YED-96 R3):** a quote may be used **verbatim in a draft that @-tags a person ONLY if it is HIGH-confidence** in the conditioned quote bank. MED / low-confidence quotes → paraphrase, drop the tag, or exclude. A clean-looking transcript must not let a misattributed line reach a post that tags the wrong person.
- **Quote-safety framing:** the brief is *permissive capture*; the post is *gated publish* — stance-license earned (post-event = high), Rule-12 source-check on thesis claims, confidence tags enforced (`content-style-guide.md` / `content-anti-patterns.md`).

**Length guardrail (added 2026-06-10):** every Tier 2 post content-correspondent returns must be **≤ 3,000 characters** (LinkedIn hard cap) — the roundtable / topics×perspectives format with verbatim quotes is the one that overruns. Cut each version to budget BEFORE Step 5 commits it; sources / resource links go to the **first comment**, never inline in the post body. Canonical rule: `.claude/references/content-style-guide.md` → LinkedIn Character Budget.

## Step 5 — Write drafts to Notion via notion-writer

Once content-correspondent returns drafts, dispatch `notion-writer` to commit them:

```
subagent_type: notion-writer
prompt: [drafts list + Notion Event URL + People relations resolved + today's date]
```

Each draft becomes one Content Drafts row with:
- `Content Type` per draft (linkedin_post_post, linkedin_dm_speaker, linkedin_dm_host, etc.)
- `Event Phase` = `post_event`
- `Content Status` = `needs_review`
- `Platform` = `linkedin`
- `Event` relation = Notion Event URL
- `People` relation = matched People DB rows for each bucketed contact

## Step 5.5 — HubSpot CRM write (GATED · selective · create-once) — YED-142

**Spec + rationale:** `.claude/proposals/post-event-hubspot-step.md`. This is the **only** place the pipeline writes to HubSpot, and it runs **post-event only** — never pre-event. Pre-event, the person record lives in **Notion People** (the knowledge graph); HubSpot (the relationship / pipeline CRM) gets a contact only once there is a real reason. Governing rules: pipeline value philosophy (*relationships, not enrichment*), CLAUDE.md **Rule 6** (prefer create over update), **Rules 10/11** (dedup-search before create), and **HubSpot Write Orchestration** (Company → Contact + association → Note).

**Topology (hard rule):** all HubSpot writes happen **in the parent thread** — the HubSpot MCP is unavailable inside subagents, and the confirmation table must render inline (memory `project_notion_writes_must_be_parent_thread`).

### 5.5a — Build the candidate list (selective — default is exclusion)
A person qualifies for a HubSpot write **only if one holds**:
- Alex **actually spoke with them** in the room (`People & Outreach State` → spoke? = yes), OR
- they are an **opt-in outreach target** (named in Step 4), OR
- they are a **deliberate pipeline / job-search target** (e.g. a hiring manager at a company Alex is pursuing).

Everyone else stays in Notion People — do NOT create a HubSpot record for "someone I researched." If the candidate list looks like the whole roster, that is the failure signal — cut it back to real relationships.

- **Showcase reuse:** for a **founder-showcase** event (Step 3.4), the contact-extraction pass already produced the candidate set (founders + explicitly called-out teammates) + the Apollo enrichment CSV — **reuse that set**, don't re-derive.
- **Default skip:** if nobody clears the bar, skip this step and note `HubSpot: skipped — no contact cleared the relevance bar; Notion People holds the roster.`

### 5.5b — Dedup-search (mandatory — Rule 11)
For each candidate, search HubSpot before deciding to write:
- `mcp__claude_ai_HubSpot__search_crm_objects` by **name + company** (email is the primary dedup key when known).
- Classify each: **NEW** (no match) vs **EXISTS** (matched contact — capture its record id).
- (If unsure of internal property names, call `mcp__claude_ai_HubSpot__search_properties` / `discover_hubspot_schema` first — per the HubSpot MCP guidance.)

### 5.5c — GATE: confirmation table (STOP — Alex approves before any write)
Present the full plan and **wait**. This is a Tier-3 irreversible external write — never auto-execute.

```
🧩 HubSpot write plan — [Event Name] ([date])   (post-event · create-once)

| # | Person            | Company       | Status | Action                    | Note preview                                  |
|---|-------------------|---------------|--------|---------------------------|-----------------------------------------------|
| 1 | [name]            | [company]     | NEW    | create Co→Contact→assoc→Note | "Met at [event] [date]; discussed X; next: Y" |
| 2 | [name]            | [company]     | EXISTS | add Note only             | "[event] [date]: discussed X; next: Y"        |
| … |                   |               |        |                           |                                               |

Approve all / edit row N / skip row N / skip HubSpot entirely?
```

### 5.5d — Write (create-once, in dependency order — only approved rows)
- **Company** (if NEW) → `mcp__claude_ai_HubSpot__manage_crm_objects` (standard fields). If the company already exists, reuse it — do not duplicate.
- **Contact** — **NEW** → create + associate to the Company (HubSpot association). **EXISTS** → do **NOT** recreate and do **NOT** field-merge existing properties (Rule 6 — the fragile update path); proceed to the Note only.
- **Note** (every approved row, new or existing) → create a Note engagement via `manage_crm_objects`, associated to the contact, body = `event · date · role · what was discussed · next step`. The Note **is** the event-association mechanism (Static Lists are unavailable via MCP).
  - **Idempotency:** before adding, check the contact for an existing Note that names **this event** — if present, skip (no note-spam on re-run).

### 5.5e — Report
Roll the results into the Step 6 summary: created contacts/companies, Notes added, rows skipped (with reason). If the HubSpot MCP is unavailable, **fail clean** — surface the candidate + note table in chat so Alex can act manually; the Notion writes (Steps 3.7–3.8, 5) are already committed and unaffected.

## Step 6 — Summary

```
✅ /post-event-content complete: [Event Name]

Granola source: [note title] — [match path used]
Drafts created: N
  - Tier 1 comment: [Notion URL]
  - Tier 2 post + visual brief: [Notion URL]
  - Bucket A outreach: N drafts
  - Bucket B outreach: N drafts

HubSpot (Step 5.5): [N contacts created / M Notes added / K skipped]  — or "skipped — no contact cleared the bar"

All drafts in needs_review. Edit in Notion → mark approved when ready to ship.
```

---

## API key storage — DORMANT (Granola off; no key needed)

**While Granola is disabled (see top banner), this section does not apply — the command requires no `GRANOLA_API_KEY`.** Retained for re-enable whenever Granola becomes operational on Alex's device.

Default storage: `~/.zshrc` export.

```bash
# Add to ~/.zshrc
export GRANOLA_API_KEY="grn_..."
```

Then either restart the terminal or run `source ~/.zshrc` before launching Claude Code.

**Caveat from project memory (`project_claude_code_env_handoff.md`):** Dock-launched Claude Code does NOT inherit `~/.zshrc`. Launch from terminal so `$GRANOLA_API_KEY` is visible. Same constraint as the Linear hook (`LINEAR_API_KEY`).

If the env var is missing at command time, the command should fail clean:

```
❌ GRANOLA_API_KEY not set. Add to ~/.zshrc:
   export GRANOLA_API_KEY="grn_..."
Then relaunch Claude Code from terminal.
```

NEVER hardcode the key in this file or in any committed file. NEVER log the key in command output.

---

## Failure modes

**Note:** the Granola-API failure modes below are **N/A while Granola is disabled** (top banner). The active failure modes now are: no transcript provided → draft from Alex's recap + pre-event brief (lower fidelity, no verbatim quotes); Notion event not found → top-3 title candidates; notion-writer fails → return drafts in chat so the work isn't lost.

- **GRANOLA_API_KEY not set** — fail clean with setup instruction (above).
- **Granola API 401** — key invalid or expired. Tell Alex to regenerate in Granola Settings → API.
- **Granola API 429** — rate limit (5/sec sustained, 25 in 5sec burst). Sleep 2s and retry once.
- **Granola API returns empty list for the date window** — widen window to event_date ±48h once. If still empty, no recording exists (common for **in-person events** — Granola has no Android app). Offer the **manual-paste path**: Alex pastes his own recording's transcript, **persist it to `event-transcripts/YYYY-MM-DD_Event.md`** so it survives across sessions (see memory `feedback-comment-workflow-2026-05-26`), then run **Step 3.5 conditioning** on it (mandatory for manual paste) → Step 4. Or skip.
- **Multiple Granola notes match with comparable confidence** — present list with title + start_time + duration, ask Alex to pick.
- **Notion Event row not found** — present top 3 title-similarity candidates from Events DB. If none, allow "create draft without Notion anchor" path.
- **Notion People DB doesn't match Granola attendees** — pass attendee names through unmatched; content-correspondent will still draft outreach but Content Draft `People` relation will be sparse. Acceptable — Alex can backfill in Notion if needed.
- **notion-writer fails** — flag the error, return the in-memory drafts to Alex in chat so the work isn't lost. He can paste manually.
- **HubSpot (Step 5.5) MCP unavailable / errors** — fail clean: surface the candidate + Note table in chat for manual entry. Notion writes (Steps 3.7–3.8, 5) are already committed and unaffected. Never retry blindly against the CRM.
- **HubSpot dedup ambiguous** (multiple contacts match name+company) — do NOT guess. Present the matches to Alex in the Step 5.5c gate and let him pick the record or mark NEW.
- **HubSpot candidate list looks like the whole roster** — that's the over-creation signal. Re-apply the 5.5a bar (spoke-with / opt-in / pursued-target) and cut it back; the rest belong in Notion People only.

---

## Why this design

The friction kill is removing the transcript-paste step, not removing Alex from the loop. Granola already does diarization + AI synthesis; piping that structured output into content-correspondent (vs. raw transcript noise) gives the skill a higher-quality input and frees Alex from the post-event drain of "now I have to find the file and paste it in."

The dual-path resolution (GCal ID first, title fuzzy fallback) means:
- Future events captured via `/check-new-events` get the deterministic join automatically
- Existing events from before the GCal ID property was added still work via fallback
- No backfill required for the 2 events tomorrow — they'll match on title+date

The `summary_markdown` + diarized `transcript` together is intentional: summary drives angle/thesis decisions, transcript provides verbatim quotes for color. Summary alone is too tidy for Alex's documentarian voice; transcript alone is too noisy for fast angle-finding.

---

## Ground truth references

- **Granola API docs**: https://docs.granola.ai/introduction (auth, endpoints, rate limits)
- **Granola Get Note schema**: https://docs.granola.ai/api-reference/get-note.md (calendar_event, transcript, attendees fields)
- **Conditioning skill (Step 3.5)**: `.claude/skills/transcript-intelligence/transcript-conditioning/SKILL.md` — speaker resolution, entity glossary, confidence-scored quote bank
- **Downstream skill**: `.claude/skills/content-correspondent/SKILL.md` — content generation logic, bucket sorting, ladder
- **Downstream agent**: `.claude/agents/ops/notion-writer.md` — Content Drafts row creation, property mapping
- **HubSpot step spec (Step 5.5)**: `.claude/proposals/post-event-hubspot-step.md` — the gated selective create-once pattern + pre-mortem
- **HubSpot CRM schema + Notes convention**: `.claude/references/notion-schema.md` (canonical fields for all three write destinations)
- **Notion Events DB ID**: `9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`
- **Notion Content Drafts DB ID**: `6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`
- **Upstream chain**: `/check-new-events` → `/event-deep-research` writes `Google Calendar Event ID` to Events DB → this command uses it
- **Discipline-break decision record**: `.claude/notes/execution-week-frictions.md` (2026-05-20 entry for Granola integration)
