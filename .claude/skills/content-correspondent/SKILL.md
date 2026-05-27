---
name: content-correspondent
description: >
  Post-event content and outreach sequencing for NYC AI/tech events. Use this skill any time Alex mentions attending an event, returning from an event, or wants to follow up after one — even casually ("just got back from a founder session", "I'm at PMF x AI tonight", "need to write something about last night"). Also triggers for: drafting LinkedIn posts from event observations, classifying contacts from an event, writing follow-up DMs after meeting someone, building a content sequence from field notes, or converting Wispr/Granola notes into outreach and posts. Also use when Alex asks about post-event strategy or how to turn room conversations into content. For reviewing how posts or outreach performed after the fact, use the event-signal-tracker skill instead.
---

# Content Correspondent — Post-Event Sequencing Skill

Alex is an enterprise AI/GTM professional embedded in the NYC AI/tech scene. He operates as a **field correspondent** — not a networker, a reporter with a POV. His job after every event is to turn live room energy into two things simultaneously: durable relationships (private track) and public content that builds audience and authority (public track).

Your job is to receive raw event input — voice notes, Granola transcripts, freeform recaps, or even just "I just got back from X" — and produce the best possible outreach drafts and content. The system has two tracks that run in parallel and feed each other. A post without private activation is a broadcast. Outreach without a content asset to point to is cold. Together they compound.

**This is a human-in-the-loop workflow.** Alex will review, edit, and send everything. So lean toward producing something real and opinionated rather than safe and hedged. A draft that's 80% right and has genuine voice is more useful than a draft that's technically correct but sounds like a marketing bot. Take swings. Alex will course-correct.

---

## Input modes — two ways this skill is invoked

### Mode A — Granola-anchored (⏸ DISABLED 2026-05-27 — Granola nonoperational)

> Granola is OFF — the app is a waitlist-only placeholder on Alex's device, so there's nothing to fetch. `/post-event-content` no longer calls Granola; **do not fire the Granola API or MCP.** Until Granola ships a working app, `/post-event-content` runs on a **manual transcript upload + `transcript-conditioning`**, then hands this skill the conditioned quote bank — i.e. **Mode B is the active intake.** Re-enable this mode when Granola records for real.

When live, this mode took the Granola transcript + AI summary that `/post-event-content` fetched via API and treated it as structured input. The structured-input shape it expects is now produced by manual upload → conditioning instead.

Expected input shape:

```
Event: [Notion Event Name]
Date: [Event Date]
Notion Event URL: [...]
Granola Note URL: [...]

=== Granola AI Summary (primary input — use for angle, takeaways, thesis) ===
[summary_markdown — Granola's pre-synthesized takeaways]

=== Granola Diarized Transcript (verbatim quote source — use for speaker quotes and color) ===
Speaker 1 (microphone): [text]
Speaker 2 (speaker): [text]
...

=== Attendees (cross-reference against Notion People DB for bucket sorting) ===
[name, email] pairs

=== Notion Pre-Event Brief (if available — for documentary thesis continuity) ===
[research_brief Content Draft content]
```

**Use the summary for angle/thesis decisions.** Granola's AI synthesis has already done the heavy lifting of "what was the room about" — don't redo it. Pull the documentarian thesis from the summary, then go to the transcript for verbatim quotes that ground it.

**Use the transcript for verbatim quotes and color.** Speaker quotes in the Tier 1 comment and Tier 2 post must come from the transcript verbatim — don't paraphrase from the summary. The summary smooths the language; the transcript preserves voice.

**Cross-reference attendees against the Notion People DB.** Each attendee with a People DB match becomes a candidate for bucket sorting (A/B/C/D). Attendees without matches are surfaced for Alex to classify or skip.

**Use the pre-event brief for thesis continuity.** If Alex pre-researched the event (Workflow A), there's a `research_brief` Content Draft linked to this Event with the predicted documentary angle. Compare post-event reality to pre-event prediction — the gap is often the most interesting content beat ("I went in expecting X, the room actually argued Y").

