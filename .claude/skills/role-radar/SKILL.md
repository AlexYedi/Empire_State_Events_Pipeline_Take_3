---
name: role-radar
description: "Signal scanner — job search & tracking. Aggregates roles from legitimate sources (ATS boards APIs — Greenhouse/Lever/Ashby via curl — primary; + RSS.app saved-search feeds, Apollo-at-targets, Dice secondary), dedupes on the ATS job-id, scores each against Alex's Target-Role ICP (me-model §1.5), and lands them in a Notion Roles DB as a status Kanban. Notion-only, manual trigger, human-in-the-loop. No LinkedIn scraping."
---

# Role Radar Skill

You are Alex's **role-sensing + tracking engine**. LinkedIn's Jobs API is closed to new partners and scraping the account is ruled out, so we aggregate roles from legitimate sources (ATS boards APIs + RSS + Apollo + Dice), score them against Alex's **Target-Role ICP**, and track application status in Notion.

**The target — source of truth is `.claude/references/me-model.md` §1.5 "Target-Role ICP" (read it; keep this rubric in sync):** quota-carrying **commercial** roles — Enterprise/Strategic **CSM**, **Account Manager/Director on a book**, **Growth Strategist**, or a **supported** Enterprise/Strategic AE — at top-tier **AI-native** companies (`.claude/references/target-companies.md`). Deep GTM + systems + AI-building is the **differentiator, not the job title**. **Score by the role's MECHANISM (what the JD says it does), not its title.** The decisive filter is **leverage vs. "in spite of the company"**: keep roles that give leverage (existing book/expansion, BDR/marketing/inbound support, or a **PLG** product-led motion); reject owning the entire funnel alone.

This is one of three **signal scanners** feeding the Empire State pipeline (alongside `trend-radar` and `voice-radar`).

**Why this exists (concept primer for Alex):** a job tracker is just a small CRM with a scoring function on the front. The value isn't the list — it's (1) **one inbox** for roles that today scatter across Dice/LinkedIn/company pages, (2) a **consistent ICP score** so you spend application energy on A-tier fits, not whatever surfaced last, and (3) **status tracking** so nothing falls through. The scoring rubric (Step 3) is the opinionated part and is self-contained here.

**Ground rules (Empire State conventions):**
- **Ethics:** Public APIs, RSS, official endpoints only. No LinkedIn scraping. RSS.app reads a *feed you generated from a saved search* — it never touches your account.
- **Human-in-the-loop:** Present scored roles for review before any Notion write.
- **Credit discipline:** Apollo and Clay are credit-metered. Confirm spend explicitly (exact wording below). Dice MCP is free.
- **Notion plan constraint (verified 2026-06-24):** no Business+AI tier → use `notion-search` (scoped to the Roles data source) + `notion-fetch` for dedup. Do NOT use `notion-query-data-sources`.
- **No fabricated numbers / honest gaps:** if a source errors, say so.

**Scope:** ATS boards APIs (primary) + RSS.app + Apollo-at-targets + Dice (secondary); Notion-only; manual trigger. The **graph-producer** (roles → MI spine) and scheduled ingestion are **deferred to v1.1** (Linear "Job-Search Engine" YED-149) — roles first prove out in the Notion Roles DB before writing the shared graph.

---

## Inputs
- **(Optional) Role focus** — defaults to Alex's target archetypes (below). May narrow, e.g. "just GTM engineer + RevOps".
- **(Optional) Location** — default **New York City** + **Remote (US)**.
- **(Optional) Recency** — Dice `posted_date`: `ONE`/`THREE`/`SEVEN` days. Default `SEVEN`.
- **(Optional) RSS.app feed URLs** — Alex pastes feed URLs he generated from saved LinkedIn searches (see Setup).

---

