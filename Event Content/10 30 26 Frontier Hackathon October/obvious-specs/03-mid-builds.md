# 03 · Mid-size backlog builds · Tier 2

Real items from the roadmap and To-dos. Each needs judgment inside a contract that already exists.
Run M1 and M3 as a hub initiative, and M2 as a pipeline initiative.

## M1 · Hub `/builds` page, replacing `/ops/content-performance` (hub)
Source: Specs & Ideas row "Hub: About/Work refresh + /builds page (replaces /ops/content-performance)" (Now, P2).
- New public route `src/app/(public)/builds/page.tsx` listing builds from a new committed, zod-validated
  `src/data/builds.json`: `{ slug, name, date, event?, oneLine, repoUrl?, demoUrl?, stack[] }`.
- Seed it with **only** these public entries, leaving fields empty where unknown: the Empire State pipeline
  (github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3), this hub, daytona-hacksprint-nyc.
- Add the link to the site header nav.
- **One-in-one-out:** the same PR deletes `src/app/ops/content-performance/` and `src/data/content-performance.ts`,
  plus any imports of them.
**Done when:** /builds renders the seed entries, the content-performance page and data are gone, and the build and check pass.
About/Work copy is out of scope (Alex writes it).

## M2 · Payload builder: catch mid-word truncation (pipeline)
Source: to-do "Fix 10-18 batch Notion formatting defects + harden the payload builder". Topic values were truncated mid-word.
- In `notion_payload.py`, add a validation that **flags** (non-zero exit, clear message naming the field) any text
  property value that ends mid-word because a length cut was applied. Define the rule precisely in the PR; for example, a value
  at exactly a known limit whose last character is a letter with no terminal punctuation.
- Add selftest cases: one truncated value fails, one complete value passes.
- It must not change the output for any payload that passes today, apart from the new flag.
**Done when:** the selftest covers it, and the PR body states the exact rule and its false-positive risk.

## M3 · RSS feed for Rooms + Journal (hub)
A distribution channel the Hub doesn't have yet. Add `src/app/feed.xml/route.ts` (statically generated) that emits RSS 2.0
with one item per room (title, link to `/rooms/<slug>`, date, the `what` line) and one per journal entry from
`src/data/build-journal.json`, newest first, capped at 50. Add `<link rel="alternate" type="application/rss+xml">` to the
public layout metadata. Only fields that are already public; no new dependencies.
**Done when:** `/feed.xml` validates as RSS 2.0, and lint, check and build pass.
