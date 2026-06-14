# Research Brief: Agents Behaving Badly — The Perils of Pushing AI Agents into Production

**Date:** Thursday, June 25, 2026, 6:00–8:00 PM ET
**Format:** In-person. Datadog HQ, NYT Building, 620 8th Ave, NYC.
**Host:** Arklex AI (+ 3 others, unnamed in invite)
**Venue host:** Datadog
**Speakers:** Kilian Lieret, PhD (AI Research Scientist, Meta Superintelligence) · Zhou (Jo) Yu (Co-Founder & CEO, Arklex AI)
**Luma:** https://luma.com/kkipue1p

---

## The 90-Second Frame

This is a **vendor-hosted technical meetup that doubles as a category-defining moment for agent evaluation** — and the lineup is unusually credentialed for a 2-hour evening event. The host (Arklex AI) sells exactly the thing the event is about: a platform that simulates and evaluates agents *before* they hit production. So read the framing as a curated thesis, not a neutral panel: "evals are the unsolved bottleneck, and you should care before your support agent does something embarrassing." That said, the two speakers are not marketing props — they're two of the more serious people you could put on a stage about this:

1. **The benchmark builder (Kilian Lieret).** Co-creator of **SWE-agent / SWE-bench**, the open-source work that essentially defined how the field measures coding agents. Now at Meta Superintelligence. He has lived the hardest version of the eval problem: benchmark contamination, the gap between leaderboard scores and real behavior. He is the "how do we even measure this honestly" voice.
2. **The production-reliability founder (Zhou Yu).** Columbia CS professor, CMU PhD, Forbes 30u30, Amazon Alexa Prize winner — and now CEO of Arklex AI, whose **ArkSim** product simulates synthetic users to stress-test agents before launch. She is the "how do you de-risk an agent in production" voice, with commercial skin in the game.

**Why it matters for Alex specifically:** This is the cleanest single-room expression of the **"evals are the new bottleneck"** discourse that's defined enterprise AI in 2026 — the LangChain 2026 report puts quality/reliability as the #1 barrier to deploying agents, with 57% of orgs running agents in production. For a full-stack GTM operator job-hunting at AI-native companies, this is the *commercial* frontier, not just the research one: every enterprise buyer's actual question right now is "how do I trust this thing," and the vendors solving it (Arklex, Datadog LLM Observability, Braintrust, Arize, LangSmith, Galileo) are a live hiring market. Zhou Yu is a genuine networking target (founder of a bootstrapped, revenue-generating startup hiring GTM); Datadog-as-venue is a tell about where the enterprise observability incumbents see the puck going.

**Best angle to work it:** The documentarian frame writes itself — *"the room where the people who measure agents and the people who sell agent-reliability converge."* But the sharper play is going deep on the **honest counter-narrative**: in a year of agent hype, this is an event whose entire premise is "agents behave badly in production, and we don't have the tools to catch it yet." That's the post.

---

## Topics

### Topic 1: Agent Evaluation in Production — the "evals are the bottleneck" thesis

