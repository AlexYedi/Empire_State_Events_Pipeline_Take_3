Invariants for every task in this repo (from CLAUDE.md §4). They must never be violated:
- NEVER commit .env*, me-model.md, target-companies.md, inbox lists, or off-the-record material. NEVER rewrite git history.
- NEVER write to Supabase, Notion, HubSpot or Linear from the sandbox. Tests use offline fixtures only.
- Graph writes MUST go through .claude/scripts/spine_client.py. NEVER add another REST writer (`spine_client.py --check-writers` must pass).
- NEVER edit guard logic in spine_client.py, inbox_boundary.py or lint_agent_tools.py, or anything in .claude/hooks/ or .claude/settings*.json. Adding selftest cases is allowed.
- NEVER put an email address or phone number in code, fixtures or data. Fixture domains end in .example.
- NEVER edit files under "Event Content/". They are content outputs.
- Every metric MUST state its do-nothing baseline.
- Before opening a PR, run the touched script's --selftest and report the output in the PR body.
- Specs live in docs/specs/. Cite the spec ID (E-n, S-n) in the PR title.
