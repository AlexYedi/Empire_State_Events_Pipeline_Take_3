# Research Brief — AI Show and Tell: New York

**Mon 2026-09-21 · 6:00–9:00pm · Microsoft Research Lab, 300 Lafayette St** · Global AI New York · 226 registered, waitlist only
Produced 2026-09-20. Prior context supplied by the substrate pack (A/B event 1, YED-172 — substrate arm preferred).

---

## THE ONE THING

**This is not a community meetup with Microsoft as a venue sponsor. It is a Microsoft Foundry roadmap night, convened by the man who founded the community, staffed entirely by Microsoft employees, with a grassroots hosting layer on top.**

Four of the four speakers are Microsoft employees presenting their own team's work. Henk Boelman — the 7:00 speaker — **founded the Global AI Community itself**. Sebastian Kowalik, listed as a host, is a Microsoft Technical Specialist and the NYC chapter's co-organizer. The org is a Dutch nonprofit (Stichting Global AI Community) that runs on Microsoft-provided Meetup Pro accounts, Azure passes, and venue support, and co-develops workshop content with Microsoft product teams.

That is not a criticism — it's the accurate frame, and it changes three things: who to prioritize (the chapter organizers, for recurring access, not just the speakers), how to read the claims (product-team claims about their own products), and what the recap's honest angle is (see Documentarian Angle).

---

## ROOM PLAN — who, in what order

| Priority | Person | Why | The play |
|---|---|---|---|
| **1** | **Mehrnoosh Sameki** (8:00) — Principal PM Manager, Azure AI Foundry | Leads GenAI/Agents Evaluation Science, AI Governance, Redteaming + Safety Eval. Co-founded Fairlearn, Error Analysis, Responsible AI Toolbox. Her subject is the exact topic where you have the most running thread and the least prior context. | Informed-outsider question, not an echo. She is the PM lead, not an evangelist restating someone else's work. |
| **2** | **Henk Boelman** (7:00) — Principal Developer Advocate, Microsoft; **founder, Global AI Community** | A relationship here compounds across every future chapter event globally, not just tonight. Also the only in-production multi-agent case study in the room. | Name the founding explicitly — most attendees will treat him as "a speaker." Then the parallel-vs-sequential question below. |
| **3** | **Sebastian Kowalik** — Microsoft Technical Specialist (Jersey City); **co-organizer, Global AI New York** | The standing door to the NYC chapter's recurring calendar. Repeat access, not a single conversation. | Ask who curates future lineups / how an attendee demo slot gets pitched. His own work is production MCP + A2A at enterprise and government scale — a real conversation, not small talk. |
| **4** | **Jay Gordon** (7:30) — Senior PM, Azure Cosmos DB, **Brooklyn-based** | Numbers-backed "what happens after the demo" case study. NYC-local. Prior stops: MongoDB, DigitalOcean, BuzzFeed. | His own published thesis is the opener: *"vibe coding doesn't replace engineering; it accelerates the path to understanding."* Ask what that means concretely for validating AI-generated code before it ships. |
| **5** | **Cedric Vidal** (7:30) — Principal Cloud Advocate / Agentic AI Evaluation Engineering lead (SF) | Background is ~4 yrs running AI data labeling for self-driving at Argo AI, then CTO at a fintech AI startup — a genuine evaluation-at-scale pedigree. | Ask about SCOPE as a *general methodology*, not the Cosmos DB details (Gordon owns those). Is it going Microsoft-wide? Is it headed for open-source like ASSERT/ACS? |
| **?** | **Stephen Simon** — Program Manager, Global AI Community (global, not NY chapter); Microsoft MVP | **Presence at this event is UNCONFIRMED.** Not on the event agenda; not on the NY chapter organizer list. Runs "Azure for Sure" / "A Dash of .NET" and HackIndia (30+ hackathons). | Don't prep a hook. If he's there, open by asking what brings him to the NY chapter. Disambiguating anchor is the handle `codewithsimon` — at least three unrelated same-named public figures exist. |

---

## THE AGENDA, AND WHAT'S ACTUALLY BEING SHOWN

**7:00 — "Your New Teammates: Architecting a Multi-Agent Workforce"** (Boelman)
hamba.nl — a live Dutch travel magazine, built with the GitHub Copilot App, run end-to-end by **seven Foundry-hosted agents** across the editorial pipeline (draft → moderate → fact-check → publish), orchestrated by Microsoft Agent Framework, tools reached over MCP, **human-in-the-loop retains final publish approval**.

