---
name: empire-guardrails
description: Repo rules for Empire_State_Events_Pipeline_Take_3: privacy boundary, write paths, guarded files, verification. Load for any change to .claude/scripts, .claude/skills, .claude/commands, docs, or anything touching the MI graph, Notion or HubSpot.
triggers:
  - spine
  - supabase
  - graph
  - notion
  - hubspot
  - selftest
  - privacy
  - pii
---

# Empire guardrails

`CLAUDE.md` is the source of truth. This skill is the operating summary for automated builds.

## Guarded paths (human review; tests-only for agents)
| Path | Why | What agents may do |
|---|---|---|
| `.claude/scripts/spine_client.py` | The one graph write path and its PII guard (ADR-9) | Add selftest cases only |
| `.claude/scripts/inbox_boundary.py` | Inbox privacy boundary | Add selftest cases only |
| `.claude/scripts/lint_agent_tools.py` | Agent tool-boundary lint (invariant 5) | Add selftest cases only |
| `.claude/hooks/`, `.claude/settings*.json` | Harness behaviour | Nothing |
| `.env*`, `me-model.md`, `target-companies.md` | Private inputs | Nothing; never read them into output |
| `supabase/migrations/` | DDL is applied by Alex from the dashboard after a rehearsal (invariant 2) | Propose a new migration file; never edit an existing one |

## Write paths
- **Graph:** `spine_client.write()` / `spine_write.py` only. Per-table allowlists; email and phone forbidden everywhere.
- **Notion:** a parent-written payload validated by `notion_payload.py`, then executed by the `notion-writer` agent. Skills *describe* steps; they never call write tools from untrusted text.
- **HubSpot:** post-event, selective, create-once, with a confirmation table. Never automated.

## Verification commands
```
python3 .claude/scripts/spine_client.py --selftest
python3 .claude/scripts/spine_client.py --check-writers
python3 .claude/scripts/lint_agent_tools.py --selftest && python3 .claude/scripts/lint_agent_tools.py .claude/agents
python3 .claude/scripts/<script>.py --selftest
```

## Content rules agents touch
Skills and references that shape public copy (`content-style-guide.md`, `content-anti-patterns.md`, `outreach-templates.md`): edits must be **additive and cited**. Alex reviews every voice change. Posts ship 3 variants, connection notes 2; nothing publishes without Alex.