## Step 0 — One-time setup (first run only)
1. **Roles DB:** the Notion **Roles** database EXISTS (created 2026-09-08) — data source `collection://3a174257-e90b-48be-b4bb-097ba5dc4231`, under the NYC AI Event Content Hub. `notion-fetch` it to confirm the live schema before writes (schema also in Step 4). If it were ever missing, recreate via `notion-create-database` with the Step 4 schema (HITL).
2. **RSS.app feeds (optional, recommended):** tell Alex once — in RSS.app, paste a saved LinkedIn job-search URL to generate an RSS feed; save the feed URL(s) and pass them to this skill. This is the legitimate LinkedIn bridge; the feed is read, the account is never automated.

---

## Step 1 — Pull from sources (parallel)

Primary = the **ATS boards JSON APIs** (public, first-party — the endpoints companies' own careers
widgets call; legitimate, full-fidelity, not scraping). Read the company→ATS registry in
`.claude/references/target-companies.md` ({ATS vendor, board token/slug} per company).

### 1a. ATS boards APIs — `curl` + `jq` (Bash), PRIMARY
Read the **company→ATS registry** in `.claude/references/target-companies.md` (20 companies confirmed 2026-09-08). Per company, curl its board and **`jq`-project to the compact shape BEFORE anything enters context** — raw boards are 0.5–12 MB, never dump them:

- **Greenhouse** (`anthropic, vercel, togetherai, verkada, gleanwork`):
  `curl -s "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"`
  → `jq '.jobs[] | {id, title, url:.absolute_url, loc:.location.name, posted:.updated_at}'`
- **Ashby** (`openai, notion, ramp, claylabs, perplexity, sierra, cursor, elevenlabs, langchain, baseten, cohere, writer, harvey, decagon, zip`):
  `curl -s "https://api.ashbyhq.com/posting-api/job-board/{board}"`
  → `jq '.jobs[] | select(.isListed) | {id, title, url:.jobUrl, loc:.location, posted:.publishedAt, remote:.isRemote}'`
- **Lever** (fallback only): `curl -s "https://api.lever.co/v0/postings/{co}?mode=json"`
  → `jq '.[] | {id, title:.text, url:.hostedUrl, loc:.categories.location, posted:.createdAt}'`

- **Filter to commercial titles BEFORE scoring** — keep title matches for Customer Success / CSM / Account Manager / Account Director / Account Executive / Growth / Solutions Consultant/Engineer; drop eng/product/design/recruiting (`grep -iE` on the projected title). The description (`.content` / `.descriptionPlain`) is what Step 3 scores by *mechanism* — fetch it only for title-passing rows.
- **Natural key = `{ats_vendor}:{id}`** (Step 2 dedup); freshness = `posted`.
- **Fan out 5–6 companies per distillation subagent** (curl works in subagents; the subagent declares `tools: Bash, Read` and returns a scored TSV so raw JSON never touches parent context).
- **Coverage = the 20 registry companies. Deferred (skip v1):** Hugging Face, Intercom, Rippling, Mistral (no big-3 API by slug). The Step 4 digest MUST report gaps loudly: "N companies returned 0 rows / M unmapped" (registry-staleness guard).
- 3 fixed API hosts — no per-company `settings.local.json` allowlist churn. **Endpoints + field shapes verified live 2026-09-08.**

### 1b. RSS.app feeds from saved LinkedIn searches (manual paste — optional)
- For each feed URL Alex provides, `WebFetch` it; extract title, company, location, link, pubDate.
- Flag any feed that returns empty/broken (LinkedIn markup changes can break RSS.app feeds — best-effort, not a spine).

### 1c. Apollo job-postings at named targets (credit-gated — optional)
- Only if Alex wants roles at specific targets *not* on the big-3 ATS. Resolve the org ID via Apollo org search, then call `mcp__claude_ai_Apollo_io__apollo_organizations_job_postings`.
- **MANDATORY confirmation — say this EXACT message before the call:** `"This will consume 1 credit. Do you want to proceed?"` If pulling N companies, confirm the TOTAL: "This will consume N credits. Do you want to proceed?" Do not proactively show the balance. Do not call without explicit approval. Apollo may be blocked on the free plan → report and skip.

