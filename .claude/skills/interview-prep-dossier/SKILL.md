---
name: interview-prep-dossier
description: Generate a job-search interview-prep dossier tailored on four axes — company × role × interview stage × interviewer. The first lens of the Market-Intelligence Engine. Use when Alex has an interview coming up and pastes a JD + company + interviewer + stage. Produces a synthesized dossier (Quick Take, Fit Thesis, company/market/competitor/funding context, commercial-depth fields, decoded role, interviewer profile, org map, stage-specific prep, likely interview rounds, curiosity-demonstrating questions, blind-spot closer) written to Notion for comment review. Triggers on "prep me for [company] interview", "interview dossier for [role]", "I have a [stage] with [interviewer] at [company]".
---

# Interview-Prep Dossier (Job-Search lens — Market-Intelligence Engine)

The first lens of the Market-Intelligence Engine (plan of record: the Notion roadmap (https://app.notion.com/p/3e9d3699c2db8163919afb3040099d3c)).
This skill proves the lens-agnostic engine end-to-end on the **Job-Search lens** by turning the same
reusable component analyses the engine runs (company · market-segment · competitor · funding · person ·
org-mapping · trend/conversation) into a single, decision-ready interview dossier.

**Orchestration shape lives in `.claude/commands/interview-prep.md`** (parent-thread fan-out of the 4
specialists → synthesis in the parent against this file + `me-model.md` §1.5 → Notion write). This file is
the **methodology** and the synthesis contract — what a great dossier is, how it's tailored, and the
quality bar. (The `dossier-synthesizer` agent, the judge gate and the Postgres persist step were retired
2026-09-28; the agent is at `docs/archive/agents/dossier-synthesizer.md`.)

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
8. **Likely Rounds and Questions** — the predicted interview rounds for this stage at this company's
   growth stage, and per round the questions this interviewer most likely asks — derived from the
   decoded role (§4) and the interviewer profile (§5), never from a generic question bank.
9. **Questions to Ask** — role/person-specific and curiosity-demonstrating (NOT generic). Two buckets:
   (a) questions that show Alex engaged with *this interviewer's* work; (b) questions that surface what he
   genuinely wants to learn about the role/team/company. Every question passes the north-star test.
10. **Curiosity & Humanity Hooks** — specific, real anchors that let Alex be genuinely curious and human
    (a thing they built he finds interesting, a shared thread, an honest point of resonance). No flattery.
11. **Blind-Spot Closer** — the dimensions Alex normally "papers over with confidence for lack of time,"
    now closed: each named, with how to frame it honestly and turn it into a thoughtful exchange.
12. **Sources & Confidence** — citations, confidence levels, and Verification Flags (any unsourced thesis
    claim listed here, never promoted to fact in the body).

### Commercial-depth fields (E-09, YED-257)

Seven fields, rendered inside **Company Context** (§3), that make the dossier answer the
commercial-depth questions an interviewer will actually probe. Each is a research output from the
fan-out above — populated from evidence, never from guesswork:

| Field | What it answers |
|---|---|
| Growth stage + headcount band | Where the company is on the curve; how big the org actually is |
| GTM motion | PLG / sales-led / partner — and the evidence for the call |
| GTM-engineering function | Does one exist? Who owns the CRM-to-product seams? |
| CRM of record + named stack | Salesforce/HubSpot + the named tooling, from research not guesswork |
| Leadership metric | The number leadership is actually managing to this quarter |
| Leadership AI posture | Building, buying, or performing — with receipts |
| Comp band | Research-sourced best-evidence range with source; honest gap when unfindable. The pass/fail verdict is evaluated against `comp_gate.py` — cited, never restated; the gate is never the band's source (see below) |

**Comp band — the one field with a hard rule (judgment J2, 2026-10-31).** The band is
**research-sourced company data**: a best-evidence range with its source named (levels.fyi, the posted
JD, a board), or — when nothing reliable is findable — an **honest gap** stated plainly ("best evidence
is X, an adjacent level/last round; treat as directional — no verified range found"), never padded with
a guess. The verdict is then **evaluated against `.claude/scripts/comp_gate.py`**, the one executable
copy of the comp rules (role-radar Step 3, ADR-12): the dossier cites the gate's invocation and its
verdict output, and **never restates the arithmetic** (a second copy drifts — the same failure
role-radar's own guidance warns about). **`comp_gate.py` is never the band's source** — it evaluates
the researched band; it does not produce it. Run it per band with the posted text; where the gitignored
private floor is unreadable (e.g. a worktree), pass `--floor` explicitly — a missing floor is a loud
failure, never a silent pass.

## Quality bar

- All 4 axes visibly drove the output — a reader can tell this dossier is for *this stage* with *this
  interviewer*, not a generic company brief.
- Fit Thesis pillars each marry skill + humanity; none is a pure credential recital.
- Every "Questions to Ask" item is specific enough that it could only be asked of *this* interviewer/role.
- Honesty rules (from `person-researcher`): no fabricated hooks — write "None found — engage in the room"
  rather than invent. No generic compliments. Unsourced thesis claims → Verification Flags only.
- Gaps are addressed, not hidden. The Blind-Spot Closer is the point of the whole dossier (Alex's Q4
  friction: "papering over blind spots with confidence").
- Every Likely-rounds question traces to the decoded role or the interviewer profile; a question you
  can't trace is cut, not templated.
- No named-client stories anywhere in the dossier (E-09 addition 2): outcomes are described unnamed;
  client names appear only in a "Key accounts" logo line.
- Confidence stated honestly per claim; thin research said so plainly, not padded.

## Persistence (parent thread only — CLAUDE.md invariant 5)

Notion only: write the dossier to Content Drafts (plain paragraphs, `needs_review`) for the comment-review
loop, search-before-create. No graph write (the Postgres persist step was retired 2026-09-28 after one
run; the dossier lives in Notion).

## HITL posture

Alex reviews the dossier by inline Notion comment. No judge gate; the quality bar above is the
self-check before the write.

## References

- `.claude/commands/interview-prep.md` — orchestration shape
- `.claude/references/me-model.md` §1.5 — Target-Role ICP (gitignored; never quoted into git)
- `.claude/agents/research/{company-researcher,person-researcher,topic-landscape-analyst,competitive-signal-scanner}.md` — reused producers
- the Notion roadmap (https://app.notion.com/p/3e9d3699c2db8163919afb3040099d3c) — MI Engine framing + milestones (the detailed `where-do-we-stand-sunny-puzzle.md` 20-Q framing file was machine-local and is retired)
