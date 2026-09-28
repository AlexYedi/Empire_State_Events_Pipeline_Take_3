# How this project got here

An archive, not a rulebook. The live rules are in `CLAUDE.md`; the plan of record is
the Notion roadmap (https://app.notion.com/p/3e9d3699c2db8163919afb3040099d3c); data-layer decisions are in `docs/adr/`. This page holds the narrative
that used to sit in `CLAUDE.md` before the 2026-09-28 complexity reset cut it from ~6,500 to ≤1,800 words.

## April 2026: the founding idea

**Predecessor.** `new-jack-city-events-pipeline` (AlexYedi/new-jack-city-events-pipeline) tried full automation
with n8n: Google Calendar → Claude research → Notion/Supabase writes. The GCal intake (YED-6) worked; research and
content (YED-12/13/14) failed repeatedly at the integration layer (Notion API chunking, n8n expressions inside
loops, HTTP body serialization). Paused. Its prompts, field mappings and content templates were the reference
material for this repo.

**The insight.** Separate "do great research" from "put it in the right places." Claude skills became the research
and content engine; MCP connectors write directly to Notion and HubSpot; no middleware. Human-in-the-loop by design:
Alex reviews as research is generated, which improved quality and removed the fragile automation chain. Two founding
principles came with it: research quality is the value and distribution is plumbing; and the human review step is
not automated away, only moved later in the pipeline over time.

**The original brief.** Alex pasted a calendar invite plus cues ("Speaker: …", "Host: …", "Topics: …"). Research had
five equally weighted sections: topics deep enough to hold a real conversation; hosts and speakers (small worlds,
often at target companies); companies (target employers and industry players); content generation (LinkedIn posts,
outreach) toward a "full-stack GTM" positioning; and the **documentarian angle**, Alex's edge as a frequent recorder
of ephemeral NYC AI/tech events that otherwise go unshared.

## The phased roadmap (Q2 2026)

- **Phase 1: event research.** A monolithic `event-research` skill, rebuilt 2026-05-04 as the multi-agent
  `/event-deep-research` (four parallel specialists → synthesizer → Notion writes). On 2026-05-07 the orchestrator
  agent was replaced by a synthesizer because subagents cannot spawn subagents; fan-out moved to the parent thread.
  `/check-new-events` (2026-05-20) added calendar-as-intake via a PIPELINE block in the invite description; in
  practice most invites have no block and the command parses the raw description.
- **Phase 2: content.** `pre-event-content`, `content-correspondent` (post-event) and `pattern-synthesis`
  (two-thesis posts from two briefs, max one a week). `/post-event-content` (2026-05-21) anchored post-event work on
  a transcript; Granola auto-fetch was disabled 2026-05-27. Speaker outreach became 200-character connection notes
  (2026-05-20) because LinkedIn free tier blocks DMs to non-connections. The visual-brief pattern (2026-05-12)
  added a 3–5 slide carousel per post; on 2026-08-07 Claude-authored HTML/SVG replaced Gamma.
- **Phase 2b: project ideation.** A skill proposing three scored projects from event topic intersections.
- **Phase 3 (form + light automation) and Phase 4 (parallel agents from a form trigger).** Never built; superseded
  by roadmap v2 (2026-09-12). The planned Vercel post-event upload form was replaced by `/post-event-content`.

## The three-layer architecture program (2026-05-13)

Goal: make "build better, not faster" the default for every project Alex opens.

| Layer | What it does | Issues |
|---|---|---|
| A. Distribution | Skills/agents/commands ship to all projects | YED-25 → YED-28 (the `alex` plugin, shipped 2026-05-15) |
| B. Discipline | Cross-project invariants (Linear as source of truth, session-start habits) | YED-26, YED-27 → YED-29 (user-scope) |
| C. Workspace | Project overlays inherit canonical defaults | YED-30 (canonical CLAUDE.md fragment + starter kit) |

## Execution focus, then the steering bias

A no-architecture, publishing-only window ran 2026-05-15 → 2026-06-11. It raised publishing, then inverted:
deferral itself became the drag. It was retired and replaced by a steering bias: build freely, but every build
removes a named friction on the publishing path. The 2026-09-28 reset generalized it: a new hook, gate, judge seat,
ledger or dashboard needs a named product failure observed at least twice.

## The build-rigor and measurement layer (2026-06-25 → 2026-09-28)

A diagnosed Shifting-the-Burden pattern (rigor lived in optional docs, not the execution path) produced: the
Definition-of-Done gate and `/dod-close`; the build-session telemetry Stop hook projected to PostHog; the
build-quality judge (`/judge-build`, rubric versions @2 → @6), later a Sonnet + Gemini quorum and a shadow OpenAI
seat with a trust ladder and calibration gates; goal-tagging and `/tag-outcome`; the weekly `/rigor-review`; and a
value-action registry. Supabase was banned from this layer (and Langfuse / gtm-os tombstoned), while Supabase became
the system of record for the Market-Intelligence Engine (2026-06-28).

On 2026-09-28 four reviews found commits running about 2:1 meta vs product and a judge layer whose calibration never
beat its do-nothing baseline. The reset removed the extra judge seats, quorum and trust ladder (YED-231), moved
telemetry out of git (YED-229), pruned dead agents/commands/skills, and cut `CLAUDE.md` to a size ceiling Alex holds
(≤1,800 words, ≤3 wired hooks, one-in-one-out). The pre-cut state is tagged `archive/pre-reset-2026-09-28`.
