# Open-items inventory — everything in flight, open, or unresolved (2026-09-13)

**Purpose:** step 1 of a re-plan. A flat read-out of every parked build, roadmap item, open question, blocker, and dangling follow-up, so the totality can be reviewed before it is pulled into a coherent plan. This is an inventory, not a decision; nothing here is prioritized.

**Sources swept:** `roadmap.md` v2 · Linear (Backlog / In Progress / recent Done) · `.claude/notes/*` · `.claude/proposals/*` · `docs/adr/*` · `dod-waivers.jsonl` · `correction-recurrence.md` · `WORKFLOWS.md` · references (spine, denylist, registry, obs) · the hub repo (data files, env, docs) · all 50 memory files · git branch/worktree state.

---

## 1. PARKED — explicitly parked, deferred, or "do not build now"

### Content & pipeline
- **Visual-selection marker** — mark which visual Alex actually posts with; two mechanisms undecided (convention line vs. `Selected Visual` property); revisit after a few posts. (memory 2026-06-05; roadmap §7)
- **Behavioral-exhaust pin** — trace-driven self-improvement in our own pipeline; revisit after Daytona content ships, framed against the measurement layer, not net-new. (memory 2026-09-09) → now partly the shape of YED-162.
- **X/Twitter as ingestion source + posting channel** — Daytona builders shared X handles; deferred to Q1 2027 / next voice-radar move. (memory 2026-09-09; roadmap §5)
- **Theme→prior-post index** — index of Alex's own posts by theme for long-tail back-linking; the offer was never made or accepted. (memory 2026-08-28; roadmap career lane)
- **Warm-outreach variant + custom messaging skill** — cold-only in V1. (CLAUDE.md Phase 2)
- **`project-complete` companion skill** — portfolio-tracker says "to be built." (CLAUDE.md Phase 2b)
- **Content Pipeline v2 Stage 2** (artifact schemas, typed skill contracts, eval gates, status automation) — header still reads "Awaiting decision"; ungated by the steering bias, never decided or built. (`proposals/content-pipeline-v2-stage2.md`, 2026-05-12)
- **Status-transition automation (Component 4)** — sequenced after the YED-23 goal flip. (same proposal + agentic-architecture proposal)
- **Empire State agentic-architecture build plan (2026-05-15)** — 18 gaps, phased plan, "none executed"; `Plan` + `head-of-product-engineering` agents deferred inside it. (`proposals/empire-state-agentic-architecture-2026-05-15.md`)
- **Scaffolded, unwired commands** — `/post-event-synthesis`, `/weekly-recap` (incl. steering two-touch), `/voice-pass` (severity rubric, Notion diff flow). Dashed edges on the public system diagram. (`WORKFLOWS.md`; hub `toolbox.json`)
- **Hooks + scheduled tasks** — SessionStart intake count, Stop-hook `/voice-pass`, "just got back from" → post-event, Sunday `/weekly-recap`, daily stale-intake nudge. Deferred until commands work. (`WORKFLOWS.md`)
- **Tier-2 skill imports** — positioning-messaging, launch-marketing, media-relations, value-story, cxo-briefing, vertical-templates, partnership-bd, BI, statistical-analyst. (`WORKFLOWS.md`)
- **Codify the raw-description fallback into `/check-new-events`** — still a manual workaround. (memory 2026-07-07)
- **Fold headless-Chrome PDF export into `visual-briefs.md`** as the default export step; spec still documents ⌘P. (memory 2026-08-12)
- **Gamma `numCards`/`cardSplit` note → visual-briefs** — batched 2026-05-27, pending green-light; likely moot post-Gamma removal. (`execution-week-frictions.md`)
- **Backfill `Google Calendar Event ID`** on pre-2026-05-21 Notion Event rows. (frictions 2026-05-21)
- **Granola** — REST path built then DISABLED (app nonoperational); MCP-server install, auto-detection, 48h window all moot until it records. (memory 2026-05-21/27)
- **`/post-event-content-manual` / `--paste` branch + auto-wiring of `transcript-conditioning`** — TODOs from 2026-05-27; probably superseded by manual-upload anchoring + Step 3.5, unverified. (frictions 2026-05-27)
- **Pre-event HubSpot writes** — parked in the 2026-08-25 restore loop; only one hand-picked create sanctioned. (`proposals/post-event-hubspot-step.md`)
- **Apollo enrichment (Step 6)** — API blocked on free plan; 900-credit upgrade is a separate web-UI evaluation. (memory)
- **Phase 3 intake form (Vercel/Lovable)** — unbuilt; Vercel plugins stay disabled until it exists. (CLAUDE.md Phase 3; memory 2026-05-26)
- **Notion `Select → Status` property migration** — optional, skipped. (`PROJECT_BRIEF.md`)

