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
Read the **company→ATS registry** in `.claude/references/target-companies.md` (21 companies confirmed 2026-09-08). Per company, curl its board and **`jq`-project to the compact shape BEFORE anything enters context** — raw boards are 0.5–12 MB, never dump them:

- **Greenhouse** (`anthropic, vercel, togetherai, verkada, gleanwork, snorkelai`):
  `curl -s "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"`
  → `jq '.jobs[] | {id, title, url:.absolute_url, loc:.location.name, updated:.updated_at}'`
  ⚠️ **Greenhouse exposes no posted date — `updated_at` is last-modified, and projecting it as `posted` is a real defect (fixed 2026-09-20).** A role open for months that got any edit this week reads as new. So: (a) project it as **`updated`**, never `posted`; (b) **never write it to the Roles DB `Posted Date`** — leave that property empty for Greenhouse rows; (c) **never use it alone to decide the recency window.** On 2026-09-19 this surfaced Vercel Enterprise AE and Anthropic CSM Tech as "this week" when both were long-open. For Greenhouse rows treat recency as **UNKNOWN** and confirm on the posting page before claiming a role is new. **Ashby `publishedAt` and Lever `createdAt` are true posted dates** and may be used normally.
- **Ashby** (`openai, notion, ramp, claylabs, perplexity, sierra, cursor, elevenlabs, langchain, baseten, cohere, writer, harvey, decagon, zip`):
  `curl -s "https://api.ashbyhq.com/posting-api/job-board/{board}"`
  → `jq '.jobs[] | select(.isListed) | {id, title, url:.jobUrl, loc:.location, posted:.publishedAt, remote:.isRemote}'`
- **Lever** (fallback only): `curl -s "https://api.lever.co/v0/postings/{co}?mode=json"`
  → `jq '.[] | {id, title:.text, url:.hostedUrl, loc:.categories.location, posted:.createdAt}'`

- **Filter to commercial titles BEFORE scoring** — keep title matches for Customer Success / CSM / Account Manager / Account Director / Account Executive / **Engagement Manager** / **Sales Director / Sales Lead / Sales Leader / Enterprise Sales Director / VP Sales / Head of Sales** / **`Growth Strategist|Growth Account|Growth AE|Scaled Growth` (never bare `Growth` — see the drop-list bullet)** / Solutions Consultant / Solutions Engineer / **Named Account / Client Director / Client Partner / Relationship Manager**; drop eng/product/design/recruiting/finance/marketing-IC (`grep -iE` on the projected title). **The keep-list is intentionally INCLUSIVE of leadership-signal titles (Sales Director, Head of Sales, Manager-of-function): they pass the title filter on purpose so IC / player-coach roles that happen to carry those titles aren't silently dropped — the v2.2 IC-vs-people-management gate in Step 3 then reads the JD and demotes the pure-leadership ones to C.** (This closes two real misses: "Enterprise Sales Director" @ Sierra and "Engagement Manager" @ Snorkel, both dropped by the old narrower list.) The description (`.content` / `.descriptionPlain`) is what Step 3 scores by *mechanism* — fetch it only for title-passing rows.
- **The drop-list runs AFTER the keep-list and WINS (fixed 2026-09-20).** A title that matched a keep term is still dropped when it also matches
  `Engineer|Developer|Designer|Scientist|Researcher|Recruiter|Accountant|Controller|Counsel|Marketing Manager|Product Manager|Program Manager|Content|Brand|Demand Gen`
  — **EXCEPT for the PROTECTED set `Solutions Engineer|Sales Engineer|Solutions Consultant`, which survive the drop-list.** Apply the protected check first: if the title matches a protected term, keep it and stop; otherwise drop-list wins over keep-list.
  ⚠️ **Why the exception exists (caught by the build-quality judge, 2026-09-20):** the keep-list deliberately keeps *Solutions Engineer*, and the drop term is a bare `Engineer` — without this carve-out, drop-wins silently kills a target title. That is a regression the first draft of this rule introduced.
  **The bare word `Growth` was the original leak** — on 2026-09-19 it passed "Growth Marketing Manager", "Senior Product Designer (Growth)" and "Senior Backend Engineer (Growth)", all dropped by hand. The keep-list above is now narrowed at source to `Growth Strategist|Growth Account|Growth AE|Scaled Growth`, so the leak is closed where the grep is built, not only here. (The leadership-signal titles — Sales Director, Head of Sales — match no drop term and are unaffected.)
