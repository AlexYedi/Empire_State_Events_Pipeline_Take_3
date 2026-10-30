# 05 · Public NYC AI Rooms MCP server (empire-state-hub) · Tier 4, stretch

Source: roadmap build **B4**, "Public NYC AI Rooms MCP server (remote MCP on Vercel over the Rooms archive)".
Read-only, with public Rooms fields only. This is the hardest test of the day: a new protocol surface, an external SDK, and contract tests.
It lives inside the hub as a route, so it needs no new repo and no new install.

## Product
Any MCP client (Claude, Cursor) can connect to `https://<hub>/api/mcp` and ask about NYC AI events Alex has
attended: who spoke, which companies were in the room, what series. It doubles as the Anthropic/MCP portfolio opener.

## Tools (read-only)
- `list_rooms({ series?, from?, to? })` → `[{ slug, name, date, series, location }]`
- `get_room({ slug })` → the room exactly as in `rooms.json` (speakers: name/title/company/LinkedIn only)
- `search_speakers({ query })` → speakers matching name or company, each with the rooms they appeared in
- `list_series()` → the distinct series with room counts

## Technical
- Route: `src/app/api/mcp/route.ts`, Streamable HTTP transport. Use the official MCP TypeScript SDK
  (`@modelcontextprotocol/sdk`) or Vercel's `mcp-handler`. **Pick one, justify it on the plan card, and check that it supports Next 16.**
- Data: import from `src/lib/rooms.ts` only. Never import Notion, Linear, or anything under `src/lib/notion` or `src/lib/linear`.
- Input validation with zod. Unknown slug → a structured MCP error, not a 500.
- No auth (public data), no write tools, no env vars.
- Tests (`node --test`): each tool returns the schema-valid shape on the committed `rooms.json`; output contains
  no field outside the public allowlist (name, title, company, linkedin, roles, plus room fields); an unknown slug errors cleanly.
- Docs: a short `docs/mcp.md` with the URL, the tool list, and a Claude Desktop / Claude Code config snippet.

**Suggested executables.** (1) SDK choice + route skeleton + `list_series`. (2) The other three tools. (3) Contract tests. (4) Docs.

**Done when:** `npx @modelcontextprotocol/inspector` against the local dev server lists 4 tools and each returns data,
the tests pass, and `pnpm check && pnpm lint && pnpm build` pass.
