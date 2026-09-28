---
description: "Job-search lens. Generate a 4-axis interview-prep dossier (company × role × stage × interviewer): fan out the 4 research specialists from this thread, synthesize here against me-model §1.5 with the interview-prep-dossier skill, write the dossier to Notion for comment review."
argument-hint: "[paste JD + company + interviewer + stage, or say 'prep me for [company]']"
---

# /interview-prep — Job-Search lens

Orchestration shape only. Methodology, north star (the best *person*, not the most qualified), the 11-section dossier structure and the quality bar: **`.claude/skills/interview-prep-dossier/SKILL.md`**. Read it first.

## Step 1 — Intake (this thread)
Confirm all four axes; ask for any that are missing:
1. **Company** (+ domain)
2. **Role**: the JD verbatim, kept as a `VERBATIM SOURCE` block and passed unchanged into every dispatch
3. **Stage**: `recruiter_screen` · `hiring_manager` · `technical` · `panel` · `cross_functional` · `executive` · `final`
4. **Interviewer(s)**: name + title (+ LinkedIn)

Also capture Alex's stated focus or worry. Then read `.claude/references/me-model.md` (gitignored), **§1.5 Target-Role ICP** and the experience sections. The ICP drives the Fit Thesis and the gaps (YED-152). Never quote me-model into git, logs, or any file outside Notion.

## Step 2 — Research fan-out (parallel `Agent` calls, one message)
Each dispatch leads with the verbatim JD, then the job-lens framing from the skill's mapping table:
1. **company-researcher**: the company, Gmail-first.
2. **topic-landscape-analyst**: the segment and the role's domain topics.
3. **competitive-signal-scanner**: the company and named competitors, last 60 days.
4. **person-researcher**: each interviewer, Gmail-first. Skip this one only if no interviewer is named.

Wait for all four. If one returns thin, re-invoke only that one with deeper scope.

## Step 3 — Synthesis (this thread)
Assemble the 11-section dossier in the skill's structure from the four returns, the intake and me-model §1.5. Do not dispatch a synthesizer; the skill is the contract. Apply the honesty rules: unsourced thesis claims go to Verification Flags, and never write a fabricated hook.

## Step 4 — Notion write (this thread; MCP writes are parent-only)
1. Search before create: `notion-search` for the company or role in Content Drafts (and in Roles, if `/scan-roles` tracked it).
2. Write the dossier to Content Drafts as plain paragraphs (never code blocks), per `notion-write-gotchas.md`, and link the Roles row in the page body if one exists.
3. Status: `needs_review`. Alex reviews by inline comment.

## Step 5 — Report
Give the Quick Take in the conversation, the Notion URL and any Verification Flags. After the interview, the recording goes through `/ingest-recording`.

## Failure modes
- **No interviewer named**: skip person-researcher. Section 5 covers what this stage's interviewer type usually probes.
- **me-model.md absent** (fresh worktree without the symlink): stop and ask. A dossier without the ICP is a company brief.
- **Notion write fails**: show the dossier in the conversation so it is not lost, then retry the write.
