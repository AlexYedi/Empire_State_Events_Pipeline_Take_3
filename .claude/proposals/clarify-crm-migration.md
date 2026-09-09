# Plan — Cutover of the pipeline CRM from HubSpot → Clarify

**Status:** DRAFT / cutover plan (2026-09-08). Actionable THIS WEEK. **No writes executed** — this is the plan, not the build.
**Decision made this session:** adopt Clarify (`clarify.ai`) as the capture + CRM layer. Notion stays the durable knowledge graph / system of record. HubSpot goes dormant (fresh, near-empty free account).
**Companion spec:** `.claude/proposals/clarify-integration.md` (the capture lane + §0 API-reality + §3 consolidation decision). This document is the *CRM-write retarget + cutover* half; read both together. **This supersedes** `clarify-integration.md` §3's "OPEN DECISION" — the decision is now made, and §4's 3-value pre-flight is carried forward here as the gate.
**Class of change:** ADR-level (account boundary + post-event data contract). ADR to write = `docs/adr/ADR-6-crm-boundary-clarify.md` (next number; current top is ADR-5).

---

## ⚠️ CORRECTION (2026-09-08 — verified live via HubSpot MCP; supersedes the "near-empty" premise below)

**HubSpot is NOT near-empty.** Live count: **245 contacts + 182 companies** (e.g. Josh Kim/MindStudio, Tanny Kang/Vibranium, Sangavi/The Shortlist) + the event Notes the pipeline attached over months. That is a real book of event relationships. **The "cutover, not migration" framing below was built on a false assumption and is overruled: a real MIGRATION of the HubSpot book into Clarify IS warranted.** See the revised §2. Everything else — the retarget, the §4 adapter, the §1 gate, dedup-against-Clarify's-auto-sync, ADR-6, the rollback posture — stands unchanged; a migration just **adds a one-time programmatic backfill step**, it does not change the target architecture.

---

## 0 — TL;DR (the shape of the week)

This is a **cutover, not a data migration.** HubSpot is a fresh free account with near-zero records, so there is nothing meaningful to bulk-move. The work is:
1. **Verify 3 free-tier unknowns** in-app (credits / retention / export) — the cutover is GATED on these.
2. **Retarget `/post-event-content` Step 5.5** from HubSpot MCP writes to Clarify REST writes, keeping the exact same discipline (selective bar, dedup-first, create-once, human gate, parent-thread only).
3. **Build a thin REST-via-`.env` write adapter** for Clarify (search / create company / create person / add note).
4. **Reconcile against Clarify's already-synced data** — Clarify auto-ingests Alex's Google Calendar + email, so it already holds person + 50+ meeting objects. The write path must dedup against that, or it will double-create.
5. **Leave HubSpot dormant** as a zero-cost fallback; write the ADR.

Confidence the cutover is the right call: **85% (high)** — the switching cost is genuinely near-zero and the value (one system for capture + CRM + AI enrichment, native write API) is real. The 15% doubt is entirely the three unverified free-tier unknowns (§1) and product youth (§7); both are mitigated by Notion-as-record + dormant-HubSpot, neither is load-bearing enough to block.

---

## 1 — Pre-flight verification (the GATE — do this first, in-app)

**Do NOT retarget Step 5.5 until these three are answered.** They are undocumented on Clarify's free tier and determine whether Clarify can be trusted as *any* kind of store. (Carried from `clarify-integration.md` §4.) If any answer is disqualifying, the fallback is: capture lane on Clarify, **CRM write stays on HubSpot** — the pipeline is unharmed either way because Notion is the record.

| # | Unknown | How to verify (in-app, this week) | Disqualifying answer | Confidence we'll pass |
|---|---|---|---|---|
| a | **AI credit ceiling** | Settings → Billing/Usage. Confirm the monthly AI-credit number and current burn. Research says **1,000/mo (~25–30 enriched meetings)**; one source said 2,500 — verify the real number. | < ~15 enriched meetings/mo (would throttle a busy event week) | 80% — CRM *writes* (person/company/note) are cheap; AI credits are spent on meeting *summaries/enrichment*, not on the CRM object creates the pipeline does. Even a low ceiling likely doesn't block the CRM-write path. |
| b | **Retention period** | Settings → Data/Recording. How long are records + meeting data kept on free? | Short auto-expiry (e.g. 30–90 days) on the CRM objects themselves | 60% — genuinely unknown. Mitigated: Notion holds the durable People/Companies knowledge; Clarify is the *live* CRM, not the archive. |
| c | **Data export on free** | Settings → look for CSV/data export, or confirm REST GET returns full records (it does — API is the export path). | No export AND no full REST read (lock-in) | 90% — the REST API already reads full `person`/`company` objects (confirmed GET 200), so export exists de facto via the adapter even if the UI button is gated. |

