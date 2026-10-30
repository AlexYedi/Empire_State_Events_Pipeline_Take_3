# Review overlay: Empire_State_Events_Pipeline_Take_3

Read `AGENTS.md` and `CLAUDE.md` §4 before reviewing.

## Blocker (score ≥ 90) if the PR:
- adds or changes any line in `.env*`, `me-model.md`, `target-companies.md`, or inbox list files
- changes guard logic in `.claude/scripts/spine_client.py`, `inbox_boundary.py` or `lint_agent_tools.py` (selftest-case additions are fine)
- touches `.claude/hooks/` or `.claude/settings*.json`
- adds a REST/HTTP write to Supabase anywhere except through `spine_client.py`
- calls a Notion, HubSpot or Linear write API from code
- adds an email address or phone number (fixtures must use `*.example`)
- edits an existing file in `supabase/migrations/`
- edits anything under `Event Content/`

## High scrutiny
- `.claude/skills/**/SKILL.md` and `.claude/commands/*.md`: does the change keep "drafts to Notion `needs_review`, nothing publishes without Alex"?
- `.claude/agents/*.md`: the `tools:` line must stay minimal. No agent that reads web or inbox text may gain a write tool.
- New metrics: each must state its do-nothing baseline.

## Already handled by tooling (don't comment)
- Agent tool-boundary rules: `lint_agent_tools.py` runs in CI.
- Secrets: the `secret-scan.yml` workflow.

## Expected in every PR body
The spec ID (E-n or S-n), the selftest output for each touched script, and any follow-ups as "Proposed Linear issue: …".
