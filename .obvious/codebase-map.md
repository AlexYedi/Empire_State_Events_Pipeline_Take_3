# Codebase Map

| Path | What it is |
|---|---|
| `.claude/` | The Claude Code harness — the pipeline itself. |
| `.claude/commands/` | Slash-command entry points (`/event-deep-research`, `/post-event-content`, `/check-new-events`, `/scan-roles`, …). |
| `.claude/agents/` | Subagent definitions with minimal `tools:` lines (linted by CI). |
| `.claude/skills/` | Methodology per skill (content-correspondent, event-research, role-radar, judge-build, …). |
| `.claude/scripts/` | Python helpers — `spine_client.py` (PII-guarded Supabase writes), `lint_agent_tools.py`, `dispatch_record.py`, `substrate.py`, `retrieve.py`, media/content scripts. Stdlib-only core. |
| `.claude/hooks/` | Event-claim lock, telemetry emit, and other wired hooks. |
| `.claude/references/` | Durable reference docs (platform constraints, agent routing, spine model, judge spec). |
| `.claude/WORKFLOWS.md` | Rerun manual — how the workflows chain, statuses, history of prunes/archives. |
| `Event Content/` | One folder per event (date + title): briefs, slide decks, drafts, rendered carousel finals. Mostly gitignored media + transcripts. |
| `docs/` | `adr/` (append-only decision records), `archive/` (retired skills/commands/notes), PRDs, migration playbook, history. |
| `supabase/` | MI-graph data layer: `migrations/` (0001–0012), `scripts/` (build/healthcheck/compute), `staging/` (twin-rehearsal + rollback SQL), specs. Applies to remote Supabase only. |
| `signal-stream/` | Signal ingestion lane: producers, sinks, ICP, SQL, MCP glue (retired inbox lane lives in ADR-11). |
| `research-briefs/` | Rendered pre-event research briefs (markdown, dated). |
| `content-correspondent-events/` | Content-correspondent skill notes for specific events. |
| `skill-updates/` | One-off skill diffs/updates pending review. |
| `.github/` | CI workflows (agent-tools-lint, secret-scan, MI nightly healthcheck) + PR template. |
| `.env.example` | Env var template (HubSpot, PostHog, OpenAI). Real keys in local `.env`, never committed. |
