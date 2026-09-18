# The Knowledge Substrate — program architecture (2026-09-18, Fable)

**Status:** architecture for decision, not built. Supersedes the scope in `yed-160-scope-2026-09-17.md`
(that scope was correct and is absorbed as Phase 1's first build; it was too small because it optimized
one producer, not the thing Alex asked for). PRD to be compressed from this document per
`prd-template.md`; the ADR this implies is **ADR-10** (proposed below). No production code, no graph
writes, no Linear/Notion records were created while producing this.

**Alex's goal, verbatim:** *"Take all of the information, events, companies, people, topics,
information, learnings, research etc. and turn it all into a cohesive effective source for elevating
future research and information generation for maximizing the value of future event attendance,
content creation, job hunting, writing, new project and software development."*

**Settled constraints:** use-case-neutral (five first-class consumers) · 2–4 week program, Phase 1 this
weekend · full schema latitude incl. pgvector · DDL is one-off SQL Alex runs · REST-only writes through
`spine_client.py` · branch-first, one worktree per workstream.

---

## 0. The one-paragraph design

Today's graph is **four node tables and one hyperedge** (`company`/`person`/`topic` + `event` +
`event_entity`), plus a bolted-on document lane (`documents`/`doc_chunks`, already pgvector-embedded) and
an empty claims staging table (`doc_claims`). The substrate adds **two things and one discipline**.
(1) A **first-class claim layer** — one row per atomic assertion, whatever produced it (a talk, a book,
an email, a transcript, a build retro), carrying *who said it · on what occasion · from which document ·
at what provenance tier · with what confidence*, embedded for semantic search, and linked to entities by
a real join table. (2) A **document layer generalized to everything the system produces** (briefs, Deep
Reads, post-event briefs, transcripts, posts, carousels, dossiers, project ideas, build retros), each
with a stable identity, version chain, embedded chunks, and an outcome row. The discipline is
**one retrieval interface** (`retrieve.py` → a Context Pack) that every consumer calls, replacing the
hand-rolled `curl` at `/event-deep-research` Step 1.7a, and **one producer library** (`substrate.py`)
that every writer calls, so backfill *is* the producers running over history. Identity (canonical
naming, aliases, a persisted merge-map) ships in the first migration because the collision probe says
it can, and because a substrate backfilled before identity exists mints the "four Elastics."

**Mechanism, in one sentence:** every future run starts by asking the substrate *"what do we already
know about these entities and this question, ranked by relatedness, recency, provenance and what has
actually been useful before"* — and every run ends by writing back what it learned and, later, how it
performed. That closed loop is what "compounding" means concretely.

---

## 1. Target architecture

### 1.1 Vocabulary (define once, use everywhere)

| Term | Meaning here | Plain-language analogy |
|---|---|---|
| **Node / entity** | A durable thing that exists independent of any occasion: `company`, `person`, `topic`. | A card in a Rolodex. |
| **Event (hyperedge)** | Something that happened at a point in time and linked N entities: a meetup, a funding round, a product launch, a job posting, a published post. `event_entity` is the join (one row per participant, with a `role`). *Hyperedge* = an edge that connects more than two nodes at once. | A meeting-minutes header: date + who was in the room. |
| **Document** | An artifact with a body: a book, a transcript, a brief, a post, a dossier, a build retro. Has a stable id, a content hash, a version chain, and embedded **chunks**. | The minutes themselves, page by page. |
| **Chunk** | A ~400-token slice of a document with an embedding (a 384-number fingerprint that lets us find "passages that mean roughly this"). | A highlighted paragraph you can find later by meaning, not keyword. |
| **Claim** | One atomic assertion extracted from a document or an occasion — *"pgvector HNSW beats IVFFlat on recall for <1M rows"* — with speaker, occasion, source document, locator, provenance tier, confidence, and an embedding. | An index card with the quote, who said it, where, and how much you trust it. |
| **Provenance tier** | How the claim came to be known: `first_hand` (Alex was in the room / transcript) > `web_verified` > `email_signal` > `notion_prior` > `reference` (a book) > `model_inferred`. | Eyewitness vs. newspaper vs. hearsay. |
| **Outcome** | What happened after an artifact shipped (post reach, connection accepted, interview stage reached, PR merged). | The scoreboard. |
| **Usage** | Which claims a produced artifact actually drew on. | The bibliography of each thing we made. |

### 1.2 What is a node, an edge, a claim, a document — decided

- **Nodes stay exactly three types:** `company`, `person`, `topic`. Roles, funds, tools, frameworks are
  *not* nodes: a VC is a `company` with `company_type`; a tool is a `company` if it has a maker and a
  `topic` if it is a concept. A speaker's title is an attribute. (Unchanged from `market-intel-spine.md`;
  every alternative I considered adds a node type without a consumer that needs it — the D7 rule from
  ADR-8 applies: no type without a query.)
