# Halyard Ventures Fund I: synthetic LP-reporting data pack

**Everything here is fictional.** Fund, GPs, LPs, companies and founders are invented; email domains use the reserved `.example` TLD. Any resemblance to a real company or person is coincidental. Built for the Deal Flow VC Hackathon (2026-10-24), LP-reporting track.

The product this pack feeds: messy founder updates → extracted metrics with source spans → reconciliation against last quarter → an ILPA-aligned quarterly LP report plus a GP narrative letter. Every number is one click from its source.

## Quick start

```bash
python3 generate.py                      # rebuilds everything below (deterministic, idempotent)
python3 eval/check_answer_key.py         # asserts every answer-key span equals its quote
python3 eval/score.py answer_key/q3_2026_metrics.json   # sanity: 100%
python3 eval/score.py path/to/your_predictions/          # your extractor, scored next to the carry-forward baseline
```

Stdlib Python 3 only. No network, no keys, no LLM calls.

## What's in the pack

| Path | What it is |
|---|---|
| `fund/fund_profile.json` | Fund terms, GPs, 35 LPs + GP commitment (`pct_of_fund` for per-LP capital accounts), FX assumption |
| `fund/capital_account.csv` | Fund-level calls, investments, fees, expenses, distributions, cash and unfunded, 2023-Q1 to 2026-Q3 |
| `fund/portfolio_marks.csv` | Per company: cost, realized, ownership, Q2 and Q3 2026 marks, valuation method, round dates |
| `fund/prior_report_Q2_2026.md` | Last quarter's LP report (NAV, TVPI, DPI, IRR, portfolio table, GP letter): the format to beat |
| `updates/Q2_2026/` | 22 clean Q2 founder updates (the "last quarter" side of the reconciliation) + `manifest.json` |
| `updates/Q3_2026/` | 21 messy Q3 founder updates (one company sent nothing) + `manifest.json` |
| `answer_key/q3_2026_metrics.json` | True Q3 values per company, each with file, char span and quote; expected flags |
| `answer_key/q2_2026_metrics.json` | Same for Q2 (source of the baseline and of "what moved") |
| `answer_key/q3_2026_fund_metrics.json` | Expected Q3 fund-level NAV, TVPI, DPI, RVPI, IRR and the Q2 comparison |
| `schema/extracted_metrics.schema.json` | JSON Schema for one company's extraction (every field = value, unit, currency, period, source_file, source_span, quote, confidence) |
| `schema/ilpa_field_map.md` | Our fields → ILPA reporting sections (approximate; verify against ilpa.org) |
| `eval/score.py` | Scores predictions vs the key, always next to the do-nothing baseline |
| `eval/baseline_carry_forward.json` | The baseline: Q2 values carried forward unchanged as the Q3 answer |
| `eval/check_answer_key.py` | Integrity test: spans, manifest, schema shape |

### File tree

