# event-research.md — Entity Recurrence Protocol diff

**Date:** 2026-04-20
**Source file:** `.claude/skills/event-research.md` (434 lines, current)
**Target file:** `skill-updates/event-research.md` (updated, this folder)

## Why this change

When Microsoft shows up at the Brooklyn AI event in February and then at an FDE event in April,
the current skill has no meaningful dedup. Step 4a reads: *"If duplicates found, ask Alex:
'Found existing record for [X]. Update it or create new?'"* That's a coin flip, not a protocol.

The updated skill formalizes a differentiated-threshold triage and explicit write semantics
per entity type, so recurring companies/people/topics don't blow up properties, lose history,
or duplicate records. Research scope and write behavior are both set by the triage — not by
a uniform "always research, always create" default.

## Summary of changes

| # | Change | Section(s) | Lines added | Risk |
|---|--------|------------|-------------|------|
| 1 | Insert **Step 1.5: Dedup + Freshness Triage** (canonicalize, search, classify, present) | after Step 1 | ~90 | Low — new step, no existing behavior overwritten |
| 2 | Rewrite **Step 2 intro** to route by triage path (NEW/REFRESH/SKIP/APPEND-ONLY) | Step 2 intro | ~14 | Low — scope-narrowing, not scope-changing |
| 3 | Replace **Step 4a** (thin dedup prompt) with **Step 4a: Apply Triage Actions** gate | Step 4a | ~15 | Low — replaces a weaker check with a stronger one |
| 4 | Add explicit **Create / Refresh / Skip** paths to Companies (4b), Topics (4c), People (4d), with entity-specific merge rules | 4b, 4c, 4d | ~100 | Medium — introduces append/merge logic; needs real-event validation |
| 5 | Add **Step 5.0 HubSpot recurrence check** + explicit Create / Refresh paths in 5a (Companies) and 5b (Contacts) | 5.0, 5a, 5b | ~50 | Medium — mirrors Notion triage at CRM layer |
| 6 | Update **Step 4g / Step 6** summaries to report `[X created, Y refreshed, Z skipped]` per entity | 4g, 6 | ~12 | Low — reporting only |
| 7 | Add **triage-missing** case to Error Handling | Error Handling | ~3 | Low — additive |

---

## Change 1: Insert Step 1.5 (Dedup + Freshness Triage)

### Location
After Step 1 confirmation ("Wait for Alex's confirmation before proceeding to Step 1.5"),
before Step 2.

### Before
```
Wait for Alex's confirmation before proceeding to Step 2.

---

## Step 2: Research
```

### After
```
Wait for Alex's confirmation before proceeding to Step 1.5.

---

## Step 1.5: Dedup + Freshness Triage

[~90 lines covering:]
- 1.5a Canonicalize names (Company legal suffix strip; Person LinkedIn > Email > Name+Company;
  Topic alias table)
- 1.5b Search Notion (table of database IDs + search fields)
- 1.5c Classify per thresholds:
    Company: ≤14d SKIP / 15–60d REFRESH light / >60d REFRESH full
    Person:  ≤30d SKIP / 31–90d REFRESH light / >90d REFRESH full
    Topic:   ≤45d APPEND-ONLY / 46–120d REFRESH selective / >120d REFRESH full
- 1.5d Present triage plan to Alex, accept overrides

---

## Step 2: Research

Research each entity using the triage from Step 1.5...
```

### Rationale
Differentiated thresholds reflect entity dynamics:
- **Companies move fast** (funding, product launches) — 14-day stale threshold is tight
- **People move slower** (job changes are 12–24 month events, public POV shifts quarterly) — 30-day stale is right
- **Topics shift fastest in current events but the core framing is durable** — append Current Events aggressively, merge the rest selectively

---

## Change 2: Modify Step 2 intro

### Location
Step 2 opening paragraph.

### Before
```
## Step 2: Research

Research each entity type using the sources below. Work through each section and compile
results before presenting. Use web search aggressively — current information is the value.
```

### After
```
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
```

### Rationale
Without this, Step 2 would default to full research for every entity, wasting time and
inventing deltas where none exist. The triage routing keeps research proportional to
what's actually likely to have changed.

---

## Change 3: Replace Step 4a (dedup prompt → triage gate)

### Location
Step 4a, first subsection of Step 4.

### Before
```
### 4a: Dedup Check (ALWAYS DO THIS FIRST)

Before creating any records, search each relevant Notion database for existing entries:
- Search Companies database for each company name
- Search People database for each person name
- Search Topics database for each topic name
- Search Events database for the event name

Use `notion-search` with the data_source_url parameter to search within specific databases.

If duplicates found, ask Alex: "Found existing record for [X]. Update it or create new?"
```

### After
```
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
```

