# Company-signals lane — replacement stack at four tiers

**For:** Alex · **Date:** 2026-11-05 · **Status:** proposal, nothing built · **Scope:** lane 2 (`lane_registry.company_signals`, inactive) in `docs/proposals/2026-11-04-market-lens-and-slices.md` §2
**Evidence:** vendor pages fetched 2026-11-05 unless dated; live reads: akta `account_status` (subscription, 951.01 credits), Clay CLI (200 data credits), prod `event` check constraints (`kind`, `signal_type` as listed in §2), `lane_registry` (6 rows, all inactive).

## 1. The answer

Build the **$ tier, run as "$0 + stack first"**: a weekly GitHub Action (the `ats_pulse.py` pattern) pulls publisher RSS/press feeds, GDELT DOC 2.0, SEC EDGAR, Hacker News and GitHub releases per watchlist company into raw `feed_items`, with Apollo's `news_articles/search` (1 credit per 25 results, credits already paid) as the first backstop; Claude classifies in the Monday session; a ≤$25/month news API (Perigon Individual) is bought **only if** the bake-off against akta shows watchlist coverage under 60%. It is the only tier whose terms are clean, whose cost is bounded by construction, and whose failure (a dead feed) shows up in `lane_run` rather than an invoice. $$ and $$$ buy classification and dedup the Monday session already does on subscription; revisit them only if brief usage proves the lane deserves a budget. Confidence 70% (§4).

## 2. The four tiers

Shared contract: the Action fetches raw text, redacts (`redact_body()` before write; the ADR-9 guard is the second layer, tested alone), writes `feed_items` and a `lane_run` row through `spine_client.py`; the Monday session classifies in a no-tools subagent returning `{kind, signal_type, event_date, url, company}` JSON; the parent runs `substrate.py --dry-run`, then `ensure-event`. Dedup = canonical URL + kind; secondary `(company, kind, week)` → `corroborates`. No person rows (ADR-7 R2). Prior art: a "trigger event" monitor (Elias & Shanto, *SHiFT!*, 2007) on a Kimball bus; Google Alerts is the consumer version.

### Tier table

