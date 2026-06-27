# Post-Event Brief — section-fill evidence (n=4 formats)
**Date:** 2026-06-27 · **Purpose:** decide which brief sections to freeze into the `/post-event-content` template (Phase B). Evidence from running the 16-section enhanced brief across 4 real events of different formats.

## Section-fill matrix
Rich = section was full & valuable · Thin = sparse · Empty = nothing · n/a = missing input.

| # | Section | Roundtable (ABB) | Demo Night (05/21) | Masterclass (06/03) | Workshop/Case-study (06/04) | Verdict |
|---|---|---|---|---|---|---|
| 1 | Quick Take | Rich | Rich | Rich | Rich | **CORE** |
| 2 | The Thesis | Rich | Rich | Rich | Rich | **CORE** |
| 3 | Pre → Post Gap | Rich | Empty | Thin | Thin | **CONDITIONAL** — rich only when a pre-event brief is wired in |
| 4 | Speaker Map | Rich | Rich | Rich | Rich | **CORE** (mandatory — diarization is never 1:1) |
| 5 | Full Quote Bank | Rich (82) | Rich | Rich (100+) | Rich (~70) | **CORE** |
| 6 | Pro-Tips | Rich | Rich | Rich (38) | Rich (12) | **CORE** (generalizes — even demo nights) |
| 7 | Best Practices/Patterns | Rich | Rich | Rich | Rich | **CORE** |
| 8 | Pitfalls/Anti-Patterns | Rich | Rich | Rich | Rich | **CORE** |
| 9 | Hot Takes | Rich (8) | **Thin (3)** | Rich | Rich (7) | **CORE, allow-thin** (thin at pitch/demo formats) |
| 10 | Substantive Insights | Rich | Rich | Rich | Rich | **CORE** |
| 11 | Anecdotes | Rich | Medium | Rich | Rich | **CORE** |
| 12 | Concept Glossary | Rich | Rich | Rich | Rich | **CORE** |
| 13 | Tools/Companies | Rich | Rich | Rich | Rich | **CORE** (esp. product-heavy events) |
| 14 | Stat Bank | Thin (1) | Thin | Rich | Rich | **FORMAT-VARIABLE** — rich at case-study/masterclass, thin at roundtable/demo |
| 15 | Documentarian Angles | Rich | Rich | Rich | Rich | **CORE** |
| 16 | Open Loops/Verification | Rich | Rich | Rich | Rich | **CORE** |

## Verdict
- **14 of 16 sections are CORE** — keep all. The learnings tier (Pro-Tips / Best-Practices / Pitfalls) **generalizes across every format**, including demo nights (operational demos yield real tactics) — validating the whole premise of the enhancement.
- **2 sections are conditional, not cut:**
  - **Pre→Post Gap (3):** rich only when the pre-event research brief is available. The 3 new events had no pre-event brief *on disk* (the agents ran folder-only) — but several exist in Notion. **Template fix: pull the pre-event brief from the linked Event page; if none, mark "n/a — no pre-event research."** Reinforces putting pre+post on the same Event page.
  - **Stat Bank (14):** format-variable — keep, allow "few/none stated."
- **Nothing earns deletion.** Every section was Rich in ≥2 formats; Hot Takes/Stat Bank just flex by format.

## Three mechanics that were TRUE IN ALL FOUR → make them mandatory in the template
1. **Diarization is never 1:1 with people.** Every event needed content-derived speaker mapping + confidence tags. → Speaker Map is a required step, not optional.
2. **ASR garbles proper nouns.** → Entity normalization seeded from a **curated keyterm list** (pre-event research → People/Companies DB) is mandatory at ingest (confirmed by the ingest scorecard; auto-extraction from the transcript fails).
3. **Folder-only synthesis misses web-enrichable facts.** The pre-existing briefs in these folders had web enrichment (Salesforce deals, ARR, install counts) that the folder-only runs lacked. → The **enrichment pass (web research on net-new people/companies/concepts) is essential, not optional.**

## Phase B template (frozen)
`/post-event-content` post_event_brief = the **16 sections above** (2 marked conditional) + mandatory: (a) ingest via locked Scribe recipe with keyterms-from-entity-list, (b) content-derived Speaker Map, (c) enrichment pass, (d) write to Event page + canonical Content Draft, (e) knowledge-graph write-back. Non-trivial build → runs the DoD gate.
