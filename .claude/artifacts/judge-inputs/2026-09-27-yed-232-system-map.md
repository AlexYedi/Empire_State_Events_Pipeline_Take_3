### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): src/data/system-map.curated.json
{
  "$note": "HAND-CURATED overlay for the System Map (YED-232, docs/system-map.prd.md). The generator (scripts/gen-system-map.mjs) merges this with facts it derives from the pipeline repo — frontmatter descriptions, first-shipped dates, tools, the ADR-8 file graph — into src/data/system-map.json. Everything here is a judgement: `why.text` must cite its `why.source`; a `status` override must carry a `reason`; `reviewed_at` is when a human last checked the entry against the code (the generator flags entries whose files changed after that date).",
  "zones": [
    {
      "id": "intake",
      "name": "Intake",
      "blurb": "Where an event enters the system — a calendar acceptance, not a form."
    },
    {
      "id": "pipelines",
      "name": "Pipelines",
      "blurb": "The research and content engines. Claude skills do the thinking; the parent thread owns the fan-out."
    },
    {
      "id": "graph",
      "name": "Knowledge graph",
      "blurb": "The Market-Intelligence Engine's system of record — one Postgres graph, claims first-class."
    },
    {
      "id": "records",
      "name": "Systems of record",
      "blurb": "Where the outputs live: Notion for content and research, HubSpot for people, Linear for what's open."
    },
    {
      "id": "rigor",
      "name": "Rigor layer",
      "blurb": "What keeps a solo build honest: gates that hold a run open, a judge, telemetry, a weekly review."
    },
    {
      "id": "surfaces",
      "name": "Surfaces",
      "blurb": "Where people see it — this site, the build journal, and LinkedIn."
    }
  ],
  "components": [
    {
      "id": "calendar",
      "zone": "intake",
      "name": "Going-to-Events calendar",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "A dedicated Google Calendar. Accepting an event there is the pipeline's only trigger.",
      "why": {
        "text": "The predecessor project (new-jack-city) chained n8n → Claude → Notion and failed repeatedly at the integration layer. Take 3 separates 'do great research' from 'put it in the right places': the trigger is the moment Alex already performs — accepting an invite — and nothing is automated between that and a human reading the brief.",
        "source": "CLAUDE.md § Architecture Philosophy; .claude/references/pipeline-block-template.md"
      },
      "build": {
        "refs": [
          "YED-6"
        ],
        "note": "The predecessor's GCal intake (YED-6) was the one piece that worked; it became the intake model here."
      },
      "tools": [
        "Google Calendar MCP"
      ],
      "files": []
    },
    {
      "id": "check-new-events",
      "zone": "intake",
      "name": "/check-new-events",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "Calendar-invite-as-structured-intake: Alex pastes a PIPELINE block into the invite at acceptance time, the command finds those events, dedups them against Notion and runs research + pre-event content per event with a continue-or-quit gate between them. Most real invites carry no block, so it also parses the raw description rather than exiting.",
        "source": ".claude/commands/check-new-events.md; CLAUDE.md § Phase 1 (2026-05-20); memory 2026-07-07 raw-calendar fallback"
      },
      "build": {
        "refs": [],
        "note": "Validated end-to-end on Ray Dev Day, 2026-05-20."
      },
      "files": [
        ".claude/commands/check-new-events.md",
        ".claude/references/pipeline-block-template.md",
        ".claude/commands/morning-refresh.md"
      ]
    },
    {
      "id": "event-claim",
      "zone": "intake",
      "name": "Event claim",
      "kind": "hook",
      "reviewed_at": "2026-09-27",
      "summary": "A machine-global lock on an event's Notion namespace for the duration of a run.",
      "why": {
        "text": "Git worktrees isolate checkouts but not Notion. On 2026-09-20 two sessions ran the same event and disagreed on two facts; duplicate effort is cheap, contradictory records that later runs read as fact are not. So a run claims the event first (exit 3 = someone else holds it → go read-only), claims expire after 4h so a crashed run can't lock an event, and the run-close gates now key on the same claim to know a run is still in progress.",
        "source": "CLAUDE.md § Git conventions (YED-213, 2026-09-24); .claude/notes/stop-gate-per-turn-2026-09-27.md"
      },
      "build": {
        "refs": [
          "YED-213",
          "YED-228"
        ]
      },
      "files": [
        ".claude/hooks/event-claim.py",
        ".claude/evals/test_event_claim.py",
        ".claude/hooks/_run_in_progress.sh"
      ]
    },
    {
      "id": "event-deep-research",
      "zone": "pipelines",
      "name": "/event-deep-research",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "The core of the system: an invite goes in, a researched brief on the room comes out. It is one artifact with two layers (ADR-5): a scannable head for the room and a ~45-minute prose Deep Read for the commute. The fan-out — four specialists in parallel, then a synthesizer — runs from the parent thread because the Agent SDK does not let a subagent spawn subagents; designing around that constraint instead of fighting it is what made the pipeline reliable. Since YED-205 the research also writes its Evidence Ledger into the knowledge graph, so the next run compounds instead of restarting.",
        "source": "docs/adr/ADR-5-event-field-guide.md; .claude/references/sdk-runtime-constraints.md; .claude/notes/yed-205-spec-2026-09-27.md"
      },
      "build": {
        "refs": [
          "YED-136",
          "YED-139",
          "YED-205",
          "YED-228"
        ],
        "note": "Monolithic skill (2026-04) → multi-agent rebuild (2026-05-04) → orchestrator-to-synthesizer pivot (2026-05-07) → Deep Read (2026-08) → graph write-back (2026-09-27)."
      },
      "tools": [
        "Notion MCP",
        "HubSpot MCP",
        "Gmail MCP",
        "WebSearch",
        "Opus (Deep Read)",
        "Sonnet (synthesis)"
      ],
      "files": [
        ".claude/commands/event-deep-research.md",
        ".claude/skills/event-research/**",
        ".claude/agents/research/company-researcher.md",
        ".claude/agents/research/person-researcher.md",
        ".claude/agents/research/topic-landscape-analyst.md",
        ".claude/agents/research/competitive-signal-scanner.md",
        ".claude/agents/research/event-research-synthesizer.md",
        ".claude/agents/research/knowledge-conditioning.md",
        ".claude/agents/content/field-guide-renderer.md",
        ".claude/agents/ops/notion-writer.md",
        ".claude/references/sdk-runtime-constraints.md",
        "docs/adr/ADR-5-event-field-guide.md",
        "docs/adr/ADR-6-research-brief-placement.md",
        ".claude/notes/yed-205-spec-2026-09-27.md",
        ".claude/skills/company-deep-research/**",
        ".claude/skills/research-methodology/**",
        ".claude/evals/score_entities.py",
        ".claude/evals/score_events.py",
        ".claude/evals/pronoun-fidelity-render-2026-09-18.md",
        ".claude/proposals/event-field-guide.md",
        ".claude/proposals/field-guide-spike-daytona.md",
        ".claude/notes/deep-read-batch-wiring-fix.md",
        ".claude/references/research-analyst-prompt.md",
        ".claude/notes/ai-mafia-roster-2026-09-21.md",
        ".claude/notes/gtm-world-tour-intake-2026-09-23.md"
      ]
    },
    {
      "id": "pre-event-content",
      "zone": "pipelines",
      "name": "Pre-event content",
      "kind": "skill",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "Turns the brief into the first half of a deliberate two-part arc: a per-event LinkedIn post (three hook variants, every one shipped to Notion for comment-based iteration), a Sunday roundup that sets the table without taking a side, prepared questions, and 200-character connection-request notes rather than DMs (LinkedIn's free tier only messages 1st-degree connections). Stance is earned by space and expertise — a hot take in a synopsis is worth nothing — so the bold point of view is deferred to the post-event recap.",
        "source": ".claude/skills/pre-event-content/SKILL.md; .claude/references/content-style-guide.md v0.5–0.9; CLAUDE.md § Phase 2 (DM rule 2026-05-20, stance rule 2026-05-30)"
      },
      "build": {
        "refs": [
          "YED-132",
          "YED-178"
        ],
        "note": "Steering-interview (Aim → Sharpen) added 2026-05-30 so Alex's angle is captured before generation, not corrected after."
      },
      "tools": [
        "Notion MCP"
      ],
      "files": [
        ".claude/skills/pre-event-content/**",
        ".claude/skills/steering-interview/**",
        ".claude/references/outreach-templates.md",
        ".claude/skills/marketing-autoresearch/**",
        ".claude/skills/project-ideation/**",
        ".claude/proposals/steering-interview-v2-collaborative.md",
        ".claude/notes/steering-v2-smoke-test-2026-08-29.md",
        ".claude/scripts/check_aimed_questions.py",
        ".claude/references/portfolio-tracker.md"
      ]
    },
    {
      "id": "post-event-content",
      "zone": "pipelines",
      "name": "/post-event-content",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "The second half of the arc: what was actually said, cashed against the pre-event setup. A manual transcript (Granola's MCP sees zero notes on the free plan; OBS + ElevenLabs Scribe is the owned capture lane) is conditioned into a quote bank, synthesized into a post_event_brief — the canonical store every downstream draft references — then drafted by the content-correspondent skill. Since ADR-10 it also creates the attended event row in the graph and attaches the pre-event claims to it.",
        "source": ".claude/commands/post-event-content.md; CLAUDE.md § Phase 2 (2026-05-21 / 05-28); memory 2026-09-09 CRM + capture decision; docs/adr/ADR-10-knowledge-substrate.md D9"
      },
      "build": {
        "refs": [
          "YED-160",
          "YED-166",
          "YED-198"
        ],
        "note": "Granola auto-fetch built then disabled 2026-05-27; recording ingest + slide alignment added 2026-09."
      },
      "tools": [
        "Notion MCP",
        "HubSpot MCP",
        "ElevenLabs Scribe",
        "OBS Studio"
      ],
      "files": [
        ".claude/commands/post-event-content.md",
        ".claude/commands/ingest-recording.md",
        ".claude/commands/evergreen-deep-dive.md",
        ".claude/skills/content-correspondent/**",
        ".claude/skills/transcript-intelligence/**",
        ".claude/scripts/ingest_recording.py",
        ".claude/scripts/align_slides.py",
        ".claude/skills/content-patterns/founder-showcase.md",
        ".claude/evals/agents-behaving-badly/**",
        ".claude/evals/run_scribe.py",
        ".claude/evals/ingest-elevenlabs-scorecard.md",
        ".claude/evals/transcription-quality-scorecard.md",
        ".claude/evals/post-event-brief-template-evidence.md",
        ".claude/tools/obs_ingest.py",
        ".claude/references/obs-capture-setup.md",
        ".claude/proposals/post-event-hubspot-step.md"
      ]
    },
    {
      "id": "scaffolded-workflows",
      "zone": "pipelines",
      "name": "Workflows B / C / D (scaffolded)",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "status": {
        "value": "scaffolded",
        "reason": "Command files exist with documented triggers and flow; never wired end-to-end. /post-event-content is the live B path; the fuller chain is parked as YED-198 (.claude/WORKFLOWS.md)."
      },
      "summary": "/post-event-synthesis, /weekly-recap and /voice-pass — documented shapes for the fuller post-event chain, the Sunday recap and a voice polish pass.",
      "why": {
        "text": "They were scaffolded in the 2026-05 rebuild as the intended systemization (transcript analysis → objection mining → insight generation → content → pattern synthesis). The day-to-day need was met by the lighter /post-event-content, and the execution-focus steering bias says: build a component when a named publishing friction motivates it, not before. None has, so they stay honest scaffolds.",
        "source": ".claude/WORKFLOWS.md § Workflow B/C/D; CLAUDE.md § Execution-focus window (2026-06-11)"
      },
      "build": {
        "refs": [
          "YED-198"
        ]
      },
      "files": [
        ".claude/commands/post-event-synthesis.md",
        ".claude/commands/weekly-recap.md",
        ".claude/commands/voice-pass.md",
        ".claude/skills/pattern-synthesis/**",
        ".claude/proposals/content-pipeline-v2-stage2.md"
      ]
    },
    {
      "id": "voice-system",
      "zone": "pipelines",
      "name": "Voice & visual system",
      "kind": "reference",
      "reviewed_at": "2026-09-27",
      "summary": "The style guide, anti-patterns, audience north star, shared content patterns and the visual-brief spec every content skill imports.",
      "why": {
        "text": "Voice is a living system, not a prompt: Alex reviews drafts as inline Notion comments, and the update-voice-and-style skill mines those comments back into the guides so every skill inherits the correction once. Visuals must add information (architecture, comparison, progression) and never re-print the post; they are authored by Claude as self-contained HTML/SVG and exported to a 4:5 PDF — Gamma was removed on 2026-08-07 because it re-interpreted content and broke labels.",
        "source": ".claude/references/content-style-guide.md; .claude/references/content-anti-patterns.md; .claude/skills/content-patterns/visual-briefs.md; CLAUDE.md Rule 13 (2026-08-07)"
      },
      "build": {
        "refs": [
          "YED-200"
        ],
        "note": "v0.5 (stance + self, 2026-05-30) → v0.6 (no I-led openers, 2026-08-07) → v0.9 (table-set context first, 2026-09-09)."
      },
      "tools": [
        "Claude design (HTML/SVG)",
        "headless Chrome (PDF export)",
        "Gemini (pictorial imagery)"
      ],
      "files": [
        ".claude/references/content-style-guide.md",
        ".claude/references/content-anti-patterns.md",
        ".claude/references/audience-north-star.md",
        ".claude/skills/content-patterns/**",
        ".claude/skills/update-voice-and-style.md",
        ".claude/skills/update-anti-patterns.md",
        ".claude/skills/content-quality/**",
        ".claude/skills/brand-storytelling/**",
        ".claude/skills/copywriting/**",
        ".claude/agents/content/voice-editor.md"
      ]
    },
    {
      "id": "interview-prep",
      "zone": "pipelines",
      "name": "/interview-prep",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "Milestone 1 of the Market-Intelligence Engine and the first job-search consumer of the graph: a four-axis dossier (company, role, stage, interviewer) built by the same specialist fan-out, judge-gated before it is written. It exists because the research engine is lens-agnostic — the same graph that preps an event can prep an interview — and the job search is running in parallel with the content work.",
        "source": ".claude/skills/interview-prep-dossier/SKILL.md; memory 2026-06-28 Market-Intelligence Engine; CLAUDE.md § standing context"
      },
      "build": {
        "refs": [
          "YED-152",
          "YED-207"
        ]
      },
      "tools": [
        "Supabase MCP (read-only)",
        "Notion MCP",
        "WebSearch"
      ],
      "files": [
        ".claude/commands/interview-prep.md",
        ".claude/skills/interview-prep-dossier/**",
        ".claude/agents/research/dossier-synthesizer.md",
        ".claude/skills/icp-research/**"
      ]
    },
    {
      "id": "signal-scanners",
      "zone": "pipelines",
      "name": "Signal scanners",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "summary": "/scan-trends, /scan-roles, /scan-voices — three radars over legitimate public sources, human-in-the-loop, writing Notion notes and (trends) graph signals.",
      "why": {
        "text": "Part of the measurement layer's answer to 'what is moving': periodic scans that feed Topics' current-events notes and the trend producer on the graph. Roles is the job-search radar; voices tracks who is saying what. All three present a digest and stop at a human gate before writing.",
        "source": ".claude/skills/trend-radar/SKILL.md; .claude/skills/role-radar/SKILL.md; .claude/skills/voice-radar/SKILL.md; CLAUDE.md § measurement layer"
      },
      "build": {
        "refs": [
          "YED-149"
        ]
      },
      "tools": [
        "WebSearch",
        "Notion MCP"
      ],
      "files": [
        ".claude/commands/scan-trends.md",
        ".claude/commands/scan-roles.md",
        ".claude/commands/scan-voices.md",
        ".claude/skills/trend-radar/**",
        ".claude/skills/role-radar/**",
        ".claude/skills/voice-radar/**"
      ]
    },
    {
      "id": "inbox-miner",
      "zone": "pipelines",
      "name": "/scan-inbox",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "Gmail is a first-class signal source (ADR-7): newsletters and event correspondence are the earliest, cheapest market signal Alex already receives. The miner reads an allowlist of senders, dedups on canonical URL, writes email signals to the graph through the one write path, and labels what it has processed. A denylist keeps private correspondence out by construction.",
        "source": "docs/adr/ADR-7-inbox-signal-source.md; .claude/skills/inbox-miner/SKILL.md"
      },
      "build": {
        "refs": [
          "YED-153",
          "YED-194"
        ]
      },
      "tools": [
        "Gmail MCP",
        "Supabase REST"
      ],
      "files": [
        ".claude/commands/scan-inbox.md",
        ".claude/skills/inbox-miner/**",
        ".claude/scripts/inbox_signal_write.py",
        ".claude/scripts/inbox_boundary.py",
        "docs/adr/ADR-7-inbox-signal-source.md",
        ".claude/evals/inbox-miner-cohort-v1.md",
        ".claude/proposals/yed-161-inbox-boundary-mechanism.md"
      ]
    },
    {
      "id": "doc-knowledge-base",
      "zone": "pipelines",
      "name": "Document knowledge base",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "status": {
        "value": "scaffolded",
        "reason": "Ingest (B1) and ask (B2) exist but are inert until /doc-digest and consumer wiring land — roadmap P1, YED-157 B3–B5."
      },
      "summary": "/ingest-doc and /ask-library — long documents (books, papers) archived to R2 and made queryable.",
      "why": {
        "text": "Large documents live outside the repos (the Knowledge Library) with R2 as the archive of record; ingesting them lets research cite primary sources instead of search snippets. It earns its keep only when digests flow into the pipelines' filter lines, which is the P1 work.",
        "source": ".claude/skills/doc-knowledge-base/SKILL.md; memory 2026-09-11 Knowledge Library; roadmap.md § 5 Phase 1"
      },
      "build": {
        "refs": [
          "YED-157",
          "YED-107"
        ]
      },
      "tools": [
        "Cloudflare R2"
      ],
      "files": [
        ".claude/commands/ingest-doc.md",
        ".claude/commands/ask-library.md",
        ".claude/skills/doc-knowledge-base/**",
        ".claude/references/doc-kb-migration-a5.sql",
        ".claude/references/doc-kb-migration-b1.sql",
        ".claude/references/doc-kb-schema.sql"
      ]
    },
    {
      "id": "gtm-suite",
      "zone": "pipelines",
      "name": "GTM research & copy suite",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "summary": "Imported market-research and copywriting commands plus the sales-methodology agents (reframe, mobilizer mapping, commercial insight).",
      "why": {
        "text": "Alex's day job is enterprise GTM; these encode the Challenger-style methodology and a research-director bench so the same toolkit serves client work and the content engine. They were imported as thin docs in 2026-07 without a PRD — an honest candidate for retro-codification, kept visible here rather than hidden.",
        "source": ".claude/WORKFLOWS.md (2026-07-02 row); .claude/agents/sales-methodology/*"
      },
      "build": {
        "refs": [],
        "note": "No PRD or Linear issue of their own — flagged in WORKFLOWS.md."
      },
      "files": [
        ".claude/commands/run-market-landscape-study.md",
        ".claude/commands/analyze-competitive-landscape.md",
        ".claude/commands/create-messaging-brief.md",
        ".claude/commands/generate-channel-copy.md",
        ".claude/commands/test-and-report.md",
        ".claude/agents/sales-methodology/**",
        ".claude/agents/research/market-insights-director.md",
        ".claude/agents/research/insights-research-director.md",
        ".claude/agents/research/quant-insights-architect.md",
        ".claude/agents/research/qualitative-field-lead.md",
        ".claude/agents/research/win-loss-analyst.md",
        ".claude/agents/research/battlecard-program-manager.md",
        ".claude/agents/content/cold-email-specialist.md",
        ".claude/agents/content/conversion-copywriter.md",
        ".claude/agents/content/copy-strategist.md",
        ".claude/skills/cold-email/**",
        ".claude/skills/conducting-user-interviews/**",
        ".claude/notes/eric-coldoutboundskills-harvest-2026-09-24.md"
      ]
    },
    {
      "id": "supabase-graph",
      "zone": "graph",
      "name": "Postgres knowledge graph",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "One Supabase project (Empire prod) holding people, companies, topics, events, documents and claims — the system of record for market intelligence.",
      "why": {
        "text": "The 'no Supabase' rule held for the base pipeline, but a lens-agnostic intelligence engine needs a graph that persists across runs: an event is a hyperedge that connects people, companies and topics, and every run should compound what the last one learned. Consolidated onto this one project (ADR-1/ADR-4) after the separate GTM spine was decommissioned; accessed over REST with a scoped key, and through the Supabase MCP only for read-only inspection.",
        "source": "docs/adr/ADR-1-data-layer.md; docs/adr/ADR-4-increment-2.md; CLAUDE.md § measurement layer (tombstone re-scoped 2026-06-28); memory 2026-09-17 Supabase MCP canonical"
      },
      "build": {
        "refs": [
          "YED-130",
          "YED-135",
          "YED-160"
        ],
        "note": "Cutover 2026-08-10 (Increment 2b); gtm spine decommissioned; nightly health-check watches coherence."
      },
      "tools": [
        "Supabase (Postgres, REST)",
        "pgvector",
        "GitHub Actions (nightly health-check)"
      ],
      "files": [
        ".claude/references/market-intel-spine.md",
        "docs/adr/ADR-0-reconciliation.md",
        "docs/adr/ADR-1-data-layer.md",
        "docs/adr/ADR-2-surface-layer.md",
        "docs/adr/ADR-3-capability-layer.md",
        "docs/adr/ADR-4-increment-2.md",
        "docs/migration-playbook.md",
        ".claude/references/market-intel-schema.sql",
        ".claude/references/market-intel-backfill.md",
        ".claude/references/postgres-glossary.md",
        ".claude/references/signal-taxonomy.md",
        "docs/adr/README.md",
        "docs/adr/evidence/**"
      ]
    },
    {
      "id": "spine-client",
      "zone": "graph",
      "name": "spine_client (the one write path)",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "Every write to the graph goes through one Python client that hard-fails on contact PII (ADR-9: email and phone never enter the spine — HubSpot holds contact detail). A single chokepoint is cheaper to audit than a Postgres constraint today and can become one later. It also carries the bounded retry that a live run exposed on 2026-09-27, when an intermittent network stall looked like a broken pipeline.",
        "source": "docs/adr/ADR-9-pii-boundary.md; .claude/scripts/spine_client.py (selftest + --check-writers)"
      },
      "build": {
        "refs": [
          "YED-81",
          "YED-205"
        ]
      },
      "tools": [
        "Supabase REST"
      ],
      "files": [
        ".claude/scripts/spine_client.py",
        ".claude/scripts/spine_write.py",
        "docs/adr/ADR-9-pii-boundary.md",
        ".claude/scripts/backfill_people.py",
        ".claude/proposals/yed-81-sec-pii-guardrails.md"
      ]
    },
    {
      "id": "substrate",
      "zone": "graph",
      "name": "Knowledge substrate (claims)",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "why": {
        "text": "ADR-10 makes claims first-class: a sourced, tiered statement ('web-verified', 'email-signal') attached to the entities it is about, with documents generalized so a research brief, a transcript and a newsletter are the same kind of thing. One producer library stages them; identity merges are human-only soft merges with a revert path. The A/B against the legacy retrieval showed the substrate wins on material and the legacy path on packaging, so both stay and the merge is the next step, not a rerun.",
        "source": "docs/adr/ADR-10-knowledge-substrate.md (Accepted 2026-09-27, Amendment 1); memory 2026-09-24 A/B verdict; memory 2026-09-27 identity S1b-lite"
      },
      "build": {
        "refs": [
          "YED-160",
          "YED-168",
          "YED-172",
          "YED-47",
          "YED-217",
          "YED-218"
        ]
      },
      "tools": [
        "Supabase REST"
      ],
      "files": [
        ".claude/scripts/substrate.py",
        ".claude/scripts/identity_probe.py",
        "docs/adr/ADR-10-knowledge-substrate.md",
        ".claude/notes/knowledge-substrate-review-2026-09-18.md",
        ".claude/notes/ab-protocol-yed172-2026-09-19.md",
        ".claude/hooks/ab-reminder.sh",
        ".claude/hooks/test_ab_reminder.py",
        ".claude/notes/knowledge-substrate-architecture-2026-09-18.md",
        ".claude/notes/substrate-handoff-to-home.md",
        ".claude/notes/substrate-vs-reconciliation-sequencing-2026-09-18.md",
        ".claude/notes/yed-160-scope-2026-09-17.md",
        ".claude/notes/yed-217-conditioner-aiming-2026-09-25.md",
        ".claude/notes/yed-47-premortem-2026-09-27.md",
        ".claude/references/graph-freeze.md"
      ]
    },
    {
      "id": "retrieve",
      "zone": "graph",
      "name": "retrieve (lenses)",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "summary": "The one retrieval interface: a lens (event · interview · content) plus seed entities in, a budgeted Context Pack of prior occasions, returning faces and scored claims out.",
      "why": {
        "text": "Consumers should never query tables directly; a lens names what a consumer needs and the interface enforces a token budget and a loud failure (exit 5) when the graph holds claims for these entities but the pack kept none — silent emptiness is how prior knowledge quietly stops compounding. The event lens is live; interview and content lenses are the open consumer work.",
        "source": ".claude/scripts/retrieve.py; docs/adr/ADR-10-knowledge-substrate.md; .claude/commands/event-deep-research.md Step 1.7a-S"
      },
      "build": {
        "refs": [
          "YED-170",
          "YED-207",
          "YED-208"
        ]
      },
      "files": [
        ".claude/scripts/retrieve.py"
      ]
    },
    {
      "id": "topic-intelligence",
      "zone": "graph",
      "name": "Topic intelligence",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "status": {
        "value": "stale",
        "reason": "The topic_intelligence tables have not been recomputed since the 2026-08-10 cutover: the nightly recompute was never wired (pg_cron not installed), the health-check went red for 9 nights into GitHub issues nobody read, and the Hub's trend panel served 7-week-old data. YED-230."
      },
      "summary": "Relevance scoring and topic movement over the graph — what is moving, for whom.",
      "why": {
        "text": "The graph is only useful if something ranks it: relevance per lens and movement per topic are what the Hub's market-intel panels and the P2 architecture lens read. It is listed stale on purpose — this is the exact failure the map exists to make visible.",
        "source": "memory 2026-09-27 systems-gaps decision; Linear YED-230; .claude/scripts/recompute_relevance.py"
      },
      "build": {
        "refs": [
          "YED-230",
          "YED-131",
          "YED-114"
        ]
      },
      "tools": [
        "Postgres functions",
        "GitHub Actions (health-check)"
      ],
      "files": [
        ".claude/scripts/recompute_relevance.py",
        ".claude/scripts/match_topic.py",
        ".claude/commands/recompute-relevance.md"
      ]
    },
    {
      "id": "notion",
      "zone": "records",
      "name": "Notion (Content + Research Hub)",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "Six bidirectionally-related databases: Events, People, Companies, Topics, Content Drafts, Project Ideas.",
      "why": {
        "text": "Notion is the review surface: Alex reads briefs and drafts there and comments inline, and those comments are mined back into the voice system. Page bodies hold long-form text, properties hold what must be filterable, and writes are dependency-ordered because relation fields need the URLs of pages created first. Notion MCP calls only work in the parent thread, which shaped the notion-writer agent's role.",
        "source": ".claude/references/notion-schema.md; .claude/references/notion-write-gotchas.md; CLAUDE.md § Notion Write Orchestration; memory 2026-06-10 parent-thread writes"
      },
      "build": {
        "refs": [],
        "note": "Schema verified via MCP 2026-04-09; gotchas (a)–(m) accumulated from live failures."
      },
      "tools": [
        "Notion MCP"
      ],
      "files": [
        ".claude/references/notion-schema.md",
        ".claude/references/notion-write-gotchas.md"
      ]
    },
    {
      "id": "hubspot",
      "zone": "records",
      "name": "HubSpot CRM",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "Companies and Contacts with associations; event tracking as Notes because Static Lists are not writable over MCP.",
      "why": {
        "text": "HubSpot is where contact detail lives — the PII boundary (ADR-9) keeps email and phone out of the graph precisely because the CRM already holds them. Contacts are created only after Alex approves a confirmation table (judgement load keeps that step manual). A CRM replacement (Clarify) was evaluated and rejected on 2026-09-09.",
        "source": "CLAUDE.md § HubSpot Write Orchestration; docs/adr/ADR-9-pii-boundary.md; memory 2026-09-09 CRM + capture decision"
      },
      "build": {
        "refs": [
          "YED-81"
        ]
      },
      "tools": [
        "HubSpot MCP"
      ],
      "files": []
    },
    {
      "id": "gmail",
      "zone": "records",
      "name": "Gmail",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "Correspondence and newsletters — read as prior knowledge before research, mined as a signal source, labeled after processing.",
      "why": {
        "text": "The inbox already receives the market: newsletters, organizer emails, follow-ups. Reading it before research (Step 1.7) and mining it on a schedule (ADR-7) turns that into graph signals without a scraper. Write scope was granted narrowly (labels only) on 2026-09-10.",
        "source": "docs/adr/ADR-7-inbox-signal-source.md; .claude/commands/event-deep-research.md Step 1.7a"
      },
      "build": {
        "refs": [
          "YED-153"
        ]
      },
      "tools": [
        "Gmail MCP"
      ],
      "files": []
    },
    {
      "id": "linear",
      "zone": "records",
      "name": "Linear",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "The single source of truth for what is open. Pulled live at every session start; the build path on this map reads it.",
      "why": {
        "text": "A static priorities block in the project instructions drifted the moment it was written, so Linear became the only place issue state lives and a SessionStart hook pulls the top priorities into every session. When git and Linear disagree, git is the fact and Linear gets corrected. Parked and deferred thoughts must be filed the same turn they are written — no 'revisit later' text without a pointer.",
        "source": "CLAUDE.md § Priorities (YED-26, 2026-05-13); .claude/references/linear-convention.md § Container rule"
      },
      "build": {
        "refs": [
          "YED-26",
          "YED-29"
        ]
      },
      "tools": [
        "Linear MCP",
        "Linear API"
      ],
      "files": [
        ".claude/references/linear-convention.md"
      ]
    },
    {
      "id": "posthog",
      "zone": "records",
      "name": "PostHog",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "Project 524367 — the projection of build-session and judge-run telemetry that the Hub's rigor dashboard reads.",
      "why": {
        "text": "The measurement layer needed a queryable projection without adding a database; PostHog captures each build session and judge run as an event, and the Hub reads them with a project-scoped key. Chosen over Langfuse and a Supabase measurement store, both tombstoned so the rigor layer stays lean.",
        "source": "CLAUDE.md § measurement layer (PostHog projection LIVE 2026-07-11); .claude/notes/measurement-layer-learnings.md"
      },
      "build": {
        "refs": [
          "YED-88",
          "YED-91"
        ]
      },
      "tools": [
        "PostHog capture + query API"
      ],
      "files": [
        ".claude/notes/measurement-layer-learnings.md"
      ]
    },
    {
      "id": "dod-gate",
      "zone": "rigor",
      "name": "Definition of Done",
      "kind": "policy",
      "reviewed_at": "2026-09-27",
      "summary": "Three items (+1) a non-trivial build must meet or explicitly waive: a spec before code, a Linear issue, an adversarial pass, a judge run — recorded by /dod-close.",
      "why": {
        "text": "A systems analysis diagnosed the root cause of quiet failures as Shifting the Burden: rigor lived in optional docs, never in the execution path, so a memory-less agent shipped on green checks and the consequence surfaced weeks later. The gate puts a floor under 'done' without blocking flow; waivers are logged as data so the pattern stays visible. It is deliberately capped at three items — growth is the rule-beating signal.",
        "source": "CLAUDE.md § Definition of Done (pilot 2026-06-25; writer wired 2026-07-11); .claude/references/prd-template.md"
      },
      "build": {
        "refs": [
          "YED-87",
          "YED-129",
          "YED-201"
        ],
        "note": "The semantic writer (/dod-close) was missing for two weeks — telemetry carried nulls in 100% of rows until it shipped."
      },
      "files": [
        ".claude/commands/dod-close.md",
        ".claude/hooks/dod-close.sh",
        ".claude/references/prd-template.md",
        ".claude/references/linear-convention.md",
        ".claude/skills/writing-prds/**"
      ]
    },
    {
      "id": "run-gates",
      "zone": "rigor",
      "name": "Run-close gates",
      "kind": "hook",
      "reviewed_at": "2026-09-27",
      "summary": "Stop hooks that hold a research run open until its Deep Read is rendered and its claims are staged to the graph — plus a session-start sweep for abandoned runs.",
      "why": {
        "text": "A silently skipped Deep Read or graph write must never close green. Each run registers a pending row; the hook refuses to close while one is pending. On 2026-09-27 the gates were found firing on every turn (Claude Code's Stop event is per turn, not per session), blocking, re-invoking the model and logging false failures — so they now treat 'pending' as in-progress while the session holds a live event claim, and fail only at the first turn after the claim is released.",
        "source": ".claude/notes/stop-gate-per-turn-2026-09-27.md; .claude/proposals/deep-read-marker-gate.md"
      },
      "build": {
        "refs": [
          "YED-139",
          "YED-205",
          "YED-228"
        ]
      },
      "files": [
        ".claude/hooks/deep-read-gate.sh",
        ".claude/hooks/deep-read-ledger.sh",
        ".claude/hooks/substrate-gate.sh",
        ".claude/hooks/_run_in_progress.sh",
        ".claude/hooks/gate-sweep-sessionstart.sh",
        ".claude/evals/test_gate_in_progress.sh",
        ".claude/proposals/deep-read-marker-gate.md",
        ".claude/notes/stop-gate-per-turn-2026-09-27.md"
      ]
    },
    {
      "id": "judge",
      "zone": "rigor",
      "name": "Build-quality judge",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "summary": "/judge-build — three seats (Sonnet voting, Gemini advisory, OpenAI shadow) score the same evidence bundle against rubric build-quality@5; a merge escalates any split to Alex.",
      "why": {
        "text": "Quality had to become a measurable signal, not a vibe, and not a model rating its own family's work. Trust is earned per seat from calibration numbers: Gemini turned out to rubber-stamp (its '83% agreement' was the always-pass baseline, κ 0.14) and was demoted to advisory. The judge is a guard, not a proof — it enforces format and surfaces disagreement — and it is now heavier per build than the builds it grades, which is the next thing to fix.",
        "source": ".claude/references/cross-provider-judge.md; memory 2026-09-19 judge seats + calibration; memory 2026-09-20 null-baseline metric class; Linear YED-231"
      },
      "build": {
        "refs": [
          "YED-89",
          "YED-109",
          "YED-206",
          "YED-209",
          "YED-231"
        ],
        "note": "Rubric @1 (2026-06) → @3 (2026-07-17, calibration gate crossed) → @5 (2026-09-19, earned 1.0 + spec-drift cap)."
      },
      "tools": [
        "Sonnet (Agent tool)",
        "Gemini API",
        "OpenAI API"
      ],
      "files": [
        ".claude/commands/judge-build.md",
        ".claude/skills/judge-build/**",
        ".claude/evals/judge_lib.py",
        ".claude/evals/quorum_merge.py",
        ".claude/evals/calibration_stats.py",
        ".claude/evals/rubrics/**",
        ".claude/evals/prompts/**",
        ".claude/hooks/gemini-judge.sh",
        ".claude/hooks/openai-judge.sh",
        ".claude/hooks/openai_judge.py",
        ".claude/hooks/seat-log.py",
        ".claude/hooks/quorum-merge.sh",
        ".claude/hooks/check-refs.sh",
        ".claude/hooks/check-tombstones.py",
        ".claude/hooks/density-check.sh",
        ".claude/references/cross-provider-judge.md",
        ".claude/proposals/third-judge-seat-openai.md",
        ".claude/evals/README.md",
        ".claude/evals/emit-judge-runs.sh",
        ".claude/evals/test_judge_lib.py",
        ".claude/evals/test_quorum_nseat.py",
        ".claude/evals/test_quorum_scenarios.py",
        ".claude/evals/test_adapter_contract.py",
        ".claude/evals/test_null_baseline.py",
        ".claude/evals/controls.py",
        ".claude/evals/controls/**",
        ".claude/notes/gemini-judge-triage-2026-09-19.md"
      ]
    },
    {
      "id": "telemetry",
      "zone": "rigor",
      "name": "Build-session telemetry",
      "kind": "hook",
      "reviewed_at": "2026-09-27",
      "summary": "A Stop hook that records each build session — files touched, DoD fields, correction rounds — to a per-session shard and projects it to PostHog.",
      "why": {
        "text": "The north-star is acted-on value, trended; that needs every build to leave a trace without anyone remembering to write one. Shards are per session so two sessions can never conflict on one file. The cost showed up later: per-turn churn in tracked files blocks every branch switch, which is why the shards are moving out of git (YED-229).",
        "source": ".claude/references/build-session-contract.md; memory 2026-09-27 systems-gaps decision"
      },
      "build": {
        "refs": [
          "YED-88",
          "YED-229"
        ]
      },
      "tools": [
        "PostHog capture"
      ],
      "files": [
        ".claude/hooks/build-session-emit.sh",
        ".claude/references/build-session-contract.md",
        ".claude/hooks/runtime_ledgers.py",
        ".claude/hooks/v2-cmd-detect.sh",
        ".claude/hooks/v2-trigger-detect.sh",
        ".claude/hooks/v2-trigger-log.sh"
      ]
    },
    {
      "id": "rigor-review",
      "zone": "rigor",
      "name": "/rigor-review + outcome capture",
      "kind": "command",
      "reviewed_at": "2026-09-27",
      "summary": "The weekly ≤10-minute learning loop over telemetry, judge logs and waivers, plus /tag-outcome, which records what each artifact actually did against its goal.",
      "why": {
        "text": "Measurement without an action is an orphan metric, so every metric in the value-action registry has a threshold, an action and a surface. The weekly review recounts what the in-session gates cannot verify (for example whether a promised make-up judge run happened) and proposes codified fixes; outcome tagging closes the loop from a draft's goal to its realized value, which is the only number that matters.",
        "source": ".claude/references/value-action-registry.md; .claude/evals/correction-recurrence.md; .claude/skills/content-patterns/goal-tagging.md"
      },
      "build": {
        "refs": [
          "YED-93",
          "YED-94",
          "YED-162",
          "YED-212"
        ]
      },
      "tools": [
        "Notion MCP"
      ],
      "files": [
        ".claude/commands/rigor-review.md",
        ".claude/skills/rigor-review/**",
        ".claude/commands/tag-outcome.md",
        ".claude/skills/tag-outcome/**",
        ".claude/references/value-action-registry.md",
        ".claude/evals/correction-recurrence.md",
        ".claude/skills/content-patterns/goal-tagging.md",
        ".claude/notes/rigor-loop-session-resume-2026-07-16.md"
      ]
    },
    {
      "id": "system-graph",
      "zone": "rigor",
      "name": "System graph (ADR-8)",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "summary": "A derived graph over the repo's own build artifacts — every skill, command, agent, hook, ADR and note as a node, every load-bearing reference as an edge — rebuilt at session start. It is the source of this map's file layer.",
      "why": {
        "text": "Drift detection needs a substrate: when a reference points at a file that no longer exists, or a plan names a script that was never written, that should be mechanical fact surfaced at session start, not something a reviewer happens to notice. The graph is derived and gitignored — never hand-edited — so it cannot itself drift from the repo.",
        "source": "docs/adr/ADR-8-system-graph-drift-router.md; .claude/scripts/build_graph.py"
      },
      "build": {
        "refs": [
          "YED-163"
        ],
        "note": "Increment 1 live; Increment 2 (skills ↔ agents ↔ commands ↔ outcomes) is roadmap P3."
      },
      "files": [
        ".claude/scripts/build_graph.py",
        ".claude/hooks/graph-sessionstart.sh",
        ".claude/hooks/graph-stop.sh",
        ".claude/hooks/run-canaries.sh",
        "docs/adr/ADR-8-system-graph-drift-router.md",
        ".claude/evals/test_canary_gate.py"
      ]
    },
    {
      "id": "systems-thinking",
      "zone": "rigor",
      "name": "Systems-thinking harness",
      "kind": "skill",
      "reviewed_at": "2026-09-27",
      "summary": "An eight-phase Meadows-style diagnostic (stocks, flows, loops, archetypes, leverage points) as a skill and a delegated analyst agent.",
      "why": {
        "text": "Chronic problems in a solo build are usually loops, not bugs: the execution-focus rule that first raised publishing and then drained it, the rigor that lived in optional docs. The harness makes 'why does this keep happening' a repeatable analysis with a rule-out discipline (name the archetypes rejected, not just the one matched), and it produced the diagnosis behind the Definition of Done.",
        "source": "CLAUDE.md § Systems-thinking harness (2026-05-04); .claude/skills/systems-thinking/SKILL.md"
      },
      "build": {
        "refs": [
          "YED-23",
          "YED-24",
          "YED-25"
        ]
      },
      "files": [
        ".claude/skills/systems-thinking/**",
        ".claude/agents/ops/systems-analyst.md",
        ".claude/commands/systems-analyze.md",
        ".claude/references/systems-thinking-workflow.md",
        ".claude/skills/risk-playbooks/**",
        ".claude/skills/head-of-product-engineering/**",
        ".claude/skills/ai-product-strategy/**",
        ".claude/skills/defining-product-vision/**",
        ".claude/skills/launch-tiering/**",
        ".claude/skills/prioritizing-roadmap/**",
        ".claude/skills/shipping-products/**",
        ".claude/skills/writing-north-star-metrics/**"
      ]
    },
    {
      "id": "operating-rules",
      "zone": "rigor",
      "name": "Operating rules",
      "kind": "policy",
      "reviewed_at": "2026-09-27",
      "summary": "The project instructions, the workflow manual, the platform-constraints registry, the git conventions and the build-in-public policy.",
      "why": {
        "text": "A memory-less agent needs its invariants where it will read them: which MCP account is which, what a subagent cannot do, why two sessions must never share a checkout, what may be public. Constraints have one home (platform-constraints.md) with memory files carrying pointers, and the reconciliation of branches is a role one session plays, not a habit everyone half-keeps.",
        "source": "CLAUDE.md; .claude/references/platform-constraints.md; .claude/references/reconciliation-terminal-charter.md; policy build-in-public"
      },
      "build": {
        "refs": [
          "YED-30",
          "YED-204"
        ]
      },
      "files": [
        "CLAUDE.md",
        ".claude/WORKFLOWS.md",
        ".claude/references/platform-constraints.md",
        ".claude/references/reconciliation-terminal-charter.md",
        ".claude/references/command-orchestration-convention.md",
        ".claude/references/roadmap.md",
        ".claude/commands/toolbox.md",
        ".claude/references/build-in-public.md",
        ".claude/references/hook-schema-reference.md",
        ".claude/references/pipeline-operations-guide.md",
        ".claude/references/stack-readme.md",
        ".claude/proposals/empire-state-agentic-architecture-2026-05-15.md",
        ".claude/proposals/yed-30-step-5-empire-state-backport.md",
        ".claude/notes/execution-week-frictions.md",
        ".claude/notes/state-reconciliation-2026-09-12.md",
        ".claude/notes/open-items-inventory-2026-09-13.md",
        ".claude/notes/backlog-triage-2026-09-18.md"
      ]
    },
    {
      "id": "hub",
      "zone": "surfaces",
      "name": "Empire State Hub",
      "kind": "surface",
      "reviewed_at": "2026-09-27",
      "summary": "This site: a public build-in-public surface with two lenses (editorial and technical) and a private /ops dashboard over Notion, Linear, PostHog and the graph.",
      "why": {
        "text": "Read-only, honesty-first, PII-safe by mechanical check. It exists to be the interview artifact — the place a hiring manager sees the system and the reasoning, not a résumé line — and to make the pipeline's own state visible to its builder. The repos are public by design; personal files are gitignored and a check fails the build on any contact-PII field.",
        "source": "Linear project Empire State Hub; scripts/verify-public-safe.mjs; memory 2026-09-16 public repos, private data"
      },
      "build": {
        "refs": [
          "YED-82",
          "YED-114",
          "YED-232"
        ]
      },
      "tools": [
        "Next.js",
        "Tailwind",
        "React Flow",
        "@linear/sdk",
        "@notionhq/client",
        "Vercel"
      ],
      "files": []
    },
    {
      "id": "build-journal",
      "zone": "surfaces",
      "name": "Build journal & arcs",
      "kind": "script",
      "reviewed_at": "2026-09-27",
      "summary": "A generator that turns git history and build sessions into the Hub's /journal and /build-arcs, with a hand-written prose sidecar at break points.",
      "why": {
        "text": "The facts of the build should instrument themselves (YED-119) so the journal never depends on remembering to write; the prose — what a shipped PR meant — is a deliberate human-authored layer added at each break point, and its lapses are tracked as data.",
        "source": "memory: public build journal at break points; .claude/scripts/build_journal.py"
      },
      "build": {
        "refs": [
          "YED-119"
        ]
      },
      "files": [
        ".claude/scripts/build_journal.py",
        ".claude/scripts/gen_build_arcs_artifact.py",
        ".claude/hooks/build-journal-refresh.sh",
        ".claude/commands/journal-entry.md",
        ".claude/references/journal-entry-prompt.md"
      ]
    },
    {
      "id": "linkedin",
      "zone": "surfaces",
      "name": "LinkedIn (manual publish)",
      "kind": "external",
      "reviewed_at": "2026-09-27",
      "summary": "Where the content actually ships. Publishing is deliberately manual — Tier 3, never started unprompted.",
      "why": {
        "text": "Outward-facing and irreversible actions are Alex's call: the pipeline drafts every variant, Alex picks, edits in Notion and posts. The goal is not volume but hiring-manager activation traceable to a post, which is what the outcome tags measure.",
        "source": "CLAUDE.md § invocation tiers (Tier 3); .claude/references/audience-north-star.md"
      },
      "build": {
        "refs": [
          "YED-178"
        ]
      },
      "files": []
    }
  ],
  "edges": [
    {
      "source": "check-new-events",
      "target": "calendar",
      "kind": "reads",
      "summary": "Lists upcoming events on the Going-to-Events calendar and parses each description (PIPELINE block or raw text)."
    },
    {
      "source": "check-new-events",
      "target": "event-deep-research",
      "kind": "dispatches",
      "summary": "Runs the research pipeline per detected event, with a continue-or-quit gate between events."
    },
    {
      "source": "check-new-events",
      "target": "pre-event-content",
      "kind": "dispatches",
      "summary": "After research, generates the pre-event post, notes and questions for the same event."
    },
    {
      "source": "event-claim",
      "target": "event-deep-research",
      "kind": "gates",
      "summary": "Step 1.0 claims the event before any parsing; a held claim sends the run read-only."
    },
    {
      "source": "event-claim",
      "target": "post-event-content",
      "kind": "gates",
      "summary": "Same claim discipline for the post-event run."
    },
    {
      "source": "run-gates",
      "target": "event-claim",
      "kind": "reads",
      "summary": "The gates read the live claim to tell 'in progress' from 'abandoned' — pending rows are not failures while the claim is live."
    },
    {
      "source": "run-gates",
      "target": "event-deep-research",
      "kind": "gates",
      "summary": "Deep Read ledger + substrate gate: the run cannot close green with a Deep Read unrendered or claims unstaged."
    },
    {
      "source": "run-gates",
      "target": "post-event-content",
      "kind": "gates",
      "summary": "Substrate gate holds the post-event run until the attended row and claims are written."
    },
    {
      "source": "event-deep-research",
      "target": "notion",
      "kind": "writes",
      "summary": "Dependency-ordered writes: Companies → Topics → People → Event → research_brief Content Draft (+ prior-context pack)."
    },
    {
      "source": "event-deep-research",
      "target": "hubspot",
      "kind": "writes",
      "summary": "Companies, Contacts with associations, and an event Note per contact — after Alex approves the confirmation table."
    },
    {
      "source": "event-deep-research",
      "target": "gmail",
      "kind": "reads",
      "summary": "Step 1.7 prior-knowledge pull: correspondence and recent newsletters about the entities."
    },
    {
      "source": "event-deep-research",
      "target": "retrieve",
      "kind": "reads",
      "summary": "Step 1.7a-S: the event-lens Context Pack (prior occasions, returning faces, scored claims)."
    },
    {
      "source": "event-deep-research",
      "target": "substrate",
      "kind": "writes",
      "summary": "Step 4.2: one claim per Evidence Ledger row, plus the researched entities and the brief as a document — never an event row (not attended yet)."
    },
    {
      "source": "pre-event-content",
      "target": "notion",
      "kind": "reads",
      "summary": "Reads the research brief, the Author Steer block and the verification flags."
    },
    {
      "source": "pre-event-content",
      "target": "notion",
      "kind": "writes",
      "summary": "Writes every variant as a Content Draft, in plain paragraphs, for inline comment review."
    },
    {
      "source": "pre-event-content",
      "target": "voice-system",
      "kind": "depends-on",
      "summary": "Style guide, anti-patterns and the visual-brief spec are read before any generation."
    },
    {
      "source": "post-event-content",
      "target": "voice-system",
      "kind": "depends-on",
      "summary": "Same guides, plus the founder-showcase pattern and the pre→post arc rule."
    },
    {
      "source": "post-event-content",
      "target": "notion",
      "kind": "reads",
      "summary": "Resolves the Event row (calendar-ID match, then fuzzy title+date) and the pre-event brief."
    },
    {
      "source": "post-event-content",
      "target": "notion",
      "kind": "writes",
      "summary": "post_event_brief + the Tier 1/Tier 2 drafts + outreach DMs as Content Drafts."
    },
    {
      "source": "post-event-content",
      "target": "hubspot",
      "kind": "writes",
      "summary": "Contacts met and follow-up Notes — after approval."
    },
    {
      "source": "post-event-content",
      "target": "substrate",
      "kind": "writes",
      "summary": "Step 3.8b: creates the attended event row and attaches the pre-event claims to it (ADR-10 D9)."
    },
    {
      "source": "pre-event-content",
      "target": "linkedin",
      "kind": "produces",
      "summary": "The per-event post and Sunday roundup, published by Alex by hand."
    },
    {
      "source": "post-event-content",
      "target": "linkedin",
      "kind": "produces",
      "summary": "The recap that cashes the pre-event setup against what was said."
    },
    {
      "source": "scaffolded-workflows",
      "target": "voice-system",
      "kind": "depends-on",
      "summary": "The voice pass would run voice-editor over needs_review drafts against the guide."
    },
    {
      "source": "gtm-suite",
      "target": "voice-system",
      "kind": "depends-on",
      "summary": "Copy commands inherit the same voice rules."
    },
    {
      "source": "interview-prep",
      "target": "retrieve",
      "kind": "reads",
      "summary": "Planned: the interview lens (YED-207). Today the dossier is built from the specialist fan-out without a Context Pack.",
      "status": "planned"
    },
    {
      "source": "interview-prep",
      "target": "spine-client",
      "kind": "writes",
      "summary": "Judge-gated dossier written to the Postgres spine and Notion."
    },
    {
      "source": "judge",
      "target": "interview-prep",
      "kind": "gates",
      "summary": "The dossier passes the judge before it is written."
    },
    {
      "source": "signal-scanners",
      "target": "notion",
      "kind": "writes",
      "summary": "Digest approved → Topics' Current Events notes and radar pages."
    },
    {
      "source": "signal-scanners",
      "target": "spine-client",
      "kind": "writes",
      "summary": "The trend producer writes market signals to the graph (roles producer is P1, YED-149)."
    },
    {
      "source": "inbox-miner",
      "target": "gmail",
      "kind": "reads",
      "summary": "Allowlisted senders, newer than the last run; denylist enforced before anything is read as signal."
    },
    {
      "source": "inbox-miner",
      "target": "gmail",
      "kind": "writes",
      "summary": "Labels processed threads (the only Gmail write scope granted)."
    },
    {
      "source": "inbox-miner",
      "target": "spine-client",
      "kind": "writes",
      "summary": "Email signals, canonical-URL deduped, through the PII guard."
    },
    {
      "source": "doc-knowledge-base",
      "target": "supabase-graph",
      "kind": "writes",
      "summary": "Ingested documents become document rows; digests into the pipelines are the unbuilt half.",
      "status": "planned"
    },
    {
      "source": "substrate",
      "target": "spine-client",
      "kind": "depends-on",
      "summary": "All substrate writes go through the one guarded client."
    },
    {
      "source": "spine-client",
      "target": "supabase-graph",
      "kind": "writes",
      "summary": "REST upserts with a scoped key; bounded retry on transient network errors; hard-fail on contact PII."
    },
    {
      "source": "retrieve",
      "target": "supabase-graph",
      "kind": "reads",
      "summary": "Events, roster, claims and signals for the seed entities, under a token budget."
    },
    {
      "source": "topic-intelligence",
      "target": "supabase-graph",
      "kind": "reads",
      "summary": "Reads signals and claims to score relevance and topic movement."
    },
    {
      "source": "topic-intelligence",
      "target": "supabase-graph",
      "kind": "writes",
      "summary": "Writes topic_intelligence tables — not since 2026-08-10 (YED-230).",
      "status": "stale"
    },
    {
      "source": "hub",
      "target": "supabase-graph",
      "kind": "reads",
      "summary": "/ops/market-intel reads topic movement and the trust strip."
    },
    {
      "source": "hub",
      "target": "notion",
      "kind": "reads",
      "summary": "/ops/content and /ops/events read Content Drafts and Events read-only."
    },
    {
      "source": "hub",
      "target": "linear",
      "kind": "reads",
      "summary": "/ops/backlog and this map's build path read open issues live."
    },
    {
      "source": "hub",
      "target": "posthog",
      "kind": "reads",
      "summary": "/ops/rigor reads build_session and judge_run events."
    },
    {
      "source": "hub",
      "target": "operating-rules",
      "kind": "depends-on",
      "summary": "The build-in-public policy governs what the hub may show; verify-public-safe enforces the PII tier."
    },
    {
      "source": "system-graph",
      "target": "hub",
      "kind": "produces",
      "summary": "The file layer of this map is generated from the ADR-8 nodes and edges."
    },
    {
      "source": "build-journal",
      "target": "hub",
      "kind": "produces",
      "summary": "build-journal.json and build-arcs.json are generated into the hub's data folder."
    },
    {
      "source": "build-journal",
      "target": "telemetry",
      "kind": "reads",
      "summary": "Reads build-session shards alongside git history to reconstruct each day."
    },
    {
      "source": "telemetry",
      "target": "posthog",
      "kind": "writes",
      "summary": "Each build_session row is captured on Stop."
    },
    {
      "source": "judge",
      "target": "posthog",
      "kind": "writes",
      "summary": "Each judge_run is captured for the rigor dashboard."
    },
    {
      "source": "dod-gate",
      "target": "telemetry",
      "kind": "writes",
      "summary": "/dod-close records dod_met / dod_waived / correction_rounds, which the Stop hook folds into the session row."
    },
    {
      "source": "dod-gate",
      "target": "judge",
      "kind": "depends-on",
      "summary": "Item 4: the judge ran on this build in this session, or the waiver names the make-up issue."
    },
    {
      "source": "dod-gate",
      "target": "linear",
      "kind": "depends-on",
      "summary": "Item 2: a Linear issue opened or updated for the workstream."
    },
    {
      "source": "systems-thinking",
      "target": "dod-gate",
      "kind": "produces",
      "summary": "The DoD gate came out of a systems-analyst diagnosis (Shifting the Burden)."
    },
    {
      "source": "rigor-review",
      "target": "telemetry",
      "kind": "reads",
      "summary": "Build sessions, waivers and gate-failure ledgers, weekly."
    },
    {
      "source": "rigor-review",
      "target": "judge",
      "kind": "reads",
      "summary": "Judge logs, seat calibration and ack latency."
    },
    {
      "source": "rigor-review",
      "target": "notion",
      "kind": "writes",
      "summary": "/tag-outcome writes Outcome / Outcome Value / Outcome Date on Content Drafts."
    },
    {
      "source": "system-graph",
      "target": "operating-rules",
      "kind": "reads",
      "summary": "Walks the repo's own artifacts and references; surfaces dangling references at session start."
    },
    {
      "source": "dod-gate",
      "target": "operating-rules",
      "kind": "depends-on",
      "summary": "The gate's scope test and waiver rules live in the project instructions."
    }
  ],
  "buildPath": {
    "$note": "Planned work attached to the components it extends. `phase` and anchor dates come from roadmap.md (parsed by the generator); title, state and priority come from Linear at build time. If Linear is unreachable the page shows the roadmap phase and says the state is unknown.",
    "items": [
      {
        "issue": "YED-229",
        "extends": [
          "telemetry"
        ],
        "why": "Per-turn telemetry churn in tracked files blocks every branch switch — move shards out of git, commit a rollup."
      },
      {
        "issue": "YED-231",
        "extends": [
          "judge"
        ],
        "why": "Right-size the judge: diff bundles so multi-file builds keep their voting seat; one voting seat; shadows silent; ack only on real escalation."
      },
      {
        "issue": "YED-230",
        "extends": [
          "topic-intelligence"
        ],
        "why": "Wire the nightly recompute so the intelligence layer cannot silently freeze again."
      },
      {
        "issue": "YED-157",
        "extends": [
          "doc-knowledge-base"
        ],
        "why": "/doc-digest + consumer wiring — where the document KB earns its keep (roadmap P1)."
      },
      {
        "issue": "YED-149",
        "extends": [
          "signal-scanners",
          "supabase-graph"
        ],
        "why": "Roles → spine producer; the job-search lens becomes graph-native (P1)."
      },
      {
        "issue": "YED-131",
        "extends": [
          "topic-intelligence"
        ],
        "why": "Nightly topic recompute on pg_cron, no LLM tokens (P1)."
      },
      {
        "issue": "YED-207",
        "extends": [
          "retrieve",
          "interview-prep"
        ],
        "why": "The interview lens: /interview-prep reads the substrate through retrieve.py."
      },
      {
        "issue": "YED-208",
        "extends": [
          "retrieve",
          "pre-event-content",
          "post-event-content"
        ],
        "why": "The content lens: drafts pull prior claims and Alex's own posts on the theme."
      },
      {
        "issue": "YED-217",
        "extends": [
          "substrate",
          "event-deep-research"
        ],
        "why": "Merge the substrate's material into the legacy packaging (the A/B verdict)."
      },
      {
        "issue": "YED-126",
        "extends": [
          "supabase-graph",
          "hub"
        ],
        "why": "The architecture lens: an Applied-AI reference architecture as taxonomy v2 + hub surface (P2). A different map from this one — it maps the industry."
      },
      {
        "issue": "YED-114",
        "extends": [
          "hub",
          "topic-intelligence"
        ],
        "why": "Topic-intelligence panels on the hub — the map needs a face (P2)."
      },
      {
        "issue": "YED-104",
        "extends": [
          "pre-event-content"
        ],
        "why": "Audience / conversation intelligence at draft time — content becomes the graph's first reader (P2)."
      },
      {
        "issue": "YED-226",
        "extends": [
          "substrate"
        ],
        "why": "Identity tier-1 in DDL — the parked half of entity dedup (P2)."
      },
      {
        "issue": "YED-48",
        "extends": [
          "judge",
          "event-deep-research"
        ],
        "why": "Eval harness for event research: 10 golden briefs + judge (P3)."
      },
      {
        "issue": "YED-162",
        "extends": [
          "rigor-review",
          "judge"
        ],
        "why": "The behavioral-exhaust loop: correction recurrence → proposed fix as a PR → judge-gated → Alex merges (P3)."
      },
      {
        "issue": "YED-163",
        "extends": [
          "system-graph"
        ],
        "why": "ADR-8 Increment 2: skills ↔ agents ↔ commands ↔ outcomes on the system graph (P3)."
      },
      {
        "issue": "YED-82",
        "extends": [
          "hub"
        ],
        "why": "Hub craft, honesty and launch — polished after the quarter's proof exists (P3)."
      }
    ]
  }
}

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): scripts/gen-system-map.mjs
#!/usr/bin/env node
// gen-system-map.mjs — build src/data/system-map.json (+ system-map.files.json) for the public
// /architecture map. Facts come from the pipeline repo (frontmatter, the ADR-8 system graph, git
// dates, roadmap.md); judgement comes from src/data/system-map.curated.json and is preserved as-is
// (merge-don't-clobber, same rule as gen-toolbox). PRD: docs/system-map.prd.md (YED-232).
//
// Run: pnpm gen:system-map            (PIPELINE_DIR=/path/to/pipeline to override the sibling default)
// Prints: components + files resolved · patterns matching nothing · unmapped files · overlay entries
// whose files changed after `reviewed_at` (the rot signal — review them, then bump the date).
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const HUB = join(dirname(fileURLToPath(import.meta.url)), "..");
const PIPELINE_DIR = process.env.PIPELINE_DIR || join(HUB, "..", "Empire_State_Events_Pipeline_Take_3");
const GRAPH_DIR = join(PIPELINE_DIR, ".claude", ".state", "system-graph");
const CURATED = join(HUB, "src", "data", "system-map.curated.json");
const OUT = join(HUB, "src", "data", "system-map.json");
const OUT_FILES = join(HUB, "src", "data", "system-map.files.json");
const REPO_URL = "https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/blob/main/";
const LINEAR_URL = "https://linear.app/yedibalian/issue/";

