# POST-EVENT BRIEF — AI Demo Night (NYC, 2026-05-21)

> **Quote-accuracy caveat:** Paraphrase-first. Verbatim quotes are reserved for lines that transcribe cleanly in the ElevenLabs scribe_v2 pass and survive a cross-check against the baseline transcript. Anything sitting on a low-confidence word (per the REVIEW list) is paraphrased or marked `[VERIFY @mm:ss]`. No quote here is invented; where a speaker's name or a product detail could not be independently confirmed via web search, it is flagged in Section 16.

---

## 1. Quick Take

AI Demo Night was a six-demo lineup that skewed hard toward **infrastructure and developer tooling for the agentic era** rather than flashy consumer AI. Two of the strongest demos came from large vendors (Red Hat, Docker, plus a Google Cloud PM) and were fundamentally about the *unglamorous plumbing* of running agents safely and cheaply at scale — sandboxing, CI triage, token optimization. The dominant signal: **the 2026 builder conversation has moved from "can the model do it?" to "how do I make agents safe, cheap, observable, and trustworthy in production?"** The grassroots demos (a cancer-genomics chat agent, a GitHub-as-resume job platform, a personal content-extraction app) showed the same maturity — every one of them had a feedback loop, an eval gate, or a trust-validation step baked in.

## 2. The Thesis

**The through-line is operational trust in agents.** Across wildly different domains — cancer research, enterprise CI/CD, job hunting, personal knowledge management, cloud agent development, and AI-coding safety — every presenter was solving the same meta-problem: *how do you let an LLM act, and then verify/contain/improve it.* The mechanisms varied but rhymed:

- **cBioPortal** — let the LLM query the database, then route the user back to the trusted website to *validate* the answer (hallucination containment), plus a thumbs-up/down → GitHub-ticket → fix → deploy *self-improvement loop*.
- **Red Hat** — an eval *gate* that auto-reverts a deployment if the LLM's output fails keyword/judge checks.
- **Docker** — a microVM *sandbox* so an agent can run for hours without nuking your prod database or leaking your secrets.
- **Google Agents CLI** — *skills + scaffolding* that constrain the agent to known-good Google Cloud patterns, cutting wasted "token-maxing."
- **RoleMate** — replace the un-trustworthy resume with *GitHub-verified proof of skill*.
- **Clips** — pull untrusted web content into *structured, inspectable* markdown "brains."

The night's implicit message to builders: **the differentiation is no longer the model — it's the trust, safety, and feedback architecture you wrap around it.**

## 3. Pre → Post Gap

No pre-event research brief or agenda was supplied, so a rigorous pre/post comparison isn't possible. **Inferred expectation vs. reality:** a "demo night" label primes you for consumer-facing, demo-friendly AI apps (chatbots, image gen, agents-that-book-your-travel). What actually showed up was **disproportionately infra/devtools** — VMMs, CI pipelines, token economics, eval harnesses. That skew is itself the headline: even at a casual NYC demo night, the center of gravity is production-grade agent operations, not consumer wow-factor. *(Note: treat this section as inference, not measured gap.)*

## 4. Speaker / Company Map

