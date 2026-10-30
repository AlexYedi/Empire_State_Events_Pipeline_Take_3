## Visual Brief — 4-slide carousel (Arc 1: Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** Long-running agents now carry five layers. Each layer has a seller and a stated limit or open question. "The keys" is really two layers, the runtime and the release pipeline, so the reader should leave able to ask who owns each layer in their own stack.

**Slide count:** 4. The arc fits in 4, so it isn't padded to 5. The cleaner-design steer also argues for fewer, emptier slides.

**Aspect ratio:** 4:5 (1080x1350), the LinkedIn carousel default

**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome → PDF. No Gemini, because nothing is pictorial.

**Palette (all slides):** dark slate ground #0F172A, white text #F8FAFC, and ONE accent, blue #60A5FA (agents/infra, lightened for contrast on dark). "Open question" cells render as dashed grey outlines (#94A3B8, a tint of the text, not a fourth colour) and carry the word "open", so meaning never rests on colour alone. Signature acid green #8FE83A appears only as the name-mark underline on slide 4.

**Carousel PDF title (public on LinkedIn):** "What a long-running agent carries, and who owns it"

### Slide 1 of 4 — Hook: the stack, as one picture

- **Job:** Shows the five layers as one vertical stack, so the post's list becomes a structure the reader can hold.
- **Visual mode:** Diagram (stacked layers)
- **Headline:** What does a long-running agent carry?
- **Body / content:** Five stacked horizontal bars, bottom to top in talk order: MACHINE STATE · PER-AGENT MEMORY · WORLD MODEL OF PRODUCTION · CUSTOMER MEMORY ACROSS CHANNELS · KEYS. The KEYS bar is split down the middle into two halves, labelled "runtime" and "pipeline" (accent blue outline). This is the teaser for slide 3. Eyebrow: "Daytona AI Builders · NYC · Oct 28". Page number 1/4.
- **Palette:** dark bg + white text + blue #60A5FA on the split KEYS bar only
- **Source attribution:** Layers: talk agenda, Daytona AI Builders NYC (Luma), 2026
- **Alt text:** A stack of five layers a long-running agent carries, from machine state at the bottom to keys at the top, with the keys layer split into runtime and pipeline.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 4 — Evidence: every layer has a seller, and a limit

- **Job:** Adds what the post doesn't carry: who sells each layer and the limit or open question each one comes with.
- **Visual mode:** Framework / matrix (5 rows × 2 columns)
- **Headline:** Every layer has a seller, and a limit
- **Body / content:** Columns: "Sold as" | "Stated limit (solid) or open question (dashed)".
  - Machine state | Daytona sandboxes | Docs: fork works on VM sandboxes only (solid)
  - Per-agent memory | AWS AgentCore Memory | Open: who settles contradictions across 10 memories? (dashed)
  - World model | Antimetal | Open: Jan layers ≠ Oct layers. Rename? (dashed)
  - Customer memory | Twilio Conversation Memory (GA May 6) | Twilio's own build post: a new customer has no context until a first conversation closes (solid)
  - Keys | Infisical Agent Vault · Daytona Secrets Manager | Infisical: Agent Vault doesn't address data sent out via an allowed API (solid)
  - Cells stay at ≤12 words, rendered at ≥36px.
- **Palette:** dark bg + white text + blue #60A5FA on the three solid "stated limit" cells' left rule; dashed grey for the two open cells
- **Source attribution:** Sources: Daytona docs (Sandboxes), 2026 · Antimetal blog, Jan 2026 · Twilio changelog, May 2026, and Twilio blog (Obert, Conversations + eve build), Oct 8 2026 · Infisical blog, Apr 2026 · talk abstracts, Luma, 2026
- **Alt text:** A table pairing each of the five layers with the product that sells it and either a limit the company itself states or an open question for the talk.
- **Tool:** Claude design (HTML/SVG)
- **Accuracy note for the render:** Twilio's cold-start concession comes from the Oct 8 Obert post, which pairs Twilio Conversations (long-term memory) with Vercel eve. It isn't from the Conversation Memory launch page, so the cell says "Twilio's own build post", not "Conversation Memory can't…". The product's design is consistent with it, since memories are extracted after a conversation goes idle, but don't upgrade the wording.

