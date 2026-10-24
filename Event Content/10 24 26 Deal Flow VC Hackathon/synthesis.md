# Deal Flow (10-24): synthesis of the deep pass

*Reconciles `market-map.md`, `value-chain-research.md` and `systems-analysis.md`. 2026-10-23.*

## Challenge anchor (everything below traces to these)

| ID | Organizers' clause | What we deliver against it |
|---|---|---|
| F1 | "LPs commit capital for ten years and get PDFs in return." | Numbers LPs can check, not a PDF they have to trust (spans + LP click-through) |
| F2 | "Quarterly reports arrive in different formats." | Reads any format, no new form |
| F3 | "Valuation marks move with little explanation." | Reconciliation diff + an unexplained-mark flag the GP can annotate but not delete |
| F4 | "Judging a GP's real track record means rebuilding it by hand." | Quarters build up into a sourced history (roadmap; Fund II data room) |
| P1 | "40 updates in 40 formats, when it gets them at all." (Track 3) | Extraction from any format; a missing-update flag |
| P2 | "Partners learn a company is in trouble when it asks for a bridge." (Track 3) | Low-runway flag a quarter early (Gantrell's footer literally says "bridge") |
| E1 | "Spreadsheets, gut feel and endless inbox triage." (event) | The inbox becomes a reconciled table |

Out of scope on purpose: secondary pricing (Track 4's last clause). Rule: a feature, task or slide with no challenge ID gets cut.

## What the three passes agree on

| Finding | Market map | Value chain | Systems |
|---|---|---|---|
| Collecting and extracting data is crowded; the letter/narrative layer is open | ✔ | ✔ (the portfolio layer stays unstandardized) | ✔ (letter-writing alone is #12 leverage) |
| Our "ILPA-aligned" claim must narrow: ILPA covers the ledger the admin owns | ✔ | ✔ | — |
| The real value is **Fund II speed and LP trust**, not hours | (hours unproven) | ✔ 79% of LPs declined a re-up; Funds I–IV got ~12% of capital | ✔ LP trust is the governing stock |
| **Provenance / reconciliation** is the differentiator | ✔ (Carta has it only on its roadmap) | ✔ value leaks at the hand-offs | ✔ #6 information flow, if it reaches the LP |
| **Privacy posture** is a design choice, not a footnote | — | ✔ LPAs, FOIA, NDAs; no ILPA guidance on LLMs | ✔ Bettina's question |
| A fluent AI letter can make things *worse* | — | ✔ (stale marks) | ✔ Shifting the Burden; fluency reads as truth |

## Where they pull against each other, and the resolution

- **The systems pass says** push provenance all the way to the LP: that's the leverage point.
- **The value-chain pass says** disclosure must be GP-controlled, because marks, LPA confidentiality and founder NDAs make a wide-open LP view a non-starter for the buyer.
- **Resolution: two layers.**
  1. **The internal ledger is fully honest.** Every number carries its source span. Any change from last quarter without an explanation is flagged red, and the flag can't be deleted, only annotated by the GP.
  2. **The LP view is published by the GP, per item.** LPs can click through to the source wherever the GP shares it. Where the GP shares only the annotation, the LP sees it as an annotation, not as an invented number.

  The GP keeps control and the LP gets verifiability. Nothing is ever smoothed silently.

## The refined thesis (replaces "the letter writes itself")

> **"Your quarterly update, explained and provable. We turn messy founder updates into a GP letter where every number traces to its source and every change is explained, so a Fund I manager can earn the trust that closes Fund II."**

- **Buyer:** the emerging-manager GP (Fund I/II). **Value:** Fund II closes faster, and hours come back as a side benefit. **Price:** about $6k per fund per year, against an admin bill of $18–60k. The LP view is free and doubles as distribution, because an LP who sees it asks their other GPs for it.
- **Positioning line:** "Carta traces numbers for the GP. We trace them for the LP."
- **Companion, not competitor, to the admin:** the admin owns the ILPA ledger; we own the portfolio narrative and performance section that sits next to it.
- **Privacy:** redact before inference by default, with founder and company names tokenized. A local-model option is on the roadmap slide. We can say plainly where the data goes.
- **Roadmap slide:** a track record that accumulates quarter by quarter becomes the Fund II data room ("the sum of the ledgers"), then a two-sided GP↔LP↔founder layer with one shared founder update for every investor on the cap table.

## What changes in the demo (3 minutes)

1. **Opening quote:** a GP from today's calls on hours or on LP pushback. Fallback: "79% of LPs declined to re-up with at least one GP last year."
2. Paste messy Q2 and Q3 founder emails for **one** company, the troubled one from the data pack.
3. Extracted metrics appear with highlighted source spans.
4. **Reconciliation diff:** ARR up, burn up, runway down, **mark unchanged**, so that row turns red: *"Unexplained, GP annotation required."* The GP types one line.
5. The letter paragraph renders **only** from reconciled deltas. Every number is clickable.
6. **LP view:** click a number and land on the founder's sentence. The annotated mark shows as an annotation.
7. **Close:** extraction accuracy vs. the carry-forward baseline (from the data pack's scorer), hours today vs. with the tool, price, and the roadmap.

## What it changes in the build kit

- **Hero screens:** the reconciliation diff (with the red flag) and the click-to-source view. The letter generator is constrained to render from deltas.
- **Must-have:** extraction with spans, the delta table with the unexplained flag, GP annotation, the click-through, and a redaction pass before the LLM call.
- **Cut first at 2:30:** PDF export, multi-company rollup, the fund-level metrics page.
- **Judge map:**
  - Bettina: privacy, redaction, data perimeter.
  - Radhika: spans, no fabrication, accuracy vs. baseline.
  - Garrett: reconciliation, hours vs. baseline, who pays.
  - Michael: operator-LPs as readers; works for any fund anywhere.
  - Abeera: portfolio scale.
  - D.J.: founders send what they already send, with no new format.

## Questions for the room and today's calls

- GPs: hours on the last letter? Who is your admin? Would you send LPs source links? *(This is the thesis-killer test.)*
- LPs: what do you rebuild by hand? Would you click?
- Michael Barone: how do Everywhere's operator-LPs receive updates?
- Bettina Sosa: what founder data may leave the perimeter?
