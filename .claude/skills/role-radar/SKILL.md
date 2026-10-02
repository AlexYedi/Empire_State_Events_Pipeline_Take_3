---
name: role-radar
description: "Signal scanner — job search & tracking. Aggregates roles from legitimate sources (ATS boards APIs — Greenhouse/Lever/Ashby/Workable via `ats_pull.py` — primary; + Apollo-at-targets, credit-gated, optional), dedupes on the ATS job-id, scores each against Alex's Target-Role ICP (me-model §1.5), and lands them in a Notion Roles DB as a status Kanban, mirrored to the MI graph as role_posted events (Step 5.5). Manual trigger, human-in-the-loop. No LinkedIn scraping."
---

# Role Radar Skill

You are Alex's **role-sensing + tracking engine**. LinkedIn's Jobs API is closed to new partners and scraping the account is ruled out, so we aggregate roles from legitimate sources (the ATS boards APIs, plus Apollo at named targets when asked), score them against Alex's **Target-Role ICP**, and track application status in Notion.

**The target — source of truth is `.claude/references/me-model.md` §1.5 "Target-Role ICP" (read it; keep this rubric in sync):** quota-carrying **commercial** roles at top-tier **AI-native** companies. **The in-scope shapes are defined ONCE, in Step 3 — go read them there; they are deliberately not restated here** (a second copy drifts, which is what happened on 2026-09-24) (`.claude/references/target-companies.md`). Deep GTM + systems + AI-building is the **differentiator, not the job title**. **Score by the role's MECHANISM (what the JD says it does), not its title.** The decisive filter is **leverage vs. "in spite of the company"**: keep roles that give leverage (existing book/expansion, BDR/marketing/inbound support, or a **PLG** product-led motion); reject owning the entire funnel alone.

This is a **signal scanner** feeding the Empire State pipeline (its siblings `trend-radar` and `voice-radar` were pruned 2026-09-28).

**Why this exists (concept primer for Alex):** a job tracker is just a small CRM with a scoring function on the front. The value isn't the list — it's (1) **one inbox** for roles that today scatter across Dice/LinkedIn/company pages, (2) a **consistent ICP score** so you spend application energy on A-tier fits, not whatever surfaced last, and (3) **status tracking** so nothing falls through. The scoring rubric (Step 3) is the opinionated part and is self-contained here.

**Ground rules (Empire State conventions):**
- **Ethics:** Public ATS APIs and official endpoints only. No LinkedIn scraping.
- **Human-in-the-loop:** Present scored roles for review before any Notion write.
- **Credit discipline:** Apollo and Clay are credit-metered. Confirm spend explicitly (exact wording below).
- **Notion plan constraint (re-verified 2026-09-27):** `notion-query-data-sources` SQL **does** work on this plan but is **quota-capped** — the shared workspace limit tripped after ~12 queries in one session. Spend it on ONE bulk pass per run (Content Hash + Tier + Status + Notes for every row — a few LIMIT/OFFSET pages of the same query, ~100 rows each), then use `notion-fetch` per page for anything else. Never design a step that needs SQL more than once; when the cap hits mid-run, fall back to `notion-fetch` — it has no such cap.
- **No fabricated numbers / honest gaps:** if a source errors, say so.

**Scope:** ATS boards APIs (primary) + Apollo-at-targets (credit-gated, optional); Notion-only; manual trigger. **Dice and RSS.app were REMOVED 2026-09-27 (Alex):** never used in any scan to date — the Dice connector was never authenticated and no RSS.app feed was ever generated — and the 38-board ATS registry covers the target list directly. Do not re-add them without a coverage case. The **graph-producer** (roles → MI graph) is **live as Step 5.5** (YED-149, 2026-09-27 — shipped once the Roles DB proved its dedup: 203 rows, 0 duplicate ATS keys). Scheduled ingestion stays deferred.

---

## Inputs
- **(Optional) Role focus** — defaults to Alex's target archetypes (below). May narrow, e.g. "just GTM engineer + RevOps".
- **(Optional) Location** — default **New York City** + **Remote (US)**.
- **(Optional) Recency** — default last 7 days on the ATS `posted` date (Ashby/Lever/Workable); Greenhouse rows have no posted date and are treated as UNKNOWN freshness.

