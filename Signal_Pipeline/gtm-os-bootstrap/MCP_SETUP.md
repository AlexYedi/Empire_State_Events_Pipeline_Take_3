# MCP Setup — gtm-os (11 servers)

**Purpose:** wire all Tier 1 GTM data + ops servers into Claude Code CLI for the gtm-os repo so every session in this directory boots with the full signal plane available.

**Tier 1 (this doc):** Notion, HubSpot, Linear, PostHog, Clay, Granola, Google Calendar, Gmail, Supabase, Vercel, n8n.

**Time budget:** ~45–60 min on a clean install. Don't try to do it all in one sitting — the verification ladder below stages it so you can stop after any rung and resume later.

**Result:** every Claude Code session in `gtm-os/` has read/write access to the full GTM stack via MCP. No paste-and-sync, no Claude.ai desktop round trips for this repo.

---

## Files involved

- `.mcp.json` — repo root, committed. Defines all 11 servers.
- `.env.example` — repo root, committed. Documents required env vars + scopes.
- `.env` — repo root, **gitignored**. Holds actual tokens.
- `MCP_FALLBACKS.md` — backup configs if hosted servers don't authenticate cleanly.

---

## Verification ladder (recommended order)

The trick to avoiding "5 things broken at once" debugging is to add servers in waves. Each wave is a stop point — verify all servers in the wave work before moving on.

| Wave | Servers | Why grouped |
|---|---|---|
| **0** | Notion, HubSpot | Already proven from Empire repo migration. Re-verify after copy. |
| **1 (API key, fast)** | Linear, PostHog, Clay, n8n, Supabase | API-key auth is fastest to set up and test. Get the easy wins. |
| **2 (OAuth, hosted)** | Granola, Vercel | OAuth via mcp-remote is reliable for these vendors. |
| **3 (OAuth, flagged)** | Google Calendar, Gmail | Hosted at `*.mcp.claude.com` — may be Claude.ai-only. Save for last; fallback in `MCP_FALLBACKS.md` if they fail. |

After each wave: run `/mcp` to confirm green status, then run a one-tool sanity query (table at the bottom of this doc) before adding the next wave.

---

## Wave 0 — Notion + HubSpot (already proven)

Both were set up in the Empire repo and pushed to gtm-os via the bootstrap kit copy.