```
README.md
generate.py
answer_key/
    q2_2026_metrics.json
    q3_2026_fund_metrics.json
    q3_2026_metrics.json
eval/
    baseline_carry_forward.json
    check_answer_key.py
    score.py
fund/
    capital_account.csv
    fund_profile.json
    portfolio_marks.csv
    prior_report_Q2_2026.md
schema/
    extracted_metrics.schema.json
    ilpa_field_map.md
updates/
    Q2_2026/
        C01_loomvale_2026-07-07.txt
        C02_tidewright_2026-07-08.txt
        C03_ossmere_2026-07-09.txt
        C04_brackenfold_2026-07-10.txt
        C05_quarrytone_2026-07-11.txt
        C06_murrelwick_2026-07-12.txt
        C07_gantrell_2026-07-13.txt
        C08_corvellum_2026-07-14.txt
        C09_stillmote_2026-07-15.txt
        C10_vellstrom_2026-07-16.txt
        C11_kettleworn_2026-07-17.txt
        C12_halcyra_2026-07-06.txt
        C13_pebblequill_2026-07-07.txt
        C14_wrenfield_2026-07-08.txt
        C15_dunmarsh_2026-07-09.txt
        C16_ashvane_2026-07-10.txt
        C17_velloway_2026-07-11.txt
        C18_thistlecrumb_2026-07-12.txt
        C19_marrowlight_2026-07-13.txt
        C20_sorrelpike_2026-07-14.txt
        C21_lanternwick_2026-07-15.txt
        C22_cinderquay_2026-07-16.txt
        manifest.json
    Q3_2026/
        C01_loomvale_2026-10-06.txt
        C02_tidewright_2026-10-09.txt
        C03_ossmere_Q3-2026-deck-export.md
        C04_brackenfold_2026-10-14.md
        C05_quarrytone_2026-10-17.txt
        C07_gantrell_2026-10-15.txt
        C08_corvellum_2026-10-07.txt
        C09_stillmote_Q3-deck.md
        C10_vellstrom_2026-10-08.md
        C11_kettleworn_2026-10-12.txt
        C12_halcyra_2026-10-05.txt
        C13_pebblequill_2026-10-16.md
        C14_wrenfield_2026-10-13.txt
        C15_dunmarsh_Q3-FY26-deck.md
        C16_ashvane_2026-10-08.txt
        C17_velloway_2026-10-20.md
        C18_thistlecrumb_2026-10-16.txt
        C19_marrowlight_2026-10-14.txt
        C20_sorrelpike_Q3-update-deck.md
        C21_lanternwick_2026-10-11.txt
        C22_cinderquay_2026-10-20.txt
        manifest.json
```

## Field definitions (the contract the scorer uses)

- `monthly_revenue`: latest month in the quarter (September for Q3). MRR when recurring, monthly billings when not. `0` for pre-revenue.
- `arr`: only for recurring revenue. The founder's stated ARR if given, else `12 x monthly_revenue` (marked `derivation` in the key, span = the MRR span). `null` for non-recurring revenue, even if the founder calls it ARR.
- `monthly_burn`: monthly net burn as reported. In a month-by-month table, the latest month.
- `cash`: cash at quarter end. `runway_months`: as stated by the founder (scorer allows ±0.5).
- `headcount`, `customers`: as of quarter end. `customers` means whatever the company counts (policies, doors, paying users); the key's `note` names it.
- Money is in whole units of the reported currency. Vellstrom reports in EUR: extract EUR, do not convert. `fund_profile.json` has a fixed FX rate for USD roll-ups.
- Spans are Python string indices (code points) into the UTF-8-decoded file, end-exclusive. `quote == text[start:end]`.
- `revenue_type`: `recurring` / `non_recurring` / `none`.
- Flags vocabulary: `missing_update`, `no_numbers_reported`, `low_runway`, `revenue_decline`, `conflicting_figures`, `non_recurring_arr`, `non_usd_currency`, `unit_inconsistency`.

## The messy cases and where each lives

