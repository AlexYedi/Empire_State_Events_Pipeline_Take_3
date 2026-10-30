# Spec: distribution channels

**Status:** v1, approved 2026-10-30 (rules audit) · **Owner:** Alex · **Referenced by:** gtm-os `CLAUDE.md` (Distribution row), pre-event and post-event content runs.

## 1. Why this exists

Distribution was locked to "LinkedIn only" in May. Since then X and Hub long reads came into scope (2026-10-15), and the north star now has two horizons: an offer by 2027-01-01 (the sprint) and standing goals of upskilling, a thought-leadership brand, and AI community engagement. This spec says which channels carry the pipeline's output, in what form, and in what order, so any event run can pull it in.

## 2. Principles

1. **One source, many cuts.** Every channel cut is derived from the same approved Notion draft and event brief (the COPE pattern: create once, publish everywhere). No channel gets net-new claims that skipped review.
2. **Owned beats rented.** LinkedIn and X can change reach overnight; the Hub and an email list can't. Every rented-channel post points back to an owned asset when it has one.
3. **Human approval on every channel.** Nothing publishes without Alex. Scheduled posts are frozen. `output-evaluator` source-checks every channel cut, not only the LinkedIn version; speaker hedges stay hedged.
4. **New format = one pilot, then pause.** The newsletter, X threads and video are unapproved formats: each ships one pilot draft to Notion `needs_review` and waits for Alex's verdict before it becomes a default.
5. **No scraping.** We publish to these channels; we never harvest from them.

## 3. Channel map

| Tier | Channel | Role | Format | Source artifact | Status |
|---|---|---|---|---|---|
| Core | **LinkedIn** | Primary: hiring managers, enterprise network | 3 variants per post, carousel PDF, one Learn-More comment | Content Draft | Live |
| Core | **X** | Where AI builders and lab people talk first | Thread of 4–7 posts cut from the chosen LinkedIn variant; post 1 stands alone; the link goes last | Chosen LinkedIn variant | Pilot |
| Core | **Hub long read** | Owned canonical version; Learn-More link target; interview leave-behind | Web-native long form, amended post-event | Brief + post-event brief | Planned |
| Next | **Newsletter** | The only owned list. Working title "NYC AI Field Report", weekly | Upcoming Week roundup + one deeper item + one build note | Roundup + briefs | Pilot (platform decided 2026-10-30: the Hub, no Substack — §6) |
| Next | **GitHub** | A credential for AI-company hiring | Pinned repos (B1–B5, hackathon builds), README written as a story: problem → build → result → what I'd do next | Build repo | Live (pins pending) |
| Next | **Communities**: AI Tinkerers NYC, Latent Space Discord, MLOps Community; Pavilion or RevGenius (GTM) | Recognition before reach; the AI-community standing goal | A value-first recap in the community's own format, never a link drop; follow each space's self-promo rules | Post-event brief | To join |
| Test | **Short video** (LinkedIn native, YouTube Shorts) | Face and voice (content v2) | One 60-second recap | Post-event brief + footage | One pilot |
| Test | **Borrowed audiences**: podcast guest spots, recap partnerships (The Shortlist, YED-244) | High-trust reach | Pitch + recap | Track record | Opportunistic |
| Skip | Threads, Bluesky, Medium, self-promo on Reddit or HN | Low reach with this audience, or hostile to promotion | n/a | n/a | Skip |

## 4. Per-event playbook

Pull the rows that apply to the event type.

**Pre-event (any event)**
1. LinkedIn pre-event post (existing `pre-event-content`).
2. X: 1 single post + 1 thread (4–7 posts), re-cut from the post's thesis (aligned to E-05, 2026-10-30 — was "a 1–3 post cut"; rules in `.claude/references/x-content.md`).
3. Newsletter: the event's line in that week's Upcoming Week roundup.

**Post-event (talks, panels)**
1. LinkedIn post (existing `/post-event-content`), then the Hub long read amended with the room.
2. X thread from the chosen variant, with the Hub link last.
3. Newsletter: the deeper item, if this event is the week's strongest.
4. Community recap in one relevant space, if it gives the space something.

**Hackathon / build events (add to post-event)**
1. **GitHub first:** public repo with the story README, a demo GIF or link, and synthetic data only (build-in-public rules).
2. LinkedIn post anchored on the build: problem statement quoted verbatim, what we built, what broke, what I'd change.
3. X thread with the demo clip in post 1.
4. Community: share the build where builders gather (AI Tinkerers, the sponsor's Discord).
5. Video pilot candidate: a 60-second "what we built in N hours."

## 5. Applying it today: NYC Frontier Hackathon (Obvious), 2026-10-30

Event folder: `Event Content/10 30 26 Frontier Hackathon October/`. The pre-event carousel already exists.

| Channel | Ship | Note |
|---|---|---|
| GitHub | Build repo + story README | Before any post links to it |
| LinkedIn | Post-event build post, 3 variants | Standard flow |
| X | **Pilot thread** (first X thread under this spec) | Pilot rule: one draft, then Alex's verdict |
| Community | One build share | Pick the space the sponsors and judges are in |
| Video | Optional pilot | Only if there's demo footage |
| Newsletter | Not yet | Platform decided: the Hub is the newsletter home, no Substack (§6) |

## 6. Channel decision and open decisions (Alex)

**Decided — 2026-10-30 (Alex).** The channel set is:

1. **LinkedIn**
2. **X**
3. **Hub long reads** (`empire-state-hub`), with rich content — visualizations, images, and video embeds.

**No Substack.** The Hub itself is the newsletter home, per this spec's own recommendation (owned beats rented; every channel points to one home).

This decision unblocks **E-05** (X content contract) and **E-06** (X surfaces on the hub).

**Still open:**

1. **Communities:** which two to join first. Recommendation: AI Tinkerers NYC (local, builder-heavy) and Latent Space Discord (lab and engineer audience).
2. **Video pilot:** which event; today's hackathon is the best candidate if there's footage.
3. **X account:** confirm the handle and whether it's on Premium (affects post length).

## 7. Measures (null-baseline rule)

Report no channel metric without its do-nothing baseline. For new channels the baseline is zero, so the first two weeks only establish one; no targets until then. The measure that matters for the sprint is **inbound conversations attributable to a channel** (DMs, intros, recruiter contacts), logged against the Roles funnel, not impressions.

## 8. Out of scope

Paid promotion, automated cross-posting without review, and any scraping. Posting cadence comes from the roadmap, not this spec.
