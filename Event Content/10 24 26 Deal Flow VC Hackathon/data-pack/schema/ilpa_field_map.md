# Field map: data pack to ILPA reporting sections

> **Approximate, verify against the ilpa.org template.** This map was written from general knowledge of the ILPA Reporting Template (capital account statement plus fees, expenses and carried interest schedule) and ILPA's performance-reporting guidance, without access to the current published files. Section and line names below are paraphrased, not quoted. Check the current template (ilpa.org, Reporting Template and Performance Template) before claiming ILPA alignment in front of judges.

## A. Capital account statement (fund level; per LP = fund level x `pct_of_fund`)

ILPA presents each line for the period (QTD), year to date and inception to date.

| ILPA-style line | Source in this pack | Notes |
|---|---|---|
| Beginning NAV | prior quarter NAV (`answer_key/q3_2026_fund_metrics.json` → `prior_quarter.nav_usd`) | Q2 NAV also in `fund/prior_report_Q2_2026.md` |
| Contributions | `fund/capital_account.csv` → `capital_called` | Per LP: multiply by `fund_profile.json` → `lps[].pct_of_fund / 100` |
| Distributions | `capital_account.csv` → `distributions` | Only Q2 2026 is non-zero (Tidewright secondary) |
| Management fees (gross) | `capital_account.csv` → `management_fees` | 2% of commitments, quarterly |
| Fee offsets / waivers | none in this fund | Report as 0 |
| Partnership expenses | `capital_account.csv` → `fund_expenses` | 2023-Q1 includes $300K organizational costs; not broken out by category (gap vs ILPA detail) |
| Realized gain / loss | `portfolio_marks.csv` → `realized_proceeds_usd - realized_cost_usd` | Tidewright only |
| Change in unrealized gain / loss | `portfolio_marks.csv` → `mark_q3_2026_usd - mark_q2_2026_usd` | Only Loomvale and Halcyra move in Q3 |
| Carried interest (accrued) | not modeled | State this explicitly in the report |
| Ending NAV | portfolio fair value + `ending_fund_cash` | |
| Unfunded commitment | `capital_account.csv` → `unfunded_commitment` | |

## B. Fees, expenses and carried interest schedule

| ILPA-style item | Source | Notes |
|---|---|---|
| Management fee, gross and net of offsets | `management_fees` | No offsets |
| Partnership expenses by category | `fund_expenses` (single line) | Category split not provided; flag as a known gap |
| Portfolio company fees (transaction, monitoring) | none | Report as 0 |
| Carried interest paid / accrued | not modeled | |

## C. Performance (fund level)

| Metric | Source | Notes |
|---|---|---|
| TVPI, DPI, RVPI | computed from `capital_account.csv` + marks | Expected Q3 values in `answer_key/q3_2026_fund_metrics.json` |
| Net IRR | XIRR on LP cash flows dated at quarter end, NAV as terminal value | Estimate; ILPA guidance prefers actual cash-flow dates |
| Gross IRR | not computed | Would need investment-level cash-flow dates |

## D. Portfolio company information (schedule of investments)

| Field | Source |
|---|---|
| Company, sector, HQ, stage at entry | `portfolio_marks.csv` |
| Initial investment date | `initial_investment_date` |
| Cost basis (remaining) / realized cost / realized proceeds | `cost_basis_usd`, `realized_cost_usd`, `realized_proceeds_usd` |
| Fair value (current, prior) | `mark_q3_2026_usd`, `mark_q2_2026_usd` |
| Ownership % (fully diluted, approximate) | `ownership_pct_q3_2026` |
| Valuation methodology | `valuation_method_q3` |
| Last round date / post-money | `last_round_date`, `last_round_post_money_usd` |

## E. Not ILPA template fields: company operating metrics

Founder-reported KPIs are not part of the ILPA capital account or fee templates. VC funds typically report them in the GP letter or a supplemental portfolio schedule. In this product they feed the GP narrative and the per-company table, each with a source span.

| Our field | Use in the LP report |
|---|---|
| `monthly_revenue`, `arr`, `revenue_type` | Portfolio table and narrative; never show `arr` for non-recurring revenue |
| `monthly_burn`, `cash`, `runway_months` | Risk section; `low_runway` drives a watch-list entry |
| `headcount`, `customers` | Portfolio table |
| `key_highlight`, `key_risk` | GP letter, one line per company |
| `flags` | Internal review queue before the report goes out; `missing_update` and `no_numbers_reported` become "update not received" rows |
| Currency (`EUR`) | Show as reported; convert for roll-ups with `fund_profile.json` → `fx_assumption` and say so |