- **Notion:** OAuth flow on first `/mcp` invocation. No token needed.
- **HubSpot:** `HUBSPOT_PRIVATE_APP_TOKEN` already in `.env` (carry over from Empire's `.env` — same Private App, no new app needed).

**Verify:**
```
Run a Notion search for the Events database (data source ID
9dcbc999-b4ed-4a51-b48a-10aaf171f1ba) and return the row count.
Then run a HubSpot search for total contacts and return the count.
```

If either fails, stop and fix before moving on. The Empire repo's `MCP_SETUP.md` troubleshooting table covers the common failures.

---

## Wave 1 — Linear, PostHog, Clay, n8n, Supabase

### 1. Linear (OAuth)

No token. On first `/mcp` after restart, click the auth link, complete in browser. Done.

### 2. PostHog (API key)

1. PostHog → **Settings → Personal API keys → Create personal API key**.
2. Label: `claude-code-gtm-os`.
3. Scopes (read-only is fine for v1):
   - `insight:read`
   - `dashboard:read`
   - `feature_flag:read`
   - `query:read`
   - `session_recording:read`
4. Copy the key. Paste into `.env` as `POSTHOG_API_KEY=`.

### 3. Clay (API key)

1. Clay → **Settings → API → Generate API key**.
2. Confirm your Clay plan tier supports the v3 MCP endpoint. If you're on a tier that doesn't, the server will return 403 — escalate to plan upgrade or defer to Tier 2.
3. Paste into `.env` as `CLAY_API_KEY=`.

### 4. n8n (API key)

1. n8n → **Settings → n8n API → Create API key**.
2. Instance: `yedimaing.app.n8n.cloud`.
3. Paste into `.env` as `N8N_API_KEY=`.

### 5. Supabase (Personal Access Token)

1. Supabase → **Account → Access Tokens → Generate new token**.
2. Note: this is account-scoped, NOT project anon/service key. The MCP server uses this to discover and operate across projects you have access to.
3. Paste into `.env` as `SUPABASE_ACCESS_TOKEN=`.

### Restart Claude Code, run /mcp

All five new servers should show as connected. If any fails, check the env var name matches `.mcp.json` exactly (these are templated with `${VAR_NAME}` in `.mcp.json`).

### Wave 1 verification queries

```
1. Linear: list my open issues assigned to me, return titles only.
2. PostHog: return the list of projects in my account.
3. Clay: search for my own company by domain (use whatever domain you've added) and return the result.
4. n8n: list active workflows on yedimaing.app.n8n.cloud.
5. Supabase: list my projects and return name + region for each.
```

If any return a 401/403, the token is wrong or scopes are insufficient — re-check.

---

## Wave 2 — Granola, Vercel

### 6. Granola (OAuth)

`/mcp` → click auth link → complete. Done.

### 7. Vercel (OAuth)

`/mcp` → click auth link → complete. Vercel will ask which team/scope to grant. Pick the scope that includes the projects you'll deploy gtm-os/Hub from.

### Wave 2 verification queries

```
1. Granola: search my recent meetings for "GTM" and return the 5 most recent matches.
2. Vercel: list my projects and return their production URLs.
```

---

## Wave 3 — Google Calendar, Gmail (FLAGGED)

These hosted URLs (`gcal.mcp.claude.com`, `gmail.mcp.claude.com`) are Anthropic's Workspace connectors built primarily for Claude.ai chat. **Confidence ~65% they work cleanly from Claude Code CLI** via mcp-remote OAuth.

**Try them first.** Run `/mcp` after restart, attempt OAuth for each.

If OAuth completes cleanly and tools appear in ToolSearch — done.

If OAuth fails, hangs, or tools never appear — switch to the npm-package fallback documented in `MCP_FALLBACKS.md` (requires creating a Google Cloud OAuth client; ~20 min extra setup but bulletproof).

### Wave 3 verification queries

```
1. Google Calendar: list my events for the next 7 days, return title + start time.
2. Gmail: search my inbox for messages from the last 24 hours containing "intro" and return subject + sender.
```

---

## Full final verification (after all 3 waves)

Once all 11 servers are green in `/mcp`, run this end-to-end signal-plane sanity check:

```
For each connected MCP server, run one read-only query and confirm a non-error response.
Report results in a table: server | query | status | one-line result.
Stop and flag any failures.
```

If all green, gtm-os is fully wired.

---

## Troubleshooting (cross-cutting)

| Symptom | Likely cause | Fix |
|---|---|---|
| `/mcp` shows server but "not connected" | OAuth flow didn't complete | Re-run `/mcp`, click auth link, complete in browser |
| 401/403 on first call | Token wrong, expired, or missing scopes | Re-check `.env` value; regenerate token if uncertain |
| `npx -y mcp-remote ...` hangs first run | npm cache priming | Wait 30s; subsequent runs are fast |
| Server never appears in ToolSearch | Session not restarted after `.mcp.json` change OR JSON syntax error in `.mcp.json` | Restart Claude Code; validate JSON with `jq` |
| `.env` shows in `git status` | gitignore mismatch | Confirm `.gitignore` has `.env` and `.env.*` entries |
| Hosted MCP returns "method not allowed" | URL is chat-only, not third-party-MCP-compatible | Switch to npm-package fallback (see `MCP_FALLBACKS.md`) |
| ToolSearch noisy after install | 11 servers × N tools each = high tool count | Use `select:<tool_name>` queries when you know the target tool |

---

## Security notes

- **Never commit `.env`.** Verify `git status` before any commit touching env-related files.
- **Token rotation:** every server above supports key rotation. Rotate on suspicion of leak — never reuse a leaked token.
- **Scope minimization:** v1 mirrors broad scopes for speed. After Phase 0 inventory, narrow scopes per server based on actual usage.
- **Hosted MCP trust model:** OAuth-based hosted servers (Notion, Linear, Granola, Vercel, Google) authenticate per Claude Code session. Tokens are not stored in `.env`. If a session leaks, re-authenticate to invalidate.
- **n8n API key is broad** — it can trigger any workflow on your instance. Treat as production credential.

---

## Related

- `.mcp.json` — config this guide describes
- `.env.example` — env template; copy to `.env` for actual values
- `MCP_FALLBACKS.md` — fallback configs for servers that don't work via hosted URLs
- `STACK_README.md` (root) — full stack inventory + tool selection rules
- `CLAUDE.md` (root) — gtm-os identity, project_architecture, behavioral rules