**Output of this step:** a 3-line note (a / b / c answered) pasted into the ADR's "Consequences" and into the Linear issue. That note is what flips the gate from RED to GREEN.

---

## 2 — Data reconciliation + the 3-system boundary

### The boundary (draw it crisply — this is the whole architecture)

| System | Role | What lives here | Write pattern |
|---|---|---|---|
| **Notion** | **Durable knowledge graph / system of record** (UNCHANGED) | People, Companies, Topics, Events, Content Drafts, Project Ideas — bidirectionally related. Every researched entity. | `/post-event-content` Step 3.8 (`notion-writer`). **Clarify does NOT replace this.** |
| **Clarify** | **Live CRM + capture + relationship/pipeline layer** (NEW target) | Only the *selective* contacts that clear the bar (spoke-with / opt-in target / deliberate pursuit) + the meeting capture Clarify auto-syncs. A working CRM, not a directory. | `/post-event-content` Step 5.5 (retargeted, §3) via REST adapter (§4). |
| **HubSpot** | **Dormant fallback** | Whatever near-empty set exists today. Frozen. | None going forward. Retire criteria in §5. |

**One-line mental model:** *Notion is what Alex knows; Clarify is who Alex is actively working; HubSpot is the parachute he keeps packed but doesn't open.*

### Migrating the HubSpot book (245 contacts / 182 companies + Notes) — REVISED

**Recommendation: MIGRATE it — programmatically, dedup-first.** (Supersedes the earlier SKIP; the "near-empty" premise was false — 245 contacts / 182 companies verified live 2026-09-08.)

Both sides are fully API-accessible, so this is a **scripted one-time backfill, not a CSV project**:
1. **Read HubSpot** via MCP: all contacts (name·email·company·title) + companies + the **Notes attached to each contact** — the Notes carry the "met at [event] [date], discussed X" context. That history is the real payload and is NOT re-derivable by "re-capture on next touch," so it must move.
2. **Dedup/merge against Clarify's auto-synced data** (the real work, per §2 above): for each HubSpot contact, search Clarify `person` by name+email — **EXISTS** (Clarify likely already has them from GCal/email sync) → attach the HubSpot Notes as comments, don't create; **NEW** → create company→person, then attach Notes as comments. Clarify's `merge-records` cleans up any duplicates that slip through.
3. **Batch through the §4 adapter** in company→person→note order. Well under Clarify's 20K-record cap, and **record creation does NOT burn the 1,000 AI-credit ceiling** (credits fund meeting summaries/enrichment, not object creates) — so a 245-contact backfill is effectively free on the free tier.
4. **Gate it:** bulk external write → present a **dedup'd batch summary** (N NEW / M EXISTS-add-note) for Alex's approval + spot-check before running (batch-level confirm, not 245 per-row rows).

**Source-of-truth note:** HubSpot is already CRM-shaped (contact·company·note), so it's the cleaner *migration source* than re-deriving from Notion; the HubSpot **Notes** are the payload worth moving. Notion stays the durable knowledge graph regardless.

**Effort:** ~1–2 hrs scripted (read → dedup → write), gated, reversible (Clarify records deletable; Notion + HubSpot untouched as sources). Confidence this is right now that the data is known: **80%** — 245 real contacts with event Notes is worth keeping live, and the auto-sync dedup is the same discipline the pipeline already enforces.

### Deduping against Clarify's already-synced data (the real reconciliation)

⚠️ **This is the non-obvious risk.** Clarify auto-syncs Alex's Google Calendar + email, so it **already holds `person` records and 50+ `meeting`/calendar objects** before the pipeline writes anything. Naive create = duplicates.