---

## Step 0 — One-time setup (first run only)
1. **Roles DB:** the Notion **Roles** database EXISTS (created 2026-09-08) — data source `collection://3a174257-e90b-48be-b4bb-097ba5dc4231`, under the NYC AI Event Content Hub. `notion-fetch` it to confirm the live schema before writes (schema also in Step 4). If it were ever missing, recreate via `notion-create-database` with the Step 4 schema (HITL).

---

## Step 1 — Pull from sources (parallel)

Primary = the **ATS boards JSON APIs** (public, first-party — the endpoints companies' own careers
widgets call; legitimate, full-fidelity, not scraping). Read the company→ATS registry in
`.claude/references/target-companies.md` ({ATS vendor, board token/slug} per company).

### 1a. ATS boards APIs — `ats_pull.py` (code, zero tokens), PRIMARY
Pulling and filtering the boards is deterministic, so it is a script, not a model step (YED-255, 2026-10-02;
it replaced the 5–6-companies-per-subagent `curl | jq` fan-out). Run from the repo root:
```bash
python3 .claude/scripts/ats_pull.py --out <scratch>/roles.tsv --jd-dir <scratch>/jds
```
It reads the **company→ATS registry** in `.claude/references/target-companies.md` (38 boards: Greenhouse,
Ashby, Lever, Workable — endpoints in the script's `ENDPOINT` map), fetches each board (one retry with a
longer timeout), projects it, and writes one TSV row per role that passes the filters, plus one plain-text
JD per row in `--jd-dir` for the Step 3 mechanism read. Raw boards (0.5–12 MB) never enter context. A full
run takes seconds. `--only "Anthropic,Runway"` narrows it; `--selftest` pins the parsing and filter rules.

What the script enforces (change the rule in the script, then this summary):
- **Natural key = `{ats_vendor}:{id}`** (Workable: `shortcode`), the Step 2 dedup key.
- **Greenhouse has no posted date.** `updated_at` is last-modified, so it lands in `updated` and `posted`
  stays EMPTY; never write it to `Posted Date` and never use it for recency (the 2026-09-19 Vercel/Anthropic
  "new this week" defect). Ashby `publishedAt`, Lever `createdAt` (epoch ms → ISO) and Workable
  `published_on` are true posted dates.
- **Title filter = keep-list, then the drop-list WINS** (`KEEP` / `DROP` in the script). Keep is inclusive of
  leadership-signal titles on purpose (Sales Director, Head of Sales) so the v2.2 book test in Step 3 decides
  them. Drop includes `Engineer` (Solutions/Sales Engineer are OUT, ruled 2026-09-24, no protected carve-out),
  `Technical Account Manager` (OUT, 2026-09-27) and marketing titles; `Growth` only passes as
  `Growth Strategist|Growth Account|Growth AE|Scaled Growth` (the bare word leaked marketing roles on 09-19).
- **Location default = NYC + Remote (US)** (Inputs): a remote role naming a non-US region drops; `--any-location`
  turns it off. Scoring still applies the location row in Step 3.
- **Struck-through registry companies** (`~~Name~~`, coverage-only, every role auto-rejects on company fit) are
  skipped, not fetched, and counted in the gap line.
- **Comp** columns come from `comp_gate.py` (Step 3, v2.3), computed **without** the emerging-seller flag.
- **Gap line (stderr), reported in Step 4 verbatim:** "N companies returned 0 rows … · M errored … · K excluded …
  · comp gate: ON|OFF". A failed board is never "no roles". **Registry-staleness guard, still manual:** also
  report the count of target companies with no big-4 board (the "five holdouts" table in `target-companies.md`),
  since the script only sees the registry.

