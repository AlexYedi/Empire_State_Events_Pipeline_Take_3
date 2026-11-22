# Build in public — what ships and what never does (ruled 2026-09-19, Alex)

Both repos (`Empire_State_Events_Pipeline_Take_3`, `empire-state-hub`) are **public on purpose**. The work is
the portfolio: transparency, engagement, and something a hiring manager can actually read. The default is
**public**. This page lists the few exceptions, and each one exists to protect *someone*, not to hide the work.

## Never public
| What | Why | How it's enforced |
|---|---|---|
| Secrets (API keys, tokens, service-role keys) | account takeover / billing abuse | `.env` gitignored; `.env.example` holds empty values only; audit 2026-09-19 found **0** secrets in any history |
| Alex's private reference files: `me-model.md`, `target-companies.md`, `inbox-allowlist.md`, `inbox-denylist.md`, `inbox-discovery-*` | personal, family, and inbox detail | gitignored; purged from local history 2026-09-16; GitHub PR refs still hold old copies (YED-204) |
| **Other people's confidences:** material from an Event or Content Draft whose Notion "Off the record" checkbox Alex ticked, plus private DMs and emails. Talks, panels and Q&A at events are on the record; a speaker saying "this stays in the room" does not change that (YED-389) | it's their information, not ours, when it reached Alex privately or he chose to keep it out | ticked inputs never enter git or the graph (`notion_export.py` skips them; `post-event-synthesizer` lists them by section only); DMs and emails stay out of tracked files |
| **Raw recorded speech:** transcripts (`event-transcripts/`, `Event Content/**/*Transcript*`), ASR REVIEW sheets, slide↔transcript alignments, quote banks, quote-heavy post-event briefs and deep-dives | other people's words are private inputs, not ours to publish wholesale (invariant 4); only the quotes Alex chooses for a post go public | gitignored (2026-09-28, option A: untracked going forward, no history rewrite); kept local + R2 `esep-library` only |
| Personal contact details of anyone but Alex (emails, phones, home addresses) | PII; ADR-9 already keeps them out of the spine | HubSpot holds contact detail; fixtures use `*.example` domains |

## Public, and good to share
Skills, agents, commands, hooks, scripts, ADRs, evals and judge logs (including the failures: that's the
rigor story), roadmap, Linear-linked notes, event research and content drafts (speakers named, thanked, and tag-able per the content rules;
quotes source-checked), and the build journal. Raw transcripts are not on this list: see above.

## Judgment calls (Alex's own information, his call)
Things about Alex himself that are safe but worth a deliberate choice before an employer reads them.
Examples: compensation expectations, the target-company list, family-business context. Default: keep
comp numbers and named target lists out of public files, and describe the *method* instead. Current
rulings are recorded in YED-204.

## Before you commit
1. `git diff --cached` doesn't touch `.env*` or any gitignored path.
2. New transcript-derived files (posts, notes): check the source Event's and Content Draft's "Off the record" checkbox. If either is ticked, nothing from that input is committed. Don't grep transcripts for phrases: words never make a talk off the record (YED-389).
3. New fixtures: `*.example` domains only.