**7:30 — title differs between sources.** The calendar says *"From Findings to Fixes: How SCOPE and Azure Cosmos DB Improved AI-Generated Apps."* The event's own registration page says *"Your Product Was Built for Humans. Is It Ready for Agents?"* Same speakers, same content, updated abstract. Use the registration-page title if you name it publicly.
The substance: SCOPE + the Cosmos DB team tested **8 AI-generated apps across 6 tech stacks over ~3 months**, producing **33 Agent Kit rule changes (4 of them new) and 51 issues resolved across 45 documentation pages.** The Cosmos DB **Agent Kit** — a public ruleset that teaches coding agents to use Cosmos DB correctly — shipped Jan 2026 with 45 rules and now carries 120+ rules across 12 categories after 200+ automated test iterations.

**8:00 — "From Intent to Enforcement: Open-Source Evaluation and Governance for AI Agents"** (Sameki)
Introduces **ASSERT** and **ACS** together. ASSERT (`github.com/responsibleai/ASSERT`) converts natural-language expectations about what an agent should and shouldn't do into executable evals. **ACS — Agent Control Specification** is an open, framework-neutral, stateless, fail-closed runtime governance contract: policy files travel with the agent and intercept at four points (before input / before tool call / after tool return / before final response), triggering allow / block / redact / human-escalate. Both announced 2026-06-02 (TechCrunch covered ACS the same day).

---

## ⚠️ FACT DISCIPLINE — read before you speak

**SCOPE: do not expand the acronym.** Three research passes produced three different answers. The primary source settles it: `github.com/microsoft/scope` is *"an open-source agentic experience evaluation platform,"* Microsoft-maintained, **Research preview**, and **gives no acronym expansion anywhere.** A proposed expansion ("Staged Code Oversight with Proportional Escalation") appeared in one research pass and **could not be sourced** — treat it as false until Vidal says otherwise. Say "SCOPE" and ask him what it stands for. That question is itself a good opener.

**The Kilian Lieret quote is your own note, not a citation.** *"Single agents are usually fine; multi-agent gains are mostly illusory given million-token context"* — heard firsthand at the Agents Behaving Badly panel, 2026-06-25. No independent web confirmation exists that he said it. Attribute it as *"I heard this argued at a panel in June,"* never as a published claim. (Rule 12.)

**Don't restate the stale Microsoft numbers.** The "$37B AI run-rate / +123% YoY" figure on file is from May 2026 and could not be refreshed — drop it. Current and sourced: **FY26 Q4 Azure revenue +43% YoY, full-year Azure revenue crossed $100B for the first time**; CY2026 capex guided ~$175B (revised down from $190B on a finance→operating lease shift) while **FY2027 capex guidance jumped to $255–260B**.

**"AI Agent Factory" is dead language.** Microsoft's current framing is "Frontier Firm" (2026 Work Trend Index, May 2026). Don't use the old phrase as if it were theirs.

**Foundry Control Plane already went GA in March 2026** — it was carried as "preview" in prior context. Evaluations, tracing, monitoring, plus a consolidated ARM API.

**Unverified, flagged:** Global AI Community's "170,000 members / 190 chapters" (single secondary source). Microsoft Agent Framework's GA status — introduced at Build 2026 as public preview, no GA announcement found; treat as still-preview.

---

## THE THREE QUESTIONS

Ranked by how hard they are to answer generically. Each is grounded in something published and dated.

**1. For Boelman — the parallel-vs-sequential test.**
> "The failure data on multi-agent systems is getting sharper — MAST's analysis of 1,600+ production traces puts about 37% of failures in inter-agent coordination, ahead of any single agent's reasoning error, and the pattern emerging is that decomposition helps on parallelizable work and hurts on sequential work. Across your seven agents, which ones actually run in parallel versus a strict handoff chain — and is coordination where hamba.nl's failures actually cluster?"

Why it lands: it takes his architecture seriously instead of treating agent-count as sophistication. The MIT result (Ao, Gao, Simchi-Levi, ~Mar 2026) is the sharper version if you want it — without genuinely new information entering the system, adding agents provably can't beat one well-designed agent. The gentler framing of the same test: *which of the seven roles is load-bearing versus decorative?*

