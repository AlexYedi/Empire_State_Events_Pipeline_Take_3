## Visual Brief — 4-slide carousel (Arc 1: Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** The four numbers around this launch are four different units, measured against four different baselines. A data refinery is four stages running in your own cloud. So the buyer's job is four questions, and each one has a recognisable good answer.

**Slide count:** 4. The arc fits in 4, and the cleaner-design steer argues against padding to 5.

**Aspect ratio:** 4:5 (1080x1350), the LinkedIn carousel default

**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome → PDF. No Gemini: nothing is pictorial.

**Palette (all slides):** dark slate ground #0F172A, white text #F8FAFC, and ONE accent, emerald #34D399 (data/infrastructure; #059669 lightened for contrast on dark). "Open / not found" cells render as dashed grey outlines (#94A3B8) and carry the words "open" or "not found", so meaning never rests on colour alone. The signature acid green #8FE83A appears only as the name-mark underline on slide 4.

**Carousel PDF title (public on LinkedIn):** "Four numbers, four units: a buyer's read on a data-curation launch"

### Slide 1 of 4 — Hook: the sum that doesn't work

- **Job:** Makes the core claim visible in one glance: four figures that can't be added.
- **Visual mode:** Bold typography card
- **Headline:** These four numbers don't add up
- **Body / content:** Four large figures in one row, each with a small unit tag underneath: "6x" (compute multiplier) · "<1%" (of pretraining tokens) · "~$450K" (one final training run) · "<20%" (of training compute). Between them sit grey "+" signs, and at the end "= ROI", with "ROI" struck through in emerald. Eyebrow: "DatologyAI Curation Studio launch · Oct 27". Page number 1/4.
- **Palette:** dark bg + white text + emerald #34D399 on the strike-through only
- **Source attribution:** Sources: Datology launch post & TR case studies, 2026 · event invite, 2026
- **Alt text:** Four figures, 6x, under 1%, about $450K and under 20%, each labelled with a different unit, followed by an equals sign and a crossed-out ROI.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 4 — Evidence: what each number is measured against

- **Job:** Adds what no variant fully carries: the baseline behind each number, which effort it comes from, and whether a public source exists.
- **Visual mode:** Framework / matrix (5 rows × 4 columns)
- **Headline:** Same launch, five different baselines
- **Body / content:** Columns: Number · Measured on · Against what · Public source?
  - 6x compute · Studio-curated public data · Datology's 39-dataset public baseline (built by Datology) · Yes, launch post, Oct 9
  - ~1/5 compute · 12B-A1.4B curated model, 440B tokens · 30B-A3B baseline, 1T tokens · Yes, launch post (not TR)
  - <1% tokens · TR April testbed: 100B legal tokens · 15T pretraining tokens, 8B model · Yes, Datology, Apr 9
  - ~$450K · TR Thomson final training run · ~$40M program (press; durations differ) · Yes, Datology, Sept 3
  - <20% compute · TR, per the invite · "strongest public data baselines" · Not found (dashed cell), as of Oct 26
  - Cells stay at ≤10 words, rendered at ≥34px.
- **Palette:** dark bg + white text + emerald #34D399 rule on the "Against what" column header; the "not found" cell uses a dashed grey outline
- **Source attribution:** Sources: Datology launch post (Oct 2026) · Datology TR case studies (Apr & Sept 2026) · The Batch / LawNext (2026) · event invite
- **Alt text:** A table listing five efficiency figures around the launch, what each was measured on, the baseline it was compared against, and whether a public source exists. No public source was found for the under-20% figure as of Oct 26.
- **Tool:** Claude design (HTML/SVG)
- **Render note:** This is the densest slide. If it overflows at 375px, drop the "Measured on" column. The baseline column is the slide's whole point.

### Slide 3 of 4 — Mechanism: the refinery, and the loop nobody has priced

- **Job:** Explains what's actually being bought (four stages inside your cloud) and where the open commercial question sits (the rerun loop).
- **Visual mode:** Diagram (left-to-right pipeline inside a boundary box)
- **Headline:** A refinery that runs in your cloud
- **Body / content:**
  - Left, "CRUDE IN": raw web · code · math · your own documents.
  - Four boxes, left to right: CLEAN ("drop junk + test-set leaks") → CURATE ("score, de-duplicate, reweight") → CREATE ("rephrase into cleaner text") → COMPOSE ("pick the mix with small proxy models").
  - Right, "OUT": a training mix → pre-training or mid-training.
  - A dashed boundary around everything, labelled "Your cloud · your GPUs".
  - A dashed emerald loop arrow from a small box "New base model" back to CLEAN, labelled "Rerun? Who owns it? (open)".
