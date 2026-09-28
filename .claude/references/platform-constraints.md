# Platform constraints — the one registry (created 2026-09-18, backlog reconciliation)

**What this is.** Environmental constraints that are *not work*: platform, SDK, MCP, env, and vendor limits that shape how everything else is built. Per `linear-convention.md` §Container rule these live here, not in memory files (which now carry one-line pointers) and not as Linear issues. The two SDK rows below absorbed `sdk-runtime-constraints.md` on 2026-09-28 (full diagnostic in git history). Format: **symptom · cause · workaround · since**. Add a row the same turn you hit a new one.

## Claude Code harness
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| Subagents cannot spawn subagents | Anthropic SDK design — `Agent` (alias `Task`, renamed v2.1.63) is absent from every subagent's tool surface, direct and via ToolSearch; not configurable ([docs](https://code.claude.com/docs/en/sub-agents.md)) | fan-out from the parent thread; subagents are text-in/text-out (the 2026-05-07 orchestrator → `event-research-synthesizer` pivot) | 2026-05-07 |
| Agent/skill registry is session-frozen | harness reads `.claude/agents/**` once at start; mid-session edits, additions and deletions (frontmatter, body, model, tools, name) are saved but not loaded | any registry edit needs a FRESH session to validate; batch such validations (YED-190) | 2026-05-07 |
| A subagent with no `tools:` line inherits the parent's full (~250) deferred-tool list and can fail pre-flight with "Prompt is too long" (`total_tokens: 0`), worst on Haiku | frontmatter default | every agent declares a minimal `tools:` line (CLAUDE.md invariant 6) | 2026-05-07 |
| claude.ai connector **writes** must run in the parent thread; connectors are unavailable in shell hooks. **Reads are NOT blocked:** a subagent that declares a Gmail read tool can call it (live test 2026-09-19: `company-researcher` ran `search_threads` successfully). The 2026-06-10 failure was the since-retired `notion-writer` agent *writing* to Notion from a subagent; other connectors are untested either way | connector auth + the injection guard (a model reading untrusted text gets no write tools) | all MCP **writes** inline in the parent; hooks can't query Notion (shapes the two-layer Deep Read gate); delegating a *read* is allowed when the agent's `tools:` line declares it | 2026-06-10, corrected 2026-09-19 (YED-203) |
| Dock-launched Claude Code does not inherit `~/.zshrc` | app launch skips the shell profile | launch `claude` from a terminal for env-dependent hooks; `launchctl setenv` documented, untested | 2026-05-14 |
| git worktrees start with no `.env` | `.env` is gitignored | `ln -s <main-checkout>/.env .env` before running anything env-dependent | 2026-09-08 |
| git worktrees also lack the gitignored private refs (`me-model.md`, `target-companies.md`, `inbox-denylist.md`) → `check-refs.sh` reports them missing and the judge caps completeness ≤0.60 (false dangling-ref) | gitignored by the public-repo privacy rule; auto-mode classifier denies symlinking them in (sensitive provenance) | with Alex's explicit go, `ln -s <main-checkout>/.claude/references/<f>.md` for each (verified 2026-09-18: stays gitignored, check-refs clean); never pass a private file as `--spec-file`; never accept a cap caused by this | 2026-09-18 |
| `git fetch/push` time out (~75s) in the default Bash sandbox | sandbox blocks git network (curl works) | run network git with the sandbox disabled; `timeout` absent on macOS | 2026-09-12 |
| `gh pr merge` is intermittently classifier-gated ("Merge Without Review") | permission classifier | attempt once on Alex's word; if denied hand him `! gh pr merge <n> --merge`; never add a blanket allow | 2026-09-12 |
| WebSearch caps ~200/session; no env var raises it | harness limit (`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` is not real) | ≤3–4 event fan-outs per session; WebFetch primary sources | 2026-08-25 |
| Pasted content from a prior session is not in context | harness | persist transcripts to `event-transcripts/` at provide-time | 2026-05-26 |
| MCP OAuth needs a real TTY | `claude mcp login` can't run via `/mcp` or the Bash tool | run `claude mcp logout <s>` then `claude mcp login <s>` in a plain Terminal window | 2026-06-27 |
| Linear's legacy `/sse` MCP endpoint is dead | vendor | the project `linear` server in `.mcp.json` uses `type: http`, `https://mcp.linear.app/mcp`; clear a stale token with `claude mcp logout linear` first. The project server works inside subagents (its tools are deferred there: `ToolSearch select:mcp__linear__…` before calling) | 2026-06-27 |
| `Stop` hooks fire at the end of every TURN, not at session close | harness | a Stop-hook gate must stay silent while a run is in progress (key it on the live event claim) and evaluate at claim release/expiry. Never wait on background work by ending turns: a blocking Stop hook re-invokes the model with full context and burns tokens in a loop. Use `run_in_background` + its completion notification, or Monitor | 2026-09-27 |
| ~10% of fresh TCP connects stall on the SYN (every host: Supabase, Notion, Linear, Google) | local Wi-Fi/router/ISP, not a vendor | reuse one keep-alive connection: new REST code goes through `spine_client.req`; never a per-call `urlopen` loop. A "mysteriously slow" script or `urlopen … timed out` → suspect this first (YED-149, PR #151) | 2026-09-27 |
| Two live sessions on one checkout churn HEAD / drop commits | shared working tree | one worktree per workstream; `reconciliation-terminal-charter.md` | 2026-08-21 |

## Notion
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| `notion-update-page` mangles `\n` into literal "n" and fuses blocks | MCP escaping | author with REAL newlines; `create-pages` is fine (`notion-write-gotchas.md` conv. m) | 2026-06-01 |
| `old_str` must include `<span discussion-urls=…>` verbatim | comment anchors | copy the span from `notion-fetch` output | 2026-05-26 |
| `notion-query-data-sources` (SQL) is plan-gated | Business + Notion AI plan | reads via `notion-search` + `notion-fetch` only | 2026-07 |
| Notion has no native dedup | product | search before create (CLAUDE.md invariant 8) | 2026-04-09 |

## Supabase
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| Supabase MCP is READ-ONLY for Empire; DDL via MCP declined | MCP DML bypasses the ADR-9 PII guard in `spine_client.py`; 2026-06-28 rule stands | REST + `spine_client.py` for writes; DDL = dashboard paste from repo migrations after a twin rehearsal; MCP for `get_advisors`/`list_*`/SELECT only; connector reaches the canonical project since 2026-09-17 | 2026-09-18 |
| Product Pass Pro credit sits on the GTM_OS org, non-transferable | org-scoped credit | do NOT reparent Empire projects; free tier covers the doc-KB; blobs on R2 | 2026-09-10 |
| `recompute_relevance.py` writes by default | script design | pass `--dry-run` to preview | 2026-09-13 |
| Producer liveness is inferred from `max(event_date)` | no `producer_run` table | YED-114 panel fix | 2026-07 |

## Vendors
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| Apollo free plan: **people data blocked**. `people/match`, `mixed_people/api_search`, `mixed_companies/search` and `organizations/{id}` all return 403 `API_INACCESSIBLE` ("not included in your Free plan"). **Works:** `GET organizations/enrich?domain=` (firmographics, ~267 technologies, parent-org ID), `contacts/search` over your own saved contacts, and `labels`. Free = 900 credits/seat/yr, granted monthly | plan tier. It is **not** key scoping: the same endpoints are blocked on all three scoped keys (`APOLLO_GTM_CONTACT_API`, `APOLLO_GTM_ORG_API`, `APOLLO_GTM_OBJECTS`) | use Apollo for company lookup only; people data needs Basic ($49/mo annual), the cheapest paid tier; master key / sequences need Organization ($119/user, 3-seat minimum). Upgrade stays a standalone decision | 2026-04-09, re-verified live 2026-09-27 (YED-234) |
| Clay free plan: 500 actions + 100 data credits/mo, 200 rows/table. **Connector works:** `search-companies` returns firmographics without enrichment; `add-company-data-points` (e.g. Tech Stack) works but the connector doesn't report credit cost and tech-stack output is noisy. Search DSL: no `location` field; `is_similar_to` only on job titles / `products_and_services`. Audiences, webhooks, HTTP API columns, signals and HubSpot sync are Growth ($495/mo) | plan tier + connector surface | enrich selectively; check spend on Clay's usage page. `CLAY_GTM_API` authenticates (403 "Insufficient permissions" on `/v3/me`, vs 401 when invalid) but the developer-API endpoints and CLI install are **unmapped**; map them from https://developers.clay.com/ (the HTTP API integration doc, https://university.clay.com/docs/http-api-integration-overview, covers the Growth-plan table-column feature, not the developer API). Other vendor API docs: Apollo https://docs.apollo.io/reference/apollo-api · Sumble https://docs.sumble.com/api/api. Spending Clay credits = Alex's call (Tier 3) | 2026-09-27 |
| Sumble free API works: `POST https://api.sumble.com/v9/organizations`, Bearer `SUMBLE_GTM_API`; 500 credits/mo (1 per matched org + 1 per paid attribute; `id/name/slug/url` free); 402 before any unaffordable call; first page of search results only. Returns `parent_id`/`subsidiary_ids` (a real hierarchy), teams, technographics. **Data quality:** duplicate subsidiaries, junk records, stale M&A (Brex had no parent despite the Capital One acquisition on 2026-04-07) | vendor data | treat as a source to verify, not truth; record source + as-of date per fact (YED-234). The Claude connector for Sumble is paid-only; use the REST API. Pro $99/mo | 2026-09-27 |
| Granola records webinars on the desktop (2026-09-18), but its MCP sees ZERO notes: the connector is authorized as `alex.e.yedi@gmail.com` (free plan), which excludes workspace notes | vendor plan tier | do not rely on the Granola API/MCP; `/post-event-content` is manual-upload anchored. For RevGenius/Goldcast webinars use the Goldcast on-demand PUBLISHER transcript first; otherwise manual paste → `event-transcripts/` → transcript-conditioning. **Supercut** (Pro, 2026-09-28) is the recording/transcript source (`.claude/references/supercut.md`); ElevenLabs Scribe (`/ingest-recording`) re-transcribes any audio when diarized speakers are needed | 2026-05-27, updated 2026-09-28 |
| Clarify API is summary-only (no raw transcript/recording/slides) | vendor | Clarify REJECTED — do not re-propose | 2026-09-09 |
| HubSpot Static Lists unavailable via MCP | MCP surface | event association via Notes on the Contact | 2026-04-09 |
| ChatPRD MCP cannot create projects or reassign a doc's project; origin 502s under load | MCP surface | file via `create_document` with the project's `openaiAssistantId`; reorganize in the UI; retry on 502 | 2026-07-22 |
| PostHog query API rejects project-secret `phs_` keys | API scoping | read with a `phx_` personal key scoped to project 524367 + `query:read` | 2026-07-30 |
| The judge refuses gitignored / symlinked / out-of-repo evidence (exit 3, no override) | `judge_lib.privacy_guard`: a public repo must never leak a private ref to a provider | pass ad-hoc spec text with `--context`; spec FILES must be tracked and inside the repo. In a worktree the private refs are symlinks, so they are refused by construction | 2026-09-19 |
| Chrome lives at `/Applications/Tech Stack/Google Chrome.app` | non-standard install | `mdfind` it; don't assume `/Applications/Google Chrome.app` | 2026-08-12 |
| Metered Claude: no `ANTHROPIC_API_KEY` in Empire `.env` | RULED 2026-09-18 (YED-176): Gemini fallback is the default | Gemini-first for scripted LLM steps behind a two-backend interface; add a Claude key only when a scripted Claude call is on the runway (YED-179 re-asks) | 2026-09-18 |
| OTEL collector / Langfuse / deep-beta traces | "rent the platform" only on a named trigger; traces need an Anthropic allowlist | today only `output_tokens` + `peak_context_tokens` are honest (`build-session-contract.md`) | 2026-06-26 |

## LinkedIn (added 2026-09-21)

- **Unauthenticated fetch of any LinkedIn URL returns HTTP 999.** This is a block, not evidence of
  absence — never record "profile not found" or infer a person doesn't exist from a 999.
- **Worse than the 999: WebFetch can return FABRICATED LinkedIn content (2026-09-27).** Behind the login
  wall, the fetch summarizer invented a "recent posts" list for a speaker, with dates after the fetch
  date. Search snippets also conflate "Clay partner" with "worked at Clay": Andreas Wernicke was listed
  as a former Clay employee, and Alex confirmed he never was (he led Clay Club NY as a non-employee).
  Rule: a LinkedIn-sourced employer, tenure, or post claim is `UNVERIFIED` until confirmed by a fetched
  post URL, the person's own non-LinkedIn page, the Chrome MCP read path below, or Alex.
- **The working read path is the Claude-in-Chrome MCP against Alex's already-authenticated session.**
  Verified 2026-09-21: navigated to `/messaging/`, opened a thread, read the full exchange. This is how
  to check what a message actually says instead of drafting blind.
  - **Read-only by policy.** Never send, reply, react, or connect from the browser session — outbound
    LinkedIn action is Tier 3 (Alex's call, every time). Reading an existing thread to ground a draft
    is fine; putting words on his account is not.
  - **Check before drafting.** On 2026-09-21 a thread recorded as "unread and unanswered" turned out to
    have **two replies from Alex already in it**. Two openers had been drafted for a problem that did
    not exist. One screenshot would have prevented both.
- **Luma is authenticated in the same browser session** — calendar Follow/Unfollow works directly
  (`lu.ma/<slug>`, button top-right of the calendar header). Following a calendar is a persistent
  subscription, so it needs Alex's say-so first; it is not a read.

## ATS boards (added 2026-09-21)

- **A wrong board slug usually returns HTTP 200, not 404.** Greenhouse/Ashby boards are namespaced by
  string, and unrelated companies hold plausible names. **A 200 is not identity verification** —
  always read a job's title/location/description text and confirm it is the intended company before
  writing a slug into the registry. Three live traps found in one session: `ashby/runway` (different
  company), `greenhouse/profound` (Boston biotech), `greenhouse/flourish` (wealth-management fintech).
  Full list + the correct slugs: `.claude/references/target-companies.md`.

## Tombstones (removed tools/decisions — mechanically checked, YED-201 Fix 2A, 2026-09-19)
A removal only sticks if it reaches every file that *uses* the removed thing. `.claude/hooks/check-tombstones.py` flags any line in `.claude/**` / `docs/**` (docs + code/config files) that names a term below **without** a removal marker within 40 characters (removed · retired · ripped · deprecated · tombstone · vestigial · killed · rejected · disabled · superseded · replaced · no longer · do not · never · legacy · historical). The judge runs it in Step 0 (the reviewer sees the hits as fact); run `--all` by hand for a repo-wide sweep. **Add a row the same turn you remove something.** Patterns are Python regex, case-sensitive; write a regex alternation `|` as `\|` (GitHub's table escape; the checker unescapes it).

| Term | Pattern | Removed | Use instead |
|---|---|---|---|
| Gamma | `\bGamma\b` | 2026-08-07 | Claude HTML/SVG → Artifact → PDF; Gemini for pictorial (`visual-briefs.md`) |
| Gamma MCP | `mcp__claude_ai_Gamma` | 2026-08-07 | same |
| Canva as a generator | `Canva(\'s)? (MCP\|fallback\|account\|editor\|auto-render)` | 2026-08-07 (vestigial) | same (Canva the *company* is not tombstoned) |
| Canva MCP | `mcp__claude_ai_Canva\|generate-design` | 2026-08-07 | same |
| Langfuse | `Langfuse` | 2026-06-26 | the lean stack: Notion + PostHog + Hub (`docs/history.md`) |
| gtm-os as the measurement layer | `gtm-os(?!-hub)[^.\n]{0,40}(measure\|telemetry\|observab\|eval\|trace)` | 2026-06-26 | same (bare "gtm-os" is the live GTM-OS program / Linear team; gtm-os-hub is live too) |
| Granola auto-fetch | `Granola[^.\n]{0,40}(fetch\b\|API\|MCP\|get_meeting)` | 2026-05-27 | Supercut transcript (`supercut.md`) or manual paste; ElevenLabs Scribe for audio |
| Clarify | `mcp__claude_ai_Clarify` | 2026-09-09 | HubSpot stays the CRM; Supercut + Scribe for capture |
| OBS capture lane (OBS Studio config + `obs_ingest.py` ETL) | `\bOBS\b\|obs_ingest\|obs-capture` | 2026-09-28 | Supercut recordings → `/post-event-content` Step 2 (`supercut.md`); `/ingest-recording` for any audio file |
| gemini-judge.sh (Gemini judge seat) | `gemini-judge\.sh` | 2026-09-28 (YED-231) | one Sonnet reviewer: `/judge-build`, spec `judge.md` |
| openai-judge.sh / openai_judge.py (OpenAI shadow seat) | `openai[-_]judge\.(sh\|py)` | 2026-09-28 (YED-231) | same |
| quorum-merge.sh / quorum_merge.py (multi-seat quorum) | `quorum[-_]merge(\.sh\|\.py)?` | 2026-09-28 (YED-231) | same; one seat, no quorum |
| run-canaries.sh (seat canaries / trust ladder) | `run-canaries(\.sh)?` | 2026-09-28 (YED-231) | same; no calibration gating |
| merge_topics.py (hard-delete merge) | `merge_topics(\.py)?` | 2026-09-27 (YED-47) | `substrate.py merge --table T --from A --into B --reason "…"` — human-only, reversible soft-merge (`--revert`); tombstones, never deletes (ADR-4 D3) |
| /dod-close + dod-close.sh (DoD gate) | `dod-close\|build_meta` | 2026-09-28 | `.github/pull_request_template.md` (3 checkboxes, no waiver log) |
| /rigor-review (weekly review) | `rigor-review` | 2026-09-28 | nothing scheduled; ask for a review when there is a question |
| value-action-registry.md | `value-action-registry` | 2026-09-28 | the null-baseline rule in CLAUDE.md §5; outcomes via `/tag-outcome` |
| correction-recurrence log | `correction-recurrence` | 2026-09-28 | the second-fix stop rule (`second-fix-stop-rule.md`) |
| notion-writer agent | `notion-writer` | 2026-09-28 | inline parent-thread writes; mapping in `notion-schema.md` §Write order |

## Git / repo
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| `.git/hooks/pre-commit` is local-only (blocks build-surface on `main`) | hooks aren't versioned | re-install on other clones; branch-first is the real rule (CLAUDE.md §5 Git) | 2026-07-18 |
| Both repos are PUBLIC by design: build in public (ruled by Alex 2026-09-19; supersedes the 2026-09-04 "never public" row) | transparency, engagement, and a portfolio hiring managers can read | follow `build-in-public.md`: secrets stay in `.env`; personal refs stay gitignored; third-party confidences get redacted before commit. **Open:** GitHub still serves pre-purge commits via `refs/pull/*` (#56–#76), which only GitHub Support can remove (YED-204) | 2026-09-19 |
| Canceling a Linear issue auto-CLOSES (not merges) an open PR whose body says "Closes YED-n" | Linear↔GitHub integration | merge the PR first, then change the issue; or write "Refs YED-n". After any Linear state change, check `gh pr view <n> --json state` | 2026-09-27 |
