## Visual Brief — 5-slide carousel (Arc: Hook → Evidence → Mechanism → Counterpoint → CTA)

**Carousel thesis:** "Who owns the data layer" is really three questions: who writes the definitions, where they run, and whether you can leave. The evidence on each is thinner than the headlines suggest.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350)
**Tool routing summary:** all slides → Claude design (HTML/SVG). No Gemini.

### Slide 1 of 5 — Hook: put the question as one concrete decision
- **Visual mode:** Bold typography card
- **Headline:** Who signs off on what "revenue" means?
- **Body / content:** Subline: "The AI Briefing by Startup Grind · Civic Hall · Fri Nov 13." Small footer: "Hosted by Joshua Ness, Startup Grind NYC."
- **Palette:** dark slate #0F172A + white text + green accent #059669 (data/infrastructure) on the word "revenue"
- **Source attribution:** none (no data on the slide)
- **Alt text:** A title card asking who in a company has the authority to define "revenue" for an AI agent, with the event name, venue and date.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 5 — Evidence: the invite read next to its sources
- **Visual mode:** Framework / matrix (two-column table, four rows)
- **Headline:** The invite, read against its sources
- **Body / content:** Columns "Invite says" | "Source says". Rows: (1) "Spend more than tripled, to 3.3%" | "BCG: doubled in under a year, ~1.7% → 3.3% (another BCG page implies ~1%)". (2) "2.8 points sit outside IT" | "BCG: more than 80% of AI spend sits outside IT". (3) "Keep definitions in a layer you could move" | "Closest match: BCG's Aug lock-in essay (own the definitions, rent the tools). The Index itself: two-thirds of future-built firms commit to one platform". (4) "8.4% (placed next to VentureBeat's respondents)" | "The Modern Data Company survey, n=540+, vendor-run (as are the 61% and 16%)". Footer line: "Most numbers check out. Some moved between sources."
- **Palette:** dark slate bg + white text + green #059669 on the "Source says" column header only
- **Source attribution:** "Sources: BCG press release 2026-09-30; BCG lock-in essay 2026-08-06; BCG Weekly Brief; IT Brief / Business Wire 2026-08-19/20; Startup Grind NYC Luma invite. BCG: 1,330 execs, self-reported."
- **Alt text:** A four-row table comparing claims in the event invite with what each original source says: spend doubled rather than tripled, more than 80% outside IT, the portable-layer advice coming from a separate BCG essay, and three figures belonging to a vendor survey.
- **Tool:** Claude design (HTML/SVG)

### Slide 3 of 5 — Mechanism: ownership breaks into three claims, each with a live signal
- **Visual mode:** Diagram (three stacked horizontal bands, left label, right annotation)
- **Headline:** "Ownership" is three different claims
- **Body / content:** Band 1 "WRITES the definitions": "Snowflake Business Ontology: serves only owner-approved definitions (announced Nov 3; public preview soon)". Band 2 "RUNS them": "BCG Index: two-thirds of future-built firms commit to one enterprise-wide platform". Band 3 "LEAVES with them": "Apache Ossie, the open standard for portable metrics: still incubating. No published case found of definitions moved out of a vendor." A fourth thin strip under the stack: "PAYS for it: Atlassian enforces usage-based pricing from early December." The exit band is outlined in dashed green to show it is the least tested.
- **Palette:** dark slate bg + white text + green #059669 (dashed outline on the exit band)
- **Source attribution:** "Sources: Snowflake press release 2026-11-03; BCG Weekly Brief 2026-09-30; Apache Incubator (Ossie); diginomica 2026-11-06. BCG: 1,330 execs, self-reported."
- **Alt text:** A three-layer diagram that splits data-layer ownership into writing definitions, running them and leaving with them, with the live vendor signal for each and a separate strip for who pays.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 5 — Counterpoint: the semantic-layer paradox, measured three times
- **Visual mode:** Paired bar chart, three waves, legend on top
- **Headline:** Teams with a layer report more failures
- **Body / content:** Legend above the chart: "Running or building a layer" (#38BDF8) · "Evaluating or no plans" (#F59E0B). Bars: Jul 50% vs 21% (recurring failures, n=101); Aug 78% vs 37% (any failure, n=130); Oct 88% vs 60% (any failure, n=100). Dark label text on the bright fills. Caption: "VentureBeat: correlation, not cause. A layer may simply detect more. Groups under 40 can swing ~15 pts."
- **Palette:** dark slate bg + white text; series #38BDF8 / #F59E0B (the repo's high-contrast chart rule, with labels so meaning does not rely on colour)
- **Source attribution:** "Source: VentureBeat Pulse, Jul/Aug/Oct 2026 waves; self-selected reader panel."
- **Alt text:** Paired bars for three monthly survey waves showing teams with a semantic layer reporting AI context failures more often than teams without one, with a note that the link is correlational.
- **Tool:** Claude design (HTML/SVG)

### Slide 5 of 5 — CTA: the open question (no "other events" slide, per the 11-09 change)
- **Visual mode:** Bold typography card
- **Headline:** Architecture, org chart, or contract?
- **Body / content:** "When a company says it owns its data layer, which one is it, and which survives the first disagreement over 'revenue'?" Footer: "Bring one wrong answer your AI gave."
- **Palette:** dark slate bg + white text + green #059669 on "contract?"
- **Source attribution:** none
- **Alt text:** A closing card asking whether data-layer ownership lives in the architecture, the org chart or the contract.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**
- Arc fit: pass. The post sets up a data-anchored tension, and slide 4 is the optional counterpoint.
- Job differentiation: pass. The jobs are question, attribution table, ownership split, paradox chart and open question.
- Frame parallelism: not applicable (Arc 1).
- Thumb test per slide: pass. Every headline is 8 words or fewer.
- Source citations: pass on slides 2, 3 and 4.
- Adds information: pass. No single variant carries the table, the three-claim split or the three-wave chart. Variant C lists the waves as text, so in C the chart adds the visual comparison only.
- Final slide earns the swipe: pass.
