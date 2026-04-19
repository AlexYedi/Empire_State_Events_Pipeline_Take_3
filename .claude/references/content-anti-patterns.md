# Content Anti-Patterns

> Words, phrases, patterns, and structural choices to avoid in all generated content.
> This list grows over time as Alex identifies what doesn't work.
> Updated via the `update-voice-and-style` skill.

---

## Off-Limits Words & Phrases

> Starting sparse. Alex will flag additions as content gets produced and reviewed.

| Category | Examples | Why |
|---|---|---|
| Omnipresent buzzwords | "leverage", "unlock", "synergy", "ecosystem", "disrupt" | Overused to the point of meaninglessness |
| Jargon stacking | "AI-powered digital transformation leveraging cutting-edge solutions" | Says nothing. Signals you have nothing specific to say. |
| Super salesy | "game-changer", "revolutionary", "I'm excited to announce" | LinkedIn cringe. Breaks the documentarian tone. |
| Thought leader cosplay | "thought leader", "visionary", "industry leader" | Self-applied titles signal insecurity, not authority |
| Empty validation | "Love your work!", "Great post!", "This is amazing!" | Zero information content. Especially in DMs. |
| Faux casual fillers | "I'm curious", "I'd love to hear", "I'm wondering" | Overused, dehumanized, lazy. Not how people talk in real conversations. |
| Observer framing | "Saw you were...", "Noticed you're..." | Implies you're watching from outside, not participating. State your involvement. |
| Citing studies in DMs | "Gartner found that 81%...", "A NAACL 2025 study shows..." | Performing research, not having a conversation. Save stats for posts. |
| Leading with company/product name | "Snowflake is...", "Datadog just..." | Reads like an ad within the first 10 characters. Lead with the insight, introduce the company later. |

## Structural Anti-Patterns

| Pattern | Why It Fails |
|---|---|
| Starting a post with "I'm excited to..." | Most common LinkedIn opener. Invisible to the algorithm and the reader. |
| Listing accomplishments as content | "I did X, Y, Z" without insight or analysis. Self-promotional, not documentarian. |
| Asking rhetorical questions as hooks | "Have you ever wondered about AI?" — No. Nobody stops scrolling for that. |
| Long preambles before the point | Get to the insight in the first 2 lines or lose the reader. |
| Ending with "Thoughts?" | Lazy CTA. If you want engagement, ask something specific enough to answer. |
| Wall of hashtags | More than 5 hashtags looks desperate. 2-5, relevant, specific. |
| Tagging everyone mentioned | Looks like engagement farming. Alex formats cross-platform manually. |

## DM Anti-Patterns

| Pattern | Why It Fails |
|---|---|
| "I'd love to pick your brain" | Signals you want something but haven't done any work yourself |
| Generic compliment opener | "I've been following your work and..." — followed by something that proves you haven't |
| Immediate ask for a meeting | Respect the relationship stage. Open a door, don't force one. |
| Copy-paste feeling | If the DM could be sent to anyone by swapping the name, it's not personalized enough |
| Multi-paragraph walls | 4-6 sentences max. Respect their time. |

## Visual Anti-Patterns

| Pattern | Why It Fails |
|---|---|
| Stock photo energy | Generic, interchangeable. Handshakes, laptops on desks, abstract geometric patterns. Signals "I didn't make anything specific to this content." |
| Canva template tell | A template where only the text changed. If the layout looks familiar to a scroller, the template did the work — not you. |
| Paragraph text on images | That's what the post body is for. Images get max 8 words in the headline. |
| Font under 48px at 1080px wide | Fails the 2-second thumb test. If you squint at 375px wide (iPhone SE viewport), the scroller won't read it either. |
| Medium-on-medium contrast | Gray text on gray, pastel on pastel, light blue on beige. Light-on-dark or dark-on-light only. |
| Chart junk | Gridlines, 3D effects, legends requiring cross-reference. Extract the insight, don't recreate the chart. |
| More than 3 colors in a visual | Background + text + accent = 3. More = noise, not design. |
| Red-green color pairings | Colorblind-hostile. 8% of men can't reliably distinguish. Use labels or patterns alongside color. |
| Pure white backgrounds on mobile | Glare on phones. Dark backgrounds read better in LinkedIn's mobile feed. |
| Neon on neon | Unreadable. Also tacky. |
| 16:9 landscape default | Loses ~65% of vertical screen space vs 4:5. Default is 1080x1350 (4:5 portrait). |
| Carousel under 5 slides | Feels thin, like you ran out of material. 5-8 is the sweet spot. |
| Carousel over 10 slides | Swipe fatigue. You lose the reader before the payoff. |
| Missing page numbers on carousel | No signal that there's more to swipe. Put them small, bottom corner. |
| Missing alt text | Accessibility miss and LinkedIn notices. Every image, every time. |
| Relying on color alone to convey meaning | Use labels, patterns, or icons alongside color — not instead of them. |
| Tiny or missing source attribution on data visuals | If the number is worth showing, the source is worth citing. Small text, bottom corner. |
| Visual tries to show multiple ideas | One visual = one idea. If you need three, make three visuals (or a carousel). |

## AI Image Prompting Anti-Patterns

| Pattern | Why It Fails |
|---|---|
| Aspirational adjectives ("professional looking") | Meaningless to the model. Specify style concretely: "flat vector illustration" / "editorial magazine photography" / "technical diagram style". |
| No negative prompts | The model fills gaps with defaults. Specify what NOT to include: "no text, no watermarks, no people, no generic tech imagery, no stock photo energy". |
| Single-shot acceptance | First output is a draft, never the deliverable. Iterate in 3 rounds minimum: prompt → evaluate → refine → evaluate → final. |
| No composition spec | The model centers everything by default. Specify: "symmetrical, negative space on left for text overlay" / "wide landscape" / "centered subject with asymmetric framing". |
| No mood specification | Output drifts generic. Specify: "authoritative and clean" / "bold and provocative" / "minimal and sophisticated". |
| Treating the prompt as a wish, not a brief | Prompt quality = output quality. Write architecturally: composition + style + mood + negatives. |

---

*Last updated: 2026-04-18*
*Version: 0.3 — Added Visual Anti-Patterns and AI Image Prompting Anti-Patterns sections from 10 best practices doc*
