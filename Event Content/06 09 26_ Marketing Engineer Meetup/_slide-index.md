# Slide Index — Marketing Engineer Meetup (2026-06-09)

Enriched metadata for the 11 slide photos captured at the event. Each slide is
associated to a speaker/talk via three independent signals: **photo capture
timestamp** (embedded in the `PXL_<date>_<HHMMSS>` filename, UTC → ET below),
**on-screen content** (incl. visible browser tabs), and **the transcript passage**
it corresponds to. Talk order derived from the slide timeline matches the
transcript order exactly (Nick → Cindy → Jack → Rani → Joe), which corroborates
the associations.

Confidence is **High** for all 11. The 19:11 slide was captured blurry and was
recovered with a PIL enhancement pass (contrast + unsharp + autocontrast); the
legible version is saved as `PXL_20260609_231142779_ENHANCED.jpg`.

> ⚠️ No slides were photographed for **Sam Seely (Knock)** opening ("AI adoption
> ladder"), **Mike Carbone (Knock)** live demo, or the closing **panel**. Those
> talks are covered by the transcript only.

| # | File | Time (ET) | Speaker / Company | Slide | What it shows (adds beyond transcript) | Conf. |
|---|------|-----------|-------------------|-------|----------------------------------------|-------|
| 1 | `PXL_20260609_225848688.jpg` | 18:58 | **Nick Lafferty / Profound** | "What Does A Marketing Engineer Do?" | Venn diagram: *The Marketing Engineer* at the center of Growth & Demand Gen, SEO & AEO, Content & Social, Brand & PR, Product Marketing — with **Marketing Operations as the foundation bar**. Deck page 11. | High |
| 2 | `PXL_20260609_230632903.jpg` | 19:06 | **Nick Lafferty / Profound** | "Profound Ads — AI Agent System" | Live dashboard. Header: *"7 specialized agents replacing $150k/month agency — estimated Claude API cost: ~$3–7/month."* Tiles: 8 total agents / 7 have run / 27 findings / 1 automated. Agent cards: Campaign Performance Monitor, Search Term Intelligence, Keyword Health, Ad Copy Performance, GeoDeviceSchedule, Competitive Intelligence, Monthly Executive Summary, **Pipeline Report (Google Ads spend + HubSpot CRM: "7 closed deals, $412,300 revenue")**. | High |
| 3 | `PXL_20260609_231142779.jpg` (→ `_ENHANCED.jpg`) | 19:11 | **Cindy Zhang / Ramp** | "The operating model for Growth" | Loop diagram: **Channel teams** (experts in their channel) ⇄ **Core Growth AI** (build shared infra + agents), with **AI-first Growth (where everyone can build)** in the center. Arrows: *needs + feedback* (channel→core), *infra + agents* (core→channel). Caption: *"Neither team gets there alone. The loop between them is the engine."* | High (recovered) |
| 4 | `PXL_20260609_231640102.jpg` | 19:16 | **Cindy Zhang / Ramp** | "Every stage turns more of the team into Marketing Engineers" | 3-phase × 2-team grid. Phases: **Personal** (automate your own work) → **Workflow** (agents run the workflow) → **System** (systems that learn). Rows: *Channel teams* and *Core Growth AI*. Notable cell: "Ship tools anyone can use **(Glass)**" and "Build the intelligence layer that compounds." | High |
| 5 | `PXL_20260609_232212473.jpg` | 19:22 | **Jack Perales / WorkOS** | "Blog Bot — Pipeline Workflow" | Header: *"25-step sequential pipeline · input classification → draft delivery."* INTAKE: Step 1 `classify` (Haiku 4.5, forced tool_use, ~30 labels), Step 3 `resolve-authors` (Haiku + fuzzy match), Step 4 `resolve-sticky-defaults`, Step 5 `resolve-format-reference`. RESEARCH begins. | High |
| 6 | `PXL_20260609_232303361.jpg` | 19:23 | **Jack Perales / WorkOS** | Blog Bot — RESEARCH | Step 2 `fetch-github-context` (GitHub REST API, regex), Step 6 `fetch-thread-history-for-draft` (Slack API, file parsing .txt/.md/.pdf/.docx), Step 7 `fetch-url-sources` (**7 connectors, Promise.all, hallucination guard** — refuses rather than hallucinate if all fetches fail), Step 8 `augment-source-for-length` (Haiku, Granola search, proportional cap). | High |
| 7 | `PXL_20260609_232353641.jpg` | 19:23 | **Jack Perales / WorkOS** | Blog Bot — FACTS / GENERATION | Step 9 `extract-source-facts` (Opus, 60k cap, JSON array of citable strings), Step 10 `extract-user-context-facts` (Opus, author-trust, 20k cap), Step 11 `build-fact-pool` (pure code, trust_level tagging author/public), Step 12 `generate-draft` (**Opus 4.7, 8192 tokens, 4 retries, 76 voice patterns**). | High |
| 8 | `PXL_20260609_232525598.jpg` | 19:25 | **Jack Perales / WorkOS** | Blog Bot — VALIDATION | Step 15 `detectDraftRefusal`, Step 16 `resolve-slug` (Webflow CMS API, slug-collision alternatives), Step 17 `review-accuracy` (Opus 4.7, marker-preserving), Step 18 **`de-claude`** (Opus 4.7, **13 AI-tell categories**: hedges, performative transitions, grandiose claims, rule-of-three, etc.), Step 19 `enforce-sentence-case` (Haiku), Step 20 `check-source-fidelity` (Opus, legacy, non-blocking). | High |
| 9 | `PXL_20260609_232608832.jpg` | 19:26 | **Jack Perales / WorkOS** | Blog Bot — DELIVERY | Step 21 `generate-images` (**Gemini 2.5 Flash**, deterministic palette), Step 22 `sensitivity-check` (Opus 4.7, 8 categories, fails open), Step 23 `save-to-d1` (phase: reviewing), Step 24 `link-check` (concurrency 8, best-effort), Step 25 `post-draft-card` (**HMAC-signed URL, 60-day TTL, Slack Block Kit** with Stage/OG/Publish/Regenerate buttons). | High |
| 10 | `PXL_20260609_234002561.jpg` | 19:40 | **Rani Kubersky / Cursor** | "The cookbook" | Recurring-pain → primitive mapping: "I always have to remind it how to create a landing page → **Build a skill**"; "summarize themes from financial-services opportunities → **Create an automation**"; "bother our data scientist to pull performance metrics → **Connect the Databricks MCP**." (Browser: *How Cursor Builds Cursor* Google Slides.) | High |
| 11 | `PXL_20260609_234837442.jpg` | 19:48 | **Joe Reitz / Vercel** | "One request in. The agent plans, gates, loops, acts." | `operator` architecture, slide 05/07. **01 Slack Event** (@mention/DM → /api/slack) → **02 Planner** (classify intent, 19 categories → narrow ~100 tools) → **03 Permissions** (wrap Salesforce writes with approval → @mops gate) → **04 Agent Loop** (generateText, Claude via **AI Gateway**, stepCountIs(N)) → **05 Integrations** (jsforce · Linear SDK · REST · MCP → real systems). Footer: **Upstash Redis** · approvals · pending confirmations · analytics · token + query caching. | High |

## Cross-cutting observations (useful for content)

- **Anthropic models are everywhere on stage**: Knock demo on Claude; WorkOS BlogBot runs Opus 4.7 (drafting) + Haiku (cheap steps); Vercel operator routes Claude via AI Gateway; Nick rebuilt his site with "the new Anthropic model." This is a strong documentarian through-line.
- **MCP is the connective tissue**: Knock MCP, Ramp's design system "Kirby" as MCP, Cursor "Connect the Databricks MCP," Vercel operator MCP integrations.
- **The "de-claude" / 76-voice-patterns step (WorkOS)** is the most striking single artifact — a production pipeline whose explicit job includes stripping AI tells. Great material.
- **Hard numbers captured on slides** (vs. only spoken): $150k/mo agency → ~$3–7/mo (Profound); $412,300 / 7 closed deals (Profound pipeline report); 25 pipeline steps, 76 voice patterns, 13 AI-tell categories (WorkOS); 19 intent categories / ~100 tools (Vercel).

*Generated 2026-06-10 from the uploaded transcript + 11 slide photos. Capture
times are local ET (filename UTC − 4h).*
