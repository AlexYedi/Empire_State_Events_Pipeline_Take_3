# Plan — Job-Search Engine v1 (Target-Role ICP + Role Radar v2, on the MI graph spine)

## Context

Alex is re-engaging his job search (post-Labor Day pickup + a natural GKY offramp). The existing
`role-radar` skill mis-models his target as the **Forward Deployed GTM Engineer** (a technical
systems archetype) — which is why a Dice run surfaced GTM-*systems-engineer* seats he does **not**
want. His actual target, confirmed with 7 exemplar JDs (Anthropic CSM Top Accounts, OpenAI Account
Director, Clay AE-Strategic + Enterprise Growth Strategist, Vercel Enterprise AE, Notion Solutions
Consultant) and a locked rubric, is:

> **Quota-carrying commercial roles — CSM / Account Manager / Account Director / Growth-focused
> seller on a book — at top-tier AI-native companies**, where deep GTM + systems + AI-building is
> the *differentiator*, not the job title. Score by the role's **mechanism (JD language), not its
> title**. The decisive disqualifier: **owning the entire funnel alone** (demand→intent→pipe-gen→
> close) with no BDR / marketing / inbound / existing-book leverage — "succeeding *in spite of* the
> company." He wants leverage (existing book + expansion, and/or pipe-gen support) so his energy
> compounds.

Alex chose **whole-job-search-engine** scope and asked for the *most robust, durable structure that
powers hiring AND feeds back into the overall knowledge base*. The enabling discovery
(exploration): the **market-intel-spine was explicitly built for the job-search lens** —
`event.kind ∈ {role_posted, application, interview}`, `company` first-class, `role` carried as an
event (not a first-class object). So the Job-Search Engine shares the **same Supabase graph**
(`oicikjyzmxqfomrrqkvf`, REST-only) as trend/voice/content — the feedback loop he asked for.

Outcome: a durable Job-Search Engine — one candidate source-of-truth, a re-pointed Role Radar that
finds the *right* roles and lands them in both Notion and the graph, and the scaffolding for resume
+ interview consumers — all reading one ICP and writing one graph.

## Durable architecture (the recommendation)

**The Job-Search Engine IS the Job-Search lens of the Market-Intelligence Engine**, on the shared
graph spine. Five components, one ICP, one graph:

1. **`me-model.md`** = candidate "self" source-of-truth. Add a **Target-Role ICP** section (the 4
   role shapes + leverage filter + location-culture rule + differentiator + comp band). Every
   downstream artifact reads this.
2. **Role Radar v2** = find → score → track roles. Rubric v2 (below), source-mix v2, a new Notion
   **Roles DB**, and a **graph-producer step** (roles → `company` upsert + `role_posted` event +
   `event_entity` edges) so roles become first-class graph signals.
3. **Interview-Prep Dossier** (already shipped, MI-Engine M1 / YED-105) — wire it to *read the
   me-model ICP* (coordination, not a rebuild).
4. **Resume / Positioning Tailor** (new) — consumes me-model ICP + a target role → tailored
   resume/cover framing. Scaffold now, harden later.
5. **Shared substrate + surface** — the graph spine (feeds the overall knowledge base) + the Empire
   State Hub job-search surface (future).

**Linear structure:** repurpose the currently-empty **"Getting Hired Flow" project → "Job-Search
Engine"** as the first-class execution home, **linked to the Market-Intelligence Engine** project
(shared spine). Rationale: durable program home, feeds the shared graph (no silo), extensible to
more lenses/consumers off the same me-model + graph.

## The Target-Role ICP (goes verbatim into `me-model.md` §"Target-Role ICP")

**Four role shapes (best → also-yes), defined by mechanism not title:**
1. Quota/consumption-carrying **Enterprise/Strategic CSM** (adoption→expansion→consumption growth on
   named/top accounts). *(Anthropic CSM Top Accounts.)*
2. **Account Director / Account Manager on a book** (retention + growth + expansion vs. a
   revenue/consumption target). *(OpenAI AD Large Enterprise — archetype; that req is Delhi, geo N/A.)*
3. **Growth Strategist / growth-focused seller** (expansion + adoption + strategic advisory).
   *(Clay Enterprise Growth Strategist.)*
4. **Supported Enterprise/Strategic AE** (new logo **with** inbound + BDR + product pull, often
   existing-book/expansion). *(Clay AE-Strategic, Vercel EAE, Notion SC-with-BDR+OA.)* — accepted
   **only** when support is explicit.

**Decisive filter (near-veto):** leverage/support present (existing book/expansion and/or
BDR/marketing/inbound) → keep. Own-the-whole-funnel-solo, no support → **REJECT**.
**Company GTM-motion (added by Alex):** strongly prefer **PLG / product-led-growth as the primary
selling style** — the product generates inbound demand, the biggest structural tailwind for a seller
(the ultimate "leverage, not in-spite-of"). Flag pure top-down/outbound-only enterprise motions where
the seller carries all demand-gen.
**Differentiator (his edge, folded in):** deep GTM + GTM-systems/AI-building + technical fluency
(SDLC, AI/ML, consumption models); weight up roles that explicitly value building-with-AI.
**Comp band:** at or above the OTE floor in the private me-model (numbers redacted 2026-09-19).

