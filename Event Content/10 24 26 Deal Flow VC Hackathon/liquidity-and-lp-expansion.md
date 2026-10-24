# Deal Flow (10-24): liquidity and LP expansion, the vision layer

*`alex:research-analyst`, 2026-10-24, about 00:30. Source-checked against primary PDFs; anything unfound is marked "verify". Feeds the team kit's #vision section. Decision: keep today's build; this is the roadmap.*

## Bottom line (70%)

**The vision slide leads with liquidity, framed as information and not a marketplace. The LP hub is a product feature, not the vision.**

- **Liquidity is the binding constraint.** Net cash flow to LPs has been −$202B since 2022, and capital follows distributions.
- **Secondaries don't reach small-GP portfolios.** The top 20 names are 86% of secondary trading value.
- **M&A is the primary exit route and the open gap.** Exit-readiness and acquirer mapping for a Fund I/II GP. Charging a subscription rather than a success fee keeps the tool outside broker-dealer rules.
- **The LP hub is crowded and carries regulatory risk.** Selective disclosure is the main exposure, and the hub has nothing the incumbents lack.

## Challenge anchor

| ID | Clause | Layer |
|---|---|---|
| F1–F4, P1–P2, E1 | See `synthesis.md` | **Today:** the provable update |
| Track 4 secondary-pricing clause (cut from today's build) | Track doc | **Roadmap:** seller-side liquidity intelligence. Verified numbers in a sale data room should narrow the opacity discount (Akerlof; 55%, a hypothesis) |
| F4 + Fund II re-up | Track doc | **Feature:** LP engagement signals (same facts, personalised framing) |

## 1. Constraints on LP commitments, by causal weight

| # | Constraint | Evidence | Conf. |
|---|---|---|---|
| 1 | Distribution drought | 2025: $61B called vs. $42B distributed; 2021 was the last net-positive year ([Cambridge Associates, Jul 2026](https://www.cambridgeassociates.com/insight/us-pe-vc-benchmark-commentary-calendar-year-2025/)). Net LP cash flow −$202B since 2022 ([Q3 2026 PitchBook-NVCA Venture Monitor, p.26](https://nvca.org/wp-content/uploads/2026/10/Q3-2026-PitchBook-NVCA-Venture-Monitor.pdf)). Only 25% of 2021-vintage funds have any DPI ([Carta](https://carta.com/data/2021-venture-funds-dpi/), vendor) | High |
| 2 | Exits concentrated | 2026 YTD exit value $2.29T, almost all SpaceX; without it, "the same constrained level" since the pandemic. M&A at a decade-high $465B, "the preferred, or at least primary, route" (Venture Monitor Q3 2026, p.29–30) | High |
| 3 | Manager concentration | 2026 YTD: $108.5B across 699 funds (2022: $224.8B / 1,838). Funds of $500M+ = 78.1% of capital; first-time funds = 4.5%; emerging firms closing a fund 927 → 211 (Venture Monitor, p.32–33) | High |
| 4 | Re-up attrition | 79% of LPs declined at least one re-up ([Coller](https://www.institutional-investment.de/fileadmin/news_import/Global_Private_Equity_Barometer.pdf)) | Medium |
| 5 | Ageing companies | Median age at IPO 12 years in 2025 vs. a long-run tech median of 8 ([Ritter](https://site.warrington.ufl.edu/ritter/files/IPOs-Age.pdf)). Age at M&A: verify | High |
| 6 | Secondary discount | Venture LP stakes ~78% of NAV vs. 92% for buyout ([Jefferies via AI-CIO](https://www.ai-cio.com/news/lp-gp-led-secondaries-grow-to-record-volumes-in-2025/)). 2021-priced names trade at a median 59% discount | Medium |
| 7 | Dry powder | ~$299B at end-2025 (NVCA Yearbook; verify). Only 16% of 2021-vintage capital is unspent (Carta, vendor), so deployment isn't the bottleneck | Low–Med |
| 8 | Time to close | 14–26 months; vendor sources conflict; verify | Low |

## 2. Seller-side liquidity landscape

| Who | What | Gap for a Fund I/II GP |
|---|---|---|
| Forge, EquityZen, Hiive, NPM, Zanbato, Augment | Direct and SPV secondaries | Late-stage names only: 98.6% of EquityZen volume is in companies older than 6 years ([PitchBook Secondary Market Watch Q2 2026](https://pitchbook.brightspotcdn.com/a0/0f/51360d314d5892e70dca12e25c58/q2-2026-us-vc-secondary-market-watch.pdf)) |
| Caplight | Pricing data | Covers the top names |
| Carta tenders | Company-run buybacks: 71 deals, ~$3B in H1 2026 (vendor) | The company decides; the GP can't initiate |
| Industry Ventures, StepStone, NewView | Fund-stake buyers | Ticket minimums; priced at ~78% of NAV |
| GP-led continuation vehicles | US VC: $14.6B over the trailing 12 months | ILPA process costs are heavy for a sub-$50M fund (assumption) |
| M&A advisors | Sell-side | Not economic below ~$50M exits (assumption) |
| **AI exit intelligence for small GPs** | **None found** | **The open gap** (low confidence; absence of evidence) |

## 3. Hard constraints

- **Transfer consent:** board approval, ROFR and co-sale rights; some issuers void unauthorized transfers.
- **Broker-dealer line:** the SEC's 2018 AngelList/FundersClub no-action letters allow no transaction-based compensation and no handling of funds ([Mintz](https://www.mintz.com/insights-center/viewpoints/2018-04-two-recent-sec-no-action-letters-establish-standards)). Subscription-priced intelligence is fine; matching for a success fee is not. Counsel to confirm.
- **Signaling:** a visible GP sale reads as negative; M&A readiness avoids it.
- **Continuation vehicles:** ILPA 2023 requires an LPAC vote, ≥10 business days, a status-quo option and a fairness opinion ([Katten](https://katten.com/a-new-era-for-continuation-fund-transactions-ilpa-issues-new-guidance)).
- **LP hub:** the Marketing Rule binds registered advisers, while many Fund I/II GPs are exempt reporting advisers bound by anti-fraud rule 206(4)-8. A report that pitches Fund II can become an advertisement (verify the existing-investor carve-out). Selective disclosure is governed by side letters, MFN and 206(4)-8. **Design rule: same facts for every LP; personalise only the framing.**

## Vision-slide numbers

1. **−$202B**: net cash flow to venture LPs since 2022 (85%).
2. **4.5%**: first-time funds' share of 2026 US VC capital (90%).
3. **86%**: share of secondary trading value in 20 names. Every seed book has no market (80%).
