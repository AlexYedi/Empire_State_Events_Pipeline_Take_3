# Research Brief: OpenClaw Show and Tell Night

**Date:** Thursday, April 23, 2026, 6:30–9:30 PM ET
**Location:** Fat Cat Fab Lab, 224 W. 4th St., Suite 206, New York, NY (West Village)
**Host:** Freedom Lab NYC — Harrison Friedes (Freedom Tech Grants Lead, Human Rights Foundation)
**Sponsors:** Kilo Code, Cake Wallet
**Format:** In-person, demo-driven community meetup

---

## The 90-Second Frame

This event sits at an unusual three-way intersection that doesn't show up on most NYC AI calendars:

1. **Open-source, local-first AI agents** (the OpenClaw artifact itself)
2. **Bitcoin / Freedom Tech / privacy community** (the host + sponsors)
3. **Maker / hackerspace culture** (the venue)

The crowd will NOT be the typical enterprise AI / VC NYC crowd. Expect cypherpunks, Bitcoin/Monero builders, HRF-funded freedom technologists, privacy engineers, independent devs, and the technically-curious end of the human rights world. This is a differentiated audience for Alex — one that reads AI through a *sovereignty and surveillance-resistance* lens, not a productivity or revenue lens.

That framing is the documentarian opportunity. Nobody in Alex's LinkedIn feed is writing about AI from this angle — the enterprise GTM crowd treats it like a vertical, and the AI-native crowd treats it like a roadmap item. The Freedom Tech community treats it like a survival question.

---

## Topic 1: OpenClaw — What It Actually Is

### The Artifact

- **Type:** Open-source autonomous AI agent. MIT license. Cross-platform (Mac/Windows/Linux).
- **Interface:** Uses messaging platforms (WhatsApp, Discord) as the primary UI.
- **Capabilities:** "Eyes and hands" — browses the web, reads/writes local files, executes shell commands autonomously, routes messages, remembers conversation history, triggers automations via natural language.
- **Philosophy:** Local compute, no telemetry, auditable code, user-controlled data. Explicitly positioned against walled-garden assistants.
- **Creator:** Peter Steinberger, Austrian independent developer. First published November 2025.

### The Rename Saga (relevant because it will come up)

This is context you'll hear referenced and should know cold:

1. **November 2025:** Launched as **Clawdbot** (portmanteau: Claude + bot).
2. **January 27, 2026:** Renamed to **Moltbot** after Anthropic filed a trademark complaint against "Clawdbot."
3. **January 30, 2026:** Renamed *again* (three days later) to **OpenClaw** because Steinberger said "Moltbot never rolled off the tongue" and he hadn't done thorough trademark searches for Moltbot either.
4. During the transition, scammers hijacked the old Clawdbot social accounts and posted fake crypto-token announcements, piggybacking on the project's viral moment.

The "🦞" lobster motif survives all three names.

### The Security Reality Check (this is the whole story)

The event description soft-pedals it: *"security protocols remain a work in progress."* That's a significant understatement. As of April 2026, OpenClaw has been publicly flagged for serious vulnerabilities by roughly every major security research org:

- **CrowdStrike, Cisco, Microsoft, Jamf, Kaspersky, Malwarebytes, Giskard** have all published advisories.
- **Prompt injection** and **indirect prompt injection** are the primary attack vectors. Any document, email, webpage, or ticket the agent ingests can carry hostile instructions.
- **Documented failures:** Leaked API keys and credentials. Remote code execution via prompt injection. Malicious "skills" uploaded to the ClawHub repo that install as arbitrary-command runners. Token exfiltration where a single stolen gateway token enables full remote control.
- **Vitalik Buterin, April 2, 2026:** In his published "self-sovereign / local / private / secure LLM setup" post, he specifically called out OpenClaw by name for allowing the agent to modify its own system prompt and critical settings without requiring human confirmation. He cited Hiddenlayer data that ~15% of AI agent skills contain malicious instructions.
- **Security consensus recommendation:** If you must run it, do so in an isolated VM with non-privileged credentials, never on a primary work or personal machine.
- **OpenClaw v2026.4.14** (released 5 days before this event) is explicitly framed as the "security update that stops AI from hacking the config" — a direct response to the prompt-injection-into-config class of attacks.

### Why This Matters for the Event

OpenClaw is *philosophically aligned* with what the Freedom Tech community wants (open, local, sovereign) but *operationally dangerous* in its current form. The Show and Tell Night is a live example of a community that has the skills and incentives to harden it — the same community that spent 15 years building trustless systems for money is now encountering the "how do we build trustless systems for AI agents" problem. That's the subtext, and it's richer than the text.

