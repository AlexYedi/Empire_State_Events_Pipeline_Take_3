# Inbox Intelligence Miner — v1 (Company/Product Signals)

## Context

Alex's Gmail inbox is a high-value, under-utilized data source. Today exactly **one thin pipe**
connects it to the pipeline: `label:Content/newsletters` → Notion Topics, via `trend-radar` /
`/morning-refresh`. Everything else — event invites (Lu.ma/Partiful/Meetup/aggregators), job
opportunities & offers, and direct-from-company product-update/development signals — arrives, gets
skimmed manually, and decays. Noise (high-frequency promotional senders) buries the signal.

**Goal:** turn the inbox into a first-class, structured ingestion source for the Market-Intelligence
graph and the downstream pipelines, and bring order to the channel. **The load-bearing insight that
makes this cheap:** in the MI graph *a signal is just an `event` row* (with a source citation) linked
to companies/people/topics via the `event_entity` hyperedge — so an email-mined signal needs **zero
new tables**. The work is a **read → classify → route into existing rails** layer, not a new database.

**v1 scope (Alex's steer):** build the **company/product-signal** route first (it extends the proven
`/morning-refresh` pattern), while the whole-inbox scan *also* classifies and **auto-labels** events /
jobs / offers so nothing is lost — those routes are wired in later phases. Plus the sender-hygiene
byproduct (unsubscribe candidates).

## Decisions (locked with Alex)

1. **First stream:** Company/product signals → MI graph (+ Notion Companies `Recent Developments`).
2. **Inbox order:** **Auto-label in Gmail** (scope expansion authorized). Labels double as the
   idempotency key (`Pipeline/processed`) so mail is never re-processed.
3. **Trigger:** **Morning cron**, target end-state — auto-write-then-review (after-the-fact morning
   digest), matching `/morning-refresh`. **Preceded by a short manual, approve-before-write shakedown**
   to prove classifier precision on the broad PII-bearing scan. Mechanism = **local `launchd` invoking
   `claude` headless** (runs on subscription); cloud routines only if billing-to-subscription confirmed.
4. **Scan scope:** **Whole inbox minus a denylist.** Broadest coverage → PII/denylist guardrails are
   first-class (Alex flagged aware of the SEC/YED-81 intersection).
5. **Execution environment:** a **git worktree** (multiple threads live in this repo — the shared-
   checkout hazard). `.env` symlinked in (worktrees start empty of it).

## Architecture

A new **`/scan-inbox` command + `inbox-miner` skill** following the `scan-*` digest→approve template.

Flow (parent-thread orchestrated; per SDK constraint + the "MCP writes must be parent-thread" rule,
Gmail + Notion + Supabase calls run **inline in the parent**, subagents only distill text):

1. **Denylist check → scoped pull.** Load `inbox-denylist` (private senders/domains/labels). Pull
   whole inbox minus denylist for the window via `mcp__claude_ai_Gmail__search_threads` →
   `get_thread` (reuse `trend-radar` SKILL Step 1c). Skip anything already carrying `Pipeline/processed`.
2. **Distill (subagent).** Hand raw thread text to a distill subagent (reuse `/morning-refresh`'s
   subagent-distills-HTML pattern) → structured items, keeping bodies out of parent context.
3. **Classify** each thread → `company_signal` | `event` | `job` | `offer` | `newsletter`(skip — already
   handled) | `personal/noise`.
