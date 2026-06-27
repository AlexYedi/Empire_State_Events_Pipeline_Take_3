# Output destinations — Notion / HubSpot / Apollo schema

Canonical schema reference for the Event Research pipeline's write destinations. Extracted from
CLAUDE.md 2026-06-02 to keep always-loaded context lean — content is unchanged. Database IDs live
in CLAUDE.md ("Notion Database IDs"). Live schema in Notion is the ultimate source of truth; verify
with `notion-fetch` on the data_source URL before any batch create (see
`notion-write-gotchas.md` rule e).

## Notion (Content + Research Hub) — 6 interconnected databases (verified via MCP, 2026-04-09)

- **Events** (9 props): Event Name (title), Event Date (date), Location (text), Event Description (text),
  Event Status (select: intake/researched/content_drafted/attended/post_complete),
  Google Calendar Event ID (text — added 2026-05-21 for `/post-event-content` Granola join key),
  relations to People/Companies/Topics/Content Drafts
  Note: Event Description stores the raw pasted invite text. No Calendar Source property —
  the pipeline generates value for events Alex attends AND events he doesn't (content + outreach
  aren't gated by physical attendance).
  Google Calendar Event ID is the raw `event.id` from the GCal MCP response (NOT iCalUID).
  Equals Granola's `calendar_event.calendar_event_id` field — deterministic join for transcript pulls.
  Populated automatically by `/check-new-events` → `/event-deep-research` → `notion-writer`.
  Empty for events created before 2026-05-21 — `/post-event-content` falls back to title+date match
  when the property is empty (dual-path resolution).
- **People** (11 props): Name (title), Current Title (text), Email (email), Phone Number (phone),
  LinkedIn URL (url), Known POV / Bio (text), Notes (text), Role Context (multi-select:
  speaker/host/organizer/attendee/contact), Last Researched (date),
  relations to Events/Company/Content Drafts
- **Companies** (9 props): Company Name (title), Description (text), Website (url), Industry / Space
  (multi-select: AI/ML, Enterprise Software, Developer Tools, VC/Investment, Data Infrastructure),
  Funding Stage (select: Seed, Series A, Series B, Series C, Series D, Series E, Series F, Series G,
  Series H, Series I, Public — NO "Pre-IPO" option; use latest Series letter for late-stage private cos),
  Recent Funding ($) (number), Recent Developments (text), Last Researched (date),
  relations to Events/People
- **Topics** (9 props): Topic (title), Current Events (text), Opportunities (text), Challenges (text),
  Use Cases & Practical Applications (text), Top Questions (text), Last Updated (date),
  relations to Events/People/Content Drafts (renamed from `Linkedin Post Drafts` 2026-05-20 via YED-38
  for cross-DB property-name consistency)
- **Content Drafts** (13 props): Title (title), Content Type (select: research_brief/linkedin_dm_speaker/
  linkedin_dm_host/linkedin_post_pre/linkedin_post_post/prepared_questions/linkedin_post_synthesis/
  post_event_brief), Event Phase (select: pre_event/during_event/post_event), Content Status (select:
  needs_review/approved/scheduled/published/archived), Platform (select: linkedin/slack/notion_only),
  Goal (select: reach/engagement/connection/meeting/hybrid/internal — added 2026-06-26, YED-90),
  Target (text — the concrete target for the Goal),
  Outcome (select: hit/partial/miss/pending/na — added 2026-06-26, YED-91), Outcome Value (text),
  Outcome Date (date), Published URL (url),
  relations to Event/People/Topics/Project Ideas
  Note: Goal + Target are the **assigned-goal** (set at creation); Outcome/Outcome Value/Outcome Date are the
  **realized outcome** (set post-publish by `/tag-outcome`). Together = the acted-on-value north-star.
  See `.claude/skills/content-patterns/goal-tagging.md` + `.claude/skills/tag-outcome/SKILL.md`.
  Note: linkedin_post_synthesis (added 2026-04-19) is used by the pattern-synthesis skill for
  two-thesis posts that relate to 2+ Events. Multi-Event relations are the tell for this type.
  Note: post_event_brief (added 2026-05-28, color: brown) is the post-event mirror of research_brief —
  produced by `/post-event-content` as the FIRST-CLASS artifact before content-correspondent drafts.
  Comprehensive Notion page = data store + short-term memory of the event (Quick Take, the Thesis,
  Pre→Post Gap, ranked Insights, Gotchas & Practitioner Playbook, Tools Mentioned, conditioned Quote
  Bank with confidence tags, Stat Bank with caveats, Slides Catalog, People & Outreach State, Content
  Assets Produced, Documentarian Angles, Conditioning Notes, Verification Flags, Open Loops). All
  downstream post-event content (Tier 1 comment, Tier 2 posts, outreach DMs) references it as their
  canonical source. Event Phase = post_event, Platform = notion_only (internal data store, not
  published). First synthesized 2026-05-28 from "Agents and MCP for Postgres" (NYC Postgres @ Google).
  Views (added 2026-04-18): 🎯 Active Kanban (Board, grouped by Content Status, filter:
  Status ≠ archived) — daily workspace. 🗄 Archive (Table, filter: Status = archived) —
  terminal state, preserves relation graph for future knowledge base synthesis.
  Status flow: needs_review → approved → scheduled → published. archived is reachable from
  any state and is terminal. Archived content stays in the same DB (relations intact) —
  deliberately not a separate archive table, to keep the graph whole for Phase 3-6 knowledge base mining.
- **Project Ideas** (17 props): Project Name (title), Status (select: needs_review/active/shipped/
  archived/deleted), Proposal Type (select: feasible/stretch), Complexity Band (select:
  prototype/small_tool/MVP/full_project), Stack Coverage % (number), Relevance (number 1-10),
  Creativity & Uniqueness (number 1-10), Tool Coverage (number 1-10), Conversation Starter
  (number 1-10), Demonstrability (number 1-10), Content Moments (number 1-10),
  Composite Score (number), Architecture Summary (text), Created (created_time),
  Last Updated (last_edited_time), relations to Events/Topics/Content Drafts
  Active projects tracked via Status select. No hard cap — Alex manages bandwidth manually (cap removed 2026-04-20).

## HubSpot (CRM — Contacts & Companies)

- Standard contact fields: firstname, lastname, email, phone, company, jobtitle
- Company records with standard fields
- Notes attached to contacts with just the event title as body text (primary event-tracking mechanism)
- Event association via Notes: each Note body = event name, searchable for "all contacts from Event X"
- Do NOT set industry on company records — generic categories are unhelpful
- Static Lists NOT available via MCP (OBJECT_LIST write = NOT_AVAILABLE) — Notes approach is the MVP workaround
- Fresh account (created April 5, 2026), full read/write on Contacts, Companies, Notes, Deals
- HubSpot owner ID: 90413044

## Apollo (Not integrated — separate evaluation)

- Not part of the event research pipeline. Alex evaluates Apollo independently via web UI
  on high-value contacts to determine if paid plan (900 credits) justifies integration.
- API blocked on free plan (`API_INACCESSIBLE` on people endpoints). If upgraded, integration
  becomes a separate decision.
