# gtm-os Handoff Prompt

**Purpose:** paste the fenced block below as the FIRST message in a fresh Claude Code session opened in your local `gtm-os` clone. It primes the session with full context to execute the migration from Empire's bootstrap kit and run the 4-wave MCP verification ladder.

**Pre-flight checklist (do BEFORE pasting):**

1. ✅ `gtm-os` repo exists on GitHub (you confirmed this earlier)
2. ✅ `gtm-os` cloned locally somewhere (e.g., `~/code/gtm-os`)
3. ✅ Empire repo also cloned locally (you'll reference its bootstrap kit) — OR you're OK with the agent fetching files from raw GitHub URLs
4. ✅ Open Claude Code CLI in the `gtm-os` directory: `cd ~/code/gtm-os && claude`
5. ✅ Paste the fenced block below as your first message

---

## Handoff prompt (copy everything between the tildes)

~~~
You are landing in a fresh Claude Code session in my new repo `AlexYedi/gtm-os`. Read this brief carefully before doing anything. Do not restate it. Do not relitigate decisions already made. Ask clarifying questions only on items not addressed below.

# Identity

I'm Alex — senior enterprise B2B SaaS professional (12+ years), currently Lead Enterprise Account Director at GKY Industries, building toward a Clay-tier full-stack GTM engineer role. I have a working, shipped events pipeline (separate repo: `AlexYedi/Empire_State_Events_Pipeline_Take_3`) that turns calendar invites into pre-event research, networking prep, and content via Claude skills + direct MCP writes to Notion and HubSpot. That events pipeline is the FIRST COMPLETED MODULE of gtm-os — it is not being restarted, redesigned, or absorbed.

# What gtm-os is

gtm-os is the always-on GTM operating system that wraps the events pipeline plus a much broader signal layer:
- Always-on signal capture (Calendar, Gmail, Granola meetings, Linear, PostHog, HubSpot, Clay enrichment)
- Notion as research + content hub
- Vercel-deployed Hub site (Project B — parallel track, not the focus right now)
- n8n for orchestration only (NOT integration plumbing — that lesson is from the predecessor failure)

This is Phase 0 — exploration and inventory, NOT build. Maps to Clay's three-rung maturity model: data foundation → modeling → activation. Phase 0 builds rung-1 + rung-2 understanding before any rung-3 activation.

# Why this repo exists separately from Empire

The Signal Pipeline started inside Empire as a subdirectory. It outgrew that scope. Splitting into gtm-os keeps Empire stable as the events-pipeline-canonical repo and gives gtm-os its own commit history from day one. Empire still uses the same Notion DBs and HubSpot records — they share the data plane, the codebases are separate.

# Your immediate task

Execute the migration from Empire's bootstrap kit + Signal_Pipeline planning artifacts INTO this gtm-os repo, then run the MCP verification ladder.

The bootstrap kit is at:
- GitHub path: `AlexYedi/Empire_State_Events_Pipeline_Take_3` branch `claude/resume-strategy-planning-06kMr` directory `Signal_Pipeline/gtm-os-bootstrap/`
- Raw URLs (use WebFetch if you don't have local Empire access):
  - https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/gtm-os-bootstrap/.mcp.json
  - https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/gtm-os-bootstrap/.env.example
  - https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/gtm-os-bootstrap/MCP_SETUP.md
  - https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/gtm-os-bootstrap/MCP_FALLBACKS.md
  - https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/gtm-os-bootstrap/README.md

The planning artifacts to also migrate:
- https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/PROJECT_BRIEF.md
- https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/SESSION_BOOTSTRAP.md
- https://raw.githubusercontent.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/claude/resume-strategy-planning-06kMr/Signal_Pipeline/Phase_0/ (5 files inside this directory — list and fetch each)

# Sequence of operations

Do these IN ORDER. Stop after each numbered step and confirm with me before the next one if anything is ambiguous.

1. **Fetch and place the bootstrap kit at gtm-os repo root:**
   - `.mcp.json` → `gtm-os/.mcp.json`
   - `.env.example` → `gtm-os/.env.example`
   - `MCP_SETUP.md` → `gtm-os/MCP_SETUP.md`
   - `MCP_FALLBACKS.md` → `gtm-os/MCP_FALLBACKS.md`
   - The bootstrap `README.md` is migration-only — DO NOT copy that one to gtm-os root, it's a one-shot doc.

2. **Fetch and place the planning artifacts:**
   - `PROJECT_BRIEF.md` → `gtm-os/PROJECT_BRIEF.md`
   - `SESSION_BOOTSTRAP.md` → `gtm-os/SESSION_BOOTSTRAP.md`
   - `Phase_0/` directory → `gtm-os/Phase_0/` (preserve structure)

3. **Update `gtm-os/SESSION_BOOTSTRAP.md`** to reflect new repo coordinates:
   - Repo name: `AlexYedi/gtm-os` (was Empire)
   - Active branch: whatever I tell you the current gtm-os main/develop branch is — ASK ME if you don't know
   - Latest commit: update to whatever the post-migration commit hash will be
   - Remove any Empire-specific paths (`Signal_Pipeline/...`) and rewrite as gtm-os root paths

4. **Verify `.gitignore` excludes `.env`:**
   - If gtm-os has a `.gitignore`, confirm it has `.env` and `.env.*` (with `!.env.example` exception)
   - If not, create one with these entries

5. **Stop and ASK ME** before proceeding to MCP setup. I need to:
   - Create `.env` from `.env.example` and paste tokens
   - Confirm I'm ready to walk the verification ladder

6. **Once I confirm**, walk me through `MCP_SETUP.md` waves 0→3:
   - Wave 0: Notion + HubSpot (carry-over from Empire — same Private App token, same Notion OAuth)
   - Wave 1: Linear, PostHog, Clay, n8n, Supabase (API-key fastpath)
   - Wave 2: Granola, Vercel (OAuth-hosted)
   - Wave 3: Google Calendar, Gmail (FLAGGED — may need fallback per MCP_FALLBACKS.md)
   - Run the verification queries listed in MCP_SETUP.md after each wave. Stop on any failure and debug with me.

7. **Final commit + push to gtm-os** with a clean message documenting the migration. Do NOT include any tokens in commit messages or files committed.

# Locked decisions (do not relitigate)

- gtm-os is its own repo, separate from Empire. ✅ Decided.
- Tier 1 = 11 MCP servers (Notion, HubSpot, Linear, PostHog, Clay, Granola, Google Calendar, Gmail, Supabase, Vercel, n8n). ✅ Decided.
- n8n at Tier 1 with scoping: orchestration/triggers/notifications only, NOT integration layer for fragile API chains. The predecessor events pipeline failed because n8n was used as integration plumbing — gtm-os keeps it for what it's good at. ✅ Decided.
- Google Workspace via hosted `*.mcp.claude.com` URLs first; fall back to npm-package + own GCP OAuth client only if hosted URLs don't authenticate from CLI. ✅ Decided, fallback documented.
- Phase 0 is exploration + inventory, NOT build. ✅ Decided.

# What NOT to do

- Don't redesign the events pipeline. It's done and lives in Empire. gtm-os reads from / writes to the same Notion + HubSpot, but doesn't touch Empire's skill code.
- Don't add a 12th MCP server to Tier 1. Hold the line at 11.
- Don't commit `.env`, tokens, or any credentials. If you see them about to be staged, refuse and flag to me.
- Don't auto-merge or push to a main/master branch without explicit approval.
- Don't skip the verification queries — every wave needs a confirmed working query before adding the next wave.

# Confidence + risk flags

- 8/11 servers should work cleanly on first install: ~90% (Notion, HubSpot, Linear, PostHog, Clay, Granola, Vercel, Supabase)
- 2 servers flagged: Google Calendar + Gmail at `*.mcp.claude.com` URLs ~65% confidence in CLI; fallback in MCP_FALLBACKS.md
- 1 server plan-dependent: Clay's v3 MCP requires sufficient plan tier; ~80% your plan supports it

# When done

1. Confirm all 11 servers green in `/mcp`
2. Confirm `gtm-os/SESSION_BOOTSTRAP.md` has correct repo coordinates
3. Tell me to come back to the Empire session to run the cleanup (remove migrated files from Empire's `Signal_Pipeline/`, leaving only `MOVED.md`)

Start by fetching the bootstrap kit. Show me the file list once placed. Don't proceed past step 5 without my confirmation.
~~~

---

## After the new session does its work

Come back here (Empire session) and say "clean up Empire" — I'll remove the migrated content and leave only `MOVED.md` as the breadcrumb.
