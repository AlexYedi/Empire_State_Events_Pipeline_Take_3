# Lane 2 bake-off, run 1 (2026-11-05): the $0 stack vs akta

The test from §3 of `docs/proposals/2026-11-05-company-signals-lane-stack.md` (YED-333), run before the akta trial ends (~2026-11-29). Nothing was written to prod. Inputs and outputs stay in the session scratchpad, because the 40-company watchlist comes from the private `target-companies.md`. **This page reports aggregates only.**

## What ran

| Candidate | Status |
|---|---|
| akta `news_signals` (the reference): 40 companies, the 25 most recent articles each | ran (run 1, 672 articles) |
| $0: company RSS/Atom feeds | ran: feeds found for 25 of 40 companies, 788 items in the window |
| $0: GDELT DOC 2.0 `artlist` | ran: 770 items. **Rate-limited (HTTP 429) on 3 passes**; 2 companies never returned |
| $0: Hacker News (Algolia), ≥5 points | ran: 337 items |
| $0: GitHub releases (non-patch, top-3 repos by stars) | ran: 50 items |
| $0: SEC EDGAR 8-K/10-Q | **blocked**: data.sec.gov returns 403 without a contact email in the User-Agent (YED-337) |
| $: Apollo `news_articles/search` | **blocked**: the `.env` key is rejected as invalid (YED-337) |
| $: Perigon free key · $$: Clay News | not run (they need a sign-up and a plan check) |

**Labelling:** all 2,617 items were labelled by blinded Fable (no source column; shuffled across 6 batches; read-only agent) on the §3 rubric: A = firm-level fact from a primary or tier-1 source, B = the same fact from a secondary source, C = mention only, D = wrong company or spam. Each item also got a kind. True signal = A or B with a kind other than "other". Alex spot-checks 20 labels; that check is pending.

## Results (window 2026-10-06 → 2026-11-05, 40 companies)

| | akta | $0 union | RSS | HN | GDELT | GitHub |
|---|---|---|---|---|---|---|
| Items | 672 | 1,945 | 788 | 337 | 770 | 50 |
| True signals | 373 | 321 | 151 | 81 | 89 | 0 |
| Precision (floor 0.67) | **0.56** | 0.17 | 0.19 | 0.24 | 0.12 | 0.00 |
| Coverage, all 40 (floor 0.60) | 0.90 | **0.62** | 0.47 | 0.30 | 0.33 | 0 |
| Coverage, the 31 job-search targets | 28/31 | **18/31** | | | | |
| Recall vs akta's true signals (floor 0.60) | n/a | **0.42** | 0.24 | 0.21 | 0.02 | 0 |
| Recall null (dates shifted ±10 days) | | 0.10 | | | | |
| URL-exact recall | | 0.02 | | | | |
| Novel true signals (akta has nothing matching) | | 223 | 83 | 57 | 83 | 0 |
| Cost | trial credits (10.74) | $0 | | | | |

**Recall vs akta by kind ($0 union):** launch 73/93 · incident/legal 39/52 · M&A 19/33 · funding 10/57 · partnership/deal 11/83 · earnings 4/38 · hiring/office 2/11 · exec move 0/6.

**Do-nothing baseline:** without this lane, the Monday brief gets zero weekly funding, launch or exec-move facts. Prod holds 13 such events in total, all from event research. Both akta and the $0 stack beat that by hundreds of items a month; the question is which clears the floors.

## Reading it

1. **The $0 stack is a launch-and-incident feed, not a deal feed.** It recalls 78% of akta's launches and 75% of its incidents. It recalls 18% of funding rounds, 13% of partnerships, 11% of earnings (EDGAR was blocked) and none of the exec moves. Those are exactly the categories that Apollo's `news_articles/search` labels.
2. **It fails two of the three floors.** Recall is 0.42 against a 0.60 floor; the shifted-date null is 0.10, so the 0.42 is real signal, just not enough. Coverage of the 31 targets is 18/31 (58%), because the AI-native startups without a press page are where it goes dark: 13 companies are covered only by akta. It clears overall coverage at 0.62.
3. **Precision is the wrong gate for raw feeds.** 17% of $0 items are true signals, but the design puts a classifier in front of the brief, and the classifier is the precision layer. What matters is the yield after classification: 321 true signals a month, 223 of them items akta did not surface. akta's own precision on the same rubric is 0.56, not the 0.67 the proposal assumed from a 12-item sample.
4. **akta's reference is uneven.** It returned only its 25 most recent articles per company, so for the highest-volume names its window is 1–2 days. Recall is measured inside those windows by matching company, kind and date within ±3 days; URL overlap is near zero (0.02), because the sources syndicate different copies of the same story.
5. **Failure modes seen live:** GDELT rate-limited us at roughly 1 request per 6 seconds even with 20–45-second backoff, and 2 companies never returned. A production lane needs one GDELT query per week with an OR across companies, or a cache. GitHub releases produced zero true signals and should be dropped.

## Decision this supports

- **Do not let akta lapse on this evidence alone.** The proposal's rule was: if $0 coverage is under 60% with Apollo in, buy Perigon. Apollo hasn't run yet. Next step: fix the Apollo key and the EDGAR User-Agent (YED-337) and re-run with `$0 + Apollo` before ~11/29. If funding and exec recall are still under 0.60, a $25–90/mo news API (Perigon Individual or NewsAPI.ai) is the measured fix.
- **Drop GitHub releases** from the $0 design. **Re-shape GDELT** to one batched query per week.

## Run 1b (2026-11-06): $0 + Clay

