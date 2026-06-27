# POST-EVENT BRIEF — "2x AI: We gave everyone the tools, and it worked"

**Event:** 2x AI — We gave everyone the tools, and it worked
**Date / venue:** 2026-06-04 (Thu), ~6:22pm ET · 18 E 50th St, New York, NY
**Format:** Hands-on AI-adoption keynote + fireside panel + audience Q&A (org-wide rollout of Claude / Claude Code, RAG, agentic coding, PR automation, internal "skills")
**Speakers (content-derived):** Brian Donohue (VP Product, Fin — formerly Intercom) · Prithvi Rajasekaran (Member of Technical Staff, Anthropic Labs) · an unnamed Fin employee acting as moderator
**Companion essays (cited only as referenced in folder):** slide footers point to `ideas.fin.ai/p/2x-nine-months`; the alignment doc also lists `ideas.fin.ai/p/we-gave-claude-code-to-everyone-at` (Andrii Yakovenko). *These essays' internal numbers are NOT reproduced here — they were not in the folder's transcript/slide sources.*

> **Sourcing & scope note (read first).** This brief is built **only from files in the event folder**: the ElevenLabs Scribe-v2 diarized transcript (`…— Transcript (ElevenLabs).md`, the primary source; speaker_0 = Brian, speaker_1 = moderator, speaker_2 = Prithvi, speaker_3/4 = audience), the partial `…Transcript.txt` (weaker ASR, cross-reference only), `slide-transcript-alignment.md` (entity/number ground truth for the 9 slide photos), and the `…REVIEW (low-confidence spots).md` ASR list. **No web enrichment was added** (per task instruction "work ONLY from files in the folder; never invent"). Where a number lived on a slide but was not spoken aloud, it is tagged "slide." The recording is **partial (~50 min)** and **cuts off mid-sentence** during Brian's answer to the final audience question (~49:35). Quote confidence: **HIGH** = clean in the diarized .md; **MED** = ASR-ambiguous, paraphrased, or contains a flagged word.

---

## 1. Quick Take

Fin (the company formerly known as Intercom) set a **deliberate, measured goal to double R&D productivity ("2X")** and hit it in **nine months** — and over 16 months claims **3X**. This was a rare AI-adoption talk that came with audited receipts on slides: median time-to-merge **5.2× faster**, a customer-bug burndown from **1,780 → 420**, PRs written by Claude going from **<40% → >90%** in three months, and a **45% decline in fully-loaded cost-per-PR** even as peak Claude Code spend hit **$128K/week**. The single most counter-cultural lesson: **bottoms-up "use whatever you want, no spending limits" flatlined for six months; the breakout came only when leadership got opinionated and *forced* adoption** — via performance reviews and a gamified, company-wide hackathon that "works as a drug." Prithvi (Anthropic Labs) supplied the model-side frame: execution is now near-trivial, value migrates up the stack (vision → strategy → execution), and the "last mile" of human intuition/judgment/taste "will be the last thing to go." For Alex this is a concrete, numbers-backed org-change playbook for AI adoption — the GTM-adjacent version of "what good looks like."

---

## 2. The Thesis

**"2X was a measured goal, not a vibe — and forcing adoption beat encouraging it."**

Two interlocking arguments run through the talk:

1. **The measurement thesis (Brian).** AI productivity gains are real and auditable if you (a) pick a "good-enough" proxy fast — **merged PRs per R&D head** — accept its flaws, and move on, and (b) triangulate it with downstream value (bug burndown, cost-per-PR, breaking-change rate, deploy frequency, product-change velocity) so it can't be dismissed as a vanity number. They named the goal "2X" *specifically so they would measure it* ("make this a goal, and therefore measure it"), and treat the 16-month 3X as proof they weren't over-optimizing a proxy.

2. **The forcing-function thesis (Brian).** "The best way to get behavior change is to force it." Phase 1 (bottoms-up, no spend limits, "softly, softly encourage") produced a **six-month flatline**. Phase 2 — top-down, opinionated, "telling you what to do, how to do it," baked into performance reviews, kicked off by a company-wide hackathon — broke the plateau. Model capability (the Dec'25–Jan'26 step-change) was necessary but **not sufficient**; "the culture around it and the work around it" did the work.

Prithvi's counter-melody: as execution collapses in cost, both the bottleneck and the value migrate **up the stack** (QA, architecture, product discovery, taste) and toward **goal-driven** rather than task-driven work with the model.

---

## 3. Pre→Post Gap

**There is no pre-event brief file in this folder**, so a true pre→post diff cannot be reconstructed from folder sources. However, `slide-transcript-alignment.md` (a folder file) records what the pre-event brief *had* expected, and notes these deltas — relayed here as in-folder claims:

| Pre-event expectation (per alignment doc) | What actually happened in the room |
|---|---|
| Two speakers: Brian + Prithvi | Confirmed — plus an **unnamed Fin-employee moderator** not in the brief. |
| Prithvi framed around **agent reliability / a doer-judge harness** | Prithvi instead talked **model design, creativity, and a "frontend design skill" he wrote** — a different facet of the same person. (Harness engineering surfaced only in an audience Q.) |
| Company = "Intercom" | Brian announces on stage that they "**finally changed the name of our company, from Intercom to Fin, just a couple weeks ago**" — i.e., ~late May 2026. |
| Host community "GenAI Collective NYC (40k+)" | Per alignment doc, Prithvi **organizes GenAI Collective NYC** — he is both speaker and host-org leader. (Membership figure unverified from folder transcript.) |

---

## 4. Speaker Map (content-derived, confidence-tagged)

