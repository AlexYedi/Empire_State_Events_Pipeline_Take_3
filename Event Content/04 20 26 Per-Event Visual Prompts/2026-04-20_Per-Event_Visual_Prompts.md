# Visual Content Prompts — Week of April 20, 2026

Pre-event visual prompts for the 7 events on the "Going to Events" calendar, Apr 20–23. Each event has three prompts: a hero image (LinkedIn header), an in-post insert image, and an infographic/diagram prompt. All tuned for the documentarian angle — observational, specific, NYC-textured, editorial.

---

## How to use this file

### Voice & visual rules (applies to all prompts)
- **No generic AI imagery.** No glowing neural nets, no humanoid robots, no blue holographic grids, no "matrix" green text, no brains with circuits.
- **Documentarian realism over hype.** Favor editorial photography (Bloomberg, The Information, Harper's Magazine), architectural specificity, ambient texture.
- **NYC is a character.** Lower Manhattan loft light, tribeca brick, west village row houses, sunken living rooms, late afternoon golden hour through warehouse windows — these read as "Alex was actually there."
- **Technical subjects get schematic treatment.** For infrastructure/agent topics, use isometric, blueprint, or data-viz-inspired visual language. Think Edward Tufte, not sci-fi.
- **Humans where humans matter.** For panel/meetup events, include people in ambient-but-not-staged compositions. Keep faces oblique, cropped, or from behind to sidestep likeness issues.

### Model selection guide
| Use case | Best model | Why |
|---|---|---|
| Photorealistic NYC interior, event ambience | **Midjourney v6.1** or **Imagen 3** | Strongest editorial aesthetic control; Imagen 3 handles interior light well |
| Schematic / isometric diagrams | **Imagen 3** or **DALL-E 3** | Better prompt adherence for structural work |
| Infographic with readable text | **Imagen 3** (best text rendering among image models) — or **Canva/Gamma** if text accuracy matters |
| Stylized editorial illustration | **Midjourney v6.1** with `--style raw` | Cleaner, less default-glossy output |

### Prompt conventions used below
- Midjourney prompts end with parameter flags (`--ar 16:9 --style raw --v 6.1`)
- Imagen 3 / DALL-E 3 prompts are prose-first with explicit style notes
- Aspect ratios: 16:9 for LinkedIn hero, 1:1 for in-post insert, 4:3 for infographic

---

## Event 1 — A Better Way to Build Agents: Workflows (Vercel)
**Mon Apr 20, 5:30–8:00pm · Spring Place, 6 St Johns Ln (Tribeca)**
Vercel Workflows launch · Peter Wielander + Flora + Danny Aziz · TypeScript agents, durable execution

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a Tribeca loft workspace at dusk, exposed brick and
cast-iron columns, long communal table lit by warm pendant bulbs, laptops
open with terminal windows glowing in the ambient light, cables coiled on
dark walnut surface, half-eaten slice of pizza on a white plate, one person
mid-typing in the blurred background, shot on 35mm film grain, cinematic
depth of field, muted palette of oxblood / charcoal / brass, the quiet
tension of a ship-it night, no faces visible --ar 16:9 --style raw --v 6.1
```

**Imagen 3 alternative:**
```
A wide editorial photograph of a Tribeca loft interior at early evening,
warm tungsten light, exposed brick walls and cast-iron columns, a long
reclaimed-wood communal table covered in open laptops showing code editors,
scattered notebooks and coffee mugs, one soft-focus silhouette of a
developer at the far end of the table, shot in the style of a Monocle
magazine feature, muted color palette, 35mm film grain texture, natural
documentary composition.
```

### In-post insert (1:1)
**Midjourney v6.1:**
```
Close-up overhead shot of hands at a keyboard, terminal window visible on
laptop screen showing blocks of TypeScript code, a single Post-it note
with "workflow.start()" handwritten in blue pen, cold brew in glass,
tangled USB-C cable, wood grain table, shallow focus, editorial
photography, no logos visible --ar 1:1 --style raw --v 6.1
```

### Infographic prompt — "Before/After: Agent Architecture"
**Imagen 3:**
```
A clean minimalist two-panel diagram in the visual style of an Edward
Tufte information graphic, off-white background, thin charcoal linework,
single accent color in deep burgundy. LEFT panel labeled "Brittle":
shows a linear chain of five nodes connected by arrows, one node visibly
cracked/broken with a small red X. RIGHT panel labeled "Durable": shows
the same five nodes but connected via a persistent state layer drawn as
a horizontal band beneath them, with small "retry" and "resume" markers
on two of the nodes. Typography: serif labels, sparse, generous white
space. No extraneous ornament. 4:3 aspect ratio.
```

---

## Event 2 — The Forward Deployed Engineer: A Conversation on the Hottest Title in AI Startups
**Mon Apr 20, 6:00–8:00pm · Spring Place, 6th Floor Sunken Living Room**
Acacia · FDE panel: Caitlin, Jordan, Kamesh (Sr. FDE @ Ripplins) · FDE postings +800% in 2025

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a sunken mid-century living room in a Tribeca
members club, shot from above and behind a small crowd seated on low
velvet couches, warm amber uplighting, four panelists visible in the
distance on a raised platform but blurred and silhouetted, wood-paneled
walls, the back of heads and shoulders in sharp foreground, notebooks
on laps, a single branded coaster on the coffee table, Monocle magazine
feature aesthetic, 35mm film grain, muted ochre and forest-green palette
--ar 16:9 --style raw --v 6.1
```

### In-post insert (1:1)
**Imagen 3:**
```
Editorial overhead photograph of a single Moleskine notebook open on a
dark velvet couch, handwritten bullet points visible but intentionally
blurred so the text is suggestive not readable, a pen resting across
the page, one business card tucked into the fold with no legible text,
dim warm light, shot in the style of a New York Times Magazine photo
essay, 1:1 aspect ratio, 35mm film aesthetic.
```

### Infographic prompt — "FDE Role Demand, 2025"
**DALL-E 3 or Imagen 3:**
```
A single-data-point bar chart infographic in the visual style of a
Bloomberg Businessweek feature. Title at top in serif: "Forward Deployed
Engineer Job Postings, 2024 vs 2025". Two vertical bars side by side,
the 2025 bar dramatically taller (9x) than the 2024 bar, rendered in a
solid deep-navy fill on an off-white textured background. Small
annotations in the margin note three hiring companies: OpenAI, Anthropic,
Palantir. Minimal serif typography. Single red dotted trendline climbing
off the top of the frame. 4:3 aspect ratio. No clip art, no icons, no
generic "growth" imagery.
```

---

## Event 3 — Rebuilding GTM: Revenue Agents That Drive Pipeline and Close
**Tue Apr 21, 1:00–1:45pm · Virtual (Goldcast)**
Revenue agents · SDR/AE workflow automation · pipeline generation · closing motion

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial split-frame photograph, cinematic composition. LEFT HALF: a
messy analog sales war-room — whiteboard covered in blue marker deal
names and dollar amounts, half-drunk coffee, crumpled Post-its, the
classic GTM bullpen aesthetic, natural daylight. RIGHT HALF: a single
laptop on a clean walnut desk with a soft-focus CRM dashboard on
screen, minimal, quiet, morning light. Visual metaphor: before and
after revenue automation. Muted desaturated palette, 35mm film grain
throughout, no logos, no visible text on screens --ar 16:9 --style raw
--v 6.1
```

### In-post insert (1:1)
**Imagen 3:**
```
A single close-up editorial photograph of an old-school sales pipeline
whiteboard being photographed on a smartphone, the hand and phone in
the foreground slightly out of focus, the whiteboard in the background
in focus but partially cropped. The visual suggests documentation and
translation from analog to digital. Warm overhead office light, shot
in the style of a Fortune magazine feature, muted blue and grey
palette, 1:1 aspect ratio.
```

### Infographic prompt — "The Revenue Agent Stack"
**Imagen 3:**
```
A clean isometric schematic diagram in the visual style of a Stripe
Press book illustration. Five horizontal layers stacked vertically on
a warm off-white background, each layer a different muted color:
(1) Data Layer — CRM + enrichment, (2) Signal Layer — intent + engagement,
(3) Agent Layer — SDR / AE / CS agents, (4) Orchestration Layer —
handoff logic, (5) Human Layer — seller + manager review. Each layer
labeled in a small serif typeface on the right margin. Thin connecting
lines between layers suggest data flow. No gradients, no drop shadows,
no 3D rendering — flat editorial diagram aesthetic. 4:3 aspect ratio.
```

---

## Event 4 — Tech Brief: Powering AI Apps and Agents at Scale on Azure App Platform
**Tue Apr 21, 2:00–3:30pm · Virtual (Microsoft)**
Azure AI Foundry · GitHub + VS Code integration · observability and cost efficiency

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a laptop on a home office desk at 2pm sharp,
the screen showing a webinar interface but rendered intentionally
out-of-focus so no logos or faces are legible, a physical notebook
open next to the laptop with a fresh blank page, pen uncapped,
coffee refilled, the distinct low-stakes focused energy of watching
a vendor tech brief. Warm afternoon window light, potted plant in
soft background, muted palette of slate blue and warm beige, shot
in the style of a Fast Company feature, 35mm film grain --ar 16:9
--style raw --v 6.1
```

### In-post insert (1:1)
**Imagen 3:**
```
Overhead editorial photograph of a single handwritten Moleskine page
with three short bullet points in blue ink, the text intentionally
blurred into legible shapes without being readable, a cup of coffee
in the top corner, the header of the page in slightly sharper focus
reading just the word "Azure" handwritten in black marker. Shot in
the style of a Monocle magazine photo essay. 1:1 aspect ratio. Warm
afternoon light.
```

### Infographic prompt — "Azure AI Foundry: What Sits Where"
**Imagen 3:**
```
A clean hierarchical block diagram in the visual style of a Microsoft
Research paper figure. Off-white background. Top tier: a single wide
box labeled "App / Agent Surface". Middle tier: three equal-width boxes
side by side labeled "Models", "Tools", "Orchestration". Bottom tier:
one wide box spanning the full width labeled "Foundation: Compute +
Observability + Governance". Connecting lines are thin and dark grey.
Typography is a clean sans-serif. Single accent color — Azure blue —
used only on the outline of the top tier. No logos, no clip art, no
gradients. 4:3 aspect ratio.
```

---

## Event 5 — NYC Voice AI Meetup
**Tue Apr 21, 5:30–8:30pm · Lower Manhattan (Agora-hosted)**
Real-time voice systems in production · sub-second latency · developer + founder + investor mix

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a crowded NYC meetup in a converted warehouse
space, shot from the middle of the crowd facing a speaker at a podium
in the distance, the speaker blurred and backlit by a projector screen
showing a soft-focus waveform visualization. Foreground: backs of heads
and shoulders, one person raising a hand, another on a phone taking a
photo, a condenser microphone stand in partial frame. Warm ambient
lighting, industrial ceiling pipes visible, the specific feeling of a
Tuesday night builder meetup. 35mm film grain, documentary photography
aesthetic, muted palette of deep teal and amber --ar 16:9 --style raw
--v 6.1
```

### In-post insert (1:1)
**Imagen 3:**
```
A single close-up editorial photograph of a studio-grade microphone on
a stand against an out-of-focus background of audience silhouettes.
The microphone is in sharp focus, a small red "on-air" light visible
but subtle. Shot in the style of an Audible campaign — premium,
minimal, suggestive. Muted background in deep navy, single warm
spotlight on the mic. 1:1 aspect ratio.
```

### Infographic prompt — "Voice AI Latency Budget"
**Imagen 3:**
```
A horizontal waterfall diagram in the visual style of a performance
engineering blog post. Single continuous horizontal bar across the
frame, segmented into five adjacent blocks each labeled with a
processing stage: "VAD" (30ms), "STT" (80ms), "LLM first-token"
(220ms), "TTS first-audio" (90ms), "Network" (40ms). Total labeled
"~460ms end-to-end" with a threshold line marked "Human-perceivable
gap: 500ms". Off-white background, thin charcoal linework, blocks
filled with a muted teal gradient. Typography is monospaced for the
millisecond values, serif for the labels. No ornament. 4:3 aspect
ratio.
```

---

## Event 6 — Tech Brief: Activate Your Data Innovation with Microsoft Fabric
**Wed Apr 22, 2:00–3:30pm · Virtual (Microsoft)**
OneLake · Fabric workloads · Copilot + Azure AI Foundry integration · governance + Purview

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a minimal home office setup, a single large
external monitor on a walnut desk showing an abstract data dashboard
intentionally blurred so no specific numbers or logos are legible,
a half-full glass of water, a pair of wireless headphones resting
beside the keyboard, soft mid-afternoon window light from the left,
a single plant in the background. The specific mood of taking a
vendor webinar at 2pm on a Wednesday. Muted palette of slate grey
and sage, 35mm film grain, shot in the style of a Wirecutter feature
--ar 16:9 --style raw --v 6.1
```

### In-post insert (1:1)
**Imagen 3:**
```
A single editorial overhead photograph of a notebook page with a
simple hand-drawn diagram: three stacked rectangles labeled "Lake",
"Warehouse", "BI" in pencil, connected by thin arrows. The drawing
is rough and human. A mug of coffee in the top corner of the frame.
Warm afternoon light, shot on 35mm film aesthetic, muted tones.
1:1 aspect ratio.
```

### Infographic prompt — "OneLake: One Copy, Many Engines"
**Imagen 3:**
```
A concentric-ring schematic diagram in the visual style of a Cloudflare
architecture blog post. At the center: a single circle labeled "OneLake
(single copy of data)". Radiating outward: five wedge-shaped sectors
around the center labeled with different compute engines — "Spark",
"SQL", "KQL", "Power BI", "Copilot". Each wedge is a different muted
shade (sage, dusty rose, slate, sand, cream). A thin dashed outer ring
labeled "Governance: Purview". Off-white background, thin charcoal
linework, clean sans-serif typography. No logos, no 3D effect, no
gradients. 4:3 aspect ratio.
```

---

## Event 7 — OpenClaw Show and Tell Night
**Thu Apr 23, 6:30–9:30pm · Fat Cat Fab Lab, West Village**
Freedom Lab · open-source AI assistant · sovereignty + privacy · hacker ethos

### Hero image (LinkedIn header, 16:9)
**Midjourney v6.1:**
```
Editorial photograph of a maker space basement in the West Village at
night, a long workbench covered in laptops, soldering stations, and
coffee cups, exposed pipes and zip-tied cables overhead, a handful of
people in hoodies leaning into laptop screens, lit by the mix of
fluorescent panels and laptop-screen glow. The specific aesthetic of
a hacker meetup below street level. Foreground: a Fat Cat Fab Lab
sticker on a laptop lid, slightly blurred. Muted palette of industrial
green, cool fluorescent, and warm laptop amber. 35mm film grain,
Vice Magazine documentary aesthetic --ar 16:9 --style raw --v 6.1
```

### In-post insert (1:1)
**Midjourney v6.1:**
```
Close-up editorial shot of an open laptop on a workbench, the screen
showing a terminal window with green text on black (legible as code
fragments but not readable as full sentences), a single sticker on
the laptop palm rest reading "self-hosted", scattered resistors and
a small screwdriver on the workbench wood. Shot under fluorescent
light with hard shadows, documentary aesthetic, 1:1 aspect ratio,
film grain --style raw --v 6.1
```

### Infographic prompt — "Open-Source AI Assistant: Trust Boundary"
**Imagen 3:**
```
A clean two-column diagram in the visual style of an EFF policy
infographic. Off-white background. LEFT column labeled "Cloud-hosted
assistant": shows a small icon-less figure at the bottom with arrows
going upward through a boundary labeled "Your data leaves here" into
a cloud shape at the top. RIGHT column labeled "Self-hosted assistant":
shows the same figure at the bottom with arrows going upward but
stopping inside a boundary labeled "Your data stays here" drawn around
both figure and cloud. Color palette: charcoal linework with a single
muted orange accent on the trust boundary lines. Typography is a clean
sans-serif. No ornament, no clip art, no logos. 4:3 aspect ratio.
```

---

## Synthesis note (bonus)

Three of this week's events (Vercel Workflows, Azure App Platform, Microsoft Fabric) are platform-layer announcements from big vendors. Two (FDE panel, NYC Voice AI Meetup) are NYC community builder nights. One (OpenClaw) is a counter-position to the big-vendor thesis. That's a clean pattern-synthesis setup for a two-thesis post later in the week — **"The platform vs. the workbench"** — which the `pattern-synthesis` skill can pick up once the briefs are in Notion. Flag it to me when you're ready to run that.

---

*Generated Sun Apr 19, 2026. Source: Going to Events calendar. Voice: documentarian realism, NYC-textured, editorial-not-hype.*