| | $0 | $ (recommended) | $$ | $$$ |
|---|---|---|---|---|
| **Sources** | Publisher RSS/press/blog feeds (resolved once per company, stored in `feed_sources`); GDELT DOC 2.0 `artlist` per company (`&mode=artlist&timespan=7d`); EDGAR full-text + 8-K for the few public names; HN Algolia `search_by_date`; GitHub releases; lane-1 `delta_wow` as a hiring signal; Exa ($10 free credit resets monthly) or Tavily (1,000 free credits/mo) for companies with no feed | $0 stack **+ Apollo `news_articles/search`** (categories: hires, investment, partnership, acquisition, product launch) from existing credits; **+ Perigon Individual** if coverage < 60% | Clay `News` signal on a company audience (per-result billing; includes funding) on Launch; or Specter/Harmonic/Crunchbase API | PitchBook, CB Insights, AlphaSense, Diffbot KG |
| **Fetch / run** | GitHub Action, Sunday, public-repo runner (free, GitHub docs) | same | Clay runs the watch; Action exports events via Clay CLI/MCP into `feed_items` | vendor UI/API; feed via Action where an API exists |
| **Classification** | Claude, Monday session, no-tools subagent | same; Apollo category pre-labels | Clay topics pre-label; Claude confirms | vendor taxonomy; Claude maps |
| **Monthly $** | **$0** | **$0 marginal** (Apollo ≈ 80 cos × 4 wk × 1 credit ≈ 320 credits/mo from paid balance) → **$25/mo** if Perigon added (perigon.io/pricing: Individual "from $25/mo", 1K req/mo, 2 monitors, 3-mo history) | Clay Launch **$185/mo** monthly / $167 annual, 2.5K data credits + 15K actions, company-news signal included (clay.com/pricing). Specter: quote-only, platform seat required for API. Harmonic: quote; Vendr median ≈ $36K/yr (3 deals). Crunchbase API: enterprise-only; third-party $30–50K+/yr | PitchBook: quote; $12–20K/seat/yr, ~$30K median (Vendr via privateequitylist, 2026). CB Insights: quote; $29.8K–100K/yr (CostBench, Mar 2026). AlphaSense: quote; $10–20K/seat (Sacra, Jun 2026), ~$18K median. Diffbot Startup **$299/mo**, 250K credits, 25 credits per KG entity (diffbot.com/pricing) |
| **Coverage vs akta (funding · launch · M&A · exec · layoff · earnings/incident)** | launch ✓ (first-party, best source) · funding ◐ (GDELT/press when announced) · M&A ◐ · exec ◐ (press releases only) · layoff ✗ (needs news search) · earnings/8-K ✓ public only · 9 GTM/data names ✓ via RSS, AI-natives ◐ | adds funding ✓, exec ✓, M&A ✓ (Apollo categories), layoff ◐ (Perigon query) | funding ✓ exec ✓ M&A ✓ layoff ✓ launch ◐ | all ✓ plus valuation, investors, cap tables (the thing nothing below buys) |
| **Freshness** | RSS minutes; GDELT 15-min updates; weekly pull → ≤7 days | same; Apollo lag unmeasured (bake-off item) | Clay daily–weekly cadence | daily |
| **Build effort** | 14–18 h (feed resolver, 5 clients, redaction, manifests, selftest, Action, `feed_items` DDL as 0020+) | +4 h (Apollo client, category map) +3 h (Perigon) | +4 h Clay signal + export path; vendor APIs +8 h each | procurement weeks; +8 h per API |
| **ToS posture** | GDELT: "unlimited and unrestricted use for any academic, commercial, or governmental use… without fee", citation required. EDGAR: 10 req/s, declared User-Agent (sec.gov). HN Algolia: free, ~10K req/h/IP (secondhand). **Google News RSS is out**: `news.google.com/robots.txt` disallows `/rss`, and Google's ToS bars automated access against machine-readable instructions. Publisher RSS exists for syndication. No LinkedIn | paid APIs with commercial terms. NewsAPI.org free is dev-only ("cannot be used in production, including internal use"); GNews free is non-commercial; neither is a $0 option | CRM use allowed; Specter API needs a seat | annual contracts, no monthly exit |
| **Failure modes** | feeds rot (coverage alarm); GDELT rate-limits (~1 req/5 s unofficial); press-release PII → redact + guard; prompt injection → no model in the Action, classifier has no tools | Apollo endpoint may be plan-gated (verify Settings › Billing › About credits first); free search tiers change terms | per-result billing on a noisy company → `creditLimit` pause that **stays paused**; vendor lock | cost dwarfs the lane; licence forbids redistribution to a public hub |
| **Lane pattern fit** | Action + `spine_client` + `lane_run`; kill rule becomes `items_written = 0 for 3 runs → FAIL` (credit cap is moot); 60%-coverage rule unchanged | identical; `credits_spent` logs Apollo/Perigon units; cap in the command | Clay's own ledger + `lane_run`; cap = Clay `creditLimit` | not a lane; a subscription |

**Where the existing stack covers a tier at $0 marginal cost.** Apollo covers the "$" news backstop from paid credits (1 credit per page, docs.apollo.io/docs/api-pricing); `organizations/enrich` (1 credit) also gives lane 5 its segment. Clay covers "$$" only on Launch or above (company-news signals are not on Free; live balance 200 data credits, plan unverified from the CLI). HubSpot Breeze intent is web-visitor intent on Alex's own properties, not company news; it answers none of Q2–Q6. akta: subscription, 951.01 credits live; the pilot cost 10.74 credits per 40-company/30-day run; the per-credit price is unverified (pricing page 403), so it cannot be ranked until Alex reads the invoice.

### Other candidates priced and set aside (vendor pages, 2026-11-05)

| Vendor | Price | Why not first |
|---|---|---|
| NewsAPI.org Business | $449/mo, 250K req, no full text | 18× Perigon |
| NewsAPI.ai 5K | $90/mo; 1 token/recent search; 2,000 free (one-time); overage $0.015/token | second choice |
| NewsData.io Basic | $199.99/mo (Capterra/G2; official page hides price); free = 200/day, 48-h window | too shallow free, too dear paid |
| GNews Essential | €49.99/mo (€39.99 annual), 1,000 req/day, full text | viable if full text matters |
| Exa / Tavily | Exa PAYG $4–7/1K, $10 free monthly; Tavily 1,000 free credits/mo, $30 for 4,000 | $0 search backstops; free-tier commercial terms unstated |

