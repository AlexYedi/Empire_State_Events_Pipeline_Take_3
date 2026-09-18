# Substrate → Home hand-off (append-only)

**What this file is.** The one channel from the Knowledge Substrate workstream to the backlog-reconciliation session. Under the partition ratified 2026-09-18, the **reconciliation session owns every shared namespace** — all Linear writes, `roadmap.md`, `CLAUDE.md`, `linear-convention.md`, memory, proposal headers, `market-intel-spine.md` §Relevance. The **substrate session owns code and new files only**. Anything the substrate needs changed in a shared namespace is appended here as a request; the home session applies it and replies as a Linear comment (or a line below).

**Rules:** append only; never edit an earlier entry. Each request = one line with a verb (`RETITLE`, `CREATE`, `RE-SCOPE`, `BLOCK`, `MOVE`, `EDIT`, `NOTE`) + target + exact change + reason. Mark applied requests by appending `→ APPLIED <date> <where>` on a new line, not by editing.

Sources: `.claude/notes/yed-160-scope-2026-09-17.md` (diagnosis) · `knowledge-substrate-architecture-2026-09-18.md` (design) · `knowledge-substrate-review-2026-09-18.md` (adversarial review) · `substrate-vs-reconciliation-sequencing-2026-09-18.md` (partition + dated plan).

---

## 2026-09-18 — Ratified by Alex (in session)

**Program shape**
- **Parallel under partition** — two worktrees (`esep-wt-substrate`, `esep-wt-home`), one live session each; `main` checkout is reconciliation-role only (merge-and-sync, no building).
- **Reconciliation Step 0 — create a `GTM-OS` Linear team:** Alex creates it in the Linear UI; the home session moves the gtm-OS Hub issues into it.

**Substrate decisions (all four review recommendations adopted)**
1. **Re-sequence to the one-week cut.** Week 1 ships **S1a — additive-only DDL** (new tables/columns; drop-only rollback that stays valid). The mutating identity half (`name_norm` index swap, `entity_alias`, `entity_merge`, table rename) moves to **week 2 as S1b**, behind a twin rehearsal. Rehearse S1a → S2 → rollback on the staging twin `ytfzzsxcxxbejnowmkmk` to exact row counts before anything touches `oicikjyzmxqfomrrqkvf`. **A/B on the next real brief by Fri 2026-09-26** (Step 1.7a N=8 pull vs `retrieve.py` pack, judged).
2. **Drop the `observed` event kind; keep `attended`.** The `source` column distinguishes the live producer from the dead 2b migration. Add `published` only (`shipped` deferred).
3. **Decline the Supabase MCP DDL reversal.** Schema changes stay a dashboard paste that Alex reads top to bottom. The 2026-06-28 rule stands. Revisit only with its own dated ADR + a verified project listing + a named friction from real DDL volume.
4. **`w_use = 0` in every lens preset until ≥20 outcome rows exist.** Keep `artifact_outcome` + `claim_usage` as tables (log from day one). **Cut** the `c:`-token grep, the nightly utility decay, and recompute-v2. **YED-131 stays the v1 recompute** (named friction = P2 hub panels) — this resolves home plan Step B #9 and the review in the same direction.

**Also folded from the review into S1a:** `claim.asserted_at` (recency by assertion date, not ingest date) · `claim_relation` (contradicts / corroborates / supersedes / refines) · unique `(external_ref, version)` + `is_current` on `documents` · the `artifact_outcome` trigger guarded with `drop trigger if exists` · VERIFY rewritten as negative/behavioral assertions.

---

## Requests for the home session (from the substrate program, 2026-09-18)

