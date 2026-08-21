---
name: event-research
description: "Research an upcoming event from a pasted calendar invite. Produces a structured brief, writes to Notion (5 databases) and HubSpot (contacts, companies, notes), and optionally enriches speakers via Apollo."
---

# Event Research Skill

You are Alex's event research engine. Alex pastes a calendar invite (or describes an event),
and you produce comprehensive research that gets written to Notion and HubSpot via MCP.

**Do not skip steps. Do not combine steps. Present research for review before writing anywhere.**

---

## Step 1: Parse & Extract

Read Alex's pasted input and extract these entities:

| Entity | Look For | Example |
|--------|----------|---------|
| **Event** | Event name, date, time, location | "AI in Enterprise — April 15, 6pm, WeWork Soho" |
| **People** | Names + titles + companies + roles (speaker/host/organizer/attendee) | "Speaker: Jane Smith, CTO at Acme Corp" |
| **Companies** | Company names from people's affiliations + any mentioned orgs | "Acme Corp", "AI NYC Meetup (host org)" |
| **Topics** | Explicit topics + inferred from description | "agentic systems", "enterprise AI adoption" |

**Parsing rules:**
- If Alex provides structured cues ("Speaker:", "Host:", "Topics:"), use them directly.
- If the input is raw invite text, infer roles from context (e.g., "presented by" = speaker,
  "organized by" = host/organizer).
- If information is ambiguous, ask Alex before guessing. Do NOT invent people or companies.
- Always confirm your extracted entities with Alex before researching:

> **Extracted from your invite:**
> - Event: [name], [date], [location]
> - People: [name — title, company (role)]
> - Companies: [list]
> - Topics: [list]
>
> **Does this look right? Anything to add or correct?**

Wait for Alex's confirmation before proceeding to Step 1.5.

---

## Step 1.5: Dedup + Freshness Triage

Entities recur across events (the same company or person shows up again; topics definitely
repeat). Before researching anything, classify each extracted entity as **NEW**, **REFRESH**,
or **SKIP**. This gates both research depth in Step 2 and write behavior in Step 4.

### 1.5a: Canonicalize names before matching

Matching is lossy if we match on raw strings. Canonicalize first:

**Companies** — strip legal suffixes and normalize whitespace/case.
- Strip (case-insensitive): `Inc.`, `Inc`, `Corp.`, `Corp`, `Corporation`, `LLC`, `L.L.C.`,
  `Ltd.`, `Ltd`, `Co.`, `Company`, `PBC`, `GmbH`, `S.A.`, `plc`
- Collapse whitespace, lowercase for compare (preserve original casing for display/write).
- Example: `Microsoft Corporation` → `microsoft` for match; write `Microsoft` if creating new.

**People** — match on identifiers in priority order, stop at first hit:
1. **LinkedIn URL** (exact, ignoring trailing slash + query params) — strongest signal
2. **Email** (exact, lowercase)
3. **Name + Company** (canonicalized company name + case-insensitive full name)

If LinkedIn URL or email is known for the incoming person but not on the existing record,
update the existing record with it as part of REFRESH (see 4d).

**Topics** — lowercase, strip punctuation and trailing `s` on last word for naive plural
collapse. Keep a small alias table for common variants:
- `agentic systems` = `agents` = `agentic ai` = `ai agents`
- `rag` = `retrieval augmented generation` = `retrieval-augmented generation`
- `llms` = `large language models` = `foundation models` (treat as same for match; write
  whichever variant is already in Notion)

When in doubt on Topic canonicalization, ask Alex rather than guessing — topic collision
is a one-way decision (merging back is painful).

### 1.5b: Search Notion for existing records

For each canonicalized entity, run a `notion-search` against its database:

| Entity | Database | Search field |
|--------|----------|--------------|
| Companies | `d5910dc3-8327-4b49-9294-fc9499709a98` | Company Name (title) |
| People | `4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` | Name (title), plus LinkedIn URL and Email property scan |
| Topics | `d61ce9df-94b3-4637-aa09-d77e09ab3a74` | Topic (title) + alias check |
| Events | `9dcbc999-b4ed-4a51-b48a-10aaf171f1ba` | Event Name (title) — detect re-runs of the same event |

For each hit, capture: page URL, `Last Researched` / `Last Updated` date, and (for Companies)
the existing `Recent Developments` text (you'll need it for the audit trail in 4b).

### 1.5c: Classify each entity (NEW / REFRESH / SKIP)

Thresholds are intentionally differentiated — companies move fast, people move slower,
topic context shifts fastest but the core framing is durable.

| Entity | No match | Match, fresh | Match, stale | Match, very stale |
|--------|----------|--------------|--------------|-------------------|
| **Company** | NEW | ≤14 days → SKIP | 15–60 days → REFRESH (light) | >60 days → REFRESH (full) |
| **Person** | NEW | ≤30 days → SKIP | 31–90 days → REFRESH (light) | >90 days → REFRESH (full) |
| **Topic** | NEW | ≤45 days → APPEND-CURRENT-EVENTS-ONLY | 46–120 days → REFRESH (selective merge) | >120 days → REFRESH (full) |

Path semantics:

- **NEW** — full Step 2 research + Step 4 create (existing behavior).
- **SKIP** — no new research. In Step 4, don't overwrite the record; only add the new Event
  to its relation field. Brief and content drafts still draw on the existing record.
- **REFRESH (light)** — targeted research on what's likely to have moved (Company: funding +
  last 90 days of news; Person: last 90 days of public activity; Topic: Current Events only).
  In Step 4, merge rather than overwrite (per Topic merge rules in 4c; per Company audit-trail
  rule in 4b; per Person overwrite rule in 4d).
- **REFRESH (full)** — rerun full Step 2 research for that entity. Merge/overwrite per the
  same rules as light refresh — full vs. light only changes research scope, not write semantics.
- **APPEND-CURRENT-EVENTS-ONLY** (Topics, ≤45 days) — skip everything except fresh Current
  Events. Append a new dated block to the Topic's Current Events (see 4c merge rules).

### 1.5d: Present the triage to Alex

Before proceeding to Step 2, show the triage plan and get approval:

> **Entity triage for [Event Name]:**
>
> **Companies**
> - Microsoft — REFRESH (full) — last researched 2026-02-10 (69 days)
> - Acme Corp — NEW
> - OpenAI — SKIP — last researched 2026-04-12 (8 days), still fresh
>
> **People**
> - Jane Smith — REFRESH (light) — last researched 2026-03-01 (50 days)
> - Bob Jones — NEW
>
> **Topics**
> - agentic systems — APPEND-CURRENT-EVENTS-ONLY — last updated 2026-03-28 (23 days)
> - enterprise AI adoption — NEW
>
> **Proceeding with this plan. OK to research?**