// ---------- small helpers ----------
const readJsonl = (p) =>
  readFileSync(p, "utf8")
    .split("\n")
    .filter(Boolean)
    .map((l) => JSON.parse(l));

function frontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  return m ? m[1] : "";
}
// Same scanner gen-toolbox uses (folded / block / wrapped scalars).
function field(block, key) {
  const lines = block.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(new RegExp(`^${key}:\\s*(.*)$`));
    if (!m) continue;
    const v = m[1].trim();
    const parts = ["", ">", "|", ">-", "|-"].includes(v) ? [] : [v.replace(/^["']|["']$/g, "")];
    for (let j = i + 1; j < lines.length; j++) {
      if (/^[A-Za-z_-]+:/.test(lines[j])) break;
      if (lines[j].trim()) parts.push(lines[j].trim());
    }
    return parts.join(" ").trim();
  }
  return "";
}
const collapse = (s) => s.replace(/\s+/g, " ").trim();
const firstSentence = (s, max = 220) => {
  const t = collapse(s);
  const m = t.match(/^.*?[.!?](\s|$)/);
  const out = m ? m[0].trim() : t;
  return out.length > max ? out.slice(0, max - 1) + "…" : out;
};

// What a file says it is, from its own header — never invented.
function describeFile(rel) {
  const p = join(PIPELINE_DIR, rel);
  if (!existsSync(p)) return "";
  const text = readFileSync(p, "utf8");
  if (rel.endsWith(".md")) {
    const fm = frontmatter(text);
    const d = field(fm, "description");
    if (d) return firstSentence(d);
    const title = text.split("\n").find((l) => l.startsWith("# "));
    return title ? title.replace(/^#\s*/, "").trim() : "";
  }
  if (rel.endsWith(".py")) {
    const m = text.match(/"""([\s\S]*?)"""/);
    return m ? firstSentence(m[1]) : "";
  }
  if (rel.endsWith(".sh")) {
    const lines = text.split("\n").slice(1, 6).filter((l) => /^#\s*\S/.test(l));
    return lines.length ? firstSentence(lines.map((l) => l.replace(/^#\s?/, "")).join(" ")) : "";
  }
  if (rel.endsWith(".json")) return "";
  return "";
}

// MCP servers / models an artifact declares. Hashed server ids (a connector's uuid) are Notion.
const MCP_NAMES = {
  notion: "Notion MCP",
  claude_ai_Gmail: "Gmail MCP",
  claude_ai_HubSpot: "HubSpot MCP",
  claude_ai_Google_Calendar: "Google Calendar MCP",
  claude_ai_Supabase: "Supabase MCP",
  claude_ai_Granola: "Granola MCP",
  claude_ai_PostHog: "PostHog MCP",
  claude_ai_ChatPRD: "ChatPRD MCP",
  linear: "Linear MCP",
};
const MODEL_NAMES = { opus: "Opus", sonnet: "Sonnet", haiku: "Haiku" };
function toolsOf(rel) {
  const p = join(PIPELINE_DIR, rel);
  if (!existsSync(p) || !rel.endsWith(".md")) return [];
  const text = readFileSync(p, "utf8");
  const out = new Set();
  for (const m of text.matchAll(/mcp__([A-Za-z0-9_-]+?)__/g)) {
    const key = m[1];
    if (/^[0-9a-f]{8}-/.test(key)) out.add("Notion MCP");
    else if (MCP_NAMES[key]) out.add(MCP_NAMES[key]);
    else out.add(`${key} MCP`);
  }
  const fm = frontmatter(text);
  const tools = field(fm, "tools");
  if (/\bWebSearch\b/.test(tools)) out.add("WebSearch");
  if (/\bWebFetch\b/.test(tools)) out.add("WebFetch");
  const model = field(fm, "model").toLowerCase();
  if (MODEL_NAMES[model]) out.add(`${MODEL_NAMES[model]} (agent model)`);
  return [...out];
}

// ---------- git dates: one pass over history, per-file first/last touch ----------
function gitDates() {
  const first = new Map();
  const last = new Map();
  let sha = "unknown";
  try {
    sha = execFileSync("git", ["-C", PIPELINE_DIR, "rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim();
    const log = execFileSync(
      "git",
      ["-C", PIPELINE_DIR, "log", "--name-only", "--format=%x00%ad", "--date=short", "--no-renames"],
      { encoding: "utf8", maxBuffer: 256 * 1024 * 1024 },
    );
    let date = "";
    for (const line of log.split("\n")) {
      if (line.startsWith("\0")) {
        date = line.slice(1).trim();
        continue;
      }
      const f = line.trim();
      if (!f) continue;
      if (!last.has(f)) last.set(f, date); // log is newest-first
      first.set(f, date); // keeps overwriting → ends on the oldest
    }
  } catch (e) {
    console.error(`  ! git history unavailable (${e.message.split("\n")[0]}); dates will be null`);
  }
  return { first, last, sha };
}

// ---------- roadmap: phases (issue → phase) + anchors ----------
function roadmap() {
  const p = join(PIPELINE_DIR, ".claude", "references", "roadmap.md");
  const phases = [];
  const anchors = [];
  if (!existsSync(p)) return { phases, anchors, issuePhase: new Map() };
  const text = readFileSync(p, "utf8");
  let cur = null;
  let inAnchors = false;
  for (const line of text.split("\n")) {
    const ph = line.match(/^### (Phase \d+) — (.+?) ·? ?(P\d)? ?\((.*?)\)(?: → \*\*(A\d)\*\*)?/);
    if (ph) {
      cur = { id: ph[3] || ph[1].replace(" ", "").toLowerCase(), label: `${ph[1]} — ${ph[2]}`, window: ph[4], anchor: ph[5] || null, issues: [] };
      phases.push(cur);
      inAnchors = false;
      continue;
    }
    if (/^## 6\./.test(line)) {
      inAnchors = true;
      cur = null;
      continue;
    }
    if (/^## /.test(line)) {
      inAnchors = false;
      cur = null;
    }
    if (cur && line.startsWith("|")) {
      for (const m of line.matchAll(/YED-\d+/g)) if (!cur.issues.includes(m[0])) cur.issues.push(m[0]);
    }
    if (inAnchors) {
      const a = line.match(/^\| \*\*(A\d) · (.+?)\*\* \((M\d)\) \| (\d{4}-\d{2}-\d{2}) \| (.+?) \|/);
      if (a) anchors.push({ id: a[1], label: a[2], milestone: a[3], date: a[4], proof: a[5] });
    }
  }
  const issuePhase = new Map();
  for (const ph of phases) for (const i of ph.issues) if (!issuePhase.has(i)) issuePhase.set(i, ph.id);
  return { phases, anchors, issuePhase };
}

// ---------- hub routes (the hub component's "files" are its own pages) ----------
function hubRoutes() {
  const app = join(HUB, "src", "app");
  const out = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      if (statSync(p).isDirectory()) walk(p);
      else if (name === "page.tsx") {
        const route = dir.slice(app.length).replace(/\/\((public)\)/g, "") || "/";
        out.push(route);
      }
    }
  };
  if (existsSync(app)) walk(app);
  return out.sort();
}

// ---------- pattern → graph nodes ----------
function matcher(pattern) {
  if (pattern.endsWith("/**")) {
    const prefix = pattern.slice(0, -2);
    return (id) => id.startsWith(prefix);
  }
  return (id) => id === pattern;
}

function main() {
  if (!existsSync(join(GRAPH_DIR, "nodes.jsonl"))) {
    console.error(
      `✗ ADR-8 graph not found at ${GRAPH_DIR}\n  Run \`python3 .claude/scripts/build_graph.py\` in the pipeline repo (or set PIPELINE_DIR) and retry.`,
    );
    process.exit(1);
  }
  const curated = JSON.parse(readFileSync(CURATED, "utf8"));
  const nodes = readJsonl(join(GRAPH_DIR, "nodes.jsonl")).filter((n) => n.exists !== false);
  const edges = readJsonl(join(GRAPH_DIR, "edges.jsonl")).filter((e) => e.exists !== false);
  const meta = existsSync(join(GRAPH_DIR, "meta.json")) ? JSON.parse(readFileSync(join(GRAPH_DIR, "meta.json"), "utf8")) : {};
  const nodeIds = nodes.map((n) => n.id);
  const { first, last, sha } = gitDates();
  const rm = roadmap();

  const fileOwner = new Map(); // node id → component id (first match wins; curated order = priority)
  const emptyPatterns = [];
  const overlayStale = [];
  const warnings = [];

  const components = curated.components.map((c) => {
    const files = [];
    for (const pat of c.files ?? []) {
      const hit = nodeIds.filter(matcher(pat));
      if (!hit.length) emptyPatterns.push(`${c.id}: ${pat}`);
      for (const id of hit) {
        if (!files.includes(id)) files.push(id);
        if (!fileOwner.has(id)) fileOwner.set(id, c.id);
      }
    }
    const primary = files[0] ?? null;
    const description = c.summary || (primary ? describeFile(primary) : "");
    if (!description) warnings.push(`${c.id}: no summary and no describable primary file`);

    const tools = new Set(c.tools ?? []);
    for (const f of files) for (const t of toolsOf(f)) tools.add(t);

    const firsts = files.map((f) => first.get(f)).filter(Boolean).sort();
    const lasts = files.map((f) => last.get(f)).filter(Boolean).sort();
    const firstShipped = firsts[0] ?? null;
    const lastChanged = lasts[lasts.length - 1] ?? null;
    if (lastChanged && c.reviewed_at && lastChanged > c.reviewed_at) overlayStale.push(`${c.id} (changed ${lastChanged}, reviewed ${c.reviewed_at})`);

    const status = c.status?.value ?? "live";
    if (c.status && !c.status.reason) warnings.push(`${c.id}: status override without a reason`);
    if (!c.why?.text || !c.why?.source) warnings.push(`${c.id}: why.text / why.source missing`);

    const refs = (c.build?.refs ?? []).map((r) => ({ id: r, url: LINEAR_URL + r }));
    const adrs = files.filter((f) => f.startsWith("docs/adr/")).map((f) => ({ id: basename(f, ".md").replace(/^ADR-(\d+)-.*/, "ADR-$1"), url: REPO_URL + f }));

    return {
      id: c.id,
      zone: c.zone,
      name: c.name,
      kind: c.kind,
      status,
      statusReason: c.status?.reason ?? null,
      description,
      why: c.why,
      build: { firstShipped, lastChanged, refs, adrs, note: c.build?.note ?? null },
      tools: [...tools].sort(),
      files: c.id === "hub" ? hubRoutes().map((r) => `hub:${r}`) : files,
      fileCount: c.id === "hub" ? hubRoutes().length : files.length,
      reviewed_at: c.reviewed_at,
      overlayStale: overlayStale.some((s) => s.startsWith(c.id + " ")),
    };
  });

  // edges: validate endpoints, give each a stable id
  const ids = new Set(components.map((c) => c.id));
  const edgesOut = curated.edges.map((e, i) => {
    if (!ids.has(e.source) || !ids.has(e.target)) warnings.push(`edge ${i}: unknown endpoint ${e.source} → ${e.target}`);
    return { id: `${e.source}--${e.kind}--${e.target}`, ...e, status: e.status ?? "live" };
  });
  const seen = new Set();
  for (const e of edgesOut) {
    if (seen.has(e.id)) warnings.push(`duplicate edge id ${e.id}`);
    seen.add(e.id);
  }

  // build path: attach roadmap phase; Linear state is fetched live by the page
  const items = curated.buildPath.items.map((it) => {
    for (const x of it.extends) if (!ids.has(x)) warnings.push(`buildPath ${it.issue}: unknown component ${x}`);
    return { ...it, phase: rm.issuePhase.get(it.issue) ?? "now", url: LINEAR_URL + it.issue };
  });

  // file layer: every existing graph node, who owns it, what it says it is
  const unmapped = nodeIds.filter((id) => !fileOwner.has(id));
  const filesOut = {
    generated_note: "GENERATED by scripts/gen-system-map.mjs from the pipeline's ADR-8 system graph. Do not hand-edit.",
    nodes: nodes.map((n) => ({
      id: n.id,
      subtype: n.subtype,
      component: fileOwner.get(n.id) ?? null,
      description: describeFile(n.id),
      firstShipped: first.get(n.id) ?? null,
      lastChanged: last.get(n.id) ?? null,
      url: REPO_URL + n.id,
    })),
    edges: edges.map((e) => ({ src: e.src, dst: e.dst, line: e.evidence?.line ?? null })),
  };

  const out = {
    generated_note:
      "GENERATED by scripts/gen-system-map.mjs. Facts (descriptions, dates, tools, files) come from the pipeline repo; " +
      "judgement (why, status reasons, edges, build path) is preserved from system-map.curated.json — edit THAT file, then run `pnpm gen:system-map`.",
    generated_at: process.env.GEN_DATE || new Date().toISOString().slice(0, 10),
    source: { pipeline_sha: sha, graph_built_at: meta.built_at ?? null, graph_nodes: nodes.length, graph_edges: edges.length, unmapped_files: unmapped.length },
    zones: curated.zones,
    components,
    edges: edgesOut,
    buildPath: { phases: rm.phases.map(({ issues, ...p }) => ({ ...p, issueCount: issues.length })), anchors: rm.anchors, items },
    overlayStale: overlayStale.map((s) => s.split(" ")[0]),
  };
  writeFileSync(OUT, JSON.stringify(out, null, 2) + "\n");
  writeFileSync(OUT_FILES, JSON.stringify(filesOut) + "\n");

  // ---- report ----
  console.log(`✓ wrote src/data/system-map.json (${components.length} components · ${edgesOut.length} edges · ${items.length} planned) + system-map.files.json (${nodes.length} files · ${edges.length} references)`);
  console.log(`  pipeline ${sha} · graph built ${meta.built_at ?? "?"} · phases ${rm.phases.map((p) => p.id).join(",")} · anchors ${rm.anchors.map((a) => `${a.id}=${a.date}`).join(" ")}`);
  const byZone = {};
  for (const c of components) byZone[c.zone] = (byZone[c.zone] ?? 0) + 1;
  console.log(`  per zone: ${JSON.stringify(byZone)}`);
  if (emptyPatterns.length) console.log(`  ! ${emptyPatterns.length} pattern(s) match no graph node:\n    ${emptyPatterns.join("\n    ")}`);
  if (unmapped.length) console.log(`  ! ${unmapped.length} graph file(s) mapped to no component (shown in the 'unmapped' bucket): e.g. ${unmapped.slice(0, 6).join(", ")}${unmapped.length > 6 ? ", …" : ""}`);
  if (overlayStale.length) console.log(`  ! overlay STALE — files changed after reviewed_at (re-read the entry, then bump the date):\n    ${overlayStale.join("\n    ")}`);
  if (warnings.length) {
    console.log(`✗ ${warnings.length} problem(s):\n    ${warnings.join("\n    ")}`);
    process.exit(1);
  }
}

main();

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): scripts/verify-system-map.mjs
// verify-system-map — the map's honesty checks, mechanically (PRD docs/system-map.prd.md §5/§6).
// Fails on: an edge or build-path item naming a component that does not exist; a curated entry
// without a sourced "why"; a status override without a reason; a component outside the 25–35 band.
// Warns (does not fail) on overlay entries whose files changed after they were last reviewed — the
// rot signal the topic-intelligence incident taught us to surface, not hide.
// Run: node scripts/verify-system-map.mjs   (wired into `pnpm check`)
import { readFileSync } from "node:fs";

const ROOT = new URL("..", import.meta.url).pathname;
const map = JSON.parse(readFileSync(`${ROOT}src/data/system-map.json`, "utf8"));
const curated = JSON.parse(readFileSync(`${ROOT}src/data/system-map.curated.json`, "utf8"));

const problems = [];
const ids = new Set(map.components.map((c) => c.id));
const zones = new Set(map.zones.map((z) => z.id));
const curatedIds = new Set(curated.components.map((c) => c.id));

if (map.components.length < 25 || map.components.length > 35) problems.push(`component count ${map.components.length} outside the 25–35 band (AC1)`);
for (const c of map.components) {
  if (!zones.has(c.zone)) problems.push(`${c.id}: unknown zone ${c.zone}`);
  if (!curatedIds.has(c.id)) problems.push(`${c.id}: in the generated map but not in the overlay (regenerate)`);
  if (!c.why?.text || !c.why?.source) problems.push(`${c.id}: why.text / why.source missing`);
  if (c.status !== "live" && !c.statusReason) problems.push(`${c.id}: status ${c.status} without a reason`);
  if (!c.description) problems.push(`${c.id}: empty description`);
}
for (const c of curated.components) if (!ids.has(c.id)) problems.push(`${c.id}: in the overlay but missing from the generated map (regenerate)`);
for (const e of map.edges) if (!ids.has(e.source) || !ids.has(e.target)) problems.push(`edge ${e.id}: unknown endpoint`);
for (const it of map.buildPath.items) for (const x of it.extends) if (!ids.has(x)) problems.push(`${it.issue}: extends unknown component ${x}`);
if (!map.buildPath.anchors.length) problems.push("no anchors parsed from roadmap.md § 6");

const stale = map.components.filter((c) => c.overlayStale).map((c) => c.id);

if (problems.length) {
  console.log(`✗ verify-system-map: ${problems.length} problem(s)`);
  for (const p of problems) console.log("  " + p);
  process.exit(1);
}
console.log(`✓ verify-system-map: ${map.components.length} components · ${map.edges.length} edges · ${map.buildPath.items.length} planned · anchors ${map.buildPath.anchors.map((a) => a.id).join(",")}`);
if (stale.length) console.log(`  ! ${stale.length} curated entr${stale.length === 1 ? "y" : "ies"} may lag the code (files changed after reviewed_at): ${stale.join(", ")}`);

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): src/components/system-map/system-map.tsx
"use client";

import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Background, MarkerType, ReactFlow, ReactFlowProvider, useNodesInitialized, useReactFlow, type Edge, type Node } from "@xyflow/react";
import type { FilesGraph, LinearState, SystemMap } from "@/lib/system-map/schema";
import { FilesSchema } from "@/lib/system-map/schema";
import type { Lens } from "@/lib/lens";
import { SIZES, applyPositions, gridLayout, layout } from "./layout";
import { NODE_TYPES, type MapNode } from "./nodes";
import { Panel } from "./panel";
import { fileSubgraph, type MapEdgeData, type Selection } from "./model";

type Props = { map: SystemMap; linear: LinearState[] | null; lens: Lens };


/** Edge styling: kind → stroke. Colour is reserved for status; kinds differ by weight and dash. */
function edgeStyle(kind: MapEdgeData["kind"], status: string, active: boolean) {
  const base: React.CSSProperties = { strokeWidth: active ? 2.5 : 1.25, stroke: active ? "var(--accent)" : "var(--muted)", opacity: active ? 1 : 0.55 };
  if (kind === "depends-on" || kind === "references") base.strokeDasharray = "2 4";
  if (kind === "gates") base.strokeDasharray = "6 3";
  if (kind === "extends" || status === "planned") base.strokeDasharray = "4 4";
  if (status === "stale") base.stroke = active ? "var(--accent)" : "#d97706";
  return base;
}

export function SystemMapView(props: Props) {
  return (
    <ReactFlowProvider>
      <Inner {...props} />
    </ReactFlowProvider>
  );
}

function Inner({ map, linear, lens }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const { fitView } = useReactFlow();
  const nodesInitialized = useNodesInitialized();

  const linearById = useMemo(() => new Map((linear ?? []).map((l) => [l.identifier, l])), [linear]);
  const [selection, setSelectionState] = useState<Selection>(() => {
    const n = params.get("node");
    const e = params.get("edge");
    const p = params.get("planned");
    const f = params.get("file");
    return n ? { type: "node", id: n } : e ? { type: "edge", id: e } : p ? { type: "planned", id: p } : f ? { type: "file", id: f } : null;
  });
  const [focus, setFocus] = useState<string | null>(() => params.get("focus"));
  const [showPath, setShowPath] = useState<boolean>(() => params.get("path") !== "0");
  const [hiddenZones, setHiddenZones] = useState<Set<string>>(new Set());
  const [files, setFiles] = useState<FilesGraph | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [layoutKey, setLayoutKey] = useState<string>("");

  // Deep links (AC8): the URL mirrors selection + focus so a view can be shared.
  const setSelection = useCallback(
    (s: Selection) => {
      setSelectionState(s);
      const q = new URLSearchParams();
      if (s) q.set(s.type, s.id);
      if (focus) q.set("focus", focus);
      if (!showPath) q.set("path", "0");
      router.replace(q.size ? `${pathname}?${q}` : pathname, { scroll: false });
    },
    [focus, showPath, pathname, router],
  );
  useEffect(() => {
    const q = new URLSearchParams();
    if (selection) q.set(selection.type, selection.id);
    if (focus) q.set("focus", focus);
    if (!showPath) q.set("path", "0");
    router.replace(q.size ? `${pathname}?${q}` : pathname, { scroll: false });
    // selection is handled by setSelection; this syncs focus/path toggles
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focus, showPath]);

  // Layer 2 data loads only when first needed (AC9).
  useEffect(() => {
    if (!focus || files) return;
    import("@/data/system-map.files.json").then((m) => setFiles(FilesSchema.parse(m.default)));
  }, [focus, files]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (selection) setSelection(null);
        else if (focus) setFocus(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selection, focus, setSelection]);

  // ---- build the React Flow graph for the current mode, then lay it out ----
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const built = focus ? buildFocus(map, files, focus) : buildOverview(map, linearById, showPath, hiddenZones);
      if (!built) return;
      const pos = "grid" in built ? gridLayout(built.grid) : await layout(built.elk);
      if (cancelled) return;
      setNodes(applyPositions(built.nodes, pos));
      setEdges(built.edges);
      setLayoutKey(JSON.stringify([focus, showPath, [...hiddenZones], files !== null]));
      // React Flow measures the new nodes in a ResizeObserver callback; fit after two frames so the
      // bounds are real. The nodesInitialized effect below covers the slow path.
      requestAnimationFrame(() => requestAnimationFrame(() => { if (!cancelled) fitView({ padding: 0.08 }); }));
    })();
    return () => {
      cancelled = true;
    };
  }, [map, linearById, showPath, hiddenZones, focus, files, fitView]);

  // Fit once React Flow has measured the new node set (a fit before that lands on stale bounds).
  useEffect(() => {
    if (nodesInitialized) fitView({ padding: 0.08 });
  }, [nodesInitialized, layoutKey, fitView]);

  // Selection highlighting is applied on top of the laid-out graph so it never triggers a re-layout.
  const shownNodes = useMemo(() => {
    const selId = selection?.type === "node" || selection?.type === "planned" || selection?.type === "file" ? selection.id : null;
    const selEdge = selection?.type === "edge" ? map.edges.find((e) => e.id === selection.id) : null;
    const touched = new Set<string>();
    if (selId && !focus) for (const e of map.edges) if (e.source === selId || e.target === selId) {
        touched.add(e.source);
        touched.add(e.target);
      }
    if (selId && !focus) for (const it of map.buildPath.items) if (it.issue === selId) it.extends.forEach((x) => touched.add(x));
    return nodes.map((n) => {
      const isSel = n.id === selId || (selEdge ? n.id === selEdge.source || n.id === selEdge.target : false);
      const dim = !!selId && !focus && n.type === "component" && !isSel && !touched.has(n.id);
      return { ...n, selected: isSel, data: { ...n.data, dim } };
    });
  }, [nodes, selection, map, focus]);

  const shownEdges = useMemo(() => {
    const selId = selection?.type === "node" || selection?.type === "planned" || selection?.type === "file" ? selection.id : null;
    return edges.map((e) => {
      const d = e.data as MapEdgeData;
      const active = selection?.type === "edge" ? e.id === selection.id : !!selId && (e.source === selId || e.target === selId);
      return {
        ...e,
        selected: selection?.type === "edge" && e.id === selection.id,
        style: edgeStyle(d.kind, d.status, active),
        zIndex: active ? 10 : 0,
        label: active && selection?.type === "edge" ? d.kind : undefined,
        labelStyle: { fill: "var(--fg)", fontSize: 10, fontFamily: "var(--font-mono)" },
        labelBgStyle: { fill: "var(--surface)" },
        markerEnd: { type: MarkerType.ArrowClosed, color: active ? "var(--accent)" : "var(--muted)", width: 14, height: 14 },
      };
    });
  }, [edges, selection]);

  const onNodeClick = useCallback(
    (_: unknown, n: Node) => {
      if (n.type === "zone") return;
      if (n.type === "neighbor") {
        setFocus(n.id.replace(/^nb:/, "") === "unmapped" ? null : n.id.replace(/^nb:/, ""));
        setSelection({ type: "node", id: n.id.replace(/^nb:/, "") });
        return;
      }
      if (n.type === "planned") return setSelection({ type: "planned", id: n.id.replace(/^plan:/, "") });
      if (n.type === "file") return setSelection({ type: "file", id: n.id.replace(/^file:/, "") });
      setSelection({ type: "node", id: n.id });
    },
    [setSelection],
  );
  const onEdgeClick = useCallback(
    (_: unknown, e: Edge) => {
      if ((e.data as MapEdgeData).kind === "references" || (e.data as MapEdgeData).kind === "extends") return;
      setSelection({ type: "edge", id: e.id });
    },
    [setSelection],
  );

  const focused = focus ? map.components.find((c) => c.id === focus) : null;
  const laying = layoutKey !== JSON.stringify([focus, showPath, [...hiddenZones], files !== null]);

  return (
    <div className="relative h-[calc(100vh-4.5rem)] min-h-[720px] w-full overflow-hidden border-y border-border bg-bg">
      <ReactFlow
        nodes={shownNodes}
        edges={shownEdges}
        nodeTypes={NODE_TYPES}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={() => setSelection(null)}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        minZoom={0.25}
        maxZoom={2}
        fitView
        fitViewOptions={{ padding: 0.08 }}
        className="!bg-bg"
      >
        <Background gap={24} size={1} color="var(--border)" />
      </ReactFlow>

      {/* Controls + legend */}
      <div className="pointer-events-none absolute left-3 top-3 z-10 flex max-w-[calc(100%-1.5rem)] flex-wrap items-center gap-2 md:left-5 md:top-5">
        {focused ? (
          <button onClick={() => { setFocus(null); setSelection({ type: "node", id: focused.id }); }} className="pointer-events-auto rounded border border-border bg-surface px-2.5 py-1 font-mono text-[11px] text-fg hover:border-accent">
            ← map · files of <span className="text-accent">{focused.name}</span>
            {files === null && <span className="ml-2 text-muted">loading…</span>}
          </button>
        ) : (
          <>
            <button
              onClick={() => setShowPath((v) => !v)}
              className={`pointer-events-auto rounded border px-2.5 py-1 font-mono text-[11px] ${showPath ? "border-accent text-accent" : "border-border text-muted"} bg-surface hover:border-accent`}
            >
              build path {showPath ? "on" : "off"}
            </button>
            {map.zones.map((z) => (
              <button
                key={z.id}
                onClick={() =>
                  setHiddenZones((s) => {
                    const n = new Set(s);
                    if (n.has(z.id)) n.delete(z.id);
                    else n.add(z.id);
                    return n;
                  })
                }
                className={`pointer-events-auto hidden rounded border px-2 py-1 font-mono text-[10px] uppercase tracking-widest sm:inline ${hiddenZones.has(z.id) ? "border-border text-muted/60 line-through" : "border-border text-fg"} bg-surface hover:border-accent`}
                title={z.blurb}
              >
                {z.name}
              </button>
            ))}
          </>
        )}
        <button onClick={() => fitView({ padding: 0.08, duration: 300 })} className="pointer-events-auto rounded border border-border bg-surface px-2.5 py-1 font-mono text-[11px] text-muted hover:border-accent hover:text-fg">
          fit
        </button>
      </div>
      <Legend focus={!!focus} lens={lens} laying={laying} />

      <Panel
        map={map}
        files={files}
        linear={linearById}
        lens={lens}
        selection={selection}
        focus={focus}
        onSelect={setSelection}
        onFocus={(id) => {
          setFocus(id);
          if (id) setSelection({ type: "node", id });
        }}
        onClose={() => setSelection(null)}
      />
    </div>
  );
}

function Legend({ focus, lens, laying }: { focus: boolean; lens: Lens; laying: boolean }) {
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 z-10 hidden rounded border border-border bg-surface/90 px-3 py-2 font-mono text-[10px] text-muted backdrop-blur md:block">
      {laying ? (
        <span>laying out…</span>
      ) : focus ? (
        <span>files of one component · solid = reference between files · dotted box = another component these files reach · click any to open</span>
      ) : (
        <span>
          <i className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-500 align-middle" />live
          <i className="ml-3 mr-1 inline-block h-2 w-2 rounded-full bg-amber-500 align-middle" />stale
          <i className="ml-3 mr-1 inline-block h-2 w-2 rounded-full bg-zinc-400 align-middle" />scaffolded
          <span className="ml-3 border border-dashed border-accent px-1 text-accent">planned</span>
          {lens === "technical" && <span className="ml-3">· dashed edge = gate · dotted = depends-on · click a node or an edge</span>}
        </span>
      )}
    </div>
  );
}

