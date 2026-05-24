---
name: writing-prds
description: Help users write effective PRDs. Use when someone is documenting product requirements, preparing specs for engineering, writing feature briefs, or defining what to build for their team.
---

# Writing PRDs

Help the user write effective product requirements documents using frameworks and insights from 11 product leaders.

## How to Help

When the user asks for help with PRDs:

1. **Start with the why** - Ask about the problem being solved and why it matters now, before features
2. **Define success upfront** - Help them articulate how they'll know the feature succeeded
3. **Choose the right format** - Discuss whether they need a traditional doc, a prototype, or executable evals
4. **Keep it actionable** - Ensure the document leads to clear team action, not just documentation

## Core Principles

### Lead with problem and context
Maggie Crowley: "The most important section is the first part - what is the background and context? What is the problem, why does it matter, and why does it matter now?" Center the team on the 'why' and the urgency before discussing solutions.

### The PR/FAQ forces clarity
Bill Carr: "Whenever we're devising a new product, we start by writing a press release describing it in a way that speaks to the customer. The idea better jump off the page." Use the PR to describe customer, problem, and solution in factual, data-rich language.

### Demos before memos in AI age
Aparna Chennapragada: "If you're not prototyping and building to see what you want to build, you're doing it wrong. Prompt sets are the new PRDs." For AI features, include functional prototypes and prompt sets as core requirements.

### Evals as living PRDs
Hamel Husain & Shreya Shankar: "This is the purest sense of what a product requirements document should be - this eval judge that's telling you exactly what it should be, and it's automatic and running constantly." Translate product requirements into executable evaluations for AI products.

### Keep it lightweight for action
Eric Simons: "We tend to keep them pretty light. I like to have the minimal amount of context that ensures everyone's on the same page and that key outcomes will be present when we get there." Focus on key outcomes rather than exhaustive details that developers ignore.

### PRDs demonstrate craft
Vikrama Dhiman: "Is your PRD quality good enough? Are you writing drafts that go to care teams, marketing teams? You must have impact through the artifacts you work on." High-quality PRDs demonstrate professional craft and create clarity at scale.

### AI can scaffold the basics
Claire Vo: "I had used ChatGPT to come up with a very serviceable PRD spec for this very technical product." Use AI to scaffold basics like user stories and out-of-scope items, then focus on high-level strategy and narrative.

### Live PRDs reduce ambiguity
Guillermo Rauch: "The product management team is now actually building the product. We've specced out in v0, think of it as a live PRD. The amount of detail - we're all saying 'just ship it.'" Interactive, animated prototypes reduce ambiguity and speed up approval.

### Include the 'Why Now'
Justify the timing of this investment against other opportunities. If you can't explain why this matters now versus later, the priority is questionable.

## Questions to Help Users

- "What problem is this solving, and why does it matter now?"
- "How will you know if this feature was successful - what metric moves?"
- "Who is the customer, and what does their life look like after this ships?"
- "What is explicitly out of scope to prevent scope creep?"
- "Could you build a quick prototype instead of writing more documentation?"
- "What are the key decisions that still need to be made?"

## Output Handling — auto-persist via ChatPRD MCP (added 2026-05-24)

Per CLAUDE.md MCP automation rule #1, when this skill produces an actual PRD
(not just guidance or questions), auto-persist the document via
`mcp__claude_ai_ChatPRD__create_document`. ChatPRD is the system of record for
PRDs; the conversation output is the draft moment.

**When to fire the MCP call:**

Run this when the skill output is a complete PRD draft — i.e., it includes
problem statement + user/customer + success metric + scope (in/out) + the
"why now." Skip the auto-write for:

- Partial drafts (one or two sections being workshopped) — Alex iterates in
  conversation first, then signals "draft is done"
- Pure guidance requests ("how should I structure the success metric for X?")
  — no PRD artifact exists yet
- Critique sessions ("review this existing PRD") — the source PRD is already
  somewhere Alex tracks it

**MCP call shape:**

```
mcp__claude_ai_ChatPRD__create_document({
  title: "<derived from problem statement — 8 words max>",
  contentMarkdown: "<full PRD draft in markdown>",
  summary: "<one-sentence what + why-now>",
  projectId: "<if Alex specifies a project context>"
})
```

Before firing, call `mcp__claude_ai_ChatPRD__list_projects` if Alex referenced a
project by name — match by fuzzy title and pass the projectId so the PRD lands
in the right project rather than as an orphan document.

**Surface the URL after the write.** The user gets a link to the persisted PRD
in ChatPRD where they can share, comment, and iterate. The conversation
output remains the draft moment; ChatPRD is durable storage.

**Failure modes:**

- ChatPRD MCP returns auth error → tell Alex to reconnect via `/mcp`. Do NOT
  silently fall back to "Alex copies the PRD manually."
- Title collision (a doc with the same title already exists) → use
  `mcp__claude_ai_ChatPRD__search_documents` to find the existing doc and
  ask Alex whether to update via `update_document` or create as new with a
  date suffix.

## Common Mistakes to Flag

- **Starting with the solution** - The document should lead with the problem and context
- **No success criteria** - Every PRD needs a clear definition of how you'll measure success
- **Exhaustive detail** - Lightweight PRDs focused on outcomes are more likely to be read and used
- **Static when prototypes work better** - For AI and UI work, live prototypes communicate more than prose
- **Missing the 'Why Now'** - Without urgency justification, priorities will be questioned

## Deep Dive

For all 14 insights from 11 guests, see `references/guest-insights.md`

## Related Skills

- Conducting User Interviews
- Writing North Star Metrics
- Prioritizing Roadmap
- Shipping Products
