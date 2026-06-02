# Notion MCP write gotchas

Non-obvious property-format and markdown-flavor rules for `notion-create-pages` and
`notion-update-page`. Each was learned live and the rejected syntax was observed to land
as escaped literal text. Follow them mechanically; the API error messages are the source
of truth if anything drifts.

Primary consumers: the `notion-writer` agent and the pipeline command files. Extracted from
CLAUDE.md 2026-06-02 to keep always-loaded context lean — content is unchanged.

## create-pages property-format rules (2026-04-18 — learned live on FDE event writes)

a. **Multi-select properties take a JSON-array-STRING, not a comma-separated string and not a native array.**
   - Correct: `"Industry / Space": "[\"AI/ML\",\"Enterprise Software\"]"`
   - Rejected: `"Industry / Space": "AI/ML,Enterprise Software"`
   - Rejected: `"Industry / Space": ["AI/ML","Enterprise Software"]`  (native array)
   - Same format for People.Role Context.
b. **Select properties must exactly match a defined DB option.** When validation fails, the API error text
   lists the valid options — trust the error, not the doc/CLAUDE.md. The authoritative schema lives in Notion.
c. **Relations take a JSON-array-string of full page URLs (not bare page IDs).** Use the `url` field returned by
   notion-create-pages verbatim. Example: `"Company": "[\"https://www.notion.so/347d3699...\"]"`.
d. **Date properties must use expanded format.** `"date:<Prop>:start"` + `"date:<Prop>:is_datetime"` (0 or 1).
   For datetimes with end times, add `"date:<Prop>:end"` alongside.
e. **Before any batch create against an unfamiliar DB, verify live schema with notion-fetch on the data_source URL.**
   Property names, option sets, and types can drift between docs and the live DB.
f. **Write order for bidirectional relations:** Companies + Topics (no deps, parallel-safe) → People (needs Company URLs)
   → Event (needs People + Companies + Topics URLs) → Content Draft (needs Event URL). Skipping this order silently
   produces empty relation fields.

## update-page markdown-flavor rules (2026-04-26 — learned during eval-harness cycle 1 delivery)

These apply to `notion-update-page` and to `create-pages` body content. Each rejected syntax was tested live
and observed to land as escaped literal text.

g. **Toggle/collapsible sections use `<details><summary>...</summary>...</details>` HTML — and ONLY this form.**
   Notion-flavored markdown's `+++ title ... +++` syntax does NOT work; lands as literal `+++` text. The `<details>`
   tag is the only allowlisted HTML form for toggles in this MCP. Inner content is auto-tab-indented in fetch output
   to indicate nesting — that's the visible signal it parsed as a real toggle block. Use this for preserving
   deprecated/superseded prior content on the same page (avoids sub-page sprawl).
h. **There is NO markdown TOC syntax that works via the Notion MCP.** Tested and rejected: `[[toc]]`, `[TOC]`,
   `+++`, `<toc/>`, `<table_of_contents/>` — all land as escaped literal text. The only path to a real auto-updating
   TOC block is the `/toc` slash command in the Notion UI (one-time per page; native block then auto-updates as
   headings change). Workaround for write-time: insert a static "Page index" callout at top (see convention `i`).
i. **Page-index callout convention** (orchestrator deliveries + any multi-section page worth scanning at a glance):
   blockquote with 📑 emoji, bold "Page index", bullet list of H1 sections each with a one-line description,
   ending with the italic tip *"Place cursor below this callout and type `/toc` to add Notion's interactive
   auto-updating table of contents — one-time per page."* Static fallback that gives glanceable structure; the
   `/toc` step is opt-in and lives in the UI.
j. **`<` in body text is auto-escaped to `\<`** in stored markdown but renders correctly in the Notion UI
   (`\<5min` → `<5min`). Cosmetic only — don't try to "fix" it by removing the escape.
k. **Markdown `|`-tables auto-convert to native `<table header-row="true">` blocks** on write. Rendered as
   real Notion tables (sortable, filterable, resizable columns) — preferred over leaving them as raw markdown.
l. **`update_content` `old_str` must match the STORED markdown, not the markdown you authored (2026-05-27).**
   Notion normalizes emphasis on write: `_italics_` is stored as `*italics*` (single asterisks). An `old_str`
   written with underscores fails with `"No matches found"` even though the rendered text looks identical.
   Fetch the page first and copy the exact stored snippet, or author the match with `*`. Em-dashes and other
   characters are preserved as-is — emphasis markers are the trap. (Learned wiring Gamma carousel URLs into
   post drafts: the `**Carousel (Gamma):** _placeholder_` line matched only after switching `_..._` → `*...*`.)

m. **`notion-update-page` `insert_content`/`update_content` mangles `\n` escapes into a literal "n" (2026-06-01).**
   Author multi-line update payloads with REAL newlines, not `\n` escape sequences. `create-pages` is unaffected —
   it handles `\n` correctly. (Tracked in user memory `project_notion_updatepage_newline_gotcha.md`.)