**2. For Sameki — where the two halves disagree.**
> "ASSERT turns written intent into executable evals and ACS enforces at runtime. When they disagree in production — an eval says the agent is compliant but an ACS interception point blocks the action anyway — which one wins, and what's the reconciliation protocol?"

Follow-ups worth holding: Is ACS actually adopted outside the Microsoft stack — LangChain, CrewAI — or Microsoft-only in practice? Is ACS designed *against* Gartner's binary-trust failure pattern (Shiva Varma, Sept 9 2026: enterprises treat agent governance as either locked-down or fully trusted, and that binary is the root cause of incidents), or convergent by accident? And the forensic gap Gartner names — agents lacking their own principal identity in access logs, and long-running sessions discarding the reasoning trail during context compression — does Foundry's durable per-agent identity actually close that, or relocate it?

**3. For Gordon / Vidal — where the human sits.**
> "SCOPE's own docs warn its automated Judge makes mistakes and needs human review. In the Cosmos DB run, where did the human actually sit in the loop, and how often did the human overrule the Judge?"

Second: OpenAI's Deployment Simulation (Jun 16 2026) found models flag synthetic eval prompts as tests ~100% of the time but real production traffic only 5.4% — does SCOPE replay real traces, or still run constructed scenarios?

---

## WHAT YOU KNOW THAT THE ROOM PROBABLY DOESN'T

- **The eval/observability layer has been consolidated out from under everyone: 8 acquisitions in 14 months.** W&B→CoreWeave, Velvet→Arize, **Humanloop→Anthropic**, **Statsig→OpenAI ($1.1B)**, Langfuse→ClickHouse, **Promptfoo→OpenAI**, Helicone→Mintlify, **Galileo→Cisco** (closed May 2026, folding into Splunk). Only Braintrust and Arize remain independent. **This is the unstated subtext of Sameki's talk**: two frontier labs now literally own eval companies, which is precisely why Microsoft is positioning ASSERT/ACS as open and framework-agnostic. Naming that out loud is the sharpest thing you can say tonight.
- **Three institutions landed on the same governance model within ~90 days** — Microsoft's product answer (per-agent durable identity, policy-travels-with-the-agent), Gartner's diagnosis (graduated autonomy: observe → advise → act-with-approval → act-autonomously-within-guardrails), and the EU AI Act's legal answer (Recitals 99–100: the compliance boundary extends to *every* agent performing a high-risk function in a chain, not just the front door). Vendor, analyst, and regulator converging independently is a real, citable pattern.
- **The EU AI Act date is widely misstated.** The AI Office's supervisory and enforcement powers did go live 2026-08-02 as scheduled — but the Digital AI Omnibus (Regulation 2026/1744) **deferred the substantive high-risk obligations to Dec 2 2027 (Annex III) and Aug 2 2028 (Annex I).** If someone asserts high-risk rules are already binding, that's the deferred timeline. Correct it quietly, one-on-one — not from the floor.
- **SWE-bench Verified is retired as a frontier discriminator,** not merely saturating: the top three models cluster within one point (96% / 95.5% / 95%) as of Sept 18 2026, and its own co-creators say it no longer measures frontier coding capability. SWE-bench Pro is the successor.
- **Judge reliability got a sharper frame in June:** *"Reliability without Validity"* (arXiv 2606.19544) — judges can be internally consistent while still not measuring the right construct. That's a better phrasing than "calibrated distrust" for the same instinct.

**Handle with care: CosmosEscape.** Wiz disclosed a CVSS 10.0 flaw chain in Azure Cosmos DB's Gremlin API (CVE-2026-66803) publicly on 2026-07-30 — a platform-wide master key permitting cross-tenant retrieval of any Cosmos DB account's primary key. Reported privately Nov 2025, hotfixed in two days, architectural fix complete; Microsoft states no customer data was accessed. **Judgment call, and my recommendation is: don't raise this from the floor at a Microsoft-hosted community night.** Gordon is a community-facing PM, not the security org, and a CVSS 10.0 gotcha in a room of 226 reads as point-scoring. If it comes up organically, the good-faith version is about threat models, not blame: *does SCOPE's escalation logic distinguish platform-layer risk from app-layer AI-generated defects, or do those get conflated?*

---

## DOCUMENTARIAN ANGLE

