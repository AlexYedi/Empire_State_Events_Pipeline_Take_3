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

## Re-running

`fetch0.py <src|all>` → `gdelt_retry.py` (until there are no 429s) → `prep_label.py` → labeller dispatches (one `alex:research-analyst` per batch on Fable, compact `k CLASS KIND` output) → `extract.py <agent transcript> labels_NN.txt` → `score.py`. The scripts expect `companies.json` and `../akta/run1.json` beside them; both are private and are never committed.