## Rubric v2 — replaces `role-radar/SKILL.md` Step 3 (weights LOCKED by Alex)

| Dimension | Pts | Scoring |
|---|---|---|
| **Role mechanism** (by JD, not title) | 0–35 | CSM-quota / AD-AM-book / Growth Strategist = 35 · supported Ent/Strategic AE = 28 · SC-hybrid w/ post-sale partner = 25 · **heavy-new-logo w/ some support = 0** · full-funnel-solo = 0 + **REJECT** |
| **AI-native company tier** | 0–25 | frontier/AI-native = 25 · AI-forward high-growth = 20 · AI-heavy SaaS = 12 · **traditional = 0** |
| **Leverage / support signal** (decisive) | 0–20 | explicit BDR/marketing/inbound, existing-book/expansion, **or PLG / product-led-growth as the primary motion (product-generated inbound demand)** = 20 · partial = 10 · none / pure top-down-outbound / "own the whole funnel" = 0 + **REJECT flag** |
| **AI-multiplier differentiator fit** | 0–10 | role explicitly values build-with-AI / GTM-systems / technical fluency / consumption-model expertise = 10 |
| **Location / culture** | 0–10 | **NYC or hybrid = 10** · **remote-listed but has an NYC office (in-office optional) = 5** · **fully remote / no office / no in-person culture = 0** (culture signal, not just seat) |

**Tiers:** A ≥78 (apply) · B 60–77 · C 40–59 · drop <40.
**Auto-reject:** "own every stage incl. prospecting/demand-gen," no support named; pure-hunter IC;
below the comp floor; non-AI company — regardless of title.

## Source-mix v2 (`role-radar/SKILL.md` Step 1)

Re-point from Dice-primary (keyword-noisy; the roles Alex wants live on company careers pages +
LinkedIn, not Dice):
- **Target-company careers-page monitoring (NET-NEW, no repo precedent):** WebFetch each target's
  careers/greenhouse/lever/ashby page; **each new domain needs a `settings.local.json` WebFetch
  allowlist entry** (LinkedIn already allowlisted). Support greenhouse/lever/ashby first.
- **RSS.app from saved LinkedIn searches** (existing pattern — `WebFetch` the feed; Step 0.2 setup).
- **Apollo job-postings at named targets** (credit-gated; exact wording `"This will consume N
  credits. Do you want to proceed?"`; **may be blocked on the free plan → confirm; if blocked,
  careers+RSS carry it**).
- **Dice = secondary/keyword sweep** (downweighted; keep the mandatory AI-disclosure line).
- **Graph-producer (NET-NEW Step 5.5):** mirror `trend-radar/SKILL.md` Step 5.5 exactly — REST-only
  to `oicikjyzmxqfomrrqkvf` (never the Supabase MCP), pre-flight `SUPABASE_API_KEY`; per role: upsert
  `company` → insert `event {kind:"role_posted", source, url, confidence, metadata}` → link
  `event_entity` (company:hiring, topic:archetype). Additive, never a gate.

## Target-company list (seed → Alex redlines in the PRD) → new `.claude/references/target-companies.md`

- **Frontier / AI-native:** Anthropic, OpenAI, Clay, Vercel, Notion, Sierra, Perplexity,
  Anysphere/Cursor, ElevenLabs, LangChain, Baseten, Together, Modal, Hugging Face, Cohere, Mistral.
- **AI-forward high-growth:** Ramp, Intercom, Verkada, Rippling, Zip, Glean, Harvey, Hebbia, Writer,
  Decagon.
(`stack-readme.md` already references a `target_companies.md` that never existed — create it for real
as the shared list role-radar + resume-tailor + interview-prep all read.)

## Files to change (consistency surface — from exploration)

1. **`.claude/references/me-model.md`** — append §"Target-Role ICP" (the ICP above); add target list ref.
2. **`.claude/skills/role-radar/SKILL.md`** — rewrite Step 3 rubric (→ v2); replace FDGTME archetype
   language (line ~67) + Tier-1 list (line ~73); add source-mix v2 (Step 1 + Step 0.2); add Step 5.5
   graph-producer.
3. **`.claude/commands/scan-roles.md`** — sync duplicated tier cutoffs + dimension names (line ~20)
   and description (line ~2) to v2; add the new-source orchestration; keep the single-thread skill-run
   shape per `command-orchestration-convention.md`.
4. **`CLAUDE.md`** line ~82 (`<standing_context>`) — reconcile the target-role statement to the ICP.
5. **Notion** — create the **Roles DB** (`notion-create-database`, schema from SKILL Step 4) under the
   NYC AI Event Content Hub; capture its `collection://` URL back into the SKILL + `notion-schema.md`.
