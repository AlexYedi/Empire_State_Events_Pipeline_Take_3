# inbox-miner — cohort eval v1 (baseline, dry run)

**Purpose:** fixed 7-newsletter cohort to measure Stage-B extraction, find data-cleaning/management challenges, scope a first-pass improvement set, then re-run the SAME cohort to diff. EDD on a golden set. **No graph writes during the eval loop.**
**Run:** baseline, 2026-09-10. Extractor = inbox-miner SKILL.md as of this date (post source≠subject + redirect-resolution + self-notification guard).

## Cohort (diverse-by-challenge)

| # | Newsletter | thread | what it stresses |
|---|---|---|---|
| 1 | GTM Engineer Pulse | 1a0861d3e39beec0 | dense multi-company GTM (already gated: 7 signals, source≠subject + redirect-resolution proven) |
| 2 | AI Business (ittnewsletter) | 1a0874e092abf2eb | **teaser/stub body** |
| 3 | Techpresso | 1a087043472fa6bc | **teaser/stub body (worst)** |
| 4 | Superhuman Code (The Code) | 1a0866676ce2e094 | dense; sponsor sections; altered names |
| 5 | a16z | 1a08680cab2332c5 | single-company deep + VC-promo + off-domain (defense) |
| 6 | ChinaTalk | 1a0863fc3027e30e | **abstain test** (policy essay, ~0 company events) |
| 7 | GenAI Works | 1a085ad363ee6c2a | dense; heavy cross-newsletter overlap |

## Per-newsletter baseline

- **#1 GTM Pulse** — 7 clean signals (OpenAI/Astra launch; Clay funding⚠️reported + Sequencer launch; Monaco funding + Overlayy acq; Adobe/Rilo acq; Snitcher MCP). Redirect-resolution caught the Monaco investor discrepancy (Founders Fund vs Benchmark). ✅ works.
- **#2 AI Business** — ❌ **plaintext body ≈ empty.** A "sneak peek" teaser: one headline (OpenAI Millennium Problem → nytimes.com) + subscription boilerplate. The subject line ("Mistral raises $3.4B, shifts course") held the richest signal and it is **NOT in the body.** Links are `link.ittnewsletter.com/click/<base64-dest>` (destination base64-encoded in the path, decodable without following).
- **#3 Techpresso** — ❌ **body is a single stub line:** "copy this link to view online: archive.techpresso.co/p/meta-launches-muse-ai-assistant". Zero extractable content in plaintext. Signal (Meta Muse, OpenAI math) is only in the web version.
- **#4 Superhuman Code** — ✅ dense. Signals: Meta→Muse (launch, +Sentinel approval agent); OpenAI→Navier-Stokes proof (research, + Buckmaster/Anthropic training-data controversy); Anthropic→Jacob Coxon departure (person-event); Uber/Spotify agent-cost case studies (borderline — *how-to*, not an entity event). Sponsor noise to drop: TigerData ("PRESENTED BY"), SpaceXAI/GrokBot event, repo/tutorial picks. Altered/parallel names: Astra=GPT-6, Fable 5.1=Claude, GrokBot/SpaceXAI=Grok/xAI, Muse=Meta agent.
- **#5 a16z / Covenant** — ✅ single-company deep: Covenant → Anthem launch + **$250M raised** + 3 factories (US/DE/IL); co-founder Ofir Dayan, Pres. Abby Denburg. BUT it's a VC promoting a portfolio co, and it's **defense-hardware — off Alex's AI/GTM domain.** Relevance question, not an extraction failure.
- **#6 ChinaTalk** — ✅ **ABSTAIN (correct target ≈0 signals).** Long Taiwan drone-policy essay. Named cos (DJI, NCSIST, Anduril, Shield AI, Kratos, AeroVironment, Thunder Tiger, Starlink) are *analysis context*, not market events. Minting e.g. "Anduril — market" here would be a FALSE signal. Baseline expectation: abstain; at most 1–2 very-low-confidence contract mentions flagged, none written.
- **#7 GenAI Works** — ✅ dense: Anthropic→Coxon/Hubinger (same story as #4); OpenAI→Navier-Stokes (same as #2,#3,#4); OpenAI→Images 2.5 launch (openai.com/index/introducing-chatgpt-images-2-5); Google DeepMind→AlphaGenome atlas launch. Tool-of-day (Goblin Tools) = filter.

## Cross-cohort issues (scored, ranked by leverage)