- **Current Events:** The dominant 2026 storyline is that **evaluation, not capability, is the constraint on shipping agents.** LangChain's 2026 State of AI Agents report: 57% of orgs have agents in production and **quality is the #1 barrier to deployment**. A widely-cited figure puts a **~37% gap between lab/benchmark scores and real-world deployment performance** for enterprise agentic systems. Cost is now a hard wall too: a single PaperBench-style eval run (with an LLM judge) reportedly runs ~$9,500; multi-seed model comparisons exceed $150K — so "AI evals are becoming the new compute bottleneck" (HuggingFace). The counter-move in 2026 is small, cheap judge models (e.g., Luna-2-class evaluators claiming sub-200ms, ~97% cheaper than GPT-4-as-judge) enabling 100% production traffic monitoring rather than sampling. ⚠️ Specific vendor latency/cost stats are vendor-published — soften if used publicly.
- **Opportunities:** A genuinely new product category is forming in real time (agent observability + simulation + eval gating). Whoever owns the "readiness gate" between dev and prod owns a structural choke point. For enterprises, reliable evals are what unlocks the move from pilot to production — i.e., where the ROI actually lives.
- **Challenges:** Non-determinism makes regression testing hard — the same input can produce different outputs, so "did this change break something?" has no clean answer. **LLM-as-judge reliability is itself unverified** — most judge setups are never checked against a human gold set, so you're measuring with an unaudited ruler. And benchmark contamination (models having seen the test set) corrupts the leaderboards everyone cites.
- **Use Cases & Practical Applications:** Customer support agents (the invite's own example: offering discounts on products that don't exist), coding agents (SWE-bench's home turf), and any autonomous multi-turn agent where drift compounds. Simulation-based pre-production testing (Arklex/ArkSim) and trace-based production monitoring (Datadog, Braintrust, LangSmith) are the two live deployment patterns.
- **Top Questions:**
  1. If LLM-as-judge is the dominant eval method and most judges are never validated against a human gold set, what's the minimum viable "audit the auditor" loop a team should run before trusting any automated score?
  2. Where does simulation (synthetic users, pre-prod) stop being predictive and production traces have to take over — is there a known crossover point, or is it domain-by-domain?
  3. Non-determinism breaks classic regression testing. What's actually replacing "did this commit break something" for agents — statistical bands, golden trajectories, something else?

### Topic 2: Reliability & Regression Testing for Non-Deterministic Systems

- **Current Events:** The field is converging on **trace-based evals and "golden trajectory"** approaches — evaluating the *path* an agent took (tool calls, reasoning steps), not just the final answer. Metrics in 2026 discourse: tool-calling success rate, task completion, trajectory adherence, faithfulness, goal completion. Arklex scores agent turns on helpfulness/coherence/relevance/faithfulness/goal-completion specifically.
- **Opportunities:** Treating evals as **CI/CD gates** (Braintrust's pitch — eval-gated deployment) brings software-engineering discipline to a domain that's been vibes-based. This is the bridge from "demo magic" to "shippable."
- **Challenges:** No schema validation on API responses, no observability on tool-call success, and **no drift detection** are the named root causes of 2026's agent failures. Regression testing a stochastic system is genuinely unsolved — you can't assert exact-match outputs.
- **Use Cases & Practical Applications:** SWE-bench/SWE-bench-Live as the canonical example of doing this honestly for coding agents (with decontaminated, continuously-updated task sets — see SWE-rebench, SWE-bench-Live). Multi-turn conversational agents via simulated users.
- **Top Questions:**
  1. SWE-bench's whole history is a fight against contamination and gamed leaderboards. What does the equivalent "the benchmark is being gamed" failure look like for *enterprise* agent evals, and how early can you see it?
  2. Is there a principled way to set the "pass" threshold on a non-deterministic eval, or is it always a business-risk judgment call dressed up as a number?

### Topic 3: Guardrails, Drift, and Off-Script Prevention

- **Current Events:** Real, citable incidents are now the genre's reference points. **Air Canada (Moffatt v. Air Canada, BC tribunal)** — the airline was held liable when its chatbot invented a bereavement-fare discount policy that didn't exist; the "it's a separate entity" defense failed. The invite's "discounts on products that don't exist" framing is almost a direct echo. A **"Klarna AI customer service refund incident" (Feb 2026)** is cited as a fresh guardrail-gap case. ⚠️ I could not independently verify the Klarna Feb-2026 incident details beyond aggregator listings — verify before public use.
- **Opportunities:** Guardrails + I/O validation + topic control is a clear product surface (Galileo, Arthur, others). The legal precedent (companies are liable for what their agents say) turns reliability from "nice to have" into "compliance/liability requirement" — which is the strongest possible enterprise budget unlock.
- **Challenges:** Guardrails that are too tight kill the agent's usefulness; too loose and it goes off-script. Drift is silent — behavior changes over time with no error thrown. Detecting "the agent is subtly wrong now" is harder than detecting "the agent crashed."
- **Use Cases & Practical Applications:** PII redaction, policy-violation detection, escalation-frequency monitoring, audit-trail completeness (the named guardrail metrics in 2026 enterprise guides). Datadog's Agent Observability ships out-of-the-box hallucination + drift evaluators plus sensitive-data scanning.
- **Top Questions:**
  1. The Air Canada ruling made companies liable for agent hallucinations. Does that change the eval bar from "good enough to ship" to "defensible in court," and does anyone actually instrument for the latter?
  2. Drift is the silent failure — no exception, just slowly-wrong. What's the leading indicator that catches drift before a customer (or a regulator) does?

---

## Companies

### Arklex AI (host; Zhou Yu's company)
- **What they do:** Agent-readiness platform — simulate, evaluate, and approve AI agents for production *before* customers and regulators encounter failures. Open-source roots (Agent-First Organization framework on GitHub) plus a commercial platform. Flagship: **ArkSim** — generates synthetic users with distinct profiles/goals/behaviors that hold realistic multi-turn conversations with your agent, scores every turn, and surfaces failures pre-launch ("find your agent's errors before your real users do"). Tagline in market: *"Prove agent readiness before production."*
- **Recent developments:** ArkSim open-sourced and promoted by Zhou Yu (March 2026, per X/LinkedIn). Reported **~$2.3M revenue with a ~21-person team in 2025, bootstrapped — no outside VC** (per GetLatka; ⚠️ third-party-reported, treat as approximate). Founded 2023.
- **Industry/Space:** AI/ML, Developer Tools, AI agent evaluation/observability.
- **Funding stage:** ⚠️ Bootstrapped / no disclosed institutional round — for schema purposes treat as Seed-equivalent or "self-funded." Do not assert a Series letter.
- **Why it matters for Alex:** A revenue-generating, bootstrapped, NYC-adjacent AI-native startup in a hot category, led by a credentialed founder — exactly the profile that hires senior GTM as it scales past founder-led sales. Highest-leverage relationship in the room.
- **Headwinds:** Bootstrapped means slower to land-grab a category where well-funded competitors (Braintrust, Arize, Galileo, plus Datadog/LangSmith bundling eval into bigger platforms) are spending aggressively. The eval/observability space is crowding fast; differentiation (simulation-first vs. trace-first) has to hold.

### Datadog (venue host)
- **What they do:** Public observability/monitoring giant; **LLM Observability** and **Agent Observability** products are its push into AI. Ships end-to-end tracing across prompts/retrieval/tool-calls/decisions, real-time latency/token/cost monitoring, out-of-the-box hallucination + drift evaluators, sensitive-data scanning/redaction, RBAC, and LLM Experiments / AI Agents Console (expanded June 2025).
- **Recent developments:** June 2025 expansion of LLM Observability for agentic AI monitoring + experimentation. Continued positioning as the "enterprise-default for Datadog shops" in 2026 observability comparisons.
- **Industry/Space:** Enterprise Software, Observability, AI/ML.
- **Funding stage:** Public (NASDAQ: DDOG).
- **Why it matters for Alex:** The incumbent tell. When the observability leader hosts the agent-eval meetup, it signals the category is real and the incumbents intend to absorb it. Useful context for any conversation about where eval tooling consolidates (standalone startups vs. platform bundling).
- **Headwinds:** Eval/observability for agents is being attacked from below by focused startups (Braintrust's eval-gated CI/CD, Arize's OTel-first open stack, Arklex's simulation angle). "Good enough, already in your stack" vs. "best-of-breed" is the live tension.

### Meta Superintelligence (Kilian Lieret's employer)
- **What they do:** Meta's superintelligence/frontier-AI lab (the reorganized high-profile AI effort under Meta). Lieret works on **agentic AI for software development** there.
- **Recent developments:** ⚠️ The lab's internal structure and naming have been in flux in public reporting (e.g., LeCun-role coverage); I did not verify specifics of Lieret's team or current mandate beyond his self-described "Research @ Meta Superintelligence." Treat any claim about what the lab is building as unverified.
- **Industry/Space:** AI/ML, frontier research.
- **Why it matters for Alex:** Context, not a target. Lieret's value is the SWE-bench lineage and the honest-measurement POV, not the Meta affiliation per se.
- **Headwinds:** N/A for this brief (not a commercial target).

---

## Signals (last ~60 days)

- **Agent-eval is consolidating into a named category.** 2026 comparison content treats six platforms as the anchors: LangSmith (LangChain-native), Langfuse (OSS leader), Arize Phoenix (ML-grade, OTel-first), Helicone (proxy), Datadog LLM Observability (enterprise-default), Honeycomb (event-based). Braintrust is the CI/CD-eval-gating standout (most generous free tier; trace-to-test pipeline). Arklex is positioned distinctly as **simulation-first** (synthetic users) vs. the trace-first majority. ⚠️ No verified 2026 funding rounds surfaced for these in search — do not cite round sizes.
- **Benchmark integrity is an active fight.** OpenAI's own audit reportedly found all frontier models show training-data overlap with SWE-bench Verified, and ~59% of hard tasks had flawed tests — driving decontaminated/auto-updating successors (SWE-rebench, SWE-bench-Live, SWE-bench Pro). This is *exactly* Lieret's domain and a sharp, current thing to raise with him. ⚠️ The 59.4% figure is from search-surfaced summaries; verify before quoting publicly.
- **Legal liability is now a forcing function.** Air Canada (Moffatt) established that companies are liable for their agents' false statements; 2026 commentary frames this as the precedent that turns guardrails from optional to mandatory. A Klarna Feb-2026 refund-guardrail incident is cited as the fresh example (⚠️ unverified specifics).
- **The cost wall is real.** "Evals are the new compute bottleneck" — frontier eval runs hitting five-to-six figures is pushing the field toward small, cheap judge models for full-traffic monitoring. ⚠️ Specific per-run dollar figures ($9,500 / $150K) are from secondary sources — frame as "reportedly."

---

## PRE-EVENT CONTENT

### 1. Pre-Event LinkedIn Post — 2 variants (A/B)

> Style notes applied: documentarian/analytical, low-medium stance license (pre-event, haven't seen it). Opens in the tension. Decenters Alex — the event/field is the subject. 2-3 data points. Source-checked claims only; the unverified stats are kept OUT of the public copy. Both target ~900-1,500 chars.

---

#### Variant A — Contrarian hook ("the honest counter-narrative") — 1,343 chars

The most credentialed AI event on my calendar this month is, essentially, about AI agents screwing up.

Not a launch. Not a demo reel. A room at Datadog called "Agents Behaving Badly: The Perils of Pushing AI Agents into Production."

Here's why that framing is the honest one. In LangChain's 2026 report, 57% of organizations now run agents in production — and quality is the #1 barrier to deploying more. The hard part stopped being "can the agent do the task." It became "can you prove it won't go off-script when no one's watching."

That problem has a name now: evaluation. How do you regression-test a system that gives a different answer to the same question twice? How do you catch drift that throws no error — the agent isn't broken, it's just slowly, quietly wrong?

The lineup tells you the field is taking this seriously. One speaker co-built SWE-bench, the benchmark that defined how we measure coding agents (and spent years fighting the contamination that corrupts those scores). The other runs a company that simulates synthetic users to break your agent before your real customers do.

Two ends of the same problem: how do we measure these things honestly, and how do we de-risk them before production.

The agents-replacing-everyone story gets the headlines. The room actually solving for production is the one admitting how badly agents still behave.

If you work on agent reliability or evals — what's the failure mode you watch for that nobody talks about?

#AgentEvals #AIReliability #AgenticAI #LLMOps #AINYC

---

#### Variant B — Question / convergence hook ("the room where the category forms") — 1,287 chars

Who actually shows up to a meetup about AI agents failing in production?

The people who measure agents, and the people who sell the tools to keep them in line. That convergence is the whole story.

On June 25, Arklex AI and Datadog are hosting "Agents Behaving Badly" — and the two names on the bill map the entire problem. One co-created SWE-bench, the open-source benchmark that defined how the field scores coding agents, and lived the unglamorous fight against contaminated leaderboards. The other founded a company whose product simulates synthetic users to stress-test agents before launch.

Measurement on one side. Pre-production reliability on the other. Sitting in a venue hosted by the observability incumbent that's busy bundling agent-eval into its platform.

That's not a coincidence — it's a category forming in real time. The 2026 enterprise question stopped being "what can agents do" and became "how do I trust one in front of a customer." LangChain's latest report puts quality as the #1 barrier to shipping more agents, with 57% of orgs already running them in production.

When the researchers, the startups, and the incumbents all converge on the same unsolved problem in the same room, that's usually where the next category gets decided.

If you're building in agent evals or observability — where do you think this consolidates?

#AgentEvals #AIObservability #AgenticAI #LLMOps #AINYC

---

### Visual Brief — 4-slide carousel (Arc: 3 — Before → After → What Changed → So What)

**Carousel thesis:** The bottleneck in shipping AI agents moved from capability to evaluation — and that shift is what created an entire new tooling category.

**Slide count:** 4
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Tool routing summary:** All 4 → Gamma (`format: social`, 4x5, Stratos dark theme, `imageOptions.source: noImages`). Slides are diagram/stat-led, not typography-only. Fallback: Canva for Slide 4 typography card.

---

#### Slide 1 of 4 — Before: the bottleneck was capability

- **Visual mode:** Split-frame / before-state diagram
- **Headline:** "2023: Can the agent do it?"
- **Body / content:** Simple funnel diagram — wide top "Can it complete the task?" narrowing to a small "Ship it." Caption beneath: *The hard question was capability. Demos were the proof.*
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) on the funnel
- **Source attribution:** none (framing slide)
- **Alt text:** A funnel showing that in 2023 the main gate to shipping an agent was whether it could complete the task.
- **Tool:** Gamma

#### Slide 2 of 4 — After: the bottleneck is evaluation

- **Visual mode:** Single-number data viz (mirrors Slide 1's frame, transformed)
- **Headline:** "2026: Can you trust it?"
- **Body / content:** Same funnel shape, but now the narrow choke point is labeled "Evaluation" and is the bottleneck. Two big stats as callouts: **57% of orgs run agents in production** and **quality = #1 barrier to deploying more.**
- **Palette:** dark slate bg + off-white text + blue accent (#1E40AF) — identical frame to Slide 1
- **Source attribution:** Source: LangChain State of AI Agents 2026
- **Alt text:** The same funnel, now showing evaluation as the narrow bottleneck to shipping agents in 2026, with 57% of orgs already in production.
- **Tool:** Gamma

#### Slide 3 of 4 — What changed: the failure mode

- **Visual mode:** Diagram with the delta highlighted (taxonomy of how agents fail silently)
- **Headline:** "The failures throw no error"
- **Body / content:** Three labeled boxes in a row — **Non-determinism** (same input, different output → regression testing breaks) · **Drift** (behavior changes over time, no exception raised) · **Off-script** (agent invents policy / offers what doesn't exist). One small footnote box: *Precedent: a chatbot invented a discount policy; the company was held liable. (Moffatt v. Air Canada)*
- **Palette:** dark slate bg + off-white text + red accent (#DC2626) on the failure-mode labels (risk topic)
- **Source attribution:** Source: Moffatt v. Air Canada, BC Civil Resolution Tribunal, 2024
- **Alt text:** Three silent agent-failure modes — non-determinism, drift, and going off-script — with the Air Canada liability case as a real-world example.
- **Tool:** Gamma

#### Slide 4 of 4 — So what: the question for your own org

- **Visual mode:** Bold typography card (closing question)
- **Headline:** "How would you catch this?"
- **Body / content:** *Your agent isn't broken. It's just slowly, quietly wrong. What's your leading indicator — before the customer, or the regulator, finds it first?*
- **Palette:** dark slate bg + off-white text, no accent (documentarian/synthesis mode)
- **Source attribution:** none
- **Alt text:** A closing question asking what leading indicator a team uses to catch an agent that has drifted into being subtly wrong.
- **Tool:** Gamma (or Canva fallback)

---

**Quality gate checks:**
- Arc fit: pass — capability→evaluation is a genuine before/after change-over-time story (Arc 3).
- Job differentiation: pass — each slide does distinct work (old gate / new gate / failure mechanism / reader's question).
- Frame parallelism (Arc 3): pass — Slides 1 & 2 share the identical funnel frame so the shift is legible.
- Thumb test per slide: pass — all headlines ≤5 words.
- Source citations: pass — LangChain stat (S2) and Air Canada case (S3) both cited; no unverified stats placed on slides.
- Adds information (not repetition): pass — the funnel shift, the failure taxonomy, and the liability precedent are NOT in the post body verbatim; the carousel visualizes the *mechanism*, not the copy.
- Final slide earns the swipe: pass — ends on the reader's own-org question, not housekeeping.

---

### 2. Connection-Request Notes (200-char cap, 2 variants per person)

---

#### Kilian Lieret — AI Research Scientist, Meta Superintelligence (speaker)
Talk/Topic: agent evaluation in production; SWE-bench/SWE-agent lineage

**Variant A — Talk-anchored** (188 chars / 200 cap)
Signal anchored: the event's core premise (measuring non-deterministic agents) tied to his benchmark work
> Going to "Agents Behaving Badly" Thu. SWE-bench fought contamination for years—what's the enterprise-agent-eval equivalent of a gamed leaderboard, and how early can a team actually see it coming?

Rubric score: 88/100
Pattern: Pattern 1 (talk-anchored)

**Variant B — Adjacent-work-anchored** (197 chars / 200 cap)
Signal anchored: the decontaminated/auto-updating successors to SWE-bench (SWE-bench-Live / SWE-rebench)
> SWE-bench-Live and the decontaminated rebuilds feel like an admission that static benchmarks rot. Does that same "continuously refresh the test set" logic have to apply to enterprise agent evals too?

Rubric score: 86/100

---

#### Zhou (Jo) Yu — Co-Founder & CEO, Arklex AI (speaker + host)
Talk/Topic: pre-production agent reliability; simulation-based evaluation (ArkSim)

**Variant A — Talk-anchored** (193 chars / 200 cap)
Signal anchored: the simulation-vs-production-traces crossover, anchored to her event premise
> Catching you at "Agents Behaving Badly" Thu. Where does simulating synthetic users stop predicting real failures and production traces have to take over—a known crossover, or domain-by-domain?

Rubric score: 90/100
Pattern: Pattern 1 (talk-anchored)

**Variant B — Adjacent-work-anchored** (199 chars / 200 cap)
Signal anchored: open-sourcing ArkSim (March 2026) + the SAGE user-simulator paper
> You open-sourced ArkSim to find agent bugs before users do. With synthetic users, how do you keep the simulated personas from drifting toward the failure modes you already know vs. the ones you don't?

Rubric score: 89/100

---

### 3. Prepared Questions (independent of the notes — for live Q&A / conversation)

## Prepared Questions: Agents Behaving Badly

### For Kilian Lieret — agent eval / benchmark integrity
1. SWE-bench's whole arc has been a fight against contamination and gamed scores. What does the *enterprise* version of "the benchmark is being gamed" look like — and what's the earliest honest signal a team has that their own eval is lying to them? — (angle: transfers his hardest-won lesson into the enterprise context; treats him as the measurement authority)
2. LLM-as-judge is now the default eval method, but most judges are never validated against a human gold set. What's the minimum viable "audit the auditor" loop before a team should trust an automated score? — (angle: the unaudited-ruler problem; ask if drift/regression comes up)
3. Coding agents have SWE-bench because "did the test pass" is verifiable. For agents where correctness is fuzzy — support, ops — is verifiable ground truth even possible, or are we permanently stuck with proxy metrics? — (angle: probes the limits of his own paradigm; good follow-up if he generalizes from coding)

### For Zhou Yu — pre-production reliability / simulation
1. Where does simulation stop being predictive and production traces have to take over? Is there a crossover point you've found, or is it domain-by-domain? — (angle: the central methodological seam in her product; her sharpest lane)
2. Synthetic users are only as good as the failure modes you can imagine. How do you generate personas that surface the failures you *haven't* thought of — the unknown unknowns — rather than just the ones you've already seen? — (angle: the hardest problem in simulation-based eval; goes one layer past the ArkSim pitch)
3. The Air Canada ruling made companies legally liable for what their agents say. Does that change the eval bar from "good enough to ship" to "defensible in court" — and does anyone actually instrument for the second one yet? — (angle: connects her commercial pitch to the liability forcing-function; ask if guardrails/compliance comes up)

### For either speaker / the room
1. Drift is the silent failure — no exception, just slowly-wrong. What's the leading indicator that catches it before a customer or a regulator does? — (angle: the universal hard problem; works as an opener with anyone in the room building eval/observability)

---

## Verification Gaps

⚠️ **Flagged for verification before any public/outbound use:**

1. **Kilian Lieret's exact Meta Superintelligence role/mandate** — confirmed he is "AI Research Scientist, Research @ Meta Superintelligence" (his own LinkedIn) and works on agentic AI for software dev. The *internal lab structure / what the team is building* is NOT verified (public reporting on the lab has been in flux). Don't assert specifics about his Meta work. SWE-agent/SWE-bench co-authorship is well-sourced and safe to use.
2. **Arklex revenue (~$2.3M) and headcount (~21), bootstrapped/no-VC** — from GetLatka (third-party aggregator), not company-confirmed. Treat as approximate; do NOT put the dollar figure in public content. The "bootstrapped, no disclosed round" framing is consistent across sources but should be softened ("appears bootstrapped").
3. **The $9,500 / $150K eval-cost figures and Luna-2 sub-200ms / 97%-cheaper stats** — secondary-source / vendor-published. Kept OUT of the public post copy deliberately. Frame as "reportedly" if ever used.
4. **OpenAI SWE-bench audit: "all frontier models show overlap" + "59.4% of hard tasks flawed"** — from search-surfaced summaries, not the primary audit doc. Safe as conversational color with Lieret; verify the 59.4% before quoting in a post.
5. **Klarna Feb-2026 customer-service refund/guardrail incident** — appears only in aggregator listings; specifics unverified. Air Canada (Moffatt v. Air Canada) is solidly sourced and is the safe precedent to cite publicly.
6. **The "+3 other hosts" on the invite** — unnamed; not researched. If they're named on the Luma page, worth a quick check for additional networking targets.
7. **Zhou Yu name disambiguation** — there are multiple "Zhou Yu" profiles on LinkedIn; the correct one is **Zhou (Jo) Yu** (Columbia CS professor + Arklex co-founder, handle zhou-jo-yu / @Zhou_Yu_AI). Confirmed via Crunchbase + her own posts. Don't connect to the wrong profile.
8. **LangChain "57% / quality = #1 barrier" stat** — attributed to LangChain's 2026 State of AI Agents report via search summary; widely repeated and low-risk, but cite the report (not a number floating free) if challenged.
