# POST-EVENT BRIEF — NYC GTM+AI Masterclass #5 (NY Tech Week Special)

**Event:** NYC GTM + AI Masterclass #5 — NY Tech Week Special
**Date:** 2026-06-03 (Tue), evening
**Venue:** Insight Partners HQ, NYC
**Host community:** NYC Go-To-Market (GTM) Community (founder: Nimo Shkedy, "Nemo")
**Sponsor:** Swan (20% discount credits)
**Format:** 5 sequential practitioner case-study talks (≤15 min + ~5 min Q&A each), then networking
**Attendance:** ~100 ("about a hundred of our soon-to-be closest friends" — Jack)

**Sources used for this brief (folder-only):**
- `…— Transcript (Scribe v2).md` — PRIMARY (ElevenLabs Scribe v2, diarized, ~119 min, 42,385 tokens, 6 raw speaker IDs)
- `slide-transcript-alignment.md` — slide/entity ground truth (22 slide photos hand-aligned to transcript)
- `06 03 26 … Recording — REVIEW (low-confidence spots).md` — ASR logprob flags

> **⚠️ Diarization caveat (applies throughout).** Raw `[speaker_N]` tags are NOT reliably 1:1 with people — they swap mid-segment and a single person spans multiple IDs (e.g., during Nikita's talk she is tagged `speaker_1`, the same ID used elsewhere for Nemo; during Kenny's talk he is `speaker_2`, the same ID used for Sangram and Jack). **All attributions below are reconciled by content and segment, not by speaker number.** Confidence is tagged HIGH / MED per item.

---

## 1. Quick Take

Five GTM practitioners — from a category-creating advisor to a 7-person cold-email shop to a $400M-ARR enterprise platform — each demoed the *same* AI-agent reference architecture (context store → connectors → agents/skills → human approval loop) at radically different maturity levels, and converged on one word they couldn't stop saying: **harness**. The night's real tension wasn't AI-vs-human; it was the spine of the evening: Kenny (CoverForce) *industrializes* cold outbound with a Claude-Code ABM bot, while host Nemo stood up and declared **"co-creation is going to replace cold outreach."** The most quotable through-line — repeated independently by three different presenters — was **"I never read the skill files."**

## 2. The Thesis

GTM is being rebuilt by individuals wielding agent harnesses, and the 2026 frontier is moving the harness off the solo operator's laptop into a **shared, cloud, multiplayer** layer (internal: whole team on one context/skills/agents stack; external: networks and co-creation replacing flooded cold channels). The model is no longer the bottleneck — **context + connection + a trained human-in-the-loop approval loop** is. Everyone agreed agents are employees you train (3× the upfront effort, then permanent leverage); nobody claimed full autonomy.

## 3. Pre→Post Gap

**No pre-event brief file exists in this folder.** The `slide-transcript-alignment.md` references a pre-event research brief that lives in **Notion** ("NYC GTM+AI Masterclass #5 — Research Brief"), not on disk, so a true pre→post diff cannot be done from folder contents alone. What the alignment doc *records* about the gap (treat as secondhand, verify against Notion):

- **Pre-event roster (4):** Sangram Vajre, Nimo Shkedy, Eric Nowoslawski, Jennifer Schwarz.
- **Added after the brief (content presenters):** **Nikita Bokil (Optimizely / Opal)** and **Kenneth "Kenny" Tsai (CoverForce)** — both Insight Partners portfolio companies, slotted in by the venue. **Jack (Insight Partners AI Lab)** did the venue intro and is not in the brief.
- **Action implied:** Nikita, Kenny, and Jack have no Notion People records yet → create on commit. Jack maps to the brief's "Insight onsite" job-search target.

## 4. Speaker Map (content-derived, confidence-tagged)

