# Adversarial review — Knowledge Substrate architecture (2026-09-18)

Reviewer: `alex:cto-principal-architect`, against `.claude/notes/knowledge-substrate-architecture-2026-09-18.md` + `.claude/notes/yed-160-scope-2026-09-17.md`. Read-only REST probe; nothing written. This is the DoD "one adversarial pass in writing" for the substrate program.

**Verdict: BUILD WITH NAMED CHANGES — and re-sequence.** Not a rethink. "The model is right and the method is wrong": the plan commits its most irreversible act (in-place DDL on the system of record, with a rollback that expires the same afternoon) on day one, and defers the only evidence the program works to day fourteen at 60% confidence. Invert that and most objections evaporate.

## Independently verified (replicated, not assumed)
- Row counts: company 189 · person 232 · topic 188 · event 105 · event_entity 472 · documents 2 · doc_chunks 305 · doc_claims **0**.
- Identity probe replicates: **0 `name_norm` collisions** (189 companies, 188 topics), 0 null norms, **0 duplicate `linkedin_url`** (150 distinct / 232 people), 0 duplicate `(name_norm, company_id)` pairs. Every unique index in S1 applies cleanly.
- Every index/constraint S1 drops by name exists under that exact name (`company_name_lower_uniq`, `topic_name_lower_uniq`, `event_kind_enum`, `documents_source_type_check`).
- `doc_claims`→`claim` rename blast radius is small: only `spine_client.ALLOW` + `doc-knowledge-base/extract_claims.py`. **The hub does not read `doc_claims`.**
- The hub mask is real: `empire-state-hub/src/lib/market-intel.ts:106` and `:181` filter `kind=eq.market`, comments explicitly excluding `attended`.

## Findings

**1 · BLOCKING — S1 mutates the live SoR in place; rollback expires on first write; not re-runnable; migration gate skipped.**
(a) Not additive: drops 2 unique indexes, renames a live table, drops/re-adds 2 CHECKs, drops a NOT NULL. `migration-playbook.md` move 5 = expand-contract; move 6 = prove rollback on a fresh clone first. ADR-4 decision 2/6 say the same. **The staging twin `ytfzzsxcxxbejnowmkmk` already exists for this and the design never mentions it.**
(b) Rollback is valid only until the first backfill write (~4 hours), then it would drop real data and one statement fails outright.
(c) **Not re-runnable:** Postgres has no `CREATE TRIGGER IF NOT EXISTS`; the unguarded `artifact_outcome_set_updated_at` trigger raises `42710` on a second run and, inside the single transaction, **rolls back the whole re-paste** — ~40 statements appear to succeed then vanish.
(d) VERIFY validates what was added, never what failed to be removed (a second differently-named CHECK still rejecting `observed` reads green); the one behavioral assertion is deferred to after commit.
**Fix (~45 min, Friday night):** cold export → rehearse S1→S2→rollback on the twin to exact row counts → add `drop trigger if exists …` → **split S1a (pure additive, drop-only rollback valid forever) from S1b (the mutating half)** → rewrite VERIFY as negative/behavioral assertions incl. an inline `begin; insert … kind='observed'; rollback;`.

**2 · SHOULD-FIX (must land in S1 or cost a third DDL round) — claim recency computed on ingest date.** `claim` inherits `created_at default now()`; backfilling ~90 briefs + 5 post-event briefs + ~25 retros in W1–W3 stamps everything late-Sept, flattening the recency term exactly when volume makes ranking matter. Also breaks the promised stance-lineage feature. **Fix:** add `asserted_at timestamptz` in S1; populate `coalesce(event.event_date, documents.doc_date, now())`; scorer + decay read it.

**3 · SHOULD-FIX — no claim↔claim edge**, so contradiction / corroboration / supersession are unrepresentable, and all three have named consumers. `pattern-synthesis` is *defined* by opposing theses; `claim_entity.role='contrasts'` links a claim to an entity, not a claim. The same fact from 3 documents = 3 competing rows each accruing its own utility (the strongest quality signal modeled as duplication). Restated stats have no ordering → a stale number can reach a post (CLAUDE.md rule 12). **Fix:** `claim_relation(from_claim_id, to_claim_id, relation in ('contradicts','corroborates','supersedes','refines'), method, confidence)` in S1 + a near-duplicate proposal in the `/digest` gate.