- `RETITLE` **YED-160** → "Knowledge Substrate W1 — producers: event rows, entities, post-event claims (`/post-event-content` Step 3.8a–c)". Fix two spec bugs in the body: Step **3.9** collides with the steering gate (use 3.8a–c); the YED-108 credit is wrong (gtm-os repo, old spine). Link the four notes above.
- `CREATE` **ADR-10 issue** — "ADR-10: Knowledge Substrate data model (claims first-class, documents generalized, `published` kind, identity deferred to S1b)". Stub minted on `main` 2026-09-18 as Proposed; body authored in the substrate worktree.
- `CREATE` **`substrate.py` producer library** — 4 verbs for W1 (`ensure-entity`, `ensure-event`, `ensure-document`, `stage-claims`); all writes through `spine_client.py`. Resolves the ADR-8 dangling ref for `.claude/scripts/post_event_spine.py` (superseded by `substrate.py`).
- `CREATE` **`retrieve.py` retrieval interface** — one lens (`event`) in W1, replaces `/event-deep-research` Step 1.7a; counting audit line + loud in-session failure when producers wrote but the pack is empty. Resolves the ADR-8 dangling ref for `.claude/scripts/retrieve.py`.
- `CREATE` **Backfill through producers** — 24 absent events (Notion ≥ 2026-08-20) + 5 existing `post_event_brief`s via `ensure-event` / `stage-claims`. Acceptance: dry-run over the **61** `attended` rows = 61 matched / 0 created; live = 24 created; re-run = 0.
- `CREATE` **Output A/B** — next real event's brief run both ways, judged; due 2026-09-26. (Pulls the core question of YED-48 forward from A3.)
- `RE-SCOPE` **YED-157 B3–B5** — `/doc-digest` becomes a generalized `/digest` over all producers; "promotion to event" is superseded (claims point at events, never promoted). Back to Backlog, `blockedBy` the substrate W1 issue.
- `MOVE` **YED-47** (identity/hygiene) M5 → M4, week 2, as **S1b**; retitle "Identity layer — name_norm, entity_alias, entity_merge (S1b)".
- `NOTE` **YED-131** stays v1 (see decision 4); add "v2 (outcome_boost, coverage_penalty) deferred until ≥20 outcome rows" to its body. Edit `market-intel-spine.md:49` to point at YED-131 (home plan Step B #9).
- `NOTE` **YED-126 / YED-162** unchanged in scope; each becomes a *consumer* of `retrieve.py` — add `blockedBy` the retrieval issue.
- `NOTE` **KILL→MERGE corrections for triage:** YED-104 T1 retrieval, `market-intel-backfill.md`, and Content-Pipeline-v2 "artifact schemas" are **absorbed by the substrate** — MERGE into the substrate issues, don't KILL.
- `EDIT` **memory** — `project_supabase_mcp_canonical_2026-09-17.md` says "READ-ONLY until Alex adopts the YED-167 policy." **YED-167 is the Postgres glossary + health review (PR #78), not a policy issue.** Rewrite the pointer: MCP stays read-only inspection; DDL reversal declined 2026-09-18 (decision 3 above).
- `NOTE` **Prioritization-after-cleanup** applies to *new starts*, not to the substrate build already in motion (per the sequencing note — the literal reading would re-create the deferral drag retired 2026-06-11).

---

## Substrate status (2026-09-18, substrate session)

- `NOTE` **Entity backfill LIVE on prod, verified + idempotent** (Alex approved in session). `substrate.py backfill` over 24 manifests: event 105→114 (+9 attended, evidence-confirmed only), person 232→299 (+67), company 189→237 (+48), event_entity 472→567 (+95). Second run: created=0. Every new row is `source='substrate:notion'` (removable by one filter). Newest attended event in the graph: 2026-09-17 (was 2026-08-20). Branch `alex/yed-160-knowledge-substrate` @ `f03f770`+.
- `NOTE` **Attendance is never inferred.** 15 events had no evidence of attendance and got entities only (no `attended` row): Spark 8/26 · AWS Model Eval 8/27 · Remy 9/2 · ER #217 9/8 · AI GTM Connect 9/9 · Clay RevOps 9/9 · ElevenLabs 9/9 · Attio Formulas 9/9 · Sip & Search 9/10 · Attio AE Playbook 9/15 · Beyond Integration 9/15 · Zo 9/15 · Clay livestream 9/16 · Notion Context is King 9/16 · Elastic × Plural 8/25 (confirmed NOT attended). Alex to say which he attended; those get an event row on a re-run.
- `EDIT` **memory** `project_no_event_producer_to_graph_2026-09-17.md` — the "24 absent / no person since 08-06" facts are now stale for the 9 attended events; add a status line pointing here. (Memory is home-owned under the partition.)
- `NOTE` **Pending in the graph:** 46 topic links deferred (topic names not yet pulled — Notion free-plan SQL quota hit; re-run once names are filled); claims + documents wait on S1a (twin Phantom-Test-Case is INACTIVE — Alex to restore; then `supabase/scripts/rehearse_s1a.py`, then Alex pastes 0009).
- `NOTE` **Data-quality flags for Notion/transcripts:** the RevGenius transcript file (`event-transcripts/2026-09-17_Signal-Rich-Action-Poor_RevGenius.md`, uncommitted on main) spells two speakers as the host pronounced them — "Minta Soe" and "Alex Lindell"; Notion (LinkedIn-sourced) has **Mintis Sow** and **Alex Lindahl**. Notion is very likely right; fix the transcript's speaker map before any public use.

## Substrate status, round 2 (2026-09-18, evening)

- `NOTE` **Migrations 0009 (S1a) + 0010 (S2) LIVE on prod** — pasted by Alex in the SQL Editor after a GREEN twin rehearsal (apply · re-paste no-op · verify PASS 27 checks · planted fault caught · S2 smoke · rollback proven to an identical fingerprint). Post-paste `s1a_verify.sql` PASS on prod. Pre-DDL cold export at `~/Documents/esep-exports/2026-09-18/` (outside the repo).
- `NOTE` **Acceptance run — Postgres Tuning (09-16): PASSED.** `stage-claims` → 46 first-hand claims (16 practice · 9 statistic · 8 pitfall · 6 hot_take · 6 learning · 1 thesis; 3 flagged do-not-publish) + 10 speaker links (Ryan Booz); re-run created 0. `retrieve.py --lens event` on a follow-up seed (Ryan Booz · pganalyze · Datadog) → graph=rpc, claims-layer=live, **46 claims kept / 0 cut, 2,650/6,000 tokens**. Claims land `candidate` pending Alex's inherited-approval ruling.
- `NOTE` **Acceptance caught a retrieval defect, fixed:** the "≤3 claims per source" diversity rule starved single-source packs (3 kept / 43 cut at 352 tokens). Now a two-pass fill — diversity first, then depth up to the budget.
- `NOTE` **YED-168 (ADR-10)** can move toward Accepted once the A/B (YED-172, due 09-26) has run — per ADR-10's own status line.
- `NOTE` **load_twin.py group 2** (gtm signal spine) fails: host `abkvgihlbwfloentugtd` no longer resolves — consistent with the pending decommission (YED-135). Drop the group or mark it dead.
- `NOTE` **Remaining claim backfill:** 6 more recent post-event briefs (Shortlist Aug · GTM Leaders Vol.1 · GLM-5.3 · Daytona Sept · LeadDev · RevGenius) + 8 older (May–Jul) — each needs its brief body saved locally, then `stage-claims`. Parser v2 is verified against the Shortlist (founder-showcase) and June formats.
