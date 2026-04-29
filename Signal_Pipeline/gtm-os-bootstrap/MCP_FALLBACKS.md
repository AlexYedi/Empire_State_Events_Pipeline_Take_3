# MCP Fallbacks — gtm-os

**Purpose:** alternative configurations for any MCP server in `.mcp.json` that doesn't authenticate or function cleanly from Claude Code CLI on first install.

**Use this when:** a server in the Tier 1 list (`MCP_SETUP.md`) shows as connected in `/mcp` but tools don't work, OR OAuth fails to complete from CLI even though the same server works in Claude.ai chat.

---

## 1. Google Calendar + Gmail (most likely to need fallback)

**The problem:** the URLs in `.mcp.json` (`https://gcal.mcp.claude.com/mcp`, `https://gmail.mcp.claude.com/mcp`) are Anthropic-hosted Workspace connectors built primarily for Claude.ai chat. They may not respond correctly to third-party MCP clients (which is what mcp-remote in Claude Code CLI is). Confidence: ~65% they work; ~35% you'll need this fallback.

**The fallback:** run a Google Workspace MCP server locally with your own GCP OAuth credentials. More setup, but durable and gives you fine-grained scope control.

### Step-by-step

#### 1a. Create a GCP project + OAuth client

1. **Google Cloud Console → Create project** named `gtm-os-mcp` (or use an existing one).
2. **APIs & Services → Library → enable:**
   - Google Calendar API
   - Gmail API
3. **APIs & Services → OAuth consent screen:**
   - User type: External
   - App name: `gtm-os-mcp`
   - Add yourself as a test user (Testing publish state is fine — no need to verify the app)
   - Scopes: add `https://www.googleapis.com/auth/calendar`, `https://www.googleapis.com/auth/gmail.readonly`, `https://www.googleapis.com/auth/gmail.send` (add `gmail.modify` only if you want Claude to label/archive)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID:**
   - Application type: Desktop app
   - Name: `gtm-os-mcp-desktop`
   - Download the JSON. Save it locally as `~/.config/gtm-os-mcp/google-oauth.json` (path must match the env var below).

#### 1b. Replace the entries in `.mcp.json`

Remove the `google-calendar` and `gmail` entries that point to `*.mcp.claude.com`. Replace with a single Workspace MCP entry:

```json
"google-workspace": {
  "command": "npx",
  "args": ["-y", "@taylorwilsdon/google_workspace_mcp@latest"],
  "env": {
    "GOOGLE_OAUTH_CREDENTIALS_PATH": "${GOOGLE_OAUTH_CREDENTIALS_PATH}",
    "GOOGLE_WORKSPACE_SERVICES": "calendar,gmail"
  }
}
```

> Package name above is illustrative — when implementing, search npm for the most-maintained `google-workspace-mcp` server. As of late 2025, `@taylorwilsdon/google_workspace_mcp` and `mcp-google-workspace` are the two leading options. Pick whichever has a recent commit and clear OAuth-flow docs.

#### 1c. Add to `.env`

```
GOOGLE_OAUTH_CREDENTIALS_PATH=/Users/<you>/.config/gtm-os-mcp/google-oauth.json
```

#### 1d. First-run auth

Restart Claude Code. The Workspace MCP server will start a local OAuth flow on first call — opens a browser, you grant scopes, server writes a refresh token to `~/.config/gtm-os-mcp/token.json` (or wherever the package stores it). After that, no further auth needed unless tokens expire (~6 months).

#### 1e. Verify

```
List my Calendar events for the next 7 days.
Search Gmail for messages from the last 24 hours containing "intro".
```

---

## 2. Clay (if v3 MCP endpoint isn't available on your plan)

**The problem:** Clay's MCP endpoint (`https://api.clay.com/v3/mcp`) requires a paid plan tier. If your plan is below the threshold, the server returns 403 on every call.

**Options:**