| # | Name (reconciled) | Role / Company | Raw IDs seen | Attribution confidence | Notes |
|---|---|---|---|---|---|
| 1 | **Jennifer Schwarz** | MC / co-host, NYC GTM Community | speaker_0 | HIGH | Self-IDs by name (line 5). Surname Schwarz (brief) vs "Schwartz" (ASR) — MED. |
| 2 | **Nimo Shkedy ("Nemo")** | Founder, NYC GTM Community; founder of **Two Hops** (GTM agency, "network operations"); ran Swan/S1 demo | speaker_1 | HIGH | Self-IDs: "I'm Nemo… founder of NYC GTM and also of Two Hops." Alignment doc also calls him "Impact 11" — DISCREPANCY, flag. |
| 3 | **Jack** | Insight Partners — **AI Lab** (applied-AI advisory team); venue host | speaker_2 (intro) | HIGH (first name only) | Surname unknown. "I am not an investor… I work on the AI Lab." |
| 4 | **Sangram Vajre** | Co-founder, **GTM Partners** (advisory); ex-Terminus co-founder, ex-Pardot | speaker_2 (his talk) | HIGH | ASR variants: "Sangram Enjay," "Sandra." Surname Vajre confirmed via slide footer + book brand. |
| 5 | **Eric Nowoslawski** | Founder, **Growth Engine X** (cold-email agency); early Clay (employee #~10) | speaker_3 (his talk) | HIGH | Jennifer's intro garbled to "Harry" once; self-ID via Growth Engine X + Clay is decisive. |
| 6 | **Nikita Bokil** | **Optimizely** — works on **Opal** (AI agent harness for marketers) | speaker_1 (her talk) | HIGH (content), MED (raw ID collides w/ Nemo) | "I work at Optimizely, specifically working on Opal." |
| 7 | **Kenneth "Kenny" Tsai** | Head of Marketing / "GTM engineer," **CoverForce** (Insight portfolio) | speaker_2 (his talk) | HIGH (content), MED (raw ID collides w/ Sangram/Jack) | "I am the Head of Marketing here at CoverForce." |

**Audience voices (unidentified):** several Q&A askers tagged speaker_2/3/4/5; "Shlomo" and "Amandeep" named in passing by Nemo; "Jared," "Jeremy" (Swan), "Patrick" referenced. None reliably attributable beyond first name.

## 5. Full Quote Bank (every quotable line, whole, attributed, confidence-tagged)

### Jennifer Schwarz (MC)
- **"When you bring the right people together in the right space with the right content, the right learning, magic happens."** — HIGH
- "We're living in a time and place when knowledge and tech development is happening so fast, we have to share knowledge… 'cause no one can do it on their own." — HIGH
- "Raise your hand if you've used Claude, ChatGPT, or an AI tool in the last twenty-four hours to do go-to-market work… Okay, you came to the right event." — HIGH
- "Raise your hand if you have found yourself at one AM hacking go-to-market workflows… you guys should call each other 'cause that's what community does." — HIGH
- "This is the fifth Masterclass, five months in a row… it keeps growing and growing." — HIGH
- "Sometimes I have to be the bad guy." (on cutting off Q&A) — HIGH

### Nimo Shkedy ("Nemo," host)
- "It started as a WhatsApp message to the YC Founders group here in New York City two years ago… 'If we did a go-to-market masterclass, would you wanna attend?' And everybody said yes." — HIGH
- "The first three events were at Clay's headquarters, and here we are at Insight Partners headquarters." — HIGH
- "All of us are doing this by ourselves… The challenge now is how to do it as part of a team." — HIGH
- "I'm Nemo. I'm the founder of NYC GTM and also of Two Hops, a go-to-market agency specializing in network operations. I'm here to talk to you about multiplayer GTM." — HIGH
- "There's only two people here whose AI systems are actually connected to everybody else's AI systems." — HIGH
- "When you're doing it this way [solo silos], you're not utilizing the whole brain, and you're not utilizing your whole organization." — HIGH
- **"It's not your Claude Code or your Codex that you're using alone on your computer with your own skills… but it's something bigger than that."** — HIGH
- "They live on your PC. If you're away, then your team can't access them. So there is a new generation coming… the same things that Claude Code is doing on your computer, but in the cloud for your whole team to use." — HIGH
- **"The word that I almost asked all of the speakers not to say, but everybody ended up saying it, is harnesses."** — HIGH
- "Can you guys describe what a harness means to your fifteen-year-old kid?" — HIGH
- On Clay: "I'm a Clay expert, I'm represented in New York City in the Clay World Cup… It's basically an Excel spreadsheet that everyone can use. But not everybody wants an Excel spreadsheet. BDRs can't use it. If they make a mistake, everybody else suffers." — HIGH (note: "Clay World Cup" flagged for sanity-check before public quoting)
- "Eric said he never reads skill files. I never do either. I didn't create this… I just prompted Swan to classify responses." — HIGH
- **"Outreach is flooded. The ads are flooded. People are becoming ad blind, and content is flooded because there's content everywhere."** — HIGH
- **"Co-creation is gonna replace cold outreach. It's gonna replace most of the content… What's going to differentiate you is collaborations."** — HIGH
- "Sangram talked about having a point of view. That's my point of view: co-creation, collaboration, network building is gonna replace cold outreach." — HIGH
- **"Instead of who is a good fit for me, [it's] who has influence over the people that I want to sell to… I don't qualify them by having the right title. I don't qualify them by working at the right company. I qualify them by influence."** — HIGH
- "That's why you need the two degrees out… You don't just want to look at who is the influencer with five million followers. You want to know who is actually viewing their posts and commenting on their posts." — HIGH
- "[Two degrees out] is like your ICP's commenters' commenters." (agreeing with audience paraphrase) — MED (audience framed it; Nemo affirmed)
- "Once you hear a word, you can't unhear it, so you're gonna start hearing this word [harness] again and again." — HIGH

### Jack (Insight Partners, AI Lab)
- "Insight Partners, very simply put, we are investors in software and AI companies… growth equity, so Series B, C, D, and beyond." — HIGH
- "I am not an investor. I work on what's called our advisory team… the AI Lab. I did not name it… you can think of it as an applied AI team for Insight's team internally, but then also for our portfolio companies." — HIGH
- "I came to the last master class, I took so much value from it… 'we need to do something at our space'… fast-forward about a month, and now we're here with about a hundred of our soon-to-be closest friends." — HIGH

### Sangram Vajre (GTM Partners)
- "I went from a ten-million-dollar company to a ten-billion-dollar company." (Pardot→ExactTarget→Salesforce) — HIGH
- "It is not how much more budget you have. It is not how many more people you have on the team. It is really how big you can really think because you get to write the rules. You get to create the playbook." — HIGH
- **"We are all getting to write the new rules of this new playbook together."** — HIGH
- "It really came down to eight questions, and it's called the Go-to-Market Operating System… the companies that do really well, they have incredible clarity around the eight questions. They are not necessarily the best at it." — HIGH
- "I was at Salesforce, and their CRM and data… was crap. I was at Pardot doing marketing automation. Our nurture programs were crap… but what they were all good at [was clarity]." — HIGH
- "We were the first company [that] was actually able to do advertising at the account level… and that created this whole category around account-based marketing." — HIGH
- "Our greatest moat was really community." — HIGH
- "Geoffrey Moore… gave a quote for the book. He said, 'Man, if I were to write Crossing the Chasm again, I would have written Move.'" — HIGH
- "This is literally building your entire go-to-market on one slide." — HIGH
- "Eight out of ten people would talk about a broader ICP than what they should be focused on, and that's the number one reason why companies fail." — HIGH
- "Don't make it complex. Make it simple." — HIGH
- "If you put your website next to your competitor's website and it looks pretty much the same and [has] the same copy, you do not have a point of view. You certainly do not have a differentiated point of view." — HIGH
- **"Anybody can build and replicate a product now… product is no longer the moat. Twenty fourteen, it was."** — HIGH
- "We had one and a half marketer… and we built a five million dollar business in the first three years." — HIGH
- "We never started with leads. We only started with customers… Spending all the time on how you got a customer is way more important than to focus on leads." — HIGH
- **"Go-to-market is the business. That's my greatest revelation… acquiring [a] customer is part of go-to-market."** — HIGH
- "I thought I'm ahead of it. Now I feel like I'm a student of it… because we're all learning at the same time." — HIGH
- **"The CEO owns go-to-market, and therefore go-to-market is the business. So anything that drives business is go-to-market."** — HIGH
- "Who will make the decision between spending more money on marketing or sales? First of all, that's a go-to-market decision and that's a CEO decision." — HIGH
- "Ten years ago the only way to grow was to get more money and hire more people… Now you have AI and Claude and MCP connectors to do a lot of the work." — HIGH
- "You and AI is not going to be your best friend… At some point, you're going to need a human that complements what you do." — HIGH
- **"There is no right answer to any of these questions. It has nothing to do [with] being right. There is no certainty except taxes and death… What this gives you is clarity."** — HIGH
- "Most executives do not have clarity on go-to-market… print this out, let your executive team do it… You'll have your entire go-to-market on a slide, and you will debate on this. You want a healthy debate." — HIGH
- "You will get better results [from] having clarity… than having a perfect answer but nobody really behind it." — HIGH
- "While building Terminus, I almost got divorced… make sure you have that part of it." — HIGH
- "If you don't have roots around whatever faith journey you're on, it is gonna be really hard to build a solid business because the market is so tough." — HIGH
- "Every company is in a problem-market fit… your product is gonna be replicated even before you know." — HIGH
- "If you want to grow, you take someone along with you. So find a great co-founder." — HIGH
- On metrics: "Now it's NRR and revenue per employee… ten years ago… for every hundred thousand dollars we're spending we should get about three, four hundred thousand back… Now it's truly… about a million." — HIGH
- "Most exec CEOs are not trying to hire [someone who needs] a strategy deck and a million dollars of tool and five employees… They want somebody [with] a strategic mind but also [who can] be an operator." — HIGH

### Eric Nowoslawski (Growth Engine X)
- "It's criminal to give someone like Sangram fifteen minutes to just talk… What he did for marketing is basically what William Shakespeare did for the tragedy." — HIGH
- "I run a cold email agency called Growth Engine X. I worked at this little company called Clay when they had ten employees." — HIGH
- "We're sending a hundred thousand cold emails per day on behalf of this one customer, and it's all driven by AI." — HIGH
- **"I kinda accidentally cut my team by fifty percent, and we're sending more emails because I made an AI employee."** — HIGH
- "We've got Dale and Milton. Dale as in Dale Carnegie… and Milton as in Milton Friedman… obviously naming them is the most important thing." — HIGH
- "Who else would agree that you're a little bit frustrated that your team isn't using AI as fast as you want them to?" — HIGH
- "[People say] 'This is groundbreaking technology. Anthropic is a trillion-dollar company. I'll let them figure it out.' But if you hired an employee with that exact same framework… that employee is gonna fail." — HIGH
- **"It's gonna take you more investment to get this thing trained up, but then once you get it trained… it's never going to stop working. It's never gonna take time off. It's not gonna go work for your competitor."** — HIGH
- On security: "I am not a security expert. Do not ask me any questions about this… We use a company called Trigger.dev that hides your API keys… I've never actually given an API key to an agent." — HIGH
- "You wanna pick a harness — OpenClaw, Hermes, whatever… For most people in this room, I highly recommend you just start with Codex first." — HIGH
- **"The three-step framework… you need to solve for context, you need to solve for connection, and then you need to solve for creation."** — HIGH
- "If they're not doing what you want them to do, [it's] your fault… Your business is not that complicated." — HIGH
- **"The models have a one million token context window. The equivalent of written word of one million tokens is the Bible. If you have more context in your company than the Bible, great. But most of you really don't."** — HIGH
- "Just say, 'Can you make a company brain for me in Markdown files,' and it'll be fine." — HIGH
- On connection: "[Before], it was like the days before password managers… 'I need this API key, and I need this API key'… Open up your Chrome browser history, copy-paste the last thirty days… 'Dedupe these and give me a list of all the tools I use.'" — HIGH
- "Maybe don't do this with your employees sharing their screen 'cause… there might be some anime bullshit on there." — HIGH
- The loop: "New Fathom recording detected, pull the transcript, read the company brain and the relevant skills, suggest what to do next. We approve or we make tweaks, and then it automatically saves feedback for the future runs." — HIGH
- **"You are a twenty dollar Codex plan away from changing your life."** — HIGH
- "Other people in my revenue band have like thirty employees. We have seven. We're in a completely different stratosphere of employee headcount." — HIGH
- "I'm only bottlenecked by just checking the AI's work. That's really where I'm bottlenecked… I think we're done cutting people." — HIGH
- "I just think you need to just start recording your life… even when I'm talking to people in person… I'll turn a voice memo on." — HIGH
- "The models are so good. It's just missing your context and your connect[ions]… I think that's all the models are missing right now." — HIGH
- On structuring data: "I don't know. Claude does that. I don't do any of that… Zero ingestion rules, nothing." — HIGH
- "These models are so much smarter than you think. And the context window is so big… I don't do any organization." — HIGH
- "Meeting transcripts and action items, it's got it nailed. That's an easy task for 5.5 at this point." — HIGH
- On harness choice: "I'm using OpenClaw and Hermes. I'm leaning more towards Hermes… as soon as you say 'that's right, you did it right,' [it] just writes a skill immediately, and it never disconnects." — HIGH
- "I literally wiped like three gaming computers, and that's where we're running it from." — HIGH
- **"I've never read a skill file."** (repeated: "No, I don't think I've ever read a skill file.") — HIGH
- "[To review skills] I'll say, 'Create an HTML mockup website and explain to me like I'm five years old with visuals and animations.'" — HIGH
- "AI is freaking awesome. Who cares? You just change the skill." — HIGH
- **"My style of cold email copywriting is I want to send the same message I would send if I were to manually research somebody's company and them personally for ten minutes."** — HIGH
- "One of the best cold email copywriters as far as training is Josh Braun, so I literally have a skill that I stole his course and put it into a skill." — HIGH
- **"Whenever you make a skill, try to make an adversarial skill… 'Pretend this is the worst idea in the world and find every problem.' 'Cause AI will get a bit sycophan[t] and just be like, 'Oh, you're the best guy ever.'"** — HIGH
- "I've never sent copywriting straight from an agent to a customer… there are still what I call meat gates [meet gates], [where] a human has to still be checking some things." — HIGH (transcribed "meet gates"; intent = human approval gates)
- "List building, that's nailed… that's just filters and rechecking the filters. But copywriting, definitely not." — HIGH
- "$400 a month on the agents — a Claude Code Max plan and a Codex Max plan. My AI cost, because we're using AI to write all the emails… I spend 15K a month." — HIGH
- "Would you trust one of your agents to run a sales call? No… I've never even tried to train an agent for a sales call. I don't think that's far away." — HIGH
- "I do think websites will start turning into chatbots pretty soon… 'Well, what do you wanna know?' That's the point of the website, right?" — HIGH

### Nikita Bokil (Optimizely / Opal)
- "I work at Optimizely, specifically working on Opal, which is our AI agent harness that we purpose-built for marketers. Optimizely [does] roughly around four hundred million in ARR. We've been around for a little over two decades." — HIGH
- "These are nine lessons that we've learned over the past two years… in a truly enterprise-ready AI harness." — HIGH
- **"The core problem we've always tried to solve is this coordination across chaos. And it's also very high stakes."** — HIGH
- "When you ship a PR [in engineering] the stakes are quite low… But in marketing… everything that you ship to your customer or a prospect is representative of your brand… legal, compliance, the product team." — HIGH
- "Every customer we work with probably has at least like fifteen different systems that they wanna pull information into." — HIGH
- "The way that we do marketing is changing… SEO, AEO, GEO now — optimizing for AI overviews and showing up in other LLMs." — HIGH
- "Chat is great… but a lot of times you don't want to just be looking at blobs of text… So we've introduced artifacts… and also action cards." — HIGH
- "[Action cards are] widgets… [that] also give the LLM better insights and structured questions… Sometimes you think 'this is a bad response' but it's because you didn't give enough good input." — HIGH
- **"Context is king, context is queen."** — HIGH
- "We think about context at three layers: the organizational layer, the user level, and then the agent level." — HIGH
- "One person needs to go and set that up [org context — brand guidelines, tone, writing style], and immediately the system is super valuable for everybody else." — HIGH
- **"Quality over quantity. Everybody has a HubSpot connector."** (crediting Nemo for the line) — HIGH
- "Our CMO went in, asked… 'Give me data about our top twenty accounts, golden customers'… and it didn't do a good job… So we actually wrote a skill because we had to guide the LLM… a translation layer on top of the raw tool call." — HIGH
- "Agents actually have their own autonomous reasoning loop… Skills are more like a static list of instructions." — HIGH
- **"Agents you can treat as an actual employee that you're able to hand off tasks to… And skills are more like the standard operating procedures."** — HIGH
- "Evals are great because… LLMs are non-deterministic systems… you can have an LLM as a judge. But… how do you still use the playbooks that have worked for decades in software engineering and apply those to agent engineering? There are still deterministic measures of quality." — HIGH
- "[Track] how are your tools performing? Do they run into failures?… thumbs up, thumbs down… trace logs… What tools is it calling? What order? Can you do anomaly detection?" — HIGH
- "One thing that has been a big unlock is actually treating agents similar to humans in the system and giving them an identity… we have agent teammates… [they] get an email address, their own account, roles and permissions, a full audit trail." — HIGH
- "We are starting to move from reactive agentic systems… to really proactive agents… imagine thousands of agents running in the background… you haven't even given them a trigger." — HIGH
- "Human in the loop becomes super critical… Slack is super great [to start], but… systems like a Jira or a ServiceNow were built for a reason — auditability, tracing, assignment." — HIGH
- On governance: "We use our whole RBAC system… [the teammate] gets its own unique identity… effectively it's a user in your system, and you assign the same permissions." — HIGH
- On artifacts: "If you're familiar with MIME types, we've basically built our own custom renderer… based on the MIME type… we've built a custom render of how that displays." — HIGH
- "The thing that we have open-sourced… is the action cards… they work seamlessly across [Microsoft adaptive cards, Slack Block Kit, OpenAI MCP apps]… you build them once, and they display the same way across every application." — HIGH
- "We are effectively building a lot of similar functionality to even a Claude Code or a Codex… we take inspiration from [them], then we need to really solve: what is our harness? What is different about using Optimizely?" — HIGH

### Kenneth "Kenny" Tsai (CoverForce)
- **"One thing about me is I'm pretty lazy. So I try to automate as much repeated work as possible."** — HIGH
- "CoverForce focuses on billion-dollar insurance brokers and wholesalers in the US, so a very limited number of companies that we can target." — HIGH
- "If we are to target one of these companies, there might be a hundred thousand people… insurance has maybe ten thousand VP titles." — HIGH
- On Aon: "They're a sixty thousand people [company]… If we look through [Sigma]/Clay/Apollo to identify filters… I would get around fifteen thousand people… if we target just VP levels and above, that's around three thousand people." — HIGH (note: "Sigma Bill" / "Sigma" is an ASR low-confidence flag)
- "All of our Gong call transcripts are added into our database. All of our HubSpot emails, pipeline data, Notion data, ICP definitions… incorporated into a marketing database I've built out in Supabase." — HIGH
- "I've broken it down into four separate [agents] focused on research, contact selection, copywriting, and routing." — HIGH
- "The research agent's job is to figure out what are their teams, who leads those teams, who works for those people, and who are the competitors." — HIGH
- "Financial statements is a great [signal]… every CEO is gonna be talking about what projects they're working on… [and] any tech initiatives they have are especially effective for us." — HIGH
- **"We also build what I call an online stalker… the best trigger point for us is, do we know anybody that's connected? We will go through, scrape their followers… stalk who they're interacting with… so we can try to build a relationship through that initial connector. And that's worked out with very high conversion rates to meetings."** — HIGH
- "With Aon, we have around sixty thousand contacts initially. We narrowed it down to twelve of our top contacts. And this is done just through a click of a button." — HIGH
- "On LinkedIn, they're not gonna say 'VP of workers' comp.' They might just say 'VP.' So we scrape each LinkedIn work history to identify keywords [for] a specific line of business." — HIGH
- **"This is all through Claude Code… we're just connecting a bunch of different systems together, and it works magically. I also don't ever look at the skills. I don't know what it's doing. But I just tap and it works."** — HIGH
- "This is the one example of our ten-touch cadence. I just call it our ABM cadence. It takes twenty-two days… a mixture between email, LinkedIn, and gifting." — HIGH
- "[This] used to take me maybe four or five hours to set up completely… But now it takes me ten, fifteen minutes of prompting for each company." — HIGH
- "We always send it off a signal… an investor that's been connecting us or an event that they've been speaking at — we always have that before sending something out." — HIGH
- "You don't want to bombard people at a company. It annoys the entire team if you're sending twenty messages to everybody… People talk, and it lowers your reputation in the company." — HIGH
- "We primarily target four contacts per day. We give them like a week grieving period before we move on to the next members of the team." — HIGH ("grieving" likely "grace"/cooldown)
- "[AEs] can approve the sequence… or pause it, which puts it on a ninety-day hold… or press a button on Slack called Edit, which allows them to prompt this ABM bot to make changes to the copy or remove certain people." — HIGH
- "The ABM bot [is] the brain. Contact selection is identifying who we want to target. The research agent is identifying why. The sequence agent is what we're sending. And routing agent is how we're sending it out." — HIGH
- "I don't wanna overwhelm our CRM with garbage data… I [also] don't wanna bother my RevOps person… Once we've identified [a] successful campaign, then we route that information back into [HubSpot]." — HIGH
- "I used Render because I didn't want to ask my engineering team for GitHub access yet." — HIGH
- "It came [about] as just a passion project because I just didn't want to upload lists anymore… Now that we externalized it for the AEs, it's more important that it's live 24/7… I follow engineering procedures." — HIGH

## 6. Pro-Tips (exhaustive — this was a how-to night)

**Context (the company brain)**
1. Treat the model as already smart enough — your only job is feeding it context; if output is wrong, the context is wrong, not the model (Eric). HIGH
2. Build a "company brain" as plain Markdown files; don't over-engineer organization — the 1M-token window ("the Bible") absorbs it (Eric). HIGH
3. Point it at your real systems of record first — Fathom call recordings + Slack were enough for Eric; he has no heavy CRM. HIGH
4. Schedule a daily task that pulls new data (calls, Slack, CRM, email) and updates the brain automatically (Eric). HIGH
5. Layer context at three levels — org / user / agent. Have ONE person set org-level context (brand, tone, writing style) so the whole company gets value day one (Nikita). HIGH
6. "Start recording your life" — flip on a voice memo when you talk through a process in person, then feed it in (Eric). HIGH

**Connection (tools/access)**
7. The 15-minute API-key sprint: have everyone export 30 days of Chrome history, dedupe it in an LLM to get the real tool list, then mint keys once (Eric). HIGH
8. Never hand raw API keys to an agent — route through a key-hiding layer like Trigger.dev (Eric). HIGH
9. Pick ONE harness and start: Codex for most people (desktop + browser control), graduate to OpenClaw/Hermes later (Eric). HIGH
10. Quality over quantity on connectors — 10 well-integrated tools beat 100 shallow ones; wrap raw tool calls in a skill that translates *your* taxonomy (e.g., what "golden accounts" means) (Nikita). HIGH
11. To bootstrap a harness on a machine: install Codex first (easiest), then have it set up Hermes/OpenClaw and the computer-use connections for you (Eric). HIGH

**Creation (the loop + skills)**
12. The improvement loop: trigger detected → pull transcript → read company brain + relevant skills → suggest next action → human approves/tweaks/rejects → save feedback for next run (Eric). HIGH
13. Run agents on a fixed schedule aligned to your calendar cadence (Eric runs his at :05/:35 around 30-min meetings). HIGH
14. Budget 3× the effort to "train" an agent vs. instructing a human — but the payoff is permanent (Eric). HIGH
15. Make an **adversarial skill** for every skill — "pretend this is the worst idea in the world, find every problem" — to counter sycophancy (Eric). HIGH
16. Encode a known expert's framework as a meta-skill (Eric baked Josh Braun's cold-email course into one). HIGH
17. Review skills you won't read by asking the model to render an "explain-like-I'm-5" HTML mockup with visuals (Eric). HIGH
18. Copy standard: "send the same message you'd send if you'd manually researched the person for 10 minutes" — make that the bar baked into the skill (Eric). HIGH
19. Always keep "meat gates" (human approval) on anything brand-facing — Eric never ships copy straight from agent to customer. HIGH

