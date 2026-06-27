# POST-EVENT BRIEF — AI Demo Night (05/21/2026)

_Format: multi-presenter live demo night (~44 min captured). Built exhaustively from in-folder transcripts only — nothing invented._
_Primary source: `05 21 26 AI Demo Night — Transcript (Scribe v2).md` (ElevenLabs Scribe v2, diarized, 6 speaker IDs). Cross-referenced: `… Recording — Transcript (ElevenLabs).md` and `… — REVIEW (low-confidence spots).md`. No slide decks or pre-event brief present in folder._

> **Diarization caveat (load-bearing):** Speaker IDs are NOT 1:1 with people. In particular `speaker_1` conflates Red Hat presenter "Grace" with the event MC/host (the inter-demo intro lines — "Next is RoleMate," "Next, we have Docker," "here from Google" — are host patter, not necessarily Grace). All attribution below is by content, not by raw ID. Presenter names are confidence-tagged; two names conflict across the two transcripts and are flagged in §16.

---

## 1. Quick Take

Six builders demoed agentic products end-to-end, and the through-line was unmistakable: 2026's interesting AI work has moved from "the model answers" to "the agent operates safely, cheaply, and verifiably inside real infrastructure." Four of six demos centered on the operational layer around agents — self-improvement loops, CI/CD triage, token-cost optimization, and sandbox isolation — not on novel model capability. The crowd was technical and forgiving of live-demo failure (multiple demos broke on stage and presenters narrated through it). This was a workbench night, not a vision night.

## 2. The Thesis

**The frontier of applied AI has shifted from capability to operability.** Every demo assumed the model is good enough; the value-add was the scaffolding — verification against trusted sources (cBioPortal), eval gates that auto-revert bad deployments (Red Hat), token-cost reduction via skills (Google Agent CLI), and secret-free microVM isolation so agents can run unattended without nuking prod (Docker). The two consumer-ish demos (RoleMate, Clips) rhymed: both convert messy real-world context (a GitHub history; a saved TikTok) into structured, agent-usable context. **Context engineering + operational safety is the 2026 builder's job; raw inference is a commodity input.**

## 3. Pre→Post Gap

**No pre-event brief exists in this folder.** Gap analysis not possible. (There is a separate file `POST-EVENT BRIEF — AI Demo Night (5-21-26).md` already in the folder — a prior pass at this same deliverable — but no `pre-event` research brief.) Recommend flagging whether a pre-event brief was ever produced for this event.

## 4. Speaker Map (content-derived, confidence-tagged)

| # | Raw ID | Name (conf) | Org / Affiliation (conf) | Product demoed | Role signal |
|---|--------|-------------|--------------------------|----------------|-------------|
| 1 | speaker_0 | **Unnamed** (name never stated in transcript) | **cBioPortal** project; collaborator note that "Victoria works at ClickHouse now" (HIGH) | cBioPortal chat interface (chat.cbioportal.org) | Cancer-genomics platform builder; deep domain (oncology data) |
| 2 | speaker_1 | **Grace** (HIGH) | **Red Hat** — "AI developer advocate" (HIGH) | Red Hat OpenShift AI pipeline-triage agent | DevRel; also appears to MC inter-demo intros (likely diarization merge — MED) |
| 3 | speaker_2 | **CONFLICT: "Jesup" (Scribe) vs "Avik" (ElevenLabs)** (LOW) — host announced product as "Jaspreet/Jesup RoleMate" | Sophomore at **Rutgers** (HIGH) | **RoleMate** (job-matching) | Student founder, pre-launch (waitlist + QR) |
| 4 | speaker_3 | **Unclear — "Max"? ("it's Max Holy time" / "fuzzy mustache")** (LOW) | Independent / solo builder (MED) | **Clips** (content→context extractor) | Solo indie dev; mentions work vs. outside-work context |
| 5 | speaker_4 | **Pierre** (HIGH) | **Google / Google Cloud** — PM (HIGH) | **Agent CLI / "Agents CLI"** (agent-first GCP CLI + skills) | Product manager; launched at Google Cloud Next, Vegas |
| 6 | speaker_5 | **Chris** (HIGH) | **Docker** — Sandboxing team, ~10 yrs at Docker (HIGH) | Docker **Sandboxes** (microVM agent isolation) | Eng; built the VMM from scratch |