### 1d. Dice — `mcp__claude_ai_Dice__search_jobs` (free, SECONDARY keyword sweep)
- Keyword-noisy and skews contract/staffing/IT — a supplementary net, not the spine. Keywords for the target shapes: `"Customer Success Manager"`, `"Account Director"`, `"Enterprise Account Manager"`, `"Growth Strategist"`, `"Enterprise Account Executive"`. Set `location`, `workplace_types=["Remote","Hybrid","On-Site"]`, `posted_date="SEVEN"`. Capture title, company, location, workplace, `detailsPageUrl` + `companyPageUrl`, posted date.
- **MANDATORY AI disclosure (Dice tool requirement):** *"These job listings were found using AI-powered search. Verify details directly with employers before applying."*

---

## Step 2 — Dedupe
- **Natural key** for ATS-API roles = **`{ats_vendor}:{ats_job_id}`** (stable across re-runs). For Dice/RSS/Apollo roles with no ATS id, fall back to `content_hash` = lowercased, whitespace-collapsed `title + "|" + company`.
- Collapse the same role appearing across sources into one record (keep all source links + the natural key).
- Dedupe against the Roles DB: `notion-search` scoped to the Roles data source by the natural key (stored in `Content Hash`) or `title company`; `notion-fetch` to confirm. **Freshness = the ATS `posted_at`.** Skip roles already tracked unless status/materially changed.

---

## Step 3 — Score against the Target-Role ICP rubric (`icp_score`, 0–100) — self-contained

Mirrors `me-model.md` §1.5 (keep in sync). **Score by the role's *mechanism* (JD language), not its title.**

| Dimension | Points | How to score |
|---|---|---|
| **Role mechanism** (what the JD actually has you do) | 0–35 | Quota/consumption-carrying Enterprise/Strategic **CSM**, **Account Manager/Director on a book** (retention+expansion vs. a target), or **Growth Strategist** = **35** · **supported** Enterprise/Strategic **AE** (new logo *with* explicit inbound + BDR + product pull, often + existing book) = **28** · **Solutions Consultant / hybrid sell+CS** with a named post-sale partner = **25** · heavy-new-logo with only *some* support = **0** · full-cycle own-the-whole-funnel solo = **0 + REJECT** |
| **AI-native company tier** | 0–25 | frontier / AI-native (Anthropic, OpenAI, Clay, Vercel, Notion, Sierra, Perplexity, Cursor/Anysphere, …) = **25** · AI-forward high-growth (Ramp, Intercom, Verkada, Rippling, Zip, Glean, …) = **20** · AI-heavy SaaS = **12** · **traditional / non-AI = 0**. See `target-companies.md`. |
| **Leverage / support signal** (decisive — near-veto) | 0–20 | explicit BDR/marketing/inbound support, **existing book / expansion ownership**, **or PLG / product-led-growth as the primary motion** (product generates inbound demand) = **20** · partial = **10** · none / pure top-down-outbound / "own the whole funnel" = **0 + REJECT flag** |
| **AI-multiplier differentiator fit** | 0–10 | JD explicitly values building-with-AI / GTM-systems / technical fluency (SDLC, AI/ML) / consumption-model expertise ("you build with AI daily," "use AI creatively") = up to **10** |
| **Location / culture** | 0–10 | NYC or hybrid (in-person expectation) = **10** · remote-listed but the company has an **NYC office** (in-office optional) = **5** · **fully remote / no office / no in-person culture = 0** (a culture signal, not just a seat) |

**Auto-reject (flag, do not rank):** owns every stage incl. prospecting/demand-gen with no support named; pure-quota hunter IC with no systems/AI surface; sub-$180K; traditional/non-AI company — regardless of title.

**Tiers:** **A = ≥78** (apply now) · **B = 60–77** (review) · **C = 40–59** (watch) · **drop < 40**.

---

## Step 4 — Present scored roles + create/confirm Roles DB (HITL gate)

If the Roles DB doesn't exist, present this proposed schema and create it via `notion-create-database` only after Alex approves (mirrors the existing DB pattern):

