# Speaker Deep-Dive Pattern (evergreen, per presenter)

The methodology for the optional final step of `/post-event-content` (Step 5.6). Ported from the
retired `/evergreen-deep-dive` command (archived in tag `archive/pre-reset-2026-09-28`); the command
file holds the orchestration, this file holds what "good" looks like.

Where the post-event recap is time-sensitive (publish within ~48h), a deep-dive is **timeless**: each
post teaches ONE presenter's framework so it reads well three months later. It builds a content bank
Alex can drip while pulling back on live attendance, and keeps him on each speaker's (and target
employer's) radar by amplifying their talk. First proven run: NYC GTM+AI Masterclass #5, five
deep-dives.

## When it applies

Any event, recent or months old, that has both:
- a **`post_event_brief`** (Content Draft, Step 3.7) with its Speaker Map and confidence-tagged Quote Bank;
- a **transcript**: Supercut first (`.claude/references/supercut.md`), else the `/ingest-recording`
  audio output (`.claude/commands/ingest-recording.md`), else a persisted paste in `event-transcripts/`.

Slide photos (or Supercut frames) and a `slide-recording-alignment` file make it richer but are optional.
Skip speakers who had no framework worth teaching (panel filler, a pure product demo with no idea).

## Step A — Build the per-presenter slice (parent thread)

1. Read the `post_event_brief` from Notion and the transcript.
2. Map slides to presenters: use the alignment file if present; else group slide photos by capture
   time (`PXL_YYYYMMDD_HHMMSS` = on-screen moment; large gaps between clusters mark presenter changes)
   and assign each cluster to that segment's speaker from the Speaker Map.
3. Produce, per presenter: {transcript span, brief segment, HIGH/MED quotes, slide files}.
4. Confirm the speaker list with Alex (he may pass a subset).

## Step B — Fan out one drafting agent per presenter (parallel, parent thread)

One `general-purpose` subagent per speaker, all dispatched in one message (subagents cannot spawn
subagents; CLAUDE.md invariant 6). Each gets ONLY its slice plus the framing rules below. Agents do web
enrichment and text only: **no Notion, HubSpot or Gmail writes** (CLAUDE.md invariant 5).

- Give each agent an **absolute** working path:
  `<repo>/.claude/.state/deep-dives/<event-slug>/<speaker-slug>.md` (gitignored). Never `Event Content/`
  or any tracked path. A relative path once misfiled a draft into the wrong event folder: `ls` the
  folder after the fan-out and relocate anything misplaced before shipping.
- A thin return gets re-invoked alone with deeper scope; don't restart the batch.

Each agent returns four deliverables:

1. **Evergreen post** (≤3,000 chars) in **3 inline hook variants** (same body, different openers;
   CLAUDE.md §6). Lead with the framework, teach it so a reader can use it Monday, credit the speaker
   and company throughout. No "last week I attended" urgency: the event is the source, not the occasion.
2. **Visual brief** (3–5 slides) that renders the speaker's own framework cleanly (diagram, matrix,
   sequence), not a quote echo, per `.claude/skills/content-patterns/visual-briefs.md`. Note which
   source slide each draws from.
3. **Radar note (PRIVATE).** How this keeps Alex visible to the speaker and company, and the soft
   positioning angle. Job-search material: it lives only in the Notion page body or `.claude/.state/`,
   never in a tracked file or commit (CLAUDE.md invariant 4).
4. **Connection note(s)** per `.claude/references/outreach-templates.md`: A talk-anchored; B
   adjacent-work-anchored only if a real anchor exists. 200-char cap.

## Framing rules (what makes it a deep-dive)

- **One framework per post.** If a speaker had two, pick the more durable; don't cram.
- **Amplify, don't pitch.** Distribute their IP with a clean render of their framework: the kind of
  post a founder reshares. Alex is a fluent practitioner-peer and curator, never "hire me." Tag the
  company where natural.
- **Quote safety.** Verbatim only from the brief's HIGH-confidence bank; paraphrase MED; respect
  `[VERIFY]` flags and the transcript's low-confidence REVIEW list.
- **Source-check** any firm- or person-level thesis claim before it appears in copy (CLAUDE.md §6
  source-check rule): unsourced means verify, soften or cut.
- Voice and anti-patterns: `.claude/references/content-style-guide.md`,
  `.claude/references/content-anti-patterns.md`, `.claude/references/audience-north-star.md`.

## Step C — Ship to Notion (parent thread, inline)

One Content Draft per speaker, search-before-create on the title (CLAUDE.md invariant 8):
- Title `Deep-Dive — <Speaker> (<framework>)`; `Content Type: linkedin_post_post`;
  `Event Phase: post_event`; `Content Status: needs_review`; `Event` relation; `People` relation to
  the speaker; Goal/Target per `.claude/skills/content-patterns/goal-tagging.md`.
- Body: the 3 hook variants, the post body, `## Visual Brief — N-slide carousel`, the connection
  note(s), then `## Radar note (private)`. All as **plain paragraphs, never code blocks**
  (`.claude/references/notion-write-gotchas.md`). Ship every variant; never pre-select.
- **Carousel: render on publish.** Keep the brief now; render with headless Chrome per
  `visual-briefs.md` → `## Execution` only when Alex picks that post to publish (evergreen posts sit
  for weeks). Render now only if he says he is posting soon.
- After Notion confirms, the `.state` working files may be deleted; Notion is the record.

**Drip plan (guidance, one line):** ~2/week, alternating broad-appeal ↔ technical, widest-appeal
framework first; surface the suggested order to Alex.

## Failure modes

- **No `post_event_brief`** → run `/post-event-content` through Step 3.7 first; a deep-dive without
  the brief has no quote-safety bank.
- **No transcript** → brief-only deep-dives are allowed but paraphrase-only (no verbatim quotes); say so.
- **A Notion write fails** → return that speaker's draft in chat so the work isn't lost.
