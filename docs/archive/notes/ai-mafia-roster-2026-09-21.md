# Flywheel "New York AI Mafia" — roster transcription (2026-09-21)

**Source.** A Flywheel-branded graphic, local copy `~/Desktop/1789413201063-1.jpg`, **plus the
source LinkedIn post text, supplied by Alex 2026-09-21.**

**Two-pass history, kept because the delta is the useful part.** Pass 1 read the graphic directly —
contrary to the session brief, it is fully legible at native resolution, so all names were read, not
guessed. Pass 2 used the post text, which **names all 15 companies outright** and settled every
company assignment. The post is now the authority for companies; the graphic remains the authority
for who appears *on it*.

**Reconciliation:** the graphic yielded **31 names**; the post names **32 people**. The delta is
**Jeff Denworth (VAST Data)** — the graphic appears to show two of VAST's three founders. Nothing
else conflicts.

## The 31 names (verbatim, as printed)

Raj Agrawal · Cristóbal Valenzuela · Alejandro Matamala · Anastasis Germanidis ·
Clément Delangue · Julien Chaumond · Thomas Wolf · Renen Hallak · Alon Horev ·
Misha Laskin · Ioannis Antonoglou · Yotam Segev · Tamar Bar-Ilan · Erik Bernhardsson ·
Akshat Bubna · Ted Bailey · Pim de Witte · Eloi Alonso · Thomas Reardon · Rob Williams ·
Maik Taro Wehmeyer · Maximilian Eber · James Cadwallader · Dylan Babbs · Gaurav Misra ·
Dwight Churchill · Benjamine Liu · TJ Ademiluyi · Adun Akanni · Anish Agarwal · Raaz Dwivedi

> **Name-fidelity note.** Spellings are exactly as the graphic prints them, including
> `Cristóbal`, `Clément`, `Benjamine Liu` (not "Benjamin"), and `Maik Taro Wehmeyer`.
> **No pronouns are inferred for anyone on this list** — use the name, or they/them.

## Company assignments — RESOLVED from the post (supersedes the pass-1 inference table)

All 15 companies, verbatim from the post. **Confidence is no longer an issue** — these are stated,
not inferred. The pass-1 logo-adjacency table is retired; it was right on 9 of 11 attempted and wrong
on the two noted below.

| # | Company | People | What it does (per the post) |
|---|---|---|---|
| 1 | **Runway** | Cristóbal Valenzuela · Alejandro Matamala · Anastasis Germanidis | Born in NYU Tisch ITP; $5.3B after a $315M Series E |
| 2 | **Hugging Face** | Clem Delangue · Julien Chaumond · Thomas Wolf | Brooklyn; open home of AI models |
| 3 | **VAST Data** | Renen Hallak · **Jeff Denworth** · Alon Horev | Data platform under the AI buildout |
| 4 | **Reflection** | Misha Laskin · Ioannis Alexandros Antonoglou | Ex-DeepMind; Brooklyn HQ |
| 5 | **Cyera** | Yotam Segev · Tamar Bar-Ilan | AI-native data security |
| 6 | **Modal** | Erik Bernhardsson · Akshat Bubna | Serverless AI compute |
| 7 | **Dataminr** | Ted Bailey | Real-time event detection, since 2009 |
| 8 | **General Intuition** | Pim de Witte · Eloi Alonso | Trains agents on Medal gameplay clips |
| 9 | **Flourish** | Thomas Reardon · Robert Williams | Neuro-AI lab; pre-product |
| 10 | **Taktile** | Maik Taro Wehmeyer · Maximilian Eber | Decision engine for AI underwriting |
| 11 | **Profound** | James Cadwallader · Dylan Babbs | How brands appear in AI answers |
| 12 | **Mirage** | Gaurav Misra · Dwight Churchill | AI video lab behind Captions |
| 13 | **Formation Bio** | Benjamine Liu | Buys stalled drug programs, finishes them with AI |
| 14 | **Alaffia Health** | TJ Ademiluyi · Adun Akanni | Sibling founders; health-plan claims |
| 15 | **Traversal** | Anish Agarwal · Raaz Dwivedi · Raj Agrawal | AI site reliability; Columbia / Cornell Tech |

**Two pass-1 errors, both instructive:**
1. **"Captions" → the company is MIRAGE.** Captions is the product. This is why `ashby/captions`
   returned 404 while `ashby/mirage` returns 11 live NYC roles.
2. **"Rob Williams" → the post writes "Robert Williams".** The graphic prints "Rob Williams". Use the
   graphic's spelling when referring to the graphic, the post's when citing the post.

> **Name-fidelity note.** Graphic spellings preserved above where they differ: `Cristóbal`,
> `Clément Delangue` (post: "Clem Delangue"), `Benjamine Liu`, `Maik Taro Wehmeyer`,
> `Ioannis Antonoglou` (post: "Ioannis Alexandros Antonoglou").
> **No pronouns are inferred for anyone on this list** — use the name, or they/them.
> **Do not repeat the post's valuation or funding figures as fact** — they are the author's claims,
> single-sourced, and several are large. Verify before any public use.

## ATS outcome (this is the part that shipped)

Probed live 2026-09-21 and **added** to the scan registry (`target-companies.md`, 21 → 30):

| Company | ATS | Slug | Open roles |
|---|---|---|---|
| Runway | ashby | `runway-ml` | 40 |
| Profound | ashby | `profound` | 73 |
| Modal | ashby | `modal` | 34 |
| Taktile | ashby | `taktile` | 43 |
| Reflection AI | ashby | `reflectionai` | 57 |
| Hugging Face | workable | `huggingface` | 8 |
| **Mirage** | ashby | `mirage` | 11 |
| **Traversal** | ashby | `traversal` | **24 — incl. Enterprise AE East + West, Solutions Engineer** |
| **Formation Bio** | greenhouse | `formationbio` | 24 |

Probed and **not resolved** (404 on every vendor): Cyera · VAST Data · General Intuition ·
Alaffia Health · Decart. **Dataminr** has a valid Workable account with **0 open roles** — left out
rather than added empty.

**THREE silent-failure traps are now recorded in the registry** — all three return HTTP 200 on the
wrong company, so they fail silently rather than erroring:
1. Runway is `runway-ml`; bare `runway` is a different company.
2. Profound is Ashby; its Greenhouse namesake is a Boston biotech.
3. **Flourish is NOT `greenhouse/flourish`** — that board belongs to a wealth-management fintech
   ("helping financial advisors since 2017"), not Thomas Reardon's neuro-AI lab. **Rejected.** The
   neuro-AI Flourish is pre-product and may have no public ATS at all.

**The headline result for the job search: Traversal.** AI SRE for the enterprise, NYC, and it has
open **Enterprise Account Executive (East and West)** plus a **Solutions Engineer** — the closest
match to Alex's target role shape in the entire batch, and it would never have surfaced without
the post resolving the logo.

Workable support was added to `role-radar` Step 1a in the same pass (PR #107) — without it the
Hugging Face row would have been a dead reference.
