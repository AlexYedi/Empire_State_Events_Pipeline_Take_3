# Eric Nowoslawski's `coldoutboundskills` repo: harvest

> **Filed:** USE-NOW items → YED-220 · personal lead magnet (entry #6) → YED-219 (parked). Source event briefs: GTM World Tour NYC https://app.notion.com/p/3e5d3699c2db81dc9690d5f998de95a8 · Clay Grok Bot livestream https://app.notion.com/p/3e5d3699c2db810e96bec309f6be540f

Source: https://github.com/growthenginenowoslawski/coldoutboundskills. Read on 2026-09-24 from a shallow clone of `main` plus a fetched copy of the unmerged branch `clay-cli-tested-playbooks`. None of the repo's code was run.

---

## 1. Repo map

**What it is:** open-source Claude Code skills for running a full cold-email operation: strategy, sending infrastructure, list building, copy, sending, and iteration. The README says the skills were "Built by GrowthEngineX from patterns across 1,000+ real B2B campaigns." It has 30 skills in 5 tracks, plus 19 "signal playbooks" in Track 6. Each playbook comes three ways: a Claude skill, a Clay table recipe, and a Clay CLI workflow.

| Item | Value |
|---|---|
| License | **MIT** (© 2026 GrowthEngineX). You can reuse, fork, or copy it commercially. You must keep the copyright and license notice in any copied portion. The README adds: "Attribution appreciated but not required." |
| Stars / forks | 727 / 254 (GitHub API, 2026-09-24) |
| Created | 2026-03-10 |
| Last commit on `main` | 2026-08-18: "Add 19 signal playbooks under skills/playbooks/" |
| Last push anywhere | 2026-09-23. Branch `clay-cli-tested-playbooks` adds "19 Clay CLI playbooks, tested live" in a commit dated 2026-09-23 15:58 UTC. The commit is co-authored by Claude Opus 5.5 and carries a Claude Code session link. It was pushed the same day as the keynote and the Clay livestream, and **it is not merged to `main` yet** |
| Stack assumed | Smartlead or Instantly (sending), Zapmail + Dynadot (inboxes and domains), Prospeo, Blitz, GetLeads, MillionVerifier, RapidAPI, Apify, OpenRouter/OpenAI, Clay CLI (`@claypi/cli`) |
| Stated cost | Month 1 is about $360, then about $130/mo recurring, for 2,000 leads, 20 domains and 40 inboxes (README) |

### Top level
- `README.md`: the index of tracks, required API keys, recommended paths, costs and an ethics note.
- `docs/roadmap.md`: a table of "which skill do I use when", plus the ideal linear flow.
- `presentation.html`: a short pitch deck titled "Cold Outbound Skills — Presentation" (problem, what's connected, flow, getting started).
- `LICENSE` (MIT) and `.env.example`.
- `Common Outbound Lists/`: a US zip-code CSV, a list of US software/SaaS companies, and a **"Google Maps Scrape - 12M US Businesses"** dataset in 13 zip files. See Risks.

### Track 1: Strategy
- `cold-email-kickoff`: the "start here" orchestrator. Runs ICP → lead magnet → strategy → `campaign-plan.md`, then hands off to the next skill.
- `icp-onboarding`: scrapes the website, runs a conversational intake, and writes `client-profile.yaml`.
- `lead-magnet-brainstorm`: a 4-question intake, 10 offer archetypes (A–J), and a 4-criterion /20 rubric.
- `campaign-strategy`: generates 15–25 campaign ideas on two axes, list (broad/focused/niche) × message. Also covers no-AI campaigns and "front-end offers" for cold traffic.
- `campaign-copywriting`: writes copy stepwise (direction → subject → body → final YAML).

### Track 2: Infrastructure
- `zapmail-domain-setup-public`: buys domains on Dynadot and provisions inboxes on Zapmail.
- `smartlead-inbox-manager`: sets warmup and signatures, and tags inboxes active / insurance / retired. Includes the 1% retirement rule.
- `email-deliverability-audit`: checks SPF/DKIM/DMARC, inbox health, the 1% rule and spam placement.
- `deliverability-incident-response`: a triage tree for spam, bounces, blacklists and warmup blocks.

### Track 3: List building
- `list-builder`: the meta skill. Multi-source lanes, a GPT-5-nano ICP judge with REJECT_AUDIT rescue, a snowball loop that runs "until dry", and an uncapped contact pull.
- `list-expander`: turns 10 seed companies into a qualified total addressable market (fingerprint → lookalikes → mined filters → pull → AI qualify → live-site verify).
- `prospeo-full-export` and `prospeo-search-api`: a title-first lead export and the filter reference.
- `blitz-list-builder`: finds contacts from a domain list.
- `google-maps-list-builder`: builds local SMB lists from Google Maps.
- `disco-like`: discovers lookalike companies.
- `competitor-engagers`: collects commenters and reactors on competitors' LinkedIn posts through RapidAPI. This is LinkedIn scraping.
- `icp-prompt-builder`: a required qualification-prompt tuning step, run in 10-company rounds until 2 rounds come back clean.
- `list-quality-scorecard`: grades a lead CSV A+ to F on 8 dimensions before sending.

### Track 4: Copy & send
- `cold-email-starter-kit`: a 14-chapter tutorial (references 00–14) plus scripts for Smartlead, Instantly, Dynadot, Zapmail and enrichment.
- `spam-word-checker` and `smartlead-spintax`: copy QA and spin variations.
- `smartlead-api`: the Smartlead API reference.
- `smartlead-campaign-upload-public`: uploads campaigns as DRAFT only. A human presses Start.

### Track 5: Iterate & automate
- `positive-reply-scoring`: classifies replies into 11 labels and reports positive replies ÷ total sent as the north star.
- `experiment-design`: single-variable experiments (list-only, copy-only, combined) with confidence weighting.
- `auto-research-public`: an 8-phase autonomous launcher (scrape → ICP → leads → personalize → upload).
- `personalization-subagent-pattern`: an approval loop that fans work out to Task sub-agents.
- `deliverability-test-public`: compares reply and bounce rates by inbox type.
- `cold-email-weekly-rhythm`: a Mon/Wed/Fri, biweekly, monthly and quarterly operating calendar.

### Track 6: Signal playbooks
Location: `skills/playbooks/`, tested versions in `skills/clay-cli-playbooks/`. Each playbook turns one signal into one copy-ready field.
- **Person signals:** new-in-role, linkedin-engagement, social-posts, warm-intros.
- **Company signals:** fundraising, hiring-surge, job-posting-language, ad-library.
- **Website signals:** pricing-page, case-study-page, tech-on-website, google-site-search.
- **List shaping:** company-name-cleaning, first-name-cleaning, social-link-finding, lookalikes, name-to-other-prospects.
- **Copy:** ai-specificity, creative-ideas.
- `clay-playbooks/SKILL.md` is the index. It holds the 7 rules that apply to all 19 playbooks and the two build harnesses (`clay-table-harness.md` for the browser, `clay-cli-harness.md` for the CLI).
- On the tested branch, the status table for the 19 CLI skills shows 14 PASS (one starred: warm-intros, whose heavier searches timed out) and 5 PARTIAL. The index prose says 13 end-to-end and 6 PARTIAL, so Eric's own docs disagree slightly. All 19 pass Clay's marketplace validator (`sungwanjo-clay/clay-skill-creator`) with 0 findings.

---

## 2. Content-grade facts (for the GTM World Tour post)

**Read this first:** several keynote items **do not appear anywhere in the repo**, on either branch:
- the "six things" offer taxonomy
- the 5-point cold-offer rubric (make money / new mechanism / insight-audit / hyper-research / case study)
- Grok Bot
- TestParty audits, Reddit audits and GTM hubs
- "domains killed/replaced weekly"

I grepped for all of them. Do not cite the repo as the source for those; they have to come from the talk transcript. The repo holds earlier or adjacent versions of the same ideas, listed below.

1. **The agents were tested live against Clay on keynote day, and Claude co-authored the commit.**
   - `skills/clay-cli-playbooks/README.md` (branch `clay-cli-tested-playbooks`): "tested live in a real Clay workspace on 2026-09-23 (CLI 1.3.0". The commit is co-authored by Claude Opus 5.5.
   - The division of labour, from the same file: "Clay supplies the facts; your agent does the judgment."
   - *Why it matters:* this is the concrete "Agentic GTM with Clay" artifact behind the livestream. The data vendor supplies facts, a Claude Code agent writes the copy, and there's one human approval gate after a 10-row batch.

2. **"Engineer a cold-traffic offer" is written down as a step.**
   - `skills/campaign-strategy/SKILL.md` §3 "Front-End Offer Suggestions": "softer front-end offers that could convert cold traffic before pitching the main service."
   - `skills/lead-magnet-brainstorm/SKILL.md`: "Cold emails with a concrete free offer outperform 'book a call' asks by 3-10x."
   - The crux question, from the same skill: "What could you do for a prospect in under 30 minutes that they'd pay $100 for?"
   - The repo's rubric is **4 criteria out of 20**: cheap to deliver, genuinely valuable, demonstrates competence, unique vs competitors. Proposals need ≥15/20. This is an earlier form than the keynote's 5-point rubric. The value-prop base in `campaign-strategy` is 4 categories: make more money / save time / save money / mitigate risk.
   - The archetypes that overlap the keynote are A "free audit / diagnostic", B "data/research piece", G "specific-to-them analysis" and J "benchmark". These are the generic forms of the TestParty-audit and Reddit-audit examples.

3. **A hard anti-hallucination rule for AI personalization.**
   - `skills/playbooks/clay-playbooks/SKILL.md` rule 3: "The model never establishes a fact."
   - Rule 2: "Abstain is empty string. Never 'N/A', never 'unknown', never a guess."
   - The rationale given: "a confident wrong sentence about someone's own job costs you the account."
   - Rule 7 bans em dashes in generated copy because they "read as machine-written."

4. **Deliverability is run as a fleet with a scheduled rotation, but it's biweekly, not weekly.**
   - `skills/cold-email-weekly-rhythm/SKILL.md` puts "Cold email: Inbox rotation" on "Every other Monday". Failing inboxes are tagged `retired`, and warmed "insurance" inboxes are promoted in their place.
   - `skills/smartlead-inbox-manager/SKILL.md`: "A healthy inbox should have an overall reply rate of ≥1% after sending 200+ emails."
   - The Monday audit pauses a campaign if bounces go above 2%. The monthly spam-placement target is ≥85% inbox.
   - When the insurance pool drops below 5 inboxes, start buying new domains. Warmup takes about 2 weeks.

5. **The north star is positive replies, not replies.**
   - `skills/positive-reply-scoring/SKILL.md`: "positive_reply_rate = positive_replies / total_sent".
   - Worked example: 1% reply at 70% positive (0.7% positive reply rate) beats 5% reply at 10% positive (0.5%).
   - In the Wednesday sweep, you answer positive replies within 30 seconds: "a reply feeling like it took minutes to return converts 3× better". This ties directly to Clay's speed-to-lead theme.

6. **Personalization runs as a Claude Code sub-agent loop, not paid API calls.**
   - `skills/personalization-subagent-pattern/SKILL.md`: "ALWAYS uses Claude Code Task tool sub-agents — never an external Anthropic/OpenAI API key."
   - The prompt locks after "2 consecutive rounds have zero edits", then the work fans out to 3–10 parallel sub-agents.

A detail for depth (optional): `clay-cli-playbooks/job-posting-language/SKILL.md` shows that matching on title + summary found **1 of 8** companies, against **5 of 8** when matching the full job description. `cold call` matched 996 postings where `cold calling` matched 2,065.

---

## 3. Harvest log (ranked by value to Alex)

| # | Name | What it is | Source | Class · target | Effort | Risk / cost |
|---|---|---|---|---|---|---|
| 1 | **Fact-before-prose + abstain-empty** | The model only turns facts that a structured source has already proven into prose. It never establishes a fact. If there's no proven fact, the field is left **empty** rather than filled with a hedge. Dates, counts and enums are computed in code. | `skills/playbooks/clay-playbooks/SKILL.md` rules 2–4 | **USE NOW** · `.claude/references/outreach-templates.md` (connection notes) + `pre-event-content` + `cold-email-specialist` agent. Add an explicit rule: each A/B variant must cite the signal row it was built from; if there's no cited signal, the variant field is empty and nothing ships. This formalizes the existing "never ship Level 2 filler" fallback and Key Pattern #12. | S | None |
| 2 | **Full-description phrase gate + enumerated token forms** | Match job postings on whole phrases in the **full** description, never on title/summary. List every inflection (call/calls/calling), otherwise about a third of matches are lost. Gate by role family too. Only cite a posting you can link and date, and that is still live. | `skills/clay-cli-playbooks/job-posting-language/SKILL.md` (tested branch) | **USE NOW** · `.claude/skills/role-radar/SKILL.md` Step 3 (it already scores "by mechanism, not title"). Add: (a) an enumerated-inflection list for mechanism phrases like "book of business", "expansion", "PLG"; (b) a required `posting_url` + `posted_date` + liveness check before any role is scored ≥ threshold. This fits the ATS-board curl path that's already primary. | S | None; public ATS APIs |
| 3 | **Positive-reply taxonomy as the outcome metric** | 11-label reply classification. The north star is positive replies ÷ sent. Out-of-office and bounces are excluded from the denominator, and hostile replies are tracked as a risk signal. | `skills/positive-reply-scoring/SKILL.md` | **USE NOW** · `tag-outcome` skill + `.claude/references/value-action-registry.md`. For `connection`/`meeting` goals, grade connection-note and DM responses into `positive_interested / positive_soft / positive_referral / negative_* / no_response`, and record Outcome Value = positives ÷ sent **alongside its null baseline**, per the null-baseline rule (YED-212). | S | None |
| 4 | **Single-variable experiments + baseline-relative verdicts** | Change one variable per test. Wait 21 days. Winner is ≥2× baseline, loser is <50% of baseline, kill and log the reason. Review every quarter. | `skills/experiment-design/SKILL.md`, `skills/cold-email-weekly-rhythm/SKILL.md` (Friday) | **USE NOW** · `rigor-review` + `content-patterns/goal-tagging.md`. When the 3 post variants differ, tag *which single variable* differs (hook type / format / opener), so outcomes can be attributed. Use baseline-relative keep/iterate/kill thresholds instead of absolute numbers. | S | None |
| 5 | **Approval-loop tuning for fan-out** | Sample 1 → batch of 10 → edits → repeat. The prompt locks after 2 zero-edit rounds, then scales out to parallel Task sub-agents. No API key needed. | `skills/personalization-subagent-pattern/SKILL.md` (also `icp-prompt-builder`) | **USE NOW** · `pre-event-content` connection-note generation for multi-speaker events, and the `role-radar` distillation subagents. Run the first 1 + 10 inline for Alex's edits, then fan out. It's also a cheap calibration pattern for the `/judge-build` rubric changes. It matches the "no metered key" position (YED-176). | S–M | Only Claude plan tokens |
| 6 | **Personal lead magnet / cold-traffic offer (the tabled idea)** | 10 offer archetypes (audit, data/research piece, competitive intel, template, intro, quick-win, specific-to-them analysis, tool, working session, benchmark). A /20 rubric: cheap / valuable / shows competence / unique. Plus "under 30 min, worth $100". Never gate it behind a form. | `skills/lead-magnet-brainstorm/SKILL.md`, `skills/campaign-strategy/SKILL.md` §3 | **REVISIT** · trigger: Alex un-tables the hiring-manager lead-magnet idea (should be filed to Linear with the `parked` label per the container rule). Use this rubric plus the keynote's 5-point version as the evaluation frame. Most relevant archetypes: B (research piece, from the event corpus), G (specific-to-them analysis, from the interview-prep dossier) and J (benchmark). Don't design it yet. | M | None |
| 7 | **"Free before paid, one 10-row gate showing cost"** | Every paid step is named by its exact action and priced from the live catalogue. A single approval shows the output, the cost and any writes for a 10-row batch. Nothing is written to the CRM. | `skills/clay-cli-playbooks/README.md` (tested branch) | **USE NOW** · the credit gates in `scan-voices` and `role-radar` (Apollo/Clay). Replace the generic "confirm spend" wording with "run 10 rows free, show the priced paid step and the rows it would touch, then ask." This keeps them Tier 3. | S | Clay/Apollo credits: gated, not recommended to spend |
| 8 | **Warm-intro alumni logic** | Search people who formerly worked at X. Drop advisor/board/fellow/intern roles (4 of 10 rows in the test). Enrich to confirm current employer (the search row has 0 of 10), then apply the ICP to the current role. | `skills/clay-cli-playbooks/warm-intros/SKILL.md` | **REVISIT** · trigger: the next `/interview-prep` where a warm path into the target company is needed. Find Meltwater / Bazaarvoice / Cohley alumni now at the target company, and apply the non-employment-title exclusion to People DB / HubSpot records. | M | The Clay free person-enrichment is 0 credits per the README. The search itself may meter; Tier 3 |
| 9 | **Hiring-surge with internal-move correction** | Measures department growth, but "5 of the 7 recent sales starters were internal moves", so raw "new hire" counts overstate growth. | `skills/playbooks/playbook-hiring-surge/SKILL.md` | **REVISIT** · trigger: the role-radar → MI graph producer work (YED-149, v1.1). Add a company-level "commercial team growing" signal to target-company scoring, with the internal-move correction. | M | May need paid people data |
| 10 | **REJECT_AUDIT on a cheap judge** | A cheap judge (GPT-5-nano) qualifies companies. Rejected rows are re-audited, and >15% disagreement triggers an automatic rescue. | `skills/list-builder/SKILL.md`, `RUNBOOK.md` | **REVISIT** · trigger: the next `/judge-build` rubric revision (`build-quality@5` per-seat recall). Audit a sample of the *rejects*, not just the passes. This is the recall half that the null-baseline finding said was missing. | S | None |
| 11 | **Em-dash conflict** | Eric bans em dashes in generated copy because they "read as machine-written". Alex's `content-quality/cold-email-personalization/assets/email-structure.md` says "**Use em dashes**". | `clay-playbooks/SKILL.md` rule 7 | **REVISIT** · trigger: the next `update-voice-and-style` pass. Decide on one rule and apply it everywhere. It's a small inconsistency, not urgent. | S | None |
| 12 | **Calendar-as-accountability ops rhythm** | Fixed Mon/Wed/Fri/biweekly/monthly/quarterly slots. There is deliberately no built-in reminder: "if it did and it broke, your ops would silently fail." | `skills/cold-email-weekly-rhythm/SKILL.md` | **SKIP** · Alex already runs `/rigor-review` weekly plus SessionStart Linear pulls. Only the philosophy is worth noting in a post. | — | None |
| 13 | **Clay CLI (`@claypi/cli`) + Clay marketplace skill validator** | Workflows can be created, published and test-run from the terminal. The CLI's tables commands are read-only. `clay-skill-creator` validates skill folders for Clay's marketplace. | `skills/clay-cli-playbooks/README.md`, `clay-playbooks/SKILL.md` | **REVISIT** · trigger: Clay credits approved for an enrichment use case, or Alex decides to publish a skill publicly (build-in-public). | M | Clay credits; Tier 3 |
| 14 | **LinkedIn engagement / social-posts / competitor-engagers** | Pulls reactors and commenters on LinkedIn posts through RapidAPI or Apify actors. | `skills/competitor-engagers/SKILL.md`, `clay-cli-playbooks/linkedin-engagement`, `social-posts` | **SKIP** · this **conflicts with Alex's "No LinkedIn scraping" rule** (role-radar / scan-voices ground rules) and likely LinkedIn's ToS. Flagged only; do not adopt. | — | ToS |
| 15 | **Sending infra + bundled lists** | Dynadot/Zapmail domain and inbox fleet, Smartlead upload, auto-research launcher, and the 12M-business Google Maps scrape. | Track 2, `auto-research-public`, `Common Outbound Lists/` | **SKIP** · Alex isn't running volume cold email. The scraped dataset has unclear provenance and Google ToS exposure. | — | ToS / cost (~$360 first month) |

---

## Risks and caveats
- **Keynote ≠ repo.** The six-things taxonomy, 5-point rubric, Grok Bot, TestParty/Reddit audits, GTM hubs and weekly domain kills are all absent. Attribute them to the talk (the transcript is in `Event Content/09 24 26 GTM World Tour · New York/`), not to the repo.
- **The tested branch is unmerged.** Cite it as the branch `clay-cli-tested-playbooks`, or link the commit, so the link doesn't 404 against `main`. The Clay *table* recipes are self-declared as unverified specifications.
- **ToS:** LinkedIn-engagement and social-posts scraping (RapidAPI/Apify) and the bundled Google Maps scrape. Do not adopt.
- **Reuse:** MIT, so copying rule text or skill structure into Empire State is fine. Keep the MIT notice in any copied file; attribution is courtesy only.
