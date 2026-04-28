# Two-Thesis Synthesis Pattern

A reusable content shape for documentarian-style LinkedIn posts that contrast two
events' strategic implications into a single load-bearing question. This file is
the authoritative definition — skills that generate, review, or cross-reference
synthesis posts should read it rather than re-derive the shape from scratch.

Owner: Alex — personal voice. Edit this file when the voice evolves; all skills
that import it inherit the change.

---

## Why this pattern exists (and why it's Alex's differentiator)

Most event posters recap. Alex's edge — per the documentarian angle called out in
the project architecture — is *synthesizing across events* into a pattern nobody
else is writing. The two-thesis synthesis is the shape of that edge. It compresses
two ephemeral rooms into a strategic question the rest of the market is also
quietly trying to answer, and it credits the speakers and hosts who surfaced the
theses in the first place.

The pattern works because it does three things at once:

1. **Demonstrates pattern recognition.** Contrasting two events shows you're not
   just "at events" — you're reading the market across them.
2. **Credits specific people.** Hosts, speakers, and the specific rooms get named.
   This is the soft-intro mechanism for the DM follow-ups.
3. **Leaves the tension unresolved.** The invitation is genuine — not rhetorical.
   The post earns replies because the question is still open.

---

## The 6-part shape

ALWAYS use this sequence. Word counts are targets, not hard caps.

| Section | Target | Role |
|---|---|---|
| **Hook** | 15-30 words | Establish that two distinct events happened in the same window and that they said opposing things. |
| **Thesis A** | 40-60 words | Compress Event A's core claim to one sentence. Then 1-2 sentences of evidence (who said what, which detail made it stick). |
| **Thesis B** | 40-60 words | Same shape as Thesis A. Event B's compressed claim + evidence. Do NOT hedge — if Thesis B is stronger, it's stronger. |
| **Tension** | 30-50 words | The strategic question the two theses force against each other. This is the load-bearing sentence of the post. If the tension is weak, the post doesn't ship. |
| **Take** | 40-70 words | Where you're landing and why — or, honestly, that you haven't landed yet and here's what would move you. Include the criterion you're using, not just the verdict. |
| **Invitation** | 15-25 words | A specific open question back to the reader. Not "what do you think?" — something the room can actually answer with a real opinion. |

Total: 180-295 words. LinkedIn's sweet spot.

---

## Voice rules specific to this pattern

- **Name names.** Speakers, hosts, companies. Credit the room. This is how the post
  serves both as content and as soft intro for the DM sequence.
- **Don't strawman either side.** Both theses should be presentable by the people
  who argued them. If you can't pass an ideological Turing test on either side,
  you haven't listened closely enough — go back to the briefs.
- **Don't false-balance.** If one thesis is clearly stronger, say so in the Take.
  "Both sides have a point" is a tell that you skipped the hard work.
- **Specific over clever.** Concrete detail (a demo, a stat, a specific architecture
  choice) beats abstract framing. The reader should be able to picture the room.
- **No throat-clearing.** No "I had the pleasure of attending..." No "great event
  by X and Y." The hook does the work. Thanks go in the DMs, not the post.
- **First person singular.** This is Alex's take, not a company post. "I" not "we."
- **No consultant-ese.** Kill "leverage," "ecosystem," "at scale" when it's vague,
  "unlock," "transformation." Use the actual words the speakers used.

---

## Trigger conditions (when this pattern applies)

Apply when ALL of these are true:

1. Two or more event research briefs exist in Notion with a Last Researched date
   inside a rolling 7-day window (either direction — briefed before attendance or
   after).
2. The dominant topics across the two briefs can be compressed into opposing
   strategic claims (not just different claims — *opposing* ones).
3. The briefs are deep enough to support confident evidence sentences. A thin
   brief produces a thin Thesis, which produces a thin post.

## Gating conditions (when to NOT write one, even if tempted)

Do NOT ship a synthesis post when any of these are true:

- **The theses converge rather than diverge.** Both events said "AI agents are
  important" = no post. There's no tension.
- **The tension is about tooling preference, not strategy.** "Tool X vs Tool Y"
  usually isn't load-bearing enough for this pattern. Save it for a different
  format.
- **One brief is too thin.** If Event B's brief is 2 sentences, Thesis B will
  feel manufactured. Wait until the brief is stronger or pair with a different
  event.
- **The pattern is already fatigued.** Max 1 synthesis post per week. Two in 7
  days and the format loses its teeth. If you've already shipped one this week,
  either queue the new one for next week or pick a different format (recap,
  pattern-across-5-events, etc.).
- **You can't identify a specific open question.** If the Invitation feels generic,
  the Tension is probably generic too. Generic tensions don't earn replies.

---

## Seed examples (from real events, April 2026)

