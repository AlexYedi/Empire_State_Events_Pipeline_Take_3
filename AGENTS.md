# AGENTS.md

**Read `CLAUDE.md` first.** Its invariants (§4) and working rules (§5) apply to every change in this repo, whether a person, Claude Code, or an automated agent (Obvious Autobuild) makes it.

## Rules every automated change follows
1. **Public repo, private inputs.** You must never commit `.env*`, `me-model.md`, `target-companies.md`, inbox lists, or anyone's off-the-record words. You must never rewrite git history.
2. **No live writes from a sandbox.** You must not write to Supabase, Notion, HubSpot or Linear. Code that writes goes through `.claude/scripts/spine_client.py` (the graph) or the `notion-writer` payload path (Notion), and is tested offline with fixtures.
3. **Guard logic is human-only.** You must not edit the guard logic in `spine_client.py`, `inbox_boundary.py` or `lint_agent_tools.py`, or anything in `.claude/hooks/` or `.claude/settings*.json`. Adding test cases is fine.
4. **No contact data, ever.** No email or phone in code, fixtures or data. Fixtures use `*.example` domains.
5. **Every metric carries its do-nothing baseline** (CLAUDE.md §5).
6. **Verify before the PR.** Run the touched script's `--selftest`. Any PR that touches the graph write path also runs `spine_client.py --selftest` and `--check-writers`.
7. **Follow-ups go in the PR body** as "Proposed Linear issue: …". Don't leave "revisit later" notes in files.

## Where the work is
Specs live in **`docs/specs/`**, in three tracks: Empire, GTM and Shared. `docs/specs/README.md` is the index across all four repos. Build from a spec, and cite it in the PR.