### MI engine & data
- **Unattended producer scheduling** — Q1 2027; also blocked on the ANTHROPIC-key decision. (roadmap §5)
- **Learned relevance weights · embedding dedup · hub session replay (YED-113)** — Q1 2027. (roadmap §5)
- **Weekly relevance-recompute producer** — spine doc says "do not build until a named friction"; ⚠️ conflicts with roadmap Phase 1 YED-131 nightly recompute. (`market-intel-spine.md:49`)
- **Per-message `email` table** — rejected for inbox v1; revisit if "which email produced this" matters. (ADR-7)
- **Inbox-miner morning cron** — behind the write gate + a measured false-merge rate. (ADR-7 D4)
- **Inbox stub-recovery web fetch** — build only if stub newsletters prove worth it. (`evals/inbox-miner-cohort-v1.md`)
- **Roles → spine producer** — deferred to v1.1 = YED-149. (`role-radar/SKILL.md`)
- **Role-radar coverage gaps** — Hugging Face, Intercom, Rippling, Mistral (no big-3 ATS slug). (same)
- **Doc-KB claim selection design** — manual flag vs. LLM extraction. (`doc-knowledge-base/SKILL.md` Phase B)
- **Hard-delete of dedup-merged entities** — soft-merge + tombstone only past validation. (ADR-4)
- **Capstone 2 (YED-55/56/59)** — canceled; re-issue as an MI lens when a real outreach friction appears. (roadmap §7)
- **Signal Stream / Confluent stretch** — `CREATE AGENT` ReAct agent, HubSpot sink, "GTM Situation Room". (`docs/adr/evidence/plans/scaffold-ask-the-stream…`)
- **Hub future fields** — more scanner sources (Reddit, GitHub Trending, Product Hunt), survivorship policy, edge backfill, coverage penalty, embedding clustering, judge scoring vs. outcomes. (hub `build-arcs.json`)

### Rigor, judge, security
- **OTEL collector + Langfuse / deep-beta OTEL traces / per-model cost accounting** — "rent the platform" only on a named trigger; traces need Anthropic allowlist. (`build-session-contract.md`; `future-state-register.md`)
- **PostHog/Notion projection of judge scores and ADR-8 graph findings** — deferred, no named friction. (ADR-8; `evals/README.md`)
- **Eval-harness deferred table (8 items)** — per-skill rubrics, CI hook on skill PRs, calibration loop, drift dashboard, multi-judge voice quorum, rubric versioning, specialized judges, pre-commit warning. (`future-state-register.md`)
- **Harness-driven Deep Read ledger row (PostToolUse) · `.state` GC + `_pending` scoping · Stop-hook Notion query for `deep_read_rendered: pending`** — stronger enforcement, not built. (`proposals/deep-read-marker-gate.md`; `notes/deep-read-batch-wiring-fix.md`) → YED-141.
- **Graph DB for the system graph / committing the graph cache** — rejected; revisit only on a slow consumer query. (ADR-8)
- **Measurement layer → `alex` plugin promotion / DoD → canonical CLAUDE.md** — gated on ≥1 merged loop-produced fix. (roadmap Phase 3; hub build-arcs)
- **PII Phase 2** — Postgres CHECK/trigger on `person`, retention/TTL ADR, client-bundle scan (into YED-82). (ADR-9)
- **`launchctl setenv`** for Dock-launched sessions — documented, never tested. (memory)
- **YED-25 bootstrap-pattern doc** — defer until the next project needs it. (memory 2026-05-04)

### Program-level (ratified 2026-09-12)
- **Orchid re-tone (YED-125)** — gtm-OS Hub is GTM-owned. · **Clarify stays dead.** · **NY Tech Week harness (YED-67–73), Full-Stack-GTM relics (41/42/46/57)** — canceled.
- **GTM University (YED-98/100/101)** — parked 09-12, **un-parked 09-13 as YED-164** (re-aimed at a GTM agent-engineering JD benchmark); the un-park lives only on unmerged branch `alex/yed-164-roadmap-gtmu-unpark`.
- **Hub: Auth.js `/ops` gate (YED-76)** — Basic-auth v1, OAuth env blank. · **On-demand revalidation webhook** — secret blank. · **Live `/changelog` from GitHub** — hand-curated constant; page not in nav. · **Google Calendar as hub source** — dropped for v1.
- **`esep-media` R2 bucket** for OBS recordings — the named cloud tipping point, untriggered. (memory 2026-09-11)
- **`ESP-jobsearch` worktree** — removed 09-12, recreate when job-search work resumes. (memory)