Additional named-but-not-present entities: **Victoria** (now at ClickHouse — cBioPortal collaborator, HIGH); **"Rui"** (referenced by Chris — "Rui wants to go out there and keep the whole thing alive"; LOW confidence transcription, role unknown — possibly host or co-presenter).

## 5. Full Quote Bank

_Whole lines, attributed by content. HIGH = verbatim-safe (clear audio, both transcripts agree). MED = transcription uncertain or paraphrase-risk. Use HIGH only for public quoting._

### cBioPortal (speaker_0)
- **[HIGH]** "We've been collecting that for over ten years. So we have data from over five hundred studies."
- **[HIGH]** "Okay, that's cool, but I know LLMs hallucinate. So did it come up with this stuff? Is it real? So now you can maybe ask, okay, maybe I can go back to the website, which I trust."
- **[HIGH]** "So now you can sort of validate that it's accurate, which in our domain is very important, obviously."
- **[MED]** "I have Claude connected to the LibreChat responses and to Langfuse so I can see the conversations, and I can just ask, 'Do you see any new feedback?' And then it files a ticket on GitHub… and then you say, 'Can you fix it?' It'll fix it. And if it looks good, then I say deploy to production."
- **[HIGH]** "So there you have sort of your self-improvement loop, which I thought is kind of something to think about for your own products. Like, how do you continuously improve it based on feedback from users?"
- **[MED]** "We made a few customizations where you can sort of select a database agent." / "We have a different agent — that's the navigator agent that helps to navigate the websites."

### Red Hat — Grace (speaker_1)
- **[HIGH]** "You might be wondering, what are you doing here at an AI Demo Night? Well, we actually have AI too, which is a surprise to a lot of people."
- **[HIGH]** "If you know anything about Red Hat, we really love open source, and we bring open source to the enterprise."
- **[HIGH]** "We're gonna have a build that succeeds, a test that fails on purpose, guys. On purpose."
- **[MED]** "An eval gate deployment where if the LLM doesn't match the certain evals or doesn't live up to your standards, it will automatically revert back to the old deployment."
- **[HIGH]** "Sometimes the good prompt is not that good, so we'll call it the bad prompt and the better prompt."
- **[MED]** "This would be a little bit more nuanced if you had a LLM as a judge kind of thing going on." (re: keyword-matcher evals)
- **[HIGH]** "We can wait for it awkwardly now." (live-demo latency)

### RoleMate (speaker_2)
- **[HIGH]** "There's this big massive tool called AI, and that's allowed people to generate more and more resumes than ever before and apply to ten times the number of applications as they would be able to before."
- **[HIGH]** "Resumes are words on a piece of paper that are no longer a valid proof of skill."
- **[MED]** "Their credibility is based on their GitHub instead of just words on a piece of paper on a resume."
- **[MED]** "If you have an identical resume to someone, but the other person has a connection to someone at a company that you're applying to, that person is always getting the job."
- **[MED]** "Your data from your private repositories doesn't leave RoleMate or get sent to the companies… this final summary and score is all that gets sent to companies."
- **[MED]** "No one knows about hire reviews until they get one in an email, and they have no chance to prepare for it." (note: "hire reviews"/"higher reviews" uncertain transcription)

