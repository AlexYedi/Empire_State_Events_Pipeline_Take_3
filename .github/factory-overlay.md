# Repository overlay

Rules for this repository, from CLAUDE.md section 4. A diff that breaks one is a blocking
`invariant` finding.

- Email addresses and phone numbers never enter the Supabase spine or any committed file.
- Every spine write goes through `.claude/scripts/spine_client.py`. No hand-rolled HTTP calls,
  curl, or SQL DML against Supabase anywhere else.
- No code adds Supabase write access through MCP; MCP is used read-only.
- Only the `notion-writer` agent writes to Notion, from a parent-written, schema-checked payload.
- No agent that reads untrusted text (web pages, transcripts, inbox content) is given write tools.
- `.env`, `me-model.md`, `target-companies.md` and inbox allow/deny lists are never added to git.
- Every script in `.claude/scripts/` that has a `--selftest` keeps it; selftests are not deleted
  or weakened to make a change pass.
