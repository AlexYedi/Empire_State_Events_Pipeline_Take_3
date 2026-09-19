# Build in public — what ships and what never does (ruled 2026-09-19, Alex)

Both repos (`Empire_State_Events_Pipeline_Take_3`, `empire-state-hub`) are **public on purpose**. The work is
the portfolio: transparency, engagement, and something a hiring manager can actually read. The default is
**public**. This page lists the few exceptions, and each one exists to protect *someone*, not to hide the work.

## Never public
| What | Why | How it's enforced |
|---|---|---|
| Secrets (API keys, tokens, service-role keys) | account takeover / billing abuse | `.env` gitignored; `.env.example` holds empty values only; audit 2026-09-19 found **0** secrets in any history |
| Alex's private reference files: `me-model.md`, `target-companies.md`, `inbox-allowlist.md`, `inbox-denylist.md`, `inbox-discovery-*` | personal, family, and inbox detail | gitignored; purged from local history 2026-09-16; GitHub PR refs still hold old copies (YED-204) |
| **Other people's confidences:** anything a speaker says is off the record ("this stays in the room", "please don't post this"), unannounced funding, private DMs or emails | it's their information, not ours; breaking a room's trust ends the documentarian edge | redact in the transcript *and* every derived file (brief, post, notes) before commit, using a dated `[REDACTED …]` marker that says why |
| Personal contact details of anyone but Alex (emails, phones, home addresses) | PII; ADR-9 already keeps them out of the spine | HubSpot holds contact detail; fixtures use `*.example` domains |

## Public, and good to share
Skills, agents, commands, hooks, scripts, ADRs, evals and judge logs (including the failures: that's the
rigor story), roadmap, Linear-linked notes, event research and content drafts, public-event transcripts
(speakers named, thanked, and tag-able per the content rules), and the build journal.

## Judgment calls (Alex's own information, his call)
Things about Alex himself that are safe but worth a deliberate choice before an employer reads them.
Examples: compensation expectations, the target-company list, family-business context. Default: keep
comp numbers and named target lists out of public files, and describe the *method* instead. Current
rulings are recorded in YED-204.

## Before you commit
1. `git diff --cached` doesn't touch `.env*` or any gitignored path.
2. New transcripts: search for "off the record|stays in the room|don't post|not public|confidential" and redact matches.
3. New fixtures: `*.example` domains only.