**Rule (encode into the adapter, §4a):** *every* Clarify write is dedup-search-first — the same Rule 11 discipline the HubSpot step used, now pointed at Clarify:
1. Before creating a `person`: search Clarify `person` by name (and email/company when known). Clarify's email sync means many event contacts **already exist** as auto-synced people — match and comment, don't create.
2. Before creating a `company`: search Clarify `company` by name/domain.
3. Meetings are already there (auto-synced) — the pipeline does **not** create meetings; it associates the person to the event via a note/comment, mirroring the HubSpot "Note = event-association mechanism" convention.

**Match classification (unchanged from the HubSpot spec):** `NEW` (no Clarify match → create) vs `EXISTS` (Clarify match → add comment/note only, never field-merge — Rule 6). Surface the classification in the confirmation table before any write.

---

## 3 — Pipeline retarget: `/post-event-content` Step 5.5 → Clarify

**The discipline is IDENTICAL to the HubSpot spec** (`.claude/proposals/post-event-hubspot-step.md`) — only the write destination changes. Preserve verbatim:
- **Selection bar** — a contact qualifies only if: Alex spoke with them in the room, OR they're a named opt-in outreach target (Step 4), OR they're a deliberate pipeline/job-search target. **Default is exclusion.** If the candidate list looks like "the whole roster," that's the failure signal — cut it.
- **Dedup-search-before-create** — now against Clarify `person`/`company` (§2), not HubSpot.
- **Create-once** — NEW → create; EXISTS → add comment/note only, never field-merge.
- **Note = event-association** — `event · date · role · what was discussed · next step`. Via Clarify `add-comment` (MCP) or the REST comment path.
- **Human gate** — the dedup'd confirmation table (person · company · NEW/EXISTS · action · note preview) → Alex approves/edits/skips **per row** before any write. Tier-3 irreversible external write; never auto-fire.
- **Idempotency** — before adding a note, check the person for an existing comment naming this event (no note-spam on re-run).
- **Parent-thread only** — like the Notion/HubSpot MCPs, Clarify writes happen inline in the parent conversation, where the confirmation table renders. (REST-via-`.env` actually sidesteps the subagent-MCP-unavailability constraint, but keep the write inline anyway so the gate and the table stay co-located.)
- **Default skip** — if nobody clears the bar, skip and say so.
- **Showcase reuse** — for founder-showcase events, Step 3.4's contact-extraction already produced the candidate set; reuse it.

### Write order (Clarify object model: `company` → `person` → note)
Mirrors the HubSpot Company → Contact → Note order:
1. **Company** — dedup-search Clarify `company`; create if NEW; capture the returned resource id.
2. **Person** — dedup-search Clarify `person`; create if NEW, associating to the company id from step 1; capture person resource id.
3. **Note** — `add-comment` on the person resource (event · date · role · discussed · next step).

### Confirmed REST path structure (from live probe 2026-09-08)
```
Base:  https://api.clarify.ai/v1/workspaces/<WORKSPACE_SLUG>/objects/<type>/resources
Types: person | company | deal | meeting | task   (all GET 200 confirmed)
Auth:  Authorization: api-key $PERSONAL_CLARIFY_KEY
       X-Clarify-Workspace: $WORKSPACE_SLUG
```
⚠️ **The write path may use the MCP (`create-or-update-records`, `add-comment`) OR REST POST/PATCH.** REST-via-`.env` is recommended (pipeline-native, no relaunch, matches the Supabase precedent). Exact REST write body shapes (POST field names, association syntax) were **not** fully probed this session — see §4 confidence flags; verify against a single dry create during the build, not assumed.

---

## 4 — The write adapter (REST-via-`.env`)

**Env (already present in repo `.env` — verified 2026-09-08):**
```
PERSONAL_CLARIFY_KEY=...          # ⚠️ PERSONAL key. A Workspace key LISTS tools but FAILS every call.
WORKSPACE_SLUG=alex-yedibalian
```
> **Naming reconciliation:** the companion spec `clarify-integration.md` §1 referenced `CLARIFY_API_KEY` / `CLARIFY_WORKSPACE`. The **actual `.env` uses `PERSONAL_CLARIFY_KEY` / `WORKSPACE_SLUG`** — these are the real names; use them. (Fix the companion spec's §1 names in a follow-up doc pass so they don't drift.)
> **Env caveat** (`project_claude_code_env_handoff`): Dock-launched Claude Code does NOT inherit `~/.zshrc`; the repo `.env` is the source (preferred here anyway).