// ---------- graph builders ----------

function buildOverview(map: SystemMap, linear: Map<string, LinearState>, showPath: boolean, hidden: Set<string>) {
  const visible = map.components.filter((c) => !hidden.has(c.zone));
  const visibleIds = new Set(visible.map((c) => c.id));
  const zoneCount = new Map<string, number>();
  for (const c of visible) zoneCount.set(c.zone, (zoneCount.get(c.zone) ?? 0) + 1);

  const nodes: MapNode[] = [];
  const items: { id: string; zone: string; w: number; h: number }[] = [];
  for (const z of map.zones) {
    if (hidden.has(z.id)) continue;
    nodes.push({ id: z.id, type: "zone", position: { x: 0, y: 0 }, data: { kind: "zone", id: z.id, name: z.name, count: zoneCount.get(z.id) ?? 0 }, selectable: false, draggable: false, zIndex: -1 });
  }
  const edges: Edge[] = map.edges
    .filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
    .map((e) => ({ id: e.id, source: e.source, target: e.target, type: "default", data: { kind: e.kind, summary: e.summary, status: e.status } satisfies MapEdgeData }));

  // planned items sit directly under the first visible component they extend
  const plannedByHome = new Map<string, typeof map.buildPath.items>();
  if (showPath) {
    for (const it of map.buildPath.items) {
      const st = linear.get(it.issue)?.stateType;
      if (st === "completed" || st === "canceled") continue; // shipped since the overlay was written
      const home = it.extends.find((x) => visibleIds.has(x));
      if (!home) continue;
      plannedByHome.set(home, [...(plannedByHome.get(home) ?? []), it]);
    }
  }
  for (const c of visible) {
    nodes.push({ id: c.id, type: "component", position: { x: 0, y: 0 }, parentId: c.zone, extent: "parent", data: { kind: "component", c }, style: { width: SIZES.component.w, height: SIZES.component.h } });
    items.push({ id: c.id, zone: c.zone, w: SIZES.component.w, h: SIZES.component.h });
    for (const it of plannedByHome.get(c.id) ?? []) {
      const id = `plan:${it.issue}`;
      nodes.push({ id, type: "planned", position: { x: 0, y: 0 }, parentId: c.zone, extent: "parent", data: { kind: "planned", item: it, linear: linear.get(it.issue) ?? null }, style: { width: SIZES.planned.w, height: SIZES.planned.h } });
      items.push({ id, zone: c.zone, w: SIZES.planned.w, h: SIZES.planned.h });
      for (const x of it.extends) {
        if (!visibleIds.has(x)) continue;
        edges.push({ id: `${x}--extends--${it.issue}`, source: x, target: id, type: "default", data: { kind: "extends", summary: it.why, status: "planned" } satisfies MapEdgeData });
      }
    }
  }
  const ROW: Record<string, 0 | 1> = { intake: 0, pipelines: 0, graph: 0, records: 0, rigor: 1, surfaces: 1 };
  const zones = map.zones.filter((z) => !hidden.has(z.id)).map((z) => ({ id: z.id, row: ROW[z.id] ?? (1 as const) }));
  return { nodes: nodes as Node[], edges, grid: { zones, items } };
}