| Case | Company | File | What to catch |
|---|---|---|---|
| (a) prose email, numbers in sentences | Loomvale Systems (`C01`) | `updates/Q3_2026/C01_loomvale_2026-10-06.txt` | Also C12, C16, C19, C21. Q2 numbers appear in the same sentences as distractors. |
| (b) pasted table email | Tidewright Labs (`C02`) | `updates/Q3_2026/C02_tidewright_2026-10-09.txt` | Tab-separated sheet paste; take the Sep column. Also C14 (markdown), C18 (space-aligned), C22 (pipe text). |
| (c) deck export markdown | Ossmere Health (`C03`) | `updates/Q3_2026/C03_ossmere_Q3-2026-deck-export.md` | Metrics spread across slide headings and a financials table. Also C15, C20. |
| (d) bullet-only update | Brackenfold (`C04`) | `updates/Q3_2026/C04_brackenfold_2026-10-14.md` | Terse bullets, no currency symbols ('MRR 19.8K', 'cash 1.24M'). Also C13, C17. |
| (e) 'all good, will send numbers next week' | Quarrytone AI (`C05`) | `updates/Q3_2026/C05_quarrytone_2026-10-17.txt` | All fields null; flag `no_numbers_reported`. Don't carry Q2 forward as if reported. |
| (f) no update at all | Murrelwick Robotics (`C06`) | `none (see manifest)` | Recorded in `updates/Q3_2026/manifest.json` as `not_received`; flag `missing_update`. |
| (g) quietly in trouble | Gantrell Dental Cloud (`C07`) | `updates/Q3_2026/C07_gantrell_2026-10-15.txt` | Upbeat prose; revenue down vs Q2; cash and `~4 months` runway only in a footnote. Flags `low_runway`, `revenue_decline`. |
| (h) summary vs table conflict | Corvellum Pay (`C08`) | `updates/Q3_2026/C08_corvellum_2026-10-07.txt` | Summary 'MRR crossed $210K' vs table $192,400 (gap = one-time fees, explained below the table). True MRR = table. Flag `conflicting_figures`. |
| (i) 'ARR' for non-recurring revenue | Stillmote Studios (`C09`) | `updates/Q3_2026/C09_stillmote_Q3-deck.md` | 'ARR: $1.2M' but 100% project revenue. `arr` = null, `revenue_type` = non_recurring, flag `non_recurring_arr`. |
| (j) units and currency | Vellstrom Data GmbH (`C10`) | `updates/Q3_2026/C10_vellstrom_2026-10-08.md` | EUR with European formats ('€38,5k', '€2.412.000'). Flag `non_usd_currency`. Units: C11 mixes '91.7k', '1.65m', a '$K' table and a 'thousands' row; flag `unit_inconsistency`. |

### Format per company (Q3)

| ID | Company | Format | File |
|---|---|---|---|
| `C01` | Loomvale Systems | (a) prose email | `updates/Q3_2026/C01_loomvale_2026-10-06.txt` |
| `C02` | Tidewright Labs | (b) pasted table (tab-separated) | `updates/Q3_2026/C02_tidewright_2026-10-09.txt` |
| `C03` | Ossmere Health | (c) deck export markdown | `updates/Q3_2026/C03_ossmere_Q3-2026-deck-export.md` |
| `C04` | Brackenfold | (d) bullet-only update | `updates/Q3_2026/C04_brackenfold_2026-10-14.md` |
| `C05` | Quarrytone AI | (e) reply with no numbers | `updates/Q3_2026/C05_quarrytone_2026-10-17.txt` |
| `C06` | Murrelwick Robotics | no update | `-` |
| `C07` | Gantrell Dental Cloud | (g) quietly in trouble (runway in footnote, revenue down) | `updates/Q3_2026/C07_gantrell_2026-10-15.txt` |
| `C08` | Corvellum Pay | (h) summary vs table conflict | `updates/Q3_2026/C08_corvellum_2026-10-07.txt` |
| `C09` | Stillmote Studios | (i) 'ARR' used for non-recurring revenue | `updates/Q3_2026/C09_stillmote_Q3-deck.md` |
| `C10` | Vellstrom Data GmbH | (j) EUR, European number formats | `updates/Q3_2026/C10_vellstrom_2026-10-08.md` |
| `C11` | Kettleworn Commerce | (j) mixed units (k / $K / m / thousands) | `updates/Q3_2026/C11_kettleworn_2026-10-12.txt` |
| `C12` | Halcyra Security | (a) prose email | `updates/Q3_2026/C12_halcyra_2026-10-05.txt` |
| `C13` | Pebblequill Learning | (d) bullet-only update | `updates/Q3_2026/C13_pebblequill_2026-10-16.md` |
| `C14` | Wrenfield Cover | (b) pasted table (markdown) | `updates/Q3_2026/C14_wrenfield_2026-10-13.txt` |
| `C15` | Dunmarsh Grid | (c) deck export markdown | `updates/Q3_2026/C15_dunmarsh_Q3-FY26-deck.md` |
| `C16` | Ashvane Legal | (a) prose email | `updates/Q3_2026/C16_ashvane_2026-10-08.txt` |
| `C17` | Velloway Mobility | (d) bullet-only update | `updates/Q3_2026/C17_velloway_2026-10-20.md` |
| `C18` | Thistlecrumb Foods | (b) pasted table (space-aligned) | `updates/Q3_2026/C18_thistlecrumb_2026-10-16.txt` |
| `C19` | Marrowlight Bio | (a) prose email | `updates/Q3_2026/C19_marrowlight_2026-10-14.txt` |
| `C20` | Sorrel & Pike People | (c) deck export markdown | `updates/Q3_2026/C20_sorrelpike_Q3-update-deck.md` |
| `C21` | Lanternwick Agents | (a) prose email | `updates/Q3_2026/C21_lanternwick_2026-10-11.txt` |
| `C22` | Cinderquay Games | (b) pasted table (pipe-separated) | `updates/Q3_2026/C22_cinderquay_2026-10-20.txt` |

