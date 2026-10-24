# Deal Flow (10-24): LP-reporting market map

*`alex:research-analyst`, 2026-10-23, public sources only. "Verify" = single or secondhand source; keep off the stage until checked.*

## Executive summary

- **Collecting and extracting the data is crowded. Writing the GP's letter is not.** Carta, Visible and Standard Metrics all collect portfolio KPIs, and AI parsing is arriving (Visible's AI Inbox sits on its Premium tier and above; Carta's roadmap promises AI collection with source tracebacks). None of them is built to draft the GP-voice "what moved and why" letter for a Fund I GP whose admin is AngelList, Sydecar or a spreadsheet.
- **Fix one claim before the judges do.** The ILPA Reporting Template v2.0 is a *fund-level* schedule of fees, expenses and carry. The fund admin produces it from the general ledger, not from founder emails. So "ILPA-aligned" should mean *we give the admin's ILPA package a matching portfolio narrative and performance section*. It should not claim *we produce the ILPA template*. (80% confident.)
- **Price at about $6k per fund per year**, roughly 10–30% of what a small fund already pays its admin.

## Competitors

| Vendor | Serves | LP-reporting role | Pricing | Gap for a Fund I/II GP |
|---|---|---|---|---|
| Carta (admin, Fund of Funds, Fund Forecasting/ex-Tactyc, Accelex) | Emerging to large funds; LPs via its Fund of Funds product | Collects data; AI collection with source tracebacks and a Tearsheet Builder are on its roadmap; LP portal | Not public. "~$20–30k/yr for emerging managers" ([Teel Lidow, 2023](https://teel.substack.com/p/the-emerging-vc-stack-angellist-vs)); ~$1.5k/mo (VCBeast 2026, **verify**) | Locked to Carta's own admin. Produces tearsheets, not a GP-voice narrative |
| Visible | Seed to growth VCs | Data requests; AI Inbox on Premium+; reports, tear sheets, LP dashboards | Investor plans: custom ([pricing](https://visible.vc/investor-pricing/)) | Collection is strong; the narrative is still written by hand |
| Standard Metrics | Mid to large VCs (Accel, BVP, GC) | Pulls from accounting systems; AI agent; managed data service; AI Analyst; MCP | Not public | Priced for institutions; too much for one GP with 15 companies (60%, inferred) |
| Juniper Square (JunieAI) | 2,300+ GPs, mostly real estate and PE | Investor portal, IR, admin, AI agents | Not public | Fund-level IR, not the portfolio narrative |
| Allvue | Mid to large PE and private credit | Fund accounting, portfolio monitoring, portal | Not public | Enterprise implementation |
| Chronograph | LPs and large GPs | LP-side analytics | Not public | Wrong buyer |
| Vestberry | European VCs | Monitoring dashboards, LP reports | Contact sales | Narrative stays manual |
| Rundit | Small to mid VCs, angel groups | Data collection, LP reporting | From €299/mo per Capterra (**verify**) | Closest on segment and price; no AI narrative or source-span claims found |
| AngelList (fund admin) | Emerging VC funds | Financial statements, K-1s, LP portal | 0.1% of fund + $10k/yr, or 0.15% + $20k ([pricing](https://www.angellist.com/pricing)) | Makes the financials, not the letter. **A distribution partner, not a rival** |
| Sydecar | SPVs, emerging funds | Admin, K-1s, LP portal | SPV: 2% of capital, $4.5k minimum | Same as AngelList |
| Aduro (FundPanel) | 550+ firms | Full-service admin, investor portal | Not public | A service firm; the narrative stays with the GP |
| Allocations | Emerging managers | Fund admin | ~$19.5k/yr (**verify**) | Same as AngelList |

Assure appears to have wound down in late 2022 (**verify**). Don't name it as a live competitor.

## Pain evidence (thin; say so on stage)

- **Solo GPs are short on time:** "if you're a solo GP, that's one of five or six jobs you have" (Turner Novak, [Fortune, 2024-01-19](https://fortune.com/2024/01/19/solo-gp-managers-2024-challenges)).
- **The letter is also a fundraising asset.** "Nine in ten LPs request past quarterly updates when evaluating a new manager"; LPs want "what changed since last quarter, why it changed" ([Embracing Emergence × EUVC LP survey, 2026-07-08](https://embracingemergence.beehiiv.com/p/what-lps-really-want-from-quarterly-updates); sample size not stated).
- **Getting founders to reply is the chronic failure.** Visible concedes it "will not dramatically (or magically) increase structured data response rates" ([Visible, 2025-12-01](https://visible.vc/blog/request-response-rates); vendor source).
- **LP dissatisfaction:** the only primary source is old (2015 ILPA survey: 52% of institutions built custom fee templates; **verify**). Figures like "73%" and "92%" come from vendor blogs. **Do not use them.**
- **Hours per quarter:** no public survey exists. Working assumption is 10–25 hours (40% confidence). **Get this number from interviews and from GPs in the room.**

## ILPA basics

- **Reporting Template v2.0** (2025-01-22). It applies to funds still in their investment period in Q1 2026, or funds starting on or after 2026-01-01.
  - Covers: capital and commitments, management fees and offsets, granular partnership expenses, chargebacks, subscription-line interest, placement fees, carried interest and portfolio-company fees.
  - Line items can't be re-ordered or repurposed ([ILPA](https://ilpa.org/industry-guidance/templates-standards-model-documents/reporting-template); [Katten](https://katten.com/ilpa-publishes-updated-reporting-template-and-new-performance-template)).
- **Performance Template (new):** gross and net IRR, TVPI and MOIC, plus cash-flow tables. It offers a granular method and a gross-up method.
- **Capital Call & Distribution Template:** updated 2025-09-11, effective Q1 2027 ([Gen II](https://gen2fund.com/news/ilpa-releases-new-capital-call-and-distribution-template-effective-q1-2027/)).
- With the SEC's private fund rule vacated, ILPA has become the de facto standard.
- **So what:** the template's fields come from the general ledger, which the admin owns. Position us as the admin-agnostic companion to the ILPA package.

## Pricing

- **List: $6,000 per fund per year** ($500/mo). Design partners: $3,000 for year one in exchange for a case study.
- **Why that number:** it's 10–30% of the admin fee, a line item GPs already accept.
- **Value math:** 15 h × 4 quarters × ~$300/h ≈ $18k of GP time a year, so we capture about a third (45% confidence; the hours figure is unvalidated).
- **Per fund, not per seat:** Fund II brings a second subscription.

## Why now

ILPA v2.0 went live for funds still investing in Q1 2026, so even Fund I/II GPs are now measured against an institutional bar with no ops team behind them. Meanwhile, LLM extraction with span-level citations has become cheap enough to sell as a $500/mo product.

## Three objections to expect

| Objection | Answer |
|---|---|
| "Carta ships this inside fund admin. You're a feature." | Carta serves its own admin customers and stops at tearsheets. We work with any admin and own the letter, the part the GP actually writes. |
| "Tiny market, $6k ACV. Where's the venture outcome?" | Emerging managers are the wedge. The same source-linked portfolio graph sells upmarket to LPs and fund-of-funds who need to verify GP claims, which is the side Carta is buying into with Accelex. |
| "A hallucinated revenue figure sent to LPs is a fiduciary problem." | Nothing ships without GP sign-off. Every figure links to its source span, any change from last quarter is flagged for review, and "not reported" is a valid output. |
