# Quote Bank — MCP Release Party (2026-07-28)

**Drafting handoff (content-correspondent Mode B input).** Every quotable line, attributed to the resolved speaker, tagged **HIGH** (verbatim-safe) or **MED** (paraphrase only, do not quote verbatim). Source: ElevenLabs scribe_v2 transcript (`event-transcripts/mcp-release-el/`). Conditioning confidence **~93%**.

> **HARD GATE (YED-96 R3):** a quote may be used verbatim in a draft that @-tags a person ONLY if it is HIGH. MED / excluded-garble → paraphrase, drop the tag, or exclude. Never print an excluded-garble entity.

---

## Speaker Resolution Table

| Raw label | Person | Affiliation | Tell | Confidence |
|---|---|---|---|---|
| speaker_0 | **Angie Jones** | MC/host — VP DevEx, AAIF; ex-Global VP DevRel, Block | Thanked as "Angie" (04:14); "little Angie discount" (95:55) | HIGH |
| speaker_1 (Talk 1, 04:05–32:13) | **Alex Hancock** | Block; MCP Rust SDK; Goose core maintainer | "software engineer at Block... ten-year mark... Rust SDK... Goose" | HIGH |
| speaker_1 (22:48 question part) | **audience member** (merged with Alex's answer) | — | diarization merge | HIGH (it's a merge) |
| speaker_1 (54:13/55:31/56:03) | **audience member — possibly Alex Hancock, UNCONFIRMED** | — | same voice cluster, no self-ID | LOW — do not tag |
| speaker_5 | **Scott Yak** | Datadog, Applied AI (MCP services) | "my name is Scott... software engineer at Datadog... I work on the MCP server" | HIGH |
| speaker_7 | **Michael Levan** | Solo.io, AI Architect | "I work at Solo as an AI architect"; introduced as "Michael Lev[an]" | HIGH (spelling: Levan, not "Levin") |
| speaker_2/3/4/6 | **audience Q&A members** (unnamed) | — | distinct questioners, no names stated | generic |

**Non-speaking roster:** Lahari Chowtoori, David DeStefano (AAIF NY organizers — thanked generically, never named on-mic; do not attribute quotes).

---

## Entity Normalization Glossary (mangled → canonical)

| ASR rendering | Canonical | Note |
|---|---|---|
| mCP / FCP | **MCP** | Model Context Protocol |
| Cloud Code / CloudCode / Call Code / quad code | **Claude Code** | |
| Cloud Desktop | **Claude Desktop** | |
| Androphic | **Anthropic** | |
| David and Justin | **David Soria Parra & Justin Spahr-Summers** | MCP co-creators |
| DSP | **David Soria Parra** | in London, didn't attend |
| Xora two / XOR two / Xora | **x402** | Coinbase HTTP-402 payments protocol |
| SEP | **Specification Enhancement Proposal** | Hancock's "SEP-2322" = MRTR |
| MRTR | **Multi-Round Trip Request** | |
| Russ SDK / Rust SDK | **Rust SDK** | went to 3.0 live |
| edals / au- edals | **evals** | Scott's per-tool evals |
| bits code | **Bits AI** | Datadog product (daily bug-sweep) |
| Dimitrios | **Demetrios** | MLOps Community, AAIF podcast |
| Michael Levin | **Michael Levan** | Solo.io |
| Solo | **Solo.io** | agentgateway / kagent |
| SPNE go ID / SPNE ID | **SPIFFE ID** | workload identity |
| K-agent | **kagent** | agent framework |
| CEL | **Common Expression Language** | (correct as spoken) |
| OBO | **On-Behalf-Of** | token exchange |
| STS | **Secure Token Service** | ("secure token server" as spoken) |
| Istio, Spire, Kyverno, Entra, Okta, Keycloak | (as spelled) | Levan's stack |
| aaif.io / aeiya | **AAIF (Agentic AI Foundation)** | |
| AgentCon / MCPCon | **AgentCon / MCPCon** | San Jose, October |