| Presenter | Company / Project | What they demoed | Stage / Funding / Notes |
|---|---|---|---|
| `[speaker_0]` — name not stated (cBioPortal / MSK team) | **cBioPortal** (chat interface) | A two-agent system over cancer-genomics data: a **DB agent** (NL → SQL over ClickHouse via MCP) and a **Navigator agent** that generates trusted website links to validate answers; feedback → GitHub ticket → auto-fix → deploy loop | Open-source academic project (Memorial Sloan Kettering–originated), 10+ yrs of data, 500+ studies. Built on LibreChat + Amazon Bedrock (Claude) + ClickHouse. Presenter noted "Victoria works at ClickHouse now" — aligns with ClickHouse's 2026 acquisition of LibreChat. |
| **Grace** (last name not stated) — AI Developer Advocate | **Red Hat** (OpenShift AI) | A **pipeline triage agent**: build succeeds → test fails on purpose → triage pod sends logs to an LLM → drafts a GitHub issue; plus an **eval gate** (good vs. bad prompt scored on 5 test cases) that can auto-revert a deployment | Public company (IBM subsidiary). Stack: OpenShift AI, "models-as-a-service" (running **Qwen**, transcribed "Quinn"), **llm-d** distributed inference (transcribed "LLAP"/"lmv"), LM Eval, OpenTelemetry → Jaeger/Elk |
| **Avik** [VERIFY name] — sophomore at Rutgers | **RoleMate** | A job-matching platform that scores your **GitHub** as proof-of-skill, surfaces best-fit jobs, finds warm-intro connections with similar career trajectories, and (early-stage) a "hire-view" interview-practice scorer | Pre-launch / waitlist (QR code shown). Free for students (bring-your-own ChatGPT key); B2B monetization = candidate-sourcing algorithm. Confirmed live at **rolemateapp.com** ("Proof of skill for the age of AI") |
| **Max** [VERIFY name] | **Clips** | A personal app that ingests links (YouTube, TikTok, articles, Reddit) and extracts them into structured, usable "brains" (markdown) via customizable "modules"; integrations to Instacart, Libby, Obsidian, MCP | Free; iOS (live), Android (beta), web app, Chrome extension, Obsidian connector. AI-agnostic (BYO key; Gemini default). Built on Firebase Pub/Sub → Cloud Run + Docker (yt-dlp, FFmpeg, Whisper C++) → Firestore/GCS. *App identity not independently verifiable — see §16* |
| **Pierre** [VERIFY name] — Product Manager | **Google Cloud — Agents CLI** | A CLI + skills bundle that turns any coding assistant into a Google Cloud agent-building expert: scaffolds full ADK projects (dev/test/deploy/observability + Terraform), runs evals, deploys to Cloud Run/GKE/Agent Runtime/Gemini Enterprise | Announced at **Google Cloud Next '26 (Vegas)**. Open source — `github.com/google/agents-cli`, ~2,000 GitHub stars cited. Claims ~40% fewer tokens vs. unaided agents |
| **Chris** (last name not stated) — CD/Docker Sandboxing team | **Docker** (Sandboxes) | A from-scratch cross-platform **VMM** running microVMs: drop a container in an isolated micro-VM, manage its filesystem + network, keep secrets *outside* the box (prompts rewritten on the way out). Live one-handed demo sandboxing a coding agent | Public company. ~10 yrs at Docker. Docker Sandboxes launched 2026; built a proprietary VMM (not Firecracker) for macOS/Windows support; Windows ARM64 "coming soon" |

## 5. Full Quote Bank

> Marked `[VERIFY]` where a key word in the line is on the low-confidence list. Paraphrase used wherever the verbatim was shaky.

### cBioPortal (`[speaker_0]`)
- **On hallucination + trust (clean):** "Okay, that's cool, but I know LLMs hallucinate. So did it come up with this stuff? Is it real?" — then routes the user back to the trusted website to validate.
- **On the self-improvement loop (clean, paraphrase-safe):** A user gives a thumbs-down; Claude (wired to LibreChat + Langfuse) is asked "Do you see any new feedback?", files a GitHub ticket, fixes it, and on approval he says "deploy to production."
- **Takeaway line (clean):** "There you have sort of your self-improvement loop, which I thought is kind of something to think about for your own products — like, how do you continuously improve it based on feedback from users?"
- *Note: the gene example "PIC3CA" is almost certainly **PIK3CA** (a real cancer gene); ASR rendered it phonetically.*

### Red Hat — Grace (`[speaker_1]`)
- **On the surprise factor (clean):** Roughly — most people know Red Hat for Linux (RHEL) or Kubernetes (OpenShift), "so you might be wondering, what are you doing here at an AI demo night? Well, we actually have AI too."
- **On the staged failure (clean):** "We're gonna have a build that succeeds, a test that fails on purpose, guys. On purpose."
- **On the eval gate (paraphrase):** If the LLM output doesn't match your evals / live up to your standards, the eval-gate deployment "will automatically revert back to the old deployment."
- **On good vs. bad prompts (clean):** the robust prompt scored ~100% keyword match; the two-sentence "bad prompt" identified only 2 of 5 failure reasons vs. 3 for the better one — a live illustration of prompt quality.