**4 · SHOULD-FIX — `observed` creates a permanent second word for `attended`.** All **61** attended rows carry `notion_page_id`, so B2 tags them and everything new becomes `observed` — every consumer, the recompute, the views and the hub must say `kind in ('attended','observed')` forever. `event.source` already carries the live-vs-dead-producer distinction and NEW-6 already ships that fix. (Also: the Saturday acceptance line says 59 rows; it is **61**.) **Fix:** either drop `observed` and let the trust strip read `source`, or re-kind all 61 in the same transaction. Keep `published`/`shipped` (real consumers, no synonyms).

**5 · SHOULD-FIX (scope discipline) — §5 is learning-to-rank built before there is a training signal, and weighted from day one.** `artifact_outcome` and `claim_usage` start empty, yet lens presets give `content` w_use=.20 and `ideation` w_use=.25. First 3–5 outcomes then dominate every pack — a reinforcing loop seeded with n=3, Success-to-the-Successful on the exact surface where an archetype trap was already diagnosed. No named friction behind `record-usage`'s `c:`-token grep, the nightly decay, or recompute-v2 → the R2 shape Alex's steering bias exists to rule out. **Fix:** keep the two tables (cheap, and capturing usage now is what makes the data exist later); **set `w_use = 0` in every preset until ≥20 outcome rows**; cut the grep mechanism, the decay job and recompute-v2 from the four weeks.

**6 · SHOULD-FIX — nothing in four weeks measures whether the *output* improved; the read path's posture is the atrophy mechanism.** Good news the design undersells: `retrieve.py` replaces a **live** consumer (Step 1.7a already reads the graph with a cost guard and a mandatory audit line). But that step is documented "best-effort … on empty, record `graph: no signals` and continue" — which becomes the mechanism by which a *filled* substrate silently stops being read. The weekly registry row catches a total outage in up to 7 days and a partial one never. And elevation is never measured: the eval that would (YED-48) is scheduled at **Dec 12**. **Fix:** (1) audit line carries counts and "producers wrote for these entities but the pack returned 0 claims" is a **loud in-session failure**, same shape as the Step-4.5 ledger gate; (2) pull a minimum-viable A/B into W2 — next two real events, brief run both ways (N=8 pull vs pack), judged by Alex or the cross-provider quorum. ~1 hour; if the briefs are indistinguishable that is the most valuable thing the program could learn.

**7 · SHOULD-FIX — decline the Supabase MCP DDL reversal.** The 2026-06-28 rule's cause was **mis-targeting a project**, and `apply_migration` takes the project as a parameter; a SQL comment is not a control over a parameter, and VERIFY runs *after* commit (on the wrong DB it returns exactly the green it expects). Benefit is ~4 minutes across two pastes — and the paste is the only step where a human reads the SQL top to bottom, which is what would have caught findings 1(c) and 2. The reviewer's own attempt to verify the connector's reach was **blocked in-session**, so the reversal's precondition is unverified. **Fix:** decline for this program; revisit only with a verified project listing + a named friction from real DDL volume. If taken anyway, it needs **its own dated ADR**, not a sentence inside ADR-10 (playbook move 2: one decision → one ADR).

## Worth knowing
- `documents` has **no uniqueness for our own artifacts** (`documents_external_ref_idx` is non-unique) and "current version" is unqueryable (`supersedes_id` points backward only) → packs can cite superseded briefs. Fix: `unique (external_ref, version) where external_ref is not null` + an `is_current` partial unique index.
- `entity_neighborhood` caps events (60) but **not** claims/documents → multi-MB jsonb over REST post-backfill. Add `max_claims`/`max_docs` and push the diversity rule into SQL.
- Multi-speaker claims are denormalized two ways (`claim.speaker_person_id` vs `claim_entity.role='asserted_by'`) — name one canonical or they drift.
- Entity-less claims may be unreachable if `filter_entity_ids` is passed (kills most `dev`-lens material). Specify: filter off for `dev`, on for `event`/`job`.
- **Saturday hides a dependency:** the B2 manifest builder is ~85–95 Notion fetches with relation expansion in the parent thread, with roster coverage already flagged unverified. Budget it as its own half-day.

