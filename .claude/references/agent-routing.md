# Agent routing: candidate menu

*Last verified 2026-10-15 · re-verify against `.claude/agents/` and the plugin on any registry change.*

A menu, not a hard-code. Hard routes cover fixed chains only; everything else is a judgment the session states out loud.

## 1. How to use it

Before any Agent dispatch:

1. **Hard route?** (§2) Use it. No judgment.
2. **Otherwise pick from §3** for the job family, and write one line before the call:
   `route: <agent> + <skills> · <why>` or `gap: no fitting agent · interim <agent>`.
   That line is what the dispatch record and the scheduled review read. No line = an unexplained dispatch.
3. **Model is a separate choice.** `model:` works on every agent: Fable for reasoning-heavy work, Opus for execution and prose, Sonnet for specialists and bulk.
4. **Check §4 budgets** before a wave.

`general-purpose` is a container for fan-out, not a thinker: use it only when no row fits, and log the gap. Plugin agents dispatch as `alex:<name>`. Bare skill names live in `.claude/skills/` or the plugin (load as `alex:<name>`); prefixed names (`engineering:`, `data:`, `anthropic-skills:`) are other installed plugins.

## 2. Hard routes (fixed chains)

| Trigger | Chain |
|---|---|
| `/event-deep-research` | `knowledge-conditioning` (Step 1.7b, always runs) → `company-researcher` ∥ `person-researcher` ∥ `topic-landscape-analyst` ∥ `competitive-signal-scanner` → `event-research-synthesizer` → `field-guide-renderer` (one call per section, then stitch) |
| Public copy before it leaves `needs_review` | `.claude/scripts/output_checks.py` → `output-evaluator` (mode `quote` and/or `source`) |
| Notion write from a validated payload | `.claude/scripts/notion_payload.py` prints VALID → `notion-writer` |
| `post_event_brief` | `post-event-synthesizer` (being added; until it lands, the parent thread) |
| Carousel render (HTML → PDF) | `visual-renderer` (being added; until it lands, the parent thread) |

HubSpot, the Supabase spine (`spine_client.py`), publishing and credit spend never route to a subagent.

## 3. Menu by job family

| Family | Candidates (pick one, say why) | Skills to load | Gap → interim |
|---|---|---|---|
| Research (market, company, trend) | `alex:research-analyst`; `topic-landscape-analyst` for a single-topic year review | `research-brief-blueprint`, `competitive-analysis`, `market-signal-tracker` | — |
| Content (posts, notes, comment loops) | `alex:content-correspondent` | `content-correspondent`, `pre-event-content`, `content-patterns`, `steering-interview` | editorial lead (calendar, format approval) → parent thread |
| Architecture / design | `alex:cto-principal-architect` (Fable); `Plan` for an implementation plan | `cto-architect`, `trade-off-analysis-method`, `ai-agent-design-patterns`, `multi-agent-orchestration` | — |
| Systems diagnosis ("why does this keep happening") | `alex:systems-analyst` (Fable) | `systems-thinking`, `systems-analyze`, `post-mortems-retrospectives` | single-incident debugger → `alex:systems-analyst` + `engineering:debug` |
| Build (scoped change, tests) | `alex:builder` | `karpathy-coder`, `tdd-workflow`, `git-collaboration-workflows` | agent engineer (prompts, skills) → `alex:builder` + `advanced-prompting-techniques`, `anthropic-skills:skill-creator` |
| Review (diff, artifact) | `alex:reviewer`; `/judge-build` on its artifact-class triggers | `code-review`, `quality-review-checklist` | — |
| Product / strategy | `alex:head-of-product` (Fable) | `ai-product-strategy`, `writing-prds`, `prioritizing-roadmap`, `consulting-roadmap-sequencing` | — |
| Career (resume, positioning, offers) | `alex:head-of-product` for framing; parent for anything reading `me-model.md` | `interview-prep-dossier`, `value-story-framework`, `creating-financial-models` | career strategist (pending) → parent thread |
| Learning (primers, recaps) | `alex:learning-coach-mentor` | `book-distiller`, `visualization-patterns`, `ai-engineering-foundations` | — |
| Data (schema, graph, queries) | `alex:cto-principal-architect`; `Explore` for read-only lookup | `knowledge-graph-modeling`, `database-designer`, `data-contract-framework`, `data:sql-queries` | data architect, DBA → `alex:cto-principal-architect` + these skills; DDL stays dashboard-only |
| Security / privacy | `alex:reviewer` (read-only) | `security-review`, `api-security-and-lifecycle` | security reviewer → `alex:reviewer` + `security-review`; guard/filter diffs still get human review |
| Ops (budgets, runs, health) | parent thread; `Explore` for log sweeps | `observability-designer`, `post-mortems-retrospectives` | system reviewer → `alex:systems-analyst` |
| Harness / Claude Code questions | `claude-code-guide` | — | — |

## 4. Budgets (per session)

| Limit | Value | On breach |
|---|---|---|
| Events in one wave | ≤3 | split across sessions |
| Live agents | ≤12 (harness hard cap 20) | stop and report; never re-dispatch silently |
| Fable or Opus in the background | ≤2 | queue the rest |
| WebSearch | 200, shared by every subagent | count in big waves; WebFetch primary sources |

A cap bounce or a spend-limit kill ends the wave: stop, report what landed, let Alex re-plan.

## 5. Trust tiers

| Tier | Agents | Web | Writes | Private files |
|---|---|---|---|---|
| Web/inbox readers | `company-researcher`, `person-researcher` (Gmail read), `competitive-signal-scanner`, `topic-landscape-analyst`, `alex:research-analyst`, `alex:learning-coach-mentor` | yes | local Write only (plugin pair); none for the specialists | no |
| Text-in / text-out | `knowledge-conditioning`, `event-research-synthesizer`, `field-guide-renderer` | no | none | only what the parent passes |
| Notion writer | `notion-writer` | no | Notion create/update, validated payload only | no |
| Builder | `alex:builder` | no | repo files under the caller's allowlist; no MCP writes | no |
| Reviewers / advisors | `output-evaluator`, `alex:reviewer`, `alex:systems-analyst`, `alex:cto-principal-architect`, `alex:head-of-product`, `alex:content-correspondent` | no | local Write at most; Notion read only | read if the parent points them at it |
| Parent thread | the session itself | yes | HubSpot, spine, Linear, Notion inline | yes |

Rule behind the tiers: no agent that reads untrusted web or inbox text holds an external write tool. `Bash` (builder, reviewer, CTO, systems analyst) is not a boundary: it can reach the network, so the tier holds by contract, not by tools line. An agent missing from the session's list means the registry is session-frozen: use a fresh session.