### RoleMate — Avik (`[speaker_2]`)
- **On the core problem (clean):** "Resumes are words on a piece of paper that are no longer a valid proof of skill."
- **On the value prop (paraphrase):** RoleMate increases the ROI of job-search time by cutting application busywork and telling you what jobs to apply to *based on your GitHub projects* — and what projects to build for the roles you want.
- **On warm intros (clean):** essentially, with an identical resume, the person "that has a connection to someone at a company that you're applying to … is always getting the job."
- **On hire-views (paraphrase; "veteran"/"attempts" flagged @19:35–19:52):** "Hire-views" [likely *hire views* / new interview format] arrive by surprise email with no prep time; RoleMate scores your practice run on tone, pace, and content to give you more than a one-shot attempt. `[VERIFY @19:35]`

### Clips — Max (`[speaker_3]`)
- **On the opening (mustache/"Holy" @24:35–24:40 flagged):** self-deprecating intro about a "fuzzy mustache" and hating using his phone. `[VERIFY @24:36]`
- **On what Clips does (clean):** it "takes links from YouTube, TikTok, articles, Reddit posts … and extracts them into usable links."
- **On modules (clean, paraphrase):** save a TikTok about the singularity → get a Libby link to rent the book; save a recipe → extract ingredients and load them into an Instacart cart ("I just got access to the Instacart API").
- **On positioning (clean):** "It's AI agnostic, so you can bring your own AI API key, and it's free. It uses Gemini by default." Free on iOS, beta on Android; web app, Chrome extension, Obsidian connector.

### Google Agents CLI — Pierre (`[speaker_4]`)
- **On the gap (paraphrase):** Antigravity/Gemini/Claude Code are good at agent work but don't always know new framework syntax (e.g., BigQuery) or best practices for connecting Google Cloud services, so they "end up token-maxing and spend lots of tokens unnecessarily" gluing things together.
- **On the metaphor (clean):** Google Cloud's services were "first designed for humans as the main users" — Agents CLI is "a common interface that makes life for agents very easy."
- **On the payoff (clean):** with the CLI, capable agents "do it with forty percent less tokens … instead of taking hours, you can do the same task in five minutes, ten minutes."
- **On the closing image (clean):** prototype → production has "a lot of squiggly lines along the way" — the CLI gives you "a highway that you can just run through."

### Docker — Chris (`[speaker_5]`)
- **On the monkey-in-a-loop problem (clean):** for the first agent shell command "you're like, 'Okay, I'll read this.' And then … the twelfth, you're like a monkey in a loop just hitting the button, which is not really ideal."
- **On why sandbox (clean):** "Somebody deletes the production database, which is not really ideal" — so "make these things run, but … put them in a box where they're not going to break anything."
- **On supply-chain risk (clean):** "Turns out npm is a great way to get a virus or a great way to leak your company's secrets." A year ago the advice was keep software up to date; now — "give it thirty days. Let somebody else work out what's wrong with it first."
- **On secrets (clean):** "We also don't give it any secrets … We rewrite the prompts on the way out. That way you don't have that problem of the LLM helping you by uploading your API key somewhere."
- **On the hard part (clean):** "We built a VMM from scratch. That was not easy."

## 6. Pro-Tips (if X, do Y)

1. **If you ship an LLM over your own data, give users a path back to a trusted source.** cBioPortal's Navigator agent generates real website links so researchers can validate the chat answer. *If your domain punishes hallucination (medicine, finance, legal), bolt a validation surface onto the agent, don't just trust the chat.*
2. **If you want continuous improvement, wire feedback straight into your dev loop.** Thumbs-down → ticket → auto-fix → "deploy to production." *If you collect feedback but it dies in a dashboard, you don't have a loop — close it to code.*
3. **If you deploy prompt-dependent features, gate deployments on evals.** Red Hat's eval gate auto-reverts when output fails. *If you change a prompt and can't auto-detect regression, you're flying blind — add a keyword/LLM-judge gate.*
4. **If your agents burn tokens gluing services together, give them skills + scaffolding.** Agents CLI's ~40% token cut came from constraining agents to known-good patterns. *If your agent "token-maxes" finding workarounds, the fix is curated skills, not a bigger model.*
5. **If you let an agent run shell commands autonomously, sandbox it in a microVM.** *If you're approving the 12th bash command by reflex, you've already lost the safety benefit — isolate instead.*
6. **If an agent needs credentials, keep secrets outside the box and rewrite prompts.** *If your agent can read your API key, it can exfiltrate it — Docker's prompt-rewriting-on-egress pattern is worth copying.*
7. **If you're early on dependency hygiene, delay updates by ~30 days.** Chris's "let someone else find the virus first" is a pragmatic supply-chain stance for small teams.

