---
name: pre-event-content
description: Generate pre-event content for NYC AI/tech events from completed research briefs. Produces LinkedIn posts (personal and "The Upcoming Week" roundup), speaker/host DMs with personalization, and prepared questions. Writes to Notion Content Drafts database. Use when Alex says "draft pre-event content for [event]", "write the LinkedIn post for [event]", "DMs for [speaker/host]", "Sunday roundup post", or anything similar. Requires a completed research brief in Notion.
---

# Skill: Pre-Event Content Generation

Generate pre-event content for NYC AI/tech events based on completed research briefs.
Produces LinkedIn posts, speaker/host DMs, and prepared questions. Writes to Notion
Content Drafts database.

**Prerequisites:** The event must have a completed research brief in Notion (generated
by the event-research skill). The skill reads from the brief — it does not do its own research.

**Reference files (read before generating any content):**
- `.claude/references/content-style-guide.md` — voice, tone, post architecture, audience, formatting
- `.claude/references/content-anti-patterns.md` — words, phrases, and patterns to avoid
- `.claude/references/outreach-templates.md` — DM structural patterns and personalization rubric

---

## Input

Alex provides one of:
- An event name (skill fetches the research brief from Notion)
- A pasted research brief (if generating outside the Notion workflow)
- A list of events for The Upcoming Week post

---

## Step 1: Load Context

1. Read all three reference files listed above
2. Fetch the research brief from Notion (search Content Drafts for the event name, Content Type = research_brief)
3. Extract from the brief:
   - Event name, date, location (virtual vs. in-person)
   - Topics with Current Events, Opportunities, Challenges, Use Cases, Top Questions
   - People with roles, POVs, connection angles
   - Companies with recent developments
   - Documentarian angle
4. Confirm with Alex what content types to generate for this event:
   - The Upcoming Week post (only if multiple events queued for the week)
   - Pre-Event LinkedIn post
   - Speaker/Host DMs
   - All of the above

---

## Step 2: Generate The Upcoming Week Post (if requested)

**When:** Sunday post covering all events for the coming week.
**Input:** Multiple event research briefs (one per event that week).
**Length:** Long-form.

### Structure

```
HOOK — Set the frame for the week. What's the through-line across the events?
       A trend, a tension, a question the week's events collectively address.

FOR EACH EVENT:
  - Event name + date + format (in-person / virtual)
  - 2-3 sentence synopsis: Why this event is relevant and consequential RIGHT NOW.
    Draw from one of these angles (pick the strongest for each event):
    * Trendiness — what's dominating the conversation in this space
    * Recent technological development — product launch, framework release, breakthrough
    * Product/industry segment shift — competitive dynamics, market moves
    * Macro/geopolitical impact — regulation, trade, investment patterns
    * Timeless criticality — if none of the above apply, why this topic is foundational
  - 1-2 sources/citations for the research behind the synopsis (so Alex can share deeper links)

EVENTS PENDING (if any):
  - Brief mention of events Alex has applied to / hoping to attend
  - Same synopsis treatment but lighter touch

CTA:
  "If you can't make it or aren't in the NYC area but have a question you wish you could
  ask — connect, message me and I'll ask it. If you're going, happy to connect before,
  don't hesitate to say and I'll see you there."
```

**Generate 2 variants** with different hooks/framing angles. Present as inline options.

### Quality Checks
- At least 2, no more than 3 data points per event synopsis
- Each synopsis passes the "So What?" test
- 2-5 relevant hashtags at the end
- Emoji used sparingly as structural markers

---

## Step 3: Generate Pre-Event LinkedIn Post

**When:** Per-event post, typically a few days before the event.
**Length:** Mid-form (8-15 lines).

### Structure

Follow the Hook-Context-Insight-CTA architecture from the style guide:

```
HOOK — First 1-2 lines. A surprising stat, a specific detail from the research,
       or a framing that makes someone stop. NOT "I'm excited to attend..."

CONTEXT — Why this event/topic matters right now. Connect to a broader trend or
          recent development from the research brief. This is where 2-3 data points land.

INSIGHT — The ONE thing. One deeply considered observation or one genuinely novel
          question about the topic. The thing that would make an expert pause.
          This is the entire value of the post.

CTA — "If you're deep into [topic], what are you most looking forward to learning
      or hearing about?"
```

**Generate 2 variants** with different hooks/insight angles. Present as inline options.

### Quality Checks
- Exactly 2-3 data points from the research brief, with sources available if Alex wants to reference
- One clear insight or question that passes the expert-pause test
- No words/patterns from the anti-patterns file
- 2-5 relevant hashtags
- Emoji sparingly
- Documentarian framing: specific detail (reporter), synthesis (student), interpretation (analyst) — hit at least one

---

## Step 3b: Generate Visual Content Briefs

For each LinkedIn post (Upcoming Week and/or Pre-Event), generate visual content briefs
Alex uses to create supporting visuals in Canva, Gamma, or Gemini (Imagen 3).