function buildFocus(map: SystemMap, files: FilesGraph | null, componentId: string) {
  if (!files) return null;
  const c = map.components.find((x) => x.id === componentId);
  if (!c) return null;
  const { own, internal, neighbors } = fileSubgraph(files, map, componentId);
  const gid = `zone:${componentId}`;
  const nodes: MapNode[] = [{ id: gid, type: "zone", position: { x: 0, y: 0 }, data: { kind: "zone", id: gid, name: `${c.name} — files`, count: own.length }, selectable: false, draggable: false, zIndex: -1 }];
  const elkNodes: { id: string; parent: string | null; w: number; h: number }[] = [];
  for (const f of own) {
    const id = `file:${f.id}`;
    nodes.push({ id, type: "file", position: { x: 0, y: 0 }, parentId: gid, extent: "parent", data: { kind: "file", f }, style: { width: SIZES.file.w, height: SIZES.file.h } });
    elkNodes.push({ id, parent: gid, w: SIZES.file.w, h: SIZES.file.h });
  }
  const edges: Edge[] = internal.map((e, i) => ({ id: `ref:${i}`, source: `file:${e.src}`, target: `file:${e.dst}`, type: "default", data: { kind: "references", summary: "", status: "live", line: e.line } satisfies MapEdgeData }));
  const elkEdges = edges.map((e) => ({ id: e.id, source: e.source, target: e.target }));
  for (const n of neighbors.slice(0, 12)) {
    const id = `nb:${n.id}`;
    const nc = n.c ?? { ...c, id: "unmapped", name: "unmapped files", kind: "reference" as const, status: "live" as const };
    nodes.push({ id, type: "neighbor", position: { x: 0, y: 0 }, data: { kind: "neighbor", c: nc, refs: n.refs }, style: { width: SIZES.neighbor.w, height: SIZES.neighbor.h } });
    elkNodes.push({ id, parent: null, w: SIZES.neighbor.w, h: SIZES.neighbor.h });
    // one aggregated edge from the group to the neighbour keeps the picture readable
    const eid = `nbe:${n.id}`;
    edges.push({ id: eid, source: gid, target: id, type: "default", data: { kind: "references", summary: "", status: "live" } satisfies MapEdgeData });
    elkEdges.push({ id: eid, source: gid, target: id });
  }
  return { nodes: nodes as Node[], edges, elk: { groups: [{ id: gid, label: c.name }], nodes: elkNodes, edges: elkEdges, direction: "RIGHT" as const } };
}

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): src/components/system-map/panel.tsx
"use client";