### Mode B — Manual paste (legacy, still supported)

When Alex pastes raw material directly into the conversation (Granola export, Wispr voice notes, freeform recap, photos with captions), run the existing flow described below. Mode A is preferred because it removes the paste friction, but Mode B remains supported for ad-hoc events that weren't pre-researched or for cases where Granola wasn't recording.

**Upstream — condition first (added 2026-05-27):** if the pasted transcript has unreliable speaker labels or ASR-mangled proper nouns (the norm for in-person / phone recordings), run the `transcript-conditioning` skill FIRST — grounded in the event's roster — and consume its quote bank + glossary in place of the raw transcript. `/post-event-content` **Step 3.5** does this automatically; for an ad-hoc manual paste, invoke it yourself before drafting. Never quote a named person verbatim from an unconditioned low-quality transcript.

---

## The Two Tracks

### Private Track — Relationship Outreach

The single non-negotiable: every message must contain a specific callback to something that was actually said, built, or shared in person. Generic follow-ups ("Great to meet you!") are deleted. Specificity is respect.

The formula: **Callback → POV → Forward Motion**. Pick up a thread from the conversation and extend it — don't just recap it. Demonstrate you were fully present, add something new you've thought of since, and create a natural next step.

**The no-CTA rule for first touch on high-signal contacts**: Do not ask for a call, a meeting, or a referral in message 1. The goal of message 1 is to make them want to respond. The ask comes after they engage.

**Rough sorting logic (first touch):**

| Bucket | Who They Are | Goal | Timing |
|--------|-------------|------|--------|
| A — High Signal | Founders/operators building something relevant, exec hiring managers at target companies, investors | Relationship, collaboration, or job pipeline | Within 24h |
| B — Peer Builders | Fellow AEs/AM/CS people making the same AI+GTM transition, builders at similar stage | Mutual amplification, referral network, accountability | Within 48h |
| C — Interesting Stranger | Compelling people you had a real conversation with, no obvious immediate mutual value | Stay warm, light touch | Within 72h |
| D — Room Presence | You noticed them, they spoke, you didn't connect 1:1 | Public engagement only (comment on their content) | Same week |

**Bucket A template — Hiring Manager:**
> "[Name] — really enjoyed our conversation about [specific topic]. Your point about [specific thing] is something I've been wrestling with too — I've been approaching it by [brief relevant POV]. If you'd find it useful, happy to share what I've been seeing from [relevant angle]. Either way, glad we connected."

**Bucket A template — Founder:**
> "[Name] — the [specific product/problem] angle you described is one I keep coming back to. One thing I didn't mention on the night: [relevant observation or customer pattern you've seen]. Curious whether [specific question based on something they said]. No agenda — it's just a genuinely interesting problem."

**Bucket B template — Peer Builder:**
> "[Name] — good to connect last night. The way you're thinking about [specific thing] is solid — I've been working through a similar problem around [your angle]. I'm going to write something about [topic] this week based on the conversation — I'll tag you if it connects to what you're doing. And if you publish anything on [relevant topic], send it my way."

**Bucket C template — Interesting Stranger:**
> "Hi [name] — we crossed paths at [event] and your take on [specific thing] stuck with me. I'm in the [AI + GTM/enterprise sales] space and often write about [adjacent topic]. Would be glad to stay connected."

When input is ambiguous about who someone is, make a reasonable assumption and flag it so Alex can correct.

---

### Multi-Touch Cadence (After First Touch)

First touch gets the conversation on the board. Most replies don't come from touch 1 — they come from touch 2 or a public-track trigger. The cadence below defines what touch 2, touch 3, and the re-engagement fallback look like, plus when the CTA rule relaxes.

**Cadence by bucket:**

