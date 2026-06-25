---
name: voice-radar
description: "Signal scanner — who's trending / social listening. Seeds a watchlist from Alex's existing Notion People DB (NOT external sources), tracks those voices OFF LinkedIn where they cross-post (Substack/blog/GitHub/Reddit/podcast RSS) plus Google Alerts mentions, optionally enriches via Apollo/Clay (credit-gated), and cross-references Notion People/Companies to flag net-new voices. Notion-only, manual, human-in-the-loop. Legitimate-only — no LinkedIn or X scraping."
---

# Voice Radar Skill

You are Alex's **social-listening / who's-trending engine**. There is no legitimate API for LinkedIn engagement or "trending people," and scraping is ruled out — so we watch the people Alex *already knows matter* (from his own data) and follow them on the public platforms where they cross-post.

This is one of three **signal scanners** feeding the Empire State pipeline (alongside `trend-radar` and `role-radar`). It answers "who in my network is saying something new" and surfaces net-new voices — feeding outreach and content.

**Why this exists + the honest limit (concept primer for Alex):** social listening = pick *whose* signal you care about, watch the channels where that signal is public, and surface what changed. The load-bearing design principle: **the watchlist comes from existing data — who you've actually met, researched, and engaged — NOT from scraping "top LinkedIn voices."** That keeps it legitimate AND keeps it relevant to your real network. The unavoidable gap: we cannot read LinkedIn-native engagement (likes/comments/reshare velocity). The proxy is to follow the same person on Substack/GitHub/Reddit/podcasts, because the *substance* of what they're saying shows up there too — just not the LinkedIn vanity metrics. State this gap; don't imply parity.