---

## Topic 2: The Freedom Tech + AI Tailwind

### What "Freedom Tech" Means

A loose but coherent movement tying Bitcoin, Monero, end-to-end encryption, Tor, Signal, and self-hosted tools together as a technology stack for people living under surveillance or authoritarian regimes (or who simply don't want to depend on corporate platforms). The Human Rights Foundation (HRF) is a major node.

### The Specific Tailwinds Pushing the OpenClaw Demo

1. **Sovereignty as a business requirement.** 93% of executives say AI sovereignty must factor into their strategy in 2026. This started as a nation-state concern (EU, India, Middle East wanting domestic AI stacks) but has filtered down to enterprise and individual users.
2. **Open-source model momentum.** More than half of production LLM deployments in 2026 use open-weights models rather than closed APIs. Alibaba's Qwen family alone is past 700M downloads. DeepSeek's breakthrough in early 2025 proved open-weights could match closed-model capability at a fraction of the training cost — the credibility ceiling lifted.
3. **The "AI as infrastructure you control" reframe.** The industry is shifting from "AI as a service" (cloud API) to "AI as infrastructure you run." Local inference, local data, sandboxed execution — Vitalik's three-pillar framework is the current cleanest articulation.
4. **Hardware enablement.** AMD's GAIA SDK (launched mid-April 2026) explicitly targets local agents on Ryzen AI chips. Consumer GPUs (Nvidia 5090) now run 35B-parameter models at 90 tok/s. The hardware caught up.
5. **Surveillance-state AI as the dark mirror.** HRF documents how AI is deployed offensively by authoritarian regimes — their recent work shows how Tibetan refugees in Nepal now live under AI-powered facial recognition networks. The Freedom Tech AI thesis is: *the same tech that lets states surveil citizens can be inverted to give citizens tools states can't touch.*
6. **High-profile personal endorsements.** Vitalik Buterin's April 2026 self-sovereign stack post (running Qwen3.5:35B locally, with a 2-of-2 human+LLM confirmation rule for outbound actions) is the single most-cited reference for this thesis right now.

### What's Different About OpenClaw Specifically

In a crowded local-agent landscape (LM Studio, Ollama, Open WebUI, self-hosted Llama stacks), OpenClaw's differentiators are:

- **Messaging-platform-native UX.** Most local agents live in a CLI or a local web UI. OpenClaw uses WhatsApp/Discord as the interface, which meets users where they already are.
- **"Any OS, any platform."** Lower-friction install than most self-hosted stacks.
- **"Skills" extension model.** Plugin-style extensibility via ClawHub. (This is also the attack surface — see security section.)
- **Viral cultural moment.** The rename drama, the lobster motif, and the clear Anthropic subtext gave it asymmetric distribution in the indie-dev and crypto-adjacent communities.

### The Shortcomings / Open Questions

- **Security posture is genuinely immature** and publicly documented as such.
- **Trust model for skills** — ClawHub is open, which means skills can be malicious. No signing, reputation, or isolation primitives at the skill level as of the April security update.
- **No human-in-the-loop confirmation by default** for high-impact actions (this is the Vitalik critique).
- **"Open source AI assistant" is an overloaded phrase** — OpenClaw itself is open-source, but the *model* it calls is usually a hosted third-party LLM. True end-to-end sovereignty requires pairing it with a local model (Ollama / Qwen / etc.) — which many users won't do.
- **Maintainer bandwidth risk.** A solo-dev-led project facing serious security pressure and explosive adoption is a fragile configuration.

---

## Topic 3: Hosts, Sponsors, and People

### Harrison Friedes — Host

- **Title used on invite:** Freedom Tech Grants Lead, Human Rights Foundation.
- **LinkedIn title:** AI for Individual Rights Program Associate (same program, different framing).
- **What that role does:** HRF's AI for Individual Rights program (1) documents how authoritarian governments use AI offensively against dissidents and (2) funds open-source AI tools that dissidents can actually use. Harrison is both a grant-maker and a community organizer for this work in NYC.
- **What to engage him on:**
  - The grant-making lens — what has he seen get funded that's worked, and what hasn't? The Top 15 Freedom Tech Projects of 2025 list is a good reference point.
  - The practitioner lens — HRF's technical lead Justin Moon has been publicly promoting Ollama, Maple AI, PayPerQ, and Routstr as safer alternatives. Where does OpenClaw sit relative to those?
  - The surveillance-resistance lens — the Nepal/Tibet surveillance reporting is fresh; how does that reshape the priorities for what dissident-facing AI actually needs?

### Freedom Lab NYC — Host Organization

- NYC's Freedom Tech community group. Operates through Meetup; overlap with the "Bitcoin Network NYC" community.
- Educational / community-first rather than product or VC driven. Expect demos, not pitches.

### Kilo Code — Sponsor

- Open-source AI coding agent. Runs in VS Code, JetBrains, CLI. 1.5M+ users. Ranked #1 coding agent on OpenRouter. 25T+ tokens processed.
- Five agent modes: Orchestrator, Architect, Coder, Debugger, Ask. Plus parallel agent execution.
- **Notable:** In early 2026 they launched **KiloClaw** — a hosted cloud agent, $49/mo, free until March 23, 2026. The naming overlap with OpenClaw is not an accident. Expect ecosystem-adjacency conversations.
- **The angle to engage:** Kilo is a commercial open-source company sponsoring a sovereignty-focused meetup. That tension (cloud-hosted agent brand showing up at a local-first event) is worth asking about directly. Where do they see the line between "open source you can inspect" and "open source you can run under your own roof"?

### Cake Wallet — Sponsor

- Non-custodial multi-currency crypto wallet. Strong Monero support (the privacy-focused cryptocurrency). Native Tor integration. Silent Payments and Payjoin for Bitcoin privacy.
- **Why they're here:** The Freedom Tech community treats financial privacy and AI privacy as the same problem in two domains. Cake is the incumbent privacy-first wallet in that world.
- **The angle to engage:** How do they think about AI agents interacting with wallet software? If OpenClaw-type agents become the dominant consumer interface to money, the wallet UX model changes completely. Are they building for that?

### Fat Cat Fab Lab — Venue

- Volunteer-run makerspace in the West Village since 2013. Laser cutters, 3D printers, electronics lab, sewing, metal shop, woodshop.
- Signals about the audience: more builder / tinkerer than VC / founder. Expect people who have actually soldered something.

---

## Topic 4: Top Questions Worth Asking in the Room

Ranked by richness of expected answer:

1. **To Harrison:** "Of the Freedom Tech projects HRF has funded, which ones have had the hardest time getting adoption even when the tech worked — and what does that tell us about what OpenClaw needs to solve beyond the code?"
2. **To a demo presenter:** "Show me the threat model you run in your head when you let OpenClaw touch your email or files. What specifically do you isolate, and what do you just trust?"
3. **To Harrison / the room:** "Vitalik's self-sovereign stack assumes a 2-of-2 human+LLM confirmation rule for outbound actions. Is that the direction OpenClaw should go, or does that kill the ergonomics that made it viral?"
4. **To Kilo:** "You've got a hosted cloud product (KiloClaw) and you're sponsoring a local-first meetup. Where's the line for you between those two models, and what would make you push one harder than the other?"
5. **To Cake Wallet:** "If agentic AI becomes the default interface to crypto in 2–3 years, what does that do to wallet UX? Are you building for an agent-first world already?"
6. **To the room:** "Most of the security advisories on OpenClaw come from corporate security firms. What's the Freedom Tech community's own threat model and remediation path — is it just 'run it in a VM,' or is there something more interesting?"
7. **To a demo presenter:** "What's the single thing you can do with OpenClaw that you couldn't comfortably do with Claude Desktop or ChatGPT, where the sovereignty difference is *load-bearing* — not ideological, but practical?"

---

## Topic 5: The Documentarian Angle (for Content)

The strongest angle for Alex's audience — ranked by sharpness:

### Angle A (sharpest): "The community best equipped to secure AI agents isn't the AI industry — it's the people who spent 15 years building trustless systems for money."

- Pulls on: Bitcoin/Monero community's deep expertise in adversarial thinking, threat modeling, and self-custody.
- Specific hook: OpenClaw's documented security issues are a solved-class-of-problem for cypherpunks (signing, isolation, revocation, key custody). The AI industry is relearning lessons the crypto community wrote the textbook on.
- Why it works for Alex's audience: hiring managers at AI-native companies are *specifically* hiring for people who can think this way. This post demonstrates that pattern recognition.

### Angle B: "The local-first AI thesis just went from ideology to infrastructure."

- Pulls on: Vitalik's stack, AMD GAIA, Qwen 700M downloads, 5090 laptops running 35B models at 90 tok/s, 93% exec sovereignty stat.
- Specific hook: Same weekend Vitalik published his stack, AMD shipped GAIA, and here's a room full of NYC builders doing it in practice with OpenClaw. The four events are the same event.
- Why it works: documentarian, synthesizes multiple signals, positions Alex as pattern-aware across the stack.

### Angle C: "The rebrand tells you what the field is actually about."

- Pulls on: Clawdbot → Moltbot → OpenClaw rename in 10 weeks, post-Anthropic trademark pressure, the scammer impersonation campaign during the rename.
- Specific hook: The viral moment, the pressure from a $60B lab, the scammer vultures — that entire arc is a miniature of what building in sovereign AI actually feels like right now.
- Why it works: human, specific, uses the rename as an entry point rather than the tech.

### Cross-angle tactic: Two-thesis synthesis opportunity

This event pairs cleanly with *any* upcoming event that represents the opposite pole — e.g., a closed-model enterprise-AI event, a hyperscaler-hosted meetup, a Series D announcement from a centralized platform. If Alex has one of those on the calendar for the same week, the `pattern-synthesis` skill's "two-thesis" format applies here. (Confirm events pending for the week before committing to this angle.)

---

## Sources

**OpenClaw (artifact and context):**
- [OpenClaw — Personal AI Assistant (official)](https://openclaw.ai/)
- [OpenClaw GitHub repo](https://github.com/openclaw/openclaw)
- [What is OpenClaw? (DigitalOcean)](https://www.digitalocean.com/resources/articles/what-is-openclaw)
- [From Clawdbot to Moltbot to OpenClaw (CNBC)](https://www.cnbc.com/2026/02/02/openclaw-open-source-ai-agent-rise-controversy-clawdbot-moltbot-moltbook.html)
- [The Complete OpenClaw Renaming Saga (BetterLink Blog)](https://eastondev.com/blog/en/posts/ai/20260204-openclaw-rename-history/)

**OpenClaw security posture:**
- [What Security Teams Need to Know About OpenClaw (CrowdStrike)](https://www.crowdstrike.com/en-us/blog/what-security-teams-need-to-know-about-openclaw-ai-super-agent/)
- [OpenClaw AI Agent Flaws (The Hacker News)](https://thehackernews.com/2026/03/openclaw-ai-agent-flaws-could-enable.html)
- [Personal AI Agents like OpenClaw Are a Security Nightmare (Cisco)](https://blogs.cisco.com/ai/personal-ai-agents-like-openclaw-are-a-security-nightmare)
- [Running OpenClaw safely (Microsoft Security)](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk/)
- [OpenClaw 2026.4.14 security update (Geek Metaverse News)](https://www.geekmetaverse.com/openclaw-2026-4-14-the-security-update-that-stops-ai-from-hacking-the-config-prompt-injection-proof/)

**Freedom Tech and HRF:**
- [AI for Individual Rights program (HRF)](https://hrf.org/program/ai-for-individual-rights/)
- [Top 15 Freedom Tech Projects of 2025 (HRF)](https://hrf.org/latest/top-15-freedom-tech-projects-of-2025/)
- [HRF Gives 1.3B Satoshis to 22 Projects (Bitcoin Magazine)](https://bitcoinmagazine.com/news/human-rights-foundation-1-3b-satoshis)
- [Freedom Lab NYC Meetup](https://www.meetup.com/bitcoin-network-nyc/)
- [Harrison Friedes — LinkedIn](https://www.linkedin.com/in/harrison-friedes/)

**Sovereignty / local-first AI tailwinds:**
- [Vitalik Buterin — My self-sovereign / local / private / secure LLM setup, April 2026](https://vitalik.eth.limo/general/2026/04/02/secure_llms.html)
- [Agentic AI 2026: Autonomous Agents & Sovereign Stacks (Vucense)](https://vucense.com/ai-intelligence/agentic-ai/agentic-ai-2026-autonomous-orchestration-sovereignty/)
- [5 Reasons Developers Are Building With Local-First AI Agents in 2026](https://programminginsider.com/5-reasons-developers-are-building-with-local-first-ai-agents-in-2026/)
- [AMD GAIA SDK launch — local agents without cloud dependency](https://aitoolly.com/ai-news/article/2026-04-14-amd-launches-gaia-sdk-an-open-source-framework-for-building-local-ai-agents-without-cloud-dependency)
- [DeepSeek and the Open Source AI Revolution 2026](https://www.programming-helper.com/tech/deepseek-open-source-ai-models-2026-python-enterprise-adoption)

**Sponsors and venue:**
- [Kilo Code](https://kilo.ai)
- [Kilo Code GitHub](https://github.com/Kilo-Org/kilocode)
- [Cake Wallet](https://cakewallet.com/)
- [Cake Wallet GitHub](https://github.com/cake-tech/cake_wallet)
- [Fat Cat Fab Lab](https://fatcatfablab.org/)

---

*Brief compiled April 19, 2026 for pre-event content generation.*
