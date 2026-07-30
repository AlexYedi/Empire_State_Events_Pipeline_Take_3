# Post-Event Drafts — MCP Release Party (2026-07-28, NYC)

> Step 4 of `/post-event-content`. Source of truth: `post-event-brief.md` + `quote-bank.md`.
> Ship ALL variants to Notion for comment-based iteration. Sources go to the FIRST COMMENT, never inline.
> Quote-safety: every verbatim quote below is drawn from a HIGH-tagged line in the quote bank. MED lines are paraphrased. No @-tags recommended in copy (Alex tags manually cross-platform).

---

## PRIMARY POST — Variant A (explainer cut) · 2,376 / 3,000

**Content Type:** `linkedin_post` · **Event Phase:** `post_event` · **Goal (suggested):** reach / engagement (documentarian recap)

On Monday night, the largest revision to the Model Context Protocol since launch shipped as a release candidate while the room watched. MCP is the standard that lets AI agents talk to tools and data. The release fixed the thing everyone building at scale was waiting for. It also made a quieter problem impossible to ignore.

Three engineers, three talks, one arc.

Alex Hancock (Block, maintainer of MCP's Rust SDK and the Goose agent) opened with the headline: "Statelessness — this is the big marquee change in this version." In plain terms: every request now carries everything the server needs to answer it. "There is no initialize anymore. There is no session anymore." Before, a server had to remember your connection, like a barista holding your tab, which meant you couldn't freely cycle servers behind it. Now any request can hit any server. Put a normal load balancer and an autoscaling pool in front, and it works. That is the infrastructure win, delivered on release day.

Then Scott Yak (Datadog) showed what that scale costs. Not in compute, in people. Datadog's MCP server grew from 47 tools to 197 in months, across roughly 83 product teams. "Monolithic MCP servers don't scale organizationally." "The context is a shared commons": one team's bloated tool description taxes everyone else's. His fix is to let each team own its own server behind a single shared URL, so no one team is on call for 200 tools.

Michael Levan (Solo.io) closed on the gap the spec still doesn't cover. "A new protocol, a new spec — that means there's going to be a new attack surface." The release added authorization improvements, but what an agent is allowed to actually do once it's authorized still isn't solved in the spec. His argument: the MCP server is a black box you can't secure from the inside, so enforcement has to move one step earlier, to the gateway that every request passes through. That, he says, is where security gets implemented "nine point nine nine nine times out of ten."

The spec closed the scaling gap and opened the authorization gap in the same release. The infrastructure is now boring, in the best way. What an authorized agent may do next is the frontier.

Thanks to Angie Jones for hosting, and to Alex Hancock, Scott Yak, and Michael Levan for the talks. To Datadog for the room and AAIF for the series.

#MCP #AIAgents #AgenticAI #CloudSecurity

---

## PRIMARY POST — Variant B (operator cut) · 2,227 / 3,000

**Content Type:** `linkedin_post` · **Event Phase:** `post_event` · **Goal (suggested):** reach / engagement (technical audience)

MCP went stateless on Monday, shipped as a release candidate mid-party. If you run agents against tools at scale, this is the release you were waiting for. It also quietly relocated the hard problem.

The arc across three talks:

Alex Hancock (Block; MCP Rust SDK; Goose) framed the change. "Statelessness — this is the big marquee change in this version." No initialize, no session. Every request is self-contained, so any request routes to any node. Standard load balancer, autoscaling pool, no sticky sessions, no shared session store. Remote-first MCP finally admitting it is remote-first.

Scott Yak (Datadog) showed the bill. 47 tools to 197 in months. Roughly 83 product teams. Traffic up more than 10x. The wall isn't compute, it's ownership: "Monolithic MCP servers don't scale organizationally." When "the context is a shared commons," one team's sloppy tool description taxes every other team's tool list. His answer is distributed servers, per-team owned, behind one URL, so the platform team stops being the review bottleneck for 200 tools it doesn't own.

Michael Levan (Solo.io) named what the spec left open. "A new protocol, a new spec — that means there's going to be a new attack surface." Authentication is who you are. Authorization is what you can do once you're in. The release improved the former. The latter (tool isolation, agent identity, what an agent is scoped to actually do) lives at the gateway, not the server. Why not the server? It's a black box: you can pen test it, but you can't enforce policy inside it. So you move enforcement one step back, to the gateway every call already crosses. He would cap tools exposed to any agent at 15 to 18; past that, hallucinations and token cost climb.

Read the three together and the release rewrites the job. Scaling MCP is now plumbing. The open work is governance: what an authorized agent is allowed to do next, and keeping that honest as the tool count keeps climbing. The spec closed the scaling gap and opened the authorization gap in the same release.

Thanks to Angie Jones (host), Alex Hancock, Scott Yak, and Michael Levan for the talks, Datadog for the venue, and AAIF for running the series.

#MCP #AIAgents #AgenticAI #PlatformEngineering

---

## PRIMARY POST — First Comment (sources) · applies to A or B

Resources from the MCP Release Party (NYC), hosted by the Agentic AI Foundation at Datadog:

- MCP 2026-07-28 release candidate (the largest spec revision since launch): blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- What MCP is: modelcontextprotocol.io
- New extensions referenced: MCP Apps (SEP-1865), Tasks (SEP-2663), Extensions framework (SEP-2133) — github.com/modelcontextprotocol
- Goose (Block's open-source agent, one of the first MCP clients): block.github.io/goose
- Datadog MCP Server: datadoghq.com/product/ai/mcp-server
- Solo.io agentgateway (where Levan argues security belongs): solo.io
- AAIF events + the six-city party series: aaif.io/events

---

## ALT DEEP-CUT — Scott Yak / Datadog ("What running a 197-tool MCP server taught Datadog") · 2,295 / 3,000

**Content Type:** `linkedin_post` · **Event Phase:** `post_event` · **Goal (suggested):** reach / engagement (operator/platform audience) · net-new material vs. pre-event brief

Datadog's MCP server grew from 47 tools to 197 in a few months, with traffic up more than 10x. (MCP is the standard that lets an AI agent call your tools in plain language, no query syntax required.) At the MCP Release Party, Scott Yak, an engineer on that server, gave the most honest operator talk of the night: the thing that broke first wasn't the infrastructure. It was the org chart.

"Monolithic MCP servers don't scale organizationally."

The mechanism: those 197 tools come from about 83 product teams. When every team ships tools through one server, the platform team owns the review for all of them. "Every time one of these 83 teams wants to change a tool description, we have to review the code, and it becomes a bottleneck." And the model's context window is finite and shared. As Yak put it, "the context is a shared commons": one team's bloated tool description costs every other team tokens on every tool list. Reading and writing those tokens is free for Datadog, but not for the agent calling in. That cost lands on whoever runs the model.

A few numbers that reframe what an MCP server even is:
- More than 50% of sessions are diagnosing errors, not querying dashboards.
- More initialize calls than tool calls. IDEs auto-connect on laptop-open and handshake without ever calling a tool.
- Agents routinely request around 50,000 output tokens they don't need.

The fix is architectural. Move to distributed servers: each product team owns its own MCP server, all behind one URL, so a caller still sees "Datadog's MCP server" but no single team is paged for 200 tools it doesn't understand. The goal Yak named is the tell: run an MCP server "just like the way we think about running an HTTP server. It becomes a boring technology" instead of someone's full-time job.

The unglamorous frontier he surfaced: evaluations. Datadog authors tests per tool to keep them honest, but as tools multiply, the team that owns the server can't write the evals for everyone else's tools. Scaling the eval authoring is the next bottleneck, and nobody has solved it yet.

Boring infrastructure is the goal. Getting there is still very much applied engineering.

Thanks to Scott Yak for the talk, Datadog for hosting, and AAIF for the series.

#MCP #AIAgents #PlatformEngineering #Observability

---

## ALT DEEP-CUT — First Comment (sources)

From Scott Yak's talk at the MCP Release Party (NYC), hosted by the Agentic AI Foundation at Datadog:

- Datadog MCP Server: datadoghq.com/product/ai/mcp-server
- MCP 2026-07-28 release candidate: blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- What MCP is: modelcontextprotocol.io
- AAIF events: aaif.io/events

_(Note: all figures — 47→197 tools, ~83 teams, >10x traffic, >50% of sessions diagnosing errors — are Datadog's own numbers, as stated by Yak on stage about his own team's server.)_

---

## Visual Brief — 5-slide carousel (Arc 3: Before → After → What Changed → So What)

**For:** the PRIMARY post (Variant A or B).

**Carousel thesis:** In one release, MCP moved the hard problem — the scaling wall came down (stateless), and the real frontier shifted up the stack to who is allowed to do what. The reader should walk away seeing *where* the value and the risk moved, not just that they did.

**Slide count:** 5
**Aspect ratio:** 4:5 (1080x1350) — LinkedIn carousel default
**Palette (all slides):** dark slate background (#0F172A) + white text + ONE accent, deep emerald green (#059669, infrastructure topic). Slide 4 distinguishes "solved" vs "open" by solid-fill vs. hollow-outline + a check/open-circle icon and column labels — never color alone.
**Tool routing summary:** All 5 → Gamma (`format: "social"`, `4x5`, dark theme e.g. Stratos, `imageOptions.source: "noImages"`, "turn every structure into a diagram, no stock imagery"). Export as one PDF for the LinkedIn document post. Slides 2–3 are a matched-frame diagram pair; slide 4 is the load-bearing framework.

---

### Slide 1 of 5 — Hook: state the moved problem

- **Visual mode:** Bold typography card
- **Headline:** "One release. Two gaps." (4 words)
- **Body / content:** Sub-line beneath, smaller: "MCP closed the scaling gap and opened the authorization gap — the same day." Small footer tag: "MCP Release Party · NYC · Jul 2026"
- **Palette:** dark slate bg + white text + emerald underline on "Two gaps"
- **Source attribution:** n/a (thesis card)
- **Alt text:** Title card reading "One release. Two gaps." over the claim that MCP's July release closed the scaling gap and opened the authorization gap simultaneously.
- **Tool:** Gamma (typography)

### Slide 2 of 5 — Before: the wall was infrastructure

- **Visual mode:** Diagram (must share frame with Slide 3)
- **Headline:** "Before: stateful = stuck" (4 words)
- **Body / content:** Diagram — a load balancer box feeding 3 server nodes. A "session" token is pinned to ONE node (highlighted, locked icon). Caption strip: "The server had to remember your connection. You had to pin traffic to one node — or bolt on a shared session store. Either way, you couldn't freely cycle the fleet."
- **Palette:** dark slate bg + white text + emerald (the pinned path in emerald, other nodes muted gray)
- **Source attribution:** "Source: Alex Hancock (Block), MCP Release Party, 2026"
- **Alt text:** Diagram showing a load balancer forced to pin a session to a single server node, with the other nodes unusable — the old stateful constraint.
- **Tool:** Gamma (diagram)

### Slide 3 of 5 — After: stateless removes the wall

- **Visual mode:** Diagram (IDENTICAL frame to Slide 2 — same box positions, same layout)
- **Headline:** "After: any request, any node" (5 words)
- **Body / content:** Same load balancer + 3 nodes, but now arrows fan from the balancer to ALL three nodes evenly (no pin, no lock). A small badge on each request reads "self-contained." Caption strip: "Every request now carries what the server needs. No initialize, no session. Add a normal load balancer and an autoscaling pool — it just works."
- **Palette:** dark slate bg + white text + emerald (all three routing arrows emerald — the unlocked state)
- **Source attribution:** "Source: Alex Hancock (Block), MCP Release Party, 2026"
- **Alt text:** The same load balancer diagram, now routing self-contained requests freely to all three nodes — the stateless model that enables autoscaling.
- **Tool:** Gamma (diagram)

### Slide 4 of 5 — What changed: where the frontier moved (load-bearing)

- **Visual mode:** Framework / matrix — a 3-layer stack, split "Solved" vs. "Open"
- **Headline:** "The frontier moved up the stack" (6 words)
- **Body / content:** A vertical stack of 3 layers, each with a SOLVED (solid emerald, check icon) or OPEN (hollow outline, open-circle icon) tag:
  - **Scaling / infrastructure** → SOLVED — "Stateless core, in the open spec." (Hancock)
  - **Org ownership** → SHIFTING — "47→197 tools, ~83 teams. Fix = distributed servers, one URL." (Yak)
  - **Authorization + evals** → OPEN — "What an authorized agent may DO. Lives at the gateway + inside ops teams, not the spec." (Levan / Yak)
  - Right-margin arrow pointing UP labeled "where the hard work moved."
- **Palette:** dark slate bg + white text + emerald; solved = filled emerald, open = white outline + open-circle icon (distinction is shape+icon+label, not color alone)
- **Source attribution:** "Source: Hancock (Block), Yak (Datadog), Levan (Solo.io) — MCP Release Party, 2026"
- **Alt text:** A three-layer stack showing scaling/infrastructure solved in the open spec, org ownership shifting to distributed servers, and authorization plus evals still open at the gateway and inside ops teams — with an arrow indicating the hard work moved up the stack.
- **Tool:** Gamma (framework/matrix)

### Slide 5 of 5 — So What: the question to carry out

- **Visual mode:** Bold typography card (matches Slide 1)
- **Headline:** "Scaling is plumbing now" (4 words)
- **Body / content:** Beneath, smaller: "The open question isn't whether MCP scales. It's what an authorized agent is allowed to do next — and where you enforce it." No "follow for more" language.
- **Palette:** dark slate bg + white text + emerald underline on "authorized agent"
- **Source attribution:** n/a (synthesis card)
- **Alt text:** Closing card reading "Scaling is plumbing now," posing the question of what an authorized agent is allowed to do next and where enforcement lives.
- **Tool:** Gamma (typography)

---

**Quality gate checks:**
- Arc fit: PASS — Arc 3 (Before → After → What Changed → So What) fits the "the problem moved" thesis; slides 2/3 are the before/after pair, slide 4 is the mechanism, slides 1/5 bookend.
- Job differentiation: PASS — hook / before / after / where-it-moved / question are all distinct jobs.
- Frame parallelism (Arc 3): PASS — slides 2 and 3 share identical diagram frame so the stateless change is legible at a glance.
- Adds information (not repetition): PASS — no slide re-prints a post quote; slides 2–4 render architecture and a solved-vs-open stack the copy only describes in prose. Slide 4 (where the frontier moved) is net-new visual information.
- Thumb test per slide: PASS — every headline ≤6 words.
- Source citations: PASS — every slide carrying a claim names the speaker + event + year.
- Final slide earns the swipe: PASS — closes on the governing question, no housekeeping CTA.

---

## Drafting notes / gates cleared

- **Quote-safety:** all verbatim quotes are HIGH-tagged. Hancock statelessness lines, Yak "monolithic…organizationally" + "shared commons" + "83 teams…bottleneck" + "boring technology," Levan "new attack surface" + "nine point nine nine nine times out of ten" + black-box + 15–18 tools — all HIGH. The evals line (MED) is **paraphrased** in the Yak deep-cut. No line attributed to the unresolved 54:13 audience member. No @-tags in copy.
- **Rule 12:** No unsourced firm/org claims in copy. AAIF's three-founder claim, "Goose was the first MCP client" (softened to "one of the first" in the first comment), and "Codex+Copilot use the Rust SDK" are all **omitted** from post bodies.
- **Named + thanked:** Angie Jones, Alex Hancock, Scott Yak, Michael Levan (spelled Levan), plus Datadog (venue) and AAIF (organizer) in every post.
- **Jargon defined inline + mechanism shown:** MCP defined; stateless explained via the barista analogy + the load-balancer mechanism; authentication vs authorization split; "black box → move enforcement to the gateway" mechanism spelled out.
- **Char counts (LinkedIn counts everything):** Primary A = 2,376 · Primary B = 2,227 · Yak deep-cut = 2,295. All ≤ 3,000. Sources in first comments, not inline.
- **Advances past the pre-event post:** does not re-teach stateless-vs-stateful from scratch; frames it as the confirmed prediction and moves to the org-scaling cost and the authorization gap the room named.