### Rationale
The old 4a was doing dedup search too late — after Alex had already approved the brief.
That meant any duplicates surfaced at the last possible moment, mid-write. Moving dedup
into 1.5 surfaces it before research, so triage informs research scope. Step 4a becomes
a gate that enforces the plan.

---

## Change 4: Add Create / Refresh / Skip paths to 4b, 4c, 4d

### 4b (Companies)

#### Added: Refresh path
```
#### Refresh path (REFRESH light | full)

Do NOT overwrite the company page blindly. Steps:

1. **Audit trail** — before any property write, append a dated block to the Event page
   body (created in 4e) capturing the prior Company.Recent Developments text:
   ```
   ### Prior [Company] snapshot (as of [prior Last Researched date])
   [prior Recent Developments text]
   ```
   This preserves history without bloating the Company record.

2. **Update in place** — on the existing company page:
   - Overwrite: Recent Developments, Funding Stage (if changed), Recent Funding ($)
     (if changed), Last Researched (today).
   - Merge: Industry / Space multi-select — union, don't drop.
   - Leave alone: Company Name, Description (unless empty), Website (unless empty or M&A).

3. **Page body** — append `## Refresh [YYYY-MM-DD] — [Event Name] context` section.
```

#### Added: Skip path
```
#### Skip path (SKIP)

No write. The Event's Companies relation in 4e picks up this company via its existing URL.
```

### 4c (Topics) — Most complex merge rules

#### Modified: Create path
Changed `Current Events` to use the dated block format from day 1, so the refresh path
can append consistently:
```
Before: "Current Events": "[dominant stories, trending developments]"
After:  "Current Events": "## [Event Name] — [YYYY-MM-DD]\n[new research]"
```

#### Added: Refresh path with per-property merge rules
- **Current Events**: prepend new dated block, rolling cap of 6 blocks, soft char budget ~1500
- **Opportunities / Challenges / Use Cases**: merge with dedup on first 40 chars lowercase;
  never drop existing bullets
- **Top Questions**: append, cap at ~10, drop oldest first

#### Added: Append-current-events-only path
Touches only Current Events + Last Updated. Everything else left alone.

### 4d (People)

#### Added: Refresh path with selective overwrite rules
- Overwrite: Current Title, Known POV / Bio, Last Researched
- Merge union: Role Context multi-select
- Fill-if-empty only: Email, LinkedIn URL (never overwrite non-empty)
- Company relation: add new company URL if person switched; keep prior company too
- Notes: append dated section (don't overwrite)

#### Added: Skip path

### Rationale
The three entity types have meaningfully different merge dynamics, so a single generic
"refresh" rule would either under-preserve (Topics would lose accumulated context) or
over-preserve (Companies would stop reflecting current reality). The per-entity rules are
tuned for each.

Specifically, the Company audit-trail pattern (prior snapshot written to Event page body
before overwrite) solves the "what did Microsoft look like 2 months ago" question without
cluttering the Company record itself. Event pages become the time-series archive.

---

## Change 5: HubSpot recurrence (Step 5.0, 5a refresh, 5b refresh)

### Added: 5.0 HubSpot recurrence check

```
### 5.0: HubSpot recurrence check (run before any create)

Mirror the Notion triage logic at the CRM layer.

Companies — search by domain first, fall back to exact name.
Contacts — search by email first, fall back to firstname+lastname+company.
Notes — always create a new Note per event (no dedup, intentional).
```

### Added: 5a refresh path
- Update `description` only if empty or clearly stale
- Never touch `name` or `domain` (HubSpot dedup fragility)
- Never set `industry` (per CLAUDE.md)

### Added: 5b refresh path
- Update `jobtitle` only if materially changed
- Update `company` only if person switched (update association too)
- Never touch `email`, `phone`, `firstname`, `lastname`
- Backfill company association if missing

### Rationale
HubSpot has dedup on email by default, but that alone doesn't protect against email-less
contacts (common from event rosters). The 5.0 check mirrors Notion triage — once the work
is done once at the Notion layer, it's cheap to apply the same logic at the CRM layer.

The "never touch identifiers on existing contacts" rule prevents CRM data rot. The most
common way CRMs degrade is well-intentioned updates overwriting verified fields with
lower-quality inputs.

---

## Change 6: Summary reporting (Steps 4g, 6)

### Before (Step 6 Notion section)
```
- Companies: [count] ([names])
- People: [count] ([names])
- Topics: [count] ([names])
```

### After
```
- Companies: [X created, Y refreshed, Z skipped] ([names])
- People: [X created, Y refreshed, Z skipped] ([names])
- Topics: [X created, Y refreshed, Z append-only] ([names])
```

Same pattern applied to Step 4g confirmation block.

### Rationale
Alex needs to see triage outcomes to spot-check the protocol is firing correctly. A blanket
"5 companies" obscures whether anything actually got refreshed vs. skipped.

---

## Change 7: Error Handling addition

### Added
```
- **Step 1.5 triage missing:** If Step 4 is reached without a triage plan from 1.5, stop.
  Do not fall back to create-always. Re-run 1.5.
