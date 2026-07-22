# Measurement / build-rigor layer — learnings & gotchas (for review)

Captured 2026-06-25/26 while building the build-rigor + measurement/eval/observability layer (Linear project "Empire State — Build-Rigor & Measurement Layer", YED-87…94). Plan of record: `~/.claude/plans/my-linkedin-on-the-scalable-acorn.md`.

## Decisions that shaped it
- **Re-homed to Empire State, NOT gtm-os** — gtm-os has nothing shipped to measure; the evals are about *this* pipeline's I/O. Dropped gtm-os / single-vs-swarm / job-hunt-system from scope. Focus repos = Empire State Take 3, Empire State Hub, agent-skills.
- **Lean foundation, defer the platform** — own the *contract*, rent the platform. Telemetry = a contract-first Stop hook → authoritative local JSONL → PostHog projection. **Deferred (non-destructive, named-trigger only): OTEL collector + Langfuse.** Build-better ≠ most elaborate; it's the right foundation that won't be redone.
- **Coordinate with eval-harness** as the Tier-2 judge engine (it owns `rubric_version`); this work establishes the shared `.claude/evals/` home it inherits. One judge, not two.
- **Manual rituals before built features** (weekly rubric review, outcome-tagging) — instantiate the loop on human time first; automate only once it proves value.
- **Context engineering: prune, don't summarize.** Full context isn't downside-free even at zero token cost (context-rot + resurrecting reversed decisions). Keep relevant context verbatim; **tombstone** reversed decisions so they don't come back.

## Gotchas (the expensive-to-rediscover ones)
1. **PostHog's OTLP endpoint ingests AI-spans only** — it drops any span whose name/attrs don't start with `gen_ai.`/`llm.`/`ai.`/`traceloop.`. Claude Code emits `claude_code.*` spans → pointing Claude Code OTEL straight at PostHog **silently captures almost nothing**. (Why we chose the hook→capture-event path.)
2. **Claude Code OTEL traces are BETA**; metrics/logs are stable. Don't make a load-bearing metric depend on beta.
3. **A `.env` is NOT auto-loaded into a hook's process.** The Stop hook must `source ./.env` itself (guarded). Otherwise `$POSTHOG_PROJECT_TOKEN` is never seen.
4. **Transcript token math is a trap (judge caught this).** Summing `usage.input_tokens` across turns is meaningless — it omits `cache_read_input_tokens` and re-counts the growing context every turn (`cache_read` summed to **145M** on one session). Honest signals only: `output_tokens` (sum = total generated) + `peak_context_tokens` (last turn `input + cache_read`). Validated against a real transcript at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`.
5. **Stop hooks emit a top-level `systemMessage`** — NOT `hookSpecificOutput.additionalContext` (the validator rejects it on Stop).
6. **`notion-query-data-sources` (SQL) is plan-gated** (needs Business + Notion AI). Use `notion-search` (data-source-scoped) + `notion-fetch` for reads/dedup.
7. **PostHog ingest key = the PROJECT/publishable `phc_` key**, NOT the personal `phx_` API key (the MCP's key). Different keys.
8. **Judge circularity** — Claude judging Claude has self-preference bias. The judge is **advisory** until ≥20 runs reach ≥80% human (`alex_ack`) agreement; it scores+flags, never rewrites/blocks.
9. **Linear `save_issue.blockedBy` is append-only** — create all issues first, then wire deps in a second pass.
10. **Real-transcript schema** (Claude Code, 2026-06): lines have top-level `.type` (assistant/user/system/…), `.timestamp`, `.message.content[]` (text|thinking|tool_use), `.message.usage{input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens}`.
11. **jq's `//` operator treats `false` as empty, not just `null` (bit the emitter 2026-07-11).** `.dod_met // null` silently collapses a legitimate `dod_met:false` → `null`. Once the semantic fields can be `false` (not just absent), extract with `if has("dod_met") then .dod_met else null end`, never `// null`. This was latent while the fields were always null; the `/dod-close` sandbox test surfaced it.
12. **A session can name its own build_meta file deterministically:** `$CLAUDE_CODE_SESSION_ID` in an in-session Bash call == the `.session_id` the Stop hook emits (verified identical). It is **`CLAUDE_CODE_SESSION_ID`**, not `CLAUDE_SESSION_ID` (that one is unset). Must be written from the MAIN conversation (subagents get a child context); `_pending.build_meta` + Stop-hook reconciliation is the fallback.

## What's live (cycle-1)
- DoD gate (CLAUDE.md `<definition_of_done>`) — **now WIRED to telemetry (2026-07-11)** via `/dod-close` → `.claude/hooks/dod-close.sh` → `.claude/.state/<session>.build_meta` (the missing writer; before this, `dod_met`/`dod_waived`/`correction_rounds` were null in 100% of rows) + the `dod-waivers.jsonl` reason log · 3 signal scanners (`/scan-trends|roles|voices`) · telemetry hook (`build-session-emit.sh` + `build-session-contract.md`) · the judge (`/judge-build`, `.claude/evals/`, still advisory — 1 of ~20 calibration). **PostHog projection LIVE** (`POSTHOG_PROJECT_TOKEN` set; dedicated project 524367 as of 2026-07-22).
- **Still to run (the loop's remaining half):** a judge-calibration batch on unjudged artifacts + the first `/rigor-review` (seeds `correction-recurrence.md`). Both need Alex acks — deferred from the build session by design.