**Enterprise / reliability**
20. Pair LLM-as-judge evals with deterministic software-engineering measures (tool success rate, failure counts, thumbs up/down, trace logs, anomaly detection on tool-call order) (Nikita). HIGH
21. Give agents a real identity — email, account, RBAC roles/permissions, full audit trail — so they're governable like employees (Nikita). HIGH
22. Don't bolt on a separate approval UI; extend the work-management system you already run (Slack to start; Jira/ServiceNow at scale) (Nikita). HIGH
23. Build interface beyond chat — artifacts (typed renderers by MIME type) + reusable action cards that work across Slack/Copilot/MCP apps (Nikita). HIGH

**ABM / outbound engineering**
24. Filter ruthlessly: 60k → 15k → 3k (VP+) → 12 named contacts, then let AEs work only the 12 (Kenny). HIGH
25. Scrape LinkedIn *work history keywords* to recover line-of-business when titles are generic ("VP" → "VP workers' comp") (Kenny). HIGH
26. The highest-converting trigger is a warm path: the "online stalker" finds who you already know connected to a target (Kenny). HIGH
27. Always open with a specific recent signal (financials, tech initiative, event they're speaking at, mutual investor) — never a templated hook (Kenny). HIGH
28. Stagger outreach (≈4 contacts/company/day, ~1 week cooldown) so you don't carpet-bomb a buying committee and tank your reputation (Kenny). HIGH
29. Keep copy <50 words; pull angle from a Notion messaging-strategies playbook keyed to buyer type × ICP segment (Kenny + slides). HIGH
30. Give AEs lightweight Slack controls only: Approve / Pause (90-day hold) / Edit-via-prompt — don't make them read every email (Kenny). HIGH
31. Use a scratch database (Supabase) for experimental marketing data; only promote winners back into the CRM (Kenny). HIGH
32. Use Render (or similar) to host so the agents run 24/7 independent of your laptop (Kenny). HIGH

**Strategy / GTM fundamentals**
33. Put your whole GTM on one slide via the 8-question GTM Operating System; run your exec team through it to force healthy debate (Sangram). HIGH
34. Narrow your ICP — 8/10 founders pitch too broad, the #1 reason companies fail (Sangram). HIGH
35. Start from customers, not leads — reverse-engineer the journeys of the few who actually closed (Sangram). HIGH
36. Buy vs. build small features — Terminus acquired 5 small companies cheaply instead of building (Sangram). HIGH
37. Measure revenue-per-employee / NRR, not just ARR (Sangram). HIGH
38. Network at "two degrees out" — target your ICP's commenters' commenters; qualify by influence, not title/company (Nemo). HIGH

## 7. Best Practices / Patterns

- **The convergent reference architecture** (the night's biggest pattern): context store + connectors + agents/skills + human approval loop — drawn 3 ways at 3 maturity levels: Eric (Context→Connection→Creation, solo), Nikita (Opal stack, enterprise product), Kenny (Signals→Agents→Outbound, mid-market in-house). HIGH
- **Agent = employee, Skill = SOP** — shared mental model across Eric, Nikita, Kenny. HIGH
- **Human-in-the-loop survived every demo** — Eric's "meat gates," Nikita's governance/volume thinking, Kenny's Slack approvals. Nobody claimed full autonomy. HIGH
- **Train, don't instruct** — invest 3× upfront, then permanent compounding leverage (Eric). HIGH
- **Clarity over certainty** — the GTM OS produces clarity and alignment, not a "right answer" (Sangram). HIGH
- **Quality over quantity** — applies to both connectors (Nikita) and network targets (Nemo). HIGH
- **Move the harness from laptop → cloud → multiplayer** — internal shared stack, then external network co-creation (Nemo). HIGH
- **Warm-path beats cold-blast** — even inside an industrialized outbound system, the warm "who do we know" trigger converts best (Kenny). HIGH

## 8. Pitfalls / Anti-Patterns

- **"Anthropic is a trillion-dollar company, I'll let them figure it out"** — outsourcing the context/training work guarantees failure, same as hiring a human with no onboarding (Eric). HIGH
- **Sycophancy** — models default to "you're the best guy ever"; without an adversarial skill you get flattery, not feedback (Eric). HIGH
- **Connector sprawl** — "everybody has a HubSpot connector," but raw remote MCP connections fail on real enterprise questions without a translation skill (Nikita). HIGH
- **Broad ICP** — 8/10 founders over-broaden; #1 failure cause (Sangram). HIGH
- **Starting from leads, not customers** — wastes effort on thousands of leads vs. the few real customer journeys (Sangram). HIGH
- **Product as moat** — replicable in 2026; community/POV/network is the moat now (Sangram). HIGH
- **Same website/copy as competitors** = no differentiated point of view (Sangram). HIGH
- **Carpet-bombing a buying committee** — 20 messages to one company annoys the team, they talk, your reputation drops (Kenny). HIGH
- **Shipping brand-facing copy without a human gate** — Eric explicitly never does. HIGH
- **Solo Claude Code / personal setups don't scale to teams** — they live on one PC, break if shared, vanish on reboot unless saved to Git (Nemo). HIGH
- **Solopreneur + AI is not enough** — "AI is not going to be your best friend"; you still need a co-founder (Sangram). HIGH
- **Flooded channels** — outreach, ads, and content are all saturated; more of the same won't cut through (Nemo). HIGH

## 9. Hot Takes

- **"Co-creation is going to replace cold outreach… and most of the content."** (Nemo) — the single contrarian thesis of the night, in direct tension with Kenny's industrialized cold-outbound machine in the same room. HIGH
- **"I've never read a skill file."** (Eric — and echoed by Nemo and Kenny) — practitioners trusting the model to self-organize; skills as write-only artifacts. HIGH
- **"Product is no longer the moat."** (Sangram) HIGH
- **"Go-to-market is the business… the CEO owns go-to-market."** (Sangram) HIGH
- **"You are a twenty dollar Codex plan away from changing your life."** (Eric) HIGH
- **"If [the agent's] not doing what you want, [it's] your fault. Your business is not that complicated."** (Eric) HIGH
- "I'll be the first one to have the layoffs." (Sangram, joking during the demo glitch — "we've got an agent strike") MED (banter)
- Qualify prospects "by influence," not title or company (Nemo). HIGH
- Websites will become chatbots ("what do you wanna know?") (Eric). HIGH (prediction)

## 10. Substantive Insights (ranked)

1. **One reference architecture, three maturity levels.** The same context→connectors→agents→approval pattern recurs from a 7-person agency to a $400M-ARR platform — strong evidence it's the durable shape of GTM-AI, not a vendor artifact. HIGH
2. **The bottleneck moved from the model to context + connection + the human review loop.** Multiple speakers independently: the model is "done," the work is feeding and gating it. HIGH
3. **The frontier is multiplayer.** Value is migrating from solo laptop harnesses to shared cloud harnesses (internal) and network/co-creation harnesses (external). HIGH
4. **The cold-outreach schism.** Industrialized outbound (Kenny: 100k+ emails/day exist on the bill) vs. "co-creation replaces cold outreach" (Nemo) — an unresolved, genuine strategic fork. HIGH
5. **Enterprise needs the boring software-engineering layer.** Identity/RBAC, audit trails, deterministic eval metrics, and existing work-management systems are what separate a demo from a deployable harness (Nikita). HIGH
6. **Agent reliability = software discipline, not vibes.** Pair LLM-judge evals with tool-success/trace-log/anomaly metrics (Nikita). HIGH
7. **Clarity beats certainty in GTM.** The 8-question OS aligns a team better than a "correct" but unowned strategy (Sangram). HIGH
8. **Warm path is the highest-converting signal even inside automation.** The "online stalker" mutual-connection trigger beats every cold signal (Kenny). HIGH
9. **Adversarial self-critique is a required skill primitive** to counter model sycophancy (Eric). HIGH
10. **Naming, framing, and human roots matter.** From naming agents (Dale/Milton) to faith/marriage/co-founders — the human layer recurred as the counterweight to automation. MED/HIGH

## 11. Anecdotes

- **Sangram's "think big" exchange:** boss said "think big" after the $100M ExactTarget acquisition; six months later, after the $2.7B Salesforce deal, said it again — "No, you don't get it." Lesson: scale is about how big you can *think*, not budget/headcount. HIGH
- **Geoffrey Moore's endorsement** of Sangram's book *MOVE*: "If I were to write Crossing the Chasm again, I would have written Move." HIGH
- **Sangram almost got divorced** building Terminus; now balances faith/family while building GTM Partners; his son (now ~15) shoots his videos, was 5 when Terminus started. HIGH
- **Eric "accidentally" cut his team 50%** and increased email volume by building an AI employee — the talk Nemo told him to give. HIGH
- **Eric's gaming-PC fleet:** "I literally wiped three gaming computers, and that's where we're running it from." HIGH
- **Eric's agent names:** Dale (Carnegie) and Milton (Friedman); proposes Judith Love Cohen — NASA engineer who solved an Apollo problem en route to the hospital, then gave birth to Jack Black. HIGH
- **The "anime bullshit" warning** about Chrome-history screen-sharing — biggest audience laugh. HIGH
- **The live "agent strike":** projector/clicker tech failed repeatedly during Sangram's and Nikita's slide loads; Sangram ad-libbed ("improv comedy is part of my routine"), joked "I'll be the first one to have the layoffs." HIGH
- **Nemo's origin story:** community began as a WhatsApp message to NYC YC founders; first 3 events at Clay HQ, now at Insight Partners. HIGH
- **Jack's path:** attended the last masterclass, took "so much value," offered Insight's space; a month later ~100 people in the room. HIGH
- **Kenny's "lazy" passion project:** built the whole ABM bot because he "just didn't want to upload lists anymore." HIGH
- **Aon walkthrough:** 60k people → 12 contacts at the click of a button. HIGH
- **Nemo's Clay World Cup** self-reference (NYC representative) — colorful, flag before quoting. MED

## 12. Concept Glossary (flag = needs enrichment before public use)

- **Harness** — the runtime/environment wrapping an LLM with tools, context, skills, and agents (Claude Code, Codex, OpenClaw, Hermes, Opal, Swan/S1). The night's keyword. ✅ well-defined in-room.
- **Skill** — a reusable, static set of instructions/SOP an agent invokes; no autonomous loop. ✅
- **Agent** — an entity with its own autonomous reasoning loop, lifecycle, and (in Nikita's model) an identity. ✅
- **Agent teammate** — Optimizely term: an agent provisioned like a human (email, account, RBAC, audit trail). 🔎 enrich (Optimizely-specific).
- **Action card** — Opal's open-sourced cross-platform UI widget (works across Slack Block Kit / MS adaptive cards / OpenAI MCP apps). 🔎 enrich.
- **Artifact** — rich rendered output (by MIME type) vs. "blobs of text." ✅
- **GTM Operating System (8 questions)** — Sangram/GTM Partners framework: Total Relevant Market, Market Investment Map, Brand & Demand, Pipeline Velocity, Customer Time-to-Value, Customer Expansion, Revenue Ops, Leadership & Mgmt (per slides). 🔎 enrich exact 8 labels from slide.
- **ABM (account-based marketing)** — category Terminus helped create; Kenny's "ABM bot" applies it. ✅
- **AEO / GEO** — Answer/Generative Engine Optimization — optimizing to show up in AI overviews/LLMs (Nikita). 🔎 newer terms, enrich.
- **Meat gates / "meet gates"** — Eric's term for mandatory human approval checkpoints. (Transcription ambiguous.) 🔎 confirm spelling/intent.
- **Online stalker** — Kenny's per-contact monitor (connections, LinkedIn activity, events, mentions). ✅ (his coinage)
- **Two degrees out** — Nemo's network targeting: your ICP's commenters' commenters. ✅
- **Multiplayer GTM** — Nemo's thesis: shared cloud harness internally + network co-creation externally. ✅
- **Co-creation** — collaborative content/webinars/testimonials with influential nodes, replacing cold outreach (Nemo). ✅
- **Adversarial skill** — a skill that argues the opposite to counter sycophancy (Eric). ✅
- **MCP / remote MCP** — connector protocol referenced repeatedly; Supabase MCP praised by Kenny. ✅
- **Reliability: SLI/SLO, eval pipeline, trace logs** — software-engineering quality discipline applied to agents (Nikita + slides). 🔎 detail from slides.

## 13. Tools / Companies Mentioned

| Name | Type | Mentioned by | Context | Notes |
|---|---|---|---|---|
| Claude / Claude Code | LLM / harness | All | Default brain across talks; "Claude Code on Pocket" (Kenny) | "5.5" referenced by Eric |
| Codex (OpenAI) | harness | Eric, Nikita | Recommended starting harness; $20 plan; Codex Max | |
| OpenClaw | harness | Eric | Solo agent harness | spelling per alignment |
| Hermes | harness | Eric | Eric's preferred; auto-writes skills, "never disconnects" | |
| Nanoclau / "Nano Claw" | harness | audience | Audience rec: "super secure Claw" | 🔴 spelling/verify |
| Opal | product (Optimizely) | Nikita, Nemo | Marketer AI agent harness; 9 lessons; action cards open-sourced | |
| Optimizely | company | Nikita | ~$400M ARR, 2 decades, Insight portfolio | |
| Swan / "S1" / "Super Agent" | product (sponsor) | Nemo, Sangram | Cloud multiplayer GTM harness; Nemo's live demo; 20% off | 🔴 naming muddy across S1/Swan/Super Agent |
| Trigger.dev | infra | Eric | Hides API keys from agents | |
| Fathom | meeting recorder | Eric | Context source for company brain | |
| Obsidian | notes/Markdown | Eric | Free company-brain store | |
| Slack | comms / approvals | Eric, Nikita, Kenny | Context + AE approval surface | |
| Clay | data/enrichment | Eric, Nemo, Kenny | Eric early employee; Nemo "Clay World Cup"; Kenny enrichment | |
| Instantly | cold-email orchestrator | Eric, Kenny | "swing" in ASR | |
| HeyReach | LinkedIn automation | Kenny | "Hayreach"/"PayReach" in ASR | |
| Gong | call recording | Kenny | Transcripts → Supabase | |
| Supabase | database (Postgres) | Kenny | Marketing scratch DB; praises MCP | |
| Render | hosting | Kenny | 24/7 agent hosting w/o GitHub access | |
| HubSpot | CRM | Nikita, Kenny | CRM + connector ("everybody has a HubSpot connector") | |
| Salesforce / GA4 / Marketo | martech | Nikita | Connector examples | |
| ServiceNow / Jira | work mgmt | Nikita | Enterprise approval-system examples | |
| Terminus | company (past) | Sangram | ABM category creator; PE exit; 5 acquisitions; 300+ employees | |
| Pardot / ExactTarget / Salesforce | M&A path | Sangram | $100M then $2.7B | |
| GTM Partners | company | Sangram | Advisory; $10M/5yrs; stack = Thinkific + Swan + Kit + Claude + Super Agent (slide) | |
| Growth Engine X | company | Eric | Cold-email agency; ~7 employees, ~60 customers | |
| CoverForce | company | Kenny | Insurance API; Insight portfolio; "Hubbard Forest" in ASR | |
| Two Hops | company | Nemo | His GTM agency, "network operations" | alignment says "Impact 11" — DISCREPANCY |
| Knock AI / "Knock" | client example | Nemo | Network co-creation case | 🔴 "Nokai" spelling unverified |
| Copperhelm | demo instance | Nemo | Company instance in Swan demo | 🔴 "copper helm" spelling unverified |
| Aon | target example | Kenny | 60k-person broker; 60k→12 contacts | "ale/aeon" in ASR |
| ZoomInfo / HubSpot (Henry/Yamini Rangan) | GTM-OS clients | Sangram | CEO examples run through the 8 questions | |
| Insight Partners | host / investor | Jack | Venue; growth equity B–D+; AI Lab | |
| Josh Braun | person | Eric | Cold-email training baked into a skill | |
| Geoffrey Moore | person | Sangram | Endorsed *MOVE* | "Jeffrey Motorsay" in ASR |
| Brian Halligan | person | Sangram | HubSpot founder; "who owns GTM" framing | |
| Dale / Milton | agent names | Eric | Named after Carnegie / Friedman | |
| Anthropic | company | Eric | "trillion-dollar company" remark | |

## 14. Stat Bank (no invented precision)

- **~100 attendees** (Jack: "about a hundred"). HIGH
- **5 presentations; 5th masterclass; 5 months in a row** (Jennifer). HIGH
- **2 investors** in the room (raised hands); **~60% founders** (Sangram's read of the hand-raise). MED (eyeballed)
- **Sangram:** Pardot→ExactTarget = **$100M**; ExactTarget→Salesforce = **$2.7B**. HIGH
- **Terminus:** founded **2014**, **3 co-founders**, **300+ employees**, acquired **5 companies in 8 years**; revenue **$1M → $5M → $15M** (yrs 1–3) with **"one and a half marketer."** HIGH
- **GTM Partners:** founded **2021**, bootstrapped, **2 co-founders**, **$10M in 5 years**; newsletter **~175,000 readers**. HIGH
- **78%** of GTM leaders said clarity on what/why = they'll hit revenue goals (Sangram's research). HIGH
- **Revenue per $100k spend:** ~$300–400k (10 yrs ago) → **~$1M/employee** target now. HIGH
- **Eric:** team **cut 50%**; **7 employees** vs peers' **~30** at same revenue band; **~60 customers**; **200–300 leads/day** generated; **100,000 cold emails/day** for one enterprise customer (~**70 leads/day** that customer; **145 leads** another customer "yesterday"); **$400/month** agent plans; **$15K/month** AI spend. HIGH
- **1M-token context window ≈ "the Bible"** (Eric's analogy). HIGH
- **Optimizely:** **~$400M ARR**, **~2 decades**; **9 lessons** from **2 years** building Opal; customers run **~15 systems**; org context = **1 person setup → whole company value**. HIGH
- Reliability targets (from slides, not narrated): tool_success **≥95%**, thumbs_down **<10%**. MED (slide-sourced)
- **CoverForce / Aon:** **60,000** people → **15,000** (broad filters) → **~3,000** (VP+) → **12** contacts; **10-touch / 22-day** ABM cadence (**4 email · 3 LinkedIn · 3 gift**); **<50 words/email**; **~4 contacts/company/day**; **90-day** pause hold; setup **4–5 hrs → 10–15 min**. HIGH
- **Tools-used slide (Kenny): 9–10 named** (Claude, Gong, Clay, Instantly, HeyReach, Slack, Supabase, Render, HubSpot). HIGH

## 15. Documentarian Angles

1. **"The word nobody could stop saying."** Four speakers, four harnesses (Hermes/OpenClaw, Opal, Swan/S1, Claude Code) — Nemo even tried to ban the word "harness." A clean glossary-meets-zeitgeist post.
2. **"Nobody reads the skills."** Three independent practitioners admitting they never read skill files — a slightly subversive, very real signal about trust in self-organizing models. Strong contrarian single post.
3. **The cold-outreach schism (two-thesis synthesis).** Kenny industrializes cold outbound in the same room where Nemo declares cold outreach dead. Map both as legitimate forks. (Use `pattern-synthesis`.)
4. **One architecture, three altitudes.** Redraw Eric (solo) / Nikita (enterprise) / Kenny (mid-market) as the *same* context→connectors→agents→approval diagram at 3 maturity levels. Carousel-ready (don't reprint any one deck — synthesize).
5. **Human-in-the-loop survived every demo.** The honest counter to "agents replace teams" — meat gates, governance, Slack approvals.
6. **The human layer as counterweight.** Sangram's divorce/faith/co-founder thread amid an automation night — the "don't lose the why" angle.
7. **Insight Partners' move:** a VC opening its space + AI Lab to a community it discovered — the firm-as-community-builder story (ties to Alex's Insight job-search target).

## 16. Open Loops & Verification Flags

- **Nemo's company:** transcript = **Two Hops**; alignment doc = **Impact 11**. Resolve before any public attribution. 🔴
- **Swan product naming:** "Swan" / "S1" / "Super Agent" used interchangeably; demo instance "**Copperhelm**" and client "**Knock AI**"/"Nokai" spellings unverified. 🔴
- **"Clay World Cup"** (Nemo) — sounds real but verify before quoting publicly. 🟡
- **Jennifer's surname:** Schwarz (brief) vs "Schwartz" (ASR). 🟡 Also alignment notes she's associated with "EcoMotion" — not stated in transcript; verify. 🟡
- **Jack's surname** unknown (first name only). Create Insight People record on commit. 🔴
- **Eric intro'd once as "Harry"** — confirmed Eric via Growth Engine X + Clay self-ID. Resolved but noted. ✅
- **"Meat gates" vs "meet gates"** — Eric's human-approval term; confirm spelling/intent. 🟡
- **ASR low-confidence words** (from REVIEW file, verify by clicking timestamp): "Sigma" (101:06, Kenny's "Sigma Bill" filtering tool — likely a real tool name, verify), "Oracle" (26:08), "LinkedIn" (103:24), "potentially," "host," "base" — 13 flagged words total, all low logprob. 🟡
- **Slides 13–15 (Nikita reliability/identity/governance)** were captured but lightly narrated — content there is slide-sourced, not spoken; don't attribute as verbatim quotes. 🟡
- **Diarization** — every attribution reconciled by content; raw speaker IDs are not 1:1 (see caveat at top). Re-verify any single-line quote against the segment before isolating it for a quote card. 🟡
- **No pre-event brief on disk** — pre→post diff is incomplete; pull the Notion research brief to close Section 3 properly. 🔴
- **An earlier post-event brief already exists** in this folder (`POST-EVENT BRIEF — NYC GTM+AI Masterclass #5 (6-3-26).md`). This file is a separately-named deliverable; reconcile/dedupe the two before committing to Notion. 🟡

---
*Built from folder sources only (Scribe v2 transcript + slide alignment + low-confidence flags). Nothing invented; uncertain items flagged. 2026-06-27.*
