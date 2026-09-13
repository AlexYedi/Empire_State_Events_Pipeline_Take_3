# SEC — the PII boundary contract + write-path enforcement

> **Linear:** YED-81 · **Date:** 2026-09-13 · **Owner:** Alex · **Status:** draft — awaiting 3 decisions (§10)
> · **Appetite:** 3–7d · **Backfilled?** no · **Mirrors:** ChatPRD (project Empire State) · Notion Project Ideas · ADR-9 (Proposed)

## 1. Problem & why now

The pipeline has **no mechanical PII control**. Diagnosis on `main` (2026-09-13):
- **No chokepoint.** Supabase writes go through six copy-pasted REST helpers (`inbox_signal_write`, `backfill_people`, `merge_topics`, `recompute_relevance`, `match_topic`, `dockb_common.supa`) plus prose-instructed `curl` in `trend-radar`, `/morning-refresh`, `/interview-prep`, `/event-deep-research`. A guard has nowhere to live.
- **`person.email` is stored and read by nothing.** `backfill_people.py` writes it; the hub only *counts* people (`EntityCountsSchema` models no names/emails); no command selects it. Pure liability, zero value.
- **The denylist is a rule that cannot enforce itself.** `inbox-denylist.md` calls itself "the primary PII/SEC control (YED-81)"; `inbox_signal_write.py` never reads it.
- **The hub is safe by absence, not by check.** Every data client is `server-only`, no `NEXT_PUBLIC_` usage, People are counted not modeled — all good — but one future `email: z.string()` would silently break it, and `replay.ts`'s "PII-scrubbed" is a comment.

**Why now.** Roadmap v2 Phase 1 adds the richest personal-data producer the pipeline will ever have — YED-160, transcripts naming people — and Phase 0 opens the whole-inbox scan (YED-161). Both are blocked on this by design.

**Press release.** *Every row the engine writes passes a PII guard that cannot be skipped, and the public hub is proven — not promised — to carry no contact data.* Would anyone care: a hiring manager evaluating "a self-improving intelligence engine" asks exactly this question first.

## 2. Goals / Non-goals

**Goals.** G1 one PII boundary contract, three tiers, recorded as **ADR-9**. G2 **one** Supabase write chokepoint with a **hard-fail** guard + self-test, adopted by every writer. G3 hub public-safety proven by a script that fails `npm run check`. G4 the Notion People write convention codified (gotchas convention *n*).

