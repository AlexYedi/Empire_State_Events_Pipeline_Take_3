---
description: "Turn any past or future event into N evergreen, presenter-level deep-dive posts — decoupled from event timing. Marries the live transcript + the post-event brief + matched slide photos into one teardown per speaker, with a radar/job-search layer. Builds a content bank to drip over weeks."
argument-hint: "[event name as it appears in Notion] [optional: --speakers \"Name1,Name2\"]"
---

# /evergreen-deep-dive — presenter-level evergreen posts from a past event

The "expand value beyond before/after the event" layer (the evolution past `/post-event-content`).
Where post-event content is time-sensitive (publish within ~48h), **deep-dives are timeless**: each
teaches ONE presenter's framework so it's valuable any week — a bank Alex can drip while pulling
back on live attendance, and a way to stay on each speaker's (and target employer's) radar by
amplifying their talk.

Proven first run: NYC GTM+AI Masterclass #5 → 5 deep-dives (Sangram/Eric/Nikita/Nimo/Kenny).

## When to run
Any event (recent or months old) that has: a **transcript** (ideally the ElevenLabs recipe output
from `/ingest-recording`) + a **post-event brief** (the data store, with the per-segment deep-dives
+ confidence-flagged quote bank). Slides + a `slide-transcript-alignment.md` make it much richer but
aren't required (no-slides events still work, e.g. AI Demo Night).

## Inputs (resolve in Step 1)
- Notion **Event row** → roster (People/Companies), Author Steer, Topics.
- **EL transcript** (verbatim quote source) + the **REVIEW (low-confidence)** list.
- **Post-event brief** (`POST-EVENT BRIEF — <event>.md`) — the per-presenter analysis spine.
- **Slide photos** + `slide-transcript-alignment.md` if present.

## Step 1 — Resolve event + build the slide→speaker map
Resolve the Notion Event row (as in `/post-event-content` Step 1). Then map slides to presenters:
- **If a `slide-transcript-alignment.md` exists:** use its segment sections + "slide capture timeline."
- **Else:** group slide photos by capture time (`PXL_YYYYMMDD_HHMMSS` filename = on-screen moment);
  the large time gaps between clusters mark presenter changes. Assign each cluster to the speaker of
  that segment (from the brief's Speaker Map).
Produce: per presenter → {transcript span, brief segment, slide filenames}.

## Step 2 — Fan out one deep-dive agent per presenter (parallel)
One subagent per speaker (general-purpose), each given ONLY its slice. Each agent:
1. Reads its transcript span + the brief's segment deep-dive + its matched slide photos.
2. Web-enriches the speaker + company (recent funding/launches; correct spellings).
3. Produces **4 deliverables** to `…/<event>/Deep-Dives/Deep-Dive — <Speaker> (<framework>).md`:
   - **Evergreen post** (≤3,000 chars) — lead with the FRAMEWORK/idea, teach it so a reader can use
     it Monday, credit the speaker + company throughout. **No "last week I attended" urgency.**
   - **Visual brief** — a carousel that *renders that speaker's own slides* (clean diagram/matrix,
     not a quote echo; per `content-patterns/visual-briefs.md`). Note which slide each draws from.
   - **Radar note** — how this keeps Alex visible to the speaker/company + the soft positioning angle.
   - **Connection note** (≤200 chars, talk-anchored).

## Framing rules (what makes a deep-dive a deep-dive)
- **Evergreen:** the idea leads; the event is the *source*, not the occasion. It should read well 3
  months later.
- **Radar / job-search layer:** genuinely amplify the speaker (distribute their IP, clean render of
  their framework) → the kind of post a founder reshares. Position Alex as a **fluent practitioner-peer
  / curator, NOT "hire me."** Tag the company where natural (employer radar).
- **Quote-safety (R1):** verbatim only from the brief's HIGH-confidence bank; paraphrase MED; respect
  `[VERIFY]` flags + the REVIEW list; never assert an unsourced thesis (CLAUDE.md Rule 12).
- **One framework per post.** If a speaker had two, pick the more durable; don't cram.

## Step 3 — Ship (main thread)
- **Notion:** one Content Draft per deep-dive — `Content Type: linkedin_post_post`, `Event Phase:
  post_event`, linked to the Event row, `needs_review`. (Title prefix `Deep-Dive — `.)
- **Gamma:** push each carousel (`format: social`, `4x5`, Stratos dark, `noImages`, PDF export).
- **Drip plan:** stagger ~2/week over 2–3 weeks; alternate broad-appeal ↔ deep/technical; lead with
  the widest-appeal framework. Surface the suggested order to Alex.

## Notes / gotchas
- Subagents can't write Notion/Gmail (memory `empire-events-notion-write-path`) → agents write the
  deep-dive FILES; the parent commits to Notion + fires Gamma.
- **Pin ABSOLUTE output paths per agent + verify locations after.** A relative `…/Deep-Dives/…` in a
  fan-out prompt caused one 2x-AI agent to misfile into the *wrong* event folder (caught in
  verification, relocated). Always give each agent the full event-folder path, and `ls` the
  Deep-Dives folders before shipping.
- Subagents can't spawn subagents (SDK constraint) — the fan-out runs from this command's main thread.
- The same brief can also feed the time-sensitive `/post-event-content` recap — deep-dives are the
  *evergreen* expansion, run later and per-speaker.

## References
- `.claude/commands/post-event-content.md` (the time-sensitive sibling; shares Step-1 resolution + the brief)
- `.claude/commands/ingest-recording.md` (produces the transcript this runs on)
- `.claude/skills/content-patterns/visual-briefs.md` · `.claude/references/content-style-guide.md`
