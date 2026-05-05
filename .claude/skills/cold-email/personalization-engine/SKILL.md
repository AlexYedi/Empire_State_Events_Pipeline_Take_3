---
name: personalization-engine
description: "Turn raw prospect data into compelling personalized email elements. Signal detection, personalization layers, and variable frameworks that make cold emails feel warm."
---

# Personalization Engine

## When to Use
- Building personalization workflows for outbound campaigns
- Training SDRs or AI systems on what "good personalization" looks like
- Designing variable strategies for email templates
- Upgrading campaigns from generic to signal-based personalization

## Framework

### The Personalization Hierarchy

Not all personalization is equal. Higher levels convert better but take more effort. Match your level to your volume and deal size.

| Level | Type | Example | Effort | Impact |
|-------|------|---------|--------|--------|
| **5** | Behavioral Signal | "Saw you just posted about switching from HubSpot to Salesforce" | High | Highest |
| **4** | Business Event | "Congrats on the Series B — scaling outbound is usually next" | Medium-High | Very High |
| **3** | Company-Specific | "{{companyName}} is hiring 3 SDRs — building the outbound team?" | Medium | High |
| **2** | Role-Specific | "Most VPs of Sales at Series B companies deal with..." | Low-Medium | Medium |
| **1** | Industry-Specific | "SaaS companies in your space typically see..." | Low | Low-Medium |
| **0** | None (Spray & Pray) | "Hi {{firstName}}, I wanted to reach out..." | None | Lowest |

**Rule of thumb:**
- High-value accounts (>$50K ACV): Level 4-5 personalization
- Mid-market (10K-50K): Level 3-4
- SMB at scale (<10K): Level 2-3 with automation

---

### 6 Signal Categories

Every personalization starts with a signal — something you observed about the prospect or their company. Here are the six signal categories ranked by conversion impact:

#### 1. Hiring Signals (Highest Intent)
**What to look for:** Job postings that indicate a need your product solves.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| Hiring SDRs/BDRs | Building outbound team | "Scaling outbound? Here's how to ramp reps 2x faster" |
| Hiring first VP Sales | Moving from founder-led to scalable sales | "The founder-to-VP Sales transition is where pipeline breaks" |
| Hiring RevOps/SalesOps | Operationalizing the GTM motion | "Systematizing your sales process? Here's what top teams automate first" |
| Hiring Marketing roles | Investing in demand gen | "Most teams hire marketers before they have the infrastructure to support them" |

**Data sources:** LinkedIn Jobs, Indeed, company careers page, Otta, Wellfound

#### 2. Funding Signals
**What to look for:** Recent capital raises that trigger growth mode.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| Seed round | Building product-market fit | "Post-seed is when most founders realize inbound won't scale" |
| Series A | Scaling what works | "Series A = time to build the repeatable pipeline machine" |
| Series B+ | Aggressive growth targets | "Series B boards expect 3x. Here's how teams actually hit that" |
| PE acquisition | Efficiency and EBITDA focus | "Post-acquisition teams usually need to do more with less" |

**Data sources:** Crunchbase, PitchBook, TechCrunch, LinkedIn announcements

#### 3. Technology Signals
**What to look for:** Tech stack changes that indicate shifting priorities.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| New CRM adoption | Sales infrastructure investment | "Migrating CRMs usually means the old process broke" |
| Adding outreach tools | Building outbound capability | "Noticed you're using {{tool}} — most teams hit a wall at step 2" |
| Removing a competitor | Dissatisfaction with current solution | "Switching from {{competitor}}? Here's what teams wish they knew" |
| Adding analytics tools | Data-driven decision making | "Companies that add BI tools are usually 6 months from optimizing their funnel" |

**Data sources:** BuiltWith, Wappalyzer, SimilarTech, G2 reviews, job descriptions (tech requirements)

#### 4. Content Signals
**What to look for:** What the prospect is publishing, sharing, or engaging with.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| LinkedIn post on a pain point | Active problem awareness | "Your post about {{topic}} resonated — we see this across our clients" |
| Podcast appearance | Thought leadership, specific opinions | "Heard you on {{podcast}} — your point about {{topic}} was spot on" |
| Blog/article published | Strategic priorities | "Your article on {{topic}} aligns with what we've been seeing" |
| Conference speaking | Industry visibility | "Your talk at {{event}} — the framework you shared maps to what we do" |