## 7. Best Practices / Patterns (recurring)

- **The trust/validation layer** — every serious demo had one (route-to-source, eval gate, sandbox, GitHub-proof, structured brains).
- **The feedback-to-code loop** — cBioPortal and Red Hat both turned user/test signal into automated tickets/reverts.
- **Constrain-don't-just-prompt** — skills, scaffolding, modules, and sandboxes all *narrow* the agent's action space to known-good paths.
- **Live demos with deliberate failure** — Red Hat's "test that fails on purpose" and Chris's one-handed live-coded slides treated fragility as honesty, not weakness.
- **Open source as the default substrate** — LibreChat, llm-d, ADK/Agents CLI, OpenShift, Docker all leaned open-source-first.
- **Observability is table stakes** — Langfuse, OpenTelemetry → Jaeger/Elk, "Lens Views" tracing all appeared without being the headline.
- **BYO-key + free** — RoleMate and Clips both used "bring your own LLM subscription, app is free" to dodge inference costs.

## 8. Pitfalls / Anti-Patterns

- **The approval-fatigue trap** — Chris named it: approving every agent command becomes reflexive ("monkey in a loop"), which silently defeats the human-in-the-loop safeguard. Approval UX that trains rubber-stamping is worse than no approval.
- **Token-maxing** — letting a smart agent brute-force its way through unfamiliar APIs wastes money and time; it *looks* like progress.
- **Trusting the chat answer alone** — in high-stakes domains, an un-validated LLM answer is a liability; cBioPortal's whole second agent exists to counter this.
- **Resume inflation via AI** — RoleMate's founding premise: AI made resumes cheap to fake, collapsing their signal value (and flooding hiring managers).
- **Secrets inside the agent's reach** — the npm/secret-leak risk Chris cited is now a live attack surface, not a hypothetical.
- **Demo-gods risk** — multiple demos stalled live ("our issue still isn't made yet," "this is a bit buggy"). The mitigation pattern (have a recording ready, narrate the wait) is itself a best practice; relying on a flawless live run is the anti-pattern.

## 9. Hot Takes (contrarian / surprising)

- **"Don't keep your software up to date — give it 30 days."** (Chris/Docker) A direct inversion of decade-old security gospel, born from the 2026 supply-chain reality.
- **The resume is dead as proof of skill** (RoleMate) — and AI killed it. Provocative for anyone whose hiring process still leads with the résumé.
- **Google Cloud's services "were designed for humans" and that's now a problem** (Pierre) — the agent-first interface thesis implies a wholesale re-platforming of cloud UX around non-human users.
- **Red Hat at an AI demo night is itself the surprise** — the "boring Linux company" reframing its entire stack around AgentOps is a quiet signal about where enterprise budgets are moving.
- **Build your own VMM from scratch in 2026** rather than use Firecracker — a contrarian engineering bet justified entirely by cross-platform (Mac/Windows) developer reality.

## 10. Substantive Insights (ranked by durability)

1. **The moat is the trust/feedback architecture, not the model.** This is the night's most durable, transferable lesson and it showed up six times independently. *(Highest content value for a GTM audience: it reframes "AI feature" buyers should ask about.)*
2. **Agent-first interfaces are a new product category.** Agents CLI and Docker Sandboxes both exist because tools built for humans don't serve agents well. Expect a wave of "for agents, not humans" re-tooling.
3. **Eval gates are becoming CI/CD primitives.** Red Hat treating "revert if evals fail" like a unit test is where the industry is heading — quality control for non-deterministic outputs.
4. **Token economics is now a first-class engineering KPI.** A 40% token cut as a *headline benefit* shows cost has moved from afterthought to selling point.
5. **Sandboxing is the precondition for agent autonomy.** You can't let agents run for hours unsupervised until containment is solved; Docker is betting that's the unlock.
6. **Proof-of-work data (GitHub) beats self-reported data (resumes)** in an AI-flooded signal environment — a pattern that generalizes well beyond hiring.
7. **The "self-improvement loop" is buildable today with off-the-shelf parts** (LibreChat + Langfuse + Claude + GitHub). Durable as a reference architecture for any team.

