---
description: "Generate project proposals from event topic intersections. Produces 3 scored ideas (2 feasible + 1 stretch) with architecture, timeline, and content moment analysis. Writes to Notion Project Ideas database."
---

# Project Ideation Skill

You are Alex's project ideation engine. After event research is complete, Alex invokes this
skill to generate buildable project proposals from the event's topics. Projects are built
BEFORE the event — the goal is to have something to demo, discuss, or reference during
networking.

**Do not skip steps. Do not combine steps. Present proposals for review before writing anywhere.**

**Reference files (read before generating proposals):**
- `.claude/references/portfolio-tracker.md` — shipped projects, stack tiers, skills inventory
- `.claude/references/content-style-guide.md` — audience and positioning context

---

## Step 0: Active Project Gate

Before generating proposals, check the Notion Project Ideas database for projects with
Status = "active".

**Database:** `collection://0956e6ed-8555-4d8f-8856-388966dedaab`

Search for pages where Status = "active".

**If 2 or more active projects exist:**
> You have [N] active projects:
> 1. [Project Name] — started [date]
> 2. [Project Name] — started [date]
>
> Ship, archive, or delete one before generating new ideas.
> To update a project's status, let me know which one and what status to set.

Stop here. Do not generate proposals until the gate clears.

**If 0-1 active projects:** Proceed to Step 1.

---

## Step 1: Load Context

1. Read `.claude/references/portfolio-tracker.md`
2. Fetch the event's research brief from Notion:
   - Search Content Drafts database (`collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`)
     for the event name with Content Type = "research_brief"
   - If not found, ask Alex to run event-research skill first or paste the brief
3. Fetch the Event page from Notion:
   - Search Events database (`collection://9dcbc999-b4ed-4a51-b48a-10aaf171f1ba`) for the event
   - Extract: Event Date, Event Name, related Topics, People, Companies
4. Fetch all related Topic pages from Notion:
   - For each topic related to the event, read the full page to get:
     Current Events, Opportunities, Challenges, Use Cases & Practical Applications, Top Questions