| Bucket | Touch 1 | Touch 2 (no reply) | Touch 3 / Fallback |
|--------|---------|--------------------|--------------------|
| A — High Signal | Callback + POV + soft forward motion. **No CTA.** Within 24h. | Day 7: "Wrote something based on the conversation — thought you might like it. [link to Tier 2 post]." The content asset is the reason to re-engage. Still no explicit ask — the asset *is* the forward motion. | Day 21: Drop private track. Do NOT send a third DM. Re-engage only via public track (comment on their next post, tag them when you write something adjacent). If they engage publicly, restart at touch 1 with a new hook. |
| B — Peer Builders | Callback + mutual amplification offer. Within 48h. | Day 10: Public track only. Tag them in a post or comment on their content. No private touch 2 unless they've already engaged. | Day 30+: If they've posted anything Alex could genuinely engage with, do that. Otherwise passive. |
| C — Interesting Stranger | Light LinkedIn connect + 1-line note. Within 72h. | No private touch 2. Public track only from here. | — |
| D — Room Presence | Comment on their post. Same week. | Continue light public track if their material earns it. | — |

**When the CTA rule relaxes (Bucket A only):**

The no-CTA rule applies to touch 1. By touch 2 (Day 7) or once they've engaged (reply, profile visit, public engagement on the post, connection acceptance with a note), the ask becomes appropriate — **but only one ask per message, not laddered**. Pick ONE:

- **Intro request** — "Would you be open to introducing me to [specific person at their network]?"
- **Call/coffee** — "Happy to hop on a call if you'd find it useful — I've been thinking about [shared topic] and your POV would sharpen mine."
- **Referral** — "If you know of any [specific role] openings where [specific fit reason], I'd appreciate the heads up."
- **Feedback** — "I'm working on [specific thing] — would value 10 min of your read on it if you have bandwidth."

Do NOT stack asks. "Would love to chat, also if you know of any roles, also would love your feedback" signals desperation and usually kills the thread.

**Re-engagement triggers (any bucket):**

A re-engagement DM is appropriate — regardless of the Day 21 drop rule — when one of these fires:

- **Their content** — they publish something Alex can genuinely add to. Use the Tier 1 comment format, not a DM. Public engagement first; DM only if their reply invites one.
- **Their news** — company funding, promotion, role change, launch. "Saw the [specific news] — [specific reaction]. [optional: 1-line forward motion]."
- **Your news** — Alex ships a project, gets a role, publishes something pattern-worthy. "Thought of our conversation at [event] — [link to the thing]. Took the [specific angle] you were pushing."

Re-engagement triggers reset the cadence clock. The goal is always to land in their feed with a reason to respond, not to chase.

---

### Public Track — Content

One event generates content at multiple levels. Default: always produce the comment draft and the short post. Everything else on request or when the material clearly earns it.

**The Content Ladder:**
```
RAW EXPERIENCE
    ↓
💬 Comment on speaker's post (same night or next morning)
    ↓
📝 LinkedIn short post — single biggest takeaway (within 24h)
    ↓
📄 LinkedIn document/carousel — pattern across 2–3 events (biweekly)
    ↓
📰 Newsletter section or long-form — the thesis that keeps showing up (monthly)
```

**The field reporter frame** is what makes the content work. Alex isn't broadcasting thought leadership from a soapbox. He's a correspondent sending dispatches from inside the NYC AI/tech scene. Write in present tense, write like someone who was actually in the room, lead with what was observed or felt before what it means. Have a take. "AI GTM is evolving" is useless. "Nobody in that room could define what 'agentic' means for a quota-carrying rep, and that gap is where deals are dying" is a conversation starter.

**On hooks**: The first line either stops the scroll or doesn't. Don't open with "I attended X last night and here's what I learned." Open with the thing that happened, the tension that emerged, the observation that stuck.

Hook examples that work:
- "The best thing I heard at last night's PMF x AI event wasn't about AI."
- "Talked to 8 founders last night. The ones building something real all said the same thing about [X]."
- "I've been to 20 of these NYC AI events. Last night was different."

**On the closing question**: End with a question that reveals something about the reader when they answer it. "What do you think?" is not a question. "Is the translation layer between infra builders and enterprise buyers a person, a process, or eventually a product?" is a question.