### ⚠️ EXCLUDED GARBLE — never quote verbatim, never print as a proper noun
- **`Gloom`** (57:25) — a third MCP-Apps-supporting client Scott named; candidates: **Glama** or **Goose**; unresolved → cut.
- **`Preacher`** (50:15) — Datadog "free credits for Preacher"; likely **"teachers"** (education credits); low-conf → cut.
- **`Kylie`** (Angie's Hancock intro, both ASR passes) — likely **"colleague"**; do not print "Kylie."
- **`BizChat` / `BizInvestigation`** — uncertain Datadog internal first-party agent names; don't over-assert.
- The 20 REVIEW low-confidence words (see `… — REVIEW (low-confidence spots).md`) — substance OK, exact word not verbatim.

---

## QUOTE BANK

### Angie Jones (MC / host — AAIF, ex-Block)

- **HIGH** — *"I've also worked in open source for a long time, and I have not seen a community that's as active and as vibrant as the MCP community... I just go in there sometimes, and I just smile. It's just like busy bees."*
- **HIGH** — *"Big shout out to Datadog for hosting us."*
- **HIGH** (on-the-spot bit) — *"Well, it works on Alex's machine."*
- **HIGH** — *"Because it's a live demo."* (deadpan, during Levan's failed connect)
- **HIGH** — *"I insisted that there must be cake if we're gonna have a party."*
- **HIGH** — *"We agreed to be great guests... We are guests in their home. We're gonna clean up behind ourselves."*
- **MED** (org claim → Rule 12) — AAIF is *"a nonprofit under Linux Foundation, founded by Anthropic, OpenAI, and Block, [that] has created the first official MCP certification."* Verify the three-founder claim before public use.
- **MED** (firm-positioning → Rule 12) — Goose was *"the first MCP client to hit the market"* / *"the reference implementation."* Hancock softened to "one of the first" — use that.

### Alex Hancock (Block / Goose / MCP Rust SDK) — Talk 1

- **HIGH** — *"I just crossed the ten-year mark the other day at Block."*
- **HIGH** — *"I'm also a core maintainer of the Goose project, which is an open source agentic harness that was one of the first MCP clients... we donated it to the Linux Foundation last year."*
- **HIGH** (release framing) — *"More and more of the usage of MCP is going to that remote use case where the client and the server are on different machines, which means that the semantics of the protocol need to change to make that work better. This is the thing that is motivating almost all of the changes in this new version."*
- **HIGH** — *"Statelessness — this is the big marquee change in this version."*
- **HIGH** — *"What it really means for the protocol to be stateless is that every request has the information that it needs for the server to handle it included in the request. So now there is no initialize anymore. There is no session anymore."*
- **HIGH** — *"You can do the very normal thing, like putting a load balancer out there, putting some auto-scaling pool of servers to handle high load. And any request from the client at any point can just go to any of those nodes."*
- **HIGH** (old-world pain) — *"You either had to pin... which causes problems where you wanna be able to cycle that fleet out... Or people would start to store the shared session information in something that all the nodes could access. But that's like an additional architectural component you have to set up."*
- **MED** (the deprecation joke — "pour" is a flagged low-conf word) — *"let's pour one out for roots, sampling, and logging."* Paraphrase: he waved goodbye to roots, sampling, and logging (deprecated this release); said he'd miss sampling.
- **HIGH** — *"With this new protocol version being cut, MCP Apps landed as the first extension... and there's another new one that just landed, for doing tasks."*
- **HIGH** (Tasks) — *"Tasks give you the ability to have tool calls do something that is asynchronous and potentially long-running... a database migration... or kick off a workflow that needs a human in the loop... it might even be over multiple days."*
- **HIGH** — *"Anything that takes a long time is a valid use of tasks."*
- **HIGH** (MRTR) — *"Your multi-round-trip request is gonna be something you hear a lot about in MCP going forward... every time information is needed from the client back to the server, the server just responds with a result indicating that."*
- **HIGH** (SDK recommendation) — *"All of the SDKs for MCP have gotten really good... our hope is that the SDKs make it easier for everybody building out there to just have a lot of it abstracted away."*
- **HIGH** — *"If you were writing an MCP program and you were handling messages yourself... you're gonna have to do a lot of work to do this upgrade, because we had to do a lot of work in the SDKs."*
- **HIGH** (Rust SDK) — *"The Rust SDK is now three point zero — or it will be after I merge the PR. It has to be today."*
- **HIGH** (Rule 12 — external claim) — *"Codex and Copilot are now both using the Rust SDK... a number of projects are coalescing onto the same SDKs."*
- **HIGH** (answering x402 comparison) — *"That is a fantastic observation. I agree. It is very similar to x402... they're very similar shapes... All these ideas I'm presenting came from community members, other maintainers."*
- **HIGH** (context-window pro-tip) — *"You wanna be a little bit careful as it starts to grow... you can look at the old pairs of tool-call requests and responses and slim those down... shunt that out to a file... 'if you need to know what this full result was, you can read it at this file path.'"*

### Scott Yak (Datadog) — Talk 2

- **HIGH** — *"You send us metrics, traces, errors... observability data about your service, and we provide the tools to help you figure out whether your service [is] running as expected."*
- **HIGH** (value) — *"Today, you can just ask your agent because you have the MCP server... this is all in natural language, so you don't actually need to know any syntax."*
- **HIGH** (the thesis line) — *"Monolithic MCP servers don't scale organizationally."*
- **HIGH** — *"More than fifty percent of our sessions are for diagnosing errors."*
- **HIGH** (self-hosting ops) — *"We are generating the daily reports from our server logs... So we can use the MCP server to help us debug our MCP server."*
- **HIGH** (Bits AI bug-sweep) — *"We have it running in the background on a daily, and so I can have a PR to review... without me having to actually write the code myself."*
- **HIGH** (scale) — *"The number of tools have grown from forty-seven to hundred and ninety-seven, and it's gonna grow even more."*
- **HIGH** — *"The number of products... has grown to about eighty-three."*
- **HIGH** (the bottleneck) — *"Every time one of these eighty-three teams want to change the tool description... we have to review the code, and it becomes a bottleneck."*
- **HIGH** (shared-commons framing) — *"Because the context is a shared resource, it's a shared commons. If one tool is very inefficient with tokens in their tool description, it will affect everyone else when the client does the list tools."*
- **HIGH** (the pain, first person) — *"We get paged when [a] tool fails and exceeds a certain threshold. And so imagine with two hundred something tools, what kind of experience that is like."*
- **HIGH** (the fix) — *"We are going to migrate to a distributed system... the individual product teams are gonna own their own MCP server... but without actually exposing a separate URL. So you just talk to Datadog's MCP URL as if it is just a single MCP server."*
- **HIGH** (the north star) — *"We think about running an MCP server just like the way we think about running an HTTP server. It becomes a boring technology... rather than being something that is your full-time job."*
- **MED** (evals — ASR "edals") — substance: *"we cannot be the ones creating the evals for all the tools... we need to figure out how to scale up the eval authoring as well."* Paraphrase the phrasing.
- **HIGH** (initialize inefficiency) — *"The number of initialized calls [is] actually more than the number of tool calls, which is quite inefficient... when people open their laptops, it just makes an initialize call without ever making a tool call."*
- **HIGH** (token cost) — *"When we read a lot of tokens or we write a lot of tokens, it doesn't actually cost us anything. But for the LLMs, it will cost the MCP host a lot."*
- **HIGH** (max_tokens pitfall) — *"Sometimes the agents will ask for fifty thousand tokens, and we are just like, why do you ever want fifty thousand?... it feels like max tokens is probably not enough."*
- **HIGH** (agents vs humans — answering audience) — *"We suspect that they are agents, but we need to verify."*
- **HIGH** (security scopes) — *"When you first auth into the MCP server, it will ask you to check what auth scopes you are allowed... you can toggle whether you are allowing MCP read or MCP write."*
- **HIGH** — *"If an agent tries to do an MCP write when they only have MCP read scope, it will show up as a four zero three."*
- **HIGH** (observability gap) — *"When we see an MCP session, all we know is the tool calls you make, but we don't know the context in which you are giving us the tool-call request. So it does make it a bit challenging to reconstruct what the user is trying to do."*

### Michael Levan (Solo.io) — Talk 3 ("The Authorization Gap Nobody's Closing")

- **HIGH** (thesis) — *"A new protocol, a new spec — that means there's going to be a new attack surface. And this new attack surface means there's going to be new threats."*
- **HIGH** — *"The biggest thing that I'm always thinking about, from a security perspective, is mitigating as much risk as you possibly can — because you're never gonna mitigate everything."*
- **HIGH** — *"We always have to think about security in terms of: something will happen at some point. If it doesn't, you're incredibly lucky."*
- **HIGH** (the gateway thesis) — *"Nine point nine nine nine times out of ten... [security] is a gateway... whatever that line of communication is in the middle, this is where security is gonna be implemented. You're talking auth, you're talking guardrails, you're talking rate limiting, you're talking OBO, you're talking OIDC-based OAuth."*
- **HIGH** (secure the response) — *"You're very rarely thinking about the response... this is a constant line of communication... you're constantly getting responses back, and you need to secure that as well, because the attack vector could be going from point B to point A."*
- **HIGH** (tool-count ceiling) — *"I believe the number is still between like fifteen and eighteen tools that you want exposed to your agent. Outside of that, you can come up with more and more hallucinations... a higher level of input tokens."*
- **HIGH** (input-token cost of tools) — *"As your agent is consuming MCP server tools, it's also consuming all of the metadata from those tools... 'I've already spent thousands of tokens before my first input request. Why is that?' Well, it could be because your agent is ingesting a whole bunch of tool descriptions."*
- **HIGH** (agent identity) — *"In this new world, it's not just the identity of a service... it's the identity of ten, twenty, thirty, forty, a hundred agents running. Now, more importantly, what the agent can do."*
- **HIGH** (the Reddit anecdote — attribute as a cited post, NOT his metric) — *"I saw this Reddit post... 'We have forty agents running, and we don't know what half of them do anymore.'"*
- **HIGH** (identity vs name) — *"You may be thinking, 'Can't I just have an expression that specifies the agent name?' You could, but the agent name can change. The workload identity can't."*
- **HIGH** (auth in one line) — *"You log into something, that's authentication. What you have the ability to do once you're logged in, that's authorization."*
- **HIGH** (the black-box argument) — *"An MCP server as a whole is like this black box... you can't do anything. You can pen test it, but... So what you have to do is, instead of putting that onus on the MCP server, take that a step back and put those decisions in your gateway."*
- **HIGH** (why gateway over harness) — *"Somebody goes into my open code configuration and says 'you have to go through this gateway.' Well, I could just take that out... But if you have your policies at the gateway level, and you're setting policies for all agents, all harnesses to go through that gateway, everything's gonna always be automatically stopped right there."*
- **HIGH** (ABAC example) — *"I live in New Jersey, therefore my working hours are nine AM to five PM. During those hours, I have root-level access to any Kubernetes cluster... but before nine AM and after five PM, I do not have access based on my geographical location — which is attribute-based access control in a nutshell."*
- **HIGH** (built-in-the-Uber) — *"This is just something that I finished up on the way here."* / *"I literally finished it on the Uber ride here."*
- **HIGH** (LLM-as-approver Q) — *"That should happen before it even gets to the LLM for the LLM to make a decision... this policy is gonna be kicked off way before the LLM has to make any type of decision."*

### Audience (attribute generically — "an audience member")

- **HIGH** (x402 catch — speaker_2) — *"This looks very similar to the x402 standard, which is a machine payment protocol. Was it inspired by it, or did you independently arrive at that conclusion?"*
- **HIGH** (agents-or-humans — speaker_4) — *"Fun question: is your larger user today an agent or a human? And when do you think that flip will happen?"*
- **HIGH** (multi-client data policy — speaker_3, Levan Q&A) — *"You're the Department of Health. You have Claude... and ChatGPT... Claude is allowed to access health data, ChatGPT is not... As an MCP server provider, how do you establish confidence in who the client is such that you can be thoughtful about what data you're returning?"*
- **HIGH** (the "Nigerian prince" line — speaker_3) — *"Say you have one [agent] doing transactions. [It] should obviously know not to give some Nigerian prince five hundred thousand dollars."* (memorable audience color)
