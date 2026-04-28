# MCP Setup — Notion + HubSpot for Claude Code CLI

**Why this exists:** the Claude.ai chat connectors (Notion, HubSpot OAuth-flow connectors) only work inside chat. To use the same services from Claude Code CLI sessions (where we run the inventory protocol), the repo needs a `.mcp.json` config and HubSpot needs a Private App token.

**Time required:** 15–20 minutes total — most of it on the HubSpot Private App scope checklist.

**Result:** Claude Code can call Notion MCP tools (read/write your databases) and HubSpot MCP tools (CRM read/write) directly from this repo's session.

---

## Files involved

- `.mcp.json` — repo root. Defines the two MCP servers. Committed to git.
- `.env.example` — repo root. Documents required env vars. Committed to git.
- `.env` — repo root. Holds the actual HubSpot token. **Gitignored**, never committed.

---

## One-time setup

### 1. HubSpot — create a Private App and grab the token

1. Open HubSpot. **Settings → Integrations → Private Apps**.
2. Click **Create private app**.
3. **Basic Info tab:** name it `claude-code-cli` (or similar). Description optional.
4. **Scopes tab:** check the following. These mirror the read/write claim in `CLAUDE.md` so the existing event-research skill keeps working from CLI too.

   **Standard scopes (CRM objects):**
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.companies.read`
   - `crm.objects.companies.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - `crm.objects.owners.read` (already in use — HubSpot owner ID 90413044)

   **Engagements (= Notes, per HubSpot's data model):**
   - The "Notes attached to contacts" pattern from CLAUDE.md uses HubSpot Engagements under the hood. The exact scope name varies by account tier; if you don't see an explicit `notes` scope, look for `sales-email-read` and `crm.objects.notes.read` / `.write`. If neither is present, the CRM object scopes above usually grant note access transitively. Verify with a test query after install.

5. Click **Create app**, then **Continue creating**.
6. **Auth tab:** copy the **Access token** (starts with `pat-na1-...` or similar). This is shown once — copy it immediately.

### 2. Put the token in `.env` (locally, never committed)

```bash
cp .env.example .env
# Open .env and paste the token after HUBSPOT_PRIVATE_APP_TOKEN=
```

The repo's `.gitignore` already excludes `.env` and `.env.*` (except `.env.example`). Verify with `git status` — `.env` should NOT appear as untracked.

### 3. Notion — nothing to do here yet

The `.mcp.json` points at the official hosted MCP at `https://mcp.notion.com/mcp`. Authentication happens via OAuth on first use, inside the Claude Code session (next step).

If for some reason hosted Notion MCP isn't available, fallback is the local server at `@notionhq/notion-mcp-server` with a Notion Internal Integration token — but try hosted first.

### 4. Restart Claude Code

The CLI reads `.mcp.json` at session start. If you added the config mid-session, exit and reopen Claude Code in the repo directory.

### 5. First-run authentication

Inside the new Claude Code session, run:

```
/mcp
```

This shows the registered MCP servers. For Notion, complete the OAuth flow (browser window will open). For HubSpot, the token from `.env` should already be in effect — verify the server shows as connected.

### 6. Verify

Ask Claude (in the session) to run a sanity query:

> Run a Notion search for the Events database (data source ID 9dcbc999-b4ed-4a51-b48a-10aaf171f1ba) and return the row count. Then run a HubSpot search for total contacts and return the count.

If both return numbers, you're connected. If either errors, the troubleshooting section at the bottom covers the common failures.

---

## What this unlocks

Once setup is done, Phase 0 inventory (Parts A and C of `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md`) can run from Claude Code CLI directly. No more "do it in Claude.ai desktop and paste back" round trip.

The current Phase 0 task is to execute the inventory and produce `Signal_Pipeline/Phase_0/inventory_findings.md`. After MCP setup is verified, just say "go" in the session and Claude will run the protocol.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/mcp` shows servers but Notion is "not connected" | OAuth flow didn't complete | Run `/mcp` again, click the auth link, complete in browser |
| HubSpot returns 401 | Token wrong, expired, or scopes missing | Re-check `.env`, regenerate Private App token if needed, verify scopes match section 1 |
| `npx -y mcp-remote ...` hangs on first run | npm cache priming | Wait 30s; subsequent runs are fast |
| Tools don't show in ToolSearch | `.mcp.json` not picked up | Verify session was restarted; check `.mcp.json` is at repo ROOT not in a subfolder |
| `.env` shows in `git status` | gitignore mismatch | Confirm `.gitignore` has `.env` and `.env.*` lines (it does in this repo) |
| HubSpot "engagements" / notes queries fail | Scope mismatch | Add `sales-email-read` to the Private App scopes; some accounts also need `crm.import` |

---

## Security notes

- **Never commit `.env`.** The `.gitignore` protects against accidental commits, but verify `git status` before every commit if you're touching env-related files.
- **Rotate the HubSpot token if it leaks.** HubSpot Private Apps support token rotation in the Auth tab.
- **Scope minimization is OK to defer.** For now, mirror the existing Claude.ai connector permissions. If a future security review wants narrower scopes, narrow then — not preemptively.
- **The Notion hosted MCP uses OAuth scoped to your Notion account.** It can read/write any page or DB you have access to. If you want to lock it down to specific DBs, the local-server alternative (`@notionhq/notion-mcp-server` with an Internal Integration) gives finer-grained control by sharing only specific pages with the integration. Not needed at our scale; flagged for future.

---

## Related

- `.mcp.json` — config that this guide describes
- `.env.example` — env template; copy to `.env` for actual values
- `Signal_Pipeline/SESSION_BOOTSTRAP.md` — fresh-session prompt; references this setup
- `Signal_Pipeline/Phase_0/00_data_inventory_protocol.md` — first task that uses these MCPs
- `CLAUDE.md` — repo-wide notes including the original event-research skill's HubSpot conventions and the verified Notion DB schemas