Alex may want to override (e.g., "force full refresh on Microsoft", "skip Bob — already
know him"). Apply overrides, then move to Step 1.7.

---

## Step 1.7: Prior-Knowledge Retrieval + Conditioning

Between triage approval (1.5d) and the research fan-out (Step 2), pull what the pipeline
already knows about this event's entities, distill it into a **Prior-Context Pack**, and
persist the pack. This is the pre-event mirror of post-event `transcript-conditioning`
(`.claude/commands/post-event-content.md` Step 3.5). Goal: research **starts from**
accumulated knowledge and compounds — without dumping stale, unfiltered prior artifacts
into the fresh pass. The pack carries **detail with provenance, framed as verify-first
leads** (never a raw dump, never a thin summary).

**All retrieval runs in the parent thread** — the Notion/Gmail MCP connectors are not
available inside subagents ([[project_notion_writes_must_be_parent_thread]]); Supabase is
REST-over-Bash. Only the conditioning distiller is a subagent (text-in / text-out).

### 1.7a: Retrieve (parent thread)

For each entity on a NEW/REFRESH path (plus SKIPs and the event series), pull prior
knowledge, reusing the page URLs already captured in Step 1.5b. **Skip entities with no
prior record** — they are pure-NEW, nothing to retrieve.

**Capture source URLs while you retrieve (added 2026-08-21 — YED-136).** When a prior brief
body, trend note, or Gmail thread carries a source link for a fact, keep the URL attached to that
fact when you hand the raw pulls to the conditioner — it flows through the Prior-Context Pack's
`[source · date · url]` tags into the Deep Read's endnotes. The render spike caught that dropping
URLs here breaks citations three stages downstream.

- **Notion** (`notion-fetch` on captured URLs; `notion-search` for the series/host — NOT
  `notion-query-data-sources`, which is plan-gated on Alex's plan):
  - Prior **Event** page bodies for the same series or overlapping people/companies — the
    `## Research Brief` / `## Post-Event Brief` sections (the continuity source).
  - **People** page bodies: Known POV/Bio, Notes, prior Talking Points, `Last Researched`.
  - **Companies** page bodies: Description, Recent Developments, Recent Funding, `Last Researched`.
  - **Topics** `Current Events`: the accumulating dated `[Trend Radar {date}] …`
    newsletter/trend notes + `Last Updated`.
- **Gmail** (`mcp__claude_ai_Gmail__search_threads` / `get_thread`): prior correspondence
  with named people/companies; recent newsletter coverage of the topics via
  `label:Content/newsletters newer_than:14d` (the **full nested label path is required** —
  leaf `label:newsletters` returns empty). Do this **once, centrally, here** — don't make
  each specialist re-run it.
- **Supabase graph** (REST to `https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1/`,
  `SUPABASE_API_KEY` from `Take_3/.env` via Bash — never the MCP; see
  `.claude/references/market-intel-spine.md`): prior `market`-kind signals on these entities
  via `event_entity` hyperedge joins
  (`/event_entity?entity_type=eq.company&entity_id=eq.{id}`;
  `/event?kind=eq.market&order=event_date.desc&limit=25`). **Expect near-empty returns**
  until event-research write-back ships — wire the read, don't depend on the payload.
  **Best-effort, non-blocking (v1.1, YED-132):** run every graph call with a bounded timeout
  (`curl --max-time 8 -s -w '%{http_code}'`); on ANY non-2xx, timeout, error, or empty array,
  record `graph: no signals (<reason>)` in the audit line and **continue immediately** — never
  retry-loop, never let the graph read gate the run. The graph is the lowest-priority source;
  a from-scratch pass is the correct fallback when it's empty or unreachable.

**Cost guard — an enforced selection procedure, not a soft cap (v1.1, YED-132).** The cap is
a step with a deterministic ranking + a required audit artifact, so it can't be silently
skipped (the prose-only `≤8` was the "rigor-in-prose-not-execution-path" trap). Execute in order:
1. **Skip-no-prior (deterministic filter):** drop every entity with no prior record from the
   retrieval set — pure-NEW entities are researched from scratch in Step 2, never retrieved here.
2. **Rank the survivors** by fixed priority: (a) the event-series / host prior brief (continuity —
   always pull if it exists); (b) returning speakers/hosts (People with a prior record);
   (c) companies with a non-empty `Recent Developments`; (d) topics with a `Current Events` note.
3. **Hard cap N = 8** (default): fetch rich bodies for the top-8 ranked only; list every remaining
   candidate by name as "not pulled — on demand."
4. **Mandatory audit line** (emit before dispatching the conditioner — this line *is* the
   enforcement; if it's absent, the cap wasn't applied):
   `Prior-knowledge retrieval — pulled: [names] · skipped-no-prior: [n] · capped/not-pulled: [names] · graph: [ok N sigs | no signals (reason)]`
The conditioner re-applies a relevance filter downstream, but the *retrieval* cap lives here so
cost is bounded **before** any large body is fetched.

### 1.7b: Condition (dispatch `knowledge-conditioning` subagent)

Hand the subagent the `VERBATIM SOURCE` block, the triage plan, and all raw pulls from 1.7a.
It returns the **Prior-Context Pack** — relevance-filtered, provenance-tagged
(`KNOWN` / `STALE` / `UNVERIFIED` + `[source · date]`), with a Continuity Ledger, per-entity
cards, Graph Signals, and an Audit (confidence + dropped + coverage gaps). Full contract:
`.claude/agents/research/knowledge-conditioning.md`. It does no I/O — it distills what it
was handed.

If NO entity had any prior record (a genuinely first-touch event), skip 1.7b/1.7c, note
"no prior context — first-touch event," and proceed to Step 2 as a from-scratch run.

### 1.7c: Persist the pack (parent thread, Notion)

Write the pack as an auditable internal artifact (mirrors the `post_event_brief` pattern) so
"what prior knowledge fed this brief" is a first-class, reviewable record and a rigor-loop
input:
- **Content Draft:** `Content Type: prior_context_pack`, `Platform: notion_only`,
  `Event Phase: pre_event`, `Content Status: needs_review`, icon 🗃️; body = the full pack
  (page-index callout per gotcha `i`). Relations to Event/People/Topics are set once the
  Event row exists (Step 4) — if it doesn't exist yet, create the Content Draft now and let
  `notion-writer` relink + mirror it in Step 4.
- The Event-page mirror (a `## Prior-Context Pack` section) is appended by `notion-writer`
  in Step 4 (see 4e).

Then move to Step 2 — pass each specialist its relevant pack slice, and the Continuity
Ledger + Graph Signals to the synthesizer (Step 2.5).

---

## Step 2: Research

Research each entity using the triage from Step 1.5. **Scope of research is set by the
triage path, not by uniform depth.**

- **NEW** entities → full research per the sources below (existing behavior).
- **REFRESH (full)** → full research, same as NEW. Tag findings with date so merge semantics
  in Step 4 can reconcile with the existing record.
- **REFRESH (light)** → narrow research scope:
  - Company: funding changes since last researched date, news from last 90 days, leadership changes
  - Person: public activity (talks, posts, podcasts) since last researched date
  - Topic: Current Events only — what's new in the last 45 days
- **SKIP** → no research. Reuse existing Notion record content when building the brief
  and content drafts.
- **APPEND-CURRENT-EVENTS-ONLY** (Topics) → Current Events research only; skip Opportunities,
  Challenges, Use Cases, and Top Questions — those are reused from the existing record.

Use web search aggressively — current information is the value.

**Three research layers the Deep Read depends on (added 2026-08-21 — YED-136).** The specialists now
gather three things beyond today's snapshot, because the Deep Read (Step 4.5) is prose that needs them:
1. **Historical spine** — topic lineage (origin of the debate, prior approach, the inflection); company
   founding-thesis → funding-arc → evolution → today; person career arc / how their POV formed. *Facts
   and dates with sources*, not prose — the renderer writes the prose.
2. **Novice on-ramp** — the *mechanism* behind key claims (how it actually works, in plain terms) + the
   jargon a newcomer must know, named so the renderer can define it inline. Common, uncontested technical
   background needs no citation; specific/recent/contestable claims (funding, CVE, metric, positioning) do.
3. **A URL-carrying Evidence Ledger** per entity — every specific/recent/contestable claim as a row with
   its `tier · source · url · date`. The Deep Read's endnotes are built **only** from these ledgers; a
   claim with no row can't be cited downstream. Contract: the specialist agent files' "Evidence Ledger" section.

**Verbatim source-text rule (added 2026-06-23 — fidelity fix).** The raw calendar `description` is the source of truth and must reach every research subagent UNCHANGED, quoted as a `VERBATIM SOURCE` block, with any parsed-entity list or framing presented *alongside* it (supplementary), never *instead of* it. Entity parsing is a lossy summary: it reliably captures names but drops talk-abstract wording, explicitly-named themes (e.g. "partnerships", "go-to-market strategy"), attendee-mix cues, agenda ordering, and timezone notes. A 2026-06-23 defect built an entire run's outputs off the summarized artifact alone — entities survived, nuance did not. Rule: read the full description, extract everything, and only then layer framing on top. Same discipline applies to the synthesizer (it receives the raw invite) and to any hole-check (diff outputs against the verbatim text, not the summary).

**Gmail as a research source (added 2026-06-21).** Before researching any person or company, check Alex's mailbox for prior correspondence — it is the highest-signal context he has and the web cannot see it (an existing thread, a prior intro, a warm contact, a cold-outbound already sent, an open deal). The `person-researcher` and `company-researcher` agents now carry `mcp__claude_ai_Gmail__search_threads` + `mcp__claude_ai_Gmail__get_thread` for this. Gmail is a connected MCP on an existing free quota (no incremental cost — automate per CLAUDE.md MCP rule 1). Report only what the mailbox actually shows; never fabricate a relationship; summarize relationship state rather than pasting private contents into public-facing drafts. A found thread flips prioritization toward re-engage and changes the connection-note angle from cold-open to follow-up. **Registry caveat:** the agent registry is session-frozen, so if a run's agents predate this change, the parent thread should run the Gmail searches and pass the correspondence into the synthesizer.

### 2a: Topics & Subtopics

**Sources:** Claude training data (deep knowledge) → WebSearch (current developments)

For each topic, research across these five dimensions:

**Current Events** — What's dominating the narrative right now?
- The most notable, impactful, trending stories with the largest share of voice
- Recent product launches, papers, shifts in consensus, major announcements
- What people in this space are actually talking about this week/month

**Opportunities** — What are the upsides?
- Potential benefits and positive impacts of this topic area
- Where the momentum and investment are flowing
- What becomes possible that wasn't before

**Challenges** — What are the shortcomings and trade-offs?
- Known limitations, risks, and downsides
- Active debates and disagreements in the community
- What's overhyped vs. what's real

**Use Cases & Practical Applications** — Where is this working in the real world?
- Current deployments and their measurable impact
- Enterprise implementations and results
- Notable examples that demonstrate the topic and its related technology in practice

**Top Questions** — 3 questions Alex could ask that would signal depth without
requiring deep technical fluency

**Research depth target:** Enough for Alex to hold a 5-minute conversation with an expert
and ask follow-ups that demonstrate genuine engagement, not surface knowledge.

### 2b: People (Hosts & Speakers)

**Sources:** Gmail (prior correspondence — check first) → WebSearch (LinkedIn profiles, recent talks, articles, podcasts) → Claude training data

For each person:
- **Prior correspondence (Gmail):** has Alex emailed this person before? Summarize relationship state + most recent date. Drives prioritization (existing thread = re-engage) and the connection-note angle (follow-up, not cold-open). Omit if nothing found.
- Current role and company (verify — titles change)
- What they're known for / their public POV on topics relevant to this event
- Recent public activity: talks, posts, articles, podcast appearances (last 6 months)
- Connection angles: shared interests, mutual topics, things Alex could reference
- What they likely care about based on their work (not generic compliments)

**Talking Points (split personal / professional)** — explicit extraction for on-site recall:
- **Personal hook** — one concrete thing (not a generic compliment). A recent post, a shared
  background detail, a non-work interest surfaced publicly, a mutual connection. Must be
  referenceable in 10 seconds without notes.
- **Professional hook** — one concrete thing tied to their work. A recent shipped product,
  a public POV they've staked, a challenge they've named in their domain, a talk they gave.
  Must connect to something Alex can plausibly engage on (not just echo).

If either hook can't be sourced honestly, write "None found — engage off topic discussion
in the room" rather than inventing one. Fake hooks are worse than no hooks.

**Prioritization Signals** — how Alex should allocate attention in the room:
- **Prioritize because:** 1–3 positive signals (hiring for X, recent POV on Y that Alex
  disagrees with, mutual connection to Z, operator at a target AI-native company, etc.)
- **De-prioritize because:** 0–2 concerns (dormant / off-topic scope / timing misaligned /
  mismatch with Alex's goals for this event). OK to leave empty.
- **Open on-site:** 1–3 questions Alex wants to learn live that he couldn't find via
  research (what's their actual lane, is the team growing, what are they building next).
  These are internal decision-support — distinct from the public "prepared questions"
  generated in pre-event content.

This block is NOT a sales-qualification exercise. It's an attention-allocation filter so
Alex knows before walking in where to spend the 20–40 minutes he'll actually get in the room.

**Important:** Search for "[Name] [Company]" AND "[Name] [Topic]" to find relevant content.
If someone is not findable via web search, note that honestly — don't fabricate a bio.

**Thesis / POV sourcing (added 2026-05-26):** any *positioning or belief* claim about a person or their org ("their thesis is X", "they bet on Y over Z", "they believe W") must cite a primary source inline. If you can't source it, put it under Verification Flags as "unverified thesis claim — source-check before public use" — never state it as fact. These claims flow into public posts and connection notes the person may read; an unsourced one is a credibility risk.

### 2c: Companies

**Sources:** Gmail (prior correspondence with anyone at the company — check first) → WebSearch (funding, product news, press) → Claude training data (industry positioning)

For each company:
- **Prior correspondence (Gmail):** has Alex emailed anyone here? Summarize relationship state + most recent date (active deal, prior pilot, warm contact, cold-outbound sent). Omit if nothing found.
- What they do (1-2 sentences — assume Alex may not know)
- Recent news: funding rounds (amount if available), product launches, partnerships, leadership changes
- Industry/Space classification: AI/ML, Enterprise Software, Developer Tools, VC/Investment, Data Infrastructure
- Estimated funding stage: Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G, Series H, Series I, Public
  (NOTE: there is no "Pre-IPO" option — for late-stage private companies, use the most recent publicly-reported Series letter)
- Recent funding amount if discoverable (for "Recent Funding ($)" field)
- Why this company matters in the context of this event and Alex's goals
- Headwinds or challenges (shows Alex is informed, not just cheerleading)

**Thesis / positioning sourcing (added 2026-05-26):** any claim about a company's *thesis, strategy, or positioning* ("their fund bets on X over Y", "they're pivoting to Z") must cite a primary source. If unsourced, flag it under Verification Flags as "unverified — source-check before public use," not as fact. These claims reach public content.

### 2d: Documentarian Angle

**Source:** Claude reasoning (synthesizing all research above)

- What makes this event worth documenting? What's the narrative?
- What perspectives or moments are unlikely to be captured elsewhere?
- What would Alex's LinkedIn audience find valuable about a recap of this event?
- 1-2 angles for post-event content (these inform the Content Draft later)

### 2e: Success Signals

**Source:** Claude reasoning (synthesizing the research above with Alex's stated goals)

Define what "paying off" would look like for this specific event. These are the signals
to watch for during and after — and what the Step 7 retro will score against.
Set 3–5 signals, concrete enough to know after the fact whether each fired.

Pull from these categories (or define others if the event warrants):

- **Conversation signals** — specific person Alex wants to meet, specific question or POV
  he wants to test in the room, topic he wants to pressure-test with builders.
- **Relationship signals** — DM replies from Bucket A contacts, warm intro offers, meeting
  requests, explicit interest in a follow-up conversation.
- **Content signals** — engagement on the Tier 1 comment or Tier 2 post from speakers/hosts
  or people in the room, post-attributed profile visits, new connection requests citing
  the content.
- **Pipeline signals** — event-linked job-hunt advances (hiring manager contact made,
  referral secured, screener scheduled), project-ideation output that actually ships,
  intro to a target company Alex hasn't cracked yet.
- **Anti-signals** — observations that would make Alex downgrade this event or series for
  future attendance (e.g., "all speakers gave the same talk they gave 6 months ago";
  "room was all recruiters, no builders"; "host was more interested in selling than
  hosting").

**Quality bar:** each signal must be scorable as hit / partial / missed after the event
without post-hoc rationalization. "Had a great conversation" is not a signal. "Met at
least one operator at a target AI-native company and exchanged contact info" is a signal.

### 2f: Quick Take (synthesis — produce last)

**Source:** Claude reasoning (synthesizing 2a–2e after all other research is done)

A 2–3 sentence executive summary that sits at the top of the brief. Designed to be readable
on a phone during the commute to the event. Must answer three questions:

1. **Who is this room?** (one sentence — who actually shows up, not what the event description claims)
2. **Why does it matter for Alex specifically?** (one sentence — given his goals and the
   current state of his projects / job hunt / content lane)
3. **Best angle to work it?** (one sentence — the sharpest entry point, whether that's a
   specific person, a topic to pressure-test, or a documentarian framing)

**Quality bar:** if Alex reads only the Quick Take, he should know whether to go, who to
aim for, and what to pay attention to. No bullet points, no hedging. Three sentences max.

---

## Step 3: Present the Brief — the SCAN HEAD (ADR-5)

The brief is **one artifact with two layers** (ADR-5 · `.claude/proposals/event-field-guide.md`): a **Scan head** (in-room, phone-glanceable) and a **Deep Read** (the prose commute read). **Step 3 presents and commits the Scan head. The Deep Read is rendered and appended later, in Step 4.5, decoupled — a render failure never blocks this.**

The synthesizer returns two blocks: the **Scan head** and a `## Evidence Set` (URL-carrying, organized by render section). **Display only the Scan head to Alex** — the Evidence Set is internal fuel for Step 4.5, not brief content. Use this exact head structure:

```
## Event Research Brief: [Event Name]
**Date:** [date] | **Location:** [location]
*Scan head — the in-room layer. A prose Deep Read is appended after you approve (Step 4.5).*

### Quick Take
[2–3 sentences: who this room is, why it matters for Alex, best angle to work it.
Mobile-readable — this is the commute-scan summary.]

### People at-a-glance
[Per person — the 10-second resolution. Full career-arc prose lives in the Deep Read, NOT here:]
#### [Name] — [Title, Company] ([Role])
- *Who:* [one line]
- *Personal hook:* [one concrete thing — not a generic compliment]
- *Professional hook:* [one concrete thing tied to their work Alex can engage on]
- *Signals:* Prioritize — [1–3] · De-prioritize — [0–2 or "None"] · Open on-site — [1–3 to learn live]

### Questions to ask
[Consolidated from the research: topic Top Questions + per-person Open-on-site, de-duped and
grouped. In-room questions only — NOT pre-event-content's outbound prepared questions.]

### Success Signals
[3–5 concrete signals: what would make this event a win; include at least one anti-signal]

### Verification Flags
[Every unverified/unsourced/ambiguous item — mismatched domains, ambiguous identities,
unsourced thesis/positioning claims. Surfaced here, never silently resolved.]

---

**This is the scan layer.** On approval I'll (1) write entities to Notion + HubSpot, then
(2) render and append the prose **Deep Read** (~45-min commute read) beneath it.
Any changes before I proceed?
```

**What is NOT in the head:** the topic/company bullet lattice. That depth is now the **Deep Read** (Primer/Landscape + Companies), rendered in Step 4.5 from the Evidence Set. Putting the lattice in the head is the regression this design exists to remove. The Documentarian Angle also drops out of the head as a standalone section — it lives as the Quick Take's "best angle" line, and the full continuity narrative becomes the Deep Read's Cross-Event Threads.

**Wait for Alex's approval.** He may want to:
- Add or remove people/companies
- Adjust research depth on specific entities
- Correct factual errors
- Add context he has that web search didn't surface

Iterate until Alex says to proceed. Then move to Step 4.

---

## Step 4: Write to Notion

Write to all 5 databases in dependency order. Capture page URLs at each step for relations.

### 4a: Apply Triage Actions (GATE — set by Step 1.5)

Dedup and freshness classification already happened in Step 1.5. This gate converts that
plan into a per-entity action before hitting the API:

- **NEW** → create new page (sections 4b/4c/4d create paths).
- **SKIP** → do NOT open the page body; do NOT overwrite properties. Only action: add the
  new Event URL to the entity's Events relation in Step 4e (via the Event's People/Companies/
  Topics relation fields, which auto-populate the reverse side).
- **REFRESH (light | full)** → follow the per-entity refresh path in 4b/4c/4d (Company
  audit-trail, Topic merge rules, Person selective-overwrite).
- **APPEND-CURRENT-EVENTS-ONLY** (Topics only) → follow Topic refresh path in 4c, scoped
  to the Current Events property + page body.

If Step 1.5 was skipped or its result is missing, stop and re-run 1.5 before any writes.
Do not silently fall back to "create always."

### 4b: Create / Refresh Companies

**Database:** `collection://d5910dc3-8327-4b49-9294-fc9499709a98`
**Parent:** `data_source_id: d5910dc3-8327-4b49-9294-fc9499709a98`

#### Create path (NEW)

Create a page with these properties:
```
"Company Name": "[company name]"                    — title
"Description": "[1-2 sentence description]"         — text
"Website": "[url]"                                  — url
"Industry / Space": "[\"AI/ML\", ...]"              — multi_select (JSON array)
"Funding Stage": "[stage]"                          — select (one of: Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G, Series H, Series I, Public)
"Recent Funding ($)": [amount as number, or null]   — number
"Recent Developments": "[recent news summary]"      — text
"date:Last Researched:start": "2026-04-09"          — date (use today's date)
"date:Last Researched:is_datetime": 0               — integer
```

Page body content: expanded company research (full analysis from Step 2c).

#### Refresh path (REFRESH light | full)

Do NOT overwrite the company page blindly. Steps:

1. **Audit trail** — before any property write, append a dated block to the **Event page
   body** (created in 4e) capturing the prior Company.Recent Developments text:
   ```
   ### Prior [Company] snapshot (as of [prior Last Researched date])
   [prior Recent Developments text]
   ```
   This preserves history without bloating the Company record.

2. **Update in place** — on the existing company page:
   - Overwrite: `Recent Developments` (fresh research replaces stale), `Funding Stage`
     (if changed), `Recent Funding ($)` (if changed), `date:Last Researched:start` (today).
   - Merge: `Industry / Space` multi-select — union new values with existing, don't drop
     existing tags Alex may have hand-curated.
   - Leave alone: `Company Name`, `Description` (unless Description is empty), `Website`
     (unless empty or the domain has genuinely changed via M&A).

3. **Page body** — append a new dated section with the refreshed research:
   ```
   ## Refresh [YYYY-MM-DD] — [Event Name] context
   [new research]
   ```
   Don't delete prior body content.

#### Skip path (SKIP)

No write. The Event's Companies relation in 4e picks up this company via its existing URL.

#### Notion create-pages gotchas (learned the hard way — do not rediscover these)

1. **Multi-select properties take a JSON-array-*string*, not a comma-separated string and not a native array.**
   - ✅ Correct: `"Industry / Space": "[\"AI/ML\",\"Enterprise Software\"]"`
   - ❌ Wrong (rejected): `"Industry / Space": "AI/ML,Enterprise Software"`
   - ❌ Wrong (rejected): `"Industry / Space": ["AI/ML","Enterprise Software"]` (native array)
   - Same pattern applies to People.Role Context multi_select.

2. **Select properties must exactly match a defined option.** If the API returns `Invalid select value for property "Funding Stage": "Pre-IPO"`, the error message lists the valid options — trust the error, not the doc. The Companies DB has NO `Pre-IPO` option; use `Series F`/`Series G`/etc. for late-stage private companies.

3. **Relations take a JSON-array-string of full page URLs** (not bare page IDs). Use the `url` field returned by create-pages exactly as-is.
   - ✅ `"Company": "[\"https://www.notion.so/347d3699c2db818aa325c06cc5777252\"]"`

4. **Date properties must use expanded format:**
   - `"date:Last Researched:start": "2026-04-18"` (date-only)
   - `"date:Last Researched:is_datetime": 0` (0 = date only, 1 = includes time)
   - For events with specific times: `"date:Event Date:start": "2026-04-20T18:00:00-04:00"` + `"date:Event Date:end": "2026-04-20T20:00:00-04:00"` + `"date:Event Date:is_datetime": 1`

5. **Before any batch create, verify live schema via `notion-fetch` on the data source URL.** The schema is authoritative; skill docs and CLAUDE.md can drift. If a validation error fires, the API error text lists the exact valid option set — use that.

6. **Write order matters (bidirectional relations).** Create Companies + Topics first (no dependencies), then People (needs Company URLs), then Event (needs People + Companies + Topics URLs), then Content Draft (needs Event URL). Skipping the order causes relation fields to come back empty.

**Capture page URLs for every company (created, refreshed, or skipped — you need URLs for People and Event relations).**

### 4c: Create / Refresh Topics (can run parallel with 4b create paths)

**Database:** `collection://d61ce9df-94b3-4637-aa09-d77e09ab3a74`
**Parent:** `data_source_id: d61ce9df-94b3-4637-aa09-d77e09ab3a74`

#### Create path (NEW)

For each new topic:
```
"Topic": "[topic name]"                                          — title
"Current Events": "## [Event Name] — [YYYY-MM-DD]\n[new research]" — text (dated block format)
"Opportunities": "[upsides, benefits, potential impacts]"        — text
"Challenges": "[shortcomings, trade-offs, downsides]"            — text
"Use Cases & Practical Applications": "[real-world deployments, enterprise examples, impact]" — text
"Top Questions": "[3 smart questions]"                           — text
"date:Last Updated:start": "2026-04-09"                          — date (use today's date)
"date:Last Updated:is_datetime": 0                               — integer
```

Note: even on create, format `Current Events` as a dated block so the refresh path can
always append consistently.

Page body content: expanded topic research (full analysis from Step 2a).

#### Refresh path (REFRESH selective merge | full)

Topics accumulate; they don't overwrite. Merge rules per property:

- **Current Events** (always append a new dated block):
  ```
  ## [Event Name] — [YYYY-MM-DD]
  [new research]
  ```
  Prepend the new block to the top of the property value (newest first).
  **Rolling cap: keep max 6 dated blocks.** If adding the 7th, drop the oldest.
  Soft char budget: if the full property would exceed ~1500 chars after appending,
  truncate older blocks aggressively (drop older beyond the 6-cap) before adding new.

- **Opportunities** / **Challenges** / **Use Cases & Practical Applications** — merge
  with dedup. Parse each as a bullet list; add new bullets not already present (fuzzy
  match on first 40 chars, lowercase). Never drop existing bullets; Alex may have
  hand-edited them.

- **Top Questions** — append new questions to the existing list, cap at ~10 total.
  If adding would exceed 10, drop the oldest questions first.

- `date:Last Updated:start` — today.

#### Append-current-events-only path (Topic ≤45 days)

Only touch Current Events (append dated block per above rules) and `date:Last Updated:start`.
Do not touch Opportunities, Challenges, Use Cases, or Top Questions.

#### Skip path

Not a Topic triage outcome — Topics always get at least APPEND-CURRENT-EVENTS-ONLY when
they match. The only way a Topic gets no write is if Alex overrides in 1.5d.

**Capture page URLs for every topic (created, refreshed, or append-only).**

### 4d: Create / Refresh People

**Database:** `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86`
**Parent:** `data_source_id: 4a1af67f-9141-4ba5-aa9d-88b07dcd5f86`

#### Create path (NEW)

For each new person:
```
"Name": "[full name]"                               — title
"Current Title": "[title]"                          — text
"Email": "[email if known]"                         — email (often empty pre-enrichment)
"LinkedIn URL": "[url if found]"                    — url
"Known POV / Bio": "[what they're known for]"       — text
"Notes": "[talking points (personal / professional hooks), prioritization signals, open on-site questions]"  — text
"Role Context": "[\"speaker\", \"host\", ...]"      — multi_select (JSON array)
"Company": "[company page URL from Step 4b]"        — relation (JSON array of page URLs)
"date:Last Researched:start": "2026-04-09"          — date
"date:Last Researched:is_datetime": 0               — integer
```

Page body content: expanded person research (full analysis from Step 2b), structured as:
- `## Bio / Known POV`
- `## Recent Activity`
- `## Talking Points` (Personal hook / Professional hook — split, one each)
- `## Prioritization Signals` (Prioritize because / De-prioritize because / Open on-site)

#### Refresh path (REFRESH light | full)

Selective overwrite — most properties on a Person record are sticky; only a few should
change per event.

- Overwrite: `Current Title` (people change jobs), `Known POV / Bio` (public POV evolves),
  `date:Last Researched:start` (today).
- Merge (union, no drops): `Role Context` multi-select — if this event adds a new context
  (e.g., "organizer" in addition to prior "speaker"), add it.
- Fill-if-empty only: `Email`, `LinkedIn URL` — if triage found a stronger identifier
  missing from the record, backfill it. Never overwrite a non-empty email or LinkedIn.
- `Company` relation — if the person has switched companies, add the new Company URL to
  the relation. Keep the prior company in the relation (career history is useful).
- `Notes` — append a dated section, don't overwrite:
  ```
  ## [Event Name] — [YYYY-MM-DD]
  [new connection angles, recent public activity]
  ```

Page body: append a new dated research section, same pattern as Companies refresh.

#### Skip path (SKIP)

No write. Person's Events relation auto-populates from the Event's People relation in 4e.

**Capture page URLs for every person (created, refreshed, or skipped).**

### 4e: Create Event

**Database:** `collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`
**Parent:** `data_source_id: 9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`

```
"Event Name": "[event name]"                        — title
"date:Event Date:start": "2026-04-15"               — date (actual event date)
"date:Event Date:is_datetime": 1                    — integer (1 if time known, 0 if date only)
"Location": "[venue + address]"                     — text
"Event Description": "[raw pasted invite text]"  — text
"Event Status": "intake"                            — select
"People": ["[person URL 1]", "[person URL 2]"]      — relation (JSON array)
"Companies": ["[company URL 1]", ...]               — relation (JSON array)
"Topics": ["[topic URL 1]", ...]                    — relation (JSON array)
```

**Relations include ALL entities from triage — created, refreshed, AND skipped.** The
whole point of the triage is that SKIP still links the existing record to this Event.

Page body content: the full research brief from Step 3 (formatted in markdown), PLUS any
"Prior [Company] snapshot" audit-trail blocks from 4b refresh paths.

**Structure the Event page body with these top-level sections so Step 4.5 and the Step 7 retro can
find and append cleanly (ADR-5 two-layer brief):**
- `## Quick Take` (2–3 sentence synthesis from 2f — first block, mobile-readable)
- `## Research Brief` (the **Scan head** from Step 3: People at-a-glance, Questions to ask, Verification Flags — NOT the old topic/company lattice; that depth is the Deep Read)
- `## Success Signals` (3–5 signals from 2e)
- `## Deep Read` — **leave empty here with a `<!-- deep_read_rendered: pending -->` marker; Step 4.5 renders and appends the prose Deep Read under it, decoupled, after this write commits.** Never block the Step-4 commit waiting on it.
- `## Prior Snapshots` (any audit-trail blocks from 4b Company refreshes — omit section if none)
- `## Prior-Context Pack` (append-only mirror of the Step 1.7 pack, if one was produced — the readable side-by-side surface; the canonical copy is the `prior_context_pack` Content Draft from 1.7c. Omit section if this was a first-touch event with no prior context. Relink the `prior_context_pack` Content Draft's Event/People/Topics relations to this Event row here.)
- `## Retro` — leave empty; Step 7 appends here after the event

**Capture the Event page URL.**

### 4f: Create Content Draft (Research Brief)

**Database:** `collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`
**Parent:** `data_source_id: 6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`

```
"Title": "[Event Name] — Research Brief"            — title
"Content Type": "research_brief"                    — select
"Event Phase": "pre_event"                          — select
"Content Status": "needs_review"                    — select
"Platform": "notion_only"                           — select
"Event": ["[event URL from Step 4e]"]               — relation (JSON array)
"People": ["[person URL 1]", ...]                   — relation (JSON array)
"Topics": ["[topic URL 1]", ...]                    — relation (JSON array)
```

Page body content: the **Scan head** (same as the Event page's `## Research Brief` +
`## Quick Take` + `## Success Signals` + `## Verification Flags`), plus an empty
`## Deep Read` section carrying the `<!-- deep_read_rendered: pending -->` marker. Step 4.5
appends the rendered prose Deep Read here too, so Alex gets the full two-layer artifact from
either the Event or the Content Drafts view. Having it in both places means the content
pipeline (`pre-event-content`, etc.) can read the one richer brief from Content Drafts.

#### Re-run path (Event already exists — the corrections case, v1.2, YED-132)

When Step 1.5b detected a **re-run** of the same Event (matching `Google Calendar Event ID`,
else title+date), a `research_brief` Content Draft already exists from the prior run — and a
re-run's whole value is often *corrections* the verify pass produced (e.g. a mis-sourced thesis,
a stale funding/stat number). Do **NOT** create a second `research_brief`: the stale copy is what
`pre-event-content` would read. Instead:
- **Update the existing `research_brief` Content Draft body in place** with the freshly-synthesized
  (corrected) brief; keep `Content Status: needs_review`.
- **Replace the Event page `## Research Brief` section** with the corrected brief (this one section
  is replaced; everything else on the page stays append-only).
- **Audit-trail the change:** prepend a one-line note to both —
  `> Re-researched [date] — corrections: [what changed, e.g. "Claygent 1B→5B runs; framework attribution Berry→Amin; dropped unverified deliverability benchmarks"]`.
This is what makes a verify-pass correction actually reach downstream content. Without it the
corrected facts live only in the `prior_context_pack` and the content flow keeps reading the stale
brief.

### 4g: Confirm Notion Writes

After all pages are created/refreshed/skipped, report:
> **Notion writes complete:**
> - Companies: [X created, Y refreshed, Z skipped] ([names per bucket])
> - Topics: [X created, Y refreshed, Z append-only] ([names per bucket])
> - People: [X created, Y refreshed, Z skipped] ([names per bucket])
> - Event: [name] created
> - Content Draft: research brief created
>
> All relations linked. [any issues to flag]

---

## Step 4.5: Render + append the Deep Read (ADR-5 — decoupled, additive)

The Deep Read is the prose "commute read" half of the one brief. It is rendered **after** Step 4
has committed the Scan head + entity records, and **appended** under the `## Deep Read` marker.
This phase is **decoupled and non-blocking**: a render failure is a warning, never a pipeline
failure — the Scan head, the entity records, and the content pipeline are already intact and
depend on nothing here (ADR-5 Decision 3). Runs **in the parent thread** — the render dispatches
and the Notion append both happen inline (MCP writes are parent-thread only;
[[project_notion_writes_must_be_parent_thread]]).

**Precondition (GATE):** Step 4 confirmed the Scan-head write (4g). If Step 4 didn't commit, do
NOT render — fix Step 4 first. Never render into a page that doesn't exist yet.

### 4.5a: Assemble render inputs

From the synthesizer's `## Evidence Set` (organized by render section, URL-carrying) plus event
meta, build the per-section evidence slices `field-guide-renderer` expects
(`.claude/agents/content/field-guide-renderer.md`). Pass each renderer call:
- **Mode:** `render-section: <section>`
- **Event meta:** name, date, location, Alex's stated focus/goals, and how novice he is on this material.
- **The evidence slice for that section** — the URL-tagged rows from the Evidence Set, tiers intact.
- **The Scan head** (for consistency — the renderer must not contradict it).

### 4.5b: Render section-by-section (one renderer call per section, in order)

Dispatch `field-guide-renderer` (Opus) **once per section**, in this order, waiting for each:

| # | Section | Skip when |
|---|---|---|
| 1 | The Frame | never (always render — it's the orientation) |
| 2 | Primer / Landscape | no topics researched |
| 3 | Companies | no companies researched |
| 4 | People | no people researched (all SKIP / none named) |
| 5 | Cross-Event Threads | first-touch event / no Continuity Ledger |

**Never ask the renderer to write the whole Deep Read in one call** — it collapses in the back
half (renderer contract). One section per call. If a section's evidence slice is thin, the
renderer's anti-padding gate makes it write 2–3 honest sentences and stop — that's correct, not
a failure. If a renderer call returns a `> Gap:` note (e.g. a `web-verified` fact missing its
URL), keep it in the output and surface it to Alex; it flags a URL to attach before public reuse.

### 4.5c: Stitch

Dispatch `field-guide-renderer` in **`stitch`** mode with all rendered sections in order. It adds
the "how to read this" opener, smooths transitions into one voice, and consolidates endnotes into
one numbered list — **without adding, changing, or removing any fact or citation.** The result is
the final Deep Read.

### 4.5d: Append under the marker (parent-inline, idempotent)

Replace the `## Deep Read` section on **both** the Event page and the `research_brief` Content
Draft with the stitched Deep Read, and flip the marker `<!-- deep_read_rendered: pending -->` →
`<!-- deep_read_rendered: [YYYY-MM-DD] -->`. Everything else on the page stays append-only; only
this one marked section is replaced (idempotent — a re-run replaces just the Deep Read).

- Use `notion-update-page` with **real newlines**, not `\n` escapes (gotcha m /
  [[project_notion_updatepage_newline_gotcha]]).
- The `## Deep Read` body reads cleanly aloud (endnotes, no inline URLs) — it's the substrate for
  a later audio step and for `pre-event-content`.

### 4.5e: Confirm (or warn)

> **Deep Read appended:** [N sections rendered · M skipped (reason) · ~W words] — Event page + Content Draft updated.
> [Any `> Gap:` notes: e.g. "Primer endnote [5] missing URL — attach before public reuse."]

If the render phase failed entirely, report it as a **warning** and leave the marker `pending`:
> ⚠️ **Deep Read not rendered** — [reason]. The Scan head + all entity records committed fine and
> the content pipeline is unaffected. Re-run just Step 4.5 to append the Deep Read (idempotent).

---

## Step 5: Write to HubSpot

### 5.0: HubSpot recurrence check (run before any create)

Mirror the Notion triage logic at the CRM layer. HubSpot has its own dedup rules — don't
rely on them alone.

**Companies** — search by domain first (exact match on `domain` property), fall back to
exact name match.
- Match → capture existing company HubSpot object ID; route to 5a refresh path.
- No match → route to 5a create path.

**Contacts** — search in this priority order:
1. Exact match on `email` (if email known)
2. Exact match on `firstname` + `lastname` + associated company
- Match → capture contact object ID; route to 5b refresh path.
- No match → route to 5b create path.

**Notes** — always create a new Note per event. Notes accumulate as event history; never
update or dedup Notes. This is the primary event-tracking mechanism.

### 5a: Create / Refresh Companies in HubSpot

#### Create path
For each new company, use `manage_crm_objects` with createRequest:
```json
{
  "objectType": "companies",
  "properties": {
    "name": "[company name]",
    "domain": "[company website domain]",
    "description": "[1-2 sentence description]"
  }
}
```

#### Refresh path
For matched companies:
- Update `description` only if it was empty or the current description is clearly stale
  (different product/positioning language).
- Do NOT touch `name` (HubSpot dedup keys on name+domain — changing name creates fragility).
- Do NOT touch `domain` unless verified corrected.
- Never set `industry` (per CLAUDE.md — generic categories are unhelpful).

**Present the confirmation table as required by HubSpot MCP before creating.**
Capture returned / existing company object IDs.

### 5b: Create / Refresh Contacts in HubSpot

#### Create path
For each new person, use `manage_crm_objects` with createRequest:
```json
{
  "objectType": "contacts",
  "properties": {
    "firstname": "[first name]",
    "lastname": "[last name]",
    "email": "[email if known]",
    "phone": "[phone if known]",
    "company": "[company name]",
    "jobtitle": "[title]"
  },
  "associations": [
    {
      "targetObjectId": [company HubSpot ID],
      "targetObjectType": "companies"
    }
  ]
}
```

#### Refresh path
For matched contacts:
- Update `jobtitle` ONLY if it has materially changed from the record (different title text,
  case-insensitive diff).
- Update `company` ONLY if the person has moved to a different company since last event
  (in that case, also update the company association to the new company's HubSpot ID).
- Never touch `email`, `phone`, `firstname`, `lastname` on an existing record. These are
  sticky identifiers; overwrites cause CRM data rot.
- If the contact exists but has no company association, add it.

**Present the confirmation table before creating.** Ask Alex to waive confirmations
for the session if there are many contacts.
Capture returned / existing contact object IDs.

### 5c: Create Notes on Contacts

For each contact (created or refreshed), always create a fresh Note per event:
```json
{
  "objectType": "notes",
  "properties": {
    "hs_note_body": "[Event Name]"
  },
  "associations": [
    {
      "targetObjectId": [contact HubSpot ID],
      "targetObjectType": "contacts"
    }
  ]
}
```

Notes never get deduped — each event creates a new Note. This is intentional: the Notes
stream on a contact IS the event history.

### 5d: Confirm HubSpot Writes

> **HubSpot writes complete:**
> - Companies: [X created, Y matched (refreshed or no-op)]
> - Contacts: [X created, Y matched] (with company associations)
> - Notes: [count] attached to contacts
>
> [any issues to flag]

---

## Step 6: Summary

Present a final summary:

```
## Research Complete: [Event Name]

### Notion
- Event page: [link]
- Companies: [X created, Y refreshed, Z skipped] ([names])
- People: [X created, Y refreshed, Z skipped] ([names])
- Topics: [X created, Y refreshed, Z append-only] ([names])
- Content Draft: research brief (needs_review)

### HubSpot
- Companies: [X created, Y matched]
- Contacts: [X created, Y matched] (with notes)
- Notes: [count] attached

### Next Steps
- Review the research brief in Notion Content Drafts
- When ready for pre-event content (LinkedIn posts, DMs, outreach), invoke the
  content generation skill (Phase 2 — coming soon)
- After you attend the event (within 24h, ideally same night), invoke Step 7 retro
  capture, then hand raw observations to content-correspondent for post-event content.
```

---

## Step 7: Post-Event Retro (Invoke After Attendance)

Event research doesn't end at the event. After attending, capture signal outcomes and
raw observations back to the Event page so the measurement surface compounds across
events. Over time, this is what powers event-tier scoring and the Signal Layer dashboard.

**When to invoke:** within 24h of attendance, ideally same night while memory is live.
**What it produces:** a dated `## Retro` block appended to the Event page body.
**Relationship to the v2 Post-Event Brief (YED-96):** the `## Retro` is the short **signal scorecard** (did the Success Signals fire? event tier?). The **comprehensive** post-event record — the full learnings-tier `post_event_brief` (whole-quote bank, pro-tips/pitfalls/hot-takes, enriched concept glossary) — is produced separately by **`/post-event-content`** and appended to the SAME Event page as `## Post-Event Brief`. The page ends up with `## Research Brief` (pre) + `## Retro` (signal scoring) + `## Post-Event Brief` (the exhaustive post record) — pre + post side-by-side. Keep the Retro short; don't duplicate the brief's content here — link to it.
**How it integrates with content-correspondent:** retro captures signal outcomes and raw
observations; content-correspondent turns observations into DMs, comments, and posts.
**Run retro first, then hand raw notes to content-correspondent.**

### 7a: Retro capture template

Append this block under the existing `## Retro` section of the Event page body:

```
## Retro — [YYYY-MM-DD]

### Signal outcomes
[For each Success Signal from the brief, mark hit / partial / missed with one-line evidence]
- [Signal 1 description]: [hit | partial | missed] — [evidence]
- [Signal 2 description]: [hit | partial | missed] — [evidence]
- ...

### Observations
[3–5 raw observations worth capturing: quotes, tensions, surprises, patterns across
multiple conversations. These are the seed material for content-correspondent.]

### Event tier
[A | B | C — one-sentence rationale]
- **A** — attend every instance; signals consistently fire
- **B** — attend when topic is hot or a specific target is there
- **C** — skip unless a specific Bucket A contact is confirmed attending

### Anti-signals fired
[Any anti-signals from the brief that fired? If so, flag for future event selection
and topic/host filtering.]

### Carryover
[1–2 things that didn't resolve and should carry into next event or next outreach round.
Example: "Didn't get to finish the conversation with [person] about [topic] — queue for
follow-up DM with a content hook."]
```

### 7b: What NOT to write to the Event page

- Don't paste full DM drafts or post drafts here — those live in content-correspondent
  output and the Content Drafts database.
- Don't write private commentary about individual attendees. The Event page is the
  shared artifact; attendee-specific notes belong on the People pages.
- Don't repeat the research brief. The retro is the delta, not a restatement.

### 7c: Update entity records from retro

If the retro surfaced new information about a specific Company, Person, or Topic
(e.g., the company's actual roadmap came up, a person shared their POV on a topic),
append a short dated note to the relevant Notion record:

- **Company** — append to `Recent Developments` using the 4b refresh format:
  `## Refresh [YYYY-MM-DD] — from [Event Name] retro\n[new info]`
- **Person** — append to `Notes` using the 4d refresh format:
  `## [Event Name] — [YYYY-MM-DD]\n[new connection angle or POV observed]`
- **Topic** — append to `Current Events` using the 4c refresh format:
  `## [Event Name] — [YYYY-MM-DD]\n[new observation or shift in the narrative]`

Keep these updates short (2–3 sentences). The Retro block on the Event page is the
primary artifact; these are just the cross-references so the entity records stay fresh.

### 7d: Handoff to content-correspondent

After the retro block is written, invoke content-correspondent with the `Observations`
section as input. content-correspondent will produce bucket sorting, DMs, Tier 1 comment,
and Tier 2 post.

### 7e: Confirm retro complete

> **Retro complete: [Event Name] ([YYYY-MM-DD])**
> - Signals scored: [hit count] hit, [partial count] partial, [missed count] missed
> - Event tier: [A | B | C]
> - Anti-signals fired: [yes/no — if yes, what]
> - Entity records updated: [count] ([Company/Person/Topic names])
> - Next: invoke content-correspondent with observations

---

## Error Handling

- **MCP tool fails:** Report the error immediately. Do NOT silently retry or fall back.
  Tell Alex exactly what failed and offer to retry or skip that step.
- **Web search returns nothing useful:** Say so honestly. Note what you searched for and
  that results were thin. Use Claude training data as fallback but flag the lower confidence.
- **Notion relation fails to set:** This is the most likely failure point. If a relation
  doesn't set, verify the page URL format and retry once. If it fails again, log it and
  move on — Alex can set it manually in Notion.
- **HubSpot duplicate detected:** HubSpot may reject a contact creation if the email already
  exists. The 5.0 recurrence check should have caught this — if it still fires, it means
  dedup search missed a record. Switch to the 5b refresh path for that contact.
- **Step 1.5 triage missing:** If Step 4 is reached without a triage plan from 1.5, stop.
  Do not fall back to create-always. Re-run 1.5.
- **Step 7 retro invoked before Step 4 complete:** The retro expects the Event page to
  exist with the `## Retro` section placeholder. If the Event page wasn't created (Step 4
  was skipped or failed), stop and complete Step 4 first. Retros without an Event page to
  attach to are homeless.
- **Retro invoked without Success Signals in the brief:** If Step 2e was skipped, the
  signal-outcomes section of the retro has nothing to score. Either run 2e now
  retroactively (still useful — forces the "what would have been a win" question) or
  skip Signal Outcomes and keep Observations + Tier + Anti-signals only.