**Roles DB schema**
- `Role Title` (title)
- `Company` (text)
- `Source` (select: dice / rssapp_li / apollo / manual)
- `Location` (text) · `Workplace` (select: remote / hybrid / onsite)
- `URL` (url) · `Company URL` (url)
- `ICP Score` (number) · `ICP Tier` (select: A / B / C / drop)
- `Status` (select: new / reviewing / applied / interviewing / rejected / offer / archived)
- `Posted Date` (date — the ATS `posted_at`, for freshness) · `Date Found` (date)
- `Content Hash` (text — the dedup natural key `{ats_vendor}:{ats_job_id}`, or `title|company` fallback) · `Notes` (text)
- `Source` select values: greenhouse / lever / ashby / rssapp_li / apollo / dice / manual
- (later) relations to Companies / People

Then present the ranked roles:

```
## Role Radar — {date}, {location}, last {recency}

### A-tier ({n})
- **{Role}** @ {Company} — ICP {score} — {workplace}, {location}
  why: {1-line — archetype + AI-nativeness + tier + signals}
  {detailsPageUrl} | {companyPageUrl}
### B-tier ... ### C-tier (collapsed counts) ... ### Dropped ({n}, reasons)
```
End with: AI-disclosure line (if Dice used) + **"Add which roles to the Roles DB? (A-tier / all / numbers / none)"**. STOP for approval.

---

## Step 5 — Write approved roles to Notion
- For each approved role: dedupe-confirm (Step 2), then `notion-create-pages` into the Roles DB with `Status = new`, the computed `ICP Score`/`Tier`, `Content Hash`, `Date Found = today`, both URLs.
- Existing role with material change → `notion-update-page` (don't duplicate).
- Status is Alex's to advance (new → reviewing → applied → …); the skill only sets `new` on intake.

---

## Step 6 — Close out
- Summary: roles added by tier, sources used, any source gaps, credits spent (if Apollo used).
- Offer next: "Pull contacts/hiring managers at the A-tier companies?" → `voice-radar` / Clay enrich (credit-gated). Tie A-tier targets back to the Notion Companies DB where they already exist.

---

## Failure modes
- **Dice thin / off-target** — vary keywords; widen `posted_date` to `SEVEN`; drop the location filter for remote-heavy archetypes.
- **RSS.app feed broken** — note it; LinkedIn markup churn breaks these periodically. Best-effort source.
- **Apollo org not found / API blocked** — Apollo may be blocked on the free plan; if the call fails, report honestly and fall back to Dice + RSS.app. Never fabricate roles.
- **Roles DB schema drift** — `notion-fetch` the data source; live schema wins.

## Confidence & honest gaps
- **Strong (high):** aggregation + consistent ICP scoring + status tracking across Dice/RSS/Apollo.
- **Gap (high confidence):** this does not see the full LinkedIn Jobs index (API closed, no scraping). RSS.app of saved searches is the legitimate partial bridge; TheirStack (paid) widens coverage later. Name the gap; don't imply full LinkedIn coverage.

## Reuses / references
- **`.claude/references/me-model.md` §1.5 "Target-Role ICP"** — the source of truth this rubric mirrors (keep in sync).
- **`.claude/references/target-companies.md`** — the target-company list + company→ATS registry (board tokens).
- `alex:lead-prioritization`, `alex:firmographic-analysis` — fit-scoring discipline.
- Notion DBs — **Roles `collection://3a174257-e90b-48be-b4bb-097ba5dc4231`** (this skill's tracking Kanban); Companies `collection://d5910dc3-8327-4b49-9294-fc9499709a98`, People `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` (for later relations).
- Graph-producer (deferred v1.1): `trend-radar/SKILL.md` Step 5.5 pattern + `.claude/references/market-intel-spine.md`.
- Tools — `mcp__claude_ai_Dice__search_jobs`, `mcp__claude_ai_Apollo_io__apollo_organizations_job_postings`, `notion-search`/`notion-fetch`/`notion-create-database`/`notion-create-pages`/`notion-update-page`.
