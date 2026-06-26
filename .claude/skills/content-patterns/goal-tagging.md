# Goal-tagging convention (Content Drafts) — assigned goal at creation

Added 2026-06-26 (Linear YED-90 / PRD US-4). Every Content Draft gets a **Goal** + **Target** *at creation*, so the measurement layer can later grade **outcome vs. assigned goal** (the acted-on-value north-star). Imported by the content skills (`pre-event-content`, `content-correspondent`, `pattern-synthesis`) and applied by `notion-writer` when it creates the row.

## Notion fields (Content Drafts DB `6c24c9f5…`)
- **Goal** (select): `reach` · `engagement` · `connection` · `meeting` · `hybrid` · `internal`
- **Target** (text): the concrete, checkable target — e.g. `"500 impressions"`, `"3%+ engagement"`, `"accept the connection"`, `"book a coffee"`.

## Default Goal by Content Type (apply unless the skill/Alex overrides)
| Content Type | Default Goal | Target hint |
|---|---|---|
| `linkedin_post_pre` (incl. "The Upcoming Week" roundup) | `reach` | impressions/views; the roundup "sets the table" |
| `linkedin_post_post` | `engagement` | comments/reshares; the depth post |
| `linkedin_post_synthesis` | `engagement` | comments/saves; the documentarian format |
| `linkedin_dm_speaker` / `linkedin_dm_host` (connection notes) | `connection` | accept the connection request |
| `prepared_questions` | `internal` | — (not published) |
| `research_brief` / `post_event_brief` | `internal` | — (notion_only data store) |

- Use `hybrid` only when a post genuinely targets both reach + engagement — name both in Target.
- Goal = the *assigned intent*; the outcome (US-5) is graded against it. **Don't leave Goal empty on a publishable draft.**
- Owned-asset distribution (a site/landing page linked from a post) → tag the post's Goal by its intent; the owned-asset analytics (US-5/US-6) measure the click-through funnel.

## How it's set
1. The content skill picks the Goal (override the default when Alex states an intent via `steering-interview`).
2. `notion-writer` sets `Goal` + `Target` on Content Draft creation; if no goal was passed, it applies the default-by-Content-Type above.
