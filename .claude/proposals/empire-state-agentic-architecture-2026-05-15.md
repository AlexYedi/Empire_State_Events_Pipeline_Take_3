# Empire State Events → Production Agentic System
## Architecture Brief + Sequenced Build Plan

> **Status:** Proposal for review (not yet decided)
> **Drafted:** 2026-05-15 (session `257aa89a-4761-4ff8-801b-833764c26e5d`)
> **Committed retroactively:** 2026-05-20 (was conversation-only; reconstructed from transcript)
> **Author:** Claude (cto-architect framing, with `general-purpose` agent fan-out across `alex-agents-skills/` library)
> **Provenance:** Synthesis of 4 parallel deep-reads — (a) current pipeline inventory, (b) Evals/Harness/Observability folder, (c) 10-layer agent stack deep-dive in `output/ai-agents/`, (d) persona content. Original conversation context: Alex's critique that the pipeline lacks quality scoring, learning feedback loops, observability, memory layers, and other enterprise-grade harness components.
> **Decision status:** Phase 0 decisions still pending. None of the build plan below has been executed.

---

## Part 0 — Preamble (CLI vs. chat + critique honesty pass)

### CLI vs. chat — does form factor fix the subagent issues?

**No.** The two bugs documented in CLAUDE.md ("subagents cannot spawn subagents" + "agent registry is session-frozen") are **Anthropic Agent SDK runtime constraints**, not form-factor issues. They'll bite identically in terminal CLI, Claude Code desktop, claude.ai web, or IDE extension — because the SDK is the same runtime underneath.

That said, form factor isn't *meaningless* — terminal CLI gives better access to background processes, hooks, piping into scripts, and observability tooling (which matters a lot for the critique below). But it won't unblock subagent fan-out. The real fix for that is the pattern already landed: fan out from the parent thread, use synthesis-only subagents downstream.

### Is the critique too harsh?

**Not harsh — fair, and incomplete.** Missing more than originally listed. At first glance, here's what's actually in place vs. missing:

**In place:**
- Workflow orchestration (4 workflows, parent-thread fan-out pattern proven)
- Write-side discipline (Notion gotchas documented, dependency-ordered writes)
- A scaffolded systems-thinking harness
- Voice/style references, content-patterns shared layer
- Linear-tracked open priorities