### Clips (speaker_3)
- **[HIGH]** "Clips basically takes links from YouTube, TikTok, articles, Reddit posts, anything of that manner, and it extracts them into usable links."
- **[MED]** "For a multimodal agent like Gemini, it's sending the video. For let's say Claude or OpenAI, it goes through YouTube CL and Whisper C++."
- **[MED]** "I just got access to the Instacart API, so you can load them all into the cart." (saved-recipe → buy ingredients)
- **[HIGH]** "It's AI agnostic, so you can bring your own AI API key, and it's free. It uses Gemini by default."
- **[MED]** "I also have a version that uses a packaged Gemma version within it, so you can run it locally, and it's free."
- **[HIGH]** "It's free on iOS right now. It's in beta on Android… It also has a web app, a Chrome extension, and an Obsidian connector."
- **[MED]** "I'm running it on fast here, so burning some tokens up pretty quickly."

### Google Agent CLI — Pierre (speaker_4)
- **[MED]** "Agents CLI is not just a CLI like the name says, but it's a CLI plus skills bundled together to try to help agents guide them through a whole life cycle on GCP."
- **[HIGH]** "These services were first designed for humans as the main users… But now we just need to have an interface that is ready first for agents, and where agents can easily jump between one service to another."
- **[HIGH]** "That's why people end up token maxing and spend lots of tokens unnecessarily, because these agents are smart enough to find workarounds and try to glue things around, but they are not very optimized for that."
- **[MED]** "Plugging in this CLI, you know, they do it with forty percent less tokens… instead of taking hours, you can do the same task in five, ten minutes."
- **[MED]** "Skills are not for giving in-depth knowledge about services, but they are for guiding through a whole journey or experience across Google Cloud."
- **[HIGH]** "You have a prototype, you have production. There is lots of squiggly lines along the way… And with this CLI, we just want to make sure that you have a highway that you can just run through it and make sure your coding agent can move as fast as possible from one side to the other."
- **[MED]** "The repository is open source. So you can see we already have two thousand stars."
- **[MED]** (demo gimmick) "A security agent that needs to review this code and write some commentary… in a Victorian language from the eighteen hundreds England, and then give very harsh feedback."

### Docker Sandboxes — Chris (speaker_5)
- **[HIGH]** "It's not great to go last… There's a big high bar that's been set."
- **[HIGH]** "This is my first live-coded set of slides, so excuse me for the mistakes."
- **[HIGH]** "Then Claude came out, you have the agent… it would print you a five-line bash command, and it'd be like, 'Are you okay with running this?' And you're like, for the first one, 'Okay, I'll read this.' And then the twelfth, you're like a monkey in a loop just hitting the button."
- **[HIGH]** "You see what happens on Twitter though — somebody deletes the production database, which is not really ideal."
- **[HIGH]** "Turns out NPM is a great way to get a virus or a great way to leak your company secrets."
- **[HIGH]** "I'd say a year ago, keep your software up to date. Now I'm like, I don't know — give it thirty days. Let somebody else work out what's wrong with it first."
- **[MED]** "We built a new, completely new platform from the VMM up. I think it's maybe the only truly cross-platform VMM at Docker now. It's Linux, Mac, Windows."
- **[MED]** "We run a microVM, we put a container inside, and then we manage the file system access and the networking on that VM, so it's completely isolated."
- **[HIGH]** "We also don't give it any secrets… We rewrite the prompts on the way out. That way you don't have that problem of the LLM helping you by uploading your API key somewhere so it can fetch data."
- **[HIGH]** "The hard part was definitely the VMM. We built a VMM from scratch. That was not easy."

## 6. Pro-Tips (actionable, builder-grade)

