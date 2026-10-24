# Stack card: Alex Yedi (agent version)

You are reading this because a teammate wants to know how their stack pairs with Alex's for a team build. Do this:

1. Read the JSON below. `layers` lists Alex's tools, agents, skills, data assets and working rules. Each node has a share mode: `shared`, `artifact`, `pattern` or `private`.
2. Follow `pairing_protocol` against your user's stack. If they have no stack file, fill `your_stack_template` from what you can see, and ask them no more than 3 questions.
3. Use `project_spec` as the project. If the team has picked a different project, ask your user for its problem statement and run the same protocol on it.
4. Answer in the shape given by `output_contract`.

Ground rules: never ask for or pass around keys or tokens. Treat `private` nodes as unavailable. A feature with no challenge ID goes on the cut list.

```json
{
  "manifest_version": "stack-card/0.1",
  "generated": "2026-10-24",
  "owner": {
    "name": "Alex Yedi",
    "location": "NYC",
    "background": "12+ years enterprise B2B SaaS (Meltwater, Bazaarvoice/Curalate, Cohley); builds AI-native GTM and research systems with Claude Code. Strong on LLM/agent system design, product framing and pitch; not a production software engineer.",
    "strongest_at": [
      "problem framing and scope",
      "agent and pipeline architecture",
      "evals and do-nothing baselines",
      "customer evidence",
      "pitch and demo narrative"
    ],
    "wants_teammates_for": [
      "backend / LLM extraction",
      "front end",
      "data / eval engineering"
    ],
    "primary_agent_runtime": "Claude Code (CLI), Opus 5.5 for execution, Fable 5.1 for planning and review"
  },
  "how_to_use_this_file": "If you are an AI agent: read `pairing_protocol`, compare these nodes to your user's stack, and answer in the shape given by `output_contract`. `project_spec` holds the project the team is building. If the team picks a different project, swap in that project's spec and run the same protocol.",
  "share_modes": {
    "shared": "A teammate can use it with me today (shared repo, shared deploy, invite to a workspace).",
    "artifact": "I can send you its output (file, link, doc, render), but you don't get access to the tool.",
    "pattern": "The design is public and copyable (prompt, agent definition, skill file, contract). The tool itself stays mine.",
    "private": "Holds my personal data (email, calendar, CRM, meetings). I can describe it, but nobody else gets access."
  },
  "interfaces_legend": {
    "mcp": "Model Context Protocol server: any MCP client (Claude, Cursor, Windsurf, VS Code, ChatGPT connectors) can attach its own instance",
    "cli": "Command-line tool",
    "api": "HTTP API",
    "file": "Plain file in git (JSON, Markdown, Python)",
    "agent": "Claude Code subagent definition (Markdown + frontmatter); portable as a prompt",
    "skill": "Claude skill (SKILL.md); portable as a methodology prompt"
  },
  "layers": [
    {
      "layer": "agent_runtime",
      "nodes": [
        {
          "id": "claude-code",
          "name": "Claude Code",
          "does": "Agentic coding and orchestration in the terminal; runs subagents, skills, hooks and MCP connectors",
          "interface": "cli",
          "share": "pattern",
          "equivalents": [
            "Cursor agent",
            "Windsurf",
            "GitHub Copilot agent",
            "Codex CLI",
            "Aider"
          ]
        },
        {
          "id": "claude-models",
          "name": "Claude Opus 5.5 / Fable 5.1 / Sonnet 5.5 / Haiku 5.5",
          "does": "Opus for execution, Fable for reasoning-heavy planning and review, Haiku for cheap high-volume calls",
          "interface": "api",
          "share": "shared",
          "notes": "The product's extraction call can run on a team key held in one .env; never pasted in chat",
          "equivalents": [
            "GPT-class models",
            "Gemini",
            "open-weight models via Hugging Face"
          ]
        }
      ]
    },
    {
      "layer": "agents",
      "description": "Specialist roles I dispatch from the main session. Each has a minimal tool list; agents that read untrusted text never hold write tools.",
      "nodes": [
        {
          "id": "agent-builder",
          "name": "builder",
          "does": "Scoped, tested code change inside a path allowlist; returns a diff summary",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-reviewer",
          "name": "reviewer",
          "does": "Read-only review in three modes: code diff, safeguards (prompt injection, secrets, data exposure), and demo (runs the demo end to end, timed, with live-failure fallbacks)",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-diagnostician",
          "name": "diagnostician",
          "does": "Finds one root cause from evidence when something breaks under time pressure; stops after two failed hypotheses",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-cto",
          "name": "cto-principal-architect",
          "does": "Architecture and build-plan decisions for small teams; battle-tested defaults, names tech debt",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-head-of-product",
          "name": "head-of-product",
          "does": "Scope challenges, PRDs, should-we-build-this checks",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-research-analyst",
          "name": "research-analyst",
          "does": "Market and competitor research with confidence levels",
          "interface": "agent",
          "share": "artifact"
        },
        {
          "id": "agent-systems-analyst",
          "name": "systems-analyst",
          "does": "Meadows-style systems analysis: loops, leverage points, second-order effects",
          "interface": "agent",
          "share": "artifact"
        },
        {
          "id": "agent-learning-coach",
          "name": "learning-coach-mentor",
          "does": "Teaches the concept behind each build step",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-research-fanout",
          "name": "event research fan-out (7 agents)",
          "does": "Four parallel researchers (company, person, topic, market signals), plus a conditioning pass, a synthesizer and a long-form renderer",
          "interface": "agent",
          "share": "pattern",
          "notes": "The parallel fan-out then synthesis pattern is reusable for any multi-source research step"
        },
        {
          "id": "agent-output-evaluator",
          "name": "output-evaluator",
          "does": "Clean-context check of public copy, one failure mode at a time (quotes, sources)",
          "interface": "agent",
          "share": "pattern"
        },
        {
          "id": "agent-visual-renderer",
          "name": "visual-renderer",
          "does": "Turns a slide brief into HTML, then a PDF carousel, and verifies there's no overflow",
          "interface": "agent",
          "share": "artifact"
        }
      ]
    },
    {
      "layer": "skills",
      "description": "Methodology files the agent loads on demand.",
      "nodes": [
        {
          "id": "skills-library",
          "name": "Personal skill library (~280 skills)",
          "does": "Product (PRDs, roadmaps, metrics, PMF), AI engineering (evals, RAG, agent design patterns, LangGraph, MCP servers, prompting), architecture (trade-off analysis, ADRs, distributed systems, data modeling), GTM (positioning, messaging, ICP, MEDDPICC), systems thinking, consulting (FMEA pre-mortem, task decomposition)",
          "interface": "skill",
          "share": "pattern",
          "hackathon_relevant": [
            "ai-evals",
            "eval-harness",
            "rag-architect",
            "ai-agent-design-patterns",
            "building-mcp-servers",
            "trade-off-analysis-method",
            "consulting-failure-design",
            "writing-prds",
            "positioning-messaging",
            "fullstack-dev",
            "frontend-dev"
          ]
        },
        {
          "id": "skills-pipeline",
          "name": "Event-pipeline skills (12)",
          "does": "Event research, pre- and post-event content, steering interview, transcript intelligence, role radar, interview prep, build judge",
          "interface": "skill",
          "share": "pattern",
          "public_source": "https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/tree/main/.claude/skills"
        }
      ]
    },
    {
      "layer": "build_and_deploy",
      "nodes": [
        {
          "id": "github",
          "name": "GitHub (gh CLI)",
          "does": "Repos, PRs, branch-per-change workflow",
          "interface": "cli",
          "share": "shared",
          "equivalents": [
            "GitLab"
          ]
        },
        {
          "id": "vercel",
          "name": "Vercel",
          "does": "Front-end and Next.js deploys, preview URLs per branch, env vars, logs",
          "interface": "mcp",
          "share": "shared",
          "equivalents": [
            "Netlify",
            "Cloudflare Pages"
          ]
        },
        {
          "id": "railway",
          "name": "Railway",
          "does": "Backend services, workers, Postgres, logs and metrics",
          "interface": "mcp",
          "share": "shared",
          "equivalents": [
            "Render",
            "Fly.io",
            "Heroku"
          ]
        },
        {
          "id": "supabase",
          "name": "Supabase",
          "does": "Postgres, auth, storage, edge functions",
          "interface": "mcp",
          "share": "shared",
          "notes": "My policy: the MCP connector is read-only; writes go through code with a guard",
          "equivalents": [
            "Neon",
            "Firebase",
            "PlanetScale"
          ]
        },
        {
          "id": "surrealdb",
          "name": "SurrealDB Cloud",
          "does": "Multi-model DB (document + graph)",
          "interface": "mcp",
          "share": "shared"
        },
        {
          "id": "n8n",
          "name": "n8n",
          "does": "Workflow automation and webhooks",
          "interface": "mcp",
          "share": "shared",
          "equivalents": [
            "Zapier",
            "Make",
            "Pipedream"
          ]
        },
        {
          "id": "huggingface",
          "name": "Hugging Face",
          "does": "Model and dataset search; source for a local or open-weight model option",
          "interface": "mcp",
          "share": "shared"
        },
        {
          "id": "posthog",
          "name": "PostHog",
          "does": "Product analytics, feature flags, LLM cost tracing",
          "interface": "mcp",
          "share": "shared",
          "equivalents": [
            "Amplitude",
            "Mixpanel"
          ]
        },
        {
          "id": "linear",
          "name": "Linear",
          "does": "Build issues that ship as PRs",
          "interface": "mcp",
          "share": "shared",
          "equivalents": [
            "Jira",
            "GitHub Issues"
          ]
        },
        {
          "id": "browser-automation",
          "name": "Claude in Chrome + Anchor Browser",
          "does": "Drive a real browser to test the live demo, or do cloud browser tasks",
          "interface": "mcp",
          "share": "artifact"
        }
      ]
    },
    {
      "layer": "design_and_presentation",
      "nodes": [
        {
          "id": "claude-html",
          "name": "Claude-authored HTML/SVG + headless Chrome",
          "does": "Technical, label-dense visuals and carousels; this page",
          "interface": "file",
          "share": "artifact"
        },
        {
          "id": "magic-patterns",
          "name": "Magic Patterns",
          "does": "UI prototypes and design systems from prompts",
          "interface": "mcp",
          "share": "artifact",
          "equivalents": [
            "v0",
            "Lovable",
            "Figma Make"
          ]
        },
        {
          "id": "mobbin",
          "name": "Mobbin",
          "does": "Real-app UI reference screens and flows",
          "interface": "mcp",
          "share": "artifact"
        },
        {
          "id": "gamma",
          "name": "Gamma",
          "does": "Design-led, low-density decks, docs and webpages with viewer analytics",
          "interface": "mcp",
          "share": "artifact",
          "notes": "Pitch deck candidate. Not for dense technical labels"
        },
        {
          "id": "canva",
          "name": "Canva",
          "does": "Brand-template design, exports",
          "interface": "mcp",
          "share": "artifact"
        }
      ]
    },
    {
      "layer": "media",
      "nodes": [
        {
          "id": "elevenlabs",
          "name": "ElevenLabs",
          "does": "Speech, transcription (scribe), voice, music",
          "interface": "mcp",
          "share": "artifact"
        },
        {
          "id": "higgsfield",
          "name": "Higgsfield",
          "does": "Image and video generation",
          "interface": "mcp",
          "share": "artifact"
        },
        {
          "id": "runway",
          "name": "Runway",
          "does": "Audio and video generation and editing",
          "interface": "mcp",
          "share": "artifact"
        }
      ]
    },
    {
      "layer": "knowledge_and_docs",
      "nodes": [
        {
          "id": "notion",
          "name": "Notion",
          "does": "System of record: events, people, companies, topics, drafts, roadmap; one schema-checked writer agent",
          "interface": "mcp",
          "share": "artifact",
          "notes": "Workspace is personal; I share pages, not the workspace"
        },
        {
          "id": "claude-docs",
          "name": "Claude Docs / Artifacts",
          "does": "Living shared docs and pages a team can read and comment on",
          "interface": "mcp",
          "share": "shared"
        },
        {
          "id": "google-drive",
          "name": "Google Drive",
          "does": "File sharing",
          "interface": "mcp",
          "share": "shared"
        },
        {
          "id": "chatprd",
          "name": "ChatPRD",
          "does": "PRD drafting",
          "interface": "mcp",
          "share": "artifact"
        }
      ]
    },
    {
      "layer": "private_data",
      "description": "Personal data. I can say what it does but can't share access.",
      "nodes": [
        {
          "id": "gmail",
          "name": "Gmail",
          "interface": "mcp",
          "share": "private"
        },
        {
          "id": "gcal",
          "name": "Google Calendar",
          "interface": "mcp",
          "share": "private"
        },
        {
          "id": "granola",
          "name": "Granola",
          "does": "Meeting notes",
          "interface": "mcp",
          "share": "private"
        },
        {
          "id": "supercut",
          "name": "Supercut",
          "does": "Recordings and transcripts",
          "interface": "mcp",
          "share": "private"
        },
        {
          "id": "hubspot",
          "name": "HubSpot",
          "does": "CRM",
          "interface": "mcp",
          "share": "private"
        },
        {
          "id": "clay",
          "name": "Clay",
          "does": "Enrichment (credit-gated)",
          "interface": "mcp",
          "share": "private"
        }
      ]
    },
    {
      "layer": "data_assets",
      "nodes": [
        {
          "id": "halyard-data-pack",
          "name": "Halyard Ventures Fund I data pack (fictional)",
          "does": "22 portfolio companies; clean Q2 and messy Q3 founder updates; fund ledger and marks; last quarter's LP report; answer key with char-span quotes; JSON Schema for extraction; scorer that always prints the carry-forward baseline",
          "interface": "file",
          "share": "shared",
          "notes": "Python stdlib only, no keys, deterministic. Baseline: 18.2% field accuracy, 0% traceback",
          "entry_points": [
            "python3 generate.py",
            "python3 eval/check_answer_key.py",
            "python3 eval/score.py <predictions_dir>"
          ],
          "contract": "schema/extracted_metrics.schema.json"
        }
      ]
    },
    {
      "layer": "working_rules",
      "description": "Conventions I bring to any team. These are where stacks plug together.",
      "nodes": [
        {
          "id": "rule-challenge-ids",
          "name": "Challenge-ID traceability",
          "does": "Every feature, task and slide traces to a quoted problem-statement clause; no ID means it gets cut",
          "interface": "file",
          "share": "pattern"
        },
        {
          "id": "rule-null-baseline",
          "name": "Null-baseline rule",
          "does": "Never report a metric without its do-nothing baseline",
          "interface": "file",
          "share": "pattern"
        },
        {
          "id": "rule-contract-first",
          "name": "Contract first",
          "does": "Agree the JSON schema before code so front end, backend and eval work in parallel against fixtures",
          "interface": "file",
          "share": "pattern"
        },
        {
          "id": "rule-no-span-no-number",
          "name": "No span, no number",
          "does": "Every extracted value carries the exact source quote; a quote that doesn't match the source is rejected",
          "interface": "file",
          "share": "pattern"
        },
        {
          "id": "rule-secrets",
          "name": "Secrets in .env only",
          "does": "Keys live in a gitignored .env or the deploy's env vars, never in chat or commits",
          "interface": "file",
          "share": "pattern"
        },
        {
          "id": "rule-one-writer",
          "name": "One writer per shared record",
          "does": "Exactly one process writes to a shared store; everyone else reads",
          "interface": "file",
          "share": "pattern"
        }
      ]
    }
  ],
  "collaboration_seams": [
    {
      "seam": "git repo",
      "why": "Every agent stack reads and writes git. One repo, one main branch, short-lived branches, merge every ~90 minutes."
    },
    {
      "seam": "JSON Schema contract",
      "why": "Any agent, any language, can generate fixtures and validate against it. It lets three people build in parallel."
    },
    {
      "seam": "HTTP endpoint between front end and backend",
      "why": "Language-neutral. Front end builds against a fixture JSON until the endpoint is live."
    },
    {
      "seam": "MCP servers",
      "why": "If we use the same vendor (Vercel, Railway, Supabase, Linear), each person attaches their own MCP client to the same project, so our agents see the same deploys and logs."
    },
    {
      "seam": "Markdown docs in the repo",
      "why": "README, prompt files and AGENTS.md / CLAUDE.md are read by every coding agent (Claude Code, Cursor, Copilot, Codex)."
    },
    {
      "seam": "the scorer",
      "why": "A stdlib Python command anyone can run; quality questions get settled by a number next to the baseline."
    }
  ],
  "project_spec": {
    "name": "Provable LP Update",
    "event": "Deal Flow: NYC VC Hackathon, Betaworks, 2026-10-24. Teams of four, about 9 hours, Funds / LP track",
    "thesis": "Your quarterly LP update, explained and provable. Messy founder updates become a GP letter where every number traces to its source and every change from last quarter is explained, so a Fund I manager can earn the trust that closes Fund II.",
    "buyer": "Emerging-manager GP (Fund I/II, under ~$100M)",
    "challenges": [
      {
        "id": "F1",
        "clause": "LPs commit capital for ten years and get PDFs in return."
      },
      {
        "id": "F2",
        "clause": "Yearly K-1s and quarterly reports arrive in different formats."
      },
      {
        "id": "F3",
        "clause": "Valuation marks move with little explanation."
      },
      {
        "id": "F4",
        "clause": "Judging a GP's real track record means rebuilding it by hand."
      },
      {
        "id": "P1",
        "clause": "A fund with 40 portfolio companies gets 40 updates in 40 formats, when it gets them at all."
      },
      {
        "id": "P2",
        "clause": "Partners often learn a company is in trouble when it asks for a bridge."
      },
      {
        "id": "E1",
        "clause": "Venture capital runs on spreadsheets, gut feel and endless inbox triage."
      }
    ],
    "out_of_scope": [
      "secondary pricing"
    ],
    "pipeline": [
      "founder updates (txt/md/deck export)",
      "redact: tokenize names",
      "extract: LLM to JSON with source spans",
      "validate: schema + span equals quote",
      "reconcile Q2 vs Q3 and raise flags",
      "GP review: annotate red rows (can't delete)",
      "letter renders only from reconciled deltas",
      "LP view: click any number to reach its source sentence"
    ],
    "must_have": [
      "extraction to the schema with source_span and quote on every value",
      "span check",
      "Q2 to Q3 diff with flags: unexplained, low_runway, conflicting_figures, non_recurring_arr, missing_update",
      "GP annotation on red rows",
      "letter paragraph where every number links to its span",
      "LP click-through view"
    ],
    "cut_first": [
      "PDF export",
      "rollup across all 22 companies (demo 3)",
      "fund-level NAV/TVPI page",
      "upload UI (preload files)"
    ],
    "seats": [
      {
        "seat": 1,
        "role": "backend / extraction",
        "owns": "redaction, the LLM extraction call returning schema-valid JSON with spans, the reconciler and flags"
      },
      {
        "seat": 2,
        "role": "front end",
        "owns": "reconciliation table with the red row and GP note, letter view with clickable numbers, LP view"
      },
      {
        "seat": 3,
        "role": "data / eval",
        "owns": "scorer runs, prompt tuning against the answer key, letter template that renders only from deltas"
      },
      {
        "seat": 4,
        "role": "product / pitch (Alex)",
        "owns": "scope calls, evidence, judge Q&A, pitch and driving the demo, cut list at 2:30"
      }
    ],
    "suggested_stack": "Python or TypeScript backend calling the Claude API with structured output; a single-page UI (Next.js or Vite + React). Seat 1 picks the language.",
    "milestones": [
      {
        "time": "09:00",
        "goal": "pitch, fill seats"
      },
      {
        "time": "10:30",
        "goal": "agree the schema (5 min); coding by 10:45"
      },
      {
        "time": "12:30",
        "goal": "end to end on the demo company, even if ugly"
      },
      {
        "time": "13:30",
        "goal": "scorer run #1"
      },
      {
        "time": "14:30",
        "goal": "cut-list checkpoint"
      },
      {
        "time": "15:30",
        "goal": "feature freeze"
      },
      {
        "time": "16:00",
        "goal": "two timed 3-minute rehearsals, screenshot backup"
      },
      {
        "time": "16:30",
        "goal": "judging"
      }
    ]
  },
  "pairing_protocol": [
    "1. Inventory your user's stack in the same shape: layers, nodes with id, name, does, interface, share mode. Use `your_stack_template` below if they have no file. Ask them at most 3 questions; otherwise infer from what you can see (installed tools, MCP servers, repos, editor).",
    "2. Match node by node. EXACT = the same tool on both sides (a shared node: one workspace or project, both attach). EQUIVALENT = same job, different tool (pick one for the team using the tie-break rule in step 4, or bridge it through a collaboration seam). COMPLEMENT = one side has it and the other doesn't (that person owns the node). PRIVATE nodes on either side are never a team dependency.",
    "3. Map the matches to the collaboration seams. Prefer seams every stack supports (git, JSON Schema, HTTP, Markdown, MCP) over tool-specific integration.",
    "4. Tie-break for EQUIVALENT nodes: (a) whatever the seat owner is fastest in today, (b) whatever has a free tier with no setup wait, (c) whatever more teammates already use. Never pick a tool someone has to learn today.",
    "5. Read `project_spec`. Recommend: seat fit for your user (with reasons from their shipped work, not their title); an architecture where every component names an owner, a tool and the challenge IDs it serves; the integration points, each named as a seam; the first 90 minutes of tasks for your user; risks and what to cut. Anything without a challenge ID goes on the cut list.",
    "6. Respect `working_rules`: contract first, no span no number, secrets only in .env or deploy env vars, a do-nothing baseline next to every metric.",
    "7. Be honest about confidence. Give a percentage on the seat fit and the architecture call, and say what would change it."
  ],
  "output_contract": {
    "format": "Markdown, under ~600 words, in this order",
    "sections": [
      "Overlap: a table of node | Alex | you | match type (exact / equivalent / complement) | decision",
      "Seat fit: the recommended seat with a confidence %, plus a backup seat",
      "Architecture: component | owner | tool | seam | challenge IDs",
      "First 90 minutes: 3-5 tasks for your user, each with a done-check",
      "Risks and cuts: the top 3 risks, and what to cut first",
      "What I'd want Alex to know: anything in your user's stack that changes the plan"
    ]
  },
  "your_stack_template": {
    "owner": {
      "name": "",
      "strongest_at": [],
      "shipped_recently": [],
      "fastest_languages_frameworks": [],
      "hard_stop_time": ""
    },
    "layers": [
      {
        "layer": "agent_runtime",
        "nodes": [
          {
            "id": "",
            "name": "",
            "does": "",
            "interface": "mcp|cli|api|file|agent|skill",
            "share": "shared|artifact|pattern|private"
          }
        ]
      },
      {
        "layer": "build_and_deploy",
        "nodes": []
      },
      {
        "layer": "design_and_presentation",
        "nodes": []
      },
      {
        "layer": "data_assets",
        "nodes": []
      },
      {
        "layer": "private_data",
        "nodes": []
      }
    ]
  }
}
```