**Convention:** `source .env` (or read the two vars) at the top of each call. All calls are parent-thread. Read-before-write for every create.

### (a) Search person / company by name (dedup — ALWAYS first)
```bash
# Confidence on exact query-param name (name= vs q= vs filter[...]): 55% — VERIFY on first run.
curl -s "https://api.clarify.ai/v1/workspaces/$WORKSPACE_SLUG/objects/person/resources?name=Jane%20Smith" \
  -H "Authorization: api-key $PERSONAL_CLARIFY_KEY" \
  -H "X-Clarify-Workspace: $WORKSPACE_SLUG"
# → parse for an existing match (auto-synced from GCal/email is likely). Match on name + email/company.
# Company dedup is identical with .../objects/company/resources?name=Acme
```
If a match returns → classify **EXISTS**, skip create, go straight to (d) note. Else **NEW** → (b)/(c).

### (b) Create company (only if NEW)
```bash
# POST body shape (attributes wrapper vs flat) is the main unknown — Confidence 50%. Dry-run ONE create first.
curl -s -X POST "https://api.clarify.ai/v1/workspaces/$WORKSPACE_SLUG/objects/company/resources" \
  -H "Authorization: api-key $PERSONAL_CLARIFY_KEY" \
  -H "X-Clarify-Workspace: $WORKSPACE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Acme Corp", "domain": "acme.com" }'
# → capture the returned resource id for the person association in (c).
```

### (c) Create person + associate to company (only if NEW)
```bash
curl -s -X POST "https://api.clarify.ai/v1/workspaces/$WORKSPACE_SLUG/objects/person/resources" \
  -H "Authorization: api-key $PERSONAL_CLARIFY_KEY" \
  -H "X-Clarify-Workspace: $WORKSPACE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Jane Smith", "email": "jane@acme.com", "title": "CTO",
        "company_id": "<company-resource-id-from-b>" }'
# ⚠️ Association field name (company_id vs relationships[...] vs companyRef): Confidence 45% — VERIFY.
# → capture person resource id for the note in (d).
```

### (d) Add note / comment (the event-association mechanism)
```bash
# Prefer the MCP `add-comment` if the Clarify MCP is connected (cleaner). REST comment path shown as fallback:
curl -s -X POST "https://api.clarify.ai/v1/workspaces/$WORKSPACE_SLUG/objects/person/resources/<person-id>/comments" \
  -H "Authorization: api-key $PERSONAL_CLARIFY_KEY" \
  -H "X-Clarify-Workspace: $WORKSPACE_SLUG" \
  -H "Content-Type: application/json" \
  -d '{ "body": "AI Demo Night · 2026-09-10 · CTO · discussed agentic eval harnesses · next: connect + share pipeline post" }'
# ⚠️ Comment endpoint path (/comments sub-resource vs add-comment MCP vs an activity object): Confidence 40% — VERIFY.
# Idempotency: GET existing comments first; skip if one already names this event.
```

**The Personal-key footgun (say it twice):** the key MUST be the **Personal** API key. A Workspace key authenticates enough to *list tools* but **fails every actual call** — a silent, confusing failure mode. If calls 401/403 while the key "looks valid," this is the first thing to check.

**Build note:** the four functions above are ~40 lines of bash or a small Python helper. Wrap them so Step 5.5 calls `clarify_dedup_person`, `clarify_create_company`, `clarify_create_person`, `clarify_add_note`. Keep it in the pipeline, REST-via-`.env`, no new service.

---

## 5 — HubSpot decommission

**Keep it dormant. Do not delete. Costs nothing (free account).**
- **Immediate:** stop all pipeline writes to HubSpot the moment Step 5.5 is retargeted and validated (§8). The HubSpot MCP stays connected but unused.
- **Why keep it:** it's the single-vendor-concentration hedge (§7). If Clarify's free tier disappoints on retention/export (§1) or the product proves too young (§7), the pipeline flips Step 5.5's target back to HubSpot in one edit — zero data loss because Notion is the record.
- **Retire criteria (delete/close HubSpot only when ALL hold):**
  1. Clarify has run as the live CRM for **≥ 60 days** without a retention/export surprise.
  2. The 3 pre-flight unknowns (§1) all resolved non-disqualifying **and stayed that way**.
  3. Alex has *not* needed the HubSpot fallback in that window.
  4. A one-time export of whatever's in HubSpot is archived (CSV to the repo or Drive) before deletion.