## 11. Anecdotes (narrative moments)

- **The one-handed live-coded demo.** Chris (Docker) opened by acknowledging he drew the worst slot — last, after a high bar — then live-coded his slides and ran the demo *one-handed*, narrating buggy moments in real time ("this is a bit buggy … there we go"). Vulnerable, credible, memorable.
- **"A test that fails on purpose, guys. On purpose."** Grace (Red Hat) repeating the line as the staged failure unfolded — turning a scripted break into audience rapport.
- **The awkward wait.** Grace narrating dead air while the GitHub issue refused to generate ("we can wait for it awkwardly now") — and it finishing right as she'd given up ("Oh, of course now it's finished").
- **Whisper redeems itself live.** The cBioPortal presenter's first chat query failed ("It doesn't work"), then the gene query worked ("Whisper works. That's great") — a small live-demo arc of failure-then-recovery.
- **The Victorian-bureaucracy multi-agent.** Pierre's demo prompt: a coder agent, a security-reviewer agent that critiques code "in Victorian language from the 1800s England" with "very harsh feedback," and a PM agent that loops — a playful way to show multi-agent orchestration via ADK.

## 12. Concept Glossary

- **MCP (Model Context Protocol)** — open standard for connecting LLMs to tools/data; cBioPortal and Clips both used MCP servers as the agent↔data bridge.
- **microVM / VMM** — a lightweight virtual machine and the Virtual Machine Monitor that runs it; Docker's isolation primitive for sandboxing agents (stronger than a container).
- **Eval gate** — a deployment guardrail that runs evaluations on model output and blocks/reverts the release if it fails a threshold.
- **LLM-as-a-judge** — using an LLM to grade another LLM's output (Grace contrasted this with simpler keyword matching).
- **Skills (agent skills)** — Markdown `SKILL.md` packages that inject specialized, current knowledge into an agent without bloating its context window (Google's Agents CLI model).
- **Token-maxing** — an agent burning excessive tokens brute-forcing workarounds it isn't optimized for.
- **Models-as-a-service** — self-service internal access to privately hosted models via an API gateway (Red Hat AI).
- **llm-d** — Red Hat's Kubernetes-native open-source framework for *distributed* LLM inference (transcribed "LLAP"/"lmv").
- **Self-improvement loop** — feedback → ticket → fix → deploy cycle that lets a product improve from user signal.
- **Proof of skill** — verifiable work artifacts (GitHub repos) used in place of self-reported credentials (resumes).

## 13. Tools / Companies Mentioned

- **cBioPortal** — open-source cancer-genomics portal; chat interface at chat.cbioportal.org. https://docs.cbioportal.org/ai-integrations/chat-interface/
- **LibreChat** — open-source multi-model chat framework; acquired by ClickHouse in 2026. https://clickhouse.com/blog/librechat-open-source-agentic-data-stack
- **ClickHouse** — columnar OLAP database; cBioPortal's analytics store. https://clickhouse.com
- **Amazon Bedrock** — AWS managed foundation-model service (serving Claude for cBioPortal). https://aws.amazon.com/bedrock/
- **Langfuse** — LLM observability/tracing platform. https://langfuse.com
- **Red Hat OpenShift AI** — enterprise MLOps/GenAIOps/AgentOps platform on Kubernetes. https://www.redhat.com/en/products/ai/openshift-ai
- **llm-d** — Kubernetes-native distributed LLM inference framework. https://llm-d.ai
- **Qwen** — Alibaba's open LLM family (Red Hat's demo model; transcribed "Quinn"). https://github.com/QwenLM
- **LM Eval** — open-source LLM evaluation harness used by Red Hat. https://github.com/EleutherAI/lm-evaluation-harness
- **RoleMate** — GitHub-as-proof-of-skill job-matching platform. https://rolemateapp.com
- **Clips** — personal link-extraction app (YouTube/TikTok/articles → structured "brains"). *Specific app URL unverified — see §16.*
- **Google Agents CLI** — CLI + skills to build/eval/deploy ADK agents on Google Cloud. https://github.com/google/agents-cli
- **Google ADK (Agent Development Kit)** — open-source code-first agent framework. https://adk.dev
- **Antigravity / Gemini / Claude Code / Codex** — coding assistants referenced as the agents the CLI augments.
- **Docker Sandboxes** — microVM isolation for AI coding agents. https://docs.docker.com/ai/sandboxes/
- **Firebase / Cloud Run / Firestore / GCS** — Clips' GCP backend; **yt-dlp, FFmpeg, Whisper C++** for media extraction.
- **Instacart API, Libby, Obsidian, Notion, NotebookLM** — Clips integration targets.
- **OpenTelemetry → Jaeger / Elk** — Red Hat's tracing/observability export path.