**Read the Visual Content section of `content-style-guide.md` before generating briefs.**
It contains the full specs for format, sizing, 2-second thumb test, color strategy,
accessibility, and format-by-content-type. Those specs are non-negotiable quality gates
embedded in each brief below.

### Step 3b.1: Pick the Format

Before writing briefs, consult the **Format Selection by Content Type** table in the
style guide. Match the strongest angle of the post to a format:

- One killer stat → single 4:5 image (Visual 1 path)
- Process / framework / multi-step → carousel (upgrade Visual 2 to carousel)
- Hot take / contrarian insight → bold typography card (Visual 3 may lead)
- Weekly preview post covering multiple events → carousel with 1 slide per event
- Comparison → single image with split layout
- Conceptual / abstract → AI-generated custom image via Gemini (Visual 3 path)

If the format deviates from the default single 4:5 image, flag it in the brief header.

### Step 3b.2: Universal Brief Requirements

**Output: 3 visual briefs per post.** Every brief MUST include:

- **Dimensions** — default 1080x1350 (4:5). Export at 2x (create at 2160x2700).
- **Headline** — max 8 words, 48px min at 1080px wide. Caps font at ~4.5% of image width.
- **Palette** — dark background + white text + ONE accent color. Pick accent by topic:
  tech/AI → blue, data/infra → green, business/GTM → amber, contrarian → red.
- **Alt text** — describes what the visual *shows*, not how it *looks*. One sentence.
- **Thumb test pass** — can a scrolling phone user get the point in 2 seconds? If not, revise.

### Visual 1: Directly Supportive (Data/Stat Visual)

A clean, designed visual that reinforces the post's key data point(s).

```
Tool: Canva (default) or Gemini (if custom style needed)
Format: Single image, 1080x1350 (4:5 portrait)
  — Upgrade to carousel if >1 stat warrants its own frame

What to visualize: [the specific stat or comparison from the post]

Hero treatment: [the number or % at 72px bold — e.g., "23% improvement"]
Supporting headline: [max 8 words — e.g., "Enterprise AI ROI, Q1 2026"]
Context line (smaller, below): [one-line explanation of what the number means]

Style principles (from style guide):
- Extract the insight, don't recreate the chart
- No gridlines, no 3D, no legends requiring cross-reference
- One accent color for the data you want seen; gray for everything else
- Source attribution: small text, bottom corner — "Source: [name], 2026"

Palette: dark bg + white text + [accent by topic]
Alt text: "[one-sentence description of the stat and what it represents]"

Thumb test: Is the hero number readable at 375px wide (iPhone SE viewport)?
  If not, shrink the headline until the number dominates.
```

### Visual 2: Directly Supportive (Conceptual/Framework Visual)

A visual that explains or maps the concept the post is about. If the concept has
>3 steps or phases, upgrade to a carousel.

```
Tool: Canva (single image) OR Gamma (carousel, 5-8 slides)
Format: Single 1080x1350 image OR carousel (PDF, 5-8 slides, all 4:5 consistent)

For SINGLE image:
  Structure: [3-column comparison / flow diagram / before-after / matrix]
  Headline: [max 8 words]
  Body: labels and flow tell the story without the caption

For CAROUSEL (if upgraded):
  Slide 1 (Hook): Bold headline + visual hook — treat as thumbnail / book cover
  Slides 2-N (Content): One idea per slide, consistent layout, progressive narrative
  Final slide (CTA): "Follow for more" or a specific comment-driving question
  Page numbers: small, bottom corner — signals more-to-swipe
  Sweet spot: 5-8 slides total. Under 5 feels thin; over 10 loses people.

What to visualize: [the framework, process, comparison, or concept]
Style: Clean, diagrammatic. Explains without the caption.
Palette: dark bg + white text + [accent by topic]
Alt text: "[one-sentence description of the framework or process shown]"

Thumb test: Can the concept be grasped on slide 1 (or the single image) in 2 seconds?
```

### Visual 3: Wild Card 🌶️

Professional but spicier. Different aesthetic, unexpected format, provocative edge.
Appropriate — still the documentarian voice — just with an angle.

```
Tool: Gemini (Imagen 3) for custom AI-generated, OR Canva for bold editorial
Format: 1080x1350 (4:5) single image, OR bold typography card for a hot take

Concept: [the provocative or unexpected angle of the post's insight]

IF using Gemini / Imagen 3, write the prompt ARCHITECTURALLY (not aspirationally):
- Composition: "centered, symmetrical, negative space on [left/right/top] for text overlay"
- Style: SPECIFIC — "flat vector illustration" / "editorial magazine photography" /
  "technical diagram style" / "minimalist line art" — NEVER "professional looking"
- Mood: "authoritative and clean" / "bold and provocative" / "minimal and sophisticated"
- Negatives: "no text, no watermarks, no people, no generic tech imagery, no stock photo energy"
- Iterate 3 rounds: prompt → evaluate → refine prompt → evaluate → final. First output is a draft.

IF using bold typography card (for hot takes):
  One sentence. Big font (72px+). Dark bg. White text. One accent color max.
  The text IS the visual.

Headline (if any): [max 8 words, 48px min]
Palette: [may break the per-topic accent to create edge — if so, justify why]
Alt text: "[one-sentence description — especially important for AI-generated imagery]"

Thumb test: Does it stop the scroll? If someone scrolls past without pausing, it's not wild enough.
Why this is the wild card: [what makes it different from Visuals 1-2]
```

