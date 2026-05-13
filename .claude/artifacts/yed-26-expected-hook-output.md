# YED-26 — Expected hook output after API key activation

**Purpose:** Lets Alex visually verify the SessionStart hook is firing correctly once `LINEAR_API_KEY` is exported. Pre-rendered from live Linear MCP query 2026-05-13.

---

## What you should see at session start (once activated)

After exporting `LINEAR_API_KEY` and opening a fresh Claude Code session, look for this block injected at the top of session context (rendered from `.claude/hooks/linear-priorities.sh`):

```
## 🟠 Linear priorities (live pull, ≤5 items, Medium+ priority)

- **[YED-26 — High, In Progress]** Single source of truth: replace CLAUDE.md priorities block with SessionStart Linear hook
- **[YED-28 — High, Backlog]** Layer A — make alex-agents-skills a Claude Code plugin (live source across all projects)
- **[YED-30 — Medium, Backlog]** Layer C — canonical CLAUDE.md fragment + new-project starter kit (build-better inheritance)
- **[YED-29 — Medium, Backlog]** Layer B — promote YED-26/27 hooks from project-scope to user-scope (universal discipline)
- **[YED-27 — Medium, Backlog]** Event-triggered Linear nudges: repo-touch hook + v2-trigger logging hook

_Source: Linear MCP via SessionStart hook (`.claude/hooks/linear-priorities.sh`). Replaces the static priorities block in CLAUDE.md — see YED-26._
```

Note that **YED-24 and YED-25 are below the cap of 5**. They're both Medium priority but were updated earlier than YED-27. To see all 7 active issues, increase `MAX_ISSUES` in the hook script (default 5).

---

## What you should see right now (fallback mode, no API key)

Until you export the API key, the hook outputs this fallback message:

```
## 🟠 Linear priorities (offline)

`LINEAR_API_KEY` not set — SessionStart hook running in graceful-fallback mode. To activate live priorities pull:

1. Create personal API key at https://linear.app/yedibalian/settings/api
2. Add to shell rc: `export LINEAR_API_KEY=lin_api_...`
3. Restart Claude Code session

Tracked under YED-26.
```

This is what should appear at session start until activation.

---

## Verification steps after API key export

1. `echo $LINEAR_API_KEY` — confirms the env var is set in your shell.
2. From this repo root, run `.claude/hooks/linear-priorities.sh | jq -r '.hookSpecificOutput.additionalContext'` — should output the live priorities block above (not the fallback message, not an error).
3. Open a fresh Claude Code session in this repo. The live priorities block should appear automatically at session start.

If step 2 outputs an API error (e.g., "Authentication required"), the API key is malformed or revoked — regenerate at https://linear.app/yedibalian/settings/api.

If step 3 doesn't show the block, Claude Code didn't pick up the hook — verify `.claude/settings.json` has the SessionStart hook entry and try restarting Claude Code entirely (not just opening a new session in the same instance).

---

## Bug log (resolved 2026-05-13)

- **Initial GraphQL query bug:** declared `$teamId: String!` but Linear's schema expects `ID!`. Surfaced during bogus-key smoke test. Fixed by changing `String!` → `ID!` in `linear-priorities.sh`. Confirmed by retesting with bogus key — now returns clean "Authentication required" error instead of type-mismatch error. The query structure is valid; only the API key is missing.
