# Proposal — Clarify as the webinar/meeting capture lane (+ CRM-consolidation decision)

**Status:** DRAFT / handoff spec (2026-09-08). Blocked on a Clarify connection (see §1). Empirically de-risked: Alex captured the GLM-5.3 webinar (9/8) in Clarify's local recorder — video + audio + on-screen slides + auto-notes, as a **non-host attendee**. That was the load-bearing unknown; it's confirmed.

**Why this exists:** webinars entered the schedule (wk of 9/8). Post-event has been manual-upload-anchored since Granola was disabled (2026-05-27). Re-verified 2026-09-08: **Granola MCP connects but has captured 0 meetings in 30 days** — capture side still dead, and it structurally can't grab slides (audio-only), which *are* the content for a webinar. Clarify solves both.

---

## §0 — ⚠️ API REALITY (verified live 2026-09-08 — changes the design)

Probed the Clarify REST API against the real GLM-5.3 capture. **The public API exposes the meeting's AI-generated SUMMARY (rich, structured BlockNote: Overview · Participants+Context · Key Discussion Points · Decisions · Open Questions · Action Items · Rapport) — but NOT the raw transcript, the recording video, or the slide/screen frames.** The object model is CRM-only (`person` / `company` / `deal` / `meeting` / `task`); every transcript / recording / media path 404s (`/meetings/{id}/transcript`, `/recordings/resources`, `objects/recording|transcript|note`, all 404). A `meeting` object carries `recording_enabled: true` + `summary`/`notes` but no media handle.

**Consequence:** the "pull recordings + process screen grabs via the pipeline" vision is **only partly** API-achievable. The API gives Clarify's *synthesis*; the *raw media (transcript verbatim, video, slides)* lives in the app and is a **manual export**. Revised two-tier design in §2. (Open: the MCP or an undocumented endpoint may expose more — a support question to Clarify, not assumed.)

---

## §1 — Connection (RESOLVED — REST via .env, working 2026-09-08)

Clarify's tools are **not** in this session (only Granola/HubSpot/Notion/etc. are). Two ways in:

- **REST via `.env` (RECOMMENDED — pipeline-native, no relaunch).** Add a **Personal API key** + workspace slug to `.env`:
  - `PERSONAL_CLARIFY_KEY=...` (⚠️ **Personal** key — a *Workspace* key lists tools but fails every call; documented footgun)
  - `WORKSPACE_SLUG=alex-yedibalian`  (confirmed 2026-09-08 from app URL `app.clarify.ai/workspaces/alex-yedibalian/home` — the segment after `/workspaces/`)
  - Call `api.clarify.ai/v1/` with headers `Authorization: api-key $PERSONAL_CLARIFY_KEY` + `X-Clarify-Workspace: $WORKSPACE_SLUG`. Matches the Supabase REST-not-MCP precedent (`market-intel-spine.md`).
- **MCP connector (alt).** Add Clarify in claude.ai connectors → **relaunch** Claude Code (MCP list is session-frozen). Native full-CRUD MCP at `api.clarify.ai/mcp` (`create-or-update-records`, `add-comment`, `import-meeting-transcript`, etc.).

Env caveat (`project_claude_code_env_handoff`): Dock-launched Claude Code doesn't inherit `~/.zshrc` — launch from terminal, or put the key in the repo `.env` (preferred here).

---

## §2 — Webinar capture lane (the build)

Reuses the existing post-event machinery; only the **capture + slide-analysis** front is new.

1. **Capture (Alex, live):** Clarify **local recorder** (NOT the bot — bots fail to get admitted to webinars). Join within ~30s of starting or it degrades to transcript-only.
2. **Pull (pipeline) — API gives the SUMMARY only (§0):** via §1, GET `objects/meeting/resources/<id>` → `attributes.summary` (structured BlockNote AI notes) + `participants` + title/date. ⚠️ **No transcript / recording / slides via API.** Resolve to the Notion Event row (title+date, or GCal ID via `event_id`/`ical_uid`).
3. **Two tiers, because the API is summary-only:**
   - **Tier A — automated (DEFAULT for webinars):** Clarify summary → `post_event_brief` (summary-derived, **paraphrase-safe, NO verbatim speaker quotes**) → content. Fast, zero manual step, good "insight" content. This is the old Granola `summary_markdown` pattern, now sourced from Clarify. **Validated on GLM-5.3, 2026-09-08.**
   - **Tier B — full treatment (MANUAL export):** for a webinar worth verbatim quotes + visuals, Alex **exports the transcript + key slide screenshots from the Clarify app** → existing manual path (`event-transcripts/<event>/`) → `transcript-conditioning` (quote-safety) + a **vision pass on the slide images** → full brief. The "screen grabs to analyze" step is **manual export from Clarify (or a live Cmd+Shift+4), NOT an API pull.**