6. **`.claude/references/target-companies.md`** — NEW (the list above).
7. **Resume/Positioning Tailor** — NEW minimal scaffold (`.claude/skills/…` + optional `/…` command)
   that reads me-model ICP + a role; full build deferred.

## Rigor artifacts (DoD gate — this is a non-trivial, multi-file build)

- **PRD one-pager → ChatPRD** (`create_document`, projectId = the project's `openaiAssistantId`;
  origin may 502 under load → retry) → **mirror to Notion** Project Ideas.
- **Linear:** repurpose "Getting Hired Flow" → "Job-Search Engine"; sub-issues: (a) me-model ICP +
  CLAUDE.md L82, (b) rubric v2, (c) source-mix v2 + Roles DB, (d) graph-producer Step 5.5, (e)
  target-companies.md, (f) resume-tailor scaffold, (g) interview-prep ICP wiring.
- **One adversarial pass** — `alex:cto-principal-architect` on the **net-new/riskiest** design
  (careers-page monitoring + the graph-producer), before coding those.
- **`/dod-close`** at the end (met/waived-with-reason + correction-rounds).

## Sequencing (build now → scaffold → defer)

- **Phase A (this build):** PRD + Linear + adversarial pass · me-model Target-Role ICP · CLAUDE.md
  L82 · `target-companies.md` · **rubric v2 + scan-roles sync** · **Roles DB** created.
- **Phase B (this build if budget):** source-mix v2 (careers-monitoring + `settings.local.json`
  allowlist entries) · graph-producer Step 5.5.
- **Phase C (scaffold/defer):** resume/positioning tailor · interview-prep ICP-consumption wiring ·
  Hub job-search surface. **Registry-freeze caveat:** any new skill/agent needs a *fresh session* to
  test end-to-end.

## Verification (end-to-end)

1. **Rubric re-score:** re-run `/scan-roles` (or re-score the roles already pulled) → confirm the
   Ramp GTM-Business-Systems-Engineer / Ironclad Director-GTM-Eng / Alloy roles now land **C/drop**,
   and CSM/AM/AD/Growth roles at AI-native cos land **A** (≥78). Location rule visibly separates
   NYC/hybrid (10) from fully-remote-no-office (0).
2. **Notion:** Roles DB exists with the schema; approved roles written with `ICP Score`/`Tier`/`Status=new`.
3. **Graph:** `GET /event?kind=eq.role_posted&select=title,confidence,source&order=event_date.desc` returns the
   new role signals with provenance; `event_entity` edges link to `company`.
4. **ICP consumption:** me-model §Target-Role ICP reads cleanly; interview-prep can cite it.
5. **Build-quality judge** (`/judge-build`) on the rewritten `role-radar/SKILL.md` + `scan-roles.md`
   (dangling-ref + command-completeness) before close.

## Open questions (redline at approval)

- **Target-company list** — add/cut names (esp. AI-forward tier).
- **Careers-monitoring ATS coverage** — greenhouse/lever/ashby first? which target domains to
  allowlist in the first batch?
- **Apollo** — confirm whether job-postings are blocked on the free plan (drives how much careers +
  RSS must carry).
- **Resume-tailor** — minimal scaffold now, or hold entirely until role-radar v2 is proven?

## Adversarial-review revisions (2026-09-08, `cto-principal-architect`)

Reviewed the net-new pieces before coding. Adopted:
1. **Ingest via ATS boards JSON APIs, not WebFetch scraping.** Greenhouse
   (`boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`) · Lever
   (`api.lever.co/v0/postings/{company}?mode=json`) · Ashby
   (`api.ashbyhq.com/posting-api/job-board/{board}`) — `curl`+`jq` (Bash), full-fidelity, no
   model-mangling, 3 API hosts (no 25-domain allowlist). Confirm each with a 10-min curl spike.
   Build a **company→ATS registry** in `target-companies.md`; cover the ~18–20 on the big-3, **skip
   custom/Workday in v1** (clean 18 > flaky 25).
2. **Dedup natural key = `{ats_vendor}:{job_id}`** (not title|company). Freshness = ATS posted
   timestamp. Subagent-distill 5–6 companies/batch (curl works in subagents; raw JSON out of parent
   context). Digest MUST report coverage gaps ("N returned 0 / M unmapped" — registry-staleness guard).
3. **Graph-producer (Step 5.5) DEFERRED to v1.1** (YED-149). Roles deliver value in the Notion Roles
   DB; wire the spine only after dedup is proven (blast radius = private DB, not the shared spine).
   When built: key on job-id, `event_date` = posted date, idempotent upsert, `confidence`=1.0, reuse
   **bounded** existing Topic archetypes (never mint from the role path), watch volume-asymmetry
   mis-weighting (hundreds of roles vs a handful of trend/voice signals).

**Revised Phase B = ATS-API source-mix + Roles DB (Notion only). Graph → v1.1.**
