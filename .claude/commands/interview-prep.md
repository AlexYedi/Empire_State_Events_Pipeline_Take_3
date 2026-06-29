---
description: "Market-Intelligence Engine — Job-Search lens. Generate a 4-axis interview-prep dossier (company × role × stage × interviewer) by fanning out the reused research specialists from this thread, synthesizing via dossier-synthesizer, judge-gating, then persisting to the Postgres graph spine + Notion. Milestone 1 of the engine."
argument-hint: "[paste JD + company + interviewer + stage, or say 'prep me for [company]']"
---

# /interview-prep — Market-Intelligence Engine, Job-Search lens (Milestone 1)

Produce a decision-ready **interview-prep dossier** tailored on four axes: **company × role × interview
stage × interviewer**. Multi-agent fan-out runs **from this parent thread** (subagents cannot spawn
subagents — Anthropic SDK constraint); a downstream synthesizer assembles the dossier; a judge gates it;
the parent persists to Supabase + Notion.

Methodology (what a great dossier is, the north star, the quality bar): **`.claude/skills/interview-prep-dossier/SKILL.md`** — read it; this file is only the orchestration shape.

**North star (do not lose):** prove Alex is the best ***person*** for the job — skills **+ humanity**
(curious, kind, thoughtful), not a fact dump. Every section helps Alex show genuine curiosity & fit.

---

## Step 1 — Intake & confirm the 4 axes (this conversation, NOT a subagent)

Collect and confirm all four:
1. **Company** (+ website/domain if known)
2. **Role** — the JD pasted verbatim → keep as a `VERBATIM SOURCE` block, carried unchanged into every dispatch
3. **Interview stage** — `recruiter_screen` | `hiring_manager` | `technical` | `panel` | `cross_functional` | `executive` | `final`
4. **Interviewer(s)** — name + title (+ LinkedIn if known)

Also capture Alex's **stated focus/worry** (e.g. "nervous about systems design", "lead with GTM-engineering").
If any axis is missing, ask before proceeding — tailoring depends on all four. Do NOT delegate this step.

Then run a quick **dedup read** against the Postgres spine (`.claude/references/market-intel-spine.md`,
project `abkvgihlbwfloentugtd`) and Notion: does this company/interviewer already exist? Note matches so
Step 5 upserts rather than duplicates.

## Step 2 — Research fan-out (this conversation, parallel `Agent` calls in one message)

Dispatch in parallel from this thread. Each dispatch leads with the verbatim JD block (source of truth),
then the job-lens framing:

1. **company-researcher** — the company. Framing: "for an interview here — what would a sharp candidate
   know? funding, stage, product, headwinds." Gmail-first (prior correspondence with anyone there changes
   everything).
2. **topic-landscape-analyst** — the company's market segment + the role's domain topics. Framing: segment
   tailwinds/headwinds, where the field is moving, what a thoughtful candidate engages on.
3. **competitive-signal-scanner** — the company + named competitors. Framing: last-60-day signals + how the
   company is positioned vs. competitors + meta (what the company/its people say, what others say about them).
4. **person-researcher** — the interviewer(s) as the "people." Gmail-first, then web. Genuine hooks, recent
   activity, what they likely probe. One block per interviewer. (Skip only if no interviewer is named.)

Wait for all to return. If one returns thin, re-invoke just that one with deeper scope — don't restart.

## Step 3 — Synthesis (delegated to dossier-synthesizer)

```
subagent_type: dossier-synthesizer
prompt: [the 4 axes + verbatim JD + Alex's stated focus + dedup notes + all specialist returns]
```

The synthesizer assembles the 11-section dossier per the skill's structure. It does NOT research, does NOT
dispatch subagents, does NOT write to Notion/Postgres. Returns the dossier as text.

## Step 4 — Judge gate (this conversation)

Score the dossier against **`.claude/evals/rubrics/dossier-quality.md`** (LLM-as-judge, per-criterion
0–1 + reasoning, weighted composite). This is **advisory** (matches `/judge-build` posture): if composite
< pass band, surface the flag + weakest criteria and either (a) re-invoke the synthesizer with the judge's
notes, or (b) proceed and note the flag in the Notion write. Never hard-block. Append the run to the
eval run-log convention (`.claude/evals/`).

## Step 5 — Persist (this conversation — MCP writes are parent-thread only)

Per [[project_notion_writes_must_be_parent_thread]], do all writes inline here, never in a subagent.

**A. Postgres graph spine** — **REST API, NOT the MCP.** PostgREST at
`https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1/` (project `empire state ai`), `SUPABASE_API_KEY` read
from `Take_3/.env` at runtime (never printed). Upsert with header
`Prefer: resolution=merge-duplicates,return=representation`. ⚠️ NEVER use `mcp__claude_ai_Supabase__*` —
it's on the wrong account (see `.claude/references/market-intel-spine.md`). Read-before-write dedup:
- `company` — upsert on lower(name); set fields + `source`.
- `topic`(s) — upsert on lower(name).
- `person` — one per interviewer; search by name (+company) before insert; set `role_context='interviewer'`.
- `event` — `kind='role_posted'`, title = "[Role] @ [Company]", `source` = JD, `event_date` = today.
- `event_entity` edges — company(role=`employer`), each interviewer(role=`interviewer`), each topic(role=`subject`).
- Bump `last_engaged_at = now()` + `engagement_count + 1` on touched entities (reinforcement signal).

**B. Notion** — write the dossier (Content Draft `linkedin`/`notion_only` page, or a dedicated dossier page)
for the comment-review loop. Capture the page id and set `notion_page_id` on the Postgres rows. Follow the
notion-write gotchas (real newlines in update-page; `notion-search` not `notion-query-data-sources`).

## Step 6 — Present + report

Show the dossier in conversation, the judge verdict, and a confirmation block: Postgres rows created/updated
(with ids), the Notion page URL, and any Verification Flags. Then the efficacy-loop reminder: when the
interview happens, the recording → ElevenLabs / `/ingest-recording` path captures it (NOT Granola — dead on
device), and an `event kind='interview'` can be added to the timeline.

---

## Failure modes
- **Specialist thin** — re-invoke just that one with deeper scope; re-synthesize. Don't restart.
- **No interviewer named** — skip person-researcher; dossier notes the interviewer profile is unavailable and
  pivots Section 5 to "what this stage's interviewer type usually cares about."
- **Supabase REST error** — STOP writes; confirm the ref is `oicikjyzmxqfomrrqkvf` (`empire state ai`)
  and `SUPABASE_API_KEY` is set in `.env`; if tables 404, the one-time DDL hasn't been applied yet
  (`.claude/references/market-intel-schema.sql` in the dashboard SQL Editor). The Notion dossier still
  stands alone. Do NOT fall back to the Supabase MCP — wrong account.
- **Agent registry session-frozen** — this command + dossier-synthesizer were added to disk; they are only
  discoverable in a FRESH conversation. First run must be a new session.

## Ground truth references
- `.claude/skills/interview-prep-dossier/SKILL.md` — methodology + dossier structure + quality bar
- `.claude/agents/research/dossier-synthesizer.md` — synthesizer contract
- `.claude/references/market-intel-spine.md` — Postgres schema, project id, dedup rules
- `~/.claude/plans/where-do-we-stand-sunny-puzzle.md` — engine framing + all decisions