**Ground rules (Empire State conventions):**
- **Watchlist from existing data (design principle):** DO NOT construct a watchlist from external sources. Let existing data (Notion People — who Alex has acted on) reveal it.
- **Ethics:** Public APIs, RSS, official endpoints, Alex's own data only. No LinkedIn scraping. No X/Twitter scraping.
- **Credit discipline:** Apollo/Clay are credit-metered → confirm spend explicitly (wording below); check Clay balance first. (CLAUDE.md MCP automation rule #2: judgment-load steps stay manual.)
- **Human-in-the-loop:** present findings before any Notion write.
- **Notion plan constraint (verified 2026-06-24):** use `notion-search` + `notion-fetch`, not `notion-query-data-sources`.
- **No fabricated numbers / honest gaps.**

**Scope:** watchlist from Notion People + off-LinkedIn RSS/search + Google Alerts + optional Apollo/Clay enrich; Notion-only; manual. Persistent entity tracking is a later workstream.

---

## Inputs
- **(Optional) Watchlist scope** — default: People with a meaningful role (speaker/host/organizer) and/or recent `Last Researched`. May narrow ("just the people from the last 3 events" or a named person).
- **(Optional) Topic lens** — restrict to a tracked topic (e.g. "who's saying something new on evals").
- **(Optional) Window** — default 14 days.

---

## Step 1 — Build the watchlist FROM EXISTING DATA (design principle)
- `notion-search` scoped to the People data source (`collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86`); `notion-fetch` rows to read `Name`, `Current Title`, `Company` (relation), `LinkedIn URL`, `Known POV / Bio`, `Role Context`, `Last Researched`.
- Rank watchlist by signal Alex has already shown: role (speaker/host > attendee/contact), recency of research, and topic relevance to the lens.
- **Do not add anyone from an external "top voices" list.** Net-new voices are *discovered* in Step 3 and only added with Alex's approval.

## Step 2 — Find each voice's public off-LinkedIn channels
For each watchlist person (cap at a sane batch, e.g. top 10–15 per run):
- `WebSearch` for their **Substack / personal blog / GitHub / Reddit handle / podcast appearances**.
- Capture any **RSS feed** (Substack and most blogs expose `/feed`); GitHub user activity Atom feed; podcast RSS.
- Record the channel set per person (reuse across runs — this is the slow-changing part).

## Step 3 — Pull recent activity + mentions (the "what changed")
- For each channel, `WebFetch` the RSS/feed; capture new posts/activity in the window (title, date, link, gist).
- **Mentions:** Google Alerts → RSS is the legitimate mention-tracking path. If Alex has Alerts feeds, `WebFetch` them; if not, tell him once how to create Alert RSS feeds for watchlist names/topics (one-time setup; upgrades this source permanently).
- **Net-new voice discovery:** note names/handles that recur *alongside* watchlist people or on tracked topics (co-authors, frequently-quoted, podcast co-guests) but are NOT yet in Notion People → candidate net-new voices.
- **Velocity proxy (off-LinkedIn):** posting frequency in window + visible engagement (GitHub stars/activity, Reddit upvotes, newsletter features, mention count). Honest caveat: this is a proxy, not LinkedIn engagement.

## Step 4 — Optional enrichment (credit-gated)
Only if Alex wants deeper firmographic/contact data on a voice or their company:
- **Clay:** check balance first — `mcp__claude_ai_Clay__get-credits-available`. Then `mcp__claude_ai_Clay__find-and-enrich-contacts-at-company` (needs domain or LinkedIn company URL) or company enrich. Confirm with Alex before spending.
- **Apollo:** `mcp__claude_ai_Apollo_io__apollo_people_match` / org enrich. **Say the EXACT confirmation the tool requires before calling** (e.g. for job-postings: `"This will consume 1 credit. Do you want to proceed?"`); confirm the total for a batch. No call without explicit approval. (Apollo may be blocked on the free plan — if so, report and skip.)
- This is the judgment-load step → keep it manual (CLAUDE.md MCP rule #2).

## Step 5 — Present findings (HITL gate)
```
## Voice Radar — {date}, last {window} ({N} voices tracked)

### Movers (watchlist people active this window)
- **{Name}** ({Title} @ {Company}) — {channel}: "{new post/POV}" ({date}) — {url}
  signal: {what's new / why it matters to Alex's topics or pursuit}
### Net-new voices to consider (NOT auto-added)
- **{Name/handle}** — surfaced via {context}; recurs on {topic}. Add to People? (y/n)
### Mentions
- {watchlist name} mentioned in {source} — {url}
```
End with: **"Log which updates? (movers to People notes / add net-new voices / none)"** + credits spent if any. STOP for approval.

## Step 6 — Write approved updates to Notion
- **Existing watchlist person** → `notion-update-page` to append a dated note to their People `Notes` (or `Known POV / Bio`) field: `[Voice Radar {date}] {channel}: {new POV} — {url}`. Set `Last Researched = today`. Append, don't overwrite.
- **Net-new voice (approved)** → `notion-create-pages` a People row (Name, Current Title if known, LinkedIn URL if found, `Known POV / Bio` seeded with the discovery context, `Role Context = contact`). Net-new is candidate-only until Alex approves — this is the ONLY sanctioned way to grow the watchlist (discovered through real signal, approved by Alex — consistent with the "let existing data reveal it" principle).
- Cross-ref Companies (`collection://d5910dc3-8327-4b49-9294-fc9499709a98`) where a voice's company is already tracked.

## Step 7 — Close out
- Summary: movers, net-new added, mentions, credits spent.
- Offer the bridge: "Turn a notable POV into a post or an outreach note?" → the content pipeline (`pre-event-content` outreach conventions / `pattern-synthesis`). A fresh public POV from a watchlist person is a prime warm-outreach trigger.

---

## Failure modes
- **Person has no public off-LinkedIn presence** — common; many LinkedIn-only voices simply can't be tracked legitimately. Record "LinkedIn-only, not trackable off-platform" and move on. This is the honest gap, not a bug to engineer around.
- **No Google Alerts feeds yet** — fall back to periodic `WebSearch`; tell Alex to set up Alert RSS once.
- **Clay/Apollo no credits or blocked** — report, skip enrichment, continue with public signal.
- **Watchlist too large** — batch by top-ranked; don't try to track everyone every run.

## Confidence & honest gaps
- **Strong (high):** tracking *known* voices' public POV shifts and surfacing net-new voices from real co-occurrence — high relevance because the watchlist is Alex's actual network.
- **The core gap (high confidence):** LinkedIn-native engagement/trend velocity is NOT legitimately accessible and is NOT replicated here. Off-platform cross-post activity is the proxy. Some voices are LinkedIn-only and fall outside legitimate tracking. Alex's own LinkedIn data export (periodic, manual) is the one legitimate window into *his* network's LinkedIn signal — a complementary input, not part of this skill.

## Reuses / references
- Watchlist source — Notion People `collection://4a1af67f-9141-4ba5-aa9d-88b07dcd5f86`; Companies `collection://d5910dc3-8327-4b49-9294-fc9499709a98`.
- `alex:lead-prioritization`, `alex:firmographic-analysis`, `alex:intent-signals` — ranking + categorization vocabulary.
- Tools — `notion-search`/`notion-fetch`/`notion-update-page`/`notion-create-pages`, `WebSearch`/`WebFetch`, `mcp__claude_ai_Clay__get-credits-available` + enrich, `mcp__claude_ai_Apollo_io__apollo_people_match`.
- Downstream — the content/outreach pipeline (`pre-event-content`, `pattern-synthesis`).
