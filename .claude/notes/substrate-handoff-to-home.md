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

## Home session replies (2026-09-18)

- `NOTE` YED-131 / `market-intel-spine.md:49` → **APPLIED 2026-09-18** in `market-intel-spine.md` §Relevance lifecycle (points at YED-131 as v1; v2 extensions deferred until ≥20 outcome rows). Linear body note on YED-131 → Linear-side, handled by the Linear thread.
- `EDIT` memory `project_supabase_mcp_canonical_2026-09-17.md` → **APPLIED 2026-09-18** (pointer rewritten: read-only inspection; DDL reversal declined; YED-167 = glossary + health review).
- `NOTE` KILL→MERGE corrections (YED-104 T1, `market-intel-backfill.md`, Content-Pipeline-v2 artifact schemas → MERGE into substrate issues) → **ACCEPTED 2026-09-18**; will be applied as verbs in triage batch 1 (pre-triage table).
- All `RETITLE` / `CREATE` / `RE-SCOPE` / `MOVE` requests (YED-160, ADR-10 issue, substrate.py, retrieve.py, backfill, A/B, YED-157, YED-47, YED-126/162 blockedBy) → **Linear-side; per Alex 2026-09-18 Linear writes are being handled in the hackathon-prep thread, not here.** Not applied by the home session; listed in the home session's Linear hand-off below.
- ADR-8 "Increment 2" collision → **APPLIED 2026-09-18** as ADR-8 Amendment 3 (skills/agents/outcomes graph = Increment 4). YED-163 retitle → Linear-side.

## Home session replies, round 2 (2026-09-18, later) — Linear-side now applied (Alex: "execute everything listed, skip the gtm-OS migration")

- `RETITLE` YED-160 → **APPLIED** (title + Step 3.8a–c + YED-108 credit fixed + four notes linked).
- `CREATE` ADR-10 issue → **APPLIED as YED-168** (MI Engine · M4 · In Progress).
- `CREATE` substrate.py → **APPLIED as YED-169** (child of YED-160).
- `CREATE` retrieve.py → **APPLIED as YED-170**.
- `CREATE` backfill → **APPLIED as YED-171** (blockedBy YED-169, YED-168).
- `CREATE` Output A/B → **APPLIED as YED-172** (due 2026-09-26; blockedBy YED-170, YED-171).
- `RE-SCOPE` YED-157 → **APPLIED** (Backlog, blockedBy YED-160, parent removed — YED-118 closed Done).
- `MOVE` YED-47 → **APPLIED** (M4, retitled "Identity layer — … (S1b)").
- `NOTE` YED-131 body → **APPLIED**.
- `NOTE` YED-126 / YED-162 blockedBy retrieval → **APPLIED** (blockedBy YED-170).
- Home Step B Linear rulings → **APPLIED**: YED-163 retitled to Increment 4; YED-118 closed Done with a close-out comment; labels `parked` + `decision` created; `project-eval-harness` + the four Devin-playbook labels retired.
- **NOT applied here by design:** gtm-OS Hub issues → `GTM-OS` team (the hackathon-prep thread owns it).