### Slide 3 of 4 — Mechanism: the keys are two layers

- **Job:** Explains why "the keys" splits, by showing where both 2026 LiteLLM compromises landed versus where a credential proxy sits.
- **Visual mode:** Diagram (left-to-right flow across two labelled zones)
- **Headline:** The keys are two layers
- **Body / content:**
  - Left zone, labelled "RELEASE PIPELINE": [maintainer / CI credentials] → [release workflow] → [PyPI · Docker].
  - Right zone, labelled "AGENT RUNTIME": [package installed in the sandbox] → [agent] → [credential proxy] → [model & tool APIs].
  - Two accent markers with text labels sit on the left zone: "Mar 2026: maintainer publishing credentials (NetSPI)" on the credentials box, and "Oct 21: stolen GitHub CLI tokens → release workflow (Datadog)" on the workflow box. Both markers carry a "HIT" text tag.
  - The proxy box in the right zone gets a white outline and the tag "keeps real keys out of the agent's box".
  - A thin dashed arrow labelled "poisoned package" runs from the left zone into the right.
  - Footer, small: "October details still moving. No link between the two established (Datadog)."
- **Palette:** dark bg + white text + blue #60A5FA on the two HIT markers
- **Source attribution:** Sources: Datadog Security Labs, 2026-10-21 · NetSPI, 2026-03-24 · Infisical docs (Agent Vault), 2026
- **Alt text:** A flow from the release pipeline into the agent runtime, showing that both LiteLLM compromises hit the pipeline side while a credential proxy sits on the runtime side.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 4 — CTA: own-it worksheet

- **Job:** Hands the reader the question as a tool to use on their own stack, not as a recap.
- **Visual mode:** Framework (fill-in grid)
- **Headline:** Who owns it in production?
- **Body / content:** Grid with 6 rows (Machine state · Per-agent memory · World model · Customer memory · Keys: runtime · Keys: pipeline) × 3 columns (Platform · Vendor · Us), all empty checkboxes. Sub-line: "One tick per row. Then: who gets paged?" Footer: "Daytona AI Builders · NYC · Oct 28". Name mark "Alex Yedi" with the #8FE83A underline. Page number 4/4.
- **Palette:** dark bg + white text + blue #60A5FA on the column headers; #8FE83A name-mark underline only
- **Source attribution:** none needed (no data or quote)
- **Alt text:** An empty worksheet asking the reader to mark whether the platform, a vendor or their own team owns each of six agent layers, keys split into runtime and pipeline.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**
- Arc fit: pass. The post is one thesis (five layers, one ownership question) grounded in one mechanism (the LiteLLM layers point). That's Arc 1. Arc 4 was rejected under its guard, because a slide per speaker would re-print the post's list.
- Job differentiation: pass. The jobs are: the structure, the sellers and limits, the keys mechanism, and the reader's worksheet. No two can be swapped.
- Frame parallelism: n/a (Arc 1). Slides 1 and 4 share the layer order and labels, so the worksheet reads as the stack turned into a tool.
- Thumb test per slide: pass on headlines (5–7 words). Flag slide 2 as the densest, against the cleaner-design steer. If it overflows at 375px, cut the "Sold as" column to company names only.
- Source citations: pass. Slides 1–3 carry source lines, and slide 4 has no data.
- Adds information (not repetition): pass. The post doesn't contain the split keys bar, the limits matrix (the VM-only fork limit, Twilio's cold-start concession), the pipeline/runtime flow, or the worksheet. Variant A mentions the Infisical limit, so that one cell overlaps A only.
- Slide count integrity: pass. Each slide is load-bearing.
- Final slide earns the swipe: pass. It's a usable worksheet, not housekeeping.
- Public-file check (carousel PDFs are downloadable): pass. No private URLs, no attendee names, no unverified claims.

**Themes (Step 1.3b, from the fixed list):** ["agents-agentic-stack", "devtools-ai-infra", "security-governance"]
