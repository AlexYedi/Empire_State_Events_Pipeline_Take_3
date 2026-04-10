# Pipeline Operations Guide
## Version 0.1

The end-to-end workflow for turning events into research, content, projects, and
CRM records. Documents every manual step, what it triggers, ideal timing, and
where automation opportunities exist.

---

## Pipeline Overview

```
DISCOVER EVENT → REGISTER → RESEARCH → CONTENT → PROJECT IDEATION → BUILD → ATTEND → POST-EVENT
     |               |          |          |              |             |        |          |
   Manual        Manual     Skill      Skill          Skill        Manual   Manual      Skill
                                                                                      (future)
```

---

## Phase-by-Phase Operations

### Phase 0: Event Discovery & Registration

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 0.1 | **Manual** | Find event (Meetup, Luma, LinkedIn, word of mouth) | — | Ongoing |
| 0.2 | **Manual** | Register for event | Event appears on Google Calendar | ASAP — longer lead time = more ambitious projects |
| 0.3 | **Manual** | Copy calendar invite text (description, speakers, topics) | You have the raw input for research | When ready to research (see timing below) |

**Ideal timing:** Register as early as possible. Research can happen anytime after, but
earlier = more time for project ideation and building.

---

### Phase 1: Event Research

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 1.1 | **Manual** | Open Claude Code, invoke event-research skill | — | 7-14 days before event (ideal) |
| 1.2 | **Manual** | Paste calendar invite text + any context cues | Skill parses entities (event, people, companies, topics) | — |
| 1.3 | **Manual** | Review extracted entities, confirm or correct | — | ~2 min |
| 1.4 | **Auto** | Skill researches all entities (web search + Claude knowledge) | Structured brief generated across 5 topic dimensions | ~5-10 min |
| 1.5 | **Manual** | Review research brief, request changes or approve | — | ~5 min |
| 1.6 | **Auto** | Skill writes to Notion (5 databases in dependency order) | Companies → Topics → People → Event → Content Draft created | ~3 min |
| 1.7 | **Auto** | Skill writes to HubSpot (companies → contacts → notes) | CRM records created with event association | ~2 min |
| 1.8 | **Manual** | Review summary, confirm everything landed | — | ~1 min |

**Trigger:** You paste an invite and say "invoke event research skill"
**Output:** Notion has 5 database entries + HubSpot has CRM records
**Total time:** ~20-30 min (mostly research generation + your review)

---

### Phase 2: Pre-Event Content Generation

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 2.1 | **Manual** | Invoke pre-event-content skill for the event | — | After research is complete |
| 2.2 | **Auto** | Skill loads research brief + reference files (style guide, anti-patterns, outreach templates) | Context assembled | ~1 min |
| 2.3 | **Manual** | Confirm which content types to generate (weekly post, per-event post, DMs, all) | — | ~30 sec |
| 2.4 | **Auto** | Skill generates LinkedIn post (2 variants) | — | ~2 min |
| 2.5 | **Auto** | Skill generates visual content briefs (3 per post) | Prompts for Canva/Gemini/Gamma | ~1 min |
| 2.6 | **Manual** | Select post variant, provide voice/tone feedback | Captures feedback for style guide updates | ~3 min |
| 2.7 | **Auto** | Skill generates speaker/host DMs (2-3 per person per topic) | — | ~3 min |
| 2.8 | **Manual** | Select DMs to send, provide feedback on tone | Unused DM questions become prepared questions | ~5 min |
| 2.9 | **Auto** | Skill compiles prepared questions from unused DMs | — | ~1 min |
| 2.10 | **Auto** | Skill writes all content to Notion Content Drafts | Posts, DMs, questions saved with relations | ~2 min |
| 2.11 | **Manual** | Create visuals using briefs (Canva, Gemini, Gamma) | Supporting images/carousels for posts | 15-30 min |
| 2.12 | **Manual** | Post to LinkedIn, send DMs | Content goes live | Per your scheduling |

**Trigger:** You say "invoke pre-event content skill for [event name]"
**Depends on:** Phase 1 complete (research brief exists in Notion)
**Output:** LinkedIn posts, DMs, prepared questions, visual briefs in Notion
**Total time:** ~15-20 min (skill) + 15-30 min (visual creation) + posting time

---

### Phase 2b: Project Ideation

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 2b.1 | **Manual** | Invoke project-ideation skill for the event | — | After research is complete |
| 2b.2 | **Auto** | Skill checks active project gate (max 2) | Blocks if 2 active projects exist | ~30 sec |
| 2b.3 | **Auto** | Skill loads research brief + portfolio tracker + topic pages | Context assembled | ~1 min |
| 2b.4 | **Manual** | Confirm context summary, approve intersection analysis | — | ~1 min |
| 2b.5 | **Auto** | Skill maps topic pairs, scores intersection strength | Intersection analysis table | ~2 min |
| 2b.6 | **Manual** | Review intersections, approve or override topic selections | You can redirect to any topic | ~2 min |
| 2b.7 | **Auto** | Skill generates 3 proposals (2 feasible + 1 stretch) with full scoring rubric | Architecture, roadmap, scoring, conversation starters | ~5 min |
| 2b.8 | **Manual** | Review proposals, discuss, select which to save/activate/discard | — | ~10 min |
| 2b.9 | **Auto** | Skill writes selected proposals to Notion Project Ideas database | Full proposals with scores and relations | ~2 min |

**Trigger:** You say "invoke project ideation skill for [event name]"
**Depends on:** Phase 1 complete (topics populated in Notion)
**Gate:** Max 2 active projects — ship, archive, or delete one first
**Output:** Project proposals in Notion with architecture, roadmap, and scoring
**Total time:** ~20-25 min

