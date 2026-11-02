## Visual Brief — 7-slide carousel: cover + 6 stats (Arc: stat pairs under Variant B's three questions)

**Carousel PDF title:** The Upcoming Week, Nov 2–6, 2026: 6 stats that sum up the week in AI events

**Carousel thesis:** Variant B asks three questions: can the agent ship, who governs it, and can you trust it at volume. Each slide gives one number (or one pair) that shows why the field is asking it. Each number carries its own comparison point, says who measured it, and names the event where the question comes up this week. The carousel takes no side: every slide ends on the open question, not a verdict.

**Slide count:** 7: a cover, then 6 stat slides, 2 per question (Alex, 2026-11-02). Replaces the 5-slide Arc 4 map/grid version (37ec24d).
**Aspect ratio:** 4:5 (1080x1350).
**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome PDF. No pictorial slides.
**Palette (whole carousel):** dark slate #0F172A background, white #FFFFFF text, ONE accent blue #3B82F6, used only on the headline number(s) and the question tag. Acid green #8FE83A appears ONLY as the underline on the name mark (small, bottom-left, every slide). Muted labels use white at 70% opacity.
**Shared slide template (every slide, one CSS class):** top-left question tag ("1 · CAN IT SHIP?" / "2 · WHO GOVERNS IT?" / "3 · CAN YOU TRUST IT AT VOLUME?") plus "n/7" top right · headline (≤8 words) · the big number visual · one "What it measures" line · one "This week:" line naming the event · source line at the bottom · name mark bottom-left. The number visual is the only part that changes shape.

### Slide 1 of 7 — Cover: 6 stats that sum up the week
- **Visual mode:** Bold typography plus a table of contents. House style, not the stat template.
- **Kicker:** Nov 2–6, 2026 · 10 events · 6 in NYC, 4 streaming
- **Headline:** 6 stats that sum up the upcoming week in AI events
- **Body / content:** the three questions stacked, each with an accent number tag and its slides: "1 · Can it ship?" (slides 2–3) · "2 · Who governs it?" (slides 4–5) · "3 · Can you trust it at volume?" (slides 6–7). Bottom: name mark + "Swipe →".
- **Source attribution:** none (table of contents; no figures).
- **Alt text:** Cover: six stats summing up the week of Nov 2–6, 2026 in AI events, grouped under three questions: can it ship, who governs it, can you trust it at volume.

### Slide 2 of 7 — 1 · CAN IT SHIP? The merge
- **Visual mode:** Split-frame comparison, two mirrored callouts of equal weight.
- **Headline:** One company's third vs the median's 0.5%
- **Body / content:**
  - Left callout "≈ 1 in 3": "Zalando PRs auto-approved as low-risk." Small label: one company's policy, 250+ teams, first-party, methodology not disclosed.
  - Right callout "0.5%": "Merges reviewed only by AI at the median company." Small label: Jellyfish's own dataset, 1,300+ companies.
  - What it measures: two different things, one company's routing policy and a cross-company median. Neither is a controlled study.
  - This week: AI DevCon NYC (livestream, Tue). Bartosz Ocytko (Zalando) on risk-tiered auto-approval.
- **Source attribution:** Source: Zalando Engineering, 2026-08-14; Jellyfish via R&D World, 2026-10-27.
- **Alt text:** Two equal callouts: about one in three Zalando PRs auto-approved as low-risk, beside 0.5% of merges reviewed only by AI at the median company in Jellyfish's dataset.

