# S-02 · Feed layer: code half (Shared)

**Linear:** YED-251 · **Repo:** Empire_State_Events_Pipeline_Take_3

## Product
Company and topic news reach research automatically: RSS, changelogs, Substack and YouTube feeds discovered from each company's website, plus Google News queries. Decisions that are still open in YED-251 (an exception to "no unattended producers", and what it retires) are Alex's. **This spec builds only the parts that don't depend on those decisions.**

## Technical (factory)
- `.claude/scripts/feeds.py` with three pure, tested stages:
  - `discover(website_html) -> [feed_url]` (link rel=alternate, common paths);
  - `parse(feed_xml) -> [item]` (RSS 2.0, Atom, YouTube);
  - `dedupe(items, seen_keys) -> [item]` (stable key = sha256 of the canonical URL).
- `render_digest(items, companies) -> markdown` for the Friday digest, grouped by company and newest first, with source links. No LLM calls.
- `--selftest` with inline XML/HTML fixtures. Network fetching sits behind `fetch(url, timeout=8)` and MUST NOT run in the selftest.

## Must not
- Create tables or migrations. The `feed_sources` / `feed_items` DDL waits for ADR-12 and Alex.
- Write anywhere.
- Scrape LinkedIn or X (public feeds and official endpoints only).

**Done when:** the selftest passes, and the PR body lists what the session-side wiring needs (DDL, writer, schedule).