1. **Build the self-improvement loop into the product, not the roadmap.** cBioPortal wires user thumbs-up/down → Langfuse → Claude reads feedback → files GitHub issue → fixes → deploys. Treat feedback-to-fix as a first-class pipeline. [cBioPortal]
2. **Ground agent answers against a source the user already trusts.** cBioPortal's "show me this on the website" navigator agent lets users verify LLM output against the canonical REST API/UI — critical in high-stakes domains. [cBioPortal]
3. **Use eval gates that auto-revert.** If a new deployment's LLM output fails the eval threshold, roll back automatically to the prior deployment. [Red Hat]
4. **Start with cheap evals, graduate to LLM-as-judge.** Keyword matchers give fast observability now; LLM-as-judge adds nuance later. [Red Hat]
5. **Keep secrets outside the agent's blast radius.** Rewrite prompts on the way out so the model never sees API keys/credentials — removes the "LLM helpfully exfiltrates your secret" failure mode. [Docker]
6. **Sandbox long-running agents in a microVM with managed FS + network.** Lets agents run unattended without the "are you sure?" approval-fatigue loop. [Docker]
7. **Optimize for token cost as a product feature.** Pre-packaged skills/scaffolding cut wasted "glue" tokens; Google claims ~40% reduction. [Google Agent CLI]
8. **Bring-your-own-key + local model fallback** keeps a consumer AI app free to run. [Clips]

## 7. Best Practices / Patterns observed

- **Verification-first AI in regulated/high-stakes domains** — never trust LLM output standalone; round-trip to canonical source. [cBioPortal]
- **Agent-first interface design** — Pierre's explicit framing: infra built for humans must be re-fronted for agents as the primary "user." [Google]
- **Skills as workflow guidance, not knowledge dumps** — skills guide the agent through a lifecycle/journey rather than stuffing in service docs. [Google]
- **"Fails on purpose" demo design** — Red Hat scripted a deliberate test failure to show the triage agent's real value (recovery, not happy path).
- **Open-source-to-enterprise positioning** — Red Hat (vLLM, LlamaStack/"LLAP", LM Eval) and Docker both lean on OSS credibility.
- **Privacy-preserving scoring** — RoleMate sends only a derived summary/score to employers, not raw private repo data.
- **Context normalization** — Clips converts heterogeneous media (video/article/recipe/paper) into typed "modules" with a JSON schema; brains stored as markdown for agent consumption.

## 8. Pitfalls / Anti-Patterns surfaced

- **Approval-fatigue loop** — humans rubber-stamping the 12th "are you okay running this?" bash command ("a monkey in a loop"). The risk this normalizes is real. [Docker]
- **Prod-database deletion by unsandboxed agents** — cited as a known Twitter-famous failure mode. [Docker]
- **Supply-chain risk via NPM** — "a great way to get a virus or leak your company secrets"; Chris now waits ~30 days before updating. [Docker]
- **Token-maxing** — capable agents waste tokens "gluing things around" when infra isn't agent-optimized. [Google]
- **LLM hallucination in domain answers** — explicitly called out as why verification is mandatory. [cBioPortal]
- **Resume credibility collapse** — AI-generated resumes flood hiring; "words on a piece of paper" no longer signal skill. [RoleMate]
- **Live-demo fragility** — multiple demos stalled/broke (cBioPortal first query failed; Red Hat GitHub issue "still not made… we can wait for it awkwardly"; Clips/Docker buggy). Pattern worth noting for any demo-night documentarian: graceful narration through failure was the norm.

## 9. Hot Takes (sharp opinions stated)

- **[Docker/Chris]** "A year ago, keep your software up to date. Now… give it thirty days. Let somebody else work out what's wrong with it first." — a genuine reversal of conventional security advice, prompted by AI-era supply-chain attacks.
- **[RoleMate]** "Resumes are words on a piece of paper that are no longer a valid proof of skill." — provocative but framed as the product's founding premise.
- **[Google/Pierre]** Cloud infra "was first designed for humans" and now needs an agent-first interface — implicitly: the human-facing console is legacy.
- _(Thin overall — demo nights skew product-signal over opinion. These three are the only genuine stances.)_

## 10. Substantive Insights (ranked)

