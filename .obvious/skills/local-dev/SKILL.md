---
name: local-dev
description: How to get this repo to a verified local state — script self-tests, no server required
---

# local-dev — Empire State Events Pipeline

Recorded by the 2026-10-30 onboarding run. This repo has **no server, no port, no local
database**. It is a Claude Code harness (skills/agents/commands/hooks) plus stdlib Python scripts.
Remote services (Supabase, Notion, HubSpot, PostHog, ElevenLabs, R2) are never provisioned
locally; touching them requires real credentials in `.env` and is gated by CLAUDE.md invariants.

## Setup steps (2026-10-30, all verified)

1. Clone and confirm `python3 --version` ≥ 3.13 (verified with 3.13.14). No install step —
   core scripts are stdlib-only. Optional doc-KB deps: `.claude/scripts/requirements-dockb.txt`
   (heavy — sentence-transformers/torch; only needed for archived ingest-doc/ask-library flows).
2. Copy `.env.example` → `.env` only if you need remote integrations. All local checks below run
   without any env vars.
3. Run the verification suite:

```bash
python3 .claude/scripts/lint_agent_tools.py --selftest   # 19/19
python3 .claude/scripts/lint_agent_tools.py .claude/agents  # 11 files, 0 failures
python3 .claude/scripts/spine_client.py --selftest        # 30/30 guard cases
python3 .claude/scripts/spine_client.py --check-writers   # 0 offenders
python3 .claude/scripts/test_dispatch_record.py           # 13/13 (run directly, NOT via unittest discover — it loads dispatch_record.py via importlib path spec)
```

4. No secrets were needed on this run; no secure-credential requests were made.

## Gotchas

- `test_dispatch_record.py` fails under `python -m unittest discover` (importlib
  `spec_from_file_location` + discover interplay). Run it directly as documented in its usage line.
- `spine_client.py --selftest` prints transient-URLError retry noise to stderr — expected, it
  exercises offline/refusal paths. Exit code 0 + `30/30` is the signal.
- `Event Content/` paths contain spaces — quote them.
- Anything writing to the Supabase spine must go through `spine_client.py`; run `--selftest` and
  `--check-writers` before any spine PR (CLAUDE.md invariant 1).
- Nightly CI (`mi-2b-nightly-healthcheck`) needs repo secrets (MI_DB_DSN, MI_SUPABASE_URL,
  MI_SUPABASE_ANON_KEY) — GitHub-side, not local.