---

## 2. ROADMAP — planned and sequenced, not started (roadmap v2, Sep 15 → Dec 12)

### Phase 0 — gates & cleanup (→ ~Sep 19)
- **YED-161 denylist enforcement in `/scan-inbox`** — In Progress; code sits on unmerged branch `alex/yed-161-…` (worktree `esep-yed161`, commit `c8eaaae`).
- **Linear reconciled to the plan** — mostly done 09-12; YED-114 still in the gtm-OS Hub project though re-homed to Empire State Hub on paper.
- **OBS live GUI pass + first smoke test** (YED-154 follow-through) — "Done on paper"; the ETL (Scribe transcribe, slide extract, OCR) is "the next build". Work on branch `feat/obs-capture`? — verify; not in current worktree list.
- **YED-81 SEC/PII** — Done 09-13 (#73, ADR-9); residuals listed under Phase 2 PII above and the §8 build-time decisions under Open Questions.

### Phase 1 — close the loops, P1 (~Sep 22 → Oct 17, anchor A1)
- **YED-160 post-event → MI producer** — `/post-event-content` Step 3.9 emits staged claims with transcript provenance; highest-leverage build; depended on YED-81 (now clear).
- **YED-157 B3–B5 `/doc-digest`** — In Progress; 4 lanes, HITL, consumer wiring, extraction eval; must cut a fresh branch (old one deleted). B1+B2 inert until this ships.
- **YED-149 roles → spine producer** — third producer.
- **YED-131 nightly topic recompute** (pg_cron) — unblocks P2 panels; see the spine-doc conflict above.
- **YED-118 doc-KB V2** — still In Progress in Linear on the closed M3 milestone; likely needs closing or re-milestoning.
- **MI remainders:** one-time Notion→graph backfill (`market-intel-backfill.md`) + a real `/scan-trends` run before `/ops/market-intel` shows non-empty state; calibration loop (veracity mechanism 6) as the "marquee fast-follow"; interview-outcome write-back to the graph.

### Phase 2 — the map, P2 (~Oct 20 → Nov 14, anchor A2)
- **YED-126 architecture lens** — Applied-AI Reference Architecture → `signal-taxonomy` v2 + topic remap + hub surface + lens query; ships as code/data only.
- **YED-114 hub topic-intelligence panels + `/system` spine node.**
- **YED-104 T1 audience/conversation intelligence at draft time.**
- **YED-47 hygiene tier-1 in code** — identity, provenance, dedup (0/182 `company.linkedin_url` populated per ADR-1).
- **YED-128 Supabase migrations as spine source of truth** — High, Backlog, not on the roadmap runway.

### Phase 3 — the loop, P3 (~Nov 17 → Dec 12, anchor A3)
- **YED-48 event-research eval harness** (10 golden + judge).
- **YED-162 behavioral-exhaust loop v1** — correction-recurrence ≥N → proposed fix PR → judge-gated → Alex merges.
- **YED-163 ADR-8 Increment 2** (skills↔agents↔commands↔outcomes) — gated on Alex seeing a finding fire in a session he didn't initiate. **Increment 3** (findings ledger, due-pair checks, 5 registry rows) needs a cto-principal-architect pre-mortem first.
- **Measurement → plugin promotion** · **YED-82 hub craft + honesty + launch.**

### Cross-provider judge (YED-109) open roadmap
- Drop "provisional" (~15 independent Approach-B acks ≥80%; was 4/15 on 07-17; "hold the bar" 09-08) · wire dual-judge into `/judge-build` (still manual dual-dispatch) · mechanize the dangling-ref check · specify the quorum merge mechanic.

### Career lane (continuous)
- **YED-151 resume tailor / `/tailor-resume`** · **YED-152 interview-prep reads me-model ICP** · **YED-65 Clay-backed warm outreach** · **YED-145 Google Alerts RSS for voice-radar** · headline test · event deep-dives · theme→post index · monthly floor of ≥1 hiring-manager activation.
- **GTM University v2 (YED-164)** — In Progress, High; 10-stage path + 28 sub-tasks in gtm-os-hub. **YED-165 GTM_OS_HUB hygiene** — In Progress, High.

### Hygiene lane (standing)
- Garbled-name verification · **YED-141 Deep Read gate hardening** · **YED-137 rename content-correspondent** · **YED-129 define ChatPRD's role + retire stale dashboard PRD** · **YED-34 fate of ~50 nested agents/commands subdirs** · **YED-30 Step 5 CLAUDE.md canonical backport** ("ready to execute, needs Alex's approval of the refactor plan") · **YED-135 gtm signal-spine decommission** (dated decommission still pending) · Linear-to-git-truth.
- gtm-OS Hub leftovers still open in Linear: **YED-79** (High), **YED-85**.

---

## 3. OPEN QUESTIONS — genuinely undecided

### Decisions with Alex's name on them
- **Metered Claude:** add an `ANTHROPIC_API_KEY` to Empire or accept the Gemini fallback? Gates YED-156 contextualization, any scripted Claude call, and unattended scheduling. (memory 2026-09-10)
- **Content Pipeline v2 Stage 2:** build all / subset / kick the can — never recorded. (proposal)
- **YED-30 Step 5 refactor plan** — approve or not.
- **Tier-split "go" on the 9-event week** — held at the Step 5 gate 09-12 (4 in-person + RevGenius now, 2 livestreams next, 2 webinars roundup-only). (hub build-journal 2026-09-12)
- **2026-05-27 live run:** ship Path A vs. Path B post, or stagger. (frictions)
- **Apollo 900-credit upgrade** — worth it? Standalone web-UI evaluation.
- **WebSearch cap knob** — file `/feedback` to Anthropic or not.
- **GitHub profile as a proof link** — hold until repos are pinned/curated.
- **Toolbox headline scope** — project-local vs. ecosystem count (`PRIMARY_SCOPE`). (hub spec)
- **Proactive call-outs** — keep by default; trim only if cumbersome. Standing re-check.

### Inbox boundary (Alex-owned)
- Are any `Companies/*` Gmail labels personal/financial (New York Life, Mercury, Brex, Ramp) → denylist?
- Which denylisted-category domains that are also job targets (e.g. `ramp.com`) get a per-purpose override?
- Personal-sender + health-provider lists are placeholder comments.
- "Meta" company alias/parent rule (collision with Meta Superintelligence Labs) — add to alias map after a ruling.
- VC-newsletter canonical URL — prefer the subject company's own URL over the aggregator post?

### PII build-time details (ADR-9 §8, deliberately uncommitted)
- Exact regex set (email; E.164 + US phone) · `linkedin_url` stays tier 2? (default yes) · `bio` refuse vs. redact (default refuse) · timeout unification across writers · the one PII hit in hub `replay.ts` (likely a public post URL).

### ADR-8 / system graph
- Multi-spec `spec_for` precedence · do `tracked` acks auto-expire on Linear Done? · hub projection of the graph.

### Pipeline design, never ratified
- What happens when invite metadata changes after research ran (speaker swap, venue move) — re-research / diff / skip? Deferred to first real edge case.
- Auto-run `/event-deep-research` vs. stage in intake; chain `pre-event-content` or wait; PIPELINE block format.
- **Roles → spine before or after YED-131 recompute?** and **spine-doc "do not build recompute" vs. roadmap YED-131** — one of them is stale.

### Rigor / rubric
- `build-quality@3` candidate cap "API/claim asserted as verified without a citation" — never adopted.
- Mechanize the dangling-ref check — "proposed", not applied.
- **State-drift systems diagnostic (H1/H2/H3)** — evidence note written 09-12 asking for 7 deliverables incl. a "do NOT build this" list; no diagnostic output exists.

### Retrospective questions never answered (execution window closed 06-11)
- Did structured input beat Mode B (prune the unused half)? Did 200-char connection notes get *sent*? Did `/check-new-events` get used weekly? Net effect on publishing rate — never a clean number ("instrument LinkedIn reality, not the Notion status field").

### Legacy docs still formally open
- `PROJECT_BRIEF.md`: Apollo credit refresh cadence · Notion text-property limits · HubSpot `event_associations` custom property.
- `HANDOFF_V2.md`: 9 plan-locking questions (watchlist size, source cost tiers, podcast ingestion, Framer vs. Next, hub v1 JTBD, channels beyond LinkedIn, cadence/auto-publish, budget band, no-scraping rule) — several answered implicitly, none closed in-file.
- `target-companies.md`: Hugging Face ATS slug `_tbd_`; "Nvidia acq. pending".

---

## 4. BLOCKERS — waiting on Alex or on something external

### Waiting on Alex (one action unblocks)
- 🔴 **Inbox denylist v1 review** — `inbox-denylist.md` still "v1 DRAFT — requires Alex's review"; blocks the first whole-inbox scan, the first real inbox write on the clean subset, the spam/deny batch, and the morning cron. Enforcement code (YED-161) is written and sitting unmerged.
- 🔴 **ADR-8 Increment 2** — gated on Alex observing a finding fire usefully in a session he did not initiate.
- **Judge de-provisionalization** — needs ~11 more independent-first-look acks ≥80%.
- **Supabase Advisor remediation (hub DB)** — Alex must paste the live Advisor findings.
- **Two unmerged branches with live worktrees:** `alex/yed-161-…` (`esep-yed161`) and `alex/yed-164-roadmap-gtmu-unpark` (`esep-yed164-roadmap`). Both 1 commit ahead of main; a stale `origin/alex/roadmap-v2-2026-09-12` remote ref also lingers.
- **Hub `src/data/build-journal.json` is modified and uncommitted** on hub `main`; the journal only publishes on hub commit + deploy.

### Spec-artifact debt (DoD item 1)
- ⚠️ **ChatPRD/Notion PRD for the cross-provider judge** — pending since 2026-07-17 across CLAUDE.md, a waiver, and a resume breadcrumb; oldest live debt.
- **ChatPRD one-pager + Notion mirror for ADR-8 / YED-158** and **for the inbox-miner (ADR-7)** — both pending; ADRs are interim specs.
- Stale machine-local plan `~/.claude/plans/check-chatprd-linear-github-tranquil-ripple.md` — refresh or supersede → YED-109.

### Platform / environment (recurring, not fixable in-repo)
- **Agent/skill registry is session-frozen** — every registry-touching build needs a fresh session; cause of the 09-08 and 09-11 judge waivers and the 4-month-old "VALIDATION PENDING" banner in WORKFLOWS.md. **Pronoun-fidelity rule (YED-140/#50) still unvalidated** for the same reason.
- **claude.ai MCP connectors unavailable in subagents** — all Notion/HubSpot/Calendar writes must be parent-thread; `notion-writer` returns a plan, not writes. Also unreachable from shell hooks (no Notion REST key) — shapes the two-layer Deep Read gate.
- **Supabase MCP is on the wrong account** — removed; REST is the only sanctioned path. **Pro credit sits on GTM_OS**, non-transferable.
- **ChatPRD MCP** — cannot create projects or reassign a doc's project; origin 502s under load.
- **PostHog read path** needs a `phx_` key scoped to project 524367 + `query:read`.
- **Apollo** — free plan returns `API_INACCESSIBLE` on people endpoints. **HubSpot Static Lists** unavailable via MCP. **Notion SQL queries** plan-gated. **Clarify** summary-only (rejected).
- **WebSearch cap ~200/session, not tunable** → ~3–4 event fan-outs per session.
- **Env inheritance** — Dock-launched Claude Code skips `~/.zshrc`; worktrees have no `.env` (symlink it). **MCP OAuth needs a real TTY.** **`git fetch/push` blocked by the Bash sandbox** (~75s). **`gh pr merge` is classifier-gated** intermittently.
- **`notion-update-page` mangles `\n`** — author with real newlines. **Prior-session pasted content is lost** — persist transcripts at provide-time.
- **Unattended scheduling** — additionally blocked on the ANTHROPIC-key decision.

---

## 5. MISCELLANEOUS — debt, stale docs, dangling follow-ups

### The rigor loop is itself drifted
- **`/rigor-review` has no entries after 2026-07-17** — ~2 months dark while the registry routes 6 metrics to "weekly review" and thresholds were to be tuned there (none re-tuned since 08-07).
- **DoD waivers (32 rows, 07-11 → 09-12):** spec/PRD waived ×12, judge-not-run ×9 (incl. 09-08 role-radar and 09-11 "run the judge next session" — both unredeemed), Linear waived ×4, ChatPRD→Notion mirror ×5.
- **`correction-recurrence.md`** — class `judge-item-waived-advisory` stuck at count 2 "self-resolving" (it isn't); `gemini-false-flag-from-missing-house-context` advisory-only; dangling-ref mechanization proposed, not applied.
- **`trigger-log.md`** — 16 entries, every one `trigger: ?`; YED-27's signal never accrued.
- **17 of 20 hooks/scripts lack a `Spec:` header** (ADR-8 `unspecced-impl`). Judge run-log emitter should write repo-relative paths (ADR-8 R6). ADR-8 D4(2) over-suppression path accepted, not fixed.
- **Judge is provisional; DoD flags self-attested; telemetry measures effort not outcome value.** (hub build-arcs)

### Stale or superseded docs
- `WORKFLOWS.md` — footer "Last updated 2026-05-07 … VALIDATION PENDING"; four-workflow body ~4 months old.
- `pipeline-operations-guide.md` — "Phase 5 Post-Event: skill not yet built" (false since May).
- `PROJECT_BRIEF.md`, `HANDOFF_V2.md` — April docs with unclosed sections.
- `future-state-register.md` — last touched 06-25 / 04-24; sole home of several deferred tables.
- `YED-96-validation-handoff.md` — resolved, tombstone candidate. `Signal_Pipeline/MOVED.md` — relocation stub.
- `docs/adr/evidence/plans/do-not-make-anything-drifting-locket.md` — status unrecorded; a matched post-performance dataset exists, so probably done.
- `market-intel-schema.sql` provenance header still references the gtm spine ref (ADR-0 follow-up).
- Hub: `toolbox.json` generated 07-30 (counts ~6 weeks stale; `architecture.ts` inherits them) → `pnpm gen:toolbox`. `content-performance.ts` frozen at 08-28. `/changelog` unlinked from nav. 5 journal entries (08-10/11/12/13, 07-22) show "Summary not yet written." Build-diary inbox empty; two job-search diary entries deliberately unmerged into changelog. Stray `Design Inspo/` screenshot. Two orphaned `PHANTOM_TEST_*` keys in `.env.local`.

### Data-quality debt
- **Nori** — HubSpot company `321485812423` + spine row carry `heynori.com`; should be `noriagentic.com`. Never cite dollar figures for Nori Agentic / subconscious.dev.
- **Notion Companies mirror appends for the 13 inbox-miner signals** + that work's PR and `/dod-close` — not done.
- Graph hygiene v1: name-only person dedup can false-merge; some entities lack a company; one name unresolved. Confidence not normalized across producers. Producer liveness inferred from `max(event_date)`, no `producer_run` table.
- ADR-1: 0/182 `company.linkedin_url`; verify the 11 pre-mortem edits landed in the Data-Layer PRD. ADR-0/ADR-4: explicit re-decision of YED-116 (shared taxonomy) still owed.
- **Field-guide spike (Daytona)** — endnote URLs must be attached and early-May CVE numbers verified before any public reuse.
- Post-event brief template: pull pre-event brief from the linked Event page, else "n/a". Transcription: a human audio-verified gold slice on one event still outstanding (Qwen→"Quinn", surname misses).
- Doc-KB V1 backlog: ligature normalization, skip front-matter/TOC, re-ingest before treating numbers as the hybrid baseline.
- Inbox allowlist: GitHub-notification denial holds only while Alex doesn't watch external orgs' repos.
- Steering-v2 smoke test left Deep Read `pending` + HubSpot writes deferred. `deep-read-gate-failures.jsonl` has never logged a failure (gate unexercised).

### Process / infra
- `.git/hooks/pre-commit` is local-only, not version-controlled; branch protection is a local hook, not server-side; PR review is self-review.
- `/ops` is HTTP Basic via proxy, with an `OPS_PASSWORD_PREVIEW` fallback; some panels read snapshots.
- Sharp edges: `recompute_relevance.py` writes by default (`--dry-run`); `spine_client.py` is the single write path (`--selftest`, `--check-writers` before spine PRs); hub `npm run check`; Chrome lives at `/Applications/Tech Stack/`; never make the pipeline repo public.
- Standing periodic reviews with no owner date: voice guidelines quarterly; north-star metrics 6–12 months; registry thresholds weekly.
- Session telemetry shard `.claude/artifacts/build-sessions/<session>.jsonl` churns untracked — never chase it.

### Standing "do not re-litigate" guardrails
- No no-build window · no Clarify · no employment-at-all-costs on gtm-os · don't archive the Linear "Empire State Hub" project · never fire Granola API/MCP · never park a worktree at detached HEAD · never use the Supabase MCP for Empire · Tanny Kang = he/him.