Apollo was not bought, so the paid leg ran on Clay instead, using the credits the workspace already had. Same 40 companies and the same window. Clay resolved 38 of 40 companies; for 2, the domain matched only a different entity.

**What ran:** a custom Claygent data point (Clay's web-research agent). It searches news outlets, press-release wires, partner releases and SEC coverage for the window. It **excludes the company's own site**, because the RSS leg already covers that. Output is one `date | kind | headline | URL` line per event.

Two other configurations were tried on one company first and dropped:
- Clay's standard "Recent News" returns 5 items across 12 months, with only 1 in the window. It also wraps every result in "growth opportunity" commentary drawn from the workspace's business profile.
- A custom prompt that allowed the company's own site returned 7 items, all from the company blog. That duplicates RSS and missed the month's largest partnership.

**Labelling:** the 85 Clay items were labelled by the same blinded Fable rubric. They were shuffled together with 60 items already labelled in run 1, shown as titles only so no row reveals its source. The labeller agreed with its run-1 true/false call on **59 of 60** anchors (53 of 60 exact class and kind).

**Cited links:** 41 of 85 resolve. The other 44 return 401/403/429 (paywalls and bot walls) or time out. None return 404, so there is no sign of fabricated URLs.

| | akta | $0 union | Clay alone | **$0 + Clay** |
|---|---|---|---|---|
| Items | 672 | 1,945 | 85 | 2,030 |
| True signals | 373 | 320 | 78 | **398** |
| Precision | 0.56 | 0.17 | **0.92** | 0.20 |
| Coverage, all 40 (floor 0.60) | 0.90 | 0.62 | 0.82 | **0.88** |
| Coverage, job-search targets | 27/30 | 17/30 | | **26/30** |
| Recall vs akta (floor 0.60) | n/a | 0.42 | 0.46 | **0.69** |
| Recall null (dates shifted −10 / +10 days) | | 0.06 / 0.13 | 0.01 / 0.07 | 0.07 / 0.18 |
| Novel true signals | | 222 | 48 | 270 |
| Cost | trial credits | $0 | ≈57 Clay credits (≈1.5 per company) | ≈57 credits |

(The target denominator is 30 here, not 31, because this run matched names to the private target list programmatically.)

**Recall vs akta by kind, $0 → $0 + Clay:**
- funding 10 → 40 of 57
- M&A 19 → 28 of 33
- partnership 11 → 36 of 83
- earnings 4 → 31 of 38
- exec move 0 → 3 of 6
- hiring/office 2 → 4 of 11
- launch 73 → 75 of 93
- incident 39 → 39 of 52

**Reading it:** Clay fills the gap the $0 stack left. It is a third-party, deal-and-money feed, and it complements the company-owned launch feeds. **$0 + Clay clears all three floors** (recall 0.69, coverage 0.88 overall and 26 of 30 targets). The 0.20 precision is acceptable because the classifier in front of the brief is the precision layer.

Clay is also a different kind of source. It returns a few curated events per company (median 2), not a firehose. That makes it cheap to label and high-precision, but it can miss smaller items. Partnerships are still the weakest kind, at 36 of 83.

**Cost to run weekly:** about 1.5 credits per company per run, so 40 companies weekly comes to about 260 credits a month. The free workspace balance covers about 2 more weekly runs, so a standing Clay lane needs a paid plan or a narrower cadence.

## Re-running

`fetch0.py <src|all>` → `gdelt_retry.py` (until there are no 429s) → `prep_label.py` → labeller dispatches (one `alex:research-analyst` per batch on Fable, compact `k CLASS KIND` output) → `extract.py <agent transcript> labels_NN.txt` → `score.py`. The scripts expect `companies.json` and `../akta/run1.json` beside them; both are private and are never committed.

## Decision and lane design (2026-11-08)

**Decision (Alex, YED-349):** lane 2 is the **$0 stack + Clay**. It is the only configuration that cleared all three floors (recall 0.69, coverage 0.88, 26 of 30 targets).

**Lane design:**
- **Weekly, Sunday GitHub Action** (`.github/workflows/company-signals.yml` → `.claude/scripts/company_signals.py fetch`). It runs GDELT as one batched OR query per week, chunked under the query-length limit with 429 backoff, plus HN Algolia stories with ≥5 points. EDGAR 8-Ks are added once the `EDGAR_USER_AGENT` secret exists (YED-337); until then the step skips with a notice. The Action is dry-run unless the repo variable `COMPANY_SIGNALS_WRITE_ENABLED` is `true`.
- **Clay research agent every second Monday session** (`company_signals.py clay-ingest`). It runs the run-1b prompt (in the script's docstring): third-party sources only, the company's own site excluded, a 14-day window. At about 1.5 credits per company, that is about 60 credits a run and about 130 a month for 40 companies. The kill rule pauses the Clay leg above about 70 credits per run.
- **Input** is the same 40-company watchlist the bake-off measured (`[{name, domain, q, cik}]`). The Action reads it from the private repo secret `COMPANY_SIGNALS_WATCHLIST` and skips green with a warning while that secret is empty. `q` disambiguates GDELT and HN queries and attributes hits; `cik` drives EDGAR. The ATS-table registry was not used because it would drop 12 of the 40 companies.
- **Company RSS stays in lane 4** (`feeds.py`, PR #272). GitHub releases are dropped.
- **Rows** are staged in `feed_items` (migration 0020, PR #305) as `kind = market`. Writes are held until `spine_client.ALLOW` carries `feed_items` (#272) and 0020 is applied. The Monday-session classifier stays the precision layer.
- **Registry:** migration 0021 rewrites the lane's schedule and kill rule. Activation (`active = true`) comes in 0022, after the first good run.