### Example 1 — FDE vs Microsoft: "Platform absorbs agents vs bespoke beats generic"

- **Event A:** FDE Panel hosted by Acacia Ventures. Speakers: Caitlin, Jordan, Kamesh.
  Thesis: *Bespoke beats generic.* The winning agentic products in enterprise aren't
  generic agents plus prompts — they're context-engineered forward-deployed builds
  that encode a specific customer's workflow, data, and exceptions.
- **Event B:** Microsoft Azure Tech Brief. Thesis: *Platform absorbs agents.* Foundry
  + GitHub + VS Code is being positioned as the unified enterprise agent stack —
  Microsoft's bet is that the platform wins and bespoke agent work commoditizes into
  building blocks.
- **Tension:** Does the agent layer commoditize (Microsoft wins) or does context
  engineering keep it bespoke (FDE wins)? Both sides see this — the disagreement is
  whether generic platform primitives can encode enough customer context to matter.
- **Why this works as an example:** Two events, one week, directly opposing theses,
  both defensible, tension unresolved. Real people said real things that can be
  quoted or paraphrased faithfully.

### Example 2 — Microsoft vs Agora: "Integration wins vs infrastructure wins"

- **Event A:** Microsoft Azure Tech Brief. Thesis: *Integration wins.* Azure Voice
  Live — voice agents ship because the integration layer (Foundry + model + telephony
  + hand-off) is unified. The moat is orchestration.
- **Event B:** NYC Voice AI Meetup hosted by Agora. Speakers: Hermes Frangoudis, Bryce
  James, Sahar Mor. Thesis: *Infrastructure wins.* Sub-200ms global latency (SD-RTN),
  VAD, barge-in, streaming pipelines — the reason a voice agent feels alive is the
  real-time transport layer, not the model. Agora's conversational AI ARR ramp is the
  signal.
- **Tension:** Where does voice-agent value actually accrue — the model-integration
  layer (Microsoft) or the real-time transport layer (Agora)? And: does a production
  voice agent need both, or will one absorb the other as the category matures?
- **Why this works as an example:** Same-day events, opposing theses, both technically
  load-bearing, tension maps to a real architectural question teams are actively
  making bets on right now.

---

## Bad examples (fabricated, with diagnostic)

### Bad Example A — Theses converge, tension is manufactured

> "I went to two AI events this week. At Event 1, they said AI agents are
> transforming how we work. At Event 2, they said AI agents are changing
> enterprise software. The tension: are agents transforming work or changing
> enterprise software? My take: both."

**What's wrong:** Those aren't opposing theses — they're the same thesis twice.
The "tension" is a false binary. The Take is empty. Fix: either find a real
contrast between the two events or abandon the synthesis format.

### Bad Example B — False balance on a clear winner

> "Event A said platforms win. Event B said bespoke wins. Both have merit. The
> answer is probably somewhere in the middle."

**What's wrong:** "Somewhere in the middle" is a cop-out when the evidence
doesn't support it. If Event B's argument had a killer example that Event A
didn't address, say so. The Take should have teeth. Fix: pick the stronger
thesis based on the evidence and say why the weaker one still has a corner where
it wins.

### Bad Example C — Generic invitation

> "...what do you think?"

**What's wrong:** Nobody can answer a generic question specifically. The
invitation should be something a reader can have an actual opinion about.
Fix: replace with a specific forked question. E.g., "Are you building voice
agents today? Where are you putting your time — the model-integration layer or
the transport layer?"

### Bad Example D — Buries the speakers

> "Went to two great events this week. Tons of good conversations. One event
> was about platforms, the other was about bespoke builds..."

**What's wrong:** No speakers named, no specific detail, no credit to the hosts.
The post is working against itself — if it won't get seen by the people who were
in the room, it can't do its soft-intro job for DMs. Fix: name at least the
speakers whose theses you're quoting, and tag them.

---

## How other skills should reference this file

- `pattern-synthesis` skill: loads this file as the canonical template before
  drafting. Quotes the 6-part shape directly. Applies the gating conditions
  before generating output.
- `pre-event-content` skill: references this file when two upcoming events share
  contrasting dominant topics. Rare path — most pre-event content is single-event.
- `post-event-content` skill (when built): references this file when a second
  recent brief would create a viable synthesis. Flags the opportunity rather than
  generating — generation is pattern-synthesis's job.
- `update-voice-and-style` skill: when Alex flags a voice learning that applies
  to this pattern (e.g., "stop using 'at scale'"), update the voice rules section
  here.

---

## Versioning

This file is living. When voice evolves, update in place and note the date + the
change at the bottom of this section.

- 2026-04-19 — Initial version. Seeded with 2 real examples (FDE/Microsoft,
  Microsoft/Agora) and 4 fabricated bad examples. 6-part shape, word targets,
  voice rules, trigger/gating conditions defined.
