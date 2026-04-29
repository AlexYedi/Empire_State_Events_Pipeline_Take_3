#!/usr/bin/env python3
"""
Field Notation — 8-slide carousel generator
The Shortlist NYC #4 documentarian field report
"""

from PIL import Image, ImageDraw, ImageFont
import random
import os

# ----- Configuration -----

OUT_DIR = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/content-drafts/carousel-shortlist-nyc-4"
FONT_DIR = "/Users/sameoldexpressions/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/f85326cc-c479-4349-956a-d3d47e404d0b/d1370235-0ed8-47e6-859d-0bec833074a3/skills/canvas-design/canvas-fonts"

W, H = 1080, 1350
MARGIN = 80

BG = (11, 11, 11)            # #0B0B0B
OFFWHITE = (245, 241, 232)   # #F5F1E8
OCHRE = (212, 162, 76)       # #D4A24C
BONE = (138, 132, 120)       # #8A8478

# Pre-load font helpers
def F(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

# Typography stack — three voices
SANS_BOLD = "InstrumentSans-Bold.ttf"
SANS_REG = "InstrumentSans-Regular.ttf"
SANS_IT = "InstrumentSans-Italic.ttf"
SERIF_IT = "InstrumentSerif-Italic.ttf"
MONO_REG = "IBMPlexMono-Regular.ttf"
MONO_BOLD = "IBMPlexMono-Bold.ttf"


# ----- Canvas helpers -----

def new_canvas():
    """Fresh canvas with paper-grain noise."""
    img = Image.new("RGB", (W, H), BG)
    # Subtle paper-grain: very low-density dark-gray noise
    pixels = img.load()
    random.seed(42)  # reproducible noise
    for _ in range(int(W * H * 0.012)):  # ~1.2% of pixels
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        # Vary intensity slightly above background
        n = random.randint(18, 28)
        pixels[x, y] = (n, n, n)
    return img


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_text(draw, text, font, max_width):
    """Break text into lines that fit max_width."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        trial = " ".join(current + [word])
        if text_width(draw, trial, font) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_wrapped(draw, x, y, text, font, color, max_width, line_height=None):
    """Draw wrapped text starting at (x, y), return final y position."""
    lines = wrap_text(draw, text, font, max_width)
    if line_height is None:
        # Default: 1.25x font size for comfortable reading
        line_height = int(font.size * 1.32)
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
    return y


def hairline(draw, x1, y, x2, color=OCHRE):
    """1px horizontal rule."""
    draw.line([(x1, y), (x2, y)], fill=color, width=2)


def page_indicator(draw, text):
    """Bottom-right page indicator."""
    f = F(MONO_REG, 16)
    w = text_width(draw, text, f)
    draw.text((W - MARGIN - w, H - MARGIN - 8), text, font=f, fill=BONE)


def top_left_label(draw, text, color=OCHRE):
    """Top-left small monospace label."""
    f = F(MONO_REG, 16)
    draw.text((MARGIN, MARGIN), text, font=f, fill=color)


def top_right_indicator(draw, text):
    """Top-right small monospace indicator."""
    f = F(MONO_REG, 16)
    w = text_width(draw, text, f)
    draw.text((W - MARGIN - w, MARGIN), text, font=f, fill=BONE)


# ----- Slide 1: COVER -----

def slide_01():
    img = new_canvas()
    draw = ImageDraw.Draw(img)

    # Top-left label
    draw.text((MARGIN, MARGIN), "FIELD REPORT — APRIL 27, 2026", font=F(MONO_REG, 17), fill=OCHRE)

    # Massive headline — two stacked lines
    head_font = F(SANS_BOLD, 122)
    line1 = "THE SHORTLIST"
    line2 = "NYC #4"

    # Vertical positioning: roughly center-upper
    head_top = 360
    line1_h = text_height(draw, line1, head_font)
    line2_h = text_height(draw, line2, head_font)

    draw.text((MARGIN, head_top), line1, font=head_font, fill=OFFWHITE)
    draw.text((MARGIN, head_top + 140), line2, font=head_font, fill=OFFWHITE)

    # Subtitle — three lines
    sub_font = F(SANS_REG, 32)
    sub_top = head_top + 320
    subtitles = ["Six founders.", "Five-minute pitches.", "One Meatpacking room."]
    for i, line in enumerate(subtitles):
        draw.text((MARGIN, sub_top + i * 46), line, font=sub_font, fill=OFFWHITE)

    # Italic accent
    italic_font = F(SERIF_IT, 30)
    draw.text((MARGIN, sub_top + 3 * 46 + 30), "A field report.", font=italic_font, fill=OCHRE)

    # Hairline rule near bottom
    hairline(draw, MARGIN, 1140, MARGIN + 380)

    # Page indicator
    page_indicator(draw, "01 / 08")

    img.save(os.path.join(OUT_DIR, "slide-01.png"), "PNG")
    return "slide-01.png"


# ----- Founder slide template (slides 2-7) -----

def founder_slide(filename, founder_label, page_label, company_lines, founder_line, blocks):
    """
    blocks: list of (label, statement) tuples.
    company_lines: list of strings (1 or 2 lines).
    """
    img = new_canvas()
    draw = ImageDraw.Draw(img)

    # Top labels — section indicator only (page indicator at bottom)
    top_left_label(draw, founder_label)

    # Company name — auto-fit between two sizes
    company_size_options = [70, 64, 58, 52]
    company_font = None
    for size in company_size_options:
        f = F(SANS_BOLD, size)
        max_line_w = max(text_width(draw, line, f) for line in company_lines)
        if max_line_w <= W - 2 * MARGIN:
            company_font = f
            company_size = size
            break
    if company_font is None:
        company_font = F(SANS_BOLD, 52)
        company_size = 52

    # Company position
    co_top = 175
    line_gap = int(company_size * 1.04)
    for i, line in enumerate(company_lines):
        draw.text((MARGIN, co_top + i * line_gap), line, font=company_font, fill=OFFWHITE)

    # Position after company
    co_bottom = co_top + len(company_lines) * line_gap

    # Founder line
    founder_font = F(SANS_REG, 24)
    draw.text((MARGIN, co_bottom + 12), founder_line, font=founder_font, fill=OFFWHITE)

    # Blocks: each has a small ochre mono label, then a body statement
    block_top = co_bottom + 100
    label_font = F(MONO_BOLD, 14)

    # Compute block layout — adapt body sizes if total height would overflow
    body_size_options = [
        # (bet_size, proof_size, watch_size)
        (28, 22, 22),
        (26, 20, 20),
        (24, 19, 19),
        (22, 18, 18),
    ]

    # Try sizes, pick one that fits
    available_h = H - block_top - MARGIN - 70  # reserve bottom for indicator
    chosen_sizes = body_size_options[0]
    for sizes in body_size_options:
        body_fonts = [F(SANS_REG, s) for s in sizes]
        # Estimate total height
        total_h = 0
        max_w = W - 2 * MARGIN
        for i, (label, stmt) in enumerate(blocks):
            total_h += 20 + 10  # label height + gap
            lines = wrap_text(draw, stmt, body_fonts[i], max_w)
            total_h += int(body_fonts[i].size * 1.32) * len(lines)
            total_h += 36  # block gap
        if total_h <= available_h:
            chosen_sizes = sizes
            break

    body_fonts = [F(SANS_REG, s) for s in chosen_sizes]

    y = block_top
    for i, (label, statement) in enumerate(blocks):
        # Label
        draw.text((MARGIN, y), label, font=label_font, fill=OCHRE)
        y += 28
        # Statement
        y = draw_wrapped(draw, MARGIN, y, statement, body_fonts[i], OFFWHITE, W - 2 * MARGIN)
        y += 28  # block gap

    # Hairline ochre rule near bottom for visual symmetry with cover/close
    hairline(draw, MARGIN, 1190, MARGIN + 380)

    # Page indicator (bottom-right only)
    page_indicator(draw, page_label)

    img.save(os.path.join(OUT_DIR, filename), "PNG")
    return filename


# ----- Slide 8: CLOSE / PATTERN -----

def slide_08():
    img = new_canvas()
    draw = ImageDraw.Draw(img)

    # Top-left label
    top_left_label(draw, "THE PATTERN")

    # Centerpiece statement — large
    head_font = F(SANS_BOLD, 56)
    head_text = "Not one founder"
    head2_text = "led with “AI.”"  # curly quotes
    head_top = 280
    draw.text((MARGIN, head_top), head_text, font=head_font, fill=OFFWHITE)
    draw.text((MARGIN, head_top + 72), head2_text, font=head_font, fill=OFFWHITE)

    # Body lead-in
    body_font = F(SANS_REG, 24)
    body_top = head_top + 200
    draw.text((MARGIN, body_top), "Every pitch was a workflow being collapsed:", font=body_font, fill=OFFWHITE)

    # Workflow list — ochre, mid-emphasis
    list_font = F(SANS_BOLD, 28)
    list_top = body_top + 64
    draw.text((MARGIN, list_top), "Claims  ·  Calibration  ·  Loyalty", font=list_font, fill=OCHRE)
    draw.text((MARGIN, list_top + 46), "Performance  ·  Onboarding  ·  SaaS itself.", font=list_font, fill=OCHRE)

    # Closing observations
    obs_font = F(SANS_REG, 24)
    obs_top = list_top + 130
    draw.text((MARGIN, obs_top), "AI is now assumed infrastructure.", font=obs_font, fill=OFFWHITE)

    # Italic question — InstrumentSerif italic for the magazine moment
    italic_font = F(SERIF_IT, 28)
    italic_top = obs_top + 56
    italic_text = "The real question is which of these six survive the"
    italic_text2 = "math at the 100,000th user."
    draw.text((MARGIN, italic_top), italic_text, font=italic_font, fill=OFFWHITE)
    draw.text((MARGIN, italic_top + 40), italic_text2, font=italic_font, fill=OFFWHITE)

    # Hairline rule near bottom
    hairline(draw, MARGIN, 1190, MARGIN + 380)

    # Bottom-left attribution
    attr_font = F(MONO_REG, 16)
    draw.text((MARGIN, H - MARGIN - 8), "— A.Y.  /  FIELD REPORT", font=attr_font, fill=OCHRE)

    # Page indicator
    page_indicator(draw, "08 / 08")

    img.save(os.path.join(OUT_DIR, "slide-08.png"), "PNG")
    return "slide-08.png"


# ----- Generate all slides -----

def main():
    results = []

    # Slide 1
    results.append(slide_01())

    # Slide 2 — General Intelligence Company
    results.append(founder_slide(
        "slide-02.png",
        "01 / 06  FOUNDERS",
        "02 / 08",
        ["GENERAL INTELLIGENCE", "COMPANY"],
        "Andrew Pignanelli  —  Founder/CEO",
        [
            ("THE BET", "One person + agent swarms = billion-dollar company."),
            ("THE PROOF SO FAR", "$10M led by USV. Demonstrating the first software company entirely run by agents in 2026."),
            ("WATCH FOR", "The model-quality plateau bet. Regulated industries that can’t accept un-auditable agents."),
        ]
    ))

    # Slide 3 — Adonis
    results.append(founder_slide(
        "slide-03.png",
        "02 / 06  FOUNDERS",
        "03 / 08",
        ["ADONIS"],
        "Akash Magoon  —  Co-founder/CEO",
        [
            ("THE BET", "AI orchestration reclaims the 17% of GDP healthcare loses to insurance friction."),
            ("THE PROOF SO FAR", "$40M Series C, March ’26. 4x revenue 2025. 130% NRR. Mt. Sinai."),
            ("WATCH FOR", "The Olive AI playbook. Insurance counterparties whose business model depends on the friction."),
        ]
    ))

    # Slide 4 — Rediem
    results.append(founder_slide(
        "slide-04.png",
        "03 / 06  FOUNDERS",
        "04 / 08",
        ["REDIEM"],
        "Sarah Ganzenmuller + Regan Plekenpol  —  Co-founders",
        [
            ("THE BET", "AI agents will shop on consumers’ behalf. Brands need community + zero-party data to stay visible."),
            ("THE PROOF SO FAR", "5 people, profitable, 10x growth. Olipop. Sun Bum. Vital Proteins."),
            ("WATCH FOR", "12–24 months ahead of the market. Capital efficiency becomes a constraint if a well-funded competitor arrives early."),
        ]
    ))

    # Slide 5 — Windmill
    results.append(founder_slide(
        "slide-05.png",
        "04 / 06  FOUNDERS",
        "05 / 08",
        ["WINDMILL"],
        "Brian Distelburger  —  Co-founder",
        [
            ("THE BET", "Continuous AI-readable work record makes performance review fair, finally."),
            ("THE PROOF SO FAR", "Yext IPO repeat founder. $12M announcing tomorrow. 120 customers."),
            ("WATCH FOR", "HR-tech graveyard. Buyers cut first in tight orgs. Surveillance backlash if framing slips."),
        ]
    ))

    # Slide 6 — Sparrow
    results.append(founder_slide(
        "slide-06.png",
        "05 / 06  FOUNDERS",
        "06 / 08",
        ["SPARROW"],
        "Daniel Kahn  —  Co-founder/CEO",
        [
            ("THE BET", "Credit unions can re-personalize banking by collapsing 6-week onboarding to 6 minutes."),
            ("THE PROOF SO FAR", "$400M+ student loans facilitated. 200+ credit unions. Profitable. CUNA + Ohio CU League."),
            ("WATCH FOR", "TAM ceiling. Big banks + Chime have more capital for Gen Z. Vertical SaaS for CUs gets acquired before scale."),
        ]
    ))

    # Slide 7 — Zo Computer
    results.append(founder_slide(
        "slide-07.png",
        "06 / 06  FOUNDERS",
        "07 / 08",
        ["ZO COMPUTER"],
        "Ben Guo  —  Co-founder/CEO",
        [
            ("THE BET", "Personal cloud replaces SaaS lock-in. Users own their context, agents, and integrations."),
            ("THE PROOF SO FAR", "Stripe + Venmo veterans. Lightspeed, South Park Commons, Craft, Rauch, Akhund."),
            ("WATCH FOR", "Consumer infrastructure is hardest to monetize. The interop dream needs cooperation from SaaS apps with no incentive to give it."),
        ]
    ))

    # Slide 8
    results.append(slide_08())

    print("\nGenerated slides:")
    for r in results:
        path = os.path.join(OUT_DIR, r)
        size_kb = os.path.getsize(path) / 1024
        print(f"  {r}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