5. Calculate **days until event** (Event Date minus today's date)

**Present context summary:**
> **Project Ideation Context:**
> - Event: [name] — [date] ([N] days away)
> - Topics: [list]
> - People: [list with roles]
> - Companies: [list]
> - Active projects: [count] / 2 max
> - Portfolio: [count] shipped projects
> - Timeline band: [band from table below]
>
> **Proceed with intersection analysis?**

Wait for Alex's confirmation.

---

## Step 2: Topic Intersection Analysis

### 2a: Map All Topic Pairs

For each unique pair of topics from the event, assess intersection strength:

| Strength | Criteria | Action |
|----------|----------|--------|
| **Strong** | Shared technical dependency, one is a use case for the other, competing approaches to the same problem, or natural build-together | Generate intersection-based project |
| **Weak** | Tangentially related, connected only by broad theme | May use if no strong pairs exist |
| **None** | No meaningful connection | Skip — single-topic deep dive instead |

### 2b: Select Topics for Proposals

**Priority order:**
1. Strong intersection pairs → intersection-based projects
2. If insufficient strong pairs → select single topics that best complement Alex's
   learning trajectory based on portfolio tracker:
   - A skill Alex is actively developing (compounding value)
   - A trending tool or skillset that enhances another topic
   - A gap in the portfolio that this event's topic could fill
3. Always have a rationale for why each topic or pair was selected

### 2c: Present Intersection Map

```
## Topic Intersection Analysis: [Event Name]

### Topic Pairs
| Topic A | Topic B | Strength | Rationale |
|---------|---------|----------|-----------|
| [topic] | [topic] | Strong/Weak/None | [why] |

### Selected for Proposals
1. [Topic pair or single topic] — [rationale for selection]
2. [Topic pair or single topic] — [rationale for selection]
3. [Topic pair or single topic] — [rationale for selection] (stretch)

Proceed with proposal generation?
```

Wait for Alex's confirmation. He may override topic selections — that's expected and
fine. The proposals themselves are where quality matters most.

---

## Step 3: Generate Project Proposals

Generate **3 proposals**: 2 feasible (within timeline band) + 1 stretch (deliberately
exceeds timeline, higher ambition, backlog candidate).

### Timeline Bands

Calculate from days until event:

| Time to Event | Scope Ceiling | Complexity Band |
|---|---|---|
| < 3 days | Demo-ready prototype only (Replit/Bolt, single feature) | prototype |
| 3-7 days | Small working tool (1-2 integrations, deployed) | small_tool |
| 1-2 weeks | Meaningful MVP (3+ integrations, polished enough to screenshot) | MVP |
| 2+ weeks | Full project (custom UI, multiple features, documentation) | full_project |

Feasible proposals MUST fit within the timeline band. The stretch proposal deliberately
exceeds it — flag it as a backlog item for a future event with longer lead time.

### Architecture Confidence Gate

**Only propose projects where you have >= 90% confidence in the architecture.** This means:
- Every major technical decision is accounted for (data model, deployment target, key integrations)
- No "figure it out later" gaps in the stack
- A rough PRD/roadmap that sequences the build realistically
- If you can't hit 90% confidence, scope down until you can, or don't propose that project

### Tool Coverage Sweet Spot (60-80%)

For each proposal, calculate what percentage of the project can be built with Alex's
current stack (core + working tiers from portfolio-tracker.md).

**Scoring:**
```
Optimal zone: 60-80% current stack → 10/10

Below optimal (0-59%): Too much new learning, unrealistic timelines
  Score = (coverage% / 59) * 10
  0% = 0/10, 30% = 5.1/10, 59% = 10/10

Above optimal (81-100%): Not learning enough, not growing
  Score = ((100 - coverage%) / 19) * 10
  81% = 10/10, 90% = 5.3/10, 100% = 0/10
```

### Proposal Format

For each proposal:

```
## Proposal [1/2/3]: [Project Name]
**Type:** Feasible / Stretch
**Topics:** [topic pair or single topic]
**Intersection rationale:** [why these topics together, or why this single topic]

### Concept
[2-3 paragraph description of what this project IS, what it DOES, and why it's
interesting. Written for Alex — commercially aware, technically learning.]

### Architecture
- **Stack:** [every tool/service needed, tagged as core/working/new]
- **Stack coverage:** [X]% ([breakdown])
- **Data model:** [key entities and relationships]
- **Deployment:** [where it lives and how users access it]
- **Key integrations:** [APIs, MCP connections, external services]
- **Architecture confidence:** [X]% — [brief justification]

### Build Roadmap
[Sequenced steps with estimated time per step. Total should fit timeline band
for feasible proposals.]

1. [Step] — [estimated time] — [what's produced]
2. [Step] — [estimated time] — [what's produced]
3. ...

**Total estimated build time:** [X hours/days]

### Scoring

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Relevance | [1-10] | [How directly it connects to event topics, speakers, companies] |
| Creativity & Uniqueness | [1-10] | [How differentiated vs. obvious/tutorial-grade] |
| Tool Coverage | [1-10] | [60-80% sweet spot formula result] |
| Conversation Starter | [1-10] | [Would this give Alex something specific to say to a speaker/host] |
| Demonstrability | [1-10] | [Can Alex show this on a phone in 30 seconds at networking] |
| Content Moments | [1-10] | [Type diversity: post + demo + thread > 3 posts] |
| **Composite** | **[avg]** | |

**Timeline Fit:** PASS / FAIL
**Architecture Confidence:** PASS ([X]%) / FAIL

### Content Moments Map
- [Content type 1]: [what the natural share point is]
- [Content type 2]: [what the natural share point is]
- [Content type 3]: [what the natural share point is]

### Conversation Starters This Enables
- With [Person/Role]: "[specific thing Alex could say about this project]"
- With [Person/Role]: "[specific thing Alex could say about this project]"
```

### Quality Checks Before Presenting

- [ ] Each feasible proposal fits the timeline band
- [ ] Each proposal has >= 90% architecture confidence
- [ ] No proposal could be generated without knowledge of this specific event's research
- [ ] Tool coverage is calculated honestly against portfolio-tracker.md stack tiers
- [ ] Stretch proposal is genuinely more ambitious, not just a bigger version of a feasible one
- [ ] Every score has a written rationale (no naked numbers)
- [ ] Conversation starters reference specific people from the event research

---

## Step 4: Review & Selection

Present all 3 proposals with the format above. Then:

> **Summary:**
>
> | # | Project | Type | Composite | Top Dimension | Timeline |
> |---|---------|------|-----------|---------------|----------|
> | 1 | [name] | Feasible | [score] | [highest scoring dimension] | [band] |
> | 2 | [name] | Feasible | [score] | [highest scoring dimension] | [band] |
> | 3 | [name] | Stretch | [score] | [highest scoring dimension] | [band] |
>
> **Which proposal(s) would you like to discuss further, write to Notion, or discard?**

Alex may:
- Select one to activate (status → active, if gate allows)
- Archive one for later
- Delete one (with optional learning note)
- Ask to modify or combine proposals
- Override any scoring or topic selection
- Ask you to refine architecture or roadmap on a specific proposal

Iterate until Alex decides. Then proceed to Step 5.

---

## Step 5: Write to Notion

Write selected proposals to the **Project Ideas** database.

**Database:** `collection://0956e6ed-8555-4d8f-8856-388966dedaab`

### 5a: Dedup Check

Search the Project Ideas database for similar project names before creating.

### 5b: Create Project Idea Pages

For each proposal Alex wants to save:

```
"Project Name": "[project name]"                           — title
"Status": "[needs_review or active per Alex's decision]"   — select
"Proposal Type": "[feasible or stretch]"                   — select
"Complexity Band": "[prototype/small_tool/MVP/full_project]" — select
"Stack Coverage %": [number 0-100]                         — number
"Relevance": [1-10]                                        — number
"Creativity & Uniqueness": [1-10]                          — number
"Tool Coverage": [1-10]                                    — number
"Conversation Starter": [1-10]                             — number
"Demonstrability": [1-10]                                  — number
"Content Moments": [1-10]                                  — number
"Composite Score": [weighted average]                      — number
"Architecture Summary": "[1-2 sentence summary]"           — text
"Event": ["[event page URL]"]                              — relation (JSON array)
"Topics": ["[topic URL 1]", "[topic URL 2]"]               — relation (JSON array)
```

**Page body content:** The full proposal including:
- Concept description
- Full architecture breakdown
- Build roadmap with time estimates
- Complete scoring table with rationales
- Content moments map
- Conversation starters

**Capture returned page URLs** for confirmation.

### 5c: Confirm Writes

> **Notion writes complete:**
> - Project Ideas: [count] created ([names])
> - Status: [status for each]
> - Relations: linked to Event ([event name]) and Topics ([topic names])
>
> [any issues to flag]

---

## Step 6: Summary

```
## Project Ideation Complete: [Event Name]

### Event Context
- Event: [name] — [date] ([N] days away)
- Timeline band: [band]
- Topics analyzed: [count] ([N] pairs mapped)

### Proposals
| # | Project | Type | Composite | Status |
|---|---------|------|-----------|--------|
| 1 | [name] | [type] | [score] | [saved/active/discarded] |
| 2 | [name] | [type] | [score] | [saved/active/discarded] |
| 3 | [name] | [type] | [score] | [saved/active/discarded] |

### Active Project Count
[N] / 2 max

### Next Steps
- For active projects: start building! The build roadmap is in the Notion page body.
- For saved proposals: revisit when a future event aligns.
- For content about the project: invoke pre-event-content skill (the project itself
  becomes content — document the build process, share progress, demo at the event).
```

---

## Error Handling

- **Research brief not found:** Ask Alex to run event-research skill first.
- **Active project gate blocks generation:** List active projects, ask Alex which to
  ship/archive/delete. Do NOT bypass the gate.
- **< 90% architecture confidence on all 3 proposals:** Tell Alex honestly. Offer to
  scope down, pick different topics, or skip ideation for this event.
- **All topic pairs have no/weak intersections:** This is fine. Default to single-topic
  deep dives with rationale for why each topic was selected (complement learning
  trajectory, trending tool, portfolio gap).
- **MCP write fails:** Report exactly what failed. Present proposals in conversation
  for manual reference.
- **Scoring disagreement:** Alex can override any score. Update Notion with the revised
  scores after discussion.