### 1b. Apollo job-postings at named targets (credit-gated — optional)
- Only if Alex wants roles at specific targets *not* on the big-4 ATS. **Off by default** — the scan runs the boards; Apollo is a per-request add-on. Resolve the org ID via Apollo org search, then call `mcp__claude_ai_Apollo_io__apollo_organizations_job_postings`.
- **MANDATORY confirmation — say this EXACT message before the call:** `"This will consume 1 credit. Do you want to proceed?"` If pulling N companies, confirm the TOTAL: "This will consume N credits. Do you want to proceed?" Do not proactively show the balance. Do not call without explicit approval. Apollo may be blocked on the free plan → report and skip.


---

## Step 2 — Dedupe
- **Natural key** for ATS-API roles = **`{ats_vendor}:{ats_job_id}`** (stable across re-runs). For Apollo roles with no ATS id, fall back to `content_hash` = lowercased, whitespace-collapsed `title + "|" + company`.
- Collapse the same role appearing across sources into one record (keep all source links + the natural key).
- Dedupe against the Roles DB: one bulk SQL read of `Content Hash` (see the plan constraint above), or `notion-search` scoped to the Roles data source by the natural key / `title company`; `notion-fetch` to confirm.
- **Fallback dedup on `title|company` (added 2026-09-27, YED-224).** Rows written before ATS keying carry `Content Hash = title|company`, and a natural-key check alone cannot see them. After the natural-key pass, compare each candidate's normalized `title|company` (lower-case, whitespace-collapsed, company alias-tolerant) against the DB. A hit means the legacy row IS this posting → **re-key that row** (write the ATS key into `Content Hash`, plus `Source`, `URL`, `Posted Date`) instead of creating a second row. Why: the 09-19 scan wrote ~20 title-hash rows; the 09-24 scan duplicated five of them by ATS key, and the 09-27 scan would have re-added Runway's Strategic Enterprise AE as "new". Re-posts (same title+company, old id gone, new id live — Writer did this to four roles on 09-22) are handled the same way: re-key, don't duplicate. **Freshness = the ATS `posted_at` for Ashby, Lever and Workable; UNKNOWN for Greenhouse** (Step 1 caveat — `updated_at` is last-modified, not a posted date). Skip roles already tracked unless status/materially changed.

---

## Step 3 — Score against the Target-Role ICP rubric (`icp_score`, 0–100) — self-contained

Mirrors `me-model.md` §1.5 (keep in sync). **Score by the role's *mechanism* (JD language), not its title.**

