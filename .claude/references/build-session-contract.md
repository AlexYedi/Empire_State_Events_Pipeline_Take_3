# `build_session` contract (v1)

The stable interface for build-session telemetry. **This contract — not any vendor — is the durable layer** ("instrument once" lives here). Tools (the local JSONL record, PostHog, a future OTEL collector + Langfuse) are swappable adapters behind it. Backing: Linear YED-88 · PRD US-2 · plan `~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`.

## Principle (build-better-not-faster)
- **Authoritative record first, projection second.** Every session is written to an append-only local record (`.claude/artifacts/build-sessions.jsonl`) — the source of truth. PostHog is a *derived projection* for dashboards; if PostHog changes/breaks, no data is lost.
- **Content-gated by construction.** The record carries **metadata + counts only** — never prompt bodies, tool inputs, or outputs. Satisfies the PII guardrail (YED-81) at the source, not after the fact.
- **Own the contract, rent the platform.** Swapping PostHog for another backend, or adding the deferred OTEL collector + Langfuse, does **not** change this schema or the emitter — it adds an adapter. Non-destructive upgrade path.

## Schema (v1)
One JSON object per session, appended to `build-sessions.jsonl`:

| field | type | reliability | meaning |
|---|---|---|---|
| `event` | string | always | constant `"build_session"` |
| `contract_version` | string | always | `"1"` — bump on shape change; never mutate old rows |
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
| `dod_met` / `dod_waived` | bool/null | optional | set later by the DoD wiring (US-1) via `.claude/.state/<session>.build_meta` |
| `correction_rounds` | int/null | optional | set later by the judge/DoD wiring (US-3/US-7) |

**Token note (validated vs a real Claude Code transcript, 2026-06-26 — the judge flagged the original):** do **NOT** sum `input_tokens` across turns — it omits cache_read and re-counts the growing context every turn (the cache_read sum reached 145M on one session). Only two honest signals are captured: `output_tokens` (sum = total generated) and `peak_context_tokens` (last turn's input+cache_read ≈ peak context). Precise per-model token/cost is the deferred OTEL-metrics upgrade.

## Forward-compatibility seam
Semantic fields (`dod_met`, `dod_waived`, `correction_rounds`) are nullable. The DoD gate (US-1) and judge (US-3) write them to `.claude/.state/<session>.build_meta` during the session; the Stop hook folds them into the record. So those features light up the same contract without changing it.

## Deferred upgrade (non-destructive) — do NOT build now
Per the 2026-06-26 decision (lean foundation, defer the platform): the **OTEL collector + Langfuse** path is deferred. Add it only on a named trigger — weekly prompt-level agent-trace debugging, or wanting Langfuse's datasets/experiments for the rubric. When added: Claude Code OTEL → collector → relabel to `gen_ai.*` → fan out to {PostHog, Langfuse}, each writing/deriving this same `build_session` contract. **If Langfuse is adopted, first resolve judge ownership (eval-harness vs Langfuse) to avoid two judges.**

## Emitter
`.claude/hooks/build-session-emit.sh` (Stop hook). Writes the authoritative JSONL always; POSTs to PostHog `/capture/` only if `$POSTHOG_PROJECT_TOKEN` is set. Disable via `settings.local.json` → `{"hooks":{"disable":["build-session-emit"]}}`.