## 14. Stat Bank

| Stat | Who said it | Confidence |
|---|---|---|
| 10+ years of curated genomics data collection | cBioPortal | Clean |
| 500+ studies in the database | cBioPortal | Clean |
| ~40% fewer tokens using Agents CLI vs. unaided agents | Pierre / Google | Clean (verbatim "forty percent") |
| Task time cut from hours → 5–10 minutes with Agents CLI | Pierre / Google | Clean |
| ~2,000 GitHub stars on the Agents CLI repo | Pierre / Google | Clean (cited live) |
| ~10 years at Docker | Chris | Clean |
| 5 test cases used in the eval demo | Grace / Red Hat | Clean |
| "Bad" prompt = 2 sentences; identified 2 of 5 failure reasons; "better" prompt identified 3 | Grace / Red Hat | Clean |
| Good prompt scored ~100% keyword match on first two cases | Grace / Red Hat | Clean |
| Apply to "ten times the number of applications" (AI-enabled) | Avik / RoleMate | Clean |
| Supply-chain hygiene: wait ~30 days before updating software | Chris / Docker | Clean |
| Windows ARM64 support "coming soon" | Chris / Docker | Clean (paraphrase) |
| 33 of 6,725 transcript words flagged low-confidence (1.0 cutoff) | ElevenLabs REVIEW file | Clean (meta) |

## 15. Documentarian Angles (post ideas for Alex)

1. **"The model isn't the moat anymore — the trust layer is."** A room-report post built on the six-demos-one-thesis observation. GTM lens: this is exactly the question enterprise buyers should be asking vendors ("show me your eval gate / your sandbox / your feedback loop"), and most AE pitches still lead with model capability. Strong differentiated POV; you have six independent data points to back it.
2. **"A demo night with no consumer demos."** The pre→post gap as the hook: you went expecting consumer AI, got VMMs and CI pipelines. GTM lens: where the *budget and the builders* actually are in 2026 NYC — infra/devtools, not chatbots. Contrarian, scannable.
3. **Company spotlight: "Red Hat showed up to an AI demo night — and it mattered."** The "boring Linux company" reframing its whole stack around AgentOps, with the staged-failure eval-gate demo as the narrative spine. GTM lens: a signal for anyone selling *into* enterprise AI — the incumbents are repositioning, fast.
4. **Build-trigger post: "The self-improvement loop you can ship this weekend."** cBioPortal's LibreChat + Langfuse + Claude + GitHub feedback loop as a reference architecture. Ties directly to your own pipeline work (feedback→ticket→fix→deploy mirrors your measurement-rigor layer) — credible because you're building the same pattern.

## 16. Open Loops & Verification Flags

