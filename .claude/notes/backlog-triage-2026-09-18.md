# Backlog triage — pre-triage table (Step C), 2026-09-18

**What this is.** Every item from `open-items-inventory-2026-09-13.md` (plus what moved since) assigned exactly one verb and a target, grouped by **source container** so each container drains in one pass. Alex confirms or overrides per batch; the drain (Step D) applies the confirmed verbs. Container rule: `linear-convention.md` §Container rule.

**Verbs.** `KILL` close/delete with reason · `MERGE` duplicate of an existing ID (comment there) · `FILE` new Linear issue (lane · label · appetite) or Notion Project Idea · `ANSWER` a decision → `decision` issue (Todo, assigned, due) or answered inline · `RECORD` an environmental constraint → `platform-constraints.md` · `DONE` already resolved by events since 09-13 (listed so it isn't re-asked).

**Scope.** Empire State projects only. gtm-OS items (migrated 2026-09-18 to the GTM-OS team: YED-164→GTM-1 · 165→GTM-2 · 98→GTM-3 · 125→GTM-4 · 79→GTM-5 · 83→GTM-6 · 84→GTM-7 · 85→GTM-8 · 99→GTM-9 · 100→GTM-10 · 101→GTM-11) are out of scope.

**Confirmation legend.** `[ ]` pending · `[x]` confirmed · `[~]` overridden (note the override inline).

---

## Batch 1 — Linear itself (status hygiene)

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 1.1 | YED-114 project home | DONE | already Empire State Hub |
| 1.2 | YED-118 In Progress on closed M3 | DONE | closed Done 09-18 with close-out comment |
| 1.3 | YED-163 titled "Increment 2" | DONE | retitled Increment 4 (ADR-8 Amendment 3) |
| 1.4 | YED-131 body vs spine doc | DONE | v1 recompute; v2 deferred until ≥20 outcome rows |
| 1.5 | YED-157 In Progress but B3–B5 unstarted | DONE | Backlog, re-scoped to `/digest`, blockedBy YED-160 |
| 1.6 | YED-47 on M5 | DONE | M4 / S1b, retitled |
| 1.7 | YED-128 Supabase migrations as spine SoT — High, not on runway | ANSWER | `decision`: fold into YED-168 ADR-10 S1a/S1b (migrations become SoT by construction) **or** keep as its own Phase 1 item. Recommend fold → close YED-128 as MERGE into YED-168. |
| 1.8 | YED-104 T1 audience intelligence | MERGE | → YED-170 (`retrieve.py` is the retrieval track); keep YED-104 open only as the *draft-time consumer* story, blockedBy YED-170 |
| 1.9 | YED-141 Deep Read gate hardening | FILE-keep | already an issue; add body pointer to `proposals/deep-read-marker-gate.md` follow-ups (ledger row via PostToolUse, `.state` GC, Stop-hook Notion query) so those stop living in the proposal |
| 1.10 | YED-137 rename content-correspondent | KEEP | Low, hygiene lane; no change |
| 1.11 | YED-129 define ChatPRD's role + retire stale dashboard PRD | ANSWER | `decision`, due 2026-10-02: product = PRD / infra = spec. Once ruled, the three pending PRD mirrors (judge, ADR-8, inbox-miner) resolve under the same rule |
| 1.12 | YED-34 fate of ~50 nested agents/commands subdirs | ANSWER | `decision`, due 2026-10-09: delete or keep. Recommend delete (unused since May) |
| 1.13 | YED-65 Clay MCP into ICP skills | KEEP | Job-Search Engine; add `Revisit trigger: first warm-outreach friction on a target-company contact` + label `parked` |
| 1.14 | YED-145 Google Alerts RSS for voice-radar | KEEP | Low; `parked` with trigger `voice-radar next moves` (same slot as X ingestion) |
| 1.15 | YED-152 interview-prep reads me-model ICP | KEEP | Low; blockedBy YED-170 (dossier becomes a retrieve.py consumer) |
| 1.16 | YED-151 resume tailor | KEEP | Medium; career lane; add appetite `3–7d` |
| 1.17 | YED-149 roles → spine producer | KEEP | now blockedBy YED-169 (`substrate.py` ensure-event) |
| 1.18 | YED-113 hub session replay | KEEP | `parked`, trigger `Q1 2027 unattended scheduling decision` |
| 1.19 | YED-76 hub Auth.js | KEEP | Backlog; add `Revisit trigger: /ops needs a second viewer` + `parked` |
| 1.20 | YED-82 hub craft + launch | KEEP | Phase 3; body gains the PII Phase-2 client-bundle scan line (ADR-9) |
| 1.21 | YED-48 eval harness | KEEP | Phase 3; note YED-172 pulls its core question forward |
| 1.22 | YED-162 exhaust loop | KEEP | blockedBy YED-170 (done) + YED-163 |
| 1.23 | YED-135 gtm spine decommission | DONE | Linear says Done. CLAUDE.md ("pending a dated decommission") and roadmap §9 are stale → EDIT in the drain pass |
| 1.24 | gtm-OS migration | DONE | all 11 issues on GTM-OS (GTM-1…11); project lead team = GTM-OS. Canceled projects "Full-Stack GTM Roadmap" + "GTM-oS" stay on EMPIRE-STATE (canceled stays canceled) |

## Batch 2 — Roadmap v2

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 2.1 | Phase 0: YED-81, YED-161 rows | DONE | dropped to §10 (PR #79) |
| 2.2 | Phase 0: "OBS live GUI pass + first smoke test" | FILE | Empire State Events · `<1d` · "OBS smoke test + ETL (Scribe transcribe, slide extract, OCR)"; YED-154 is Done-on-paper — this is the follow-through issue |
| 2.3 | Phase 0: "Linear reconciled" | DONE | this workstream (PR #79 + this table) |
| 2.4 | §3 career lane "headline test", "event deep-dives", "theme→prior-post index" | FILE ×1 | one Job-Search Engine issue "Career-lane content plays: headline test · theme→post index" · `3–7d`; event deep-dives are already the content pipeline |
| 2.5 | §3 hygiene lane "garbled-name verification" | RECORD | it's a standing rule (founder-showcase.md guard), not work; no issue |
| 2.6 | §5 "Measurement → alex plugin promotion" | KEEP | stays a roadmap line, gated on one merged loop fix; no issue until then |
| 2.7 | §5 deferred-to-Q1-2027 list | FILE ×1 | one `parked` issue "Q1 2027 slate: unattended scheduling · learned weights · embedding dedup · X ingestion" with `Revisit trigger: A3 closes (2026-12-12)` — one row, not five |
| 2.8 | MI remainders: Notion→graph backfill | MERGE | → YED-171 (backfill through producers supersedes `market-intel-backfill.md`) |
| 2.9 | MI remainders: real `/scan-trends` run before `/ops/market-intel` is non-empty | FILE | MI Engine · `<1d` · "First real /scan-trends run + approve digest" |
| 2.10 | MI remainders: calibration loop (veracity mechanism 6) | FILE | MI Engine · `parked` · trigger `≥20 artifact_outcome rows` (same gate as w_use) |
| 2.11 | MI remainders: interview-outcome write-back | MERGE | → YED-152 body |
| 2.12 | §7 parked list | DONE | collapsed to a pointer (PR #79) |
| 2.13 | §9 decision log references to YED-98/100/101/125/164/165 | EDIT | rewrite to GTM- IDs in the drain pass |

## Batch 3 — Proposals (9 files)

| # | File | Verb | Target / reason |
|---|---|---|---|
| 3.1 | `content-pipeline-v2-stage2.md` — "Awaiting decision" since 05-12 | ANSWER | `decision`, due 2026-10-02. Recommendation: **KILL the proposal as a unit**; its live parts are absorbed — artifact schemas → substrate (YED-168), eval gates → YED-48/judge, status automation → still deferred behind the YED-23 goal flip. Header → `Status: absorbed/killed 2026-10-02 · Linear: YED-n` |
| 3.2 | `empire-state-agentic-architecture-2026-05-15.md` — 18 gaps, none executed | KILL | superseded by roadmap v2 + ADR-0…10; header → `Status: superseded by roadmap v2 (2026-09-12)`; any still-live gap surfaces on its own |
| 3.3 | `deep-read-marker-gate.md` follow-ups | MERGE | → YED-141 body (see 1.9); header → `Linear: YED-139 (shipped) · follow-ups YED-141` |
| 3.4 | `deep-read-marker-gate.md` `.state` GC | MERGE | → YED-141 |
| 3.5 | `event-field-guide.md` (approved, built as ADR-5) | DONE | header → `Status: shipped (ADR-5, YED-136)` |
| 3.6 | `field-guide-spike-daytona.md` — endnote URLs + CVE verification before public reuse | FILE | Empire State Events · `<1d` · "Daytona field-guide: attach endnote URLs + verify May-2026 CVE numbers before reuse" |
| 3.7 | `post-event-hubspot-step.md` — pre-event HubSpot writes parked | ANSWER-inline | rule stands (one hand-picked pre-event create, manual). Header → `Status: shipped YED-142 · pre-event writes: manual-only by rule` |
| 3.8 | `steering-interview-v2-collaborative.md` — "proposed → building" | DONE | PR #54 merged; header → `Status: shipped 2026-08-29 (smoke test note)` |
| 3.9 | `yed-30-step-5-empire-state-backport.md` — "Ready to execute, needs approval" | ANSWER | `decision`, due 2026-10-02: approve the refactor plan or kill. Recommend approve after this reconciliation lands (CLAUDE.md is calmer now) |
| 3.10 | `yed-81-sec-pii-guardrails.md` §8 build-time details (regex set, linkedin_url tier, bio refuse/redact, timeouts, replay.ts hit) | MERGE | → one comment on YED-81 (Done) + a `parked` issue "PII Phase 2 — DB constraint, retention ADR, regex set" trigger `first spine writer outside spine_client` |
| 3.11 | `yed-161-inbox-boundary-mechanism.md` | DONE | shipped #74/#75; header → `Status: shipped` |

## Batch 4 — ADR follow-ups

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 4.1 | ADR-8 open questions: `spec_for` precedence · ack auto-expiry on Linear Done · hub projection | KEEP-in-ADR | genuine design questions that belong with the spec; add "resolve at Increment 3 build time" — no issue |
| 4.2 | ADR-8 Increment 2 gate (Alex sees a finding fire) | RECORD | it's a gate, stays in the ADR; YED-163 body already says so |
| 4.3 | ADR-8: 17/20 hooks lack `Spec:` header | FILE | Build-Rigor · `<1d` · "Add Spec: headers to 17 hooks/scripts" |
| 4.4 | ADR-8 R6 judge emitter repo-relative paths | MERGE | → YED-163 body (Increment 2 build note) — actually ADR Increment 2, no Linear issue yet → FILE Build-Rigor "ADR-8 Increment 2 — neighborhood as judge context" · `3–7d` (this is the *real* Increment 2 and had no issue) |
| 4.5 | ADR-8 D4(2) over-suppression accepted | RECORD | recorded in ADR; nothing to do |
| 4.6 | ADR-8 baseline count columns retired | RECORD | recorded |
| 4.7 | ADR-9 Phase 2 (CHECK/trigger, retention ADR, client-bundle scan) | MERGE | → the `parked` PII Phase 2 issue (3.10) + YED-82 body |
| 4.8 | ADR-7: `email` table rejected; cron deferred; stub-recovery fetch | RECORD | alternatives-considered; no issue. Cron: `parked` trigger `false-merge rate measured over 4 scans` — fold into 5.x inbox row |
| 4.9 | ADR-4 hard-delete deferred | RECORD | in ADR; resurfaces under YED-47 S1b |
| 4.10 | ADR-1: 0/182 `company.linkedin_url`; verify 11 pre-mortem edits landed | FILE | MI Engine · `<3d` · "ADR-1 backlog: linkedin_url backfill + pre-mortem edit audit" |
| 4.11 | ADR-0/ADR-4: explicit re-decision of YED-116 (shared taxonomy) | MERGE | → YED-126 (taxonomy v2 IS the re-decision) |
| 4.12 | `market-intel-schema.sql` provenance header still cites gtm ref | FILE-trivial | fold into 4.10 |
| 4.13 | ADR-2/ADR-3 "detail deferred to PRD" | RECORD | by design |
| 4.14 | ADR-10 stub Proposed | DONE | YED-168 |
| 4.15 | Confluent Signal Stream out-of-scope list | KILL | plan file is evidence; nothing live |

## Batch 5 — Notes + future-state-register

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 5.1 | frictions 05-27 findings 1/2/4 | DONE | marked (PR #79) |
| 5.2 | frictions 05-20 "invite metadata changes after research" | ANSWER-inline | rule: re-run `/event-deep-research` REFRESH-light on speaker/venue change; silent on time-only change. Write as a line in `check-new-events.md`; mark the note |
| 5.3 | frictions 05-20 PIPELINE block format / auto-run vs stage | DONE | defaults held for 4 months = ratified; mark |
| 5.4 | frictions 05-27 "pick Path A vs B post" + Gamma carousels | KILL | stale content decision; Gamma gone |
| 5.5 | frictions end-of-window questions (Granola voice, 36h window, Mode B prune, notes sent?, publish-rate number) | KILL | window closed 06-11; the one live piece — "instrument LinkedIn reality for publish rate" — is now the post-performance backfill (shipped 09-14) |
| 5.6 | frictions: `trigger-log.md` 16 × `trigger: ?` | KILL | delete the file; YED-27's signal never accrued and the container rule replaces it |
| 5.7 | `state-reconciliation-2026-09-12.md` §6–7 systems diagnostic requested, never produced | ANSWER | `decision`: run `/systems-analyze` on it now (1 session) or drop. Recommend **drop** — this reconciliation is the intervention; the diagnosis would describe what we're already fixing |
| 5.8 | `rigor-loop-session-resume-2026-07-16.md` judge roadmap (drop provisional, wire dual-judge, mechanize dangling-ref, quorum mechanic) | FILE ×1 | Build-Rigor · "Judge hardening: wire dual-dispatch into /judge-build + mechanize dangling-ref check" · `3–7d`; de-provisional stays passive |
| 5.9 | same note: stale machine-local plan `~/.claude/plans/check-chatprd-…` | KILL | machine-local plans are retired |
| 5.10 | `measurement-layer-learnings.md` OTEL/Langfuse deferral | RECORD | → `platform-constraints.md` "measurement: rent-on-trigger" |
| 5.11 | `future-state-register.md` Build-Rigor table (OTEL traces, cost accounting, promotion) | RECORD + KILL | constraints → platform-constraints; promotion already a roadmap line; delete file after 5.12 |
| 5.12 | `future-state-register.md` eval-harness 8 deferred items | FILE ×1 | Build-Rigor · `parked` · "Eval-harness deferred slate (per-skill rubrics, CI hook, drift dashboard, rubric versioning…)" trigger `YED-48 ships` |
| 5.13 | `YED-96-validation-handoff.md` | KILL | delete (resolved, historical) |
| 5.14 | `steering-v2-smoke-test` non-blockers (Deep Read pending, HubSpot deferred) | RECORD | standing rules; nothing |
| 5.15 | `deep-read-batch-wiring-fix.md` Stop-hook Notion query | MERGE | → YED-141 |
| 5.16 | `obs-capture-setup.md` "ETL is the next build" | MERGE | → 2.2 |

## Batch 6 — Evals + DoD waivers + correction-recurrence

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 6.1 | `/rigor-review` dark since 07-17 | FILE | Build-Rigor · `<1d` · "Run /rigor-review (first since 07-17) + adopt the container-rule grep"; then weekly |
| 6.2 | 9 judge-not-run waivers incl. 09-08 role-radar and 09-11 | FILE ×1 | Build-Rigor · `<1d` · "Redeem judge waivers: role-radar v2.4, 09-11 content build" (fresh session) |
| 6.3 | 12 spec/PRD waivers + 5 ChatPRD→Notion mirror waivers (judge PRD, ADR-8, inbox-miner) | ANSWER | gated on 1.11 (YED-129). If "infra = spec": ADRs *are* the spec and the three mirrors are KILL. If "PRD always": one issue "Backfill 3 PRD mirrors" |
| 6.4 | correction-recurrence `judge-item-waived-advisory` stuck at 2 | MERGE | → 6.1 (recount in the review) |
| 6.5 | `dangling-reference-cap-under-applied-by-models` proposed | MERGE | → 5.8 |
| 6.6 | `gemini-false-flag-from-missing-house-context` advisory | RECORD | → platform-constraints (cross-provider judge caveat) |
| 6.7 | `build-quality@3` candidate cap "claim asserted verified without citation" | ANSWER-inline | adopt in the next rubric bump (`@4`) → MERGE into 5.8 |
| 6.8 | inbox-miner cohort gaps: "Meta" alias rule · VC-newsletter canonical URL · stub fetch | ANSWER-inline ×2 + KILL | Meta: add alias `Meta` → parent `Meta Platforms`, exclude `Meta Superintelligence Labs`; VC URL: prefer subject-company URL. Both → `inbox-allowlist.md`. Stub fetch: KILL |
| 6.9 | `post-event-brief-template-evidence.md` fix (pull pre-event brief from linked Event) | FILE-trivial | Empire State Events · `<1d` · fold into 2.2's sibling "post-event polish" or apply inline now |
| 6.10 | `transcription-quality-scorecard.md` gold slice | FILE | Empire State Events · `<1d` · "Audio-verified gold slice on one event" |
| 6.11 | doc-KB V1 backlog (ligatures, TOC skip, re-ingest baseline) | MERGE | → YED-157 body |
| 6.12 | `deep-read-gate-failures.jsonl` never fired | RECORD | good signal; nothing |
| 6.13 | inbox-allowlist GitHub-notification exception | RECORD | conditional rule; nothing |

## Batch 7 — Memory files holding state (rewrite as pointers — LAST)

| # | Memory | Verb | Target / reason |
|---|---|---|---|
| 7.1 | `project_visual_selection_marker_parked` | FILE + pointer | `parked` issue, Empire State Events, trigger `≥5 posts shipped with multi-visual drafts`; memory keeps the two-option note as pointer |
| 7.2 | `project_behavioral_exhaust_pin` | MERGE + pointer | → YED-162 |
| 7.3 | `project_x_twitter_channel_signal` | MERGE + pointer | → 2.7 Q1 slate |
| 7.4 | `feedback_cross_reference_prior_posts_longtail` (theme→post index offer) | MERGE + keep | → 2.4; feedback rule text stays |
| 7.5 | `project_me_model_and_jobsearch` (`/tailor-resume` next build; GitHub proof-link hold) | MERGE + keep | → YED-151; GitHub hold = `parked` line in YED-151 body |
| 7.6 | `reference_visual_brief_pdf_export_path` (fold into visual-briefs spec) | FILE-trivial | Empire State Events · `<1d` · "visual-briefs.md: headless-Chrome export as default step" |
| 7.7 | `project_check_new_events_raw_calendar` (codify fallback) | FILE-trivial | Empire State Events · `<1d` · "check-new-events: codify raw-description fallback" |
| 7.8 | `project_apollo_credits` + Apollo lines | RECORD | → platform-constraints; memory → pointer |
| 7.9 | `project_granola_integration` | RECORD | → platform-constraints ("Granola nonoperational; never fire"); memory → pointer + the rule |
| 7.10 | `project_crm_capture_decision` (OBS ETL unbuilt) | MERGE | → 2.2 |
| 7.11 | `project_knowledge_library_local_home` (`esep-media` R2 tipping point) | MERGE | → 2.2 body ("when recordings pile up: extend R2") |
| 7.12 | `project_systems_thinking_buildout` (YED-25 defer; YED-24 discoverability) | KILL | YED-24/25 resolved by events (plugin shipped; agents discoverable); memory → pointer |
| 7.13 | `project_market_intelligence_engine_2026-06-28` (Supabase MCP blocker; calibration fast-follow; audience-definition dependency) | REWRITE | blocker resolved (memory 09-17); calibration → 2.10; audience → shipped (`audience-north-star.md`) |
| 7.14 | `project_supabase_credit_and_metered_key_gate` (ANTHROPIC key decision) | ANSWER | `decision`, due 2026-10-02: add key vs Gemini fallback. Recommend **Gemini fallback stays default; add key only when a scripted Claude call is on the runway** (none is) |
| 7.15 | `reference_websearch_cap_not_tunable` (`/feedback` knob?) | KILL | not worth the ask; RECORD the cap in platform-constraints |
| 7.16 | `feedback_leaderless_collective` (call-outs cumbersome?) | RECORD | standing preference; nothing |
| 7.17 | `project_field_guide_renderer_name_fix_pending_validation` (pronoun rule unvalidated) | MERGE | → 6.2 (fresh-session validation batch) |
| 7.18 | `project_claude_code_env_handoff` (`launchctl setenv` untested) | RECORD | platform-constraints |
| 7.19 | `project_worktree_reconciliation` (YED-114 home; hook team-wide; `ESP-jobsearch` recreate) | REWRITE | all three resolved (Empire State Hub; GTM-OS team; worktree on demand) |
| 7.20 | `project_roadmap_reanchor_2026-08-07` (YED-68–73 confirm-before-cancel) | KILL | roadmap v2 §7 ratified the cancel; memory → tombstone line in roadmap-v2 memory |
| 7.21 | `project_inbox_miner` (Notion Companies mirror appends for 13 signals; PR + dod-close) | FILE | MI Engine · `<1d` · "Inbox-miner: mirror 13 signals to Notion Companies + close DoD" |
| 7.22 | `reference_nori_agentic_domain` | FILE-trivial | MI Engine · `<1d` · "Fix Nori domain in HubSpot + spine" |
| 7.23 | `project_worktree_env_missing`, `project_linear_mcp_transport_and_tty_auth`, `project_notion_writes_must_be_parent_thread`, `project_notion_updatepage_newline_gotcha`, `reference_chatprd_mcp_projects`, `project_auto_commit_to_main` | RECORD | → platform-constraints; memories → pointer + rule |
| 7.24 | `reference_reconciliation_terminal_charter` amendment | MERGE | → the charter file itself (append the "scratch worktree" amendment) |

## Batch 8 — Hub repo

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 8.1 | `toolbox.json` stale (07-30) → `architecture.ts` counts | FILE | Empire State Hub · `<1d` · "Regenerate toolbox + wire gen:toolbox into the deploy checklist" |
| 8.2 | `content-performance.ts` frozen 08-28 | MERGE | → 8.1 (same refresh) — or KILL if the 09-14 post-performance backfill replaced it |
| 8.3 | `build-journal.json` uncommitted on hub main | FILE-trivial | commit + deploy (Alex's GHD step); flag only |
| 8.4 | 5 journal entries without prose | FILE | Empire State Hub · `<1d` · "Write the 5 missing journal summaries" |
| 8.5 | `/changelog` unlinked; live GitHub path unbuilt | ANSWER-inline | link it in nav (trivial) → 8.1; live path stays `parked` in YED-82 |
| 8.6 | `build-arcs.json` `future` fields (10 arcs) | KILL-as-state | rewrite each `future` to a one-line "next: YED-n" pointer or drop; futures live in Linear |
| 8.7 | Auth.js / revalidation / GCal source | DONE | YED-76 / YED-82 bodies |
| 8.8 | `PHANTOM_TEST_*` orphan keys, `Design Inspo/` stray | FILE-trivial | fold into 8.1 |
| 8.9 | producer liveness inferred; confidence not normalized | MERGE | → YED-114 body |
| 8.10 | graph hygiene v1 limits (false-merge, entities without company) | MERGE | → YED-47 |
| 8.11 | build-diary unmerged job-search entries | RECORD | deliberate |

## Batch 9 — Legacy docs

| # | File | Verb | Target / reason |
|---|---|---|---|
| 9.1 | `HANDOFF_V2.md` | KILL | delete; the 9 questions are answered by roadmap v2 / ADRs or moot |
| 9.2 | `PROJECT_BRIEF.md` open sections | KILL-sections | delete "Open Questions", "Tech Debt Log", "Next Steps"; keep the purpose/architecture body |
| 9.3 | `Signal_Pipeline/MOVED.md` | KILL | delete |
| 9.4 | `.claude/notes/YED-96-validation-handoff.md` | KILL | delete (5.13) |
| 9.5 | `.claude/artifacts/future-state-register.md` | KILL | delete after 5.11/5.12 |
| 9.6 | `.claude/artifacts/trigger-log.md` | KILL | delete (5.6) |
| 9.7 | `pipeline-operations-guide.md` Phase 5 | DONE | refreshed (PR #79) |
| 9.8 | `WORKFLOWS.md` footer | DONE | superseded (PR #79) |
| 9.9 | `target-companies.md` HF slug `_tbd_` / Nvidia acq | FILE-trivial | Job-Search Engine · `<1d` · fold into YED-151 or a "target-companies refresh" line |
| 9.10 | `docs/adr/evidence/plans/do-not-make-anything-drifting-locket.md` status unrecorded | DONE | post-performance backfill shipped 09-14 (`a2de692`); add status line |
| 9.11 | `open-items-inventory-2026-09-13.md` | SNAPSHOT | header: superseded by Linear as of drain date; do not update |

---

## Tally (pre-confirmation)

| Verb | Count |
|---|---|
| DONE (by events since 09-13) | 20 |
| KILL | 17 |
| MERGE | 25 |
| RECORD | 22 |
| FILE (new issues, after folding) | ~22 → **~14 issues** once trivial ones fold |
| ANSWER (decisions) | **9** → 1.7 · 1.11 · 1.12 · 3.1 · 3.9 · 5.7 · 6.3 · 7.14 · (+ inline: 5.2, 6.7, 6.8, 8.5) |
| KEEP (already an issue, minor body edit) | 14 |

**The nine `decision` issues are the whole judgment load.** Everything else is confirm-by-skim. Recommended due dates: 2026-10-02 for the four that gate other items (1.11 ChatPRD role, 3.1 pipeline-v2, 3.9 YED-30, 7.14 metered key), 2026-10-09 for the rest.

## Batch 10 — inventory "Parked" items the table missed (added in the drain, 2026-09-18)

| # | Item | Verb | Target / reason |
|---|---|---|---|
| 10.1 | Scaffolded commands `/post-event-synthesis`, `/weekly-recap`, `/voice-pass` | FILE (parked) | one issue, trigger `a weekly-recap or voice-pass friction named in a rigor-review` |
| 10.2 | Deferred hooks + scheduled tasks (WORKFLOWS.md) | MERGE | → 10.1 |
| 10.3 | `project-complete` companion skill / portfolio-tracker | MERGE | → 10.1 |
| 10.4 | Tier-2 skill imports | RECORD | "bring in when a use case warrants" — WORKFLOWS.md already says so |
| 10.5 | Warm-outreach variant + custom messaging skill | MERGE | → YED-65 (parked; same trigger) |
| 10.6 | Notion `Select → Status` migration | KILL | lived only in PROJECT_BRIEF (section deleted) |
| 10.7 | Phase 3 intake form (Vercel/Lovable) | RECORD | CLAUDE.md Phase 3 "when volume demands it" — no issue until it does |
| 10.8 | Backfill `Google Calendar Event ID` on pre-May Notion rows | KILL | dual-path title+date resolution covers it |
| 10.9 | Signal Stream / Confluent stretch | KILL | evidence plan only |

## Rulings (2026-09-18, Alex)
YED-129 infra = spec (3 PRD mirrors closed) · YED-173 killed · YED-174 approved → work item · YED-176 Gemini default. Remaining decisions: YED-128, YED-34, YED-175 (due 2026-10-09).

## Drain record (2026-09-18)
Applied: decisions YED-128/129/34 (converted) + YED-173–176 (new) · new issues YED-177–197 + the Batch-10 parked issue · keep-edits on YED-104/141/65/145/152/151/149/113/76/82/48/162 · merge comments on YED-171/157/114/47/126/81 · `platform-constraints.md` created · 9 proposal headers · deletions (HANDOFF_V2, MOVED.md, YED-96 note, future-state-register, trigger-log, PROJECT_BRIEF open sections) · roadmap / CLAUDE.md / ADR-8 / charter / rigor-review / check-new-events / frictions / allowlist edits · memory pointers · hub build-arcs futures → pointers + `/changelog` nav link (hub PR).