- **Natural key = `{ats_vendor}:{id}`** (Step 2 dedup); freshness = `posted` for **Ashby and Lever only**. For **Greenhouse, freshness is UNKNOWN** — `updated` is not a posted date (see the caveat above).
- **Fan out 5–6 companies per distillation subagent** (curl works in subagents; the subagent declares `tools: Bash, Read` and returns a scored TSV so raw JSON never touches parent context).
- **Coverage = the 21 registry companies. Deferred (skip v1; recorded on YED-149):** Hugging Face, Intercom, Rippling, Mistral (no big-3 API by slug). The Step 4 digest MUST report gaps loudly: "N companies returned 0 rows / M unmapped" (registry-staleness guard).
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
- Dedupe against the Roles DB: `notion-search` scoped to the Roles data source by the natural key (stored in `Content Hash`) or `title company`; `notion-fetch` to confirm. **Freshness = the ATS `posted_at` for Ashby/Lever; UNKNOWN for Greenhouse** (Step 1 caveat — `updated_at` is last-modified, not a posted date). Skip roles already tracked unless status/materially changed.

---

## Step 3 — Score against the Target-Role ICP rubric (`icp_score`, 0–100) — self-contained

Mirrors `me-model.md` §1.5 (keep in sync). **Score by the role's *mechanism* (JD language), not its title.**

| Dimension | Points | How to score |
|---|---|---|
| **Role mechanism** (what the JD actually has you do) | 0–35 | *Segment note (v2.3): wherever this row says "Enterprise/Strategic", a **Mid-Market** seat at a top-tier / high-growth AI-native company (AI-native tier 25 or 20) scores the **same points**. MM at any other company is not covered by v2.3: score it on the JD's mechanism and write the call in `Notes`.* · Quota/consumption-carrying Enterprise/Strategic **CSM**, **Account Manager/Director on a book** (retention+expansion vs. a target), or **Growth Strategist** = **35** · **supported** Enterprise/Strategic **AE** (new logo *with* explicit inbound + BDR + product pull, often + existing book) = **28** · **Solutions Consultant / hybrid sell+CS** with a named post-sale partner = **25** · heavy-new-logo with only *some* support = **0** · full-cycle own-the-whole-funnel solo = **0 + REJECT** |
| **AI-native company tier** | 0–25 | frontier / AI-native (Anthropic, OpenAI, Clay, Vercel, Notion, Sierra, Perplexity, Cursor/Anysphere, …) = **25** · AI-forward high-growth (Ramp, Intercom, Verkada, Rippling, Zip, Glean, …) = **20** · AI-heavy SaaS = **12** · **traditional / non-AI = 0**. See `target-companies.md`. |
| **Leverage / support signal** (decisive — near-veto) | 0–20 | explicit BDR/marketing/inbound support, **existing book / expansion ownership**, **or PLG / product-led-growth as the primary motion** (product generates inbound demand) = **20** · partial = **10** · none / pure top-down-outbound / "own the whole funnel" = **0 + REJECT flag** |
| **AI-multiplier differentiator fit** | 0–10 | JD explicitly values building-with-AI / GTM-systems / technical fluency (SDLC, AI/ML) / consumption-model expertise ("you build with AI daily," "use AI creatively") = up to **10** |
| **Location / culture** | 0–10 | NYC or hybrid (in-person expectation) = **10** · remote-listed but the company has an **NYC office** (in-office optional) = **5** · **fully remote / no office / no in-person culture = 0** (a culture signal, not just a seat) |

**Auto-reject (flag, do not rank):** owns every stage incl. prospecting/demand-gen with **no existing-business component and no support named**; pure-quota hunter IC with no systems/AI surface; **below the OTE floor** (v2.3; the number lives in `me-model.md` §1.5); traditional/non-AI company — regardless of title. **Only the first two rejects (owns-the-whole-funnel, pure-quota hunter) can be lifted by the v2.1 exemptions below** (explicit existing-business component, or PLG-primary motion). **The OTE floor and the traditional/non-AI-company reject are hard gates: no exemption or intangible lifts them** (fixed 2026-09-19, YED-202: the old wording read as lifting all four).

**Tiers (v2.4, 2026-09-11):** **A = ≥85** (apply now) · **B = 60–84** (review) · **C = 40–59** (watch) · **drop < 40**.

> **Why 85, not 78 (raised 2026-09-11 — Alex).** The registry is pre-filtered to AI-native companies (tier 20–25) and most run PLG (leverage 20), so a supported/book-owning role reaches **75–80 on mechanism + tier + leverage alone**, *before* location — and location (max 10) cannot sink an 82. At ≥78, ~half of everything scanned landed in A, which destroyed A's usefulness as a triage signal. **85 restores discrimination** without distorting the mechanism scoring. Roles scoring 78–84 are still strong — they are B (review), not rejects.

