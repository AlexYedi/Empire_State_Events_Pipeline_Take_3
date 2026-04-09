# STACK_README.md
**Owner:** Alex — Lead Enterprise Account Director / AI Builder  
**Last Updated:** 2026-04-09  
**Version:** 1.1  
**Purpose:** Single source of truth for all tools, integrations, MCP connections, automation workflows, and architectural decisions. Upload this file into every Claude Project so all role modules have full stack awareness.

---

## Table of Contents

1. [Stack Overview Map](#1-stack-overview-map)
2. [Tool Inventory by Category](#2-tool-inventory-by-category)
3. [MCP Connections Index](#3-mcp-connections-index)
4. [n8n Workflow Registry](#4-n8n-workflow-registry)
5. [Data & Infrastructure Architecture](#5-data--infrastructure-architecture)
6. [Claude Projects Structure](#6-claude-projects-structure)
7. [Tool Selection Rules](#7-tool-selection-rules)
8. [Integration Harness Patterns](#8-integration-harness-patterns)
9. [Decision Log](#9-decision-log)
10. [Known Gaps & Planned Additions](#10-known-gaps--planned-additions)

---

## 1. Stack Overview Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUTS & CAPTURE                         │
│  Wispr Flow (voice) · Granola (meetings) · Perplexity (research)│
│  NotebookLM (doc analysis + audio) · Google Workspace           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      AI BRAIN LAYER                             │
│  Claude (primary) · Gemini / Google AI Studio (secondary)       │
│  ElevenLabs (voice/audio)                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   ORCHESTRATION & AUTOMATION                    │
│              n8n (central automation hub)                       │
│         triggers → workflows → tool calls → outputs             │
└──────┬──────────────────────┬────────────────────────┬──────────┘
       │                      │                        │
┌──────▼──────┐    ┌──────────▼────────┐    ┌─────────▼──────────┐
│   BUILD     │    │    MANAGE         │    │    DISTRIBUTE       │
│             │    │                   │    │                     │
│ Cursor      |    | Linear (issues)   |    | Buffer (social)     │
| Warp        │    | Vercel (deploy)   │    | Railway (backend)   |
│ Replit      │    │ ChatPRD (docs)    │    │ GitHub (source)     │
│ Bolt        │    │ Miro (strategy)   │    │ Supabase (DB/auth)  │
│ Lovable     │    │ Notion (wiki/KB)  │    │                     │
│ Framer      │    │ PostHog (metrics) │    │                     │
│ Devin       │    │ Granola (notes)   │    │                     │
│ Factory     |    | HubSpot (CRM)     |    |                     |
| Codex       │    │                   │    │                     │
└─────────────┘    └───────────────────┘    └──────────────────── ┘
       │                     |                        |
┌──────▼──────────────────────────────────────────────────────────┐
│                  DESIGN, CONTENT & MEDIA                        │
│  Canva · Gamma · Magic Patterns · Mobbin · Miro                 │
│  Gemini/Imagen 3 (image gen) · Google Vids (video)              │
│  NotebookLM Audio Overviews · ElevenLabs (narration)            │
└─────────────────────────────────────────────────────────────────┘
```

**The rule:** n8n is the automation hub. Supabase is the data layer. Claude is the reasoning layer. Everything else is a specialized tool that feeds into or out of those three.

---

## 2. Tool Inventory by Category

### 🤖 AI & Reasoning

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Claude** | Primary AI brain | All reasoning, writing, code review, strategy, coaching | Claude.ai Projects + API via artifacts |
| **Gemini** | Secondary AI + visual/media generation | Long-context document processing, Google Workspace integration, multimodal tasks, **image generation (Imagen 3)**, **video generation (Veo 2)** | Use when >200k token context needed, deep Google integration required, or when generating images/video. Imagen 3 is best-in-class for photorealistic and designed image outputs. |
| **Perplexity** | Research & search | Real-time web research, competitive intel, market sizing, fact-checking | Preferred over web search for sourced, cited answers |
| **NotebookLM** | Document intelligence + audio content | Deep Q&A on uploaded PDFs/docs, research synthesis, **Audio Overviews (podcast-style discussions from source material)** | Best for processing large document sets. Audio Overviews turn research briefs into listenable content — a differentiated distribution format. Future content pipeline integration. |
| **ElevenLabs** | Voice & audio | TTS for demos, voiceovers, audio content generation | MCP connected |
| **Google AI Studio** | AI development environment & secondary reasoning | Gemini API access and prototyping, long-context document processing (1M+ token window), multimodal tasks (image/audio/video + text), model comparison and experimentation, Google Workspace deep integration | Use when context exceeds Claude's window, or when task requires native Google ecosystem integration. Gemini 2.0 Flash for speed; Gemini 2.0 Pro for reasoning depth. Not a replacement for Claude — a complement for specific constraints. |
| **Google Vids** | AI video creation | Presentation-style videos from text/slides, short-form video summaries, event recaps | Part of Google Workspace. Relevant for post-event video content, pre-event teasers, and visual briefs. Lower effort than manual video editing. |

### 🏗️ Build & Development

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|

| **Cursor** | Primary IDE | All serious development work; AI-assisted coding with full codebase context | Use for production code. Set up `.cursorrules` per project | 
| **Replit** | Sandboxed prototyping | Quick experiments, testing concepts, sharing runnable demos | Not for production |
| **Bolt** | Full-stack scaffolding | Rapid full-stack app generation from prompts | Good for v0 scaffolds; migrate to Cursor for serious work |
| **Lovable** | Frontend scaffolding | React app generation; UI-first projects | Similar to Bolt; stronger on UI polish |
| **Devin** | Autonomous coding agent | Long-horizon coding tasks, background execution, multi-file changes | Use for well-defined tasks with clear acceptance criteria |
| **Factory** | Code automation | PR automation, code review workflows, CI/CD tasks | Integrate with GitHub |
| **Warp** | AI terminal | Terminal with AI assistance; command history and context | Replace standard terminal |
| Use only when: interactive AI-assisted terminal debugging is required in real time. For all scripting, file ops, and CLI automation — use Cursor terminal, Claude bash_tool, or the relevant MCP connection first. |

### 🗄️ Infrastructure & Data

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Supabase** | Primary database + backend | Postgres DB, auth, storage, edge functions, vector (pgvector) | MCP connected. Central data layer for all apps |
| **Vercel** | Frontend deployment | All Next.js / React app deployments | MCP connected. Auto-deploy from GitHub |
| **Railway** | Backend deployment | Node/Python backend services, background workers, cron jobs | Use when Vercel serverless limits are hit |
| **GitHub** | Source control | All code versioning, CI/CD pipelines, collaborative development | Source of truth for all code |
| **n8n** | Workflow automation | All automation, agent pipelines, tool integrations, scheduled jobs | MCP connected. Self-hosted on n8n.cloud |
| **Google Antigravity** | Compute resource scheduling & infrastructure optimization | Intelligent workload scheduling across compute resources, resource allocation optimization for AI/ML workloads, cost management for compute-intensive tasks, integration with Google Cloud infrastructure | Use when running compute-heavy AI workloads that need intelligent resource scheduling. Relevant at the infrastructure layer — not a user-facing tool. Complements Railway and Vercel for workloads that require Google Cloud's compute fabric. |

### 💼 CRM & Pipeline Management

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **HubSpot** | Primary CRM | Pipeline management, contact/deal tracking, sales workflow automation, reporting | MCP connected. Central system of record for all sales and relationship data |

### 📚 Knowledge Base & Content Management

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Notion** | Knowledge base, wiki, databases, content management | Project documentation, wiki pages, structured databases, content planning, team knowledge sharing | MCP connected. Use for anything beyond simple README-level docs |

### 📣 Social Media & Distribution

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Buffer** | Social media management | Content scheduling, cross-platform distribution, post analytics | Default for all social media publishing and scheduling |

### 📊 Analytics & Monitoring

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **PostHog** | Product analytics | Event tracking, funnels, retention, session recording, feature flags | MCP connected. Instrument every shipped feature |
| **Google Sheets** | Data analysis & reporting | Metrics dashboards, financial models, data manipulation | Part of Google Workspace suite |

### 🎨 Design & Content

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Canva** | Visual design | Marketing assets, social graphics, presentations, brand materials | MCP connected |
| **Magic Patterns** | UI component design | React component generation, design system exploration | MCP connected. Use before building custom UI |
| **Gamma** | Decks & documents | Investor decks, research briefs, proposals, sales materials | MCP connected. Default for presentation-ready output |
| **Framer** | Interactive prototypes | Marketing sites, interactive demos, no-code web publishing | Use for sites that need animation and polish |
| **Miro** | Visual collaboration | Strategy workshops, journey mapping, architecture diagrams, ICP canvases | Good for async visual thinking |
| **Mobbin** | UI research | iOS/Android/web UI pattern research, design inspiration | Reference before designing flows |

### 📋 Product & Project Management

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **PROJECT_BRIEF** | Project handoff protocol | Structured context doc that every agent reads at session start and updates at session end. Lives in GitHub repo root per project.| Template: PROJECT_BRIEF_template.md. Prevents context loss across agent rotations.
| **Linear** | Issue tracking | Sprint planning, bug tracking, feature backlog, roadmap | MCP connected. Primary project management tool |
| **ChatPRD** | Product documentation | PRD generation, feature specs, product briefs | MCP connected |
| **Granola** | Meeting intelligence | Automatic meeting notes, action item extraction, summary generation | MCP connected. Run on all important calls |
| **Miro** | Strategic planning | OKRs, roadmap visualization, discovery workshops | (also listed under Design) |

### 📥 Input & Capture

| Tool | Role in Stack | Primary Use Cases | Notes |
|------|--------------|-------------------|-------|
| **Wispr Flow** | Voice-to-text | Dictation across all apps; faster than typing for longer inputs | Use for prompts, notes, messages |
| **Google Workspace** | Documents & collaboration | Docs (long-form writing), Sheets (data), Slides (presentations), Gmail, Calendar | Full suite; deep integration with Gemini |
| **NotebookLM** | Document Q&A | (also listed under AI) | |

---

## 3. MCP Connections Index

*MCP (Model Context Protocol) connections allow Claude to directly interact with these services mid-conversation.*

| Service | MCP URL | Status | What Claude Can Do | Auth Notes |
|---------|---------|--------|--------------------|------------|
| **Linear** | `https://mcp.linear.app/mcp` | ✅ Active | Create/update issues, manage sprints, query roadmap | OAuth |
| **Supabase** | `https://mcp.supabase.com/mcp` | ✅ Active | Query DB, run migrations, manage tables, deploy edge functions | API key |
| **Vercel** | `https://mcp.vercel.com` | ✅ Active | Deploy, check build logs, manage projects, get runtime logs | OAuth |
| **n8n** | `https://yedimaing.app.n8n.cloud/mcp-server/http` | ✅ Active | Trigger workflows, search workflows, get workflow details | API key |
| **PostHog** | `https://mcp.posthog.com/mcp` | ✅ Active | Query analytics, create dashboards, manage feature flags | API key |
| **Google Calendar** | `https://gcal.mcp.claude.com/mcp` | ✅ Active | Create/update/delete events, find free time, respond to invites | OAuth |
| **Gmail** | `https://gmail.mcp.claude.com/mcp` | ✅ Active | Search messages, read threads, create drafts | OAuth |
| **Canva** | `https://mcp.canva.com/mcp` | ✅ Active | Generate designs, create assets | OAuth |
| **Magic Patterns** | `https://mcp.magicpatterns.com/mcp` | ✅ Active | Create/iterate UI components, publish artifacts | API key |
| **Gamma** | `https://mcp.gamma.app/mcp` | ✅ Active | Create and update decks/docs | OAuth |
| **Granola** | `https://mcp.granola.ai/mcp` | ✅ Active | Retrieve meeting notes, search transcripts | OAuth |
| **ChatPRD** | `https://app.chatprd.ai/mcp` | ✅ Active | Create/update product documents | API key |
| **Clay** | `https://api.clay.com/v3/mcp` | ✅ Active | Enrich contacts/companies, search accounts, run subroutines | API key |
| **ClickUp** | `https://mcp.clickup.com/mcp` | ✅ Active | Task management (secondary to Linear) | OAuth |
| **Monday.com** | `https://mcp.monday.com/mcp` | ✅ Active | Board management, item tracking | OAuth |
| **Hugging Face** | `https://huggingface.co/mcp` | ✅ Active | Model search, space interaction, paper research | OAuth |
| **Microsoft Learn** | `https://learn.microsoft.com/api/mcp` | ✅ Active | Azure/Microsoft documentation search | Public |
| **Dice** | `https://mcp.dice.com/mcp` | ✅ Active | Job search | Public |
| **Google BigQuery** | `https://bigquery.googleapis.com/mcp` | ✅ Active | Data warehouse queries | OAuth |
| **Similarweb** | `https://mcp.similarweb.com` | ✅ Active | Website traffic & competitive intelligence | API key |
| **ElevenLabs** | Via Claude.ai | ✅ Active | Voice generation, music, sound effects | OAuth |
| **HubSpot** | Via Claude.ai | ✅ Active | CRM — manage contacts, deals, pipeline, properties, search records | OAuth |
| **Notion** | Via Claude.ai | ✅ Active | Knowledge base — search/create/update pages, databases, comments | OAuth |

### MCP Usage Rules
- **Always prefer MCP over manual** when a connected service is involved — don't ask Alex to do things Claude can do directly
- **Never store credentials in prompts** — auth is handled at the connector level
- **Flag MCP failures immediately** — don't silently fall back to a manual workaround without telling Alex
- **Rate limits**: n8n and Clay have the tightest rate limits; batch calls where possible

---

## 4. n8n Workflow Registry

*n8n is the central automation hub. All recurring tasks, agent pipelines, and cross-tool integrations should be built here first.*

**Instance:** `yedimaing.app.n8n.cloud`

### Active Workflows
*(Update this section as workflows are built)*

| Workflow Name | Trigger | What It Does | Tools Used | Status |
|---------------|---------|--------------|------------|--------|
| Engineering_meetingToLinear_onGranolaComplete | Granola meeting webhookExtracts action items via Claude → creates Linear issuesGranola, Claude API, Linear, Gmail🔵 In Design — brief ready| 
| | 
| |
| |

### Workflow Naming Convention
```
[DOMAIN]_[ACTION]_[FREQUENCY/TRIGGER]
Examples:
  GTM_ICP_enrichment_onNewLead
  Research_competitorMonitoring_weekly
  JobSearch_applicationTracker_onNewRole
  Engineering_deployNotification_onVercelDeploy
```

---

## 5. Data & Infrastructure Architecture

### Primary Data Layer: Supabase

```
supabase_project/
├── auth/                    — User authentication (if applicable)
├── storage/                 — File storage (docs, assets, uploads)
├── database/
│   ├── public schema        — Application tables
│   └── extensions/
│       └── pgvector         — Vector embeddings for RAG
└── edge_functions/          — Serverless functions (TypeScript)
```

**Supabase conventions:**
- All tables use `snake_case`
- Every table has `id uuid`, `created_at timestamptz`, `updated_at timestamptz`
- Row Level Security (RLS) enabled by default on all tables
- Use edge functions for lightweight API endpoints before spinning up Railway

### Deployment Architecture

```
GitHub (source) 
    → Vercel (auto-deploy: Next.js frontends)
    → Railway (backend services, workers, cron)
    → Supabase (DB migrations via Supabase CLI)
```

### Environment Variables Convention
```
# Never commit .env files. Store in:
# - Vercel: environment variables UI
# - Railway: environment variables UI  
# - Local: .env.local (gitignored)

NEXT_PUBLIC_*     = client-safe variables
*_SECRET_*        = server-only, never exposed to client
SUPABASE_URL      = project URL
SUPABASE_ANON_KEY = public key (safe to expose)
SUPABASE_SERVICE_ROLE_KEY = server-only, never expose
```

---

## 6. Claude Projects Structure

*Each Project has a dedicated system prompt = Alex Core + Role Module. Project files = living documentation.*

### Project Map

| Project Name | System Prompt | Key Uploaded Files |
|--------------|--------------|-------------------|
| `⚙️ Build — AI Engineering & Product Dev` | Alex Core + CTO Module | `STACK_README.md`, active `schema.sql`, `architecture_decisions.md` | PROJECT_BRIEF_template.md | n8n_meeting_to_linear_brief.md
| `📣 GTM — Marketing, ICP & Growth Strategy` | Alex Core + CMO Module | `STACK_README.md`, `ICP_profiles.md`, `channel_playbook.md`, `competitor_map.md` | gtm-cmo-growth_prompt.md
| `🧠 Product — Roadmap, PRDs & Feature Strategy` | Alex Core + Head of Product Module | `STACK_README.md`, `roadmap.md`, `PRD_library/`, `PostHog_event_taxonomy.md` |
| `💼 Sales — Deal Strategy & Enterprise Execution` | Alex Core + Enterprise Sales Module | `STACK_README.md`, `MEDDPICC_templates.md`, `active_accounts.md` |
| `🔬 Research — Market Intel & Competitive Analysis` | Alex Core + Research Analyst Module | `STACK_README.md`, `market_map.md`, `research_archive/` |
| `🧑‍🏫 Learn — AI Engineering & Skill Building` | Alex Core + Learning Coach Module | `STACK_README.md`, `learning_roadmap.md`, `project_log.md` |
| `💼 Career — Job Search & Positioning` | Alex Core + Career Module | `STACK_README.md`, `resume_master.md`, `target_companies.md`, `outreach_templates.md` | career-job-search_prompt.md

### File Update Protocol
- Update `STACK_README.md` whenever a tool is added, removed, or significantly changed
- Re-upload to affected Projects after major updates
- Tag updates with date: `<!-- Updated: 2026-04-09 -->`

---

## 7. Tool Selection Rules

*When multiple tools could do a job, use these rules to pick one consistently.*

### Build decisions

| Scenario | Use This | Not That |
|----------|----------|----------|
| New app from scratch, fast | Bolt or Lovable → migrate to Cursor | Starting in Cursor cold |
| Production code, serious work | Cursor | Replit, Bolt |
| Quick throwaway experiment | Replit | Cursor (overkill) |
| Autonomous task, well-defined, single | Codex| Codex (overkill for one task)|
| Autonomous tasks, 2+ independent, parallel | Codex | Devin (sequential costs per task)|
| R automation / CI/CD workflow | Factory | Codex or Devin |
| Long-horizon ambiguous task needing judgment | Devin | Codex (less suited to ambiguity) |
| Backend API service | Railway + Supabase edge functions | Vercel serverless (for long-running) |
| Frontend deployment | Vercel | Railway (not optimized for frontend) |
|Interactive real-time terminal debugging with AI | Warp | Cursor terminal (no AI mid-session)|
|All other terminal/scripting tasks | Cursor terminal or Claude bash_tool | Warp (costs tokens unnecessarily)|


### Content & design decisions

| Scenario | Use This | Not That |
|----------|----------|----------|
| Investor deck / proposal | Gamma | Canva (not structured enough), Google Slides |
| Social graphics / marketing assets | Canva | Gamma |
| Social media scheduling / distribution | Buffer | Manual posting across platforms |
| Interactive marketing site | Framer | Webflow (not in stack) |
| UI component generation | Magic Patterns | Building from scratch |
| UI research / pattern reference | Mobbin | Googling screenshots |
| Strategy visualization | Miro | Miro is the default for anything spatial |
| Project wiki / documentation | Notion | GitHub markdown (for anything beyond READMEs) |

### Visual & media content decisions

| Scenario | Use This | Not That |
|----------|----------|----------|
| Custom image / conceptual visual for social post | Gemini (Imagen 3) | Stock photos, generic templates |
| Social-optimized infographic / designed visual | Canva | Gemini (Canva has social templates + export) |
| Multi-slide carousel for LinkedIn | Gamma or Canva | Google Slides (less design polish) |
| Presentation-style video from text/slides | Google Vids | Manual video editing |
| Podcast-style audio from research brief | NotebookLM Audio Overviews | ElevenLabs (NotebookLM is zero-effort from existing briefs) |
| High-quality narration / voiceover from script | ElevenLabs | NotebookLM (less control over voice/delivery) |
| Data visualization / concept diagram | Canva or Gamma | NapkinAI (removed from stack) |
| Post-event recap video with screen grabs | Google Vids | Manual assembly |

### Research decisions

| Scenario | Use This | Not That |
|----------|----------|----------|
| Real-time market research | Perplexity | Claude alone (no live web access by default) |
| Deep doc analysis | NotebookLM | Uploading raw PDFs to Claude |
| Competitive traffic data | Similarweb MCP | Manual web lookups |
| Contact/company enrichment | Clay MCP | Manual LinkedIn research |
| CRM lookups / pipeline data | HubSpot MCP | Spreadsheets or manual tracking |

### AI model decisions

| Scenario | Use This | Not That |
|----------|----------|----------|
| Reasoning, writing, strategy, code | Claude (Sonnet or Opus) | Defaulting to Gemini |
| 200k+ token doc processing | Gemini (Google AI Studio) | Claude (context limit) |
| Voice output | ElevenLabs | Built-in TTS |
| Research with citations | Perplexity | Claude without web search |

---

## 8. Integration Harness Patterns

*Reusable connection patterns for common cross-tool workflows.*

### Pattern 1: Research → Structured Output → Storage
```
Perplexity (research) 
  → Claude (synthesize + structure) 
  → Supabase (store) 
  → Gamma (format for output)
```
*Use for: competitive analysis, market research, ICP research*

### Pattern 2: Meeting → Action Items → Task Management
```
Granola (meeting notes) 
  → n8n webhook trigger 
  → Claude (extract action items) 
  → Linear (create issues) 
  → Gmail (send summary)
```
*Use for: all important meetings and calls*

### Pattern 3: Idea → Spec → Build
```
Claude GTM/Product Project (define + spec) 
  → ChatPRD (formalize PRD) 
  → Linear (create issues) 
  → Cursor/Bolt (build) 
  → Vercel/Railway (deploy) 
  → PostHog (instrument)
```
*Use for: all product feature development*

### Pattern 4: Lead → Enrich → Qualify → Outreach
```
Source (LinkedIn / Dice / inbound) 
  → Clay (enrich: firmographic, contact) 
  → HubSpot (store + manage pipeline)
  → n8n (trigger outreach sequence) 
  → Gmail (send personalized email)
```
*Use for: outbound prospecting, job search outreach, pipeline management*

### Pattern 5: Build → Ship → Measure
```
GitHub PR merge 
  → Vercel (auto-deploy) 
  → PostHog (event fires) 
  → n8n (alert if error rate spikes) 
  → Linear (auto-close related issue)
```
*Use for: all production deployments*

---

## 9. Decision Log

*Why key architectural and tool choices were made. Update when significant decisions are made.*

| Date | Decision | Rationale | What Would Change It |
|------|----------|-----------|---------------------|
| 2026-03-23 | n8n as central automation hub | Self-hosted, MCP-connected, visual, covers 80% of automation needs | If workflow complexity requires LangGraph-level agent orchestration |
| 2026-03-23 | Supabase as primary data layer | Postgres + auth + storage + vector + edge functions in one; MCP connected | If scale requires dedicated infrastructure |
| 2026-03-23 | Cursor as primary IDE | Best AI-assisted coding experience; project-wide context; `.cursorrules` support | If Devin/Factory mature enough for most coding tasks |
| 2026-03-23 | Claude as primary AI | Best reasoning, writing, and code quality; MCP ecosystem; Claude Projects | If a specific task category clearly requires another model |
| 2026-03-23 | Linear over ClickUp/Monday for issues | Faster, cleaner, better GitHub integration, engineer-preferred | If team collaboration requires more non-technical stakeholder tooling |
| 2026-03-25 | PROJECT_BRIEF as standard handoff artifact | Context degrades across agent rotations without a durable per-project state doc; template + handoff log enforces continuity | If a proper project management tool (Linear projects + docs) can fully replace the need| 
|2026-03-25 | Warp reserved for interactive debugging only | Token cost is not justified for scripted or automated terminal tasks; Claude bash_tool and Cursor terminal cover 95% of cases | If Warp pricing changes or a workflow genuinely requires its team-sharing features| 
| 2026-03-25 | Codex preferred over Devin for parallel tasks | ChatGPT Pro subscription makes Codex effectively free at current volume; Devin charges per task; for parallelizable, well-scoped work, Codex is the better economics | If Devin meaningfully outperforms on task quality or if Codex usage hits Pro limits |
| 2026-04-09 | HubSpot as primary CRM | MCP connected, handles pipeline management, contact/deal tracking, fills the "No CRM" gap | If sales workflow needs shift to a more developer-centric CRM like Attio |
| 2026-04-09 | Notion as knowledge base & content management | MCP connected, structured databases + wiki + content planning in one tool; outgrew GitHub markdown for project wikis | If a more integrated solution emerges or if Notion performance degrades at scale |
| 2026-04-09 | Buffer for social media management | Dedicated scheduling and cross-platform distribution; keeps content workflow separate from creation tools | If native platform scheduling becomes sufficient or a more integrated tool emerges |

---

## 10. Known Gaps & Planned Additions

### Current Gaps
- [ ] **Vector search not yet configured** — Supabase pgvector installed but no embedding pipeline built yet
- [ ] **No unified observability** — logging scattered across Vercel, Railway, Supabase; needs consolidation
- [ ] **n8n workflow library in progress** — `Engineering_meetingToLinear` brief complete, awaiting CTO Agent build session
- [x] **PostHog event taxonomy complete** — `PostHog_event_taxonomy.md` created; instrumentation pending first workflow build
- [x] **CRM added** — HubSpot connected via MCP; pipeline management operational
- [x] **Knowledge base added** — Notion connected via MCP; project wikis migrating from GitHub markdown
- [x] **Social media management added** — Buffer for scheduling and distribution

### Planned Additions (Under Evaluation)
| Tool | Category | Why | Priority |
|------|----------|-----|----------|
| LangSmith | LLM observability | Trace and evaluate LLM calls in production | Medium |
| Pinecone | Vector DB | If pgvector proves insufficient for RAG at scale | Low |
| Composio | Agent tool integrations | Broader tool connectivity for agents | Medium |

### Tools Evaluated & Rejected
| Tool | Reason Not Adopted |
|------|--------------------|
| ChatGPT | Removed from model stack — Claude covers all reasoning, writing, strategy, and code needs; Gemini covers long-context and Google integration. No unique role for ChatGPT. |
| NapkinAI | No MCP/API access (browser-only). Canva, Gamma, and Gemini (Imagen 3) cover diagram, data visualization, and concept map needs with better integration into the content pipeline. Removed 2026-04-09. |

---

## Maintenance

**Update this file when:**
- A new tool is added to the stack
- An MCP connection is added, removed, or changes URL/auth
- A new n8n workflow is built and deployed
- A significant architectural decision is made
- A tool is deprecated or replaced

**Version format:** `MAJOR.MINOR` — increment MINOR for additions, MAJOR for architectural changes

**Storage locations:**
- Primary: GitHub repo root (`/STACK_README.md`)
- Uploaded to: All active Claude Projects (re-upload after major updates)
- Reference copy: Notion (primary) or Google Drive (optional)

---

*This document is a living system. The goal is that any version of Claude, in any Project, reading this file, knows exactly what you're working with and how it fits together — without you having to explain it again.*