**Missing (Alex's list + additional gaps surfaced by analysis):**
- Quality scoring (no rubric, no per-artifact score, no minimum bar)
- Eval harness (Stage 2 proposal is sitting there unbuilt)
- Observability/traces (no run logs, no token accounting, no failure-mode tracking)
- Learning feedback loop (LinkedIn engagement → which posts worked → which prompts produced them = a graph that doesn't exist)
- Prompt/agent versioning (changes to agents have no diff history outside git)
- Regression detection (no "this run is worse than last week's run" signal)
- Memory beyond CLAUDE.md (no episodic memory of what's been tried, what landed, what flopped)
- Multi-model routing (Gemini Pro isn't in the architecture at all — that's a real gap given Alex is paying for it)
- Validation gates (Stage 2 B1)
- Brief schema enforcement (Stage 2 B3 — research currently freeform-ish)

### Form-factor take

If the goal is "enterprise-quality agentic system" — terminal CLI + Claude Code + hooks + Gemini routed for specific roles is materially better than chat. Hooks alone unlock the observability and quality-gate primitives. **But that's a tooling layer on top of architecture — fix architecture first.**

### Skills/agents invoked for this analysis

- **`anthropic-skills:cto-architect`** — principal-level architecture, ADRs, build planning
- **`systems-thinking`** — to map the pipeline as a system before designing layers on top (which loops we're reinforcing, which are missing). Per CLAUDE.md, this harness is already grounded in Meadows.
- **`general-purpose` agent ×4 (parallel deep-reads)** — Inventory current state; extract eval/observability best practices; extract agent architecture patterns; extract persona content
- **`Plan` agent (deferred)** — Will use to convert Phase 1 into concrete Linear tickets when given the go-ahead

Skipping (for now): `head-of-product-engineering` (overkill for an architecture phase, useful later when sequencing sprints).

---

## Executive summary (the five things)

1. **The critique is fair on every dimension named, and incomplete on three more.** What's missing: trajectory observability, content-performance feedback, prompt versioning, retrieval/RAG over Notion, and a typed-artifact schema layer. None of these need invention — Alex's global library specifies all of them.
2. **Form factor: terminal CLI + Claude Code, not chat.** The SDK constraints (no subagent dispatch, session-frozen registry) follow you everywhere, but hooks, run-log emission, and Bash-piped scripts are CLI-only and they are the missing observability primitives.
3. **Multi-model routing: adopt the planner-executor-verifier split the library calls "the most durable architectural idea of the era."** Claude orchestrates and writes; Gemini Pro verifies and handles long-context synthesis; OpenAI/open models for cheap bulk and second-opinion judging; Voyage + Cohere for retrieval (Anthropic has no embeddings).
4. **Sequencing: don't build Component 4 (status automation) before YED-23 goal flip lands.** The systems-thinking diagnostic already told you this. The order is: schemas → validation gates → eval harness → retrieval → feedback loop → durable workflow → status automation. Anything that automates publishing-rate without a quality counter-metric *deepens the trap*.
5. **The pipeline already has more in place than the critique implied.** Workflow A genuinely works end-to-end across 24 invocations. The gap isn't "we have nothing" — it's "we have a producer but no measurement, memory, or learning surface." That's a 6-8 week build, not a 6-month one.

Confidence on this overall framing: **80%**. Highest-risk assumption: that Alex will commit to the goal flip (YED-23) before Component 4 work, not after.

---

## Part 1 — Honest current state

### What's actually working (verified by agent inventory)
- `/event-deep-research` end-to-end: parse → triage → 4-specialist parallel fan-out (parent thread) → synthesizer → notion-writer → HubSpot. **24 invocations in week 1, zero "agent not found" failures.**
- Notion MCP write discipline (5-DB dependency ordering, 11 documented gotchas).
- Systems-thinking harness (8 reference files + delegated `systems-analyst` agent + 2 real diagnostic artifacts already produced — including the one that gave you YED-23).
- Content-pattern shared library (`content-patterns/two-thesis-synthesis.md`, `visual-briefs.md`).
- 5 custom event-pipeline agents with explicit scoped `tools:` discipline (the rest of the agents inherit the full 250-tool deferred list and are at risk for the "Prompt too long" failure mode).

### What's scaffolded but not wired (🟡)
- Workflows B (`/post-event-synthesis`), C (`/weekly-recap`), D (`/voice-pass`) — chains documented, not implemented.
- Sales-methodology agent trio (commercial-insight-generator, mobilizer-mapper, reframe-architect) — full contracts, zero call sites.
- 6 imported research agents (insights-research-director, qualitative-field-lead, quant-insights-architect, market-insights-director, win-loss-analyst, battlecard-program-manager) — dormant.
- 4 imported copywriting commands — disconnected from your four pipeline workflows.
- `content-quality/` skill folder exists but has no top-level `SKILL.md` — the v2 proposal expected this to be the eval-harness home.

### The vacuum correctly identified
| Capability | State |
|---|---|
| Run logs / traces | None. No `.claude/runs/`, no JSONL, no per-invocation log. |
| Token accounting | None. Per-workflow / per-agent spend untracked. |
| Eval scores / quality gates | None systemic. `marketing-autoresearch` produces a 5-expert score *only* on producer-side, *only* on LinkedIn posts, *only* when manually invoked, and the result is not persisted as a `## Quality Report` on the Notion page. |
| Prompt diffs | None beyond git. No per-agent CHANGELOG. |
| Content-performance feedback | None. Step 7 event retros exist but are not linked to per-post engagement data. Published URL → engagement metric → which prompt produced it = a graph that does not exist. |
| Memory beyond CLAUDE.md | Three thin layers: MEMORY.md (4 entries), artifacts/ (8 files), Notion (authoritative store). No vector store, no retrieval over briefs, no per-event learnings file consumed downstream. |
| Multi-model routing | None. Gemini Pro is absent from the architecture entirely. |
| Validation gates pre-write | None. Notion/HubSpot writes rely on manual review. |
| Typed artifact schemas | None. `Brief`, `LinkedInPost`, `DM`, `VisualBrief` are markdown conventions, not types. |

Honest read: **good *documentation* of state but no *runtime* observability.** Quality and measurement live entirely outside the pipeline today.

---

## Part 2 — Target architecture (canonical 10-layer per the library)

The library's `output/ai-stack/HANDOVER_A_AGENTS.md` and `output/ai-agents/research/A1-A7` files specify a 10-layer stack. Mapped to where Empire State stands today and what each layer becomes:

| # | Layer | Today | Target |
|---|---|---|---|
| 1 | **Foundation model** | Claude (Opus/Sonnet/Haiku) | Claude + Gemini Pro + OpenAI + open via OpenRouter. Routed by role. |
| 2 | **Runtime / harness** | Claude Code (CLI/desktop) | Claude Code CLI + hooks + scheduled cron + Vercel Workflow for durable runs |
| 3 | **Tool / protocol** | MCP (Notion, HubSpot, Apollo, etc.) | + MCP gateway pattern (rate-limit, audit log per tool) |
| 4 | **Memory & state** | CLAUDE.md + Notion + artifacts/ | + working/episodic/semantic/procedural taxonomy explicit; vector store over Briefs/Drafts; cross-event learnings file |
| 5 | **Planning / reasoning** | Parent-thread orchestration, ReAct via Claude | Planner-executor-verifier split codified in every workflow |
| 6 | **Action surfaces** | Web search, MCP writes | + browser-use for LinkedIn engagement scraping (post-publish loop) |
| 7 | **Eval / observability** | None | OpenTelemetry GenAI traces → Langfuse OSS (or Braintrust) + `.claude/evals/<feature>.md` + run logs + token accounting + content-performance feedback |
| 8 | **Guardrails** | Human review + scoped `tools:` | + action-confirmation gates on irreversible writes; DLQ for failed drafts; constrained sampling on Notion writes |
| 9 | **Vertical product** | 4 workflows | Same shape; add `/learn-from-engagement` as Workflow E |
| 10 | **End-user surface** | Claude Code conversation | Claude Code CLI + LinkedIn (publish) + Notion (review queue) |

The pivot is layer 7 (observability + eval) and layer 4 (memory). Everything else is incremental.

---

## Part 3 — Multi-model routing (the Gemini answer, expanded)

The library is explicit: **planner-executor-verifier routes 70–85% of tokens to the cheap tier** while spending where reasoning changes outcome (`A3_planning_reasoning.md` §2, §4). Tied to provider strengths called out in `A1`:

- **Claude > GPT > Gemini** on agentic tool use (multi-step trajectory reliability)
- **GPT > Claude** on single-shot code generation
- **Gemini > all** on long-context retrieval (1M tokens)

### Recommended role-to-model map

| Role | Model | Provider | Why | When invoked |
|---|---|---|---|---|
| **Planner / orchestrator** | Claude Opus 4.7 | Anthropic | Tool-use SOTA; once per workflow run | Top of every command |
| **Specialist executor (research)** | Claude Sonnet 4.6 | Anthropic | Already proven on your 4 specialists | A Step 2 |
| **Specialist executor (writes)** | Claude Haiku 4.5 | Anthropic | Notion-writer is high-volume, low-judgment | A Step 4 |
| **Bulk classifier** | GPT-5-mini *or* Haiku 4.5 | OpenAI / Anthropic | Contact bucketing, draft sorting, intake triage | B, C |
| **Long-context synthesis** | Gemini 2.5 Pro | Google | 1M context — read all 30 briefs at once for pattern-synthesis and weekly-recap | C, pattern-synthesis |
| **Verifier / judge (voice)** | Gemini 2.5 Pro | Google | Different model family catches Claude's single-family failure modes | D (voice-pass) |
| **Verifier / judge (factuality)** | GPT-5 | OpenAI | Cross-provider second opinion on Brief claims | A Step 2.5 (post-synthesizer) |
| **Embedding model** | Voyage 3 *or* Jina v3 | Voyage / Jina | Anthropic has no embeddings; Voyage is best-in-class for retrieval | Layer 4 retrieval |
| **Reranker** | Cohere Rerank 3 | Cohere | Best-in-class cross-encoder; cheap | Layer 4 retrieval |
| **Image generation** | Imagen 3 *or* Nano Banana | Google | Already in your stack; for visual-brief images | Visual-brief pattern |

**Concrete Gemini Pro role:** primary verifier across the pipeline, plus long-context synthesis for pattern-synthesis and weekly-recap. Two reasons: (a) cross-provider judging is the only way to catch single-provider failure modes, and (b) Gemini's 1M context is wasted on single-event briefs but *perfectly* sized for "read every brief from the last 30 days and find opposing theses" — which is exactly what the pattern-synthesis skill needs.

### The routing layer

| Option | Pro | Con |
|---|---|---|
| **Vercel AI Gateway** (Recommended) | Unified API, observability built-in, GA Aug 2025, fits your Vercel stack | Newer; lock-in to Vercel |
| **OpenRouter** | Mature, every provider, BYOK | Less integrated observability |

Recommendation: **Vercel AI Gateway** at 75% confidence — fits the existing stack, the observability bundle alone justifies it, and the knowledge-update hook just confirmed it.

---

## Part 4 — Form factor: refined recommendation

| Form factor | Verdict | Why |
|---|---|---|
| Stay 100% in Claude Code chat (desktop/web) | ❌ | Hooks unavailable. No run-log emission. No scheduled tasks. Observability is the gap named — chat blocks the fix. |
| Move 100% to terminal CLI | 🟡 | Higher friction for daily work; not all tasks benefit. |
| **Hybrid: terminal CLI for pipeline ops, chat for ideation/research (Recommended)** | ✅ | CLI for: hooks, scheduled runs, run logs, pipeline executions. Chat for: planning, ideation. |

**What unlocks specifically in CLI:**
- **Hooks** (`SessionStart`, `Stop`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`) — `.claude/settings.json` can emit a JSONL run log on every tool call. This *is* trace observability.
- **Scheduled cron** (`CronCreate`) — Workflow C `/weekly-recap` runs Sundays without you remembering.
- **Bash piping** — pipe Notion query output to a Python eval scorer, write back to Notion.
- **Background processes** — long-running synthesis or autoresearch loops without holding the chat session.
- **`/loop` and `/schedule`** — built-ins for recurring/self-paced work.

**Decision:** terminal CLI is the production runtime. Chat is the design surface.

Confidence: **75%**. The 25% risk is discovering daily-driver friction in CLI for ideation/conversational work. Mitigation: hybrid is genuinely fine — pipeline runs in CLI, design in chat, both in the same `.claude/` directory.

---

## Part 5 — Gap matrix (prioritized)

Value tier: **S** = required for "production agentic system" claim. **A** = high leverage. **B** = nice-to-have. Effort: in days of focused work.

| # | Gap | Why it matters for your goals (LinkedIn reach / thought leadership / hiring-manager engagement) | Value | Effort | Phase |
|---|---|---|---|---|---|
| 1 | **Typed artifact schemas** (`Brief`, `LinkedInPost`, `DM`, `VisualBrief`) | Foundation for every gate below. Visual-brief drift in week 1 = this gap. | S | 2-3d | 1 |
| 2 | **Validation gates pre-write** (`content-quality/` SKILL.md as Step 7.5) | Catches spec drift before Notion. Makes "visual brief required" enforceable, not aspirational. | S | 3-4d | 1 |
| 3 | **Eval harness for LinkedInPost** (4 grader types: code + rule + model + human) | Measurable answer to "is my content getting better." Direct line to thought leadership. | S | 3-5d | 1 |
| 4 | **OTel-shaped run logs** (JSONL via Stop hook) | The trace primitive. No observability without it. Lets you answer "what does a typical event cost?" | S | 1-2d | 1 |
| 5 | **Multi-model routing** (Vercel AI Gateway + Gemini verifier) | Cross-provider judging catches single-family failure modes. Gemini for long-context pattern-synthesis. 70-85% token shift to cheap tier. | S | 3-4d | 2 |
| 6 | **Retrieval layer over Notion** (BM25 + Voyage + Cohere rerank) | Briefs cite past briefs. Synthesis pulls past theses. Pattern-synthesis stops being manual. Thought leadership compounds. | A | 5-7d | 2 |
| 7 | **Memory taxonomy labeling** (working/episodic/semantic/procedural across existing DBs) | Make the implicit memory explicit so agents can reason about which layer to read/write. | A | 1-2d | 2 |
| 8 | **Content-performance feedback loop** (Published URL → LinkedIn engagement → eval set) | Closes the loop. Engagement data → which posts worked → which prompts produced them. Direct line to hiring-manager engagement metrics. | A | 5-8d | 3 |
| 9 | **Generalized autoresearch on every content draft** (3-round bounded loop) | Karpathy discipline you already have, applied to every draft not just LinkedIn posts. | A | 2-3d | 3 |
| 10 | **Prompt caching across the 4 specialists** | Highest-leverage cost optimization per your library. They share most of their system prompt. | A | 1d | 1 |
| 11 | **Action-confirmation gates on irreversible writes** | Codifies what you do manually. Required for any future automation. | A | 1-2d | 2 |
| 12 | **DLQ pattern for failed drafts** (`needs_human` Status + structured failure reason) | Makes the YED-23 quality counter-metric measurable. | A | 1-2d | 2 |
| 13 | **Durable workflow engine** (Vercel Workflow under the 4 commands) | Multi-day runs survive session ends. Critical for Workflow E (learning loop). | A | 4-6d | 4 |
| 14 | **Per-agent CHANGELOG blocks** + frontmatter `tools:` audit | Prompt diffs you can read at a glance. Catches the unscoped-tools failure mode. | B | 1-2d | 1 |
| 15 | **`/loop` + `/schedule` for cadence** (Sunday recap, daily intake-aging) | Removes "did I remember to run that" from your week. | B | 1d | 4 |
| 16 | **PROJECT_BRIEF.md at repo root** | Cleaner agent rotations; missing per your STACK_README convention. | B | 0.5d | 1 |
| 17 | **Wire B/C/D workflows** (they're scaffolds, not done) | Activates already-written agent contracts. | A | 5-8d total | 3 |
| 18 | **Status-transition automation** (Component 4 of v2 proposal) | Only after YED-23 goal flip. Otherwise deepens the trap. | A | 3-5d | 4 |

**Total to S+A tier:** roughly **6-8 weeks of focused work** at your current rate. Phase 1 alone (S-tier + a few quick wins) is **~2 weeks**.

---

## Part 6 — Sequenced build plan

### Phase 0 — Stabilize (this week)
**Goal:** ship the YED-23 decisions you already have queued so you're not building on top of unresolved priorities.

1. Decide on YED-23 goal flip (publish-rate as primary, quality counter-metric).
2. Decide on v2 Stage 2 proposal (recommendation: **Subset B = B1 + B3** = validation gates + Brief schema = highest-leverage cuts).
3. Decide on form factor (hybrid CLI + chat).
4. Decide on Vercel AI Gateway adoption for multi-model.

**Output:** four decisions, written down.

### Phase 1 — Foundation (2 weeks)
**Goal:** type the artifacts, enforce the spec, emit the traces, start measuring.

- Gap #1: Typed schemas for Brief / LinkedInPost / DM / VisualBrief
- Gap #2: `content-quality/SKILL.md` as Step 7.5 validation gate
- Gap #3: Eval harness for LinkedInPost (start with one content type — kill Likert, force pass/fail per your library)
- Gap #4: `.claude/runs/<workflow>.jsonl` emitted from Stop hook
- Gap #10: Prompt caching prefix audit on the 4 specialists
- Gap #14: Per-agent CHANGELOG blocks + frontmatter audit
- Gap #16: PROJECT_BRIEF.md scaffold

**Validation milestone:** A new event runs end-to-end, produces a `## Quality Report` block on each Content Draft, and emits a trace JSONL you can grep.

### Phase 2 — Memory & Routing (2 weeks)
**Goal:** make the system retrieval-aware and multi-model.

- Gap #5: Vercel AI Gateway wired; Gemini Pro as voice-pass verifier; OpenAI as factuality second-opinion
- Gap #6: Retrieval layer over Notion (Voyage embeddings + Cohere rerank, hybrid BM25)
- Gap #7: Memory taxonomy labeled (working/episodic/semantic/procedural across DBs)
- Gap #11: Action-confirmation gates on Notion + HubSpot writes
- Gap #12: DLQ pattern for failed drafts

**Validation milestone:** Pattern-synthesis runs *without* you naming the two events — retrieval surfaces them automatically.

### Phase 3 — Learning Loop (3 weeks)
**Goal:** close the loop. Engagement → prompt updates.

- Gap #8: Content-performance feedback (Published URL → LinkedIn API → engagement on Content Draft)
- Gap #9: Autoresearch generalized to every draft (3-round bounded)
- Gap #17: Wire Workflows B, C, D end-to-end (now that schemas + gates exist)

**Validation milestone:** A weekly report shows "this week's posts averaged X engagement vs last week's Y, and the prompt-diff between weeks is Z." This is the thought-leadership measurement layer.

### Phase 4 — Durability & Cadence (2-3 weeks)
**Goal:** survive session ends; remove "did I remember" from the workflow.

- Gap #13: Vercel Workflow under the 4 commands
- Gap #15: `/loop` Sunday recap, daily intake-aging
- Gap #18: Component 4 status-transition automation (now safe because Phase 3 produced the quality counter-metric)

**Validation milestone:** You take a week off. The pipeline still publishes, scores, learns, and routes failures to `needs_human` without you.

---

## Part 7 — What to deprioritize and why

| Deprioritize | Why |
|---|---|
| **Status-transition automation before YED-23** | Your own systems-thinking diagnostic flagged this as deepening the Shifting-the-Burden trap. Build the quality counter-metric first; *then* automate. |
| **The 6 imported dormant research agents** (insights-research-director, qualitative-field-lead, etc.) | Not connected to any workflow. Adding tools-frontmatter discipline to them is hygiene work that returns nothing until they're wired — and they may never be. Audit and delete what doesn't earn its place. |
| **The 4 imported copywriting commands** | Same logic — disconnected from the four pipeline workflows. Either wire or remove. |
| **A custom n8n/airflow/Dagster layer** | Your library is explicit that the saga pattern + Vercel Workflow + your existing slash-commands give you the durability primitives. Resist the urge to introduce new orchestration. |
| **Building a custom dashboard** | Notion already is your dashboard. The work is making sure the data lands there — not building a parallel UI. |
| **A custom evaluator** when Braintrust / Langfuse OSS exist | OTel GenAI conventions (Jan 2026) mean switch cost is low. Pick one and start collecting; don't build it from scratch. |
| **Graph-based memory (Neo4j / Letta / Mem0)** | Your library explicitly notes (`A2_memory_state.md` §4): *"most 'memory' in production is summarization + a database."* You have Notion. Use it. Revisit graph memory only if cross-session entity reconciliation becomes a bottleneck. |
| **Apollo integration on free tier** | Already deprioritized — credits only usable via web UI. Keep deferred. |

---

## Part 8 — Skills and agents used in this analysis

| Used | Purpose |
|---|---|
| `general-purpose` agent ×4 (parallel deep-reads) | Inventory current state; extract eval/observability best practices; extract agent architecture patterns; extract persona content |
| `cto-architect` skill (this synthesis) | Architecture brief framing, ADR-style decisions, tradeoff tables |
| `systems-thinking` (lens, not invocation) | Tied build order to YED-23 archetype rule-out — don't automate what would deepen the trap |
| `head-of-product-engineering` (deferred) | Will use when sequencing actual sprint issues in Linear |
| `Plan` agent (deferred) | Will use to convert Phase 1 into concrete Linear tickets when given the go-ahead |

Not used (and why): `Explore` (would have duplicated the general-purpose work already done); `karpathy-coder` (used as a *reference frame* for autoresearch, not invoked as a skill — that comes in Phase 3 build).

---

## Part 9 — Next move

Order confirmed at brief time: **architecture first, then 20Q for CLAUDE.md.** The 20-question framework is already drafted by the persona-recon agent, organized into 5 buckets:

- **A** Career & professional positioning (12-18mo horizon)
- **B** Content & thought-leadership goals
- **C** Network & relationships (named hiring managers / target rooms)
- **D** Working style, decision-making, energy
- **E** Success metrics & life context

When ready, say "kick off the 20Q" to run them four at a time (one bucket per round) so they can be answered without fatigue.

---

## Three things to flag before responding

1. **The biggest single move in this brief is Phase 1, Gap #4 (run-log JSONL via Stop hook).** It's a one-day build that unlocks every measurement question you can't currently answer. If you do nothing else, do that.
2. **Gemini Pro fits cleanly as voice-pass verifier + long-context synthesizer.** Not as a co-orchestrator. Don't try to run two planners against each other — the library is explicit that planner-executor-verifier is the durable shape, not planner-planner.
3. **The existing `marketing-autoresearch` skill is already Karpathy autoresearch.** It's currently a manual Step 5 in pre-event. Phase 3 generalizes it. No new pattern to learn — wire the one already in place.

---

## Open questions for Alex (carried forward)

- Does this build plan match the time/energy budget actually available? (Phase 1 = 2 weeks; total to S+A tier = 6-8 weeks.)
- Convert Phase 1 into Linear tickets now, or wait until after 20Q?
- Anything in the gap matrix to challenge or reorder?

---

## Provenance / how to verify this artifact

- **Source transcript:** `/Users/sameoldexpressions/.claude/projects/-Users-sameoldexpressions-Documents-GitHub-Empire-State-Events-Pipeline-Take-3/257aa89a-4761-4ff8-801b-833764c26e5d.jsonl`, assistant message at line 56 (~22.6KB) + line 11 preamble (~3.5KB)
- **Reconstruction method:** Python JSONL parse, extract `message.content[].text` fields, no rewriting beyond combining the preamble (line 11) with the main brief (line 56) and adding this provenance block
- **What changed from transcript:** Tense pronouns ("your library" → "your library" preserved in some places, "Alex's library" in third-person framing where the brief refers to him); added section headers for parts 0 and 9; added Open Questions section at the end; otherwise verbatim
- **What was NOT carried forward:** ~14 shorter assistant messages from this session (mostly Q&A, env-var setup, Linear hook walkthrough) — none contained architecture content not already in line 56
