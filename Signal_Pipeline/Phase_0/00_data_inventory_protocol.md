# Phase 0 — Data Inventory Protocol

**Status:** V0, 2026-04-21. Draft before first run; expect 2–3 iterations after actually executing against the data.
**Owner:** Alex. Ideally paired with Claude Code running the MCP queries.
**Time box:** 3–4 hours of focused work over 1–2 days. If it takes more, we got the scope wrong and should narrow.

---

## Why this exists

Before any signal-layer architecture gets drawn, we need to know what we actually have. The events pipeline has been running for real events — there is real data in the 6 Notion DBs + HubSpot + Alex's LinkedIn activity. That data is both (a) our only free, owned, high-signal training corpus and (b) the thing that tells us what "high-value signal" means *for Alex specifically* as opposed to "for a Clay customer."

If we skip this step and jump to watchlists + source stacks, we're guessing. Phase 0 is the anti-guess.

The output is three artifacts:
1. **Entity inventory sheet** — row counts, completeness, quality flags per DB.
2. **Content performance audit** — which of Alex's LinkedIn posts drove replies/DMs/visits, and what was different about them.
3. **Signal seed list** — the 5–10 concrete signal types that the data *itself* suggests are worth building the pipeline around.

Artifacts 1 and 3 live in this repo. Artifact 2 is a short writeup with whatever data Alex can export from LinkedIn (which is limited — use what's free).

---

## Rule: every query runs through MCP, not by hand

Notion MCP and HubSpot MCP are both live. Every number in the inventory sheet should be traceable to a live MCP query. Don't eyeball counts from the Notion UI — it's easy to miss hidden records and we'd lose trust in the baseline.

If a query fails, note it and move on — don't fabricate numbers. The point of the inventory is calibration, not a perfect score.

---

## Part A — Notion inventory (6 databases)

### A.1 — Row counts per database

For each DB, capture:

| DB | Data source ID | Row count | Created in last 30d | Last modified in last 30d |
|---|---|---|---|---|
| Events | `9dcbc999-b4ed-4a51-b48a-10aaf171f1ba` | TBD | TBD | TBD |
| People | `4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` | TBD | TBD | TBD |
| Companies | `d5910dc3-8327-4b49-9294-fc9499709a98` | TBD | TBD | TBD |
| Topics | `d61ce9df-94b3-4637-aa09-d77e09ab3a74` | TBD | TBD | TBD |
| Content Drafts | `6c24c9f5-66c9-4eed-a61d-3f9b87c3f775` | TBD | TBD | TBD |
| Project Ideas | `0956e6ed-8555-4d8f-8856-388966dedaab` | TBD | TBD | TBD |

**What the numbers tell us:**
- If Events / People / Companies are under ~20 rows each, signal discovery is underpowered; we'll need to seed with 2–3 more event runs before the signal work is meaningful. Flag and decide.
- If 30-day activity is thin, the pipeline has been dormant and we need to restart the event run cadence in parallel with Phase 0.

### A.2 — Property completeness per entity type

For each of the five entity DBs (skip Events — too heterogeneous by design), compute:

**People DB — completeness checks:**
- % with non-null `Email`
- % with non-null `LinkedIn URL`
- % with non-null `Current Title`
- % with non-null `Company` relation (at least one)
- % with non-null `Role Context` (at least one tag)
- % with non-null `Known POV / Bio`
- % with `Last Researched` within last 90 days

**Companies DB — completeness checks:**
- % with non-null `Website`
- % with non-null `Industry / Space` (at least one tag)
- % with non-null `Funding Stage`
- % with non-null `Recent Developments`
- % with `Last Researched` within last 60 days

**Topics DB — completeness checks:**
- % with non-null `Current Events`
- % with non-null `Opportunities` / `Challenges` / `Use Cases` / `Top Questions` (each)
- % with `Last Updated` within last 45 days

**Content Drafts DB — completeness checks:**
- Count by `Content Status` (needs_review / approved / scheduled / published / archived)
- Count by `Content Type`
- Count by `Event Phase` (pre / during / post)
- % with non-null `Published URL` (only counts against `published` status — that's the one where it should be set)

**Project Ideas DB — completeness checks:**
- Count by `Status` (needs_review / active / shipped / archived / deleted)
- % with `Composite Score` set
- Count with `Stack Coverage %` outside the 60–80% "sweet spot"

**What this tells us:**
- Low completeness on identity-like fields (`Email`, `LinkedIn URL`) means we can't dedup reliably, which means the hygiene layer has a real job. This is expected; we want to measure it.
- Low completeness on derived fields (`Industry / Space`, `Role Context`) means the enrichment side isn't firing. Less critical than identity gaps, but flags where hygiene tier-1 needs enforcement.
- High recency on `Last Researched` means the triage logic in event-research is doing its job. Low recency means we've had few event runs and the system hasn't been stress-tested.

### A.3 — Relation density

For a sample (all if small, 20 random rows if > 50) of each DB, count:
- People: avg # of Events per person, avg # of Companies per person, avg # of Content Drafts per person
- Companies: avg # of Events per company, avg # of People per company
- Topics: avg # of Events per topic, avg # of People per topic, avg # of Content Drafts per topic
- Events: avg # of People, Companies, Topics, Content Drafts per event

**What this tells us:**
- The interconnectedness of the graph. A person with many Events is a recurring contact; that's a pattern worth naming. A topic with many Events is a durable theme.
- Isolates — records with zero relations or only one. Isolates are either (a) orphans from early runs (hygiene tier-1 flags these) or (b) evidence that a whole event's relations never got written (skill bug).

### A.4 — The "who / what recurs" list

This is the high-signal output of Part A. Query:

- Top 10 People by Event count (who shows up at multiple events Alex attended?)
- Top 10 Companies by Event count (what companies are present across multiple events?)
- Top 10 Topics by Event count (what themes recur?)
- Top 10 People by Content Draft count (who is Alex actually writing about?)
- Top 10 Companies by Content Draft count (what companies is Alex actually writing about?)

**Why this is load-bearing:** this is the *revealed watchlist*. It's what Alex has actually found worth writing about, research-scrolling about, meeting multiple times. It's a stronger starting point for a signal-layer watchlist than any named list we'd construct from the Clay blog — because it's *us*, not Clay.

Compare it against the skills-map V1.1 named-operators list and the 7 Clay-blog companies. Overlaps, gaps, and novel entries all matter. Discussed in signal-discovery.

---

## Part B — Content performance audit

The goal here is to pair the Notion record of a Content Draft with whatever Alex can see about how that content performed. LinkedIn's free data is limited — use what's there, don't scrape.

### B.1 — What to pull for each published draft

For every Content Draft with `Content Status = published` and a `Published URL` set, capture whatever of these Alex can see on LinkedIn:

- **Date published**
- **Post length** (character count — approximate)
- **Reactions** (total)
- **Comments** (total + rough unique commenters)
- **Reposts** (if any)
- **Replies from targeted people** — did anyone from the People DB (esp. speakers/hosts) engage?
- **DMs received** (if attributable to this post — use judgment)
- **Profile visits** (LinkedIn shows a 7-day window — capture if proximate)
- **New connection requests** (if attributable)

### B.2 — Tag each post with its Content Type and a structural note

- Content Type from the Notion record (linkedin_post_pre / post / synthesis / etc.)
- Presence of: specific named person, specific named company, specific named topic, external link, image/visual, numbered list, question-ending
- Event-tethered? (pre_event / post_event) or standalone?

### B.3 — What the audit produces

A small table (can be a Notion DB if you want to track it over time; can be a markdown table in this repo for V0). Each row is a published post; columns are the signals above.

**What this tells us:**
- Which Content Types convert to replies / DMs at higher rates.
- Whether named-entity specificity correlates with engagement.
- Whether event-tethered content outperforms standalone.
- The rough rate: how many published posts → how many meaningful responses? This is the denominator we'll need later when we want to say "the pipeline produces N leads per month."

**If the sample is under 10 posts:** take what we can, but note that conclusions are thin and flag that as a "signal: we need more publishing history before this audit is conclusive." That's a fine answer — don't force a pattern.

---

## Part C — HubSpot inventory

Lighter than Notion because HubSpot holds less modeled data for our purposes, but it's where event associations live.

### C.1 — Object counts

- Total Contacts
- Total Companies
- Total Notes (these are our event-association layer per CLAUDE.md)
- Notes per contact distribution (mean, median, max)

### C.2 — Dedup and identity audit

- Contacts with no email — these are orphans from the "create without email" risk flagged in CLAUDE.md. Count them.
- Contacts where the name matches a name in another contact record but with different email / no email — candidate merges. Sample 10, eyeball, note the rate.
- Companies with no domain — similar orphan risk.

### C.3 — Event-association sampling

- Pick 5 recent events from the Notion Events DB.
- For each, search Notes with body = event name.
- Confirm the associated Contacts match the Notion Event's People relation.
- Flag mismatches.

**What this tells us:**
- How reliable the Notion ↔ HubSpot bridge is as a dedup/lookup surface.
- Whether the Notes-as-event-tracking approach is actually working at the volume we have.

---

## Part D — LinkedIn activity (Alex-side)

No scraping. Use only:
- Your own LinkedIn Activity export (Settings → Data privacy → Get a copy of your data).
- Your Creator Hub analytics (if enabled — it shows post-level performance for the last 365 days).
- Manual judgment on DMs received (which posts triggered which DMs — you'll remember).

### D.1 — Post cadence baseline

Last 90 days:
- Total posts
- Average per week
- Longest gap
- Variance week-over-week

This is your current publishing capacity baseline. If the Phase 1 plan calls for 3–4 posts/week and the current baseline is 1/week, we need to re-scope OR understand what will change.

### D.2 — Engagement baseline

- Average reactions per post
- Average comments per post
- Median values (better signal — averages get distorted by one viral post)
- % of posts with zero engagement

### D.3 — Attributable outcomes

Over the last 90 days, as best you can reconstruct:
- How many meaningful DMs (= reply from a person you wanted to talk to, not a recruiter spam)?
- How many warm intros offered?
- How many new connections from people at target companies?
- How many interviews / conversations attributable to content vs. direct application vs. referral?

This is rough. It's a sanity check on whether content is currently moving your funnel at all, not a precise metric.

---

## Part E — What to do with the inventory (output)

At the end of Parts A–D, write a single markdown file: `Signal_Pipeline/Phase_0/inventory_findings.md`. Structure:

1. **Headline numbers** — counts per DB, completeness summary, post cadence baseline.
2. **What's healthier than expected** — positive surprises.
3. **What's weaker than expected** — quality gaps, completeness holes, dedup risk.
4. **Revealed watchlist** — the top-recurring People / Companies / Topics from A.4.
5. **Engagement patterns** — what kinds of posts actually move Alex's funnel (Part B + D).
6. **Open questions surfaced** — things we didn't expect to find or can't explain.

This findings doc is the input to `01_signal_discovery_method.md` — it's literally the data we'll "let speak."

---

## Failure modes to guard against

1. **Rabbit-holing on a single interesting record.** The inventory is a scan, not an analysis. Budget per-DB: 30 minutes max. Don't fall into one Company's story.
2. **Skipping the parts we don't like.** If Part D's engagement numbers are embarrassing, capture them anyway. The whole discovery method depends on seeing the real data, not the version that makes the roadmap look vindicated.
3. **Treating absence as signal.** A topic with zero activity in 30 days might be dead OR might be between events. Don't mark a topic "stale" in Phase 0 — that's a modeling decision, not an inventory decision.
4. **Pretending we have more data than we do.** If the People DB is under 30 rows, say so and plan around it. The hygiene and modeling work can still proceed on a small corpus; it just means we'll iterate more.

---

## What comes next

Once this inventory is done, `01_signal_discovery_method.md` picks up the findings and asks the modeling question: *what of this predicts "worth writing about / worth reaching out on"?* That's where we stop counting and start modeling.

The hygiene writeup (`02_hygiene_tier_1_spec.md`) is in parallel — it takes the gaps surfaced in Part A and C and turns them into the entity identity / provenance / suppression spec we'll implement in Phase 1.