- **Speaker names:** Only first names were stated for most presenters. **"Avik" (RoleMate, Rutgers sophomore)**, **"Max" (Clips)**, and **"Pierre" (Google PM)** are transcribed first names not independently confirmed via web search — treat as tentative before tagging anyone publicly. **Grace (Red Hat)** and **Chris (Docker)** first names are clear from audio but last names are unknown. The **cBioPortal presenter is unnamed** in the transcript.
- **"Clips" app identity unresolved.** "Clips" is too generic to confirm a specific product via search; the GCP/Instacart/Obsidian feature set is distinctive but I could not match it to a verified public listing. Confirm the exact app name/URL with the presenter before referencing.
- **"Hire-views" / "veteran interviews"** (@19:35–19:52) — low-confidence words ("veteran," "attempts," "for," "your"). The intended term is likely a new one-shot interview format; meaning paraphrased. `[VERIFY @19:35]`
- **"Quinn" = Qwen** and **"LLAP"/"lmv" = llm-d** are high-confidence ASR corrections based on Red Hat's stack, but worth a 2-second confirm if quoted.
- **"PIC3CA" = PIK3CA** — near-certain gene-name correction; verify if used verbatim.
- **"Lens Views" (Clips tracing)** — possibly a product name (Langfuse? a custom tracer?) garbled by ASR; unverified.
- **"Victoria works at ClickHouse now"** — consistent with the ClickHouse/LibreChat acquisition but the named individual is unverified.
- **GitHub-star count (~2,000) for Agents CLI** — cited live; verify current number if used as a hard stat.
- **RoleMate two GitHub repos found** (`devgladstone/rolemate` and the live `rolemateapp.com`); confirm which is the demoed product before linking.

## 17. Enrichment Resolutions (verified via web search)

- **cBioPortal chat stack confirmed.** Built on LibreChat + Amazon Bedrock (Claude) + ClickHouse, with MCP servers bridging Claude to the data; two agents (cBioDBAgent, cBioNavigator). Sources: [cBioPortal chat interface docs](https://docs.cbioportal.org/ai-integrations/chat-interface/), [cBioPortal MCP docs](https://docs.cbioportal.org/ai-integrations/mcp/).
- **ClickHouse acquired LibreChat (2026)** — corroborates the presenter's "Victoria works at ClickHouse now." Sources: [ClickHouse blog](https://clickhouse.com/blog/librechat-open-source-agentic-data-stack), [SalesTechStar](https://salestechstar.com/partner-management-channel-enablement/clickhouse-acquires-librechat-to-democratize-ai-driven-analytics-through-the-open-source-agentic-data-stack/).
- **Google Agents CLI confirmed**, announced at **Google Cloud Next '26**; open source at `github.com/google/agents-cli`; turns any coding assistant into a Google Cloud agent-building expert via ADK + skills + scaffolding. Sources: [github.com/google/agents-cli](https://github.com/google/agents-cli), [Google Cloud docs — ADK + Agents CLI quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents/quickstart-adk), [Next '26 dev keynote codelab](https://codelabs.developers.google.com/next26/dev-keynote/building-agents-with-skills).
- **Docker Sandboxes confirmed** — launched 2026, microVM isolation for AI coding agents, **proprietary cross-platform VMM (not Firecracker) for macOS/Windows**, Sandbox Kits (YAML specs). Matches Chris's "built a VMM from scratch / Linux-Mac-Windows / secrets stay outside." Sources: [Docker Sandboxes docs](https://docs.docker.com/ai/sandboxes/), [Why MicroVMs — Docker blog](https://www.docker.com/blog/why-microvms-the-architecture-behind-docker-sandboxes/), [InfoWorld explainer](https://www.infoworld.com/article/4177309/docker-sandboxes-and-microvms-explained.html).
- **Red Hat AI stack confirmed** — OpenShift AI with MLOps/GenAIOps/AgentOps, **models-as-a-service** (API-gateway self-serve), **llm-d** distributed inference; a CI-failure-triage-via-LLM use case is documented by Red Hat. Sources: [Red Hat OpenShift AI](https://www.redhat.com/en/products/ai/openshift-ai), [Red Hat AI for developers](https://developers.redhat.com/products/red-hat-ai).
- **RoleMate confirmed live** at [rolemateapp.com](https://rolemateapp.com) — "Proof of skill for the age of AI," scores your GitHub, finds events/warm intros, drafts the intro. Matches the demo precisely. A related repo: [github.com/devgladstone/rolemate](https://github.com/devgladstone/rolemate) (confirm authorship before attributing).
- **Clips — not independently verifiable.** Searches surfaced generic Obsidian/TikTok clipping tools but no clean match to the demoed GCP-backed app with Instacart/Libby/Obsidian modules. Flagged as unresolved (§16).
