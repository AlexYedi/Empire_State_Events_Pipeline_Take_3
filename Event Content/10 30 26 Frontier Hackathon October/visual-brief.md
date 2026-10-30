## Visual Brief — 4-slide carousel (Arc 1: Hook → Evidence → Mechanism → CTA)

**Carousel thesis:** A software factory has eight controls. Each one physically lives somewhere: a file, a setting or a merge. The prediction is that a non-engineer holds the words at the front and the judgment at the end, not the machinery in between. Whether "the words" carry over between vendors is a testable question about one file.

**Slide count:** 4. The arc fits in 4, so it isn't padded. The cleaner-design steer also argues for fewer, emptier slides.

**Aspect ratio:** 4:5 (1080x1350), the LinkedIn carousel default

**Tool routing summary:** all slides → Claude design (HTML/SVG) → headless Chrome → PDF. Nothing is pictorial, so no Gemini.

**Palette (all slides):** dark slate ground #0F172A, white text #F8FAFC, and ONE accent, blue #60A5FA (agents, lightened for contrast on dark). Prediction marks are text labels ("SOLO", "HELP", "OUT OF REACH") with different border styles: solid blue for solo, dashed white for help, dotted grey #94A3B8 for out of reach. Meaning never rests on colour alone. Signature acid green #8FE83A appears only as the name-mark underline on slide 4.

**Carousel PDF title (public on LinkedIn):** "Eight controls, one non-engineer: a scorecard published before the day"

### Slide 1 of 4 — Hook: the eight controls as one line, with the prediction on it

- **Job:** Turns the post's list into a production line, so the reader sees where the predicted marks cluster (front and end solo, middle not), which the post states only in a sentence.
- **Visual mode:** Diagram (left-to-right flow with a return arrow)
- **Headline:** Eight controls. Which can I hold alone?
- **Body / content:** A horizontal flow: SPECS → CONTEXT → SKILLS → [agents build in a sandbox] → QA → CI → REVIEW, with a curved return arrow from REVIEW back to SPECS labelled LOOPS. DESIGN SYSTEMS is a side input feeding the build box. Each control node carries its predicted tag: SPECS solo · CONTEXT solo · SKILLS solo · QA help · CI out of reach · REVIEW solo · LOOPS help · DESIGN SYSTEMS out of reach. A legend sits ON TOP (solid = solo, dashed = needed help, dotted = out of reach). A bracket under SPECS–SKILLS reads "words", a bracket under REVIEW reads "judgment", and a bracket under QA–CI reads "machinery". Footer: "Predicted 4 of 8 solo · my bar: 5 · results after Oct 30". Page number 1/4.
- **Palette:** dark bg + white text + blue #60A5FA on the solid "solo" borders only
- **Source attribution:** Control list: Frontier Build NYC 2 invite, 2026. Prediction: the author's.
- **Alt text:** Eight software-factory controls drawn as a production line, with a prediction tag on each: the spec, context, skills and review ends marked solo, and the QA, CI, loops and design-system machinery in between marked as needing help or out of reach.
- **Tool:** Claude design (HTML/SVG)

### Slide 2 of 4 — Evidence: where each control lives in Obvious

- **Job:** Adds what the post doesn't carry: the concrete artifact or setting behind each control, per Obvious's own docs, so "control" stops being abstract.
- **Visual mode:** Framework / matrix (8 rows × 2 columns)
- **Headline:** Where each control lives
- **Body / content:** Columns "Control" | "In Obvious (per its docs)":
  - Specs | Product, UX, Technical phases; an agent can draft one from an idea
  - Context | AGENTS.md + .obvious/obvious.md; three clear rules beat thirty vague ones
  - Skills | SKILL.md folders, default branch only, cached up to 15 min
  - Review | config.yml rules: first match wins, max 20
  - QA | tests once per changed package, in parallel
  - CI | your existing pipeline runs on every PR
  - Loops | Loop Designer: on demand, trigger or schedule
  - Design systems | no Obvious doc found (rendered as a dashed "none found" cell)
  - Cells are ≤10 words each, rendered at ≥34px.
- **Palette:** dark bg + white text + blue #60A5FA on the Skills row's "default branch only" phrase (the hinge of the post's insight)
- **Source attribution:** Sources: Obvious Help Center (spec framework, repository context, custom skills, config.yml reference) and Autobuild page, fetched Oct 2026
- **Alt text:** A table mapping each of the eight controls to the file, folder or setting that holds it in Obvious, with design systems marked as having no documentation found.
- **Tool:** Claude design (HTML/SVG)
- **Accuracy note for the render:** the three-rules line paraphrases Obvious's repository-context page ("A file with three clear rules is more useful than a file with thirty vague ones"); keep it unquoted, with the source line. Don't add a loops retry count here. The "three tries" cap is from a homepage example only.

### Slide 3 of 4 — Mechanism: the CLAUDE.md test, as a 2×2

- **Job:** Shows the CLAUDE.md vs AGENTS.md test as an experiment with four possible outcomes and what each would mean, which the post only describes in two sentences.
- **Visual mode:** Framework / matrix (2×2)
- **Headline:** Does the factory read my rules?
- **Body / content:** Rows: "Run 1: repo as-is (CLAUDE.md only)" / "Run 2: + one-line AGENTS.md pointer". Columns: "Rule followed" / "Rule ignored". Each of the four cells carries a one-line meaning:
  - Run 1 followed → "CLAUDE.md is read. Rules port as-is."
  - Run 1 ignored → "Expected: Obvious's context page doesn't mention CLAUDE.md."
  - Run 2 followed → "A pointer is enough. Low switching cost."
  - Run 2 ignored → "The rules file is the lock-in."
  - All four cells carry an empty checkbox, to be ticked in the post-event version. A strip above reads: "Test task: one that only a CLAUDE.md rule can answer."