**Short post structure (150–300 words):**
1. **Hook** (1 sentence, stops scroll)
2. **Setup** (2–3 sentences — what was the room, who was there, what was the tension)
3. **The Take** (3–4 sentences — your actual POV, specific, with a tension or counterpoint)
4. **Invitation** (1–2 sentences — a specific, interesting question)
5. **Optional**: Tag 1–2 people from the event if earned (e.g., "as [name] said last night...")

**Tier 1 comment (same night/next morning):**
Use the "Yes, And" format — add a new dimension, counterpoint, or specific observation. Not "great event!" A comment that sounds like a person, not a marketing bot:
> "The [specific point they made] is something I've been watching play out in [your specific context]. What I'd add from the enterprise/GTM side: [your observation]. Curious whether others in the room saw [specific dynamic] the same way."

#### Audience-Specific Post Angles

The same event can generate different post angles. Pick one per event and commit. Vary across events to test which audience resonates.

| Audience | Angle | Hook Style |
|----------|-------|------------|
| Founders & Builders | "What I observed about [problem/market] from the inside" | "The founders who are actually gaining traction all share one counterintuitive habit..." |
| Execs & Hiring Managers | "What the talent and team dynamics in this scene tell you about the market" | "I've noticed the best enterprise AI hires I keep meeting are all coming from [unexpected background]..." |
| Peers (AEs, CS, AM in transition) | "What I'm learning from builders about how our jobs are changing" | "Honest admission: I came expecting to ask questions. I left feeling like the one who should be building." |
| General Tech/AI Audience | "Signal from the NYC AI scene — what's real vs. noise" | "Everyone talks about AI GTM. Last night I was in a room of 60 people actually doing it. Here's the gap." |

---

## The Closed Loop

The most powerful output is when both tracks reinforce each other:

```
Attend event
    → Write post within 24h
    → Tag 1-2 Bucket B peers
    → DM Bucket A contacts: "I wrote something based on what we discussed — curious your take"
    → Bucket A engages with post OR responds to DM
    → Their engagement surfaces you to their network
    → New people comment / connect
    → You now have warm context for outreach to those new connections
    → LOOP
```

Always produce the outreach DM and the post in the same session — the post gives the DM something to point to, and the DM activates the post.

---

## What to Produce

When Alex gives you event input, produce:

1. **Contact sort** — who goes in which bucket and why (brief, not a full table unless it's useful)
2. **Outreach drafts (touch 1)** — ready to copy-paste, one per relevant contact
3. **Tier 1 comment draft** — 2–3 sentences, additive not validating
4. **Tier 2 post draft(s) — always produce a primary AND at least one alternate ("another") version.** Post-event content is multi-version by default (150–300 words each, field-dispatch format): ship the primary post plus ≥1 alternate cut so Alex can pick or combine. The catalog of alternate version-types is provisional and grows as Alex posts and spots patterns — for now, always create at least one alternate. (Added 2026-05-27.)
   - **Pre→post bridge (primary version):** when a pre-event post exists, open the primary by bridging "what I expected" → "what actually happened." Content straying from the pre-event hypothesis is normal and expected; the bridge is what ties the pre/post pair together.
   - **Roundtable / panel format — ALWAYS one of the alternates for these events:** for **multi-speaker events where all speakers are part of ONE shared conversation** (NOT separate talks/demos), always create a version structured as the **3–5 most valuable topics, each with the named speakers' perspectives** (verbatim, attributed). Minimal editorializing — get out of the way and let the operators' perspectives carry it. Rationale (Alex): "summarization and analysis can be done by anyone; the perspectives can only be found by attending — that's the unique value to share afterward."
   - **Event-type gate:** topics×perspectives is for **shared-conversation panels / roundtables only.** For **multi-presenter events** (each speaker their own talk or demo, e.g. a demo night), do NOT use it — use per-presenter / per-demo angles (what each actually built or showed).
5. **Visual carousel brief for the Tier 2 post** — one 3-5 slide carousel
   following the canonical pattern in `../content-patterns/visual-briefs.md`.
   Read that file in full before drafting; pick the arc that matches the post's
   argument structure (single-thesis field dispatch → Arc 1; change-over-time
   observation → Arc 3; multi-perspective room dispatch → Arc 4). Append the
   brief under the post draft with a `## Visual Brief — N-slide carousel` H2.
   The carousel and the post ship together — they are one Content Draft, not
   two. Run the quality gates from `visual-briefs.md` before handing the brief
   to Alex.

6. **Auto-render the visual via Gamma MCP** (default; updated 2026-05-26) — after
   the brief is finalized AND the Content Draft is written to Notion via
   `notion-writer`, generate with `mcp__claude_ai_Gamma__generate` per
   `../content-patterns/visual-briefs.md` → `## MCP execution — Gamma (default);
   Canva (fallback only)`: `format: "social"`, `cardOptions.dimensions: "4x5"`,
   `numCards` = slide count, Stratos theme, `imageOptions.source: "noImages"`,
   stats-as-visuals in `additionalInstructions`. Surface the `gamma.app/docs/...`
   URL(s); Gamma can't be MCP-edited (Alex refines in the Gamma editor); export
   carousels as PDF. Gamma is the default — Canva is a fallback only (demoted
   2026-05-26 for garbling dense labels). The brief still ships in the Notion
   page body as the human reference.

**On request (or when Day 7 / Day 21 timing comes up in the conversation):**

5. **Touch 2 drafts** — Day 7 re-engagement DMs for Bucket A contacts who didn't reply,
   framed around the Tier 2 post as the forward motion.
6. **Re-engagement triggers** — if Alex mentions news about a specific contact (their
   funding, launch, role change), draft a re-engagement DM on the spot regardless of
   where they sit in the cadence.

If input is sparse (just an event name, no contacts or takeaways), ask three things only:
1. Who are the 1–2 most important people you met, and what did they say?
2. What was the single sharpest thing you took away from the room?
3. Was there any tension, disagreement, or surprise?

Don't ask for more. Produce from what you have.

---

## Execution Infrastructure

- **Granola** → primary source. Pulled automatically via `/post-event-content` slash command (Mode A above). Provides AI summary + diarized transcript + attendee list. Replaces manual transcript paste.
- **Wispr Flow** → optional supplement when Granola wasn't recording, or for the Uber/subway-home dictation of "things I didn't say out loud but want in the post" (interior color the room transcript can't capture)
- **Claude** → outreach and post drafts (this workflow, with Mode A or Mode B input)
- **Notion** → all drafts land in Content Drafts DB via `notion-writer` agent (status: `needs_review`)
- **n8n** → not used (event pipeline is Claude-skill-first, not middleware)
- **PostHog** → future: track which posts drive profile visits and connection requests

**The 2-hour post-event window:**
1. Classify contacts into buckets
2. Draft Bucket A and B outreach while memory is live
3. Write one rough sentence: "The one thing I'd post about tonight is ___"

**Next morning:**
1. Send queued outreach DMs (touch 1)
2. Publish Tier 1 LinkedIn post using last night's sentence as the hook seed
3. If Granola transcript is available, pull speaker quotes for color

**Day 7 (calendar reminder after event):**
1. Check reply status on Bucket A touch 1 DMs
2. Draft touch 2 re-engagement for any that didn't reply — use Tier 2 post as the forward motion
3. Scan any Bucket B/D contacts' feeds for content worth engaging (public track)

**Day 21 (calendar reminder):**
1. Drop private track on Bucket A contacts who still haven't replied
2. Move remaining engagement to public track only (their content, Alex's content tagging them)
3. Re-engagement only via trigger events (their news / Alex's news)

---

## Calibration and Performance Review

To review how posts or outreach performed — impressions, DM response rates, what's working across multiple events — use the **event-signal-tracker** skill. It handles diagnosis, pattern detection across events, and the progressive tier assessment (when to add the comment, when to add the pattern post, etc.). This skill creates; that skill reviews.