### Rubric v2.1 — exemptions & intangibles (added 2026-09-08 — Alex)

Three refinements sit on top of the table above. **Every override-by-exemption call MUST be written and reasoned in the role's `Notes` — a silent bump is not allowed** (keeps the score honest + auditable).

1. **Hybrid new+existing is NOT a hunter.** If a JD *explicitly* names an existing-business / book / largest-account / retention / expansion component **alongside** new logo, the existing book counts as leverage: score leverage **≥10 (floor)**, up to **20** when the existing-book weight is substantial — and the own-the-whole-funnel REJECT does **not** fire. Only a role that owns *every* stage with **no** existing-business component and **no** named support is a pure-hunter reject.
2. **PLG exemption (primary-motion PLG → never drop an all-new-business role).** When the company's **primary GTM motion is PLG** (the product generates inbound demand), an all-new-business seat is **not** auto-rejected — the seller isn't owning the funnel alone; the product is. Floor it into **B/C tier** and set its position inside B/C by the intangibles read below.
3. **Intangibles lever.** For PLG-new-business and hybrid roles, weigh company **intangibles — growth trajectory/stage, founder & exec pedigree, funding, competitive position/market, role-specific upside**. Intangibles (a) *slide* position within B/C, and (b) when **exceptional** (e.g. top-decile growth + world-class founder/backing) grant a **TOP-OPTION EXEMPTION** promoting an otherwise-B role to **A**, and may **override the location hard-negative**. Analyze and state the intangibles explicitly.

*Worked example (2026-09-08):* Sierra **Enterprise Sales Director** (US-Remote) = structural **75 (B)** — hybrid new+existing, leverage 15, loc 0. Promoted to **A by intangibles exemption**: one of the fastest-growing companies globally + founder pedigree (Bret Taylor, OpenAI board chair / ex-co-CEO Salesforce; Clay Bavor, ex-Google Labs) + category-defining agents + funding. Rationale written to the role's Notes.

### Rubric v2.2 — IC vs. people-management axis (added 2026-09-08 — Alex; the title-disambiguation rule)

**Alex is targeting individual-contributor (IC) roles** that directly own a book / accounts / quota / relationships. **People-management / team-leadership roles are OUT for this search** — he wants back to direct impact and to grow *into* leadership via promotion, not enter at that level. Score the IC-vs-leadership axis **from the JD's responsibilities, never from the title string** — the title only raises the question.

**The single test: does the role carry a personal book / quota / accounts?** Yes → in (IC or player-coach). No, it's purely running a team → out.

