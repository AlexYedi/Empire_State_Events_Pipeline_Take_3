# Deal Flow (10-24): LP reporting as a trust system, not a document pipeline

*`alex:systems-analyst` (Fable), 2026-10-23. Meadows eight-phase analysis. Everything is inference unless marked; confidence on key claims.*

## The core read

- **The stock that governs behavior is LP trust in the GP, not GP hours.** The "letter writes itself" pitch targets GP hours, which is the smallest stock in the system.
- **Other stocks:** verified track record (close to zero for Fund I/II), unexplained variance ("fog" that builds up every quarter a mark moves without a reason), founder attention (a commons every investor draws on), and GP hours.
- **The 10-year lock-up is a huge buffer.** It lets the system run with broken feedback for a decade.

## Loops

- **R1 Opacity ratchet:** smoothed marks plus selective narrative mean fewer awkward questions now, so opacity looks free and grows. This loop dominates between fundraises.
- **B1 Trust correction:** a surprise markdown or DPI gap lowers trust, so Fund II comes in slower or smaller, so the GP discloses more. The delay is 2–4 years, which produces an overshoot-and-collapse shape. This loop dominates at the Fund II raise, which is exactly when emerging managers feel the pain.
- **R2 Success to the successful:** big GPs can fund a CFO and Carta, which gets them ILPA-grade reporting, institutional LPs and more fees. Emerging managers send PDFs, attract HNW LPs only, earn thin fees, and keep sending PDFs.
- **B2 Founder burden (perverse):** the GP asks for more, founders reply later and thinner, so the GP asks for more again.
- **R3 Rebuild cost:** rebuilding a track record is expensive, so LPs rarely do it, so GP narrative goes unchecked.

## Archetypes

- **Shifting the Burden (80%):** an AI letter-writer relieves the symptom while the GP's own discipline (knowing *why* each number moved) wastes away. As framed, the current wedge risks *being* that intervention.
- **Success to the Successful (80%):** R2 above.
- **Tragedy of the Commons (60%):** founder attention.
- **Seeking the Wrong Goal (65%):** "polished report shipped" is effort; "the LP can answer their own question" is the result.

## Who benefits from opacity

- GPs (mark timing, which story gets told), founders (when bad news reaches the GP), fund admins (complexity sustains fees) and secondary buyers (the fog sets their discount).
- **Only LPs pay for all of it.**
- **The tension:** the buyer (the GP) partly benefits from the asymmetry the tool removes.
- **The resolution:** for a Fund I/II manager with no track record, *verifiable transparency is a costly signal* that incumbents' narrative can't cheaply copy. **Provenance substitutes for track record.** (Costly signaling is Spence 1973; extrapolated beyond Meadows.)

## Stakeholders

| Actor | What they actually want | Stance toward the tool |
|---|---|---|
| Emerging GP (Fund I/II) | Close Fund II with minimum hours and hard questions | Buyer. Pays if it speeds up Fund II; resists if it exposes unexplained marks |
| Fund CFO / multi-partner GP | Clean audit, no restatements | Wants reconciliation, not prose |
| Platform team | Fewer founder complaints | Ally if founder burden falls |
| Fund admin | Keep their fees | Resists commoditization; a channel later |
| Auditor | Low liability | Neutral; likes source links |
| Founder | Minimal reporting time; delay bad news | Welcomes parsing of what they already send; resists new formats |
| Institutional / FoF LP | No surprises; benchmark GPs | Captures the most value; not the buyer today |
| Family office / HNW / operator-LP | Low effort, trust | Will click a source link; won't pay |
| Secondary buyer | Buy at a discount | Loses from transparency; never sell to them first |

## Leverage points (Meadows)

- **What the current pitch pushes:** #12 parameters (hours) and #9 delays (a faster report). Those are real, but Carta, Visible and Standard Metrics already sit there, and they don't touch R1, R2 or B1.
- **Highest workable:** **#6 information flows.** "Every number one click from its source" counts *when the click reaches the LP*, not only the GP. That strengthens B1 and shortens its delay from years to the quarter the change happened.
- **Next:** **#3 goals.** Redefine the output from "report produced" to "unexplained variance = 0": reconciliation that refuses to smooth.
- **Roadmap only:** **#10/#5**, a two-sided GP↔LP↔founder data layer with one shared founder update for every cap-table investor (it ends the commons problem). Too much cold-start for six hours.
- **Warning:** a fluent LLM letter-writer pushes #6 *backwards*, because it adds more narrative per unit of data and fluency reads as truth. **Architectural fix:** narrative sentences may be generated only from reconciled deltas that have spans; anything unsupported can't be rendered.

