# Deal Flow (10-24): LP-reporting value chain and stakeholders

*`alex:research-analyst` (Fable), 2026-10-23. Pain data comes mostly from vendors; "vendor" and "verify" are marked inline.*

**Short answer:** own the **portfolio-data-to-narrative seam, with provenance**. Pitch it as a **Fund II fundraising instrument**, and make the **privacy posture** a first-class design choice.

## Five insights

1. **Value is destroyed at the hand-offs, not inside the stages (80%).** Three seams leak:
   - Founder → GP: unstructured updates, patchy response.
   - Fund admin → tax preparer: the main cause of late K-1s ([Carta](https://carta.com/blog/k-1-delivery-for-funds/), vendor).
   - GP PDF → LP spreadsheet: Canoe exists to re-digitize GP output, "50M+ documents… 1,000 LPs, 44,000 funds" ([Canoe](https://www.silicon.co.uk/press-release/canoe-intelligence-raises-36-million-series-c-funding-led-by-goldman-sachs-to-further-market-expansion), vendor).

   A report generator competes with Visible and Carta. The open gap is a **reconciliation and provenance layer that survives the seams**.
2. **For an emerging manager, the quarterly report is a fundraising asset first and a compliance artifact second (75%).**
   - 79% of LPs declined to re-up with at least one GP last year ([Coller Barometer](https://www.institutional-investment.de/fileadmin/news_import/Global_Private_Equity_Barometer.pdf)).
   - Only ~12% of H1-2025 commitments went to Funds I–IV ([Pipeline Road citing WITHIntelligence](https://pipelineroad.com/blog/fundraising-outlook-2026), secondary).
   - "A first-time fund rarely loses a commitment to another new manager. It loses it to the re-up list" ([Metz](https://metz.substack.com/p/before-you-raise)).
   - Between Fund I close and Fund II launch, the report is the only recurring touchpoint. **The buyer's value is "Fund II closes faster," not "saves 20 hours."**
3. **ILPA 2025 standardizes the ledger, not the portfolio (85%).**
   - Reporting Template: from Q1 2026 for funds in their investment period.
   - Performance Template: data captured from Q1 2026, first delivered after Q1 2027 ([ILPA](https://ilpa.org/news/ilpa-releases-updated-reporting-template-and-new-performance-template-for-industry-adoption/); [BDO](https://www.bdo.com/insights/industries/asset-management/preparing-for-q1-2026-the-new-era-of-ilpa-reporting-and-performance-templates)).
   - Portfolio-company data (metrics, runway, narrative) stays unstandardized. That's where an LLM pipeline adds value without fighting the admin.
4. **Marks are the trust boundary, and the market already discounts venture NAV by ~22% (70%).**
   - Venture LP stakes cleared at ~78% of NAV in 2025, vs. 92% for buyout ([Jefferies via AI-CIO](https://www.ai-cio.com/news/lp-gp-led-secondaries-grow-to-record-volumes-in-2025/)).
   - IPEV 2025 (applies to periods from 2026-04-01): "the price of recent investment is not automatically fair value" ([Houlihan](https://www.houlihancapital.com/2025-ipev-valuation-guidelines/)).
   - Showing "what changed at the source" raises LP trust but exposes stale marks. **Design: disclosure the GP controls, on top of reconciliation that is honest internally.**
5. **Confidentiality is both the moat and the kill switch (80%).**
   - After the 2002 FOIA rulings, top-quartile VCs stopped taking public LPs ([Abuzov, Gornall, Strebulaev, JFE 2025](https://corpgov.law.harvard.edu/2025/06/03/the-value-of-privacy-and-the-choice-of-limited-partners-by-venture-capitalists/)).
   - LPAs were "drafted in a pre-AI environment" ([Hogan Lovells](https://www.hoganlovells.com/en/publications/ai-on-lp-led-secondaries-is-the-market-ready)).
   - ILPA's DDQ 2.0 has a third-party data-security section but no guidance on LLMs.
   - **Local or redaction-first inference is a differentiator.** A judge runs a privacy-first local-AI company.

## Value chain

| Stage | Who / tools | Cost / time | Failure modes |
|---|---|---|---|
| Founder data collection | Associate or platform team; email, Visible, Carta, forms | 4+ reminders needed; automation saves ~63 h/yr (vendor) | Non-lead investors get lower response; definitions inconsistent; no audit trail. Emailed-survey baselines are 25–50% ([MaRS](https://www.marsdd.com/results/mars_venturesurvey_2014_methodology)) |
| Valuation / marks | GP committee; ASC 820 / IPEV; year-end audit | Audit $15–40k/yr (vendor) | Anchoring to the last round; stale marks; weak documentation |
| Fund accounting | Admin (AngelList, Carta, Juniper Square, Allvue) | Admin $8–25k/yr up to $20–95k; total run-rate $35–75k/yr (vendor) | Admin → tax hand-off; "~40% of venture funds have K-1 delays or errors" (unnamed, **verify**) |
| Transformation into the report | GP writes the letter; admin maps to ILPA | 45 days is "ambitious", 60 days reliable; K-1s slide to September | The narrative is hand-written every quarter |
| Distribution | Portals, data rooms, PDF | Low cost | PDF is the format of record; portals don't fix the content |
| LP consumption | Canoe, Cobalt, Burgiss, iLEVEL; manual re-keying | 68% of LPs say responsiveness depends on manual work ([PE Wire](https://www.privateequitywire.co.uk/majority-lps-attracted-tech-enabled-pe-managers/)) | Re-keying errors; metrics don't line up across GPs |
| Insight / feedback | IC memos, AGMs, re-ups, secondaries | Re-up declines 42% performance-driven; venture stakes at ~78% of NAV | 64% of LPs want better visibility into capital calls and distributions |

## Stakeholders

| Stakeholder | Wants | Fears | Pays for | Conflict |
|---|---|---|---|---|
| Solo / Fund I–II GP | Re-ups, Fund II momentum, hours back | Looking amateur; a mark challenged; leaking founder data | A credible report, fast; narrative drafting | Smoothing marks vs. LP transparency |
| Fund CFO / controller | Clean admin data | Restatements, liability | Reconciliation checks, variance flags | Speed vs. accuracy |
| Fund admin | Keep the mandate | Disintermediation; blame for K-1s | Integrations | A reconciler exposes their errors |
| Auditor | Defensible marks | Unsupported fair values | Nothing directly | Pushes marks down |
| Founders | One format, minimal asks, something back | Leaks; update fatigue | Nothing; they need reciprocity (benchmarks, intros) | Depth LPs want vs. the burden on founders |
| Institutional LP / FoF | ILPA-standard, machine-readable | FOIA exposure; re-keying | Already pay Canoe/Burgiss | Standardization vs. narrative |
| Family office / HNW | A letter + capital statement | Being ignored | Little | Low appetite for detail |
| Operator-LPs (e.g., Everywhere's ~500) | Narrative, asks for help, deal access | Irrelevance | Community | Want more detail than LPAs allow |
| Secondary buyers | Source-level data | Stale marks | Diligence access | Benefit from opacity |
| Placement agents | A credible track-record package | Unverifiable numbers | A clean data room | — |

## Second- and third-order effects (55%, directional)

- **The chain:** faster, transparent reporting → lower LP ops burden → higher re-up odds → a shorter Fund II close (15–26-month ranges; PitchBook citations conflict) → better benchmarking → the secondaries discount narrows toward 92% → more LP liquidity.
- **Regulation:**
  - The Fifth Circuit vacated all Private Fund Adviser rules on 2024-06-05, including the Quarterly Statement Rule ([MoFo](https://www.mofo.com/resources/insights/240612-fifth-circuit-vacates-sec-private-fund-adviser-rules)).
  - What survives: the Marketing Rule (net performance shown with equal prominence, which matters for Fund II decks), the SEC's exam focus on fees, and ILPA.
  - **Quarterly statements are now a market expectation, not a legal one**, so a voluntary, high-quality statement differentiates.
- **Upstream costs:** founders need reciprocity; admins must export ledger data and will resist a layer that flags their errors.

## Tailoring

- **Institutions** expect the ILPA structure; **individuals** are "generally happy with a quarterly letter and a capital account statement."
- **Family offices split:** ~500 run institutionally; 8,500+ don't.
- LPs reward acknowledged uncertainty over false certainty.
- **One output, two audiences:** existing LPs and prospective Fund II LPs, with different permissions (75%, inferred).
- Everywhere's own LP update format: unverified. Ask in the room.

## Gaps

- Hours per quarter (GP writing, LP re-keying): **no credible figure exists.** Get it from interviews and from the room.
- No public example of a venture capital-account restatement.
- No recent ILPA adoption survey.

## Teaching layer

- **Value-chain analysis** (Porter, 1985): margin lives in the *linkages* between activities.
- **The fair-value hierarchy** (ASC 820 / IPEV 2025): the price of a recent round is a calibration input, not fair value.
- **The lemons discount** (Akerlof, 1970): the ~78%-of-NAV venture clearing price is the market pricing opacity.
