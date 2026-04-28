# Research Brief: Multi-Agent Hackathon — Sky Valley Ambient Computing × Tribute Labs

**Date:** Thursday, April 30, 2026
**Format:** **HACKATHON** (build event, not panel/talk). Alex is BUILDING.
**Hosts:**
- **Sky Valley Ambient Computing** — Iris ten Teije, Noam Tenne (already in Notion via Tue panel research)
- **Tribute Labs** — building ADIN (Autonomous Deal Infrastructure Network), AI-native venture platform

---

## The 90-Second Frame (Building-Mode Edition)

This is a different brief shape than the others. **Alex is BUILDING at this event**, not attending. That changes everything downstream:

- The pre-event content shifts from "looking forward to" → "what I'm building toward."
- Speaker DMs aren't relevant — the right relationships happen by sitting next to people while they code.
- Visual content shifts from "stat carousel" → "build-in-public progress documentation."
- Documentation continues *during and after* the event, not just before.

**The provocative thesis the hackathon is built on:** *"What becomes possible when agents coordinate themselves?"* The hosts are explicitly betting against the orchestrator-first paradigm (LangChain, AutoGPT-style architectures) and proposing **emergent self-coordination via shared intent broadcast**.

If Sky Valley + Tribute Labs are right, this is the architectural debate that gets resolved over the next 24 months. Alex building something here that ships isn't just a learning exercise — it's a stake in the ground on the architecturally contested side of the agent stack.

---

## Topic 1: The Two Hosts — What They're Betting On

### 1.1 Sky Valley Ambient Computing

(Already deeply researched in Tue brief — `2026-04-28_Software_Is_the_New_Media.md`. Key context here:)

- Builds **Differ** (adaptive runtime where agents observe user behavior, edit-then-redeploy autonomously) and **Intent Space** (open-source coordination protocol).
- Co-founders **Iris ten Teije** (Tue panelist) and **Noam Tenne**.
- **Architectural position: orchestrator-FREE** — agents broadcast intent to a shared log; others self-select what to pick up.
- This is the hackathon's substrate. Whatever Alex builds will use Intent Space.

### 1.2 Tribute Labs

**The artifact:** Tribute Labs is building **ADIN** (Autonomous Deal Infrastructure Network) — an AI-native venture capital fund that operates more autonomously than any traditional fund. Launched 2025. Tribute Labs serves as limited general partner; ADIN evolves toward a decentralized DAO structure.

**How ADIN works (this is the killer detail for content):**
- **~12 specialized agents,** each with a distinct persona and investing thesis.
- **Network Hunter** scrapes user telemetry and social graphs.
- **Tech Oracle** audits repos and patents.
- **Monopoly Maker** models barriers to entry.
- **Unit Master** analyzes margins and runway.
- **Value Guy** sanity-checks price against comparables.
- Agents work on diligence in parallel; the system generates institutional-grade reports in minutes that would take weeks of human work.
- **Humans required for "last mile":** meeting founders, ultimately deciding whether to cut checks.

