# SDK runtime constraints (added 2026-05-07 — orchestrator → synthesizer pivot)

Resolved-diagnostic record. Extracted from CLAUDE.md 2026-06-02 to keep always-loaded context
lean — content is unchanged. These constraints are durable and govern every agent/command design
in `.claude/`. See also `.claude/WORKFLOWS.md` for the orchestration rerun manual.

**Subagents cannot spawn other subagents.** This is an Anthropic SDK runtime constraint, not configurable via frontmatter or settings. The `Agent` tool (formerly `Task` — renamed in v2.1.63, both names alias) is not exposed to subagent contexts. The constraint exists by design to prevent runaway nesting.

**Implication for any "orchestrator" pattern:** any workflow that needs to fan out specialists must run that fan-out from the parent thread (the slash command's main conversation), not from inside another subagent. Synthesis-only agents (text in, text out, no dispatch) are fine as subagents.

**Confirmation:**
- Official docs: [code.claude.com/docs/en/sub-agents.md](https://code.claude.com/docs/en/sub-agents.md) — *"Subagents cannot spawn other subagents. If your workflow requires nested delegation, use Skills or chain subagents from the main conversation."*
- Empirical: 6-agent layer-by-layer test (2026-05-07) confirmed `Task`/`Agent` is absent from every subagent's tool surface — directly callable AND deferred-via-ToolSearch — across the orchestrator + 4 specialists + notion-writer. `ToolSearch select:Task,Agent` returned "No matching deferred tools found" in 5/5 attempts.

**Pivot landed 2026-05-07:** `event-research-orchestrator` agent deleted; replaced by `event-research-synthesizer` (text-in, brief-out, `tools: Read`). `/event-deep-research` Step 2 now dispatches the four specialists in parallel **from the parent thread**, then Step 2.5 dispatches the synthesizer. See WORKFLOWS.md "✅ Resolved 2026-05-07" for the full diagnostic record.

**Related fix landed same day — frontmatter `tools:` discipline:**
`notion-writer` was failing with `"Prompt is too long"` because its frontmatter had no `tools:` line, so it inherited the parent's full ~250-tool deferred list. With Haiku's smaller effective context window, the pre-flight harness check rejected invocations before the agent ran (`total_tokens: 0, tool_uses: 0`). Fixed by scoping `tools:` to Notion MCP + Read only. All 4 research specialists got `tools: WebSearch, WebFetch, Read` for hygiene.

**Best-practice rule going forward:** every subagent in `.claude/agents/` should declare an explicit `tools:` frontmatter line scoped to the minimum tools it needs. This prevents context bloat AND makes the agent contract reviewable at a glance. The pattern is established by `systems-analyst.md` (`tools: Read, Bash, WebSearch, WebFetch, Grep, Glob`) and now applied to the entire event-pipeline agent set.

**What this means for YED-24** (Wire systems-analyst into commands/agents architecture): systems-analyst CAN be dispatched from a slash command's parent thread (where `Agent` is available) — that path is unaffected. systems-analyst CANNOT be dispatched from inside another subagent's context (e.g., as a step inside event-research-synthesizer). Plan slash-command integration accordingly.

**Second SDK constraint (discovered same day) — the agent registry is session-frozen.** The harness loads the list of available agents from `.claude/agents/**/*.md` ONCE at conversation start and uses that registry for the rest of the session. Edits, additions, and deletions to agent files mid-conversation are saved to disk but are NOT reflected in the live registry. Confirmed empirically 2026-05-07: after deleting `event-research-orchestrator.md` and creating `event-research-synthesizer.md` mid-conversation, the runtime still listed `event-research-orchestrator` as available and could not find `event-research-synthesizer` (or any other newly-named agent like `notion-writer-v2`). **Validation rule:** any change to a `.claude/agents/` file requires a FRESH conversation to test. Mid-session edits cannot be smoke-tested in the same session that made them. This is the same root cause as the long-standing "custom agent discoverability mid-conversation is unreliable" gotcha noted in WORKFLOWS.md, but applies more broadly than just newly-created agents — it applies to ALL agent definition changes (frontmatter, body, model, tools, name).