4. **Route (v1 = company_signal only):**
   - Upsert `company` / `topic` on `lower(name)` (`Prefer: resolution=merge-duplicates`); `person`
     read-before-write, **never fuzzy-merge**.
   - Insert signal `event` (`kind` from taxonomy — `market` / `launch` / `exec_move`; `source:"inbox_miner:…"`;
     mandatory `url` + `metadata.sources`; `confidence` 0–1; leave `relevance_score` 0).
   - Link `event_entity` rows `(event_id, entity_type, entity_id, role)`.
   - Append to Notion Companies `Recent Developments` (dedup rules #10/#11) and/or Topics `Current Events`.
5. **Capture-not-route** for `event` / `job` / `offer`: auto-label (`Pipeline/event`, `Pipeline/job`,
   `Pipeline/offer`) so they're captured for the later phases; surfaced in the digest as "detected, not
   yet routed."
6. **Auto-label** every classified thread + `Pipeline/processed`; tag high-frequency senders
   `Pipeline/unsubscribe-candidate`.
7. **Digest + hygiene table.** v1 (manual): present classified digest + sender-frequency → unsubscribe
   worksheet, write only approved. Cron (later): auto-write append-only, report all writes in the
   morning digest.

**Guardrails (SEC / ADR / playbook):** denylist checked first; `person.email` and any PII kept **off
anon-exposed `signal_read` views** (ADR-1/2); **no PII in logs** (migration-playbook); the pipeline
writes as `service_role` (bypasses RLS) so it must stay scoped to the `public` producer tables it
already writes — no intelligence-schema writes. Graph write is **additive, never a gate** — skip with a
logged notice if `SUPABASE_API_KEY` is unset; **never** the Supabase MCP.

## Files

**New**
- `.claude/commands/scan-inbox.md` — orchestrator (follow the 7-step `command-orchestration-convention`).
- `.claude/skills/inbox-miner/SKILL.md` + `references/` — classifier taxonomy, label map, routing rules,
  denylist policy.
- `.claude/references/inbox-denylist.md` — private senders / domains / labels (draft from a sender scan,
  Alex reviews).
- `docs/adr/ADR-7-*.md` — email-signal source governance + Gmail write-scope expansion (+ any new signal
  `kind`). Append-only per ADR practice.
- *(optional)* `.claude/scripts/inbox_signal_write.py` — REST client reusing the `recompute_relevance.py`
  pattern, if inline REST gets unwieldy.

**Reuse (build on, not beside)**
- `.claude/skills/trend-radar/SKILL.md` Step 1c — Gmail pull pattern (note nested-label gotcha).
- `.claude/commands/morning-refresh.md` — subagent-distill + auto-write-then-review pattern.
- `.claude/scripts/recompute_relevance.py` — canonical REST client (base URL, headers, `.env` read).
- `.claude/references/market-intel-spine.md` + `market-intel-schema.sql` — the signal contract.
- `.claude/references/signal-taxonomy.md` — canonical topic slugs (prevents graph fragmentation).
- `.claude/commands/scan-trends.md` / `scan-roles.md` — digest→approve HITL template.
- Notion Companies `d5910dc3-8327-4b49-9294-fc9499709a98` / Topics `d61ce9df-94b3-4637-aa09-d77e09ab3a74`.

**Gmail write scope — verify first:** the deferred tool list exposes `create_label`, `label_thread`,
`label_message`, `update_message_labels`, but `trend-radar` notes the connector as read-only. **Test a
label write early** (Phase 1); if the OAuth scope blocks it, fall back to a self-maintained
processed-message-id ledger for dedup and treat in-Gmail labeling as a follow-up.

## Phases

- **Phase 0 — Spec & guardrails (PRD-first, per DoD):** ChatPRD one-pager → mirror to Notion; open Linear
  issue(s); draft ADR-7; draft denylist v1; adversarial pass (`alex:cto-principal-architect` /
  `alex:risk-playbooks`).
- **Phase 1 — Read + classify + hygiene, manual, no graph writes:** whole-inbox-minus-denylist scan →
  classified digest + unsubscribe worksheet; verify Gmail label-write scope. Proves precision safely.
- **Phase 2 — Route company signals + auto-label, manual approve-before-write:** wire company_signal →
  MI graph + Notion; auto-label all classes + `Pipeline/processed`; idempotency proven on a 2nd run.
- **Phase 3 — Flip on the morning cron:** local `launchd` → `claude` headless, `.env` loaded, auto-write-
  then-review + morning digest. (Confirm subscription billing of the mechanism before enabling.)
- **Later (separate builds):** wire event route (→ event pipeline intake, own dedup key since no GCal id);
  job/offer route (→ Roles DB + **new offer schema** — offers have no home today); learned relevance.

## Verification (end-to-end)

1. **Classification dry-run** on a known week of mail; eyeball precision/recall per class.
2. **One company-signal end-to-end:** email → `event` row (verify via REST `GET /event`) → `event_entity`
   edge → Notion Companies `Recent Developments` append.
3. **Idempotency:** run twice; `Pipeline/processed` prevents re-writes.
4. **Denylist:** a known private sender is excluded from the scan.
5. **PII:** confirm no `person.email` appears in any anon-exposed `signal_read` view; no PII in logs.
6. **Label-write scope** confirmed (or ledger fallback engaged).
7. **Cron:** manual `launchd`-style headless invocation sees `.env` and completes a full run; morning
   digest renders.
8. **DoD close:** `/dod-close` with met/waived per item.

## Execution setup (step 0, at exit-from-plan)

- Create worktree (branch `feat/inbox-miner`) via `EnterWorktree`.
- **Symlink `.env`** from the main checkout into the worktree (Supabase/Gmail/judge calls no-op without it).
- Confirm `SUPABASE_API_KEY` resolves inside the worktree before any write step.
