# Platform constraints — the one registry (created 2026-09-18, backlog reconciliation)

**What this is.** Environmental constraints that are *not work*: platform, SDK, MCP, env, and vendor limits that shape how everything else is built. Per `linear-convention.md` §Container rule these live here, not in memory files (which now carry one-line pointers) and not as Linear issues. Extends `sdk-runtime-constraints.md` (which keeps the full diagnostic record for the two SDK constraints). Format: **symptom · cause · workaround · since**. Add a row the same turn you hit a new one.

## Claude Code harness
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| Subagents cannot spawn subagents | Anthropic SDK design — `Agent` absent in subagent contexts | fan-out from the parent thread; subagents are text-in/text-out | 2026-05-07 |
| Agent/skill registry is session-frozen | harness reads `.claude/agents/**` once at start | any registry edit needs a FRESH session to validate; batch such validations (YED-190) | 2026-05-07 |
| claude.ai MCP connectors (Notion, HubSpot, Calendar, Gmail, Granola, Gamma) unavailable in subagents and shell hooks | connector auth is parent-thread only; no REST key in repo | all MCP writes inline in the parent; hooks can't query Notion (shapes the two-layer Deep Read gate) | 2026-06-10 |
| Dock-launched Claude Code does not inherit `~/.zshrc` | app launch skips the shell profile | launch `claude` from a terminal for env-dependent hooks; `launchctl setenv` documented, untested | 2026-05-14 |
| git worktrees start with no `.env` | `.env` is gitignored | `ln -s <main-checkout>/.env .env` before running anything env-dependent | 2026-09-08 |
| `git fetch/push` time out (~75s) in the default Bash sandbox | sandbox blocks git network (curl works) | run network git with the sandbox disabled; `timeout` absent on macOS | 2026-09-12 |
| `gh pr merge` is intermittently classifier-gated ("Merge Without Review") | permission classifier | attempt once on Alex's word; if denied hand him `! gh pr merge <n> --merge`; never add a blanket allow | 2026-09-12 |
| WebSearch caps ~200/session; no env var raises it | harness limit (`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` is not real) | ≤3–4 event fan-outs per session; WebFetch primary sources | 2026-08-25 |
| Pasted content from a prior session is not in context | harness | persist transcripts to `event-transcripts/` at provide-time | 2026-05-26 |
| MCP OAuth needs a real TTY | `claude mcp login` can't run via `/mcp` or the Bash tool | run `claude mcp logout <s>` then `claude mcp login <s>` in a plain Terminal window | 2026-06-27 |
| Two live sessions on one checkout churn HEAD / drop commits | shared working tree | one worktree per workstream; `reconciliation-terminal-charter.md` | 2026-08-21 |

## Notion
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| `notion-update-page` mangles `\n` into literal "n" and fuses blocks | MCP escaping | author with REAL newlines; `create-pages` is fine (`notion-write-gotchas.md` conv. m) | 2026-06-01 |
| `old_str` must include `<span discussion-urls=…>` verbatim | comment anchors | copy the span from `notion-fetch` output | 2026-05-26 |
| `notion-query-data-sources` (SQL) is plan-gated | Business + Notion AI plan | reads via `notion-search` + `notion-fetch` only | 2026-07 |
| Notion has no native dedup | product | search before create (rules #10/#11) | 2026-04-09 |

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
| Apollo API blocked on the free plan (`API_INACCESSIBLE` on people endpoints; only `/users/api_profile` works) | plan tier | credits only spendable in the web UI; skill Step 6 skipped; upgrade is a standalone web-UI evaluation | 2026-04-09 |
| Granola app is a waitlist placeholder on Alex's device — records nothing | vendor | NEVER fire the Granola API/MCP; `/post-event-content` is manual-upload anchored; OBS + ElevenLabs Scribe is the capture lane | 2026-05-27 |
| Clarify API is summary-only (no raw transcript/recording/slides) | vendor | Clarify REJECTED — do not re-propose | 2026-09-09 |
| HubSpot Static Lists unavailable via MCP | MCP surface | event association via Notes on the Contact | 2026-04-09 |
| ChatPRD MCP cannot create projects or reassign a doc's project; origin 502s under load | MCP surface | file via `create_document` with the project's `openaiAssistantId`; reorganize in the UI; retry on 502 | 2026-07-22 |
| PostHog query API rejects project-secret `phs_` keys | API scoping | read with a `phx_` personal key scoped to project 524367 + `query:read` | 2026-07-30 |
| Gemini judge seat false-flags convention/anti-pattern criteria without house context | cross-provider blind spot | Gemini's `convention_adherence` / `anti_pattern` votes stay advisory (`cross-provider-judge.md`) | 2026-07-17 |
| Chrome lives at `/Applications/Tech Stack/Google Chrome.app` | non-standard install | `mdfind` it; don't assume `/Applications/Google Chrome.app` | 2026-08-12 |
| Metered Claude: no `ANTHROPIC_API_KEY` in Empire `.env` | decision pending → YED-176 | Gemini-first for scripted LLM steps; build two-backend interfaces | 2026-09-10 |
| OTEL collector / Langfuse / deep-beta traces | "rent the platform" only on a named trigger; traces need an Anthropic allowlist | today only `output_tokens` + `peak_context_tokens` are honest (`build-session-contract.md`) | 2026-06-26 |

## Git / repo
| Constraint | Cause | Workaround | Since |
|---|---|---|---|
| `.git/hooks/pre-commit` is local-only (blocks build-surface on `main`) | hooks aren't versioned | re-install on other clones; branch-first is the real rule (CLAUDE.md Git conventions) | 2026-07-18 |
| The pipeline repo must never be public | holds `.env`, personal CLAUDE.md, private notes | hub repo is the public surface; `npm run check` there | 2026-09-04 |
| `build-sessions/<session>.jsonl` churns untracked | Stop hook | never chase it | 2026-09-12 |