- Until all four: **dormant, not deleted.** Revisit at the 60-day mark, not before.

---

## 6 — ADR (`docs/adr/ADR-6-crm-boundary-clarify.md`)

Write this **before** flipping Step 5.5 (DoD item 1 — spec/decision artifact before code). Structure (match the existing ADR-1…5 house style):
- **Title:** ADR-6 — CRM boundary: Clarify as live CRM, Notion as record, HubSpot dormant.
- **Status:** Proposed → Accepted (once §1 gate is GREEN + Alex signs off).
- **Context:** fresh near-empty HubSpot; Clarify adopted as capture layer (`clarify-integration.md`); need one deliberate CRM-write target; ADR-1 established Notion + the data-layer boundaries this refines.
- **Decision:** post-event selective CRM writes go to Clarify (REST-via-`.env`, `company→person→note`, dedup-first, create-once, human-gated); Notion remains system of record; HubSpot dormant fallback.
- **Alternatives considered:** (i) stay on HubSpot — rejected: Clarify unifies capture + CRM + enrichment, HubSpot has zero data lock-in keeping us; (ii) bulk-migrate HubSpot → Clarify — rejected: fresh account, re-capture-on-touch yields better data than importing thin records; (iii) Clarify replaces Notion too — **rejected hard**: Clarify retention/export unverified + youth; Notion's relational knowledge graph is the durable asset.
- **Consequences:** paste the §1 3-value verification result; note the credit ceiling as a watch item; note the retarget touches `/post-event-content` Step 5.5 + adds the §4 adapter; note the HubSpot retire criteria (§5).
- **Reversal:** reversing this ADR = writing ADR-7, not editing ADR-6 (per CLAUDE.md ADR discipline). One-edit rollback path documented in §7.

---

## 7 — Rollback + risks