- **Palette:** dark bg + white text + blue #60A5FA outline on the Run 2 row
- **Source attribution:** Source: Obvious Help Center, "Give Autobuild repository context," fetched Oct 2026
- **Alt text:** A two-by-two grid of the two test runs (CLAUDE.md alone, then with an AGENTS.md pointer) against whether the rule was followed, with what each outcome would mean for switching costs.
- **Tool:** Claude design (HTML/SVG)

### Slide 4 of 4 — CTA: who may click merge, vendor by vendor

- **Job:** Puts the human line next to the reader's own, using three vendors' documented positions on the merge click (four lines; GitHub has two), and ends on the question.
- **Visual mode:** Split-frame comparison (4 stacked rows) + closing question
- **Headline:** Who may click merge?
- **Body / content:**
  - GitHub AI Scan (Oct 15) | advisory: can't block a merge
  - Copilot code review (Sept 1) | can approve, on admin-chosen paths, off by default
  - Obvious | require-human-merge, set per workspace
  - Vercel Foreman template | stops at a draft PR; merge isn't one of its tools
  - Closing line, large: "Where would you draw it on your repo?"
  - Name mark "Alex Yedi" with the #8FE83A underline. Page number 4/4.
- **Palette:** dark bg + white text + blue #60A5FA on the vendor names; #8FE83A name-mark underline only
- **Source attribution:** Sources: GitHub changelog, Sept 1 and Oct 15 2026 · Obvious Help Center, workspace settings · Vercel docs, Software factory, Sept 2026
- **Alt text:** Three vendors' documented rules (GitHub twice, Obvious, Vercel) for whether an agent may approve or merge a pull request, from advisory-only to human-merge-required, ending with a question to the reader.
- **Tool:** Claude design (HTML/SVG)

**Quality gate checks:**
- Arc fit: pass. There's one thesis (which controls a non-engineer can hold) and one mechanism (the rules-file test), so Arc 1. Arc 4 doesn't fit because no speakers are named, and Arc 3 has no "before" to show.
- Job differentiation: pass. The jobs are the predicted line, the artifact map, the test's outcome space, and the vendor merge lines. No two can be swapped.
- Frame parallelism: n/a (Arc 1).
- Thumb test per slide: pass on headlines (4–7 words). Slide 2 is the densest and is flagged against the cleaner-design steer. If it overflows at 375px, drop the second clause of each cell.
- Source citations: pass on all four slides.
- Adds information (not repetition): pass. The post has none of the words / judgment / machinery layout, the per-control artifact map, the four-outcome meanings or the vendor-by-vendor merge comparison. Variant B mentions three of the four vendor lines in prose, so slide 4 overlaps B only, and it adds Vercel Foreman.
- Slide count integrity: pass.
- Final slide earns the swipe: pass. It's a question the reader can answer about their own repo.
- Public-file check (carousel PDFs are downloadable): pass. No private files, paths or URLs, and no attendee names. The prediction is labelled as the author's.

**Themes (Step 1.3b, from the fixed list):** ["agents-agentic-stack", "devtools-ai-infra", "security-governance"]

**Goal / Target suggestion (for the parent's payload):** Goal: hybrid (reach + connection). Target: someone who has run an agent factory on a real repo replies naming the control that surprised them, or what they checked before Install. That's the Anti-Goodhart signal: an outsider using the scorecard. Secondary target: Jon Bell or the Obvious team engages before Friday. It also sets up the post-event results post as the payoff.

Excluded per provenance: [the "Cofounder / CPO" title · "retrain your intuition" and every unsourced Boskovic/Obvious thesis line ("babysitting prompt windows", the "individual velocity vs organizational throughput" line) · the invite's adoption quotes ("co-managers", "loudest skeptic", "four-week plan") and "at least one technical member" (private invite text, and Alex hasn't yet decided whether to tell the host he's solo) · the Level 1/2 ladder and edition 1 entirely (Alex didn't attend) · Jon Bell's 33B-token / $30K+ recap · the "first-hand" paraphrase in the post body (used only in the private note) · Obvious's Fusion, the prize amounts and the 23,500-credit arithmetic · Cognition's valuation and its Fusion · Factory's $5B raise, Router's 63% and Mentlio · Anthropic's 97% / 13.6% / 89% / 12→7% auto-mode figures · Anthropic's 70+ platforms / 1M skills · the 45-agent / 266-vuln claim · the Turan inverted-U · the "12 weeks of roadmap in 2 days" tagline · "1,000 PRs in one day" · Paragon, the ~3,000 teams and the ~$100M cumulative · Flatfile funding totals · why Microsoft hosts, and the venue address (Luma hides it) · ~158 attendees · all interior block times · "10+ hours" · the Daytona Sept 9 Shifrina content (unverified, unpublished) · BCG "agentic software factory" · private file names and paths in the repo · job-search and hiring framing · private Notion URLs]

⟦carousel-link⟧