**Data sources:** LinkedIn feed, podcast directories, company blog, event speaker lists

#### 5. Company Event Signals
**What to look for:** Organizational changes that create new needs.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| Product launch | New market/audience expansion | "New product = new ICP. Most teams underestimate the outbound lift needed" |
| Office expansion | Growth phase | "New markets usually mean new pipeline targets" |
| Leadership change | Strategic shift likely | "New leadership often means new priorities for the sales team" |
| M&A activity | Integration and growth mandates | "Post-merger teams usually need to consolidate and scale fast" |

#### 6. Performance Signals
**What to look for:** Publicly visible indicators of business performance.

| Signal | What It Means | Personalization Angle |
|--------|--------------|----------------------|
| G2/Capterra reviews declining | Customer satisfaction issues | Approach carefully — focus on solutions, not the problem |
| Glassdoor sales complaints | Sales team challenges | "High SDR turnover usually means the process needs fixing" |
| Website traffic changes | Growth or contraction | "Noticed {{companyName}} traffic is up 40% — is inbound keeping up?" |
| Award/recognition | Positive momentum | "Congrats on the {{award}} — companies at your stage usually..." |

---

### The Personalization Formula

Every personalized email element follows this 3-part structure:

```
[OBSERVATION] + [IMPLICATION] + [BRIDGE]
```

| Part | What It Does | Example |
|------|-------------|---------|
| **Observation** | What you noticed (the signal) | "Saw you're hiring 3 SDRs" |
| **Implication** | What that usually means | "Which usually means you're building a scalable outbound motion" |
| **Bridge** | How it connects to your value | "Most teams at that stage need X to avoid Y" |

**Bad personalization:** "Hi Sarah, I see you work at Acme Corp. We help companies like Acme..."
**Good personalization:** "Sarah — noticed Acme just posted 3 SDR roles in Austin. Scaling the outbound team usually means the founder-led selling phase worked, but the playbook isn't documented yet."

The difference: bad personalization names facts. Good personalization draws insights from facts.

---

### Variable Architecture

Design your email templates with a layered variable system:

#### Tier 1: Auto-Populated (No Manual Work)
These come straight from your lead list:

| Variable | Source | Example |
|----------|--------|---------|
| `{{firstName}}` | Lead data | Sarah |
| `{{companyName}}` | Lead data | Acme Corp |
| `{{title}}` | Lead data | VP of Sales |
| `{{industry}}` | Enrichment | B2B SaaS |
| `{{companySize}}` | Enrichment | 150 employees |
| `{{location}}` | Lead data | Austin, TX |

#### Tier 2: Enrichment-Derived (Automated Research)
These require data enrichment but can be automated:

| Variable | Source | Example |
|----------|--------|---------|
| `{{recentFunding}}` | Crunchbase/PitchBook | Series B, $25M |
| `{{techStack}}` | BuiltWith/Wappalyzer | Uses Salesforce, Outreach |
| `{{headcount_growth}}` | LinkedIn/data providers | +40% in 6 months |
| `{{openRoles}}` | Job boards | 3 SDRs, 1 AE |
| `{{competitorUsed}}` | Tech detection | Currently using ZoomInfo |

#### Tier 3: Research-Derived (Manual or AI-Assisted)
These require reading/analyzing content:

| Variable | Source | Example |
|----------|--------|---------|
| `{{linkedinInsight}}` | LinkedIn posts | "Your post about cold email being dead..." |
| `{{podcastQuote}}` | Podcast appearance | "On the Revenue Podcast you mentioned..." |
| `{{specificChallenge}}` | Content + inference | "Scaling past 10 reps without losing quality" |
| `{{customCampaignIdea}}` | AI analysis of company | "Target CFOs at PE-backed SaaS with the efficiency angle" |

---

### Personalization at Scale: The Bucket Strategy

For high-volume campaigns (1,000+ leads), you can't write individual emails. Instead, create personalization "buckets":