- **Palette:** dark bg + white text + emerald #34D399 on the rerun loop only
- **Source attribution:** Sources: Datology Curation Studio launch post, Oct 2026 · explainx, Oct 2026
- **Alt text:** A four-stage pipeline, clean, curate, create and compose, turning raw data into a training mix inside the customer's cloud, with an open question marked on the loop back when the base model changes.
- **Tool:** Claude design (HTML/SVG)
- **Accuracy note:** The stage names follow explainx ("Clean, Calibrate, Create, Compose"). The StartupHub summary uses "curate" for stage 2. Check the label against the launch post before rendering.

### Slide 4 of 4 — CTA: the buyer's checklist

- **Job:** Hands the reader the four questions as a tool, with what a good answer sounds like. This is added information the post doesn't carry.
- **Visual mode:** Framework (2-column checklist)
- **Headline:** Before you buy a data refinery
- **Body / content:** Columns: Ask · A good answer names…
  - What's the unit? · seat, tokens, compute share or outcome, plus a typical first-deal size
  - Against what baseline? · who built it, and whether it was compute-matched
  - Which number is yours? · a result on your data, scored on evals held out of curation
  - Who reruns it? · who re-curates when the base model changes, and the cost
  - Footer: "DatologyAI Curation Studio launch · Oct 27, 2026". Name mark "Alex Yedi" with the #8FE83A underline. Page number 4/4.
- **Palette:** dark bg + white text + emerald #34D399 on the "Ask" column; #8FE83A name-mark underline only
- **Source attribution:** none needed (no data or quote)
- **Alt text:** A four-row checklist pairing each buyer question about a data-curation product with what a good answer would include.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**

- Arc fit: pass. One thesis (four numbers can't be summed) grounded in evidence (the baselines table), with a mechanism (the refinery and its rerun loop) and a usable CTA. Arc 4 was rejected because a slide per speaker would add nothing pre-event.
- Job differentiation: pass. The four jobs are the claim, the baselines, the product mechanics and the reader's tool. No two can be swapped.
- Frame parallelism: n/a (Arc 1).
- Thumb test per slide: pass on headlines (5–6 words). Slide 2 is flagged as dense against the cleaner-design steer, with the drop-a-column fallback above.
- Source citations: pass. Slides 1–3 carry source lines; slide 4 has no data.
- Adds information (not repetition): pass, with one overlap. Slide 1's four figures restate the post's list, which is acceptable for a hook and is why its unit tags and the struck-through "ROI" are the content. Slides 2–4 carry the baseline column, the one-fifth row in table form, the four-stage pipeline with the rerun loop, and "what a good answer names". None of that is in any variant.
- Slide count integrity: pass.
- Final slide earns the swipe: pass. It's a checklist a buyer can reuse, not housekeeping.
- Public-file check (carousel PDFs are downloadable): pass. No private URLs, no attendee names. The under-20% figure is labelled "not found as of Oct 26" rather than asserted.

**Themes (Step 3b, from the fixed list):** ["data-databases", "devtools-ai-infra"]

**Goal / Target suggestion (for the parent's payload):** Goal: reach. Target: someone outside the room replies with the unit their own training-data or curation contract priced on, or asks which of the four numbers held up after the session (the Anti-Goodhart signal). Secondary: engagement from any of the four DatologyAI speakers.

**Content Type / properties for the payload:** linkedin_post_pre · Event Phase pre_event · Content Status needs_review · Platform linkedin · Event = the DatologyAI Event page · People = Morcos, Gaza, Merrick, Wills · Topics = the brief's topic pages (training-data curation, Small Task-Specific Models, AI-Ready Data stays OFF per the brief's do-not-conflate flag)

Excluded per provenance: [Morcos's "Thomson-1 beat GPT-5.6 Sol at 100x lower cost per task" (protocol undisclosed) · the 57% vs 33% blind-preference figure · "second only to Claude Opus 4.8" · Thomson-1.0's base model (contested: Qwen / Cohere / Imperial-Snowdon) · the $40M program's duration (two years vs three months) · the ODSC "model factory, not a model" line and ODSC's "data quality … greater returns" framing · StartupHub's "signal per token" (secondhand summary, not an Ari quote) · the careers page's "7–40x faster" · 46.8% vs 37.7% · 23 PiB processed and the Zephon numbers · Datology Labs details · "several of the Mag 7" customers · Arcee and Deepgram (not needed; kept for post-event) · Datology funding totals, headcount and the "new raise is plausible" inference · Snorkel run-rate (>$350M, from ~$20M) and the Handshake–Cleanlab deal · the Dwarkesh 12x / 3.7x study · the Gartner 3x small-model forecast · all AI-Ready Data stats · the Small Task-Specific Models "models side meets data side" framing (gated on Success Signal 4) · any attribution of the April case study to Luke Merrick · Merrick's Fiddler history · Gaza's Moonsense switch motive · Wills's agents-and-long-pipelines view (kept for questions only) · that TR's own pages name Datology (they don't; every TR claim is attributed to Datology's case studies or press) · any claim about what the session will show or conclude]

⟦carousel-link⟧