1. **Operability, not capability, is the 2026 differentiator.** 4 of 6 demos were about the operational shell around agents (verification, eval gates, cost, sandboxing) — the model is assumed good enough. _(Highest-confidence cross-cutting signal.)_
2. **Agent-first infrastructure is an emerging design discipline.** Google is productizing the idea that platforms must expose an agent-native interface distinct from the human UI (Agent CLI + skills). Strategic, not incremental.
3. **Security is the wedge for agent autonomy.** Docker's bet: agents can only run unattended if isolated (microVM) and secret-blind. Removing approval fatigue safely unlocks autonomy.
4. **The self-improving product loop is now buildable by one person.** cBioPortal's feedback→Langfuse→Claude→GitHub→deploy loop is a small-team-achievable continuous-improvement pattern.
5. **Eval gates as deployment guardrails** are moving from theory to default — auto-revert on eval failure. [Red Hat]
6. **Context extraction is the consumer-AI wedge.** Both consumer demos (Clips, RoleMate) win by turning messy real-world artifacts (saved media; GitHub history) into structured, queryable context.
7. **Token economics are a first-class product metric** — a stated ~40% reduction is pitched as a headline benefit, signaling cost is now a buying criterion.

## 11. Anecdotes

- **Chris (Docker) going last:** "It's not great to go last… there's a big high bar," then live-coded his slides and demoed one-handed (held phone — "please excuse the fuzzy mustache"). Self-deprecating, high-credibility delivery.
- **The "monkey in a loop"** story — origin myth for why Docker built sandboxing: approval fatigue on repeated agent bash commands.
- **Red Hat's "fails on purpose"** — Grace repeatedly reassuring the room the test failure was intentional ("On purpose, guys. On purpose.").
- **Pierre's Victorian-bureaucracy demo** — to show the multi-agent scaffold, he had a security agent deliver "very harsh feedback in Victorian language from the eighteen hundreds England." Memorable demo-craft.
- **"Victoria works at ClickHouse now"** — aside revealing the cBioPortal/ClickHouse personnel link.

## 12. Concept Glossary

_★ = likely needs external enrichment for a non-technical reader._