| Risk | Severity | Mitigation | Rollback |
|---|---|---|---|
| **AI credit ceiling hit in a busy event week** | Med | CRM *writes* are cheap (not AI-credit-metered the way summaries are); §1a verifies. Recording is free/uncapped. | Throttle enrichment, not CRM writes; CRM path keeps working. |
| **Retention/export disappoints (§1b/c)** | Med-High | Notion is the record — Clarify losing data doesn't lose the knowledge graph. §1 gate catches it *before* cutover. | Flip Step 5.5 back to HubSpot (dormant, ready). |
| **Product youth / API instability** (undocumented free-tier behavior, write-body shapes unprobed) | Med | Adapter is 4 thin functions; §4 confidence-flags every unverified write shape → verify on first dry create, don't assume. | HubSpot MCP write path is preserved in git history; revert Step 5.5. |
| **Single-vendor concentration** (capture + CRM both on Clarify) | Med | Notion-as-record + dormant-HubSpot = two independent hedges. Capture lane and CRM lane can be split back apart (capture on Clarify, CRM on HubSpot) without touching Notion. | Independent per-lane rollback. |
| **Duplicate contacts** (Clarify's auto-synced people/companies) | Med | Mandatory dedup-search-first (§2, §4a); classify NEW/EXISTS before any write; the human gate shows the classification. | Merge in Clarify UI; tighten the dedup match key. |
| **Personal-vs-Workspace key footgun** | Low | Documented twice (§4); first thing to check on any 401/403. | Swap key. |
| **Wrong-person note** | Low | Confirmation table shows note preview + resolved company before write; garbled names web-verified upstream. | Per-row skip at the gate. |

**Overall rollback posture:** because Notion is the record and HubSpot stays dormant, **every failure mode has a one-edit rollback** (repoint Step 5.5) with zero knowledge loss. This is what makes the cutover safe to do this week rather than after a long trial.

---

## 8 — This-week ordered checklist

Each item small and doable. Gate items marked 🔴 must pass before the item after them.

1. **[Verify]** 🔴 In-app: read the 3 pre-flight values — (a) AI credit ceiling, (b) retention period, (c) export availability (§1). Write the 3-line result down. *~15 min.*
2. **[Gate]** 🔴 If any value is disqualifying → STOP the CRM retarget; keep CRM on HubSpot, capture on Clarify; note why and revisit. If all clear → proceed. *Decision, ~2 min.*
3. **[Smoke test]** Confirm the REST connection live: `GET .../objects/person/resources` with `PERSONAL_CLARIFY_KEY` + `WORKSPACE_SLUG` → expect 200 + see the auto-synced people. Confirms key type + slug. *~5 min.*
4. **[Probe writes]** Do ONE dry `company` create + ONE `person` create + ONE comment against a throwaway/test name to nail the unverified body shapes in §4b/c/d (association field, comment path). Delete the test records after. *~20 min — this resolves the 40–55% confidence flags.*
5. **[ADR]** Write `docs/adr/ADR-6-crm-boundary-clarify.md` (§6), pasting the step-1 verification result into Consequences. *DoD item 1 — before code. ~20 min.*
6. **[Linear]** Open a Linear issue for the retarget workstream (DoD item 2); link the ADR + this plan. *~5 min.*
7. **[Adapter]** Build the 4 REST functions (§4a–d) as a small helper; test each against the probe results from step 4. *~45 min.*
8. **[Retarget]** Edit `/post-event-content` Step 5.5: swap HubSpot MCP calls for the Clarify adapter, preserving the selection bar / dedup / create-once / human-gate / idempotency verbatim (§3). Update `.claude/proposals/post-event-hubspot-step.md` or supersede it with a Clarify note. *~30 min.*
9. **[Validate end-to-end]** Run `/post-event-content` on the next real event (or a recent one), confirm: candidate bar excludes the roster, dedup catches Clarify's auto-synced people, the confirmation table renders, an approved row writes company→person→note correctly, re-run doesn't note-spam. *The real test.*
10. **[Backfill]** 🔴 **Migrate the HubSpot book** (245 contacts / 182 companies + Notes) into Clarify — §2 REVISED. **Sequenced AFTER step 9** proves the adapter on a live event (trust the write path before running 245). Script: read HubSpot via MCP (contacts + companies + each contact's Notes) → dedup-search each against Clarify `person`/`company` → classify NEW vs EXISTS → present a **batch summary** (N NEW · M EXISTS-add-note) for Alex's approval + spot-check → on approval, batch-write `company→person→note` via the §4 adapter (**EXISTS → attach the HubSpot Note as a comment only, never field-merge; NEW → create then note**). Record-creates don't burn the AI-credit ceiling; well under the 20K-record cap. Fully reversible (Clarify records deletable; HubSpot + Notion untouched as sources). *~1–2 hrs, batch-gated.*
11. **[Decommission]** Flip HubSpot to dormant (stop writes) — now that BOTH the live pipeline (step 9) and the historical book (step 10) are in Clarify. Record the §5 retire criteria + the 60-day revisit date in Linear. *~5 min.*
12. **[DoD close]** Run `/dod-close` for the retarget + backfill build (spec ✅ ADR+this plan, Linear ✅, adversarial pass ✅ §7 pre-mortem + §2 dedup analysis); note any waiver. *~2 min.*

**Adversarial pass (DoD item 3) is embedded** in §7's risk table + the §2 duplicate-contact analysis — the sharpest failure mode is Clarify's pre-existing auto-synced data causing silent duplicates, which the dedup-first rule (§4a) is built to catch.

---

## References
- `.claude/proposals/clarify-integration.md` — capture lane + API reality (§0: API is summary-only for meetings, but CRM objects `person`/`company`/`deal`/`meeting`/`task` are fully writable) + the consolidation decision this plan executes.
- `.claude/proposals/post-event-hubspot-step.md` — the Step 5.5 discipline being preserved (selection bar, dedup, create-once, gate).
- `.claude/references/notion-schema.md` — Notion (system of record) schemas + the Company→Contact→Note write-order convention mirrored here.
- `docs/adr/` — ADR-1 (data layer) … ADR-5; this adds ADR-6.
- CLAUDE.md — Rules 6 (create-over-update), 10/11 (dedup-before-create); pipeline value philosophy (relationships, not enrichment); DoD gate.
- Memory: `feedback_pipeline_value_philosophy`, `project_notion_writes_must_be_parent_thread`, `project_claude_code_env_handoff`.
- Clarify: pricing `clarify.ai/pricing` · MCP `docs.clarify.ai/en/articles/13367278` · auth `developer.clarify.ai/docs/getting-started/authentication`.