---

### Phase 3: Project Building

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 3.1 | **Manual** | Set project status to "active" in Notion (if not already) | — | When you decide to build |
| 3.2 | **Manual** | Follow build roadmap from project proposal | Building the project | Per roadmap timeline |
| 3.3 | **Manual** | Document the build (screenshots, learnings, milestones) | Content moments for LinkedIn | During build |
| 3.4 | **Manual** | Deploy to Vercel | Live URL for demos | Before event |
| 3.5 | **Manual** | Invoke project-complete skill (future) | Portfolio tracker updated, project → shipped | When done |

**Trigger:** Your decision to start building
**Depends on:** Phase 2b complete (proposal exists)
**Timeline constraint:** Must fit within the timeline band for the event date
**Output:** Deployed project + content moments

---

### Phase 4: Event Attendance

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 4.1 | **Manual** | Review prepared questions before the event | Ready for networking | 30 min before event |
| 4.2 | **Manual** | Send selected DMs to speakers/hosts | Pre-event outreach | 1-3 days before event |
| 4.3 | **Manual** | Attend event, take notes/photos, demo project | Raw material for post-event content | During event |
| 4.4 | **Manual** | Capture key moments, quotes, insights | Documentarian angle | During event |

**Trigger:** The event happening
**Output:** Raw notes, photos, connections, project feedback

---

### Phase 5: Post-Event (Future — skill not yet built)

| Step | Type | What You Do | What Happens | Timing |
|------|------|-------------|--------------|--------|
| 5.1 | **Manual** | Upload photos/notes/audio to post-event form (future) | — | Within 24 hrs of event |
| 5.2 | **Manual** | Invoke post-event-content skill (future) | Recap post, follow-up DMs, documentarian content | Within 48 hrs |
| 5.3 | **Manual** | Post recap content to LinkedIn | — | 1-3 days after event |
| 5.4 | **Manual** | Update project with event feedback/conversations | — | Within a week |

**Trigger:** You returning from the event with raw material
**Status:** Skill not yet built (Phase 2 roadmap)

---

## Typical Week Workflow

### Sunday
- [ ] Run pre-event content skill for all events that week
- [ ] Generate "The Upcoming Week" LinkedIn post (if multiple events)
- [ ] Create visuals for weekly post
- [ ] Post "The Upcoming Week" to LinkedIn

### Monday–Thursday (per event)
- [ ] Post per-event LinkedIn post (2-3 days before event)
- [ ] Send speaker/host DMs (1-3 days before event)
- [ ] Build project if one is active for this event
- [ ] Review prepared questions day-of

### Event Day
- [ ] Review prepared questions (30 min before)
- [ ] Attend, document, network, demo project
- [ ] Capture photos/notes/key moments

### Day After Event
- [ ] Post-event content (when skill is built)
- [ ] Follow-up DMs to people you met
- [ ] Update project with event feedback

---

## Manual Steps Summary

Quick reference of everything that requires your action:

| Category | Manual Steps | Frequency |
|----------|-------------|-----------|
| **Discovery** | Find + register for events | Ongoing |
| **Research trigger** | Paste invite, invoke skill, review brief | Per event |
| **Content trigger** | Invoke skill, select variants, feedback on voice/tone | Per event |
| **Visual creation** | Use Canva/Gemini/Gamma with generated briefs | Per event |
| **Content publishing** | Post to LinkedIn, send DMs | Per event |
| **Ideation trigger** | Invoke skill, review proposals, select projects | Per event |
| **Building** | Execute roadmap, deploy, document | Per active project |
| **Attending** | Show up, network, document, demo | Per event |
| **Project management** | Set statuses (active/shipped/archived/deleted) | As needed |
| **Style evolution** | Invoke update-voice-and-style or update-anti-patterns when you notice issues | As needed |

---

## Automation Opportunities (Future Phases)

Areas where manual steps could be reduced or eliminated:

| Current Manual Step | Automation Target | Phase | Complexity |
|--------------------|--------------------|-------|------------|
| Copy/paste calendar invite | Google Calendar → auto-detect new events | Phase 3 | Medium |
| Invoke research skill | Auto-trigger on new calendar event | Phase 3 | Medium |
| Review research brief | Move review to after-generation (parallel agents) | Phase 4 | High |
| Create visuals from briefs | Direct Canva/Gemini API integration | Phase 3+ | Medium |
| Post to LinkedIn | Scheduling + auto-publish via API | Phase 3+ | Medium |
| Send DMs | LinkedIn API (limited, may need manual) | Phase 3+ | High (API limits) |
| Invoke content skill | Auto-chain after research completes | Phase 3 | Low |
| Invoke ideation skill | Auto-chain after research completes | Phase 3 | Low |
| Upload post-event materials | Vercel form → Notion | Phase 3 | Low (form exists) |
| Project status management | Notion automation rules | Phase 3 | Low |

**Priority for automation:** Skill chaining (research → content → ideation auto-flow)
is the highest-value, lowest-complexity automation. Event intake from Google Calendar
is the second priority.

---

## Skill Invocation Quick Reference

| Skill | Command | Prerequisites |
|-------|---------|---------------|
| Event Research | "invoke event research skill" + paste invite | Calendar invite text |
| Pre-Event Content | "invoke pre-event content skill for [event]" | Research brief in Notion |
| Project Ideation | "invoke project ideation skill for [event]" | Research brief in Notion, < 2 active projects |
| Update Voice & Style | "invoke update voice and style" + feedback | Observed content issues |
| Update Anti-Patterns | "invoke update anti-patterns" + items | Observed pattern issues |
| Post-Event Content | *Not yet built* | Event attended, raw materials |
| Project Complete | *Not yet built* | Project shipped |