**Non-goals (hard).** Not a security program: no auth changes (YED-76), no secret rotation, no client-bundle scan (that is YED-82's launch gate). No retention automation/TTLs — v1 retention = *never-enters* + explicit tiers; TTLs are a future ADR. No HubSpot changes (already gated + create-once; the contract only states it is one-way). Not the scan-side denylist logic (YED-161 owns it; this adds the write-side backstop). No changes to read paths.

## 3. Solution sketch + alternatives considered

**Sketch.**
1. **ADR-9 — three tiers.** *Tier 0 — never enters:* anything matching the inbox denylist. *Tier 1 — Notion (private review surface):* may hold contact PII (Email · Phone · Notes) **only from Alex-provided input, never from research/scrape**. *Tier 2 — the MI spine:* professional-public identity only — `name · title · company_id · linkedin_url · bio/role_context` (free text scanned) — **email and phone never**. *Tier 3 — hub / public:* aggregates and public-figure context only; no person rows. *HubSpot:* the CRM; one-way from the gated post-event step; never read back into tier 2 or 3.
2. **`.claude/scripts/spine_client.py`** — `load_key()`, `req()`, and `guard(table, row)`: per-table column allowlist · email/phone pattern scan over **every string, recursively through JSON** · denylist domain check on `event.source` / `url` / `metadata` for inbox-sourced rows · raises `PIIViolation` (exit 2), **never advisory** · `--selftest` with positive/negative fixtures (the `build_graph.py` convention). All six writers import it. A `spine_write.py` CLI so commands/skills stop hand-rolling curl for writes.
3. **Hub `scripts/verify-public-safe.mjs`** — scans `src/lib/**` Zod schemas and `src/data/**` for forbidden field names on person shapes (`email`, `phone*`, `notes`) and email/phone literals; wired into `npm run check`; exits non-zero. Source-level in v1; bundle-level stays with YED-82.
4. **Notion convention (n)** in `notion-write-gotchas.md` + `backfill_people.py` and `/post-event-content` Step 3.8 stop writing Email; one-time REST `PATCH /person?email=not.is.null` → `{"email": null}` once ADR-9 is accepted (rows exported to a gitignored file first).

**Alternatives weighed.**
- *Postgres-side enforcement* (drop the column / CHECK / trigger) — rejected for v1: needs DDL by Alex in the dashboard and covers neither Notion nor the denylist. **Recommended as Phase-2 hardening** — a constraint can't be bypassed by a rogue script (§8).
- *Keep email, hide it* (RLS/encryption) — rejected: no consumer needs it; the simplest safe state is not storing it.
- *Advisory guard, ADR-8 style* — rejected: PII is the one place a warning is the wrong design; an unread warning is Shifting the Burden.
- *Wrap only the new producer (YED-160)* — rejected: leaves five existing writers unguarded; the chokepoint **is** the point.

## 4. Leverage & systems check

- **Leverage point:** #5 *rules of the system* placed at a #6 *information flow* — one rule at the single point every write passes. **Direction check:** fewer PII fields stored, not more controls layered on top of the same data.
- **Shifting the Burden** guarded: the literal pattern here was a comment ("PII-scrubbed") standing in for a check. **Rule-beating** guarded: a producer stuffing PII into `metadata` JSON to dodge the column allowlist → the guard scans JSON recursively; a script copy-pasting `req()` again → a repo check (ADR-8 finding class) flags any `rest/v1` writer outside `spine_client`.

## 5. Rabbit holes + pre-mortem

**Rabbit holes.** (a) Pattern false positives on bios (a public talk quote containing "email me at…") — v1 *refuses*, with the exact field named; no in-run override flag, so automation can never route around it. (b) Migrating six writers drifts behavior (30s vs 60s timeouts; `dockb` raises where others return) — preserve both semantics behind explicit parameters. (c) Hub scan over-matching prose copy ("email" on the About page) — scan schemas + data files only, never `.tsx` copy.

**Pre-mortem — six weeks later this is a regret because…** (1) a new script copy-pasted `req()` again → the repo check makes that a blocking finding at session start. (2) the guard refused a legitimate write mid post-event run and got disabled → the refusal names field · tier rule · fix, and `spine_write.py --dry-run` exists. (3) the email-null migration removed something needed → rows exported first; nothing reads the column.

## 6. Success criteria + eval

- **North-star:** **PII-guarded write share** = writes through `spine_client.guard` ÷ all spine writes — the only honest target for a chokepoint is **100%**. **Counter-metric:** guard refusals Alex has to work around per week — sustained >0 means the guard is too tight or a producer is leaking; either is a fix, never a bypass.
- **Value-action-registry rows:** `{guard refusal on a producer run → fix the producer before its next run, never bypass → in-session}` · `{any `rest/v1` writer outside spine_client (repo check) → block the PR → in-session DoD}`.
- **Acceptance criteria (judge-gradeable):**
  - AC1 `spine_client.py --selftest` refuses: an email in `person.email`; an email inside `bio`; a phone inside `metadata`; an inbox row from a denylisted domain — and accepts a clean row.
  - AC2 Repo check: no file under `.claude` except `spine_client.py` defines a REST writer to `rest/v1`; the six writers import it; `trend-radar` / `/morning-refresh` prose points at `spine_write.py`.
  - AC3 `person.email` is null for every row after the migration; `backfill_people.py` and Step 3.8 no longer write Email.
  - AC4 Hub `npm run check` runs `verify-public-safe` and fails on a fixture schema containing `email`; passes on `main`.
  - AC5 ADR-9 Accepted + README row; gotchas convention (n) present.
  - AC6 build-quality judge ≥ 0.70.

## 7. AI-native fields

**Human–AI boundary:** the guard decides mechanically; Alex decides the tiers (ADR-9) and any exception — there is no in-run override. **Failure UX:** refusal = field · tier rule · fix, one line. **Built for the slope:** patterns and per-table allowlists live in one table at the top of the module; a new tier or table is one row. **Living acceptance layer:** the self-test + the repo check, both graded by the judge.

## 8. Build-time details — deferred, not committed

Exact regex set (email; E.164 + US phone) · whether `linkedin_url` stays in tier 2 (default: yes — public professional identifier) · `bio` scanning: refuse vs redact (default: refuse) · timeout unification · **Phase-2: Postgres CHECK/trigger on `person`** · bundle scan (YED-82) · the single PII-pattern hit in hub `replay.ts` (verify; likely a public post URL).

## 9. Invariants this build honors

CLAUDE.md: Supabase via REST, never the MCP · Notion writes parent-thread · HubSpot writes parent-thread + confirmation table · Rules 10/11 dedup · `market-intel-spine.md` (person dedup = name+company, so email was never the key) · ADR-0/1 one graph · **ADR-7** (inbox boundary = tier 0; D5 injection guard) · **ADR-8** (new finding class: rogue writer) · `notion-write-gotchas.md` · git conventions (one worktree per workstream — `esep-yed81`).

## 10. Linear wiring + decision log

**Linear:** YED-81 (this). **Blocks:** YED-160, YED-161. **Relates:** YED-82 (launch gate), YED-47 (identity/provenance — provenance columns are allowed fields), YED-163 (finding class). Milestone: M4 gate.

**Decisions for Alex (the PRD is approved when these are answered):**
1. **Email and phone never enter the spine** — null the existing `person.email` values; stop writing them. *(Recommended: yes — no consumer reads them.)*
2. **Hard-fail guard, not advisory.** *(Recommended: yes.)*
3. **Chokepoint now, DB constraint in Phase 2.** *(Recommended: yes — DDL is a dashboard step for you; the chokepoint covers Notion + denylist too.)*

**Decision log (append-only):**
- `2026-09-13` — three-tier PII boundary proposed (ADR-9); email/phone never in the spine — no consumer reads them — supersedes the implicit "store whatever research finds" behavior of `backfill_people.py`.
- `2026-09-13` — hard-fail guard, not advisory — PII is the one place a warning is the wrong design.
- `2026-09-13` — chokepoint before constraints — Postgres CHECK deferred to Phase 2 (needs DDL; doesn't cover Notion/denylist).