| Person | Role / Company | At this event | Confidence & basis |
|---|---|---|---|
| **Brian Donohue** | VP Product, Fin (formerly Intercom) | Delivered the entire "2X Story" deck + sat the panel | **HIGH** — moderator introduces him ("Brian leads product for us at Fin… came in last minute… usually speaks at 2X speed"); content matches alignment doc's roster. Note he references a *different* "Brian, one of our principal engineers" (March plugins stat) — two Brians. The moderator twice calls him "Ryan" (ASR artifact) — same person. |
| **Prithvi Rajasekaran** | Member of Technical Staff, **Anthropic Labs** (formerly **Apply AI** team) | Panel / co-speaker | **HIGH** — self-identifies ("I work on the Labs team"); states he **wrote the frontend design skill**; alignment doc confirms identity and that he organizes GenAI Collective NYC. |
| **Moderator** | A **Fin employee** (joined Jan 2026, non-technical) | Ran the fireside + Q&A | **MED on role / NAME UNKNOWN** — self-describes: "I joined Fin in January, non-technical person… finished ~130 of 700 in the hackathon." 🔴 **Do NOT publish a name.** The "Christy" in `…Transcript.txt`/alignment doc is an **ASR mishearing of "Prithvi"** (the clean diarized .md shows Brian saying *"Does that align with your thinking, Prithvi?"* at that exact point). |
| **"Dara / Darren / Tara"** | Exec who wrote the internal "2X" letter; Brian loosely calls "our CEO" | Not present (cited) | 🔴 **MED / internal name ASR-uncertain — do not attribute quotes or publish.** Alignment doc flags these as garbled internal names; notes the public-record returning CEO is **Eoghan McCabe** (Brian's "Owen, our CEO, came back" = likely ASR for Eoghan). |
| **"Mario," one of our principal engineers** | Fin engineer (cited re December inflection) | Not present (cited) | 🔴 internal name — flag, do not over-attribute. |
| **"Sarah"** (@11:14) | Cited re the SpaceX/system-pain analogy | Not present (cited) | 🔴 LOW — name flagged in REVIEW list (conf≈19%); do not attribute. |
| **Ciaran Lee** | Intercom **co-founder / former CTO** | Appears at **#3** on hackathon leaderboard (slide 4) | **HIGH** — per alignment doc; supports the "everyone, including the founders" color. |
| Audience members | speaker_3 (×2), speaker_4 | Asked harness / Zoom-agentic / OpenAI-vs-Claude questions | n/a |

---

## 5. Full Quote Bank (attributed, HIGH/MED tagged)

> Every quotable line from the diarized transcript, kept whole. ASR-corrected words are bracketed. Internal personal names are withheld from attribution per the flags above.

### Brian Donohue (Fin) — the 2X keynote

- **[HIGH]** "I have a lot of charts to show… but I promise they will not be boring."
- **[HIGH]** "Twenty twenty-two was not a good time, in the company we were then, Intercom… the post-COVID decline. We are blue. The SaaS average is in black, and we were doing much worse than the SaaS average. Everyone was suffering. We were suffering worse."
- **[HIGH]** "We basically felt that the customer service team's business was slowing, and we kinda felt like, if we don't go after this, someone else is gonna make our business die. **We have to basically be willing to make our own business die.** And so we decided pretty fast to go all in."
- **[HIGH]** "Our Fin revenue is gonna be over half of our business by the end of the year."
- **[HIGH]** "We changed our branding, and we actually finally changed the name of our company, from Intercom to Fin, just a couple weeks ago."
- **[HIGH]** "We had to go all in on the [forward-]deployed engineer thing. We had never had any of that before."
- **[HIGH]** (on the 2X framing, paraphrasing the internal letter) "It feels like we should say ten X, but I don't know if we'll be able to do two X. And two X is still ambitious, and we're gonna measure this, and let's actually do it."
- **[HIGH]** "This is not like an aspiration, let's see if we can do it. **Make this a goal, and therefore measure it.**"
- **[HIGH]** "It took us nine months to get there, and we did it."
- **[HIGH]** "Phase one… softly, softly. Encourage… whatever tool you want, use anything. We'll support anything… there's no spending limits here. Just go for it… And basically — **flatlined. Flatlined for, like, six months**… mediocre adoption, very little standardization, incremental gains, and no real meaningful change."
- **[HIGH]** "Phase two was like… we gotta be way more deliberate… being opinionated about the system and aggressively driving change. This became not just a top-down 'here's the goal, go after it, team'… no, no, no. **We are going in and telling you what to do, how to do it.**"
- **[HIGH]** "Just wanna acknowledge the model capability is a huge part of the change as well." (re the Dec/Jan inflection)
- **[HIGH]** "**The best way to get behavior change is to force it.**"
- **[HIGH]** "It started nice and easy with [a hackathon / 'Make-a-Thon']… build your own RAG system for Fin… here's the questions to evaluate against… run it and score it… see where you're going against the leaderboard. **It's like the basic gamification works as a drug.**"
- **[HIGH]** "It started with engineering… then [we] actually said, 'All of R&D, you must do this.' So it made everyone do this."
- **[HIGH]** "These were a lot of people who had no idea what they were actually doing, and **entirely vibe coding through Claude**, and then leaning in and figuring out what they needed to do."
- **[HIGH]** "It got everyone like, '**Holy [redacted], I knew nothing about this, and I was actually getting to a reasonable place.**' That mental unlock is what we brought with that gamification."
- **[HIGH]** (the vacation anecdote) "I remember one guy, he's on vacation… 'You're spending way too much time on this damn leaderboard. You gotta come back over here to where the family is.'"
- **[HIGH]** "Do you taste the drug of what Claude Code is? Because it's unreal what it unlocks."
- **[HIGH]** "**We need to onboard your agent, Claude, like you would a senior engineer.**"
- **[HIGH]** "This is March, where [a principal engineer] is talking about we've got **thirteen plugins, like a hundred skills and hooks**, and I think we had like **sixty people contributing** to the system that was enabling engineers to use Claude to code."
- **[HIGH]** "You've gotta be thinking like you're onboarding a human — how do you write good code, test the code… putting that same effort into the system for Claude."
- **[HIGH]** "It's like hundreds of iterations and loops… every time where it's not working, where it's failing, fixing that and solving that, treating it like a system that you're building."
- **[HIGH]** "This is Feb of '26… **nearly seventy engineers contributing**… shipping these skills to Claude — observability, incident response — a bunch of individual skills to actually enable Claude to work like an engineer."
- **[HIGH]** "**This is not optional. You must use this. It was part of performance reviews for engineers.** … EMs need to have shipped **ten PRs**… Stop just being on the sidelines managing. Everyone is contributing here."
- **[HIGH]** "Ninety percent by end of Feb '26." (PR target)
- **[HIGH]** "The first time they build the factories with electricity, the factories are still built in the old way. **You need to rebuild the thinking of the factory, find the bottlenecks.**"
- **[HIGH]** (SpaceX slide) "This is from the SpaceX stuff — the iterations to the engines. It's messy as hell initially… look how beautifully clean and simple that looks. Of course, we have no idea how the hell these things are working." *(Diarization resolves this slide to Brian; the alignment doc had flagged attribution as uncertain.)*
- **[HIGH]** "We're literally trying to make Claude the level of a senior engineer… giving all the context needed so Claude can actually do that… therefore everyone needs to get to that staff level."
- **[HIGH]** "We got there in nine months. If you look back sixteen months, it was actually **three X**. This is PRs per R&D person — designers, [grad] folks, PMs, everyone is in the metric."
- **[HIGH]** "Is that not a ridiculously reductionistic measurement? … everyone knows all the drawbacks… **but it was good enough**, and it gave us a reasonably good proxy for progress that we could measure and move on… rather than spending three months trying to get the right metric. Looking back, [the exec is] like, 'Oh, that was one of our best decisions. Just go with that.'"
- **[HIGH]** "We had nearly two thousand open defects… **death by a thousand cuts**… These are all customer-reported ones. These are not theoretical… there's like twenty-five hundred bugs that we closed."
- **[HIGH]** "Internally, we were like, '**Suspicious. Is this real? Do we really buy this?**' … How much have you closed with just a duplicate bug or not? … We had to use an LM, of course, to evaluate this. **Only five percent of those were non-fixes.** Almost all the rest… was code shift to actually close this bug."
- **[HIGH]** "**We've [got] teams with zero defects. I never thought we would ever have that. That seemed impossible.** And this is a product that's like twelve years old."
- **[HIGH]** "The number of PRs that Claude is actually writing… from **under forty percent to over ninety percent** over the space of three months."
- **[HIGH]** "The bottleneck, of course, is review. Who's reviewing the code? So teaching Claude to actually review the code and getting up to like **twenty percent**. That number is higher now."
- **[HIGH]** "A good PR is usually a smaller focus. Solve one problem, test that… **under twenty lines** is the type of PR we want engineering shipping."
- **[HIGH]** "Is this slop that's going out there? We have a bunch of efforts to measure code quality… even that is now **for the first time crossed into the green**."
- **[HIGH]** "Weekly deployments more than doubled… but breaking code changes have actually **reduced — by thirty-five percent** — while two-X-ing the productivity."
- **[HIGH]** "We're shipping lots of money to Anthropic… this is massive, and **we did not expect this**… But the flip side is the **cost per PR is actually reduced**… this doesn't solve the spend problem, but it's a more efficient spend of R&D… fully loaded across all R&D — how much does it cost to ship a PR?"
- **[HIGH]** "We're basically two-X-ing our product changes and the speed of shipping… this is the change your customers feel, not just PRs, a lot of which are invisible behind the scenes."
- **[HIGH]** "This is the distribution of engineers and their efficiency… **we still see huge discrepancy** here despite all of that… you have outliers totally rocking it… it's important to not just take the average numbers."
- **[HIGH]** "We're what, **fourteen hundred employees**, most people active Claude Code users. We actually got **over seven hundred people** to do that hackathon."
- **[HIGH]** "**Claude for data** — everyone has access to your data, but then you're using the wrong database, the wrong numbers… we built this thing internally, a Claude-for-data plugin, to control the quality… the usage is off the charts — like **two thousand individual reports** people could never have created before."
- **[HIGH]** "This is literally from an all-hands today… what our go-to-market team is looking at — AI answer optimization, a tool we built for ourselves because we couldn't get something on the market… a data quality engine… automated outreach."
- **[HIGH]** "The ceiling for our potential is far higher than we normally think… **by default, you're thinking too small** of what you can accomplish with this. You need to think way more ambitiously about what you're setting Claude out after to build."
- **[HIGH]** "This isn't just a bottoms-up 'go for it, team.' This was really deliberate — forcing this, pushing this, putting it into performance reviews."
- **[HIGH]** "[The exec] is still thinking we can two-X again this year. I don't know… but there doesn't feel like there's a ceiling we've reached so far."

### Brian Donohue — panel answers

- **[HIGH]** (the existential moment) "A lot of it's in your head, and then eventually you start seeing it around you… working in tech, everything is simultaneously way faster than you think, but also way slower… **the technology overhang we have now is massive. I don't know if we've ever had this level.**"
- **[HIGH]** "It's almost an internal forcing function to force yourself to make hard decisions one way or another… every three months, another major strategic decision… '**Are we going big enough? God, we just asked this three months ago, but we need to ask this again.**'"
- **[HIGH]** "It does require leadership-level decisions — like CTO-level decisions. It's critical the exec team is **not just behind this, but driving this**… a mandate's not enough. You actually gotta operationalize it… the full shift in a company requires that **cultural change coming from the top**."
- **[HIGH]** "For me as a product leader — am I feeling it? Sometimes it's hard to know how long [a big project] would have taken before. But… for the first time the team's like, '**Hey, we need more roadmap stuff. We're actually running out of stuff to do.**' You never hear that." *([VERIFY] "season on the team came" @33:03 — garbled framing word.)*
- **[HIGH]** "How much of a meaty R&D project is actually writing code? It's not eighty percent of the time… if that part is dramatically sped up, the other parts don't speed up as much — the feedback loop, getting customers, talking to customers, getting feedback… **the bigger the breadth, the bigger the uncertainty, the more human overlap is still needed.**"
- **[HIGH]** "Issues are where it's off-the-charts good at solving. Smaller features, very good. But the bigger the breadth… building new products is murkier."
- **[HIGH]** "When we ask what AI can do without being reflective on **how humans normally operate**… design trends, apps seem pretty damn similar — how much creativity is there? Mostly I just want you to get the core UX right, the affordance."
- **[HIGH/MED]** "Have you actually built UX into [Claude] design, or is that organically learned? It feels like it's something to build in." *(ASR "cloud design" = Claude design.)*
- **[HIGH]** (future of UI) "The **GUI is not dead, but it's moved to the background** — chat with on-demand GUI being built in is kind of replacing it… cowork to me is the model… is this where the future of all apps goes? … a lot of UX will fade into the background… you're working with the LLMs in a **goal-driven way, not a task-driven way. That's the huge shift**… conversations will be increasingly dominant as the form of UI, but **not on their own — you still need reference artifacts.**"
- **[HIGH]** (re Operator) "When we shipped Operator, I've asked a lot of people, 'Would you actually want to do this in co-work?'… there's a lot you can build uniquely into your app there."
- **[HIGH]** (Zoom / agentic positioning Q) "A bunch of companies are trying to say, 'How can we be at the center of things?' … For Fin, we're framing it as: this is the agent your company uses to communicate with its customers… **AI is a convergent force** [attributed to a Fin co-founder]. Any boundaries you put around your product, AI just washes those away… everyone feels like they're on some version of a collision course."
- **[MED]** (performance-review Q) "I'm not sure is the short answer… engineering is where it's not looser… is it on spend or PR? I'm not sure which one we've used… sorry, can't answer that one."

### Prithvi Rajasekaran (Anthropic Labs)

- **[HIGH]** "Thanks so much for having me… I work on the **Labs team** — focused on new experiments, product initiatives, applied research."
- **[HIGH]** (flattening) "You see folks from very diverse backgrounds — an engineer, a UX designer, a product background… there's definitely folks that a few years ago **you would never see near the code base that are shipping tons and tons of PRs now**… it's allowed someone like myself who's an engineer to do more product thinking or design thinking… **we definitely see the boundaries getting a little bit fuzzier with AI.**"
- **[HIGH]** (the value stack) "If you zoom out at how productive things get done, you can roughly split it into **vision, strategy, execution**. With AI, **execution has become a lot more trivial** than it was a few years ago… that said, you need higher-level systems for people to coordinate toward a common goal."
- **[HIGH]** "I was super impressed by all the programs you guys have put into place to absorb this change and deliberate it across your organization. That definitely requires a lot of deliberate thought."
- **[HIGH]** (does Anthropic help teams build structures) "It's a bit of both… my old team was **Apply AI** — we'd work very closely with companies to build technical processes, products, change management… but there's so much bottoms-up experimentation that anyone can pick up these tools and do something unique and novel."
- **[HIGH]** (autonomy spectrum) "Think of a copilot or chatbot — you're still in the loop, but increasingly giving more autonomy to the LLM. On the execution layer we're giving a lot of autonomy… as the models get better it'll go up that stack… it's like humans going from walking to horses to cars — the layer of abstraction you're operating at is just much higher."
- **[HIGH]** "I definitely find Claude giving me novel ideas these days, synthesizing different sources of information internally and externally."
- **[HIGH]** (slop / volume) "If you're producing ten times the volume of code, **there's like ten times the QA**… LLMs have certain failure modes… before I was spending more time writing the code; now I'm probably spending more time **QA-ing the code, making sure it follows the right architecture and design patterns.**"
- **[HIGH]** (visual sameness / design) "The model is very good at writing code if you format the instructions as a front-end problem — more tactical. But things that are fuzzy — **why is something beautiful** — that's very hard to convey in written language… we'll see the models get very good, but under the hood we're breaking it down into a mathematical or scientific manner that's easy to verbalize rigorously. And **that last mile of human intuition, judgment, taste — that'll be the last thing to go.**"
- **[HIGH]** (creativity) "There's a book… **Steal Like an Artist** — the assertion is that every good piece of art is a remix of some other piece of art. If you give the model a reference and have it remix it in some way… you're almost **asymptotically approaching what real creativity can be**. That said, the biological brain has an amazing capability to do things the silicon brain definitely can't."
- **[HIGH]** (the design skill) "A lot of our front-end capabilities comes from a **frontend design skill, which is something that I wrote** — a set of instructions to make the model more creative. I definitely saw the model get to a point where it was designing front-ends **way better than what I was designing**… I'm more of a code guy, not a design guy — I'm sure there are grandmasters at the skill — but a lot of stuff is relatively on-distribution, which is what models are good at." *(ASR rendered "frontend design skill" as "foreign design skill.")*
- **[MED]** (next paradigm) "The place you start from is the customer problem… on the technical side, **what is the model capability I'm trying to invoke** or express? Agentic coding wasn't even a thing three years ago because we didn't have the capability to harness… the successful folks say, 'We understand this market and these pain points really well, the model is getting good at these capabilities, and we have a unique edge in how we wrap that into a delightful experience.'" *([VERIFY] "invoke" @42:23.)*
- **[MED]** (harness engineering, audience Q) "Harness engineering is the layer immediately wrapping the model — system prompt, tooling, sometimes GUI, anything on the product layer. I'm very much a harness-engineering guy… Claude Code is a great example: we had the model and the capability, but it wasn't until we put it in this [harness] suit that it could go do these things. Someone writes the perfect prompt, orchestrates the tools correctly, and **suddenly the model achieves state-of-the-art performance** — we're seeing that over and over." *([VERIFY] ASR garbled the harness metaphor as "RNN suit" — paraphrase, don't quote the literal phrase.)*

### Moderator (unnamed Fin employee — paraphrase only; do not publish a name)

- **[HIGH]** "Brian leads product for us at Fin. He came in and did this presentation last minute… Brian usually speaks at two-X speed. I think we were only at one-point-five-X today."
- **[HIGH]** "I joined Fin in January, non-technical person… on my second week [joined] the hackathon… I finished **a hundred and thirty out of seven hundred** people. I didn't get into the top hundred, though."
- **[HIGH]** (to Prithvi) "Your title is Member of the Technical Staff — so that could mean you're the recently resigned CTO of a major SaaS company. [joke] … These tools really **flatten an organization** — they give everyone access to capabilities and skills they never had before."
- **[HIGH]** "We are paying you guys a ton of money, and we're happy to do so."
- **[HIGH]** (Netflix parallel) "Netflix's big pivot was at a massive threatening point… they had to let a lot of people go. There are parallels with our story… and then there's Netflix's famous culture deck. What is it about the **DNA of the leadership team** that allowed this?"
- **[HIGH]** "Claude Code was built using Claude Code… do you think we get to a point where **AI helps us decide what to build**?"
- **[HIGH]** (show of hands) "Show of hands — companies where people have access to [agentic] code creation for free… now, show of hands for anyone who's discovered that **the volume of what you're creating is becoming a problem**… So is more better? Are we sacrificing quality for more? **Where are you starting to see slop emerging?**"
- **[HIGH]** "AI defaults to a very similar visual language — the fifty dashboards that all look the same… how much is left in the UX world before these tools take that over?"
- **[HIGH]** "What does the experience look like in two years — what does the product world shift to in twenty twenty-eight?"

### Audience

- **[HIGH]** (speaker_3) "Prithvi, can you say something about how **harness engineering** is gonna affect the way we use things like Claude in the future? It should improve a lot of the inefficiency, rule out repeats, focus the selection of workflows/tokens."
- **[HIGH]** (speaker_3) "Question for Brian — on the last **earnings call for Zoom**, they talked about their product being a gateway for all of agentic in the enterprise. **How does Fin fit in the overall enterprise ecosystem for agentic?**"
- **[HIGH]** (speaker_4) "Brian — what has changed for you since we last met [at OpenAI's office]? What's the difference between these two larger LLM providers? And Prithvi — what's the future of LLMs… where does Claude stand… what about open-source LLMs?" *(Recording cuts off during Brian's answer.)*

---

## 6. Pro-Tips (actionable)

1. **Make it a goal so you're forced to measure it.** Naming "2X" converted a vibe into a tracked metric — "make this a goal, and therefore measure it."
2. **Pick a "good-enough" proxy fast; don't spend three months perfecting the metric.** Merged-PRs-per-head was admittedly crude — and "one of our best decisions." Then triangulate it with downstream signals so it can't be gamed.
3. **Run a gamified, company-wide hackathon to manufacture the "mental unlock."** A real-time **individual** leaderboard + a buildable mini-RAG target turned non-engineers into addicts. Open it to *everyone* (Fin got 700+ participants), require it for R&D.
4. **Onboard the agent like a senior hire.** Give Claude the same context, conventions, code-review standards, and skills you'd give a new staff engineer — encoded as plugins/skills/hooks. (Fin: 13 plugins, ~100+ skills/hooks, ~70 contributors.)
5. **Bake adoption into performance reviews.** "Not optional." EMs had a 10-PR floor; engineers a 90%-by-end-Feb target. Force the behavior, then operationalize it.
6. **Always show cost-per-unit-of-output, not just spend.** $128K/week looks alarming alone; cost-per-PR falling 45% reframes it as efficiency. Show both numbers together.
7. **Hunt the *new* bottleneck.** Speeding execution exposes downstream bottlenecks — code review (taught to Claude, ~20%), QA, product discovery, customer feedback loops. "Rebuild the thinking of the factory," don't electrify the old one.
8. **Keep PRs small and single-purpose.** "Solve one problem, test that" — under-20-line PRs are the shape that earns auto-approval and keeps quality up.
9. **Audit suspicious wins with an LLM.** When the bug burndown looked too good, they used an "LM" to check how many closes were duplicates/no-ops — only ~5% were non-fixes.
10. **For fuzzy/creative tasks, give the model a reference to remix.** Reframe "make this beautiful" as a tactical, well-specified task; "give the model a reference and have it remix it."
11. **Build domain "guidance skills" for non-engineers.** "Claude for data" encodes the right tables/metrics so non-experts stop pulling wrong numbers — 2,000+ self-serve reports resulted.
12. **Re-ask the big strategic question every ~3 months.** "Are we going big enough?" — treat all-in as a recurring decision, not a one-time bet.

---

## 7. Best Practices / Patterns

- **Two-phase adoption (encourage → force).** Bottoms-up to surface champions; top-down mandate to cross the chasm. The flatline is expected — plan for it.
- **A written "skill" is the unit of capability — said convergently by both companies.** Fin's engineers build eval/RAG/observability/incident-response skills; Anthropic's Prithvi hand-writes the frontend-design skill. Leverage lives in the skill file, not the one-off prompt. *(Alignment doc flags this as a synthesis candidate with a prior "nobody reads the skills" thread.)*
- **Treat the agent as a system you iterate.** "Hundreds of iterations and loops… every time it's not working, fixing that" — a flywheel of plugins, skills, hooks, contributed by ~60–70 people.
- **Smaller PRs as a quality lever.** Under-20-line, single-purpose PRs are the auto-approval target; review itself is taught to Claude.
- **Triangulate the headline metric.** PRs/head → defect burndown → cost-per-PR → breaking-change rate (−35%) → deploy frequency (>2×) → product-change velocity (>2×). No single number stands alone.
- **Leadership must drive, not just endorse.** "CTO-level decisions"; "a mandate's not enough — you actually gotta operationalize it."
- **Manage the distribution, not the average.** Persistent, large variance in per-person efficiency even post-adoption — go after the long tail explicitly.
- **Extend beyond engineering.** Claude-for-data, GTM tools (AI answer optimization, data-quality engine, automated outreach) — "we gave *everyone* the tools."

---

## 8. Pitfalls / Anti-Patterns (what broke / what stalls)

- **"Just give everyone AI and get out of the way" stalls.** Six-month flatline under no-limits bottoms-up — "mediocre adoption, very little standardization, no real meaningful change."
- **Volume-without-QA = slop.** "Ten times the volume of code → ten times the QA." The room confirmed by show of hands that output volume itself is becoming a problem.
- **Mistaking model capability for the whole story.** The Dec–Jan model step-change was necessary but **not sufficient**; without the cultural/system work it stays flat.
- **Over-engineering the metric before shipping.** The trap they explicitly avoided — "rather than spending three months trying to get the right metric."
- **Trusting too-good numbers without an audit.** They were "suspicious — do we really buy this?" and checked for duplicate/no-op closes before believing the burndown.
- **Averages hide the distribution.** "Huge discrepancy" persists; don't celebrate the mean.
- **Cost denial.** "This doesn't solve the spend problem." Per-unit deflation ≠ lower total spend; budget for the bill ($128K/week peak, "not yet optimized").
- **Thinking too small.** The recurring human failure mode — under-scoping what you ask the model to build.
- **Faster code ≠ faster product.** Execution speeds up; discovery, customer feedback, and big-uncertainty work do not — "building new products is murkier."

---

## 9. Hot Takes

- **"The best way to get behavior change is to force it."** A direct repudiation of bottoms-up AI-adoption gospel.
- **"You have to be willing to make our own business die."** Self-cannibalization as explicit strategy.
- **"Gamification works as a drug."** Said admiringly — the leaderboard was the conversion engine ("do you taste the drug of what Claude Code is?").
- **Execution is now trivial; taste is the moat.** (Prithvi) "That last mile of human intuition, judgment, taste… will be the last thing to go."
- **The GUI is moving to the background; chat becomes the primary UI** — but "the rest doesn't go away; you still need reference artifacts." (Brian — goal-driven vs task-driven.)
- **"AI is a convergent force."** Product boundaries are dissolving; "everyone feels like they're on some version of a collision course." (Brian, attributing the phrase to a co-founder.)
- **EMs must ship code.** "Stop just being on the sidelines managing. Everyone is contributing here." (Management-as-coding-IC, enforced via reviews.)

---

## 10. Substantive Insights (ranked)

1. **Force beats encourage — with an in-company A/B test.** The 6-month flatline (Phase 1) → forced-adoption breakout (Phase 2) is a rare natural experiment on AI-rollout strategy. Highest-value, most contrarian takeaway.
2. **2X was measured, and the proof is multi-metric.** 5.2× faster merge, 1,780→420 burndown, <40%→>90% agent-driven PRs, −45% cost-per-PR, −35% breaking changes, >2× product velocity. The triangulation is the credibility.
3. **The cost story cuts both ways.** $128K/week peak ("not yet optimized") *and* 45% cheaper per PR. All-in is simultaneously expensive and deflationary — the most nuanced, least-quoted number in the deck.
4. **The "skill" is the unit of capability — convergently, from both Fin and Anthropic.** A portable, version-controlled instruction file is where leverage compounds; Fin distributes them as plugins; Anthropic ships them (frontend-design skill).
5. **Value migrates up the stack as execution collapses.** QA, architecture, product discovery, taste become the bottleneck and the differentiator (Prithvi). Redesign the factory, don't electrify it.
6. **"Everyone" is literal — and qualitatively new.** Non-engineers vibe-coding to "a reasonable place"; a co-founder mid-leaderboard; Claude-for-data, GTM tools. The "we gave everyone the tools" claim is visible in the leaderboard itself.
7. **Distribution variance is the real management problem.** "Huge discrepancy" persists post-adoption; the average flatters, the tail is where the program lives or dies.
8. **The change was driven by recurring forcing functions, not one decision.** "Every three months… are we going big enough?" — all-in as a repeated re-commitment.

---

## 11. Anecdotes

- **The vacation leaderboard.** An engineer on holiday couldn't put the hackathon down — "you're spending way too much time on this damn leaderboard, come back to the family." The gamification "drug" in one image.
- **The non-technical moderator's 130/700.** A non-technical Fin hire (joined Jan 2026) entered the hackathon in week two and placed ~130th of 700 — proof the unlock reached beyond engineers. (He noted, wryly, he didn't crack the top 100.)
- **The co-founder mid-leaderboard.** Ciaran Lee, Intercom co-founder/former CTO, sits at #3 (25.65) on the leaderboard slide — leadership in the arena, not above it.
- **"Suspicious — do we really buy this?"** When the bug burndown looked too good, they used an LLM to audit how many closes were duplicate/no-op. Only ~5% were non-fixes.
- **"We're running out of stuff to do."** A team asked Brian for *more roadmap* after execution sped up — "you never hear that."
- **Raptor 1→3.** Brian used SpaceX's engine evolution (messy → "beautifully clean and simple") as the visual for how their internal system matured through "hundreds of iterations and loops."
- **The "recently resigned CTO" joke.** The moderator riffed that "Member of Technical Staff" at Anthropic "could mean you're the recently resigned CTO of a major SaaS company" — a wink at how flattened/fluid AI-org titles have become.

---

## 12. Concept Glossary (★ = flagged for enrichment; not fully defined in folder)

- **2X / 2X** — Fin's named goal to double R&D productivity, set deliberately *as a goal so it would be measured*. Hit in 9 months; claimed 3X over 16 months.
- **Merged-PRs-per-R&D-head** — the chosen "good-enough" proxy productivity metric (denominator = all of R&D: PMs, designers, engineers).
- **Auto-review / Claude reviewing code** — Claude reviewing & approving PRs to relieve the human-review bottleneck; reached ~20% in-talk ("higher now"). ★ exact auto-approval % not narrated; slide 7 (per alignment doc) shows 19% — verify against deck.
- **Harness / harness engineering** — "the layer immediately wrapping the model — system prompt, tooling, GUI, anything on the product layer." Prithvi's specialty. ★ the "RNN suit" phrasing is an ASR garble — the harness/scaffold concept is the intended meaning.
- **Skill / Agent Skill** — a portable instruction file encoding how to do a task (frontend-design, RAG eval, observability, incident response). The unit of capability both companies build and distribute.
- **Frontend design skill** — a Claude skill Prithvi wrote: "a set of instructions to make the model more creative." ★ co-authors/install metrics not in folder.
- **Plugins / hooks** — packaging/automation layer for shipping skills to Claude inside Fin's dev workflow (13 plugins cited).
- **Claude for data** — Fin's internal plugin that constrains data queries to the right tables/metrics so non-experts get correct numbers.
- **Goal-driven vs task-driven** — the interaction shift: you shape *the goal* conversationally rather than issue granular tasks; the GUI recedes.
- **"AI is a convergent force"** — a Fin co-founder's phrase: AI dissolves the boundaries you draw around a product's scope.
- **Cowork / Operator** — agentic-workspace surfaces Brian referenced as candidate "future of all apps." ★ which company's products these are is not disambiguated in folder.
- **Fully-loaded cost-per-PR** — (payroll + AI spend) ÷ merged PRs; the deflation metric (−45%).
- **Forward-deployed engineer** — a role Fin "went all in on" that they "never had before." ★ defined only by reference.
- **"Steal Like an Artist"** — book (Austin Kleon, per alignment doc) Prithvi cited: "every good piece of art is a remix."
- **Apply AI / Labs (Anthropic)** — Prithvi's current (Labs) and former (Apply AI) teams; Apply AI does hands-on company change-management/build work.

---

## 13. Tools / Companies Mentioned

| Tool / Company | What it is (per folder) | How it came up |
|---|---|---|
| **Claude Code** (Anthropic) | Agentic coding tool | Central tool; <40%→>90% of PRs agent-driven; "do you taste the drug of what Claude Code is?" |
| **Claude** (Anthropic) | Model | "Onboard your agent, Claude, like a senior engineer"; reviewing code; giving novel ideas |
| **Anthropic** | Model + Claude Code provider; Prithvi's employer | "Shipping lots of money to Anthropic"; Labs / Apply AI teams |
| **Fin** (formerly Intercom) | AI customer-service company + the AI agent product | Subject company; renamed from Intercom "a couple weeks ago"; ~1,400 employees |
| **"Claude for data"** (internal Fin plugin) | Data-query guidance layer | 2,000+ self-serve reports |
| **Internal AI-built GTM tools** | AI answer optimization, data-quality engine, automated outreach | Shown from "an all-hands today" |
| **RAG system (mini)** | The hackathon build target ("build your own RAG system for Fin") | The gamified onboarding artifact |
| **Operator / cowork** | Agentic workspace surfaces | Brian's "future of all apps" musing |
| **SpaceX (Raptor 1/2/3)** | Engine-evolution image | Iterate-toward-simplicity metaphor (slide 5) |
| **Zoom** | — | Audience Q on agentic enterprise positioning (Zoom earnings call) |
| **Netflix** | — | Moderator's culture-deck / existential-pivot parallel |
| **OpenAI / ChatGPT** | — | The Nov 2022 catalyst; audience member referenced a prior meeting "at OpenAI's office" |
| **Google Fonts** | — | Prithvi's example of a "tactical" framable front-end task |
| **GenAI Collective NYC** | Host community | Per alignment doc, organized by Prithvi |
| **"Steal Like an Artist"** (Austin Kleon) | Book | Prithvi on creativity-as-remix |

---

## 14. Stat Bank (slide- and speech-sourced; no invented precision)

> "slide" = read from the 9 photos via `slide-transcript-alignment.md` (authoritative for numbers not spoken aloud); "spoken" = narrated in the diarized transcript. Where a slide value was not separately narrated, cite it as "slide," not "Brian said."

| Stat | Value | Source |
|---|---|---|
| Productivity goal | 2× R&D productivity | spoken |
| Time to hit 2X | **9 months** | spoken |
| 16-month figure | **3×** | spoken |
| Intercom growth trough | **~4%** (≈Q1'23) | slide 1 |
| Intercom growth recovery | **37%** projected (Q4'26) | slide 1 |
| Fin revenue share | **>half of business** by end of year | spoken (forward projection) |
| Phase-1 flatline duration | **~6 months** | spoken / slide 3 |
| Open defects (peak) | **~2,000** ("nearly two thousand") | spoken |
| Bug burndown | **1,780 → 420** (Apr'25→Apr'26) | slide 6 |
| Total bugs resolved | **2,500+** | spoken / slide 6 |
| New incoming absorbed | **1,400+** | slide 6 |
| Audited non-fix closures | **~5%** | spoken |
| Teams at zero defects | "teams with zero defects" (no count) | spoken |
| Product age | **~12 years old** | spoken |
| Median time to merge | **5.2× faster** | slide 7 |
| Auto-approved merge time | **14.6 min** (vs org median 73.8 min) | slide 7 |
| % of PRs auto-approved | **19%** (60% evaluated; 50% goal line) | slide 7 |
| Auto-approved PR size | **86% ≤20 lines** (41% 1–5, 45% 6–20, 11% 21–50) | slide 7 |
| % of PRs Claude-written | **<40% → >90%** over ~3 months | spoken |
| Claude reviewing PRs | **~20%** in-talk ("higher now") | spoken |
| Breaking-change reduction | **−35%** (while >2× deploys) | spoken |
| Weekly deployments | **more than doubled** | spoken |
| Code quality | "for the first time crossed into the green" | spoken |
| Peak weekly Claude Code spend | **$128K** (ramp ~$10K Jan 5 → $128K mid-Mar) | slide 8 |
| Cost-per-PR decline | **45%** (Oct $1,097 → Mar $603; Dec spike $1,477) | slide 9 |
| Product-change velocity | **>2×** | spoken |
| Company headcount | **~1,400** ("fourteen hundred") | spoken |
| Hackathon participants | **700+** | spoken |
| Plugins | **13** | spoken |
| Skills/hooks | **~100** (March, growing) | spoken |
| Skill contributors | **~60** (March) → **~70** (Feb '26) | spoken |
| EM requirement | **10 PRs shipped** | spoken |
| Engineer PR target | **90% by end Feb '26** | spoken |
| Self-serve data reports | **2,000+** | spoken |
| Moderator hackathon rank | **~130 / 700** | spoken |
| Leaderboard top scores | #1 Henry Larkin 26.96 · #2 Miles McGuire 25.68 · #3 Ciaran Lee 25.65 | slide 4 |
| Talk pace | "1.5×" (moderator's joke; "Brian usually speaks at 2×") | spoken |

*Numbers explicitly NOT included (web/essay-only, not in folder): Salesforce acquisition price, ARR/NRR figures, frontend-design-skill install counts, 267-skills/153-contributor cumulative totals, ~500 R&D denominator. Flag these for enrichment if a public asset needs them.*

---

## 15. Documentarian Angles (GTM / revenue lens)

1. **"Is 2X real? I read the receipts."** A scorecard post: claim → slide → caveat. Lead with the audited triangulation (5.2× merge, 1,780→420 burndown, −45% cost-per-PR), then keep it honest with the two costs the headline hides (the 6-month flatline + $128K/week spend). *Visual: claim → evidence → asterisk scorecard — not a re-printed chart.*
2. **"The bottoms-up AI rollout is a myth — here's the org that proved it."** The force-beats-encourage thesis for GTM/RevOps leaders rolling AI into sales/CS. The hackathon as the conversion play. *Visual: the two-phase adoption curve (flatline → breakout) with the forcing functions labeled.*
3. **"$128K/week — and cheaper than ever."** The cost-paradox post: spend exploded *and* unit cost fell 45%. A CFO-grade reframe of AI spend as efficiency — directly useful to anyone building an AI business case. *Visual: dual-axis (spend up, cost-per-PR down).*
4. **"The skill is the new unit of work."** Synthesis candidate (per alignment doc) with the prior "nobody reads the skills" thread: both Fin and Anthropic treat the written skill file as the leverage point; Fin distributes them as plugins. *Visual: where leverage moved — prompt → skill → skill-marketplace.*
5. **"Execution is free now. Taste is the moat."** Prithvi's value-stack frame for a GTM/PM audience: as execution collapses, differentiation moves to discovery, judgment, and taste — the "last mile." *Visual: the vision/strategy/execution stack with the value arrow moving up.*
6. **"Onboard your agent like a senior hire."** A practitioner post on the operational pattern — plugins/skills/hooks, performance-review mandates, EM 10-PR floors — for leaders standing up an internal AI program. *Visual: the "agent onboarding checklist" (context, conventions, review standards, skills).*

*(Cadence note: angle #1 is the lead per the alignment doc's "measured, not a vibe" pick; #4 is the cross-event synthesis candidate — max 1 synthesis post/week.)*

---

## 16. Open Loops & Verification Flags

- 🔴 **Moderator name — UNKNOWN.** Do not publish or quote verbatim. The "Christy" in `…Transcript.txt`/`slide-transcript-alignment.md` is an **ASR mishearing of "Prithvi"** — the diarized .md shows Brian saying "Does that align with your thinking, Prithvi?" at that exact moment. (Correction to the alignment doc.)
- 🔴 **"Dara / Darren / Tara"** — the 2X-letter author Brian loosely calls "our CEO." ASR-uncertain internal name; do not publish. Alignment doc notes the public returning CEO is **Eoghan McCabe** (Brian's "Owen" ≈ Eoghan). The letter's author and the returning CEO may or may not be the same person — **unresolved from folder sources.** *(Web enrichment in the sibling brief identifies the author as Darragh Curran — deliberately excluded here as out-of-folder.)*
- 🔴 **Other internal Fin names** ("Mario" principal eng; "Sarah" @11:14, conf≈19%) — ASR-uncertain; do not attribute quotes.
- 🟡 **"RNN suit" @~43:53** — ASR garble of Prithvi's harness metaphor; intended sense = the harness/scaffold around the model. Paraphrase, don't quote literally.
- 🟡 **Moderator calls Brian "Ryan" / "Green Product"** (@32:31, @41:00) — ASR/aside artifacts; it's Brian Donohue throughout. Do not introduce a "Ryan."
- 🟡 **Low-confidence ASR words** (from REVIEW list, logprob < −1.0): `technical` @25:32 · `MRI` @26:03 (context word) · `ChatGPT` @26:04 · `He's` @07:16 · `Sarah` @11:14 · `invoke` @42:23 · `peripheries` @04:47 (Brian's "putting it into [PR] reviews") · `quality` @31:33 · `season` @33:03 · `Green` @32:37 · `office` @48:56. Paraphrase around these.
- 🟡 **Slide-vs-speech numbers.** Slides 6–9 (burndown, PR triptych, $128K spend, −45% cost) were photographed but **not narrated** in the captured audio — cite as "from Fin's deck," not "Brian said." Slide 3 y-values are illegible — describe as "flat," don't quote values.
- 🟡 **Auto-approval / merge-time precision** — only the slide carries 14.6 min / 73.8 min / 19%; the transcript narrates ~20% review and "<40%→>90%" written. Treat slide figures as deck snapshots.
- ✅ **Speaker split confirmed** by diarization (+ alignment doc / Alex's in-room recall): Brian = 2X deck + Raptor slide; Prithvi = design/creativity/harness; moderator ran Q&A. *(This brief resolves the alignment doc's "Raptor slide attribution uncertain" flag to Brian — he narrates the SpaceX/factory passage directly.)*
- ⚠️ **Recording is partial** — cuts off ~49:35 during Brian's answer to the final audience question (OpenAI-vs-Claude / future-of-LLMs). Brian's comparison answer and Prithvi's open-source-LLM answer are **not captured.** Audio file (`…Recording.m4a`) and 9 slide photos are in the folder if deeper recovery is needed.

### Enrichment targets (would require out-of-folder sources)
1. Identity of the 2X-letter author / the returning CEO (and whether they're the same person).
2. The moderator's name.
3. Companion-essay numbers (267 skills / 153 contributors, defect-% reduction, ~500 R&D denominator, idea-to-ship time) — cited in the sibling brief from `ideas.fin.ai`, not present in folder.
4. Frontend-design-skill provenance (co-authors, install counts).
5. Any post-event corporate developments (rename confirmation date, ownership changes) — explicitly out of scope here.

---

*Built 2026-06-27 · Folder-only sources: ElevenLabs Scribe-v2 diarized transcript (primary, ~50 min partial) + `…Transcript.txt` (cross-ref) + `slide-transcript-alignment.md` (9 slides) + REVIEW low-confidence list. No web enrichment. Internal Fin personal names excluded from all public-ready copy. A sibling web-enriched brief (`POST-EVENT BRIEF — 2x AI by Fin (6-4-26).md`) exists in this folder with additional out-of-folder context.*