## Second- and third-order effects (provenance-first variance reporting)

- **First order:** GP hours fall; the letter is consistent; the LP can click.
- **Second order:**
  - Parsing messy updates lowers founder burden and may *raise* response rates.
  - GPs may stop pushing founders for structure (burden shift).
  - Fewer LP calls and faster re-ups.
  - The Fund II data room becomes "the sum of the ledgers."
  - Secondary discounts tighten for transparent funds.
- **Third order:**
  - GPs curate which updates get ingested (selection moves upstream).
  - Founders write more defensively once their words become LP-visible.
  - Cross-fund benchmarking emerges and R2 re-forms around the tool. That's desirable, but mid-tier GPs will resist.
- **Perverse effects to design against:**
  1. Polished narrative hides more. Fix: "unexplained" flags can't be deleted, only annotated.
  2. Extraction errors carry false confidence. Fix: span-level confidence and GP sign-off per delta.
  3. The GP rubber-stamps the review. Fix: review is a *diff of deltas*, not a read of prose.
  4. A weak fund gets dressed up. Provenance itself limits this.
- **New healthy loop B3:** LP clicks show the GP what gets questioned, so the GP explains it proactively next quarter.
- **Pre-mortem:** GPs love the time saved and quietly switch off the LP-facing links. If use stays GP-internal, it's a Carta feature.

## Recommendation

1. **"The letter writes itself"** (letter automation). Crowded, #12 leverage. Not recommended as the headline.
2. **"What moved and why, with provenance the LP can click."** Variance explanation plus source spans *is* the product; the letter is one output. Same build, reframed around #6/#8. Positioning: *"Carta traces numbers for the GP; we trace them for the LP."* **Recommended (75%).** Open risk: will GPs actually send the links?
3. **The two-sided GP↔LP↔founder data layer.** Use it as the roadmap slide; don't build it Saturday.

**Track-record reconstruction for Fund II is option 2 accumulated over quarters.** Say that to the judges; it answers the organizers' "rebuild by hand" line directly.

## Demo (3 minutes)

One company, two quarters:
1. Paste two messy founder emails (Q2, Q3).
2. Metrics appear with highlighted source spans.
3. Reconciliation table: ARR +40%, burn up, runway down, **mark unchanged**.
4. A variance paragraph where every number is clickable. One delta renders red: *"unexplained, GP annotation required."* The GP types a one-line reason.
5. Switch to the **LP view**: click a number and land on the founder's sentence.
6. Close on the null baseline: hours today (from a call) vs. with the tool.

The red flag the GP can't delete makes the systems insight visible without naming it.

## Business model

- **The GP pays per fund per year,** because the GP captures hours and Fund II speed.
- **The LP view is free.** An LP in ten funds asks the other nine GPs for it, which is the distribution loop and the cheap way to attack R2.
- **Fund admins:** a channel later, never the first buyer.
- **Never sell data to secondary buyers.**

## What to watch / what would prove this wrong

- **Watch:** share of reports sent with LP links on; unexplained flags per quarter (should fall); LP click-throughs; founder response rate vs. the quarter before.
- **Wrong if:** GPs buy, use it internally and disable LP links at scale, or LPs never click.
- **Interview questions that test it:** guide Q4 (LP pushback on numbers) and Q7 (what the GP would pay).

## Teaching layer

1. **Leverage-points hierarchy** (Meadows, *Thinking in Systems*, ch. 6). Parameters < delays < balancing loops < information flows < rules < goals. "Faster report" is a parameter; "the reader can verify the number" is an information flow.
2. **Shifting the Burden** (Meadows ch. 5; Senge). A fix that relieves the symptom while the system's own capacity wastes away. The escape is a tool that strengthens the GP's explanation discipline (the red flag) instead of replacing it.
3. **Costly signaling** (Spence 1973). A signal is credible when it's expensive for the low-quality type to fake. Provenance is cheap for an honest Fund I and expensive for a smoothed one.

**Interview framing:** "Most AI-in-finance pitches automate the document; I'd argue the product is the information flow. Scoping an LP-reporting agent, I asked who benefits from today's opacity and who pays for it. The answer flipped the product from 'write the GP letter faster' to 'let the LP click any number to its source,' the only version an emerging manager can use to buy trust it hasn't earned yet."