> **THE FIVE SHAPES — nothing else is in scope (ruled by Alex 2026-09-24).**
> **(1) Account Manager · (2) Account Director · (3) quota-carrying Customer Success Manager ·
> (4) "all channel" Account Executive — existing book AND outbound · (5) Growth Strategist —
> *only when it carries a book* (see the Growth book test below).**
>
> **(5) GROWTH STRATEGIST — IN, but the title only raises the question (ruled 2026-09-24).** Alex:
> *"growth strategist should be kept, but it is tough to keep up with all of the fun names that
> companies come up with — so yes, but no when it refers only to a marketing function, which many
> companies do."* So run the **same book test** rubric v2.2 uses for IC-vs-management:
> **does the role own accounts, a book, expansion or a quota?** Yes → score it as shape 5.
> No — it runs campaigns, demand-gen, lifecycle, funnel metrics or content → **it is a marketing
> function and is OUT: score it `0 + REJECT` on role mechanism**, however good the company. (Stated
> explicitly because every other failure path in Step 3 names its bucket — judge round 2.) This is the *same leak* the narrowed keep-list
> already guards (bare `Growth` passed "Growth Marketing Manager" on 2026-09-19); the grep narrows
> the candidates, the book test decides them.
>
> **No technical roles.** Solutions Engineer, Sales Engineer, Solutions Consultant **and (ruled 2026-09-27) Technical Account Manager** are **OUT** — the first three
> were removed from the keep-list, the drop-list carve-out and the scoring table on 2026-09-24. A
> pre-sales/technical-win seat is not a book.
>
> Shape 4 is the one that needs care: **"all channel" means existing + outbound, not outbound-only.**
> An AE who prospects and closes with no existing-business component is still the own-the-whole-funnel
> reject, however good the comp. *(Worked example, 2026-09-24: Modal AE-Enterprise KEPT — "drive new
> business by generating pipeline" AND "expand existing accounts"; Traversal Enterprise AE REJECTED —
> "own the full sales cycle, from strategic prospecting to closing" with only Sales-Engineering support
> and no book, despite an OTE above the floor and an in-person NYC seat.)*
>
> **"End-to-end" framing is the own-the-funnel signal (ruled 2026-09-28 — Alex).** When the JD's
> framing puts the whole onus on the seller ("end-to-end", "own the entire sales cycle", "from first
> touch to close"), score it as the own-the-funnel case. **A passing mention of expansion or renewal
> does NOT offset that framing:** judge the JD's weight, not an isolated keyword. *(Worked example,
> 2026-09-28: Factory AE Mid-Market NYC demoted B→C. It mentions "expansion and renewal" but is a
> pure-play end-to-end AE. Cognition Account Director Enterprise (East) has the same shape and was
> promoted to A only under the v2.1 #3 intangibles exemption: company quality, recent raise, pay,
> enterprise AD seat, SDRs prospecting the account list. Reason written to Notes.)*
>
> **VERTICAL-TERRITORY REJECT: financial services and government (ruled 2026-09-28 — Alex).** A role
> whose territory is **financial services** (banks, insurers, capital markets, FSI) or
> **government / public sector** (federal, state & local, SLED, agencies) is **`drop`**, however good
> the company or pay. Alex, verbatim: *"I do not have enough subject matter expertise to honestly compete
> for those roles … those are specific customer types that people build a career around selling to."*
> This is separate from the company-level vertical exclusion (e.g. legal AI): it applies to the
> **territory of a role at a horizontal company** (Databricks FS AE, Scale AI FS AE, Databricks State &
> Local all dropped 2026-09-28). Check title AND JD territory before scoring. In the Roles DB, a
> dropped row is set `ICP Tier = drop` + `Status = archived`, **never deleted**, so dedup keeps
> blocking the re-add. **Healthcare / life-sciences territory is unruled:** send it to the Held bucket; don't assume either way.

| Dimension | Points | How to score |
|---|---|---|
| **Role mechanism** (what the JD actually has you do) | 0–35 | *Segment note (v2.3): wherever this row says "Enterprise/Strategic", a **Mid-Market** seat at a top-tier / high-growth AI-native company (AI-native tier 25 or 20) scores the **same points**. MM at any other company is not covered by v2.3: score it on the JD's mechanism and write the call in `Notes`.* · Quota/consumption-carrying Enterprise/Strategic **CSM**, **Account Manager/Director on a book** (retention+expansion vs. a target), or **Growth Strategist** *(shape 5 — apply the Growth book test above; a marketing-function "Growth Strategist" is OUT, not 35)* = **35** · **"all channel" Enterprise/Strategic AE (shape 4)** — new logo *with* explicit inbound + BDR + product pull **AND a named existing-book / expansion component** = **28**. **The existing-book component is REQUIRED, not optional** (tightened 2026-09-24; the old wording read "often + existing book", which let an outbound-only seat score 28). **Support without a book is NOT shape 4** — it scores **0 on this row** (the heavy-new-logo bucket). **To be precise about what that does and does not mean** (the earlier wording said "rescued only by the PLG exemption", which was ambiguous — judge round 2): a support-named/no-book role is **NOT auto-rejected**, because the auto-reject below requires *no existing-business component **AND** no support named*. It simply scores 0 on mechanism, which caps it out of A on arithmetic alone. At a **PLG-primary** company the PLG exemption (v2.1 #2) then floors it into **B/C**; everywhere else it keeps the 0 and lands where the remaining dimensions put it · heavy-new-logo with only *some* support = **0** · full-cycle own-the-whole-funnel solo = **0 + REJECT** |
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