- **A. Upgrade Clay plan** — if Clay enrichment is core to the signal layer, this is the right spend. Clay's standard paid plans start around $149/mo (verify live pricing — Clay updates often).
- **B. Defer Clay entirely** — remove the entry from `.mcp.json`, use Clay manually via web UI for now, revisit when budget supports the upgrade. Phase 0 inventory will quantify whether Clay-via-MCP is high-leverage enough to justify.
- **C. Use HubSpot enrichment as a partial substitute** — HubSpot has built-in firmographic enrichment for paid tiers. Less GTM-specific than Clay but $0 marginal cost if you already have it.

**Recommendation:** B (defer) unless Phase 0 shows a clear case where Clay-via-CLI vs Clay-via-web makes a meaningful workflow difference.

---

## 3. n8n (if hosted URL doesn't accept the API key format)

**The problem:** n8n's MCP endpoint format depends on the n8n version on `yedimaing.app.n8n.cloud`. If the auth header format in `.mcp.json` doesn't match what your instance expects, calls return 401.

**Diagnostic:**

```bash
curl -H "Authorization: Bearer ${N8N_API_KEY}" \
     https://yedimaing.app.n8n.cloud/mcp-server/http
```

If 401: try `X-N8N-API-KEY` header instead:

```json
"args": [
  "-y",
  "mcp-remote",
  "https://yedimaing.app.n8n.cloud/mcp-server/http",
  "--header",
  "X-N8N-API-KEY:${N8N_API_KEY}"
]
```

If still 401: check n8n cloud's API docs for your specific version's auth scheme. Some n8n cloud tiers don't expose the MCP server endpoint at all — check **Settings → n8n API → MCP** in your n8n UI.

---

## 4. Supabase (if Personal Access Token auth fails)

**The problem:** the `@supabase/mcp-server-supabase` package occasionally has issues with Personal Access Token format on first install.

**Fallback:** the official Supabase MCP server can also accept a project-scoped service role key via env. Less ideal (broader blast radius if leaked) but works.

```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest"],
  "env": {
    "SUPABASE_URL": "${SUPABASE_URL}",
    "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}"
  }
}
```

Add to `.env`:
```
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

**Security flag:** service role key bypasses RLS. Only use this fallback if Personal Access Token approach fails AND you understand the implications.

---

## 5. PostHog (if hosted URL has rate-limit issues)

PostHog's hosted MCP can throttle aggressively on free/small plans. If you hit rate limits frequently, the local NPM package (`@posthog/mcp` or community equivalents) can be configured to use your project's API endpoint directly with longer-lived auth.

**Fallback config:**

```json
"posthog": {
  "command": "npx",
  "args": ["-y", "@posthog/mcp@latest"],
  "env": {
    "POSTHOG_API_KEY": "${POSTHOG_API_KEY}",
    "POSTHOG_HOST": "https://us.i.posthog.com"
  }
}
```

(Adjust `POSTHOG_HOST` if you're on EU cloud.)

---

## 6. Vercel + Linear + Granola (OAuth-based, hosted)

These three are the most reliable hosted MCPs in the Tier 1 list. Failure modes are almost always one of:

- OAuth flow not completing (browser popup blocked, tab closed too early)
- Token expired (re-run `/mcp` to re-auth)
- Wrong workspace selected during OAuth grant (Vercel team scope, Linear workspace, Granola account)

**Fallback:** none usually needed. If any of these consistently fail, file an issue with the vendor — these are vendor-maintained MCPs and outside our config control.

---

## When to add a fallback to `.mcp.json` vs keep it here as a doc

- **Add to `.mcp.json` and remove the original entry** if the hosted URL fails completely and the fallback is the steady-state config (e.g., Google Workspace via npm package after confirming hosted URLs don't work).
- **Keep in this doc only** if the fallback is a one-time diagnostic or temporary workaround you might remove later (e.g., Supabase service role key fallback).

When you switch to a fallback, update `MCP_SETUP.md` Wave 1/2/3 instructions to reflect the new setup steps so future fresh installs follow the working path, not the broken one.

---

## Related

- `MCP_SETUP.md` — primary setup doc (try this first)
- `.mcp.json` — current config
- `.env.example` — env vars for current config (update if fallbacks add new vars)