```

### Rationale
Defense in depth. If 1.5 is accidentally skipped (model drift, conversation branching),
the worst outcome is silent duplication. This error case forces it back on track.

---

## Self-review

Reading the full updated file end-to-end, here's what I noticed and how it resolves:

### ✅ Works as designed
- **Triage happens once, consumed twice.** Step 1.5 produces a plan; Step 2 uses it to scope
  research, Step 4 uses it to route writes. Single source of truth.
- **Dedup search cost is paid once.** Old skill had 4a searching Notion mid-write; now 1.5
  searches upfront, and 4a is a pure gate.
- **Skip path still links the Event.** The critical relationship — "this company came up at
  this event" — is preserved via Event.Companies relation even when the Company itself is skipped.
- **Topic Current Events format is consistent from create to refresh.** Create path uses
  the `## [Event] — [Date]` block format, so refresh can always append.

### ⚠️ Watch items (not blockers, but worth flagging)

1. **Merge logic for Topic Opportunities/Challenges/Use Cases is fuzzy-match-on-40-chars.**
   That will work for most cases but may fail on e.g. two bullets that start with the same
   40 chars and diverge after. Alternative: embedding similarity, but that's overkill for V1.
   Accept the fuzziness; Alex can prune manually if it gets ugly.

2. **Rolling cap of 6 Current Events blocks.** For a hot topic (agentic systems) that Alex
   attends events on weekly, blocks will rotate out in 6 weeks. That's probably fine — older
   context lives on the Event pages. But if Alex wants longer memory, the cap should bump to 8–10.
   Flagging as a tuning knob.

3. **The Company audit-trail write order has a subtle dependency.** The refresh path says
   "append prior snapshot to Event page body (created in 4e)," but 4b runs before 4e. The
   fix is to stage the audit-trail text during 4b and append it to the Event body during 4e.
   The updated 4e says "PLUS any 'Prior [Company] snapshot' audit-trail blocks from 4b refresh
   paths" — that phrasing covers it, but the executing model needs to keep the snapshots
   staged between 4b and 4e. Worth calling out in a real dry-run.

4. **Person.Company relation on job change.** The rule says "add new company URL, keep prior."
   That produces a person with 2+ company relations, which is correct for career history
   but may confuse the Content Drafts generation (which company should outreach reference?).
   Probably fine — Content Drafts skill can use the most recently-added company. Flagging
   as a Phase 2 consideration.

5. **No test for the threshold boundaries.** What happens at exactly 14 days? The table says
   `≤14 days → SKIP` and `15–60 days → REFRESH (light)`. Clean boundary. But at exactly
   60 days: `15–60 days → REFRESH (light)` inclusive of 60, and `>60 days → REFRESH (full)`.
   Clean. Boundaries match. ✓

### ✅ Design principles held

- **No breaking changes to the write schema.** Notion property shapes are unchanged; what
  changes is when/whether we write them.
- **No new gotchas introduced.** The Notion create-pages gotchas block in 4b is preserved
  verbatim.
- **Human-in-the-loop preserved.** Triage plan in 1.5d requires Alex's approval before Step 2
  spins up. Brief review in Step 3 unchanged.
- **CLAUDE.md rules respected.** Never set industry in HubSpot, use Recent Funding ($) number
  field, funding stages match the published option set, etc.

### Net risk assessment

**Medium — appropriate for a V1 of entity recurrence.** The logic is testable (run the same
event through twice, should see SKIP on second run for all entities). The failure mode is
graceful (if triage is missing, error; if merge fails, write falls through to overwrite with
the existing gotcha protections). Validation path: next time Microsoft appears at an event,
we'll see the full flow end-to-end.

### What's NOT in this update (deferred)

- Apollo integration — still separate per CLAUDE.md
- Conflict resolution when Alex has hand-edited a field (e.g., he rewrote Microsoft's Description
  and then the refresh tries to append). Current rule: `Description` is leave-alone on refresh
  unless empty, so hand-edits are safe. But Opportunities/Challenges/Use Cases do merge,
  which could collide with hand-edits. Accept for V1; flag if it causes pain.
- Historical backfill — this protocol only applies to NEW events going forward. Existing
  Notion records (the 14 from the FDE event) are unaffected.

---

## How to apply

The `.claude/skills/` path is protected in this Cowork session, so I couldn't edit the file
in place. The updated skill file is at:

- `skill-updates/event-research.md` — full updated skill, drop-in replacement
- `skill-updates/event-research-diff-2026-04-20.md` — this document

To ship:
```
cp skill-updates/event-research.md .claude/skills/event-research.md
```

Then test on the next real event. The first recurring company (Microsoft, if/when it
surfaces again) is the real validation.