### Slide 3 of 7 — 1 · CAN IT SHIP? The skill
- **Visual mode:** Horizontal bar chart, 4 bars, 0–100% axis.
- **Headline:** A skill the agent never opens
- **Body / content:**
  - Bars (pass rate, Vercel's coding-agent eval): No docs (baseline) 53% · Skill available 53% · Skill + explicit instruction 79% · Docs index in AGENTS.md 100%.
  - Callout on the "Skill available" bar: "never invoked in 56% of eval cases".
  - What it measures: one vendor-run eval of framework knowledge, not a general benchmark.
  - This week: Agentics Spotlight (NYU, Wed). Jesse Vincent (Prime Radiant) on skills, harnesses and hooks.
- **Source attribution:** Source: Vercel, "AGENTS.md outperforms skills in our agent evals," 2026-01-27 (vendor-run eval).
- **Alt text:** Bar chart of Vercel's eval pass rates: 53% with no docs, 53% with a skill available but often not invoked, 79% when told to use it, 100% with a docs index in AGENTS.md.

### Slide 4 of 7 — 2 · WHO GOVERNS IT? The definitions
- **Visual mode:** Two-bar drop chart (tall bar to short bar).
- **Headline:** Clean schemas 91%. Real enterprise work 21%.
- **Body / content:**
  - Bars (best agent, share of tasks solved): Spider 1.0, clean academic databases, 91.2% · Spider 2.0, real enterprise text-to-SQL workflows, 21.3%.
  - What it measures: the same kind of task on clean vs messy data. The gap is definitions, joins and dialects: what a governed business context is meant to fix.
  - This week: Snowflake Expedition, technical day (livestream, Tue). "Build One Business Context" and "Secure and Govern Data & Agents".
- **Source attribution:** Source: Spider 2.0, ICLR 2025 (arXiv 2411.07763).
- **Alt text:** Two bars: the best agent solves 91.2% of tasks on clean academic databases (Spider 1.0) but 21.3% on real enterprise workflows (Spider 2.0).

### Slide 5 of 7 — 2 · WHO GOVERNS IT? The CRM write
- **Visual mode:** Six-tile grid, one tile per demo company; 5 tiles in accent outline with an "MCP" tag, 1 plain.
- **Headline:** Five of six demos open a door
- **Body / content:**
  - Tiles: ZoomInfo · Airspeed · Goldcast · Firmable · Syft AI (tagged "MCP connector advertised") · TitanX (no tag).
  - What it measures: what each company's own site advertises, not verified usage. Only ZoomInfo's launch is press-verified this quarter.
  - Open question line: "When an agent can write to the CRM, who approves the write?"
  - This week: Revolt! Demo Days (RevGenius, livestream, Wed–Thu).
- **Source attribution:** Source: company websites, checked Nov 2026; ZoomInfo GTM AI launch page.
- **Alt text:** Six company tiles from Revolt Demo Days; five are marked as advertising an MCP connector, TitanX is not.

### Slide 6 of 7 — 3 · CAN YOU TRUST IT AT VOLUME? The review queue
- **Visual mode:** Two paired up-arrows of equal weight.
- **Headline:** Twice the merges, nearly twice the review
- **Body / content:**
  - Callout 1 "+98%": "PRs merged" · Callout 2 "+91%": "PR review time". Label: developers on high-AI-adoption teams.
  - What it measures: Faros AI's own telemetry, 10,000+ developers across 1,255 teams, as of mid-2025. Correlation, not a controlled study.
  - This week: Ghosts in the System (Ro HQ, Thu). Three companies' published approaches to checking AI output at volume: expert audit, always-on QA, curated answer sets.
- **Source attribution:** Source: Faros AI, "The AI Productivity Paradox," 2025-07-23 (vendor telemetry).
- **Alt text:** Two equal arrows: 98% more pull requests merged and 91% longer PR review time on high-AI-adoption teams, per Faros AI telemetry.

### Slide 7 of 7 — 3 · CAN YOU TRUST IT AT VOLUME? The turn
- **Visual mode:** Trade-off scale (a balance: left pan "−100–200 ms latency", right pan "+50–70% LLM calls").
- **Headline:** Faster replies, more model calls
- **Body / content:**
  - Left: "100–200 ms" trimmed from end-to-end latency · Right: "50–70%" more LLM calls. Label: Deepgram Flux "eager end-of-turn", which starts the LLM before the caller is surely done.
  - What it measures: the vendor's own documented trade-off, not a field measurement.
  - This week: NYC Voice Agent Hackathon (Fri). Judged partly on response time and turn-taking, tested on a real phone line.
  - Closing line (smaller, under the source): "Six numbers, ten events, Nov 2–6. Not in NYC? Send me the question you'd ask."
- **Source attribution:** Source: Deepgram developer docs, Flux voice-agent eager end-of-turn (vendor), 2026.
- **Alt text:** A balance showing Deepgram's documented trade-off: eager end-of-turn trims 100–200 ms of latency at the cost of 50–70% more LLM calls.

**Quality gate checks:**
- Arc fit: a cover, then the three-question structure of Variant B, 2 stat slides per question (Alex's spec). The cover summarizes the week and maps the questions to slides.
- Job differentiation: six different numbers, each tied to a different event (DevCon, Agentics, Expedition, Revolt, Ghosts, Voice). No slide repeats the post copy's figures except the Zalando/Jellyfish pair, which slide 1 adds the method and sample size to.
- Null-baseline rule: every number has a comparison point (Zalando vs Jellyfish; 53% baseline; Spider 1.0 vs 2.0; 5 of 6; merges vs review time; latency vs calls).
- Takes no side: each slide states what the number measures and its limits, then the event. No verdicts.
- Thumb test: headlines are 5–8 words; one big number visual per slide.
- Source citations: all 6 slides. Sources checked 2026-11-02: Vercel, Faros and Deepgram against their own pages; Zalando/Jellyfish, Spider 2.0 and the Revolt MCP count carried from the source-checked briefs and carousels.
- Final slide (7) earns the swipe: the sixth number plus a one-line invitation, not "follow for more".
- Public-file check: no private material.