**Important:** These are briefs/prompts for Alex to bring into the tools directly.
Do NOT generate images via MCP. Alex is building intuition with these tools and needs
hands-on time with prompting and iteration.

---

## Step 4: Generate Speaker & Host DMs

**For each person** identified in the research brief (speakers, hosts, organizers):

Generate **2-3 DMs per person per topic** they're associated with. Each DM should:

1. Follow one of the structural patterns from `outreach-templates.md`
2. Meet **Level 3 personalization** (connect their specific work to a specific research insight)
3. Be **4-6 sentences**
4. Always reference the specific event topic or their specific talk topic
5. Include **1 question** good enough to use as a prepared question at the event

### DM Angle Differentiation

When generating 2-3 DMs for the same person, vary the angle:
- **DM 1:** Focus on their talk's core thesis — engage with their argument
- **DM 2:** Focus on a tangent or implication of their work — go somewhere adjacent
- **DM 3 (if applicable):** Focus on the intersection of their company/role and the topic — commercial angle

### Presentation Format

Present DMs grouped by person:

```
### [Person Name] — [Role] at [Company]
Talk/Topic: [their specific talk or the event topic]

**DM Option A** (angle: [thesis engagement])
> [full DM text]

**DM Option B** (angle: [adjacent implication])
> [full DM text]

**DM Option C** (angle: [company/role intersection])
> [full DM text]

Alex selects the strongest for outreach. Unused questions feed Step 5.
```

### Quality Checks
- Each DM passes Level 3 personalization (not Level 1 or 2)
- No DM could be sent to a different person by swapping the name
- No anti-pattern phrases ("love your work", "pick your brain", etc.)
- Light close, no hard ask
- 4-6 sentences, no walls of text

---

## Step 5: Compile Prepared Questions

After Alex selects which DMs to send (Step 4), the remaining DM questions become
the **Prepared Questions** list for the event.

Format:

```
## Prepared Questions: [Event Name]

### For [Person Name] — [Talk Topic]
1. [Question from unused DM] — (angle: [description])
2. [Question from unused DM] — (angle: [description])

### For [Person Name] — [Talk Topic]
1. [Question from unused DM] — (angle: [description])
```

Include context notes: "Ask this if [X topic] comes up" or "Good follow-up if they mention [Y]"

---

## Step 6: Write to Notion

Write all approved content to the **Content Drafts** database.

**Database:** `collection://6c24c9f5-66c9-4eed-a61d-3f9b87c3f775`

### Content pages to create:

**The Upcoming Week post (if generated):**
```
"Title": "The Upcoming Week — [date range]"
"Content Type": "linkedin_post_pre"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to all events mentioned in the post]
"Topics": [relation to all topics across events]
```
Page body: the approved post variant

**Pre-Event LinkedIn post:**
```
"Title": "[Event Name] — Pre-Event Post"
"Content Type": "linkedin_post_pre"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to event page]
"People": [relation to people mentioned]
"Topics": [relation to topics covered]
```
Page body: the approved post variant

**Speaker/Host DMs (one page per person):**
```
"Title": "DM — [Person Name] re: [Event Name]"
"Content Type": "linkedin_dm_speaker" or "linkedin_dm_host"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "linkedin"
"Event": [relation to event page]
"People": [relation to person]
"Topics": [relation to relevant topics]
```
Page body: the selected DM + all alternate DMs preserved for reference

**Prepared Questions:**
```
"Title": "Prepared Questions — [Event Name]"
"Content Type": "prepared_questions"
"Event Phase": "pre_event"
"Content Status": "needs_review"
"Platform": "notion_only"
"Event": [relation to event page]
"People": [relation to all people with questions]
"Topics": [relation to relevant topics]
```
Page body: the compiled question list from Step 5

---

## Step 7: Summary

```
## Pre-Event Content Complete: [Event Name]

### Generated
- The Upcoming Week: [Yes/No] ([X] events covered)
- Pre-Event Post: [variant selected]
- Speaker/Host DMs: [count] people, [count] DMs total
- Prepared Questions: [count] questions compiled

### Written to Notion
- Content Drafts: [count] pages created
- All relations linked to Event, People, Topics

### Content Status
All drafts set to "needs_review" — Alex reviews and moves to "approved" when ready to post.
```

---

## Error Handling

- **Research brief not found:** Ask Alex to run event-research skill first or paste the brief directly.
- **No people in the brief:** Skip DM generation (Steps 4-5). Only produce posts.
- **MCP write fails:** Report exactly what failed. Offer to retry or present content in conversation for manual copy.
- **Anti-pattern detected in own output:** Flag it, explain why, and regenerate that section.
- **Personalization below Level 3:** Flag the DM as weak and explain what's missing. Offer to regenerate with more context or skip.