- **cBioPortal** — open-source cancer-genomics data portal; React front-end, Spring Boot back-end, ClickHouse DB; >500 curated studies over 10 yrs.
- **LibreChat** — open-source chat-UI framework used by cBioPortal for its chat interface (built-in thumbs up/down feedback).
- **Langfuse** ★ — LLM observability/tracing platform; here, the conversation/feedback store Claude reads from.
- **Amazon Bedrock** — AWS managed foundation-model service hosting cBioPortal's chat.
- **MCP (Model Context Protocol)** — agent-to-tool interface; appears across demos (Clips "bi-directional MCP," cBioPortal "MCDs" likely = MCPs — transcription error).
- **OpenShift / OpenShift AI** — Red Hat enterprise Kubernetes + its AI platform ("models as a service").
- **vLLM / LM Eval / LlamaStack ("LLAP")** ★ — Red Hat-supported OSS: inference server, eval harness, and an "AI at scale" stack (transcribed "LLAP" — verify exact project name).
- **Qwen ("Quinn")** — open-weight LLM (Alibaba) used by Red Hat's demo as the triage model.
- **OpenTelemetry / Jaeger / "Elk Flow"** — tracing/observability stack options for shipping pipeline traces.
- **Eval gate / auto-revert** — deployment guard that rolls back if LLM output fails evals.
- **LLM-as-judge** ★ — using an LLM to score outputs more nuancedly than keyword matching.
- **microVM / VMM** ★ — lightweight virtual machine + Virtual Machine Monitor; Docker's isolation primitive (cross-platform, built from scratch).
- **Memory ballooning** — dynamically adjusting VM memory so it "doesn't feel like a VM." [Docker]
- **Agent CLI / "Agents CLI"** ★ — Google Cloud's agent-first CLI + skills bundle for the GCP agent lifecycle; announced at Google Cloud Next (Vegas); ~2,000 GitHub stars; open source. **Verify exact product name.**
- **ADK (Agent Development Kit)** — Google's agent framework used in Pierre's demo.
- **Antigravity** ★ — referenced alongside Cloud Code/Gemini as an agentic coding tool (verify — likely Google's Antigravity IDE).
- **Clips** — solo-built app extracting saved media (YouTube/TikTok/articles/Reddit) into structured "modules"/"brains" (markdown) for agent context. Firebase + Pub/Sub + Cloud Run + Docker image (Node, yt-dlp, FFmpeg, Whisper C++).
- **RoleMate** — job-matching tool scoring candidates from GitHub projects rather than resumes; surfaces warm LinkedIn intros; "hire review" interview-practice feature. Pre-launch (waitlist).
- **"Hire reviews"** ★ — RoleMate's term for a recruiting-stage review step (transcription uncertain — could be "higher reviews"/other). Verify the actual concept.

## 13. Tools / Companies Mentioned

| Entity | Type | Context | Confidence |
|---|---|---|---|
| cBioPortal | Product/Org | Cancer-genomics portal + new chat interface | HIGH |
| ClickHouse | Company/DB | cBioPortal's DB; "Victoria works there now" | HIGH |
| LibreChat | OSS framework | Chat UI for cBioPortal | HIGH |
| Langfuse | Tool | LLM observability/feedback store | MED (name clear, spelling ok) |
| Amazon Bedrock | Platform | Hosts cBioPortal chat | HIGH |
| Claude (Anthropic) | LLM/agent | Used by cBioPortal (feedback loop), Clips, Docker | HIGH |
| Whisper / Whisper C++ | ASR | Voice input (cBioPortal); transcription (Clips) | HIGH |
| Red Hat | Company | Enterprise OSS; AI DevRel demo | HIGH |
| OpenShift / OpenShift AI | Platform | Enterprise K8s + AI models-as-a-service | HIGH |
| Qwen ("Quinn") | LLM | Red Hat triage model | HIGH (Qwen) |
| vLLM | OSS | Inference server (Red Hat) | MED |
| LM Eval | OSS | Eval tool (Red Hat) | HIGH |
| LlamaStack / "LLAP" | OSS | "AI at scale" stack (Red Hat) | LOW (name) |
| OpenTelemetry / Jaeger | Observability | Trace shipping options (Red Hat) | HIGH / MED |
| GitHub | Platform | Issue creation (cBioPortal, Red Hat); RoleMate scoring source | HIGH |
| RoleMate | Product | GitHub-based job matching (pre-launch) | HIGH |
| Rutgers | University | RoleMate founder's school | HIGH |
| ChatGPT Plus | Product | Referenced as BYO subscription for RoleMate | HIGH |
| Clips | Product | Media→context extractor (solo build) | HIGH |
| Firebase / Pub/Sub / Cloud Run | GCP infra | Clips backend | HIGH |
| FFmpeg / yt-dlp / Node | OSS tools | Clips Docker image | HIGH/MED |
| Gemini / Gemma | LLM (Google) | Clips default + local model | HIGH |
| Instacart API | API | Clips recipe→cart feature | HIGH |
| Obsidian / Notion / NotebookLM | Apps | Clips connectors (Notion/NotebookLM in progress) | HIGH |
| Google / Google Cloud | Company | Pierre's employer; Agent CLI | HIGH |
| Agent CLI / "Agents CLI" | Product | Agent-first GCP CLI + skills | MED (name) |
| Google Cloud Next (Vegas) | Event | Agent CLI launch venue | HIGH |
| ADK (Agent Development Kit) | Framework | Used in Pierre's demo | HIGH |
| Antigravity / Cloud Code / Codex | Agent tools | Referenced agentic coding tools | MED |
| BigQuery | GCP service | Cited as example agents don't know syntax of | HIGH |
| Terraform | IaC | Scaffolded in Agent CLI output | HIGH |
| Cloud Run / GKE / Agent Runtime / Gemini Enterprise | GCP deploy targets | Agent CLI deploy options | HIGH |
| Docker | Company | Sandboxing team; Chris ~10 yrs | HIGH |
| Docker Sandboxes | Product | microVM agent isolation (GitHub) | HIGH |
| Microcode / "Microsandbox" | Tool | Install target in Docker demo (transcribed "Microcode" — verify) | LOW |
| NPM | Ecosystem | Cited supply-chain risk | HIGH |
| LXD | Tech | Chris's recent work area at Docker | MED |

## 14. Stat Bank (no invented precision)

- **6** presenters/demos captured in ~44 min. [HIGH]
- cBioPortal: **>10 years** collecting data; **>500 studies**. [HIGH]
- Red Hat eval demo: **5 test cases**; good prompt scored ~**100%** keyword match on first two; "bad" prompt identified **2 of 5** failure reasons, "better" prompt **3**. [MED — live, partial]
- Google Agent CLI: **~40% fewer tokens**; tasks "in five, ten minutes" vs. "hours"; **~2,000 GitHub stars**. [MED — presenter claims, unverified]
- Docker: Chris **~10 years** at Docker; cross-platform VMM (Linux/Mac/Windows, incl. Windows ARM64 "not released yet"). [MED]
- Docker security heuristic: wait **~30 days** before updating dependencies. [HIGH — as stated]
- RoleMate: AI lets applicants apply to "**ten times** the number of applications." [MED — rhetorical]
- _No attendance count, no revenue/funding figures, no benchmark numbers were stated._

## 15. Documentarian Angles (for Alex's content)

1. **"Operability over capability" — the 2026 demo-night tell.** Strong room-report thesis: count how many demos were about the shell around the model, not the model. Six-demo dataset supports it cleanly.
2. **Contrast post: cBioPortal vs. Docker** — two opposite answers to "how do you trust an agent?" One verifies output against a trusted source; the other isolates the agent so wrong actions can't hurt. Verification vs. containment.
3. **The approval-fatigue → autonomy arc** (Docker's "monkey in a loop") is a sharp, relatable narrative hook for a build-trigger or signal post.
4. **Agent-first infrastructure** (Google's framing) — a forward-looking "where the value moves" angle: from human consoles to agent-native interfaces.
5. **Demo-craft as content** — Red Hat's "fails on purpose," Pierre's Victorian-bureaucracy agent, Chris going last live-coding one-handed. A meta post on how builders handle live-demo risk.
6. **Student-builder spotlight** — a Rutgers sophomore shipping RoleMate; the resume-credibility-collapse thesis is timely given Alex's own AI-native job search.

## 16. Open Loops & Verification Flags

- **Presenter-name conflict (RoleMate):** Scribe v2 = "Jesup"; ElevenLabs = "Avik"; host intro = "Jaspreet/Jesup RoleMate." **Name unresolved — verify before any outreach/tag.**
- **Clips presenter name unknown** — best guess "Max" from "it's Max Holy time" (LOW). Verify.
- **cBioPortal presenter name never stated** — needs external lookup (likely a cBioPortal/MSKCC contributor).
- **"Rui"** referenced by Chris (LOW-confidence transcription, role unknown) — possibly host/co-presenter; verify.
- **speaker_1 = Grace OR host?** Inter-demo MC lines are attributed to speaker_1 but read as host patter; likely a diarization merge. Confirm whether Grace also MC'd or a separate host exists.
- **Product-name spellings to verify:** "Agent CLI"/"Agents CLI" (Google); "LLAP" (likely LlamaStack); "Microcode" (likely Microsandbox/another sandbox tool); "MCDs" (almost certainly MCPs); "hire reviews" (RoleMate term); "YouTube CL/XL" (likely yt-dlp).
- **Unverified vendor claims:** Google's 40% token reduction, 2,000 stars, "hours→minutes"; Docker's "only truly cross-platform VMM." Treat as presenter claims, not facts.
- **Event metadata absent:** no host org, venue, attendee count, or sponsor list in transcript. Source externally if needed.
- **Two briefs now exist for this event:** this file + `POST-EVENT BRIEF — AI Demo Night (5-21-26).md`. Reconcile/dedupe.
- **No pre-event brief in folder** (see §3).