import type { BuildItem, FilesGraph, LinearState, MapEdge, SystemMap } from "@/lib/system-map/schema";
import type { Lens } from "@/lib/lens";
import { EDGE_VERB, KIND_GLYPH, componentById, interactionsOf, plannedFor, type Selection } from "./model";
import { STATUS_DOT } from "./nodes";

type Props = {
  map: SystemMap;
  files: FilesGraph | null;
  linear: Map<string, LinearState>;
  lens: Lens;
  selection: Selection;
  focus: string | null;
  onSelect: (s: Selection) => void;
  onFocus: (componentId: string | null) => void;
  onClose: () => void;
};

const REPO = "https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/blob/main/";

/** The six-field panel (PRD AC2) for a component, or the kind + summary panel for an edge (AC3). */
export function Panel(p: Props) {
  const { selection } = p;
  if (!selection) return null;
  let body: React.ReactNode = null;
  if (selection.type === "node") body = <ComponentPanel {...p} id={selection.id} />;
  else if (selection.type === "edge") body = <EdgePanel {...p} id={selection.id} />;
  else if (selection.type === "planned") body = <PlannedPanel {...p} id={selection.id} />;
  else if (selection.type === "file") body = <FilePanel {...p} id={selection.id} />;
  if (!body) return null;
  return (
    <aside
      className="absolute inset-x-0 bottom-0 z-20 max-h-[58vh] overflow-y-auto border-t border-border bg-bg/95 backdrop-blur md:inset-y-0 md:left-auto md:right-0 md:max-h-none md:w-[400px] md:border-l md:border-t-0"
      aria-live="polite"
    >
      <button
        onClick={p.onClose}
        className="absolute right-3 top-3 rounded px-2 py-1 font-mono text-[11px] text-muted hover:bg-surface hover:text-fg"
        aria-label="Close panel"
      >
        esc ✕
      </button>
      <div className="px-5 pb-8 pt-5 text-[13px] leading-relaxed">{body}</div>
    </aside>
  );
}

