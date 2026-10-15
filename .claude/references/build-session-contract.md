# `build_session` contract (v3)

The stable interface for build-session telemetry. **This contract — not any vendor — is the durable layer** ("instrument once" lives here). Tools (the local JSONL record, PostHog, a deferred OTEL collector + Langfuse) are swappable adapters behind it. Backing: Linear YED-88 · PRD US-2 · plan of record: the Notion roadmap (see CLAUDE.md §3) (retired the machine-local `~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`).

## Principle (build-better-not-faster)
- **Authoritative record first, projection second.** Every session is written to an append-only local record (`.claude/.state/telemetry/build-sessions/<session_id>.jsonl` — one shard per session, GITIGNORED since 2026-09-28/YED-229; the pre-2026-09-12 single file `build-sessions.jsonl` and the pre-2026-09-28 tracked shards under `.claude/artifacts/build-sessions/` are frozen history and still read) — the source of truth. PostHog is a *derived projection* for dashboards; if PostHog changes/breaks, no data is lost.
- **Content-gated by construction.** The record carries **metadata + counts only** — never prompt bodies, tool inputs, or outputs. Satisfies the PII guardrail (YED-81) at the source, not after the fact.
- **Own the contract, rent the platform.** Swapping PostHog for another backend, or adding the deferred OTEL collector + Langfuse, does **not** change this schema or the emitter — it adds an adapter. Non-destructive upgrade path.

## Schema (v2)
One JSON object per session, appended to that session's shard `.claude/.state/telemetry/build-sessions/<session_id>.jsonl` (**storage sharded 2026-09-12, YED-159** — the shared single file was the one guaranteed merge conflict across worktrees; **moved out of git 2026-09-28, YED-229** — sharding fixed the conflicts but not the churn, every Stop still dirtied a tracked file; **v2 2026-09-28**: the three DoD fields were dropped, see below):

| field | type | reliability | meaning |
|---|---|---|---|
| `event` | string | always | constant `"build_session"` |
| `contract_version` | string | always | `"2"` — bump on shape change; never mutate old rows |
| `session_id` | string | always | Claude Code session id (idempotency key) |
| `run_version` | string | always | repo git short-sha (or `nogit`) |
| `project` | string | always | the repo/dir the session ran in |
| `started_at` / `ended_at` | ISO-8601 | ended always; started best-effort | session window |
| `tool_uses` | int | reliable | count of tool invocations |
| `assistant_messages` | int | reliable | count of assistant messages (text/thinking/tool_use are separate messages — not logical "turns") |
| `user_prompts` | int | reliable | count of real user text prompts (excludes tool_result messages) — raw feedback-round signal for the friction vector |
| `tools_used` | string[] | reliable | unique tool names |
| `build_dir_touched` | bool | reliable | did the session Edit/Write under `.claude/{skills,agents,commands,hooks}` (i.e. a "build")? |
| `output_tokens` | int | reliable | sum of `usage.output_tokens` = total generated (incl. thinking) |
| `peak_context_tokens` | int | reliable | last turn's `input_tokens + cache_read_input_tokens` ≈ peak context size |