## The defended one-week cut line (Sat 09-20 → Fri 09-26)
Prove the whole loop on one narrow slice, both halves, **before** the mutating DDL is committed.
**In:** Fri night cold export + twin rehearsal to exact row counts · **S1a additive only** (claim generalization incl. `asserted_at`, `claim_entity`, `claim_relation`, `document_entity`, documents generalization + unique `(external_ref, version)`, `artifact_outcome` + `claim_usage` as tables, `event_kind_enum += 'published'`) · `substrate.py` with four verbs (`ensure-entity`, `ensure-event`, `ensure-document`, `stage-claims`) · backfill B2 + B3 only (24 events, 5 post-event briefs) · `retrieve.py` one lens (`event`), `w_use=0`, replacing Step 1.7a, counting audit line + hard in-session failure · the A/B on the next real brief.
**Deferred to W2 (= YED-47 S1b):** the **entire identity half** — it carries every mutating statement, and the probe shows 0 collisions with one writer that normalizes and reads-before-writing. The unique index is belt to `substrate.py`'s suspenders; `entity_alias` can be added any time with zero rework.
**Out, with reasons:** the other four lenses (six numbers each once one lens proves out) · `record-usage` / `c:` grep / nightly decay / recompute-v2 (no training signal) · `/digest` generalization (nothing to digest until B6/B7) · B4–B9 · the hub trust-strip change (can stay masked a week) · `shipped` · entity embeddings + `match_entities` · S3/pg_cron.

## What must not be relitigated (reviewer's words)
Claims-as-first-class pointing at events is **load-bearing, not clever** — the standard assertion/occasion/entity reification split; the rejected alternative mints N rows per occasion, conflates "said" with "happened," and corrupts trust-strip semantics. Three node types with D7 enforced. And **"one producer library + one retrieval interface + backfill runs through the producers"** is the best idea in the document: it makes the 2b-migration failure class mechanically impossible rather than merely discouraged.

---

## A/B verdict — YED-172, closed 2026-09-24 (DRAFT, for Alex's edit)

**Ruling: the substrate does NOT replace the legacy Step 1.7a pull. ADR-10 stays Proposed.**

Two events counted, two blind raters each, pre-registered sheet. Apollo GraphQL (09-24, entity-rich): Alex
preferred the substrate on topic-card depth, the Sonnet seat preferred the legacy pull on speaker-named questions
— a split *between raters on one event*, which the rule did not anticipate. AI Builders (09-24, deliberately
thin): **both seats preferred the legacy pull.** The rule required the substrate to be preferred-or-tied on both
events; it was not, so the legacy pull stands. A third event, AI Show and Tell (09-20), was run and then dropped —
Alex did not attend, so he could not honestly score "usable in the room."

**The result is real, and it is also narrower than it looks.** Alex's two preferences split by *event type*, not
randomly: substrate on the event where genuine continuity existed to retrieve, legacy on the event where neither
arm had entity coverage and Notion's hand-curated topic pages simply held more substance than the graph. On that
reading this was partly a **coverage** comparison rather than a **method** comparison — the graph holds claims
extracted from post-event briefs, while Notion topic pages hold depth accumulated by hand over months. That is
interpretation, recorded as such, and deliberately not used to soften the ruling.

**What the experiment actually bought is not the winner.** It is that the two arms are good at different things:
the substrate on **material** (Alex, Apollo: *"topic cards are far stronger"*), the legacy pull on **packaging**
(both seats, both events: speaker-named chase-able questions, dated numerically-specific signals). The legacy
arm's advantage traced to a concrete mechanism — Notion topic pages carry a `Top Questions` property that has been
accumulating for months, and the substrate has no question-shaped claim type to retrieve. That is YED-217
(conditioner aims material at named speakers) and YED-218 (question claim type). Both matter **more** after this
result, not less.

Worth recording separately: **zero errors on all four packs from both seats.** Neither arm padded under thinness,
which was the designed test for event 2.

**Caveats that belong next to the ruling:** n=2 events and 2 raters; event 1 was dropped after being run, changing
the sample mid-experiment; Apollo required a decontamination deviation (a parallel session had written
event-specific research into Notion for that exact event) and AI Builders did not; and the Apollo confounds
favoured the legacy arm on balance — a hand-written keyword list for its market-signal sweep, plus residual
batch-window leakage — so **the legacy win is if anything slightly overstated.**

**Consequences:** graph-write freeze lifts (it was contingent on measurement finishing, not on a verdict) · YED-47
and YED-205 unblock · ADR-10 remains Proposed · the substrate is **re-scoped, not retired** — it stays the
post-event claim store and the job-search/interview lens, and the open question becomes coverage, not method.

Full scorecards, confounds and the rater-correction record: `.claude/evals/logs/2026-09-24-ab-yed172-*.jsonl`.