**Press coverage:** [DNYUZ, March 2026 — "Can AI Kill the Venture Capitalist?"](https://dnyuz.com/2026/03/09/can-ai-kill-the-venture-capitalist/)

**Why Tribute Labs is co-hosting:** ADIN is the most mature live demo of "specialized agents with distinct personas coordinating toward a shared goal" — exactly what Intent Space is meant to enable. They're proof-pointing the architectural thesis with a real product.

**Architectural alignment with Sky Valley:** Both are betting that coordination among many specialized agents — without a central orchestrator deciding work allocation — outperforms a single-agent or single-orchestrator approach.

---

## Topic 2: Intent Space — What Alex is Actually Building With

(Drawn from Sky Valley research; supplemented by hackathon's stated structure.)

**The primitive in one sentence:** A shared append-only log where agents post what they want done; other agents independently decide whether to pick it up.

**Concrete operational model (best understanding from public materials):**
1. Agent A reaches a point in its work where it needs another capability (e.g., "summarize this 50-page document").
2. Instead of calling a known function or routing through an orchestrator, Agent A posts an *intent* to the shared Intent Space: `{intent: "summarize", payload: <doc>, requirements: [...], reward: <something>}`.
3. Agent B (or N other agents) is *scanning* the intent space. Agent B sees the intent, evaluates whether it can fulfill it, makes a *voluntary commitment*, and starts work.
4. Agent A doesn't know who's working on its intent or how many. Multiple agents may compete; the first to deliver wins (or several deliver and a consensus mechanism resolves).
5. The result is broadcast back; Agent A consumes it.

**Why it's interesting:** Removes orchestration overhead, enables emergent specialization, fault-tolerant by design (any agent failing doesn't crash the system).

**Where it might fail:** Coordination cost (lots of broadcast traffic), quality variance (any agent can claim an intent), economic incentives unclear (why does Agent B work for Agent A?), latency on critical paths.

The hackathon is the place where these failure modes become observable.

---

## Topic 3: Project Ideas Alex Could Build (Hackathon Inspiration List Mapped to Alex's Stack)

The host's stated inspiration list:
> *"A swarm that researches, debates, and drafts — with each agent's reasoning visible in real time. A game where NPCs coordinate without a script. A society simulation. A customer support system where agents self-assign and escalate without a queue manager. A creative tool where agents build on top of each other's output. A social network with private and public spaces. A marketplace with bidding capabilities."*

**Three ideas mapped to Alex's existing stack and content thesis:**

### Idea A (highest content leverage): "Event-research swarm built on Intent Space"

**The build:** Take the Empire State Events Pipeline pattern (research a NYC AI/tech event end-to-end) and rebuild it as an Intent Space coordination problem. Instead of one Claude conversation orchestrating the research, have **specialized agents** post intents to a shared log: company-research agent, person-research agent, topic-synthesis agent, documentarian-angle agent, dedup agent.

**Why it works:**
- **Builds on what Alex already knows.** The pipeline architecture is already in Alex's head. The hackathon becomes a re-implementation in a different paradigm — instructive, not greenfield.
- **Killer documentary angle.** Alex has been writing about events using the orchestrator-first pattern (Claude skills + MCP writes). Switching architectures and writing about the comparison is a perfect post: *"I rebuilt my events pipeline without an orchestrator. Here's what got better and what got worse."*
- **Demoable in 4-6 hours.** The scope is bounded; Alex has the underlying logic already; only the coordination layer is new.

### Idea B (highest collaboration potential): "AI-augmented hiring shortlist generator"

**The build:** Mirror what Andrew Yeung + Ivor Stratford do at the Shortlist (Mon's event Alex just attended). Multiple agents source operators from various signal sources (LinkedIn, GitHub, Substack, event RSVPs), debate fit against a target role, and collaboratively produce a ranked shortlist with reasoning visible per agent.

**Why it works:**
- **Builds on Alex's GTM domain expertise** (talent matching is downstream of enterprise sales, similar pattern recognition).
- **Direct use case overlap with ADIN's diligence agents** — Tribute Labs team will recognize the architecture immediately. Conversation starter built in.
- **Risk: scope creep.** Need to constrain to one role-type or one source.

### Idea C (highest personal-curiosity play): "Documentarian agent swarm"

**The build:** A swarm that watches Alex's calendar + browser + Granola transcripts + Wispr voice notes, and posts intents to Intent Space when it detects a content moment. Specialized agents pick up: hook-writer, fact-checker, hashtag-suggester, visual-brief-generator. The output is a draft post Alex can ship.

**Why it works:**
- **Most personal** — directly extends Alex's content engine.
- **Most architecturally aligned** with Sky Valley/Differ thesis (software that adapts to user behavior).
- **Risk: too much scope, and the personal data integration eats most of the hackathon time.**

**Recommendation:** **Idea A** is the right call. Highest content payoff, lowest scope risk, most directly demonstrable, and the comparison-to-existing-pipeline framing is content gold.

---

## Topic 4: Collaboration Plays in the Room

The hackathon will have a mix of:
- **Sky Valley team** (Iris, Noam, others) — they'll be circulating, helping people unblock on Intent Space mechanics.
- **Tribute Labs team** — fewer of them, but their interest is "what other use cases does our agent-coordination thesis unlock?" Build something that answers that question, and they engage.
- **Indie devs and AI builders** — likely the largest cohort. Mostly heads-down building. Pick someone whose project is complementary to Alex's and propose a 30-min pairing on the integration point.
- **VC-adjacent observers** — there will be some. Lower density than usual NYC events because hackathons select for builders.

**Best move:** **Sit next to someone in the first 30 minutes and ask what they're building.** A 5-min conversation establishes whether your projects can integrate. If yes, work near each other for the day. The post-event story becomes "here's what I built with [X], met them at the hackathon" — much more credible than a solo project.

**Specific people to find if possible:**
- **Iris ten Teije** — confirm you saw her at the Tue panel. The cross-event reference is the natural opener.
- **Anyone from Tribute Labs / ADIN** — ADIN's architecture is the most mature live demo of the thesis. Their feedback on what Alex builds is high-signal.

---

## Topic 5: Documentarian Angle (Building-in-Public Edition)

### Pre-event (Wed evening)

**Hook:** *"Building tomorrow at the Sky Valley × Tribute Labs hackathon. The bet: agent coordination without an orchestrator, using Sky Valley's Intent Space. I'm rebuilding a piece of my events pipeline in this paradigm. Will report back on what got better and what got worse."*

Short. Specific. Sets up the comparison frame for the post-event content. No promises about the build itself — just the experiment shape.

### During (live)

Two posts, kept short:
1. **Mid-event (mid-afternoon):** Photo of laptop + Intent Space dashboard. One sentence on what's working/breaking.
2. **End-of-event:** A 30-second video of the demo working (or failing visibly — failure videos perform unreasonably well on LinkedIn).

### Post-event (Friday)

**The killer post:** *"I rebuilt my events research pipeline without an orchestrator. Here's what got better and what got worse."*

Structure:
- **Hook:** specific data point — minutes saved, agents added, errors avoided (or surfaced).
- **Setup:** one-sentence Intent Space explanation (don't drown readers in the architecture).
- **What got better:** 2-3 specific things (parallelism, fault tolerance, surprise emergent behaviors).
- **What got worse:** 2-3 specific things (latency, debug complexity, coordination overhead).
- **The take:** *"Most agents will run inside orchestrators in 2026 because the tooling exists. The teams that win in 2027 are the ones who learned where orchestrators broke first."* Or whatever the genuine take ends up being.
- **CTA:** *"What's the smallest workflow you'd port to no-orchestrator coordination, and what would the failure look like?"*

This is one of the strongest content angles of the entire week because:
- It's specific (Alex actually built something).
- It reports failure honestly (rare in LinkedIn AI content).
- It connects to the broader debate (orchestrator vs. emergent — the synthesis-tension flagged earlier in the week).
- It builds on three other events Alex attended that same week.

### Cross-event observation

**This event closes the loop on the orchestrator-vs-emergent debate that ran through Tuesday's panel (Iris on Sky Valley) and Wednesday-evening (LangChain orchestrator-first).** The Friday post-event content can reference all three events and become the most synthesis-rich piece of the week — even though the user opted out of the formal pattern-synthesis post.

---

## Sources

**Tribute Labs / ADIN:**
- [Tribute Labs](https://tributelabs.xyz)
- [ADIN — AI Powered Venture Capital](https://adin.online/)
- [ADIN and the Rise of Self-Running Institutions — Substack](https://adinonline.substack.com/p/adin-and-the-rise-of-self-running)
- [About ADIN](https://adin.online/about)
- [Can AI Kill the Venture Capitalist? — DNYUZ, March 2026](https://dnyuz.com/2026/03/09/can-ai-kill-the-venture-capitalist/)
- [Tribute Labs on X](https://x.com/tributelabsxyz)

**Sky Valley Ambient Computing / Intent Space** (also in Tue brief):
- [Sky Valley Ambient Computing](https://skyvalley.ac/)
- [Iris ten Teije — LinkedIn](https://www.linkedin.com/in/iristenteije/)
- [Noam Tenne — LinkedIn (Sky Valley co-founder)](https://www.linkedin.com/in/noam-tenne/)

---

*Brief compiled April 26, 2026 (T-4) for hackathon BUILDING-mode content generation.*