- **Events stay the temporal hyperedge AND the signal model.** Three new `kind` values, each with a
  named consumer: `observed` (an attended event *as an occasion for first-hand claims* — distinct from
  the 59 migrated `attended` rows so the hub stops confusing a dead migration with a live producer);
  `published` (Alex published an artifact on a date, linking the topics/people it names — the content
  lens's "what have I already said," and the anchor for outcomes); `shipped` (a project/build shipped,
  linking topics — project-ideation's "what do I already have"). `reference` (YED-157 B1) stays but is
  **no longer the promotion target for claims** (see 1.4).
- **Claims are first-class and are NOT events.** Yesterday's plan (and YED-157/YED-160 as written)
  promoted each approved claim into its own `event` row. That mints N events per real event, corrupts
  the trust strip's producer semantics, and forces the relevance recompute to treat "a thing someone said"
  as "a thing that happened." In the substrate, a claim points *at* the event that was its occasion
  (`claim.event_id`) and *at* the document it was extracted from (`claim.document_id`); the event row is
  minted once per real occasion. `doc_claims.promoted_event_id` is deprecated (kept, unused).
- **Documents are every artifact with a body**, ours and theirs. The existing `documents` table is
  generalized (source-type vocabulary widened, `blob_key` made nullable because our own artifacts have
  no R2 blob, `event_id` + `external_ref` + `version`/`supersedes_id` + `produced_by` + `visibility`
  added). Notion remains the *review surface* for our artifacts (ADR-6); the substrate holds the
  canonical *body-as-knowledge* (chunks + claims) keyed by the Notion page id. This is exactly the
  "document with stable identity for RAG provenance" argument ADR-6 already made.
- **Entities ↔ documents get their own join** (`document_entity`), because "the dossier about Ramp"
  and "the transcript where Ryan Booz spoke" are relationships that are neither claims nor events.

### 1.3 The layered picture

```
                       ┌──────────────────────────────────────────────────────┐
  CONSUMERS (5)        │  retrieve.py  →  Context Pack (one contract, 5 lens presets)  │
                       └──────────────┬───────────────────────────────────────┘
                                      │ reads (RPC + REST GET)
   ┌──────────────────────────────────┼─────────────────────────────────────────────┐
   │  KNOWLEDGE PLANE  (public schema, oicikjyzmxqfomrrqkvf)                          │
   │                                                                                 │
   │   claim ──claim_entity──▶ company / person / topic ◀──event_entity── event        │
   │     │  \                        ▲      ▲                                  ▲      │
   │     │   └─ speaker_person_id ───┘      │ entity_alias / entity_merge      │      │
   │     ▼                                  │ (identity)                       │      │
   │   documents ──document_entity──────────┘                    claim.event_id┘      │
   │     │  ├─ doc_chunks (embedding 384, tsv)                                        │
   │     │  ├─ artifact_outcome  (goal · target · outcome · value · date)             │
   │     │  └─ claim_usage       (which claims this artifact drew on)                 │
   │     └─ version chain (supersedes_id)                                             │
   │                                                                                 │
   │   topic_intelligence.* (ADR-1/4, unexposed, grants-only)  signal_read.* (anon views) │
   └──────────────────────────────────┬─────────────────────────────────────────────┘
                                      │ writes (ONLY via spine_client.guard)
                       ┌──────────────┴───────────────────────────────────────┐
  PRODUCERS (≈14)      │  substrate.py  (ensure-event · ensure-document · stage-claims ·│
                       │   approve · link · record-outcome · record-usage · embed)      │
                       └──────────────────────────────────────────────────────┘
```

**What stays outside the substrate, on purpose:**
- **Build telemetry, judge run-logs, DoD waivers, correction-recurrence** stay in the rigor layer
  (JSONL shards + PostHog). The measurement-layer tombstone (CLAUDE.md) says Supabase is not the
  observability store, and ADR-8 says the repo's own build-artifact graph is a local derived cache.
  **What DOES enter the substrate from builds is knowledge, not measurement:** a build retro's *claims*
  ("PostgREST cannot run DDL", "generated columns need IMMUTABLE functions", "the Stop hook folds
  `.build_meta`") as `documents(source_type='build_retro')` + claims with `provenance_tier='first_hand'`,
  and a correction-recurrence *class* as a claim of `claim_type='pitfall'`. The line: **a number about
  the system → rigor layer; a lesson about the world or the stack → substrate.** This is the software-
  development consumer's feed, and it is the only place the two tombstones needed reconciling.
- **`me-model.md` and `target-companies.md`** (personal, gitignored). Recommendation: **do not ingest
  the me-model body**; `retrieve.py --lens job` reads it locally at query time as a side-input. Ingest
  only a *flag* — `company.metadata.target = true` for target companies (company-level, not PII). The
  spine is service-key-only today, but ADR-2 commits to anon-safe `signal_read` views and the hub is
  tier-3 public; a private career document does not belong one grant away from a public view.
  **Decision Alex owns** (§9).
- **HubSpot** stays one-way (ADR-9). `person.email`/`phone` never enter; unchanged.

### 1.4 What changes vs today's model, and the ADR implications

| Change | Why | ADR touch |
|---|---|---|
| `doc_claims` → `claim` (generalized: `document_id`, `event_id`, `speaker_person_id`, `provenance_tier`, `embedding`, `tsv`, `utility_score`, `use_count`) + `claim_entity` join | One claim contract for every source; `proposed_entities` jsonb is not queryable; claims need semantic + relational retrieval | **ADR-10 (new).** Supersedes YED-157's "promote claim → `event(kind=reference)`" decision; does not reverse ADR-1..4 (same graph, same account, same REST rule) |
| `documents` generalized to all artifacts; `document_entity`; version chain | The body of every brief/post/transcript is knowledge; ADR-6 already argued documents need stable identity for RAG | ADR-10; consistent with ADR-5/6 (Notion stays review surface) |
| 3 new event kinds: `observed`, `published`, `shipped` | Live first-hand producer distinct from the dead 2b migration; content + ideation lenses need "what I published / shipped" as occasions with outcomes | ADR-10 amends the `event_kind_enum` (ADR-7's "no new kind" was about inbox signals and still holds for them) |
| Identity: `name_norm` generated columns + unique indexes, `entity_alias`, `entity_merge` (persisted, reversible; **people merge is `method='human'` by CHECK**) | YED-47; ADR-4 "merge-map first, never fuzzy-merge people" becomes a constraint rather than prose | ADR-10 mechanizes ADR-4 D3 |
| `artifact_outcome`, `claim_usage` | The feedback half: without them the substrate cannot learn what was useful | ADR-10; extends the value-action registry |
| `topic.embedding`, `company.embedding` (384) | Embedding-assisted match-before-create for topics/companies (surfacing candidates; Claude/Alex still decide) | Roadmap §5 deferred "embedding-based dedup" to Q1 — pulled forward as *assist*, not auto-merge |
| Trust strip reads producers from `claim` + all `event` kinds, not `kind=eq.market` | The hub codified the mask (yesterday's finding) | empire-state-hub change; ADR-2 unaffected (still a read-only client) |
| `spine_client.ALLOW` extended to the new tables; email/phone forbidden everywhere; claim text scanned | ADR-9 chokepoint unchanged in principle, wider in scope | ADR-9 holds; no new ADR |

**Not changed:** the three entity tables' shape; `person.company_id` FK; `event_entity` closed role set
(`subject · tagged_topic · speaker · host · panelist · attendee`); `topic_intelligence` /
`signal_read` (ADR-1/4 grants model) — the recompute (YED-131) will later read `observed` events too;
REST-only writes; Notion as review surface; HubSpot one-way.

---

## 2. Producer inventory (everything the system has produced or will produce)

Legend — **Path:** *direct* = write on completion, no human gate (facts already reviewed upstream);
*staged* = candidates until approved; *derived* = computed from other rows. **Dedup key** = the
idempotency identity `substrate.py` uses so a re-run is a no-op.

| # | Artifact | Emits into substrate | Path | Dedup key | Value/effort | Notes |
|---|---|---|---|---|---|---|
| 1 | **Notion Event row** (all ~85–95; 27 since 08-20) | `event(kind='observed')` + `event_entity` (speaker/host/tagged_topic) + `person`/`company`/`topic` upserts | direct (facts Alex reviewed at research time) | `notion_page_id` → (title, date, kind) fallback | **very high / low** — yesterday's `ensure-event`; the 24 absent events | Phase 1, day 1 |
| 2 | **`post_event_brief`** (5 exist: Shortlist Aug, GTM Leaders Vol.1, Daytona Sept, LeadDev, Postgres Tuning) | `documents(source_type='post_event_brief')` + chunks; **claims** from the numbered learnings sections (Pro-Tips · Best Practices · Pitfalls · Hot Takes · Insights · Stat Bank), `provenance_tier='first_hand'`, `speaker_person_id` from the Speaker Map | **direct-approved when the brief's Notion `Content Status='approved'`; staged otherwise** | `claim_key = sha256(norm(claim_text))` scoped by `document_sha256` | **very high / low-medium** — the richest Alex-only signal | The brief review IS the approval gate — see §8 decision |
| 3 | **`research_brief` Scan head + Deep Read** (~90 events' worth in Notion; 6 legacy `.md` in `research-briefs/`) | `documents(source_type='research_brief' / 'deep_read')` + chunks; claims from Quick Take / Verification Flags / Deep Read endnoted facts, `web_verified` or `notion_prior` per the ADR-5 tier tag already in the text | direct (chunks) · claims staged unless the tier tag is `web-verified` with a URL | Notion page id + body sha256 (version chain on re-research) | high / medium | The Deep Read's endnote citations are already provenance-shaped |
| 4 | **Prior-Context Packs** (`prior_context_pack` Content Drafts) | `documents(source_type='prior_context_pack')` + `claim_usage` rows (which prior claims fed which brief) | direct | Notion page id | medium / low | Makes "what fed this brief" queryable — the retrieval audit |
| 5 | **Transcripts** (12 in `event-transcripts/`, ElevenLabs Scribe JSON with timestamps/speakers; more via `/ingest-recording`) | `documents(source_type='transcript')` + chunks with `locator={t_start,t_end,speaker_id}`; **no claims minted directly** (claims come from the conditioned brief, #2) | direct | file sha256 | high / low | ADR-9: transcripts name people → `person` rows only for Speaker-Map HIGH/MED; audience members never become rows; chunk text is scanned by the guard (no emails/phones) |
| 6 | **Published posts + carousels** (Content Drafts with `Content Status=published`; `Event Content/`, `content-drafts/`) | `event(kind='published')` linking topics/people/event + `documents(source_type='linkedin_post'/'carousel')` + chunks + `artifact_outcome` (Goal/Target now; Outcome via #12) | direct | Notion page id; `Published URL` as `event.url` | **high / low** — the content lens's memory and the theme→prior-post index the memory file asked for | Feeds "what have I already said" + long-tail back-links |
| 7 | **Connection notes / DMs / prepared questions** | `documents` (private, `visibility='private'`), no chunks unless asked | direct | Notion page id | low / low | Mostly for outcome tracking (connection accepted) |
| 8 | **Knowledge Library** (2 ingested; `~/Documents/Knowledge Library/`, R2 `esep-library`) | already `documents`+`doc_chunks`; **claims** via `extract_claims.py` (Gemini) → `claim` staged, `provenance_tier='reference'`, confidence ≤ 0.6 | staged (YED-157 B2 exists) | `documents.sha256` + `claim_key` | high / low (exists) | `/doc-digest` → generalized `/digest` (§3.6) |
| 9 | **Inbox signals** (`inbox_miner`, 13 events) | unchanged `event` + `event_entity`; **add** `claim` rows for the one-line signal text with `provenance_tier='email_signal'` and `document_entity`-less provenance in `metadata` (ADR-7: no per-message table) | unchanged (HITL write gate) | canonical URL | medium / very low | One extra `substrate.py stage-claims` call in `inbox_signal_write.py` |
| 10 | **Trend / role / voice scans** | trend: unchanged `market` events (+ optional claim per approved digest line); **roles: new** `event(kind='role_posted')` + `company` upsert + `topic` tags (YED-149) — the job lens becomes graph-native; voices: `person` enrich + `event(kind='market')` for off-LinkedIn activity | HITL (existing digests) | trend: (title, date, kind) → canonical URL; roles: `{ats_vendor}:{ats_job_id}`; voices: canonical URL | roles **high** / medium; others low | Roles producer is a Phase 3 item; today Notion-only |
| 11 | **Interview dossiers** (`/interview-prep` Step 5 already writes company/topic/person) | add `documents(source_type='dossier')` + chunks + claims (`web_verified`/`notion_prior`) + `event(kind='interview')` when a stage is real | direct | Notion page id | high / low | The job lens's memory across interviews at the same company |
| 12 | **Outcomes** (`/tag-outcome` writes Outcome/Value/Date to Notion) | mirror to `artifact_outcome` for the matching `documents` row; job-search outcomes as `event(kind='application'/'interview')` state in `metadata` | direct (HITL upstream) | `documents.id` | **very high / very low** — the whole feedback loop hangs on it | One `substrate.py record-outcome` call added to the tag-outcome skill |
| 13 | **Project ideas** (Notion Project Ideas; Status=shipped) | `documents(source_type='project_idea')` + `document_entity` (topics) + `event(kind='shipped')` when Status flips to shipped | direct | Notion page id | medium / low | Ideation's gap analysis needs "what exists" |
| 14 | **Build retros / notes corpus** (`.claude/notes/*.md`, ADR amendments, `deep-read-batch-wiring-fix.md`, `measurement-layer-learnings.md`) | `documents(source_type='build_retro' or 'note')` + chunks + claims (`claim_type='pitfall'/'practice'`, `first_hand`) | staged (an LLM extracts; Alex approves in `/digest`) | file sha256 (version chain on edit) | medium / low | The software-development consumer's feed. Correction-recurrence *classes* enter as pitfall claims; the counts stay in the rigor layer |
| 15 | **Judge runs, telemetry, DoD waivers** | **nothing** (measurement tombstone + ADR-8) | — | — | — | Read by `/rigor-review`, not by the substrate |
| 16 | **Glossaries** (YED-167 Postgres glossary; future `glossary.md`) | `documents(source_type='glossary')` + one `claim(claim_type='definition')` per term, linked to its topic | direct | file sha256 + term key | medium / low | Definitions are the novice on-ramp every consumer wants |

**Ranking by value-per-effort (what to build first):** #1 → #2 → #12 → #6 → #5 → #3 → #11 → #14 → #8 (exists) → #9 → #13 → #16 → #10 roles → #4 → #7 → #10 voices/trend claims.

**The pattern every producer follows (no exceptions):** parent thread does the MCP/file reads → builds a
**manifest JSON** → calls `substrate.py <verb> --manifest m.json` → the script resolves identities
(read-before-write), dedups on the key above, writes through `spine_client.guard`, prints a
matched/created/skipped table, and exits non-zero on any refusal. This is `inbox_signal_write.py`'s shape,
generalized. A command's write-back step is therefore *one line*, and backfill is *the same line in a loop*.

---

## 3. Retrieval / consumption contracts (half the design)

### 3.1 The one interface

`python3 .claude/scripts/retrieve.py --lens <event|content|job|ideation|dev> --seed seed.json
[--budget-tokens 6000] [--out pack.md] [--json]`

**Input (`seed.json`):** `{entities: [{type,name|id}], text: "<verbatim source / question / JD>",
focus: "<Alex's stated focus>", window_days: N, exclude_document_ids: [...]}`.

**What it does (mechanism):**
1. **Resolve** seed entities through `entity_alias` → canonical ids (read-only; unresolved names are
   reported, never guessed).
2. **Relational pull (1-hop neighborhood)** — RPC `entity_neighborhood(ids)`: every `event` any seed
   entity participated in (all kinds), the co-participants of those events, and every `claim` /
   `document` linked to the seed entities via `claim_entity` / `document_entity` / `claim.event_id`.
3. **Semantic pull** — embed `text` locally (bge-small, same model as ingest — the pinned invariant),
   then RPC `match_claims_hybrid` (dense ∪ keyword, reciprocal-rank fusion, `status='approved'` only)
   and `match_doc_chunks_hybrid` over documents. *Reciprocal-rank fusion* = combine two ranked lists by
   summing `1/(k+rank)` so a passage strong in either list surfaces.
4. **Score** each candidate once:
   `score = w_sem·semantic + w_rel·relational + w_rec·recency + w_prov·provenance + w_conf·confidence + w_use·utility`
   where `relational` ∈ {1.0 direct entity match, 0.5 one hop, 0 none}; `recency = 0.5^(age/half_life)`
   (half-life 90d for claims, 14d for `market` signals — matching `recompute_relevance.py`);
   `provenance` = {first_hand 1.0, web_verified 0.9, email_signal 0.7, notion_prior 0.6, reference 0.5,
   model_inferred 0.3}; `utility` = normalized `utility_score` (§5). **Lens presets set the weights**
   (table below). Apply a diversity rule: ≤3 claims per source document (a cheap MMR — *maximal marginal
   relevance* — so one long brief cannot crowd out five short signals).
5. **Budget by tokens, not by N.** The current N=8 hard cap was a cost guard on *Notion body fetches*;
   the substrate serves pre-chunked, pre-extracted text, so the right guard is a token budget (default
   6k, `--budget-tokens`). Fill the budget in score order; list the cut-off tail by title.
6. **Emit the Context Pack** — the existing Prior-Context Pack schema (Continuity Ledger · Company /
   People / Topic Cards · Graph Signals · Audit) **plus** two new sections: **Library** (book/doc claims
   with locators — YED-157 B4's line, generalized) and **What you've already said** (own `published`
   documents on these topics, for the content lens's non-repetition and the long-tail back-link set).
   Every line carries `[tier · source · date · url] c:<8-char claim id>` — the `c:` token is what
   `record-usage` greps later (§5).
7. **Persist the pack** as `documents(source_type='prior_context_pack')` + a `retrieval` metadata block
   `{lens, seed, budget, candidates, kept, cut}` and print the mandatory audit line — the enforcement
   pattern Step 1.7a already uses.

The `knowledge-conditioning` agent keeps its job (relevance filter + trust flags), but it now receives
**one pack from `retrieve.py`** instead of raw Notion bodies + curl output; its `KNOWN/STALE/UNVERIFIED`
mapping becomes deterministic from `provenance_tier` + age (KNOWN = web_verified/first_hand ≤60d;
STALE = older; UNVERIFIED = notion_prior/model_inferred or any thesis-type claim).

### 3.2 Lens presets (the weights are the lens)

| Lens | w_sem | w_rel | w_rec | w_prov | w_conf | w_use | Extra pulls | Default budget |
|---|---|---|---|---|---|---|---|---|
| **event** | .25 | .35 | .15 | .10 | .10 | .05 | series continuity (prior `observed` events sharing host/series), returning people | 6k |
| **content** | .30 | .20 | .15 | .10 | .05 | **.20** | own `published` docs on the theme (+ outcomes), hot-take claims, stat bank | 5k |
| **job** | .30 | .30 | .15 | .10 | .10 | .05 | people met at target company (speaker/host edges), inbox signals on the company, prior dossiers; **me-model read locally** | 8k |
| **ideation** | .35 | .15 | .10 | .10 | .05 | **.25** | topic co-occurrence (from `topic_intelligence` via `signal_read`), `pitfall` claims as build triggers, `shipped` events for gap analysis | 6k |
| **dev** | .40 | .10 | .15 | .15 | .10 | .10 | `build_retro` + `pitfall`/`practice` claims, glossary definitions, correction classes | 4k |

### 3.3 Consumer 1 — event research & attendance (`/event-deep-research`, `/check-new-events`)

- **Attach point:** Step 1.7a becomes `retrieve.py --lens event --seed <entities + VERBATIM SOURCE + focus>`.
  The Notion `notion-fetch` loop and the ad-hoc Supabase `curl` are **deleted** (the Gmail pull stays —
  correspondence is not in the substrate by design). The mandatory audit line is emitted by the script.
- **What it gets that it cannot get today:** first-hand claims from prior events by the *same speakers*
  ("Ryan Booz said X at Postgres Tuning"), series continuity (all `observed` events by this host),
  what Alex already published on these topics (so the brief's documentarian angle is *new*), book claims
  with locators, inbox signals on the companies, and the `UNVERIFIED` thesis claims routed to
  Verification Flags automatically.
- **Write-back (Step 4 + Step 4.5):** `substrate.py ensure-event` (kind `observed`, the event row
  minted at research time — yesterday's "day-2 fast-follow" becomes day 1), `ensure-document` for the
  brief and, after 4.5, the Deep Read (version chain), `stage-claims` from the Scan head's
  Verification Flags (`notion_prior`) and the Deep Read's endnoted facts (`web_verified` where a URL is
  present), `record-usage` from the `c:` tokens the synthesizer carried. Ledger gate (YED-139 pattern)
  extended: a run whose `ensure-event` did not return an id cannot close green.

### 3.4 Consumer 2 — content creation & writing (`pre-event-content`, `/post-event-content`,
`pattern-synthesis`, `/weekly-recap`, `evergreen-deep-dive`, `voice-pass`)

- **Attach points:** `pre-event-content` Step 1 (before drafting) and `/post-event-content` Step 3.7
  (brief synthesis) and Step 3.9 (Sharpen) call `retrieve.py --lens content` seeded with the event's
  entities + the thesis candidates. `pattern-synthesis` seeds with both events; `/weekly-recap` with the
  week's events.
- **What changes in the output:** the "learn-more set" and inline back-links to Alex's own prior posts
  on the theme come from the **What you've already said** section (this closes the memory item
  *cross-reference prior posts for long-tail*); stance lineage ("you argued X in July; the room now says
  Y") becomes a Sharpen fork; quotes are pulled from the `first_hand` claim bank with speaker ids so
  the name-fidelity rules have canonical names; `hot_take` claims with high `utility_score` are
  surfaced as proven hooks.
- **Write-back:** Step 3.8 extends to 3.8a (`ensure-event observed` if missing) / 3.8b
  (`ensure-document post_event_brief` + `stage-claims` — **approved on brief approval**, §8) / 3.8c
  (`record-usage`). On publish (Content Status → published), `substrate.py publish` mints the
  `event(kind='published')` + document + `artifact_outcome(goal,target)`; `/tag-outcome` later fills the
  outcome (§5).

### 3.5 Consumer 3 — job hunting (`/interview-prep`, `/scan-roles`, resume tailoring YED-151)

- **Attach point:** `/interview-prep` Step 1's "quick dedup read" becomes `retrieve.py --lens job`
  seeded with the company + interviewer + JD text; `me-model.md` is passed as a local side-file (never
  ingested). `/scan-roles` Step 3 scoring gets the company's neighborhood (recent signals, people Alex
  has met there, prior dossiers) as a relevance feature.
- **What it gets:** every speaker/host Alex has seen from the company (with the event and what they
  said), inbox launches/funding on the company, prior dossiers for the same company (version chain),
  book claims on the company's domain, and `target` flags. The dossier-synthesizer receives it as its
  "prior knowledge" block.
- **Write-back:** `/interview-prep` Step 5 adds `ensure-document dossier` + `stage-claims`
  (`web_verified`) + `event(kind='interview')` when a real stage exists; application/interview outcomes
  land through `record-outcome`.

### 3.6 Consumer 4 — new project ideation (`project-ideation`)

- **Attach point:** Step 1 (topic fetch) becomes `retrieve.py --lens ideation` seeded with the event's
  topics. The intersection-strength step reads `signal_read.v_topic_intersections` (already exposed)
  instead of eyeballing.
- **What it gets:** `pitfall`/`practice` claims on the candidate topics (the concrete "build trigger"
  — a recurring pain the room named), `shipped` events (what already exists in the portfolio, so the
  60–80% stack-coverage rule is computed against reality), and which topics have high relevance but no
  `published`/`shipped` coverage (the "uncovered" leg the recompute deferred).
- **Write-back:** proposals → `ensure-document project_idea`; Status=shipped → `event(kind='shipped')`.

### 3.7 Consumer 5 — software development (the pipeline itself: `/rigor-review`, `/judge-build`,
skill edits, `/ask-library` → `/ask`)

- **Attach points:** `/rigor-review` Step 3 (correction-recurrence) pulls `pitfall` claims from
  `build_retro` documents to check whether a proposed fix already exists as a lesson; `/judge-build`'s
  neighborhood pre-pass (ADR-8 Increment 2) stays on the local repo graph — **the substrate does not
  replace it** — but the judge prompt may cite substrate `dev` claims as house context; `/ask-library`
  generalizes to **`/ask`** over chunks + claims of every source type (the same script, `--lens dev`
  default, `--source-type` filter).
- **What it gets:** "what did we learn last time we touched pg_cron / PostgREST / the Notion API",
  glossary definitions, and the Postgres health-review recommendations (YED-167) as approved claims —
  i.e., the stack knowledge that today lives in `.claude/notes/` and memory files and is found by grep.
- **Write-back:** `/dod-close` offers to file the session's retro as a `build_retro` document
  (the journal-entry prose sidecar is already written at break points; this is its knowledge twin).

### 3.8 The generalized review surface: `/digest`

YED-157 B3 (`/doc-digest`, 4 lanes) becomes **`/digest`**: one HITL command that lists `candidate`
claims across all producers (books, build retros, Gemini-extracted brief claims), grouped by source,
≤12 lines, with resolved entity targets shown — approve/reject/edit → `substrate.py approve`. The
inbox miner's resolved-target write gate is the model. Lane B/C/D (content angle, glossary, Linear
recommendation) stay as digest *actions*, not separate pipelines.

---

## 4. Identity & hygiene (foundational — sequenced FIRST)

**Problem it prevents:** "four Elastics" — `Elastic`, `Elastic N.V.`, `Elasticsearch`, `elastic` as
four company rows, each with a slice of the truth. Every relational pull then misses three quarters of
what we know. Backfilling ~90 events through the producers *before* identity exists would create this
on day one.

**Measured today (read-only probe, 2026-09-18):** under a legal-suffix-stripped, punctuation-collapsed
normalization there are **0 collisions** among 189 companies, 188 topics, 232 people; 150/232 people
have a LinkedIn URL; 211/232 have a company. So the unique indexes can ship in migration S1 without a
pre-dedup pass. (Notion has duplicates — Cursor×2, LangChain×2 per YED-47 — the graph does not, because
the 2b link already merged them; the alias table records those merges so Notion→graph resolution hits.)

**Design (all in S1):**
1. **Canonical name = `name_norm`**, a *generated column* (Postgres computes and stores it; no writer can
   forget it) from `norm_name()`: lowercase, strip legal suffixes as whole words, collapse
   non-alphanumerics. Unique on `company(name_norm)` and `topic(name_norm)`; replaces `lower(name)`.
   `person`: unique on `linkedin_url` where present; `(name_norm, company_id)` indexed, **not** unique
   (people share names — ADR-4).
2. **`entity_alias`** — every other name a thing is known by (`Elastic N.V.`, `ESRE`, a Notion title
   variant, an ATS company slug), with `source` and `confidence`. Resolution order in `substrate.py`
   and `retrieve.py`: exact `name_norm` → alias `alias_norm` → embedding candidates (topics/companies
   only) **shown to Claude/Alex** → create. Every "created this run" entity is flagged in the run report
   (ADR-7 R5/R8 discipline, generalized).
3. **`entity_merge`** — the persisted, reversible merge-map (ADR-4 D3 as a table): `from_id`, `to_id`,
   `method ∈ {exact_id, strong_name, human}`, `from_snapshot jsonb`, `reverted_at`. **CHECK: a `person`
   merge must be `method='human'`.** `substrate.py merge` re-points `event_entity`, `claim_entity`,
   `document_entity`, `claim.speaker_person_id`, `person.company_id`, writes an alias for the old name,
   tombstones the source (sets `metadata.merged_into`), never deletes. `merge_topics.py` retires into it.
4. **Provenance tiers on every claim** (§1.1) and `source` prefix on every event/document
   (`event-deep-research:` · `post_event:` · `inbox_miner:` · `doc_kb:` · `build_retro:` …) so the trust
   strip and the registry can name a producer.
5. **Standing hygiene query** (weekly, in `/rigor-review`): near-duplicate topics by embedding cosine
   > 0.92 with different `name_norm`; companies sharing a `website` host; people sharing `linkedin_url`
   (should be impossible after S1); orphan `event_entity`/`claim_entity` rows (should be impossible via
   FK cascade — the query is the check that the constraint is doing its job).

**Where YED-47 lands:** items 1–3 *are* YED-47's "identity + provenance + dedup in code" — it moves from
M5 to M4 and becomes Phase 1 week 1 (it was blocking, not blocked).

---

## 5. Outcome feedback (how the substrate learns what was useful)

Three signals, one mechanism.

| Signal | Source | Lands as | Reinforces |
|---|---|---|---|
| **Content outcomes** | `/tag-outcome` writes Outcome/Value/Date to Notion → `substrate.py record-outcome` | `artifact_outcome` on the `published` document | every claim in that artifact's `claim_usage` gets `utility_score += w(outcome)` (hit 1.0 · partial 0.5 · miss −0.25 · pending 0); the topics/people the `published` event links get `engagement_count += 1`, `last_engaged_at = now` |
| **Job-search outcomes** | `/interview-prep` / `/scan-roles` state changes (applied → screened → onsite → offer/no) | `event(kind='application'/'interview')` with `metadata.stage`, `artifact_outcome` on the dossier | company/person relevance; dossier claims' utility |
| **Build outcomes** | judge verdict + PR merged + DoD close (rigor layer) | **not stored in the substrate** — but `/dod-close` files the retro (`build_retro`) and `record-usage` for `dev` claims consulted; `utility` for those claims rises when the build's PR merges (a one-line call from `/dod-close` with the PR state) | `dev` claims' utility |

**Usage capture (the missing half of "acted-on value"):** `retrieve.py` stamps every pack line with
`c:<id>`; the writer step of each consumer (`notion-writer`, the brief/post persistence, the dossier
persist) greps the final artifact for `c:` tokens → `substrate.py record-usage --document <artifact>
--claims <ids> --consumer <lens>`. A claim that is retrieved 20 times and used 0 times is *noise for that
lens* and decays; a claim used in a `hit` post is gold. This is the value-action registry's north-star
(acted-on value) applied at claim grain.

**Relevance recompute v2 (`recompute_relevance.py`, REST, no DDL):**
`relevance = recency_decay(last_engaged_at) × (1 + ln(1 + confidence_mass + claim_mass)) + event_proximity + outcome_boost − coverage_penalty`
where `claim_mass` = Σ approved-claim confidence on the entity, `outcome_boost` = Σ utility of the
entity's used claims (capped), and `coverage_penalty` down-ranks topics with a `published` event in the
last 21 days (the "uncovered" leg the V1 deferred — now computable because `published` events exist).
Claims decay independently: `utility_score *= 0.5^(days_since_last_used/180)` nightly; never below 0.

**Registry rows to add (a metric without a row does not ship):**

| Metric | Threshold | Action | Surface |
|---|---|---|---|
| retrieval runs / week while producers wrote ≥1 row | 0 | the substrate is a landfill — wire or fix the consumer that skipped `retrieve.py` | weekly review |
| claims `candidate` age | > 14d | run `/digest`; if approval rate < 30% for a producer, tighten its extractor | weekly review |
| claim usage rate (used ÷ retrieved, 30d) per lens | < 10% | re-weight that lens's preset; inspect what is crowding the budget | weekly review |
| entities created-this-run without alias/website/linkedin | > 0 | human resolve-or-merge before they can surface in content | in-session (producer report) |
| embedding staleness (`claim.embedding is null` or `documents` chunks missing) | > 0 for > 24h | run `substrate.py embed` (the nightly `launchd` job if adopted) | weekly / trust strip |
| producer liveness incl. `post_event:` / `event-deep-research:` | silent > 14d on active event weeks | check the write-back step (this is the gap that hid for six weeks) | Hub trust strip |

---

## 6. Migration & backfill

### 6.1 Principles (from `docs/migration-playbook.md`, applied)

- **Additive-first, no `public` mutation of existing rows' meaning.** Everything below is `add column`,
  `create table`, `add constraint … check` (widened), new indexes, new RPCs. Nothing is dropped except
  the `lower(name)` unique indexes *after* the `name_norm` ones exist (S1 does both in one transaction,
  so the table is never unguarded). Rollback of S1 = drop the new tables/columns/indexes; the old
  `lower(name)` indexes are recreated by the rollback script (included).
- **Backfill runs THROUGH the producers.** There is no "backfill script" — there is
  `substrate.py … --manifest` invoked over a list, and a manifest builder per source. If a backfill needs
  code the live producer does not have, the producer is wrong. Idempotency proof for each: the second run
  reports `created: 0`.
- **Measure before and after.** Counts per table/kind/source before, after each batch, and the standing
  invariants (§6.4).
- **DDL is Alex's, in the dashboard SQL editor** (PostgREST cannot DDL). Two migrations, not five;
  each ends with its verification block.

### 6.2 Migration S1 — the substrate core (paste as one script; ~2 min)

```sql
-- =====================================================================
-- S1 — Knowledge Substrate core (ADR-10). ADDITIVE. Project oicikjyzmxqfomrrqkvf ONLY.
-- Apply once in the `empire state ai` SQL Editor. Run the VERIFY block at the end.
-- Precondition: doc-kb-schema.sql, doc-kb-migration-a5.sql, doc-kb-migration-b1.sql applied
-- (verified 2026-09-18: documents=2, doc_chunks=305, doc_claims=0, kind 'reference' present).
-- =====================================================================
begin;

create extension if not exists vector;
create extension if not exists pgcrypto;

-- 1. Event kinds: three new occasions, each with a named consumer (see architecture §1.2)
alter table public.event drop constraint if exists event_kind_enum;
alter table public.event add constraint event_kind_enum check (kind in (
  'attended','market','funding','launch','exec_move',
  'role_posted','application','interview',
  'reference',
  'observed',    -- an attended event as the OCCASION for first-hand claims (live producer; distinct from the 2b 'attended' migration rows)
  'published',   -- Alex published an artifact (content lens memory + outcome anchor)
  'shipped'      -- a project/build shipped (ideation gap analysis)
));

-- 2. Identity ------------------------------------------------------------
create or replace function public.norm_name(t text) returns text
language sql immutable parallel safe as $$
  select nullif(trim(regexp_replace(
           regexp_replace(lower(coalesce(t,'')),
             '\m(inc|llc|ltd|corp|corporation|co|gmbh|plc|sa|ag|limited|incorporated)\M\.?', '', 'g'),
           '[^a-z0-9]+', ' ', 'g')), '')
$$;

alter table public.company add column if not exists name_norm text
  generated always as (public.norm_name(name)) stored;
alter table public.topic   add column if not exists name_norm text
  generated always as (public.norm_name(name)) stored;
alter table public.person  add column if not exists name_norm text
  generated always as (public.norm_name(name)) stored;

-- Probe 2026-09-18 found 0 collisions under this normalization, so the unique indexes ship now.
-- If either CREATE UNIQUE fails, STOP: run the COLLISIONS query (verify block) and merge first.
create unique index if not exists company_name_norm_uq on public.company (name_norm);
create unique index if not exists topic_name_norm_uq   on public.topic   (name_norm);
drop index if exists public.company_name_lower_uniq;
drop index if exists public.topic_name_lower_uniq;
create index if not exists person_name_norm_company_idx on public.person (name_norm, company_id);
create unique index if not exists person_linkedin_uq on public.person (lower(linkedin_url))
  where linkedin_url is not null and linkedin_url <> '';

create table if not exists public.entity_alias (
  id           uuid primary key default gen_random_uuid(),
  entity_type  text not null check (entity_type in ('company','person','topic')),
  entity_id    uuid not null,
  alias        text not null,
  alias_norm   text generated always as (public.norm_name(alias)) stored,
  source       text not null,                 -- notion | inbox_miner | ats | merge | manual
  confidence   numeric default 1.0,
  created_at   timestamptz not null default now(),
  unique (entity_type, alias_norm)
);
create index if not exists entity_alias_entity_idx on public.entity_alias (entity_type, entity_id);

create table if not exists public.entity_merge (
  id             uuid primary key default gen_random_uuid(),
  entity_type    text not null check (entity_type in ('company','person','topic')),
  from_id        uuid not null,
  to_id          uuid not null,
  method         text not null check (method in ('exact_id','strong_name','human')),
  confidence     numeric,
  decided_by     text not null default 'alex',
  from_snapshot  jsonb not null,               -- the merged row as it was: makes the merge reversible
  merged_at      timestamptz not null default now(),
  reverted_at    timestamptz,
  -- ADR-4 D3 mechanized: people are NEVER machine-merged
  constraint person_merge_is_human check (entity_type <> 'person' or method = 'human')
);

-- embedding-assisted match-before-create (assist only; the decision stays with Claude/Alex)
alter table public.topic   add column if not exists embedding vector(384);
alter table public.company add column if not exists embedding vector(384);

-- 3. Documents: generalize to every artifact with a body ------------------
alter table public.documents alter column blob_key drop not null;   -- our own artifacts have no R2 blob
alter table public.documents drop constraint if exists documents_source_type_check;
alter table public.documents add constraint documents_source_type_check check (source_type in (
  'book','whitepaper','filing','pdf','other',
  'research_brief','deep_read','prior_context_pack','post_event_brief','transcript',
  'linkedin_post','carousel','connection_note','dossier','project_idea',
  'scan_digest','build_retro','note','glossary'
));
alter table public.documents
  add column if not exists event_id       uuid references public.event(id) on delete set null,
  add column if not exists external_ref   text,          -- Notion page id · file path · PR url · message-id
  add column if not exists doc_date       timestamptz,   -- when the artifact is "about" (event date / publish date)
  add column if not exists version        integer not null default 1,
  add column if not exists supersedes_id  uuid references public.documents(id) on delete set null,
  add column if not exists produced_by    text,          -- command/skill/source that produced it
  add column if not exists visibility     text not null default 'private'
                                           check (visibility in ('private','public_ok')),
  add column if not exists metadata       jsonb not null default '{}';
create index if not exists documents_event_idx       on public.documents (event_id);
create index if not exists documents_source_type_idx on public.documents (source_type);
create index if not exists documents_external_ref_idx on public.documents (external_ref);

create table if not exists public.document_entity (
  document_id  uuid not null references public.documents(id) on delete cascade,
  entity_type  text not null check (entity_type in ('company','person','topic')),
  entity_id    uuid not null,
  role         text not null default 'about',  -- about | author | mentions
  created_at   timestamptz not null default now(),
  primary key (document_id, entity_type, entity_id, role)
);
create index if not exists document_entity_entity_idx on public.document_entity (entity_type, entity_id);

-- 4. Claims: the unified layer (generalizes doc_claims; 0 rows today so the rename is safe) ---
alter table if exists public.doc_claims rename to claim;
alter index if exists public.doc_claims_status_idx rename to claim_status_idx;
alter index if exists public.doc_claims_sha_idx    rename to claim_source_idx;
comment on column public.claim.document_sha256 is
  'Source identity: sha256 of the source document, or a synthetic key for occasion-sourced claims (e.g. sha256(''post_event:''||notion_event_id)). Paired with claim_key for idempotency.';
comment on column public.claim.promoted_event_id is
  'DEPRECATED by ADR-10: claims are first-class and are not promoted into event rows. Kept for compatibility; not written.';
alter table public.claim
  add column if not exists document_id        uuid references public.documents(id) on delete set null,
  add column if not exists event_id           uuid references public.event(id) on delete set null,     -- the occasion
  add column if not exists speaker_person_id  uuid references public.person(id) on delete set null,
  add column if not exists provenance_tier    text not null default 'reference'
       check (provenance_tier in ('first_hand','web_verified','email_signal','notion_prior','reference','model_inferred')),
  add column if not exists embedding          vector(384),
  add column if not exists tsv                tsvector
       generated always as (to_tsvector('english', coalesce(claim_text,'') || ' ' || coalesce(quote,''))) stored,
  add column if not exists utility_score      numeric not null default 0,
  add column if not exists use_count          integer not null default 0,
  add column if not exists last_used_at       timestamptz,
  add column if not exists metadata           jsonb not null default '{}';
-- claim_type vocabulary (documented, not CHECKed — producers evolve it):
--   thesis | definition | statistic | practice | prediction | pitfall | hot_take | anecdote | recommendation | learning
create index if not exists claim_document_idx  on public.claim (document_id);
create index if not exists claim_event_idx     on public.claim (event_id);
create index if not exists claim_speaker_idx   on public.claim (speaker_person_id);
create index if not exists claim_tsv_gin       on public.claim using gin (tsv);
create index if not exists claim_embedding_hnsw on public.claim using hnsw (embedding vector_cosine_ops);

create table if not exists public.claim_entity (
  claim_id     uuid not null references public.claim(id) on delete cascade,
  entity_type  text not null check (entity_type in ('company','person','topic')),
  entity_id    uuid not null,
  role         text not null default 'about',   -- about | asserted_by | contrasts
  created_at   timestamptz not null default now(),
  primary key (claim_id, entity_type, entity_id, role)
);
create index if not exists claim_entity_entity_idx on public.claim_entity (entity_type, entity_id);

-- 5. Outcomes + usage (the feedback half) -----------------------------------
create table if not exists public.artifact_outcome (
  document_id   uuid primary key references public.documents(id) on delete cascade,
  goal          text,            -- reach | engagement | connection | meeting | hybrid | internal | application | interview
  target        text,
  outcome       text check (outcome in ('hit','partial','miss','pending','na')),
  outcome_value text,
  outcome_date  timestamptz,
  source        text not null default 'tag_outcome',
  updated_at    timestamptz not null default now()
);
create trigger artifact_outcome_set_updated_at before update on public.artifact_outcome
  for each row execute function set_updated_at();

create table if not exists public.claim_usage (
  id           uuid primary key default gen_random_uuid(),
  claim_id     uuid not null references public.claim(id) on delete cascade,
  document_id  uuid not null references public.documents(id) on delete cascade,  -- the artifact that used it
  consumer     text not null,   -- event | content | job | ideation | dev
  used_at      timestamptz not null default now(),
  unique (claim_id, document_id)
);
create index if not exists claim_usage_claim_idx on public.claim_usage (claim_id);

-- 6. Security: RLS on, service-key only (matches every existing table) ----------
alter table public.entity_alias     enable row level security;
alter table public.entity_merge     enable row level security;
alter table public.document_entity  enable row level security;
alter table public.claim_entity     enable row level security;
alter table public.artifact_outcome enable row level security;
alter table public.claim_usage      enable row level security;

commit;

-- ============================ VERIFY (run after commit) ============================
-- expect: 0 rows (no collisions) — if S1 failed on a unique index, THIS is the list to merge first
select 'company' t, name_norm, count(*) from public.company group by 1,2 having count(*)>1
union all select 'topic', name_norm, count(*) from public.topic group by 1,2 having count(*)>1;
-- expect: 11 kinds allowed (probe 'observed' insert-then-delete is done by substrate.py --selftest, not here)
select pg_get_constraintdef(oid) from pg_constraint where conname='event_kind_enum';
-- expect: claim exists, doc_claims gone; new tables present
select table_name from information_schema.tables where table_schema='public'
  and table_name in ('claim','doc_claims','entity_alias','entity_merge','document_entity','claim_entity','artifact_outcome','claim_usage')
  order by 1;
-- expect: 3 rows with data_type = text (generated)
select table_name, column_name, is_generated from information_schema.columns
  where table_schema='public' and column_name='name_norm';
-- expect: hnsw index on claim.embedding present
select indexname from pg_indexes where tablename='claim' and indexname like '%hnsw%';
```

**Rollback S1 (keep beside it; run only if S1 must be undone before any data lands):**
```sql
begin;
drop table if exists public.claim_usage, public.artifact_outcome, public.claim_entity,
  public.document_entity, public.entity_merge, public.entity_alias;
alter table public.claim drop column if exists document_id, drop column if exists event_id,
  drop column if exists speaker_person_id, drop column if exists provenance_tier,
  drop column if exists embedding, drop column if exists tsv, drop column if exists utility_score,
  drop column if exists use_count, drop column if exists last_used_at, drop column if exists metadata;
alter table public.claim rename to doc_claims;
alter table public.documents drop column if exists event_id, drop column if exists external_ref,
  drop column if exists doc_date, drop column if exists version, drop column if exists supersedes_id,
  drop column if exists produced_by, drop column if exists visibility, drop column if exists metadata;
alter table public.documents alter column blob_key set not null;   -- only valid while every row still has one
alter table public.documents drop constraint if exists documents_source_type_check;
alter table public.documents add constraint documents_source_type_check
  check (source_type in ('book','whitepaper','filing','pdf','other'));
alter table public.topic drop column if exists embedding; alter table public.company drop column if exists embedding;
drop index if exists public.company_name_norm_uq; drop index if exists public.topic_name_norm_uq;
drop index if exists public.person_linkedin_uq; drop index if exists public.person_name_norm_company_idx;
create unique index company_name_lower_uniq on public.company (lower(name));
create unique index topic_name_lower_uniq on public.topic (lower(name));
alter table public.company drop column if exists name_norm; alter table public.topic drop column if exists name_norm;
alter table public.person drop column if exists name_norm;
drop function if exists public.norm_name(text);
alter table public.event drop constraint if exists event_kind_enum;
alter table public.event add constraint event_kind_enum check (kind in
  ('attended','market','funding','launch','exec_move','role_posted','application','interview','reference'));
commit;
```

### 6.3 Migration S2 — retrieval RPCs (paste after S1; week 2, before `retrieve.py` ships)

```sql
-- =====================================================================
-- S2 — Retrieval RPCs for the Knowledge Substrate (ADR-10). ADDITIVE. Same project. Apply after S1.
-- =====================================================================
begin;

-- Hybrid claim search: dense ∪ keyword → reciprocal-rank fusion. approved-only by default.
-- Optional entity scope: only claims linked (via claim_entity or claim.event_id→event_entity) to these ids.
create or replace function public.match_claims_hybrid (
  query_embedding    vector(384),
  query_text         text,
  match_count        int    default 20,
  candidate_n        int    default 40,
  rrf_k              int    default 60,
  filter_entity_ids  uuid[] default null,
  filter_status      text   default 'approved',
  filter_tiers       text[] default null
)
returns table (id uuid, claim_text text, claim_type text, quote text, locator jsonb,
               provenance_tier text, confidence numeric, utility_score numeric,
               document_id uuid, event_id uuid, speaker_person_id uuid, created_at timestamptz,
               dense_rank integer, keyword_rank integer, rrf_score float)
language sql stable as $$
  with base as (
    select c.*
    from public.claim c
    where (filter_status is null or c.status = filter_status)
      and (filter_tiers is null or c.provenance_tier = any(filter_tiers))
      and (filter_entity_ids is null or exists (
            select 1 from public.claim_entity ce
            where ce.claim_id = c.id and ce.entity_id = any(filter_entity_ids)
          ) or exists (
            select 1 from public.event_entity ee
            where ee.event_id = c.event_id and ee.entity_id = any(filter_entity_ids)
          ))
  ),
  dense as (
    select id, row_number() over (order by embedding <=> query_embedding) as r
    from base where embedding is not null
    order by embedding <=> query_embedding limit candidate_n
  ),
  kw as (
    select id, row_number() over (order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc) as r
    from base where tsv @@ websearch_to_tsquery('english', query_text)
    order by ts_rank_cd(tsv, websearch_to_tsquery('english', query_text)) desc limit candidate_n
  ),
  fused as (
    select coalesce(d.id, k.id) as id, d.r as dr, k.r as kr,
           coalesce(1.0/(rrf_k + d.r), 0) + coalesce(1.0/(rrf_k + k.r), 0) as score
    from dense d full outer join kw k on d.id = k.id
  )
  select b.id, b.claim_text, b.claim_type, b.quote, b.locator, b.provenance_tier, b.confidence,
         b.utility_score, b.document_id, b.event_id, b.speaker_person_id, b.created_at,
         f.dr::integer, f.kr::integer, f.score::float
  from fused f join base b on b.id = f.id
  order by f.score desc, b.created_at desc
  limit match_count;
$$;
alter function public.match_claims_hybrid(vector, text, int, int, int, uuid[], text, text[]) set search_path = public;

-- 1-hop neighborhood: every event a seed entity participated in, the co-participants, and linked docs/claims.
create or replace function public.entity_neighborhood (
  seed_ids   uuid[],
  since      timestamptz default null,
  max_events int default 60
)
returns jsonb language sql stable as $$
  with ev as (
    select distinct e.id, e.title, e.kind, e.event_date, e.source, e.url, e.confidence
    from public.event e join public.event_entity ee on ee.event_id = e.id
    where ee.entity_id = any(seed_ids) and (since is null or e.event_date >= since)
    order by e.event_date desc nulls last limit max_events
  ),
  co as (
    select ee.event_id, ee.entity_type, ee.entity_id, ee.role,
           coalesce(c.name, p.name, t.name) as name
    from public.event_entity ee
    left join public.company c on c.id = ee.entity_id and ee.entity_type='company'
    left join public.person  p on p.id = ee.entity_id and ee.entity_type='person'
    left join public.topic   t on t.id = ee.entity_id and ee.entity_type='topic'
    where ee.event_id in (select id from ev)
  ),
  docs as (
    select distinct d.id, d.title, d.source_type, d.doc_date, d.external_ref, d.event_id
    from public.documents d
    left join public.document_entity de on de.document_id = d.id
    where de.entity_id = any(seed_ids) or d.event_id in (select id from ev)
  ),
  cl as (
    select distinct c.id, c.claim_text, c.claim_type, c.provenance_tier, c.confidence, c.utility_score,
           c.event_id, c.document_id, c.speaker_person_id, c.created_at
    from public.claim c
    left join public.claim_entity ce on ce.claim_id = c.id
    where c.status = 'approved'
      and (ce.entity_id = any(seed_ids) or c.event_id in (select id from ev))
  )
  select jsonb_build_object(
    'events',   (select coalesce(jsonb_agg(to_jsonb(ev)), '[]'::jsonb) from ev),
    'edges',    (select coalesce(jsonb_agg(to_jsonb(co)), '[]'::jsonb) from co),
    'documents',(select coalesce(jsonb_agg(to_jsonb(docs)), '[]'::jsonb) from docs),
    'claims',   (select coalesce(jsonb_agg(to_jsonb(cl)), '[]'::jsonb) from cl)
  );
$$;
alter function public.entity_neighborhood(uuid[], timestamptz, int) set search_path = public;

-- Embedding-assisted entity match (assist only). Returns the closest existing topics/companies to a query vector.
create or replace function public.match_entities (
  query_embedding vector(384), entity_kind text default 'topic', match_count int default 5
)
returns table (id uuid, name text, similarity float) language sql stable as $$
  select id, name, 1 - (embedding <=> query_embedding) as similarity
  from (select id, name, embedding from public.topic   where entity_kind='topic'   and embedding is not null
        union all
        select id, name, embedding from public.company where entity_kind='company' and embedding is not null) x
  order by embedding <=> query_embedding limit match_count;
$$;
alter function public.match_entities(vector, text, int) set search_path = public;

commit;

-- ============================ VERIFY ============================
-- expect 5 functions: match_doc_chunks, match_doc_chunks_hybrid, match_claims_hybrid, entity_neighborhood, match_entities
select proname from pg_proc where pronamespace = 'public'::regnamespace
  and proname in ('match_doc_chunks','match_doc_chunks_hybrid','match_claims_hybrid','entity_neighborhood','match_entities') order by 1;
-- smoke (returns [] / empty until data lands; must not error):
select public.entity_neighborhood(array[(select id from public.company limit 1)]);
```

**S3 (optional, week 4, only if `pg_cron` is enabled on the project — UNVERIFIED):** schedule the
nightly relevance + claim-decay recompute in-database. Until then `recompute_relevance.py` (REST) runs
from `/morning-refresh` as today; a `launchd` job is the no-DDL alternative (needs `.env` loaded
explicitly — the ADR-7 R4 hazard).

### 6.4 Backfill sequence (through the producers; each batch has an idempotency proof)

| Step | Producer verb | Source | Volume | Idempotency proof | Gate |
|---|---|---|---|---|---|
| B0 | `substrate.py --selftest` | — | — | 25+ guard cases incl. new tables; an `observed` insert-then-delete | S1 applied |
| B1 | `ensure-entity` (alias seeding) | Notion Companies/Topics/People titles + graph names → `entity_alias(source='notion')`; the 2b `merge_map` (12 false splits) → `entity_merge(method='strong_name')` + aliases | ~600 aliases | second run: `created 0` | B0 |
| B2 | `ensure-event` | Notion Events (all, oldest first), kind `observed`, edges from People `Role Context` (speaker/host) + Topics/Companies relations | ~85–95 events; the 59 `attended` 2b rows are **matched by `notion_page_id`** (they carry it) and re-tagged `metadata.also_observed=true`, never duplicated | run twice; second run `created 0`; **the 59 rows untouched** (yesterday's acceptance) | B1 |
| B3 | `ensure-document` + `stage-claims` | the 5 `post_event_brief` pages (Notion body) | ~150–300 claims (learnings sections) | `claim_key` collisions → `skipped` | B2 |
| B4 | `ensure-document` (+ chunks) | 12 transcripts (`event-transcripts/`) | ~12 docs, ~1.5–3k chunks | file sha256 | B2 |
| B5 | `publish` | Content Drafts `published` (+ `Published URL`, Goal/Target, Outcome if tagged) | est. 40–80 posts | Notion page id | B2 |
| B6 | `ensure-document` + `stage-claims` | `research_brief` + Deep Read bodies (Scan head Verification Flags → `notion_prior`; endnoted facts with URL → `web_verified`) | ~90 docs | body sha256 → version chain | B2 |
| B7 | `ensure-document` + `stage-claims` | `.claude/notes/*.md`, `docs/adr/*.md` (retros), `.claude/evals/correction-recurrence.md` (pitfall classes) | ~25 docs | file sha256 | B0 |
| B8 | `embed` | all `claim.embedding is null`, `topic.embedding`, `company.embedding` | ~1k vectors | null-count → 0 | any |
| B9 | recompute v2 | — | — | scores stable on re-run | B5 |

**Volume caveat:** Notion Events total is an estimate (59 pre-08-10 + 27 since 08-20 + a handful in the
gap); the B2 manifest builder prints the true count before any write. Approval bandwidth for B3/B6/B7
candidates is the real constraint (§8 decision: brief-approved claims land `approved` directly).

### 6.5 Standing invariants (checked after every batch; later a weekly query)
1. No `event_entity`/`claim_entity`/`document_entity` row whose `entity_id` has no row in its type table.
2. No two `company`/`topic` rows share `name_norm` (guaranteed by index; the query proves the index exists).
3. Every `event(kind in ('observed','published','shipped'))` has ≥1 `event_entity` row.
4. Every `claim(status='approved')` has `provenance_tier` and either `document_id` or `event_id`.
5. Every `documents` row with `source_type` in our-artifact types has `external_ref`.
6. `person.email` is null everywhere; no string in `claim.claim_text`/`quote`/`documents.metadata` matches the guard's email/phone regex (the guard prevents it; the query proves the guard ran).
7. Trust strip producer set ⊇ {`event-deep-research`, `post_event`, `inbox_miner`, `trend_radar`} once B2/B3 land.

---

## 7. The program plan

### 7.1 Shape: 4 weeks, Sep 20 → Oct 17 (= roadmap A1 / Linear M4), then A2/A3 consume it

| Week | Theme | Ships | Proof |
|---|---|---|---|
| **W1 · Sep 20–26** — *Foundation + first producer* | S1 DDL · `substrate.py` (ensure-entity/ensure-event/ensure-document/stage-claims/approve/link/embed) · ALLOW-list extension + `--check-writers` · B0–B3 backfill · `/post-event-content` 3.8a–c wired + ledger gate · `/event-deep-research` Step 4 `ensure-event` | 24 absent events present; Postgres Tuning (09-16) claims in the graph; `created 0` on second run; trust strip shows `post_event` |
| **W2 · Sep 27–Oct 3** — *Retrieval* | S2 DDL · `retrieve.py` (5 presets, budget, pack, audit, persist) · `knowledge-conditioning` consumes the pack · Step 1.7a replaced · `/interview-prep` Step 1 wired · B4 transcripts, B8 embed · `/digest` (generalizes `/doc-digest`, YED-157 B3) | one real `/event-deep-research` run whose pack cites a first-hand claim from a prior event by the same speaker; retrieval recall ≥80% on a 20-question set drawn from the 5 briefs |
| **W3 · Oct 4–10** — *The other producers + consumers* | `publish` verb + B5 · B6 briefs · B7 retros · `record-outcome` in `/tag-outcome` · `record-usage` in the writers · content/ideation/dev lens wiring · hub trust strip + a "substrate" tile (claims by producer, candidate age) | a `pre-event-content` run back-links two prior posts via the pack; `/tag-outcome` writes one `artifact_outcome`; `/rigor-review` cites a `build_retro` claim |
| **W4 · Oct 11–17** — *Feedback + hygiene + eval* | recompute v2 (claim mass, outcome boost, coverage penalty, claim decay) · hygiene query in `/rigor-review` · registry rows · ADR-10 Accepted · PRD decision log closed · YED-149 roles producer if capacity | A1 proof: three live producers on the strip (post_event, event-deep-research, inbox) + doc-KB claims approved; relevance ranking changes after an outcome is tagged; a claim's `utility_score` moves |
| **A2 · Nov 14** (YED-126) | architecture lens **on top of** the substrate: `topic.layer` (taxonomy v2), per-layer density from claims + events, YED-131 recompute reading `observed` | "what's moving in the harness layer" answered from claims, not prose |
| **A3 · Dec 12** (YED-162, YED-48) | the loop reads `dev` claims + rigor telemetry; event-research eval uses the retrieval eval set | first exhaust-derived fix merged |

### 7.2 Phase 1 — concretely startable this weekend (the exact first build)

**Friday night (already done):** this document → PRD compressed into ChatPRD + Notion mirror (Fable);
open the Linear set below (Alex confirms).

**Saturday — build 1: `S1` + `substrate.py ensure-event` (branch `feat/substrate-s1-ensure-event`, own worktree, `.env` symlinked).**
1. Alex pastes **S1** in the SQL editor; runs the VERIFY block; pastes results into the session.
2. Extend `spine_client.ALLOW` for `claim` (renamed), `entity_alias`, `entity_merge`, `document_entity`,
   `claim_entity`, `artifact_outcome`, `claim_usage`; add selftest cases (email inside `claim_text` →
   refuse; `person` merge with `method='strong_name'` is refused by the DB, asserted by test);
   `--check-writers` still green.
3. `substrate.py` with **`ensure-entity`** (resolution ladder: `name_norm` → alias → create; alias
   seeding from a manifest) and **`ensure-event`** (yesterday's spec, kind `observed`, edges from Role
   Context, `--dry-run`, matched/created table). Manifest builder: parent-thread `notion-fetch` over the
   Events DB → `events.json` (title, date, notion_page_id, GCal id, People with Role Context + LinkedIn,
   Companies, Topics).
4. **Acceptance:** dry-run over the 59 `attended` rows → 59 matched / 0 created; live run over the
   27 recent events → 24 created (2 `not_attending` skipped, 1 matched); second live run → `created 0`.
   Postgres Tuning (09-16) has Ryan Booz as `speaker`.
5. `/judge-build` on `substrate.py`; `/dod-close`.

**Sunday — build 2: `stage-claims` + `/post-event-content` 3.8a–c.**
1. `stage-claims --brief <notion page> --event <id>`: strict header parse of the numbered learnings
   sections; `claim_key = sha256(norm(text))`; `speaker_person_id` from the Speaker Map (HIGH/MED only);
   `provenance_tier='first_hand'`; `confidence` = HIGH 0.8 / MED 0.6; quote ≤25 words;
   `status='approved'` **iff** the brief's Notion `Content Status='approved'`, else `candidate`
   (§8 decision); **zero-claim parse warns LOUD** (the brief format drifted).
2. Wire 3.8a/b/c into `post-event-content.md` (extend 3.8, do not add 3.9 — the existing steering gate);
   ledger row `substrate:<event>` pending → written; Stop-hook gate reuses `deep-read-gate.sh`'s shape.
3. Backfill B3 over the 5 briefs; `embed` the resulting claims (venv bge-small; ~1 minute).
4. **Acceptance:** ≥5 approved claims per brief with `speaker_person_id`; re-run no-op; a `GET
   /claim?event_id=eq.<postgres-tuning>&status=eq.approved` returns rows with `provenance_tier=first_hand`.

That is two focused builds, each with a spec (this doc → PRD), an issue, a judge run, and a proof line.
The rest of W1 (B1 alias seeding, Step 4 `ensure-event` in `/event-deep-research`) follows on weekdays.

### 7.3 Linear — the proposed set (NOT created; Alex confirms; then one session writes them)

| Issue | Proposal | Milestone |
|---|---|---|
| **YED-160** | **Keep, retitle:** *"Substrate producer 1: events + first-hand claims (`ensure-event` / `stage-claims`), `/post-event-content` 3.8a–c"* — the Phase 1 build; fix the two spec bugs (3.9 → 3.8a–c; drop the YED-108 credit); depends on the new ADR-10 issue; blockedBy YED-81 already Done | M4 |
| **YED-47** | **Keep, pull forward M5 → M4, retitle:** *"Identity layer: `name_norm` + `entity_alias` + `entity_merge` (S1) + alias seeding + hygiene query"*. It was blocking the backfill, not blocked by the map | M4 |
| **YED-157** | **Keep, re-scope B3–B5:** B3 becomes `/digest` (all producers); B4 "two filter lines" becomes *retrieval interface consumer wiring* (absorbed by the new retrieval issue); B1's `promote → event(reference)` superseded by ADR-10 (claims first-class) — note in the issue | M4 |
| **YED-131** | **Keep, extend:** recompute reads `observed` events + claims; add relevance v2 (claim mass, outcome boost, coverage penalty, claim decay); pg_cron if available (S3) | M4 → A2 |
| **YED-126** | **Unchanged** — becomes a *consumer* of the substrate (`topic.layer`, per-layer claim density); explicitly depends on the retrieval issue | M5 |
| **YED-162** | **Unchanged** — add a dependency on the `dev` lens (retros as claims) | M6 |
| **YED-167** | **Split:** (a) glossary + health review as-is; (b) **new decision item:** *Supabase MCP policy for DDL* — see §9 | Events / MI |
| **YED-108** | Close-as-Done-elsewhere / annotate "gtm-os repo, old spine" (no longer credited by YED-160) | — |
| **NEW-1** | *ADR-10 — Knowledge Substrate: unified claim layer, generalized documents, identity tables, three occasion kinds* (decision-before-code; Proposed → Accepted at W4) | M4 |
| **NEW-2** | *`substrate.py` producer library + ALLOW extension + selftest* (the write side) | M4 |
| **NEW-3** | *`retrieve.py` retrieval interface + Context Pack + lens presets + S2 RPCs; replaces Step 1.7a; wires `/interview-prep`, `pre-event-content`, `project-ideation`, `/rigor-review`* | M4 |
| **NEW-4** | *Backfill through producers B1–B9 (idempotency proofs, invariant checks)* | M4 |
| **NEW-5** | *Outcome + usage feedback: `record-outcome` in `/tag-outcome`, `record-usage` in writers, `publish` verb, registry rows* | M4 |
| **NEW-6** | *Hub: trust strip reads all producers (claims + all kinds); substrate tile* (empire-state-hub repo) | Hub |
| **NEW-7** | *Retrieval eval: 20-question set from the 5 briefs, recall@budget ≥80%, usage-rate telemetry* | M4 |
| **YED-149** (roles producer) | Keep in M4 as capacity allows; now a `substrate.py` manifest consumer, not bespoke | M4/M5 |

Convention check: one issue per requirement, appetite bands not estimates, `blockedBy` from the
"depends on" lines above, labels `project-mi-engine` + `cycle-1/2`. No initiative (fewer than 3
projects connect).

---

## 8. Decision log + inline pre-mortem

### 8.1 Alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| **Claims as `event` rows** (YED-157/160 as written; yesterday's Option A/B) | N rows per real occasion; conflates "said" with "happened"; breaks trust-strip semantics; forces the recompute to treat books as events. A claim *points at* its occasion instead. |
| **A property-graph / Neo4j / separate vector DB** | Postgres + pgvector already hold the data and the readers; a second store re-creates the two-spine problem ADR-0/1 just closed. Revisit only if `entity_neighborhood` needs >1 hop routinely (measure first). |
| **Notion as the substrate** (extend the 6 DBs) | Notion has no vector search, no joins, no idempotency keys, and the MCP is plan-gated for queries; ADR-6 already decided Notion is the review surface. |
| **One flat `knowledge` table with a `type` column** (polymorphic everything) | The gtm-os model ADR-1 rejected — lossy FKs; the five consumers need typed joins (speaker → person, occasion → event). |
| **Direct writes everywhere, no staging** | An unreviewed transcript or a Gemini extraction becomes "truth". Staging stays for model-extracted claims; **approval is inherited** from the artifact review for brief-derived claims (below). |
| **Everything staged / HITL** (YED-160 as written) | Rationalization for facts Alex already reviewed; produces the "candidates pile up" failure by design. |
| **Ingest me-model / target-companies into the spine** | Personal document one grant from a public read-model; local side-input at query time gives the job lens the same value with zero exposure. |
| **Build telemetry / judge runs into the substrate** | Violates the measurement tombstone and ADR-8's local-cache decision; only *lessons* enter, as claims. |
| **N=8 cap kept as the retrieval guard** | It guarded Notion fetch cost; the substrate serves pre-extracted text — a token budget with an audit line is the right guard. |
| **Separate producers per source with bespoke writers** (today's pattern) | Six writers already existed before ADR-9 forced one chokepoint; the same drift would return. One library, manifest in. |
| **Auto-merge entities by embedding** | ADR-4: never fuzzy-merge people; for companies/topics the candidate is *shown*, the decision is Claude/Alex's; a wrong merge is silent and expensive. |

### 8.2 Decisions taken in this design (dated; append-only from here)

- **2026-09-18** — Claims are first-class rows, not promoted events — supersedes YED-157 B1's promotion target and yesterday's Option A/B.
- **2026-09-18** — `doc_claims` renamed to `claim` and generalized (0 rows; B3 unbuilt) — the compatibility cost is one ALLOW key and `extract_claims.py`'s table name.
- **2026-09-18** — Three new occasion kinds (`observed`, `published`, `shipped`), each with a named consumer; `reference` retained but unused for promotion.
- **2026-09-18** — Identity ships in S1 (probe: 0 collisions), before any backfill.
- **2026-09-18** — Approval is inherited: claims parsed from an Alex-approved brief land `approved`; model-extracted claims land `candidate` and go through `/digest`. **Pending Alex.**
- **2026-09-18** — me-model stays local; only `company.metadata.target` enters. **Pending Alex.**
- **2026-09-18** — Build telemetry stays in the rigor layer; build *lessons* enter as `build_retro` claims. Reconciles the measurement tombstone with the dev consumer.
- **2026-09-18** — Backfill runs only through `substrate.py` verbs; there is no separate backfill script.

### 8.3 Pre-mortem — "it's December 18 and this is a regret; why?"

| Failure mode | How it happens | Fix folded into the plan |
|---|---|---|
| **Substrate built but unread** — producers write, no command calls `retrieve.py` | Step 1.7a rewired, but `pre-event-content`/`project-ideation` never get the one-line call; the graph fills and nobody notices | Registry row *retrieval runs = 0 while producers wrote* → weekly; the pack is persisted as a document so absence is queryable; W2's proof is a real run citing a prior claim, not a unit test |
| **Claims pile up unapproved** | Gemini extraction over 90 briefs mints 3k candidates; `/digest` at 12 lines/session never catches up | Inherited approval for reviewed briefs (the bulk); model-extracted candidates capped per run; registry row *candidate age > 14d*; approval rate < 30% → fix the extractor, not the reviewer |
| **Embeddings stale or inconsistent** | a producer writes claims without embedding; someone swaps bge-small for bge-base on the query side | `embed` verb is idempotent and run at the end of every producer + nightly; `EMBED_MODEL` pinned in one module; registry row *null embeddings > 24h*; the `vector(384)` dimension is a hard invariant |
| **Entity resolution never run; the four Elastics return via aliases nobody seeds** | `ensure-entity` creates on miss because the alias table is empty for ATS/inbox spellings | B1 seeds aliases from Notion + the 2b merge-map before B2; every created-this-run entity is flagged in the run report and blocks content surfacing until resolved (ADR-7 R8 generalized); embedding candidates shown at create time |
| **The hub masks the gap again** | trust strip still filters `kind=eq.market`; `observed` rows invisible; a dead producer reads as fine | NEW-6 in W3: producer health from `claim` + all kinds by `source` prefix; liveness row names `post_event:` and `event-deep-research:` explicitly |
| **Backfill drift** — a one-off script writes rows the live producer can't reproduce | exactly the 2b pattern | no script other than `substrate.py`; idempotency proof (`created 0`) required per batch and recorded in the PR |
| **The token budget starves the pack of the one continuity fact** | a 6k budget filled by five verbose book claims | diversity rule (≤3 per source doc), lens weights, series-continuity pull is *unconditional* in the event preset (like today's rank (a)) |
| **PII leaks through claim text** | a transcript quote contains an email/phone or an audience member's name | guard scans `claim_text`/`quote`/`metadata`; audience never becomes `person` (Speaker Map HIGH/MED only); `visibility='private'` default; invariant 6 |
| **DDL applied to the wrong project** | the Supabase MCP now reaches multiple projects | S1/S2 header names the ref; VERIFY block; the selftest's `observed` probe fails loudly on the wrong DB (no `claim` table) |
| **Scope creep to a platform** | new node/edge types "for later" | D7 rule inherited from ADR-8: no table/kind/column without a consumer query in the same increment; this doc lists the consumer for every addition |
| **Two sessions on one checkout** | the 2026-09-12 collision class | one worktree per workstream; `.env` symlinked; ADR-10 number minted from `main` |

---

## 9. Honest uncertainty (confidence + qualifier), what I could not verify, what Alex owns

**Major claims:**
- The claims-first-class / not-events model is the right shape for five lenses — **85%, high**: it is the standard knowledge-graph split (assertion vs occasion vs entity) and it removes yesterday's open `kind` problem outright; the residual is that some consumer wants "claims on the signal feed," which a claims panel on the hub solves without changing the model.
- S1/S2 SQL is valid Postgres and additive on this project — **80%, fairly high**: patterns copied from the applied a5/b1 migrations; unverified details: `norm_name` as a generated column requires IMMUTABLE (declared), HNSW on a nullable column is fine, `alter table ... rename` while `spine_client` still says `doc_claims` breaks any write to it until the ALLOW key is updated (planned same build). **Run the VERIFY block; if anything fails, stop and paste the error.**
- Identity can ship before backfill (no dedup pass needed) — **90%, high**: measured 0 collisions today; Notion titles may still differ from graph names → handled by B1 aliases, not by the unique index.
- Retrieval quality (hybrid + presets) beats today's N=8 Notion pull on the first real run — **75%, moderate**: doc-KB measured 84–88% recall on book chunks; short claims embed well with bge-small in general but this corpus is unmeasured — hence NEW-7 (20-question eval) in W2 before declaring it.
- 4-week appetite to A1 (Oct 17) — **60%, coin-flip-plus**: code volume is modest (two Python scripts, two SQL files, ~10 one-line wirings); risk is approval bandwidth for B3/B6 candidates and Alex's hub change; the one-week cut line is W1+W2 (events + claims + retrieval), which is already the whole of yesterday's value plus the consumption side.
- Reconciling the measurement tombstone with the dev consumer via "numbers stay, lessons enter" — **80%**: consistent with CLAUDE.md's stated intent; it is an interpretation, so it belongs in ADR-10 for Alex to ratify.

**Could not verify (read-only session):** `pg_cron` availability on the project (S3 is optional); total
Notion Events count (estimate 85–95; the B2 manifest prints the truth); whether every Notion People
row's `Role Context` maps to speaker/host for all events (webinars may have no roster → `observed`
event with topic edges only); whether the Supabase MCP connector can apply migrations to this project
under Alex's policy; write timing on the live DB (S1 on ~800 rows should be seconds).

**Decisions Alex owns before Saturday:**
1. **Approve the ADR-10 shape** (claims first-class; documents generalized; three kinds; identity tables) — it changes YED-157's promotion design.
2. **Inherited approval** for brief-derived claims (recommended) vs. everything staged.
3. **me-model boundary**: local side-input (recommended) vs. ingest as `visibility='private'`.
4. **DDL path** (YED-167 policy): paste S1/S2 in the dashboard (the standing rule) **or** allow the
   Supabase MCP `apply_migration` for *Alex-approved DDL only*, REST remaining the sole data-write path.
   My recommendation: allow it for DDL with the ref pinned in the script header — it removes the one
   manual step that has gated every schema change, and DDL is inherently Alex-in-the-loop. Flag: this
   is a policy reversal of the 2026-06-28 "if a Supabase MCP reappears, do not use it" line and needs an
   ADR-10 sentence, not a quiet exception.
5. **The Linear re-shape** in §7.3 (retitle YED-160/47, re-scope 157, seven new issues).
6. **The hub change** (NEW-6) is a second repo/worktree — schedule it or accept the strip stays masked until W3.

**What this document is not:** the PRD (≤1 page + decision log, to be compressed from §0, §1.4, §8, §9),
the ADR (to be minted from `main` as ADR-10 with §1.2/§1.4/§8.1), or code.