4. **Transcript quality:** if Clarify's transcript proper-noun accuracy is weak, keep the proven `/ingest-recording` ElevenLabs recipe (scribe_v2 + roster keyterms, ~87% vs ~55% recorder-ASR) as the transcript path; Clarify still supplies notes + slides. Decide after one real comparison.
5. **Condition → brief → content:** feed transcript + slide-analysis + Clarify notes into the **existing** flow — `transcript-conditioning` (Step 3.5) → `post_event_brief` (Step 3.7, add a **"Visuals Analyzed"** subsection beyond the current Slides Catalog) → `content-correspondent` (Step 4) → `notion-writer`. **No change downstream of the brief.**

Net-new work = a Clarify pull adapter + the slide keyframe→vision step + one `post_event_brief` subsection. Everything else is reuse.

---

## §3 — CRM consolidation (HubSpot → Clarify): OPEN DECISION for Alex

**Recommendation: adopt Clarify as capture + CRM; do NOT migrate — start fresh via MCP/REST; keep Notion as the durable system of record; leave HubSpot free account dormant as fallback.**

Rationale (holds *because of Alex's situation*): HubSpot is a fresh, near-empty free account → **zero switching cost**; one system does capture + CRM + AI enrichment; native CRUD API keeps the pipeline's programmatic-write pattern. Post-event CRM write (`/post-event-content` Step 5.5, currently HubSpot) would retarget to Clarify (`create-or-update-records` company→person→`add-comment` note), same gated/selective/create-once discipline.

**This is an ADR-level change** (account boundary + post-event data contract; see `docs/adr/`). Do NOT flip the Step 5.5 target until Alex explicitly approves and the §4 unknowns clear. Until then: capture lane on Clarify, CRM write stays HubSpot.

---

## §4 — Guardrails + verify-before-trust (from research 2026-09-08)

- **Free-tier credit ceiling = 1,000 AI credits/mo** (summary 30, prep 30, task 10, field-update 10, deal-detect 20) → **~25–30 AI-enriched meetings/mo**. Recording itself is free/uncapped (20K records). Watch heavy weeks. *(One source says 2,500 — verify live.)*
- ⚠️ **UNKNOWN on free tier: recording retention period, storage caps, data export.** Undocumented. **Verify in-app before trusting Clarify as any kind of store.** This is why Notion stays system of record.
- **macOS-only** local recorder (fine — Alex on Mac). **Personal-not-Workspace** API key.
- **Do the 3-value in-app check** before wiring CRM: (a) credit count, (b) retention, (c) export.

---

## §5 — Next-session execution checklist (once §1 connection is live)

1. Confirm Clarify reachable (`get_account_info` / a REST `GET /v1/...` smoke test).
2. Pull the **GLM-5.3 (9/8)** recording → transcript + notes + slides = **first real end-to-end test** of the lane.
3. Run it through `transcript-conditioning` → `post_event_brief` (with Visuals Analyzed) → `content-correspondent` → `notion-writer`, linked to the GLM Event row (`3d5d3699-c2db-81bb-aff3-e4f2c696c37b`).
4. Compare Clarify transcript quality vs. the ElevenLabs recipe → decide the transcript path (§2.4).
5. Report the 3 verified free-tier values (§4) → then take the §3 CRM decision to Alex.

**Definition-of-Done note:** the actual build (adapter + slide step + Step 5.5 retarget) is non-trivial → PRD (ChatPRD + Notion) + Linear issue + adversarial pass before shipping, per CLAUDE.md DoD gate. This proposal is the pre-build spec, not the build.

---

## References
- `.claude/commands/post-event-content.md` — the flow this extends (Steps 3.5 / 3.7 / 4 / 5 / 5.5)
- `.claude/proposals/post-event-hubspot-step.md` — the Step 5.5 spec that CRM-consolidation would retarget
- `.claude/references/notion-schema.md` — write-destination schemas; `docs/adr/` — data-layer decisions (CRM boundary = ADR)
- Clarify: pricing `clarify.ai/pricing` · recording docs `docs.clarify.ai/en/articles/12407671-meeting-recording` · MCP `docs.clarify.ai/en/articles/13367278-clarify-mcp` · auth `developer.clarify.ai/docs/getting-started/authentication`