| # | Issue | Severity | Evidence |
|---|---|---|---|
| **I1** | **Cross-newsletter dedup** — same event in many issues. OpenAI Navier-Stokes appeared in **4 of 6** (#2,#3,#4,#7); Coxon departure in 2 (#4,#7); Astra across #1+refs. Naive per-signal write = 4 duplicate rows. | **HIGH** | 4× same week |
| **I2** | **Dedup key must be the canonical URL, not (company,kind,date)** — OpenAI shipped Navier-Stokes AND Images 2.5 same day, both "launch-ish" → (company,kind,date) would OVER-MERGE two distinct events. The **resolved canonical primary_url is the natural dedup key** (Navier-Stokes vs Images-2.5 have different URLs) — and it MERGES the same event across newsletters (all 4 resolve to the same openai.com URL). Ties redirect-resolution + dedup into one mechanism. | **HIGH** | #7 vs #2–4 |
| **I3** | **Teaser/stub bodies** — plaintext body empty/redirect-only. Need: detect stub → fallback to (a) subject-line parse, (b) fetch the "view online"/archive URL, (c) decode base64 `click/<b64>` links. | **HIGH** | 2 of 7 (#2,#3) = 29% |
| **I4** | **Sponsor/ad filtering** — "PRESENTED BY", "Tool of the Day", sponsored events (TigerData, Goblin Tools, GrokBot event) must not become company signals. | **MED** | #4,#7 |
| **I5** | **Relevance scoping (DECISION for Alex)** — capture ALL company signal, or filter to Alex's domains (AI-native / GTM / enterprise-SaaS)? Covenant (defense-hardware) + the ChinaTalk defense cos are the test: real events, off-lens. | **MED (decision)** | #5,#6 |
| **I6** | **Name aliasing** — same entity, different names across newsletters (Grok/xAI/GrokBot/SpaceXAI; GPT-6/Astra). Alias map needed so they resolve to one company row. | **MED** | #4 |
| **I7** | **Event-kind mapping + abstain bar** — research result / researcher departure / cost case-study don't map cleanly to launch|market|funding|exec_move. Need mapping guidance + a firmer "interesting-but-not-an-entity-event → abstain" bar (Uber/Spotify how-tos, ChinaTalk analysis). | **MED** | #4,#6,#7 |

## Scoped first-pass improvements (to implement, then re-run this cohort)

1. **[I1+I2] Canonical-URL dedup, run-batched.** Resolve every signal's redirect → canonical URL (already required); make that URL the **primary dedup key**. Dedup ACROSS all newsletters in a run *before* the write gate: one event row per canonical URL, carrying N source citations (`metadata.sources = [newsletter domains]`). `(company,kind,date)` becomes a coarse fallback only when no URL.
2. **[I3] Stub detection + fallback ladder.** If plaintext body < N chars or is a "view online" stub: (a) parse the subject line for the headline signal, (b) resolve/decode the primary link (follow redirect OR base64-decode `click/<b64>`), (c) optionally fetch the web/archive version. Flag stub-sourced signals lower-confidence.
3. **[I4] Sponsor/section filter.** Drop content under "PRESENTED BY / SPONSORED / Tool of the Day / Top Repo / Trending Cookbook" headers before extraction.
4. **[I6] Alias map.** Seed `inbox-miner` alias table (Grok↔xAI↔GrokBot; GPT-6↔Astra; Claude↔Fable 5.1) feeding the company-slug resolver; grows per run like `signal-taxonomy.md`.
5. **[I7] Kind + abstain guidance.** Explicit mapping (research-result→market; notable-departure→exec_move w/ person in desc; case-study/how-to→abstain) + a raised abstain bar for analysis/opinion with no entity event.
6. **[I5] — hold for Alex's ruling** (relevance scope). Not built until decided.

## Metrics to diff on re-run
- signals extracted per newsletter (recall) + junk rate (precision)
- **dedup: unique events after cross-newsletter merge** (target: Navier-Stokes = 1 row / 4 sources, NOT 4 rows; Images-2.5 stays separate)
- stub-recovery rate (#2,#3 yield signal after fallback, vs 0 at baseline)
- sponsor-leak count (target 0)
- abstain correctness (#6 ChinaTalk ≈0 written)
- URL-resolution success + discrepancies caught

---

# Re-run v1.1 (same cohort, improved extractor) — 2026-09-10

Applied: canonical-URL dedup (run-batched) · stub-fallback ladder · sponsor filter · alias map · kind/abstain bar · relevance tag. Still dry (no writes).

## Unique events after cross-newsletter merge (canonical-URL keyed)

| Event | canonical_url | sources (merged) | company resolve | kind | relevance | flags |
|---|---|---|---|---|---|---|
| OpenAI Navier-Stokes proof | openai.com/index/navier-stokes-solution | **4** (#2,#3,#4,#7) | MATCHED OpenAI | market | ai-native | ⚠️verify (Buckmaster dispute) |
| OpenAI Images 2.5 | openai.com/index/introducing-chatgpt-images-2-5 | 1 (#7) | MATCHED OpenAI | launch | ai-native | — (kept SEPARATE from Navier-Stokes — over-merge avoided) |
| OpenAI GPT-6 Astra | openai.com/index/gpt-6-astra | #1(+refs) | MATCHED OpenAI | launch | ai-native | — |
| Anthropic — Coxon departure / Hubinger doom | cnbc.com/2026/09/09/anthropic-researcher-quits-ai-safety.html | 2 (#4,#7) | MATCHED Anthropic | exec_move | ai-native | person in desc, no row |
| Meta — Muse agent | introducing.muse.ai | 2 (#3-recovered,#4) | ⚠️ CREATE Meta (or parent of existing "Meta Superintelligence Labs"?) | launch | ai-native | alias/parent question |
| Google DeepMind — AlphaGenome atlas | blog.google/…/alphagenome-atlas | 1 (#7) | MATCHED Google (alias DeepMind→google) | launch | ai-native | — |
| Clay $7B (reported) | axios.com/…/clay-7-billion… | #1 | MATCHED Clay | funding | gtm | ⚠️reported |
| Clay Sequencer GA | clay.com/blog/clay-email-sequencer | #1 | MATCHED Clay | launch | gtm | — |
| Monaco $35M + Overlayy acq | businessinsider.com/…/monaco | #1 | CREATE Monaco | funding/market | gtm | ⚠️verify (investor conflict) |
| Adobe → Rilo acq | techcrunch.com/…/adobe-acquires-…-rilo | #1 | CREATE Adobe | market | enterprise | — |
| Snitcher MCP | snitcher.com/blog/…-mcp-server | #1 | CREATE Snitcher | launch | gtm | — |
| Covenant — Anthem + $250M | a16z.news/p/introducing-covenant | #5 | CREATE Covenant | launch/funding | **off-domain** | ⚠️secondhand (VC post, not Covenant's own site) |
| Mistral $3.4B raise | *(unresolved — stub subject-line lead)* | #2 | (held) | funding | ai-native | ⚠️ from_stub, no citable URL → needs web-version fetch |

## Diff vs baseline — improvements
- **I1/I2 dedup ✅** — Navier-Stokes collapsed 4→1 event (4 citations); Images-2.5 correctly kept separate despite same company+day (proves URL-key beats (company,kind,date)).
- **I3 stub recovery ✅ (partial)** — #2 recovered the "Mistral $3.4B" lead from the subject line (baseline=0 from body); #3 Meta-Muse recovered via cross-ref. Remaining gap: Mistral has no citable URL without step-(c) web-version fetch → correctly held, not written.
- **I4 sponsor filter ✅** — TigerData, Goblin Tools, GrokBot event dropped (0 leaks).
- **I6 abstain ✅** — ChinaTalk → 0 signals (Anduril/Shield-AI/DJI stayed context, none minted).
- **I5 relevance tag ✅** — Covenant tagged `off-domain` (captured, not dropped); rest ai-native/gtm/enterprise.
- **I6 alias ✅** — DeepMind→google resolved to the matched row.

## Diff vs baseline — remaining gaps / new misfires
1. **Meta company resolution** — "Meta" not in the 183-row table; risk of confusion with existing "Meta Superintelligence Labs". Needs an alias/parent rule (is the lab a child of Meta?). Add to alias map after a ruling.
2. **VC-newsletter as source (Covenant)** — canonical only resolved to the a16z post, not Covenant's own announcement → `secondhand` flag. Fix: for VC/aggregator sources, prefer the subject company's own primary URL when findable (a second resolution hop).
3. **Stub step-(c)** — subject-line recovery gets the lead but not a citable URL; the web-version fetch (ladder step c) isn't exercised yet. Build it if stub newsletters prove worth the fetch.

**Verdict:** the first-pass improvements resolved the two HIGH issues (dedup, stubs-partial) and both MED filters (sponsor, abstain) on the same cohort. 3 residual gaps are scoped + smaller. Extractor is materially better; ready to consider a first real write on the clean subset — pending Alex.
