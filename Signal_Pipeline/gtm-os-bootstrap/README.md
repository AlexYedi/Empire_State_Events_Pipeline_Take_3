# gtm-os Bootstrap Kit

**What this is:** four files staged in the Empire repo, ready to be copied into the `AlexYedi/gtm-os` repo when that session starts. They wire 11 MCP servers (full GTM data + ops plane) into Claude Code CLI for gtm-os.

**Why they live here:** this Claude Code sandbox is hard-scoped to the Empire repo — it can't push to gtm-os directly. So the artifacts are drafted here and copied across in the new gtm-os session.

---

## Files in this kit

| Source (here) | Destination (gtm-os) | Purpose |
|---|---|---|
| `.mcp.json` | `gtm-os/.mcp.json` (repo root) | 11-server MCP config for Claude Code CLI |
| `.env.example` | `gtm-os/.env.example` (repo root) | Token placeholders + scope notes per server |
| `MCP_SETUP.md` | `gtm-os/MCP_SETUP.md` (repo root) | Per-server setup with 3-wave verification ladder |
| `MCP_FALLBACKS.md` | `gtm-os/MCP_FALLBACKS.md` (repo root) | Backup configs if hosted URLs don't authenticate from CLI |

## Migration sequence (when ready to spin up gtm-os)

1. **Clone gtm-os locally** outside this sandbox:
   ```
   git clone https://github.com/AlexYedi/gtm-os.git
   cd gtm-os
   ```

2. **Copy the four files** from this bootstrap kit into the gtm-os root:
   ```
   cp /path/to/Empire_State_Events_Pipeline_Take_3/Signal_Pipeline/gtm-os-bootstrap/.mcp.json .
   cp /path/to/Empire_State_Events_Pipeline_Take_3/Signal_Pipeline/gtm-os-bootstrap/.env.example .
   cp /path/to/Empire_State_Events_Pipeline_Take_3/Signal_Pipeline/gtm-os-bootstrap/MCP_SETUP.md .
   cp /path/to/Empire_State_Events_Pipeline_Take_3/Signal_Pipeline/gtm-os-bootstrap/MCP_FALLBACKS.md .
   ```

3. **Create `.env`** from the example and fill in tokens (see `MCP_SETUP.md` waves 0–3):
   ```
   cp .env.example .env
   ```

4. **Verify `.gitignore`** in gtm-os excludes `.env` and `.env.*` (except `.env.example`). If it doesn't, add it.

5. **Also migrate Signal Pipeline planning artifacts** from Empire's `Signal_Pipeline/` directory into gtm-os root (these are the gtm-os-native docs — they were drafted here under "Signal_Pipeline" naming because that was the working name):
   - `PROJECT_BRIEF.md`
   - `SESSION_BOOTSTRAP.md` (update repo coordinates inside it from Empire to gtm-os)
   - `Phase_0/` directory (entire subtree)

6. **Commit + push to gtm-os.**

7. **Open a fresh Claude Code session in gtm-os.** Run `/mcp` to start the auth ladder. Follow waves 0 → 1 → 2 → 3 in `MCP_SETUP.md`.

8. **Back in Empire:** add a `Signal_Pipeline/MOVED.md` pointer noting the work continues at `AlexYedi/gtm-os`. Optional: delete the rest of `Signal_Pipeline/` from Empire after verifying everything migrated cleanly.

## Server count summary

| Tier | Count | Servers |
|---|---|---|
| Tier 1 (this kit) | 11 | Notion, HubSpot, Linear, PostHog, Clay, Granola, Google Calendar, Gmail, Supabase, Vercel, n8n |
| Tier 2 (add later) | 3 | Gamma, Canva, Magic Patterns |
| Tier 3 (occasional) | 3 | Similarweb, BigQuery, ChatPRD |
| Skip | — | n8n was originally on this list per Empire's "no n8n" rule from the predecessor failure; promoted to Tier 1 with scoping (orchestration only, NOT integration layer). See gtm-os CLAUDE.md when written. |

## Confidence

- **8 of 11 servers should work cleanly on first install:** Notion, HubSpot, Linear, PostHog, Clay, Granola, Vercel, Supabase. ~90%.
- **2 servers flagged:** Google Calendar + Gmail at `*.mcp.claude.com` URLs. ~65% they work in CLI; fallback documented in `MCP_FALLBACKS.md`.
- **1 server plan-dependent:** Clay's v3 MCP requires sufficient plan tier. ~80% your plan supports it; fallback options documented.

## After this kit is consumed

Delete this `gtm-os-bootstrap/` directory from Empire (or leave as historical reference — your call). The artifacts inside are one-shot migration tools, not living docs.