- **IC = ideal (mechanism scored normally), title notwithstanding:** Account Manager, Customer Success Manager, Engagement Manager, Technical Account Manager, Account Director, an IC Sales Director. Here "Manager/Director" modifies the *accounts/book* owned.
- **Player-coach / team-lead / senior-IC "Lead" = ALSO desirable (keep as IC):** a role that **retains a personal book/quota** while also guiding others ("Account Executive Lead", "Account Manager Lead") is the exact direct-impact-and-grow path Alex wants. Guiding others is fine; the disqualifier is *pure* people-management with **no** book.
- **Pure people-management = drop to C or REJECT (regardless of other dimensions):** the role's primary job is managing a *team* with **no personal book/quota** — hire / coach / develop reps, own the team's number, carry direct reports as the job. Applies even when company + mechanism otherwise score high.
- **Syntactic tell (raises the question only — the JD's book test answers it):** **"[Function] Manager/Director"** (function as adjective — "Customer Success Manager", "Account Director") = usually IC; **"Manager, [Function]" / "Head of [Function]" / "Director of [Function]" / "VP …" / "Sales Manager"** = usually pure people-management → but confirm against the personal-book test, since a "Manager, X" can occasionally be a player-coach with a book (keep) and a "Lead" can occasionally be pure team-lead (still fine per above).

The JD responsibility pattern is the arbiter. When book-ownership can't be determined from available text, **flag it for review rather than scoring it high.**

### Rubric v2.3 — comp floor & level flexibility (added 2026-09-09 — Alex)

- **Comp gate = the OTE floor in `me-model.md` §1.5** (auto-reject below; the numbers and bands live only there, since comp targets stay private). Within range, use the me-model's **ideal / strong / fully-acceptable bands, and do NOT penalize the fully-acceptable band.** Comp is a floor + a tiebreaker, never a linear "higher = better"; weigh it against company growth/opportunity (a floor-level seat at a top-tier rocketship can beat an ideal-band seat at a laggard). When comp isn't posted, **don't infer a reject** — treat as unknown and score on mechanism.
- **Posted RANGE vs. the floor — rule not yet written; decision owed (YED-210, opened 2026-09-20).** The gate is phrased for a single OTE number, but postings publish ranges. Until Alex rules: a range that **straddles** the floor, or **tops out exactly at** it, is **HELD — written to the Roles DB with `ICP Tier` left blank and a `Notes` line naming the ruling owed**, never auto-ranked and never auto-rejected. Two roles hit this on 2026-09-19 (Vercel Scaled Commercial AE Install Base; Anthropic CSM Enterprise Tech). Do not invent a midpoint/top/bottom convention — that is the decision YED-210 exists to make.
- **Level flexibility — Mid-Market is IN at top-tier companies** *(wired into the Role-mechanism row of the scoring table via its segment note; change both together).* Score **MM roles at high-growth / top-tier / more-technical AI-native companies as full fits on MECHANISM** (book / expansion / consumption ownership); do **NOT** down-rank for segment size vs. Enterprise/Strategic. This encodes Alex's deliberate **step-back-to-step-forward** strategy (land MM at a top-tier company, prove value, work back to Enterprise). Enterprise/Strategic stays ideal; MM at the right company is squarely in.

---

## Step 4 — Present scored roles + create/confirm Roles DB (HITL gate)

If the Roles DB doesn't exist, present this proposed schema and create it via `notion-create-database` only after Alex approves (mirrors the existing DB pattern):

**Roles DB schema**
- `Role Title` (title)
- `Company` (text)
- `Source` (select: greenhouse / lever / ashby / rssapp_li / apollo / dice / manual)
- `Location` (text) · `Workplace` (select: remote / hybrid / onsite)
- `URL` (url) · `Company URL` (url)
- `ICP Score` (number) · `ICP Tier` (select: A / B / C / drop)
- `Status` (select: new / reviewing / applied / interviewing / rejected / offer / archived)
- `Posted Date` (date — the ATS `posted_at`, for freshness; **leave EMPTY for Greenhouse rows** — `updated_at` is last-modified and writing it here launders a wrong date into the DB) · `Date Found` (date)
- `Content Hash` (text — the dedup natural key `{ats_vendor}:{ats_job_id}`, or `title|company` fallback) · `Notes` (text)
- (later) relations to Companies / People

Then present the ranked roles:

```
## Role Radar — {date}, {location}, last {recency}

### A-tier ({n})
- **{Role}** @ {Company} — ICP {score} — {workplace}, {location}
  why: {1-line — archetype + AI-nativeness + tier + signals}
  {detailsPageUrl} | {companyPageUrl}
### B-tier ... ### C-tier (collapsed counts) ... ### Dropped ({n}, reasons)

### Held — needs your ruling ({n})
- **{Role}** @ {Company} — **no tier** — {the undefined case, e.g. "posted range straddles the OTE floor"} — {what it would score on mechanism alone}
```
**Freshness marker per row:** a Greenhouse row has **no posted date** (Step 1 caveat), so never let the `last {recency}` header imply one. Mark Greenhouse rows `freshness: UNKNOWN`; only Ashby/Lever rows may show a posted date.

**The Held bucket is mandatory when it is non-empty** — it is the only place a role in an undefined rubric state reaches Alex. A held role is never silently ranked and never silently dropped. Current known case: the posted-comp-range-vs-floor gap (YED-210).

End with: AI-disclosure line (if Dice used) + **"Add which roles to the Roles DB? (A-tier / all / numbers / none)"**. STOP for approval.

---

## Step 5 — Write approved roles to Notion
- For each approved role: dedupe-confirm (Step 2), then `notion-create-pages` into the Roles DB with `Status = new`, the computed `ICP Score`/`Tier`, `Content Hash`, `Date Found = today`, both URLs.
- **`Posted Date`: write it ONLY for Ashby/Lever rows. Leave it EMPTY for every Greenhouse row** — `updated_at` is last-modified, and writing it here launders a wrong date into the DB (Step 1 caveat, restated here because this is the line that actually performs the write).
- **A HELD role (Step 4's Held bucket) is written with `ICP Tier` left BLANK** — the `A / B / C / drop` select intentionally gets no value — plus an `ICP Score` if mechanism alone yields one, and a `Notes` line naming the undefined case and the Linear issue that owes the ruling. Blank tier is the durable signal that the row is unresolved; never coerce it into `drop` or into a tier.
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
