# Empire_State_Events_Pipeline_Take_3

Full Funnel NYC AI and Agentic Events Pipeline. **This is not a server application** — it is an
AI-native content/research pipeline built as a Claude Code harness: skills, agents, commands, hooks
and Python helper scripts. The pipeline is the product (see `CLAUDE.md` §2); event media and
content live alongside the code. Both repos are public by design — private inputs never enter git
(CLAUDE.md invariant 4).

## Stack

- **Runtime:** Python 3.13 (stdlib only for the core scripts; optional deps for the retired doc-KB
  tooling in `.claude/scripts/requirements-dockb.txt`). No package manager, no lockfile, no build.
- **Harness:** Claude Code — `.claude/` (commands, agents, skills, hooks, references, settings).
- **Remote services (no local instances):** Supabase (Postgres MI graph, project `The-Prod-Brain`),
  Notion (databases + drafts), HubSpot (CRM, post-event writes), PostHog (telemetry), ElevenLabs
  (transcription), Cloudflare R2 (media archive). All accessed over the network; nothing to
  provision locally.
- **Env vars:** see `.env.example` (`HUBSPOT_PRIVATE_APP_TOKEN`, `POSTHOG_*`, `OPENAI_API_KEY`,
  `SUPABASE_API_KEY`). None are required for the local checks below.

## Commands

```bash
# Agent-tools lint (CI: .github/workflows/agent-tools-lint.yml)
python3 .claude/scripts/lint_agent_tools.py --selftest
python3 .claude/scripts/lint_agent_tools.py .claude/agents

# PII guard self-tests — run before any spine PR (CLAUDE.md invariant 1)
python3 .claude/scripts/spine_client.py --selftest
python3 .claude/scripts/spine_client.py --check-writers

# Offline regression test (run directly — not via unittest discover)
python3 .claude/scripts/test_dispatch_record.py

# Secret scan (CI: .github/workflows/secret-scan.yml, gitleaks 8.30.1)
```

There is no dev server, no port, no local database. "Starting the app" means invoking a skill or
command through Claude Code; the verifiable local surface is the script self-tests above.

## Codebase map

See [codebase-map.md](codebase-map.md).

## Local verification

Minimum bar before a PR (matches CI + CLAUDE.md invariants):

1. `lint_agent_tools.py --selftest` → `19/19 passed`
2. `lint_agent_tools.py .claude/agents` → `0 failure(s)`
3. `spine_client.py --selftest` → `30/30 guard cases pass`
4. `spine_client.py --check-writers` → `0 script offender(s)`
5. `test_dispatch_record.py` → `13/13 passed`

Recorded 2026-10-30, all passing (onboarding run).

## Repo rules that bind any agent

- Read `CLAUDE.md` first: invariants (PII boundary, read-only Supabase MCP, one-writer-per-event,
  public-repo hygiene) and working rules (branch → PR → merge for harness changes; PR template
  discipline). Supabase DDL only from repo migrations after a twin rehearsal.
- PII (email/phone) never enters the Supabase spine — all spine writes go through
  `.claude/scripts/spine_client.py`.
- Event media (audio/video/transcripts) is gitignored; heavy A/V lives in R2/Drive.
- `Event Content/` folder names are dates + event titles with spaces — always quote paths.

## Snapshot

- Snapshot ID: `8p27v006a9lxkgc1vq1n:default`
- Captured: 2026-10-30T14:54:31Z
- State: fresh `main` checkout, all local checks passing (see Local verification).