## 3. Comparing tiers before committing

Run while akta is live (trial ends ~2026-11-29). Same 40 companies, window 2026-10-06 → 2026-11-05. Reference set: akta's 674 articles, labelled on a stratified 120 (30 per `news_score` quartile) by a no-tools subagent with Alex checking 20, then extended to the full set. Candidates: $0 stack; $0 + Apollo; $0 + Apollo + Perigon (free test key, one monitor); Clay `News` on a 40-company audience (only if on Launch). One Action dispatch per candidate on a branch; nothing written to prod.

| Metric | Definition | Floor |
|---|---|---|
| Precision | true signals ÷ items returned, per the 4-class rubric below | ≥ akta's sampled 8/12 ≈ 0.67 |
| Recall vs akta | akta true signals matched by canonical URL or `(company, kind, ±3 days)` | ≥ 0.60 |
| Coverage | companies with ≥1 true signal ÷ 40 | ≥ 0.60 (registry kill rule); akta: 36/40 |
| Novelty | true signals the candidate found that akta missed | report, no floor |
| Lag | median days, `asserted_at` → first fetchable | ≤ 7 |
| Cost per true signal | $ or credits ÷ true signals | report |
| PII rate | redactions per 100 raw items (layer 1) and guard hits that reached layer 2 (must be 0) | 0 at layer 2 |

Rubric: **A** firm-level fact with a date and a primary or tier-1 source (round, acquisition, launch, named exec move, layoff, incident, earnings) · **B** same fact, secondary source or no date · **C** mention only (listicle, vendor blog, translated duplicate) · **D** wrong company or spam. True = A+B. Scored twice, permutation-null: shuffle company labels 200× to show the match rate a random pairing would produce (expect ≈ 0).

**Do-nothing baseline.** Without this lane the Monday brief gets: lane 1 hiring deltas per company per week (Q2, Q5 partially); lane 3 papers and model releases (Q7, not company-level); lane 0 research claims, historical not weekly. For Q3, Q4 and Q6 the weekly count of funding/launch/exec_move facts is **zero**; prod holds 3 funding, 9 launch and 1 exec_move events in total, all from event research, so the baseline is "news about companies in rooms Alex already sat in." Every tier is judged against that zero and against akta's 0.67 precision.

## 4. Recommendation

**$ tier, started as $0 + Apollo, Perigon gated on the bake-off.** Confidence **70%**: high that the $0 skeleton is right (it is the approved lane-4 feeds design pointed at the watchlist, with the cleanest terms); lower on whether coverage clears 60% without a paid search API, which the bake-off measures. The 30% splits between "Apollo's news endpoint is plan-gated or thin" and "AI-native startups without press pages yield only GDELT noise."

**Irreversible or contractual decisions for Alex.**
1. Let akta lapse ~11-29 unless the bake-off shows it beating $0 + Apollo on recall by ≥ 0.20; read the per-credit price off the invoice first.
2. Migration 0020+ (`feed_sources`, `feed_items`) after the twin rehearsal: additive, but DDL he pastes.
3. Perigon or NewsAPI.ai card-on-file only after the bake-off, cap in the command.
4. Verify the Clay plan before any signal is created (a new signal is paused and spends nothing until resumed).
5. No $$$ contract: PitchBook's one real addition, deal depth for dossiers, is a $12K+ job-search decision, not a weekly-brief one.

**What would change my mind.** Coverage under 0.60 with Apollo in → buy Perigon ($25) or NewsAPI.ai ($90), re-run. ≥3 `claim_usage` rows per brief from this lane for four weeks → it has earned a budget; move to Clay Launch. Apollo alone at high recall → drop GDELT. Any layer-2 guard hit in the bake-off → stop and redesign redaction before a prod write.

---

**Teaching layer.** "Stack, free, paid" taken literally: the paid products sell classification and dedup (the Monday session already does that on subscription) and deal depth (this lane does not need it). Keep three ideas: *trigger-event monitoring* (watch the change, not the state); *precision and coverage floors with a null baseline*; *terms of service as an architectural constraint* (Google News RSS failed on robots.txt, not price). Interview framing: "I replaced a trial vendor with a terms-clean $0 lane plus an API we already pay for, and gated new spend on a measured coverage gap against the vendor's own output."