## Scoring

`eval/score.py` takes a predictions directory (one `<company_id>.json` per company, schema-shaped) or a single JSON file (`{"companies": [...]}`). It reports:

- **Field accuracy**: 7 numeric fields + `revenue_type` x 22 companies. Money within 1% and same currency; runway within 0.5 months; counts exact. A field whose true value is `null` (not reported) is correct only if you also return `null`: abstaining is scored, hallucinating is penalized.
- **Accuracy on reported fields** (truth non-null) and **abstention accuracy** (truth null), so nulls can't inflate the headline.
- **Flags**: micro precision, recall, F1 against the expected flags.
- **Traceback**: of the correctly valued reported fields, the share whose cited span is in the right file and overlaps the key's span.

Every number prints next to the **carry-forward baseline** (Q2 values copied unchanged). An accuracy figure without that column means nothing: the baseline already gets some fields right (headcount that didn't change, revenue type).

## Demo story: three companies

1. **Gantrell Dental Cloud (`C07`), the troubled one.** The email is upbeat ("biggest pipeline yet"). Revenue is down from $61K to $52.8K MRR, customers from 87 to 74, burn up, and the only place runway appears is a footnote under the signature: `~4 months`. The GP's Q3 mark still holds it at the last round ($1.65M). Show: `low_runway` + `revenue_decline` flags, each linked to its span, and the report's watch list. The judge line: a GP skimming 22 emails misses this one; the system doesn't.
2. **Corvellum Pay (`C08`), the conflicting one.** The headline says "MRR crossed $210K"; the board table says $192,400; a line under the table explains the gap (one-time implementation fees, $18K). Show: the `conflicting_figures` flag with both spans side by side, and the system choosing the table figure with the reason.
3. **Loomvale Systems (`C01`), the clean one.** Prose email, every metric present, a new round at a $48M post that drives the Q3 markup from $1.5M to $3.15M. Show the happy path end to end: extraction → reconcile vs Q2 (MRR +20%, headcount 14 → 19) → the company's line in the LP report → the mark change in the capital account.

Expected Q3 fund numbers (for checking your report): NAV $32,577,000, TVPI 1.31x, DPI 0.04x, net IRR estimate 11.5%.

## Known simplifications

- Marks are set by formula (ownership x last post-money, cost, a 30% discount, or the secondary price); there is no independent valuation policy.
- Calls are sized to keep at least $250K of fund cash; no recallable distributions, no credit facility, no carry accrual.
- Gantrell's Q3 mark is deliberately stale (held at last round despite the update). That's a demo hook for "flag marks that the founder update contradicts", not an answer-key flag.
- One answer per field. Where a founder states a value twice consistently (Kettleworn MRR), the key lists the second mention in `alt_spans` and traceback accepts either.
