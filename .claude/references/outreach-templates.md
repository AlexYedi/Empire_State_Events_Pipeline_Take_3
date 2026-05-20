# Outreach Templates — LinkedIn Connection Request Notes (200-char hard cap)

> These are NOT fill-in-the-blank templates. They are structural patterns for crafting
> LinkedIn connection request notes within the 200-character free-tier limit. The goal
> is acceptance of the connection request, not engagement after acceptance.
>
> **Operational reality:** LinkedIn free tier — non-1st-degree connections can only be
> reached via connection request notes (**200 char on free, 300 on Premium**). Direct
> messages to non-connections require InMail credits which are scarce and burn on
> first-touch with strangers. The connection request note IS the channel for first-touch
> outreach to speakers, hosts, and organizers Alex doesn't already know.
> Updated via the `update-voice-and-style` skill.

---

## Pattern 1: Sharp Question, Talk-Anchored

**Use when:** You have a specific claim, framing, or example from their talk abstract or session description.

```
[Lead with the question, anchored to a specific moment in their talk]
```

**Why this works:**
- No greeting wastes 8-15 chars on nothing the recipient doesn't already see (LinkedIn shows your name+headline)
- Anchoring to a specific abstract moment proves you read the material, not just the event listing
- The question is the value — let it land first

**Example structure (not a template):**
> "On [specific claim] in your [event] talk — is [tension/implication] something you've seen play out, or is the bottleneck somewhere else?" (171 chars)

---

## Pattern 2: Signal from Recent Work

**Use when:** You have a specific moment from their recent post, podcast, open-source commit, or shipped product.

```
[Reference the specific work + a sharp question that goes one layer deeper than the source did]
```

**Why this works:**
- Shows you tracked their recent output, not just their bio
- "Goes one layer deeper" signals you'd be worth talking to — the question is a gift, not extraction

**Example structure:**
> "Your point on [specific claim] in [post/podcast] — does that hold when [adjacent constraint]? Catching you at [event] this week." (135 chars)

---

## Pattern 3: Topic Intersection, Host-Curation Angle

**Use when:** Writing to the event host/organizer (who rarely gets thoughtful outreach — most messages they receive are "can I speak at your event?" pitches).

```
[Reference the deliberate curation + a question about WHY they framed the event the way they did]
```

**Why this works:**
- Hosts almost always get pitches, not engagement on their curatorial POV
- Asking about a deliberate framing positions them as the intentional curator they are
- Acceptance rate is high because the message is in the top 1% of what they typically receive

**Example structure:**
> "The [specific framing in event title] framing — deliberate, or did the agenda land there? Asking because [your hypothesis]." (124 chars)

---

## Anti-Patterns at 200 char

These eat your character budget for zero value. Cut all of them:

| Anti-pattern | Why it's wrong |
|---|---|
| "Hi [Name]," | LinkedIn already shows your message in their inbox with names attached. 8-15 wasted chars. |
| "I'm Alex, I work in [field]" | Your profile carries this. 30+ wasted chars. |
| "I noticed your..." / "I've been thinking..." | Filler — get to the point. |
| "Would love to connect" / "Let's connect" | The connection request IS the CTA. Saying it is redundant. |
| "Coffee?" / "Quick call?" / "20 min chat?" | Connection notes don't book meetings. Save that for AFTER acceptance. |
| Multiple sentences before the question | Question first; context if there's room. |
| "Looking forward to your talk!" | Fluff. Burns chars on nothing. |
| "Hope this finds you well" | Don't. |
| Compliments without specifics ("Love your work", "Big fan") | Generic praise reads as filler at any length, and burns chars you can't afford. |

---

## Personalization Rubric (unchanged bar — tighter form)

Target Level 3 every time. If you can't reach Level 3 within 200 chars, **flag as "needs more research" rather than shipping a Level 2 note.** A weak note is worse than no note — it burns the impression.

| Level | What It Looks Like | Quality |
|---|---|---|
| Level 1 | "Saw your work at [Company], would love to connect" | Generic. No signal. Don't send. |
| Level 2 | "Your talk on [Topic] at [Event] sounds interesting" | Better, but no specific anchor. Below the bar. |
| Level 3 | "On [specific claim/moment from their actual work] — [sharp question]" | The bar. Specific anchor + a question worth answering. |

---

## Variant generation rule (added 2026-05-20)

The `pre-event-content` skill generates **2 variants per person — Variant A and Variant B — anchored to materially different signals**:

- **Variant A** uses Pattern 1 (talk-anchored) — references the speaker's session/abstract for the upcoming event
- **Variant B** uses Pattern 2 (adjacent-work-anchored) — references recent posts, podcasts, OSS commits, or other work outside the talk

The two variants must NOT be reworded versions of the same idea. They must be anchored to genuinely different research signals, so the picker decision is "which signal lands harder for this person" rather than "which phrasing reads better."

**Fallback:** if only one Tier 1 signal exists (e.g., a talk abstract but no recent adjacent work), generate only that variant and explicitly note "Variant B (or A) skipped — no [X] signal found." Never ship a Level 2 filler variant just to have two.

**For hosts/organizers** (rather than speakers): Variant A uses Pattern 1 if they're also presenting, or Pattern 3 (host-curation angle) if they're purely organizing. Variant B uses Pattern 2 (their adjacent work).

---

## Note-to-Question Relationship

Connection request notes and Prepared Questions are now generated **independently** from the same research insights (changed 2026-05-20 — previously, prepared questions came from unused DM variants):

1. **Per-person research** surfaces N candidate questions/signals from talk abstracts, recent posts, work
2. **Step 4** picks the SHARPEST one and trims it to ≤200 chars for the connection note
3. **Step 6** keeps the longer-form versions of these (plus others not used for the note) as Prepared Questions for live engagement at the event

The note and the prepared questions can share research foundation but serve different moments:
- **Note:** punchy, optimized for connection request acceptance, ≤200 chars
- **Prepared questions:** textured, optimized for in-person depth, multi-sentence OK

If the connection request is accepted, the prepared questions become the natural follow-up
material — but they live in your Notion artifact, not in the connection note itself.

---

## Counting characters

Character count includes spaces and punctuation. Generate, then count, then trim — never trust
that "this looks short enough." Quick mental ruler:
- 200 chars ≈ 30-40 words
- Typical tweet is ~70 chars / ~280 chars upper bound
- 200 chars is roughly 2-3 short sentences max, often just 1 dense sentence + 1 question

When in doubt, count.

---

*Last updated: 2026-05-20*
*Version: 0.2 — Reframed from multi-sentence DMs to 200-char connection request notes.
LinkedIn free-tier operational reality made the prior 4-6-sentence DM spec wrong; replacement
spec optimizes for connection request acceptance on the free plan.*