The continuity thread you've been building across three months of rooms — *verification is the bottleneck* — has been running almost entirely through independent builders: Agents Behaving Badly (Jun 25), Daytona AI Builders (Sept 9). Your Microsoft exposure ran on a separate track: Fabric and Azure App Platform tech briefs in April, Ray Dev Day in May, all product-surface, none agent-evaluation.

**Tonight is the first room that is both at once.** That's the post: *the verification-is-the-bottleneck thread finally lands inside the vendor's own stack* — and the honest question is whether Microsoft's answer (ASSERT, ACS, SCOPE, Foundry Control Plane) operationalizes what the independent builders already converged on — state-level verification over trace inspection, don't let the writer grade its own work, keep a human as the final line, keep eval scenarios model-agnostic — or diverges from it.

Two complications worth writing into the recap rather than smoothing over:
1. **The governance tooling is fragmented across at least three separately-branded Microsoft projects** shipped inside one year — Foundry Control Plane (Mar), Agent Governance Toolkit (Apr), ASSERT + ACS (Jun). A prospective adopter has a real "which one do I actually use" problem. That's a fair, non-hostile question and a genuinely useful observation for a recap.
2. **The room's headline talk is a seven-agent production system, and the 2026 academic current is running against multi-agent architectures** — three independent results (MIT's information-theoretic proof, Tran & Kiela's compute-normalized benchmark showing single agents match or beat multi-agent under equal thinking-token budgets, and a 150-task survey cataloguing 14 distinct failure modes). Not a refutation of hamba.nl specifically. But the tension between what vendors are shipping and what the literature is finding is the most interesting thing in the room, and nobody on stage is incentivized to name it.

Cross-reference candidates for the recap's learn-more set: your Agents Behaving Badly write-up (Jun 25) and the Daytona AI Builders piece (Sept 9) — this post is chapter three of the same thread.

---

## EVIDENCE SET

Dates are publication dates. Every claim used above traces to one of these.

**Microsoft product**
- Foundry Agent Service GA — techcommunity.microsoft.com/blog/azure-ai-foundry-blog/announcing-general-availability-of-azure-ai-foundry-agent-service/4414352 — 2026-03-16
- Bring Your Own Model GA — techcommunity.microsoft.com/blog/azure-ai-foundry-blog/bring-your-own-model-to-foundry-agent-service-is-now-generally-available/4515133 — 2026-04-28
- Microsoft Agent Framework (AutoGen + Semantic Kernel), public preview — azure.microsoft.com/en-us/blog/introducing-microsoft-agent-framework/ — 2026-05/06
- Foundry Control Plane GA (evals, tracing, monitoring) — aguidetocloud.com/blog/microsoft-build-2026-recap/ — 2026-03
- Agent Governance Toolkit, MIT license, claims full OWASP agentic Top 10 coverage — opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/ — 2026-04-02
- ASSERT — github.com/responsibleai/ASSERT + commandline.microsoft.com/assert-written-intent-executable-evals/ — 2026-06-02
- ACS (Agent Control Specification) — commandline.microsoft.com/agent-control-specification-runtime-governance/ · techcrunch.com/2026/06/02/microsoft-offers-devs-a-better-way-to-control-ai-agent-behavior/ — 2026-06-02
- SCOPE — github.com/microsoft/scope — research preview, **no acronym expansion published**
- Cosmos DB Agent Kit GA (45→120+ rules, 200+ test iterations) — devblogs.microsoft.com/cosmosdb/azure-cosmos-db-agent-kit-now-battle-tested-for-ga/ — 2026-09
- "Frontier Firm" framing supersedes "AI Agent Factory" — blogs.microsoft.com/blog/2026/05/05/how-frontier-firms-are-rebuilding-the-operating-model-for-the-age-of-ai/ — 2026-05-05
- FY26 Q4: Azure +43% YoY, full-year Azure >$100B; CY26 capex ~$175B, FY27 guide $255–260B — microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast · valueaddvc.com/pulse/microsoft-azure-100-billion-fy27-capex-2026 — 2026-07
- CosmosEscape CVE-2026-66803, CVSS 10.0 — wiz.io/blog/cosmosescape-taking-over-every-database-in-azure-cosmos-db · infoq.com/news/2026/08/cosmosescape-master-key/ — 2026-07-30

