---
name: interview-prep-dossier
description: Generate a job-search interview-prep dossier tailored on four axes — company × role × interview stage × interviewer. The first lens of the Market-Intelligence Engine. Use when Alex has an interview coming up and pastes a JD + company + interviewer + stage. Produces a synthesized dossier (Quick Take, Fit Thesis, company/market/competitor/funding context, decoded role, interviewer profile, org map, stage-specific prep, curiosity-demonstrating questions, blind-spot closer) written to Notion for comment review and persisted to the Postgres graph spine. Triggers on "prep me for [company] interview", "interview dossier for [role]", "I have a [stage] with [interviewer] at [company]".
---

# Interview-Prep Dossier (Job-Search lens — Market-Intelligence Engine)

The first lens of the Market-Intelligence Engine (plan of record: `.claude/references/roadmap.md`).
This skill proves the lens-agnostic engine end-to-end on the **Job-Search lens** by turning the same
reusable component analyses the engine runs (company · market-segment · competitor · funding · person ·
org-mapping · trend/conversation) into a single, decision-ready interview dossier.

**Orchestration shape lives in `.claude/commands/interview-prep.md`** (mirrors `/event-deep-research`:
parent-thread fan-out → synthesizer → judge gate → writes). This file is the **methodology** — what a
great dossier is, how it's tailored, and the quality bar.

## North star — the "best *person*" frame (do not lose this)

The goal is NOT a fact dump that proves Alex is the most *qualified*. It is to prove Alex is the best
***person*** for the job — skills **+ humanity**: curious, kind, thoughtful. "I'll get the job done and
then some, and they want to work with that guy." Every section is judged against one test:

> **Does this help Alex show genuine curiosity, thoughtfulness, and fit — not just recite facts?**

Concretely: surface real things Alex can be *genuinely* curious about, questions that demonstrate he
engaged with their actual work, and an honest read of where he fits. Banned: flattery, generic
compliments, fabricated hooks, and trivia with no conversational use.

## Required intake (the 4 axes)

1. **Company** — name (+ website/domain if known).
2. **Role** — the JD text, pasted verbatim (this is the `VERBATIM SOURCE` — never work off a summary of it).
3. **Interview stage** — one of: `recruiter_screen` · `hiring_manager` · `technical` · `panel` ·
   `cross_functional` · `executive` · `final`. (If unknown, ask; the dossier tailors heavily to it.)
4. **Interviewer** — name + title (+ LinkedIn if known). If a panel, list each; the dossier profiles each.

If any axis is missing, ask before generating — the tailoring depends on all four. Capture Alex's stated
focus too (e.g. "I'm worried about the systems-design portion", "I want to lead with GTM-engineering").

## Component analyses → researcher mapping (run from the parent thread)

The engine's reusable components, mapped to the existing research agents (reused, not rebuilt):

| Component | Agent | Job-lens framing passed in the dispatch |
|---|---|---|
| Company · funding · headwinds | `company-researcher` | "for an interview at this company — what would a sharp candidate know?" |
| Market-segment · competitor · trend/conversation · meta-sentiment | `topic-landscape-analyst` + `competitive-signal-scanner` | the company's segment + named competitors + what the company/its people say and what others say about them |
| Interviewer (+ org map signals) | `person-researcher` | the interviewer(s) as the "people" — Gmail prior-correspondence FIRST, then web; genuine hooks, what they likely probe |

Gmail-first applies (a prior thread with anyone at the company changes everything). Verbatim JD goes in
every dispatch ahead of the entity list (fidelity rule from `/event-deep-research`).

## Dossier structure (the deliverable Alex walks in with)

1. **Quick Take** — 30-sec mobile read: who they are · why this role/stage matters · the single sharpest
   angle for THIS interviewer at THIS stage.
2. **Fit Thesis** — the "why I'm the best *person*" narrative for this exact role: 3 pillars, each marrying
   a concrete skill/experience with a human dimension, framed in *this company's* context.