**Token note (validated vs a real Claude Code transcript, 2026-06-26 — the judge flagged the original):** do **NOT** sum `input_tokens` across turns — it omits cache_read and re-counts the growing context every turn (the cache_read sum reached 145M on one session). Only two honest signals are captured: `output_tokens` (sum = total generated) and `peak_context_tokens` (last turn's input+cache_read ≈ peak context). Precise per-model token/cost is the deferred OTEL-metrics upgrade.

## v1 → v2 (2026-09-28)
v1 rows also carried nullable `dod_met`, `dod_waived`, `correction_rounds`, folded in from a retired `/dod-close` side file. The DoD gate was retired (replaced by `.github/pull_request_template.md`): the fold was present in 3 of 51 sessions and `dod_met` was `true` 34 of 35 times, i.e. no signal above the do-nothing baseline. v2 drops the fields; old rows are not rewritten, and readers must treat them as absent.

## v3 (2026-10-15, YED-259): the `subagent_dispatch` record

v3 adds a second, local-only event; the `build_session` row's shape is unchanged (its `contract_version` now reads `"3"`). Why: the 2026-10-15 routing audit needed a 112-line extractor and six judge passes to learn what one row per dispatch would have shown. The record is the input to concurrency budgets, the "earn a seat" triggers, and the scheduled system review.

**Storage.** `.claude/.state/telemetry/dispatches/<session_id>.jsonl` (gitignored), written by `.claude/scripts/dispatch_record.py`, called from the same Stop hook. The script **rewrites the whole file** from the transcript on every Stop, so it is idempotent and a background agent's final status lands on a later Stop. Never projected to PostHog. Content-gated: no prompt, tool-input or result bodies.

| field | meaning | OTel GenAI analogue (Development status) |
|---|---|---|
| `event` | constant `"subagent_dispatch"` | — |
| `contract_version` | `"3"` | — |
| `session_id`, `tool_use_id`, `seq` | ids; `seq` = dispatch order within the session | `gen_ai.conversation.id` |
| `dispatched_at`, `ended_at` | ISO timestamps; `ended_at` falls back to the subagent's last record if no completion was seen | span start/end |
| `agent` | `subagent_type` (default `general-purpose`) | `gen_ai.agent.name` |
| `description` | the 3-5 word dispatch label (parent-authored, ≤80 chars) | `gen_ai.agent.description` |
| `model_requested`, `model_resolved` | `model:` override, and what the harness actually ran | `gen_ai.request.model`, `gen_ai.response.model` |
| `background`, `isolation` | `run_in_background`, `isolation` inputs | — |
| `prompt_chars`, `handback_chars` | sizes only | — |
| `agent_id` | the subagent id (links to `<session>/subagents/agent-<id>.jsonl`) | `gen_ai.agent.id` |
| `status` | `completed` / `async_launched` (still running) / `failed` / `killed` / `error` | — |
| `is_error`, `error_class` | `cap` (20-agent limit), `spend` (account limit), `stall`, `registry`, `other`, or null | `error.type` |
| `concurrent_at_dispatch` | earlier dispatches still running when this one launched | — |
| `sub_turns`, `sub_tool_calls`, `sub_tool_names` | the subagent's own activity | — |
| `mcp_write_tool_names` | MCP tools the subagent called whose name implies a write | — |
| `duration_s` | first-to-last record of the subagent transcript | span duration |

**Validated 2026-10-15** against four audit sessions: it reproduced the audit's 23 concurrency-cap bounces exactly and found **9** spend-limit kills where the manual audit counted 3 (the audit's extractor missed background failures that arrive as queued notifications). Runtime ≈0.1 s on a 14-dispatch session.

**Known gaps:** no per-dispatch tokens or cost (subagent transcripts carry usage per message; add when the cost ledger is built); no per-event `run_key` (needs the pipeline commands to label dispatches).

## Deferred upgrade (non-destructive) — do NOT build now — recorded in `platform-constraints.md` §Vendors (2026-09-18)
Per the 2026-06-26 decision (lean foundation, defer the platform): the **OTEL collector + Langfuse** path is deferred. Add it only on a named trigger — weekly prompt-level agent-trace debugging, or wanting the deferred Langfuse path's datasets/experiments for the rubric. When added: Claude Code OTEL → collector → relabel to `gen_ai.*` → fan out to {PostHog, the deferred Langfuse}, each writing/deriving this same `build_session` contract. **If the deferred Langfuse is ever adopted, first resolve judge ownership (eval-harness vs that platform) to avoid two judges.**

## Emitter
`.claude/hooks/build-session-emit.sh` (Stop hook). Writes the authoritative JSONL always; POSTs to PostHog `/capture/` only if `$POSTHOG_PROJECT_TOKEN` is set. Disable via `settings.local.json` → `{"hooks":{"disable":["build-session-emit"]}}`.

## PostHog projection (moved from CLAUDE.md 2026-09-28)
Canonical var set, the same in both repos' env files: `POSTHOG_PROJECT_TOKEN` (`phc_`, capture) ·
`POSTHOG_PERSONAL_API_KEY` (`phx_`, query/read; must be scoped to the project + `query:read`) ·
`POSTHOG_PROJECT_API_KEY` (all-access spare) · `POSTHOG_PROJECT_ID=524367` · `POSTHOG_HOST`. The emitter
captures with the project token; the hub dashboard reads with the personal key. Project **524367
(`empire_state_events`)** is the dedicated build-telemetry surface (pipeline writes, hub reads); project
**466893 (`empire state hub`)** is reserved for future hub *web* analytics, not this loop. A project-secret
`phs_` key is rejected by the query API (`platform-constraints.md`).
