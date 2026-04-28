# The Shortlist NYC #4 — Documentarian Carousel Visual Prompts

**Post:** Field Report — Shortlist NYC #4 (Documentarian Carousel)
**Event date:** Monday, April 27, 2026
**Carousel length:** 8 slides (1 cover + 6 founders + 1 close)
**Format:** 1080×1350 px (4:5 portrait) per slide
**Intent:** Editorial documentary register. Field-guide feel. Reads like a Bloomberg / The Information piece, not a startup pitch deck.
**Source brief:** `research-briefs/2026-04-27_Shortlist_NYC_April_Founder_Showcase.md`
**Companion post drafts:** `content-drafts/2026-04-27_Shortlist_NYC_Post-Event_Content.md`

---

## Master design system (applies to every slide)

- **Dimensions:** 1080×1350 (4:5 portrait). LinkedIn carousel native.
- **Background:** near-black `#0B0B0B` with subtle paper-grain texture overlay (5% noise, off-black `#1A1A1A` grain).
- **Primary text:** off-white `#F5F1E8` (Bloomberg-warm, not pure white).
- **Accent text** (numbers, "WATCH FOR", attribution): warm ochre `#D4A24C`.
- **Subdued text** (labels, page indicators): muted bone `#8A8478`.
- **Typography:**
  - Headlines: editorial sans-serif (Inter Display, Söhne, or GT America), tight tracking
  - Body: same family, regular weight
  - Numbers / labels: monospaced (GT America Mono / IBM Plex Mono) for editorial-typewriter feel
- **Page indicator:** small, bottom-right corner of each slide: `01 / 08` style.
- **Margins:** 80px outer padding all sides minimum.
- **Slides 1 + 8 (cover + close):** full-bleed photographic / atmospheric backgrounds.
- **Slides 2–7 (founders):** text-forward, identical layout — variable copy creates rhythm.

## Visual rules (carry over from existing visual-prompts conventions)