3. **Company Context** — synthesized: what they do · stage · funding (recency + citation) · market segment
   + tailwinds/headwinds · competitors + where they sit · signals from the last 90 days (funding, launches,
   exec moves). Each thesis/positioning claim carries a source (rule #12); unsourced → flag, don't state.
4. **The Role, Decoded** — what the JD is *really* hiring for (the unstated need behind the bullets) · how
   Alex's background maps, line by line · the 1–3 gaps to address proactively (not paper over).
5. **The Interviewer(s)** — bio · known POV · recent activity (last 6mo) · **prior correspondence** (Gmail)
   · genuine connection points · what they likely care about and will probe. One block per interviewer.
6. **Org Map** — who else is in/around the process · who influences the decision even if not in the room
   (skip-level, peers, the person whose problem this hire solves) · likely reporting line.
7. **Stage-Specific Prep** — tailored to the stage: what this stage actually tests, what to emphasize/
   de-emphasize, the common failure mode at this stage, and the one thing to nail.
8. **Questions to Ask** — role/person-specific and curiosity-demonstrating (NOT generic). Two buckets:
   (a) questions that show Alex engaged with *this interviewer's* work; (b) questions that surface what he
   genuinely wants to learn about the role/team/company. Every question passes the north-star test.
9. **Curiosity & Humanity Hooks** — specific, real anchors that let Alex be genuinely curious and human
   (a thing they built he finds interesting, a shared thread, an honest point of resonance). No flattery.
10. **Blind-Spot Closer** — the dimensions Alex normally "papers over with confidence for lack of time,"
    now closed: each named, with how to frame it honestly and turn it into a thoughtful exchange.
11. **Sources & Confidence** — citations, confidence levels, and Verification Flags (any unsourced thesis
    claim listed here, never promoted to fact in the body).

## Quality bar

- All 4 axes visibly drove the output — a reader can tell this dossier is for *this stage* with *this
  interviewer*, not a generic company brief.
- Fit Thesis pillars each marry skill + humanity; none is a pure credential recital.
- Every "Questions to Ask" item is specific enough that it could only be asked of *this* interviewer/role.
- Honesty rules (from `person-researcher`): no fabricated hooks — write "None found — engage in the room"
  rather than invent. No generic compliments. Unsourced thesis claims → Verification Flags only.
- Gaps are addressed, not hidden. The Blind-Spot Closer is the point of the whole dossier (Alex's Q4
  friction: "papering over blind spots with confidence").
- Confidence stated honestly per claim; thin research said so plainly, not padded.

## Persistence (parent thread only — MCP not available in subagents)

After Alex-review-grade synthesis passes the judge gate, persist to the graph spine via **REST** (project
`empire state ai`, ref `oicikjyzmxqfomrrqkvf`, `SUPABASE_API_KEY` from `.env` — **never the Supabase MCP**,
which is on the wrong account; see `.claude/references/market-intel-spine.md`) and mirror to Notion:
- **Postgres:** upsert `company` (dedup on lower(name)); upsert `topic`(s); upsert `person` for each
  interviewer (search-before-create); create an `event` with `kind='role_posted'` (title = role @ company,
  source = JD) + `event_entity` edges (company role=`employer`, interviewer(s) role=`interviewer`, topics
  role=`subject`). This seeds the timeline; Alex's eventual application/interview become later events.
- **Notion:** write the dossier as a Content Draft (or a dedicated page) for the comment-review loop, and
  set each row's `notion_page_id` back on the Postgres rows. Notion = review surface; Postgres = SoR.

## HITL posture

Judge-gated auto-commit, then async Notion-comment feedback — Alex is never a pre-commit bottleneck
(matches the engine's HITL decision and existing ship-all-variants + comment-review patterns). The
dossier-quality judge (`.claude/evals/rubrics/dossier-quality.md`) runs before the Notion write; a flag
is surfaced, not a hard block.

## References

- `.claude/commands/interview-prep.md` — orchestration shape
- `.claude/agents/research/dossier-synthesizer.md` — synthesizer contract
- `.claude/agents/research/{company-researcher,person-researcher,topic-landscape-analyst,competitive-signal-scanner}.md` — reused producers
- `.claude/references/market-intel-spine.md` — Postgres schema + project coordinates + dedup rules
- `.claude/references/roadmap.md` — MI Engine framing + milestones (the detailed `where-do-we-stand-sunny-puzzle.md` 20-Q framing file was machine-local and is retired)
