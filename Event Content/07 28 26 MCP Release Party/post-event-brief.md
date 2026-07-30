> 🗃️ **Post-Event Brief — MCP Release Party (Jul 28, 2026)** · data store / short-term memory for all downstream drafts.
> `post_event_processed: 2026-07-28` · Type `post_event_brief` · Phase `post_event` · Status `needs_review` · Platform `notion_only`.
> Page is long — use `/toc` in Notion to jump. Completeness over curation: this brief keeps everything; the post selects from it.

# Post-Event Brief — MCP Release Party (NYC)

**Event:** MCP Release Party — New York (one of a six-city global series)
**Date:** 2026-07-28 (the day the MCP 2026-07-28 spec release candidate shipped)
**Venue:** The New York Times Building (Datadog's NYC office), Manhattan
**Host / organizer:** Agentic AI Foundation (AAIF) — nonprofit under the Linux Foundation
**Sponsor / space:** Datadog
**Format tag (for content routing):** multi-presenter showcase (3 sequential talks + Q&A, single MC), followed by networking/cake
**Notion Event:** https://app.notion.com/p/3abd3699c2db8101a296c5405e3ee315

---

## 1. Quick Take

Three back-to-back talks on the biggest MCP spec change since launch — shipped *that day* — turned a release party into an operator's tour of what the new stateless protocol fixes and what it deliberately leaves open. Alex Hancock (Block/Goose) framed the marquee change (statelessness) as the fix for remote-first MCP at scale; Scott Yak (Datadog) showed what running a 197-tool MCP server actually costs *organizationally*; Michael Levan (Solo.io) closed on the authorization gap the spec still doesn't cover. **Headline: the room delivered the infrastructure win exactly as the pre-event brief predicted, then spent the two operator talks on the two frontiers the brief said would stall production — runtime authorization scope and eval-under-drift.** Event-type: multi-presenter showcase — route to a per-talk deep post + one synthesis post; low outreach yield (no one flagged).

## 2. The Thesis

**MCP's July release solved the infrastructure problem (stateless scaling) in the open; the problems that gate production — what an authorized tool is allowed to *do*, and keeping evals honest as tools multiply — are being solved privately, at the gateway and inside ops teams, not in the spec.** Levan's framing is the quotable spine: *"a new protocol, a new spec, that means there's going to be a new attack surface."* The spec closed the scaling gap and opened an authorization gap in the same release.

## 3. Pre → Post Gap (highest-value beat)

Pre-event thesis (from the pre-event brief/post): MCP nailed **infrastructure** (stateless scaling) and **identity** (enterprise-managed authorization), but the two things that stall production stayed open — **runtime authorization scope** (what a tool may *do* after the call is authorized) and **eval-under-drift** (agents lose competence when a tool's schema changes). Alex's operator-grade angle: *"everything after the call is authorized is the frontier."*

| Pre-event prediction | What the room actually said | Verdict |
|---|---|---|
| MCP nailed **infrastructure / stateless scaling** | Alex Hancock: statelessness is *"the big marquee change"* — no more `initialize`, no session state; every request is self-contained, so you can put a normal load balancer + autoscaling pool in front. Exactly the predicted win, delivered on release day. | **CONFIRMED** |
| **Runtime authorization scope** ("what a tool may DO after auth") is the open frontier | Michael Levan's entire talk = *"the authorization gap nobody's closing."* The spec gives you authN + some authZ; what the agent can actually *do* (tool isolation, agent identity, OBO/token exchange, ABAC/ReBAC) is unsolved and lives **at the gateway, not the MCP server or the spec.** The MCP server is *"a black box"* you can't secure at the server; enforcement must happen a step earlier. | **CONFIRMED + SHARPENED** — named as the talk's thesis |
| **Eval-under-drift** — keeping agents honest as tools change | Scott Yak: Datadog's tool count grew **47 → 197** in months; their team now authors evals per tool, and *"we cannot be the ones who are creating the evals for all the tools... we need to figure out how to scale up the eval authoring as well."* Eval-authoring-under-tool-growth is an unsolved org bottleneck. | **CONFIRMED + EXTENDED** — reframed from model-competence drift to an org-scaling problem |
| (Not predicted) | Scott surfaced a *new* frontier the brief didn't name: **organizational scaling** — a monolithic MCP server makes the platform team the review bottleneck for 83 product teams; *"the context is a shared commons."* Distributed/per-team MCP servers behind one URL is Datadog's answer. | **NEW — net-add to the thesis** |

**Documentarian payoff (one line):** *The release nailed the infrastructure win the pre-event brief predicted — and then both operator talks confirmed, out loud, that the frontier is exactly where the brief said it was: everything after "the call is authorized," plus keeping evals honest as tools multiply. The spec closed the scaling gap and opened the authorization gap in the same release.*

## 4. Speaker Map (content-derived — raw diarization IDs are NOT 1:1 with people)

| Raw label(s) | Resolved person | Role / affiliation | Tell | Confidence |
|---|---|---|---|---|
| speaker_0 | **Angie Jones** (MC/host) | VP Developer Experience, **Agentic AI Foundation**; ex-Global VP DevRel, **Block** | Alex Hancock thanks *"Angie"* (04:14); self-refers to a *"little Angie discount"* (95:55); runs housekeeping, intros all 3 speakers, gives AAIF event/cert plugs | **HIGH** (name); HIGH (identity via enrichment) |
| speaker_1 (04:05–32:13, during Talk 1) | **Alex Hancock** | Software engineer, **Block** (10 yrs); MCP maintainer (**Rust SDK**), core maintainer of **Goose** | *"I'm a software engineer at Block... I just crossed the ten-year mark... I work on the Rust SDK... core maintainer of the Goose project"* (04:34–05:02) | **HIGH** |
| speaker_1 (22:48) | **Merged: audience question + Alex's answer** | — | Diarization glued an audience member's *"Hey thanks, that was really good, I had a couple questions"* to Alex's answer that follows. Attribute the question to *"an audience member,"* the answer to Alex. | HIGH (that it's a merge) |
| speaker_1 (54:13, 55:31, 56:03 — during Scott's Q&A) | **Unresolved audience member** (possibly Alex Hancock — same voice cluster, unconfirmed) | — | Asks Scott about token usage + tool descriptions. Same diarization cluster as Alex, but no self-identifying tell. **Do NOT tag anyone publicly.** | LOW |
| speaker_5 | **Scott Yak** | Senior software engineer, **Datadog** — Applied AI / MCP services | *"my name is Scott. I'm a software engineer at Datadog. I work on the MCP server"* (33:49) | **HIGH** |
| speaker_7 | **Michael Levan** | AI Architect / Principal Solutions Engineer, **Solo.io**; Microsoft MVP, CNCF Ambassador, AAIF "AI Young Ambassador" | *"I work at Solo as an AI architect"* (~60:00); Angie intros *"one of our AI Young Ambassadors, Michael Lev[an]"* (58:31) | **HIGH** (transcript spells "Levin"; canonical **Levan**) |
| speaker_2, speaker_3, speaker_4, speaker_6 | **Audience Q&A members** (unnamed) | — | Distinct questioners across the three Q&A blocks; none state a name. Attribute generically ("an audience member"). speaker_3 asks the sharpest security follow-ups in Levan's Q&A (payments/health-data multi-client scenario). | Generic by design |

**Not on stage (roster / organizers, did not speak):** Lahari Chowtoori and David DeStefano (listed as AAIF NY community organizers in the pre-event roster). Angie thanks *"the community organizers... volunteers"* generically (101:32) but names neither — treat both as organizers, not speakers, and do not attribute any line to them.

## 5. Full Quote Bank

> Full confidence-tagged quote bank with per-line attribution lives in the companion file `quote-bank.md`. The load-bearing lines, by talk:

**Alex Hancock (Block / Goose / Rust SDK):**
- *"Statelessness — this is the big marquee change in this version."* (HIGH)
- *"What it really means for the protocol to be stateless is that every request has the information that it needs for the server to handle it included in the request. So now there is no initialize anymore. There is no session anymore."* (HIGH)
- *"So let's pour one out — for roots, sampling, and logging."* (MED — "pour" is a flagged low-confidence word at 08:11; paraphrase the deprecation, don't hang the joke on the exact word)
- *"With this new protocol version being cut, MCP Apps landed as the first extension... and there's another new one that just landed... for doing tasks."* (HIGH)
- On Tasks: *"anything that takes a long time is a valid use of tasks... an MCP server that exposes something that might take hours or days, which wasn't really practical before with tool calls."* (HIGH)
- On the SDKs: *"all of the SDKs for MCP have gotten really good... our hope is that the SDKs make it easier for everybody building out there to just have a lot of it abstracted away."* (HIGH)
- *"Codex and Copilot are now both using the Rust SDK."* (HIGH as *what he said*; **Rule 12** — external claim about other companies' products, verify before asserting as fact)

**Scott Yak (Datadog):**
- *"Monolithic MCP servers don't scale organizationally."* (HIGH — his own closing summary line)
- *"Because the context is a shared resource, it's a shared commons... if one tool is very inefficient with tokens in their tool description, it will affect everyone else."* (HIGH)
- *"We get paged when [a] tool fails and exceeds a certain threshold. And so imagine with two hundred something tools, what kind of experience that is like."* (HIGH)
- *"We think about running an MCP server just like the way we think about running an HTTP server... It becomes a boring technology... rather than being something that is your full-time job."* (HIGH)
- On evals: *"we cannot be the ones who are creating the evals for all the tools... we need to figure out how to scale up the eval authoring as well."* (MED — "evals" is ASR-rendered "edals/au- edals"; substance certain, paraphrase the phrasing)
- *"When we read a lot of tokens or we write a lot of tokens, it doesn't actually cost us anything. But... for the LLMs, it will cost the MCP host... a lot."* (HIGH)

**Michael Levan (Solo.io):**
- *"A new protocol, a new spec — that means there's going to be a new attack surface."* (HIGH)
- *"It's always about mitigating as much risk as you possibly can, because you're never gonna mitigate everything."* (HIGH)
- *"Nine point nine nine nine times out of ten... security is gonna be implemented [at the gateway]."* (HIGH)
- On tool isolation: *"I believe the number is still between like fifteen and eighteen tools that you want exposed to your agent. Outside of that, you can come up with more and more hallucinations."* (HIGH)
- On agent identity: *"it's not just the identity of a service... it's the identity of ten, twenty, thirty, forty, a hundred agents running."* (HIGH)
- *"I saw this Reddit post... 'We have forty agents running, and we don't know what half of them do anymore.'"* (HIGH — attribute as *a Reddit post he cited*, not his own metric)
- On securing the server: *"an MCP server as a whole is like this black box... you can't do anything. You can pen test it, but... So what you have to do is instead of putting that onus on the MCP server, you have to take that a step back and put those decisions in your gateway."* (HIGH)

## 6. Pro-Tips (actionable "if X → do Y")

- **If you scale an MCP server, go stateless first** — statelessness is what lets you put a standard load balancer + autoscaling pool in front without sticky sessions or a shared Redis/session store (Hancock). HIGH.
- **If you maintain an MCP program by hand, migrate to an SDK before upgrading to the new spec** — the SDKs absorbed the breaking changes; hand-rolled message handling means *"a lot of work"* to upgrade (Hancock). HIGH.
- **If you have a long-running or human-in-the-loop operation, use the new Tasks extension** instead of going around the protocol — create a task, hand back a task ID, poll for status (Hancock). HIGH.
- **If you're building a multi-team MCP surface, don't ship a monolith** — make each product team own its own MCP server behind one URL, so no single team is on-call for 200 tools (Yak). HIGH.
- **Treat the tool-list/context window as a shared commons** — one team's bloated tool description taxes every other tool's `list tools`; review token-efficiency centrally (Yak). HIGH.
- **Cap tools exposed to an agent at ~15–18** — beyond that, hallucination rate and input-token cost climb as the agent ingests all the tool metadata (Levan). HIGH.
- **Put security at the gateway, not the MCP server** — the server is a black box you can't enforce inside; do tool isolation, identity, rate-limiting, guardrails, OBO/token-exchange at the AI gateway a step before the LLM (Levan). HIGH.
- **Secure the response path, not just the request path** — guardrails must inspect what comes *back*; the attack vector can run B→A (Levan). HIGH.
- **Use workload/agent identity (e.g., SPIFFE ID via service account), not the agent name** — names change, workload identities don't (Levan). HIGH.
- **Run a daily automated bug-sweep on your own MCP server** — Datadog points an agent (Bits AI) at the last 24h of logs to find the top error, root-cause it, implement a fix, and open a PR to review (Yak). HIGH.

## 7. Best Practices / Patterns (recurring across speakers)

- **Stateless / self-contained requests** as the enabling primitive — Hancock (protocol), Yak (drops the session store), Levan (gateway enforcement per-request). All three lean on it.
- **Consolidate cross-cutting concerns at a platform/gateway layer** — auth, rate-limiting, config enforcement, token optimization handled once, not per team (Yak + Levan converge here from different angles: ops platform vs. security gateway).
- **MCP as "boring infrastructure"** — the maturity goal both Yak and Hancock name: an engineer's baseline skill, not a specialist full-time job.
- **MCP Apps extension adoption** — both Hancock (framed it as extension #1) and Yak (ships ad-hoc visualizations/interactive widgets via MCP Apps) are already on it.

## 8. Pitfalls / Anti-Patterns (named in the room)

- **Stateful sessions behind a round-robin load balancer** — the old-world failure: sticky-session pinning blocks fleet cycling; a shared session store adds an architectural component and its own scaling limits (Hancock). HIGH.
- **The platform team as tool-review bottleneck** — being code-owner for every tool description across 83 product teams doesn't scale; you get paged for 200 tools you don't own the use cases for (Yak). HIGH.
- **`initialize` calls exceeding tool calls** — IDEs/hosts auto-connect to configured MCP servers on laptop-open and fire `initialize` without ever making a tool call; a real source of inefficiency (Yak). HIGH.
- **`max_tokens` as the token-control lever** — agents ask for 50k tokens they don't need (often a weaker model over-requesting); Datadog concluded max_tokens *"is probably not enough"* and they need to optimize outputs more aggressively (Yak). HIGH.
- **Trusting the MCP server to enforce client-level data policy** — wrong layer; the server is a black box, enforcement belongs at the gateway (Levan). HIGH.
- **Auto-approving agent actions ("yes, yes, yes" / auto-mode)** — people stop reading output, so authorization must be enforced behind the scenes, not at the prompt (Levan). HIGH.

## 9. Hot Takes (contrarian / surprising — captured raw; publish gate decides)

- **"Monolithic MCP servers don't scale organizationally."** (Yak) — the non-obvious one: MCP's scaling wall is org/ownership, not compute.
- **"An MCP server is a black box... securing what data it returns to which client is NOT the job of the MCP server."** (Levan) — pushes back on a customer's instinct; enforcement is a gateway concern.
- **"Is your larger user today an agent or a human? ... We suspect they are agents, but we need to verify."** (Yak, answering an audience member) — Datadog thinks agents already outnumber humans on their MCP server.
- **"The authorization gap nobody's closing"** (Levan's title) — the spec added authorization improvements the *same day*, and his framing is still that the real gap is unclosed.

## 10. Substantive Insights (ranked by durability / content value)

1. **The July 28 release is remote-first MCP finally admitting it** — every change (stateless, MRTR, deprecating roots/sampling/logging) follows from "MCP is now used across machines, not on one machine" (Hancock). Most durable framing of the whole release.
2. **The frontier moved from protocol to enforcement** — with scaling handled in-spec, the unsolved work (runtime authZ scope, evals) is now operator/gateway work, done privately. This is the pre→post confirmation and the synthesis spine.
3. **MCP's scaling wall is organizational** — 47→197 tools, 83 teams, a platform team as bottleneck; the fix is distributed ownership behind one URL (Yak). Non-obvious, operator-grade.
4. **Eval-authoring doesn't scale with tool growth** — the quiet admission that keeping evals current is the next bottleneck (Yak). Direct hit on the eval-under-drift thesis.
5. **Agent identity ≠ service identity** — the security model has to reason about tens/hundreds of agents, each with its own identity and permission scope, not just users and services (Levan).
6. **MRTR ≈ x402** — the new multi-round-trip request pattern (server says "I need more info," client re-sends the same call with it) is the same shape as Coinbase's x402 payment-required flow; an audience member spotted it and Hancock agreed (SEP-2322).

## 11. Anecdotes (narrative — for hooks)

- **The live release, live on stage.** Angie puts Hancock on the spot — *"Is the Rust SDK ready?"* — and he admits *"it's not merged yet... I'm gonna merge the release PR right now."* The Rust SDK went to 3.0 during the party. "Well, it works on Alex's machine." Great cold-open.
- **The demo gods.** Levan's live auth/elicitation demo won't connect over port 3000; Angie deadpans *"Because it's a live demo,"* he says *"I shouldn't have done that,"* and finishes on the second try. Classic ephemeral-room texture.
- **"Literally finished it on the Uber ride here."** Levan's agent-mesh (Istio/kagent/agentgateway/SPIFFE) demo was built in the car on the way over. The room's build-in-public energy in one line.
- **The MC flew in for this.** Angie's plane got diverted to Baltimore (BWI) under a flood watch; she took an Uber to a train to make the NYC party. *"I appreciate you all showing up for me."*
- **"I just go in there sometimes, and I just smile."** Angie on the MCP contributors' Discord — dozens of channels, working groups, *"busy bees"* — the community-vibrancy hook.
- **Cake, insisted upon.** *"I insisted that there must be cake if we're gonna have a party."* Release-party color.

## 12. Concept Glossary (enriched — brief stands alone)

- **MCP (Model Context Protocol)** — open standard connecting AI clients to tools/data. Created at Anthropic by David Soria Parra and Justin Spahr-Summers; open-sourced Nov 25, 2024; **donated to the Agentic AI Foundation (Linux Foundation) in Dec 2025.** [source: anthropic.com/news/model-context-protocol]
- **The 2026-07-28 release** — largest MCP spec revision since launch; shipped as a release candidate the day of this party. Stateless core achieved via six SEPs. [blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/]
- **Statelessness** — no `initialize`/session; every request self-contained. Enables standard load balancers + autoscaling without sticky sessions or a shared session store.
- **MRTR (Multi-Round Trip Request)** — new pattern for server→client asks (e.g., elicitation): server responds "I need more info," client re-sends the same tool call with the added info; repeats until complete. SEP-2322 per Hancock. Shape mirrors x402.
- **Elicitation** — server needs input from the user mid-tool-call (fill a form, confirm permission); now implemented over MRTR instead of a held-open SSE stream.
- **Extensions framework (SEP-2133)** — formal path from experimental → official; reverse-DNS IDs, negotiated via a capabilities map, versioned independently of core. [github.com/modelcontextprotocol]
- **MCP Apps (SEP-1865)** — extension #1; servers ship interactive HTML UIs hosts render in a sandboxed iframe (weather widget, Airbnb-style UI). Datadog uses it for ad-hoc visualizations.
- **Tasks (SEP-2663)** — extension #2; async, long-running tool calls (DB migration, human-in-the-loop over days) via create → task ID → poll → complete. Redesigned around the stateless model.
- **Deprecated in this release:** roots, sampling, logging.
- **Authorization change (this release):** clients now require an `issuer` in authorization metadata; will start rejecting metadata without one in a future version.
- **x402** — Coinbase's HTTP-402-based payments protocol for internet-native / agent micropayments (client hits resource → 402 Payment Required → resends with payment proof → 200). Now under Linux Foundation governance. Cited by an audience member as MRTR's structural twin. [github.com/coinbase/x402]
- **Goose** — Block's open-source agentic harness; one of the first MCP clients; reference-adjacent client implementation; donated to the Linux Foundation. Connects to 4,000+ MCP servers. [block.github.io/goose]
- **Rust SDK (MCP)** — the SDK Hancock maintains; went to 3.0 at the event; heading to "tier one" (fully up-to-date, supported, cross-company maintainer roster). Hancock: Codex and GitHub Copilot both now use it (Rule-12 external claim).
- **Datadog MCP Server** — Datadog's observability interface for AI agents; NL access to metrics/logs/traces without Datadog query syntax. 47→197 tools; ~83 products/tool-sets. [datadoghq.com/product/ai/mcp-server]
- **Bits AI** — Datadog's AI product; Yak runs it as a daily background bug-sweep on the MCP server's own logs (root-cause + fix PR). ("bits code" in ASR.)
- **agentgateway** — Solo.io's AI-native proxy that speaks MCP/A2A natively; where Levan says security enforcement belongs. [solo.io]
- **kagent** — agent framework integrated with agentgateway (Levan's demo stack). CNCF-adjacent.
- **Agent Mesh (Solo.io)** — service-mesh concept extended to agents: workload/agent identity via SPIFFE, enforced in an ambient (Istio) mesh. [solo.io/blog/from-service-mesh-to-agentic-mesh]
- **SPIFFE / SPIRE** — workload-identity standard/runtime; agent gets a SPIFFE ID from its Kubernetes service account ("SPNE go ID" in ASR = SPIFFE ID). [enrichment]
- **Istio / ambient mesh / mTLS** — service-to-service security substrate Levan maps onto agents.
- **CEL (Common Expression Language)** — the policy language Levan uses to scope which agent may hit which tool/server.
- **OBO (On-Behalf-Of) / token exchange / STS** — an agent acts with a user's permissions (or its own) via a token with a claim, obtained from a secure token service at the gateway.
- **ABAC / ReBAC** — attribute-based (e.g., "9am–5pm from NJ → root access") and relationship-based access control; Levan's runtime-authZ toolkit. Kyverno / OPA-style policy enforcement.
- **Agent identity** — the identity of *the agent* (vs. user or service) and, more importantly, what that identity is permitted to *do*.
- **Tool isolation** — exposing only a permitted subset of a server's tools to a given agent/user (security + token cost).
- **AAIF (Agentic AI Foundation)** — nonprofit under the Linux Foundation; per Angie on stage, founded by Anthropic, OpenAI, and Block (**Rule 12 — verify before public assertion**). Runs the six-city party series, AgentCon/MCPCon (San Jose, October), and the first official MCP certification (in beta). aaif.io/events.
- **Agentic Conversations** — AAIF podcast led by Demetrios (MLOps Community). Angie's colleague.

## 13. Tools / Companies Mentioned

| Name | What it is | Context in the room |
|---|---|---|
| **Block** | Fintech; Hancock's employer, Goose's origin | Goose donated to Linux Foundation; AAIF co-founder (per Angie) |
| **Datadog** | Observability platform | Host/sponsor; Yak's MCP-server case study |
| **Solo.io** | Cloud-native networking / AI gateway | Levan's employer; agentgateway/kagent/Agent Mesh |
| **Anthropic** | MCP's origin; AAIF co-founder (per Angie) | Referenced re: reference implementation, Claude |
| **OpenAI** | AAIF co-founder (per Angie); Codex | Codex on the Rust SDK (Hancock, Rule 12) |
| **Goose** | Open-source MCP client/agent harness (Block) | First-ish MCP client; Hancock core-maintains |
| **GitHub Copilot / Codex** | Coding agents | Both now on the MCP Rust SDK (Hancock, Rule 12) |
| **Claude Code / Claude Desktop** | Anthropic clients | Yak's demo host; MCP Apps support |
| **ChatGPT** | OpenAI client | MCP Apps support |
| **Coinbase (x402)** | Payments protocol | MRTR's structural twin (audience) |
| **Linux Foundation** | Open-source foundation | Parent of AAIF; Goose + MCP + x402 governance |
| **AAIF** | Agentic AI Foundation | Organizer; events + MCP cert |
| **MLOps Community** | Demetrios's community | Runs the AAIF "Agentic Conversations" podcast |
| **Istio / SPIFFE / SPIRE / kagent / Kyverno** | Cloud-native security stack | Levan's agent-mesh demo |

## 14. Stat Bank (numbers as claimed — no invented precision)

| Stat | Value | Speaker | Confidence / caveat |
|---|---|---|---|
| Party series | 6 cities: NY (sold out), SF ×2 (sold out), Austin, Seattle, London, Amsterdam | Angie | HIGH |
| Datadog MCP tool growth | **47 → 197** tools | Yak | HIGH |
| Datadog products / tool-sets | ~**83** | Yak | HIGH |
| Tool-call traffic growth | **>10×** over ~5 months | Yak | HIGH |
| Error-diagnosis share of sessions | **>50%** | Yak | HIGH |
| `initialize` calls | **more than** tool calls (inefficiency) | Yak | HIGH |
| Tool timeout | **60 seconds** | Yak | HIGH |
| Unauthorized MCP write | returns **403** | Yak | HIGH |
| Over-large token request example | agents ask for **~50,000** tokens they don't need | Yak | HIGH (illustrative) |
| Recommended tools exposed to an agent | **~15–18** before hallucination/token cost climbs | Levan | HIGH |
| Agents-per-org anecdote | **"40 agents running, don't know what half do"** | Levan (citing a Reddit post) | MED — third-party anecdote, not a measured stat |
| Hancock tenure at Block | **10 years** | Hancock | HIGH |
| Goose age | **~2 years** | Hancock | HIGH |
| Rust SDK version | **3.0** (merged live) | Hancock | HIGH |
| AAIF event | AgentCon/MCPCon, **San Jose, October**; code `meetup15` = 15% off | Angie | HIGH |

## 15. Documentarian Angles (cuts available for future content)

- **PRIMARY — "The spec closed the scaling gap and opened the authorization gap in the same release."** The pre→post confirmation post: infrastructure win landed as predicted; both operator talks put the frontier exactly where the pre-event brief called it (runtime authZ scope + evals). Alex's operator voice, three named speakers, one thesis. **Highest value.**
- **ALT 1 — Per-talk deep post: "What running a 197-tool MCP server actually taught Datadog."** Yak's org-scaling story (monolith → distributed, context-as-commons, eval-authoring bottleneck, agents-outnumber-humans). Operator-grade, stat-rich.
- **ALT 2 — Per-talk deep post: "The authorization gap nobody's closing."** Levan's gateway thesis — server-as-black-box, agent identity, ~15–18-tool ceiling, ABAC/ReBAC, secure-the-response-path. Security-audience cut.
- **ALT 3 — "MCP went stateless — here's what that actually fixes."** Hancock's accessible explainer: stateful-behind-a-load-balancer pain → self-contained requests; MRTR ≈ x402; Tasks/Apps as the first two extensions. Define-jargon-inline cut for the developing audience.
- **SYNTHESIS candidate** — pair this with any recent event whose thesis is "the protocol/infra layer is solved, the governance/enforcement layer isn't." Two-thesis format (max 1/week).
- **Thank-the-speakers beat (memory rule):** name and thank Angie Jones (host), Alex Hancock, Scott Yak, Michael Levan; credit Datadog (venue) + AAIF (organizer).

## 16. Open Loops & Verification Flags

**Rule-12 items — do NOT assert publicly without independent source:**
- **AAIF "founded by Anthropic, OpenAI, and Block"** (Angie, on stage) — an org-structure claim; verify before printing as fact. (Enrichment supports AAIF-under-Linux-Foundation and MCP donation Dec 2025; the specific three-founder claim should still be sourced.)
- **"Goose was the first MCP client to hit the market" / "reference implementation"** (Angie) — firm-positioning claim; Hancock himself softened to *"one of the first."* Use "one of the first."
- **"Codex and Copilot are now both using the Rust SDK"** (Hancock) — external claim about other companies' products; attribute to Hancock, verify before stating as fact.
- **Datadog's own numbers** (47→197 tools, >10×, 83 products, 60s timeout) — primary source (Yak on his own employer); safe to attribute to Yak, fine to quote.

**Follow-ups / content ops:**
- Confirm final spelling/title for **Michael Levan** (transcript "Levin") before any @-tag — canonical **Levan**, Solo.io (enrichment-confirmed).
- The low-confidence audience-member ("possibly Alex Hancock" at 54:13) — do NOT tag anyone on those questions.
- Excluded-garble entities (§ Conditioning Notes) must never reach a public post.
- Photos not OCR'd — if a slide quote is needed, open the specific frame first.

## 17. Enrichment Resolutions (Step 3.6 — what the pass resolved/corrected)

- **"Angie" → Angie Jones**, VP Developer Experience at AAIF, ex-Global VP Developer Relations at Block (led AI-agent rollout to ~12,000 employees), Test Automation University founder, first Black woman Java Champion. This resolves the MC identity and explains the Block/Goose/AAIF through-line. She is a *third host* (the MC), distinct from the pre-event roster's Lahari Chowtoori / David DeStefano (community organizers, non-speaking). [linkedin.com/in/angiejones · aaif.io/author/angie-jones]
- **Michael Levan (canonical spelling; transcript "Levin")** — AI Architect / Principal Solutions Engineer, Solo.io; Microsoft MVP, CNCF Ambassador, Kubernetes release-team alum. Confirms auth-gap talk provenance. [linkedin.com/in/michaellevan · solo.io]
- **Scott Yak** — Datadog, "Applied AI (MCP services)"; works on the Datadog MCP server. Confirms Talk 2 attribution. [linkedin.com/in/scottyak]
- **x402** — Coinbase HTTP-402 payments protocol (audience's MRTR comparison confirmed real, not garble). [github.com/coinbase/x402]
- **agentgateway / kagent / Agent Mesh / SPIFFE** — Solo.io's AI-gateway + agent-identity stack (Levan's demo); "SPNE go ID" = SPIFFE ID. [solo.io]
- **David Soria Parra + Justin Spahr-Summers** — MCP co-creators at Anthropic ("David and Justin" in Hancock's talk); DSP in London (couldn't attend). [anthropic.com]
- **MCP Apps = SEP-1865, Tasks = SEP-2663, Extensions framework = SEP-2133**; the 2026-07-28 release is the RC of the largest spec change since launch. Hancock's "SEP-2322" = the MRTR proposal. [blog.modelcontextprotocol.io]
- **Demetrios** (transcript "Dimitrios") — MLOps Community, leads AAIF's "Agentic Conversations" podcast. Matches pre-event roster.
- **RULE-12 trap AVOIDED:** the pre-event brief warned that the "10 tool-poisoning attacks, 6 got through" study is **Rock Lambros's**, not Levan's. **Levan did not cite those numbers on stage** — no tool-poisoning stat appears in his talk. Do not attribute it to him. (His only numeric heuristics: ~15–18 tools, and the third-party "40 agents" Reddit anecdote.)
- **UNRESOLVED / low-confidence (excluded from public copy):** "Gloom" (a third MCP-Apps-supporting client Scott named — candidates: Glama or Goose; flagged low-conf, cut); "Preacher" (Datadog free credits "for Preacher" — likely "teachers," low-conf, cut); "BizChat/BizInvestigation" (Datadog internal first-party agent names — uncertain, don't over-assert).

## 18. — see §17 (Enrichment Resolutions) —

---

## Operational sub-sections (pipeline plumbing)

### Slides / Photos Catalog (12 — cataloged by filename + timestamp; NOT OCR'd)

Source: `~/Library/CloudStorage/GoogleDrive-alex.e.yedi@gmail.com/My Drive/(Owned) Professional /Events/MCP Release Party 07 28 26/`. Filename timestamps are UTC; EDT = UTC−4. Talk mapping is inferred from transcript timing, not confirmed by OCR.

| File | UTC | ~EDT | Inferred moment |
|---|---|---|---|
| PXL_20260728_221252232.jpg | 22:12:52 | 18:12 | Alex Hancock talk (statelessness) |
| PXL_20260728_221441205.jpg | 22:14:41 | 18:14 | Alex Hancock talk |
| PXL_20260728_221856653.jpg | 22:18:56 | 18:18 | Alex Hancock talk (MRTR/elicitation) |
| PXL_20260728_222259074.jpg | 22:22:59 | 18:22 | Alex Hancock talk (extensions/Tasks) |
| PXL_20260728_222346372.jpg | 22:23:46 | 18:23 | Alex Hancock talk |
| PXL_20260728_224313717.MP.jpg | 22:43:13 | 18:43 | Scott Yak / Datadog talk |
| PXL_20260728_224846701.MP.jpg | 22:48:46 | 18:48 | Scott Yak / Datadog talk (scaling stats) |
| PXL_20260728_225149116.MP.jpg | 22:51:49 | 18:51 | Scott Yak / Datadog talk (distributed arch) |
| PXL_20260728_225308805.jpg | 22:53:08 | 18:53 | Scott Yak / Datadog talk |
| PXL_20260728_230857630.MP.jpg | 23:08:57 | 19:08 | Michael Levan / Solo.io talk (auth/gateway) |
| PXL_20260728_230933949.jpg | 23:09:33 | 19:09 | Michael Levan talk (agent identity) |
| PXL_20260728_231150004.jpg | 23:11:50 | 19:11 | Michael Levan talk (demo) |

Also present: `Jul 28 at 18-05.m4a` (40 MB source recording), phone-ASR transcript, ElevenLabs transcript (`event-transcripts/mcp-release-el/`).

### People & Outreach State

Outreach is **OPT-IN** (v2 rule) — none flagged by Alex for this event → **outreach skipped**. State captured for the graph + future re-engagement:

| Person | Role | Bucket | Spoke? | Next action |
|---|---|---|---|---|
| Angie Jones | Host / MC; VP DevEx, AAIF (ex-Block) | A (high-value connector) | Yes (MC) | None auto — candidate thank-you connect if Alex opts in |
| Alex Hancock | Block / Goose / MCP Rust SDK | A | Yes (Talk 1) | None auto — strong follow candidate |
| Scott Yak | Datadog, Applied AI (MCP) | A | Yes (Talk 2) | None auto |
| Michael Levan | Solo.io, AI Architect | A | Yes (Talk 3) | None auto — explicitly invited connects in his Q&A |
| Lahari Chowtoori | AAIF NY organizer | C | No | None |
| David DeStefano | AAIF NY organizer | C | No | None |
| Audience Q&A members | — | D | Q&A only | None (unnamed) |

### Content Assets Produced

_(fill after Step 4/5)_ — Tier-2 post(s) + visual carousel brief → Gamma; Notion Content Draft URLs; comment.

### Conditioning Notes

- **Speaker resolution table:** § 4 above (+ full version in `quote-bank.md`).
- **Entity normalization glossary:** in `quote-bank.md` (mangled → canonical map).
- **⚠️ Excluded-garble list (never quote verbatim, never print as a proper noun):** `Gloom` (57:25, MCP-Apps client — candidates Glama/Goose, unresolved); `Preacher` (50:15, Datadog credits — likely "teachers"); `Kylie` (Angie's intro of Hancock — likely "colleague," consistent across both ASR passes); `BizChat`/`BizInvestigation` (uncertain Datadog internal agent names); plus the 20 REVIEW low-confidence words (`the`, `things`, `building`, `pour`, `shit`, `some`, `to`, `of`, `this`, `merge`, `Go`, `keep`, `pivot`, `timelines`, `Cloud`, `Gloom.`, `AM`, `called`, `AM`, `community.`) — substance may be used, exact word must not be quoted.
- **Conditioning confidence score:** **~93%.** ElevenLabs scribe_v2 transcript is high fidelity (20 low-confidence words / 17,262 = 99.9% clean), speaker resolution is content-anchored and cross-checked against the phone-ASR pass + web enrichment. Down-weighted: (a) audience-member attribution during Q&A (kept generic); (b) the single low-confidence audience question at 54:13 (possible Alex Hancock, unconfirmed); (c) three excluded garbles above. The three main speakers are HIGH-confidence; every verbatim quote proposed is drawn from clean spans.