- **IC = ideal (mechanism scored normally), title notwithstanding:** Account Manager, Customer Success Manager, Engagement Manager, Account Director, an IC Sales Director. *(Technical Account Manager was listed here until 2026-09-27; it is a technical seat and is OUT — see the drop-list.)* Here "Manager/Director" modifies the *accounts/book* owned.
- **Player-coach / team-lead / senior-IC "Lead" = ALSO desirable (keep as IC):** a role that **retains a personal book/quota** while also guiding others ("Account Executive Lead", "Account Manager Lead") is the exact direct-impact-and-grow path Alex wants. Guiding others is fine; the disqualifier is *pure* people-management with **no** book.
- **Pure people-management = drop to C or REJECT (regardless of other dimensions):** the role's primary job is managing a *team* with **no personal book/quota** — hire / coach / develop reps, own the team's number, carry direct reports as the job. Applies even when company + mechanism otherwise score high.
- **Syntactic tell (raises the question only — the JD's book test answers it):** **"[Function] Manager/Director"** (function as adjective — "Customer Success Manager", "Account Director") = usually IC; **"Manager, [Function]" / "Head of [Function]" / "Director of [Function]" / "VP …" / "Sales Manager"** = usually pure people-management → but confirm against the personal-book test, since a "Manager, X" can occasionally be a player-coach with a book (keep) and a "Lead" can occasionally be pure team-lead (still fine per above).

The JD responsibility pattern is the arbiter. When book-ownership can't be determined from available text, **flag it for review rather than scoring it high.**

### Rubric v2.3 — comp floor & level flexibility (added 2026-09-09 — Alex)

- **Comp gate = `comp_gate.py` against the OTE floor in `me-model.md` §1.5** (the number lives only there;
  the script reads it at runtime). Run it per row with the posted text: `comp_gate.py --text "<comp_text>"
  [--emerging]` → `PASS | REJECT | UNKNOWN`, the figure used and a ready-made `Notes` line. Write that line to
  `Notes` verbatim. `ats_pull.py` already fills the verdict for the non-emerging case. **REJECT = the hard
  auto-reject; UNKNOWN (nothing posted, or non-USD) is never a reject:** score on mechanism. Comp is a floor + a
  tiebreaker, never "higher = better" (a floor-level seat at a rocketship can beat an ideal-band seat at a laggard).
  **The model owns two judgment inputs, the script owns the arithmetic:**
  1. **Emerging seller?** The JD pitches the seat at an early-career seller (ex-SDR/BDR, "next step into
     full-cycle ownership", "first closing role") → re-run with `--emerging`.
  2. **Label sanity.** The script labels each posted band from its own clause: OTE / base ("salary", "base pay",
     "+ commission", "Offers Commission") / unlabelled; when a posting shows both a base and an OTE band, the OTE
     band is the one tested. Non-USD amounts (CA$, MX$, GBP via Lever) come back UNKNOWN. If the JD body contradicts the structured field, the JD body is the posting:
     re-run on the JD sentence.
  The rulings the script implements (2026-09-27, Alex, YED-210 — pinned by `--selftest`): OTE or unlabelled
  band → **midpoint** · base/salary band → **top** · emerging seller → **low end** · one-sided "up to $X" →
  **X − $20K** · two rules at once → the **higher** figure · **exactly at the floor clears** (≥).
  A range is no longer a Held case.
- **Level flexibility — Mid-Market is IN at top-tier companies** *(wired into the Role-mechanism row of the scoring table via its segment note; change both together).* Score **MM roles at high-growth / top-tier / more-technical AI-native companies as full fits on MECHANISM** (book / expansion / consumption ownership); do **NOT** down-rank for segment size vs. Enterprise/Strategic. This encodes Alex's deliberate **step-back-to-step-forward** strategy (land MM at a top-tier company, prove value, work back to Enterprise). Enterprise/Strategic stays ideal; MM at the right company is squarely in.

---

## Step 4 — Present scored roles + create/confirm Roles DB (HITL gate)

If the Roles DB doesn't exist, present this proposed schema and create it via `notion-create-database` only after Alex approves (mirrors the existing DB pattern):

**Roles DB schema**
- `Role Title` (title)
- `Company` (text)
- `Source` (select: greenhouse / lever / ashby / **workable** / apollo / manual — `rssapp_li` and `dice` remain in the live Notion select for historical rows only and are never written since the 2026-09-27 removal) — **`workable` was added to the live Notion select 2026-09-24**; it was missing since Workable support shipped on 09-21, so a Hugging Face row had no valid `Source` value to write. Caught by the build-quality judge, round 2.
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
- **{Role}** @ {Company} — **no tier** — {the undefined case — one the rubric has no rule for} — {what it would score on mechanism alone} — **Linear: {YED-nnn, filed this turn}**
```
**Freshness marker per row:** a Greenhouse row has **no posted date** (Step 1 caveat), so never let the `last {recency}` header imply one. Mark Greenhouse rows `freshness: UNKNOWN`; **Ashby, Lever and Workable** rows may show a posted date.

**The Held bucket is mandatory when it is non-empty** — it is the only place a role in an undefined rubric state reaches Alex. A held role is never silently ranked and never silently dropped. The posted-range-vs-floor case was ruled 2026-09-27 (v2.3 midpoint rule, YED-210) and is no longer a Held case; the bucket exists for the next undefined state, and every new one gets a Linear issue the same turn.

End with: **"Add which roles to the Roles DB? (A-tier / all / numbers / none)"**. STOP for approval.

---

## Step 5 — Write approved roles to Notion
- For each approved role: dedupe-confirm (Step 2), then `notion-create-pages` into the Roles DB with `Status = new`, the computed `ICP Score`/`Tier`, `Content Hash`, `Date Found = today`, both URLs.
- **`Source`: write the ATS vendor that produced the row** — the same token used in the `Content Hash` natural key (`{ats_vendor}:{id}`), so the two can never disagree. One of the eight select options above.
- **`Posted Date`: write it for Ashby, Lever and Workable rows. Leave it EMPTY for every Greenhouse row** — `updated_at` is last-modified, and writing it here launders a wrong date into the DB (Step 1 caveat, restated here because this is the line that actually performs the write).
- **A HELD role (Step 4's Held bucket) is written with `ICP Tier` left BLANK** — the `A / B / C / drop` select intentionally gets no value — plus an `ICP Score` if mechanism alone yields one, and a `Notes` line naming the undefined case and the Linear issue that owes the ruling. Blank tier is the durable signal that the row is unresolved; never coerce it into `drop` or into a tier.
- Existing role with material change → `notion-update-page` (don't duplicate).
- Status is Alex's to advance (new → reviewing → applied → …); the skill only sets `new` on intake.

---

## Step 5.5 — Mirror the written roles into the MI graph (YED-149)

Every Roles row written or re-keyed in Step 5 becomes one `role_posted` event in the graph, plus a `company —subject→`
edge. Spec + the reasoning behind every rule: `docs/archive/notes/yed-149-spec-2026-09-27.md`. Runs inline in this thread
(REST through `spine_client`; never the Supabase MCP). Additive, never a gate: if `SUPABASE_API_KEY` is unset, print
`graph write skipped: SUPABASE_API_KEY not set` in Step 6 and stop here.

1. **Pull the rows just written, SQL shape.** `notion-query-data-sources` on the Roles data source, selecting
   `url, "Role Title", "Company", "Content Hash", "ICP Tier", "ICP Score", "date:Posted Date:start", "Source",
   "userDefined:URL", "Status", "Location", "Workplace"` and filtering to this run's pages. **Never select `Notes`**:
   Alex's free text stays in Notion.
2. **Write them to a scratch file** as `{"roles": [<rows verbatim>]}` (in the session scratchpad, never the repo).
3. **Dry-run, then live:**
   `.venv/bin/python .claude/scripts/substrate.py ensure-roles --manifest <file> --aliases-from .claude/references/target-companies.md --dry-run`,
   then the same without `--dry-run`. `--aliases-from` maps board slugs and registry names (`acmelabs`, `acme`) to
   the name the graph already uses (`Acme`, `Acme (Parent)`). Read the dry run's `would create N companies:`
   line first. A listed company that already exists in the graph under another name (e.g. `Acme` vs `Acme Labs`)
   is a duplicate in the making: add `"company_aliases": {"acme": "Acme Labs"}` to the manifest (or fix the
   registry name), re-run the dry run, and only then write. A `REFUSED <ats key>` line means the same posting sits
   on two Notion pages; resolve that in Notion.
4. **Rules the verb enforces (don't re-implement them):** the Roles page id is the only idempotency key (a rescan
   creates 0; a missing page id is refused); ICP Tier `drop` is skipped and counted; Greenhouse rows get no
   `event_date`; `confidence = 1.0`; topics are never minted from this path.
5. Step 6 summary line: `Graph: N role events (created X · matched Y · skipped drop Z)`.

What the graph does with them: `/event-deep-research`'s Context Pack **never lists roles in the ledger**. A seed
company gets one count line instead ("Acme — N tracked roles (A:x B:y)"), and applications/interviews appear
nowhere (migration 0011 + `retrieve.py`).

---

## Step 6 — Close out
- Summary: roles added by tier, sources used, any source gaps, credits spent (if Apollo used).
- **Rows in the DB that are NOT on the boards (added 2026-09-27, YED-224):** count and name every non-archived row whose `Content Hash` was not seen this run. Before calling one closed, check it against the **raw, unfiltered** board — the title filter drops out-of-scope titles (Solutions Consultant/Engineer since the 09-24 ruling), and those read as "gone" when they are merely out of scope. Closed → propose `Status = archived` with a dated note; re-posted under a new id → re-key the existing row (Step 2). Present this as its own block in the close-out; it is HITL like every other write.
- Offer next: "Pull contacts/hiring managers at the A-tier companies?" → Clay enrich (credit-gated). Tie A-tier targets back to the Notion Companies DB where they already exist.

---

## Failure modes
- **An ATS board errors, times out or rate-limits** — `ats_pull.py` retries once with a longer timeout, then names it in the "M errored" gap line. Report it in Step 4 by name. Never treat a failed board as "no roles".
- **`ats_pull.py` exits 3** (registry unreadable, or 0 rows parsed because the registry heading/table drifted) — stop and say which; don't fall back to hand-curling 38 boards.
- **OTE floor unreadable** (`comp_gate` exit 3, or ats_pull's "no OTE floor" warning, e.g. running from a worktree where the gitignored `me-model.md` is absent) — pass `--me-model <path>` or `--floor`; never treat a missing floor as PASS.
- **Apollo org not found / API blocked** — Apollo may be blocked on the free plan; if the call fails, report honestly and run on the ATS boards alone. Never fabricate roles.
- **Roles DB schema drift** — `notion-fetch` the data source; live schema wins.

## Confidence & honest gaps
- **Strong (high):** aggregation + consistent ICP scoring + status tracking across the 38 ATS boards (+ Apollo when asked).
- **Gap (high confidence):** this does not see the full LinkedIn Jobs index (API closed, no scraping). RSS.app of saved searches was the intended partial bridge and was removed 2026-09-27 unused; TheirStack (paid) is the option if coverage ever becomes the constraint. Name the gap; don't imply full LinkedIn coverage.

## Reuses / references
- **`.claude/references/me-model.md` §1.5 "Target-Role ICP"** — the source of truth this rubric mirrors (keep in sync).
- **`.claude/references/target-companies.md`** — the target-company list + company→ATS registry (board tokens).
- `alex:lead-prioritization`, `alex:firmographic-analysis` — fit-scoring discipline.
- Notion DBs — **Roles `collection://3a174257-e90b-48be-b4bb-097ba5dc4231`** (this skill's tracking Kanban); Companies `collection://d5910dc3-8327-4b49-9294-fc9499709a98`, People `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86` (for later relations).
- Graph-producer (Step 5.5): `substrate.py ensure-roles` · spec `docs/archive/notes/yed-149-spec-2026-09-27.md` · `.claude/references/market-intel-spine.md`.
- Tools — `.claude/scripts/ats_pull.py` (ATS boards) + `.claude/scripts/comp_gate.py` (comp gate), `mcp__claude_ai_Apollo_io__apollo_organizations_job_postings` (optional), `notion-search`/`notion-fetch`/`notion-create-database`/`notion-create-pages`/`notion-update-page`.