function H({ children }: { children: React.ReactNode }) {
  return <h3 className="mt-5 font-mono text-[10px] uppercase tracking-widest text-muted">{children}</h3>;
}

function Pill({ children, tone = "" }: { children: React.ReactNode; tone?: string }) {
  return <span className={`inline-block rounded border border-border px-1.5 py-0.5 font-mono text-[10px] ${tone}`}>{children}</span>;
}

function ComponentPanel({ map, linear, lens, id, onSelect, onFocus, focus }: Props & { id: string }) {
  const c = componentById(map, id);
  if (!c) return <p className="text-muted">Unknown component.</p>;
  const zone = map.zones.find((z) => z.id === c.zone);
  const interactions = interactionsOf(map, id);
  const next = plannedFor(map, id).filter((it) => !["completed", "canceled"].includes(linear.get(it.issue)?.stateType ?? ""));
  const technical = lens === "technical";
  return (
    <div>
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted">
        <span>{zone?.name}</span>
        <span>·</span>
        <span>{KIND_GLYPH[c.kind]}</span>
      </div>
      <h2 className="mt-1 pr-14 text-lg font-semibold leading-tight text-fg">{c.name}</h2>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 font-mono text-[11px]">
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[c.status]}`} />
          {c.status}
        </span>
        {c.overlayStale && <Pill tone="text-muted">curated notes may lag — files changed after {c.reviewed_at}</Pill>}
      </div>
      {c.statusReason && <p className="mt-2 rounded border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-[12px] text-fg">{c.statusReason}</p>}

      <H>What it does</H>
      <p className="text-fg">{c.description || <span className="text-muted">No description in the source file.</span>}</p>

      <H>Why it exists</H>
      <p className="text-fg">{c.why.text}</p>
      <p className="mt-1 font-mono text-[11px] text-muted">source: {c.why.source}</p>

      <H>Build story</H>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[12px]">
        <dt className="text-muted">first shipped</dt>
        <dd className="tabular-nums">{c.build.firstShipped ?? "—"}</dd>
        <dt className="text-muted">last changed</dt>
        <dd className="tabular-nums">{c.build.lastChanged ?? "—"}</dd>
        {c.build.refs.length > 0 && (
          <>
            <dt className="text-muted">Linear</dt>
            <dd className="flex flex-wrap gap-1">
              {c.build.refs.map((r) => (
                <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className="font-mono text-[11px] text-accent hover:underline">
                  {r.id}
                </a>
              ))}
            </dd>
          </>
        )}
        {c.build.adrs.length > 0 && (
          <>
            <dt className="text-muted">decisions</dt>
            <dd className="flex flex-wrap gap-1">
              {c.build.adrs.map((r) => (
                <a key={r.id} href={r.url} target="_blank" rel="noreferrer" className="font-mono text-[11px] text-accent hover:underline">
                  {r.id}
                </a>
              ))}
            </dd>
          </>
        )}
      </dl>
      {c.build.note && <p className="mt-2 text-[12px] text-muted">{c.build.note}</p>}

      {(technical || c.tools.length > 0) && (
        <>
          <H>Tools used</H>
          {c.tools.length ? (
            <div className="flex flex-wrap gap-1">
              {c.tools.map((t) => (
                <Pill key={t}>{t}</Pill>
              ))}
            </div>
          ) : (
            <p className="text-muted">None declared.</p>
          )}
        </>
      )}

      <H>Interactions ({interactions.length})</H>
      <ul className="space-y-1">
        {interactions.map(({ edge, outgoing, other }) => (
          <li key={edge.id}>
            <button onClick={() => onSelect({ type: "edge", id: edge.id })} className="group w-full text-left hover:text-accent">
              <span className="font-mono text-[11px] text-muted">{outgoing ? "→" : "←"} </span>
              <span className="font-mono text-[11px] text-muted">{outgoing ? EDGE_VERB[edge.kind] : `is ${passive(edge.kind)}`} </span>
              <span className="text-fg group-hover:text-accent">{other.name}</span>
              {edge.status !== "live" && <Pill tone="ml-1 text-amber-500">{edge.status}</Pill>}
            </button>
          </li>
        ))}
        {interactions.length === 0 && <li className="text-muted">No edges yet — a gap in the overlay, not the system.</li>}
      </ul>

      <H>Files ({c.fileCount})</H>
      {c.id === "hub" ? (
        <ul className="font-mono text-[11px] text-muted">
          {c.files.map((f) => (
            <li key={f}>{f.replace(/^hub:/, "")}</li>
          ))}
        </ul>
      ) : c.fileCount === 0 ? (
        <p className="text-muted">External system — nothing in the repo is this component itself.</p>
      ) : (
        <>
          {technical && (
            <ul className="font-mono text-[11px] text-muted">
              {c.files.slice(0, 6).map((f) => (
                <li key={f} className="truncate">
                  <a href={REPO + f} target="_blank" rel="noreferrer" className="hover:text-accent">
                    {f}
                  </a>
                </li>
              ))}
              {c.fileCount > 6 && <li>… {c.fileCount - 6} more</li>}
            </ul>
          )}
          <button
            onClick={() => onFocus(focus === c.id ? null : c.id)}
            className="mt-2 rounded border border-border px-2.5 py-1 font-mono text-[11px] text-fg hover:border-accent hover:text-accent"
          >
            {focus === c.id ? "← back to the map" : `Explore ${c.fileCount} files ↗`}
          </button>
        </>
      )}

      {next.length > 0 && (
        <>
          <H>What&apos;s next here</H>
          <ul className="space-y-2">
            {next.map((it) => (
              <li key={it.issue}>
                <NextRow item={it} state={linear.get(it.issue) ?? null} onClick={() => onSelect({ type: "planned", id: it.issue })} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function passive(kind: MapEdge["kind"]) {
  return { reads: "read by", writes: "written to by", dispatches: "dispatched by", gates: "gated by", produces: "produced by", consumes: "consumed by", "depends-on": "depended on by" }[kind];
}

function NextRow({ item, state, onClick }: { item: BuildItem; state: LinearState | null; onClick: () => void }) {
  return (
    <button onClick={onClick} className="w-full text-left hover:text-accent">
      <span className="font-mono text-[11px] text-accent">{item.issue}</span>
      <span className="ml-2 font-mono text-[10px] uppercase tracking-widest text-muted">{item.phase === "now" ? "now" : item.phase}</span>
      {state && <span className="ml-2 font-mono text-[10px] text-muted">{state.state}</span>}
      <div className="text-[12px] text-fg">{state?.title ?? item.why}</div>
    </button>
  );
}

function EdgePanel({ map, id, onSelect }: Props & { id: string }) {
  const e = map.edges.find((x) => x.id === id);
  if (!e) return <p className="text-muted">Unknown edge.</p>;
  const s = componentById(map, e.source)!;
  const t = componentById(map, e.target)!;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted">interaction · {e.kind}</div>
      <h2 className="mt-1 pr-14 text-base font-semibold leading-snug text-fg">
        <button onClick={() => onSelect({ type: "node", id: s.id })} className="hover:text-accent">
          {s.name}
        </button>
        <span className="mx-2 font-mono text-[12px] font-normal text-muted">{EDGE_VERB[e.kind]}</span>
        <button onClick={() => onSelect({ type: "node", id: t.id })} className="hover:text-accent">
          {t.name}
        </button>
      </h2>
      {e.status !== "live" && (
        <p className="mt-2">
          <Pill tone="text-amber-500">{e.status}</Pill>
        </p>
      )}
      <H>What flows</H>
      <p className="text-fg">{e.summary}</p>
      <H>Kind</H>
      <p className="text-muted">{KIND_HELP[e.kind]}</p>
    </div>
  );
}

const KIND_HELP: Record<MapEdge["kind"], string> = {
  reads: "The source reads from the target without changing it.",
  writes: "The source creates or updates records in the target.",
  dispatches: "The source launches the target (a sub-workflow or a set of agents) and waits for it.",
  gates: "The source can hold or block the target — a run cannot close green past it.",
  produces: "The source's output is what the target is made of.",
  consumes: "The source takes the target's output as input.",
  "depends-on": "The source relies on the target's rules or code; it does not call it at runtime.",
};

function PlannedPanel({ map, linear, id, onSelect }: Props & { id: string }) {
  const it = map.buildPath.items.find((x) => x.issue === id);
  if (!it) return <p className="text-muted">Unknown item.</p>;
  const state = linear.get(it.issue) ?? null;
  const phase = map.buildPath.phases.find((p) => p.id === it.phase);
  const anchor = phase?.anchor ? map.buildPath.anchors.find((a) => a.id === phase.anchor) : null;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted">planned · {it.phase === "now" ? "in flight now" : phase?.label ?? it.phase}</div>
      <h2 className="mt-1 pr-14 text-base font-semibold leading-snug text-fg">
        <a href={it.url} target="_blank" rel="noreferrer" className="font-mono text-accent hover:underline">
          {it.issue}
        </a>
        <span className="ml-2">{state?.title ?? ""}</span>
      </h2>
      <div className="mt-2 flex flex-wrap gap-1">
        {state ? (
          <>
            <Pill>{state.state}</Pill>
            <Pill>{state.priorityLabel}</Pill>
          </>
        ) : (
          <Pill tone="text-muted">Linear state unknown (not reachable at build)</Pill>
        )}
        {phase && <Pill tone="text-muted">{phase.window}</Pill>}
        {anchor && (
          <Pill tone="text-muted">
            {anchor.id} · {anchor.date}
          </Pill>
        )}
      </div>
      <H>Why</H>
      <p className="text-fg">{it.why}</p>
      {anchor && (
        <>
          <H>Proves</H>
          <p className="text-muted">{anchor.proof}</p>
        </>
      )}
      <H>Extends</H>
      <ul>
        {it.extends.map((x) => (
          <li key={x}>
            <button onClick={() => onSelect({ type: "node", id: x })} className="text-fg hover:text-accent">
              {componentById(map, x)?.name ?? x}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FilePanel({ files, map, id, onSelect }: Props & { id: string }) {
  const f = files?.nodes.find((n) => n.id === id);
  if (!f) return <p className="text-muted">Unknown file.</p>;
  const inbound = files!.edges.filter((e) => e.dst === id);
  const outbound = files!.edges.filter((e) => e.src === id);
  const owner = f.component ? componentById(map, f.component) : null;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted">
        file · {f.subtype}
        {owner && (
          <>
            {" · "}
            <button onClick={() => onSelect({ type: "node", id: owner.id })} className="hover:text-accent">
              {owner.name}
            </button>
          </>
        )}
      </div>
      <h2 className="mt-1 break-all pr-14 font-mono text-[13px] font-semibold leading-snug text-fg">
        <a href={f.url} target="_blank" rel="noreferrer" className="hover:text-accent">
          {f.id}
        </a>
      </h2>
      <H>What it says it is</H>
      <p className="text-fg">{f.description || <span className="text-muted">No header description.</span>}</p>
      <H>Dates</H>
      <p className="font-mono text-[11px] text-muted">
        first {f.firstShipped ?? "—"} · last {f.lastChanged ?? "—"}
      </p>
      <H>References ({outbound.length} out · {inbound.length} in)</H>
      <ul className="max-h-56 overflow-y-auto font-mono text-[11px] text-muted">
        {outbound.slice(0, 20).map((e) => (
          <li key={"o" + e.dst + e.line} className="truncate">
            <button onClick={() => onSelect({ type: "file", id: e.dst })} className="hover:text-accent">
              → {e.dst}
            </button>
          </li>
        ))}
        {inbound.slice(0, 20).map((e) => (
          <li key={"i" + e.src + e.line} className="truncate">
            <button onClick={() => onSelect({ type: "file", id: e.src })} className="hover:text-accent">
              ← {e.src}
              {e.line ? `:${e.line}` : ""}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): src/components/system-map/layout.ts
// Deterministic layered layout with elk. Zones are compound nodes so the reader sees swim-lanes,
// and elk decides lane order from the edges (intake feeds pipelines feed the graph and the records).
// No force simulation: the map must look the same on every load (PRD §5 rabbit hole #1).
import type { Edge, Node } from "@xyflow/react";
import type { ElkExtendedEdge, ElkNode } from "elkjs/lib/elk-api";

export const SIZES = {
  component: { w: 208, h: 66 },
  planned: { w: 188, h: 52 },
  file: { w: 250, h: 42 },
  neighbor: { w: 208, h: 56 },
} as const;

type ElkLike = { layout: (g: ElkNode) => Promise<ElkNode> };
let elk: ElkLike | null = null;
async function getElk(): Promise<ElkLike> {
  if (!elk) {
    const mod = await import("elkjs/lib/elk.bundled.js");
    const ELK = (mod.default ?? mod) as unknown as new () => ElkLike;
    elk = new ELK();
  }
  return elk;
}

export type LayoutInput = {
  /** Compound groups (zones). Children are laid out inside; a node's `parent` names its group. */
  groups: { id: string; label: string }[];
  nodes: { id: string; parent: string | null; w: number; h: number }[];
  edges: { id: string; source: string; target: string }[];
  direction?: "RIGHT" | "DOWN";
};

export type Positioned = {
  nodes: Record<string, { x: number; y: number; w: number; h: number }>;
  groups: Record<string, { x: number; y: number; w: number; h: number }>;
};

export async function layout(input: LayoutInput): Promise<Positioned> {
  const engine = await getElk();
  const dir = input.direction ?? "RIGHT";
  const common = {
    "elk.algorithm": "layered",
    "elk.direction": dir,
    "elk.layered.spacing.nodeNodeBetweenLayers": "56",
    "elk.spacing.nodeNode": "22",
    "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
    "elk.edgeRouting": "SPLINES",
  };
  const childrenOf = (gid: string | null): ElkNode[] =>
    input.nodes
      .filter((n) => n.parent === gid)
      .map((n) => ({ id: n.id, width: n.w, height: n.h }));

  const graph: ElkNode = {
    id: "root",
    layoutOptions: { ...common, "elk.hierarchyHandling": "INCLUDE_CHILDREN", "elk.spacing.componentComponent": "48", "elk.padding": "[top=8,left=8,bottom=8,right=8]" },
    children: [
      ...input.groups.map((g) => ({
        id: g.id,
        layoutOptions: { ...common, "elk.padding": "[top=44,left=20,bottom=20,right=20]", "elk.spacing.nodeNode": "18" },
        children: childrenOf(g.id),
      })),
      ...childrenOf(null),
    ],
    edges: input.edges.map<ElkExtendedEdge>((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  };

  const out = await engine.layout(graph);
  const nodes: Positioned["nodes"] = {};
  const groups: Positioned["groups"] = {};
  for (const top of out.children ?? []) {
    const isGroup = input.groups.some((g) => g.id === top.id);
    if (isGroup) {
      groups[top.id] = { x: top.x ?? 0, y: top.y ?? 0, w: top.width ?? 0, h: top.height ?? 0 };
      for (const ch of top.children ?? []) nodes[ch.id] = { x: ch.x ?? 0, y: ch.y ?? 0, w: ch.width ?? 0, h: ch.height ?? 0 };
    } else {
      nodes[top.id] = { x: top.x ?? 0, y: top.y ?? 0, w: top.width ?? 0, h: top.height ?? 0 };
    }
  }
  return { nodes, groups };
}

/** Apply elk positions to React Flow nodes (children are positioned relative to their parent). */
export function applyPositions<N extends Node>(rfNodes: N[], pos: Positioned): N[] {
  return rfNodes.map((n) => {
    const p = n.type === "zone" ? pos.groups[n.id] : pos.nodes[n.id];
    if (!p) return n;
    return { ...n, position: { x: p.x, y: p.y }, ...(n.type === "zone" ? { style: { ...n.style, width: p.w, height: p.h } } : {}) };
  });
}

export type RfEdge = Edge;

// ---------- overview: a fixed zone grid, packed columns inside each zone ----------
// The lanes read left→right in the order work flows (intake → pipelines → graph → records) with the
// rigor layer and surfaces underneath. elk was tried here first and scattered the zones by edge
// count, which made the map illegible at fit-zoom; a fixed grid is the honest choice for six lanes.
export type GridInput = {
  zones: { id: string; row: 0 | 1 }[];
  /** Items in reading order; planned items should directly follow the component they extend. */
  items: { id: string; zone: string; w: number; h: number }[];
};

const ZONE_PAD = { top: 44, side: 18, bottom: 18 };
const GAP = { col: 18, row: 12, zone: 40 };

function columnsFor(n: number) {
  return n <= 4 ? 1 : n <= 9 ? 2 : n <= 15 ? 3 : 4;
}

export function gridLayout(input: GridInput): Positioned {
  const nodes: Positioned["nodes"] = {};
  const groups: Positioned["groups"] = {};
  const zoneSize = new Map<string, { w: number; h: number }>();

  // 1. pack each zone: fill columns top-to-bottom, balanced by count
  for (const z of input.zones) {
    const items = input.items.filter((i) => i.zone === z.id);
    const cols = columnsFor(items.length);
    const perCol = Math.ceil(items.length / cols) || 1;
    const colW = Math.max(...items.map((i) => i.w), 0);
    const colHeights = new Array(cols).fill(ZONE_PAD.top);
    items.forEach((it, idx) => {
      const c = Math.floor(idx / perCol);
      const x = ZONE_PAD.side + c * (colW + GAP.col) + (colW - it.w) / 2;
      const y = colHeights[c];
      nodes[it.id] = { x, y, w: it.w, h: it.h };
      colHeights[c] += it.h + GAP.row;
    });
    const w = ZONE_PAD.side * 2 + cols * colW + (cols - 1) * GAP.col;
    const h = Math.max(...colHeights) - GAP.row + ZONE_PAD.bottom;
    zoneSize.set(z.id, { w: Math.max(w, 220), h: Math.max(h, 90) });
  }

  // 2. place zones: row 0 flows left→right; row 1 sits beneath, spread to the same total width
  const rows: [string[], string[]] = [[], []];
  for (const z of input.zones) rows[z.row].push(z.id);
  let x = 0;
  let row0H = 0;
  for (const id of rows[0]) {
    const s = zoneSize.get(id)!;
    groups[id] = { x, y: 0, w: s.w, h: s.h };
    x += s.w + GAP.zone;
    row0H = Math.max(row0H, s.h);
  }
  const totalW = x - GAP.zone;
  const row1W = rows[1].reduce((a, id) => a + zoneSize.get(id)!.w, 0) + GAP.zone * (rows[1].length - 1);
  let x1 = Math.max(0, (totalW - row1W) / 2);
  for (const id of rows[1]) {
    const s = zoneSize.get(id)!;
    groups[id] = { x: x1, y: row0H + GAP.zone, w: s.w, h: s.h };
    x1 += s.w + GAP.zone;
  }
  // stretch every row-0 zone to the row height so the lanes read as one band
  for (const id of rows[0]) groups[id].h = row0H;
  return { nodes, groups };
}

### FILE (empire-state-hub @ alex/yed-232-system-map 381d3af): src/lib/linear/issues.ts
import "server-only";
import { unstable_cache } from "next/cache";
import { LinearClient } from "@linear/sdk";
import type { LinearState } from "@/lib/system-map/schema";

// Live state for a named set of issues (the system map's build path). Linear stays the source of
// truth for "what's open": the map never restates an issue's state, it reads it. Returns null when
// the key is absent or the API fails, and the page says so instead of guessing.
async function fetchIssues(identifiers: string[]): Promise<LinearState[] | null> {
  if (!process.env.LINEAR_API_KEY) return null;
  try {
    const linear = new LinearClient({ apiKey: process.env.LINEAR_API_KEY });
    const teamKey = process.env.LINEAR_TEAM_KEY ?? "YED";
    const numbers = identifiers.map((i) => Number(i.split("-")[1])).filter((n) => Number.isFinite(n));
    const page = await linear.issues({
      first: 100,
      filter: { team: { key: { eq: teamKey } }, number: { in: numbers } },
    });
    const out: LinearState[] = [];
    for (const issue of page.nodes) {
      const state = await issue.state;
      out.push({
        identifier: issue.identifier,
        title: issue.title,
        state: state?.name ?? "—",
        stateType: state?.type ?? "",
        priorityLabel: issue.priorityLabel ?? "No priority",
        url: issue.url,
      });
    }
    return out;
  } catch {
    return null;
  }
}

export const getIssues = (identifiers: string[]) =>
  unstable_cache(() => fetchIssues(identifiers), ["linear-issues", identifiers.join(",")], {
    revalidate: 300,
    tags: ["linear-issues"],
  })();