**Event + people**
- Event page (agenda, abstracts, the 8-apps/6-stacks/33-rules/51-issues numbers) — globalai.community/e/783bfa20 — accessed 2026-09-20
- Global AI Community = Stichting Global AI Community (NL nonprofit, KVK 96447265); Microsoft-provided Meetup Pro, Azure passes, venue support — globalai.community/about/
- NY chapter organizers = Kowalik + Boelman — globalai.community/chapters/new-york/
- Boelman: Principal Developer Advocate; founder, Global AI Community — henkboelman.com · developer.microsoft.com/en-us/advocates/henk-boelman
- Sameki: Principal PM Manager, Azure AI Foundry; co-founded Fairlearn / Error Analysis / Responsible AI Toolbox — commandline.microsoft.com (2026-06-02) · infoq.com/profile/Mehrnoosh-Sameki/
- Gordon: Senior PM Azure Cosmos DB, Brooklyn; prior MongoDB/DigitalOcean/BuzzFeed; "vibe coding doesn't replace engineering" — devblogs.microsoft.com/cosmosdb/everyone-is-talkin-bout-vibes/
- Vidal: Agentic AI Evaluation Engineering lead / Principal Cloud Advocate; prior Argo AI (AI data labeling, self-driving), CTO Quicksign — github.com/cedricvidal · developer.microsoft.com/en-us/advocates/cedric-vidal
- Kowalik: Microsoft Technical Specialist, Jersey City; MCP + A2A at enterprise/government scale; NY chapter co-organizer — sebastiankowalik.com
- Simon: Program Manager, Global AI Community (global); MVP; HackIndia — in.linkedin.com/in/codewithsimon · codewithsimon.dev — **tie to this event unconfirmed**

**Research + market**
- MAST: ~36.94% of failures in 1,600+ production traces = inter-agent coordination — arxiv.org/pdf/2607.05775 — 2026-07
- Single vs multi-agent under equal thinking-token budgets (Tran & Kiela) — arxiv.org/html/2604.02460v1 — 2026-04
- Paired noise-floor protocol for multi-agent benchmark gains — arxiv.org/pdf/2606.20695 — 2026-06
- MIT (Ao, Gao, Simchi-Levi): no new information → added agents can't beat one well-designed agent — secondary coverage only, ~2026-03, **verify before public use**
- "Reliability without Validity" (LLM-as-judge) — arxiv.org/pdf/2606.19544 — 2026-06
- RAND Judge Reliability Harness — arxiv.org/abs/2603.05399 — 2026-03
- OpenAI Deployment Simulation (synthetic flagged ~100% vs 5.4% real traffic; 120K coding trajectories, simulator realism 49.5%) — 2026-06-16
- SWE-bench Verified retired as frontier discriminator — news.ycombinator.com/item?id=47912620 — 2026-09-18
- A2A v1.0 → Agentic AI Foundation; AAIF <40 → 250+ members — axios.com/2026/08/17/a2a-agentic-ai-foundation-open-ai-standards — 2026-08-20
- Foundry A2A endpoints + MCP access to 1,400+ tools — techcommunity.microsoft.com/blog/azure-ai-foundry-blog/a2a-endpoints-and-a2a-tool-in-microsoft-foundry-agents/4557115 — 2026
- EU AI Act: enforcement powers live 2026-08-02; Digital AI Omnibus (Reg. 2026/1744) defers Annex III to 2027-12-02, Annex I to 2028-08-02; Recitals 99–100 per-agent compliance boundary — knowledge.dlapiper.com · datamatters.sidley.com
- OWASP Top 10 for Agentic Applications (ASI01–ASI10) — genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ — 2025-12-09
- Gartner (Shiva Varma): binary trust is the root cause; graduated autonomy prescribed; agent-identity forensic gap — hpcwire.com/aiwire/2026/09/09/autopsy-of-an-agent-incident-three-patterns-behind-gartners-40-failure-rate/ — 2026-09-09 — **medium confidence, direct fetch 403'd**
- Eval/observability acquisition cluster (8 in 14 months) — ai-evals.tools/editorial/llm-evals-observability-company-acquisitions
- Meta Muse + Sentinel approval agent, US launch — quasa.io/insights/meta-s-muse-can-book-and-buy-sentinel-decides-when-to-ask-you — 2026-09-08

**Explicit gaps**
- Stephen Simon's presence/role at this event — unresolved
- Microsoft Agent Framework GA status — no announcement found
- hamba.nl incident history — none reported publicly, which is silence, not proof of robustness
- Global AI Community membership/chapter counts — single secondary source
