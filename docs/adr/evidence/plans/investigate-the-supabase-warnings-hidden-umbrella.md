# Plan — Investigate & Resolve Supabase Advisor Warnings (Hub DB)

## Context

The Supabase dashboard surfaces **Advisor lints** (Security + Performance advisors) for a project. Alex wants these investigated for the **Hub database** (`GTM_OS_HUB`, ref `nnywrmetdoixdbevvsvf` — the `learning` schema / GTM University data plane, the one live, actively-built DB), each warning classified **benign vs. real**, prioritized, and turned into a remediation plan. Scope excludes the retiring spine (`abkvgihlbwfloentugtd`, YED-130) and the out-of-repo Empire canonical graph (different account).

Two facts shape the plan:
1. **The live Advisor list cannot be pulled from this session** — Supabase here is REST-CRUD only (`lib/supabase/*.ts`), the Supabase MCP is retired, and there's no psql/`get_advisors` path. **Alex will paste the actual Advisor findings**; this plan pre-triages every finding predictable from the SQL and gives a disposition rule for anything else.
2. **Hub migrations are the source of truth for its DB** (kept in sync via `supabase db push`, per `docs/GTM_UNIVERSITY.md`) — unlike the spine, there's no migration/live drift here. Fixes land as a new migration file.

All file paths below are in **`/Users/sameoldexpressions/Documents/GitHub/gtm-os-hub`**.

## Predicted findings & triage (Hub)

Derived from `supabase/migrations/0001`–`0004`. **The 3 CRITICAL items Alex surfaced are confirmed** (dashboard screenshots) = exactly the predicted DEFINER views (row 2). Extend against the rest of the pasted list.

| # | Advisor finding | Object(s) | Severity | Verdict | Action |
|---|---|---|---|---|---|
| 1 | `function_search_path_mutable` | `learning.uuid_generate_v7()` (0001 L8), `learning.set_updated_at()` (0001 L21) | WARN | **REAL — fix** | Add `SET search_path` + fully-qualify body calls. One migration. **P1** |
| 2 | `security_definer_view` | `public.v_public_curriculum` (0002 L77), `public.v_public_progress` (0002 L82), `public.v_public_submissions` (0002 L91) | **CRITICAL** (confirmed) | **True-positive detection, BENIGN for this design** | Do NOT flip to `security_invoker`. Document rationale (ADR/ARCHITECTURE) + dismiss in dashboard + light hardening. **P3** |
| 3 | `rls_enabled_no_policy` (INFO) | any `learning.*` table w/o policy | INFO | **BENIGN** | `learner`/`unit_progress`/`submission`/`time_entry`/`curriculum_unit` all have policies (0001 L122–133); INFO-only if it appears. No action. |
| 4 | Auth advisors (leaked-password protection off, MFA options, OTP expiry) | project auth config | WARN | **REAL-ish — config** | Dashboard toggles; cheap. Enable if flagged. **P2** |
| 5 | `extension_in_public` / `unindexed_foreign_keys` / `unused_index` | ext + FK/index | INFO/WARN | **Perf/hygiene** | Assess if flagged; add covering indexes or move extension. **P4** |

### Why the 3 CRITICALs are benign-by-design (the load-bearing call)

Supabase flags any SECURITY DEFINER view as CRITICAL because such a view runs with the **owner's** (here `postgres`) permissions and bypasses RLS. That detection is correct — but here it is **intentional and the safer of the available designs**:

- **The views are the deliberate anon window.** Anon has **no** grant on `learning.*` (no schema USAGE, no table SELECT). Anon reads only the three narrow, explicit-column, PII-free `public.v_public_*` views. DEFINER semantics are *required* for that to return rows.
- **Supabase's suggested fix (`security_invoker=true`) makes it WORSE.** Invoker views run as anon, so to keep them working you must `GRANT SELECT` on `learning.*` base tables to anon + add RLS policies — giving anon **direct base-table access** and column-level PII exposure on any "public" row. That enlarges the attack surface and weakens the PII contract. Net: flipping the property to satisfy the linter is a security *downgrade*.
- **The PII boundary is the view definitions** (`v_public_progress` → `handle` only; `v_public_submissions` → `where is_public = true`; explicit column lists, no `select *`), backed by the `§0 PII contract` in `ARCHITECTURE.md`.

**Residual risk to close (P3 hardening):** because the views bypass RLS, a *future* edit that adds a PII column to a `v_public_*` view (or a `select *`) would leak with no RLS backstop. Mitigate by: (a) confirm all three use explicit column lists (they do), and (b) add a **DB-level** assertion test that selects from each `v_public_*` and fails if any PII column name appears — don't rely solely on the app-layer `lib/public-safety.test.ts`, which guards egress, not the view schema. Optional defense-in-depth: re-own the views under a dedicated low-privilege role instead of `postgres` (narrows what the bypass can reach; does **not** clear the lint).