**Step 1: Segment your list by signal type**
```
List of 2,000 leads
├── Bucket A: Recently funded (400 leads)
├── Bucket B: Hiring sales roles (350 leads)
├── Bucket C: Tech stack change (250 leads)
├── Bucket D: Industry-specific pain (600 leads)
└── Bucket E: No strong signal (400 leads)
```

**Step 2: Write bucket-specific opening lines**
Each bucket gets its own personalized opener that feels individual but applies to the whole segment:

| Bucket | Opening Line |
|--------|-------------|
| Recently funded | "Post-{{fundingRound}} is when most {{industry}} companies realize outbound needs to be a machine, not a side project." |
| Hiring sales | "Hiring {{openRoles}} is usually the sign that founder-led sales worked — now you need the playbook to scale it." |
| Tech stack change | "Teams switching to {{newTool}} are usually 90 days into a bigger GTM overhaul." |
| Industry pain | "{{industry}} companies at your stage typically hit a wall at {{specificMilestone}}." |
| No signal | Use Archetype 6 (Whole Offer) from copy-frameworks — lead with your strongest proof point |

**Step 3: Layer in Tier 1 variables for the personal touch**

The result: every lead gets an email that feels researched, but you wrote 5 versions, not 2,000.

---

### Personalization Quality Scoring

Rate every personalized email element on this scale before sending:

| Score | Criteria | Example |
|-------|----------|---------|
| **5 — Exceptional** | References specific, timely signal + draws a non-obvious insight | "Your LinkedIn post last week about SDR burnout — we just published data showing teams with AI-assisted prospecting see 40% less rep turnover" |
| **4 — Strong** | References a real signal + connects to a relevant outcome | "Saw you raised a Series B — most teams at this stage need to 3x pipeline in 6 months" |
| **3 — Good** | References company-level data + makes a reasonable inference | "With 3 SDR roles open, it looks like you're building the outbound engine" |
| **2 — Adequate** | Role or industry-level personalization | "Most VPs of Sales at B2B SaaS companies face..." |
| **1 — Weak** | Name and company only | "Hi Sarah, I noticed Acme Corp..." |
| **0 — None** | No personalization | "Hi, I wanted to reach out about..." |

**Minimum threshold:** Score 3+ for mid-market, Score 4+ for enterprise.

## Templates

### Signal Research Template
```
For each lead, capture:

Company: {{companyName}}
Contact: {{firstName}} {{lastName}}, {{title}}

Signal Scan:
- [ ] Hiring signals: ___
- [ ] Funding signals: ___
- [ ] Tech signals: ___
- [ ] Content signals: ___
- [ ] Company events: ___
- [ ] Performance signals: ___

Strongest signal: ___
Personalization angle: ___
Opening line draft: ___
Quality score (1-5): ___
```

### Personalization Brief (For AI or SDR)
```
Client: {{clientName}}
Target Persona: {{persona}}
Campaign Angle: {{angle}}

Personalization Requirements:
- Minimum quality score: {{minScore}}
- Required signal types: {{signalTypes}}
- Variables available: {{variableList}}

Bucket Definitions:
- Bucket A ({{bucketName}}): {{criteria}} → {{openingApproach}}
- Bucket B ({{bucketName}}): {{criteria}} → {{openingApproach}}
- Bucket C ({{bucketName}}): {{criteria}} → {{openingApproach}}
```

## Tips
- The best personalization references something the prospect DID, not something they ARE. "I saw you posted about X" beats "I see you're a VP of Sales" every time.
- Don't over-personalize Step 1 if it comes at the cost of volume. A Level 3 email sent to 500 people beats a Level 5 email sent to 50 — unless your ACV justifies the time.
- Keep a running database of which signal types drive the highest positive reply rates. After 3 months, you'll know exactly which signals to prioritize.
- When in doubt, lead with the hiring signal. It's the most reliable indicator of active buying intent.
- AI can handle Tier 1-2 personalization at scale. Reserve human effort for Tier 3 (content-based insights) on your highest-value targets.
- Test "no personalization" as a control variant. Sometimes a strong offer with zero personalization beats weak personalization — and it tells you if your copy is doing the heavy lifting.

---

*Progressive disclosure: load signal-specific research playbooks and enrichment tool integrations only when building personalization for a specific campaign.*
