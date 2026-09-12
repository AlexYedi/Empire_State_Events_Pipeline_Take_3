---
description: "Mine Gmail as a Market-Intelligence signal source. Stage A (discover) = one-time metadata-only pass → candidate allowlist + unsubscribe/spam worksheets. Stage B (extract) = allowlist-only body extraction → company/product signals into the Supabase MI graph + Notion Companies, through a permanent resolved-target write gate. Legitimate-only, HITL. See ADR-7."
argument-hint: "[discover | extract] [window e.g. 12m | 7d]"
---

# /scan-inbox — Inbox Intelligence Miner

Orchestrates the `inbox-miner` skill. Methodology + all invariants live in
`.claude/skills/inbox-miner/SKILL.md`; this file is the orchestration shape.
Decision record: `docs/adr/ADR-7-inbox-signal-source.md`.

**Thread placement — scoped precisely (corrected 2026-09-11 after the build-quality judge flagged an over-extended citation):**
- **All WRITES run in the parent thread** — Notion/Supabase/Gmail-label writes. ([[project_notion_writes_must_be_parent_thread]] covers Notion/Gamma/HubSpot/Calendar; the Supabase rule is REST-not-MCP per ADR-0; Gmail *writes* are kept in the parent by **this** command's design, for the injection guard in ADR-7 D5 — a subagent that ingests attacker-controlled email text must never hold a write tool.)
- **Gmail READS may legitimately be delegated.** Contrary to an earlier over-broad claim here, `search_threads`/`get_thread` ARE available to subagents — this repo's `company-researcher` and `person-researcher` already declare them. v1 still fetches in the parent for simplicity.
- **Known optimization (not yet built):** because Gmail reads *are* subagent-available, the distill subagent could call `get_thread` itself instead of the parent fetching and passing bodies down. That would keep large newsletter bodies out of the parent's context entirely — the exact context-bloat problem hit during the v1 cohort run. Worth doing before the cron goes unattended.

## 1. Intake & validate (parent thread)
- Parse args: **stage** (`discover`|`extract`) and **window**. Default stage = `discover` if
  `.claude/references/inbox-allowlist.md` has no curated senders yet, else `extract`. Default window:
  discover = 12 months, extract = since last run (else 7d).
- **Load the boundary files first:** `inbox-denylist.md` (required — refuse to scan if missing) and,
  for `extract`, `inbox-allowlist.md` (refuse to extract if it has no curated entries — run `discover`
  first). Read `SKILL.md` for the methodology.
- **Pre-flight for `extract`:** confirm `SUPABASE_API_KEY` is in `.env`; if absent, **hard-fail loudly**
  and stop (do not proceed to any write or label — ADR-7 R4).

## 2. Dispatch / fan-out (parent thread, explicit)
- **Gmail reads run in the parent** (MCP not available to subagents). For `extract`, once bodies are
  fetched, hand raw thread text to a **distill subagent** (`general-purpose`) — text in, schema-valid
  structured signals out, **NO write tools** (injection guard, ADR-7 D5). Multiple threads → batch the
  distill calls in one message. Stage A does no body dispatch (metadata only).

## 3. Collect & handle thin returns
- Aggregate distill returns. If a batch returns thin/garbled, re-invoke just that batch with the raw
  text again; never restart the whole run. Drop non-signal / low-confidence per SKILL B2.

## 4. Synthesize (inline, parent)
- **Stage A:** build the sender histogram and the three worksheets (SKILL A2–A3).
- **Stage B:** resolve entities (deterministic slug; `GET /company`, `GET /event`) into the
  resolved-target write-gate digest (SKILL B3–B4).

## 5. Judge gate
- N/A — this command's output is signal data through a human write gate, not a quality-graded artifact.
  (The build of the skill/command itself is judged via `/judge-build`, separately.)

## 6. Output destination — NAMED
- **Stage A:** the three worksheets → **conversation** (HITL). On approval: allowlist/denylist file
  appends + Gmail `mark_thread_spam` (batch, approved only). Nothing to the graph.
- **Stage B:** the write-gate digest → **conversation** (HITL). On approval:
  **Supabase** (`event` + `event_entity` + upserted `company`/`topic`, REST, `SUPABASE_API_KEY`, never MCP)
  + **Notion Companies `Recent Developments`** (parent-thread MCP; `notion-search` not
  `notion-query-data-sources`; real newlines) + Gmail labels (`Pipeline/processed` + class label) applied
  **only after the DB write confirms**.

## 7. Failure modes
- **Denylist/allowlist file missing** → refuse to scan (Step 1).
- **`SUPABASE_API_KEY` absent (extract)** → hard-fail, write nothing, do not label.
- **Gmail label/spam write scope not granted** → probe first; fall back to a processed-message-id ledger
  (idempotency) + manual unsubscribe worksheet; never assume the write worked.
- **Distill subagent thin/empty** → re-invoke that batch once; if still thin, report the gap, don't invent.
- **Discovery window too large to fully enumerate** → aggregate what's retrieved, report coverage
  honestly, offer to widen. Never claim a full sweep not performed.
- **Company slug generic/ambiguous, or no primary-source URL** → abstain + flag (never blind-upsert).

## Close out
- Summarize: senders bucketed / signals written (matched vs created) / labels applied / spam batched /
  coverage. Flag any company created-this-run for source-check. Reconcile Linear (YED-153) if the run
  surfaced build work; `/dod-close` at the build boundary.