- **No generic AI imagery.** No neural net glow, no humanoid robots, no blue holographic grids.
- **Documentarian realism over hype.** Editorial photography (Bloomberg, The Information, Harper's Magazine).
- **NYC is a character.** Meatpacking brick, warehouse-loft windows, late-afternoon golden hour, ambient room texture.
- **Faces oblique or cropped.** Sidesteps likeness issues + matches Bloomberg ethics.
- **Schematic for technical subjects** (Slides 1 + 8 may use atmospheric photography per below).

## Color palette (designer hand-off)

```
Background:        #0B0B0B
Primary text:      #F5F1E8
Accent (ochre):    #D4A24C
Subdued (bone):    #8A8478
Grain overlay:     #1A1A1A at 5% opacity
```

## Tooling stack

| Asset | Recommended generator |
|---|---|
| Slide 1 hero photo | **Midjourney v6.1** (best editorial control) or **Imagen 3** (handles interior light well) |
| Slide 8 atmospheric photo | Same as Slide 1 |
| Slides 2–7 (text-forward, no photo) | **Figma** or **Canva** — pure typography on solid background. No image gen needed. |
| Final assembly | Figma frame at 1080×1350, export PNG per slide, upload as carousel to LinkedIn |

---

## Slide 1 — Cover

**Layout:**
- Full-bleed photographic background (the room)
- Top-left: small monospaced label `FIELD REPORT — APRIL 27, 2026`
- Center-vertical: massive headline (`72pt+`)
- Below headline: subtitle (`28pt`)
- Bottom-left: italic accent line (`22pt`)
- Bottom-right: page indicator `01 / 08`

**Copy (on slide):**

```
FIELD REPORT — APRIL 27, 2026

THE SHORTLIST NYC #4

Six founders.
Five-minute pitches.
One Meatpacking room.

A field report.
```

**Hero image prompt (Midjourney v6.1):**

> Editorial documentary photograph, evening event inside Betaworks-style Meatpacking District loft, exposed brick warehouse walls, late afternoon golden hour through tall industrial windows, soft warm window light raking across the room, audience of 100 seated in rows facing a small low stage, photographed from the back of the room, audience cropped at shoulder-and-back showing only the backs of heads, speaker silhouette barely visible in soft focus on the stage, deep moody chiaroscuro, dark color palette with one shaft of warm amber window light, restrained editorial style, Bloomberg / The Information aesthetic, no faces visible, no logos, no signage, no text, 35mm film grain, shot on Leica Q3, natural ambient light only --ar 4:5 --style raw --v 6.1

**Fallback prompt (Imagen 3):**

> Editorial documentary photograph of an evening event in a NYC Meatpacking District loft venue, exposed brick walls, warehouse-loft windows with late afternoon golden hour light spilling in, audience seated facing a small stage, photographed from the back showing audience from shoulders down so no faces are visible, speaker on stage in soft focus silhouette, deep dark color palette with single warm amber light source, Bloomberg magazine documentary aesthetic, 35mm film grain, no text or logos. 4:5 portrait.

**Text overlay treatment:** apply 60% black gradient overlay from bottom 40% of frame upward, so the white text reads cleanly against the photographic background. Headline white drop shadow at 25% opacity for legibility.

---

## Slide 2 — General Intelligence Company (founder slide template)

> The same layout repeats for slides 2–7. Slide 2 spec'd in full as the template; slides 3–7 give variable copy only.

**Layout (slides 2–7):**
- Background: solid `#0B0B0B` with paper-grain texture (no photography)
- Top-left: section number, monospaced, ochre — `01 / 06 FOUNDERS`
- Top-right: page indicator — `02 / 08`
- Center-top: COMPANY NAME (62pt, all caps, off-white, tight tracking)
- Below company: founder name + role (24pt, off-white, regular weight)
- Spacer
- Three labeled blocks, vertically stacked, left-aligned:
  - **THE BET** (label: 14pt monospaced ochre, all caps) → statement (28pt off-white)
  - **THE PROOF SO FAR** (label: 14pt monospaced ochre, all caps) → statement (24pt off-white)
  - **WATCH FOR** (label: 14pt monospaced ochre, all caps) → statement (24pt off-white)
- Bottom-right: page indicator `02 / 08` (subdued bone color)

**Copy:**

```
01 / 06  FOUNDERS                                          02 / 08

GENERAL INTELLIGENCE
COMPANY

Andrew Pignanelli — Founder/CEO


THE BET
One person + agent swarms = billion-dollar company.

THE PROOF SO FAR
$10M led by USV. Demonstrating the first software
company entirely run by agents in 2026.

WATCH FOR
The model-quality plateau bet. Regulated industries
that can't accept un-auditable agents.
```

**Visual texture (no photo):** solid `#0B0B0B`, 5% noise overlay (paper grain). Optional: a single thin 1px ochre rule across the slide at the 50% vertical mark, separating identity (top) from analysis (bottom). Decorative; can omit if too busy.

---

## Slide 3 — Adonis

```
02 / 06  FOUNDERS                                          03 / 08

ADONIS

Akash Magoon — Co-founder/CEO


THE BET
AI orchestration reclaims the 17% of GDP healthcare
loses to insurance friction.

THE PROOF SO FAR
$40M Series C, March '26. 4x revenue 2025.
130% NRR. Mt. Sinai.

WATCH FOR
The Olive AI playbook. Insurance counterparties
whose business model depends on the friction.
```

---

## Slide 4 — Rediem

```
03 / 06  FOUNDERS                                          04 / 08

REDIEM

Sarah Ganzenmuller + Regan Plekenpol — Co-founders


THE BET
AI agents will shop on consumers' behalf.
Brands need community + zero-party data to stay visible.

THE PROOF SO FAR
5 people, profitable, 10x growth.
Olipop. Sun Bum. Vital Proteins.

WATCH FOR
12–24 months ahead of the market. Capital efficiency
becomes a constraint if a well-funded competitor
arrives early.
```

---

## Slide 5 — Windmill

```
04 / 06  FOUNDERS                                          05 / 08

WINDMILL

Brian Distelburger — Co-founder


THE BET
Continuous AI-readable work record makes
performance review fair, finally.

THE PROOF SO FAR
Yext IPO repeat founder. $12M announcing tomorrow.
120 customers.

WATCH FOR
HR-tech graveyard. Buyers cut first in tight orgs.
Surveillance backlash if framing slips.
```

---

## Slide 6 — Sparrow

```
05 / 06  FOUNDERS                                          06 / 08

SPARROW

Daniel Kahn — Co-founder/CEO


THE BET
Credit unions can re-personalize banking by
collapsing 6-week onboarding to 6 minutes.

THE PROOF SO FAR
$400M+ student loans facilitated. 200+ credit unions.
Profitable. CUNA + Ohio CU League.

WATCH FOR
TAM ceiling. Big banks + Chime have more capital
for Gen Z. Vertical SaaS for CUs gets acquired
before scale.
```

---

## Slide 7 — Zo Computer

```
06 / 06  FOUNDERS                                          07 / 08

ZO COMPUTER

Ben Guo — Co-founder/CEO


THE BET
Personal cloud replaces SaaS lock-in.
Users own their context, agents, and integrations.

THE PROOF SO FAR
Stripe + Venmo veterans. Lightspeed, South Park
Commons, Craft, Rauch, Akhund.

WATCH FOR
Consumer infrastructure is hardest to monetize.
The interop dream needs cooperation from SaaS apps
with no incentive to give it.
```

---

## Slide 8 — Close / Pattern

**Layout:**
- Atmospheric background (echoes cover but darker / more abstract)
- Top-left: small monospaced label `THE PATTERN`
- Center-vertical: large statement (52pt+)
- Below: short list of workflows being collapsed (mid-tier text)
- Bottom statement (28pt) — the takeaway
- Bottom-right: page indicator `08 / 08` + small `— A.Y. / FIELD REPORT` attribution in ochre

**Copy:**

```
THE PATTERN

Not one founder led with "AI."

Every pitch was a workflow being collapsed:

  Claims · Calibration · Loyalty
  Performance · Onboarding · SaaS itself.

AI is now assumed infrastructure.

The real question is which of these six
survive the math at the 100,000th user.

                                                — A.Y. / FIELD REPORT
                                                            08 / 08
```

**Background image prompt (Midjourney v6.1):**

> Atmospheric editorial photograph, NYC Meatpacking District at night through a rain-streaked warehouse window, soft amber sodium street lights blurred in the distance, the inside of an empty event venue after hours, brick walls in deep shadow, single shaft of warm light from somewhere off-frame, deep moody chiaroscuro, very dark image with most of the frame in near-black, restrained editorial documentary style, Bloomberg / The Information aesthetic, no people, no faces, no text, no logos, 35mm film grain --ar 4:5 --style raw --v 6.1

**Text overlay treatment:** the background should be 70% darker than the cover so the white statement text dominates. Apply additional 50% black gradient overlay if needed.

---

## Production checklist

- [ ] Generate Slide 1 hero photo via Midjourney v6.1 or Imagen 3 (use prompt above)
- [ ] Generate Slide 8 atmospheric photo via Midjourney v6.1 or Imagen 3 (use prompt above)
- [ ] Set up Figma frame at 1080×1350 with master design system applied
- [ ] Build Slides 2–7 using identical typography template, variable copy
- [ ] Compose Slides 1 + 8 with photo backgrounds + text overlay treatment
- [ ] Export 8 PNGs at 1080×1350
- [ ] Upload to LinkedIn as carousel post

## Post copy for LinkedIn (carousel caption)

```
A field report from The Shortlist NYC #4 — six founders, five-minute pitches, one Meatpacking room.

What each is building, what makes their pitch credible right now, and what could break them on the path to a durable company.

Swipe →
```

(Caption is intentionally brief — the carousel does the work.)