## Approach

### Step 0 — Reconcile the pasted list (start here)
Map each finding Alex pastes to the triage table above. For any finding not predicted, classify with the disposition rule: *config/perf/real → remediate; "by design" (DEFINER views, deny-all RLS) → document + dismiss; never flip a control that the PII contract depends on.*

### Step 1 — P1 fix: mutable function search_path (the only code change)
Create **`supabase/migrations/0005_advisor_hardening.sql`** that `CREATE OR REPLACE`s the two `learning.*` functions with a pinned search path. Reuse the exact current bodies from `0001_learning_init.sql` (L8 `uuid_generate_v7`, L21 `set_updated_at`); the only additions are:
- `... SET search_path = ''` (empty is safest per Supabase guidance), and
- fully-qualify every call in each body (`pg_catalog.now()`, and for `uuid_generate_v7` qualify `gen_random_bytes`/any helper to its real schema — check the body when editing).

Note: `public.uni_*` RPCs (0003/0004) already set `search_path = learning, public` — leave them alone. This migration touches only the two `learning.*` helpers.

Apply via `supabase db push` (or SQL editor, then commit the migration so repo stays authoritative).

### Step 2 — P2: auth config (only if flagged)
For each auth advisor Alex pastes: enable leaked-password protection, add MFA option(s), tighten OTP expiry — Supabase Dashboard → Authentication → Providers/Policies. Dashboard-only; not code.

### Step 3 — P3: the 3 CRITICALs — document, harden, then dismiss
1. **Document the ADR.** Add a short **"Advisor exceptions"** subsection to `ARCHITECTURE.md` (near `§0 PII contract`) recording: the 3 `security_definer_view` CRITICALs (and any `rls_enabled_no_policy` INFO) are accepted-by-design; the full rationale from the triage above (DEFINER required for the anon window; `security_invoker` is a *downgrade*; explicit-column view defs are the PII boundary); and that flipping to `security_invoker` is explicitly prohibited.
2. **Harden the residual risk.** Add a DB-level test that queries each `public.v_public_*` view and asserts the returned column set contains no PII column names (email, linkedin, auth_user_id, etc.) — this is the real backstop for the RLS-bypass. Keep it alongside `lib/public-safety.test.ts` but assert against the DB, not the app layer.
3. **Dismiss with rationale.** Acknowledge/dismiss the 3 lints in the Supabase Advisor UI (Security Advisor → each finding → dismiss, with a one-line reason pointing at the ADR) so the dashboard goes clean and future *real* findings aren't buried under known-benign noise.

### Step 4 — P4: perf/hygiene (only if flagged)
Add covering indexes for any `unindexed_foreign_keys`; move any `extension_in_public` to the `extensions` schema; drop confirmed `unused_index`. Bundle into `0005_advisor_hardening.sql` or a `0006_`.

## Critical files
- **New:** `supabase/migrations/0005_advisor_hardening.sql` — the function search_path fix (+ optional indexes).
- **Edit:** `ARCHITECTURE.md` — add "Advisor exceptions" subsection under `§0`.
- **Reference (do not edit):** `supabase/migrations/0001_learning_init.sql` (function bodies to copy), `0002_learning_views.sql` (view defs — confirm PII-free), `lib/public-safety.test.ts` (the compensating-control test).

## Verification
1. **Functions:** after `db push`, in SQL editor `SELECT learning.uuid_generate_v7();` returns a uuid; `UPDATE` a `learning.*` row and confirm `updated_at` advances (trigger fires) → proves the pinned search_path didn't break the bodies.
2. **Public reads intact:** `curl` `v_public_curriculum`/`v_public_progress` with the **publishable/anon** key → still returns rows (confirms DEFINER views + dismissal unchanged). Or load `/university` on the Hub.
3. **Advisor re-run:** Dashboard → Advisors → re-run. Expect: function warnings **cleared**; the 3 DEFINER-view findings **acknowledged/green**; auth findings cleared if Step 2 done.
4. **Test guard:** `npm test` (or the runner) → `lib/public-safety.test.ts` still green.
5. **Repo/DB parity:** confirm `0005` is committed so `supabase/migrations/` still equals the live Hub DB.

## Out of scope
- Spine (`abkvgihlbwfloentugtd`) — retiring per YED-130; its advisor warnings (same two classes) are low-value. Note only.
- Empire canonical graph (`oicikjyzmxqfomrrqkvf`) — separate account, Empire pipeline repo, outside this session.
- Linear: consider a small issue under the Roadmap project to track the fix (per source-of-truth discipline) — not created here (plan mode).
